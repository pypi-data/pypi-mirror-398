"""
Convenience functions for handling HEAObjects.
"""

from heaserver.service.util import LockManager
from . import client
from .representor import factory as representor_factory
from .representor.error import ParseException
from heaobject.root import HEAObject, DesktopObjectTypeVar, DesktopObjectDict, DesktopObject, \
    desktop_object_type_for_name, Permission, DefaultPermissionGroup, PermissionContext, EnumWithAttrs
from heaobject.user import is_system_user, SYSTEM_USERS
from heaobject.person import encode_group
from heaobject.error import DeserializeException
from heaobject.person import Person, Group
from heaserver.service.oidcclaimhdrs import SUB
from aiohttp import web
import logging
from typing import Union, Optional, Type
from collections.abc import Sequence, Mapping, AsyncIterator, Iterable
from yarl import URL
from asyncio import Lock


class RESTPermissionGroup(EnumWithAttrs):
    """
    Enum that maps heaobject's root.Permission enum values to get, post, put, and delete REST API calls. These are
    aliases to the heaobject package's heaobject.root.PermissionGroup enum.

    In order to execute a GET request for an object, the user must have at least one of the permissions in the
    GETTER_PERMS permission group (VIEWER, COOWNER, or EDITOR) for the object. GETTER_PERMS is an alias to heaobject's
    ACCESSOR_PERMS.

    In order to execute a POST request to create an object, the user must have at least one of the permissions in the
    POSTER_PERMS permission group (CREATOR, COOWNER) for the container in which the object will be created.
    POSTER_PERMS is an alias to heaobject's CREATOR_PERMS.

    In order to execute a PUT request to update an object, the user must have at least one of the permissions in the
    PUTTER_PERMS permission group (EDITOR, COOWNER) for the object. PUTTER_PERMS is an alias to heaobject's
    UPDATER_PERMS.

    In order to execute a DELETE request to delete an object, the user must have at least one of the permissions in the
    DELETER_PERMS permission group (DELETER, COOWNER) for the object. DELETER_PERMS is an alias to heaobject's
    DETETER_PERMS.
    """

    GETTER_PERMS = DefaultPermissionGroup.ACCESSOR_PERMS.perms
    PUTTER_PERMS = DefaultPermissionGroup.UPDATER_PERMS.perms
    POSTER_PERMS = DefaultPermissionGroup.CREATOR_PERMS.perms
    DELETER_PERMS = DefaultPermissionGroup.DELETER_PERMS.perms

    def __init__(self, perms: Iterable[Permission]):
        self.__perms = list(perms)

    @property
    def perms(self) -> list[Permission]:
        """
        The permissions that are part of the group.
        """
        return list(self.__perms)

    def get_perms_as_strs(self) -> list[str]:
        """
        Returns the permissions in the group as strings.
        """
        return list(perm.name for perm in self.__perms)

    async def has_any(self, obj: DesktopObject, context: PermissionContext) -> bool:
        """
        Returns whether the object has any of the permissions in this group.

        :param: obj: a desktop object (required).
        :param: context: the permission context (required).
        :return: True or False.
        """
        return await obj.has_permissions(self.__perms, context)

    def __contains__(self, item: Permission) -> bool:
        """
        Checks if the given permission is in the group.
        """
        return item in self.__perms


async def new_heaobject_from_type_name(request: web.Request, type_name: str) -> DesktopObject:
    """
    Creates a new HEA desktop object of the given type and populates its
    attributes from the body of a HTTP request. The form field names are
    assumed to correspond to attributes of the desktop object, and the
    attributes are set to the values in the form in order of appearance in the
    request. If the object's owner is None or no owner property was provided,
    the owner is set to the current user.

    :param request: the HTTP request.
    :param type_name: the type name of DesktopObject.
    :return: an instance of the given DesktopObject type. It is compared to the
    type of the HEA desktop object in the request body, and a
    DeserializeException is raised if the type of the HEA object is not an
    instance of this type. If the desktop object in the body has no type
    attribute, a DeserializeException is raised.
    :return: an instance of the given DesktopObject type.
    :raises DeserializeException: if creating a HEA object from the request
    body's contents failed.
    """
    _logger = logging.getLogger(__name__)
    obj = desktop_object_type_for_name(type_name)()
    return await populate_heaobject(request, obj)


