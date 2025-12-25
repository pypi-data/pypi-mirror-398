import unittest
import sys
from heaserver.service.testcase import testenv, mockaws, mockmongo

class MyTestCase(unittest.TestCase):
    def test_docker_imported(self):
        self.assertFalse('docker' in sys.modules)

    def test_testcontainers_imported(self):
        self.assertFalse('testcontainers' in sys.modules)
