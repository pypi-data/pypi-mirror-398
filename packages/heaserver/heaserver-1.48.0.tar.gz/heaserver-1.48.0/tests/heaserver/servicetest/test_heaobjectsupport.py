import copy
import unittest.result

from aiohttp.test_utils import AioHTTPTestCase
from aiohttp import web, TCPConnector, ClientSession
from .componenttestcase import fixtures1 as fixtures, content1 as content
from heaserver.service import appproperty, runner, wstl
from heaserver.service.heaobjectsupport import populate_heaobject, new_heaobject_from_type, type_to_resource_url
from heaserver.service.testcase.mockmongo import MockMongoManager
from heaobject.folder import Folder
from heaobject import user, root, error
from . import service
from heaobject.root import json_dumps
from contextlib import ExitStack


class TestHEAObjectSupport(AioHTTPTestCase):

    async def setUpAsync(self):
        await super().setUpAsync()
        self.__body = {
            'created': None,
            'derived_by': None,
            'derived_from': [],
            'description': None,
            'display_name': 'Reximus',
            'id': None,
            'instance_id': None,
            'invites': [],
            'modified': None,
            'name': 'reximus',
            'owner': user.NONE_USER,
            'shares': [],
            'user_shares': [],
            'group_shares': [],
            'source': None,
            'source_detail': None,
            'type': 'heaobject.folder.Folder',
            'mime_type': 'application/x.folder',
            'path': None,
            'type_display_name': 'Folder',
            'super_admin_default_permissions': [],
            'dynamic_permission_supported': False
        }
        self.app[appproperty.HEA_CLIENT_SESSION] = ClientSession(connector=TCPConnector(), connector_owner=True,
                                                                 json_serialize=json_dumps,
                                                                 raise_for_status=True)

    async def tearDownAsync(self) -> None:
        await super().tearDownAsync()
        await self.app[appproperty.HEA_CLIENT_SESSION].close()

    def run(self, result: unittest.result.TestResult | None = ...) -> unittest.result.TestResult | None:
        self.__mock_mongo_manager = MockMongoManager()
        with ExitStack() as stack:
            self.__mock_mongo_manager.start_database(stack)
            self.__mock_mongo_manager.insert_all(fixtures, content)
            return super().run(result)

    async def get_application(self):
        async def test_new_heaobject(request):
            try:
                obj = await new_heaobject_from_type(request, Folder)
            except error.DeserializeException as e:
                return web.Response(status=400, body=str(e).encode())
            return web.Response(status=200, body=obj.to_json(), content_type='application/json')

        async def test_populate_heaobject(request):
            obj = await populate_heaobject(request, Folder())
            return web.Response(status=200, body=obj.to_json(), content_type='application/json')

        async def test_type_to_resource_url(request):
            app[appproperty.HEA_REGISTRY] = f'http://127.0.0.1:{request.url.port}'
            url = await type_to_resource_url(request, Folder)
            return web.Response(status=200, body=url, content_type='text/plain')

        app = runner.get_application(db=self.__mock_mongo_manager,
                                     wstl_builder_factory=wstl.builder_factory(package=service.__package__))
        app.router.add_post('/testnewheaobject', test_new_heaobject)
        app.router.add_post('/testpopulateheaobject', test_populate_heaobject)
        app.router.add_get('/testtypetoresourceurl', test_type_to_resource_url)
        app.router.add_get(
            '/components/bytype/{type}/byfilesystemtype/{filesystemtype}/byfilesystemname/{filesystemname}',
            service.get_components_by_type)
        return app

    async def test_new_heaobject(self):
        obj = await self.client.request('POST', '/testnewheaobject', json=self.__body)
        self.assertEqual(self.__body, await obj.json())

    async def test_new_heaobject_no_type(self):
        body = copy.deepcopy(self.__body)
        del body['type']
        obj = await self.client.request('POST',
                                        '/testnewheaobject',
                                        json=body)
        self.assertEqual(400, obj.status)

    async def test_populate_heaobject(self):
        obj = await self.client.request('POST', '/testpopulateheaobject', json=self.__body)
        self.assertEqual(self.__body, await obj.json())

    async def test_type_to_resource_url_status(self):
        response = await self.client.request('GET', '/testtypetoresourceurl')
        self.assertEqual(200, response.status)

    async def test_type_to_resource_url_response(self):
        response = await self.client.request('GET', '/testtypetoresourceurl')
        self.assertEqual('http://localhost/folders', await response.text())

    async def test_has_permissions_owner(self):
        f = Folder()
        f.owner = user.NONE_USER
        context = root.PermissionContext(user.NONE_USER)
        assert await f.has_permissions([root.Permission.COOWNER], context)

    async def test_has_permissions_none_user(self):
        f = Folder()
        f.owner = user.NONE_USER
        with self.assertRaises(ValueError):
            context = root.PermissionContext(None)

