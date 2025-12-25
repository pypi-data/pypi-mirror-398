"""Connectivity to a MongoDB database for HEA resources.
"""
import io
from contextlib import AbstractContextManager, ExitStack
from uuid import uuid4 as gen_uuid

from heaserver.service.config import Configuration
from ..db.mongoexpr import mongo_expr, sub_filter_expr
from ..db.mongo import Mongo, MongoManager
from ..heaobjectsupport import RESTPermissionGroup
from mongoquery import Query
from aiohttp import web
from pymongo.results import UpdateResult, DeleteResult
from heaobject.root import DesktopObject, DesktopObjectDict, desktop_object_from_dict, to_dict, PermissionContext
from heaobject.keychain import Credentials
from heaobject.error import DeserializeException
from heaobject.user import NONE_USER
from heaobject.encryption import Encryption
from typing import AsyncGenerator, Optional, IO, Mapping, Literal, Any
from unittest.mock import MagicMock
from ..db.database import InMemoryDatabase, query_fixtures, CollectionKey
from ..aiohttp import AsyncReader
from ..response import SupportsAsyncRead
from ..db.database import query_content
from ..oidcclaimhdrs import SUB
from .mockdatabase import MockDatabase
from copy import copy
import configparser
from .util import freeze_time
from ..util import now
from collections.abc import Sequence
from pymongo.errors import DuplicateKeyError
import logging


