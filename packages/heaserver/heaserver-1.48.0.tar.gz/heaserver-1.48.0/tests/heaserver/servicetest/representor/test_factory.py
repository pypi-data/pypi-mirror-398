import unittest
from heaserver.service.representor import factory, cj, nvpjson, wstljson
from heaserver.service.representor.factory import AcceptHeaderFilter


class TestFactory(unittest.TestCase):

    def test_from_content_type_none(self):
        self.assertIsInstance(factory.from_content_type_header(None), cj.CJ)

    def test_from_content_type_empty_string(self):
        self.assertIsInstance(factory.from_content_type_header(''), cj.CJ)

    def test_from_content_type_cj(self):
        self.assertIsInstance(factory.from_content_type_header(cj.MIME_TYPE), cj.CJ)

    def test_from_content_type_json(self):
        self.assertIsInstance(factory.from_content_type_header(nvpjson.MIME_TYPE), nvpjson.NVPJSON)

    def test_from_content_type_wstljson(self):
        self.assertIsInstance(factory.from_content_type_header(wstljson.MIME_TYPE), wstljson.WeSTLJSON)

    def test_from_content_type_cj_case(self):
        self.assertIsInstance(factory.from_content_type_header(cj.MIME_TYPE.upper()), cj.CJ)

    def test_from_accept_cj(self):
        self.assertIsInstance(factory.from_accept_header(cj.MIME_TYPE + ';q=2, ' +
                                                         nvpjson.MIME_TYPE + '; q=1, ' +
                                                         wstljson.MIME_TYPE + ';q=0'), cj.CJ)

    def test_from_accept_json(self):
        self.assertIsInstance(factory.from_accept_header(cj.MIME_TYPE + '; q=1, ' +
                                                         nvpjson.MIME_TYPE + ';q=2, ' +
                                                         wstljson.MIME_TYPE), nvpjson.NVPJSON)

    def test_from_accept_wstljson(self):
        self.assertIsInstance(factory.from_accept_header(cj.MIME_TYPE + ',' +
                                                         nvpjson.MIME_TYPE + ';q=2, ' +
                                                         wstljson.MIME_TYPE + '; q=3'), wstljson.WeSTLJSON)

    def test_from_accept_default(self):
        self.assertIsInstance(factory.from_accept_header(None), cj.CJ)

    def test_from_accept_filter_none(self):
        self.assertIsInstance(factory.from_accept_header(None, None), cj.CJ)

    def test_from_accept_filter_any(self):
        self.assertIsInstance(factory.from_accept_header(None, AcceptHeaderFilter.ANY), cj.CJ)

    def test_from_accept_filter_links(self):
        self.assertIsInstance(factory.from_accept_header(None, AcceptHeaderFilter.SUPPORTS_LINKS), cj.CJ)

    def test_from_accept_filter_links_wstl(self):
        self.assertIsNone(factory.from_accept_header(wstljson.MIME_TYPE, AcceptHeaderFilter.SUPPORTS_LINKS))
