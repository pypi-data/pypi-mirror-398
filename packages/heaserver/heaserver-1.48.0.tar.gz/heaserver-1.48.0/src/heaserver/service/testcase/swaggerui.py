"""
This module implements a simple API for launching a swagger UI for trying out a HEA microservice's REST APIs.

This module assumes the testcontainers package is installed. Do not import it into environments where testcontainers
will not be available, for example, in any code that needs to run outside automated testing or the SwaggerUI interface.
"""

from aiohttp_swagger3 import SwaggerDocs, SwaggerUiSettings
from aiohttp_swagger3.handlers import application_json
from aiohttp_swagger3.swagger_info import SwaggerInfo
from aiohttp import web
from importlib.metadata import version
from typing import Dict, List, Tuple, Callable, Iterable, Optional, Type, Mapping
from .testenv import app_context, DockerContainerConfig
from ..wstl import RuntimeWeSTLDocumentBuilder
from ..runner import client_session_cleanup_ctx
from ..db.database import CollectionKey, MicroserviceDatabaseManager, validate_collection_keys
from .dockermongo import DockerMongoManager, RealRegistryContainerConfig
from ..db.database import convert_to_collection_keys, FixtureKeyTypes
from heaobject.root import DesktopObjectDict
from ..openapi import download_openapi_spec
from .util import maybe_docker_is_not_running


def run(project_slug: str,
        desktop_objects: Mapping[CollectionKey | str, List[DesktopObjectDict]],
        routes: Iterable[Tuple[Callable, str, Callable]],
        content: Mapping[CollectionKey | str, Mapping[str, bytes]] | None = None,
        wstl_builder_factory: Optional[Callable[[], RuntimeWeSTLDocumentBuilder]] = None,
        registry_docker_image: Optional[str] = None,
        other_docker_images: Optional[List[DockerContainerConfig]] = None,
        db_manager_cls: Optional[Type[MicroserviceDatabaseManager]] = DockerMongoManager):
    """
    Launches a swagger UI for trying out the given HEA APIs. It downloads the HEA OpenAPI spec from gitlab.com. It
    launches Docker containers for any other projects specified in the other_docker_images argument. It also
    launches two MongoDB databases in Docker containers, one for the project being tested, and the other for the other
    containers. It inserts the given HEA objects into both databases, creates HEA Server Registry entries for all
    containers, and makes the given routes available to query in swagger. All containers run on Docker's default bridge
    network.

    This function creates two MongoDB databases because the project being tested is not running in a Docker container,
    so it needs any other containers' external URLs (starting with localhost) rather than Docker's internal network's
    IP addresses. To simplify this function's arguments, we load the exact same data into both MongoDB databases,
    except for the registry components, which differ only in their base URLs and names. The latter is set to the
    component's base URL. One of the databases will contain localhost base URLs, and the other will contain Docker
    bridge network IP addresses. This function logs each MongoDB container's mongo connection string at the info level
    so that you can tell which container is which.

    :param project_slug: the Gitlab project slug of interest. Required.
    :param desktop_objects: a mapping of mongo collection -> list of HEA objects as dicts. Required.
    :param routes: a list of three-tuples containing the command, path and collable of each route of interest. The
    commands are one of: aiohttp.web.get, aiohttp.web.delete, aiohttp.web.post, aiohttp.web.put or aiohttp.web.view.
    :param content: a mapping of mongo collection -> mapping of id -> content in bytes. Optional if the service's
    objects are not supposed to have content.
    :param wstl_builder_factory: a zero-argument callable that will return a RuntimeWeSTLDocumentBuilder. Optional if
    this service has no actions. Typically, you will use the heaserver.service.wstl.get_builder_factory function to
    get a factory object.
    :param registry_docker_image: an heaserver-registry docker image in REPOSITORY:TAG format, that will be launched
    after the MongoDB container is live.
    :param other_docker_images: optional list of ContainerSpec objects, which specify additional HEA microservice
    Docker containers to start.
    :param db_manager_cls: a database manager class from the heaserver.server.db package for the microservice being
    tested, if database connectivity is needed. Sets the appproperty.HEA_DB application property to this object. If
    omitted or None, heaserver.service.db.mongo.MongoManager is used.
    :raises OSError: If an error occurred accessing the OpenAPI spec.
    """
    if other_docker_images and registry_docker_image is None:
        raise ValueError('registry_docker_image must not be None when other_docker_images is not empty')
    if db_manager_cls is not None:
        db_ = db_manager_cls
    else:
        db_ = DockerMongoManager
    with maybe_docker_is_not_running():
        with download_openapi_spec() as open_api_spec_file:
            validate_collection_keys(desktop_objects)
            if content is not None:
                validate_collection_keys(content)
            with app_context(db_manager_cls=db_,
                            desktop_objects=convert_to_collection_keys(desktop_objects),
                            content=convert_to_collection_keys(content) if content else None,
                            other_docker_images=other_docker_images,
                            registry_docker_image=RealRegistryContainerConfig(image=registry_docker_image) if registry_docker_image is not None else None,
                            wstl_builder_factory=wstl_builder_factory) as (app, _):
                _init_swagger_docs(app, open_api_spec_file, project_slug, routes)
                app.cleanup_ctx.append(client_session_cleanup_ctx)
                web.run_app(app)


async def application_octet_stream(request: web.Request) -> Tuple[bytes, bool]:
    """
    Media type handler for application/octet-stream data.

    :param request: aiohttp request (required).
    :return: a two-tuple with the data, and whether the returned data is "raw" (untransformed).
    """
    return await request.read(), True


async def text_plain(request: web.Request) -> tuple[bytes, bool]:
    """
    Media type handler for text/plain data.

    :param request: aiohttp request (required).
    :return: a two-tuple with the data, and whether the returned data is "raw" (untransformed).
    """
    return await request.read(), True


def _init_swagger_docs(app: web.Application, openapi_spec_file: Optional[str], project_slug: str,
                       routes: Iterable[Tuple[Callable, str, Callable]]) -> None:
    swagger = SwaggerDocs(app,
                          swagger_ui_settings=SwaggerUiSettings(path="/docs"),
                          info=SwaggerInfo(title=project_slug,
                                           version=version(project_slug),
                                           description='A HEA microservice'),
                          components=openapi_spec_file)
    swagger.register_media_type_handler('application/vnd.collection+json', application_json)
    swagger.register_media_type_handler('application/octet-stream', application_octet_stream)
    swagger.register_media_type_handler('text/plain', text_plain)
    swagger.add_routes([r[0](r[1], r[2]) for r in routes])



