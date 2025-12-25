import abc
import logging
import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable, Collection, Hashable, Iterable, Mapping
from contextvars import ContextVar  # noqa: pycharm
from typing import Any, Dict, FrozenSet, Generic, List, Literal, NewType, Optional, TypedDict, TypeVar, Union

from aiohttp.web import Application

from kaiju_tools.types import Namespace, NSKey, RequestContext, Scope, Session


__all__ = [
    'Cache',
    'DataStore',
    'UserInterface',
    'TokenInterface',
    'AbstractRPCCompatible',
    'PublicInterface',
    'SessionInterface',
    'AuthenticationInterface',
    'Locks',
    'RPCServer',
    'RPCClient',
    'ServiceManagerInterface',
    'App',
    'TokenLoginInterface',
    'Stream',
    '_Session',
]


_Session = TypeVar('_Session', bound=Session)


class App(Application, Generic[_Session]):
    """Web application."""

    id: str
    """Unique instance id (auto-generated)."""

    name: str
    """Application name (i.e. type)."""

    version: str
    """App version."""

    env: str
    """Current environment: dev, prod, etc."""

    debug: bool
    """App is running in debug mode (with --debug flag)."""

    loglevel: str
    """Root log level."""

    logger: logging.Logger
    """Application root logger."""

    services: 'ServiceManagerInterface'
    """Services map."""

    settings: dict
    """Application settings."""

    namespace: 'Namespace'
    """Application namespace."""

    namespace_shared: 'Namespace'
    """Shared namespace for the current environment."""

    request_context: ContextVar[RequestContext | None]
    """Client request context is stored here."""

    request_session: ContextVar[_Session | None]
    """Client session context is stored here."""

    db_meta: Any
    """Database metadata."""

    cookie_key: str
    """HTTP cookie key for client sessions."""


class ServiceManagerInterface(abc.ABC):
    """Application service initializer interface."""

    @abc.abstractmethod
    async def __aenter__(self):
        ...

    @abc.abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        ...

    @abc.abstractmethod
    def __getitem__(self, item: str) -> object:
        ...

    @abc.abstractmethod
    def add_service(self, service, required: bool = True, name: str = None) -> None:
        ...

    @abc.abstractmethod
    def discover_service(self, name=None, cls=None, required: bool = True) -> Optional:
        ...

    @abc.abstractmethod
    def items(self) -> Iterable:
        ...


class Cache(abc.ABC):
    """Data key-value store."""

    namespace: Namespace

    @abc.abstractmethod
    async def get(self, id: NSKey) -> Any:
        ...

    @abc.abstractmethod
    async def m_get(self, id: Collection[NSKey]) -> dict[NSKey, Any]:
        ...

    @abc.abstractmethod
    async def exists(self, id: NSKey) -> bool:
        ...

    @abc.abstractmethod
    async def m_exists(self, id: Collection[NSKey]) -> frozenset[NSKey]:
        ...

    @abc.abstractmethod
    async def set(self, id: NSKey, data, ttl: int = None) -> None:
        ...

    @abc.abstractmethod
    async def m_set(self, data: dict[NSKey, Any], ttl: int = None) -> None:
        ...

    @abc.abstractmethod
    async def delete(self, id: NSKey) -> None:
        ...

    @abc.abstractmethod
    async def m_delete(self, id: Collection[NSKey]) -> None:
        ...


class Stream(abc.ABC):
    """Streaming interface."""

    @abc.abstractmethod
    async def lock(self) -> None:
        ...

    @abc.abstractmethod
    async def unlock(self) -> None:
        ...

    @property
    @abc.abstractmethod
    def locked(self) -> bool:
        ...


class Locks(abc.ABC):
    """Shared (between apps) locks management."""

    LockId = NewType('LockId', str)

    @abc.abstractmethod
    async def acquire(
        self, id: NSKey, identifier: LockId = None, ttl: int = None, wait: bool = True, timeout: float = None
    ) -> LockId:
        ...

    @abc.abstractmethod
    async def release(self, id: NSKey, identifier: LockId) -> None:
        ...

    @abc.abstractmethod
    async def owner(self, id: NSKey) -> LockId | None:
        ...

    @abc.abstractmethod
    async def is_owner(self, id: NSKey) -> bool:
        ...

    @abc.abstractmethod
    async def m_exists(self, id: Collection[NSKey]) -> frozenset[NSKey]:
        ...


_Columns = Union[Collection[str], Literal['*'], None]


class DataStore(abc.ABC):
    """Data row-column store."""

    @abc.abstractmethod
    async def get(self, id: Hashable, columns: _Columns = '*', _connection=None):
        ...

    @abc.abstractmethod
    async def m_get(self, id: Collection[Hashable], columns: _Columns = '*', _connection=None):
        ...

    @abc.abstractmethod
    async def exists(self, id: Hashable, _connection=None):
        ...

    @abc.abstractmethod
    async def m_exists(self, id: Collection[Hashable], _connection=None):
        ...

    @abc.abstractmethod
    async def delete(self, id: Hashable, columns: _Columns = None, _connection=None):
        ...

    @abc.abstractmethod
    async def m_delete(
        self, id: Collection[Hashable] = None, conditions: dict = None, columns: _Columns = None, _connection=None
    ):
        ...

    @abc.abstractmethod
    async def create(
        self,
        data: dict,
        columns: _Columns = '*',
        _connection=None,
        on_conflict: str = None,
        on_conflict_keys: Collection = None,
        on_conflict_values=None,
    ):
        ...

    @abc.abstractmethod
    async def m_create(
        self,
        data: Collection,
        columns: _Columns = '*',
        _connection=None,
        on_conflict: str = None,
        on_conflict_keys: Collection = None,
        on_conflict_values: dict = None,
    ):
        ...

    @abc.abstractmethod
    async def update(self, id: Hashable, data, columns: _Columns = '*', _connection=None):
        ...

    @abc.abstractmethod
    async def m_update(
        self, id: Collection[Hashable], data, conditions: dict = None, columns: _Columns = '*', _connection=None
    ):
        ...

    @abc.abstractmethod
    async def iter(
        self, conditions: dict = None, sort=None, offset: int = 0, limit: int = 10, columns: _Columns = '*'
    ) -> AsyncGenerator[list, None]:
        ...


