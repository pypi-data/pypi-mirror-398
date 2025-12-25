"""
Portions of this module require that the testcontainers package is installed, as described below in the docstrings of
this module's functions and classes.
"""
from contextlib import ExitStack
from copy import deepcopy, copy
from typing import Optional, Dict, List, Type, NamedTuple
from aiohttp import web
from heaobject.registry import Resource
from heaobject.root import DesktopObjectDict, to_dict
from .. import runner
from .. import wstl
from ..db.database import CollectionKey, MicroserviceDatabaseManager
from ..db.database import get_collection_key_from_name
from .mockmongo import MockMongoManager
from ..util import TypeEnforcingFrozenDataclass
from dataclasses import dataclass
from contextlib import contextmanager, closing
from collections.abc import Generator, Sequence, MutableSequence, Mapping, MutableMapping, Callable
from abc import ABC
from ..util import retry
import logging


@dataclass(frozen=True)
class DockerVolumeMapping(TypeEnforcingFrozenDataclass):
    """
    Docker volume mapping. This class is immutable.

    Attributes:
        host: the host file or directory to map.
        container: the container directory.
        mode: the read-write mode (default 'ro' for read-only).
    """
    host: str
    container: str
    mode: str = 'ro'


@dataclass(frozen=True)
class BindPort(TypeEnforcingFrozenDataclass):
    """
    Bind port pair.

    Attributes:
        host: the host port.
        container: the container port to which the host port is mapped.
    """
    host: int
    container: int

    def pair(self) -> str:
        """
        Returns a host:container port mapping string.
        """
        return f'{self.host}:{self.container}'

    def __str__(self):
        """
        Returns a host:container port mapping string.
        """
        return self.pair()

    @staticmethod
    def from_port_mapping_string(pair: str) -> 'BindPort':
        """
        Factory for creating a bind port from a host:container port mapping string.
        """
        host_, container_ = pair.split(':')
        return BindPort(int(host_), int(container_))

class DockerContainerConfig:
    """
    Docker image and configuration for starting a container. This class is immutable.
    """

    def __init__(self, image: str, ports: list[int] | None, check_path: Optional[str] = None,
                 check_port: int | None = None, check_status: int = 200,
                 volumes: Optional[List[DockerVolumeMapping]] = None, env_vars: Optional[Mapping[str, str]] = None,
                 bind_ports: list[BindPort] | None = None):
        """
        Constructor.

        :param image: the image tag (required).
        :param ports: the exposed network ports.
        :param check_path: the URL path to check if the microservice is running.
        :param check_port: the network port to use with the check_path. If None or omitted, the first port in the ports
        list will be used.
        :param check_status: the status code expected from the check_path when successful.
        :param volumes: a list of volume mappings.
        :param env_vars: a dict containing environment variable names mapped to string values.
        :param bind_ports: the bind ports for the container as two tuples (host and container).
        """
        if image is None:
            raise ValueError('image cannot be None')
        if any(not isinstance(port, int) for port in ports or []):
            raise ValueError('ports must contain only ints')
        if any(not isinstance(volume, DockerVolumeMapping) for volume in volumes or []):
            raise TypeError(f'volumes must contain only {DockerVolumeMapping} objects')
        if any(not isinstance(k, str) and isinstance(v, str) for k, v in (env_vars or {}).items()):
            raise TypeError('env_vars must be a str->str dict')
        if any(not isinstance(bind_port, BindPort) for bind_port in bind_ports or []):
            raise TypeError('bind_ports must contain BindPort objects')
        self.__image = str(image)
        self.__ports = list(ports) if ports is not None else []
        self.__bind_ports = list(bind_ports) if bind_ports is not None else []
        self.__check_path = str(check_path) if check_path is not None else None
        self.__check_port = int(check_port) if check_port is not None else self.__ports[0]
        self.__check_status = int(check_status)
        self.__volumes = list(volumes) if volumes else []
        self.__env_vars = dict(env_vars) if env_vars is not None else {}

    @property
    def image(self) -> str:
        """
        The image tag (read-only).
        """
        return self.__image

    @property
    def ports(self) -> list[int]:
        """
        The exposed ports (read-only).
        """
        return list(self.__ports)

    @property
    def bind_ports(self) -> list[BindPort]:
        return list(self.__bind_ports)

    @property
    def check_path(self) -> Optional[str]:
        """
        The URL path to check for whether the microservice is running (read-only).
        """
        return self.__check_path

    @property
    def check_port(self) -> int:
        """
        The network port to use with the check_path. If None or omitted, the first port in the ports
        list will be used.
        """
        return self.__check_port

    @property
    def check_status(self) -> int:
        """
        The status code expected from a successful call to the check path. Is 200 by default.
        """
        return self.__check_status

    @property
    def volumes(self) -> List[DockerVolumeMapping]:
        """
        A list of VolumeMapping instances indicating what volumes to map (read-only, never None).
        """
        return copy(self.__volumes)

    @property
    def env_vars(self) -> Dict[str, str]:
        """
        A dict of environment variable names to string values.
        """
        return copy(self.__env_vars)

    def with_env_vars(self, env_vars: Optional[Mapping[str, str]]) -> 'DockerContainerConfig':
        """
        Returns a new DockerContainerConfig with the same values as this one, plus any environment variables in the
        env_vars argument.

        :param env_vars: any environment variables.
        :return:
        """
        new_env_vars = self.env_vars
        if env_vars is not None:
            new_env_vars.update(env_vars)
        return DockerContainerConfig(image=self.image, ports=self.ports, check_path=self.check_path,
                                     volumes=self.volumes, env_vars=new_env_vars)

    def get_bridge_components(self, bridge_url: str) -> list[DesktopObjectDict]:
        return []

    def get_external_components(self, external_url: str) -> list[DesktopObjectDict]:
        return []


