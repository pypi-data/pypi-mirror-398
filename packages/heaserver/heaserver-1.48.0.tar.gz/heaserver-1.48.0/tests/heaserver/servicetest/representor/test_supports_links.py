import unittest
from heaserver.service.representor import cj, nvpjson


class TestFactory(unittest.TestCase):

    def test_cj(self):
        self.assertTrue(cj.CJ.supports_links())

    def test_default(self):
        self.assertFalse(nvpjson.NVPJSON.supports_links())
