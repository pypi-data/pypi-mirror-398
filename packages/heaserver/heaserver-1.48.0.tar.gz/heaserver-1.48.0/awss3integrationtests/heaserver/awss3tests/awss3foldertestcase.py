"""
Runs integration tests for the HEA folder service.

Note that each test opens an aiohttp server listening on port 8080.
"""

from heaserver.service.db.database import CollectionKey
from heaserver.service.testcase import expectedvalues
from heaserver.service.testcase.awss3microservicetestcase import get_test_case_cls_default
from heaserver.service.db.database import get_collection_from_name
from heaserver.service.testcase.dockermongo import MockDockerMongoManager

from heaserver.service.testcase.awsdockermongo import MockS3WithMockDockerMongoManager
from . import service
from heaserver.service.testcase.mockaws import MockS3Manager
from heaobject import user
from heaobject.root import Permission

from base64 import b64encode

db_values = {CollectionKey(name='awss3folders_items', db_manager_cls=MockS3Manager): [
    {
        'created': '2022-05-17T00:00:00+00:00',
        'derived_by': None,
        'derived_from': [],
        'description': None,
        'display_name': 'TestFolder',
        'id': 'VGVzdEZvbGRlci8=',
        'instance_id': 'heaobject.folder.AWSS3ItemInFolder^VGVzdEZvbGRlci8=',
        'invites': [],
        'modified': '2022-05-17T00:00:00+00:00',
        'name': 'VGVzdEZvbGRlci8=',
        'owner': user.NONE_USER,
        'shares': [],
        'source': 'AWS S3',
        'source_detail': None,
        'type': 'heaobject.folder.AWSS3ItemInFolder',
        'actual_object_type_name': 'heaobject.folder.AWSS3Folder',
        'actual_object_id': 'VGVzdEZvbGRlci8=',
        'actual_object_uri': '/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3folders/VGVzdEZvbGRlci8=',
        's3_uri': 's3://arp-scale-2-cloud-bucket-with-tags11/TestFolder/',
        'storage_class': 'STANDARD',
        'mime_type': 'application/x.item',
        'size': None,
        'human_readable_size': None,
        'volume_id': '666f6f2d6261722d71757578',
        'folder_id': 'root',
        'bucket_id': 'arp-scale-2-cloud-bucket-with-tags11',
        'key': 'TestFolder/',
        'super_admin_default_permissions': [],
        'dynamic_permission_supported': False
    },
    {
        'created': '2022-05-17T00:00:00+00:00',
        'derived_by': None,
        'derived_from': [],
        'description': None,
        'display_name': 'TestFolder2',
        'id': 'VGVzdEZvbGRlcjIv',
        'instance_id': 'heaobject.folder.AWSS3ItemInFolder^VGVzdEZvbGRlcjIv',
        'invites': [],
        'modified': '2022-05-17T00:00:00+00:00',
        'name': 'VGVzdEZvbGRlcjIv',
        'owner': user.NONE_USER,
        'shares': [],
        'source': 'AWS S3',
        'source_detail': None,
        'type': 'heaobject.folder.AWSS3ItemInFolder',
        'actual_object_type_name': 'heaobject.folder.AWSS3Folder',
        'actual_object_id': 'VGVzdEZvbGRlcjIv',
        'actual_object_uri': '/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3folders/VGVzdEZvbGRlcjIv',
        's3_uri': 's3://arp-scale-2-cloud-bucket-with-tags11/TestFolder2/',
        'storage_class': 'STANDARD',
        'mime_type': 'application/x.item',
        'size': None,
        'human_readable_size': None,
        'volume_id': '666f6f2d6261722d71757578',
        'folder_id': 'root',
        'bucket_id': 'arp-scale-2-cloud-bucket-with-tags11',
        'key': 'TestFolder2/',
        'super_admin_default_permissions': [],
        'dynamic_permission_supported': False
    }
],
    CollectionKey(name='components', db_manager_cls=MockDockerMongoManager): [
        {
            'id': '666f6f2d6261722d71757578',
            'created': None,
            'derived_by': None,
            'derived_from': [],
            'description': None,
            'display_name': 'Reximus',
            'invited': [],
            'modified': None,
            'name': 'reximus',
            'owner': user.NONE_USER,
            'shared_with': [],
            'source': None,
            'type': 'heaobject.registry.Component',
            'base_url': 'http://localhost:8080',
            'resources': [{'type': 'heaobject.registry.Resource', 'resource_type_name': 'heaobject.folder.AWSS3Folder',
                           'base_path': 'volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3folders',
                           'resource_collection_type_display_name': 'heaobject.folder.AWSS3Folder', 'manages_creators': False},
                          {'type': 'heaobject.registry.Resource', 'resource_type_name': 'heaobject.folder.AWSS3Item',
                           'base_path': 'items',
                           'resource_collection_type_display_name': 'heaobject.folder.AWSS3Item', 'manages_creators': False}],
        'super_admin_default_permissions': [Permission.VIEWER.name, Permission.EDITOR.name],
        'dynamic_permission_supported': False
        }
    ],
    CollectionKey(name='filesystems', db_manager_cls=MockDockerMongoManager): [{
        'id': '666f6f2d6261722d71757578',
        'created': None,
        'derived_by': None,
        'derived_from': [],
        'description': None,
        'display_name': 'Amazon Web Services',
        'invited': [],
        'modified': None,
        'name': 'DEFAULT_FILE_SYSTEM',
        'owner': user.NONE_USER,
        'shared_with': [],
        'source': None,
        'type': 'heaobject.volume.AWSFileSystem',
        'super_admin_default_permissions': [p.name for p in Permission],
        'dynamic_permission_supported': False
    }],
    CollectionKey(name='volumes', db_manager_cls=MockDockerMongoManager): [{
        'id': '666f6f2d6261722d71757578',
        'created': None,
        'derived_by': None,
        'derived_from': [],
        'description': None,
        'display_name': 'My Amazon Web Services',
        'invited': [],
        'modified': None,
        'name': 'amazon_web_services',
        'owner': user.NONE_USER,
        'shared_with': [],
        'source': None,
        'type': 'heaobject.volume.Volume',
        'file_system_name': 'DEFAULT_FILE_SYSTEM',
        'file_system_type': 'heaobject.volume.AWSFileSystem',
        'credential_id': None,  # Let boto3 try to find the user's credentials.
        'super_admin_default_permissions': [p.name for p in Permission],
        'dynamic_permission_supported': False
    }],
    CollectionKey(name='buckets', db_manager_cls=MockS3Manager): [{
        "arn": None,
        "created": '2022-05-17T00:00:00+00:00',
        "derived_by": None,
        "derived_from": [],
        "description": None,
        "display_name": "arp-scale-2-cloud-bucket-with-tags11",
        "encrypted": True,
        "id": "arp-scale-2-cloud-bucket-with-tags11",
        "invites": [],
        "locked": False,
        "mime_type": "application/x.awsbucket",
        "modified": '2022-05-17T00:00:00+00:00',
        "name": "arp-scale-2-cloud-bucket-with-tags11",
        "object_count": None,
        "owner": "system|none",
        "permission_policy": None,
        "region": "us-west-2",
        "s3_uri": "s3://arp-scale-2-cloud-bucket-with-tags11/",
        "shares": [],
        "size": None,
        "source": None,
        "tags": [],
        "type": "heaobject.bucket.AWSBucket",
        "versioned": False,
        'super_admin_default_permissions': [],
        'dynamic_permission_supported': False
    },
    {
        "arn": None,
        "created": '2022-05-17T00:00:00+00:00',
        "derived_by": None,
        "derived_from": [],
        "description": None,
        "display_name": "arp-scale-2-cloud-bucket-with-tags1",
        "encrypted": True,
        "id": "arp-scale-2-cloud-bucket-with-tags1",
        "invites": [],
        "locked": False,
        "mime_type": "application/x.awsbucket",
        "modified": '2022-05-17T00:00:00+00:00',
        "name": "arp-scale-2-cloud-bucket-with-tags1",
        "object_count": None,
        "owner": "system|none",
        "permission_policy": None,
        "region": "us-west-2",
        "s3_uri": "s3://arp-scale-2-cloud-bucket-with-tags1/",
        "shares": [],
        "size": None,
        "source": None,
        "tags": [],
        "type": "heaobject.bucket.AWSBucket",
        "versioned": False,
        'super_admin_default_permissions': [],
        'dynamic_permission_supported': False
    }
    ],
    CollectionKey(name='awsaccounts', db_manager_cls=MockS3Manager): [
        {
            'email_address': 'no-reply@example.com',
            'alternate_contact_name': None,
            "alternate_email_address": None,
            "alternate_phone_number": None,
            "created": '2022-05-17T00:00:00+00:00',
            "derived_by": None,
            "derived_from": [],
            "description": None,
            "display_name": "311813441058",
            "full_name": None,
            "id": "311813441058",
            "invites": [],
            "mime_type": "application/x.awsaccount",
            "modified": '2022-05-17T00:00:00+00:00',
            "name": "311813441058",
            "owner": "system|none",
            "phone_number": None,
            "shares": [],
            "source": None,
            "type": "heaobject.account.AWSAccount",
            'super_admin_default_permissions': [],
            'dynamic_permission_supported': False
        }
    ],
    CollectionKey(name='awss3folders', db_manager_cls=MockS3Manager): [{
        'created': '2022-05-17T00:00:00+00:00',
        'derived_by': None,
        'derived_from': [],
        'description': None,
        'display_name': 'TestFolder',
        'id': 'VGVzdEZvbGRlci8=',
        'invites': [],
        'modified': '2022-05-17T00:00:00+00:00',
        'name': 'VGVzdEZvbGRlci8=',
        'owner': user.NONE_USER,
        'shares': [],
        'source': 'AWS S3',
        'type': 'heaobject.folder.AWSS3Folder',
        'mime_type': 'application/x.folder',
        's3_uri': 's3://arp-scale-2-cloud-bucket-with-tags11/TestFolder/',
        'storage_class': 'STANDARD',
        'presigned_url': None,
        'bucket_id': 'arp-scale-2-cloud-bucket-with-tags11',
        'key': 'TestFolder/',
        'super_admin_default_permissions': [],
        'dynamic_permission_supported': False
    },
        {
            'created': '2022-05-17T00:00:00+00:00',
            'derived_by': None,
            'derived_from': [],
            'description': None,
            'display_name': 'TestFolder2',
            'id': 'VGVzdEZvbGRlcjIv',
            'invites': [],
            'modified': '2022-05-17T00:00:00+00:00',
            'name': 'VGVzdEZvbGRlcjIv',
            'owner': user.NONE_USER,
            'shares': [],
            'source': 'AWS S3',
            'type': 'heaobject.folder.AWSS3Folder',
            'mime_type': 'application/x.folder',
            's3_uri': 's3://arp-scale-2-cloud-bucket-with-tags11/TestFolder2/',
            'storage_class': 'STANDARD',
            'presigned_url': None,
            'bucket_id': 'arp-scale-2-cloud-bucket-with-tags11',
            'key': 'TestFolder2/',
            'super_admin_default_permissions': [],
            'dynamic_permission_supported': False
        }
    ],
    CollectionKey(name='credentials', db_manager_cls=MockDockerMongoManager): [
        {
            'id': '0123456789ab0123456789ab',
            'created': None,
            'derived_by': None,
            'derived_from': [],
            'description': None,
            'display_name': 'Luximus',
            'invites': [],
            'modified': None,
            'name': 'luximus',
            'owner': user.NONE_USER,
            'shares': [],
            'source': None,
            'account': None,
            'where': 'us-east-1',
            'password': None,
            'session_token': None,
            'expiration': '2022-05-16T12:34:41Z',
            'role_arn': "arn:aws:193843492343:test_role",
            'type': 'heaobject.keychain.AWSCredentials',
            'super_admin_default_permissions': [p.name for p in Permission],
            'dynamic_permission_supported': False
        },
        {
            'id': '666f6f2d6261722d71757578',
            'created': None,
            'derived_by': None,
            'derived_from': [],
            'description': None,
            'display_name': 'Luximus',
            'invites': [],
            'modified': None,
            'name': 'luximus',
            'owner': user.NONE_USER,
            'shares': [],
            'source': None,
            'account': '1234',
            'where': None,
            'password': 'cloud_password1',
            'session_token': 'cloud_token',
            'expiration': '2022-05-18T12:34:41Z',
            'role_arn': None,
            'type': 'heaobject.keychain.AWSCredentials',
            'super_admin_default_permissions': [p.name for p in Permission],
            'dynamic_permission_supported': False
        }
    ],
    CollectionKey(name='properties', db_manager_cls=MockDockerMongoManager): [{
        "type": "heaobject.registry.Property",
        "name": "CLOUD_AWS_CRED_URL",
        "display_name": "CLOUD_AWS_CRED_URL",
        "value": "https://amazon_test_api_gateway.us-west-1.amazonaws.com/creds",
        "created": "2022-05-17T00:00:00+00:00",
        "owner": user.NONE_USER,
        "shares": [
            {
                "type": "heaobject.root.ShareImpl",
                "user": "system|all",
                "permissions": ["VIEWER"]
            }
        ],
        'super_admin_default_permissions': [p.name for p in Permission],
        'dynamic_permission_supported': False
    }
    ]

}