class MicroserviceContainerConfig(DockerContainerConfig):
    """
    Docker image and configuration for starting a microservice. This class is immutable.
    """

    def __init__(self, image: str, port: int, check_path: str | None = None, check_status: int = 200,
                 resources: List[Resource] | None = None,
                 volumes: List[DockerVolumeMapping] | None = None,
                 env_vars: Mapping[str, str] | None = None,
                 db_manager_cls: type[MicroserviceDatabaseManager] | None = None):
        """
        Constructor.

        :param image: the image tag (required).
        :param port: the exposed port (required).
        :param check_path: the URL path to check if the microservice is running.
        :param check_status: the status code expected from the check_path when successful.
        :param resources: a list of heaobject.registry.Resource dicts indicating what content types this image is designed for.
        :param volumes: a list of volume mappings.
        :param env_vars: a dict containing environment variable names mapped to string values.
        :param db_manager_cls: the database manager type for this microservice, or None if the service does not use a
        database.
        """
        if port is None:
            raise ValueError('port cannot be None')
        super().__init__(image=image, ports=[port], check_path=check_path, check_status=check_status, volumes=volumes,
                         env_vars=env_vars)
        if any(not isinstance(r, Resource) for r in resources or []):
            raise TypeError(f'resources must contain only {Resource} objects')
        self.__port = int(port)
        self.__resources = [deepcopy(e) for e in resources or []]
        self.__volumes = list(volumes) if volumes else []
        self.__env_vars = dict(env_vars) if env_vars is not None else {}
        self.__db_manager_cls = db_manager_cls  # immutable

    @property
    def port(self) -> int:
        """
        The exposed port (read-only).
        """
        return self.ports[0]

    @property
    def resources(self) -> Optional[List[Resource]]:
        """
        A list of heaobject.registry.Resource dicts indicating what content types this image is designed for (read-only).
        """
        return deepcopy(self.__resources)

    @property
    def env_vars(self) -> Dict[str, str]:
        """
        A dict of environment variable names to string values.
        """
        return copy(self.__env_vars)

    @property
    def db_manager_cls(self) -> Optional[type[MicroserviceDatabaseManager]]:
        """
        The database manager class, if any.
        """
        return self.__db_manager_cls  # immutable

    def with_env_vars(self, env_vars: Optional[Mapping[str, str]]) -> 'MicroserviceContainerConfig':
        """
        Returns a new MicroserviceContainerConfig with the same values as this one, plus any environment variables in
        the env_vars argument.

        :param env_vars: any environment variables.
        :return:
        """
        new_env_vars = self.env_vars
        if env_vars is not None:
            new_env_vars.update(env_vars)
        return MicroserviceContainerConfig(image=self.image, port=self.port, check_path=self.check_path,
                                           resources=self.resources, volumes=self.volumes, env_vars=new_env_vars,
                                           db_manager_cls=self.db_manager_cls)

    def get_bridge_components(self, bridge_url: str) -> list[DesktopObjectDict]:
        logger = logging.getLogger(__name__)
        result = super().get_bridge_components(bridge_url)
        logger.debug('Adding bridge component for resources %s', self.resources)
        result.append({'type': 'heaobject.registry.Component', 'base_url': bridge_url, 'name': bridge_url,
                       "owner": "system|none",
                       'resources': [to_dict(r) for r in self.resources or []]})
        return result

    def get_external_components(self, external_url: str) -> list[DesktopObjectDict]:
        logger = logging.getLogger(__name__)
        result = super().get_external_components(external_url)
        logger.debug('Adding external component for resources %s', self.resources)
        result.append({'type': 'heaobject.registry.Component', 'base_url': external_url, 'name': external_url,
                       "owner": "system|none", 'resources': [to_dict(r) for r in self.resources or []]})
        return result


