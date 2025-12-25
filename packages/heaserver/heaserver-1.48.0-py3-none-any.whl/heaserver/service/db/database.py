import abc
import asyncio
from abc import ABC, abstractmethod
from contextlib import AbstractAsyncContextManager, ExitStack, asynccontextmanager, contextmanager, AbstractContextManager
from types import TracebackType

from aiohttp import web
from typing import Any, Mapping, Optional, Type, TypeVar, Union, Protocol, Generic, Awaitable, runtime_checkable
from collections.abc import AsyncGenerator, Mapping, AsyncIterator, Sequence
from aiohttp.web import Request

from aiohttp.web_request import Request
from aiohttp.web_response import Response
from heaobject.keychain import Credentials, CredentialTypeVar, CredentialsView
from heaobject.volume import FileSystemTypeVar, FileSystem, Volume, NoFileSystem
from heaobject.root import DesktopObjectDict, DesktopObject, HEAObjectDict, PermissionContext
from heaobject.registry import Property
from yarl import URL
from multidict import istr, CIMultiDict, CIMultiDictProxy

from heaobject.user import NONE_USER

from heaserver.service.config import Configuration
from heaserver.service.util import to_type

from .. import client, response
from ..heaobjectsupport import type_to_resource_url, desktop_object_type_or_type_name_to_type
from ..oidcclaimhdrs import SUB
from ..util import modified_environ
from ..aiohttp import extract_sub
from cachetools import TTLCache
from copy import copy, deepcopy
import logging


_T = TypeVar('_T')


class NotStartedError(ValueError):

    def __init__(self, *args: object) -> None:
        super().__init__('The database is not running. Call start_database() first.', *args)

@runtime_checkable
class DatabaseConnection(Protocol):
    def close(self) -> None | Awaitable[None]:
        ...


DatabaseConnectionTypeVar = TypeVar('DatabaseConnectionTypeVar', bound=DatabaseConnection)

class Database(abc.ABC):
    """
    Connectivity to databases and other data storage systems for HEA microservices. The database object may be
    optionally configured by providing a Configuration object to the constructor. The Configuration class provides a
    similar structure to what is found in Windows INI files, including the use of section headers. Section headers
    should be prefixed by the Database subclass' full class name as produced by str(cls) to avoid name clashes.
    Properties in the Configuration object should be named using CamelCase. This class is not designed for multiple
    inheritance.
    """

    def __init__(self, config: Optional[Configuration], managed = False, request: web.Request | None = None, **kwargs) -> None:
        """
        Initializes the database object. Subclasses must call this constructor.

        :param config: Optional HEA configuration.
        :param managed: Whether this database instance is managed by a database manager.
        :param request: the HTTP request that is initializing this database instance, if any.
        """
        super().__init__(**kwargs)
        self.__managed = managed
        self.__request = request
        logger = logging.getLogger(__name__)
        if logger.getEffectiveLevel() == logging.DEBUG:
            logger.debug('Initialized %s database object', type(self))
        # Sub and volume_id -> file system and credentials. We include the sub to preserve permissions.
        self.__volume_id_to_file_system_and_credentials: TTLCache[tuple[str, str], tuple[FileSystem, Credentials | None]] = TTLCache(maxsize=128, ttl=30)

    @property
    @abstractmethod
    def file_system_type(self) -> type[FileSystem]:
        """The type of file system accessed by this database."""
        pass

    @classmethod
    def get_config_section(cls) -> str:
        """
        Gets this database type's section in the HEA configuration. By default, the section name is that produced by
        str(cls) in order to avoid name clashes. When overriding this method, take care not to construct a name that
        might clash with the current or future section header of another Database class.
        """
        return str(cls)

    async def get_file_system_and_credentials_from_volume(self, request: web.Request, volume_id: str) -> tuple[FileSystem, Credentials | None]:
        """
        Gets the file system and credentials for the given volume. It uses the registry microservice to access the
        file system and credentials microservices. Override this method to mock getting a file system and credentials.
        The results are cached.

        :param request: the aiohttp request (required).
        :param volume_id: a volume id string (required).
        :return: a tuple containing a FileSystem object and, if one exists, a Credentials object (or None if one does
        not).
        :raises ValueError: if no volume with that id exists, or no file system exists for the given volume.
        """
        sub = extract_sub(request)
        if (result := self.__volume_id_to_file_system_and_credentials.get((sub, volume_id))) is not None:
            return result
        else:
            result = await get_file_system_and_credentials_from_volume(request, volume_id, self.file_system_type)
            self.__volume_id_to_file_system_and_credentials[(sub, volume_id)] = result
            return result

    @abc.abstractmethod
    async def get_credentials_from_volume(self, request: web.Request, volume_id: str) -> Credentials | None:
        """
        Gets the volume's credentials. The results are cached.

        :param request: the HTTP request (required).
        :param volume_id: the volume id (required).
        :return a Credentials object, or None if no credentials were found.
        :raises ValueError: if no volume with that id exists.
        """
        pass

    async def get_volumes(self, request: Request, file_system_type_or_type_name: str | type[FileSystem],
                          account_ids: Sequence[str] | None = None) -> AsyncIterator[Volume]:
        """
        An async iterator of volumes of a given file system type. This implementation is identical to the module-level
        get_volumes() function.

        :param request: the HTTP request (required).
        :param file_system_type_or_type_name: the file system type or type name string (required).
        :raises ValueError: if no volume microservice is registered.
        :raises TypeError: if file_system_type_or_type_name is a type but not a FileSystem.
        """
        async for volume in get_volumes(request, file_system_type_or_type_name, account_ids=account_ids):
            yield volume

    async def is_creator(self, request: Request, for_type_or_type_name: str | type[DesktopObject]) -> bool:
        """
        Returns whether the current user may create new desktop objects of the given type. This method consults the
        registry service metadata to determine the user's create permissions.

        :param request: the HTTP request (required).
        :param for_type_or_type_name: the desktop object type or type name.
        :return: True or False.
        :raises ValueError: if an error occurred checking the registry service, or if the provided type is not
        registered in the heaserver-registry service.
        """
        if isinstance(for_type_or_type_name, type) and issubclass(for_type_or_type_name, DesktopObject):
            type_ = for_type_or_type_name.get_type_name()
        else:
            type_ = str(for_type_or_type_name)
        component = await client.get_component(request.app, type_)
        if component is None:
            raise ValueError(f'Could not find component for type {type_}')
        resource = component.get_resource(type_)
        if resource is None:
            raise ValueError(f'No resource found for type {type_}')
        return resource.is_creator_user(request.headers.get(SUB, NONE_USER))

    async def get_property(self, app: web.Application, name: str) -> Optional[Property]:
        """
        This is a wrapper function to be extended by tests
        Gets the Property with the given name from the HEA registry service.

        :param app: the aiohttp app.
        :param name: the property's name.
        :return: a Property instance or None (if not found).
        """
        return await client.get_property(app=app, name=name)


    def get_default_permission_context(self, request: Request) -> PermissionContext:
        """
        Gets the default permission context for the current user. This is used to determine whether the user has
        permission to perform a given action on a given object. The default implementation returns a PermissionContext
        instance, which checks a user's permissions against the owner and user share attributes of a desktop object but
        has no group checking.

        :param request: the HTTP request (required).
        :return: a PermissionContext object.
        """
        return PermissionContext(request.headers.get(SUB, NONE_USER))

    def really_close(self):
        """
        Cleans up all resources associated with the database connection. This method may be called multiple times. The
        default implementation does nothing.
        """
        pass

    def close(self):
        """Cleans up resources associated with database connections. This method may omit closing some clients, for
        example when it's more efficient to keep the client open for the lifetime of an application. When closing the
        application, call the really_close() method to close everything. The default implementation does nothing."""
        pass

    @property
    def managed(self) -> bool:
        """Whether this database instance is managed by a database manager."""
        return self.__managed

    @property
    def request(self) -> web.Request | None:
        """The HTTP request that initialized this database instance, if any."""
        return self.__request


