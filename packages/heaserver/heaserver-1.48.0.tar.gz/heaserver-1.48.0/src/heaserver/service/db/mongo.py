"""Connectivity to a MongoDB database for HEA resources.

A MongoDB collection name may only be used by one microservice in a database instance. In addition, for microservices
with content, the collections <collection_name>.files and <collection_name>.chunks will be used for storing the
content. The following collection names are used by existing HEA microservices and are reserved:

folders
folder_items
data_adapters
components
properties
volumes
organizations
"""
from motor import motor_asyncio
from aiohttp import web
from copy import deepcopy

from heaserver.service.config import Configuration

from .mongoexpr import mongo_expr, sub_filter_expr
from ..heaobjectsupport import RESTPermissionGroup, HEAServerPermissionContext
from ..aiohttp import RequestFileLikeWrapper
from .database import get_file_system_and_credentials_from_volume, get_credentials_from_volume
from ..crypt import SecretDecryption
import bson
from bson.codec_options import CodecOptions
import logging
from typing import Literal, Optional, Any, IO, overload
from collections.abc import Collection, Sequence, Mapping, AsyncGenerator
from heaobject import user, root, error
from heaobject.volume import MongoDBFileSystem, FileSystem
from heaobject.keychain import Credentials
from heaobject.encryption import Encryption
from pymongo.results import UpdateResult, DeleteResult
from .database import Database, DatabaseContextManager, MicroserviceDatabaseManager
from yarl import URL
from motor.motor_asyncio import AsyncIOMotorGridFSBucket
from ..response import SupportsAsyncRead
from ..aiohttp import extract_sub
from ..oidcclaimhdrs import SUB
from gridfs.errors import NoFile
from bson import ObjectId
from heaserver.service.appproperty import HEA_DB
from typing import cast
from ..util import now
from copy import copy
from cachetools import TTLCache

_codec_options: CodecOptions = CodecOptions(tz_aware=True)


