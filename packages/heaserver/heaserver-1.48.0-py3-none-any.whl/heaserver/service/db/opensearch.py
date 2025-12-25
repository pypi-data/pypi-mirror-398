import asyncio
import logging
from typing import Optional, TypeVar, Any, AsyncGenerator

import opensearchpy
from aiohttp import web
from cachetools import TTLCache
from heaobject.error import DeserializeException
from heaobject.keychain import Credentials
from heaobject.root import HEAObjectDict, json_dumps
from heaobject.volume import OpenSearchFileSystem, FileSystem
from opensearchpy import AsyncOpenSearch, RequestError, NotFoundError
from heaserver.service.aiohttp import extract_sub
from heaserver.service.appproperty import HEA_DB
from heaserver.service.config import Configuration
from heaserver.service.db.aws import S3
from heaserver.service.db.database import Database, DatabaseContextManager, MicroserviceDatabaseManager, \
    get_file_system_and_credentials_from_volume, get_credentials_from_volume
from heaobject.folder import Item

from heaserver.service.db.mongo import Mongo

from heaserver.service.testcase.util import run_coroutine_in_new_event_loop

CONFIG_SECTION="Opensearch"

ItemTypeVar = TypeVar('ItemTypeVar', bound=Item)

class OpenSearch(Database):

    def __init__(self, config: Configuration | None,
                 host: str | None = None,
                 port: int | None = None,
                 use_ssl: bool | None = False,
                 verify_certs: bool | None = False,
                 index: str | None = None,
                 username: str | None = None,
                 password: str | None = None,
                 **kwargs):
        """
        Initializes the OpenSearch client and stores configuration parameters.

        :param host: host of opensearch microservice
        :param port: port of opensearch microservice
        :param use_ssl: Whether to use SSL for the connection.
        :param verify_certs: Whether to verify SSL certificates.
        :param index_name: The name of the index to act upon.
        """
        super().__init__(config, **kwargs)
        self.__host = host
        self.__port = port
        self.__use_ssl = use_ssl
        self.__verify_certs = verify_certs
        self.__index = index
        self.__scroll_ids: list[str] = []  # Keep track of scroll IDs
        self.__volume_id_to_credentials: TTLCache[tuple[str, str], Credentials | None] = TTLCache(maxsize=128, ttl=30)
        self.__username = username
        self.__password = password

        if config and CONFIG_SECTION in config.parsed_config:
            _section = config.parsed_config[CONFIG_SECTION]
            self.__host = _section.get('Hostname', fallback=self.__host)
            self.__port = _section.getint( 'Port', fallback=self.__port)
            self.__use_ssl = _section.getboolean('UseSSL', fallback=self.__use_ssl)
            self.__verify_certs = _section.getboolean('VerifyCerts', fallback=self.__verify_certs)
            self.__index = _section.get('Index', fallback=self.__index)
            self.__username = _section.get('Username', fallback=self.__username)
            self.__password = _section.get('Password', fallback=self.__password)

        self.__client = AsyncOpenSearch(
            hosts=[{'host': self.__host, 'port': self.__port}],
            http_auth=(self.__username, self.__password) if self.__username and self.__password else None,
            use_ssl=self.__use_ssl,
            verify_certs=self.__verify_certs,
        )

    @property
    def file_system_type(self) -> type[FileSystem]:
        return OpenSearchFileSystem

    async def get_credentials_from_volume(self, request: web.Request, volume_id: str) -> Credentials | None:
        sub = extract_sub(request)
        if (credentials := self.__volume_id_to_credentials.get((sub, volume_id))) is not None:
            return credentials
        else:
            # mypy can't seem to distinguish between this method and the module-level function.
            credentials = await get_credentials_from_volume(request, volume_id, Credentials)  # type:ignore[func-returns-value]
            self.__volume_id_to_credentials[(sub, volume_id)] = credentials
            return credentials

    def __filter_doc_fields(self, doc: HEAObjectDict, mapping: dict) -> dict:
        """
        Filters a document to include only fields that exist in the index mapping.

        :param doc: The original document to filter.
        :param mapping: The mapping of the index.
        :return: A new document containing only the fields that are present in the mapping.
        """

        properties = mapping.get("properties", {})
        filtered_doc: dict[str, Any] = {}

        for key, value in doc.items():
            if key in properties:
                field_type = properties[key].get("type")
                if field_type == "text" and isinstance(value, str):
                    filtered_doc[key] = value
                elif field_type == "keyword" and isinstance(value, str):
                    filtered_doc[key] = value
                elif field_type == "integer" and isinstance(value, int):
                    filtered_doc[key] = value
                elif field_type == "boolean" and isinstance(value, bool):
                    filtered_doc[key] = value
                elif field_type == "float" and isinstance(value, (int, float)):
                    filtered_doc[key] = float(value)
                elif value is None:
                    filtered_doc[key] = None
                # Add more type checks if needed for specific field types
        return filtered_doc

    async def _get_index_mapping(self, index: str | None) -> dict :
        """
        Retrieves the mapping of the specified OpenSearch index.

        :param index: The name of the index.
        :return: The mapping of the index as a dictionary.
        """
        try:
            response = await self.__client.indices.get_mapping(index=index)
        except opensearchpy.TransportError as te:
            raise te
        return response.get(index, {}).get("mappings", {})

    async def create_index(self, index: Optional[str] = None, body: Optional[dict] = None) -> bool:
        """
        Creates an OpenSearch index.

        :param index: The name of the index to create. Defaults to the class variable __index.
        :param body: (Optional) A dictionary specifying the index settings and mappings.
        :return: True if the index was created successfully, False otherwise.
        :raises ValueError: If no index name is provided or the class variable __index is not defined.
        """
        if not index and not self.__index:
            raise ValueError("Index name must be provided.")
        idx = index if index else self.__index

        try:
            await self.__client.indices.create(index=idx, body=body)
            return True
        except opensearchpy.RequestError as e:
            if e.error == "resource_already_exists_exception":
                logging.warning(f"Index '{idx}' already exists.")
            else:
                raise e
        return False


    async def delete_index(self, index: str | None = None) -> bool:
        """
        Deletes an OpenSearch index.

        :param index: The name of the index to delete. Defaults to the class variable __index.
        :return: True if the index was deleted successfully, False otherwise.
        :raises ValueError: If no index name is provided or the class variable __index is not defined.
        """
        if not index and not self.__index:
            raise ValueError("Index name must be provided.")
        idx = index if index else self.__index

        try:
            await self.__client.indices.delete(index=idx)
            return True
        except opensearchpy.NotFoundError:
            logging.warning(f"Index '{idx}' does not exist.")
        return False

    async def insert(self, doc: HEAObjectDict, index: str | None = None) -> Optional[str]:
        """
        Updates or inserts a document in the specified OpenSearch index.

        :param doc: The document data to be inserted or updated. If the document contains an `id` field,
                    it will be used as the document ID. Otherwise, a new ID will be generated.
        :param index: (Optional) The name of the OpenSearch index where the document should be updated.
                      If not provided, the default index will be used.

        :return: The ID of the updated or inserted document, or `None` if the operation failed.

        :raises ValueError: Raised if the `index` parameter is not provided.
        :raises Exception: Raised for any other errors encountered during the update operation.
        """
        logger = logging.getLogger(__name__)
        try:
            if not index and not self.__index:
                raise ValueError("Index name must be provided.")
            idx = index if index else self.__index
            # Fetch index mapping
            mapping = await self._get_index_mapping(idx)

            # Filter document fields based on the mapping
            logger.debug(f"mapping: {mapping}" )
            doc_id = doc.get('id', None)
            filtered_doc = self.__filter_doc_fields(doc, mapping)

            response = await self.__client.index(
                index=idx,
                id=doc_id,
                body=filtered_doc,
                refresh=True  # Optional: Refresh the index to make the change immediately searchable
            )
            return response["_id"]
        except Exception as e:
            logger.debug(f"Failed to update document: {e}")
            return None

    async def batch_insert(self, bulk_doc_gen: AsyncGenerator[ItemTypeVar, None]) -> bool:
        """
        Insert multiple documents into the index in bulk.
        :param bulk_doc_gen: An asynchronous generator of documents to be inserted.
        :return: True if all documents were successfully inserted, False otherwise.
        """
        return await self.__batch_operation(bulk_doc_gen, action_type="index")

    async def batch_delete(self, bulk_doc_ids: AsyncGenerator[str, None]) -> bool:
        """
        Delete multiple documents from the index in bulk.
        :param bulk_doc_ids: An asynchronous generator of document IDs to be deleted.
        :return: True if all documents were successfully deleted, False otherwise.
        """
        return await self.__batch_operation(bulk_doc_ids, action_type="delete")

    async def __batch_operation(self, bulk_gen: AsyncGenerator[Any, None], action_type: str) -> bool:
        """
        Perform bulk operations (insert/delete) on the index.
        :param bulk_gen: An asynchronous generator of documents or document IDs.
        :param action_type: The type of bulk operation ('index' for insert, 'delete' for delete).
        :return: True if the operation was successful, False otherwise.
        """
        logger = logging.getLogger(__name__)
        success = False
        try:
            actions = []
            async for item in bulk_gen:
                if action_type == "index":
                    action = {"index": {"_index": self.__index, "_id": item.id}}
                    actions.append(f"{json_dumps(action)}\n{json_dumps(item.to_dict())}")
                elif action_type == "delete":
                    action = {"delete": {"_index": self.__index, "_id": item}}
                    actions.append(json_dumps(action))
                else:
                    raise ValueError(f"Unsupported action type: {action_type}")

                # Send in batches of 1000 for efficiency
                if len(actions) >= 1000:
                    bulk_body = "\n".join(actions) + "\n"
                    response = await self.__client.bulk(body=bulk_body)
                    if response["errors"]:
                        raise ValueError(f"Some documents failed during batch {action_type}.")
                    actions.clear()

            # Process remaining items if any
            if actions:
                bulk_body = "\n".join(actions) + "\n"
                response = await self.__client.bulk(body=bulk_body)
                if response["errors"]:
                    logger.debug("Some documents failed during batch %s." % action_type)
                    return False
            success = True
        except RequestError as re:
            logger.exception("Failed to perform bulk operation: %s", re)
            success = False
        except Exception as e:
            logger.exception("Failed to perform bulk operation: %s", e)
            success = False
        return success

    async def get_doc(self, item_id: str, search_item_type: type[ItemTypeVar], index: str | None = None) -> ItemTypeVar | None:
        """
        Fetch a single item from OpenSearch by its document ID.

        :param item_id: The ID of the document to retrieve.
        :param search_item_type: The type used to deserialize the document.
        :param index: (Optional) the index to query against.
        :return: A single deserialized item or None if not found.
        """
        try:
            if not index and not self.__index:
                raise ValueError("Index name must be provided.")
            idx = index if index else self.__index

            response = await self.__client.get(index=idx, id=item_id)
            if "_source" not in response:
                return None

            item = search_item_type()
            response["_source"]["id"] = response["_id"]
            response["_source"]["type"] = item.get_type_name()
            item.from_dict(response["_source"])
            return item

        except NotFoundError:
            return None  # Let caller handle missing doc case cleanly
        except Exception as e:
            logging.exception(f"Unexpected error getting item {item_id}: {e}")
            raise



    async def search(self, query: dict, search_item_type: type[ItemTypeVar],
                     index: str | None = None,
                     max_results: int = 1000,
                     size: int = 100
                     ) -> list[ItemTypeVar]:
        """
        Perform a paginated search with a maximum limit of results.

        :param search_item_type: The type used to deserialize the documents.
        :param index: The OpenSearch index to query.
        :param query: The query dictionary.
        :param size: Number of results per page.
        :param max_results: The maximum number of results to retrieve.
        :return: A list of documents matching the query.
        """
        search_items = []
        total_results = 0
        from_offset = 0  # Used for pagination

        try:
            while total_results < max_results:
                paginated_query = {
                    **query,
                    "from": from_offset,
                    "size": size,
                    "sort": [{"_doc": {"order": "asc"}}]  # Ensures consistent ordering for pagination
                }

                response = await self.__client.search(index=index, body=paginated_query)
                hits = response.get("hits", {}).get("hits", [])

                if not hits:
                    break  # No more results

                for hit in hits:
                    hit_id = hit["_id"]
                    if "_source" in hit:
                        search_item = search_item_type()
                        hit["_source"]["id"] = hit_id
                        hit["_source"]["type"] = search_item.get_type_name()
                        search_item.from_dict(hit["_source"])
                        search_items.append(search_item)
                        total_results += 1

                        if total_results >= max_results:
                            break  # Stop if max limit reached

                from_offset += size  # Move to next batch

        except DeserializeException as de:
            raise de
        except Exception as e:
            raise e

        return search_items


    async def delete_doc(self, item_id: str, index: str | None = None) -> bool:
        """
        Delete a single document from OpenSearch by its document ID.

        :param item_id: The ID of the document to delete.
        :param index: (Optional) the index to delete from.
        :return: True if the document was deleted, False if not found.
        """
        try:
            if not index and not self.__index:
                raise ValueError("Index name must be provided.")
            idx = index if index else self.__index

            response = await self.__client.delete(index=idx, id=item_id, ignore=[404])
            return response.get("result") == "deleted"

        except Exception as e:
            logging.exception(f"Failed to delete item {item_id}: {e}")
            raise e

    def really_close(self):
        logger = logging.getLogger(__name__)
        if self.__client:
            logger.debug("Closing OpenSearch client...")
            run_coroutine_in_new_event_loop(self.__client.close())
            logger.debug("OpenSearch client closed.")


