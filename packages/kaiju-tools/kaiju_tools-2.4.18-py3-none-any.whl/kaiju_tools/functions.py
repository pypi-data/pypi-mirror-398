"""Commonly used functions."""

import asyncio
import ctypes
import os
from asyncio import sleep
from binascii import b2a_hex
from collections.abc import Collection, Coroutine
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as ConcurrentTimeoutError
from functools import partial
from secrets import randbits
from typing import TypedDict
from uuid import UUID


__all__ = [
    "retry",
    "retry_",
    "RETRY_EXCEPTION_CLASSES",
    "terminate_thread",
    "async_run_in_thread",
    "async_",
    "RetryParams",
    "secure_uuid",
    "not_implemented",
    "timeout",
    "get_short_uid",
    "RetryException",
    "suppress_exception",
]


class RetryException(Exception):
    """Base class for retry catchable exception.

    You may inherit an exception from this class to tell the retry function that your exception should
    be catchable.
    """


RETRY_EXCEPTION_CLASSES = frozenset(
    [
        ConnectionError,
        TimeoutError,
        ConcurrentTimeoutError,
        asyncio.TimeoutError,
        asyncio.CancelledError,
        RetryException,
    ]
)  #: default catchable exception classes for :py:func:`~kaiju_tools.functions.retry`

SUPRESS_EXCEPTION_CLASSES = tuple(
    RETRY_EXCEPTION_CLASSES
)  #: default catchable exception classes for :py:func:`~kaiju_tools.functions.supress_exception`


def get_short_uid(n: int = 5) -> str:
    """Get a short uid string.

    :param n: unicode length
    :returns: an uid hex string, n x 2 length
    """
    return b2a_hex(os.urandom(n)).decode()


class RetryParams(TypedDict, total=False):
    """Parameters for the retry function."""

    exec_timeout: int
    retries: int
    retry_timeout: float
    multiplier: float
    max_retry_timeout: float
    exception_classes: Collection[str | Exception]


async def suppress_exception(
    coro: Coroutine,
    *,
    exception_classes: tuple[type[Exception], ...] = SUPRESS_EXCEPTION_CLASSES,
    exec_timeout: int = None,
    default=None,
    logger=None,
):
    """Suppress a coroutine exception and write a log.

    :param coro: called coroutine
    :param exception_classes: exception classes that the function will supress
    :param exec_timeout: optional execution timeout
    :param default: default value to return on suppressed exception
    :param logger: logger instance, otherwise print is used
    :return: coroutine result or default

    How to use it:

    .. code-block:: python

        async def get_from_cache(key) -> Any:
            ...

        cached = await supress_exception(get_from_cache('123'))  # will return value or None

    """
    try:
        if exec_timeout:
            async with timeout(exec_timeout):
                return await coro
        else:
            return await coro
    except Exception as exc:
        if isinstance(exc, exception_classes):
            if logger:
                logger.error(str(exc), exc_info=exc)
            else:
                print(exc)
        return default


async def retry(
    func,
    args: tuple = None,
    kws: dict = None,
    *,
    exec_timeout: int = None,
    retries: int = 1,
    retry_timeout: float = 0.5,
    multiplier: float = 0.1,
    max_retry_timeout: float = 10.0,
    exception_classes: Collection[type[Exception]] = RETRY_EXCEPTION_CLASSES,
    logger=None,
):
    """Repeat an asynchronous operation if a specific exception occurs.

    :param func: async callable
    :param args: function arguments
    :param kws: function keyword arguments
    :param exec_timeout: exec timeout (None for no timeout) for each function call
    :param retries: max number of retries, 0 for infinite retries
    :param retry_timeout: time between consequent tries
    :param max_retry_timeout: max time between consequent tries
    :param multiplier: retry_timeout multiplier for each try, the formula:
    :param exception_classes: exception classes that the retry function should catch and retry
    :param logger: you may pass a logger object to log tries
    :returns: function result
    :raises StopIteration: if max number of retries reached and no exception was stored (rare)

    A formula for wait time is sophisticated with increased wait time at each iteration to prevent spamming.

    .. code-block:: python

        wait_time = min(max_retry_timeout, retry_timeout * (1 + multiplier)**n)

    By default, it will catch and retry timeout errors, cancelled asyncio tasks and all errors subclassed from
    :py:class:`~kaiju_tools.functions.RetryException`.

    How to use the retry function:

    .. code-block:: python

        async def call_something_async(a, b, c):
            ...

        await retry(call_something_async, (1, 2, 3), retries=10)

    """
    exc = None
    modifier = 1.0 + multiplier
    if args is None:
        args = tuple()
    if kws is None:
        kws = {}
    if retries <= 0:
        retries = float("Inf")

    while retries:
        try:
            if exec_timeout:
                async with timeout(exec_timeout):
                    result = await func(*args, **kws)
            else:
                result = await func(*args, **kws)
        except Exception as err:
            if err.__class__ in exception_classes:
                if logger:
                    logger.info("Retrying: %s", err)
                exc = err
                await sleep(retry_timeout)
                retry_timeout = min(max_retry_timeout, retry_timeout * modifier)
                retries -= 1
                continue
            raise

        return result

    if exc:
        raise exc

    raise StopIteration


