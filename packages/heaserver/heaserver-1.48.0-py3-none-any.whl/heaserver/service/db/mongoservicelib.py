import heaobject.root

from heaserver.service.crypt import get_attribute_key_from_app, get_attribute_key_from_request
from heaserver.service.util import queued_processing
from .. import response
from ..heaobjectsupport import new_heaobject_from_type, RESTPermissionGroup
from ..appproperty import HEA_DB, HEA_CACHE
from ..aiohttp import extract_sort_attrs, extract_sorts, SortOrder
from aiohttp.web import Application
from .mongo import MongoContext, Mongo
from heaobject.error import DeserializeException
from aiohttp.web import Request, StreamResponse, Response, HTTPError
from typing import Any, AsyncGenerator, Literal, IO, overload, Optional
from heaobject.root import DesktopObject, DesktopObjectDict, Permission, DesktopObjectTypeVar, \
    desktop_object_from_dict, to_dict, DesktopObjectDictIncludesEncrypted
from heaobject.user import NONE_USER
from heaobject.encryption import Encryption
from heaserver.service.oidcclaimhdrs import SUB
from pymongo.errors import WriteError, DuplicateKeyError
from collections.abc import Sequence, Mapping, Callable, Awaitable, Iterator
from asyncio import gather
from enum import Enum
from copy import deepcopy
from itertools import chain, repeat
import logging

from heaserver.service import appproperty


SortDict = dict[str, Literal[-1, 1]]
SortDictCacheKey = tuple[tuple[str, Literal[-1, 1]], ...]


async def get_dict(request: Request, collection: str, volume_id: str | None = None, mongo: Mongo | None = None,
                   context: heaobject.root.PermissionContext | None = None) -> DesktopObjectDict | None:
    """
    Gets the requested desktop object as a desktop object dict.

    :param request: the HTTP request, which must have an id path parameter. Required.
    :param collection: the Mongo collection name. Required.
    :param volume_id: the id string of the volume containing the requested HEA object. If None, the root volume is
    assumed.
    :param mongo: the Mongo context. If None, a new Mongo context is created.
    :param context: the permission context. If None, a new context is created.
    :return: a desktop object dict or None if the object was not found.
    """
    sub = request.headers.get(SUB, NONE_USER)
    cache_key = (sub, collection, f'id^{request.match_info["id"]}')
    cached_value = request.app[HEA_CACHE].get(cache_key)
    if cached_value is not None:
        return deepcopy(cached_value)
    else:
        async def fetch_from_mongo(mongo: Mongo) -> DesktopObjectDict | None:
            context_ = context if context else mongo.get_default_permission_context(request)
            result = await mongo.get(request, collection, var_parts='id', context=context_)

            if result is not None:
                obj = _desktop_object_from_dict(request, result)
                permitted = await RESTPermissionGroup.GETTER_PERMS.has_any(obj, context_)
                if not permitted:
                    return None
                request.app[HEA_CACHE][cache_key] = to_dict(obj)  # Need an unencrypted copy for the cache.
                return to_dict(obj)
            else:
                return None
        if mongo:
            return await fetch_from_mongo(mongo)
        else:
            async with MongoContext(request, volume_id) as mongo:
                return await fetch_from_mongo(mongo)


@overload
async def get_desktop_object(request: Request, collection: str, *, volume_id: str | None = None,
                             obj: DesktopObject | None = None,
                             mongo: Mongo | None = None,
                             context: heaobject.root.PermissionContext | None = None) -> DesktopObject | None:
    ...

@overload
async def get_desktop_object(request: Request, collection: str, *,
                             type_: type[DesktopObjectTypeVar], volume_id: str | None = None,
                             obj: DesktopObjectTypeVar | None = None,
                             mongo: Mongo | None = None,
                             context: heaobject.root.PermissionContext | None = None) -> DesktopObjectTypeVar | None:
    ...

async def get_desktop_object(request: Request, collection: str, *,
                             type_ = DesktopObject, volume_id: str | None = None,
                             obj: DesktopObject | None = None,
                             mongo: Mongo | None = None,
                             context: heaobject.root.PermissionContext | None = None) -> DesktopObject | None:
    """
    Gets the desktop object with the specified id.

    :param request: the HTTP request, which must have an id value in the match_info mapping. Required.
    :param collection: the Mongo collection name. Required.
    :param type_: optional object type.
    :param volume_id: the id string of the volume containing the requested HEA object. If None, the root volume is
    assumed.
    :param obj: the desktop object to populate from mongo.
    :param mongo: the Mongo context. If None, a new Mongo context is created.
    :param context: the permission context. If None, a new context is created.
    :return: a Response with the requested HEA object or Not Found.
    :raises TypeError: if the object retrieved from Mongo does not match the value of the type_ argument, or if the obj
    argument is not an instance of the type_ argument.
    """
    obj_dict = await get_dict(request, collection, volume_id, mongo=mongo, context=context)
    return _dict_to_desktop_object(request, obj_dict, type_=type_, obj=obj)


async def get(request: Request, collection: str, volume_id: str | None = None,
              context: heaobject.root.PermissionContext | None = None) -> Response:
    """
    Gets an HTTP response with the desktop object with the specified id in the body. The desktop object is
    formatted according to the requested mime types in the HTTP request's
    Accept header as one of the formats supported by the
    heaserver.service.representor module.

    :param request: the HTTP request, which must have an id value in the match_info mapping. Required.
    :param collection: the Mongo collection name. Required.
    :param volume_id: the id string of the volume containing the requested HEA object. If None, the root volume is
    assumed.
    :param context: the PermissionContext. If None, a new context is created.
    :return: a Response with the requested HEA object or Not Found.
    """
    async with MongoContext(request, volume_id) as mongo:
        context = context or mongo.get_default_permission_context(request)
        result = await get_dict(request, collection, volume_id, mongo=mongo, context=context)
        if result is None:
            return await response.get(request, None)
        else:
            obj = _desktop_object_from_dict(request, result)
            return await response.get(request, to_dict(obj), await obj.get_permissions(context),
                                    await obj.get_all_attribute_permissions(context))


