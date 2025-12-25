"""RPC services and classes."""

import abc
import asyncio
import inspect
import os
import warnings
from binascii import b2a_hex
from collections.abc import Awaitable, Callable, Collection, Mapping
from enum import Enum
from fnmatch import fnmatch
from time import time
from typing import Any, NotRequired, TypedDict, cast, overload

from msgspec import ValidationError as MsgSpecValidationError

from kaiju_tools.annotations import AnnotationParser, FunctionAnnotation
from kaiju_tools.app import REQUEST_CONTEXT, REQUEST_SESSION, ContextableService, RequestContext, Scheduler
from kaiju_tools.exceptions import *
from kaiju_tools.functions import get_short_uid, retry, timeout
from kaiju_tools.interfaces import (
    AbstractRPCCompatible,
    AuthenticationInterface,
    PublicInterface,
    RPCClient,
    RPCServer,
    SessionInterface,
)
from kaiju_tools.jsonschema import compile_schema
from kaiju_tools.sessions import TokenClientService
from kaiju_tools.templates import Template
from kaiju_tools.types import Scope, Session


__all__ = (
    "JSONRPC",
    "RPCRequest",
    "RPCResponse",
    "RPCError",
    "JSONRPCHeaders",
    "AbstractRPCCompatible",
    "PermissionKeys",
    "AbstractTokenInterface",
    "RPCClientError",
    "RPCServer",
    "RPCClient",
    "MethodInfo",
    "JSONRPCServer",
    "Scope",
    "Session",
    "BaseRPCClient",
    "debug_only",
)

JSONRPC = "2.0"  #: protocol version


_RequestId = int | None


def debug_only(f):
    """Decorate a debug-only method (will not be available in production)."""
    f._debug_only_ = True
    return f


class RPCRequest(TypedDict):
    """RPC request object."""

    id: NotRequired[_RequestId]
    method: str
    params: NotRequired[dict | None]


class RPCResponse(TypedDict):
    """RPC response object."""

    id: _RequestId
    result: Any


class RPCError(TypedDict):
    """RPC error object."""

    id: _RequestId
    error: APIException


class JSONRPCHeaders:
    """List of JSONRPC request / response headers."""

    AUTHORIZATION = "Authorization"
    CONTENT_TYPE_HEADER = "Content-Type"
    USER_AGENT = "User-Agent"

    APP_ID_HEADER = "App-Id"
    SERVER_ID_HEADER = "Server-Id"
    CORRELATION_ID_HEADER = "Correlation-Id"

    REQUEST_DEADLINE_HEADER = "Deadline"
    REQUEST_TIMEOUT_HEADER = "Timeout"
    RETRIES = "RPC-Retries"
    CALLBACK_ID = "RPC-Callback"
    ABORT_ON_ERROR = "RPC-Batch-Abort-Error"
    USE_TEMPLATE = "RPC-Batch-Template"

    SESSION_ID_HEADER = "Session-Id"


class PermissionKeys:
    """Permission scopes."""

    GLOBAL_SYSTEM_PERMISSION = Scope.SYSTEM
    GLOBAL_USER_PERMISSION = Scope.USER
    GLOBAL_GUEST_PERMISSION = Scope.GUEST


class AbstractTokenInterface(abc.ABC):
    """Describes a token provider service methods to be able to be used by the :class:`.AbstractRPCClientService`."""

    @abc.abstractmethod
    async def get_token(self) -> str:
        """Must always return a valid auth token."""


class RPCClientError(APIException):
    """JSON RPC Python exception class."""

    def __init__(self, *args, response=None, **kws):
        super().__init__(*args, **kws)
        self.response = response

    def __str__(self):
        return self.message


class _Task(asyncio.Task):
    deadline: int
    started: int


class _Aborted(APIException):
    pass


class MethodInfo(TypedDict):
    """Stored method data."""

    f: Callable
    args: frozenset
    kws: frozenset
    keys: frozenset
    variable_args: bool
    signature: FunctionAnnotation
    service_name: str
    permission: Scope
    validator: Callable


