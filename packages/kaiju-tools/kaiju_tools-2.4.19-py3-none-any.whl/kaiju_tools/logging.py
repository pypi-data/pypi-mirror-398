"""Logging handlers, formatters and interfaces."""

import abc
import inspect
import logging.handlers
import queue
import sys
from contextvars import ContextVar  # noqa: pycharm
from logging import DEBUG, ERROR, INFO, WARNING
from time import sleep
from typing import TypedDict, cast

from kaiju_tools.context_vars import REQUEST_CONTEXT
from kaiju_tools.encoding import ENCODERS, MimeType
from kaiju_tools.exceptions import APIException, InternalError
from kaiju_tools.interfaces import App
from kaiju_tools.registry import ClassRegistry


__all__ = [
    'LogTrace',
    'LogException',
    'LogExceptionTrace',
    'LogMessage',
    'TextFormatter',
    'DataFormatter',
    'Logger',
    'StreamHandler',
    'JSONHandler',
    'TextHandler',
    'FormatterInterface',
    'HandlerInterface',
    'Formatters',
    'Handlers',
    'FORMATTERS',
    'HANDLERS',
]


class LogTrace(TypedDict):
    """Log trace data."""

    path: str  #: full module path
    func: str  #: function name
    module: str  #: module name
    lineno: int  #: log record line number


class LogExceptionTrace(TypedDict):
    """Log exception trace and debug info."""

    stack: str  #: stack trace
    locals: dict  #: local variables
    lineno: int  #: exception line number


class LogException(TypedDict):
    """Log exc_info data."""

    cls: str  #: exception class name
    cls_full: str  #: full class name i.e. __qualname__
    message: str  #: exception message
    trace: LogExceptionTrace | None  #: stack trace data


class LogMessage(TypedDict):
    """Log message data."""

    timestamp: float  #: UNIX timestamp
    name: str  #: logger name
    level: str  #: log level
    message: str  #: log text message
    ctx: dict  #: context information (service variables, session data etc)
    data: dict  #: log message extras
    trace: LogTrace  #: log record trace information
    error: LogException | None  #: exc_info data


class _LogRecord(logging.LogRecord):
    _cid = None
    _sid = None
    _ctx = None
    _data = None

    def __init__(self, *args, **kws):
        super().__init__(*args, **kws)
        for key in ('_data', '_cid', '_sid'):
            if key not in self.__dict__:
                setattr(self, key, None)

    @staticmethod
    def get_log_record(*args, **kws) -> '_LogRecord':
        """Get log record object."""
        return _LogRecord(*args, **kws)


class Logger(logging.Logger):
    """Main logger class."""

    def info(self, msg, /, *args, **kws) -> None:
        """INFO log."""
        if self.isEnabledFor(INFO):
            self._log(INFO, msg, args, **kws)

    def debug(self, msg, /, *args, **kws) -> None:
        """DEBUG log."""
        if self.isEnabledFor(DEBUG):
            self._log(DEBUG, msg, args, **kws)

    def error(self, msg, /, *args, **kws) -> None:
        """ERROR log."""
        if self.isEnabledFor(ERROR):
            self._log(ERROR, msg, args, **kws)

    def warning(self, msg, /, *args, **kws) -> None:
        """WARNING log."""
        if self.isEnabledFor(WARNING):
            self._log(WARNING, msg, args, **kws)

    def _log(
        self,
        level,
        msg,
        args,
        exc_info=None,
        extra=None,
        stack_info=False,
        stacklevel=1,
        **kws,
    ):
        if extra is None:
            extra = {}
        ctx = REQUEST_CONTEXT.get()
        if ctx:
            extra.update({'_cid': ctx['correlation_id'], '_sid': ctx['session_id'], '_ctx': ctx['data']})
        extra['_data'] = kws
        super()._log(  # noqa: reasonable
            level=level,
            msg=msg,
            args=args,
            exc_info=exc_info,
            extra=extra,
            stack_info=stack_info,
            stacklevel=stacklevel,
        )

    def makeRecord(self, name, level, fn, lno, msg, args, exc_info, func=None, extra=None, sinfo=None):  # noqa
        """A factory method which can be overridden in subclasses to create specialized LogRecords."""
        rv = _LogRecord(name, level, fn, lno, msg, args, exc_info, func, sinfo)  # noqa
        if extra is not None:
            for key in extra:
                rv.__dict__[key] = extra[key]
        return rv


logging.setLoggerClass(Logger)
logging.setLogRecordFactory(_LogRecord.get_log_record)


class FormatterInterface(logging.Formatter, abc.ABC):
    """Formatter base class."""


class TextFormatter(FormatterInterface):
    """Formatter for human-readable text."""

    default_date_fmt = '%H:%M:%S'
    default_log_fmt = '%(asctime)s | %(levelname)5s | %(_cid)s | %(name)s | %(message)s | %(_data)s'

    def __init__(self, *args, datefmt: str = default_date_fmt, fmt: str = default_log_fmt, **kws):
        """Initialize.

        :param output_data: output log extra data
        :param output_context: output log adapter context data
        :param datefmt: log date format
        :param fmt: log format
        :param limit_var: limit variables in log in symbols
        :param args: see `logging.Formatter.__init__`
        :param kws: see `logging.Formatter.__init__`
        """
        super().__init__(*args, fmt=fmt, datefmt=datefmt, **kws)


