"""Docker images build services.

Note that this module requires docker package as additional dependency.

.. code-block:: console

    pip install docker

"""

import subprocess
import tempfile
import textwrap
import uuid
from collections.abc import Awaitable
from datetime import datetime
from pathlib import Path
from time import sleep
from typing import List, Optional, Union


try:
    import docker
    from docker.errors import NotFound
except ModuleNotFoundError:
    pass

from kaiju_tools.app import ContextableService
from kaiju_tools.functions import async_run_in_thread


__all__ = ['DockerImage', 'DockerContainer', 'DockerStack']


class DockerImage(ContextableService):
    """Docker image builder. Builds docker images from dockerfiles.

    Usage:

    .. code-block:: python

        img = DockerImage('myapp')
        img.build()

    Within a service context (it can remove image automatically on exit):

    .. code-block:: python

        with DockerImage('myapp') as img:
            ...

    Async versions of commands and the context are supported. All async functions use internal threading wrapped
    in coroutines.

    This class is made compatible with the service context manager class thus you may init it within the web app as a
    service to start the environment before the application itself (however it's not a very fast way to do it since
    it usually takes time to start and health check containers).
    """

    DOCKERFILE = './Dockerfile'
    NAMESPACE = 'systems.elemento'
    REPOSITORY = 'docker.io'

    _tempfile_prefix = '_docker_image'

    class Image:
        """Used for type hinting in docker container class."""

        tag: str
        version: str
        dockerfile: str
        labels: dict
        namespace: str
        remove_on_exit: bool
        always_build: bool
        pull: bool
        repository: str

    def __init__(
        self,
        tag: str,
        version: str = 'latest',
        dockerfile=DOCKERFILE,
        labels: dict = None,
        namespace=NAMESPACE,
        remove_on_exit=False,
        always_build=False,
        pull=True,
        repository=REPOSITORY,
        app=None,
        logger=None,
        **build_params,
    ):
        """Initialize.

        :param tag: base image tag, for example "mysite.com/myapp"
        :param version: version tag (latest by default)
        :param dockerfile: dockerfile location, uses `DOCKERFILE` by default
        :param labels: optional dictionary of labels, namespace will be automatically prefixed to the keys
        :param namespace: label namespace, usually it should be reversed domain of your organization
            about namespaces and labels you can use `opencontainers.org` conventions as reference

            https://github.com/opencontainers/image-spec/blob/master/annotations.md

        :param remove_on_exit: remove the image on context exit
        :param pull: will try to pull first before trying to build it locally
        :param repository: docker repository url
        :param always_build: always rebuild the image even if it exists
        :param logger:
        :param build_params: other build parameters for docker `build` command
        """
        self._docker_cli = docker.from_env()
        self._build_params = build_params
        self.tag = tag
        self.version = version
        self.fullname = f'{tag}:{version}'
        self.namespace = namespace
        self.dockerfile = Path(dockerfile)
        self.labels = labels if labels else {}
        self.repo = Path(repository)
        self._image = None
        self._pull = pull
        self._remove_on_exit = remove_on_exit
        self._always_build = always_build
        super().__init__(app=app, logger=logger)

    def __repr__(self):
        return f'{self.__class__.__name__}.{self.tag}'

    def __enter__(self):
        if self._pull and not self.exists:
            try:
                self.pull()
            except NotFound:
                self.logger.info('Image not found in repo.')
            else:
                return self
        if self._always_build or not self.exists:
            self.build()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._remove_on_exit:
            self.remove()

    async def init(self):
        if self._pull and not self.exists:
            try:
                await self.pull_async()
            except NotFound:
                self.logger.info('Image not found in repo.')
            else:
                return
        if self._always_build or not self.exists:
            await self.build_async()

    async def close(self):
        if self._remove_on_exit:
            await self.remove_async()

    @property
    def closed(self) -> bool:
        return not self._image

    @property
    def metadata(self) -> dict | None:
        """Returns docker metadata about the image or None if it doesn't exist."""
        images = self._docker_cli.images.list(name=self.fullname)
        meta = next((i.attrs for i in images if self.fullname in i.tags), None)
        return meta

    @property
    def exists(self) -> bool:
        return self.metadata is not None

    @classmethod
    def from_string(cls, dockerfile_str: str, dockerfile: str = None, *args, **kws) -> 'DockerImage':
        """Create an image object from a dockerfile string.

        It stores the dockerfile under a temporary name. You still will need to initiate build manually.

        :param dockerfile_str: dockerfile string in docker format
        :param dockerfile: here dockerfile name is not required but you may pass it to store the image string at a
            specific location
        :param args: see `DockerImage.__init__`
        :param kws: see `DockerImage.__init__`
        """
        dockerfile_str = textwrap.dedent(dockerfile_str)
        if dockerfile:
            with open(dockerfile, mode='w') as f:
                f.write(dockerfile_str)
        else:
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                f.write(dockerfile_str)
        image = DockerImage(dockerfile=f.name, *args, **kws)
        return image

    def build_async(self) -> Awaitable:
        return async_run_in_thread(self.build)

    def remove_async(self) -> Awaitable:
        return async_run_in_thread(self.remove)

    def pull_async(self) -> Awaitable:
        return async_run_in_thread(self.pull)

    def build(self):
        """Build a docker image. It may take a lot of time (depending on your dockerfile)."""
        self.logger.info('Building a docker image from %s.', self.dockerfile)
        self._check_dockerfile_exists()
        with open(self.dockerfile, mode='rb') as f:
            self._image = self._docker_cli.images.build(
                fileobj=f, tag=self.fullname, labels=self._get_labels(), **self._build_params
            )
        self.logger.info('Successfully built a docker image with tag %s.', self.tag)

    def pull(self):
        self.logger.info('Pulling image %s from %s.', self.fullname, self.repo)
        url = str(self.repo / self.tag)
        self._docker_cli.images.pull(repository=url, tag=self.version)
        self.logger.info('Pulled a new image.')

    def remove(self):
        self.logger.info('Removing the docker image.')
        self._docker_cli.images.remove(image=self.fullname, force=True)
        self._image = None
        self.logger.info('Successfully removed the docker image.')

    def _check_dockerfile_exists(self):
        if not self.dockerfile.exists() or not self.dockerfile.is_file():
            raise ValueError('Dockerfile %s does not exist.' % self.dockerfile)

    def _get_labels(self) -> dict:
        labels = {'created': datetime.now().isoformat()}
        labels.update(self.labels)
        labels = {f'{self.namespace}.{key}': str(value) for key, value in labels.items()}
        return labels

    def _get_logger_name(self):
        return self.__repr__()


