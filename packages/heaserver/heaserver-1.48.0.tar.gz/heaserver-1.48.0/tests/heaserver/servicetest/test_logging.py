"""
Tests for the SensitiveDataFilter logging filter. It tests with a logger named as this module's __name__.
"""
from abc import ABC, abstractmethod
import logging
from unittest import TestCase

from yarl import URL
from heaserver.service.logging import ScrubbingLogger, SensitiveDataFilter
from heaobject.keychain import AWSCredentials


log_record = {
    'user': 'alice',
    'password': 'mysecretpassword',
    'token': 'abcd1234',
    'info': 'This is a test log'
}

log_record_list = [log_record]

EXPECTED = "User login attempt: {'user': 'alice', 'password': '******', 'token': '******', 'info': 'This is a test log'}\n"


class AbstractTestLogging(TestCase, ABC):

    @abstractmethod
    def __init__(self, filter: logging.Filter, methodName='runTest'):
        super().__init__(methodName=methodName)
        self.filter = filter

    def setUp(self):
        self.logger = ScrubbingLogger(__name__)
        self.logger.propagate = False
        self.logger.setLevel(logging.INFO)
        self.stream_handler = logging.StreamHandler()
        self.stream_handler.addFilter(self.filter)
        self.logger.addHandler(self.stream_handler)

    def tearDown(self):
        try:
            self.stream_handler.close()
        finally:
            self.stream_handler.removeFilter(self.filter)
            self.logger.removeHandler(self.stream_handler)
            # There's no way to remove a logger from the logging module's internal registry,

    def _read_output_keys(self) -> str:
        return self._read_output('User login attempt: %r', log_record)

    def _read_output_str(self) -> str:
        return self._read_output(f'User login attempt: {log_record}')

    def _read_output_keys_list(self) -> str:
        return self._read_output('User login attempt: %r', log_record_list)

    def _read_output(self, str, args=None) -> str:
        self.logger.info(str, args) if args else self.logger.info(str)
        stream = self.stream_handler.stream
        stream.seek(0)
        return stream.read()


class TestKeyScrubbing(AbstractTestLogging):
    def __init__(self, methodName='runTest'):
        super().__init__(SensitiveDataFilter(), methodName=methodName)

    def test_logging_sensitive_keys(self):
        self.assertEqual(EXPECTED, self._read_output_keys())

class TestStrScrubbing(AbstractTestLogging):
    def __init__(self, methodName='runTest'):
        super().__init__(SensitiveDataFilter(), methodName=methodName)

    def test_logging_sensitive_str(self):
        self.assertEqual(EXPECTED, self._read_output_str())

    def test_logging_sensitive_str_regex(self):
        message = "Getting content at %s with headers"
        url = 'http://heaserver-volumes:8080/volumes/byfilesystemtype/heaobject.volume.AWSFileSystem?account_id=heaobject.account.AWSAccount%5E123456678901'
        expected = "Getting content at http://heaserver-volumes:8080/volumes/byfilesystemtype/heaobject.volume.AWSFileSystem?account_id=****** with headers\n"
        self.assertEqual(expected, self._read_output(message, url))

    def test_logging_sensitive_URL_regex(self):
        message = "Getting content at %s with headers"
        url = URL('http://heaserver-volumes:8080/volumes/byfilesystemtype/heaobject.volume.AWSFileSystem?account_id=heaobject.account.AWSAccount%5E123456678901')
        expected = "Getting content at http://heaserver-volumes:8080/volumes/byfilesystemtype/heaobject.volume.AWSFileSystem?account_id=****** with headers\n"
        self.assertEqual(expected, self._read_output(message, url))


class TestListScrubbing(AbstractTestLogging):
    def __init__(self, methodName='runTest'):
        super().__init__(SensitiveDataFilter(), methodName=methodName)

    def test_logging_sensitive_list(self):
        expected = "User login attempt: [{'user': 'alice', 'password': '******', 'token': '******', 'info': 'This is a test log'}]\n"
        self.assertEqual(expected, self._read_output_keys_list())