class NoDatabase(Database):
    def __init__(self):
        super().__init__(None)

    @property
    def file_system_type(self) -> type[FileSystem]:
        return NoFileSystem

    async def get_credentials_from_volume(self, request: web.Request, volume_id: str) -> Credentials | None:
        return None

class InMemoryDatabase(Database, abc.ABC):
    """
    In-memory store of desktop objects and content.
    """

    def __init__(self, config: Optional[Configuration] = None,
                 desktop_objects: dict[str, list[DesktopObjectDict]] | None = None,
                 content: dict[str, dict[str, bytes]] | None = None,
                 **kwargs) -> None:
        """
        Initializes the in-memory database.

        :param config: a Configuration object.
        """
        super().__init__(config, **kwargs)
        if desktop_objects:
            self.__desktop_objects = dict(deepcopy(desktop_objects))
        else:
            self.__desktop_objects = {}
        if content:
            self.__content = dict(deepcopy(content))
        else:
            self.__content = {}

    def add_desktop_objects(self, data: Mapping[str, list[DesktopObjectDict]] | None):
        """
        Adds the given desktop objects to the given collection. If the collection does not exist, add that collection
        along with its objects.

        :param data: A dictionary whose keys are collections and whose contents are desktop objects
        """
        for coll, objs in (data or {}).items():
            if coll in self.__desktop_objects:
                self.__desktop_objects[coll].extend(deepcopy(objs))
            else:
                self.__desktop_objects.update({coll: deepcopy(objs)})

    def get_all_desktop_objects(self) -> dict[str, list[DesktopObjectDict]]:
        return deepcopy(self.__desktop_objects)

    def get_desktop_objects_by_collection(self, coll: str) -> list[DesktopObjectDict]:
        return deepcopy(self.__desktop_objects.get(coll, []))

    def get_desktop_object_by_collection_and_id(self, coll: str, id_: Optional[str]) -> Optional[DesktopObjectDict]:
        return deepcopy(next((d for d in self.__desktop_objects.get(coll, []) if d['id'] == id_), None))

    def update_desktop_object_by_collection_and_id(self, coll: str, id_: Optional[str],
                                                   new_value: DesktopObjectDict):
        """
        Updates the desktop object at the given location.

        :param coll: The collection in which the desktop object is located
        :param id_: The ID of the desktop object
        :param new_value: The new value of the desktop object
        """
        index = next((i for i, d in enumerate(self.__desktop_objects.get(coll, [])) if d['id'] == id_), None)
        if index is not None:
            self.__desktop_objects[coll][index] = new_value

    def remove_desktop_object_by_collection_and_id(self, coll: str, id_: Optional[str]):
        """
        Removes the desktop object (and its associated content) at the given location.

        :param coll: The collection in which the desktop object is located
        :param id_: The ID of the desktop object
        """
        index = next((i for i, d in enumerate(self.__desktop_objects.get(coll, [])) if d['id'] == id_), None)
        if index is not None:
            del self.__desktop_objects[coll][index]
            if coll in self.__content and id_ in self.__content[coll]:
                self.__content[coll].pop(id_)

    def add_content(self, content: Mapping[str, Mapping[str, bytes]] | None):
        """
        Adds the given content to the given collection. If there already is content for the object at the ID, replaces
        the content with new content.

        :param content: A dictionary whose keys are collections and whose values are dictionaries whose keys are the IDs
        of their corresponding desktop objects and whose values are the content
        """
        for coll, data in (content or {}).items():
            if coll in self.__content:
                self.__content[coll].update(dict(data))
            else:
                self.__content.update({coll: dict(data)})

    def get_all_content(self) -> dict[str, dict[str, bytes]]:
        return deepcopy(self.__content)

    def get_content_by_collection(self, coll: str) -> Optional[dict[str, bytes]]:
        return copy(self.__content.get(coll, None))

    def get_content_by_collection_and_id(self, coll: str, id_: str) -> Optional[bytes]:
        if (result := self.__content.get(coll, None)) is not None:
            return result.get(id_, None)
        else:
            return None


