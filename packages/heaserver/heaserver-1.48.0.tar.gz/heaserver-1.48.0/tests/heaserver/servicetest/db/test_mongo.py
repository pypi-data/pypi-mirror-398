from unittest import TestCase
from heaserver.service.db.mongo import replace_id_with_object_id
from bson import ObjectId


class ReplaceIDWithObjectIDTestCase(TestCase):
    def test_replace_id_with_object_id(self):
        """Checks if replace_id_with_object_id replaces the id field with an ObjectID object."""
        expected = {'_id': ObjectId('666f6f2d6261722d71757578'), 'something': 'bar'}
        actual = replace_id_with_object_id({'id': '666f6f2d6261722d71757578', 'something': 'bar'})
        self.assertEqual(expected, actual)