class RegistryContainerConfig(MicroserviceContainerConfig, ABC):
    """
    Abstract base class for builders that configure and create HEA Registry Service docker containers.

    This class assumes that the testcontainers package is installed. Do not create instances of it when testcontainers
    will not be available, for example, in any code that needs to run outside automated testing or the SwaggerUI
    interface. Using it as a type annotation for optional parameters and the like where no actual instances of it
    will be created is okay, however.
    """

    def __init__(self, *args, db_manager_cls: type[MicroserviceDatabaseManager], **kwargs):
        super().__init__(*args, **kwargs)
        self.__db_manager_cls = db_manager_cls

    @property
    def db_manager_cls(self) -> type[MicroserviceDatabaseManager]:
        return self.__db_manager_cls  # type:ignore  # mypy bug? It won't accept removing Optional from the return type.


class MockRegistryContainerConfig(RegistryContainerConfig):
    """
    Creates an HEA Registry Service docker container configured to use a mock mongodb database for data management.

    This class assumes that the testcontainers package is installed. Do not create instances of it when testcontainers
    will not be available, for example, in any code that needs to run outside automated testing or the SwaggerUI
    interface. Using it as a type annotation for optional parameters and the like where no actual instances of it
    will be created is okay, however.

    :param image: the label of the docker image to use (required).
    """

    def __init__(self, image: str):
        super().__init__(image=image, port=8080, check_path='/components', db_manager_cls=MockMongoManager)


class DockerContainerPorts(NamedTuple):
    """
    A docker image and its external and bridge URLs.

    Parameters:
        image: the name of the image.
        external_url: the URL of the container from outside the docker bridge network as a string.
        bridge_url: the URL of the container on the docker bridge network as a string.
    """
    image: str
    external_url: str
    bridge_url: str


