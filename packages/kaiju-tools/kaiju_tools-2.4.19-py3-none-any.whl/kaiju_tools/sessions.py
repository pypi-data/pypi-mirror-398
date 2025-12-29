"""Sessions and authentication."""
import abc
import uuid
from base64 import b64decode
from binascii import Error as B64Error
from datetime import datetime
from enum import Enum
from hashlib import blake2b
from secrets import randbits
from time import time
from typing import Optional, Tuple, Union, cast, final

from kaiju_tools.app import ContextableService, Scheduler
from kaiju_tools.exceptions import NotAuthorized, NotFound
from kaiju_tools.interfaces import (
    AuthenticationInterface,
    Cache,
    DataStore,
    PublicInterface,
    RPCClient,
    SessionInterface,
    TokenInterface,
    TokenLoginInterface,
    UserInterface,
    _Session,
)
from kaiju_tools.types import Session


__all__ = [
    'SessionService',
    'AuthType',
    'AuthenticationService',
    'LoginService',
    'UserInterface',
    'TokenInterface',
    'SessionInterface',
    'AuthenticationInterface',
    'Session',
    'TokenClientService',
]


@final
class AuthType(Enum):
    """Client authentication types."""

    PASSWORD = 'PASSWORD'  #: login-password auth
    TOKEN = 'TOKEN'  #: token based auth
    BASIC = 'BASIC'  #: basic auth


class SessionService(ContextableService, SessionInterface):
    """Session store interface used by the rpc server."""

    service_name = 'sessions'
    session_cls = Session

    def __init__(
        self,
        app,
        session_store: DataStore,
        cache_service: Cache = None,
        session_idle_timeout: int = 24 * 3600,
        exp_renew_interval: int = 3600,
        salt: str = 'SALT',
        shared: bool = False,
        logger=None,
    ):
        """Initialize.

        :param app: web app
        :param cache_service: cache service instance
        :param session_idle_timeout: (s) Idle lifetime for each session.
        :param exp_renew_interval: (s)
        :param salt: salt for user agent hashing, change it to invalidate all current sessions
        :param logger:
        """
        super().__init__(app, logger=logger)
        self.ns = self.app.namespace_shared if shared else self.app.namespace
        self.ns = self.ns / '_session'
        self._cache = cache_service
        self._store = session_store
        self.session_idle_timeout = session_idle_timeout
        self.exp_renew_interval = exp_renew_interval
        self.salt = salt.encode('utf-8')

    async def init(self):
        self._cache = self.discover_service(self._cache, cls=Cache)
        self._store = self.discover_service(self._store, cls=DataStore)

    def get_new_session(self, data: dict, *, user_agent: Union[str, bytes] = '') -> Session:
        """Create and return a new session (not stored yet).

        :param data: session data
        :param user_agent: user agent or client id or hash to match session in subsequent requests
        """
        h_agent = self._get_agent_hash(user_agent) if type(user_agent) is str else user_agent
        session = self._create_new_session(data, h_agent)
        self.logger.debug('new session', session_id=session.id)
        return session

    async def session_exists(self, session_id: str, /) -> bool:
        """Check if session exists in the session cache."""
        return await self._cache.exists(self.ns.get_key(session_id))

    async def save_session(self, session: Session, /) -> None:
        """Save session to the storage.

        The session will be stored only if it is marked as stored, and it has been changed.
        Token-auth sessions and initial sessions without data won't be stored.
        """
        if not session or not session.stored:
            return

        key = self.ns.get_key(session.id)
        exp = int(time()) + self.session_idle_timeout
        if session.changed:
            self.logger.info('saving session', session_id=session.id)
            await self._cache.set(key, session.repr(), ttl=self.session_idle_timeout)
            data = session.repr()
            data['expires'] = exp
            await self._save_session(data)
        elif session.loaded and session.expires - time() < self.exp_renew_interval:
            asyncio.create_task(self._cache._transport.expire(key, exp))  # noqa
            await self._update_session_exp(session.id, exp)

    async def _save_session(self, session_data: dict) -> None:
        """Save session in database backend."""
        await self._store.create(session_data, columns=None)

    async def _update_session_exp(self, session_id, exp) -> None:
        """Save session in database backend."""
        await self._store.update(session_id, {'expires': exp}, columns=None)

    async def delete_session(self, session: Session, /) -> None:
        """Delete session from the storage."""
        if session and session.stored and session.loaded:
            self.logger.info('removing session', session_id=session.id)
            key = self.ns.get_key(session.id)
            await self._cache.delete(key)
            try:
                await self._delete_session(session.id)
            except NotFound:
                pass

    async def _delete_session(self, session_id) -> None:
        """Delete session in database."""
        await self._store.delete(session_id, columns=None)

    async def load_session(self, session_id: str, /, *, user_agent: str = '') -> Optional[Session]:
        """Load session from the storage.

        :param session_id: unique session id
        :param user_agent: user agent or client id for security purposes
        :return: returns None when session is not available
        """
        key = self.ns.get_key(session_id)
        session = cached = await self._cache.get(key)
        if not session:
            try:
                session = await self._get_session(session_id)
            except NotFound:
                self.logger.info('session not found', session_id=session_id)
                return

            if session['expires'] < time():
                self.logger.debug('session expired', session_id=session_id)
                await self._cache.delete(key)
                await self._delete_session(session_id)
                return

        agent_hash = self._get_agent_hash(user_agent)
        session = self.session_cls(**session, _stored=True, _changed=False, _loaded=True)
        if session.h_agent and session.h_agent != agent_hash:
            self.logger.info('user agent mismatch', session_id=session_id)
            return

        self.logger.debug('session loaded', session_id=session_id)
        if not cached:
            ttl = int(session.expires - time())
            await self._cache.set(key, session.repr(), ttl=ttl)
        return session

    async def _get_session(self, session_id) -> dict:
        """Get session data from db."""
        return await self._store.get(session_id, columns='*')

    def _create_new_session(self, data: dict, h_agent: bytes) -> Session:
        """Create a new session object."""
        return self.session_cls(
            id=uuid.UUID(int=randbits(128)).hex,
            user_id=None,
            permissions=frozenset(),
            data=data,
            expires=int(time()) + self.session_idle_timeout,
            created=datetime.now(),
            h_agent=h_agent,
            _changed=bool(data),
            _stored=True,
            _loaded=False,
        )

    def _get_agent_hash(self, user_agent: str) -> bytes:
        return blake2b(user_agent.encode('utf-8'), digest_size=16, salt=self.salt).digest()


