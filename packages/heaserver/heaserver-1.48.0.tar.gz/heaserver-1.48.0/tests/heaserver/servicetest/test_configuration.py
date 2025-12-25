import unittest

import heaserver.service.defaults
from heaserver.service import runner
from unittest.mock import patch
from unittest.result import TestResult as _TestResult  # Keeps pytest from trying to parse it as a test case.
from typing import Optional
from heaserver.service.config import Configuration
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile
from cryptography.fernet import Fernet


class TestDefaultConfiguration(unittest.TestCase):

    def run(self, result: Optional[_TestResult] = None) -> Optional[_TestResult]:
        """
        Patches sys.argv with an empty list before running each test. This keeps pytest command line argument parsing
        from conflicting with HEA command line argument parsing.

        :param result: a TestResult object for compiling which tests passed and failed.
        :return: the same TestResult object, with the results of another test recorded.
        """
        with patch.object(sys, 'argv', []):
            return super().run(result)

    def setUp(self) -> None:
        self.config = runner.init_cmd_line(description='foo')

    def test_default_base_url(self) -> None:
        self.assertEqual(heaserver.service.defaults.DEFAULT_BASE_URL, self.config.base_url)


class TestCustomConfiguration(unittest.TestCase):

    def run(self, result: Optional[_TestResult] = None) -> Optional[_TestResult]:
        """
        Patches sys.argv with an empty list before running each test. This keeps pytest command line argument parsing
        from conflicting with HEA command line argument parsing.

        :param result: a TestResult object for compiling which tests passed and failed.
        :return: the same TestResult object, with the results of another test recorded.
        """
        with patch.object(sys, 'argv', []):
            return super().run(result)

    def setUp(self) -> None:
        self.config_str = """
[DEFAULT]
Registry = http://customhost:9090/hea-service
EncryptionKey = Xx0TnPIeA4B2jokub4HMjKkIIqDPBdEpPFtD8gD70Fg=
"""
        self.config = Configuration(config_str=self.config_str)

    def test_custom_registry(self) -> None:
        self.assertEqual('http://customhost:9090/hea-service', self.config.registry_url)

    def test_encryption_key(self) -> None:
        self.assertEqual(b'Xx0TnPIeA4B2jokub4HMjKkIIqDPBdEpPFtD8gD70Fg=', self.config.get_attribute_encryption_key())


class TestCustomConfigurationWithEncryptionKeyFile(unittest.TestCase):

    def run(self, result: Optional[_TestResult] = None) -> Optional[_TestResult]:
        """
        Patches sys.argv with an empty list before running each test. This keeps pytest command line argument parsing
        from conflicting with HEA command line argument parsing.

        :param result: a TestResult object for compiling which tests passed and failed.
        :return: the same TestResult object, with the results of another test recorded.
        """
        with patch.object(sys, 'argv', []):
            return super().run(result)

    def setUp(self) -> None:
        with NamedTemporaryFile(delete=False) as temp_file:
            self.temp_file = temp_file
            self.key = Fernet.generate_key()
            self.temp_file.write(self.key)

        self.config_str = f"""
[DEFAULT]
Registry = http://customhost:9090/hea-service
EncryptionKeyFile = {self.temp_file.name}
"""
        self.config = Configuration(config_str=self.config_str)

    def tearDown(self):
        Path(self.temp_file.name).unlink(missing_ok=True)

    def test_encryption_key_file(self) -> None:
        self.assertEqual(self.temp_file.name, self.config.encryption_key_file)

    def test_encryption_key_from_file(self) -> None:
        self.assertEqual(self.key, self.config.get_attribute_encryption_key())