class Mongo(Database):
    """
    Connectivity to a MongoDB database for HEA resources.

    For desktop objects, creating an object in the database automatically sets its created timestamp to the current
    time in UTC. Updating an object automatically sets its modified timestamp to the current time in UTC. Any values
    for those attributes that are previously set are ignored.

    If the provided user is not a system user, the heaserver-people service may be consulted when checking permissions
    on desktop objects.
    """

    def __init__(self, config: Optional[Configuration],
                 connection_string: Optional[str] = None,
                 username: Optional[str] = None,
                 password: Optional[str] = None,
                 database_name: Optional[str] = None,
                 managed = False,
                 request: web.Request | None = None,
                 **kwargs) -> None:
        """
        Performs initialization.

        :param config: a Configuration object, which should have a MongoDB section with two properties:

                ConnectionString = the MongoDB connection string, default is http://localhost:5432
                Name = the database name, default is heaserver

                If the MongoDB section is missing or config argument is None, the default database name will be heaserver, and
                the default connection string will be http://localhost:27017.
        :param connection_string: an optional MongoDB connection string that will override any database connection
        string in a provided config file.
        :param username: an optional user name that will override any user name in the connection string.
        :param password: an optional password that will override any password in the connection string. If prefixed
        with '{crypt}', it is assumed to be encrypted and will be decrypted before use.
        :param database_name: an optional database name that will override any database name in a provided config file.
        :param managed: whether or not this database instance is managed by a DatabaseManager.
        :param request: the HTTP request that is initializing this database instance, if any.
        """
        super().__init__(config, managed=managed, request=request, **kwargs)
        logger = logging.getLogger(__name__)
        default_connection_string = 'mongodb://heauser:heauser@localhost:27017/hea'

        config_section = Mongo.get_config_section()
        if config and config_section in config.parsed_config:
            logger.debug('Parsing MongoDB section of config file')
            database_section = config.parsed_config[config_section]
            try:
                if connection_string is not None:
                    conn_url = URL(connection_string)
                else:
                    connection_string = database_section.get('ConnectionString', default_connection_string)
                    conn_url = URL(connection_string)
            except ValueError as e:
                # We wrap the original exception so we can see the URL string that caused it.
                raise ValueError(f'Error creating URL {connection_string}') from e
            if username is not None:
                conn_url = conn_url.with_user(username)
            if password is not None:
                conn_url = conn_url.with_password(password)
            if secret_decryption := ((SecretDecryption.from_request(request) if request else None) or config.get_secret_decryption()):
                logger.debug('\tDecrypting MongoDB connection string password')
                decrypted_password = secret_decryption.decrypt_config_property(conn_url.password)
                conn_url = conn_url.with_password(decrypted_password)
            logger.debug('\tUsing connection string %s', conn_url.with_password('xxxxxxxx'))
            name = database_name if database_name is not None else database_section.get('Name')
            self.__client = motor_asyncio.AsyncIOMotorClient(str(conn_url))
            logger.debug('\tUsing database %s', name or 'default from connection string')
            self.__connection_pool = self.__client.get_database(name=name)
        else:
            if connection_string is not None:
                try:
                    conn_url = URL(connection_string)
                except ValueError as e:
                    # We wrap the original exception so we can see the URL string that caused it.
                    raise ValueError(f'Error creating URL {connection_string}') from e
            else:
                conn_url = URL(default_connection_string)
            if username is not None:
                conn_url = conn_url.with_user(username)
            if password is not None:
                conn_url = conn_url.with_password(password)
            logger.debug('\tUsing connection string %s',
                         str(conn_url.with_password('xxxxxxxx')) if conn_url.password is None else str(conn_url))
            self.__client = motor_asyncio.AsyncIOMotorClient(str(conn_url), maxIdleTimeMS=30 * 1000)
            if database_name is not None:
                self.__connection_pool = self.__client.get_database(name=database_name)
            else:
                self.__connection_pool = self.__client.get_database()
        # Sub and volume-id -> credentials. We include the sub to preserve permissions.
        self.__volume_id_to_credentials: TTLCache[tuple[str, str], Credentials | None] = TTLCache(maxsize=128, ttl=30)

    @classmethod
    def get_config_section(cls) -> str:
        return 'MongoDB'

    @property
    def file_system_type(self) -> type[FileSystem]:
        return MongoDBFileSystem

    async def get_credentials_from_volume(self, request: web.Request, volume_id: str) -> Credentials | None:
        sub = extract_sub(request)
        if (credentials := self.__volume_id_to_credentials.get((sub, volume_id))) is not None:
            return credentials
        else:
            # mypy can't seem to distinguish between this method and the module-level function.
            credentials = await get_credentials_from_volume(request, volume_id, Credentials)  # type:ignore[func-returns-value]
            self.__volume_id_to_credentials[(sub, volume_id)] = credentials
            return credentials


    async def get(self, request: web.Request, collection: str, var_parts: str | Sequence[str] | None = None, mongoattributes=None,
                  context: root.PermissionContext | None = None) -> Optional[root.DesktopObjectDict]:
        """
        Gets an object from the database.

        :param request: the aiohttp Request object (required).
        :param collection: the mockmongo collection (required).
        :param var_parts: the names of the dynamic resource's variable parts.
        :param mongoattributes: the attribute to query by. The default value is None. If None, the var_parts will be
        used as the attributes to query by.
        :param context: the the permission context. Defaults to None.
        :return: a HEA name-value pair dict, or None if not found. Any encrypted attributes need to be decrypted by the
        caller.
        :raises pymongo.errors.PyMongoError: if an error occurs while getting the object from the database.
        """
        logger = logging.getLogger(__name__)
        coll = self._get_collection(collection)
        try:
            extra_ = await sub_filter_expr(permissions=RESTPermissionGroup.GETTER_PERMS.get_perms_as_strs(),
                                     context=context)
            q = Mongo.__replace_object_ids(mongo_expr(request, var_parts, mongoattributes, extra_))
            logger.debug('Query is %s', q)
            result = await coll.find_one(q)
            if result is not None:
                logger.debug('Got from mongo: %s', result)
                return self.__copy_to_dict(result)
            else:
                return None
        except bson.errors.InvalidId as e:
            logger.debug('Skipped mongo query: %s', e)
            return None

    async def get_content(self, request: web.Request, collection: str, var_parts: str | Sequence[str] | None = None, mongoattributes=None,
                          context: root.PermissionContext | None = None) -> Optional[SupportsAsyncRead]:
        """
        Handles getting a desktop object's associated content. Assumes the object's id is a URL parameter.

        :param request: the HTTP request. Required.
        :param collection: the Mongo collection name. Required.
        :param var_parts: See heaserver.service.db.mongoexpr.mongo_expr.
        :param mongoattributes: See heaserver.service.db.mongoexpr.mongo_expr.
        :param context: the permission context. Defaults to None.
        :return: an object with an async read() method and a close() method, or None if no content was found. It's up
        to the caller to close the stream when done with it.
        :raises pymongo.errors.PyMongoError: if an error occurs while getting the desktop object metadata from the
        database.
        :raises gridfs.errors.GridFSError: if an error occurs while reading the content except for
        gridfs.errors.NoFile.
        """
        obj = await self.get(request, collection, var_parts, mongoattributes, context)
        if obj is None:
            return None
        fs = self.__new_gridfs_bucket(collection)
        try:
            return await fs.open_download_stream(ObjectId(request.match_info['id']))
        except NoFile:
            return None

    async def get_all(self, request: web.Request, collection: str, var_parts=None, mongoattributes=None,
                      sort: dict[str, Literal[-1, 1]] | None = None,
                      context: root.PermissionContext | None = None) -> AsyncGenerator[root.DesktopObjectDict, None]:
        """
        Handle a get request.

        :param request: the HTTP request (required). This function uses the following query parameters, if present:
            begin: the index of the first object of the collection to return, inclusive.
            end: the index of the last object of the collection to return, exclusive.
        :param collection: the MongoDB collection containing the requested object (required).
        :param var_parts: the names of the dynamic resource's variable parts (required).
        :param mongoattributes: the attributes to query by. The default value is None. If None, the var_parts will be
        used as the attributes to query by.
        :param sort: optional properties to sort by.
        :param context: the permission context. Defaults to None.
        :return: an async generator of HEA name-value pair dicts with the results of the mockmongo query. Any encrypted
        attributes need to be decrypted by the caller.
        :raises pymongo.errors.PyMongoError: if an error occurs while getting the object from the database.
        """
        logger = logging.getLogger(__name__)
        begin = int(request.query.get('begin', 0))
        end = request.query.get('end', None)
        end_ = int(end) if end is not None else None
        coll = self._get_collection(collection)
        if var_parts is not None or mongoattributes is not None:
            q: dict[str, Any] | None = Mongo.__replace_object_ids(mongo_expr(request,
                                                      var_parts,
                                                      mongoattributes,
                                                      await sub_filter_expr(permissions=RESTPermissionGroup.GETTER_PERMS.get_perms_as_strs(),
                                                                            context=context))
                                           )
        else:
            q = await sub_filter_expr(permissions=RESTPermissionGroup.GETTER_PERMS.get_perms_as_strs(),
                                context=context)
        logger.debug('Query is %s; sort order is %s', q, sort)
        if sort is not None and (begin > 0 or end_ is not None):
            sort_: dict[str, Literal[-1, 1]] = sort | {'_id' : 1} if 'id' not in sort else {}
        else:
            sort_ = sort or {}
        cursor = coll.find(q) if not sort_ else coll.find(q).sort([(k, v) for k, v in sort_.items()])
        try:
            if begin > 0:
                cursor = cursor.skip(begin)
            if end_ is not None:
                cursor = cursor.limit(end_ - begin)
            async for result in cursor:
                logger.debug('Get all from mongo, one result at a time: %s', result)
                yield self.__copy_to_dict(result)
        finally:
            await cursor.close()

    async def empty(self, request: web.Request, collection: str, var_parts: str | Sequence[str] | None = None, mongoattributes=None,
                    context: root.PermissionContext | None = None) -> bool:
        """
        Returns whether there are no results returned from the query.

        :param request: the HTTP request (required).
        :param collection: the MongoDB collection containing the requested object (required).
        :param var_parts: the names of the dynamic resource's variable parts (required).
        :param mongoattributes: the attributes to query by. The default value is None. If None, the var_parts will be
        used as the attributes to query by.
        :param context: the permission context. Defaults to None.
        :return: True or False.
        :raises pymongo.errors.PyMongoError: if an error occurs while checking the object in the database.
        """
        logger = logging.getLogger(__name__)
        coll = self._get_collection(collection)
        if var_parts is not None or mongoattributes is not None:
            q: dict[str, Any] | None = Mongo.__replace_object_ids(mongo_expr(request,
                                                      var_parts,
                                                      mongoattributes,
                                                      await sub_filter_expr(permissions=RESTPermissionGroup.GETTER_PERMS.get_perms_as_strs(),
                                                                      context=context))
                                           )
            logger.debug('Query is %s', q)
            result = await coll.find_one(q) is None
        else:
            q = await sub_filter_expr(permissions=RESTPermissionGroup.GETTER_PERMS.get_perms_as_strs(),
                                context=context)
            logger.debug('Query is %s', q)
            result = await coll.find_one(q) is None
        logger.debug('Got from mongo: %s', result)
        return result

    async def post(self, request: web.Request, obj: root.DesktopObject, collection: str,
                   default_content: Optional[IO] = None, encryption: Encryption | None = None) -> str:
        """
        Handle a post request. The desktop object's id field is ignored, and a new id is generated by mongo.

        :param request: the HTTP request (required).
        :param obj: the HEAObject instance to post. If an encryption object is provided, any attributes that require
        encryption are encrypted before persisting them.
        :param collection: the MongoDB collection containing the requested object (required).
        :param default_content: the content the HEA object will have once the object has been posted. If None, the
        object will not have content.
        :param encryption: an optional Encryption instance to use when persisting the object.
        :return: the generated id of the created object.
        :raises pymongo.errors.PyMongoError: if an error occurs during insertion.
        :raises gridfs.errors.GridFSError: if an error occurs while writing the content.
        :raises ValueError: if the given dict is not a desktop object dict.
        """
        # Need to check if the user has permission to insert into the requested collection.
        return await self.insert_admin(obj, collection, default_content, encryption=encryption)

    async def put(self, request: web.Request, obj: root.DesktopObject, collection: str,
                  context: root.PermissionContext | None = None,
                  encryption: Encryption | None = None) -> Optional[UpdateResult]:
        """
        Handle a put request.

        :param request: the HTTP request (required).
        :param obj: the desktop object instance to put (required). The object must have been previously persisted,
        indicated by a non-None id attribute. The object is persisted with its modified attribute set to the current
        time in UTC. If an encryption object is provided, any attributes that require encryption are encrypted before
        persisting them.
        :param collection: the MongoDB collection containing the requested object (required).
        :param context: the permission context. Defaults to None.
        :param encryption: an optional Encryption instance to use when persisting the object.
        :return: an instance of pymongo.results.UpdateResult or None. If the object was not found, either None is
        returned, or the UpdateResult has an updated_count of 0.
        :raises pymongo.errors.PyMongoError: if an error occurs during persistence.
        :raises ValueError: if the given dict is not a desktop object dict or does not have an id property, or if the
        given desktop object has a None id attribute.
        """
        coll = self._get_collection(collection)
        if obj.id is None:
            raise ValueError('Object must have an id')
        obj_ = copy(obj)
        obj_.modified = now()
        try:
            extra_ = await sub_filter_expr(permissions=RESTPermissionGroup.PUTTER_PERMS.get_perms_as_strs(),
                                           context=context)
            mongo_expr_ = Mongo.__replace_object_ids(mongo_expr(request, 'id', extra=extra_))
            return await coll.replace_one(mongo_expr_, replace_id_with_object_id(obj_.to_dict(encryption=encryption)))
        except bson.errors.InvalidId:
            return None

    async def put_content(self, request: web.Request, collection: str, id_: str, display_name: str) -> bool:
        """
        Handle a put request of an HEA object's content.

        :param request: the HTTP request containing the content (required).
        :param collection: the MongoDB collection containing the requested object (required).
        :param id_: the id of the object to update (required).
        :param display_name: the display name of the object (required).
        :return: Whether or not it was successful.
        :raises gridfs.errors.GridFSError: if an error occurs while writing the content.
        :raises pymongo.errors.PyMongoError: if an error occurs during desktop object persistence.
        """
        try:
            fs = self.__new_gridfs_bucket(collection)
            fileobj = RequestFileLikeWrapper(request)
            fileobj.initialize()
            try:
                await fs.upload_from_stream_with_id(ObjectId(id_), display_name, fileobj)
            finally:
                fileobj.close()
            return True
        except bson.errors.InvalidId:
            return False
        except NoFile:
            # Delete orphaned chunks from gridfs if an error occurred
            raise

    async def delete(self, request: web.Request, collection: str, var_parts: str | Sequence[str] | None = None, mongoattributes: dict[str, Any] | None = None,
                     context: root.PermissionContext | None = None) -> Optional[DeleteResult]:
        """
        Handle a delete request.

        :param request: the HTTP request.
        :param collection: the MongoDB collection containing the requested object (required).
        :param var_parts: See heaserver.service.db.mongoexpr.mongo_expr.
        :param mongoattributes: See heaserver.service.db.mongoexpr.mongo_expr.
        :param context: the permission context. Defaults to None.
        :return: an instance of pymongo.results.DeleteResult. DeleteResult.deleted_count of 0 or None indicates the
        object was not found.
        :raises pymongo.errors.PyMongoError: if an error occurs while deleting the desktop object.
        :raises gridfs.errors.GridFSError: if an error occurs while deleting the desktop object's content.
        """
        coll = self._get_collection(collection)
        try:
            mongo_expr_ = await self.__mongo_expr(request, RESTPermissionGroup.DELETER_PERMS.perms,
                                                  var_parts, mongoattributes, context)
            result = await coll.find_one_and_delete(mongo_expr_)
            if result is not None:
                res = DeleteResult(raw_result={'n': 1}, acknowledged=True)
                fs = self.__new_gridfs_bucket(collection)
                try:
                    await fs.delete(result['_id'])
                    return res
                except NoFile:
                    return res
            else:
                return DeleteResult(raw_result={'n': 0}, acknowledged=True)
        except bson.errors.InvalidId:
            return None

    async def delete_admin(self, collection: str, var_parts: str | Sequence[str] | None = None, mongoattributes: dict[str, Any] | None = None) -> DeleteResult | None:
        """
        Deletes an object from the database with no permission checking.

        :param collection: the MongoDB collection to update (required).
        :param mongoattributes: filter criteria (required).
        :return: whether object deletion was successful. DeleteResult.deleted_count of 0 or None indicates the object
        was not found.
        :raises pymongo.errors.PyMongoError: if an error occurs while deleting the desktop object.
        :raises gridfs.errors.GridFSError: if an error occurs while deleting the desktop object's content.
        """
        logger = logging.getLogger(__name__)
        coll = self._get_collection(collection)
        try:
            q = Mongo.__replace_object_ids(mongo_expr(None,
                                                      var_parts,
                                                      mongoattributes))
            logger.debug('Query is %s', q)
            result_ = await coll.find_one_and_delete(q)
            if result_ is not None:
                res = DeleteResult(raw_result={'n': 1}, acknowledged=True)
                fs = self.__new_gridfs_bucket(collection)
                try:
                    await fs.delete(result_['_id'])
                    return res
                except NoFile:
                    return res
            else:
                return DeleteResult(raw_result={'n': 0}, acknowledged=True)
        except bson.errors.InvalidId:
            return None

    async def get_admin(self, collection: str, mongoattributes=None) -> root.DesktopObjectDict | None:
        """
        Gets a desktop object from the database with no permissions checking.

        :param collection: the MongoDB collection containing the requested object (required).
        :param mongoattributes: filter criteria. Omit or set to None to use the object's id.
        :return: a desktop object dict, or None if not found. Any encrypted attributes must be decrypted by the caller.
        :raises pymongo.errors.PyMongoError: if an error occurs while deleting the desktop object.
        """
        logger = logging.getLogger(__name__)
        coll = self._get_collection(collection)
        try:
            q = Mongo.__replace_object_ids(mongo_expr(None,
                                                      None,
                                                      mongoattributes))
            logger.debug('Query is %s', q)
            result = await coll.find_one(q)
            if result is not None:
                logger.debug('Got from mongo: %s', result)
                return self.__copy_to_dict(result)
            else:
                return None
        except bson.errors.InvalidId:
            return None

    async def get_admin_nondesktop_object(self, collection: str, mongoattributes=None) -> dict[str, Any] | None:
        """
        Gets an object from the database with no permissions checking.

        :param collection: the MongoDB collection containing the requested object (required).
        :param mongoattributes: filter criteria. Omit or set to None to use the object's id property.
        :return: a dict representing the object, or None if not found. Any encrypted attributes must be decrypted by
        the caller.
        :raises pymongo.errors.PyMongoError: if an error occurs while getting the object from the database.
        """
        logger = logging.getLogger(__name__)
        coll = self._get_collection(collection)
        try:
            q = Mongo.__replace_object_ids(mongo_expr(None,
                                                      None,
                                                      mongoattributes))
            logger.debug('Query is %s', q)
            result = await coll.find_one(q)
            if result is not None:
                logger.debug('Got from mongo: %s', result)
                return dict({'id' if k == '_id' else k: str(v) if k == '_id' else v for k, v in result.items()})
            else:
                return None
        except bson.errors.InvalidId:
            return None

    async def get_all_admin(self, collection: str, mongoattributes=None, sort: dict[str, Literal[-1, 1]] | None = None) -> AsyncGenerator[root.DesktopObjectDict, None]:
        """
        Gets all matching desktop objects from the database with no permissions checking.

        :param collection: the MongoDB collection containing the requested object (required).
        :param mongoattributes: filter criteria, if any.
        :return: a async generator of desktop object dicts representing the objects, if any are found. Any encrypted
        attributes must be decrypted by the caller.
        :raises pymongo.errors.PyMongoError: if an error occurs while getting the objects from the database.
        """
        logger = logging.getLogger(__name__)
        coll = self._get_collection(collection)
        q = Mongo.__replace_object_ids(mongo_expr(None, None, mongoattributes))
        logger.debug('Query is %s; sort order is %s', q, sort)
        cursor = coll.find(q) if sort is None else coll.find(q).sort([(k, v) for k, v in sort.items()])
        try:
            async for result in cursor:
                logger.debug('Get all from mongo: %s', result)
                yield self.__copy_to_dict(result)
        finally:
            await cursor.close()

    async def upsert_admin(self, obj: root.DesktopObject | root.DesktopObjectDict, collection: str,
                           mongoattributes: Mapping[str, Any] | None=None,
                           default_content: Optional[IO] = None, encryption: Encryption | None = None) -> str | None:
        """
        Updates a desktop object into the database, if an object with the same id or attributes is already present;
        otherwise inserts a new object. The object's content, if any, is also inserted or updated. No permission
        checking is performed.

        :param obj: the HEAObject instance to post.
        :param collection: the MongoDB collection containing the requested object (required).
        :param mongoattributes: filter criteria.  If present, these criteria are used to match the provided object
        to an existing one, and for any matches the _id properties must match. If the the matching provided object has
        no _id property, an _id will be added. If not present, a match is made solely on the provided object's _id
        property.
        :param default_content: the content the HEA object will have once the object has been posted. If None, the
        object will not have content. If trying to post content, obj must have a display_name attribute.
        :param encryption: an optional Encryption instance to use when persisting the object.
        :return: the generated id of the created or updated object, or None if the object could not be inserted or was
        None.
        :raises pymongo.errors.PyMongoError: if an error occurs while persisting the object.
        :raises ValueError: if the given object is neither a desktop object nor a desktop object dict.
        """
        try:
            if isinstance(obj, root.DesktopObject):
                obj_ = obj
            else:
                obj_ = root.desktop_object_from_dict(obj)
            coll = self._get_collection(collection)
            if mongoattributes is None and not obj_.id:
                inserted_result = await coll.insert_one(obj_.to_dict(encryption=encryption))
                if inserted_result and default_content is not None:
                    fs = self.__new_gridfs_bucket(collection)
                    await fs.upload_from_stream_with_id(inserted_result.inserted_id, obj_.display_name, default_content)
                return str(inserted_result.inserted_id)
            else:
                upserted_result = await coll.replace_one({'_id': ObjectId(obj_.id)} if mongoattributes is None else mongoattributes,
                                                         self.__replace_object_ids(obj_.to_dict(encryption=encryption)), upsert=True)
                if upserted_result and default_content is not None:
                    fs = self.__new_gridfs_bucket(collection)
                    await fs.upload_from_stream_with_id(upserted_result.upserted_id, obj_.display_name, default_content)
                return str(upserted_result.upserted_id)
        except error.DeserializeException as e:
            raise ValueError(f'Error parsing desktop object dictionary {obj}') from e

    async def upsert_admin_nondesktop_object(self, obj: dict[str, Any], collection: str,
                                             mongoattributes: Mapping[str, Any] | None=None) -> str | None:
        """
        Updates an arbitrary object into the database, if an object with the same id or attributes is already present;
        otherwise inserts a new object. No permission checking is performed.

        :param obj: the dictionary to post. Any data that should be encrypted must be encrypted by the caller.
        :param collection: the MongoDB collection containing the requested object (required).
        :param mongoattributes: filter criteria. If present, these criteria are used to match the provided object
        to an existing one, and for any matches the _id properties must match. If the the matching provided object has
        no _id property, an _id will be added. If not present, a match is made solely on the provided object's _id
        property.
        :return: the generated id of the created object, or None if the object could not be inserted or was None.
        :raises pymongo.errors.PyMongoError: if an error occurs while persisting the object.
        :raises ValueError: if the given object or dict has invalid data.
        """
        try:
            coll = self._get_collection(collection)
            if mongoattributes is None and 'id' not in obj:
                inserted_result = await coll.insert_one(obj)
                return str(inserted_result.inserted_id)
            else:
                upserted_result = await coll.replace_one({'_id': ObjectId(obj['id'])} if mongoattributes is None else mongoattributes,
                                                         self.__replace_object_ids(obj), upsert=True)
                return str(upserted_result.upserted_id)
        except bson.errors.InvalidId as e:
            raise ValueError(f'Object {obj} has invalid id attribute {obj.get("id")}') from e

    async def insert_admin(self, obj: root.DesktopObject | root.DesktopObjectDict, collection: str,
                           default_content: Optional[IO] = None, encryption: Encryption | None = None) -> str:
        """
        Inserts a desktop object into the database, with its content if provided, and with no permission checking. The
        desktop object's id field is ignored, and a new id is generated by mongo. It encrypts any encrypted attributes
        before persisting the object if an Encryption instance is provided.

        :param obj: the HEAObject or HEAObjectDict instance to post.
        :param collection: the MongoDB collection containing the requested object (required).
        :param default_content: the content the desktop object will have once the object has been posted. If None, the
        object will not have content. If trying to post content, obj must have a display_name attribute.
        :param encryption: an optional Encryption instance to use when persisting the object.
        :return: the generated id of the created object, or None if the object could not be inserted or was None.
        :raises pymongo.errors.PyMongoError: if an error occurs during insertion.
        :raises gridfs.errors.GridFSError: if an error occurs while writing the content.
        :raises ValueError: if the given object is neither a desktop object nor a desktop object dict.
        """
        if isinstance(obj, root.DesktopObject):
            obj_ = copy(obj)  # The created and id attributes are mutated below.
        else:
            try:
                obj_ = root.desktop_object_from_dict(obj)
            except error.DeserializeException as e:
                raise ValueError(f'Error parsing desktop object dictionary {obj}') from e
        obj_.created = now()
        obj_.id = None
        coll = self._get_collection(collection)
        result = await coll.insert_one(document=obj_.to_dict(encryption=encryption))
        if result and default_content is not None:
            fs = self.__new_gridfs_bucket(collection)
            await fs.upload_from_stream_with_id(ObjectId(result.inserted_id), obj_.display_name, default_content)
        return str(result.inserted_id)


    async def insert_admin_nondesktop_object(self, obj: dict[str, Any], collection: str) -> str:
        """
        Inserts an object into the database with no permission checking. The dict's id property, if any, is ignored.

        :param obj: the dict to insert (required). Any data that should be encrypted must be encrypted by the caller.
        :param collection: the MongoDB collection to insert into (required).
        :return: the generated id of the created object.
        :raises pymongo.errors.PyMongoError: if an error occurs during insertion.
        """
        coll = self._get_collection(collection)
        if 'id' in obj:
            obj = copy(obj)
            del obj['id']
        result = await coll.insert_one(document=obj)
        return str(result.inserted_id)


    async def update_admin(self, obj: root.DesktopObject | root.DesktopObjectDict, collection: str,
                           default_content: Optional[IO] = None, encryption: Optional[Encryption] = None) -> UpdateResult:
        """
        Updates a desktop object in the database, with its content if provided, and with no permission checking.

        :param obj: the HEAObject instance to update (required). The object must have been persisted previously,
        indicated by a non-None id attribute. The object is persisted with its modified attribute set to the current
        time in UTC. If an encryption object is provided, any encrypted attributes will be encrypted before
        persisting them.
        :param collection: the MongoDB collection to update (required).
        :param default_content: the content the HEA object will have once the object has been posted. If None, the
        object will not have content.
        :param encryption: an optional Encryption instance to use for encrypting the object's attributes.
        :return: whether the object was successfully updated. UpdateResult.modified_count of 0 indicates the
        update was unsuccessful.
        :raises pymongo.errors.PyMongoError: if an error occurs during persistence.
        :raises gridfs.errors.GridFSError: if an error occurs while writing the content.
        :raises ValueError: if the given object is neither a desktop object nor a desktop object dict.
        """
        if isinstance(obj, root.DesktopObject):
            obj_ = copy(obj)  # we mutate the modified attribute below
        else:
            try:
                obj_ = root.desktop_object_from_dict(obj)
            except error.DeserializeException as e:
                raise ValueError(f'Error parsing desktop object dictionary {obj}') from e
        if obj_.id is None:
            raise ValueError('Object must have an id')
        obj_.modified = now()
        obj_dict = obj_.to_dict(encryption=encryption)
        coll = self._get_collection(collection)
        filter = {'_id': ObjectId(obj_.id)}
        del obj_dict['id']
        result = await coll.replace_one(filter, obj_dict)
        if result and default_content is not None:
            fs = self.__new_gridfs_bucket(collection)
            await fs.upload_from_stream_with_id(ObjectId(obj_.id), obj_.display_name, default_content)
        return result

    async def update_admin_nondesktop_object(self, obj: dict[str, Any], collection: str) -> UpdateResult:
        """
        Updates an arbitrary object in the database with no permission checking.

        :param obj: the object to update (required). It must have an id property but otherwise does not have to
        resemble a desktop object's structure. Any data that should be encrypted must be encrypted by the caller.
        :param collection: the MongoDB collection to update (required).
        :return: whether the object was successfully updated. UpdateResult.modified_count of 0 indicates the
        update was unsuccessful.
        :raises pymongo.errors.PyMongoError: if an error occurs during persistence.
        :raises KeyError: if the given dict does not have an id property.
        """
        coll = self._get_collection(collection)
        filter = {'_id': ObjectId(obj['id'])}
        result = await coll.replace_one(filter, obj)
        return result

    async def aggregate(self, collection: str, pipeline: Sequence[Mapping[str, Any]], *args, **kwargs) -> AsyncGenerator[root.DesktopObjectDict, None]:
        """
        Execute the provided aggregate pipeline on a collection. Aggregate command parameters should be passed as
        keyword arguments to this method. Unlike the other methods that return desktop object dictionaries, this one
        does not ignore id properties returned from mongo, nor does it assume there is an _id ObjectId property and
        convert it to a str id property.

        :param collection: the name of the collection (required).
        :param pipeline: the pipeline (required).
        :return: the returned documents. Any encrypted attributes must be decrypted by the caller.
        """
        coll = self._get_collection(collection)
        agg = coll.aggregate(pipeline, *args, **kwargs)
        try:
            async for doc in agg:
                yield {k: v for k, v in doc.items()}
        finally:
            await agg.close()

    def get_default_permission_context(self, request: web.Request) -> root.PermissionContext:
        return HEAServerPermissionContext(request.headers.get(SUB, user.NONE_USER), request)

    async def ping(self):
        """
        Raises an exception if the database does not respond to a ping command.
        """
        await self.__connection_pool.command('ping')

    def really_close(self):
        """Closes the MongoDB client connection, and it also calls the superclass' really_close method."""
        super().really_close()
        self.__client.close()

    def close(self):
        """Skips closing the MongoDB client connection if this is a managed Mongo instance. It also closes the
        superclass' close method."""
        super().close()
        if not self.managed:
            self.__client.close()

    def __copy_to_dict(self, result: Mapping[str, Any]) -> root.DesktopObjectDict:
        return dict({'id' if k == '_id' else k: str(v) if k == '_id' else v for k, v in result.items() if k != 'id'})

    def _get_collection(self, collection: str) -> motor_asyncio.AsyncIOMotorCollection:
        """
        Get the requested collection object.

        :param collection: the name of the collection to get.
        :return: the collection object.
        """
        return self.__connection_pool.get_collection(collection, codec_options=_codec_options)

    @staticmethod
    async def __mongo_expr(request: web.Request,
                           perms: Collection[root.Permission],
                           var_parts=None,
                           mongoattributes=None,
                           context: root.PermissionContext | None = None) -> dict[str, Any]:
        perms_ = [perm.name for perm in perms]
        extra_ = await sub_filter_expr(permissions=perms_, context=context)
        return Mongo.__replace_object_ids(mongo_expr(request, var_parts, mongoattributes, extra_))

    @staticmethod
    def __replace_object_ids(filter_criteria: dict[str, Any]) -> dict[str, Any]:
        """
        Replaces all "id" fields with string value with an "_id" field with its bson.objectid.ObjectId value.

        :param filter_criteria: a MongoDB filter
        :return: a deep copy of the same filter, with string id fields replaced with ObjectId _id fields.
        :raises bson.errors.InvalidId: if any id fields are not a 12-byte input or a 24-character hex string.
        """
        logger = logging.getLogger(__name__)
        logger.debug('Input: %s', filter_criteria)

        def do_replace(filter_criteria_: dict[str, Any]):
            result_ = {}
            for nm, val in filter_criteria_.items():
                if nm == 'id':
                    if val is not None:
                        result_['_id'] = ObjectId(val)
                    result_.pop('id', None)
                elif isinstance(val, dict):
                    result_[nm] = do_replace(val)
                else:
                    result_[nm] = deepcopy(val)
            return result_

        result = do_replace(filter_criteria)
        logger.debug('Output: %s', result)
        return result

    def __new_gridfs_bucket(self, bucket: str) -> AsyncIOMotorGridFSBucket:
        return AsyncIOMotorGridFSBucket(self.__connection_pool, bucket)