content_ = [{'collection': {'version': '1.0', 'href': 'http://localhost:8080/folders/root/items/', 'items': [{'data': [
    {'name': 'created', 'value': None, 'prompt': 'created', 'display': True},
    {'name': 'derived_by', 'value': None, 'prompt': 'derived_by', 'display': True},
    {'name': 'derived_from', 'value': [], 'prompt': 'derived_from', 'display': True},
    {'name': 'description', 'value': None, 'prompt': 'description', 'display': True},
    {'name': 'display_name', 'value': 'Reximus', 'prompt': 'display_name', 'display': True},
    {'name': 'id', 'value': '666f6f2d6261722d71757578', 'prompt': 'id', 'display': False},
    {'name': 'invites', 'value': [], 'prompt': 'invites', 'display': True},
    {'name': 'modified', 'value': None, 'prompt': 'modified', 'display': True},
    {'name': 'name', 'value': 'reximus', 'prompt': 'name', 'display': True},
    {'name': 'owner', 'value': 'system|none', 'prompt': 'owner', 'display': True},
    {'name': 'shares', 'value': [], 'prompt': 'shares', 'display': True},
    {'name': 'source', 'value': None, 'prompt': 'source', 'display': True},
    {'name': 'actual_object_type_name', 'value': 'heaobject.folder.Folder', 'prompt': 'actual_object_type_name',
     'display': True},
    {'name': 'actual_object_id', 'value': '666f6f2d6261722d71757579', 'prompt': 'actual_object_id', 'display': True},
    {'name': 'folder_id', 'value': 'root', 'prompt': 'folder_id', 'display': True},
    {'name': 'bucket_id', 'prompt': 'bucket_id', 'value': 'arp-scale-2-cloud-bucket-with-tags11'},
    {'name': 'key', 'prompt': 'key', 'value': 'Reximus/'},
    {'section': 'actual_object', 'name': 'created', 'value': None, 'prompt': 'created', 'display': True},
    {'section': 'actual_object', 'name': 'derived_by', 'value': None, 'prompt': 'derived_by', 'display': True},
    {'section': 'actual_object', 'name': 'derived_from', 'value': [], 'prompt': 'derived_from', 'display': True},
    {'section': 'actual_object', 'name': 'description', 'value': None, 'prompt': 'description', 'display': True},
    {'section': 'actual_object', 'name': 'display_name', 'value': 'Reximus', 'prompt': 'display_name', 'display': True},
    {'section': 'actual_object', 'name': 'id', 'value': '666f6f2d6261722d71757579', 'prompt': 'id', 'display': False},
    {'section': 'actual_object', 'name': 'invites', 'value': [], 'prompt': 'invites', 'display': True},
    {'section': 'actual_object', 'name': 'modified', 'value': None, 'prompt': 'modified', 'display': True},
    {'section': 'actual_object', 'name': 'name', 'value': 'reximus', 'prompt': 'name', 'display': True},
    {'section': 'actual_object', 'name': 'owner', 'value': 'system|none', 'prompt': 'owner', 'display': True},
    {'section': 'actual_object', 'name': 'shares', 'value': [], 'prompt': 'shares', 'display': True},
    {'section': 'actual_object', 'name': 'source', 'value': None, 'prompt': 'source', 'display': True},
    {'section': 'actual_object', 'name': 'version', 'value': None, 'prompt': 'version', 'display': True},
    {'section': 'actual_object', 'name': 'mime_type', 'value': 'application/x.folder', 'prompt': 'mime_type',
     'display': True}], 'links': [{'prompt': 'Move', 'rel': 'mover',
                                   'href': 'http://localhost:8080/folders/root/items/666f6f2d6261722d71757578/mover'},
                                  {'prompt': 'Open', 'rel': 'hea-opener-choices',
                                   'href': 'http://localhost:8080/folders/root/items/666f6f2d6261722d71757578/opener'},
                                  {'prompt': 'Duplicate', 'rel': 'duplicator',
                                   'href': 'http://localhost:8080/folders/root/items/666f6f2d6261722d71757578/duplicator'}]}],
                            'template': {'prompt': 'Properties', 'rel': 'properties', 'data': [
                                {'name': 'id', 'value': '666f6f2d6261722d71757578', 'prompt': 'Id', 'required': True,
                                 'readOnly': True, 'pattern': ''},
                                {'name': 'source', 'value': None, 'prompt': 'Source', 'required': False,
                                 'readOnly': False, 'pattern': ''},
                                {'name': 'version', 'value': None, 'prompt': 'Version', 'required': False,
                                 'readOnly': False, 'pattern': ''},
                                {'name': 'display_name', 'value': 'Reximus', 'prompt': 'Name', 'required': True,
                                 'readOnly': False, 'pattern': ''},
                                {'name': 'description', 'value': None, 'prompt': 'Description', 'required': False,
                                 'readOnly': False, 'pattern': ''},
                                {'name': 'owner', 'value': 'system|none', 'prompt': 'Owner', 'required': False,
                                 'readOnly': False, 'pattern': ''},
                                {'name': 'created', 'value': None, 'prompt': 'Created', 'required': False,
                                 'readOnly': True, 'pattern': ''},
                                {'name': 'modified', 'value': None, 'prompt': 'Modified', 'required': False,
                                 'readOnly': True, 'pattern': ''},
                                {'name': 'invites', 'value': [], 'prompt': 'Share invites', 'required': False,
                                 'readOnly': True, 'pattern': ''},
                                {'name': 'shares', 'value': [], 'prompt': 'Shared with', 'required': False,
                                 'readOnly': False, 'pattern': ''},
                                {'name': 'derived_by', 'value': None, 'prompt': 'Derived by', 'required': False,
                                 'readOnly': True, 'pattern': ''},
                                {'name': 'derived_from', 'value': [], 'prompt': 'Derived from', 'required': False,
                                 'readOnly': True, 'pattern': ''},
                                {'name': 'items', 'value': None, 'prompt': 'Items', 'required': False, 'readOnly': True,
                                 'pattern': ''}]}}}, {
                'collection': {'version': '1.0', 'href': 'http://localhost:8080/folders/root/items/', 'items': [{
                    'data': [
                        {
                            'name': 'created',
                            'value': None,
                            'prompt': 'created',
                            'display': True},
                        {
                            'name': 'derived_by',
                            'value': None,
                            'prompt': 'derived_by',
                            'display': True},
                        {
                            'name': 'derived_from',
                            'value': [],
                            'prompt': 'derived_from',
                            'display': True},
                        {
                            'name': 'description',
                            'value': None,
                            'prompt': 'description',
                            'display': True},
                        {
                            'name': 'display_name',
                            'value': 'Reximus',
                            'prompt': 'display_name',
                            'display': True},
                        {
                            'name': 'id',
                            'value': '0123456789ab0123456789ab',
                            'prompt': 'id',
                            'display': False},
                        {
                            'name': 'invites',
                            'value': [],
                            'prompt': 'invites',
                            'display': True},
                        {
                            'name': 'modified',
                            'value': None,
                            'prompt': 'modified',
                            'display': True},
                        {
                            'name': 'name',
                            'value': 'reximus',
                            'prompt': 'name',
                            'display': True},
                        {
                            'name': 'owner',
                            'value': 'system|none',
                            'prompt': 'owner',
                            'display': True},
                        {
                            'name': 'shares',
                            'value': [],
                            'prompt': 'shares',
                            'display': True},
                        {
                            'name': 'source',
                            'value': None,
                            'prompt': 'source',
                            'display': True},
                        {
                            'name': 'actual_object_type_name',
                            'value': 'heaobject.folder.Folder',
                            'prompt': 'actual_object_type_name',
                            'display': True},
                        {
                            'name': 'actual_object_id',
                            'value': '0123456789ab0123456789ac',
                            'prompt': 'actual_object_id',
                            'display': True},
                        {
                            'name': 'folder_id',
                            'value': 'root',
                            'prompt': 'folder_id',
                            'display': True},
                        {
                            'section': 'actual_object',
                            'name': 'created',
                            'value': None,
                            'prompt': 'created',
                            'display': True},
                        {
                            'section': 'actual_object',
                            'name': 'derived_by',
                            'value': None,
                            'prompt': 'derived_by',
                            'display': True},
                        {
                            'section': 'actual_object',
                            'name': 'derived_from',
                            'value': [],
                            'prompt': 'derived_from',
                            'display': True},
                        {
                            'section': 'actual_object',
                            'name': 'description',
                            'value': None,
                            'prompt': 'description',
                            'display': True},
                        {
                            'section': 'actual_object',
                            'name': 'display_name',
                            'value': 'Reximus',
                            'prompt': 'display_name',
                            'display': True},
                        {
                            'section': 'actual_object',
                            'name': 'id',
                            'value': '0123456789ab0123456789ac',
                            'prompt': 'id',
                            'display': False},
                        {
                            'section': 'actual_object',
                            'name': 'invites',
                            'value': [],
                            'prompt': 'invites',
                            'display': True},
                        {
                            'section': 'actual_object',
                            'name': 'modified',
                            'value': None,
                            'prompt': 'modified',
                            'display': True},
                        {
                            'section': 'actual_object',
                            'name': 'name',
                            'value': 'reximus',
                            'prompt': 'name',
                            'display': True},
                        {
                            'section': 'actual_object',
                            'name': 'owner',
                            'value': 'system|none',
                            'prompt': 'owner',
                            'display': True},
                        {
                            'section': 'actual_object',
                            'name': 'shares',
                            'value': [],
                            'prompt': 'shares',
                            'display': True},
                        {
                            'section': 'actual_object',
                            'name': 'source',
                            'value': None,
                            'prompt': 'source',
                            'display': True},
                        {
                            'section': 'actual_object',
                            'name': 'version',
                            'value': None,
                            'prompt': 'version',
                            'display': True},
                        {
                            'section': 'actual_object',
                            'name': 'mime_type',
                            'value': 'application/x.folder',
                            'prompt': 'mime_type',
                            'display': True},
                        {
                            'name': 'bucket_id',
                            'prompt': 'bucket_id',
                            'value': 'arp-scale-2-cloud-bucket-with-tags11'
                        },
                        {
                            'name': 'key',
                            'prompt': 'key',
                            'value': 'Reximus/'
                        }],
                    'links': [
                        {
                            'prompt': 'Move',
                            'rel': 'mover',
                            'href': 'http://localhost:8080/folders/root/items/0123456789ab0123456789ab/mover'},
                        {
                            'prompt': 'Open',
                            'rel': 'hea-opener-choices',
                            'href': 'http://localhost:8080/folders/root/items/0123456789ab0123456789ab/opener'},
                        {
                            'prompt': 'Duplicate',
                            'rel': 'duplicator',
                            'href': 'http://localhost:8080/folders/root/items/0123456789ab0123456789ab/duplicator'}]}],
                               'template': {'prompt': 'Properties', 'rel': 'properties', 'data': [
                                   {'name': 'id', 'value': '0123456789ab0123456789ab', 'prompt': 'Id', 'required': True,
                                    'readOnly': True, 'pattern': ''},
                                   {'name': 'source', 'value': None, 'prompt': 'Source', 'required': False,
                                    'readOnly': False, 'pattern': ''},
                                   {'name': 'version', 'value': None, 'prompt': 'Version', 'required': False,
                                    'readOnly': False, 'pattern': ''},
                                   {'name': 'display_name', 'value': 'Reximus', 'prompt': 'Name', 'required': True,
                                    'readOnly': False, 'pattern': ''},
                                   {'name': 'description', 'value': None, 'prompt': 'Description', 'required': False,
                                    'readOnly': False, 'pattern': ''},
                                   {'name': 'owner', 'value': 'system|none', 'prompt': 'Owner', 'required': False,
                                    'readOnly': False, 'pattern': ''},
                                   {'name': 'created', 'value': None, 'prompt': 'Created', 'required': False,
                                    'readOnly': True, 'pattern': ''},
                                   {'name': 'modified', 'value': None, 'prompt': 'Modified', 'required': False,
                                    'readOnly': True, 'pattern': ''},
                                   {'name': 'invites', 'value': [], 'prompt': 'Share invites', 'required': False,
                                    'readOnly': True, 'pattern': ''},
                                   {'name': 'shares', 'value': [], 'prompt': 'Shared with', 'required': False,
                                    'readOnly': False, 'pattern': ''},
                                   {'name': 'derived_by', 'value': None, 'prompt': 'Derived by', 'required': False,
                                    'readOnly': True, 'pattern': ''},
                                   {'name': 'derived_from', 'value': [], 'prompt': 'Derived from', 'required': False,
                                    'readOnly': True, 'pattern': ''},
                                   {'name': 'items', 'value': None, 'prompt': 'Items', 'required': False,
                                    'readOnly': True, 'pattern': ''}]}}}]