class MockMongo(MockDatabase, InMemoryDatabase, Mongo):
    """
    Mock implementation of the Mongo class.

    It does not implement an aggregate method due the lack of good ways to mock such a thing.
    """

    def __init__(self, config: Optional[Configuration] = None,
                 mongo: Optional['MockMongo'] = None,
                 **kwargs) -> None:
        """
        Sets the db property of the app context with a motor MongoDB client instance.

        :param config: a Configuration object. MockMongo does not have a config section of its own.
        """
        super().__init__(config, **kwargs)
        if mongo is not None:
            self.add_desktop_objects(mongo.get_all_desktop_objects())
            self.add_content(mongo.get_all_content())

    async def get_credentials_from_volume(self, request: web.Request, volume_id: str) -> Credentials | None:
        return Credentials()

    async def get(self, request: web.Request, collection: str, var_parts: str | Sequence[str] | None = None, mongoattributes=None,
                  context: PermissionContext | None = None) -> Optional[dict]:
        """
        Gets an object from the database.

        :param request: the aiohttp Request object (required).
        :param collection: the Mongo DB collection (required).
        :param var_parts: the names of the dynamic resource's variable parts (required).
        :param mongoattributes: the attribute to query by. The default value is None. If None, the var_parts will be
        used as the attributes to query by.
        :param context: the permission context to use. Defaults to None.
        :return: a HEA name-value pair dict, or None if not found.
        """
        query = Query(mongo_expr(request,
                                 var_parts=var_parts,
                                 mongoattributes=mongoattributes,
                                 extra=await sub_filter_expr(permissions=RESTPermissionGroup.GETTER_PERMS.get_perms_as_strs(),
                                                                         context=context)))
        return next((d for d in self.get_desktop_objects_by_collection(collection) if query.match(d)), None)

    async def get_admin(self, collection: str, mongoattributes=None) -> DesktopObjectDict | None:
        """
        Gets an object from the database with no permissions checking.
        """
        logger = logging.getLogger(__name__)
        q = Query(mongo_expr(None, None, mongoattributes))
        logger.debug('Query is %s', q)
        return next((d for d in self.get_desktop_objects_by_collection(collection) if q.match(d)), None)

    async def get_admin_nondesktop_object(self, collection: str, mongoattributes=None) -> dict[str, Any] | None:
        logger = logging.getLogger(__name__)
        q = Query(mongo_expr(None, None, mongoattributes))
        logger.debug('Query is %s', q)
        return next((d for d in self.get_desktop_objects_by_collection(collection) if q.match(d)), None)

    async def get_content(self, request: web.Request, collection: str, var_parts: str | Sequence[str] | None = None,
                          mongoattributes=None, context: PermissionContext | None = None) -> Optional[SupportsAsyncRead]:
        """
        Handles getting a HEA object's associated content.

        :param request: the HTTP request. Required.
        :param collection: the Mongo collection name. Required.
        :param var_parts: See heaserver.service.db.mongoexpr.mongo_expr.
        :param mongoattributes: See heaserver.service.db.mongoexpr.mongo_expr.
        :param context: the permission context. Defaults to None.
        :return: a Response with the requested HEA object or Not Found.
        """
        obj = await self.get(request, collection, var_parts, mongoattributes, context)
        if obj is None:
            return None
        b = self.get_content_by_collection_and_id(collection, obj['id'])
        if b is not None:
            return AsyncReader(b)
        else:
            return None

    async def get_all(self, request: web.Request, collection: str, var_parts: str | Sequence[str] | None = None, mongoattributes=None,
                      sort: dict[str, Literal[-1, 1]] | None = None,
                      context: PermissionContext | None = None) -> AsyncGenerator[DesktopObjectDict, None]:
        """
        Handle a get request.

        :param request: the HTTP request (required).
        :param collection: the MongoDB collection containing the requested object (required).
        :param var_parts: the names of the dynamic resource's variable parts (required).
        :param mongoattributes: the attributes to query by. The default value is None. If None, the var_parts will be
        used as the attributes to query by.
        :param sort: optional sorting of result. -1 means reverse chronological order, and 1 means chronological order.
        :param context: the permission context to use. Defaults to None.
        :return: an async generator of HEA name-value pair dicts with the results of the mockmongo query.
        """
        begin = int(request.query.get('begin', 0))
        end = request.query.get('end', None)
        end_ = int(end) if end is not None else None
        query = Query(mongo_expr(request,
                                 var_parts=var_parts,
                                 mongoattributes=mongoattributes,
                                 extra=await sub_filter_expr(permissions=RESTPermissionGroup.GETTER_PERMS.get_perms_as_strs(),
                                                       context=context)))
        result = [d for d in self.get_desktop_objects_by_collection(collection) if query.match(d)]
        if sort is not None:
            if (begin > 0 or end is not None) and 'id' not in sort:
                result.sort(key=lambda x: str(x['id']))
            for attr, order in reversed(sort.items()):
                def key_fn(obj):
                    val = obj.get(attr)
                    return (val is None, val) if order == 1 else (val is not None, val)
                result.sort(key=key_fn, reverse=True if order == -1 else False)
        for i, r in enumerate(result, start=begin if begin is not None else 0):
            if end_ is not None and i >= end_:
                break
            yield r

    async def get_all_admin(self, collection: str, mongoattributes=None, sort: dict[str, Literal[-1, 1]] | None = None) -> AsyncGenerator[DesktopObjectDict, None]:
        logger = logging.getLogger(__name__)
        q = Query(mongo_expr(None, None, mongoattributes))
        logger.debug('Query is %s; sort order is %s', q, sort)
        result = [d for d in self.get_desktop_objects_by_collection(collection) if q.match(d)]
        if sort is not None:
            def sorter(obj: DesktopObjectDict):
                modified = obj.get('modified')
                if modified is not None:
                    return modified
                else:
                    return obj.get('created')
            result.sort(key=sorter, reverse=True if sort == -1 else False)
        for r in result:
            yield r

    async def upsert_admin(self, obj: DesktopObject | DesktopObjectDict, collection: str, mongoattributes: Mapping[str, Any] | None=None,
                           default_content: Optional[IO] = None, encryption: Encryption | None = None) -> str | None:
        """
        Updates a desktop object into the database, if an object with the same id or attributes is already present;
        otherwise inserts a new object. The object's content, if any, is also inserted or updated. No permission
        checking is performed.

        :param obj: the HEAObject instance to post.
        :param collection: the MongoDB collection containing the requested object (required).
        :param mongoattributes: the query parameters (optional). If omitted, this function uses obj.id to find an existing
        object.
        :param default_content: the content the HEA object will have once the object has been posted. If None, the
        object will not have content.
        :param encryption: an optional Encryption instance to use when persisting the object.
        :return: the generated id of the created object, or None if the object could not be inserted or was None.
        """

        if isinstance(obj, DesktopObject):
            obj_ = copy(obj)  # we possibly mutate the id below.
        else:
            obj_ = desktop_object_from_dict(obj)

        if mongoattributes is None and not obj_.id:
            f = None
        else:
            query = Query({'id': obj_.id} if mongoattributes is None and obj_.id else mongoattributes)
            f = next((d for d in self.get_desktop_objects_by_collection(collection) if query.match(d)), None)
        if f is None:
            if obj_.id is None:
                obj_.id = gen_uuid().hex
            self.add_desktop_objects({collection: [to_dict(obj_)]})
            if default_content is not None:
                self.add_content({collection: {obj_.id: default_content.read()}})
        else:
            self.update_desktop_object_by_collection_and_id(collection, str(f['id']), to_dict(obj_))
        return str(f['id']) if f else None

    async def upsert_admin_nondesktop_object(self, obj: dict[str, Any], collection: str, mongoattributes: Mapping[str, Any] | None=None) -> str | None:
        result = MagicMock(type=UpdateResult)
        result.raw_result = None
        result.acknowledged = True
        if mongoattributes is None and 'id' not in obj:
            match: dict[str, Any] | None = None
            id_: str | None = None
        else:
            id_ = obj.get('id')
            query = Query({'id': id_} if mongoattributes is None and id_ else mongoattributes)
            match = next((d for d in self.get_desktop_objects_by_collection(collection) if query.match(d)), None)
        if match is None:
            if id_ is None:
                obj = copy(obj)
                while True:
                    id_ = gen_uuid().hex
                    if self.get_desktop_object_by_collection_and_id(collection, id_) is None:
                        obj['id'] = id_
                        break
            self.add_desktop_objects({collection: [obj]})
        else:
            id_ = match['id']
            assert id_ is not None, 'id_ cannot be None'
            self.update_desktop_object_by_collection_and_id(collection, id_, obj)
        result.matched_count = result.modified_count = 1 if match is not None else 0

        return id_

    async def empty(self, request: web.Request, collection: str, var_parts: str | Sequence[str] | None = None, mongoattributes=None,
                    context: PermissionContext | None = None) -> bool:
        """
        Returns whether there are no results returned from the query.

        :param request: the HTTP request (required).
        :param collection: the MongoDB collection containing the requested object (required).
        :param var_parts: the names of the dynamic resource's variable parts (required).
        :param mongoattributes: the attributes to query by. The default value is None. If None, the var_parts will be
        used as the attributes to query by.
        :param context: the permission context to use. Defaults to None.
        :return: True or False.
        """
        query = Query(mongo_expr(request,
                                 var_parts=var_parts,
                                 mongoattributes=mongoattributes,
                                 extra=await sub_filter_expr(permissions=RESTPermissionGroup.GETTER_PERMS.get_perms_as_strs(),
                                                       context=context)))
        return not any(d for d in self.get_desktop_objects_by_collection(collection) if query.match(d))

    async def insert_admin(self, obj: DesktopObject | DesktopObjectDict, collection: str,
                   default_content: Optional[IO] = None, encryption: Encryption | None = None) -> str:
        """
        Handle a post request: add the object to the given collection and give it default content.

        :param request: the HTTP request (required).
        :param obj: the HEAObject instance to post.
        :param collection: the MongoDB collection containing the requested object (required).
        :param default_content: the default content to store.
        :return: the generated id of the created object, or None if obj is None or the object already exists.
        """
        if isinstance(obj, DesktopObject):
            obj_ = copy(obj)
        else:
            obj_ = desktop_object_from_dict(obj)
        while True:
            obj_.id = gen_uuid().hex  # type: ignore[misc]
            if self.get_desktop_object_by_collection_and_id(collection, obj_.id) is None:  # Object already exists
                break
        obj_.created = now()
        self.add_desktop_objects({collection: [obj_.to_dict()]})  # type: ignore
        if default_content is not None:
            self.add_content({collection: {obj_.id: default_content.read()}})
        assert obj_.id is not None, 'obj has a None id'
        return obj_.id

    async def insert_admin_nondesktop_object(self, obj: dict[str, Any], collection: str) -> str:
        obj = copy(obj)
        while True:
            id_ = gen_uuid().hex
            if self.get_desktop_object_by_collection_and_id(collection, id_) is None:  # Object already exists
                obj['id'] = id_
                break
        self.add_desktop_objects({collection: [obj]})  # type: ignore
        return id_

    async def post(self, request: web.Request, obj: DesktopObject, collection: str,
                   default_content: Optional[IO] = None, encryption: Encryption | None = None) -> str:
        """
        Handle a post request: add the object to the given collection and give it default content.

        :param request: the HTTP request (required).
        :param obj: the HEAObject instance to post.
        :param collection: the MongoDB collection containing the requested object (required).
        :param default_content: the default content to store.
        :param encryption: an optional Encryption instance to use when persisting the object.
        :return: the generated id of the created object, or None if obj is None or the object already exists.
        :raises pymongo.errors.PyMongoError: if an error occurs while persisting the object.
        """
        if obj.id is None:
            obj.id = gen_uuid().hex  # type: ignore[misc]
        f = self.get_desktop_object_by_collection_and_id(collection, obj.id)
        if f is not None:  # Object already exists
            raise DuplicateKeyError(f'Object with id {obj.id} already exists')
        else:
            self.add_desktop_objects({collection: [obj.to_dict() | {'created': now()}]})  # type: ignore
            if default_content is not None:
                self.add_content({collection: {obj.id: default_content.read()}})
            return obj.id

    async def update_admin(self, obj: DesktopObject | DesktopObjectDict, collection: str,
                           default_content: IO | None = None, encryption: Encryption | None = None) -> UpdateResult:
        """
        Update a desktop object and optionally its content in the database with no permission checking.

        :param request: the HTTP request (required).
        :param obj: the HEAObject instance to update.
        :param collection: the MongoDB collection containing the requested object (required).
        :param default_content: the default content to store.
        :return: an object with a modified_count attribute that contains the number of records updated.
        :raises pymongo.errors.PyMongoError: if an error occurs while persisting the object.
        :raises gridfs.errors.GridFSError: if an error occurs while persisting the content.
        :raises ValueError: if the object is neither a desktop object nor a desktop object dict.
        """
        result = MagicMock(type=UpdateResult)
        result.raw_result = None
        result.acknowledged = True
        if not isinstance(obj, DesktopObject):
            try:
                obj_ = desktop_object_from_dict(obj)
            except DeserializeException as e:
                raise ValueError(f'obj is neither a desktop object nor a desktop object dict: {e}') from e
        else:
            obj_ = obj
        id_ = obj_.id
        query = Query({'id': id_})
        f = next((d for d in self.get_desktop_objects_by_collection(collection) if query.match(d)), None)
        result.matched_count = result.modified_count = 1 if f is not None else 0
        if result.matched_count > 0:
            assert obj_.id is not None, 'obj has a None id'
            obj_.modified = now()
            self.update_desktop_object_by_collection_and_id(collection, obj_.id, to_dict(obj_))
            if default_content is not None:
                self.add_content({collection: {obj_.id: default_content.read()}})
        return result

    async def update_admin_nondesktop_object(self, obj: dict[str, Any], collection: str) -> UpdateResult:
        """
        Updates an arbitrary object in the database with no permission checking.

        :param obj: the object to update (required).
        :param collection: the MongoDB collection to update (required).
        :return: whether the object was successfully updated. None or UpdateResult.modified_count of 0 indicates the
        update was unsuccessful.
        """
        result = MagicMock(type=UpdateResult)
        result.raw_result = None
        result.acknowledged = True
        id_ = obj.get('id')
        query = Query({'id': id_})
        f = next((d for d in self.get_desktop_objects_by_collection(collection) if query.match(d)), None)
        result.matched_count = result.modified_count = 1 if f is not None else 0
        if result.matched_count > 0:
            assert obj['id'] is not None, 'obj has a None id'
            self.update_desktop_object_by_collection_and_id(collection, obj['id'], obj)
        return result

    async def put(self, request: web.Request, obj: DesktopObject, collection: str,
                  context: PermissionContext | None = None,
                  encryption: Encryption | None = None) -> UpdateResult | None:
        """
        Handle a put request.

        :param request: the HTTP request (required).
        :param obj: the HEAObject instance to put.
        :param collection: the MongoDB collection containing the requested object (required).
        :param context: the permission context to use. Defaults to None.
        :return: an object with a matched_count attribute that contains the number of records updated.
        """
        result = MagicMock(type=UpdateResult)
        result.raw_result = None
        result.acknowledged = True
        query = Query(mongo_expr(request,
                                 var_parts='id',
                                 extra=await sub_filter_expr(permissions=RESTPermissionGroup.PUTTER_PERMS.get_perms_as_strs(),
                                                       context=context)))
        f = next((d for d in self.get_desktop_objects_by_collection(collection) if query.match(d)), None)
        result.matched_count = result.modified_count = 1 if f is not None else 0
        obj.modified = now()
        self.update_desktop_object_by_collection_and_id(collection, request.match_info['id'], to_dict(obj))
        return result

    async def put_content(self, request: web.Request, collection: str, id_: str, display_name: str) -> bool:
        """
        Handle a put request of an HEA object's content.

        :param request: the HTTP request (required).
        :param collection: the MongoDB collection containing the requested object (required).
        :param id_: the id of the object to update (required).
        :param display_name: the display name of the object (required).
        :return: Whether or not it was successful.
        """
        buffer = io.BytesIO()
        while chunk := await request.content.read(1024):
            buffer.write(chunk)
        if buffer.getvalue() != b'The quick brown fox jumps over the lazy dog':
            return False
        self.add_content({collection: {id_: buffer.getvalue()}})
        return True

    async def delete_admin(self, collection: str, var_parts: str | Sequence[str] | None = None, mongoattributes: dict[str, Any] | None = None) -> DeleteResult | None:
        """
        Deletes an object from the database with no permission checking.

        :param collection: the MongoDB collection to update (required).
        :param mongoattributes: filter criteria.
        :return: whether objects were deleted. DeleteResult.deleted_count of 0 indicates nothing was deleted, and None
        indicates the delete was unsuccessful.
        """
        query = Query(mongo_expr(request=None, var_parts=var_parts, mongoattributes=mongoattributes))
        to_be_deleted = next((d for d in self.get_desktop_objects_by_collection(collection) if query.match(d)), None)
        result = MagicMock(type=DeleteResult)
        result.raw_result = None
        result.acknowledged = True
        if to_be_deleted is not None:
            self.remove_desktop_object_by_collection_and_id(collection, str(to_be_deleted['id']))
        result.deleted_count = 1 if to_be_deleted is not None else 0
        return result

    async def delete(self, request: web.Request, collection: str, var_parts=None, mongoattributes=None,
                     context: PermissionContext | None = None) -> DeleteResult:
        """
        Handle a delete request.

        :param request: the HTTP request.
        :param collection: the MongoDB collection containing the requested object (required).
        :param var_parts: See heaserver.service.db.mongoexpr.mongo_expr.
        :param mongoattributes: See heaserver.service.db.mongoexpr.mongo_expr.
        :param context: the permission context to use. Defaults to None.
        :return: an object with a deleted_count attribute that contains the number of records deleted.
        """
        query = Query(mongo_expr(request,
                                 var_parts=var_parts,
                                 mongoattributes=mongoattributes,
                                 extra=await sub_filter_expr(permissions=RESTPermissionGroup.DELETER_PERMS.get_perms_as_strs(),
                                                             context=context)))
        to_be_deleted = next((d for d in self.get_desktop_objects_by_collection(collection) if query.match(d)), None)
        result = MagicMock(type=DeleteResult)
        result.raw_result = None
        result.acknowledged = True
        if to_be_deleted is not None:
            self.remove_desktop_object_by_collection_and_id(collection, str(to_be_deleted['id']))
        result.deleted_count = 1 if to_be_deleted is not None else 0
        return result

    async def ping(self):
        """
        Raises an exception if the database does not respond to a ping command. The mock implementation never throws
        an exception.
        """
        pass

    def get_default_permission_context(self, request: web.Request) -> PermissionContext:
        return PermissionContext(sub=request.headers.get(SUB, NONE_USER))


