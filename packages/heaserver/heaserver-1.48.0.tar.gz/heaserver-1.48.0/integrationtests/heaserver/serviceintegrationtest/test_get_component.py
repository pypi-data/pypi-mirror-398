from .componenttestcase import ComponentTestCase
from heaserver.service.testcase.mixin import GetOneMixin
from heaserver.service.oidcclaimhdrs import SUB
from heaobject.user import NONE_USER
from heaobject.volume import MongoDBFileSystem
from aiohttp import hdrs


class TestGetComponent(ComponentTestCase, GetOneMixin):  # type: ignore
    pass


class TestMissingFileSystemAttribute(ComponentTestCase):
    _headers = {SUB: NONE_USER, hdrs.X_FORWARDED_HOST: 'localhost:8080'}

    async def test_missing_file_system_attribute(self):
        obj = await self.client.request('GET',
                                        (self._href / 'bytype' / 'heaobject.folder.Folder' / 'byfilesystemtype' / MongoDBFileSystem.get_type_name()).path,
                                        headers=TestMissingFileSystemAttribute._headers)
        self.assertEqual(200, obj.status)