class S3WithOpenSearch(S3, OpenSearch):
    def __init__(self, config:  Configuration | None = None, **kwargs):
        super().__init__(config, **kwargs)

class MongoWithOpenSearch(Mongo, OpenSearch):
    def __init__(self, config:  Configuration | None = None, **kwargs):
        super().__init__(config, **kwargs)

class S3AndMongoWithOpenSearch(S3, Mongo, OpenSearch):
    def __init__(self, config:  Configuration | None = None, **kwargs):
        super().__init__(config, **kwargs)

class OpenSearchManager(MicroserviceDatabaseManager):

    def __init__(self, config:  Configuration | None = None):
        super().__init__(config)


    def get_database(self) -> OpenSearch:
        """
        Initializes and returns an instance of OpenSearchClient with the provided configuration.
        """
        return OpenSearch(config=self.config, managed=True)

    @classmethod
    def database_types(self) -> list[str]:
        return ['system|opensearch']


class S3WithOpenSearchManager(OpenSearchManager):

    def get_database(self) -> S3WithOpenSearch:
        """
        Initializes and returns an instance of OpenSearchClient with the provided configuration.
        """
        client = S3WithOpenSearch(config =self.config, managed=True)
        return client


class MongoWithOpenSearchManager(OpenSearchManager):

    def get_database(self) -> MongoWithOpenSearch:
        """
        Initializes and returns an instance of OpenSearchClient with the provided configuration.
        """
        client = MongoWithOpenSearch(config=self.config, managed=True)
        return client

