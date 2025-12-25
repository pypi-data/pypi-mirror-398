from heaserver.service.testcase.simpleaiohttptestcase import SimpleAioHTTPTestCase
from heaserver.service import wstl
from heaserver.service.representor import cj, error
from heaobject import user
from datetime import datetime
from unittest.mock import AsyncMock
from aiohttp.web import Request
from aiohttp import hdrs
import json
from multidict import CIMultiDict, CIMultiDictProxy


class TestCj(SimpleAioHTTPTestCase):

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
            'owner': user.NONE_USER,
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

    async def test_formats_default(self):
        b = wstl.builder('servicetest', resource='representor/all.json')
        actual, _ = await b.represent_from_request(self.__request(), None)
        expected = '[{"collection": {"href": "#", "permissions": [], "version": "1.0"}}]'
        self._assert_json_string_equals(expected, actual)

    async def test_formats_data(self):
        runtime_wstl_builder = wstl.builder('servicetest.representor', resource='all.json')
        runtime_wstl_builder.href = 'http://localhost/test'
        actual, _ = await runtime_wstl_builder.represent_from_request(self.__request(), self.__body)
        expected = '''[{"collection":
                          {"version": "1.0",
                           "href": "http://localhost/test",
                           "permissions": [[]],
                           "items": [
                               {"data": [
                                   {"name": "items", "value": [], "prompt": "items", "display": true},
                                   {"name": "created", "value": "2021-12-02T17:31:15.630000", "prompt": "created", "display": true},
                                   {"name": "derived_by_uri", "value": null, "prompt": "derived_by_uri", "display": true},
                                   {"name": "derived_from_uris", "value": [], "prompt": "derived_from_uris", "display": true},
                                   {"name": "description", "value": null, "prompt": "description", "display": true},
                                   {"name": "display_name", "value": "Reximus", "prompt": "display_name", "display": true},
                                   {"name": "id", "value": "1", "prompt": "id", "display": false},
                                   {"name": "invites", "value": [], "prompt": "invites", "display": true},
                                   {"name": "modified", "value": null, "prompt": "modified", "display": true},
                                   {"name": "name", "value": "reximus", "prompt": "name", "display": true},
                                   {"name": "owner", "value": "system|none", "prompt": "owner", "display": true},
                                   {"name": "shares", "value": [], "prompt": "shares", "display": true},
                                   {"name": "source_uri", "value": null, "prompt": "source_uri", "display": true},
                                   {"name": "type", "value": "heaobject.folder.Folder", "prompt": "type", "display": true},
                                   {"name": "version", "value": null, "prompt": "version", "display": true},
                                   {"section": "nested_dict", "name": "foo", "value": "oof", "prompt": "foo", "display": true},
                                   {"section": "nested_dict", "name": "baz", "value": "zab", "prompt": "baz", "display": true},
                                   {"section": "nested_dict", "name": "type", "value": "heaobject.registry.Component", "prompt": "type", "display": true},
                                   {"section": "nested_list", "index": 0, "name": "foo", "value": "oof", "prompt": "foo", "display": true},
                                   {"section": "nested_list", "index": 0, "name": "baz", "value": "zab", "prompt": "baz", "display": true},
                                   {"section": "nested_list", "index": 0, "name": "type", "value": "heaobject.registry.Component", "prompt": "type", "display": true},
                                   {"section": "nested_list", "index": 1, "name": "foo", "value": "oof", "prompt": "foo", "display": true},
                                   {"section": "nested_list", "index": 1, "name": "baz", "value": "zab", "prompt": "baz", "display": true},
                                   {"section": "nested_list", "index": 1, "name": "type", "value": "heaobject.registry.Component", "prompt": "type", "display": true},
                                   {"name": "empty_nested_list", "prompt": "empty_nested_list", "value": [], "display": true},
                                   {"name": "plain_list", "prompt": "plain_list", "value": [1, 2, 3, 4], "display": true}
                                   ],
                                   "links": []
                               }
                           ]}}]'''
        self._assert_json_string_equals(expected, actual)

    async def test_formats_two_items_empty_permissions(self):
        runtime_wstl_builder = wstl.builder('servicetest.representor', resource='all.json')
        runtime_wstl_builder.href = 'http://localhost/test'
        actual, _ = await runtime_wstl_builder.represent_from_request(self.__request(), [self.__body, self.__body])
        expected = '''[{"collection":
                          {"version": "1.0",
                           "href": "http://localhost/test",
                           "permissions": [[], []],
                           "items": [
                               {"data": [
                                   {"name": "items", "value": [], "prompt": "items", "display": true},
                                   {"name": "created", "value": "2021-12-02T17:31:15.630000", "prompt": "created", "display": true},
                                   {"name": "derived_by_uri", "value": null, "prompt": "derived_by_uri", "display": true},
                                   {"name": "derived_from_uris", "value": [], "prompt": "derived_from_uris", "display": true},
                                   {"name": "description", "value": null, "prompt": "description", "display": true},
                                   {"name": "display_name", "value": "Reximus", "prompt": "display_name", "display": true},
                                   {"name": "id", "value": "1", "prompt": "id", "display": false},
                                   {"name": "invites", "value": [], "prompt": "invites", "display": true},
                                   {"name": "modified", "value": null, "prompt": "modified", "display": true},
                                   {"name": "name", "value": "reximus", "prompt": "name", "display": true},
                                   {"name": "owner", "value": "system|none", "prompt": "owner", "display": true},
                                   {"name": "shares", "value": [], "prompt": "shares", "display": true},
                                   {"name": "source_uri", "value": null, "prompt": "source_uri", "display": true},
                                   {"name": "type", "value": "heaobject.folder.Folder", "prompt": "type", "display": true},
                                   {"name": "version", "value": null, "prompt": "version", "display": true},
                                   {"section": "nested_dict", "name": "foo", "value": "oof", "prompt": "foo", "display": true},
                                   {"section": "nested_dict", "name": "baz", "value": "zab", "prompt": "baz", "display": true},
                                   {"section": "nested_dict", "name": "type", "value": "heaobject.registry.Component", "prompt": "type", "display": true},
                                   {"section": "nested_list", "index": 0, "name": "foo", "value": "oof", "prompt": "foo", "display": true},
                                   {"section": "nested_list", "index": 0, "name": "baz", "value": "zab", "prompt": "baz", "display": true},
                                   {"section": "nested_list", "index": 0, "name": "type", "value": "heaobject.registry.Component", "prompt": "type", "display": true},
                                   {"section": "nested_list", "index": 1, "name": "foo", "value": "oof", "prompt": "foo", "display": true},
                                   {"section": "nested_list", "index": 1, "name": "baz", "value": "zab", "prompt": "baz", "display": true},
                                   {"section": "nested_list", "index": 1, "name": "type", "value": "heaobject.registry.Component", "prompt": "type", "display": true},
                                   {"name": "empty_nested_list", "prompt": "empty_nested_list", "value": [], "display": true},
                                   {"name": "plain_list", "prompt": "plain_list", "value": [1, 2, 3, 4], "display": true}
                                   ],
                                   "links": []
                               },
                               {"data": [
                                   {"name": "items", "value": [], "prompt": "items", "display": true},
                                   {"name": "created", "value": "2021-12-02T17:31:15.630000", "prompt": "created", "display": true},
                                   {"name": "derived_by_uri", "value": null, "prompt": "derived_by_uri", "display": true},
                                   {"name": "derived_from_uris", "value": [], "prompt": "derived_from_uris", "display": true},
                                   {"name": "description", "value": null, "prompt": "description", "display": true},
                                   {"name": "display_name", "value": "Reximus", "prompt": "display_name", "display": true},
                                   {"name": "id", "value": "1", "prompt": "id", "display": false},
                                   {"name": "invites", "value": [], "prompt": "invites", "display": true},
                                   {"name": "modified", "value": null, "prompt": "modified", "display": true},
                                   {"name": "name", "value": "reximus", "prompt": "name", "display": true},
                                   {"name": "owner", "value": "system|none", "prompt": "owner", "display": true},
                                   {"name": "shares", "value": [], "prompt": "shares", "display": true},
                                   {"name": "source_uri", "value": null, "prompt": "source_uri", "display": true},
                                   {"name": "type", "value": "heaobject.folder.Folder", "prompt": "type", "display": true},
                                   {"name": "version", "value": null, "prompt": "version", "display": true},
                                   {"section": "nested_dict", "name": "foo", "value": "oof", "prompt": "foo", "display": true},
                                   {"section": "nested_dict", "name": "baz", "value": "zab", "prompt": "baz", "display": true},
                                   {"section": "nested_dict", "name": "type", "value": "heaobject.registry.Component", "prompt": "type", "display": true},
                                   {"section": "nested_list", "index": 0, "name": "foo", "value": "oof", "prompt": "foo", "display": true},
                                   {"section": "nested_list", "index": 0, "name": "baz", "value": "zab", "prompt": "baz", "display": true},
                                   {"section": "nested_list", "index": 0, "name": "type", "value": "heaobject.registry.Component", "prompt": "type", "display": true},
                                   {"section": "nested_list", "index": 1, "name": "foo", "value": "oof", "prompt": "foo", "display": true},
                                   {"section": "nested_list", "index": 1, "name": "baz", "value": "zab", "prompt": "baz", "display": true},
                                   {"section": "nested_list", "index": 1, "name": "type", "value": "heaobject.registry.Component", "prompt": "type", "display": true},
                                   {"name": "empty_nested_list", "prompt": "empty_nested_list", "value": [], "display": true},
                                   {"name": "plain_list", "prompt": "plain_list", "value": [1, 2, 3, 4], "display": true}
                                   ],
                                   "links": []
                               }
                           ]}}]'''
        self._assert_json_string_equals(expected, actual)

    async def test_formats_data_with_item_href(self):
        runtime_wstl_builder = wstl.builder('servicetest.representor', resource='all_cj_item_href.json')
        runtime_wstl_builder.href = 'http://localhost/test'
        runtime_wstl_builder.add_run_time_action('data-adapter-open', path='foo/bar/{id}',
                                                 root='http://localhost:8080')
        actual, _ = await runtime_wstl_builder.represent_from_request(self.__request(), self.__body)
        expected = '''[{"collection":
                         {"version": "1.0",
                          "href": "http://localhost/test",
                          "permissions": [[]],
                          "items": [
                              {"data": [
                                  {"name": "items", "value": [], "prompt": "items", "display": true},
                                  {"name": "created", "value": "2021-12-02T17:31:15.630000", "prompt": "created", "display": true},
                                  {"name": "derived_by_uri", "value": null, "prompt": "derived_by_uri", "display": true},
                                  {"name": "derived_from_uris", "value": [], "prompt": "derived_from_uris", "display": true},
                                  {"name": "description", "value": null, "prompt": "description", "display": true},
                                  {"name": "display_name", "value": "Reximus", "prompt": "display_name", "display": true},
                                  {"name": "id", "value": "1", "prompt": "id", "display": false},
                                  {"name": "invites", "value": [], "prompt": "invites", "display": true},
                                  {"name": "modified", "value": null, "prompt": "modified", "display": true},
                                  {"name": "name", "value": "reximus", "prompt": "name", "display": true},
                                  {"name": "owner", "value": "system|none", "prompt": "owner", "display": true},
                                  {"name": "shares", "value": [], "prompt": "shares", "display": true},
                                  {"name": "source_uri", "value": null, "prompt": "source_uri", "display": true},
                                  {"name": "type", "value": "heaobject.folder.Folder", "prompt": "type", "display": true},
                                  {"name": "version", "value": null, "prompt": "version", "display": true},
                                  {"section": "nested_dict", "name": "foo", "value": "oof", "prompt": "foo", "display": true},
                                  {"section": "nested_dict", "name": "baz", "value": "zab", "prompt": "baz", "display": true},
                                  {"section": "nested_dict", "name": "type", "value": "heaobject.registry.Component", "prompt": "type", "display": true},
                                  {"section": "nested_list", "index": 0, "name": "foo", "value": "oof", "prompt": "foo", "display": true},
                                  {"section": "nested_list", "index": 0, "name": "baz", "value": "zab", "prompt": "baz", "display": true},
                                  {"section": "nested_list", "index": 0, "name": "type", "value": "heaobject.registry.Component", "prompt": "type", "display": true},
                                  {"section": "nested_list", "index": 1, "name": "foo", "value": "oof", "prompt": "foo", "display": true},
                                  {"section": "nested_list", "index": 1, "name": "baz", "value": "zab", "prompt": "baz", "display": true},
                                  {"section": "nested_list", "index": 1, "name": "type", "value": "heaobject.registry.Component", "prompt": "type", "display": true},
                                  {"name": "empty_nested_list", "prompt": "empty_nested_list", "value": [], "display": true},
                                  {"name": "plain_list", "prompt": "plain_list", "value": [1, 2, 3, 4], "display": true}
                                  ],
                                  "rel": "",
                                  "href": "http://localhost:8080/foo/bar/1",
                                  "links": []
                              }
                          ]}}]'''
        self._assert_json_string_equals(expected, actual)

    async def test_formats_data_with_item_link(self):
        runtime_wstl_builder = wstl.builder('servicetest.representor', resource='all_cj_item_link.json')
        runtime_wstl_builder.href = 'http://localhost/test'
        runtime_wstl_builder.add_run_time_action('data-adapter-open', path='foo/bar/{id}',
                                                 root='http://localhost:8080')
        actual, _ = await runtime_wstl_builder.represent_from_request(self.__request(), self.__body)
        expected = '''[{"collection":
                          {"version": "1.0",
                           "href": "http://localhost/test",
                           "permissions": [[]],
                           "items": [
                               {"data": [
                                   {"name": "items", "value": [], "prompt": "items", "display": true},
                                   {"name": "created", "value": "2021-12-02T17:31:15.630000", "prompt": "created", "display": true},
                                   {"name": "derived_by_uri", "value": null, "prompt": "derived_by_uri", "display": true},
                                   {"name": "derived_from_uris", "value": [], "prompt": "derived_from_uris", "display": true},
                                   {"name": "description", "value": null, "prompt": "description", "display": true},
                                   {"name": "display_name", "value": "Reximus", "prompt": "display_name", "display": true},
                                   {"name": "id", "value": "1", "prompt": "id", "display": false},
                                   {"name": "invites", "value": [], "prompt": "invites", "display": true},
                                   {"name": "modified", "value": null, "prompt": "modified", "display": true},
                                   {"name": "name", "value": "reximus", "prompt": "name", "display": true},
                                   {"name": "owner", "value": "system|none", "prompt": "owner", "display": true},
                                   {"name": "shares", "value": [], "prompt": "shares", "display": true},
                                   {"name": "source_uri", "value": null, "prompt": "source_uri", "display": true},
                                   {"name": "type", "value": "heaobject.folder.Folder", "prompt": "type", "display": true},
                                   {"name": "version", "value": null, "prompt": "version", "display": true},
                                   {"section": "nested_dict", "name": "foo", "value": "oof", "prompt": "foo", "display": true},
                                   {"section": "nested_dict", "name": "baz", "value": "zab", "prompt": "baz", "display": true},
                                   {"section": "nested_dict", "name": "type", "value": "heaobject.registry.Component", "prompt": "type", "display": true},
                                   {"section": "nested_list", "index": 0, "name": "foo", "value": "oof", "prompt": "foo", "display": true},
                                   {"section": "nested_list", "index": 0, "name": "baz", "value": "zab", "prompt": "baz", "display": true},
                                   {"section": "nested_list", "index": 0, "name": "type", "value": "heaobject.registry.Component", "prompt": "type", "display": true},
                                   {"section": "nested_list", "index": 1, "name": "foo", "value": "oof", "prompt": "foo", "display": true},
                                   {"section": "nested_list", "index": 1, "name": "baz", "value": "zab", "prompt": "baz", "display": true},
                                   {"section": "nested_list", "index": 1, "name": "type", "value": "heaobject.registry.Component", "prompt": "type", "display": true},
                                   {"name": "empty_nested_list", "prompt": "empty_nested_list", "value": [], "display": true},
                                   {"name": "plain_list", "prompt": "plain_list", "value": [1, 2, 3, 4], "display": true}
                                ],
                                "links": [
                                    {"prompt": "Open", "rel": "", "href": "http://localhost:8080/foo/bar/1"}
                                ]
                           }]}}]'''
        self._assert_json_string_equals(expected, actual)

    async def test_formats_data_with_item_link_item_if_True(self):
        runtime_wstl_builder = wstl.builder('servicetest.representor', resource='all_cj_item_link.json')
        runtime_wstl_builder.href = 'http://localhost/test'
        runtime_wstl_builder.add_run_time_action('data-adapter-open', path='foo/bar/{id}',
                                                 root='http://localhost:8080', itemif='True')
        actual, _ = await runtime_wstl_builder.represent_from_request(self.__request(), self.__body)
        expected = '''[{"collection":
                          {"version": "1.0",
                           "href": "http://localhost/test",
                           "permissions": [[]],
                           "items": [
                               {"data": [
                                   {"name": "items", "value": [], "prompt": "items", "display": true},
                                   {"name": "created", "value": "2021-12-02T17:31:15.630000", "prompt": "created", "display": true},
                                   {"name": "derived_by_uri", "value": null, "prompt": "derived_by_uri", "display": true},
                                   {"name": "derived_from_uris", "value": [], "prompt": "derived_from_uris", "display": true},
                                   {"name": "description", "value": null, "prompt": "description", "display": true},
                                   {"name": "display_name", "value": "Reximus", "prompt": "display_name", "display": true},
                                   {"name": "id", "value": "1", "prompt": "id", "display": false},
                                   {"name": "invites", "value": [], "prompt": "invites", "display": true},
                                   {"name": "modified", "value": null, "prompt": "modified", "display": true},
                                   {"name": "name", "value": "reximus", "prompt": "name", "display": true},
                                   {"name": "owner", "value": "system|none", "prompt": "owner", "display": true},
                                   {"name": "shares", "value": [], "prompt": "shares", "display": true},
                                   {"name": "source_uri", "value": null, "prompt": "source_uri", "display": true},
                                   {"name": "type", "value": "heaobject.folder.Folder", "prompt": "type", "display": true},
                                   {"name": "version", "value": null, "prompt": "version", "display": true},
                                   {"section": "nested_dict", "name": "foo", "value": "oof", "prompt": "foo", "display": true},
                                   {"section": "nested_dict", "name": "baz", "value": "zab", "prompt": "baz", "display": true},
                                   {"section": "nested_dict", "name": "type", "value": "heaobject.registry.Component", "prompt": "type", "display": true},
                                   {"section": "nested_list", "index": 0, "name": "foo", "value": "oof", "prompt": "foo", "display": true},
                                   {"section": "nested_list", "index": 0, "name": "baz", "value": "zab", "prompt": "baz", "display": true},
                                   {"section": "nested_list", "index": 0, "name": "type", "value": "heaobject.registry.Component", "prompt": "type", "display": true},
                                   {"section": "nested_list", "index": 1, "name": "foo", "value": "oof", "prompt": "foo", "display": true},
                                   {"section": "nested_list", "index": 1, "name": "baz", "value": "zab", "prompt": "baz", "display": true},
                                   {"section": "nested_list", "index": 1, "name": "type", "value": "heaobject.registry.Component", "prompt": "type", "display": true},
                                   {"name": "empty_nested_list", "prompt": "empty_nested_list", "value": [], "display": true},
                                   {"name": "plain_list", "prompt": "plain_list", "value": [1, 2, 3, 4], "display": true}
                                ],
                                "links": [
                                    {"prompt": "Open", "rel": "", "href": "http://localhost:8080/foo/bar/1"}
                                ]
                           }]}}]'''
        self._assert_json_string_equals(expected, actual)

    async def test_formats_data_with_item_link_item_if_True_include_data_false(self):
        runtime_wstl_builder = wstl.builder('servicetest.representor', resource='all_cj_item_link.json')
        runtime_wstl_builder.href = 'http://localhost/test'
        runtime_wstl_builder.add_run_time_action('data-adapter-open', path='foo/bar/{id}',
                                                 root='http://localhost:8080', itemif='True')
        actual, _ = await runtime_wstl_builder.represent_from_request(self.__request(), self.__body, include_data=False)
        expected = '''[{"collection":
                          {"version": "1.0",
                           "href": "http://localhost/test",
                           "permissions": [[]],
                           "items": [
                               {"links": [
                                    {"prompt": "Open", "rel": "", "href": "http://localhost:8080/foo/bar/1"}
                                ]
                           }]}}]'''
        self._assert_json_string_equals(expected, actual)

    async def test_formats_data_with_item_link_item_if_False(self):
        runtime_wstl_builder = wstl.builder('servicetest.representor', resource='all_cj_item_link.json')
        runtime_wstl_builder.href = 'http://localhost/test'
        runtime_wstl_builder.add_run_time_action('data-adapter-open', path='/foo/bar/{id}',
                                                 root='http://localhost:8080', itemif='False')
        actual, _ = await runtime_wstl_builder.represent_from_request(self.__request(), self.__body)
        expected = '''[{"collection":
                          {"version": "1.0",
                           "href": "http://localhost/test",
                           "permissions": [[]],
                           "items": [
                               {"data": [
                                   {"name": "items", "value": [], "prompt": "items", "display": true},
                                   {"name": "created", "value": "2021-12-02T17:31:15.630000", "prompt": "created", "display": true},
                                   {"name": "derived_by_uri", "value": null, "prompt": "derived_by_uri", "display": true},
                                   {"name": "derived_from_uris", "value": [], "prompt": "derived_from_uris", "display": true},
                                   {"name": "description", "value": null, "prompt": "description", "display": true},
                                   {"name": "display_name", "value": "Reximus", "prompt": "display_name", "display": true},
                                   {"name": "id", "value": "1", "prompt": "id", "display": false},
                                   {"name": "invites", "value": [], "prompt": "invites", "display": true},
                                   {"name": "modified", "value": null, "prompt": "modified", "display": true},
                                   {"name": "name", "value": "reximus", "prompt": "name", "display": true},
                                   {"name": "owner", "value": "system|none", "prompt": "owner", "display": true},
                                   {"name": "shares", "value": [], "prompt": "shares", "display": true},
                                   {"name": "source_uri", "value": null, "prompt": "source_uri", "display": true},
                                   {"name": "type", "value": "heaobject.folder.Folder", "prompt": "type", "display": true},
                                   {"name": "version", "value": null, "prompt": "version", "display": true},
                                   {"section": "nested_dict", "name": "foo", "value": "oof", "prompt": "foo", "display": true},
                                   {"section": "nested_dict", "name": "baz", "value": "zab", "prompt": "baz", "display": true},
                                   {"section": "nested_dict", "name": "type", "value": "heaobject.registry.Component", "prompt": "type", "display": true},
                                   {"section": "nested_list", "index": 0, "name": "foo", "value": "oof", "prompt": "foo", "display": true},
                                   {"section": "nested_list", "index": 0, "name": "baz", "value": "zab", "prompt": "baz", "display": true},
                                   {"section": "nested_list", "index": 0, "name": "type", "value": "heaobject.registry.Component", "prompt": "type", "display": true},
                                   {"section": "nested_list", "index": 1, "name": "foo", "value": "oof", "prompt": "foo", "display": true},
                                   {"section": "nested_list", "index": 1, "name": "baz", "value": "zab", "prompt": "baz", "display": true},
                                   {"section": "nested_list", "index": 1, "name": "type", "value": "heaobject.registry.Component", "prompt": "type", "display": true},
                                   {"name": "empty_nested_list", "prompt": "empty_nested_list", "value": [], "display": true},
                                   {"name": "plain_list", "prompt": "plain_list", "value": [1, 2, 3, 4], "display": true}
                                ],
                                "links": []
                           }]}}]'''
        self._assert_json_string_equals(expected, actual)

    async def test_formats_data_with_toplevel_link_for_item(self):
        runtime_wstl_builder = wstl.builder('servicetest.representor', resource='all_cj_toplevel_link_for_item.json')
        runtime_wstl_builder.href = 'http://localhost/test'
        runtime_wstl_builder.add_run_time_action('data-adapter-open', path='foo/bar', root='http://localhost:8080')
        actual, _ = await runtime_wstl_builder.represent_from_request(self.__request(), self.__body)
        expected = '''[{"collection": {
                          "version": "1.0",
                          "href": "http://localhost/test",
                          "permissions": [[]],
                          "items": [
                              {"data": [
                                  {"name": "items", "value": [], "prompt": "items", "display": true},
                                  {"name": "created", "value": "2021-12-02T17:31:15.630000", "prompt": "created", "display": true},
                                  {"name": "derived_by_uri", "value": null, "prompt": "derived_by_uri", "display": true},
                                  {"name": "derived_from_uris", "value": [], "prompt": "derived_from_uris", "display": true},
                                  {"name": "description", "value": null, "prompt": "description", "display": true},
                                  {"name": "display_name", "value": "Reximus", "prompt": "display_name", "display": true},
                                  {"name": "id", "value": "1", "prompt": "id", "display": false},
                                  {"name": "invites", "value": [], "prompt": "invites", "display": true},
                                  {"name": "modified", "value": null, "prompt": "modified", "display": true},
                                  {"name": "name", "value": "reximus", "prompt": "name", "display": true},
                                  {"name": "owner", "value": "system|none", "prompt": "owner", "display": true},
                                  {"name": "shares", "value": [], "prompt": "shares", "display": true},
                                  {"name": "source_uri", "value": null, "prompt": "source_uri", "display": true},
                                  {"name": "type", "value": "heaobject.folder.Folder", "prompt": "type", "display": true},
                                  {"name": "version", "value": null, "prompt": "version", "display": true},
                                  {"section": "nested_dict", "name": "foo", "value": "oof", "prompt": "foo", "display": true},
                                  {"section": "nested_dict", "name": "baz", "value": "zab", "prompt": "baz", "display": true},
                                  {"section": "nested_dict", "name": "type", "value": "heaobject.registry.Component", "prompt": "type", "display": true},
                                  {"section": "nested_list", "index": 0, "name": "foo", "value": "oof", "prompt": "foo", "display": true},
                                  {"section": "nested_list", "index": 0, "name": "baz", "value": "zab", "prompt": "baz", "display": true},
                                  {"section": "nested_list", "index": 0, "name": "type", "value": "heaobject.registry.Component", "prompt": "type", "display": true},
                                  {"section": "nested_list", "index": 1, "name": "foo", "value": "oof", "prompt": "foo", "display": true},
                                  {"section": "nested_list", "index": 1, "name": "baz", "value": "zab", "prompt": "baz", "display": true},
                                  {"section": "nested_list", "index": 1, "name": "type", "value": "heaobject.registry.Component", "prompt": "type", "display": true},
                                  {"name": "empty_nested_list", "prompt": "empty_nested_list", "value": [], "display": true},
                                  {"name": "plain_list", "prompt": "plain_list", "value": [1, 2, 3, 4], "display": true}
                               ],
                               "links": []
                               }
                          ],
                          "links": [
                              {"prompt": "Open", "rel": "", "href": "http://localhost:8080/foo/bar"}
                          ]}}]'''
        self._assert_json_string_equals(expected, actual)

    async def test_formats_data_with_toplevel_link_for_list(self):
        runtime_wstl_builder = wstl.builder('servicetest.representor', resource='all_cj_toplevel_link_for_list.json')
        runtime_wstl_builder.href = 'http://localhost/test'
        runtime_wstl_builder.add_run_time_action('data-adapter-list', path='foo/bar', root='http://localhost/test')
        actual, _ = await runtime_wstl_builder.represent_from_request(self.__request(), self.__body)
        expected = '''[{"collection": {
                                  "version": "1.0",
                                  "href": "http://localhost/test",
                                  "permissions": [[]],
                                  "items": [
                                      {"data": [
                                          {"name": "items", "value": [], "prompt": "items", "display": true},
                                          {"name": "created", "value": "2021-12-02T17:31:15.630000", "prompt": "created", "display": true},
                                          {"name": "derived_by_uri", "value": null, "prompt": "derived_by_uri", "display": true},
                                          {"name": "derived_from_uris", "value": [], "prompt": "derived_from_uris", "display": true},
                                          {"name": "description", "value": null, "prompt": "description", "display": true},
                                          {"name": "display_name", "value": "Reximus", "prompt": "display_name", "display": true},
                                          {"name": "id", "value": "1", "prompt": "id", "display": false},
                                          {"name": "invites", "value": [], "prompt": "invites", "display": true},
                                          {"name": "modified", "value": null, "prompt": "modified", "display": true},
                                          {"name": "name", "value": "reximus", "prompt": "name", "display": true},
                                          {"name": "owner", "value": "system|none", "prompt": "owner", "display": true},
                                          {"name": "shares", "value": [], "prompt": "shares", "display": true},
                                          {"name": "source_uri", "value": null, "prompt": "source_uri", "display": true},
                                          {"name": "type", "value": "heaobject.folder.Folder", "prompt": "type", "display": true},
                                          {"name": "version", "value": null, "prompt": "version", "display": true},
                                          {"section": "nested_dict", "name": "foo", "value": "oof", "prompt": "foo", "display": true},
                                          {"section": "nested_dict", "name": "baz", "value": "zab", "prompt": "baz", "display": true},
                                          {"section": "nested_dict", "name": "type", "value": "heaobject.registry.Component", "prompt": "type", "display": true},
                                          {"section": "nested_list", "index": 0, "name": "foo", "value": "oof", "prompt": "foo", "display": true},
                                          {"section": "nested_list", "index": 0, "name": "baz", "value": "zab", "prompt": "baz", "display": true},
                                          {"section": "nested_list", "index": 0, "name": "type", "value": "heaobject.registry.Component", "prompt": "type", "display": true},
                                          {"section": "nested_list", "index": 1, "name": "foo", "value": "oof", "prompt": "foo", "display": true},
                                          {"section": "nested_list", "index": 1, "name": "baz", "value": "zab", "prompt": "baz", "display": true},
                                          {"section": "nested_list", "index": 1, "name": "type", "value": "heaobject.registry.Component", "prompt": "type", "display": true},
                                          {"name": "empty_nested_list", "prompt": "empty_nested_list", "value": [], "display": true},
                                          {"name": "plain_list", "prompt": "plain_list", "value": [1, 2, 3, 4], "display": true}
                                       ],
                                       "links": []
                                       }
                                  ],
                                  "links": [
                                      {"prompt": "List", "rel": "", "href": "http://localhost/test/foo/bar"}
                                  ]}}]'''
        self._assert_json_string_equals(expected, actual)

    async def test_formats_data_with_queries(self):
        runtime_wstl_builder = wstl.builder('servicetest.representor', resource='all_cj_queries.json')
        runtime_wstl_builder.href = 'http://localhost/test'
        runtime_wstl_builder.add_run_time_action('data-adapter-search', path='foo/bar', root='http://localhost/test')
        actual, _ = await runtime_wstl_builder.represent_from_request(self.__request(), self.__body)
        expected = '''[{"collection": {
                              "version": "1.0",
                              "href": "http://localhost/test",
                              "permissions": [[]],
                              "items": [
                                  {"data": [
                                      {"name": "items", "value": [], "prompt": "items", "display": true},
                                      {"name": "created", "value": "2021-12-02T17:31:15.630000", "prompt": "created", "display": true},
                                      {"name": "derived_by_uri", "value": null, "prompt": "derived_by_uri", "display": true},
                                      {"name": "derived_from_uris", "value": [], "prompt": "derived_from_uris", "display": true},
                                      {"name": "description", "value": null, "prompt": "description", "display": true},
                                      {"name": "display_name", "value": "Reximus", "prompt": "display_name", "display": true},
                                      {"name": "id", "value": "1", "prompt": "id", "display": false},
                                      {"name": "invites", "value": [], "prompt": "invites", "display": true},
                                      {"name": "modified", "value": null, "prompt": "modified", "display": true},
                                      {"name": "name", "value": "reximus", "prompt": "name", "display": true},
                                      {"name": "owner", "value": "system|none", "prompt": "owner", "display": true},
                                      {"name": "shares", "value": [], "prompt": "shares", "display": true},
                                      {"name": "source_uri", "value": null, "prompt": "source_uri", "display": true},
                                      {"name": "type", "value": "heaobject.folder.Folder", "prompt": "type", "display": true},
                                      {"name": "version", "value": null, "prompt": "version", "display": true},
                                      {"section": "nested_dict", "name": "foo", "value": "oof", "prompt": "foo", "display": true},
                                      {"section": "nested_dict", "name": "baz", "value": "zab", "prompt": "baz", "display": true},
                                      {"section": "nested_dict", "name": "type", "value": "heaobject.registry.Component", "prompt": "type", "display": true},
                                      {"section": "nested_list", "index": 0, "name": "foo", "value": "oof", "prompt": "foo", "display": true},
                                      {"section": "nested_list", "index": 0, "name": "baz", "value": "zab", "prompt": "baz", "display": true},
                                      {"section": "nested_list", "index": 0, "name": "type", "value": "heaobject.registry.Component", "prompt": "type", "display": true},
                                      {"section": "nested_list", "index": 1, "name": "foo", "value": "oof", "prompt": "foo", "display": true},
                                      {"section": "nested_list", "index": 1, "name": "baz", "value": "zab", "prompt": "baz", "display": true},
                                      {"section": "nested_list", "index": 1, "name": "type", "value": "heaobject.registry.Component", "prompt": "type", "display": true},
                                      {"name": "empty_nested_list", "prompt": "empty_nested_list", "value": [], "display": true},
                                      {"name": "plain_list", "prompt": "plain_list", "value": [1, 2, 3, 4], "display": true}
                                   ],
                                   "links": []
                                   }
                              ],
                              "queries": [{
                                  "data": [{
                                      "name": "keywords",
                                      "pattern": null,
                                      "prompt": "Keywords",
                                      "readOnly": false,
                                      "required": true,
                                      "value": ""}, {
                                      "name": "match-case",
                                      "pattern": null,
                                      "prompt": "Match case?",
                                      "readOnly": false,
                                      "required": true,
                                      "value": ""}],
                                  "href": "http://localhost/test/foo/bar",
                                  "prompt": "Search",
                                  "rel": ""}]}}]'''
        self._assert_json_string_equals(expected, actual)

    async def test_formats_data_with_template(self):
        runtime_wstl_builder = wstl.builder('servicetest.representor', resource='all_cj_template.json')
        runtime_wstl_builder.href = 'http://localhost/test'
        runtime_wstl_builder.add_run_time_action('data-adapter-search', path='/foo/bar', root='http://localhost/test')
        actual, _ = await runtime_wstl_builder.represent_from_request(self.__request(), self.__body)
        expected = '''[{"collection": {
                                  "version": "1.0",
                                  "href": "http://localhost/test",
                                  "permissions": [[]],
                                  "items": [
                                      {"data": [
                                          {"name": "items", "value": [], "prompt": "items", "display": true},
                                          {"name": "created", "value": "2021-12-02T17:31:15.630000", "prompt": "created", "display": true},
                                          {"name": "derived_by_uri", "value": null, "prompt": "derived_by_uri", "display": true},
                                          {"name": "derived_from_uris", "value": [], "prompt": "derived_from_uris", "display": true},
                                          {"name": "description", "value": null, "prompt": "description", "display": true},
                                          {"name": "display_name", "value": "Reximus", "prompt": "display_name", "display": true},
                                          {"name": "id", "value": "1", "prompt": "id", "display": false},
                                          {"name": "invites", "value": [], "prompt": "invites", "display": true},
                                          {"name": "modified", "value": null, "prompt": "modified", "display": true},
                                          {"name": "name", "value": "reximus", "prompt": "name", "display": true},
                                          {"name": "owner", "value": "system|none", "prompt": "owner", "display": true},
                                          {"name": "shares", "value": [], "prompt": "shares", "display": true},
                                          {"name": "source_uri", "value": null, "prompt": "source_uri", "display": true},
                                          {"name": "type", "value": "heaobject.folder.Folder", "prompt": "type", "display": true},
                                          {"name": "version", "value": null, "prompt": "version", "display": true},
                                          {"section": "nested_dict", "name": "foo", "value": "oof", "prompt": "foo", "display": true},
                                          {"section": "nested_dict", "name": "baz", "value": "zab", "prompt": "baz", "display": true},
                                          {"section": "nested_dict", "name": "type", "value": "heaobject.registry.Component", "prompt": "type", "display": true},
                                          {"section": "nested_list", "index": 0, "name": "foo", "value": "oof", "prompt": "foo", "display": true},
                                          {"section": "nested_list", "index": 0, "name": "baz", "value": "zab", "prompt": "baz", "display": true},
                                          {"section": "nested_list", "index": 0, "name": "type", "value": "heaobject.registry.Component", "prompt": "type", "display": true},
                                          {"section": "nested_list", "index": 1, "name": "foo", "value": "oof", "prompt": "foo", "display": true},
                                          {"section": "nested_list", "index": 1, "name": "baz", "value": "zab", "prompt": "baz", "display": true},
                                          {"section": "nested_list", "index": 1, "name": "type", "value": "heaobject.registry.Component", "prompt": "type", "display": true},
                                          {"name": "empty_nested_list", "prompt": "empty_nested_list", "value": [], "display": true},
                                          {"name": "plain_list", "prompt": "plain_list", "value": [1, 2, 3, 4], "display": true}
                                       ],
                                       "links": []
                                       }
                                  ],
                                  "template": {
                                      "data": [
                                          {"name": "keywords",
                                           "pattern": null,
                                           "prompt": "Keywords",
                                           "readOnly": false,
                                           "required": true,
                                           "value": ""},
                                          {"name": "match-case",
                                           "pattern": null,
                                           "prompt": "Match case?",
                                           "readOnly": false,
                                           "required": true,
                                           "value": "",
                                           "type": "select",
                                           "options": [{"value": "true"}, {"value": "false"}]},
                                           {"section": "nested_dict",
                                           "name": "foo",
                                           "pattern": null,
                                           "prompt": "foo",
                                           "required": true,
                                           "value": "oof",
                                           "readOnly": false},
                                           {"section": "nested_dict",
                                           "name": "baz",
                                           "pattern": null,
                                           "prompt": "baz",
                                           "required": true,
                                           "value": "zab",
                                           "readOnly": false},
                                           {"name": "empty_nested_list",
                                           "pattern": null,
                                           "prompt": "Empty nested list",
                                           "readOnly": false,
                                           "required": true,
                                           "value": []},
                                           {"section": "nested_list",
                                           "index": -1,
                                           "name": "foo",
                                           "pattern": null,
                                           "prompt": "foo",
                                           "required": true,
                                           "value": "",
                                           "readOnly": false},
                                           {"section": "nested_list",
                                           "index": -1,
                                           "name": "baz",
                                           "pattern": null,
                                           "prompt": "baz",
                                           "required": true,
                                           "value": "",
                                           "readOnly": false},
                                           {"section": "nested_list",
                                           "index": 0,
                                           "name": "foo",
                                           "pattern": null,
                                           "prompt": "foo",
                                           "required": true,
                                           "value": "oof",
                                           "readOnly": false},
                                           {"section": "nested_list",
                                           "index": 0,
                                           "name": "baz",
                                           "pattern": null,
                                           "prompt": "baz",
                                           "required": true,
                                           "value": "zab",
                                           "readOnly": false},
                                           {"section": "nested_list",
                                           "index": 1,
                                           "name": "foo",
                                           "pattern": null,
                                           "prompt": "foo",
                                           "required": true,
                                           "value": "oof",
                                           "readOnly": false},
                                           {"section": "nested_list",
                                           "index": 1,
                                           "name": "baz",
                                           "pattern": null,
                                           "prompt": "baz",
                                           "required": true,
                                           "value": "zab",
                                           "readOnly": false},
                                           {"name": "plain_list",
                                           "pattern": null,
                                           "prompt": "Plain list",
                                           "required": true,
                                           "value": [1, 2, 3, 4],
                                           "readOnly": false}],
                                      "prompt": "Search",
                                      "rel": ""}}}]'''
        self._assert_json_string_equals(expected, actual)

    async def test_formats_data_with_template_include_data_true(self):
        runtime_wstl_builder = wstl.builder('servicetest.representor', resource='all_cj_template.json')
        runtime_wstl_builder.href = 'http://localhost/test'
        runtime_wstl_builder.add_run_time_action('data-adapter-search', path='/foo/bar', root='http://localhost/test')
        actual, _ = await runtime_wstl_builder.represent_from_request(self.__request(), self.__body, include_data=True)
        expected = '''[{"collection": {
                                  "version": "1.0",
                                  "href": "http://localhost/test",
                                  "permissions": [[]],
                                  "items": [
                                      {"data": [
                                          {"name": "items", "value": [], "prompt": "items", "display": true},
                                          {"name": "created", "value": "2021-12-02T17:31:15.630000", "prompt": "created", "display": true},
                                          {"name": "derived_by_uri", "value": null, "prompt": "derived_by_uri", "display": true},
                                          {"name": "derived_from_uris", "value": [], "prompt": "derived_from_uris", "display": true},
                                          {"name": "description", "value": null, "prompt": "description", "display": true},
                                          {"name": "display_name", "value": "Reximus", "prompt": "display_name", "display": true},
                                          {"name": "id", "value": "1", "prompt": "id", "display": false},
                                          {"name": "invites", "value": [], "prompt": "invites", "display": true},
                                          {"name": "modified", "value": null, "prompt": "modified", "display": true},
                                          {"name": "name", "value": "reximus", "prompt": "name", "display": true},
                                          {"name": "owner", "value": "system|none", "prompt": "owner", "display": true},
                                          {"name": "shares", "value": [], "prompt": "shares", "display": true},
                                          {"name": "source_uri", "value": null, "prompt": "source_uri", "display": true},
                                          {"name": "type", "value": "heaobject.folder.Folder", "prompt": "type", "display": true},
                                          {"name": "version", "value": null, "prompt": "version", "display": true},
                                          {"section": "nested_dict", "name": "foo", "value": "oof", "prompt": "foo", "display": true},
                                          {"section": "nested_dict", "name": "baz", "value": "zab", "prompt": "baz", "display": true},
                                          {"section": "nested_dict", "name": "type", "value": "heaobject.registry.Component", "prompt": "type", "display": true},
                                          {"section": "nested_list", "index": 0, "name": "foo", "value": "oof", "prompt": "foo", "display": true},
                                          {"section": "nested_list", "index": 0, "name": "baz", "value": "zab", "prompt": "baz", "display": true},
                                          {"section": "nested_list", "index": 0, "name": "type", "value": "heaobject.registry.Component", "prompt": "type", "display": true},
                                          {"section": "nested_list", "index": 1, "name": "foo", "value": "oof", "prompt": "foo", "display": true},
                                          {"section": "nested_list", "index": 1, "name": "baz", "value": "zab", "prompt": "baz", "display": true},
                                          {"section": "nested_list", "index": 1, "name": "type", "value": "heaobject.registry.Component", "prompt": "type", "display": true},
                                          {"name": "empty_nested_list", "prompt": "empty_nested_list", "value": [], "display": true},
                                          {"name": "plain_list", "prompt": "plain_list", "value": [1, 2, 3, 4], "display": true}
                                       ],
                                       "links": []
                                       }
                                  ],
                                  "template": {
                                      "data": [
                                          {"name": "keywords",
                                           "pattern": null,
                                           "prompt": "Keywords",
                                           "readOnly": false,
                                           "required": true,
                                           "value": ""},
                                          {"name": "match-case",
                                           "pattern": null,
                                           "prompt": "Match case?",
                                           "readOnly": false,
                                           "required": true,
                                           "value": "",
                                           "type": "select",
                                           "options": [{"value": "true"}, {"value": "false"}]},
                                           {"section": "nested_dict",
                                           "name": "foo",
                                           "pattern": null,
                                           "prompt": "foo",
                                           "required": true,
                                           "value": "oof",
                                           "readOnly": false},
                                           {"section": "nested_dict",
                                           "name": "baz",
                                           "pattern": null,
                                           "prompt": "baz",
                                           "required": true,
                                           "value": "zab",
                                           "readOnly": false},
                                           {"name": "empty_nested_list",
                                           "pattern": null,
                                           "prompt": "Empty nested list",
                                           "readOnly": false,
                                           "required": true,
                                           "value": []},
                                           {"section": "nested_list",
                                           "index": -1,
                                           "name": "foo",
                                           "pattern": null,
                                           "prompt": "foo",
                                           "required": true,
                                           "value": "",
                                           "readOnly": false},
                                           {"section": "nested_list",
                                           "index": -1,
                                           "name": "baz",
                                           "pattern": null,
                                           "prompt": "baz",
                                           "required": true,
                                           "value": "",
                                           "readOnly": false},
                                           {"section": "nested_list",
                                           "index": 0,
                                           "name": "foo",
                                           "pattern": null,
                                           "prompt": "foo",
                                           "required": true,
                                           "value": "oof",
                                           "readOnly": false},
                                           {"section": "nested_list",
                                           "index": 0,
                                           "name": "baz",
                                           "pattern": null,
                                           "prompt": "baz",
                                           "required": true,
                                           "value": "zab",
                                           "readOnly": false},
                                           {"section": "nested_list",
                                           "index": 1,
                                           "name": "foo",
                                           "pattern": null,
                                           "prompt": "foo",
                                           "required": true,
                                           "value": "oof",
                                           "readOnly": false},
                                           {"section": "nested_list",
                                           "index": 1,
                                           "name": "baz",
                                           "pattern": null,
                                           "prompt": "baz",
                                           "required": true,
                                           "value": "zab",
                                           "readOnly": false},
                                           {"name": "plain_list",
                                           "pattern": null,
                                           "prompt": "Plain list",
                                           "required": true,
                                           "value": [1, 2, 3, 4],
                                           "readOnly": false}],
                                      "prompt": "Search",
                                      "rel": ""}}}]'''
        self._assert_json_string_equals(expected, actual)

    async def test_formats_data_with_template_include_data_false(self):
        runtime_wstl_builder = wstl.builder('servicetest.representor', resource='all_cj_template.json')
        runtime_wstl_builder.href = 'http://localhost/test'
        runtime_wstl_builder.add_run_time_action('data-adapter-search', path='/foo/bar', root='http://localhost/test')
        actual, _ = await runtime_wstl_builder.represent_from_request(self.__request(), self.__body, include_data=False)
        expected = '''[{"collection": {
                                  "version": "1.0",
                                  "href": "http://localhost/test",
                                  "permissions": [[]],
                                  "items": [
                                      {"links": []}
                                  ],
                                  "template": {
                                      "data": [
                                          {"name": "keywords",
                                           "pattern": null,
                                           "prompt": "Keywords",
                                           "readOnly": false,
                                           "required": true,
                                           "value": ""},
                                          {"name": "match-case",
                                           "pattern": null,
                                           "prompt": "Match case?",
                                           "readOnly": false,
                                           "required": true,
                                           "value": "",
                                           "type": "select",
                                           "options": [{"value": "true"}, {"value": "false"}]},
                                           {"section": "nested_dict",
                                           "name": "foo",
                                           "pattern": null,
                                           "prompt": "foo",
                                           "required": true,
                                           "value": "oof",
                                           "readOnly": false},
                                           {"section": "nested_dict",
                                           "name": "baz",
                                           "pattern": null,
                                           "prompt": "baz",
                                           "required": true,
                                           "value": "zab",
                                           "readOnly": false},
                                           {"name": "empty_nested_list",
                                           "pattern": null,
                                           "prompt": "Empty nested list",
                                           "readOnly": false,
                                           "required": true,
                                           "value": []},
                                           {"section": "nested_list",
                                           "index": -1,
                                           "name": "foo",
                                           "pattern": null,
                                           "prompt": "foo",
                                           "required": true,
                                           "value": "",
                                           "readOnly": false},
                                           {"section": "nested_list",
                                           "index": -1,
                                           "name": "baz",
                                           "pattern": null,
                                           "prompt": "baz",
                                           "required": true,
                                           "value": "",
                                           "readOnly": false},
                                           {"section": "nested_list",
                                           "index": 0,
                                           "name": "foo",
                                           "pattern": null,
                                           "prompt": "foo",
                                           "required": true,
                                           "value": "oof",
                                           "readOnly": false},
                                           {"section": "nested_list",
                                           "index": 0,
                                           "name": "baz",
                                           "pattern": null,
                                           "prompt": "baz",
                                           "required": true,
                                           "value": "zab",
                                           "readOnly": false},
                                           {"section": "nested_list",
                                           "index": 1,
                                           "name": "foo",
                                           "pattern": null,
                                           "prompt": "foo",
                                           "required": true,
                                           "value": "oof",
                                           "readOnly": false},
                                           {"section": "nested_list",
                                           "index": 1,
                                           "name": "baz",
                                           "pattern": null,
                                           "prompt": "baz",
                                           "required": true,
                                           "value": "zab",
                                           "readOnly": false},
                                           {"name": "plain_list",
                                           "pattern": null,
                                           "prompt": "Plain list",
                                           "required": true,
                                           "value": [1, 2, 3, 4],
                                           "readOnly": false}],
                                      "prompt": "Search",
                                      "rel": ""}}}]'''
        self._assert_json_string_equals(expected, actual)

    async def test_parses_template(self):
        cj_str = '{"template": {"data": [{"name": "foo", "value": "bar"}, {"name": "baz", "value": "oof"}]}}'
        actual = await cj.CJ().parse(self.__request(cj_str))
        expected = {"foo": "bar", "baz": "oof"}
        self.assertEqual(expected, actual)

    async def test_parses_missing_data_object(self):
        cj_str = '{"template": {}}'
        actual = await cj.CJ().parse(self.__request(cj_str))
        expected = {}
        self.assertEqual(expected, actual)

    async def test_parses_empty_data_array(self):
        cj_str = '{"template": {"data": []}}'
        actual = await cj.CJ().parse(self.__request(cj_str))
        expected = {}
        self.assertEqual(expected, actual)

    async def test_parses_missing_template_property(self):
        with self.assertRaises(error.ParseException):
            await cj.CJ().parse(self.__request('{"tmplte": {"data": []}}'))

    async def test_parses_empty(self):
        with self.assertRaises(error.ParseException):
            await cj.CJ().parse(self.__request('{}'))

    async def test_parses_no_name(self):
        with self.assertRaises(error.ParseException):
            await cj.CJ().parse(self.__request('{"template": {"data": [{"nm": "foo"}]}}'))

    async def test_parses_no_list(self):
        with self.assertRaises(error.ParseException):
            await cj.CJ().parse(self.__request('{"template": {"data": {"name": "foo"}}}'))

    def __request(self, jsons: str = None) -> AsyncMock:
        request = AsyncMock(spec=Request)
        request.text.return_value = jsons
        request.json.side_effect = lambda loads=json.loads: loads(jsons)
        request.match_info = {}
        header_md = CIMultiDict()
        header_md[hdrs.ACCEPT] = cj.MIME_TYPE
        request.headers = CIMultiDictProxy(header_md)
        return request

    def test_to_nvpjson(self):
        input = {'template': {'data': [
            {"name": "id",
             "value": "1"},
            {"name": "derived_by_uri",
             "value": None},
            {"name": "derived_from_uris",
             "value": []},
            {"name": "invites",
             "value": []},
            {"name": "description",
             "value": None},
            {"name": "modified",
             "value": None},
            {"name": "source_uri",
             "value": None},
            {"name": "version",
             "value": None},
            {"name": "display_name",
             "value": "Reximus"},
            {"name": "name",
             "value": "reximus"},
            {"name": "owner",
             "value": user.NONE_USER},
            {"section": "nested_dict",
             "name": "foo",
             "value": "oof"},
            {"section": "nested_dict",
             "name": "baz",
             "value": "zab"},
            {"name": "empty_nested_list",
             "value": []},
            {"name": "shares",
             "value": []},
            {"section": "nested_list",
             "index": 0,
             "name": "foo",
             "value": "oof"},
            {"section": "nested_list",
             "index": 1,
             "name": "foo",
             "value": "oof"},
            {"section": "nested_list",
             "index": 0,
             "name": "baz",
             "value": "zab"},
            {"section": "nested_list",
             "index": 1,
             "name": "baz",
             "value": "zab"},
            {"name": "plain_list",
             "value": [1, 2, 3, 4]},
            {"name": "created",
             "value": datetime(2021, 12, 2, 17, 31, 15, 630000)}
        ]}}
        expected = {
            'created': datetime(2021, 12, 2, 17, 31, 15, 630000),
            'derived_by_uri': None,
            'derived_from_uris': [],
            'description': None,
            'display_name': 'Reximus',
            'id': '1',
            'invites': [],
            'modified': None,
            'name': 'reximus',
            'owner': user.NONE_USER,
            'shares': [],
            'source_uri': None,
            'version': None,
            'nested_dict': {'foo': 'oof', 'baz': 'zab'},
            'nested_list': [{'foo': 'oof', 'baz': 'zab'},
                            {'foo': 'oof', 'baz': 'zab'}],
            'empty_nested_list': [],
            'plain_list': [1, 2, 3, 4]
        }
        actual = cj.to_nvpjson(input)
        return self.assertEqual(expected, actual)

    def test_add_extended_property_values_with_optionsFromUrl(self):
        input = {
            "hea": {
                "optionsFromUrl": {
                    'href': 'http://localhost:8080/people/',
                    "path": "/people/",
                    "value": "name",
                    "text": "display_name"
                }
            },
            "type": "select",
            "name": "user",
            "prompt": "User"
        }
        actual = {}
        expected = {
            'options': {
                'href': 'http://localhost:8080/people/',
                'text': 'display_name',
                'value': 'name'
            },
            "type": "select"
        }
        cj.add_extended_property_values(input, actual)
        self.assertEqual(expected, actual)

    def test_add_extended_property_values_with_suggest(self):
        input = {
            "suggest": [
                {"value": "COOWNER", "text": "Co-owner"},
                {"value": "CREATOR", "text": "Creator"},
                {"value": "DELETER", "text": "Deleter"},
                {"value": "EDITOR", "text": "Editor"},
                {"value": "SHARER", "text": "Sharer"},
                {"value": "VIEWER", "text": "Viewer"}
            ],
            "type": "select",
            "name": "user",
            "prompt": "User"
        }
        actual = {}
        expected = {
            'options': [
                {"value": "COOWNER", "text": "Co-owner"},
                {"value": "CREATOR", "text": "Creator"},
                {"value": "DELETER", "text": "Deleter"},
                {"value": "EDITOR", "text": "Editor"},
                {"value": "SHARER", "text": "Sharer"},
                {"value": "VIEWER", "text": "Viewer"}
            ],
            "type": "select"
        }
        cj.add_extended_property_values(input, actual)
        self.assertEqual(expected, actual)

    def test_add_extended_property_values_with_related(self):
        input = {
            "suggest": {
                "related": "testList",
                "value": "id",
                "text": "userName"
            },
            "type": "select",
            "name": "user",
            "prompt": "User",
            "related": {
                "testList": [
                    {
                        "id": 1,
                        "userName": 'joe'
                    }
                ]
            }
        }
        actual = {}
        expected = {
            'options': [{'text': 'joe', 'value': 1}], 'type': 'select'
        }
        cj.add_extended_property_values(input, actual)
        self.assertEqual(expected, actual)
