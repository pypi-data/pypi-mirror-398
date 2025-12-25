from unittest import TestCase, IsolatedAsyncioTestCase
from aiohttp.test_utils import make_mocked_request
from heaserver.service.db.mongoexpr import mongo_expr, sub_filter_expr
from heaobject.user import NONE_USER, ALL_USERS
from heaobject.root import PermissionContext
from heaserver.service.heaobjectsupport import RESTPermissionGroup


class MongoExpressionTestCase(TestCase):
    __mock_request = make_mocked_request('GET',
                                         '/',
                                         match_info={
                                             'id': 'foo',
                                             'name': 'foobar',
                                             'display_name': 'Foo Bar'
                                         })

    def test_var_parts_str_mongoattributes_str(self) -> None:
        """
        Checks if mongo_expr returns the expected expression when var_parts is an aiohttp dynamic resource variable
        part and mongoattributes is a string.
        """
        self.assertDictEqual({'bar': 'foo'}, mongo_expr(self.__mock_request, var_parts='id', mongoattributes='bar'))

    def test_var_parts_str_mongoattributes_none(self) -> None:
        """
        Checks if mongo_expr returns the expected expression when var_parts is an aiohttp dynamic resource variable
        part and mongoattributes is None.
        """
        self.assertDictEqual({'id': 'foo'}, mongo_expr(self.__mock_request, var_parts='id'))

    def test_var_parts_any_mongoattributes_dict(self) -> None:
        """
        Checks if mongo_expr returns the expected expression when var_parts is None and mongoattributes is a
        dictionary.
        """
        mongo_attrs = {
            'resources': {
                '$elemMatch': {
                    'resource_type_name': {
                        '$eq': 'heaobject.folder.Folder'
                    },
                    '$or': [
                        {
                            'file_system_type': {
                                '$exists': False
                            }
                        },
                        {
                            'file_system_type': {
                                '$in': [
                                    'heaobject.volume.MongoDBFileSystem',
                                    None
                                ]
                            }
                        }
                    ]
                }
            }
        }
        self.assertDictEqual(mongo_attrs, mongo_expr(self.__mock_request, var_parts=None, mongoattributes=mongo_attrs))

    def test_var_parts_iter_mongoattributes_str_iter(self):
        """
        Checks if mongo_expr returns the expected expression when var_parts is an iterable of aiohttp dynamic
        resource variable parts and mongoattributes is an iterable of strings.
        """
        self.assertDictEqual({
                                 'foo': 'foo',
                                 'bar': 'foobar',
                                 'baz': 'Foo Bar'
                             }, mongo_expr(self.__mock_request, var_parts=['id', 'name', 'display_name'],
                                           mongoattributes=['foo', 'bar', 'baz']))

    def test_var_parts_iter_mongoattributes_none(self):
        """
        Checks if mongo_expr returns the expected expression when var_parts is an iterable of aiohttp dynamic
        resource variable parts and mongoattributes is None.
        """
        self.assertDictEqual({
            'id': 'foo',
            'name': 'foobar',
            'display_name': 'Foo Bar'
        }, mongo_expr(self.__mock_request, var_parts=['id', 'name', 'display_name']))

    def test_var_parts_int_mongoattributes_int(self):
        """
        Checks if mongo_expr raises a TypeError when both are specified but are neither a dict, an iterable of
        strings nor a string.
        """
        self.assertRaises(TypeError, mongo_expr, self.__mock_request, var_parts=1, mongoattributes=2)

    def test_var_parts_none_mongoattributes_none(self):
        """Checks if mongo_expr returns an empty expression when both var_parts and mongoattributes are None."""
        self.assertDictEqual({}, mongo_expr(self.__mock_request, var_parts=None, mongoattributes=None))

    def test_extra(self):
        """Checks if mongo_expr returns the expected expression when extra is specified."""
        extra = {
            'resources': {
                '$elemMatch': {
                    'resource_type_name': {
                        '$eq': 'heaobject.folder.Folder'
                    },
                    '$or': [
                        {
                            'file_system_type': {
                                '$exists': False
                            }
                        },
                        {
                            'file_system_type': {
                                '$in': [
                                    'heaobject.volume.MongoDBFileSystem',
                                    None
                                ]
                            }
                        }
                    ]
                }
            }
        }
        self.assertDictEqual({'bar': 'foo', **extra}, mongo_expr(self.__mock_request, var_parts='id',
                                                                 mongoattributes='bar', extra=extra))

    def test_extra_invalid(self):
        """Checks if mongo_expr raises a TypeError when extra is not a dictionary."""
        self.assertRaises(TypeError, mongo_expr, self.__mock_request, var_parts='id', mongoattributes='bar', extra=1)


class SubFilterExpressionTestCase(IsolatedAsyncioTestCase):
    async def test_with_perms(self):
        """Checks if sub_filter_expr returns the correct expression when permissions are specified."""
        self.assertDictEqual({
            '$or': [
                {'owner': NONE_USER},
                {'dynamic_permission_supported': True},
                {
                    'shares': {
                        '$elemMatch': {
                            '$or': [{'user': {'$in': [NONE_USER, ALL_USERS]}}, {'group': {'$in': []}}],
                            'permissions': {
                                '$elemMatch': {
                                    '$in': RESTPermissionGroup.GETTER_PERMS.get_perms_as_strs()
                                }
                            }
                        }
                    }
                }
            ]
        }, await sub_filter_expr(permissions=RESTPermissionGroup.GETTER_PERMS.get_perms_as_strs(),
                                 context=PermissionContext(NONE_USER)))

    async def test_no_perms(self):
        """Checks if sub_filter_expr returns the correct expression when permissions are not specified."""
        self.assertDictEqual({
            '$or': [
                {
                    'owner': NONE_USER
                },
                {
                    'dynamic_permission_supported': True
                },
                {
                    'shares': {
                        '$elemMatch': {
                            '$or': [{'user': {'$in': [NONE_USER, ALL_USERS]}}, {'group': {'$in': []}}],
                            'permissions': {
                                '$elemMatch': {
                                    '$in': []
                                }
                            }
                        }
                    }
                }
            ]
        }, await sub_filter_expr(permissions=[], context=PermissionContext(NONE_USER)))
