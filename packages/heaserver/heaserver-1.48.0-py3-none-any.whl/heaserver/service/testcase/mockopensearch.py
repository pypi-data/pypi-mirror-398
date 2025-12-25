from contextlib import AbstractContextManager, ExitStack
from typing import Optional, Sequence, Mapping

from heaobject.root import DesktopObjectDict

from heaserver.service.config import Configuration
from heaserver.service.db.database import InMemoryDatabase, CollectionKey, query_content, query_fixtures
from heaserver.service.db.opensearch import OpenSearch, OpenSearchManager, ItemTypeVar, MongoWithOpenSearch, \
    S3WithOpenSearch
from heaserver.service.testcase.mockdatabase import MockDatabase
from .util import freeze_time


class MockOpenSearch(MockDatabase, InMemoryDatabase, OpenSearch ):
    """
    Mock implementation of the Mongo class.

    It does not implement an aggregate method due the lack of good ways to mock such a thing.
    """

    def __init__(self, config: Optional[Configuration] = None,
                 opensearch: Optional['MockOpenSearch'] = None,
                 **kwargs) -> None:
        """
        Sets the db property of the app context with a motor MongoDB client instance.

        :param config: a Configuration object. MockMongo does not have a config section of its own.
        """
        super().__init__(config, **kwargs)
        if opensearch is not None:
            self.add_desktop_objects(opensearch.get_all_desktop_objects())
            self.add_content(opensearch.get_all_content())

    async def search(self,query: dict, search_item_type: type[ItemTypeVar],
                     index: str | None = None,
                     max_results: int = 1000,
                     size: int = 100) -> list[ItemTypeVar]:
        """
        Gets an object from the index.

        :param request: the aiohttp Request object (required).
        used as the attributes to query by.
        :param search_item_type: The class to be instantiated for holding search data
        :param index: name of opensearch index
        :param max_results: maximum number of results to return
        :param size: number of results to return
        :return: a list of SearchItems
        """

        return [search_item_type()]


    async def ping(self):
        """
        Raises an exception if the database does not respond to a ping command. The mock implementation never throws
        an exception.
        """
        pass


class MockOpenSearchManager(OpenSearchManager):
    """
    Database manager for a mock of OpeanSearch that stores collections in memory.
    """

    def __init__(self) -> None:
        super().__init__()
        self.__opensearch: Optional[MockOpenSearch] = None

    @classmethod
    def get_context(cls) -> list[AbstractContextManager]:
        result = super().get_context()
        result.append(freeze_time())
        return result

    def start_database(self, context_manager: ExitStack) -> None:
        self.__opensearch = MockOpenSearch(managed=True)
        super().start_database(context_manager)

    def insert_desktop_objects(self, desktop_objects: Optional[Mapping[CollectionKey, Sequence[DesktopObjectDict]]]):
        super().insert_desktop_objects(desktop_objects)
        assert self.__opensearch is not None
        if desktop_objects:
            self.__opensearch.add_desktop_objects({k: v for k, v in query_fixtures(desktop_objects, db_manager=MockOpenSearchManager).items() if k is not None})

    def insert_content(self, content: Optional[Mapping[CollectionKey, Mapping[str, bytes]]]):
        super().insert_content(content)
        assert self.__opensearch is not None
        if content:
            self.__opensearch.add_content({k: v for k, v in query_content(content, db_manager=MockOpenSearchManager).items() if k is not None})

    def get_database(self) -> MockOpenSearch:
        """
        Gets a mock mongo database object (only available after start_database() has been called).
        """
        if self.__opensearch is None:
            raise ValueError('start_database not called')
        return self.__opensearch

    def get_mongo(self) -> MockOpenSearch | None:
        return self.__opensearch


class MockMongoWithOpenSearch(MockDatabase, InMemoryDatabase, MongoWithOpenSearch):
    """
    Mock implementation of the MongoWithOpenSearch class.
    """
    def __init__(self, config: Optional[Configuration] = None,
                 mongo_opensearch: Optional['MockMongoWithOpenSearch'] = None,
                 **kwargs) -> None:
        super().__init__(config, **kwargs)
        if mongo_opensearch is not None:
            self.add_desktop_objects(mongo_opensearch.get_all_desktop_objects())
            self.add_content(mongo_opensearch.get_all_content())

    async def search(self, query: dict,  search_item_type: type[ItemTypeVar],
                     index: str | None = None,
                     max_results: int = 1000,
                     size: int = 100) -> list[ItemTypeVar]:
        return [search_item_type()]

    async def ping(self):
        pass