@contextmanager
def app_context(db_manager_cls: Type[MicroserviceDatabaseManager],
                desktop_objects: Mapping[CollectionKey, Sequence[DesktopObjectDict]],
                other_docker_images: Optional[Sequence[DockerContainerConfig]] = None,
                registry_docker_image: Optional[RegistryContainerConfig] = None,
                content: Mapping[CollectionKey, Mapping[str, bytes]] | None = None,
                wstl_builder_factory: Optional[Callable[[], wstl.RuntimeWeSTLDocumentBuilder]] = None,
                package_name: str | None = None) -> Generator[
    tuple[web.Application, list[DockerContainerPorts]], None, None]:
    """
    Starts the test environment. The test environment consists of: a "bridge" database that is accessible from the
    internal docker network; an "external" database that is accessible from outside the network; a "bridge" registry
    service that is accessible from the internal docker network; an "external" registry service that is accessible from
    outside the network; the service being tested, which is run from outside of docker; and any service dependencies,
    which are run as docker containers. The provided context manager will clean up any resources upon exit.

    Do not pass DockerContainerConfig nor RegistryContainerConfig objects into this function unless the testcontainer
    package is installed.


    :param db_manager_cls: the database manager class for the microservice being tested (required).
    :param desktop_objects: HEA desktop objects to load into the database (required), as a map of collection -> list of
    desktop object dicts.
    :param other_docker_images: the docker images of any service dependencies.
    dictionary keys are strings. If None, defaults to db_manager_cls.
    :param registry_docker_image: an HEA registry service docker image.
    :param content: any content to load into the database.
    :param wstl_builder_factory: a zero-argument callable that will return a RuntimeWeSTLDocumentBuilder. Optional if
    this service has no actions. Typically, you will use the heaserver.service.wstl.get_builder_factory function to
    get a factory object.
    :param package_name: the service's distribution package name, used to dynamically register metadata about this
    service with the registry service. Do not pass a package name if no registry service is running.
    :return: a generator of two tuples containing the aiohttp Application object and a list of DockerContainerPorts
    containing the ports for each requested docker image.
    """

    bridge_desktop_objects: MutableMapping[CollectionKey, MutableSequence[DesktopObjectDict]] = dict({k: list(v) for k, v in deepcopy(desktop_objects).items()})
    external_desktop_objects: MutableMapping[CollectionKey, MutableSequence[DesktopObjectDict]] = dict({k: list(v) for k, v in deepcopy(desktop_objects).items()})

    def _bridge_dbs_to_start() -> set[type[MicroserviceDatabaseManager]]:
        bridge_db_manager_cls = set()
        if other_docker_images:
            bridge_db_manager_cls.update(
                [img.db_manager_cls for img in other_docker_images if
                 isinstance(img, MicroserviceContainerConfig) and img.db_manager_cls is not None])
        if registry_docker_image is not None and registry_docker_image.db_manager_cls is not None:
            bridge_db_manager_cls.add(registry_docker_image.db_manager_cls)
        return bridge_db_manager_cls

    class TestEnvExitStack(ExitStack):
        @retry(ValueError, IOError, retries=6, cooldown=10)
        def __exit__(self, exc_type, exc_val, exc_tb) -> bool | None:
            return super().__exit__(exc_type, exc_val, exc_tb)

    with TestEnvExitStack() as context_manager, closing(db_manager_cls()) as external_db_, \
        db_manager_cls.environment(), db_manager_cls.context():

        bridge_dbs = [context_manager.enter_context(closing(bridge_db_cls())) for bridge_db_cls in
                        _bridge_dbs_to_start()]

        external_db_.start_database(context_manager)
        for bridge_db in bridge_dbs:
            bridge_db.start_database(context_manager)

        if registry_docker_image is not None:
            (_, bridge_registry_url), (external_registry_url, _) = map(
                lambda dbs: _start_registry_service(dbs, context_manager, registry_docker_image), [bridge_dbs, [external_db_]])
        else:
            external_registry_url = None
            bridge_registry_url = None

        if other_docker_images:
            if registry_docker_image is None:
                raise ValueError('registry_docker_image is required when other_docker_images is non-None')
            docker_image_ports = _start_other_docker_containers(
                bridge_desktop_objects,
                external_desktop_objects,
                other_docker_images, bridge_registry_url,
                bridge_dbs,
                context_manager,
                registry_docker_image.db_manager_cls)
        else:
            docker_image_ports = []
        if registry_docker_image is not None:
            docker_image_ports.append(DockerContainerPorts(image=registry_docker_image.image,
                                                            external_url=external_registry_url,
                                                            bridge_url=bridge_registry_url))

        config_file = _generate_config_file(external_db_, external_registry_url)
        config_ = runner.init(config_string=config_file)
        external_db_.insert_all(external_desktop_objects, content)
        for b_ in bridge_dbs:
            b_.insert_all(bridge_desktop_objects, content)

        yield runner.get_application(package_name=package_name, db=external_db_, wstl_builder_factory=wstl_builder_factory,
                                     config=config_), docker_image_ports