async def get_content(request: Request, collection: str, volume_id: str | None = None) -> StreamResponse:
    """
    Gets the HEA object's associated content.

    :param request: the HTTP request. Required.
    :param collection: the Mongo collection name. Required.
    :param volume_id: the id string of the volume containing the requested HEA object. If None, the root volume is
    assumed.
    :return: an aiohttp StreamResponse with the requested HEA object or Not Found.
    """
    sub = request.headers.get(SUB, NONE_USER)
    async with MongoContext(request, volume_id) as mongo:
        context = mongo.get_default_permission_context(request)
        result = await mongo.get(request, collection, var_parts='id', context=context)

        if result is not None:
            obj = _desktop_object_from_dict(request, result)
            permitted = await RESTPermissionGroup.GETTER_PERMS.has_any(obj, context)
            if not permitted:
                return response.status_not_found()
        out = await mongo.get_content(request, collection, var_parts='id', context=context)
        if out is not None:
            return await response.get_streaming(request, out, 'text/plain')
        else:
            return response.status_not_found()


async def get_by_name(request: Request, collection: str,
                      volume_id: str | None = None) -> Response:
    """
    Gets an HTTP response object with the requested desktop object in the body.
    The desktop object is formatted according to the requested mime types in
    the HTTP request's Accept header as one of the formats supported by the
    heaserver.service.representor module.

    :param request: the HTTP request, which must have a name value in the match_info mapping. Required.
    :param collection: the Mongo collection name. Required.
    :param volume_id: the id string of the volume containing the requested
    desktop object. If None, the root volume is assumed.
    :return: a Response with the requested desktop object or Not Found.
    """
    async with MongoContext(request, volume_id) as mongo:
        result = await get_by_name_dict(request, collection, volume_id, mongo=mongo)
        if result is None:
            return await response.get(request, None)
        else:
            obj = _desktop_object_from_dict(request, result)
            context = mongo.get_default_permission_context(request)
            return await response.get(request, to_dict(obj) if result is not None else None,
                                    permissions=await obj.get_permissions(context),
                                    attribute_permissions=await obj.get_all_attribute_permissions(context))

async def get_by_name_dict(request: Request, collection: str,
                           volume_id: str | None = None, mongo: Mongo | None = None,
                           context: heaobject.root.PermissionContext | None = None) -> DesktopObjectDict | None:
    """
    Gets the requested desktop object as a desktop object dict.

    :param request: the HTTP request, which must have a name value in the match_info mapping. Required.
    :param collection: the Mongo collection name. Required.
    :param volume_id: the id string of the volume containing the requested HEA
    object. If None, the root volume is assumed.
    :param mongo: the Mongo context. If None, a new Mongo context is created.
    :param context: the permission context. If None, a new context is created.
    :return: a desktop object dict or None if the object was not found.
    """
    sub = request.headers.get(SUB, NONE_USER)
    cache_key = (sub, collection, f'name^{request.match_info["name"]}')
    cached_value = request.app[HEA_CACHE].get(cache_key)
    if cached_value is not None:
        return cached_value
    else:
        async def fetch_from_mongo(mongo: Mongo) -> DesktopObjectDict | None:
            context_ = context if context else mongo.get_default_permission_context(request)
            result = await mongo.get(request, collection, var_parts='name', context=context_)

            if result is not None:
                obj = _desktop_object_from_dict(request, result)
                permitted = await RESTPermissionGroup.GETTER_PERMS.has_any(obj, context_)
                if not permitted:
                    return None
                request.app[HEA_CACHE][cache_key] = to_dict(obj)  # Need an unencrypted copy for the cache.
                return to_dict(obj)
            else:
                return None



        if mongo:
            return await fetch_from_mongo(mongo)
        else:
            async with MongoContext(request, volume_id) as mongo:
                return await fetch_from_mongo(mongo)


@overload
async def get_by_name_desktop_object(request: Request, collection: str, *, volume_id: str | None = None,
                             obj: DesktopObject | None = None,
                             mongo: Mongo | None = None,
                             context: heaobject.root.PermissionContext | None = None) -> DesktopObject | None:
    ...


@overload
async def get_by_name_desktop_object(request: Request, collection: str, *,
                             type_: type[DesktopObjectTypeVar], volume_id: str | None = None,
                             obj: DesktopObjectTypeVar | None = None,
                             mongo: Mongo | None = None,
                             context: heaobject.root.PermissionContext | None = None) -> DesktopObjectTypeVar | None:
    ...


async def get_by_name_desktop_object(request: Request, collection: str, *,
                                     type_ = DesktopObject, volume_id: str | None = None,
                                     obj: DesktopObject | None = None,
                                     mongo: Mongo | None = None,
                                     context: heaobject.root.PermissionContext | None = None) -> DesktopObject | None:
    """
    Gets the desktop object with the specified name.

    :param request: the HTTP request, which must have a name value in the match_info mapping. Required.
    :param collection: the Mongo collection name. Required.
    :param type_: optional object type.
    :param volume_id: the id of the volume containing the requested HEA object. If None, the root volume is assumed.
    :param obj: the desktop object to populate from mongo.
    :param mongo: the Mongo context. If None, a new Mongo context is created.
    :param context: the permission context. If None, a new context is created.
    :return: a Response with the requested HEA object or Not Found.
    :raises TypeError: if the object retrieved from Mongo does not match the value of the type_ argument, or if the obj
    argument is not an instance of the type_ argument.
    """
    obj_dict = await get_by_name_dict(request, collection, volume_id, mongo=mongo, context=context)
    return _dict_to_desktop_object(request, obj_dict, type_=type_, obj=obj)


