from kaiju_tools.app import *  # noqa: legacy
from kaiju_tools.http import HTTPService, RPCClientService
from kaiju_tools.rpc import AbstractRPCCompatible, JSONRPCServer  # noqa: legacy
from kaiju_tools.sessions import AuthenticationService, LoginService, SessionService


SERVICE_CLASS_REGISTRY.register(LoggingService)
SERVICE_CLASS_REGISTRY.register(Scheduler)
SERVICE_CLASS_REGISTRY.register(SessionService)
SERVICE_CLASS_REGISTRY.register(LoginService)
SERVICE_CLASS_REGISTRY.register(AuthenticationService)
SERVICE_CLASS_REGISTRY.register(JSONRPCServer)
SERVICE_CLASS_REGISTRY.register(HTTPService)
SERVICE_CLASS_REGISTRY.register(RPCClientService)
