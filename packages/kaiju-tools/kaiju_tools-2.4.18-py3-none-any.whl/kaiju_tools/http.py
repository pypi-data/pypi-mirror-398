"""HTTP services and classes."""

import logging
from collections.abc import Collection
from pathlib import Path
from time import time
from typing import cast

from aiohttp import BasicAuth
from aiohttp.client import ClientResponseError, ClientSession, TCPConnector
from aiohttp.cookiejar import CookieJar
from aiohttp.web import HTTPUnauthorized, Request, Response, View, middleware
from aiohttp.web_exceptions import HTTPClientError
from aiohttp_cors import CorsViewMixin

from kaiju_tools.app import ContextableService
from kaiju_tools.context_vars import REQUEST_SESSION
from kaiju_tools.encoding import dumps, loads
from kaiju_tools.exceptions import ClientError, HTTPRequestError, InternalError
from kaiju_tools.interfaces import App
from kaiju_tools.rpc import BaseRPCClient, JSONRPCHeaders, RPCError, RPCRequest


__all__ = [
    "HTTPService",
    "RPCClientService",
    "error_middleware",
    "JSONRPCView",
    "RPCClientService",
    "session_middleware",
    "simple_token_auth_middleware",
]


class HTTPService(ContextableService):
    """HTTP transport."""

    UPLOAD_CHUNK_SIZE = 4096 * 1024

    def __init__(
        self,
        app,
        *,
        host: str = "http://localhost:80",
        headers: dict = None,
        session: ClientSession = None,
        conn_settings: dict = None,
        tcp_connector_settings: dict = None,
        auth: dict | str = None,
        cookie_settings: dict = None,
        request_logs: bool = False,
        response_logs: bool = False,
        logger: logging.Logger = None,
    ):
        """Initialize.

        :param app: web app
        :param host: full hostname
        :param headers: default request headers
        :param session: session object
        :param conn_settings: aiohttp ClientSession params
            read_timeout: int - (s) max total time for a request
            conn_timeout: int - (s) max time to establish a connection
        :param tcp_connector_settings: aiohttp TCPConnector params
            limit: int - max number of connections in the pool
        :param auth: basic auth settings — "login", "password" and
            (optional) "encoding" (ignored if a session has been passed)
            or pass a single string which goes directly into the authorization header.
        :param cookie_settings: aiohttp cookie jar settings
        :param response_logs: log responses
        :param logger: a logger for a super class
        :param request_logs: enable request logs
        """
        super().__init__(app=app, logger=logger)
        self.host = host.rstrip("/")
        self.cookie_settings = cookie_settings or {}
        self.conn_settings = conn_settings or {}
        self.tcp_connector_settings = tcp_connector_settings or {}
        self.headers = headers or {}
        if isinstance(auth, str):
            headers["Authorization"] = auth
            self.auth = None
        elif isinstance(auth, dict):
            self.auth = BasicAuth(**auth)
        else:
            self.auth = None
        self._request_logs = request_logs
        self._response_logs = response_logs
        self.session = None

    async def init(self):
        connector = TCPConnector(ssl=False, **self.tcp_connector_settings)
        self.session = ClientSession(
            connector=connector,
            cookie_jar=CookieJar(**self.cookie_settings),
            headers=self.headers,
            json_serialize=dumps,
            raise_for_status=False,
            auth=self.auth,
            **self.conn_settings,
        )

    async def close(self):
        if not self.closed:
            await self.session.close()

    async def upload_file(self, uri: str, file: Path | str, method: str = "post", chunk_size=UPLOAD_CHUNK_SIZE):
        """Upload file to a remote location."""
        """Upload a file."""

        def _read_file(path):
            with open(path, "rb") as f:
                chunk = f.read(chunk_size)
                while chunk:
                    yield chunk
                    chunk = f.read(chunk_size)

        if type(file) is str:
            file = Path(file)
        result = await self.request(method=method, uri=uri, data=_read_file(file))
        return result

    async def request(
        self,
        method: str,
        uri: str,
        *,
        data=None,
        json=None,
        params=None,
        headers=None,
        accept_json: bool = True,
        **kws,
    ) -> dict:
        """Make a http rest request."""
        url = self.resolve(uri)
        if params:
            params = {str(k): str(v) for k, v in params.items()}
        if self._request_logs:
            if json:
                record = json
            elif data:
                record = "[BYTES]"
            else:
                record = None
            self.logger.info("Request", method=method, url=url, params=params, body=record)
        if headers:
            headers = {k: str(v) for k, v in headers.items()}
        t0 = time()
        if json:
            data = dumps(json)
        async with self.session.request(
            method,
            url,
            params=params,
            headers=headers,
            data=data,
            # cookies=self.session.cookie_jar._cookies,  # noqa ? pycharm
            **kws,
        ) as response:
            response.encoding = "utf-8"
            text = await response.text()
            t = int((time() - t0) * 1000)
            if response.status >= 400:
                try:
                    if accept_json:
                        text = loads(text)
                except (TypeError, ValueError):
                    text = None
                exc = ClientResponseError(
                    message=str(text) if text else "",
                    request_info=response.request_info,
                    history=response.history,
                    status=response.status,
                )
                exc.params = params
                exc.took_ms = t
                exc.request = json if json else None
                exc.response = text
                self.logger.error(
                    "Response (error)",
                    method=method,
                    url=url,
                    params=params,
                    status=response.status,
                    body=text,
                    took_ms=t,
                )
                raise HTTPRequestError(base_exc=exc, message=str(exc))

        if accept_json:
            text = loads(text) if text else None
        if self._response_logs:
            self.logger.info(
                "Response",
                method=method,
                url=url,
                params=params,
                status=response.status,
                body=text if accept_json else "[BYTES]",
                took_ms=t,
            )
        return text

    def resolve(self, uri: str) -> str:
        return f"{self.host}/{uri.lstrip('/')}"


