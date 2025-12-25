from heaserver.service.representor.nvpjson import NVPJSON
from heaserver.service.representor.error import ParseException
from heaserver.service.testcase.simpleaiohttptestcase import SimpleAioHTTPTestCase
from unittest.mock import AsyncMock
from heaserver.service import wstl
from aiohttp.web import Request
from aiohttp import hdrs
import json

from datetime import datetime
from heaobject.user import NONE_USER


class NVPJSONTestCase(SimpleAioHTTPTestCase):
    async def setUpAsync(self):
        await super().setUpAsync()
        self.__body = {
            'items': [],
            'created': datetime(2021, 12, 2, 17, 31, 15, 630000),
            'derived_by_uri': None,
            'derived_from_uris': [],
            'description': None,
            'display_name': 'Reximus',
            'id': '1',
            'invites': [],
            'modified': None,
            'name': 'reximus',
            'owner': NONE_USER,
            'shares': [],
            'source_uri': None,
            'type': 'heaobject.folder.Folder',
            'version': None,
            'nested_dict': {'foo': 'oof', 'baz': 'zab', 'type': 'heaobject.registry.Component'},
            'nested_list': [{'foo': 'oof', 'baz': 'zab', 'type': 'heaobject.registry.Component'},
                            {'foo': 'oof', 'baz': 'zab', 'type': 'heaobject.registry.Component'}],
            'empty_nested_list': [],
            'plain_list': [1, 2, 3, 4]
        }
        self.maxDiff = None

    async def test_formats_default(self) -> None:
        b = wstl.builder('servicetest', resource='representor/all.json')
        actual = await NVPJSON().formats(self.__request(), b())
        expected = b'[]'
        self._assert_json_string_equals(expected, actual)

    async def test_formats_data(self) -> None:
        runtime_wstl_builder = wstl.builder('servicetest.representor', resource='all.json')
        runtime_wstl_builder.href = 'http://localhost/test'
        actual, _ = await runtime_wstl_builder.represent_from_request(self.__request(), self.__body)
        expected = \
            b'''[{"items": [],
                  "created": "2021-12-02T17:31:15.630000",
                  "derived_by_uri": null,
                  "derived_from_uris": [],
                  "description": null,
                  "display_name": "Reximus",
                  "id": "1",
                  "invites": [],
                  "modified": null,
                  "name": "reximus",
                  "owner": "system|none",
                  "shares": [],
                  "source_uri": null,
                  "type": "heaobject.folder.Folder",
                  "version": null,
                  "nested_dict": {"foo": "oof", "baz": "zab", "type": "heaobject.registry.Component"},
                  "nested_list": [{"foo": "oof", "baz": "zab", "type": "heaobject.registry.Component"}, {"foo": "oof", "baz": "zab", "type": "heaobject.registry.Component"}],
                  "empty_nested_list": [],
                  "plain_list": [1, 2, 3, 4]}]'''
        self._assert_json_string_equals(expected, actual)

    async def test_parse(self) -> None:
        self.assertDictEqual({'foo': 'bar', 'baz': 1, 'spam': ['some', 'spam', 2]},
                             await NVPJSON().parse(self.__request(
                                 '''{"foo": "bar",
                                     "baz": 1,
                                     "spam": ["some", "spam", 2]}'''
                             )))

    async def test_parse_invalid(self) -> None:
        with self.assertRaises(ParseException):
            await NVPJSON().parse(self.__request('foobar'))

    async def test_parse_empty(self) -> None:
        self.assertEqual({}, await NVPJSON().parse(self.__request('{}')))

    def __request(self, jsons: str = None) -> AsyncMock:
        request = AsyncMock(spec=Request)
        request.text.return_value = jsons
        request.json.side_effect = lambda loads=json.loads: loads(jsons)
        request.match_info = {}
        request.headers = {hdrs.ACCEPT: NVPJSON.MIME_TYPE}
        return request