_User = TypeVar('_User')


class UserInterface(Generic[_User], abc.ABC):
    """User login interface."""

    @abc.abstractmethod
    async def auth(self, username: str, password: str) -> _User | None:
        """User login and password check.

        Must return None if no user or token is invalid.
        """

    @abc.abstractmethod
    async def register(self, username: str, email: str, password: str, settings: dict = None) -> _User:
        """Register a new user."""

    @abc.abstractmethod
    async def change_password(self, username: str, password: str, new_password: str):
        """Change user password."""

    @abc.abstractmethod
    async def update_profile(self, id: uuid.UUID, settings: dict):
        """Update current user profile."""

    @abc.abstractmethod
    async def get_user_and_permissions(self, id: uuid.UUID):
        """Get user and user permissions info."""


class TokenInterface(Generic[_User], abc.ABC):
    """Auth token interface."""

    class TokenClaims(TypedDict):
        """JWT token claims data."""

        id: uuid.UUID
        permissions: Collection[str]

    class TokenInfo(TypedDict):
        """JWT methods output."""

        access: str
        refresh: str

    @abc.abstractmethod
    async def auth(self, token: str, /) -> TokenClaims | None:
        """Verify an auth token and return token user data.

        Must return None if no user or token is invalid.
        """

    @abc.abstractmethod
    async def get(self, claims: TokenClaims, /) -> TokenInfo:
        """Generate a token pair (access / refresh tokens)."""

    @abc.abstractmethod
    async def refresh(self, token: str, /) -> TokenInfo | None:
        """Generate a token pair (access / refresh tokens)."""


class SessionInterface(Generic[_Session], abc.ABC):
    """Session management interface."""

    @abc.abstractmethod
    def get_new_session(self, data: dict, *, user_agent: str | bytes = None) -> _Session:
        ...

    @abc.abstractmethod
    async def load_session(self, session_id: str, /, *, user_agent: str = None) -> _Session | None:
        ...

    @abc.abstractmethod
    async def session_exists(self, session_id: str, /) -> bool:
        ...

    @abc.abstractmethod
    async def save_session(self, session: _Session, /) -> None:
        ...

    @abc.abstractmethod
    async def delete_session(self, session: _Session, /) -> None:
        ...


class AuthenticationInterface(Generic[_Session], abc.ABC):
    """Authentication from auth strings / headers / tokens."""

    @abc.abstractmethod
    async def header_auth(self, auth_string: str, /) -> _Session | None:
        ...

    @abc.abstractmethod
    async def basic_auth(self, auth_string: str, /) -> _Session:
        ...

    @abc.abstractmethod
    async def password_auth(self, session: _Session, username: str, password: str) -> _Session:
        ...

    @abc.abstractmethod
    async def token_auth(self, token: str, /) -> _Session:
        ...


class TokenLoginInterface(abc.ABC):
    """Token client interface."""

    @abc.abstractmethod
    async def get_token(self) -> TokenInterface.TokenInfo:
        ...


class PublicInterface(abc.ABC):
    """Class with an RPC interface."""

    DEFAULT_PERMISSION = '*'

    class PermissionKeys:
        """Permission scopes."""

        GLOBAL_SYSTEM_PERMISSION = Scope.SYSTEM
        GLOBAL_USER_PERMISSION = Scope.USER
        GLOBAL_GUEST_PERMISSION = Scope.GUEST

    app: App  # service app

    def get_session(self):
        """Get current user session."""
        return self.app.request_session.get()

    def get_request_context(self) -> RequestContext | None:
        """Get current user request context."""
        return self.app.request_context.get()

    def get_user_id(self):
        """Return current session user id."""
        session = self.get_session()
        return session.user_id if session else None

    def has_permission(self, permission: str) -> bool:
        """Check  if a user session has a particular permission."""
        session = self.get_session()
        return permission in session.permissions or self.system_user() if session else True

    def system_user(self) -> bool:
        """Check if user session has the system scope."""
        session = self.get_session()
        return self.PermissionKeys.GLOBAL_SYSTEM_PERMISSION.value >= session.scope.value if session else None

    @property
    def routes(self) -> dict:
        """List RPC routes."""
        return {}

    @property
    def permissions(self) -> dict:
        """List RPC routes permissions."""
        return {}

    @property
    def validators(self) -> dict:
        """List of RPC routes validation schemas."""
        return {}


AbstractRPCCompatible = PublicInterface


class RPCServer(abc.ABC):
    """JSONRPC server interface."""

    @abc.abstractmethod
    async def call(
        self,
        body,
        headers: Mapping,
        callback: Callable[..., Awaitable] = None,
    ) -> tuple:
        pass


class RPCClient(abc.ABC):
    """JSONRPC client interface."""

    @abc.abstractmethod
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
    ) -> Optional:
        ...

    @abc.abstractmethod
    async def call_multiple(
        self,
        requests,
        raise_exception: bool = True,
        nowait: bool = False,
        max_timeout: int = None,
        use_context: bool = True,
        retries: int = None,
        abort_on_error: bool = None,
        use_template: bool = None,
        headers: dict = None,
    ) -> Optional:
        ...