async def get_all(request: Request,
                  collection: str,
                  volume_id: str | None = None,
                  mongoattributes: Any | None = None,
                  sort: SortDict | None = None,
                  context: heaobject.root.PermissionContext | None = None) -> Response:
    """
    Gets an HTTP response with all requested desktop objects in the body. The desktop objects are formatted according
    to the requested mime types in the HTTP request's Accept header as one of the formats supported by the
    heaserver.service.representor module.  This function caches its results. The cache key it uses is
    (sub, collection, None, tuple of sort key-value tuples, and the cache value it stores is
    (list of desktop object dicts, list of object permissions, list of attribute permissions).

    :param request: the HTTP request. Required.
    :param collection: the Mongo collection name. Required.
    :param volume_id: the id string of the volume containing the requested HEA object. If None, the root volume is
    assumed.
    :param sort: the sort order of the desktop objects as a dict of desktop object attribute to 1 or -1 for ascending
    or descending.
    :param context: the PermissionContext. If None, a new context is created.
    :return: a Response with a list of HEA object dicts. If no desktop objects are found, the body will contain an
    empty list.
    """
    sub = request.headers.get(SUB, NONE_USER)
    if mongoattributes is None and not request.query:
        cache_key = (sub, collection, None, tuple((key, val) for key, val in (sort or {}).items()))
        cached_value = request.app[HEA_CACHE].get(cache_key)
    else:
        cached_value = None
    if mongoattributes is None and cached_value is not None:
        return await response.get_all(request, data=cached_value[0], permissions=cached_value[1],
                                      attribute_permissions=cached_value[2])
    else:
        l: list[DesktopObjectDict] = []
        async with MongoContext(request, volume_id) as mongo:
            context = context or mongo.get_default_permission_context(request)
            gen = get_all_desktop_objects_gen(request, collection,
                                              volume_id=volume_id, mongoattributes=mongoattributes, sort=sort,
                                              mongo=mongo, context=context)
            try:
                perms: list[list[Permission]] = []
                attr_perms: list[dict[str, list[Permission]]] = []
                async def the_iter():
                    async for obj in gen:
                        l.append(obj.to_dict())
                        yield obj
                buffer: list[DesktopObject] = []
                async def process_buffer(buffer: list[DesktopObject]):
                    async def process_obj(obj: DesktopObject):
                        return await obj.get_permissions(context), await obj.get_all_attribute_permissions(context)
                    results = await gather(*(process_obj(o) for o in buffer))
                    for perm, attr_perm in results:
                        perms.append(perm)
                        attr_perms.append(attr_perm)
                async def process_desktop_object(obj: DesktopObject):
                    buffer.append(obj)
                    if len(buffer) >= 50:
                        await process_buffer(buffer)
                        buffer.clear()
                await queued_processing(the_iter(), process_desktop_object, num_workers=1)
                if buffer:
                    await process_buffer(buffer)
                if mongoattributes is None and not request.query:
                    request.app[HEA_CACHE][cache_key] = (l, perms, attr_perms)
                return await response.get_all(request, l, permissions=perms, attribute_permissions=attr_perms)
            finally:
                await gen.aclose()

async def get_all_dict(request: Request,
                       collection: str,
                       volume_id: str | None = None,
                       mongoattributes: Any | None = None,
                       sort: SortDict | None = None,
                       mongo: Mongo | None = None,
                       context: heaobject.root.PermissionContext | None = None) -> list[DesktopObjectDict]:
    """
    Gets all HEA objects as a list of desktop object dicts. This function does not cache its results, but if there are
    cached results from a prior get_all function call, it will use them. The cache key it looks for is
    (sub, collection, None, tuple of sort key-value tuples)

    :param request: the HTTP request. Required.
    :param collection: the Mongo collection name. Required.
    :param volume_id: the id string of the volume containing the requested HEA
    object. If None, the root volume is assumed.
    :param sort: the sort order of the desktop objects as a dict of desktop
    object attribute to 1 or -1 for ascending or descending.
    :param mongo: the Mongo context. If None, a new Mongo context is created.
    :param context: the PermissionContext. If None, a new context is created.
    :return: a list of DesktopObjectDict. If no desktop objects are found, the
    return value will be an empty list.
    """
    sub = request.headers.get(SUB, NONE_USER)
    if mongoattributes is None and not request.query:
        cache_key = (sub, collection, None, tuple((key, val) for key, val in (sort or {}).items()))
        cached_value = request.app[HEA_CACHE].get(cache_key)
    else:
        cached_value = None
    if mongoattributes is None and cached_value is not None:
        return deepcopy(cached_value[0])
    else:
        return [to_dict(obj) async for obj in get_all_desktop_objects_gen(request, collection, volume_id=volume_id,
                                                                        mongoattributes=mongoattributes, sort=sort,
                                                                        mongo=mongo, context=context)]