class CustomSensitiveDataFilter(SensitiveDataFilter):
    sensitive_keys = SensitiveDataFilter.sensitive_keys | {'user'}
EXPECTED_CUSTOM = "User login attempt: {'user': '******', 'password': '******', 'token': '******', 'info': 'This is a test log'}\n"

class TestCustomKeyList(AbstractTestLogging):
    def __init__(self, methodName='runTest'):
        super().__init__(CustomSensitiveDataFilter(), methodName=methodName)

    def test_logging_sensitive_keys_extra_keys(self):
        self.assertEqual(EXPECTED_CUSTOM, self._read_output_keys())

class TestInStrCustomKeyList(AbstractTestLogging):
    def __init__(self, methodName='runTest'):
        super().__init__(CustomSensitiveDataFilter(), methodName=methodName)

    def test_logging_sensitive_str_extra_keys(self):
        self.assertEqual(EXPECTED_CUSTOM, self._read_output_str())


class AWSCredentialsLogging(AbstractTestLogging):
    def __init__(self, methodName='runTest'):
        super().__init__(SensitiveDataFilter(), methodName=methodName)

    def test_logging_aws_credentials(self):
        self.maxDiff = None
        c: AWSCredentials = AWSCredentials()
        c.password = 'mysecretpassword'
        c.session_token = 'abcd1234'
        actual = self._read_output('User login attempt: %r', c)
        self.assertIn("'display_name': '******'", actual)
        self.assertIn("'session_token': '******'", actual)
        self.assertIn("'password': '******'", actual)
        self.assertIn("'managed': False", actual)

class SequenceOfAWSCredentialsLogging(AbstractTestLogging):
    def __init__(self, methodName='runTest'):
        super().__init__(SensitiveDataFilter(), methodName=methodName)
        self.maxDiff = None
        self.c1: AWSCredentials = AWSCredentials()
        self.c1.password = 'mysecretpassword1'
        self.c1.session_token = 'abcd1234'
        self.c2: AWSCredentials = AWSCredentials()
        self.c2.password = 'mysecretpassword2'
        self.c2.session_token = 'efgh5678'

    def test_logging_list_of_aws_credentials(self):
        actual = self._read_output('User login attempt: %r', [self.c1, self.c2])
        self.assertIn("'display_name': '******'", actual)
        self.assertIn("'session_token': '******'", actual)
        self.assertIn("'password': '******'", actual)
        self.assertIn("'managed': False", actual)

    def test_logging_tuple_of_aws_credentials(self):
        actual = self._read_output('User login attempt: %r', (self.c1, self.c2))
        self.assertIn("'display_name': '******'", actual)
        self.assertIn("'session_token': '******'", actual)
        self.assertIn("'password': '******'", actual)
        self.assertIn("'managed': False", actual)

class TestNonStrings(AbstractTestLogging):
    def __init__(self, methodName='runTest'):
        super().__init__(SensitiveDataFilter(), methodName=methodName)

    def test_logging_integer(self):
        self.assertEqual('User login attempt: 4\n', self._read_output('User login attempt: %d', 4))

    def test_logging_decimal(self):
        self.assertEqual('User login attempt: 4.20\n', self._read_output('User login attempt: %.2f', 4.2))

class TestScrubRegexes(AbstractTestLogging):
    def __init__(self, methodName='runTest'):
        super().__init__(SensitiveDataFilter(), methodName=methodName)

    def test_logging_sensitive_regex(self):
        log_record = 'Received access_token=abcd1234 from user'
        expected = 'Received access_token=****** from user\n'
        self.assertEqual(expected, self._read_output(log_record))

    def test_logging_unsensitive_regex(self):
        log_record = 'No sensitive data here'
        expected = 'No sensitive data here\n'
        self.assertEqual(expected, self._read_output(log_record))