async def new_heaobject_from_type(request: web.Request, type_: Type[DesktopObjectTypeVar]) -> DesktopObjectTypeVar:
    """
    Creates a new HEA desktop object of the given type and populates its
    attributes from the body of a HTTP request. The form field names are
    assumed to correspond to attributes of the desktop object, and the
    attributes are set to the values in the form in order of appearance in the
    request. If the object's owner is None or no owner property was provided,
    the owner is set to the current user.

    :param request: the HTTP request.
    :param type_: A DesktopObject type. It is compared to the type of the HEA
    desktop object in the request body, and a DeserializeException is raised if
    the type of the HEA object is not an instance of this type. If the desktop
    object in the body has no type attribute, a DeserializeException is raised.
    :return: an instance of the given DesktopObject type.
    :raises DeserializeException: if creating a HEA object from the request
    body's contents failed.
    """
    _logger = logging.getLogger(__name__)
    try:
        representor = representor_factory.from_content_type_header(request.headers['Content-Type'])
        _logger.debug('Using %s input parser', representor)
        result = await representor.parse(request)
        _logger.debug('Got dict %s', result)
        if 'type' not in result:
            raise KeyError("'type' not specified in request body. All types must be specified explicitly in the "
                           "body of the request.")
        actual_type = desktop_object_type_for_name(result['type'])
        if not issubclass(actual_type, type_):
            raise TypeError(f'Type of object in request body must be type {type_} but was {actual_type}')
        if result.get('owner', None) is None:
            result['owner'] = request.headers.get(SUB, None)
        obj = actual_type()
        obj.from_dict(result)
        return obj
    except ParseException as e:
        raise DeserializeException(str(e)) from e
    except (ValueError, TypeError) as e:
        raise DeserializeException(str(e)) from e
    except KeyError as e:
        raise DeserializeException(str(e)) from e
    except Exception as e:
        raise DeserializeException(str(e)) from e


async def populate_heaobject(request: web.Request, obj: DesktopObjectTypeVar) -> DesktopObjectTypeVar:
    """
    Populate an HEA desktop object from a POST or PUT HTTP request.

    :param request: the HTTP request. Required.
    :param obj: the HEAObject instance. Required.
    :return: the populated object.
    :raises DeserializeException: if creating a HEA object from the request body's contents failed.
    """
    _logger = logging.getLogger(__name__)
    try:
        representor = representor_factory.from_content_type_header(request.headers['Content-Type'])
        _logger.debug('Using %s input parser', representor)
        result = await representor.parse(request)
        _logger.debug('Got dict %s', result)
        obj.from_dict(result)
        return obj
    except (ParseException, ValueError) as e:
        _logger.exception('Failed to parse %s%s', obj, e)
        raise DeserializeException from e
    except Exception as e:
        _logger.exception('Got exception %s', e)
        raise DeserializeException from e


async def type_to_resource_url(request: web.Request, type_or_type_name: Union[str, Type[DesktopObject]],
                               parameters: Optional[Mapping[str, Union[Sequence[Union[int, float, complex, str]], Mapping[str, Union[int, float, complex, str]], tuple[str, Union[int, float, complex, str]], int, float, complex, str]]] = None,
                               **kwargs: Union[Sequence[Union[int, float, complex, str]], Mapping[str, Union[int, float, complex, str]], tuple[str, Union[int, float, complex, str]], int, float, complex, str]) -> str:
    """
    Use the HEA registry service to get the resource URL for accessing HEA objects of the given type. The result is
    cached to avoid unnecessary service calls.

    :param request: the HTTP request. Required.
    :param type_or_type_name: the type or type name of HEA desktop object. Required.
    :param parameters: for resource URLs with a URI template, the template parameters.
    :return: the URL string.
    :raises ValueError: if no resource URL was found in the registry or there was a problem accesing the registry
    service.
    """
    result = await client.get_resource_url(request.app, type_or_type_name, client_session=None, parameters=parameters, **kwargs)
    if result is None:
        raise ValueError(f'No resource in the registry for type {type_or_type_name}')
    return result