content = {
    CollectionKey(name='folders', db_manager_cls=MockDockerMongoManager): {
        '666f6f2d6261722d71757579': content_
    }
}

AWSS3FolderTestCase = \
    get_test_case_cls_default(
        href='http://localhost:8080/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3folders/',
        wstl_package=service.__package__,
        coll='awss3folders',
        fixtures=db_values,
        db_manager_cls=MockS3WithMockDockerMongoManager,
        get_all_actions=[
            expectedvalues.Action(
                name='heaserver-awss3folders-folder-get-open-choices',
                url='http://localhost:8080/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/opener',
                rel=['hea-opener-choices']),
            expectedvalues.Action(
                name='heaserver-awss3folders-folder-duplicate',
                url='http://localhost:8080/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/duplicator',
                rel=['hea-duplicator']),
            expectedvalues.Action(
                name='heaserver-awss3folders-folder-get-properties',
                rel=['hea-properties']
            )
        ],
        get_actions=[
            expectedvalues.Action(
                name='heaserver-awss3folders-folder-get-open-choices',
                url='http://localhost:8080/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/opener',
                rel=['hea-opener-choices']),
            expectedvalues.Action(
                name='heaserver-awss3folders-folder-duplicate',
                url='http://localhost:8080/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/duplicator',
                rel=['hea-duplicator']),
            expectedvalues.Action(
                name='heaserver-awss3folders-folder-get-properties',
                rel=['hea-properties']
            )
        ],
        duplicate_action_name='heaserver-awss3folders-folder-duplicate-form',
        exclude=['body_put', 'body_post'])