class AuthenticationService(ContextableService, AuthenticationInterface):
    """User authentication service."""

    def __init__(
        self,
        *args,
        session_service: SessionService = None,
        user_service: UserInterface = None,
        token_service: TokenInterface = None,
        enable_token_auth: bool = True,
        enable_basic_auth: bool = False,
        **kws,
    ):
        super().__init__(*args, **kws)
        self._sessions = session_service
        self._users = user_service
        self._tokens = token_service
        self.enable_basic_auth = enable_basic_auth
        self.enable_token_auth = enable_token_auth

    async def init(self):
        self._users = self.discover_service(self._users, cls=UserInterface)
        self._sessions = self.discover_service(self._sessions, cls=SessionService)
        self._tokens = self.discover_service(self._tokens, cls=TokenInterface, required=False)

    async def header_auth(self, auth_string: str) -> _Session:
        """Authenticate user using 'Authorization' header."""
        if auth_string.startswith('Bearer ') and self._tokens and self.enable_token_auth:
            return await self.token_auth(auth_string.replace('Bearer ', '', 1))
        elif auth_string.startswith('Basic ') and self.enable_basic_auth:
            return await self.basic_auth(auth_string.replace('Basic ', '', 1))
        else:
            raise NotAuthorized('Unsupported auth method')

    async def basic_auth(self, auth_string: str) -> _Session:
        """Try basic auth.

        Supports both plain '<user>:<password>' strings and b64 encoded (preferred).

        :raises AuthenticationFailed:
        """
        username, password = self._parse_auth_str(auth_string)
        user = await self._users.auth(username=username, password=password)
        if not user:
            raise NotAuthorized('Invalid credentials')
        session = self._sessions.get_new_session({})
        self._update_session(session, user, AuthType.BASIC)
        self.logger.info('login completed', auth_type=AuthType.BASIC.value, user_id=user['id'])
        return session

    async def password_auth(self, session: _Session, username: str, password: str) -> _Session:
        """Authenticate a user by directly providing a login / password.

        :raises AuthenticationFailed:
        """
        user = await self._users.auth(username=username, password=password)
        if not user:
            raise NotAuthorized('Invalid credentials')
        self._update_session(session, user, AuthType.PASSWORD)
        self.logger.info('login completed', auth_type=AuthType.PASSWORD.value, user_id=user['id'])
        return session

    async def token_auth(self, token: str) -> _Session:
        """Try token auth (JWT or similar).

        :raises AuthenticationFailed:
        """
        user = await self._tokens.auth(token)
        if not user:
            raise NotAuthorized('Invalid credentials')
        session = self._sessions.get_new_session({})
        self._update_session(session, user, AuthType.TOKEN)
        self.logger.info('login completed', auth_type=AuthType.TOKEN.value, user_id=user['id'])
        return session

    @staticmethod
    def _parse_auth_str(auth_str: str) -> Tuple[str, str]:
        """Parse a basic auth string (both b64 and not b64 encoded)."""
        if ':' not in auth_str:
            try:
                auth_str = b64decode(auth_str).decode('utf-8')
            except (B64Error, UnicodeDecodeError):
                raise NotAuthorized('Invalid credentials')
            if ':' not in auth_str:
                raise NotAuthorized('Invalid credentials')
        login, password = auth_str.split(':')
        return login, password

    @staticmethod
    def _update_session(session: Session, user: TokenInterface.TokenClaims, auth_type: AuthType) -> None:
        """Store user data in a provided session."""
        if session and user:
            session.user_id = user['id']
            session.permissions = user['permissions']
            session._changed = True
            session._stored = auth_type == AuthType.PASSWORD


