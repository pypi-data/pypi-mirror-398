from .aiohttptestcase import HEAAioHTTPTestCase
from ..db.database import convert_to_collection_keys
from .expectedvalues import Action, Link, expected_values
from .. import wstl
from aiohttp.web import Application
from ..oidcclaimhdrs import SUB
from .testenv import app_context, RegistryContainerConfig, DockerContainerConfig
from ..db.database import CollectionKey, MicroserviceDatabaseManager, validate_collection_keys
from heaserver.service.testcase.mockmongo import MockMongoManager
from aiohttp import hdrs
from heaobject.user import NONE_USER
from heaobject.root import DesktopObjectDict, PermissionContext, DesktopObject
from typing import Optional, Any, Iterable, Type, Mapping
from .util import maybe_docker_is_not_running
from collections.abc import Sequence
from copy import deepcopy
from yarl import URL
import logging
import abc


class MicroserviceTestCase(HEAAioHTTPTestCase, abc.ABC):
    """
    Abstract base class for testing HEA microservices. It provides many expected values that should be returned from
    requests.
    """

    @abc.abstractmethod
    def __init__(self,
                 coll: str,
                 desktop_objects: Mapping[CollectionKey | str, Sequence[DesktopObjectDict]],
                 db_manager_cls: Optional[Type[MicroserviceDatabaseManager]] = MockMongoManager,
                 wstl_package: str | None = None,
                 href: Optional[str | URL] = None,
                 body_post: Optional[Mapping[str, Mapping[str, Any]]] = None,
                 body_put: Optional[Mapping[str, Mapping[str, Any]]] = None,
                 content_id: Optional[str] = None,
                 expected_all: Optional[list[Mapping[str, Any]]] = None,
                 expected_one: Optional[list[Mapping[str, Any]]] = None,
                 expected_one_wstl: Optional[Mapping[str, Any]] = None,
                 expected_all_wstl: Optional[Mapping[str, Any]] = None,
                 expected_one_duplicate_form: Optional[Mapping[str, Any]] = None,
                 expected_opener: Optional[str | URL] = None,
                 expected_opener_body: Optional[Sequence[Mapping[str, Any]]] = None,
                 content: Mapping[CollectionKey | str, Mapping[str, bytes]] | None = None,
                 content_type: Optional[str] = None,
                 put_content_status: Optional[int] = None,
                 methodName='runTest',
                 port: Optional[int] = None,
                 sub: Optional[str] = NONE_USER,
                 registry_docker_image: Optional[RegistryContainerConfig] = None,
                 other_docker_images: Iterable[DockerContainerConfig] | None = None,
                 package_name: str | None = None):
        """
        Default constructor for initializing a test case class. Subclasses must provide a constructor where the first
        argument after self is methodName and accepts a string, and there are no positional arguments after methodName.
        The subclass' constructor must call this default implementation.

        :param coll: collection name (required).
        :param desktop_objects: HEA desktop objects to load into the database (required), as a map of collection ->
        list of desktop object dicts.
        :param db_manager_cls: the database factory class. Defaults to TestMockMongoManager.
        :param wstl_package: the name of the package containing the WeSTL data package.
        :param href: the resource being tested. If None, uses http://localhost:{port}/{coll}/, where {coll} is the
        collection name, and {port} is the port ultimately used by this test case.
        :param body_post: a Collection+JSON template as a dictionary, to be used for submitting POST requests.
        Populates the _body_post protected attribute. If None, _body_post will be None.
        :param body_put: a Collection+JSON template as a dictionary, to be used for submitting PUT requests. Populates
        the _body_put protected attribute. If None, _body_put will be None. Populates the _body_put protected
        attribute. If None, _body_put will be None.
        :param content_id: the ID of an object that has content, to be used for getting and updating content.
        :param expected_all: the expected JSON dictionary list from a GET all request for a Collection+JSON document.
        Populates the _expected_all protected attribute. If None, _expected_all will be None.
        :param expected_one: the expected JSON dictionary list from a GET one request for a Collection+JSON document.
        If None, expected_all will be used. Populates the _expected_one attribute. If None and expected_all is None,
        _expected_one will be None.
        :param expected_one_wstl: the expected JSON dictionary list from a GET one request for a run-time WeSTL
        document. Populates the _expected_one_wstl protected attribute. If None, the value of expected_all_wstl will be
        used. If None and expected_all_wstl is None, _expected_one_wstl will be None.
        :param expected_all_wstl: the expected JSON dictionary list from a GET all request for a run-time WeSTL
        document. Populates the _expected_all_wstl protected attribute. If None, _expected_all_wstl will be None.
        :param expected_one_duplicate_form: expected JSON from a GET request for a form template to duplicate an
        object. Populates the _expected_one_duplicate_form protected attribute. If None, _expected_one_duplicate_form
        will be None.
        :param expected_opener: the expected URL of the resource that does the opening.
        :param expected_opener_body: expected list of JSON mappings for GET calls for an HEA desktop object's opener
        choices.
        :param content: content to send via a PUT content request. It should not be the same as the content already
        associated with the object whose ID is content_id.
        :param content_type: the MIME type of the content included with the objects (e.g., text/plain; charset=utf-8).
        Must be specified if content_type is specified.
        :param put_content_status: the status code expected from a response to a PUT content request.
        :param methodName: the name of the method to test.
        :param port: the port number to run aiohttp. If None, a random available port will be chosen.
        :param sub: the user from which the requests will be sent. Defaults to heaobject.user.NONE_USER.
        :param registry_docker_image: a RegistryContainerConfig for a docker image of the HEA Registry Microservice.
        :param other_docker_images: an iterable of DockerContainerConfigs for docker images of other microservices.
        :param package_name: the service's distribution package name. If None, service metadata will not be registered
        with the registry service, which may be what you want if no registry service is running.
        """
        super().__init__(methodName=methodName, port=port)
        if href is None:
            href_ = f'/{coll}/'  # FIXME: href default needs to include root (http://localhost:...)
        else:
            href_ = str(href)
            if not href_.endswith('/'):
                href_ += '/'
        self._href = URL(href_)
        self._coll = str(coll)
        self._body_post = deepcopy(body_post)
        self._body_put = deepcopy(body_put)
        self._content_id = content_id
        self._expected_all = deepcopy(expected_all)
        self._expected_one = deepcopy(expected_one or expected_all)
        self._expected_one_wstl = deepcopy(expected_one_wstl or expected_all_wstl)
        self._expected_all_wstl = deepcopy(expected_all_wstl)
        self._expected_one_duplicate_form = deepcopy(expected_one_duplicate_form)
        self._expected_opener = expected_opener
        self._expected_opener_body = deepcopy(expected_opener_body)
        self._wstl_package = wstl_package
        validate_collection_keys(desktop_objects)
        self.__desktop_objects = deepcopy(convert_to_collection_keys(desktop_objects))
        if content is not None:
            validate_collection_keys(content)
        self._content = deepcopy(convert_to_collection_keys(content) if content else None)
        self._content_type = content_type
        self._put_content_status = put_content_status
        self._headers = {SUB: sub if sub is not None else NONE_USER, hdrs.X_FORWARDED_HOST: 'localhost:8080'}
        self.__registry_docker_image = registry_docker_image
        self.__other_docker_images = deepcopy(other_docker_images)
        self.__db_manager_cls = MockMongoManager if db_manager_cls is None else db_manager_cls
        self.__package_name = str(package_name) if package_name is not None else None
        self.maxDiff = None

    def run(self, result=None):
        """
        Runs a test using a freshly created MongoDB Docker container. The container is destroyed upon concluding
        the test.

        :param result: a TestResult object into which the test's result is collected.
        :return: the TestResult object.
        """
        _logger = logging.getLogger(__name__)
        with self._caplog.at_level(logging.DEBUG):
            with maybe_docker_is_not_running():
                with app_context(package_name=self.__package_name,
                                db_manager_cls=self.__db_manager_cls,
                                desktop_objects=self.__desktop_objects,
                                other_docker_images=list(
                                    self.__other_docker_images) if self.__other_docker_images is not None else None,
                                registry_docker_image=self.__registry_docker_image,
                                content=self._content,
                                wstl_builder_factory=wstl.builder_factory(self._wstl_package,
                                                                        href=self._href)) as (app, docker_container_ports):
                    self._docker_container_ports = docker_container_ports
                    self.__app = app
                    return super().run(result)


    async def get_application(self) -> Application:
        return self.__app

    def expected_one_id(self) -> str:
        """
        Gets the ID of the expected GET data.

        :return: an id string.
        :raises TypeError: if _expected_one is None.
        :raises StopIteration: if no suitable id could be found.
        """
        assert self._expected_one is not None, 'self._expected_one cannot be None'
        first_expected_one_data = self._expected_one[0]['collection']['items'][0]['data']
        return next(e.get('value') for e in first_expected_one_data if e['name'] == 'id' and e.get('value') is not None)

    def body_put_id(self) -> str:
        """
        Gets the ID of the target of a PUT request, determined by the value of the template ``_body_put``.

        :return: an id string.
        :raises TypeError: if _body_put is None.
        :raises StopIteration: if no suitable id could be found.
        """
        assert self._body_put is not None, 'self._body_put cannot be None'
        logging.getLogger(__name__).debug('Template is %s', self._body_put)
        return next(e.get('value') for e in self._body_put['template']['data'] if e['name'] == 'id' and e.get('value') is not None)


