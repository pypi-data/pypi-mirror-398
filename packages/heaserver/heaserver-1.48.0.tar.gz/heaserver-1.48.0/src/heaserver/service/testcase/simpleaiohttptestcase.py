from aiohttp.test_utils import AioHTTPTestCase, make_mocked_request
from aiohttp import web
from json import loads
from typing import Union


class SimpleAioHTTPTestCase(AioHTTPTestCase):

    async def get_application(self) -> web.Application:
        return web.Application()

    def _assert_json_string_equals(self, expected: Union[str, bytes, bytearray, None], actual: Union[str, bytes, bytearray, None]) -> None:
        self.assertEqual(loads(expected) if expected is not None else None, loads(actual) if actual is not None else None)