async def opener(request: Request, collection: str, volume_id: str | None = None,
                 include_desktop_object: bool = True) -> Response:
    """
    Gets choices for opening an HEA desktop object's content.

    :param request: the HTTP request. Required. If an Accepts header is provided, MIME types that do not support links
    will be ignored.
    :param collection: the Mongo collection name. Required.
    :param volume_id: the id string of the volume containing the requested HEA object. If None, the root volume is
    assumed.
    :return: a Response object with status code 300, and a body containing the HEA desktop object and links
    representing possible choices for opening the HEA desktop object; or Not Found.
    """
    sub = request.headers.get(SUB, NONE_USER)
    cache_key = (sub, collection, f"id^{request.match_info['id']}")
    cached_value = request.app[HEA_CACHE].get(cache_key)
    if include_desktop_object is None:
        include_desktop_object_ = True
    else:
        include_desktop_object_ = bool(include_desktop_object)
    if cached_value is not None:
        return await response.get_multiple_choices(request, cached_value if include_desktop_object_ else None)
    else:
        async with MongoContext(request, volume_id) as mongo:
            context = mongo.get_default_permission_context(request)
            result = await mongo.get(request, collection, var_parts='id', context=context)
            if result is not None:
                obj = _desktop_object_from_dict(request, result)
                if not await RESTPermissionGroup.GETTER_PERMS.has_any(obj, context):
                    return response.status_not_found()
                request.app[HEA_CACHE][cache_key] = retval = to_dict(obj)
                return await response.get_multiple_choices(request, retval if include_desktop_object_ else None)
            else:
                return response.status_not_found()



async def post(request: Request, collection: str, type_: type[DesktopObject], default_content: IO | None = None,
               volume_id: str | None = None, resource_base: str | None = None) -> Response:
    """
    Posts the desktop object from a request body.

    :param request: the HTTP request containing the desktop object. The object's owner and the request's OIDC_CLAIM_sub
    header must match.
    :param collection: the Mongo collection name. Required.
    :param type_: The HEA object type. Required. The type of the object in the request body is compared to this type
    for whether the object is an instance of the given type, and a response with a 400 status code is returned if it is
    not. The type can be abstract as it is used only for input validation. If using mypy to type check your code, you
    may need to use a type: ignore[type-abstract] comment to avoid a type check error if you pass an abstract type
    here.
    :param default_content: an optional blank document or other default content as a file-like object. This must be
    not-None for any microservices that manage content.
    :param volume_id: the id string of the volume containing the requested HEA object. If None, the root volume is
    assumed.
    :param resource_base: the base path of the created resource. If None, the collection is used as the base path.
    :return: a Response object with a status of Created and the object's URI in the Location header, otherwise returns
    a Response with an appropriate status code.
    """
    logger = logging.getLogger(__name__)
    sub = request.headers.get(SUB, NONE_USER)
    try:
        obj = await new_heaobject_from_type(request, type_)
    except DeserializeException as e:
        return response.status_bad_request(str(e))
    if not await request.app[HEA_DB].is_creator(request, type(obj)):
        logger.debug('Permission denied to %s creating object %s', sub, obj)
        return response.status_forbidden(f'Permission denied creating object of type {type_.get_type_name()}')
    if obj.owner != sub:
        logger.debug('Permission denied to %s creating object with owner %s', sub, obj.owner)
        return response.status_forbidden(f'Permission denied creating object of type {type_.get_type_name()}')
    async with MongoContext(request, volume_id) as mongo:
        try:
            result = await mongo.post(request, obj, collection, default_content,
                                      encryption=_get_encryption_from_request(request))
            to_delete = []
            for cache_key in request.app[HEA_CACHE]:
                if cache_key[1] == collection and cache_key[2] is None:
                    to_delete.append(cache_key)
            for cache_key in to_delete:
                request.app[HEA_CACHE].pop(cache_key, None)
            return await response.post(request, result, resource_base if resource_base is not None else collection)
        except DuplicateKeyError as e:
            return response.status_conflict(f'Object {obj.display_name} already exists')

async def post_dict_return_id(request: Request, obj_dict: DesktopObjectDict, collection: str,
                              type_: type[DesktopObject], default_content: IO | None = None,
                              volume_id: str | None = None) -> str | None:
    """
    Posts the desktop object from a request body.

    :param request: the HTTP request containing the desktop object. The object's owner and the request's OIDC_CLAIM_sub
    header must match.
    :param obj_dict: the object to create (required).
    :param collection: the Mongo collection name. Required.
    :param type_: The HEA object type. Required. The type of the object in the request body is compared to this type
    for whether the object is an instance of the given type, and a response with a 400 status code is returned if it is
    not.
    :param default_content: an optional blank document or other default content as a file-like object. This must be not-None
    for any microservices that manage content.
    :param volume_id: the id string of the volume containing the requested HEA object. If None, the root volume is
    assumed.
    :return: the created object's id.
    :raises HTTPError: if an error occurs creating the object on the server.
    """
    logger = logging.getLogger(__name__)
    sub = request.headers.get(SUB, NONE_USER)
    owner = obj_dict.get('owner')
    if sub != owner:
        logger.debug('Permission denied to %s creating object %s', sub, obj_dict)
        raise response.status_forbidden(f'Permission denied creating object with owner {owner}')
    try:
        obj = _desktop_object_from_dict(request, obj_dict, type_=type_)
    except (DeserializeException, ValueError, TypeError) as e:
        raise response.status_bad_request(str(e))
    async with MongoContext(request, volume_id) as mongo:
        try:
            return await mongo.post(request, obj, collection, default_content,
                                    encryption=_get_encryption_from_request(request))
        except DuplicateKeyError as e:
            raise response.status_conflict(f'Object {obj.display_name} already exists')

async def post_dict(request: Request, obj_dict: DesktopObjectDict, collection: str, type_: type[DesktopObject],
                    default_content: IO | None = None, volume_id: str | None = None,
                    resource_base: str | None = None) -> Response:
    """
    Posts a desktop object dict.

    :param request: the HTTP request (required). The owner property in the obj_dict parameter and the request's
    OIDC_CLAIM_sub header must match.
    :param obj_dict: a desktop object dict (required).
    :param collection: the Mongo collection name (required).
    :param type_: The HEA object type. Required. The type of the object in the request body is compared to this type
    for whether the object is an instance of the given type, and a response with a 400 status code is returned if it is
    not.
    :param default_content: an optional blank document or other default content as a file-like object. This must be not-None
    for any microservices that manage content.
    :param volume_id: the id string of the volume containing the requested HEA object. If None, the root volume is
    assumed.
    :param resource_base: the base path of the created resource. If None, the collection is used as the base path.
    :return: a Response object with a status of Created and the object's URI in the Location header if the request was
    successful, otherwise a Response object with an error status code.
    """
    try:
        result = await post_dict_return_id(request, obj_dict, collection, type_, default_content, volume_id)
        return await response.post(request, result, resource_base if resource_base is not None else collection)
    except HTTPError as e:
        return e