async def get_dict(request: web.Request, id_: str, type_or_type_name: Union[str, Type[DesktopObject]],
                   headers: Optional[Mapping[str, str]] = None) -> Optional[DesktopObjectDict]:
    """
    Gets the HEA desktop object dict with the provided id from the service for the given type, file system type,
    and file system name.

    :param request: the aiohttp request (required).
    :param id_: the id of the HEA desktop object of interest.
    :param type_or_type_name: the desktop object type or type name.
    :param headers: optional HTTP headers to use.
    :return: the requested HEA desktop object dict, or None if not found.
    :raises ValueError: if no appropriate service was found or there was a problem accessing the registry service.
    """
    url = await type_to_resource_url(request, type_or_type_name=type_or_type_name)
    return await client.get_dict(request.app, URL(url) / id_, headers)


async def get(request: web.Request, id_: str, type_: Type[DesktopObjectTypeVar],
              headers: Optional[Mapping[str, str]] = None) -> Optional[DesktopObjectTypeVar]:
    """
    Gets the HEA desktop object with the provided id from the service for the given type, file system type, and file
    system name.

    :param request: the aiohttp request (required).
    :param id_: the id of the HEA desktop object of interest.
    :param type_: the desktop object type.
    :param headers: optional HTTP headers to use.
    :return: the requested HEA desktop object, or None if not found.
    :raises ValueError: if no appropriate service was found or there was a problem accessing the registry service.
    """
    url = await type_to_resource_url(request, type_or_type_name=type_)

    return await client.get(request.app, URL(url) / id_, type_, headers)


async def get_all(request: web.Request, type_: Type[DesktopObjectTypeVar],
                  headers: Optional[Mapping[str, str]] = None) -> AsyncIterator[DesktopObjectTypeVar]:
    """
    Async iterator for all HEA desktop objects from the service for the given type, file system type, and file system
    name.

    :param request: the aiohttp request (required).
    :param type_: the desktop object type.
    :param headers: optional HTTP headers to use.
    :return: an async iterator with the requested desktop objects.
    :raises ValueError: if no appropriate service was found or there was a problem accessing the registry service.
    """
    url = await type_to_resource_url(request, type_or_type_name=type_)

    return client.get_all(request.app, url, type_, headers)


def desktop_object_type_or_type_name_to_type(type_or_type_name: str | type[DesktopObject], default_type: type[DesktopObject] | None = None) -> type[DesktopObject]:
    """
    Takes a variable that may contain either a DesktopObject type or type name, and return a type. If a type is passed
    in, and it is a subclass of DesktopObject, it will be returned as-is. If a type name is passed in, its corresponding
    type will be returned if the type is a subclass of DesktopObject.

    :param type_or_type_name: the type or type name. Required.
    :param default_type: what to return if type_or_type_name is None. If omitted, None is returned.
    """
    if default_type is not None and not issubclass(default_type, DesktopObject):
        raise TypeError('default_type is defined and not a DesktopObject')
    if isinstance(type_or_type_name, type):
        if not issubclass(type_or_type_name, DesktopObject):
            raise TypeError(f'type_or_type_name not a DesktopObject')
        if issubclass(type_or_type_name, DesktopObject):
            result_ = type_or_type_name
        else:
            raise TypeError('type_or_type_name not a DesktopObject')
    else:
        file_system_type_ = desktop_object_type_for_name(type_or_type_name)
        if not issubclass(file_system_type_, DesktopObject):
            raise TypeError(f'file_system_type_or_type_name is a {file_system_type_} not a DesktopObject')
        else:
            result_ = file_system_type_
    if result_ is None:
        return default_type
    else:
        return result_


def type_or_type_name_to_type(type_or_type_name: str | type[HEAObject], default_type: type[HEAObject] | None = None) -> type[HEAObject]:
    """
    Takes a variable that may contain either a HEAObject type or type name, and return a type. If a type is passed
    in, and it is a subclass of HEAObject, it will be returned as-is. If a type name is passed in, its corresponding
    type will be returned if the type is a subclass of HEAObject.

    :param type_or_type_name: the type or type name. Required.
    :param default_type: what to return if type_or_type_name is None. If omitted, None is returned.
    """
    if default_type is not None and not issubclass(default_type, HEAObject):
        raise TypeError('default_type is defined and not a HEAObject')
    if isinstance(type_or_type_name, type):
        if not issubclass(type_or_type_name, HEAObject):
            raise TypeError(f'type_or_type_name not a HEAObject')
        if issubclass(type_or_type_name, HEAObject):
            result_ = type_or_type_name
        else:
            raise TypeError('type_or_type_name not a HEAObject')
    else:
        file_system_type_ = desktop_object_type_for_name(type_or_type_name)
        if not issubclass(file_system_type_, HEAObject):
            raise TypeError(f'file_system_type_or_type_name is a {file_system_type_} not a HEAObject')
        else:
            result_ = file_system_type_
    if result_ is None:
        return default_type
    else:
        return result_