class DockerContainer(ContextableService):
    """Single docker container management.

    You can use it in your tests or an automatic environment setup for your app.

    See the official Docker documentation for init parameters description.

    Usage:

    .. code-block:: python

        with DockerContainer('postgres', 'latest', 'my_postgres', ports={5444: 5432}) as c:
            ...

    Or with a docker image object:

    .. code-block:: python

        img = DockerImage('my_image')

        with DockerContainer(img, 'latest', 'my_postgres', ports={5444: 5432}) as c:
            ...

    Async versions of commands and the context are supported. All async functions use internal threading wrapped
    in coroutines.

    This class is made compatible with the service context manager class thus you may init it within
    the web app as a service to start the environment before the application itself (however it's not a very fast
    way to do it since it usually takes time to start and health check containers).
    """

    image_class = DockerImage  #: wraps dict or str `image` param in __init__

    def __init__(
        self,
        image: str | image_class.Image | image_class,
        name: str = None,
        command: str = None,
        ports: dict = None,
        env: dict = None,
        healthcheck: dict = None,
        sleep_interval=0,
        remove_on_exit=False,
        stop_before_run=True,
        wait_for_start=True,
        wait_for_stop=True,
        max_timeout=10,
        app=None,
        logger=None,
        **run_args,
    ):
        """Initialize.

        :param image: image tag string or an image object, in case of a dict or str argument
            it will be automatically wrapped in `DockerImage` class
        :param env: environment variables
        :param command: command to run
        :param name: container name
        :param ports: port mappings
        :param healthcheck: optional docker healthcheck
        :param sleep_interval: optional sleep interval after executing a start command
        :param remove_on_exit: remove the image on context exit
        :param wait_for_start: wait for containers ready when starting
        :param wait_for_stop: wait for containers stopped when stopping
        :param stop_before_run: stop container before running if it's already running
        :param max_timeout: max waiting time for wait_for_start and wait_for_stop commands
            in the first case it will raise an error if container is not up for an exceeded time
            in the latter case it will try to kill the container if it's up
        :param run_args: other docker run command arguments
        :param logger:
        """
        self._docker_cli = docker.from_env()
        self._command = command
        self._env = env
        self._name = name if name else str(uuid.uuid4())[:8]
        self._ports = ports
        self._healthcheck = healthcheck
        self._remove_on_exit = remove_on_exit
        self._wait_for_start = wait_for_start
        self._wait_for_stop = wait_for_stop
        self._stop_before_run = stop_before_run
        self.sleep_interval = float(sleep_interval)
        self.max_timeout = float(max_timeout)
        self._run_args = run_args
        self._container = None
        self._started = False
        super().__init__(app=app, logger=logger)
        self._image = self._init_image_from_args(image)

    def __repr__(self):
        return f'{self.__class__.__name__}.{self._name}'

    def __enter__(self):
        if self._remove_on_exit:
            self.remove()
        self._image.__enter__()
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._image.__exit__(exc_type, exc_val, exc_tb)
        self.stop()
        if self._remove_on_exit:
            self.remove()

    async def init(self):
        if self._remove_on_exit:
            await self.remove_async()
        await self._image.init()
        await self.start_async()

    async def close(self):
        await self.stop_async()
        await self._image.close()
        if self._remove_on_exit:
            await self.remove_async()

    @property
    def closed(self) -> bool:
        return not self._started

    @property
    def metadata(self) -> dict | None:
        """Returns docker container metadata or None if container doesn't exist."""
        try:
            return self._docker_cli.api.inspect_container(self._name)
        except NotFound:
            return None

    @property
    def exists(self) -> bool:
        return self.metadata is not None

    @property
    def status(self) -> str | None:
        """Return a container status string."""
        return self._get_status(self.metadata)

    @property
    def running(self) -> bool:
        return self.status == 'running'

    @property
    def healthy(self) -> bool:
        return self.status == 'healthy'

    @property
    def exited(self) -> bool:
        return self.status == 'exited'

    @property
    def ready(self) -> bool:
        metadata = self.metadata
        status = self._get_status(metadata)
        exit_code = metadata['State']['ExitCode']
        return any(
            [
                self._healthcheck and status == 'healthy',
                not self._healthcheck and status == 'running',
                status == 'exited' and exit_code == 0,
            ]
        )

    def start_async(self, *args, **kws) -> Awaitable:
        return async_run_in_thread(self.start, *args, **kws)

    def stop_async(self, *args, **kws) -> Awaitable:
        return async_run_in_thread(self.stop, *args, **kws)

    def remove_async(self, *args, **kws) -> Awaitable:
        return async_run_in_thread(self.remove, *args, **kws)

    def start(self, wait=None):
        """Run a container.

        If the container is already exists it will be restarted using `docker start` command. You can suppress this
        behaviour by setting `remove_on_exit` to True.

        :param wait: wait until the container is running and healthy
        """
        image = self._image.fullname
        if wait is None:
            wait = self._wait_for_start

        if self.exists:
            self.logger.info('Starting a previously stopped container.')
            self._container = self._docker_cli.api.start(self._name)
        else:
            self.logger.info('Starting a new container.')
            self._container = self._docker_cli.containers.run(
                image,
                environment=self._env,
                command=self._command,
                name=self._name,
                ports=self._ports,
                auto_remove=False,
                detach=True,
                healthcheck=self._healthcheck,
                **self._run_args,
            )

        if wait:
            self._wait_start()

        if self.sleep_interval:
            sleep(self.sleep_interval)

        self._started = True
        self.logger.info('Started.')

    def stop(self, wait=None):
        """Stop a running container.

        :param wait: wait for containers stopped when stopping
        """
        if wait is None:
            wait = self._wait_for_stop

        self.logger.info('Stopping the container.')
        if self.running:
            self._docker_cli.api.stop(self._name)

        if wait:
            self._wait_stop()

        self._container = None
        self._started = False
        self.logger.info('Stopped.')

    def pause(self):
        if self.running:
            self._container.pause()

    def unpause(self):
        if self.running:
            self._container.unpause()

    def remove(self):
        """Remove a container (delete its state)."""
        self.logger.info('Removing the container.')
        if self.exists:
            self._docker_cli.api.remove_container(self._name, force=True)
        self.logger.info('Removed the container.')

    def _get_logger_name(self):
        return self.__repr__()

    def _get_status(self, metadata):
        if not metadata:
            return None
        if self._healthcheck:
            status = metadata['State']['Health']['Status'].lower()
        else:
            status = metadata['State']['Status'].lower()
        return status

    def _wait_start(self):
        counter, dt = 0, 0.25
        self.logger.info('Waiting until the container is ready.')
        while not self.ready:
            counter += dt
            sleep(dt)
            if counter > self.max_timeout:
                raise RuntimeError('Container initialization timeout reached.')

    def _wait_stop(self):
        counter, dt = 0, 0.25
        self.logger.info('Waiting until the container is stopped.')
        while self.running:
            counter += dt
            sleep(dt)
            if counter > self.max_timeout:
                self.logger.info('Killing the container.')
                self._docker_cli.api.kill(self._name)
                break

    def _init_image_from_args(self, image) -> DockerImage:
        if isinstance(image, dict):
            if 'dockerfile_str' in image:
                image = self.image_class.from_string(**image)
            else:
                image = self.image_class(**image)
        elif isinstance(image, str):
            image = self.image_class(tag=image, app=self.app, logger=self.logger)
        return image