def replace_id_with_object_id(obj: dict[str, Any]):
    """
    Returns a shallow copy of the provided dict with any id key replaced by an _id key with an ObjectId value.
    :param obj: a HEA object as a dict.
    :return: a newly created dict.
    """
    if 'id' in obj:
        f_ = dict(obj)
        f_['_id'] = bson.ObjectId(f_.pop('id', None))
        return f_
    else:
        return dict(obj)


class MongoManager(MicroserviceDatabaseManager):
    """
    Database manager for a MongoDB database.
    """

    def __init__(self, config: Configuration | None = None):
        super().__init__(config)

    def get_database(self) -> Mongo:
        return Mongo(config=self.config, managed=True)

    @classmethod
    def get_environment_updates(cls) -> dict[str, str]:
        """
        Returns any environment variables that need to be given to the mongo docker container.

        :return: a dictionary of environment variable names to values.
        """
        result = super().get_environment_updates()
        result['MONGO_DB'] = 'hea'
        return result

    @classmethod
    def database_types(self) -> list[str]:
        return ['system|mongo']


class MongoContext(DatabaseContextManager[Mongo, Credentials]): # Go into db package?
    """
    Provides a Mongo database client object as the 'connection', since in the python motor driver the client object
    abstracts away connections. If neither a volume nor a credentials object is passed into the constructor, the
    connection string in the microservice's configuration file will be used, otherwise it will use the default
    localhost connection string.
    """

    async def connection(self) -> Mongo:
        return await _get_mongo(self.request, self.volume_id)


async def _get_mongo(request: web.Request, volume_id: Optional[str]) -> Mongo:
    """
    Gets a mongo client.

    :param request: the HTTP request (required).
    :param volume_id: the id string of a volume.
    :return: a Mongo client for the file system specified by the volume's file_system_name attribute. If no volume_id
    was provided, the return value will be the "default" Mongo client for the microservice found in the HEA_DB
    application-level property. If the default Mongo client is used, its close method will do nothing since it's closed
    on microservice shutdown.
    :raise ValueError: if there is no volume with the provided volume id, the volume's file system does not exist,
    or a necessary service is not registered.
    """

    if volume_id is not None:
        file_system, credentials = await get_file_system_and_credentials_from_volume(request, volume_id, MongoDBFileSystem)
        if credentials is None:
            return Mongo(None, connection_string=file_system.connection_string, request=request)
        else:
            return Mongo(None, connection_string=file_system.connection_string, username=credentials.account,
                         password=credentials.password, request=request)
    else:
        return cast(Mongo, request.app[HEA_DB])