class LoginService(ContextableService, PublicInterface):
    """User login service."""

    service_name = 'auth'

    def __init__(
        self,
        *args,
        session_service: SessionInterface = None,
        auth_service: AuthenticationInterface = None,
        token_service: TokenInterface = None,
        user_service: UserInterface = None,
        **kws,
    ):
        super().__init__(*args, **kws)
        self._sessions = session_service
        self._auth = auth_service
        self._users = user_service
        self._tokens = token_service

    @property
    def routes(self) -> dict:
        return {
            'login': self.login,
            'jwt.get': self.get_token,
            'jwt.refresh': self.refresh_token,
            'logout': self.logout,
            'register': self.register,
            'change_password': self.change_password,
            'update_profile': self.update_profile,
            'user_info': self.user_info,
        }

    @property
    def permissions(self) -> dict:
        return {
            'login': self.PermissionKeys.GLOBAL_GUEST_PERMISSION,
            'register': self.PermissionKeys.GLOBAL_GUEST_PERMISSION,
            'change_password': self.PermissionKeys.GLOBAL_GUEST_PERMISSION,
            'logout': self.PermissionKeys.GLOBAL_USER_PERMISSION,
            'jwt.get': self.PermissionKeys.GLOBAL_GUEST_PERMISSION,
            'update_profile': self.PermissionKeys.GLOBAL_USER_PERMISSION,
            'user_info': self.PermissionKeys.GLOBAL_USER_PERMISSION,
        }

    async def init(self):
        self._sessions = self.discover_service(self._sessions, cls=SessionInterface)
        self._auth = self.discover_service(self._auth, cls=AuthenticationInterface)
        self._tokens = self.discover_service(self._tokens, cls=TokenInterface, required=False)
        self._users = self.discover_service(self._users, cls=UserInterface)

    async def register(self, username: str, email: str, password: str) -> _Session:
        await self._users.register(username=username, email=email, password=password)
        return await self.login(username=username, password=password)

    async def change_password(self, username: str, password: str, new_password: str) -> _Session:
        await self._users.change_password(username=username, password=password, new_password=new_password)
        return await self.login(username=username, password=new_password)

    async def update_profile(self, settings: dict):
        return await self._users.update_profile(self.get_user_id(), settings)

    async def user_info(self):
        user_id = self.get_user_id()
        if user_id:
            return await self._users.get_user_and_permissions(user_id)

    async def login(self, username: str, password: str) -> _Session:
        """Authenticate a user by directly providing a login / password."""
        await self.logout()
        session = self._sessions.get_new_session({})
        session = await self._auth.password_auth(session, username, password)
        self.app.request_session.set(session)
        self.logger.info('login', auth_type=AuthType.PASSWORD.value, user_id=session.user_id)
        return session

    async def logout(self) -> None:
        ctx = self.get_request_context()
        if not ctx:
            raise NotImplementedError('Not implemented for non-context calls.')
        session = self.get_session()
        if session:
            session = cast(Session, session)
            if session.loaded:
                await self._sessions.delete_session(session)
            self.logger.info('logout', user_id=session.user_id)
            new_session = self._sessions.get_new_session({}, user_agent=session.h_agent)
            ctx['session_id'] = new_session.id
            self.app.request_session.set(new_session)

    async def get_token(self, username: str, password: str) -> TokenInterface.TokenInfo:
        """Authenticate and get a new token pair."""
        if not self._tokens:
            raise NotAuthorized('Unsupported auth method')
        session = await self._auth.password_auth(
            self._sessions.get_new_session({}), username=username, password=password
        )
        self.app.request_session.set(None)
        return await self._tokens.get(TokenInterface.TokenClaims(permissions=session.permissions, id=session.user_id))

    async def refresh_token(self, access: str, refresh: str) -> TokenInterface.TokenInfo:  # noqa: future use
        """Refresh token pair."""
        if not self._tokens:
            raise NotAuthorized('Unsupported auth method')
        token_info = await self._tokens.refresh(refresh)
        if not token_info:
            raise NotAuthorized('Invalid credentials')
        return token_info