class AWSS3ItemTestCase(
    get_test_case_cls_default(
        href='http://localhost:8080/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3folders/root/items/',
        wstl_package=service.__package__,
        coll='awss3folders_items',
        fixtures=db_values,
        db_manager_cls=MockS3WithMockDockerMongoManager,
        get_all_actions=[
            expectedvalues.Action(
                name='heaserver-awss3folders-item-get-open-choices',
                url='http://localhost:8080/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{folder_id}/items/{id}/opener',
                rel=['hea-opener-choices']),
            expectedvalues.Action(
                name='heaserver-awss3folders-item-duplicate',
                url='http://localhost:8080/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{folder_id}/items/{id}/duplicator',
                rel=['hea-duplicator']),
            expectedvalues.Action(
                name='heaserver-awss3folders-item-get-properties',
                rel=['hea-properties']
            ),
            expectedvalues.Action(
                name='heaserver-awss3folders-item-move',
                url='http://localhost:8080/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{folder_id}/items/mover',
                rel=['hea-mover']
            )
        ],
        get_actions=[
            expectedvalues.Action(
                name='heaserver-awss3folders-item-get-open-choices',
                url='http://localhost:8080/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{folder_id}/items/{id}/opener',
                rel=['hea-opener-choices']),
            expectedvalues.Action(
                name='heaserver-awss3folders-item-duplicate',
                url='http://localhost:8080/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{folder_id}/items/{id}/duplicator',
                rel=['hea-duplicator']),
            expectedvalues.Action(
                name='heaserver-awss3folders-item-get-properties',
                rel=['hea-properties']
            ),
            expectedvalues.Action(
                name='heaserver-awss3folders-item-move',
                url='http://localhost:8080/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{folder_id}/items/{id}/mover',
                rel=['hea-mover']
            )
        ],
        duplicate_action_name='heaserver-awss3folders-item-duplicate-form',
        exclude=['body_put'])
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self._body_post:
            encoded = b64encode(b'Tritimus/').decode('utf-8')
            original = db_values[get_collection_from_name(db_values, self._coll)][0]
            modified_data = {**original,
                             'display_name': 'Tritimus',
                             'actual_object_id': encoded,
                             'actual_object_uri': '/'.join(original['actual_object_uri'].split('/')[:-1] + [encoded]),
                             'name': encoded,
                             's3_uri': '/'.join(original['s3_uri'].split('/')[:-2] + ['Tritimus', '']),
                             'key': 'Tritimus/'}
            if 'id' in modified_data:
                del modified_data['id']
            self._body_post = expectedvalues._create_template(modified_data)
