from unittest import TestCase
from aiohttp.test_utils import make_mocked_request
from heaserver.service.db.mongoservicelib import MongoSortOrder


class MongoServiceLibTestCase(TestCase):

    def test_sort_from_request(self):
        """Make sure one sort order without an attribute correctly uses the provided default attribute."""
        request = make_mocked_request('GET', '/test?sort=asc')
        self.assertEqual([('foo', MongoSortOrder.ASCENDING)], list(MongoSortOrder.from_request(request, 'foo')))

    def test_sort_from_request_key_case_sensitivity(self):
        """Make sure one sort order without an attribute correctly uses the provided default attribute."""
        request = make_mocked_request('GET', '/test?SORT=asc')
        self.assertEqual([], list(MongoSortOrder.from_request(request, 'foo')))

    def test_sort_from_request_value_case_insensitivity(self):
        """Make sure one sort order without an attribute correctly uses the provided default attribute."""
        request = make_mocked_request('GET', '/test?sort=ASC')
        self.assertEqual([('foo', MongoSortOrder.ASCENDING)], list(MongoSortOrder.from_request(request, 'foo')))

    def test_sort_multiple_from_request(self):
        """Make sure multiple sort orders without attributes correctly error out."""
        request = make_mocked_request('GET', '/test?sort=asc&sort=desc')
        with self.assertRaises(ValueError):
            self.assertEqual([('foo', MongoSortOrder.ASCENDING)],
                            list(MongoSortOrder.from_request(request, 'foo')))

    def test_sort_two_sorts_and_one_attr_from_request(self):
        """Make sure one missing sort attribute is replaced with the provided default."""
        request = make_mocked_request('GET', '/test?sort=asc&sort=desc&sort_attr=bar')
        self.assertEqual([('bar', MongoSortOrder.ASCENDING),
                          ('foo', MongoSortOrder.DESCENDING)],
                          list(MongoSortOrder.from_request(request, 'foo')))

    def test_sort_two_orders_and_two_attrs_from_request(self):
        """Make sure sort attributes and orders are correctly extracted."""
        request = make_mocked_request('GET', '/test?sort=asc&sort=desc&sort_attr=bar&sort_attr=foo')
        self.assertEqual([('bar', MongoSortOrder.ASCENDING),
                          ('foo', MongoSortOrder.DESCENDING)],
                          list(MongoSortOrder.from_request(request)))

    def test_sort_two_orders_and_three_attrs_from_request(self):
        """Make sure sort attributes without orders are sorted in ascending order."""
        request = make_mocked_request('GET', '/test?sort=asc&sort=desc&sort_attr=bar&sort_attr=foo&sort_attr=baz')
        self.assertEqual([('bar', MongoSortOrder.ASCENDING),
                          ('foo', MongoSortOrder.DESCENDING),
                          ('baz', MongoSortOrder.ASCENDING)],
                          list(MongoSortOrder.from_request(request)))

    def test_sort_three_attrs_and_no_orders_from_request(self):
        """Make sure sort attributes without orders are sorted in ascending order."""
        request = make_mocked_request('GET', '/test?sort_attr=bar&sort_attr=foo&sort_attr=baz')
        self.assertEqual([('bar', MongoSortOrder.ASCENDING),
                          ('foo', MongoSortOrder.ASCENDING),
                          ('baz', MongoSortOrder.ASCENDING)],
                          list(MongoSortOrder.from_request(request)))

    def test_sort_as_dict(self):
        """Make sure sort orders and attributes are correctly extracted as a dict."""
        request = make_mocked_request('GET', '/test?sort=asc&sort=desc&sort_attr=bar&sort_attr=foo')
        self.assertEqual({'bar': MongoSortOrder.ASCENDING.value,
                          'foo': MongoSortOrder.DESCENDING.value},
                          MongoSortOrder.from_request_dict(request))
