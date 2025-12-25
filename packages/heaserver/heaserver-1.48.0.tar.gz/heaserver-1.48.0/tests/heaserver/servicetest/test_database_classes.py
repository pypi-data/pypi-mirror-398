from unittest import TestCase
from heaserver.service.db.mongo import Mongo
from heaserver.service.testcase.mockmongo import MockMongo
from heaserver.service.util import public_methods


class TestMockMongo(TestCase):
    def test_has_same_public_methods(self):
        MockMongo_public_methods = public_methods(MockMongo)
        Mongo_public_methods = public_methods(Mongo)
        blacklist = [Mongo.aggregate.__name__]
        def missing_methods():
            return ', '.join(method for method in Mongo_public_methods \
                             if method not in MockMongo_public_methods and method not in blacklist)
        self.assertTrue(set(MockMongo_public_methods).issuperset(set(Mongo_public_methods) - set(blacklist)),
                        f'Missing methods: {missing_methods()}')

