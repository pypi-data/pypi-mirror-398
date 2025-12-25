from unittest import IsolatedAsyncioTestCase, TestCase

from aiohttp.test_utils import make_mocked_request
from heaobject.aws import AWSDesktopObject, S3StorageClass, S3ArchiveDetailState
from heaobject.data import AWSS3FileObject
from heaobject.root import Permission
from heaserver.service.db import awsservicelib
from botocore.exceptions import ClientError

import heaserver.service.db.aws
from heaserver.service.db.aws import S3ObjectPermissionContext
from heaserver.service.testcase.mockaws import MockS3
from collections.abc import Sequence
from types import MethodType

class TestAWSServiceLib(TestCase):

    def test_handle_client_error_404(self):
        c = ClientError(error_response={'Error': {'Code': heaserver.service.db.aws.CLIENT_ERROR_404}}, operation_name='foo')
        self.assertEqual(404, awsservicelib.handle_client_error(c).status)

    def test_handle_client_error_no_such_bucket(self):
        c = ClientError(error_response={'Error': {'Code': heaserver.service.db.aws.CLIENT_ERROR_NO_SUCH_BUCKET}}, operation_name='foo')
        self.assertEqual(404, awsservicelib.handle_client_error(c).status)

    def test_handle_client_error_unknown(self):
        c = ClientError(error_response={'Error': {'Code': "It's wrecked"}},
                        operation_name='foo')
        self.assertEqual(500, awsservicelib.handle_client_error(c).status)


class TestArchiveStatus(IsolatedAsyncioTestCase):

    def setUp(self):
        self.request = make_mocked_request('GET', '/')
        self.request.app['HEA_db'] = MockS3(None)
        self.perm_context: S3ObjectPermissionContext = S3ObjectPermissionContext(self.request)

        async def mock_is_super_admin(self) -> bool:
            return False
        async def mock_simulate_perms(self, obj: AWSDesktopObject, actions: Sequence[str]) -> list[Permission]:
            return [Permission.VIEWER, Permission.EDITOR, Permission.DELETER]
        async def mock_is_account_owner(self) -> bool:
            return False
        self.perm_context.is_super_admin = MethodType(mock_is_super_admin, self.perm_context)
        self.perm_context._simulate_perms = MethodType(mock_simulate_perms, self.perm_context)
        self.perm_context.is_account_owner = MethodType(mock_is_account_owner, self.perm_context)

    async def test_handle_display_name_attribute_permissions_glacier_deep_archive(self):
        obj: AWSS3FileObject = AWSS3FileObject()
        obj.storage_class = S3StorageClass.DEEP_ARCHIVE
        obj.archive_detail_state = S3ArchiveDetailState.ARCHIVED
        obj.key = 'test_key'
        self.assertEqual([Permission.VIEWER], await self.perm_context.get_attribute_permissions(obj, 'display_name'))

    async def test_handle_display_name_attribute_permissions_glacier_instant_retrieval(self):
        obj: AWSS3FileObject = AWSS3FileObject()
        obj.storage_class = S3StorageClass.GLACIER_IR
        obj.archive_detail_state = S3ArchiveDetailState.NOT_ARCHIVED
        obj.key = 'test_key'
        self.assertEqual(set([Permission.VIEWER, Permission.EDITOR]), set(await self.perm_context.get_attribute_permissions(obj, 'display_name')))

    async def test_handle_display_name_attribute_permissions_standard(self):
        obj: AWSS3FileObject = AWSS3FileObject()
        obj.storage_class = S3StorageClass.STANDARD
        obj.key = 'test_key'
        self.assertEqual(set([Permission.VIEWER, Permission.EDITOR]), set(await self.perm_context.get_attribute_permissions(obj, 'display_name')))

    async def test_handle_display_name_attribute_permissions_unknown(self):
        obj: AWSS3FileObject = AWSS3FileObject()
        obj.key = 'test_key'
        self.assertEqual(set([Permission.VIEWER, Permission.EDITOR]), set(await self.perm_context.get_attribute_permissions(obj, 'display_name')))

    async def test_handle_display_name_attribute_permissions_restoring(self):
        obj: AWSS3FileObject = AWSS3FileObject()
        obj.key = 'test_key'
        obj.storage_class = S3StorageClass.DEEP_ARCHIVE
        obj.archive_detail_state = S3ArchiveDetailState.RESTORING
        self.assertEqual([Permission.VIEWER], await self.perm_context.get_attribute_permissions(obj, 'display_name'))

    async def test_handle_display_name_attribute_permissions_restored(self):
        obj: AWSS3FileObject = AWSS3FileObject()
        obj.key = 'test_key'
        obj.storage_class = S3StorageClass.DEEP_ARCHIVE
        obj.archive_detail_state = S3ArchiveDetailState.RESTORED
        self.assertEqual(set([Permission.VIEWER, Permission.EDITOR]), set(await self.perm_context.get_attribute_permissions(obj, 'display_name')))