def _start_registry_service(dbs, context_manager, registry_docker_image):
    from .docker import start_microservice_container
    bridge_config_ = _add_db_config(registry_docker_image, dbs)
    _, bridge_registry_url = start_microservice_container(bridge_config_, context_manager)
    return _, bridge_registry_url


def _add_db_config(docker_container_config: MicroserviceContainerConfig,
                   dbs: list[MicroserviceDatabaseManager]) -> MicroserviceContainerConfig:
    """
    Returns a copy of the docker_container_config with additional environment variables needed for connecting to the
    database.

    This function assumes that the testcontainers package is installed. Do not use it when testcontainers
    will not be available, for example, in any code that needs to run outside automated testing or the SwaggerUI
    interface.

    :param docker_container_config: a DockerContainerConfig (required).
    :param dbs: the available database containers.
    :return: a newly created DockerContainerConfig.
    """
    db_manager = _get_db_manager(dbs, docker_container_config.db_manager_cls)
    if db_manager is not None:
        env_vars = db_manager.get_env_vars()
    else:
        env_vars = None
    return docker_container_config.with_env_vars(env_vars)


def _get_db_manager(dbs: list[MicroserviceDatabaseManager],
                    db_manager_cls_: Optional[type[MicroserviceDatabaseManager]]) -> Optional[
    MicroserviceDatabaseManager]:
    """
    Returns the database manager with the given type.

    :param dbs: the available database managers.
    :param db_manager_cls_: the type of interest.
    :return: a database manager, or None if no database manager with the given type is available.
    """
    if db_manager_cls_ is not None:
        return next((b for b in dbs if isinstance(b, db_manager_cls_)), None)
    else:
        return None


def _start_other_docker_containers(
    bridge_desktop_objects: MutableMapping[CollectionKey, MutableSequence[DesktopObjectDict]],
    external_desktop_objects: MutableMapping[CollectionKey, MutableSequence[DesktopObjectDict]],
    other_docker_images: Optional[Sequence[DockerContainerConfig]],
    registry_url: Optional[str],
    bridge_dbs: list[MicroserviceDatabaseManager],
    stack: ExitStack,
    components_db_manager_cls: Type[MicroserviceDatabaseManager]) -> list[DockerContainerPorts]:
    """
    Starts the provided microservice containers.

    This function assumes that the testcontainers package is installed. Do not use it when testcontainers
    will not be available, for example, in any code that needs to run outside automated testing or the SwaggerUI
    interface.

    :param bridge_desktop_objects: data to go into the database that is internal to the docker network, as a map of
    collection -> list of desktop object dicts. This map must not be copied before being passed in.
    :param external_desktop_objects: data to go into the database that is outside of the docker network, as a map of
    collection -> list of desktop object dicts. This map must not be copied before being passed in.
    :param other_docker_images: a list of docker images to start.
    :param registry_url: the URL of the registry microservice.
    :param stack: the ExitStack.
    :param components_db_manager_cls: the database manager for registry components (required).
    """

    def _start_container_partial(img: DockerContainerConfig) -> DockerContainerPorts | None:
        if isinstance(img, MicroserviceContainerConfig):
            return _start_microservice(bridge_dbs, bridge_desktop_objects, external_desktop_objects, img, registry_url,
                                       stack,
                                       components_db_manager_cls)
        else:
            _start_other_container(img, stack)
            return None

    return [dcp for dcp in map(_start_container_partial, (i for i in other_docker_images or [])) if dcp is not None]


def _start_other_container(docker_container_config: DockerContainerConfig, stack: ExitStack) -> None:
    from .docker import start_other_container
    start_other_container(docker_container_config, stack)