class TokenClientService(ContextableService, TokenLoginInterface, abc.ABC):
    """Token client."""

    def __init__(self, *args, rpc_client: RPCClient, scheduler: Scheduler = None, username: str, password: str, **kws):
        super().__init__(*args, **kws)
        self._client = rpc_client
        self._username = username
        self._password = password
        self._scheduler = scheduler
        self._access_token = None
        self._refresh_token = None
        self._refresh_task = None

    async def init(self):
        self._client = self.discover_service(self._client, cls=RPCClient)
        self._scheduler = self.discover_service(self._scheduler, cls=Scheduler)
        await self._load_token()

    async def close(self):
        self._refresh_task.enabled = False

    def get_token(self) -> Optional[str]:
        return self._access_token

    async def _load_token(self) -> None:
        tokens = await self._client.call('auth.jwt.get', {'username': self._username, 'password': self._password})
        self._access_token = tokens['access']
        self._refresh_token = tokens['refresh']
        exp = self._get_exp_time(self._access_token)
        interval = (exp - time()) / 2
        self._refresh_task = self._scheduler.schedule_task(
            self._refresher_token, interval=interval, name=f'{self.service_name}._refresher_token'
        )

    async def _refresher_token(self) -> None:
        tokens = await self._client.call(
            'auth.jwt.refresh', {'access': self._access_token, 'refresh': self._refresh_token}
        )
        self._access_token = tokens['access']
        self._refresh_token = tokens['refresh']
        exp = self._get_exp_time(self._access_token)
        interval = (exp - time()) / 2
        self._refresh_task.interval = interval

    @abc.abstractmethod
    def _get_exp_time(self, token: str) -> int:
        """Return token expiration time in unix time."""