class MockMongoWithOpenSearchManager(OpenSearchManager):
    """
    Mock manager for MongoWithOpenSearch that stores collections in memory.
    """
    def __init__(self) -> None:
        super().__init__()
        self.__mongo_opensearch: Optional[MockMongoWithOpenSearch] = None

    @classmethod
    def get_context(cls) -> list[AbstractContextManager]:
        result = super().get_context()
        result.append(freeze_time())
        return result

    def start_database(self, context_manager: ExitStack) -> None:
        self.__mongo_opensearch = MockMongoWithOpenSearch(managed=True)
        super().start_database(context_manager)

    def insert_desktop_objects(self, desktop_objects: Optional[Mapping[CollectionKey, Sequence[DesktopObjectDict]]]):
        super().insert_desktop_objects(desktop_objects)
        assert self.__mongo_opensearch is not None
        if desktop_objects:
            self.__mongo_opensearch.add_desktop_objects({k: v for k, v in query_fixtures(desktop_objects, db_manager=MockMongoWithOpenSearchManager).items() if k is not None})

    def insert_content(self, content: Optional[Mapping[CollectionKey, Mapping[str, bytes]]]):
        super().insert_content(content)
        assert self.__mongo_opensearch is not None
        if content:
            self.__mongo_opensearch.add_content({k: v for k, v in query_content(content, db_manager=MockMongoWithOpenSearchManager).items() if k is not None})

    def get_database(self) -> MockMongoWithOpenSearch:
        if self.__mongo_opensearch is None:
            raise ValueError('start_database not called')
        return self.__mongo_opensearch


class MockS3WithOpenSearch(MockDatabase, InMemoryDatabase, S3WithOpenSearch):
    """
    Mock implementation of the S3WithOpenSearch class.
    """
    def __init__(self, config: Optional[Configuration] = None,
                 s3_opensearch: Optional['MockS3WithOpenSearch'] = None,
                 **kwargs) -> None:
        super().__init__(config, **kwargs)
        if s3_opensearch is not None:
            self.add_desktop_objects(s3_opensearch.get_all_desktop_objects())
            self.add_content(s3_opensearch.get_all_content())

    async def search(self,query: dict, search_item_type: type[ItemTypeVar],
                     index: str | None = None,
                     max_results: int = 1000,
                     size: int = 100) -> list[ItemTypeVar]:
        return [search_item_type()]

    async def ping(self):
        pass


class MockS3WithOpenSearchManager(OpenSearchManager):
    """
    Mock manager for S3WithOpenSearch that stores collections in memory.
    """
    def __init__(self) -> None:
        super().__init__()
        self.__s3_opensearch: Optional[MockS3WithOpenSearch] = None

    @classmethod
    def get_context(cls) -> list[AbstractContextManager]:
        result = super().get_context()
        result.append(freeze_time())
        return result

    def start_database(self, context_manager: ExitStack) -> None:
        self.__s3_opensearch = MockS3WithOpenSearch(managed=True)
        super().start_database(context_manager)

    def insert_desktop_objects(self, desktop_objects: Optional[Mapping[CollectionKey, Sequence[DesktopObjectDict]]]):
        super().insert_desktop_objects(desktop_objects)
        assert self.__s3_opensearch is not None
        if desktop_objects:
            self.__s3_opensearch.add_desktop_objects({k: v for k, v in query_fixtures(desktop_objects, db_manager=MockS3WithOpenSearchManager).items() if k is not None})

    def insert_content(self, content: Optional[Mapping[CollectionKey, Mapping[str, bytes]]]):
        super().insert_content(content)
        assert self.__s3_opensearch is not None
        if content:
            self.__s3_opensearch.add_content({k: v for k, v in query_content(content, db_manager=MockS3WithOpenSearchManager).items() if k is not None})

    def get_database(self) -> MockS3WithOpenSearch:
        if self.__s3_opensearch is None:
            raise ValueError('start_database not called')
        return self.__s3_opensearch
