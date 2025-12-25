from unittest import TestCase
from heaserver.service import response


class TestResponse(TestCase):
    def test_status_not_found_body_str(self):
        assert response.status_not_found('Salt Lake City').body == b'Salt Lake City'

    def test_status_not_found_body_bytes(self):
        assert response.status_not_found(b'Salt Lake City').body == b'Salt Lake City'

    def test_status_multiple_choices_body_str(self):
        assert response.status_multiple_choices('http://localhost/multchoice',
                                                body='Salt Lake City').body == b'Salt Lake City'

    def test_status_multiple_choices_body_bytes(self):
        assert response.status_multiple_choices('http://localhost/multchoice',
                                                body=b'Salt Lake City').body == b'Salt Lake City'

    def test_status_bad_request_body_str(self):
        assert response.status_bad_request('Salt Lake City').body == b'Salt Lake City'

    def test_status_bad_request_body_bytes(self):
        assert response.status_bad_request(b'Salt Lake City').body == b'Salt Lake City'

    def test_status_ok_body_str(self):
        assert response.status_ok('Salt Lake City').body == b'Salt Lake City'

    def test_status_ok_body_bytes(self):
        assert response.status_ok(b'Salt Lake City').body == b'Salt Lake City'

    def test_status_not_found_body_none(self):
        assert response.status_not_found(None).body == b'404: Not Found'

    def test_status_multiple_choices_body_none(self):
        assert response.status_multiple_choices('http://localhost/multchoice',
                                                body=None).body == b'300: Multiple Choices'

    def test_status_bad_request_body_none(self):
        assert response.status_bad_request(None).body == b'400: Bad Request'

    def test_status_ok_body_none(self):
        assert response.status_ok(None).body == b'200: OK'

    def test_status_not_found_body_omitted(self):
        assert response.status_not_found().body == b'404: Not Found'

    def test_status_multiple_choices_body_omitted(self):
        assert response.status_multiple_choices('http://localhost/multchoice').body == b'300: Multiple Choices'

    def test_status_bad_request_body_omitted(self):
        assert response.status_bad_request().body == b'400: Bad Request'

    def test_status_ok_body_omitted(self):
        assert response.status_ok().body == b'200: OK'