async def get_file_system_and_credentials_from_volume(request: Request, volume_id: str, file_system_type: type[FileSystemTypeVar]) -> tuple[FileSystemTypeVar, Credentials | None]:
    """
    Get the file system and credentials for the given volume.

    :param request: the aiohttp request (required).
    :param volume_id: a volume id string (required).
    :param file_system_type: the type of file system (required).
    :param credential_type: the type of credential (required).
    :return: a tuple containing a FileSystem object and, if one exists, a Credentials object (or None if one does not).
    :raise ValueError: if no volume with that id exists, no file system exists for the given volume, the volume's
    credentials were not found, or there was a problem accessing the registry service.
    """
    headers = {SUB: request.headers[SUB]} if SUB in request.headers else None
    (volume, _), fs_url = await asyncio.gather(_get_volume(request.app, volume_id, headers),
                                                        type_to_resource_url(request, FileSystem))
    if volume is None:
        raise ValueError(f'No volume with id {volume_id}')
    assert fs_url is not None, 'No file system service registered'
    file_system_type_ = desktop_object_type_or_type_name_to_type(volume.file_system_type)
    if file_system_type_ != file_system_type:
        raise ValueError("file_system_type does not match the volume's file system type")
    file_system_future = client.get(request.app,
                                   URL(fs_url) / 'bytype' / file_system_type.get_type_name() / 'byname' / volume.file_system_name,
                                   file_system_type,
                                   headers=headers)
    credentials_future = _get_credentials(request.app, volume, Credentials, headers)
    file_system, credentials = await asyncio.gather(file_system_future, credentials_future)
    if file_system is None:
        raise ValueError(f"Volume {volume.id}'s file system {volume.file_system_name} does not exist")
    return file_system, credentials


async def get_credentials_from_volume(request: Request, volume_id: str,
                                      credential_type: type[CredentialTypeVar]) -> CredentialTypeVar | None:
    """
    Get the credentials for the given volume.

    :param request: the aiohttp request (required).
    :param volume_id: a volume id string (required).
    :param credential_type: the type of credential (required).
    :return: a Credentials object (or None if one does not).
    :raise ValueError: if no volume with that id exists, no file system exists for the given volume, or the volumes's
    credentials were not found.
    """
    headers = {SUB: request.headers[SUB]} if SUB in request.headers else None
    volume, volume_url = await _get_volume(request.app, volume_id, headers)
    if volume is None:
        raise ValueError(f'No volume with id {volume_id}')
    if volume_url is None:
        raise ValueError(f'Volume {volume_id} has no URL')
    return await _get_credentials(request.app, volume, credential_type, headers)


async def has_volume(request: Request, volume_id: Optional[str] = None,
                     headers: Optional[Mapping[str, str]] = None) -> Response:
    if volume_id is None:
        if 'volume_id' in request.match_info:
            volume_id_ = request.match_info['volume_id']
        elif 'id' in request.match_info:
            volume_id_ = request.match_info['id']
        else:
            volume_id_ = None
    else:
        volume_id_ = volume_id
    if volume_id_ is not None:
        volume_url = await type_to_resource_url(request, Volume)
        volume = await client.get(request.app, URL(volume_url) / volume_id_, Volume, headers=headers)
        if volume is None:
            return response.status_not_found()
        return response.status_ok()
    else:
        return response.status_not_found()