_correlation_id = JSONRPCHeaders.CORRELATION_ID_HEADER
_deadline = JSONRPCHeaders.REQUEST_DEADLINE_HEADER
_timeout = JSONRPCHeaders.REQUEST_TIMEOUT_HEADER
_authorization = JSONRPCHeaders.AUTHORIZATION
_retries = JSONRPCHeaders.RETRIES
_use_template = JSONRPCHeaders.USE_TEMPLATE
_abort_on_error = JSONRPCHeaders.ABORT_ON_ERROR


class JSONRPCServer(ContextableService, PublicInterface, RPCServer):
    """A simple JSON RPC interface with method execution and management tasks."""

    service_name = "rpc"
    _permission_levels = {
        PublicInterface.PermissionKeys.GLOBAL_SYSTEM_PERMISSION: Scope.SYSTEM,
        PublicInterface.PermissionKeys.GLOBAL_USER_PERMISSION: Scope.USER,
        PublicInterface.PermissionKeys.GLOBAL_GUEST_PERMISSION: Scope.GUEST,
    }
    secrets = {"password", "token", "access", "refresh", "secret"}

    def __init__(
        self,
        app,
        *,
        scheduler: Scheduler = None,
        session_service: SessionInterface = None,
        auth_service: AuthenticationInterface = None,
        max_parallel_tasks: int = 128,
        default_request_time: int = 90,
        max_request_time: int = 600,
        enable_permissions: bool = True,
        request_logs: bool = False,
        response_logs: bool = False,
        blacklist_routes: list[str] = None,
        blacklist_scope: int = Scope.SYSTEM.value - 1,
        use_annotation_parser: bool = False,
        logger=None,
    ):
        """Initialize.

        :param app: web app
        :param scheduler: task scheduler
        :param session_service: session backend
        :param max_parallel_tasks: max number of tasks in the loop
        :param default_request_time: default request time in seconds if not specified by a header
        :param max_request_time: maximum allowed request time in seconds
        :param enable_permissions: enable perm checks in requests
        :param request_logs: log request body and also log responses (even successful ones)
        :param blacklist_routes: wildcard patterns to blacklist certain RPC routes
        :param blacklist_scope: integer value to blacklist permission scopes lower or equal to this value
        :param use_annotation_parser: annotation parser for non-validated method will be used and will try to
            create a method validator from its annotations
            (currently it's not very reliable)
        :param logger: logger instance
        """
        ContextableService.__init__(self, app=app, logger=logger)
        self._scheduler = scheduler
        self._sessions = session_service
        self._auth = auth_service
        self._max_parallel_tasks = max(1, int(max_parallel_tasks))
        self._default_request_time = max(1, int(default_request_time))
        self._max_request_time = max(self._default_request_time, int(max_request_time))
        self._enable_permissions = enable_permissions
        self._debug = self.app.debug
        self._request_logs = request_logs
        self._response_logs = response_logs
        self._logs = self._request_logs or self._response_logs
        self._blacklist_routes = blacklist_routes if blacklist_routes else []
        self._blacklist_scope = blacklist_scope
        self._use_annotation_parser = use_annotation_parser
        self._counter = self._max_parallel_tasks
        self.not_full = asyncio.Event()
        self.not_full.set()
        self._empty = asyncio.Event()
        self._empty.set()
        self._methods: dict[str, MethodInfo] = {}
        self._task_reset_state = None

    async def init(self):
        if not self._enable_permissions:
            warnings.warn("Server permissions are disabled.")
        self._counter = self._max_parallel_tasks
        self._empty.set()
        self.not_full.set()
        self._scheduler = self.discover_service(self._scheduler, cls=Scheduler)
        self._sessions = self.discover_service(self._sessions, cls=SessionInterface, required=False)
        self._auth = self.discover_service(self._auth, cls=AuthenticationInterface, required=False)
        await super().init()
        self._task_reset_state = self._scheduler.schedule_task(
            self._reset_empty_state, interval=5, name=f"{self.service_name}._reset_empty_state"
        )

    async def post_init(self):
        for service_name, service in self.app.services.items():
            if isinstance(service, PublicInterface):
                self.register_service(service_name, service)

    async def close(self):
        await self._empty.wait()
        self._task_reset_state.enabled = False
        await super().close()

    @property
    def routes(self):
        return {"api": self.get_routes, "status": self.get_status, "tasks": self.get_tasks}

    @property
    def permissions(self):
        return {
            "api": self.PermissionKeys.GLOBAL_GUEST_PERMISSION,
            "status": self.PermissionKeys.GLOBAL_SYSTEM_PERMISSION,
            "tasks": self.PermissionKeys.GLOBAL_SYSTEM_PERMISSION,
        }

    @staticmethod
    async def get_tasks() -> list:
        """Get all current asyncio tasks."""
        tasks = asyncio.all_tasks(asyncio.get_running_loop())
        t = int(time())
        tasks_info = []
        for task in tasks:
            name = task.get_name()
            data = {"name": name}
            if name.startswith("rpc:"):
                task = cast(_Task, task)
                data.update(
                    {
                        "system": False,
                        "cid": name.split(":")[1],
                        "time_elapsed": t - task.started,
                        "time_left": task.deadline - task.started,
                    }
                )
            else:
                f_code = task.get_stack(limit=1)[-1].f_code
                data.update({"system": True, "coro": f_code.co_name})
            tasks_info.append(data)

        tasks_info.sort(key=lambda o: (o["system"], o["name"]))
        return tasks_info

    async def get_status(self) -> dict:
        """Get server status and current tasks."""
        return {
            "app": self.app.name,
            "app_id": self.app.id,
            "env": self.app.env,
            "debug": self._debug,
            "rpc_tasks": self._max_parallel_tasks - self._counter,
            "queue_full": not self.not_full.is_set(),
            "server_time": int(time()),
            "max_tasks": self._max_parallel_tasks,
            "max_timeout": self._max_request_time,
            "default_timeout": self._default_request_time,
            "enable_permissions": self._enable_permissions,
        }

    async def get_routes(self, pattern: str = "*") -> dict:
        """Get all RPC routes (you are here)."""
        session = self.get_session()
        routes = [
            {
                "route": route,
                "signature": method["signature"],
            }
            for route, method in self._methods.items()
            if not self._enable_permissions
            or (session and method["permission"].value >= session.scope.value and fnmatch(route, pattern))
        ]
        routes.sort(key=lambda o: o["route"])
        return {"api": "jsonrpc", "version": JSONRPC, "spec": "https://www.jsonrpc.org/specification", "routes": routes}

    def register_service(self, service_name: str, service: PublicInterface) -> None:
        """Register an RPC compatible service and its methods."""
        if not isinstance(service, PublicInterface):
            raise TypeError("Service must be rpc compatible.")
        permissions = service.permissions
        validators = service.validators
        for route, f in service.routes.items():
            full_name = f"{service_name}.{route}"
            if self._route_blacklisted(full_name):
                continue
            if not self.app.debug and getattr(f, "_debug_only_", False):
                continue
            route_perm = PublicInterface.PermissionKeys.GLOBAL_SYSTEM_PERMISSION
            for pattern, perm in permissions.items():
                if fnmatch(route, pattern):
                    route_perm = perm
            if route_perm.value <= self._blacklist_scope:
                continue
            try:
                annotation = AnnotationParser.parse_method(type(service), route, f)
            except Exception as exc:
                warnings.warn(f"Cannot automatically create validator for {route}: {exc}")
                annotation = None
            validator = None
            if route in validators:
                params = validators[route]
                if params:
                    if isinstance(params, Callable):
                        validator = params
                    else:
                        validator = compile_schema(params)
            elif self._use_annotation_parser and annotation:
                params = annotation["params"]
                if params:
                    params = params.repr()
                    if params:
                        validator = compile_schema(params)

            sig = inspect.signature(f)
            args, kws = set(), set()
            variable = False
            for key in sig.parameters.values():
                if key.kind == key.VAR_KEYWORD:
                    variable = True
                elif key.kind == key.VAR_POSITIONAL:
                    continue
                elif key.default is key.empty:
                    args.add(key.name)
                else:
                    kws.add(key.name)
            keys = args | kws
            method = MethodInfo(
                f=f,
                args=frozenset(args),
                kws=frozenset(kws),
                keys=frozenset(keys),
                variable_args=variable,
                permission=self._permission_levels[route_perm],
                validator=validator,
                service_name=service_name,
                signature=annotation,
            )
            self._methods[full_name] = method

    def _route_blacklisted(self, route: str) -> bool:
        """Check if a route is blacklisted in the server's `blacklist_routes`."""
        for pattern in self._blacklist_routes:
            if fnmatch(route, pattern):
                return True
        return False

    @overload
    async def call(
        self,
        body: Collection[RPCRequest],
        headers: Mapping,
        scope: Scope = Scope.GUEST,
        session_id: str = None,
        callback: Callable[..., Awaitable] = None,
    ) -> (dict, Collection[RPCResponse | RPCError] | None): ...

    @overload
    async def call(
        self,
        body: RPCRequest,
        headers: Mapping,
        scope: Scope = Scope.GUEST,
        session_id: str = None,
        callback: Callable[..., Awaitable] = None,
    ) -> (dict, RPCResponse | RPCError | None): ...

    async def call(
        self,
        body,
        headers: Mapping,
        scope: Scope = Scope.GUEST,
        session_id: str = None,
        callback: Callable[..., Awaitable] = None,
    ):
        """Call a registered RPC method.

        :param body: request body (RPC request or a batch)
        :param headers: request headers containing request execution instructions for the server
        :param scope: default scope, determines whether a user has a right to call a specific method
        :param session_id: current user session id to acquire user permissions and scope (if None then the `scope`
            arg value will be used as default for this request)
        :param callback: optional response callback which should contain (session, headers, result) input params
        :returns: headers and response body or headers and None if it's a notification request

        There are two ways of calling an RPC method:

        1. Direct with waiting for the result. It requires the request to have `id` other than `None` and `callback`
            argument must also be `None`. The request will be run on the server and the result will be returned
            containing response headers and response / error tuple. Example of the request body:

        .. code-block:: python

            {"id": 0, "params": {}}

        2. Notify request with or without callback. It requires `id` set to `None` or `callback` argument provided
            to the method. The server will return the response headers and `None` result immediately after the request
            validation. The actual request will be processed in background and the result will be send to the
            callback function eventually (if it's provided). Example of the request body:

        .. code-block:: python

            {"id": None, "params": {}}

        If a request id is not provided it's assumed that this request has id=0.

        """
        session = None
        if self._sessions and session_id:
            session = await self._sessions.load_session(session_id)
            if session:
                scope = session.scope
        if self._auth and not session and _authorization in headers:
            try:
                session = await self._auth.header_auth(headers[_authorization])
                if session:
                    scope = session.scope
            except NotAuthorized as exc:
                correlation_id, *_ = self._get_request_headers(headers)
                headers = self._get_response_headers(correlation_id, session)
                return headers, RPCError(id=None, error=exc)

        correlation_id, request_deadline, retries, use_template, abort_on_error = self._get_request_headers(headers)
        if type(body) in {list, tuple}:
            try:
                reqs = [self._prepare_request(req, session, scope, n, use_template) for n, req in enumerate(body)]
                return_result = callback is None and any(req[0] is not None for req in reqs)
            except JSONRPCError as exc:
                headers = self._get_response_headers(correlation_id, session)
                return headers, RPCError(id=exc.data.get("id"), error=exc)

            coro = self._execute_batch(
                reqs,
                retries=retries,
                request_deadline=request_deadline,
                abort_on_error=abort_on_error,
                use_template=use_template,
                session=session,
                correlation_id=correlation_id,
                callback=callback,
            )
        else:
            try:
                f, req_id, method, params = self._prepare_request(body, session, scope, 0, use_template=False)
                return_result = callback is None and req_id is not None
            except JSONRPCError as exc:
                headers = self._get_response_headers(correlation_id, session)
                return headers, RPCError(id=exc.data.get("id"), error=exc)

            coro = self._execute_single(
                f,
                req_id,
                method,
                params,
                retries=retries,
                request_deadline=request_deadline,
                session=session,
                correlation_id=correlation_id,
                callback=callback,
            )
        if not self.not_full.is_set():
            await self.not_full.wait()
        self._counter -= 1
        if self._counter <= 0:
            self._counter = 0
            self.not_full.clear()

        if return_result:
            try:
                return await coro
            finally:
                self._counter += 1
                if not self.not_full.is_set():
                    self.not_full.clear()
        else:
            task = asyncio.create_task(coro)
            task.add_done_callback(self._request_done_cb)
            return self._get_response_headers(correlation_id, session), None

    @staticmethod
    def _get_int_header(value: str | None, default: int) -> int:
        """Parse an integer header value.

        https://httpwg.org/specs/rfc8941.html#integer
        """
        try:
            return int(value) if value else default
        except ValueError:
            return default

    @staticmethod
    def _get_bool_header(value: str | None, default: bool) -> bool:
        """Parse a boolean header value.

        https://httpwg.org/specs/rfc8941.html#boolean
        """
        return value == "?1" if value else default

    def _get_request_headers(self, headers: Mapping) -> tuple:
        t0 = int(time())
        if _deadline in headers:
            request_deadline = min(self._get_int_header(headers[_deadline], 0), t0 + self._max_request_time)
        elif _timeout in headers:
            request_timeout = min(
                self._max_request_time,
                max(1, self._get_int_header(headers[_timeout], self._default_request_time)),
            )
            request_deadline = t0 + request_timeout + 1
        else:
            request_deadline = t0 + self._default_request_time
        if _correlation_id in headers:
            correlation_id = headers[_correlation_id]
        else:
            correlation_id = b2a_hex(os.urandom(5)).decode()
        if _retries in headers:
            retries = min(10, max(0, self._get_int_header(headers.get(_retries), 0)))
        else:
            retries = 0
        if _use_template in headers:
            use_template = self._get_bool_header(headers[_use_template], False)
        else:
            use_template = False
        if _abort_on_error in headers:
            abort_on_error = self._get_bool_header(headers[_abort_on_error], False)
        else:
            abort_on_error = False
        return correlation_id, request_deadline, retries, use_template, abort_on_error

    async def _execute_single(
        self,
        f: Callable,
        request_id: _RequestId,
        method: str,
        params: dict,
        retries: int,
        request_deadline: int,
        session: Session | None,
        correlation_id: str,
        callback: Callable[..., Awaitable],
    ) -> tuple[dict, RPCResponse | RPCError] | None:
        """Execute a single rpc request."""
        ctx = REQUEST_CONTEXT.get()
        new_ctx = RequestContext(
            session_id=session.id if session else None,
            request_deadline=request_deadline,
            correlation_id=correlation_id,
            data={},
        )
        if ctx is None:
            ctx = new_ctx
        else:
            ctx.update(new_ctx)
        REQUEST_CONTEXT.set(ctx)
        if session:
            REQUEST_SESSION.set(session)
        try:
            async with timeout(request_deadline - time()):
                result = await self._execute_request(f, request_id, method, params, retries)
        except TimeoutError:
            result = RPCError(
                id=request_id, error=RequestTimeout(message="Request timeout", request_deadline=request_deadline)
            )
        if self._sessions:
            session = self.get_session()
            if session and session.stored and session.changed:
                await self._sessions.save_session(session)
        if callback:
            headers = self._get_response_headers(correlation_id, session)
            cb = asyncio.create_task(callback(session, headers, result))  # noqa
        if request_id is not None or "error" in result:
            headers = self._get_response_headers(correlation_id, session)
            return headers, result

    @staticmethod
    def _get_response_headers(correlation_id: str, session: Session | None) -> dict:
        headers = {}
        if correlation_id:
            headers[_correlation_id] = correlation_id
        if session:
            if session.stored and (session.changed or session.loaded):
                headers[JSONRPCHeaders.SESSION_ID_HEADER] = session.id
            else:
                headers[JSONRPCHeaders.SESSION_ID_HEADER] = ""
        return headers

    async def _execute_batch(
        self,
        requests: list[tuple[Callable, _RequestId, str, dict]],
        retries: int,
        request_deadline: int,
        abort_on_error: bool,
        use_template: bool,
        session: Session | None,
        correlation_id: str,
        callback: Callable[..., Awaitable],
    ) -> tuple[dict, list[RPCResponse | RPCError]]:
        """Execute multiple coroutine functions."""
        ctx = REQUEST_CONTEXT.get()
        new_ctx = RequestContext(
            session_id=session.id if session else None,
            request_deadline=request_deadline,
            correlation_id=correlation_id,
            data={},
        )
        if ctx is None:
            ctx = new_ctx
        else:
            ctx.update(new_ctx)
        REQUEST_CONTEXT.set(ctx)
        if session:
            REQUEST_SESSION.set(session)
        results, template_ctx, req_id = [], {}, None
        for n, (f, req_id, method, params) in enumerate(requests):
            try:
                if use_template:
                    if n > 0:
                        params = Template(params).fill(template_ctx)
                    _method = self._methods[method]
                    if _method["validator"]:
                        params = _method["validator"](params)
                async with timeout(request_deadline - time()):
                    result = await self._execute_request(f, req_id, method, params, retries)
                if abort_on_error and "error" in result:
                    raise _Aborted from None
                if use_template and "result" in result:
                    template_ctx[str(n)] = result["result"]
            except TimeoutError:
                results.extend(
                    (
                        RPCError(
                            id=req_id,
                            error=RequestTimeout(message="Request timeout", request_deadline=request_deadline),
                        )
                        for f, req_id, method, params in requests[n:]
                    )
                )
                break
            except Exception as exc:
                self.logger.error("Batch error", batch_num=n, request_id=req_id, exc_info=exc)
                results.append(RPCError(id=req_id, error=ValidationError(base_exc=exc)))
                results.extend(
                    (
                        RPCError(id=req_id, error=Aborted(message="Aborted"))
                        for f, req_id, method, params in requests[n + 1 :]
                    )
                )
                break
            else:
                if req_id is not None or "error" in result:
                    results.append(result)
        if self._sessions:
            session = self.get_session()
            if session and session.stored and session.changed:
                await self._sessions.save_session(session)
        headers = self._get_response_headers(correlation_id, session)
        if callback:
            cb = asyncio.create_task(callback(session, headers, result))  # noqa
        if results:
            return headers, results

    def _prepare_request(
        self, body: RPCRequest, session: Session | None, scope: Scope, default_id: int, use_template: bool
    ) -> tuple[Callable, _RequestId, str, dict]:
        """Pre-validate and prepare request for execution."""
        if type(body) is not dict:
            raise InvalidRequest(id=None, message="Request must be an object") from None

        _id = body.get("id", default_id)
        _method_name = body.get("method")
        _method = self._methods.get(_method_name, "")
        if not _method or (
            self._enable_permissions
            and all(
                (
                    _method["permission"].value < scope.value,
                    not session or _method_name not in session.permissions,
                    not session or _method["service_name"] not in session.permissions,
                )
            )
        ):
            raise MethodNotFound(id=_id, message="Method not found", request_method=_method_name) from None

        _params = body.get("params")
        if type(_params) is not dict:
            _params = {}
        if not use_template and _method["validator"]:
            try:
                _params = _method["validator"](_params)
            except Exception as exc:
                raise InvalidParams(id=_id, message=str(exc), base_exc=exc) from None

        if not _method["variable_args"] and (
            not _method["keys"].issuperset(_params) or not _method["args"].issubset(_params)
        ):
            raise InvalidParams(
                id=_id,
                message="Invalid params",
                required_args=_method["args"],
                optional_args=_method["kws"],
                provided_args=list(_params),
            ) from None

        return _method["f"], _id, _method_name, _params

    async def _execute_request(
        self, f: Callable, request_id: _RequestId, method: str, params: dict, retries: int
    ) -> RPCResponse | RPCError:
        """Execute a coro and process an exception."""
        try:
            if retries:
                result = await retry(f, kws=params, retries=retries, logger=self.logger)
            elif params:
                result = await f(**params)
            else:
                result = await f()
        except ClientError as exc:
            result = RPCError(id=request_id, error=exc)
            self.logger.info(
                "Client error", request_id=request_id, method=method, params=self._remove_secrets(params), error=exc
            )
        except APIException as exc:
            result = RPCError(id=request_id, error=exc)
            self.logger.error(
                "Internal error",
                request_id=request_id,
                method=method,
                params=self._remove_secrets(params),
                exc_info=exc,
            )
        except MsgSpecValidationError as exc:
            error_data = getattr(exc, "data", {})
            exc = ValidationError(message=str(exc), data=error_data)
            self.logger.info(
                "Validation error", request_id=request_id, method=method, params=self._remove_secrets(params), error=exc
            )
            result = RPCError(id=request_id, error=exc)
        except Exception as exc:
            result = RPCError(id=request_id, error=InternalError(base_exc=exc, message="Internal error"))
            self.logger.error(
                "Internal error",
                request_id=request_id,
                method=method,
                params=self._remove_secrets(params),
                exc_info=exc,
            )
        else:
            result = RPCResponse(id=request_id, result=result)
            if self._response_logs:
                self.logger.info(
                    "request",
                    request_id=request_id,
                    method=method,
                    params=self._remove_secrets(params),
                    result=result["result"],
                )
            elif self._request_logs:
                self.logger.info("request", request_id=request_id, method=method, params=self._remove_secrets(params))
        return result

    @classmethod
    def _remove_secrets(cls, params: dict) -> dict:
        """Remove sensitive information from the request body."""
        if params:
            for key in cls.secrets:
                if key in params:
                    del params[key]
        return params

    async def _reset_empty_state(self) -> None:
        """Check and reset empty state if needed."""
        if self._counter >= self._max_parallel_tasks:
            self._counter = self._max_parallel_tasks
            self._empty.set()

    def _request_done_cb(self, task: asyncio.Task) -> None:
        """Increment the counter when a request is finished."""
        self._counter += 1
        if not self.not_full.is_set():
            self.not_full.set()
        exc = task.exception()
        if exc:
            self.logger.error("task execution error", exc_info=exc)