def display_name_for_multiple_objects(objs: Sequence[DesktopObject]) -> str:
    """
    Returns a user-friendly display name for multiple desktop objects. For one
    object, it will return just the object's display name.

    :param objs: a sequence of desktop objects
    :raises ValueError: if objs is None or an empty sequence.
    """
    if objs is None:
        raise ValueError('objs cannot be None')
    match len(objs):
        case 0:
            raise ValueError('No objects in objs')
        case 1:
            return objs[0].display_name
        case 2:
            return f'{objs[0].display_name} and 1 other object'
        case _:
            return f'{objs[0].display_name} and {len(objs) - 1} other objects'


class HEAServerPermissionContext(PermissionContext):
    """
    A context for checking permissions on HEA desktop objects that uses the heaserver-people service to access the
    current user's groups and checks group-level permissions in addition to permissions that are assigned directly to
    the user. If the current user is a system user, the heaserver-people service is not consulted.
    """

    def __init__(self, sub: str, request: web.Request, **kwargs):
        super().__init__(sub, **kwargs)
        if request is None:
            raise ValueError('request cannot be None')
        self.__request = request
        self.__groups: list[str] | None = None
        self.__group_to_group_id: dict[str, str | None] = {user: user for user in SYSTEM_USERS}
        self.__group_to_group_id_lock = LockManager[str]()
        self.__groups_lock = Lock()

    @property
    def request(self) -> web.Request:
        """The HTTP request."""
        return self.__request

    async def get_groups(self) -> list[str]:
        """
        Gets the group ids for the current user. This implementation consults the heaserver-people service, unless the
        current user is a system user.

        :return: the group ids for the current user.
        """
        async with self.__groups_lock:
            if self.__groups is None:
                sub = self.sub
                if is_system_user(sub):
                    self.__groups = []
                else:
                    url = await type_to_resource_url(self.request, Person)
                    groups = await client.get_all_list(self.request.app, URL(url) / sub / 'groups', Group,
                                                    headers={SUB: sub})
                    assert all(group.id is not None for group in groups), f'One or more groups in {groups} has no id'
                    self.__groups = [group.id for group in groups if group.id is not None]
            return self.__groups

    async def group_id_from(self, group: str) -> str:
        """
        Gets the group id for a group. This implementation consults the REST APIs of the service responsible for
        Groups, unless the user is a system user.

        :param group: the group (required).
        :return: the group id.
        :raises ValueError: if the group was not found.
        """
        async with self.__group_to_group_id_lock.lock(group):
            if group in self.__group_to_group_id:
                group_id = self.__group_to_group_id[group]
                if group_id is not None:
                    return group_id
                group_: Group | None = None
            else:
                url = await type_to_resource_url(self.request, Group)
                group_ = await client.get(self.request.app, URL(url) / 'byname' / encode_group(group), Group,
                                          headers={SUB: self.sub})
                self.__group_to_group_id[group] = group_.id if group_ is not None else None
            if group_ is None:
                raise ValueError(f'Group {group} not found')
            assert group_.id is not None, f'Group {group_} has no id'
            return group_.id

    async def can_create(self, desktop_object_type: type[DesktopObject]) -> bool:
        """
        Checks if the current user can create a desktop object of the given type. This implementation consults the
        REST APIs of the service responsible for registry Components.

        :param desktop_object_type: the type of the desktop object (required).
        :return: True if the user can create the object, False otherwise.
        """
        component = await client.get_component(self.request.app, desktop_object_type)
        if component is None or (resource := component.get_resource(desktop_object_type.get_type_name())) is None:
            raise ValueError(f'Invalid desktop object type {desktop_object_type}')
        return resource.manages_creators and await resource.is_creator(self)