class S3MongoOpenSearchMananger(OpenSearchManager):

    def get_database(self) -> S3AndMongoWithOpenSearch:
        """
        Initializes and returns an instance of OpenSearchClient with the provided configuration.
        """
        client = S3AndMongoWithOpenSearch(config =self.config, managed=True)
        return client


class OpenSearchContext(DatabaseContextManager[OpenSearch, Credentials]): # Go into db package?
    """
    Provides a OpenSearch index connection object. If neither a volume nor a credentials object is passed into the
    constructor, the host, port in the microservice's configuration file will be used, it will use defaults of OpenSearch
    filesystem.
    """

    async def connection(self) -> OpenSearch:
        return await _get_opensearch(self.request, self.volume_id)



async def _get_opensearch(request: web.Request, volume_id: Optional[str]) -> OpenSearch:
    """
    Gets a opensearch client.

    :param request: the HTTP request (required).
    :param volume_id: the id string of a volume.
    :return: a OpenSearch client for the file system specified by the volume's file_system_name attribute. If no volume_id
    was provided, the return value will be the "default" OpenSearch client for the microservice found in the HEA_DB
    application-level property.
    :raise ValueError: if there is no volume with the provided volume id, the volume's file system does not exist,
    or a necessary service is not registered.
    """

    if volume_id is not None:
        file_system, credentials = await get_file_system_and_credentials_from_volume(request, volume_id, OpenSearchFileSystem)
        if credentials is None:
            return OpenSearch(None, host=file_system.host, port=file_system.port, index=file_system.index)
        else:
            return OpenSearch(None, host=file_system.host, port=file_system.port, index=file_system.index,
                              username=credentials.account, password=credentials.password)
    else:
        return request.app[HEA_DB]