async def get_volumes(request: Request, file_system_type_or_type_name: Union[str, type[FileSystem]],
                      account_ids: Sequence[str] | None = None) -> AsyncIterator[Volume]:
    """
    Gets the volumes accessible to the current user that have the provided filesystem type.

    :param request: the aiohttp request (required).
    :param file_system_type_or_type_name: the filesystem type or type name.
    :return: an async iterator of Volume objects.
    :raises ValueError: if no volume microservice is registered.
    :raises TypeError: if file_system_type_or_type_name is a type but not a FileSystem.
    """
    headers = {SUB: request.headers[SUB]} if SUB in request.headers else None
    volume_url = await type_to_resource_url(request, Volume)
    file_system_type_ = desktop_object_type_or_type_name_to_type(file_system_type_or_type_name)
    if not issubclass(file_system_type_, FileSystem):
        raise TypeError(f'Provided file_system_type_or_type_name is a {file_system_type_} not a FileSystem')
    get_volumes_url = URL(volume_url) / 'byfilesystemtype' / file_system_type_.get_type_name()
    if account_ids:
        query = [('account_id', account_id) for account_id in account_ids]
    else:
        query = None
    async for volume in client.get_all(request.app, get_volumes_url.with_query(query) if query else get_volumes_url, Volume, headers=headers):
        yield volume


async def get_options(request: Request, methods: list[str]):
    """
    Responds to an OPTIONS request. It calls the provided function, checks for the 200 status code, and if 200 is
    returned, returns a response with a 200 status code and an Allow header.

    :param request: the HTTP request (required).
    :param methods: a list of methods to include in the Allow header (required).
    :return: the HTTP response.
    """
    return await response.get_options(request, methods)


async def _get_volume(app: web.Application, volume_id: str, headers: Union[Mapping[Union[str, istr], str], CIMultiDict[str], CIMultiDictProxy[str], None] = None) -> tuple[Volume, str]:
    """
    Gets the volume with the provided id.

    :param app: the aiohttp app (required).
    :param volume_id: the id string of a volume.
    :param headers: any headers.
    :return: a two-tuple with either the Volume and its URL.
    :raise ValueError: if there is no volume with the provided volume id, or there was a problem accessing the registry
    service.
    """
    if volume_id is None:
        raise ValueError('volume_id cannot be None')
    volume_url = await client.get_resource_url(app, Volume)
    if volume_url is None:
        raise ValueError(f'No volume resource in the registry service')
    volume = await client.get(app, URL(volume_url) / volume_id, Volume, headers=headers)
    if volume is None:
        raise ValueError(f'No volume with volume_id={volume_id}')
    return volume, volume_url


async def _get_credentials(app: web.Application, volume: Volume, cred_type: type[CredentialTypeVar],
                           headers: Union[Mapping[Union[str, istr], str], CIMultiDict[str], CIMultiDictProxy[str], None] = None) -> CredentialTypeVar | None:
    """
    Gets a credential specified in the provided volume, or if there is none, a credential with the where attribute set
    to the volume's URL.

    :param app: the aiohttp app (required).
    :param volume: the Volume (required).
    :param volume_url: the volume's URL (required).
    :param cred_type: the volume's credential_type_name attribute value must be a subclass of the provided Credentials
    type.
    :param headers: any headers.
    :return: the Credentials, or None if the volume has no credentials.
    :raise ValueError: if the volume's credentials were not found, there was a problem accessing the registry
    service, or the type of credential associated with the volume is not equal to cred_type.
    """
    if volume.credentials_id is not None:
        creds_view_url = await client.get_resource_url(app, CredentialsView)
        if creds_view_url is None:
            raise ValueError('CredentialsView service not found')
        creds_view = await client.get(app, URL(creds_view_url) / volume.credentials_id, type_or_obj=CredentialsView,
                                      headers=headers)
        if creds_view is not None:
            assert creds_view.actual_object_type_name is not None, 'CredentialsView actual_object_type_name is None'
            if not issubclass(desktop_object_type_or_type_name_to_type(creds_view.actual_object_type_name), desktop_object_type_or_type_name_to_type(cred_type.get_type_name())):
                raise ValueError('CredentialsView actual_object_type_name is not a subclass of cred_type')
            creds_url = await client.get_resource_url(app, creds_view.actual_object_type_name)
            assert creds_url is not None, f'Credential service for type {creds_view.actual_object_type_name} not found'
            assert creds_view.actual_object_id is not None, 'CredentialsView actual_object_id is None'
            return await client.get(app, URL(creds_url) / creds_view.actual_object_id, cred_type, headers=headers)
        else:
            raise ValueError(f'Credential {volume.credentials_id} not found')
    else:
        return None


