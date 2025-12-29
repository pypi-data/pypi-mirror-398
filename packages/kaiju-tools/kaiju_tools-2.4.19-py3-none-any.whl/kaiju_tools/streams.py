"""Message stream services and classes."""

import abc
import asyncio
from collections.abc import Collection
from typing import final

from kaiju_tools.app import ContextableService, Scheduler, Service
from kaiju_tools.encoding import ENCODERS, MimeType
from kaiju_tools.interfaces import AuthenticationInterface, Locks, SessionInterface, Stream
from kaiju_tools.logging import Logger
from kaiju_tools.rpc import BaseRPCClient, JSONRPCHeaders, JSONRPCServer, RPCError, RPCRequest
from kaiju_tools.types import SCOPES, Namespace, NSKey, Scope


__all__ = ['Listener', 'StreamRPCClient', 'Topic']


@final
class Topic:
    """Default topic names."""

    RPC = 'rpc'
    MANAGER = 'manager'
    EXECUTOR = 'executor'


class Listener(ContextableService, Stream, abc.ABC):
    """Stream consumer assigned to a particular topic."""

    lock_check_interval = 10
    namespace_prefix = '_stream'

    def __init__(
        self,
        app,
        topic: str = Topic.RPC,
        rpc_service: JSONRPCServer = None,
        locks_service: Locks = None,
        scheduler: Scheduler = None,
        session_service: SessionInterface = None,
        authentication_service: AuthenticationInterface = None,
        transport: Service = None,
        shared: bool = False,
        max_parallel_batches: int = None,
        scope: str = Scope.GUEST.name,
        use_sessions: bool = False,
        encoders=ENCODERS,
        logger: Logger = None,
    ):
        super().__init__(app=app, logger=logger)
        self._transport = transport
        self.topic = topic
        self.max_parallel_batches = max_parallel_batches
        self._counter = asyncio.Semaphore(max_parallel_batches) if max_parallel_batches else None
        _ns = self.app.namespace_shared if shared else self.app.namespace
        _ns = _ns / self.namespace_prefix
        self._key = _ns.get_key(self.topic)
        self._lock_key = _ns.create_namespace('_lock').get_key(self.topic)
        self._lock_id = None
        self._scheduler = scheduler
        self._rpc = rpc_service
        self._locks = locks_service
        self._sessions = session_service
        self._auth = authentication_service
        self._scope = SCOPES[scope]
        self._use_sessions = use_sessions
        self._unlocked = asyncio.Event()
        self._idle = asyncio.Event()
        self._loop = None
        self._lock_task = None
        self._closing = True
        self._dumps, self._loads = encoders[MimeType.msgpack.value]

    async def init(self):
        self._closing = False
        self._unlocked.set()
        self._idle.set()
        self._rpc = self.discover_service(self._rpc, cls=JSONRPCServer)
        self._locks = self.discover_service(self._locks, cls=Locks)
        self._sessions = self.discover_service(self._sessions, cls=SessionInterface, required=False)
        self._transport = self.get_transport()
        self._scheduler = self.discover_service(self._scheduler, cls=Scheduler)
        self._auth = self.discover_service(self._auth, cls=AuthenticationInterface, required=False)
        self._loop = asyncio.create_task(self._read(), name=f'{self.service_name}.{self.topic}._read')
        self._lock_task = self._scheduler.schedule_task(
            self._check_lock, interval=self.lock_check_interval, name=f'{self.service_name}._check_lock'
        )

    async def close(self):
        self._closing = True
        self._lock_task.enabled = False
        await self._idle.wait()

    @abc.abstractmethod
    def get_transport(self):
        ...

    async def lock(self) -> None:
        self.logger.info('lock', topic=self._key)
        self._lock_id = await self._locks.acquire(self._lock_key)
        self._unlocked.clear()
        await asyncio.sleep(self.lock_check_interval)  # ensure that everyone else is locked
        if not self._idle.is_set():
            await self._idle.wait()

    async def unlock(self) -> None:
        self.logger.info('unlock', topic=self._key)
        if self._lock_id:
            await self._locks.release(self._lock_key, self._lock_id)
            self._lock_id = None
        self._unlocked.set()

    @property
    def locked(self) -> bool:
        return not self._unlocked.is_set()

    @abc.abstractmethod
    async def _read_batch(self) -> list:
        """Get messages from a stream."""

    @abc.abstractmethod
    async def _process_batch(self, batch: list) -> None:
        """Define your own message processing and commit here."""

    async def _process_request(self, data) -> None:
        """Process a single request in a batch."""
        body, headers = data
        if type(body[0]) is str:  # RPC method
            body = RPCRequest(id=None, method=body[0], params=body[1])
        else:  # batch
            body = [RPCRequest(id=None, method=r[0], params=r[1]) for r in body]
        if self._use_sessions:
            session_id = headers.get(JSONRPCHeaders.SESSION_ID_HEADER)
        else:
            session_id = None
        headers, result = await self._rpc.call(body=body, headers=headers, session_id=session_id, scope=self._scope)
        if type(result) is RPCError:  # here it can be only a pre-request error due to nowait=False
            self.logger.info('Client error', result=result)

    async def _read(self) -> None:
        """Read from a stream."""
        self.logger.info('Starting')
        while not self._closing:
            await self._unlocked.wait()
            try:
                batch = await self._read_batch()
                self._idle.clear()
                if self.max_parallel_batches:
                    async with self._counter:
                        if batch:
                            await self._process_batch(batch)
                else:
                    if batch:
                        await self._process_batch(batch)
            except Exception as exc:
                self.logger.error('Read error', exc_info=exc, topic=self._key)
            finally:
                self._idle.set()

    async def _check_lock(self) -> None:
        """Check for existing shared lock and lock / unlock if needed."""
        existing = await self._locks.m_exists([self._lock_key])
        if self._lock_key in existing:
            if not self.locked:
                self._unlocked.clear()
        elif self.locked:
            self._unlocked.set()


