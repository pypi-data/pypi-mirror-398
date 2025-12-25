from aiohttp.test_utils import AioHTTPTestCase
from aiohttp import web, TCPConnector, ClientSession, hdrs
from aiohttp.client_exceptions import ClientResponseError, ClientError
from heaserver.service import client, runner, response
from heaserver.service.aiohttp import AsyncReader
from heaserver.service.testcase.mixin import _ordered
from heaobject.folder import Folder, AWSS3Folder
from heaobject import user
import json
from heaobject.root import json_dumps, Permission
from heaserver.service import appproperty


class TestClient(AioHTTPTestCase):

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
            'type_display_name': 'Folder',
            'mime_type': 'application/x.folder',
            'path': None,
            'super_admin_default_permissions': [],
            'dynamic_permission_supported': False
        }
        self.app[appproperty.HEA_CLIENT_SESSION] = ClientSession(connector=TCPConnector(), connector_owner=True,
                                                                 json_serialize=json_dumps,
                                                                 raise_for_status=True)

    async def tearDownAsync(self) -> None:
        await super().tearDownAsync()
        await self.app[appproperty.HEA_CLIENT_SESSION].close()

    async def get_application(self):
        async def post_folder(request: web.Request):
            data = await request.json()
            f = Folder()
            f.from_dict(data)
            if f.display_name == 'hello':
                return response.status_generic(201, headers={hdrs.LOCATION: 'http://127.0.0.1:8080/foo'})
            else:
                return response.status_bad_request()

        async def get_folder_client(request):
            f = Folder()
            f.display_name = 'hello'
            location = await client.post(request.app, f'http://127.0.0.1:{request.url.port}/postfolder', f)
            return response.status_ok(location)

        async def post_awss3folder(request: web.Request):
            data = await request.json()
            f = AWSS3Folder()
            f.from_dict(data)
            if f.display_name == 'hello':
                return response.status_generic(201, headers={hdrs.LOCATION: 'http://127.0.0.1:8080/foo'})
            else:
                return response.status_bad_request(body=f'display_name should be hello but was {f.display_name}')

        async def get_awss3folder_client(request):
            f = AWSS3Folder()
            f.display_name = 'hello'
            try:
                location = await client.post(request.app, f'http://127.0.0.1:{request.url.port}/postawss3folder', f)
                return response.status_ok(location)
            except ClientResponseError as e:
                return response.status_generic(e.status, e.message)
            except ClientError as e:
                return response.status_generic(500, str(e))

        async def get_awss3folder_dict_client(request):
            f = AWSS3Folder()
            f.display_name = 'hello'
            try:
                location = await client.post(request.app, f'http://127.0.0.1:{request.url.port}/postawss3folder', f.to_dict())
                return response.status_ok(location)
            except ClientResponseError as e:
                return response.status_generic(e.status, e.message)
            except ClientError as e:
                return response.status_generic(500, str(e))

        async def test_folder_get(request):
            return web.Response(status=200,
                                body=json.dumps([self.__body]),
                                content_type='application/json')

        async def test_get_content(request):
            return await response.get_streaming(request, AsyncReader(b'The quick brown fox jumped over the lazy dogs'))

        async def test_get_content_client(request):
            return await client.get_streaming(request, f'http://127.0.0.1:{request.url.port}/testgetcontent')

        async def test_get(request):
            obj = await client.get(request.app, f'http://127.0.0.1:{request.url.port}/folders', Folder)
            return web.Response(status=200,
                                body=obj.to_json() if obj is not None else None,
                                content_type='application/json')

        app = runner.get_application()
        app.router.add_get('/folders', test_folder_get)
        app.router.add_get('/testget', test_get)
        app.router.add_get('/testgetcontent', test_get_content)
        app.router.add_get('/testgetcontentclient', test_get_content_client)
        app.router.add_post('/postfolder', post_folder)
        app.router.add_get('/getfolderclient', get_folder_client)
        app.router.add_post('/postawss3folder', post_awss3folder)
        app.router.add_get('/getawss3folderclient', get_awss3folder_client)
        app.router.add_get('/getawss3folderdictclient', get_awss3folder_dict_client)

        return app

    async def test_get(self):
        obj = await self.client.request('GET', '/testget')
        self.assertEqual(_ordered(self.__body), _ordered(await obj.json()))

    async def test_get_content(self):
        obj = await self.client.request('GET', '/testgetcontentclient')
        self.assertEqual(b'The quick brown fox jumped over the lazy dogs', await obj.read())

    async def test_post_folder(self):
        obj = await self.client.request('GET', '/getfolderclient')
        self.assertEqual(200, obj.status)

    async def test_post_folder_location(self):
        obj = await self.client.request('GET', '/getfolderclient')
        self.assertEqual('http://127.0.0.1:8080/foo', await obj.text())

    async def test_post_folder_body(self):
        obj = await self.client.request('GET', '/getfolderclient')
        self.assertEqual('http://127.0.0.1:8080/foo', await obj.text())

    async def test_post_awss3folder(self):
        obj = await self.client.request('GET', '/getawss3folderclient')
        self.assertEqual(200, obj.status)

    async def test_post_awss3folder_location(self):
        obj = await self.client.request('GET', '/getawss3folderclient')
        self.assertEqual('http://127.0.0.1:8080/foo', await obj.text())

    async def test_post_awss3folder_body(self):
        obj = await self.client.request('GET', '/getawss3folderclient')
        self.assertEqual('http://127.0.0.1:8080/foo', await obj.text())

    async def test_post_awss3folderdict_body(self):
        obj = await self.client.request('GET', '/getawss3folderdictclient')
        self.assertEqual('http://127.0.0.1:8080/foo', await obj.text())

