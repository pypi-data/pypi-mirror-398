"""API exceptions."""

from aiohttp.client import ClientResponseError
from fastjsonschema import JsonSchemaValueException

from kaiju_tools.encoding import Serializable
from kaiju_tools.registry import ClassRegistry


__all__ = [
    'APIException',
    'InternalError',
    'ClientError',
    'ValidationError',
    'NotFound',
    'MethodNotFound',
    'InvalidParams',
    'InvalidRequest',
    'RequestTimeout',
    'Aborted',
    'MethodNotAllowed',
    'Conflict',
    'JSONParseError',
    'PermissionDenied',
    'NotAuthorized',
    'InvalidLicense',
    'HTTPRequestError',
    'JSONRPCError',
    'ErrorRegistry',
    'ERROR_CLASSES',
]


class APIException(Serializable, Exception):
    """Base exception.

    You should use this class as a base when creating an exception which is meant to propagated across services, since
    this class is serializable.
    """

    __slots__ = ('message', 'status', 'data', 'id', 'debug', 'base_exc')

    status_code = 500
    """RPC error status code."""

    def __init__(
        self,
        message: str = '',
        *,
        id: int | None = None,
        base_exc: Exception = None,
        debug: bool = False,
        data: dict = None,
        **extras,
    ):
        """Initialize.

        :param message: error messages
        :param id: request id
        :param base_exc: base exception object (when used as a wrapper)
        :param debug: debug mode error
        :param data: additional data
        :param extras: will be merged with `data`
        """
        self.id = id
        self.message = message
        self.base_exc = base_exc
        self.data = data if data else {}
        self.data.update(extras)
        self.debug = debug

    def __str__(self):
        """Get error message."""
        return self.message

    def repr(self) -> dict:
        """Serialize."""
        data = {
            'code': self.status_code,
            'message': self.message,
            'data': dict(self.data),
        }
        data['data'].update({'type': self.__class__.__name__, 'base_type': self.__class__.__base__.__name__})
        if self.debug and self.base_exc:
            data['data'].update(
                {
                    'base_exc_type': self.base_exc.__class__.__name__,
                    'base_exc_data': getattr(self.base_exc, 'extras', {}),
                    'base_exc_message': str(self.base_exc),
                }
            )
        data['data'].update(self.data)
        return data


class ClientError(APIException):
    """Any kind of error happened because of a client's actions."""

    status_code = 400


class JSONParseError(ClientError, ValueError):
    """Wrongly formatted JSON data."""

    status_code = -32700


class JSONRPCError(ClientError):
    """Common JSONRPC error."""


class InvalidRequest(JSONRPCError):
    """Invalid RPC request format."""

    status_code = -32600


MethodNotAllowed = InvalidRequest  # compatibility


class MethodNotFound(JSONRPCError):
    """RPC method does not exist or not available for this type of user."""

    status_code = -32601


class InvalidParams(JSONRPCError):
    """JSONSchema validation error."""

    status_code = -32602

    def repr(self) -> dict:
        """Serialize."""
        data = super().repr()
        if self.base_exc and isinstance(self.base_exc, JsonSchemaValueException):
            data['data'].update(
                {
                    'name': '.'.join(('params', *self.base_exc.path[1:])),
                    'definition': self.base_exc.definition,
                    'rule': self.base_exc.rule,
                    'rule_definition': self.base_exc.rule_definition,
                    'value': self.base_exc.value,
                }
            )
        return data


ValidationError = InvalidParams  # compatibility


class RequestTimeout(ClientError):
    """Request reached its timeout."""

    status_code = -32002


class Aborted(ClientError):
    """Aborted by the server due to timeout or other conditions."""

    status_code = -32001


class InternalError(APIException):
    """Any internal error happened on the server and not caused by a client."""

    status_code = -32603


class HTTPRequestError(InternalError):
    """HTTP response error."""

    status_code = -32603

    def repr(self) -> dict:
        """Serialize."""
        data = super().repr()
        if self.debug and self.base_exc and isinstance(self.base_exc, ClientResponseError):
            data['data'].update(
                {
                    'status': self.base_exc.status,
                    'method': str(self.base_exc.request_info.method),
                    'url': str(self.base_exc.request_info.url),
                    'params': getattr(self.base_exc, 'params', None),
                    'took_ms': getattr(self.base_exc, 'took_ms', None),
                    'request': getattr(self.base_exc, 'request', None),
                    'response': getattr(self.base_exc, 'response', None),
                }
            )
        return data


class NotAuthorized(ClientError):
    """Authorization required."""

    status_code = -32000


PermissionDenied = MethodNotFound  # compatibility


class NotFound(ClientError):
    """Requested object or resource doesn't exist."""

    status_code = 404


class Conflict(ClientError):
    """New object/data is in conflict with existing."""

    status_code = 409


class FailedDependency(APIException):
    """Something."""

    status_code = 424


class InvalidLicense(ClientError):
    """Invalid license exception."""

    status_code = 451


class ErrorRegistry(ClassRegistry):
    """Error classes."""

    @classmethod
    def get_base_classes(cls) -> tuple[type, ...]:
        return (APIException,)


ERROR_CLASSES = ErrorRegistry()
"""Global registry of error classes, see :py:class:`~kaiju_tools.registry.ClassRegistry`."""

ERROR_CLASSES.register_from_namespace(locals())
