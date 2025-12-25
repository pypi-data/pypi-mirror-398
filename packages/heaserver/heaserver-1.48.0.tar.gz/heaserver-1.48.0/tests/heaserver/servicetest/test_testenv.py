from unittest import TestCase
from heaserver.service.testcase.testenv import MicroserviceContainerConfig


class TestEnvTestCase(TestCase):
    def test_port_microservice_ports(self):
        c = MicroserviceContainerConfig('foo', 8080)
        self.assertTrue([8080], c.ports)

    def test_port_microservice_port(self):
        c = MicroserviceContainerConfig('foo', 8080)
        self.assertTrue(8080, c.port)

    def test_port_microservice_none(self):
        with self.assertRaises(ValueError):
            MicroserviceContainerConfig('foo', None)