async def put(request: Request, collection: str, type_: type[DesktopObjectTypeVar], volume_id: str | None = None,
              obj: DesktopObjectTypeVar | None = None,
              pre_save_hook: Callable[[Request, DesktopObjectTypeVar], Awaitable[None]] | None = None) -> Response:
    """
    Updates the HEA object with the specified id.

    :param request: the HTTP request. Required.
    :param collection: the Mongo collection name. Required.
    :param type_: The HEA object type. Required. The type can be abstract as it is used only for input validation. If
    using mypy to type check your code, you may need to use a type: ignore[type-abstract] comment to avoid a type check
    error if you pass an abstract type here.
    :param volume_id: the id string of the volume containing the requested HEA object. If None, the root volume is
    assumed.
    :param obj: desktop object to use instead of what is in the request body (optional). There will be no validation
    performed on the PUT body.
    :param pre_save_hook: an optional hook to call after the save request has been validated and before saving the
    object.
    :return: a Response object with a status of No Content, Forbidden, or Not Found.
    """
    async with MongoContext(request, volume_id) as mongo:
        if obj is not None:
            obj_ = obj
        else:
            try:
                obj_ = await new_heaobject_from_type(request, type_)
            except DeserializeException as e:
                return response.status_bad_request(str(e))
        try:
            context = mongo.get_default_permission_context(request)
            permitted = await RESTPermissionGroup.PUTTER_PERMS.has_any(obj_, context)
            if not permitted:
                if await RESTPermissionGroup.GETTER_PERMS.has_any(obj_, context):
                    return response.status_forbidden()
                else:
                    return response.status_not_found()
            if pre_save_hook is not None:
                await pre_save_hook(request, obj_)
            result = await mongo.put(request, obj_, collection, context=context,
                                     encryption=_get_encryption_from_request(request))  # if lacks permissions or object is not in database, then updates no records.
        except WriteError as e:
            err_msg = e.details.get('errmsg') if e.details else None
            if e.code == 66:
                return response.status_bad_request(err_msg)
            else:
                return response.status_internal_error(err_msg)
        if result is not None and result.matched_count:
            to_delete = []
            for cache_key in request.app[HEA_CACHE]:
                if cache_key[1] == collection and cache_key[2] in (None, f"id^{request.match_info['id']}"):
                    to_delete.append(cache_key)
            for cache_key in to_delete:
                request.app[HEA_CACHE].pop(cache_key, None)
        return await response.put(bool(result.matched_count if result is not None else None))

async def upsert(request: Request, collection: str, type_: type[DesktopObject], volume_id: str | None = None, filter: Mapping[str, Any] | None = None) -> Response:
    """
    Updates the HEA object, using the specified filter if provided otherwise the object's id, and inserting a new object
    if none matches the filter or the id.

    :param request: the HTTP request. Required.
    :param collection: the Mongo collection name. Required.
    :param type_: The HEA object type. Required.
    :param volume_id: the id string of the volume containing the requested HEA object. If None, the root volume is
    assumed.
    :param filter: optional filter criteria.
    :return: a Response object with a status of No Content, Forbidden, or Not Found.
    """
    sub = request.headers.get(SUB, NONE_USER)
    async with MongoContext(request, volume_id) as mongo:
        try:
            obj = await new_heaobject_from_type(request, type_)
        except DeserializeException as e:
            return response.status_bad_request(str(e).encode())
        try:
            context = mongo.get_default_permission_context(request)
            permitted = await RESTPermissionGroup.PUTTER_PERMS.has_any(obj, context) and \
                await RESTPermissionGroup.POSTER_PERMS.has_any(obj, context)
            if not permitted:
                if await RESTPermissionGroup.GETTER_PERMS.has_any(obj, context):
                    return response.status_forbidden()
                else:
                    return response.status_not_found()

            result = await mongo.upsert_admin(obj, collection, mongoattributes=filter,
                                              encryption=_get_encryption_from_request(request))
        except WriteError as e:
            err_msg = e.details.get('errmsg') if e.details is not None else None
            if e.code == 66:
                return response.status_bad_request(err_msg)
            else:
                return response.status_internal_error(err_msg)
        to_delete = []
        for cache_key in request.app[HEA_CACHE]:
            if cache_key[1] == collection and cache_key[2] in (None, f"id^{request.match_info['id']}"):
                to_delete.append(cache_key)
        for cache_key in to_delete:
            request.app[HEA_CACHE].pop(cache_key, None)
        return await response.put(bool(result))


async def put_content(request: Request, collection: str, type_: type[DesktopObject], volume_id: str | None = None) -> Response:
    """
    Updates the HEA object's associated content.

    :param request: the HTTP request. Required.
    :param collection: the Mongo collection name. Required.
    :param type_: The HEA object type. Required.
    :param volume_id: the id string of the volume containing the requested HEA object. If None, the root volume is
    assumed.
    :return: a Response object with a status of No Content, Forbidden, or Not Found.
    """
    async with MongoContext(request, volume_id) as mongo:
        context = mongo.get_default_permission_context(request)
        result = await mongo.get(request, collection, var_parts='id', context=context)

        if result is not None:
            obj = heaobject.root.desktop_object_from_dict(result)
            assert obj.id is not None, 'Object id is None'
            permitted = await RESTPermissionGroup.PUTTER_PERMS.has_any(obj, context)
            if not permitted:
                if await RESTPermissionGroup.GETTER_PERMS.has_any(obj, context):
                    return response.status_forbidden()
                else:
                    return response.status_not_found()
            result2 = await mongo.put_content(request, collection, obj.id, obj.display_name)  # if lacks permissions, then updates no records.
            return await response.put(result2)
        else:
            return response.status_not_found()