class DatabaseManager(ABC):
    """
    Abstract base class for database managers. These classes start a database, load data into it, return a Database
    object for manipulating the data, and delete the data. All subclasses of DatabaseManager must have a no-arg
    constructor, and they are expected to be immutable.
    """

    def __init__(self, config: Configuration | None = None):
        self.__started = False
        self.config = config
        self.__databases: list[Database] = []

    @property
    def config(self) -> Configuration | None:
        """
        Database configuration.
        """
        return self.__config

    @config.setter
    def config(self, config: Configuration | None):
        self.__config = config

    def start_database(self, context_manager: ExitStack) -> None:
        """
        Starts the database. The provided context manager will destroy the database automatically. Override this
        method to start a database, such as in a docker container. Place the super() call after the database is
        already started.

        :param context_manager: a context manager for creating and destroying the database (required).
        :raises heaserver.service.error.DatabaseStartException: if the database fails to start.
        """
        self.__started = True

    @property
    def started(self) -> bool:
        return self.__started

    def get_env_vars(self, ) -> dict[str, str]:
        """
        Gets environment variables to connect to this database. This default implementation
        returns an empty dict. This method may only be called after the start_database() method. Override this method
        to return a dictionary of environment variable name-value pairs.

        :return: a str->str dict.
        """
        return {}

    def get_config_file_section(self) -> str:
        """
        Creates a HEA configuration file section for connecting to this database. This default implementation returns
        an empty string. This method may only be called after the start_database() method.

        :return: a string.
        """
        return ''

    @abstractmethod
    def insert_all(self, desktop_objects: Optional[dict['CollectionKey', list[DesktopObjectDict]]],
                   content: Optional[dict['CollectionKey', dict[str, bytes]]]):
        """
        Inserts all data and content. Failure may put the object in an inconsistent state where one is properly
        inserted but the other is not. This method is not designed to be overridden.

        :raises KeyError: if an unexpected key was found in the data or the content.
        """
        pass

    @abstractmethod
    def delete_all(self):
        pass

    def close(self):
        """
        Removes all data and content, and cleans up any other resources created by other methods of this object. This
        method is not designed to be overridden. This method may be called multiple times.
        """
        if self.started:
            try:
                self.delete_all()
            finally:
                try:
                    exceptions = []
                    while self.__databases:
                        try:
                            self.__databases.pop().really_close()
                        except Exception as e:
                            exceptions.append(e)
                finally:
                    if exceptions:
                        raise exceptions[0]  # Use exception groups in Python 3.11.

    @classmethod
    def get_environment_to_remove(cls) -> list[str]:
        """
        Gets any environment variables that need to be removed temporarily for the database.

        :return: a list of environment variable names, or the empty list.
        """
        return []

    @classmethod
    def get_environment_updates(cls) -> dict[str, str]:
        """
        Gets a newly created dict with any environment variables that are needed by the database.

        :return: environment variable name -> value dict, or the empty dict if no environment variables are needed.
        """
        return {}

    @classmethod
    @contextmanager
    def environment(cls):
        with modified_environ(*cls.get_environment_to_remove(), **cls.get_environment_updates()):
            yield

    @classmethod
    def get_context(cls) -> list[AbstractContextManager]:
        """
        Gets a newly created list of context managers, or the empty list if there are none. This method is called by
        the context() context manager, which instantiates any context managers in the list.
        """
        return []

    @classmethod
    @contextmanager
    def context(cls):
        with ExitStack() as stack:
            for context_ in cls.get_context():
                stack.enter_context(context_)
            yield

    @classmethod
    @abstractmethod
    def database_types(self) -> list[str]:
        pass

    @abstractmethod
    def get_database(self) -> Database:
        """
        Gets a database object to perform queries. This object's close() method must be called when you are done with
        it. Accessing the object via the database() context manager causes it to be closed automatically. Concrete
        subclasses must implement this method. Assumes the database is already started.

        :return: the database object.
        """
        pass

    @asynccontextmanager
    async def database(self) -> AsyncGenerator[Database, None]:
        """
        Context manager that creates the corresponding Database object.
        Override this method to return a Database instance. The database object
        will be closed automatically.

        :return: the database object.
        """
        db = self.get_database()
        if db is None:
            raise ValueError('The database is not running. Did you call start_database()?')
        try:
            yield db
        finally:
            await asyncio.to_thread(db.really_close)

class MicroserviceDatabaseManager(DatabaseManager, ABC):
    """
    Abstract base class for database managers. These classes start a database, load data into it, return a Database
    object for manipulating the data, and delete the data. All subclasses of TestDatabaseManager must have a no-arg
    constructor, and they are expected to be immutable.
    """

    def insert_desktop_objects(self, desktop_objects: Optional[Mapping['CollectionKey', Sequence[DesktopObjectDict]]]):
        """
        Inserts data into the database. The start_database() method must be called before calling this method. The
        default implementation does nothing and is expected to be overridden with an implementation for a specific
        database technology. Implementations should anticipate multiple inheritance. Call super(), and do not pass
        desktop object collections that are handled by this collection into the superclass' implementation.

        :param desktop_objects: a dict of collection -> list of desktop object dicts. Required.
        :raises KeyError: if an unexpected key was found in the data.
        """
        if not self.started:
            raise NotStartedError

    def insert_content(self, content: Optional[Mapping['CollectionKey', Mapping[str, bytes]]]):
        """
        Inserts content into the database. The start_database() method must be called before calling this method.
        The default implementation does nothing and is expected to be overridden with an implementation for a specific
        database technology. Implementations should anticipate multiple inheritance. Call super(), and do not pass
        content collections that are handled by this collection into the superclass' implementation.

        :param content: a dict of collection -> dict of desktop object id -> content. Required.
        :raises KeyError: if an unexpected key was found in the content.
        """
        if not self.started:
            raise NotStartedError

    def insert_all(self, desktop_objects: Optional[Mapping['CollectionKey', Sequence[DesktopObjectDict]]],
                   content: Optional[Mapping['CollectionKey', Mapping[str, bytes]]]):
        """
        Inserts all data and content. Failure may put the object in an inconsistent state where one is properly
        inserted but the other is not. This method is not designed to be overridden.

        :raises KeyError: if an unexpected key was found in the data or the content.
        """
        self.insert_desktop_objects(desktop_objects)
        self.insert_content(content)

    def delete_desktop_objects(self):
        """
        Deletes data from the database. The start_database() method must be called before calling this method. This
        should support being called multiple times, and after the first time have no effect. Override this method to
        delete the provided desktop objects from the database.

        :raises KeyError: if an unexpected key was found in the data.
        """
        if not self.started:
            raise NotStartedError

    def delete_content(self):
        """
        Deletes content from the database. The start_database() method must be called before calling this method. This
        should support being called multiple times, and after the first time have no effect. Override this method to
        delete the provided content from the database.

        :raises KeyError: if an unexpected key was found in the content.
        """
        if not self.started:
            raise NotStartedError

    def delete_all(self):
        try:
            self.delete_desktop_objects()
        finally:
            self.delete_content()


