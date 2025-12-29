from contextvars import ContextVar  # noqa: pycharm
from typing import Optional

from kaiju_tools.types import RequestContext, Session


__all__ = ['REQUEST_CONTEXT', 'REQUEST_SESSION']

REQUEST_CONTEXT: ContextVar[Optional[RequestContext]] = ContextVar('RequestContext', default=None)
REQUEST_SESSION: ContextVar[Optional[Session]] = ContextVar('RequestSession', default=None)