async def delete(request: Request, collection: str, volume_id: str | None = None) -> Response:
    """
    Deletes the HEA object with the specified id and any associated content.

    :param request: the HTTP request. Required.
    :param collection: the Mongo collection name. Required.
    :param volume_id: the id string of the volume containing the requested HEA object. If None, the root volume is
    assumed.
    :return: No Content, Forbidden, or Not Found.
    """
    async with MongoContext(request, volume_id) as mongo:
        context = mongo.get_default_permission_context(request)
        obj = await mongo.get(request, collection, var_parts='id', context=context)

        if obj is not None:
            obj_ = heaobject.root.desktop_object_from_dict(obj)
            permitted = await RESTPermissionGroup.DELETER_PERMS.has_any(obj_, context)
            if not permitted:
                return response.status_forbidden()
            delete_result = await mongo.delete(request, collection, var_parts='id',
                                               context=context)  # if lacks permissions, then deletes no records.
            if delete_result and delete_result.deleted_count:
                _delete_cached(request.app, collection, request.match_info['id'])
            return await response.delete(bool(delete_result.deleted_count) if delete_result else False)
        else:
            return response.status_not_found()


async def ping(request: Request) -> Response:
    """
    Sends a ping command to the database.

    :param request: the HTTP request.
    :return: an HTTP response with status code 200 if the ping is successful, 500 otherwise.
    """
    async with MongoContext(request) as mongo:
        try:
            await mongo.ping()
            return response.status_ok()
        except Exception as e:  # The exact exception is not documented.
            raise response.status_internal_error() from e

async def aggregate(request: Request, collection: str,
                    pipeline: Sequence[Mapping[str, Any]], volume_id: str | None = None) -> Response:
    """
    Execute an aggregation pipeline that returns a list of desktop object dicts that the current user has access to.
    Unlike the other methods that return a response with desktop object dictionaries, this one does not ignore id
    properties returned from mongo, nor does it assume there is an _id ObjectId property and convert it to a str id
    property.

    :param request: the HTTP request (required).
    :param collection. The Mongo collection name (required).
    :param volume_id: the volume_id of the Mongo database. If None, the root volume is assumed.
    :return: a 200 status code response with the desktop object dicts from the pipeline.
    """
    async with MongoContext(request, volume_id) as mongo:
        result: list[DesktopObject] = []
        permissions: list[list[Permission]] = []
        attribute_permissions: list[dict[str, list[Permission]]] = []
        agg = mongo.aggregate(collection, pipeline)
        try:
            context = mongo.get_default_permission_context(request)
            async for r in agg:
                obj = _desktop_object_from_dict(request, r)
                permitted = await RESTPermissionGroup.GETTER_PERMS.has_any(obj, context)
                if permitted:
                    perms_to_add, attr_perms_to_add = await gather(obj.get_permissions(context), obj.get_all_attribute_permissions(context))
                    permissions.append(perms_to_add)
                    attribute_permissions.append(attr_perms_to_add)
                    result.append(obj)
            return await response.get_all(request, [to_dict(obj) for obj in result], permissions=permissions,
                                          attribute_permissions=attribute_permissions)
        finally:
            await agg.aclose()


async def get_all_desktop_objects(request: Request,
                      collection: str,
                      type_: type[DesktopObject] | None = None,
                      volume_id: str | None = None,
                      mongoattributes: Any | None = None,
                      sort: SortDict | None = None,
                      mongo: Mongo | None = None,
                      context: heaobject.root.PermissionContext | None = None) -> list[DesktopObject]:
    """
    Gets a list of all desktop objects matching the query. This function does not cache its results, but if there are
    cached results from a prior get_all function call, it will use them. The cache key it looks for is
    (sub, collection, None, tuple of sort key-value tuples)

    :param request: the HTTP request. Required.
    :param collection: the Mongo collection name. Required.
    :param type_: the expected type of desktop object in the generator.
    :param volume_id: the id string of the volume containing the requested desktop object. If None, the root volume is
    assumed.
    :param mongoattributes: the mongo query to use. If None, all desktop objects from the collection are returned.
    :param sort: the sort order of the desktop objects as a dict of attributes to 1 (ascending) or -1 (descending).
    :param mongo: the Mongo context. If None, a new Mongo context is created.
    :param context: the PermissionContext. If None, a new context is created.
    :return: a list of DesktopObject.
    """
    sub = request.headers.get(SUB, NONE_USER)
    if mongoattributes is None and not request.query:
        cache_key = (sub, collection, None, tuple((key, val) for key, val in (sort or {}).items()))
        cached_value = request.app[HEA_CACHE].get(cache_key)
    else:
        cached_value = None
    if mongoattributes is None and cached_value is not None:
        return [desktop_object_from_dict(obj_dict, type_=type_) for obj_dict in cached_value[0]]
    else:
        return [obj async for obj in get_all_desktop_objects_gen(request, collection, type_=type_, volume_id=volume_id,
                                                                mongoattributes=mongoattributes, sort=sort,
                                                                mongo=mongo, context=context)]


@overload
def get_all_desktop_objects_gen(request: Request, collection: str, *,
                      volume_id: str | None = None,
                      mongoattributes: Any | None = None,
                      sort: SortDict | None = None,
                      mongo: Mongo | None = None,
                      context: heaobject.root.PermissionContext | None = None) -> AsyncGenerator[DesktopObject, None]: ...