class BaseRPCClient(ContextableService, RPCClient, abc.ABC):
    """JSONRPC client."""

    class Topic(Enum):
        """Default topic names."""

        RPC = "rpc"
        MANAGER = "manager"
        EXECUTOR = "executor"

    def __init__(
        self,
        *args,
        transport: str,
        request_logs: bool = False,
        response_logs: bool = False,
        auth_str: str = None,
        scheduler: Scheduler = None,
        token_client: TokenClientService = False,
        error_classes: ErrorRegistry | None = ERROR_CLASSES,
        **kws,
    ):
        super().__init__(*args, **kws)
        self._transport = transport
        self._scheduler = scheduler
        self._request_logs = request_logs
        self._response_logs = response_logs
        self._auth_str = auth_str
        self._token_client = token_client
        self._errors = error_classes

    async def init(self):
        self._transport = self.get_transport()
        self._token_client = self.discover_service(self._token_client, cls=TokenClientService, required=False)

    @abc.abstractmethod
    def get_transport(self): ...

    async def call(
        self,
        method: str,
        params: dict | None = None,
        nowait: bool = False,
        request_id: int = 0,
        max_timeout: int = None,
        use_context: bool = True,
        retries: int = None,
        headers: dict = None,
    ) -> Any | None:
        """Make an RPC call.

        :param method: rpc method name
        :param params: method call arguments
        :param nowait: create a 'notify' request - do not wait for the result
        :param request_id: optional request id (usually you don't need to set it)
        :param max_timeout: request timeout in sec
        :param use_context: use app request context such as correlation id and request chain deadline
        :param retries: optional number of retries (on the server side)
        :param headers: additional headers
        """
        t0 = time()
        headers = self._create_request_headers(headers, max_timeout, use_context, nowait, retries, None, None)
        _id = None if nowait else request_id
        body = RPCRequest(id=_id, method=method, params=params)
        response = await self._request(body, headers)
        result = self._process_response(response) if response else None
        if isinstance(result, Exception):
            raise result
        if self._response_logs:
            self.logger.info("request", request=body, result=response, took_ms=int((time() - t0) * 1000))
        elif self._request_logs:
            self.logger.info("request", request=body, took_ms=int((time() - t0) * 1000))
        return result

    async def call_multiple(
        self,
        requests: Collection[RPCRequest],
        raise_exception: bool = True,
        nowait: bool = False,
        max_timeout: int = None,
        use_context: bool = True,
        retries: int = None,
        abort_on_error: bool = None,
        use_template: bool = None,
        headers: dict = None,
    ) -> list | None:
        """Make an RPC batch call.

        :param requests: list of request dicts
        :param nowait: create a 'notify' request - do not wait for the result
        :param max_timeout: request timeout in sec
        :param use_context: use app request context such as correlation id and request chain deadline
        :param raise_exception: raise exception instead of returning error objects in the list
        :param retries: optional number of retries (on the server side)
        :param abort_on_error: abort the whole batch on the first error
        :param use_template: use templates in batch requests
        :param headers: additional headers
        """
        headers = self._create_request_headers(
            headers, max_timeout, use_context, nowait, retries, abort_on_error, use_template
        )
        for n, req in enumerate(requests):
            req["id"] = n
        response = await self._request(requests, headers)
        if response is None:  # for notify requests
            return
        results = []
        for resp in response:
            resp = self._process_response(resp)
            if isinstance(resp, Exception) and raise_exception:
                raise resp
            results.append(resp)
        return results

    @abc.abstractmethod
    async def _request(self, body: RPCRequest | Collection[RPCRequest], headers: dict):
        """Make an external requests via transport service."""

    def _create_request_headers(
        self, headers, max_timeout, use_context, nowait, retries, abort_on_error, use_template
    ) -> dict:
        headers = headers if headers else {}
        ctx = REQUEST_CONTEXT.get() if use_context else None
        if ctx:
            if JSONRPCHeaders.CORRELATION_ID_HEADER not in headers:
                headers[JSONRPCHeaders.CORRELATION_ID_HEADER] = ctx["correlation_id"]
            if not nowait:
                if ctx["request_deadline"] and not max_timeout:
                    headers[JSONRPCHeaders.REQUEST_DEADLINE_HEADER] = ctx["request_deadline"]
        elif JSONRPCHeaders.CORRELATION_ID_HEADER not in headers:
            headers[JSONRPCHeaders.CORRELATION_ID_HEADER] = get_short_uid()
        if max_timeout:
            headers[JSONRPCHeaders.REQUEST_TIMEOUT_HEADER] = max_timeout
        if self._auth_str:
            headers[JSONRPCHeaders.AUTHORIZATION] = self._auth_str
        elif self._token_client:
            token = self._token_client.get_token()
            if token:
                headers[JSONRPCHeaders.AUTHORIZATION] = f"Bearer {token}"
        if retries:
            headers[JSONRPCHeaders.RETRIES] = retries
        if abort_on_error:
            headers[JSONRPCHeaders.ABORT_ON_ERROR] = "?1"
        if use_template:
            headers[JSONRPCHeaders.USE_TEMPLATE] = "?1"
        return headers

    def _process_response(self, response: RPCResponse | RPCError):
        if "error" in response:
            return self._create_exception(response["error"])
        else:
            return response["result"]

    def _create_exception(self, error_data: dict) -> RPCClientError:
        data = error_data.get("data", {})
        if "type" in data:
            cls = data["type"]
        elif "base_type" in data:
            cls = data["base_type"]
        else:
            cls = None
        cls = self._errors[cls] if self._errors and cls in self._errors else RPCClientError
        exc = cls(message=error_data.get("message"), data=error_data["data"])
        exc.status_code = error_data["code"]
        return exc