class DockerStack(ContextableService):
    """Docker stack management class.

    You can use it in your tests or an automatic environment setup for your app.

    For more info about docker-compose see:

    https://docs.docker.com/compose/

    https://docs.docker.com/compose/compose-file/compose-file-v3/

    Usage:

    .. code-block:: python

        with DockerStack(compose_files=['compose-file.yaml', 'compose-file-dev.yaml']) as stack:
            ...

    Async context is also provided (via threaded coroutines). All async functions use internal threading wrapped
    in coroutines.

    This class is made compatible with the service context manager class thus you may init it within
    the web app as a service to start the environment before the application itself (however it's not a very fast
    way to do it since it usually takes time to start and health check containers).

    .. note::

        If you are using Pycharm run configurations you may not be able to run docker because of crippled initialization
        of $PATH in some of docker installations. What you need to do is to echo $PATH from your terminal and copy
        them to the same variable inside your run configuration environment options.

    Recommendations:

    It's recommended to give a proper name to a stack and use profiles to manage services (see docker-compose
    profiles documentation). You should also try to inherit a base compose template in your compose files for different
    environments - this is done by using a list of compose files in arguments, the first file will be sequentially
    updated by other files. This is a standard docker-compose behaviour.

    """

    COMPOSE_FILE = './docker-compose.yaml'

    def __init__(
        self,
        name: str,
        compose_files: str | list = None,
        profiles: list[str] = None,
        services: list[str] = None,
        sleep_interval=0,
        stop_before_run=True,
        remove_containers=True,
        wait_for_start=True,
        wait_for_stop=True,
        build=False,
        max_timeout=10,
        app=None,
        logger=None,
    ):
        """Initialize.

        :param app:
        :param compose_files: list of compose files (see official docs about compose file inheritance and format)
            by default `COMPOSE_FILE` is used
        :param name: custom docker stack (project) name
        :param profiles: list of compose profiles (see official docs about that)
        :param services: list of services to run (None means all)
        :param sleep_interval: optional sleep interval after executing a start command
        :param remove_containers: remove containers after stop
        :param wait_for_start: wait for containers ready when starting
        :param wait_for_stop: wait for containers shutdown when stopping
        :param max_timeout: max waiting time for wait_for_start and wait_for_stop commands
            in the first case it will raise an error if container is not up for an exceeded time
            in the latter case it will try to kill the container if it's up
        :param stop_before_run: stop the stack before running if it's already running
        :param build: equivalent of --build flag - build images before the start
        :param logger:
        """
        self.sleep_interval = int(sleep_interval)
        if isinstance(compose_files, str):
            compose_files = [compose_files]
        elif not compose_files:
            compose_files = [self.COMPOSE_FILE]
        self._name = name if name else str(uuid.uuid4())[:8]
        self._compose_files = tuple(Path(compose_file) for compose_file in compose_files)
        self._profiles = profiles if profiles else []
        self._services = services if services else []
        self._remove_containers = remove_containers
        self._wait_for_start = wait_for_start
        self._wait_for_stop = wait_for_stop
        self.max_timeout = max_timeout
        self._stop_before_run = stop_before_run
        self._build = build
        self._started = False
        super().__init__(app=app, logger=logger)

    @classmethod
    def from_string(cls, compose_file_str: str, compose_files: str = None, *args, **kws) -> 'DockerStack':
        """Create an image object from a dockerfile string.

        It stores the dockerfile under a temporary name. You still will need to initiate build manually.

        :param compose_file_str: docker compose file yaml formatted string
        :param compose_files: compose file name is not required but you may pass it to store the string in a
            specific location
        :param args: see `DockerStack.__init__`
        :param kws: see `DockerStack.__init__`
        """
        compose_file_str = textwrap.dedent(compose_file_str)
        if isinstance(compose_files, (list, tuple)):
            compose_files = compose_files[0]
        if compose_files:
            with open(compose_files, mode='w') as f:
                f.write(compose_files)
        else:
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                f.write(compose_file_str)
        stack = DockerStack(compose_files=f.name, *args, **kws)
        return stack

    def __enter__(self):
        if self._stop_before_run and self.running:
            self.stop()
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._remove_containers:
            self.remove()
        else:
            self.stop()

    def __repr__(self):
        return f'{self.__class__.__name__}.{self._name}'

    async def init(self):
        if self._stop_before_run and self.running:
            await self.stop_async()
        await self.start_async()

    async def close(self):
        if self._remove_containers:
            await self.remove_async()
        else:
            await self.stop_async()

    @property
    def closed(self) -> bool:
        return not self._started

    @property
    def ready(self) -> bool:
        compose_files = self._get_compose_files_cli()
        cmd = f"docker-compose {compose_files} ps | grep -E 'unhealthy|starting'"
        value = self._run_cmd(cmd, check=False)
        return not bool(value)

    @property
    def running(self) -> bool:
        compose_files = self._get_compose_files_cli()
        cmd = f"docker-compose {compose_files} ps | grep -E 'unhealthy|healthy|starting|running'"
        value = self._run_cmd(cmd, check=False)
        return bool(value)

    @property
    def exists(self) -> bool:
        compose_files = self._get_compose_files_cli()
        cmd = f'docker-compose {compose_files} ps -q --all'
        value = self._run_cmd(cmd, check=False)
        return bool(value)

    def start_async(self, *args, **kws) -> Awaitable:
        return async_run_in_thread(self.start, *args, **kws)

    def stop_async(self) -> Awaitable:
        return async_run_in_thread(self.stop)

    def remove_async(self) -> Awaitable:
        return async_run_in_thread(self.remove)

    def start(self, wait=None, build=None):
        """Start the container stack.

        :param wait: wait until all containers are healthy (for this option
            you must implement health check functions in all your stack services
        :param build: rebuild containers on start
        """
        if wait is None:
            wait = self._wait_for_start
        if build is None:
            build = self._build
        self.logger.info('Starting a docker stack.')
        self._check_compose_files_exist()
        compose_files = self._get_compose_files_cli()
        profiles = ' '.join(f'--profile {profile}' for profile in self._profiles)
        services = ' '.join(self._services)
        if build:
            build = '--build'
        else:
            build = ''
        cmd = f'docker-compose {compose_files} {profiles} up {build} --force-recreate -d {services}'
        self._run_cmd(cmd)
        if wait:
            self._wait_start()
        if self.sleep_interval:
            sleep(self.sleep_interval)
        self.logger.info('The docker stack should be ready by now.')
        self._started = True

    def stop(self, wait=None):
        """Stop the container stack.

        :param wait: wait until all containers are healthy (for this option
            you must implement health check functions in all your stack services
        """
        if wait is None:
            wait = self._wait_for_stop
        self.logger.info('Stopping the docker stack.')
        compose_files = self._get_compose_files_cli()
        cmd = f'docker-compose {compose_files} stop'
        self._run_cmd(cmd)
        if wait:
            self._wait_stop()
        self.logger.info('Stopped the docker stack')
        self._started = False

    def remove(self, wait=None):
        """Remove the container stack.

        :param wait: wait until all containers are healthy (for this option
            you must implement health check functions in all your stack services
        """
        if wait is None:
            wait = self._wait_for_stop
        self.logger.info('Removing the docker stack.')
        compose_files = self._get_compose_files_cli()
        cmd = f'docker-compose {compose_files} rm -sfv'
        self._run_cmd(cmd)
        if wait:
            self._wait_stop()
        self.logger.info('Removed the stack.')

    def _wait_start(self):
        counter, dt = 0, 0.25
        self.logger.info('Waiting until the stack is ready.')
        while not self.ready:
            counter += dt
            sleep(dt)
            if counter > self.max_timeout:
                raise RuntimeError('Stack initialization timeout reached.')

    def _wait_stop(self):
        counter, dt = 0, 0.25
        self.logger.info('Waiting until the stack is stopped.')
        while self.running:
            counter += dt
            sleep(dt)
            if counter > self.max_timeout:
                raise RuntimeError('Stack termination timeout reached.')

    def _check_compose_files_exist(self):
        for compose_file in self._compose_files:
            if not compose_file.exists() or not compose_file.is_file():
                raise ValueError('Compose file %s does not exist.' % compose_file)

    def _get_logger_name(self):
        return self.__repr__()

    def _get_compose_files_cli(self) -> str:
        project = f'-p {self._name}'
        compose_files = ' '.join(f'-f {file}' for file in self._compose_files)
        return f'{project} {compose_files}'

    def _run_cmd(self, cmd: str, check=True) -> str:
        self.logger.debug(cmd)
        result = subprocess.run(cmd, shell=True, check=check, capture_output=True)
        r = result.stdout.decode()
        self.logger.debug('stdout: %s', r)
        self.logger.debug('stderr: %s', result.stderr.decode())
        return r