class MockMongoManager(MongoManager):
    """
    Database manager for a mock of MongoDB that stores collections in memory.
    """

    def __init__(self) -> None:
        super().__init__()
        self.__mongo: Optional[MockMongo] = None

    @classmethod
    def get_context(cls) -> list[AbstractContextManager]:
        result = super().get_context()
        result.append(freeze_time())
        return result

    def start_database(self, context_manager: ExitStack) -> None:
        self.__mongo = MockMongo(managed=True)
        super().start_database(context_manager)

    def insert_desktop_objects(self, desktop_objects: Optional[Mapping[CollectionKey, Sequence[DesktopObjectDict]]]):
        super().insert_desktop_objects(desktop_objects)
        assert self.__mongo is not None
        if desktop_objects:
            self.__mongo.add_desktop_objects({k: v for k, v in query_fixtures(desktop_objects, db_manager=MockMongoManager).items() if k is not None})

    def insert_content(self, content: Optional[Mapping[CollectionKey, Mapping[str, bytes]]]):
        super().insert_content(content)
        assert self.__mongo is not None
        if content:
            self.__mongo.add_content({k: v for k, v in query_content(content, db_manager=MockMongoManager).items() if k is not None})

    def get_database(self) -> MockMongo:
        """
        Gets a mock mongo database object (only available after start_database() has been called).
        """
        if self.__mongo is None:
            raise ValueError('start_database not called')
        return self.__mongo

    def get_mongo(self) -> MockMongo | None:
        return self.__mongo