def get_test_case_cls_default(coll: str,
                              fixtures: Mapping[CollectionKey | str, list[DesktopObjectDict]],
                              duplicate_action_name: str | None = None,
                              db_manager_cls: Type[MicroserviceDatabaseManager] = MockMongoManager,
                              wstl_package: Optional[str] = None,
                              content: Mapping[CollectionKey | str, dict[str, bytes]] | None = None,
                              content_type: Optional[str] = None,
                              put_content_status: Optional[int] = None,
                              href: Optional[str | URL] = None,
                              get_actions: Optional[list[Action]] = None,
                              get_all_actions: Optional[list[Action]] = None,
                              expected_opener: Optional[Link] = None,
                              registry_docker_image: Optional[RegistryContainerConfig] = None,
                              other_docker_images: Iterable[DockerContainerConfig] | None = None,
                              port: Optional[int] = None,
                              sub = NONE_USER,
                              exclude: Optional[list[str]] = None,
                              duplicate_action_actions: list[Action] | None = None,
                              package_name: str | None = None,
                              context: PermissionContext | None = None) -> Type[MicroserviceTestCase]:
    """
    Create a test case class for testing a specific HEA microservice.

    :param coll: the name of the collection that the microservice uses (required).
    :param fixtures: HEA desktop objects to load into the database, as a map of collection keys ->
    list of desktop object dicts (required).
    :param duplicate_action_name: the name of the duplication action for this microservice (optional).
    :param db_manager_cls: the type of the database manager that will be used as the default for collection keys that
    are strings. Under typical circumstances, this should be used by the collection specified in coll. For Mongo unit
    tests, use MockMongoManager. For AWS unit tests, use MockS3ManagerWithMockMongo. For Mongo integration tests, use
    DockerMongoManager. For AWS integration tests, use MockS3Manager. Defaults to MockMongoManager.
    :param wstl_package: the name of the package containing the WeSTL data package, in standard module format
    (foo.bar).
    :param content: a mapping of collection keys -> HEA object IDs -> content that will be included with the
    objects inserted into the database. If None, objects will not have content.
    :param content_type: the MIME type of the content included with the objects (e.g., text/plain; charset=utf-8).
    Must be specified if content_type is specified.
    :param put_content_status: the expected HTTP response code for updating the content of the HEA object. Normally
    should be 204 if the content is updatable and 405 if not. Default is None, which will cause associated tests to be
    skipped.
    :param href: the resource being tested. If None, uses http://localhost:{port}/{coll}/, where {coll} is the
    collection name, and {port} is the port ultimately used by this test case.
    :param get_actions: the list of actions associated with the GET one route of the microservice.
    :param get_all_actions: the list of actions associated with the GET all route of the microservice.
    :param expected_opener: The expected URL of the resource that does the opening, including a list of HTML rel
    values.
    :param registry_docker_image: a RegistryContainerConfig for a Docker image of the HEA Registry Microservice. It
    will be launched once the MongoDB container is live. If the microservice depends on there being a registry, you
    should use testenv.MockRegistryContainerConfig for unit tests and dockermongo.RealRegistryContainerConfig for
    integration tests. Must be specified if other_docker_images is specified.
    :param other_docker_images: an iterable of DockerContainerConfigs for Docker images of other microservices. They
    will be launched once the MongoDB container is live.
    :param port: the port number to run aiohttp. If None, a random available port will be chosen.
    :param sub: the user from which the requests will be sent. It should be set to heaobject.user.TEST_USER for
    permissions testing. Defaults to heaobject.user.NONE_USER.
    :param exclude: a list of expected value names to exclude from test case class creation. Tests that need any
    expected value you specify here will be skipped.
    :param package_name: the service's distribution package name, used to register metadata about the running service
    with the registry service.
    :return: A test case class for testing the microservice.
    """
    if context is None:
        context = PermissionContext(sub)
    exclude_ = exclude if exclude is not None else []
    coll_ = coll if isinstance(coll, CollectionKey) else CollectionKey(name=coll, db_manager_cls=db_manager_cls)
    expected_values_ = {k: v for k, v in expected_values(fixtures, coll_, wstl.builder(package=wstl_package), context,
                                                         duplicate_action_name, href,
                                                         get_actions=get_actions,
                                                         get_all_actions=get_all_actions,
                                                         opener_link=expected_opener,
                                                         duplicate_action_actions=duplicate_action_actions,
                                                         exclude=exclude_,
                                                         sub=sub).items() if v is not None}

    class ExpectedValuesMicroserviceTestCase(MicroserviceTestCase):
        def __init__(self, methodName: str = 'runTest') -> None:
            super().__init__(package_name=package_name, coll=coll, desktop_objects=fixtures,
                             db_manager_cls=db_manager_cls,
                             wstl_package=wstl_package, href=href, content=content, content_type=content_type,
                             put_content_status=put_content_status, registry_docker_image=registry_docker_image,
                             other_docker_images=other_docker_images, port=port, sub=sub, methodName=methodName,
                             **expected_values_)

    return ExpectedValuesMicroserviceTestCase