class RPCClientService(BaseRPCClient):
    """HTTP JSONRPC client service."""

    _transport: HTTPService

    def __init__(self, *args, base_uri: str = "/public/rpc", **kws):
        """Initialize."""
        super().__init__(*args, **kws)
        self.base_uri = base_uri

    def get_transport(self):
        return self.discover_service(self._transport, cls=HTTPService)

    async def _request(self, body: RPCRequest | Collection[RPCRequest], headers: dict):
        """Make a HTTP request."""
        return await self._transport.request("post", self.base_uri, json=body, headers=headers)


@middleware
async def error_middleware(request: Request, handler):
    """Wrap an error in RPC exception."""
    try:
        return await handler(request)
    except HTTPClientError as exc:
        request.app.logger.error(str(exc))
        error = ClientError(message=str(exc), uri=request.raw_path, base_exc=exc)
        error.status_code = exc.status_code
        return Response(
            body=dumps(RPCError(id=None, error=error)),
            status=exc.status_code,
            content_type="application/json",
        )
    except Exception as exc:
        request.app.logger.error(str(exc), exc_info=exc)
        return Response(
            body=dumps(RPCError(id=None, error=InternalError(message="Internal error", base_exc=exc))),
            status=500,
            content_type="application/json",
        )


@middleware
async def simple_token_auth_middleware(request: Request, handler):
    """Simple token authorization middleware.

    Checks an incoming request against a static auth token. Would block any HTTP routes if the token is invalid.
    This auth method does not provide any roles or permissions and does not require user services.

    Expects an `Authorization: Bearer <token>` header.

    You should add a token value to your application config into `settings.etc.token` key.
    """
    app = cast(App, request.app)
    headers = request.headers
    auth = headers.get("Authorization")
    if auth and auth.startswith("Bearer "):
        token = auth.replace("Bearer", "").strip()
        if token == app.settings.etc.get("token"):
            return await handler(request)

    raise HTTPUnauthorized()


_session_header = JSONRPCHeaders.SESSION_ID_HEADER


@middleware
async def session_middleware(request: Request, handler):
    """Load and save session id."""
    app = cast(App, request.app)
    headers = request.headers
    if _session_header in headers:
        request["session_id"] = headers[_session_header]
        return await handler(request)
    else:
        # set up a session id for the handler
        if app.cookie_key in request.cookies:
            request["session_id"] = session_id = request.cookies[app.cookie_key]
        else:
            session_id = None
        response = await handler(request)
        if _session_header in response.headers:
            new_session_id = response.headers[_session_header]
            if new_session_id != session_id:
                session = REQUEST_SESSION.get()
                if session:
                    response.set_cookie(
                        app.cookie_key, new_session_id, max_age=session.lifetime, secure=not app.debug, httponly=True
                    )

        return response


class JSONRPCView(CorsViewMixin, View):
    """JSON RPC server endpoint."""

    async def _iter(self):
        req = self.request
        if req.method.lower() != "post":
            self._raise_allowed_methods()
        if not req.can_read_body:
            return Response()
        rpc = req.app.services["rpc"]  # noqa
        if not rpc.not_full.is_set():
            await rpc.not_full.wait()
        data = await req.read()
        data = loads(data)
        headers, result = await rpc.call(data, headers=req.headers, session_id=req.get("session_id"))
        data = dumps(result)
        return Response(
            body=data,
            status=200,
            headers=headers,
            content_type="application/json",
        )
