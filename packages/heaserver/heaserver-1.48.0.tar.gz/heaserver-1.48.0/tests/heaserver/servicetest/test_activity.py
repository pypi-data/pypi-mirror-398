from unittest import IsolatedAsyncioTestCase
from heaserver.service import activity
from heaserver.service.util import yield_control
from aiohttp.test_utils import make_mocked_request
from aiohttp.web import Application, Request
from heaobject.root import DesktopObject
from heaobject.activity import Status
from heaserver.service import appproperty
from mypy_boto3_s3 import S3Client
from typing import Any
import asyncio

class ActivityTestCase(IsolatedAsyncioTestCase):

    async def test_desktop_object_actions_number(self):
        app = Application()
        request = make_mocked_request('GET', '/helloworld', app=app)
        app[appproperty.HEA_DB] = self.__mock_s3()
        desktop_objects = []
        async def publish_desktop_object(app: Application, desktop_object: DesktopObject,
                                 appproperty_=appproperty.HEA_MESSAGE_BROKER_PUBLISHER):
            desktop_objects.append(desktop_object)
        async with activity.DesktopObjectActionLifecycle(request, 'hea-get', 'hello world', activity_cb=publish_desktop_object) as _:
            await yield_control()

        self.assertEqual(2, len(desktop_objects))

    async def test_desktop_object_actions_number_nothing_awaited(self):
        app = Application()
        request = make_mocked_request('GET', '/helloworld', app=app)
        app[appproperty.HEA_DB] = self.__mock_s3()
        desktop_objects = []
        async def publish_desktop_object(app: Application, desktop_object: DesktopObject,
                                 appproperty_=appproperty.HEA_MESSAGE_BROKER_PUBLISHER):
            desktop_objects.append(desktop_object)
        async with activity.DesktopObjectActionLifecycle(request, 'hea-get', 'hello world', activity_cb=publish_desktop_object) as _:
            pass

        self.assertEqual(1, len(desktop_objects))

    async def test_desktop_object_actions_status_succeeded(self):
        app = Application()
        request = make_mocked_request('GET', '/helloworld', app=app)
        app[appproperty.HEA_DB] = self.__mock_s3()
        statuses = []
        async def publish_desktop_object(app: Application, desktop_object: DesktopObject,
                                 appproperty_=appproperty.HEA_MESSAGE_BROKER_PUBLISHER):
            statuses.append(desktop_object.status)

        async with activity.DesktopObjectActionLifecycle(request, 'hea-get', 'hello world', activity_cb=publish_desktop_object) as _:
            await yield_control()

        self.assertEqual([Status.IN_PROGRESS, Status.SUCCEEDED], statuses)

    async def test_desktop_object_actions_status_code(self):
        app = Application()
        request = make_mocked_request('GET', '/helloworld', app=app)
        app[appproperty.HEA_DB] = self.__mock_s3()
        codes = []
        async def publish_desktop_object(app: Application, desktop_object: DesktopObject,
                                 appproperty_=appproperty.HEA_MESSAGE_BROKER_PUBLISHER):
            codes.append(desktop_object.code)

        async with activity.DesktopObjectActionLifecycle(request, 'hea-get', 'hello world', activity_cb=publish_desktop_object) as _:
            await yield_control()

        self.assertEqual(['hea-get', 'hea-get'], codes)

    async def test_desktop_object_actions_status_description(self):
        app = Application()
        request = make_mocked_request('GET', '/helloworld', app=app)
        app[appproperty.HEA_DB] = self.__mock_s3()
        codes = []
        async def publish_desktop_object(app: Application, desktop_object: DesktopObject,
                                 appproperty_=appproperty.HEA_MESSAGE_BROKER_PUBLISHER):
            codes.append(desktop_object.description)

        async with activity.DesktopObjectActionLifecycle(request, 'hea-get', 'hello world', activity_cb=publish_desktop_object) as _:
            await yield_control()

        self.assertEqual(['hello world', 'hello world'], codes)

    async def test_desktop_object_actions_status_began(self):
        app = Application()
        request = make_mocked_request('GET', '/helloworld', app=app)
        app[appproperty.HEA_DB] = self.__mock_s3()
        timestamps = []
        async def publish_desktop_object(app: Application, desktop_object: DesktopObject,
                                 appproperty_=appproperty.HEA_MESSAGE_BROKER_PUBLISHER):
            timestamps.append(desktop_object.began)

        async with activity.DesktopObjectActionLifecycle(request, 'hea-get', 'hello world', activity_cb=publish_desktop_object) as _:
            await asyncio.sleep(0.1)

        self.assertEqual([True, True], [began is not None for began in timestamps])

    async def test_desktop_object_actions_status_failed_began(self):
        app = Application()
        request = make_mocked_request('GET', '/helloworld', app=app)
        app[appproperty.HEA_DB] = self.__mock_s3()
        timestamps = []
        async def publish_desktop_object(app: Application, desktop_object: DesktopObject,
                                 appproperty_=appproperty.HEA_MESSAGE_BROKER_PUBLISHER):
            timestamps.append(desktop_object.began)

        with self.assertRaises(ValueError):
            async with activity.DesktopObjectActionLifecycle(request, 'hea-get', 'hello world', activity_cb=publish_desktop_object) as _:
                await yield_control()
                raise ValueError

        self.assertEqual([True, True], [began is not None for began in timestamps])

    async def test_desktop_object_actions_status_failed_exception(self):
        app = Application()
        request = make_mocked_request('GET', '/helloworld', app=app)
        app[appproperty.HEA_DB] = self.__mock_s3()
        timestamps = []
        async def publish_desktop_object(app: Application, desktop_object: DesktopObject,
                                 appproperty_=appproperty.HEA_MESSAGE_BROKER_PUBLISHER):
            timestamps.append(desktop_object.ended)

        with self.assertRaises(ValueError):
            async with activity.DesktopObjectActionLifecycle(request, 'hea-get', 'hello world', activity_cb=publish_desktop_object) as _:
                raise ValueError

    async def test_desktop_object_actions_status_failed_ended(self):
        app = Application()
        request = make_mocked_request('GET', '/helloworld', app=app)
        app[appproperty.HEA_DB] = self.__mock_s3()
        timestamps = []
        async def publish_desktop_object(app: Application, desktop_object: DesktopObject,
                                 appproperty_=appproperty.HEA_MESSAGE_BROKER_PUBLISHER):
            timestamps.append(desktop_object.ended)

        async with activity.DesktopObjectActionLifecycle(request, 'hea-get', 'hello world', activity_cb=publish_desktop_object) as _:
            await yield_control()

        self.assertEqual([False, True], [ended is not None for ended in timestamps])

    async def test_desktop_object_actions_status_ended(self):
        app = Application()
        request = make_mocked_request('GET', '/helloworld', app=app)
        app[appproperty.HEA_DB] = self.__mock_s3()
        timestamps = []
        async def publish_desktop_object(app: Application, desktop_object: DesktopObject,
                                 appproperty_=appproperty.HEA_MESSAGE_BROKER_PUBLISHER):
            timestamps.append(desktop_object.ended)

        async with activity.DesktopObjectActionLifecycle(request, 'hea-get', 'hello world', activity_cb=publish_desktop_object) as _:
            await yield_control()

        self.assertEqual([False, True], [ended is not None for ended in timestamps])

    async def test_desktop_object_actions_status_failed(self):
        app = Application()
        request = make_mocked_request('GET', '/helloworld', app=app)
        app[appproperty.HEA_DB] = self.__mock_s3()
        statuses = []
        async def publish_desktop_object(app: Application, desktop_object: DesktopObject,
                                 appproperty_=appproperty.HEA_MESSAGE_BROKER_PUBLISHER):
            statuses.append(desktop_object.status)

        with self.assertRaises(ValueError):
            async with activity.DesktopObjectActionLifecycle(request, 'hea-get', 'hello world', activity_cb=publish_desktop_object) as _:
                raise ValueError

    async def test_desktop_object_actions_status_failed_statuses(self):
        app = Application()
        request = make_mocked_request('GET', '/helloworld', app=app)
        app[appproperty.HEA_DB] = self.__mock_s3()
        statuses = []
        async def publish_desktop_object(app: Application, desktop_object: DesktopObject,
                                 appproperty_=appproperty.HEA_MESSAGE_BROKER_PUBLISHER):
            statuses.append(desktop_object.status)
        async with activity.DesktopObjectActionLifecycle(request, 'hea-get', 'hello world', activity_cb=publish_desktop_object) as activity_:
            await yield_control()
            activity_.status = Status.FAILED
        self.assertEqual([Status.IN_PROGRESS, Status.FAILED], statuses)

    def __mock_s3(self) -> Any:
        class MockS3:
            async def get_client(self, request: Request, service_name: str, volume_id: str) -> S3Client:
                return None
        return MockS3()


