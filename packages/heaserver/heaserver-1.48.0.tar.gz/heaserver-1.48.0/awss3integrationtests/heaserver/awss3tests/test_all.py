from unittest import IsolatedAsyncioTestCase


from .awss3foldertestcase import AWSS3FolderTestCase
from heaserver.service.db.aws import S3
import boto3
from moto import mock_aws


class TestS3GetAccount(IsolatedAsyncioTestCase):

    @mock_aws()
    def run(self, result):
        super().run(result)

    async def test_get_account(self):
        sts = boto3.client('sts')
        actual = await S3._get_basic_account_info(sts)
        self.assertEqual('123456789012', actual.id)


class TestAWSProperties(AWSS3FolderTestCase):
    async def test_get_property(self):
        async with self.client.request('GET', '/properties/CLOUD_AWS_CRED_URL') as resp:
            self.assertEqual(200, resp.status)

    async def test_get_property_not_found(self):
        async with self.client.request('GET', '/properties/TEST') as resp:
            self.assertEqual(404, resp.status)


class TestMockAWSAccount(AWSS3FolderTestCase):
    @mock_aws()
    def run(self, result):
        super().run(result)

    async def test_get_volume_id_for_account_id(self):
        async with self.client.request('GET', '/accounts/123456789012') as resp:
            self.assertEqual(200, resp.status)