class DatabaseContextManager(Generic[DatabaseConnectionTypeVar, CredentialTypeVar], AbstractAsyncContextManager[DatabaseConnectionTypeVar], ABC):
    """
    Abstract base class for creating context managers for HEA database connections. This generic class is parameterized by: the
    DatabaseConnectionTypeVar, a database connection object; and the CredentialTypeVar, a Credentials object.
    """

    def __init__(self, request: Request, volume_id: str | None = None, credentials: CredentialTypeVar | None = None) -> None:
        """
        Create the context manager.

        :param request: the HTTP request (required).
        :param volume_id: optional volume id. Subclasses may require that you either provide a volume id or a
        credentials object.
        :param credentials: optional credentials object. Subclasses may require that you provide a volume id or a
        credentials object. The credentials object may be updated by this context manager, for example, if an access
        token was updated.
        """
        if request is None:
            raise ValueError('Request cannot be None')
        if not isinstance(request, Request):
            raise ValueError(f'request {request} must be a Request')
        self.__request = request
        self.__volume_id = str(volume_id) if volume_id is not None else None
        self.__credentials = credentials  # intentionally not deep-copied so that updates are picked up.

    async def __aenter__(self) -> DatabaseConnectionTypeVar:
        """
        Gets/creates and returns a database connection.
        """
        self.__connection = await self.connection()
        return self.__connection

    async def __aexit__(self, exc_type: type[BaseException] | None,
                        exc_value: BaseException | None,
                        traceback: TracebackType | None) -> None:
        """
        Closes or releases the connection and returns None, permitting the exceptions to be raised on exit.

        :param exc_type: the type of exception thrown in the context body, if any.
        :param exc_value: the exception itself, if any.
        :param traceback: the traceback, if any.
        """
        self.__connection.close()

    @abstractmethod
    async def connection(self) -> DatabaseConnectionTypeVar:
        """Returns a new database connection."""
        pass

    @property
    def request(self) -> Request:
        return self.__request

    @property
    def volume_id(self) -> str | None:
        return self.__volume_id

    @property
    def credentials(self) -> CredentialTypeVar | None:
        return self.__credentials   # intentionally not deep-copied so that updates are picked up.


class NoDatabaseManager(MicroserviceDatabaseManager):
    def get_database(self) -> Database:
        return NoDatabase()

    @classmethod
    def database_types(self) -> list[str]:
        return ['system|nodatabase']


class CollectionKey:
    """
    A key to a collection that contains its name and relevant database manager class. CollectionKeys should only ever
    be used in testing environments.
    """

    def __init__(self, *, name: str | None,
                 db_manager_cls: type[MicroserviceDatabaseManager] | None = None):
        """
        Creates a collection key with a provided name and a database manager class.

        :param name: The name of the collection. If None, the key refers to any collection relevant to the given
        database manager. Required (keyword-only).
        :param db_manager_cls: A MicroserviceDatabaseManager type to which the collection is relevant. Defaults to
        MicroserviceDatabaseManager (keyword-only).
        """
        if db_manager_cls is not None and not issubclass(db_manager_cls, MicroserviceDatabaseManager):
            raise TypeError(
                f'db_manager_cls has incorrect type: expected {MicroserviceDatabaseManager}, was {db_manager_cls}')
        self.__name = str(name) if name is not None else None
        self.__db_manager_cls = db_manager_cls

    @property
    def name(self) -> str | None:
        """
        The collection key's name.
        """
        return self.__name

    @property
    def db_manager_cls(self) -> type[MicroserviceDatabaseManager] | None:
        """
        The collection key's database manager class. The default value is MicroserviceDatabaseManager.
        """
        return self.__db_manager_cls

    def matches(self, other: 'str | CollectionKey',
                default_db_manager_cls: Type[MicroserviceDatabaseManager] | None = None) -> bool:
        """
        Determines if the collection represented by this CollectionKey is represented by a part or entirety of the
        other string or CollectionKey. Since all DatabaseManagers inherit relevant collections from their superclasses,
        the database manager of the other collection key may be a subclass of the DatabaseManager class stored with
        this CollectionKey.

        :param other: the other collection key, as either a string or CollectionKey (required).
        :param default_db_manager_cls: if other is a string, then this database manager class is used as the
        database manager class for the other collection key. Defaults to DatabaseManager (i.e. match
        any DatabaseManager).
        :return: True if the other collection key matches this one, otherwise False.
        """
        if isinstance(other, CollectionKey):
            other_ = other
        else:
            other_ = CollectionKey(name=str(other), db_manager_cls=default_db_manager_cls)

        return (self.name == other_.name if (self.name is not None and other_.name is not None) else True) \
               and (self.db_manager_cls is None or \
                    other_.db_manager_cls is None or \
                    bool(set(self.db_manager_cls.database_types()).intersection(other_.db_manager_cls.database_types())))

    def __repr__(self):
        return f'CollectionKey(name={self.name}, db_manager_cls={self.db_manager_cls})'