@overload
def get_all_desktop_objects_gen(request: Request, collection: str, *,
                      type_: type[DesktopObjectTypeVar],
                      volume_id: str | None = None,
                      mongoattributes: Any | None = None,
                      sort: SortDict | None = None,
                      mongo: Mongo | None = None,
                      context: heaobject.root.PermissionContext | None = None) -> AsyncGenerator[DesktopObjectTypeVar, None]: ...


@overload
def get_all_desktop_objects_gen(request: Request, collection: str, *,
                      type_: type[DesktopObject] | None,
                      volume_id: str | None = None,
                      mongoattributes: Any | None = None,
                      sort: SortDict | None = None,
                      mongo: Mongo | None = None,
                      context: heaobject.root.PermissionContext | None = None) -> AsyncGenerator[DesktopObject, None]: ...


async def get_all_desktop_objects_gen(request: Request, collection: str, *,
                      type_: type[DesktopObject] | None = None,
                      volume_id: str | None = None,
                      mongoattributes: Any | None = None,
                      sort: SortDict | None = None,
                      mongo: Mongo | None = None,
                      context: heaobject.root.PermissionContext | None = None) -> AsyncGenerator[DesktopObject, None]:
    """
    Gets an async generator of all desktop objects. This generator does no desktop object caching, nor does it use any
    previously cached data.

    :param request: the HTTP request. Required.
    :param collection: the Mongo collection name. Required.
    :param type_: the expected type of desktop object in the generator.
    :param volume_id: the id string of the volume containing the requested desktop object. If None, the root volume is
    assumed.
    :param mongoattributes: the mongo query to use. If None, all desktop objects from the collection are returned.
    :param sort: the sort order of the desktop objects as a dict of attributes to 1 (ascending) or -1 (descending).
    :param mongo: the Mongo context. If None, a new Mongo context is created.
    :param context: the PermissionContext. If None, a new context is created.
    :return: an async generator of DesktopObject.
    """
    async def fetch_objects(mongo: Mongo) -> AsyncGenerator[DesktopObject, None]:
        context_ = mongo.get_default_permission_context(request) if context is None else context
        gen = mongo.get_all(request, collection, mongoattributes=mongoattributes, sort=sort,
                            context=context_)
        try:
            async for desktop_object_dict in gen:
                obj = _desktop_object_from_dict(request, desktop_object_dict, type_=type_)
                if await RESTPermissionGroup.GETTER_PERMS.has_any(obj, context_):
                    yield obj
        finally:
            await gen.aclose()

    if mongo:
        f = fetch_objects(mongo)
        try:
            async for obj in f:
                yield obj
        finally:
            await f.aclose()
    else:
        async with MongoContext(request, volume_id) as mongo:
            f = fetch_objects(mongo)
            try:
                async for obj in f:
                    yield obj
            finally:
                await f.aclose()


class MongoSortOrder(Enum):
    """
    Enum for mongo query sort order.
    """
    _value_: Literal[-1, 1]
    ASCENDING = 1
    DESCENDING = -1

    def as_sort_order(self) -> SortOrder | None:
        """
        Converts a MongoSortOrder to a SortOrder.

        :return: a SortOrder.
        """
        return SortOrder.ASC if self is MongoSortOrder.ASCENDING else \
            SortOrder.DESC if self is MongoSortOrder.DESCENDING else None

    def to_sort_dict(self, sort_attribute: str) -> SortDict:
        """
        Returns a sort dict suitable to pass into MongoDB queries.

        :param sort_attributes: an attribute to sort on. Required.
        :return: a dict of attribute name to 1 (ascending) or -1 (descending).
        """
        return {sort_attribute: self.value}

    @overload
    @classmethod
    def from_sort_order(cls, sort_order: SortOrder) -> 'MongoSortOrder': ...

    @overload
    @classmethod
    def from_sort_order(cls, sort_order: None) -> None: ...

    @classmethod
    def from_sort_order(cls, sort_order: SortOrder | None) -> Optional['MongoSortOrder']:
        """
        Converts a SortOrder to a MongoSortOrder.

        :param sort_order: the SortOrder to convert.
        :return: a MongoSortOrder or None if the sort_order is None.
        """
        if sort_order is None:
            return None
        elif sort_order is SortOrder.ASC:
            return cls.ASCENDING
        elif sort_order is SortOrder.DESC:
            return cls.DESCENDING
        else:
            raise ValueError(f'Invalid sort order: {sort_order}')

    @staticmethod
    def from_request(request: Request, default_attr: str | None = None,
                     default_sort_order: Optional['MongoSortOrder'] = None) -> Iterator[tuple[str, 'MongoSortOrder']]:
        """
        Extracts MongoSortOrders by attribute from the request's sort query parameter.

        :param request: the HTTP request. Required.
        :param default_attr: the default attribute to use if no sort attribute is present. If omitted, there must be at
        least as many sort attributes as sort orders.
        :param default_sort_order: the default sort order to use if no sort order is present. If omitted, the default
        sort order is ascending.
        :return: iterator of attribute-MongoSortOrder tuples, if present.
        """
        sort_orders = list(MongoSortOrder.from_sort_order(sort) for sort in extract_sorts(request))
        len_sort_orders = len(sort_orders)
        sort_attrs = list(sort_attr for sort_attr in extract_sort_attrs(request))
        len_sort_attrs = len(sort_attrs)
        max_len = max(len_sort_orders, len_sort_attrs)
        if len_sort_attrs < max_len - 1:
            raise ValueError('Ambiguous sort attributes: more than one sort order specified without an attribute')
        sort_orders_chain = chain(sort_orders, repeat(default_sort_order or MongoSortOrder.ASCENDING, max_len - len_sort_orders))
        if not default_attr:
            return zip(sort_attrs, sort_orders_chain, strict=True)
        else:
            sort_attrs_chain = chain(sort_attrs, repeat(default_attr, max_len - len_sort_attrs))
            return zip(sort_attrs_chain, sort_orders_chain, strict=True)

    @staticmethod
    def from_request_dict(request: Request, default_attr: str | None = None,
                          default_sort_order: Optional['MongoSortOrder'] = None) -> SortDict:
        """
        Extracts the sort order from the request query parameters, and returns a sort dict suitable to pass into
        MongoDB queries.

        :param request: the HTTP request. Required.
        :param default_attr: the default attribute to use if no sort attribute is present. If omitted, there must be at
        least as many sort attributes as sort orders.
        :param default_sort_order: the default sort order to use if no sort order is present. If omitted, the default
        sort order is ascending.
        :return: a dict of attribute names to 1 (ascending) or -1 (descending), or the empty dict if no order is
        specified.
        """
        return {attr_: order.value for attr_, order in MongoSortOrder.from_request(request, default_attr,
                                                                                   default_sort_order=default_sort_order)}

    @staticmethod
    def from_request_dict_raises_http_error(request: Request, default_attr: str | None = None,
                                            default_sort_order: Optional['MongoSortOrder'] = None) -> SortDict:
        """
        Extracts the sort order from the request query parameters, and returns a sort dict suitable to pass into
        MongoDB queries. Raises an HTTPError if the sort query parameter is invalid.

        :param request: the HTTP request. Required.
        :param default_attr: the default attribute to use if no sort attribute is present. If omitted, there must be at
        least as many sort attributes as sort orders.
        :param default_sort_order: the default sort order to use if no sort order is present. If omitted, the default
        sort order is ascending.
        :return: a dict of attribute names to 1 (ascending) or -1 (descending), or the empty dict if no order is
        specified.
        :raises HTTPError: if the sort parameter is invalid.
        """
        try:
            return MongoSortOrder.from_request_dict(request, default_attr=default_attr,
                                                    default_sort_order=default_sort_order)
        except ValueError as e:
            raise response.status_bad_request(f'Invalid sort parameter: {e}')