def retry_(**retry_params):
    """Wrap a function in a retry function (decorator).

    :param retry_params: args for :py:func:`~kaiju_tools.functions.retry`

    Usage:

    .. code-block:: python

        @retry_(retries=1)
        async def call_something_async(a, b, c):
            ...

    """

    def wrapper(func):
        def retry_func(*args, **kws):
            return retry(func, args=args, kws=kws, **retry_params)

        return retry_func

    return wrapper


async def async_run_in_thread(f, args: tuple = None, kws: dict = None, max_timeout: float = None):
    """Run a synchronous function in a separate thread as an async function.

    :param f: callable object
    :param args: function arguments
    :param kws: function keyword arguments
    :param max_timeout: max execution time in seconds (None for no limit)
    :return: function result
    :raises ConcurrentTimeoutError: on execution timeout
    """
    loop = asyncio.get_event_loop()
    if args is None:
        args = tuple()
    if kws is None:
        kws = {}
    f = partial(f, *args, **kws)

    with ThreadPoolExecutor(max_workers=1) as tp:
        future = loop.run_in_executor(tp, f, *tuple())
        try:
            if max_timeout:
                async with timeout(max_timeout):
                    result = await future
            else:
                result = await future
        except ConcurrentTimeoutError:
            tp.shutdown(wait=False)
            for t in tp._threads:  # noqa # pylint: disable=all
                terminate_thread(t)  # noqa: reasonable
            raise
        else:
            return result


def async_(__f):
    """Wrap a synchronous function in an async thread (decorator)."""

    def _wrapper(*args, **kws):
        return async_run_in_thread(__f, *args, **kws)

    return _wrapper


def terminate_thread(__thread):
    """Terminate a python thread from another thread.

    Found it on stack overflow as an only real way to stop a stuck python thread.
    https://code.activestate.com/recipes/496960-thread2-killable-threads/
    Use with caution.
    """
    if not __thread.isAlive():
        return

    exc = ctypes.py_object(SystemExit)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(__thread.ident), exc)
    if res == 0:
        raise ValueError("Nonexistent thread id.")
    if res > 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(__thread.ident, None)
        raise SystemError("PyThreadState_SetAsyncExc failed.")


def secure_uuid() -> UUID:
    """Get a secure version of random UUID."""
    return UUID(int=randbits(128))


def not_implemented(message: str = None, /):
    """Decorate a not implemented method or function so it raises `NotImplementedError` when called.

    :param message: optional message for `NotImplementedError`

    Usage:

    .. code-block:: python

        @not_implemented('This method is disabled.')
        async def call_something(self):
            ...

    """

    def __params(_):
        def _wrap(*_, **__):
            raise NotImplementedError(message if message else "Not implemented.")

        return _wrap

    return __params


class _Timeout:
    __slots__ = ("_timeout", "_loop", "_task", "_handler")

    def __init__(self, _timeout: float, loop=None):
        self._timeout = max(0.0, _timeout)
        self._loop = loop
        self._handler = None

    async def __aenter__(self):
        if self._loop is None:
            loop = asyncio.get_running_loop()
        else:
            loop = self._loop
        task = asyncio.current_task()
        self._handler = loop.call_at(loop.time() + self._timeout, self._cancel_task, task)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is asyncio.CancelledError:
            raise TimeoutError
        if self._handler:
            self._handler.cancel()

    @staticmethod
    def _cancel_task(task: asyncio.Task):
        task.cancel()


def timeout(t: float, /):
    """Run asynchronous tasks with a timeout.

    :param t: timeout in seconds

    It creates an async context block, so async calls inside this block must finish before the specified time.

    .. code-block:: python

        async with timeout(1000):
            await do_something_asynchronous()

    """
    return _Timeout(t)
