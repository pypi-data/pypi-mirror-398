"""
Utility functions and classes for working with docker images and containers.

This module assumes the testcontainers package is installed. Do not import it into environments where testcontainers
will not be available, for example, in any code that needs to run outside automated testing or the SwaggerUI interface.
"""
import logging
from contextlib import ExitStack, closing
from typing import Optional, Tuple
from heaserver.service.util import retry
from testcontainers.core.waiting_utils import wait_container_is_ready
from testcontainers.core.container import DockerContainer
import requests
from enum import Enum
from yarl import URL
from docker.errors import APIError

from heaserver.service.testcase.testenv import DockerContainerConfig, MicroserviceContainerConfig, _with_hea_env_vars


class DockerImages(Enum):
    """
    Images to use for SwaggerUI, tests, and other situations in which we want HEA to start Docker containers
    automatically.
    """
    MONGODB = 'percona/percona-server-mongodb:4.4.9'


@wait_container_is_ready()
def get_exposed_port(container: DockerContainer, port: int) -> str:
    """
    Returns the actual port that the docker container is listening to. It tries getting the port repeatedly until the
    container has sufficiently started to assign the port number.

    :param container: the docker container (required).
    :param port: the port to which the container's application is listening internally.
    :return: the exposed port.
    """
    return container.get_exposed_port(port)


@retry(IOError, retries=24, cooldown=5)
def wait_for_status_code(url, status: int) -> None:
    """
    Makes a HTTP GET call to the provided URL repeatedly until the returned status code is equal to the provided code.

    :param url: the URL to call.
    :param status: the status code to check for.
    :raises ValueError: if the status passed in does not match the actual status code returned by the request.
    """
    with closing(requests.get(url, timeout=30)) as response:
        actual_status = response.status_code
        if actual_status != status:
            raise ValueError(f'Expected status {status} and actual status {actual_status}')


@wait_container_is_ready()
def get_bridge_ip(container: DockerContainer) -> str:
    """
    Returns the IP address of the container on the default bridge network.
    :param container: a docker container.

    :return: an IP address.
    """
    return container.get_docker_client().bridge_ip(container.get_wrapped_container().id)


def start_other_container(container_config: DockerContainerConfig, stack: ExitStack) -> tuple[DockerContainer, str]:
    """
    Starts a Docker container that is not a HEA microservice. If the container_config has a check_path,
    the function will wait until the microservice successfully returns a GET call to the path before
    returning.

    :param container_config: the Docker image to start (required).
    :param stack: the ExitStack (required). The started container is added to the stack.
    :return: the started container and its external URL.
    """
    logger = logging.getLogger(__name__)
    container = _start_container(container_config, stack)
    external_url = f'http://{container.get_container_host_ip()}:{get_exposed_port(container, container_config.check_port)}'
    logger.debug('External URL of docker image %s is %s', container_config.image, external_url)
    if container_config.check_path is not None:
        wait_for_status_code(str(URL(external_url).with_path(container_config.check_path)),
                             container_config.check_status)
    return container, external_url


def start_microservice_container(container_config: MicroserviceContainerConfig, stack: ExitStack,
                                 registry_url: Optional[str] = None) -> Tuple[str, str]:
    """
    Starts a Docker container with the provided HEA microservice image and configuration (container_spec argument),
    Mongo database container, and exit stack for cleaning up resources. If the container_config has a check_path,
    the function will wait until the microservice successfully returns a GET call to the path before
    returning a two-tuple with the container's external and bridge URLs.

    The following environment variables are set in the container and will overwrite any pre-existing values that were
    set using the image's env_vars property:
        MONGO_HEA_DATABASE is set to the value of the hea_database argument.
        HEASERVER_REGISTRY_URL is set to the value of the registry_url argument.

    Any other environment variables set using the image's env_vars property are retained.

    :param container_config: the Docker image to start (required).
    :param stack: the ExitStack (required).
    :param registry_url: optional base URL for the heaserver-registry microservice.
    :return: a two-tuple containing the container's external URL string and the bridge URL string.
    """
    logger = logging.getLogger(__name__)
    logger.debug('Starting docker container %s', container_config.image)
    container_config_ = _with_hea_env_vars(container_config, registry_url)

    microservice = _start_container(container_config_, stack)

    external_url = f'http://{microservice.get_container_host_ip()}:{get_exposed_port(microservice, container_config_.port)}'
    logger.debug('External URL of docker image %s is %s', container_config_.image, external_url)

    if container_config_.check_path is not None:
        wait_for_status_code(str(URL(external_url).with_path(container_config_.check_path)), 200)

    bridge_url = f'http://{get_bridge_ip(microservice)}:{container_config_.port}'
    logger.debug('Internal URL of docker image %s is %s', container_config_.image, bridge_url)

    return external_url, bridge_url


@retry(APIError)
def _start_container(container_config: DockerContainerConfig, stack: ExitStack) -> DockerContainer:
    container = DockerContainer(container_config.image)
    for env, val in container_config.env_vars.items():
        container.with_env(env, val)
    for volume in container_config.volumes:
        container.with_volume_mapping(volume.host, volume.container, volume.mode)
    container.with_exposed_ports(*container_config.ports)
    for bind_port in container_config.bind_ports:
        container.with_bind_ports(container=bind_port.container, host=bind_port.host)
    microservice = stack.enter_context(container)
    return microservice