def _start_microservice(bridge_dbs: list[MicroserviceDatabaseManager],
                        bridge_desktop_objects: MutableMapping[CollectionKey, MutableSequence[DesktopObjectDict]],
                        external_desktop_objects: MutableMapping[CollectionKey, MutableSequence[DesktopObjectDict]],
                        docker_container_config: MicroserviceContainerConfig, registry_url: Optional[str],
                        stack: ExitStack,
                        components_db_manager_cls: Type[MicroserviceDatabaseManager]) -> DockerContainerPorts:
    """
    Starts a docker container with the provided image. As a side effect, it adds HEA registry components to the
    bridge_desktop_objects and external_desktop_objects dictionaries.

    :return: a DockerContainerPorts instance.
    :raises ValueError: if the microservice failed to start.
    """
    logger = logging.getLogger(__name__)

    logger.debug('Bridge desktop objects before: %s', bridge_desktop_objects)
    logger.debug('External desktop objects before: %s', external_desktop_objects)
    from .docker import start_microservice_container
    db_manager = _get_db_manager(bridge_dbs, docker_container_config.db_manager_cls)
    if db_manager is not None:
        docker_container_config_ = docker_container_config.with_env_vars(db_manager.get_env_vars())
    else:
        docker_container_config_ = docker_container_config
    logger.debug('Starting container %s', docker_container_config_.image)
    try:
        external_url, bridge_url = start_microservice_container(docker_container_config_, stack, registry_url)
    except ValueError as e:
        raise ValueError(f'Failed to start docker container {docker_container_config_.image}') from e
    logger.debug('Container %s started', docker_container_config_.image)
    components_collection_key = CollectionKey(name='components', db_manager_cls=components_db_manager_cls)
    bridge_components = bridge_desktop_objects \
        .setdefault(
        get_collection_key_from_name(bridge_desktop_objects, name='components') or components_collection_key, [])
    items_to_add = docker_container_config_.get_bridge_components(bridge_url)
    bridge_components.extend(items_to_add)

    logger.debug('Bridge desktop objects after: %s', bridge_desktop_objects)
    external_desktop_objects \
        .setdefault(
        get_collection_key_from_name(external_desktop_objects, name='components') or components_collection_key, []) \
        .extend(docker_container_config_.get_external_components(external_url))
    logger.debug('External desktop objects after: %s', external_desktop_objects)
    return DockerContainerPorts(image=docker_container_config_.image, external_url=external_url, bridge_url=bridge_url)


def _generate_config_file(db_manager: MicroserviceDatabaseManager, registry_url: Optional[str]) -> str:
    """
    Generates a HEA microservice configuration file.

    :param db_manager: a DatabaseManager instance (required).
    :param registry_url: the URL of the registry service.
    :returns: the configuration file string.
    """
    if db_manager is not None:
        if registry_url is None:
            config_file = db_manager.get_config_file_section()
        else:
            config_file = f"""
    [DEFAULT]
    Registry={registry_url}

    {db_manager.get_config_file_section()}
                    """
    else:
        if registry_url is None:
            config_file = ''
        else:
            config_file = f"""
        [DEFAULT]
        Registry={registry_url}
                        """
    return config_file


def _with_hea_env_vars(container_config: MicroserviceContainerConfig,
                       registry_url: Optional[str]) -> MicroserviceContainerConfig:
    """
    Copies the provided container_spec, adding the environment variables corresponding to the provided arguments.

    This function assumes that the testcontainers package is installed. Do not use it when testcontainers
    will not be available, for example, in any code that needs to run outside automated testing or the SwaggerUI
    interface.

    :param container_config: the image and configuration (required).
    :param db_manager: a TestDatabaseFactory instance (required).
    :param registry_url: the URL of the registry service, which populates the HEASERVER_REGISTRY_URL environment
    variable.
    :return: the copy of the provided container_spec.
    """
    env_vars: Dict[str, str] = {}
    if registry_url is not None:
        env_vars['HEASERVER_REGISTRY_URL'] = registry_url
    return container_config.with_env_vars(env_vars)