FixtureKeyTypes = TypeVar('FixtureKeyTypes', CollectionKey, str, CollectionKey | str)


def query_fixtures(fixtures: Mapping[FixtureKeyTypes, Sequence[DesktopObjectDict]] | None,
                   default_db_manager: MicroserviceDatabaseManager | Type[MicroserviceDatabaseManager] | None = None,
                   strict=False, *,
                   name: str | None = None,
                   db_manager: MicroserviceDatabaseManager | Type[MicroserviceDatabaseManager] | None = None,
                   key: FixtureKeyTypes | None = None) -> dict[str | None, list[DesktopObjectDict]]:
    """
    Query a dictionary of fixtures by collection.

    :param fixtures: The fixtures to query. If the key to a collection is a string, then the database manager class
    will be assumed to be default_db_manager. If None, returns the empty dictionary. Required.
    :param default_db_manager: The database manager to use if the collection key is a string. Defaults to DatabaseManager.
    :param strict: If True, raises KeyError if nothing is found. If False, an empty dictionary is returned. Defaults
    to False.
    :param name: If specified, the name of the collection must match the given name.
    :param db_manager: If specified, the database manager of the collection must be the given database manager, its
    class if it is an instance of a database manager, or a subclass.
    :param key: If specified, the name and database manager class must match those stored in the CollectionKey if
    key is a CollectionKey. If key is a string, it is the same as specifying name. Both name and db_manager are
    ignored if this argument is specified.
    :return: All the collections and their data that matches the given query parameters. Any CollectionKeys in the
    keys of the given fixtures are replaced with their names if key is either not specified or not a CollectionKey.
    """
    default_db_manager_ = to_type(default_db_manager)
    if db_manager is None:
        db_manager_ = default_db_manager_
    else:
        db_manager_ = to_type(db_manager)
    if not fixtures:
        return {}

    key_ = key if isinstance(key, CollectionKey) else CollectionKey(name=str(key) if key is not None else None)
    coll_key = key_ if key else CollectionKey(name=str(name) if name is not None else None, db_manager_cls=db_manager_)
    result = {(coll.name if isinstance(coll, CollectionKey) else coll): list(data)
              for coll, data in fixtures.items() if coll_key.matches(coll, default_db_manager_cls=default_db_manager_)}

    if result:
        return result
    elif strict:
        raise KeyError(f'query result is empty: {key_}')
    else:
        return {}


def query_fixture_collection(fixtures: Mapping[FixtureKeyTypes, list[DesktopObjectDict]],
                             key: FixtureKeyTypes,
                             default_db_manager: MicroserviceDatabaseManager | Type[MicroserviceDatabaseManager] | None = None,
                             strict=True) -> list[DesktopObjectDict]:
    """
    Get the collection with the given key.

    :param fixtures: The fixtures to query. Required.
    :param key: The name and database manager class must match those stored in the CollectionKey if
    key is a CollectionKey. If key is a string, then the database manager class is assumed to be default_db_manager.
    :param default_db_manager: The database manager to if the collection key is a string. Defaults to DatabaseManager.
    :param strict: If True, raises KeyError if nothing is found. If False, returns None if nothing is found. Defaults
    to True.
    :return: The objects in the collection that match with the given key, or the empty list if none do.
    """
    if fixtures is None:
        raise TypeError('fixtures may not be None')
    if isinstance(key, CollectionKey) and key.name is None:
        raise TypeError('the name of the CollectionKey may not be None when used as a parameter to '
                        'query_fixture_collection')
    result = query_fixtures(fixtures, default_db_manager=default_db_manager, strict=strict, key=key)
    if not result:
        return []
    else:
        return result[key.name if isinstance(key, CollectionKey) else key]


