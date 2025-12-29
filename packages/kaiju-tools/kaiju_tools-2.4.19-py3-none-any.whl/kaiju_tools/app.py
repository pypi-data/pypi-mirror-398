"""Application essential services and loaders."""

import abc
import asyncio
import errno
import importlib
import logging
import os
import pathlib
import uuid
from argparse import ArgumentParser
from ast import literal_eval
from collections.abc import Awaitable, Callable, Collection, Iterable
from contextvars import ContextVar  # noqa: pycharm
from enum import Enum
from time import time
from typing import NewType, TypedDict, TypeVar, Union, cast, final
from warnings import warn
from weakref import proxy

from aiohttp.web import Application, AppRunner, run_app

import kaiju_tools.jsonschema as js
from kaiju_tools.context_vars import *
from kaiju_tools.encoding import loads, yaml_loads
from kaiju_tools.functions import retry, timeout
from kaiju_tools.interfaces import App, PublicInterface, ServiceManagerInterface
from kaiju_tools.logging import HANDLERS, Logger
from kaiju_tools.mapping import recursive_update
from kaiju_tools.registry import ClassRegistry
from kaiju_tools.templates import Template
from kaiju_tools.types import Namespace, RequestContext, SortedStack


__all__ = [
    "Service",
    "ContextableService",
    "ServiceClassRegistry",
    "SERVICE_CLASS_REGISTRY",
    "ServiceConfigurationError",
    "ServiceNotAvailableError",
    "ServiceContextManager",
    "RequestContext",
    "run_command",
    "Commands",
    "COMMANDS",
    "BaseCommand",
    "LoggingService",
    "Scheduler",
    "ExecPolicy",
    "RequestContext",
    "ServiceConfig",
    "REQUEST_SESSION",
    "REQUEST_CONTEXT",
    "HandlerSettings",
    "LoggerSettings",
    "ConfigLoader",
    "get_cli_parser",
    "ConfigurationError",
    "Settings",
    "AppSettings",
    "RunSettings",
    "ProjectSettings",
    "MainSettings",
    "ServiceSettings",
    "init_app",
    "run_server",
    "ScheduledTask",
]


class ServiceConfig(TypedDict, total=False):
    """Service configuration parameters."""

    cls: str  #: service class name as in :py:class:`~kaiju_tools.services.service_class_registry`
    name: str  #: unique service name, each service should have a default value for this
    enabled: bool  #: disable service
    required: bool  #: skip a service and proceed on initialization error
    override: bool  #: replace an existing service with the same name
    settings: dict  #: custom settings, unpacked to a service's __init__


class ConfigurationError(KeyError):
    """Configuration key not found."""


class Settings(dict):
    """Settings object."""

    validator: js.Object = None

    def __init__(self, seq):
        """Initialize."""
        if self.validator:
            seq = js.compile_schema(self.validator)(seq)
        super().__init__(seq)

    def __getattr__(self, item):
        """Get a parameter from settings dict."""
        try:
            return self[item]
        except KeyError:
            raise ConfigurationError(f"No such config value: {item}")


class AppSettings(Settings):
    """Web application init settings."""

    validator = js.Object(
        {"debug": js.Boolean(default=False), "client_max_size": js.Integer(minimum=1024, default=1024**2)},
        additionalProperties=False,
        required=[],
    )


class RunSettings(Settings):
    """Server run settings."""

    validator = js.Object(
        {
            "host": js.Nullable(js.String(minLength=1, default=None)),
            "port": js.Nullable(js.Integer(minimum=1, maximum=65535, default=None)),
            "path": js.Nullable(js.String(minLength=1, default=None)),
            "shutdown_timeout": js.Integer(minimum=0, default=30),
            "keepalive_timeout": js.Integer(minimum=0, default=60),
        },
        additionalProperties=False,
        required=[],
    )