class DataFormatter(TextFormatter):
    """Colored formatter is used to pretty-print colored text in CLI.

    Text color depends on log level.
    """

    def __init__(
        self,
        *args,
        debug: bool = False,
        encoder: str = MimeType.json.value,
        encoders=ENCODERS,
        **kws,
    ):
        """Initialize.

        :param debug: output debug information about exceptions
        :param encoder: data encoding format or encoder object itself or None for no additional encoding
        :param encoders: optional encoder classes registry
        :param args: see :py:class:`~kaiju_base.logging.TextFormatter`
        :param kws: see :py:class:`~kaiju_base.logging.TextFormatter`
        """
        super().__init__(*args, **kws)
        self._dumps, _ = encoders[encoder]
        self._debug = debug

    def format(self, record):
        """Format log record."""
        return self._dumps(self.create_message(record))  # noqa

    def formatMessage(self, record) -> str:
        """Format log message."""
        pass

    def formatException(self, ei):
        """Format exception (skip it)."""
        pass

    def create_message(self, record: _LogRecord) -> LogMessage:
        """Create log message dict from a log record."""
        msg = {
            't': record.created,
            'name': record.name,
            'lvl': record.levelname,
            'msg': record.getMessage(),
            'cid': record._cid,
            'sid': record._sid,
            'data': record._data,
            'ctx': record._ctx,
        }
        if record.exc_info:
            error_cls, error, stack = record.exc_info
            if not isinstance(error, APIException):
                error = InternalError(message=str(error), base_exc=error)
            error.debug = self._debug
            error.debug = True  # a little hack to enable trace info (probably there's a better way)
            if 'data' not in msg:
                msg['data'] = {}
            msg['data']['error'] = error.repr()
            error.debug = False
            if stack and stack.tb_next:
                msg['data']['error']['trace'] = {
                    'file': inspect.getabsfile(stack.tb_next),
                    'lineno': stack.tb_next.tb_lineno,
                }
        return msg  # noqa


class HandlerInterface(logging.Handler, abc.ABC):
    """Base log handler interface."""

    app: App


class StreamHandler(logging.StreamHandler, HandlerInterface):
    """Modified stream handler with `sys.stdout` by default."""

    stream_types = {'stdout': sys.stdout, 'stderr': sys.stderr}  #: available stream types

    def __init__(self, app=None, bytestream: bool = True, stream: str = None):
        """Initialize.

        If stream is not specified, `sys.stdout` is used.

        :param app: web app
        :param stream: optional stream type
        """
        if stream is None:
            stream = sys.stdout
        elif isinstance(stream, str):
            stream = self.stream_types[stream]
        if bytestream:
            self.terminator: bytes = self.terminator.encode('utf-8')
            stream = stream.buffer
        super().__init__(stream=stream)
        self.app = app


class QueueListener(logging.handlers.QueueListener):
    """Queued log listener with buffering.

    Used by the log handlers to store log records.
    """

    def _monitor(self):
        """Monitor the queue for records, and ask the handler to deal with them."""
        q = self.queue
        handler = cast(StreamHandler, self.handlers[0])
        fmt = handler.format
        stream = handler.stream
        term = handler.terminator
        while True:
            record = fmt(q.get(True))
            q.task_done()
            n = q.qsize()
            if n:
                records = term.join(fmt(q.get_nowait()) for _ in range(n))  # noqa
                for _ in range(n):
                    q.task_done()
                stream.write(record + term + records + term)  # noqa
            else:
                stream.write(record + term)  # noqa
            stream.flush()
            sleep(0)


class TextHandler(logging.handlers.QueueHandler, HandlerInterface):
    """Human-readable text log queue handler."""

    bytestream = False
    formatter_cls = TextFormatter

    def __init__(self, app=None, formatter: dict = None, stream: str = None):
        """Initialize.

        :param app: web app
        :param formatter: formatter class settings
        :param stream: optional stream type 'stdout' or 'stderr'
        """
        q = queue.Queue(-1)
        super().__init__(q)
        self._stream = StreamHandler(app=app, bytestream=self.bytestream, stream=stream)
        self._listener = QueueListener(q, self._stream)
        if formatter is None:
            formatter = {}
        self._stream.setFormatter(self.formatter_cls(**formatter))
        self.app = app
        self._listener.start()

    def setFormatter(self, fmt) -> None:
        self._stream.setFormatter(fmt)

    def prepare(self, record):
        # Ignoring all possible log handler conflicts for now.
        return record


class JSONHandler(TextHandler):
    """JSON log queue handler (better performance)."""

    bytestream = True
    formatter_cls = DataFormatter


class Formatters(ClassRegistry[str, type[FormatterInterface]]):
    """Log formatter classes registry."""

    @classmethod
    def get_base_classes(cls) -> tuple[type, ...]:
        return (FormatterInterface,)


class Handlers(ClassRegistry[str, type[HandlerInterface]]):
    """Log handler classes registry."""

    @classmethod
    def get_base_classes(cls) -> tuple[type, ...]:
        return (HandlerInterface,)


FORMATTERS = Formatters()
"""Registry of log formatter classes (see :py:class:`~kaiju_tools.registry.ClassRegistry` for available methods)."""

HANDLERS = Handlers()
"""Registry of log handlers classes (see :py:class:`~kaiju_tools.registry.ClassRegistry` for available methods)."""

FORMATTERS.register_from_namespace(locals())
HANDLERS.register(TextHandler)
HANDLERS.register(JSONHandler)