class StreamRPCClient(BaseRPCClient, abc.ABC):
    """Stream client for RPC requests."""

    namespace_prefix = Listener.namespace_prefix

    def __init__(self, *args, app_name: str = None, topic: str = Topic.RPC, **kws):
        """Initialize.

        :param app_name: application (topic) name
        :param listener_service: stream listener service instance
        :param topic: topic name
        """
        super().__init__(*args, **kws)
        self.app_name = app_name if app_name else self.app.name
        self.topic = topic

    async def call(
        self,
        method: str,
        params: dict | None = None,
        nowait: bool = True,
        request_id: int = 0,
        max_timeout: int = None,
        use_context: bool = True,
        retries: int = None,
        headers: dict = None,
        app: str = None,
        topic: str = None,
    ):
        if app is None:
            app = self.app_name
        if topic is None:
            topic = self.topic
        if headers is None:
            headers = {}
        headers['_topic'] = self.get_topic_key(app, topic)
        return await super().call(
            method=method,
            params=params,
            nowait=True,
            max_timeout=max_timeout,
            use_context=use_context,
            retries=retries,
            headers=headers,
        )

    async def call_multiple(
        self,
        requests: Collection[RPCRequest],
        raise_exception: bool = True,
        nowait: bool = True,
        max_timeout: int = None,
        use_context: bool = True,
        retries: int = None,
        abort_on_error: bool = None,
        use_template: bool = None,
        headers: dict = None,
        app: str = None,
        topic: str = None,
    ):
        if app is None:
            app = self.app_name
        if topic is None:
            topic = self.topic
        if headers is None:
            headers = {}
        headers['_topic'] = self.get_topic_key(app, topic)
        return await super().call_multiple(
            requests=requests,
            raise_exception=raise_exception,
            nowait=True,
            max_timeout=max_timeout,
            use_context=use_context,
            retries=retries,
            abort_on_error=abort_on_error,
            use_template=use_template,
            headers=headers,
        )

    def get_topic_key(self, app_name: str, topic: str = Topic.RPC) -> NSKey:
        return Namespace.join(self.app.env, app_name, self.namespace_prefix, topic)

    @abc.abstractmethod
    async def write(self, topic: NSKey, body, headers: dict, key=None) -> None:
        """Submit a message to a stream.

        :param topic: full topic name
        :param body: message body
        :param headers: message headers
        :param key: (optional) unique message id
        """

    async def _request(self, body: RPCRequest | Collection[RPCRequest], headers: dict) -> None:
        """Send an RPC request via stream."""
        if type(body) is dict:  # single
            body = (body['method'], body.get('params'))
        else:  # batch
            body = [(r['method'], r.get('params')) for r in body]  # noqa
        await self.write(headers.pop('_topic'), body, headers=headers)