class MainSettings(Settings):
    """Main project settings."""

    validator = js.Object(
        {
            "name": js.String(minLength=1),
            "version": js.String(minLength=1),
            "env": js.String(minLength=1),
            "loglevel": js.Enumerated(enum=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO"),
        },
        additionalProperties=False,
        required=["name", "version", "env"],
    )


class ServiceSettings(Settings):
    """Service configuration."""

    validator = js.Object(
        {
            "cls": js.String(minLength=1),
            "name": js.String(minLength=1),
            "enabled": js.Boolean(default=True),
            "required": js.Boolean(default=True),
            "override": js.Boolean(default=False),
            "loglevel": js.JSONSchemaObject(enum=["DEBUG", "INFO", "WARNING", "ERROR", None], default=None),
            "settings": js.Object(),
        },
        additionalProperties=False,
        required=["cls"],
    )

    def __init__(self, seq):
        if type(seq) is str:
            seq = {"cls": seq}
        super().__init__(seq)


class ProjectSettings(Settings):
    """Validation schema for project settings."""

    def __init__(self, packages: list, app: dict, run: dict, main: dict, etc: dict, services: list):
        """Initialize.

        :param packages: list of kaiju library packages for automatic service classes import
        :param app: `Application <https://docs.aiohttp.org/en/stable/web_reference.html#aiohttp.web.Application>`_
            settings
        :param run: `run_app() <https://docs.aiohttp.org/en/stable/web_reference.html#aiohttp.web.run_app>`_
            settings
        :param main: project settings
        :param etc: metadata and additional settings
        :param services: list of service settings
        """
        super().__init__(
            dict(
                packages=tuple(packages),
                app=AppSettings(app),
                run=RunSettings(run),
                main=MainSettings(main),
                etc=Settings(etc),
                services=tuple(ServiceSettings(srv) for srv in services),
            )
        )


def get_cli_parser() -> ArgumentParser:
    """Parse application CLI args."""
    _parser = ArgumentParser(prog="aiohttp web application", description="web application run settings")
    _parser.add_argument("--host", dest="host", default=None, help="web app host (default - from settings)")
    _parser.add_argument("--port", dest="port", type=int, default=None, help="web app port (default - from settings)")
    _parser.add_argument(
        "--path", dest="path", default=None, metavar="FILE", help="socket path (default - from settings)"
    )
    _parser.add_argument(
        "--debug", dest="debug", action="store_true", default=None, help="run in debug mode (default - from settings)"
    )
    _parser.add_argument(
        "-c",
        "--config",
        dest="cfg",
        default=[],
        metavar="FILE",
        action="append",
        help="yaml config paths, use multiple times to merge multiple configs (default - settings/config.yml)",
    )
    _parser.add_argument(
        "-l",
        "--log",
        dest="loglevel",
        default=None,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="log level",
    )
    _parser.add_argument(
        "-f",
        "--env-file",
        dest="env_file",
        default=[],
        metavar="FILE",
        action="append",
        help="env file paths (default to ./settings/env.json + ./settings/env.local.json)",
    )
    _parser.add_argument(
        "-e",
        "--env",
        dest="env",
        default=[],
        metavar="KEY=VALUE",
        action="append",
        help="overrides env variable (may be used multiple times)",
    )
    _parser.add_argument(
        "--no-os-env", dest="no_os_env", action="store_true", default=False, help="do not use OS environment variables"
    )
    _parser.add_argument(
        "cmd", metavar="COMMAND", default=None, nargs="?", help="optional management command to execute"
    )
    return _parser


class ConfigLoader:
    """Config loader class. It is intended to be used before the app start."""

    CmdName = NewType("CmdName", str)
    config_class = ProjectSettings
    _file_loaders = {".json": loads, ".yml": yaml_loads, ".yaml": yaml_loads}

    def __init__(
        self,
        base_config_paths: Iterable[str] = tuple(),
        base_env_paths: Iterable[str] = tuple(),
        default_env_paths: Iterable[str] = tuple(),
    ):
        """Initialize.

        :param base_config_paths: list of base paths to .yml config files in sequential order
        :param base_env_paths: list of base paths to .env files in sequential order
        :param default_env_paths: list of paths to .env files which may be overriden by the `--env-file` flag
        """
        self.base_config_paths = base_config_paths
        self.base_env_paths = base_env_paths
        self.default_env_paths = default_env_paths
        self.logger = logging.getLogger("loader")

    def configure(self) -> (CmdName | None, ProjectSettings):
        """Load project config and command.

        Loading order:

        - ./settings/config.yml
        - .yml files, first to last
        - ./settings/env.json
        - .env files, first to last
        - os env vars (unless --no-os-env specified)
        - CLI env vars

        """
        parser = get_cli_parser()
        args = parser.parse_known_args()[0].__dict__
        config_paths = [*self.base_config_paths, *args.get("cfg", [])]
        _paths = args.get("env_file", [])
        if not _paths:
            _paths = self.default_env_paths
        env_paths = [*self.base_env_paths, *_paths]
        config = {"packages": [], "main": {}, "app": {}, "etc": {}, "services": []}
        env = {}
        for cfg_path in config_paths:
            _data = self._from_file(cfg_path)
            _packages = _data.pop("packages", [])
            if _packages:
                config["packages"].extend(_packages)
            _services = _data.pop("services", [])
            if _services:
                config["services"].extend(_services)
            config = recursive_update(config, _data)
        for env_path in env_paths:
            env.update(self._from_file(env_path))
        self._update_env_from_cli(env, args)
        config = Template(config)
        if not args["no_os_env"]:
            self._update_env_from_os(env, config.keys)
        config = config.fill(env)
        config = self.config_class(**config)
        self._update_config_from_cli(config, args)
        command = args.get("cmd")
        config = ProjectSettings(**config)
        return command, config

    def _from_file(self, path) -> dict:
        """Load data from a config file."""
        self.logger.info("Loading %s", path)
        path = pathlib.Path(path)
        if path.suffix not in self._file_loaders:
            raise ConfigurationError(f"Unknown config file format: {path}")
        loader = self._file_loaders[path.suffix]
        if not path.exists() or path.is_dir():
            warn("Config path does not exist or it's a directory." ' "%s" - not found!' % path)
            return {}
        with open(path, "rb") as f:
            data = loader(f.read())
        return data

    def _update_env_from_os(self, env: dict, keys: Collection[str]) -> None:
        """Get env arguments from OS env."""
        self.logger.debug("Loading OS")
        for key in keys:
            value = os.getenv(key)
            if value:
                self.logger.info("From OS: %s", key)
                env[key] = self._init_env_value(value)

    def _update_env_from_cli(self, env: dict, args: dict) -> None:
        """Update env map from CLI arguments."""
        self.logger.debug("Loading CLI")
        for record in args.get("env", []):
            k, v = record.split("=")
            if v:
                self.logger.info("From CLI: %s", k)
                env[k] = self._init_env_value(v)

    @staticmethod
    def _update_config_from_cli(config: ProjectSettings, args: dict):
        """Set CLI arguments."""
        for key in ("host", "port", "path"):
            value = args.get(key)
            if value is not None:
                config.run[key] = value
        debug = args.get("debug")
        if debug is not None:
            config.app["debug"] = debug
        log = args.get("loglevel")
        if log is not None:
            config.main["loglevel"] = log

    @staticmethod
    def _init_env_value(value: str):
        """Parse env arg from --env or unix environment."""
        if value is None:
            return None
        value = value.strip()
        if not value:
            return None
        _value = value.lower()
        if _value == "true":
            value = True
        elif _value == "false":
            value = False
        elif _value == "none":
            value = None
        else:
            try:
                value = literal_eval(value)
            except Exception:  # noqa: reasonable
                pass
        return value


class Service(abc.ABC):
    """Base service class."""

    service_name = None  #: you may define a custom service name here

    def __init__(self, app: App = None, logger=None):
        """Initialize.

        :param app: aiohttp web application
        :param logger: a logger instance (None - app logger)
        """
        self.app = app
        if logger is None:
            logger = logging.getLogger(self.app.name)
        self.logger: Logger = logger

    def discover_service(
        self,
        name: Union[str, "Service", False, None],
        cls: str | type | Iterable[str | type] = None,
        required=True,
    ):
        """Discover a service using specified name and/or service class.

        :param name: specify a service name or service instance (in latter case
            it will be returned as is)
            False means that nothing will be returned, i.e. service will be disabled
        :param cls: specify service class. If name wasn't specified, then the first
            service matching given class will be returned. If name and class
            both were specified, then the type check will be performed on a newly
            discovered service
        :param required: means that an exception will rise if service doesn't exist
            otherwise in this case None will be returned

        Discover by class:

        .. code-block:: python

            service = self.discover_service(None, cls=MyDependencyService)

        Discover by name:

        .. code-block:: python

            service = self.discover_service(service_name, cls=MyDependencyService)

        Discover if exists, otherwise return `None`:

        .. code-block:: python

            service = self.discover_service(None, cls=MyDependencyService, required=False)

        Skip discovery and return `None`. Use this to disable a dependency in a config file by settings a dependency
        name to `False`. Note that `required=False` is mandatory, otherwise a dependency error will be produced.

        .. code-block:: python

            service = self.discover_service(False, cls=MyDependencyService, required=False)

        """
        if name is False and not required:
            return
        elif isinstance(name, Service):
            return name
        else:
            return self.app.services.discover_service(name=name, cls=cls, required=required)


class ContextableService(Service):
    """A service which must be asynchronously initialized after it was created."""

    async def init(self):
        """Initialize asynchronous context of the service.

        This method is called automatically on start by the aiohttp cleanup context.
        """

    async def post_init(self):
        """Execute additional procedures. after all init methods of all services are called."""

    async def close(self):
        """Close asynchronous context of the service.

        This method is called automatically on exit by the aiohttp cleanup context.
        """

    @property
    def closed(self) -> bool:
        """The service async context is closed."""
        return False

    async def __aenter__(self):
        await self.init()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


Contextable = ContextableService


class ServiceConfigurationError(RuntimeError):
    """An error during services configuration or initialization."""


class ServiceNotAvailableError(ValueError):
    """Service with such name doesn't exist."""


class ServiceClassRegistry(ClassRegistry[str, type[Service]]):
    """Class registry for service classes.

    This registry is used by the app to produce services objects from a config file.
    """

    @classmethod
    def get_base_classes(cls) -> tuple[type, ...]:
        return (Service,)


SERVICE_CLASS_REGISTRY = ServiceClassRegistry(raise_if_exists=False)  #: default service class registry

_Service = TypeVar("_Service", bound=Service)


class ServiceContextManager(ContextableService, ServiceManagerInterface):
    """Services manager."""

    service_name = "srv"

    def __init__(
        self,
        app: App,
        settings: list[ServiceConfig | str],
        class_registry: ServiceClassRegistry = SERVICE_CLASS_REGISTRY,
        logger=None,
    ):
        """Initialize."""
        super().__init__(app=app, logger=logger)
        self._settings = settings
        self._registry = class_registry
        self._required = set()
        self._running_services = []
        self._services = {}

    async def init(self):
        for name, service in self._services.items():
            try:
                await self.start_service(name)
            except Exception as exc:
                self.logger.error("Service failed", service=name, exc_info=exc)
                if name in self._required:
                    await self.close()
                    raise
        for name, service in self._services.items():
            if isinstance(service, ContextableService):
                await service.post_init()

    async def close(self):
        for name in self._running_services[::-1]:
            await self.terminate_service(name)
        self._running_services.clear()

    def add_service(self, service: Service, required: bool = True, name: str = None) -> None:
        """Add a service directly to the service map.

        This method is supposed to be used in testing / debugging, not intended for production use.
        """
        name = self._get_service_name(type(service), name)
        service.service_name = name
        self._services[name] = service
        service.logger = self.app.logger.getChild(name)
        if required:
            self._required.add(service.service_name)

    async def start_service(self, name: str) -> None:
        """Start an idle service."""
        service = self._services[name]
        if name in self._running_services:
            return
        if isinstance(service, ContextableService):
            self.logger.debug("Starting service", service=service.service_name)
            await service.init()
            self._running_services.append(name)

    async def terminate_service(self, name: str) -> None:
        """Terminate a running service."""
        service = self._services[name]
        if name not in self._running_services:
            return
        if isinstance(service, ContextableService):
            self.logger.debug("Closing service", service=service.service_name)
            try:
                await service.close()
            except Exception as exc:
                self.logger.error("Service failed to close", service=name, exc_info=exc)
        self._running_services.remove(name)

    async def cleanup_context(self, _):
        """Get aiohttp cleanup context."""
        try:
            await self.init()
        except Exception as exc:
            # Handle new python/aiohttp not propagating errors in cleanup ctx
            raise RuntimeError("App initialization failed: see the trace above") from exc
        yield
        try:
            await self.close()
        except Exception as exc:
            self.logger.error("Cleanup failed", exc_info=exc)

    def __getattr__(self, item):
        return self._services[item]

    def __getitem__(self, item):
        return self._services[item]

    def __contains__(self, item):
        return item in self._services

    def items(self):
        return self._services.items()

    def discover_service(
        self,
        name: str | _Service | False = None,
        cls: type[_Service] = None,
        required: bool = True,
    ) -> _Service | None:
        """Discover a service using specified name and/or service class.

        :param name: specify a service name or service instance (in latter case
            it will be returned as is)
        :param cls: specify service class or a list of classes. If name wasn't specified,
            then the first service matching given class will be returned. If name and class
            both were specified, then the type check will be performed on a newly
            discovered service. If multiple classes are provided they will be checked in
            priority order one by one.
        :param required: means that an exception will rise if service doesn't exist
            otherwise in this case None will be returned
        """
        if isinstance(name, Service):
            return name

        if name:
            if name not in self._services:
                raise ServiceNotAvailableError(f'Service not found: "{name}".')
            service = self._services[name]
            if not isinstance(service, cls):
                raise ServiceNotAvailableError(f"Service class mismatch: {cls} vs {type(service)}.")
            return service

        service = next((service for service in self._services.values() if isinstance(service, cls)), None)
        if service:
            return service
        elif required:
            raise ServiceNotAvailableError(f"Service not found: {name}/{cls}.")

    @staticmethod
    def _get_service_name(service_cls: type, name: str | None) -> str:
        if not name:
            name = getattr(service_cls, "service_name", None)
        if name is None:
            name = service_cls.__name__
        return name

    def create_services(self) -> None:
        """Create all services from the loaded configuration."""
        for settings in self._settings:
            if type(settings) is str:
                settings = ServiceConfig(cls=settings)
            if not settings.get("enabled", True):
                continue
            cls = self._registry[settings["cls"]]
            name = self._get_service_name(cls, settings.get("name"))
            if name in self._services and not settings.get("override"):
                raise ServiceConfigurationError('Service with name "%s" already registered.' % name)
            _name = cls.service_name
            cls.service_name = name  # TODO: fix it
            service = cls(app=self.app, **settings.get("settings", {}), logger=self.app.logger.getChild(name))  # noqa
            cls.service_name = _name
            service.service_name = name
            self._services[name] = service
            if settings.get("required", True):
                self._required.add(name)
            loglevel = settings.get("loglevel")
            if loglevel:
                service.logger.setLevel(loglevel)


_Callable = Callable[..., Awaitable]


@final
class ExecPolicy(Enum):
    """Task policy for a scheduled task.

    This policy takes place when the scheduler must activate the task, but the previous task call
    is still going.
    """

    WAIT = "WAIT"  #: wait until the previous call has finished
    CANCEL = "CANCEL"  #: cancel the previous call immediately and restart the task


@final
class ScheduledTask:
    """Scheduled local task."""

    class _TaskDisableCtx:
        def __init__(self, task):
            self._task = proxy(task)

        def __enter__(self):
            self._task.enabled = False

        def __exit__(self, exc_type, exc_val, exc_tb):
            self._task.enabled = True

    __slots__ = (
        "_scheduler",
        "name",
        "method",
        "params",
        "interval",
        "policy",
        "called_at",
        "_enabled",
        "executed",
        "retries",
        "max_timeout",
        "__weakref__",
    )

    def __init__(
        self,
        scheduler: "Scheduler",
        name: str,
        method: Callable,
        params: dict | None,
        interval: float,
        policy: ExecPolicy,
        max_timeout: float,
        retries: int,
    ):
        """Initialize."""
        self._scheduler = proxy(scheduler)
        self.name = name
        self.method = method
        self.params = params
        self.interval = interval
        self.max_timeout = max_timeout
        self.policy = policy
        self.called_at = 0
        self.retries = retries
        self._enabled = True
        self.executed: asyncio.Task | None = None

    @property
    def enabled(self) -> bool:
        """Task is enabled for execution."""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Enable or disable task."""
        self._enabled = value
        if value is True:
            t_ex = self.called_at + self.interval
            self._scheduler._stack.insert(t_ex, self)  # noqa

    def disable(self) -> _TaskDisableCtx:
        """Get a task disable context."""
        return self._TaskDisableCtx(self)


class Scheduler(ContextableService, PublicInterface):
    """Schedule and execute local functions.

    It can be used to set up periodic execution of local service methods at specific intervals. The best way to do it
    is to discover the scheduler in your service `init()` and create a task using
    :py:meth:`~kaiju_tools.app.Scheduler.schedule_task` method.

    .. code-block:: python

        from kaiju_tools import Scheduler, ContextableService

        class CacheService(ContextableService):

            async def reload_cache(self):
                ...

            async def init(self):
                scheduler = self.discover_service(None, cls=Scheduler)
                self._task_reload = scheduler.schedule_task(self.reload_cache, 60, name='CacheService.reload')

    It's a good idea to disable the task on service exit by setting `enabled=False`.
    A disabled task will not be re-scheduled until enabled.

    .. code-block:: python

            async def close(self):
                self._task_reload.enabled = False

    You can also temporarily disable your task using the task disable context. The task will be automatically enabled
    on context exit.

    .. code-block:: python

        async def rebuild_database(self):
            with self._task_reload.disable():
                ...

    You can manage how the task is handled if the previous execution hasn't finished on time.
    By default, a not finished task will be cancelled and rescheduled.
    Change it to :py:attr:`~kaiju_tools.app.ExecPolicy.WAIT` to wait for a previous call to finish instead.

    .. code-block:: python

        self._task_reload = scheduler.schedule_task(self.reload_cache, 60, policy=ExecPolicy.WAIT)

    You can set a retry policy to handle timeouts or connection errors by setting the maximum number of retries.
    The scheduler uses :py:func:`~kaiju_tools.func.retry` function to handle retries.

    .. code-block:: python

        self._task_reload = scheduler.schedule_task(self.reload_cache, 60, retries=5)

    """

    ExecPolicy = ExecPolicy
    WAIT_TASK_TIMEOUT_SAFE_MOD = 4.0
    MIN_REFRESH_RATE = 0.1
    ON_EXIT_TIMEOUT_S = 5.0

    def __init__(self, *args, refresh_rate: float = 1.0, **kws):
        """Initialize.

        :param refresh_rate: base refresh rate
        """
        super().__init__(*args, **kws)
        self.refresh_rate = refresh_rate
        self._stack = SortedStack()
        self._tasks: list[ScheduledTask] = []
        self._scheduler_task: asyncio.Task | None = None

    async def init(self):
        """Initialize."""
        self._scheduler_task = asyncio.create_task(self._iter())

    async def close(self):
        """Close."""
        self._scheduler_task.cancel()
        self._scheduler_task = None
        self._stack.clear()
        await asyncio.gather(
            *(
                asyncio.wait_for(task.executed, self.ON_EXIT_TIMEOUT_S)
                for task in self._tasks
                if task.executed and not (task.executed.done() or task.executed.cancelled())
            ),
            return_exceptions=True,
        )

    @property
    def routes(self):
        return {"tasks": self.list_tasks}

    async def list_tasks(self):
        """List registered tasks."""
        return [
            {
                "name": task.name,
                "enabled": task.enabled,
                "interval": task.interval,
                "policy": task.policy.value,
                "retires": task.retries,
                "executed": task.executed is not None,
                "called_at": task.called_at,
            }
            for task in self._tasks
        ]

    @property
    def tasks(self):
        """Get a list of registered tasks."""
        return self._tasks

    def schedule_task(
        self,
        method: _Callable,
        interval: float,
        params: dict | None = None,
        *,
        policy: ExecPolicy = ExecPolicy.CANCEL,
        max_timeout: float = None,
        retries: int = 1,
        name: str = None,
    ) -> ScheduledTask:
        """Schedule a periodic task.

        :param method: asynchronous function
        :param params: input kw arguments
        :param interval: schedule interval in seconds
        :param policy: task execution policy
        :param max_timeout: optional max timeout in seconds, for :py:obj:`~kaiju_tools..app.ExecPolicy.CANCEL`
            the lowest between `max_timeout` and `interval` will be used, by default `interval` is used for
            cancelled tasks and `interval * 4` for waited tasks
        :param retries: number of retries if any, see :py:func:`~kaiju_tools.functions.retry` for more info
        :param name: optional custom task name, which will be shown in the app's server list of task
        :returns: an instance of scheduled task
        """
        if name is None:
            name = f"scheduled:{method.__name__}"
        if params is None:
            params = {}
        if policy == ExecPolicy.CANCEL:
            max_timeout = min(interval, max_timeout) if max_timeout else interval
        elif not max_timeout:
            max_timeout = self.WAIT_TASK_TIMEOUT_SAFE_MOD * interval
        self.logger.debug("schedule", task_name=name, interval=interval, max_timeout=max_timeout, policy=policy.value)
        task = ScheduledTask(self, name, method, params, interval, policy, max_timeout, retries)
        self._tasks.append(task)
        self.refresh_rate = min(self.refresh_rate, interval, self.MIN_REFRESH_RATE)
        t_ex = time() + interval
        self._stack.insert(t_ex, task)
        return task

    async def _iter(self) -> None:
        """Iterate over the tasks ready to run."""
        while 1:
            to_execute = self._stack.pop_many(time())
            for scheduled in to_execute:
                scheduled = cast(ScheduledTask, scheduled)
                if not scheduled.enabled:
                    continue
                if scheduled.executed and not (scheduled.executed.done() or scheduled.executed.cancelled()):
                    if scheduled.policy is ExecPolicy.CANCEL:
                        scheduled.executed.cancel(msg="Cancelled by the scheduler")
                    elif scheduled.policy is ExecPolicy.WAIT:
                        continue
                    else:
                        raise RuntimeError(f"Unsupported exec policy: {scheduled.policy}")

                scheduled.executed = task = asyncio.create_task(self._run_task(scheduled))
                scheduled.called_at = time()
                task._scheduled = scheduled
                task.add_done_callback(self._task_callback)
                task.set_name(scheduled.name)

            await asyncio.sleep(self._get_sleep_interval())

    async def _run_task(self, task: ScheduledTask) -> None:
        """Run task in a wrapper."""
        try:
            async with timeout(task.max_timeout):
                if task.retries:
                    await retry(task.method, kws=task.params, retries=task.retries)
                else:
                    await task.method(**task.params)
        except Exception as exc:
            self.logger.error("task error", task_name=task.name, exc_info=exc)

    def _get_sleep_interval(self) -> float:
        """Get real sleep interval for the scheduler loop."""
        lowest_score = self._stack.lowest_score
        if lowest_score is None:
            lowest_score = 0
        t0 = time()
        interval = min(max(lowest_score - t0, t0), self.refresh_rate)
        return interval

    def _task_callback(self, task: asyncio.Task) -> None:
        """Capture a task result."""
        result = task.result()
        if isinstance(result, Exception):
            self.logger.error(str(result), exc_info=result)
        scheduled = task._scheduled  # noqa
        self._stack.insert(scheduled.called_at + scheduled.interval, scheduled)
        scheduled.executed = None
        task._scheduled = None


class HandlerSettings(TypedDict, total=False):
    """Log handler settings in a config file."""

    cls: str
    """Handler class."""

    name: str
    """Handler unique name."""

    enabled: bool
    """Enable this handler for loggers."""

    settings: dict
    """Init parameters for the handler class."""

    loglevel: str
    """Minimum log level for this handler."""


class LoggerSettings(TypedDict, total=False):
    """Logger settings in a config file."""

    name: str
    """Logger name (same as in python)."""

    enabled: bool
    """Enable this logger output."""

    handlers: list[str] | bool
    """List of handler names assigned to this logger. Setting it to `True` enables all handlers for this logger."""

    loglevel: str
    """Minimum level for this logger."""


class LoggingService(ContextableService):
    """Log handler and formatter configuration for application loggers."""

    def __init__(
        self,
        *args,
        loggers: Collection[LoggerSettings] = None,
        handlers: Collection[HandlerSettings] = None,
        loglevel: str = None,
        handler_classes=HANDLERS,
        **kws,
    ):
        """Initialize."""
        super().__init__(*args, **kws)
        self.handler_classes = handler_classes
        self.logger_settings: Collection[LoggerSettings] = loggers
        self.handler_settings: Collection[HandlerSettings] = handlers
        self.loglevel = loglevel if loglevel else getattr(self.app, "loglevel", "INFO")
        self.clear_root_logger()
        self.handlers = self.init_handlers()
        self.loggers = self.init_loggers()

    @staticmethod
    def clear_root_logger() -> None:
        """Remove all existing handlers from the root logger."""
        logger = logging.getLogger()
        logger.handlers.clear()
        logger.setLevel(logging.FATAL)

    def init_handlers(self) -> dict:
        """Initialize handler classes."""
        handlers = {}
        for settings in self.handler_settings:
            if not settings.get("enabled", True):
                continue
            cls = self.handler_classes[settings["cls"]]
            handler = cls(app=self.app, **settings.get("settings", {}))
            loglevel = settings.get("loglevel", self.loglevel)
            handler.setLevel(loglevel)
            handlers[settings["name"]] = handler
        return handlers

    def init_loggers(self) -> dict:
        """Initialize logger classes."""
        loggers = {}
        for settings in self.logger_settings:
            if not settings.get("enabled", True):
                continue
            logger = logging.getLogger(settings["name"])
            if settings["handlers"] is True:
                logger_handlers = self.handlers.keys()
            else:
                logger_handlers = settings["handlers"]
            for handler in logger_handlers:
                logger.addHandler(self.handlers[handler])
            loglevel = settings.get("loglevel", self.loglevel)
            logger.setLevel(loglevel)
            loggers[settings["name"]] = logger
        return loggers


class BaseCommand(ContextableService, abc.ABC):
    """Base application command, recognized by CLI."""

    service_name = None  #: command name after `python -m my_app [...]`
    run_app = True  #: run the application server for this command

    def __init__(self, app: App, logger=None):
        """Initialize."""
        super().__init__(app=app, logger=logger)
        self._runner = AppRunner(app)
        self._closed = True

    @classmethod
    def get_parser(cls) -> ArgumentParser:
        """Get an argument parser for CLI command arguments.

        You can provide additional CLI args for this particular command here.
        """
        return ArgumentParser()

    @abc.abstractmethod
    async def command(self, **kws):
        """Run a specific command."""

    async def init(self):
        """Initialize."""

    async def close(self):
        """Close command context."""

    @property
    def closed(self) -> bool:
        return self._closed

    def run(self):
        result = 1
        loop = asyncio.new_event_loop()
        try:
            self.logger.info("Setting up a webapp runner.")
            if self.run_app:
                loop.run_until_complete(self._runner.setup())
            self.logger.info("Initialization.")
            loop.run_until_complete(self.init())
            self._closed = False
            params, _ = self.get_parser().parse_known_args()
            self.logger.info('Executing command "%s" with params: "%s"', self.service_name, params)
            result = loop.run_until_complete(self.command(**params.__dict__))
        except Exception as err:
            self.logger.error("Command failed.", exc_info=err)
        finally:
            self.logger.info("Closing.")
            loop.run_until_complete(self.close())
            if self.run_app:
                loop.run_until_complete(self._runner.cleanup())
            loop.close()
            self._closed = True
            return result


class Commands(ClassRegistry[str, type[BaseCommand]]):
    """Map of all available commands."""

    @classmethod
    def get_base_classes(cls) -> tuple[type, ...]:
        return (BaseCommand,)


COMMANDS = Commands()  # : CLI commands registry, see :py:class:`~kaiju_tools.registry.ClassRegistry`


def run_command(app: App, command: ConfigLoader.CmdName, commands_registry: Commands = COMMANDS) -> int:
    """Run an app with a CLI command.

    :param app: application object
    :param command: command name after python -m app ...
    :param commands_registry: provide an instance of command class registry
    :returns: unix exit code
    """
    if command in commands_registry:
        cmd = commands_registry[command]
        cmd = cmd(app=app, logger=app.logger.getChild("CLI"))
        result = cmd.run()
    else:
        app.logger.error('Unknown command "%s".', command)
        result = errno.ENOENT
    return result


def init_app(
    settings: ProjectSettings,
    attrs: dict = None,
    middlewares: Collection = None,
    class_registry: ServiceClassRegistry = SERVICE_CLASS_REGISTRY,
) -> App:
    """Create a web application object.

    :param settings: project settings, usually provided by the configuration service.
    :param attrs: additional application attributes
    :param middlewares: list of additional aiohttp middlewares
    :param class_registry: registry of service classes
    """
    from kaiju_tools.http import error_middleware, session_middleware

    if middlewares is None:
        middlewares = []

    if settings.packages:
        for pkg in settings.packages:
            importlib.import_module(f"{pkg}.services")

    middlewares = [error_middleware, session_middleware, *middlewares]
    app = Application(middlewares=middlewares, logger=logging.getLogger(settings.main.name), **settings.app)
    app.request_context = REQUEST_CONTEXT
    app.request_session = REQUEST_SESSION
    app.id = uuid.uuid4()
    for key, value in settings.main.items():
        app[key] = value
        setattr(app, key, value)
    if attrs:
        for key, value in attrs.items():
            app[key] = value
            setattr(app, key, value)
    app.settings = settings
    app = cast(App, app)
    app.cookie_key = f"{app.env}-{app.name}-sid"
    app.namespace = Namespace(env=app.env, name=app.name)
    app.namespace_shared = Namespace(env=app.env, name="_shared")
    app.services = services = ServiceContextManager(
        app=app, settings=settings.services, class_registry=class_registry, logger=app.logger
    )
    services.create_services()
    app.cleanup_ctx.append(services.cleanup_context)
    return app


def run_server(
    init_app_func=init_app,
    base_config_paths: Collection[str] = None,
    base_env_paths: Collection[str] = None,
    default_env_paths: Collection[str] = None,
    enable_loader_logs: bool = False,
) -> None:
    """Run aiohttp server or command.

    :param init_app_func: app initialization function
    :param base_config_paths: list of base paths to .yml config files in sequential order
    :param base_env_paths: list of base paths to .env files in sequential order
    :param default_env_paths: list of additional paths to .env files which may be overriden by the `-e` CLI flag
    :param enable_loader_logs: enable logs for the config loader

    You should use this in the `__main__` section of the project to start the app since it starts an infinite loop.
    """
    if enable_loader_logs:
        logging.basicConfig(level="INFO")  # to be able to log config loader
    else:
        logging.basicConfig(level="FATAL")
    config_loader = ConfigLoader(
        base_config_paths=base_config_paths, base_env_paths=base_env_paths, default_env_paths=default_env_paths
    )
    command, config = config_loader.configure()
    logging.root.handlers = []
    app: App = init_app_func(config)
    if config.app.debug:
        warn("Running in debug mode")
    if command:
        run_command(app, command)
    else:
        run_app(app, access_log=None, **config.run)
