from heaserver.service.representor.xwwwformurlencoded import XWWWFormURLEncoded
from heaserver.service.representor.error import ParseException
from heaserver.service.testcase.simpleaiohttptestcase import SimpleAioHTTPTestCase
from unittest.mock import AsyncMock
from heaserver.service import wstl
from aiohttp.web import Request
import json

from datetime import datetime
from heaobject.user import NONE_USER


class XWWWFormURLEncodedTestCase(SimpleAioHTTPTestCase):
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

    async def test_parse(self) -> None:
        self.assertDictEqual({'foo': 'oof', 'baz': 'zab', 'type': 'heaobject.registry.Component'},
                             await XWWWFormURLEncoded().parse(self.__request(
                                 'foo=oof&'
                                 'baz=zab&'
                                 'type=heaobject.registry.Component'
                             )))

    async def test_parse_invalid(self) -> None:
        with self.assertRaises(ParseException):
            await XWWWFormURLEncoded().parse(self.__request('foobar'))

    def __request(self, jsons: str = None) -> AsyncMock:
        request = AsyncMock(spec=Request)
        request.text.return_value = jsons
        request.json.side_effect = lambda loads=json.loads: loads(jsons)
        request.match_info.return_value = {}
        return request