@overload
def sort_dict_to_cache_key(sort: None) -> None: ...


@overload
def sort_dict_to_cache_key(sort: SortDict) -> SortDictCacheKey: ...


def sort_dict_to_cache_key(sort: SortDict | None) -> SortDictCacheKey | None:
    """
    Converts a sort dict to a cache key tuple.

    :param sort: the sort dict. Required.
    :return: a tuple of the sort keys and values.
    """
    return tuple((key, val) for key, val in sort.items()) if sort is not None else None


def _delete_cached(app: Application, collection: str, id_: str):
    """
    Deletes the cached desktop object with the specified id in the specified collection.

    :param collection: the Mongo collection name. Required.
    :param id_: the id of the desktop object to delete from the cache. Required.
    """
    to_delete = []
    for cache_key in app[HEA_CACHE]:
        if cache_key[1] == collection and cache_key[2] in (None, f"id^{id_}"):
            to_delete.append(cache_key)
    for cache_key in to_delete:
        app[HEA_CACHE].pop(cache_key, None)


@overload
def _dict_to_desktop_object(request: Request, obj_dict: None, *, type_: type[DesktopObject],
                            obj: DesktopObject | None = None) -> None:
    ...


@overload
def _dict_to_desktop_object(request: Request, obj_dict: DesktopObjectDict, *,
                            obj: DesktopObject | None = None) -> DesktopObject:
    ...


@overload
def _dict_to_desktop_object(request: Request, obj_dict: DesktopObjectDict, *, type_: type[DesktopObjectTypeVar],
                            obj: DesktopObjectTypeVar | None = None) -> DesktopObjectTypeVar:
    ...


def _dict_to_desktop_object(request: Request, obj_dict: DesktopObjectDict | None, *, type_ = DesktopObject, obj:
                            DesktopObject | None = None) -> DesktopObject | None:
    """
    Converts a desktop object dict to a desktop object. If the dictionary is None, None is returned.
    If the dictionary is not None, the object is created from the dictionary and returned.
    If the object is not None, the dictionary is used to update the object and the object is returned.

    :param request: the HTTP request.
    :param obj_dict: the dictionary to convert.
    :param type_: the type of the object to create. If None, the type key of the dictionary is used to determine the
    type of the object to create.
    :param obj: the object to populate from the desktop object dict. If None, a new object is created.
    :return: the object created from the dictionary or None if the dictionary is None.
    """
    if obj_dict is None:
        return None
    elif obj:
        if not isinstance(obj, type_):
            raise TypeError(f'Object {obj} is not of type {type_}')
        obj.from_dict(obj_dict)
        return obj
    else:
        return _desktop_object_from_dict(request, obj_dict, type_=type_)


def _get_encryption_from_request(request: Request) -> Optional[Encryption]:
    """
    Returns the Encryption instance for the request's app, if it exists.

    :param request: the HTTP request.
    :return: the Encryption instance, or None if no key is set.
    """
    key = get_attribute_key_from_request(request)
    if key:
        return Encryption(key=key)
    else:
        return None


def _desktop_object_from_dict(request: Request, d: DesktopObjectDict | DesktopObjectDictIncludesEncrypted,
                              type_: type[DesktopObject] | None = None) -> DesktopObject:
    """
    Converts a desktop object dict to a desktop object. If the dictionary is None, None is returned.

    :param request: the HTTP request.
    :param d: the desktop object dict.
    :param type_: the type of the object to create. If None, the type key of the dictionary is used to determine the
    type of the object to create.
    :return: the object created from the dictionary.
    """
    return desktop_object_from_dict(d, type_=type_, encryption=_get_encryption_from_request(request))