def query_content(content: Mapping[FixtureKeyTypes, Mapping[str, bytes]] | None,
                  default_db_manager: MicroserviceDatabaseManager | Type[MicroserviceDatabaseManager] | None = None,
                  strict=False, *,
                  name: str | None = None,
                  db_manager: MicroserviceDatabaseManager | Type[MicroserviceDatabaseManager] | None = None,
                  key: FixtureKeyTypes | None = None) -> dict[str | None, dict[str, bytes]]:
    """
    Query a dictionary of content by collection.

    :param content: The content dictionary to query. If the key to a collection is a string, then the database manager
    class will be assumed to be default_db_manager. If None, returns the empty dictionary. Required.
    :param default_db_manager: The database manager to use if the collection key is a string. Defaults to
    DatabaseManager.
    :param strict: If True, raises KeyError if nothing is found. If False, an empty dictionary is returned. Defaults
    to False.
    :param name: If specified, the name of the collection must match the given name.
    :param db_manager: If specified, the database manager of the collection must be the given database manager, its
    class if it is an instance of a database manager, or a subclass.
    :param key: If specified, the name and database manager class must match those stored in the CollectionKey if
    key is a CollectionKey. If key is a string, it is the same as specifying name. Both name and db_manager are
    ignored if this argument is specified.
    :return: All the collections and their content that matches the given query parameters. Any CollectionKeys in the
    keys of the given content dictionary are replaced with their names.
    """
    default_db_manager_ = to_type(default_db_manager)
    if db_manager is None:
        db_manager_ = default_db_manager_
    else:
        db_manager_ = to_type(db_manager)
    if not content:
        return {}
    key_ = key if isinstance(key, CollectionKey) else CollectionKey(name=str(key) if key is not None else None)
    if db_manager is None:
        db_manager_ = default_db_manager if isinstance(default_db_manager, type) or default_db_manager is None else type(default_db_manager)
    else:
        db_manager_ = db_manager if isinstance(db_manager, type) else type(db_manager)
    coll_key = key_ if key else CollectionKey(name=str(name) if name is not None else None, db_manager_cls=db_manager_)
    result = {(coll.name if isinstance(coll, CollectionKey) else str(coll)): dict(data)
              for coll, data in content.items() if coll_key.matches(coll)}
    if result:
        return result
    elif strict:
        raise KeyError('query result is empty')
    else:
        return {}


def query_content_collection(content: dict[FixtureKeyTypes, dict[str, bytes]] | None,
                             key: FixtureKeyTypes,
                             default_db_manager: MicroserviceDatabaseManager | type[MicroserviceDatabaseManager] | None = None,
                             strict=True) -> dict[str, bytes] | None:
    """
    Get the collection with the given key.

    :param content: The content dictionary to query. If None, returns the empty dictionary. Required.
    :param key: The name and database manager class must match those stored in the CollectionKey if
    key is a CollectionKey. If key is a string, then the database manager class is assumed to be default_db_manager.
    :param default_db_manager: The database manager to use if the collection key is a string. Defaults to
    DatabaseManager.
    :param strict: If True, raises KeyError if nothing is found. If False, returns None if nothing is found. Defaults
    to True.
    :return: The content in the collection that matches with the given key.
    """
    if content is None:
        raise TypeError('content may not be None')
    else:
        if isinstance(key, CollectionKey) and key.name is None:
            raise TypeError('the name of the CollectionKey may not be None when used as a parameter to '
                            'query_fixture_collection')
        result = query_content(content, default_db_manager=default_db_manager, strict=strict, key=key)
        if not result:
            return None
        elif isinstance(key, CollectionKey):
            return result[key.name]
        else:
            return result[key]


def simplify_collection_keys(collections: Mapping[FixtureKeyTypes, _T]) -> dict[str | None, _T]:
    """
    Convert all CollectionKeys in the given collection dictionary to strings that are equal to their names.
    """
    return {(coll_key.name if isinstance(coll_key, CollectionKey) else coll_key): objs
            for coll_key, objs in collections.items()}


def validate_collection_keys(collections: Mapping[FixtureKeyTypes, Any]):
    """
    Raises a TypeError if the provided collections' keys are not either all-strings or all-CollectionKeys.
    """
    if not all(isinstance(key_name, str) for key_name in collections.keys()) and not all(
        isinstance(key, CollectionKey) for key in collections.keys()):
        raise TypeError(
            f'collections must have either all-string or all-CollectionKey keys, but actually has {set(type(k) for k in collections.keys())}')


def convert_to_collection_keys(collections: Mapping[FixtureKeyTypes, _T],
                               default_db_manager: MicroserviceDatabaseManager | type[MicroserviceDatabaseManager] | None = None) \
    -> dict[CollectionKey, _T]:
    """
    Creates a new collection dictionary with all string keys converted to CollectionKeys with the given default
    database manager. This acts like a shallow copy, i.e., the dictionary's values are not copied.

    :param collections: any mapping with either all-string or all-CollectionKey keys (required).
    :param default_db_manager: the MicroserviceDatabaseManager to use for converting the string keys (optional).
    :return: a dictionary of CollectionKey -> the same values as in collections.
    """
    if default_db_manager is None or isinstance(default_db_manager, type):
        db_manager = default_db_manager
    else:
        db_manager = type(default_db_manager)
    result: dict[CollectionKey, _T] = {}
    for key, objs in collections.items():
        if isinstance(key, CollectionKey):
            key_: CollectionKey = key
        else:
            key_ = CollectionKey(name=key, db_manager_cls=db_manager)
        result[key_] = objs
    return result


def get_collection_key_from_name(collections: Mapping[CollectionKey, Any], name: str) -> CollectionKey | None:
    """
    Get the key to access the collection with the given name. If there are multiple collections with the same name,
    behavior is undefined because this should never happen. If there is no collection with the name, return None.
    """
    return next(iter([x for x in collections.keys() if x.name == name]), None)


def get_collection_from_name(collections: Mapping[str, Any] | Mapping[CollectionKey, Any],
                             name: str) -> str | CollectionKey | None:
    """
    Get the key to access the collection with the given name. If there are multiple collections with the same name,
    behavior is undefined because this should never happen. If there is no collection with the name, return None.
    """
    return next(iter([x for x in collections.keys() if (x.name if isinstance(x, CollectionKey) else str(x)) == name]),
                None)
