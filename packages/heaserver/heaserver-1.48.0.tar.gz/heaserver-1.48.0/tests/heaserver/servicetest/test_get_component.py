from .componenttestcase import ComponentTestCase, ComponentTestCase2, ComponentTestCase3
from heaserver.service.representor import cj
from heaserver.service.testcase.mixin import GetOneMixin
from heaserver.service.oidcclaimhdrs import SUB
from heaobject.user import NONE_USER
from heaobject.volume import MongoDBFileSystem
from aiohttp import hdrs
import aiohttp.client_exceptions


class TestGetComponent(ComponentTestCase, GetOneMixin):  # type: ignore
    async def test_get_by_type(self):
        """
        Checks if a GET request for the object with the expected resources type in ``_expected_one`` succeeds and
        returns the expected data. The test is skipped if the object has no resources or if the type of its resources
        is not defined.
        """
        obj_resources = self._expected_one_wstl[0]['wstl']['data'][0].get('resources', None) or None
        if obj_resources is None:
            self.skipTest('the _expected_one object has no resources')
        obj_resources_type = None
        for resource in obj_resources:
            obj_resources_type = resource.get('resource_type_name', None)
            if obj_resources_type is not None:
                break
        if obj_resources_type is None:
            self.skipTest('the object\'s resources do not have a type')
        response = await self.client.request('GET',
                                             (self._href / 'bytype' / obj_resources_type).path,
                                             headers={**self._headers, hdrs.ACCEPT: cj.MIME_TYPE})
        try:
            self._assert_equal_ordered(self._expected_one[0]['collection']['items'][0]['data'], (await response.json())[0]['collection']['items'][0]['data'])
        except aiohttp.client_exceptions.ContentTypeError as e:
            raise AssertionError(f'GET request failed ({await response.text()}): {e}') from e

    async def test_get_by_type_invalid_type(self):
        """Checks if a GET request for the object with the type 'foo.bar' fails with status 404."""
        response = await self.client.request('GET',
                                             (self._href / 'bytype' / 'foo.bar').path,
                                             headers={**self._headers, hdrs.ACCEPT: cj.MIME_TYPE})
        self.assertEqual(404, response.status)


class TestGetComponent2(ComponentTestCase2, GetOneMixin):  # type: ignore
    pass


class TestGetComponent3(ComponentTestCase3, GetOneMixin):  # type: ignore
    pass


class TestMissingFileSystemAttribute(ComponentTestCase):
    _headers = {SUB: NONE_USER, hdrs.X_FORWARDED_HOST: 'localhost:8080'}

    async def test_missing_file_system_attribute(self):
        obj = await self.client.request('GET',
                                        (self._href / 'bytype' / 'heaobject.folder.Folder' / 'byfilesystemtype' / MongoDBFileSystem.get_type_name()).path,
                                        headers=TestMissingFileSystemAttribute._headers)
        self.assertEqual(200, obj.status)
