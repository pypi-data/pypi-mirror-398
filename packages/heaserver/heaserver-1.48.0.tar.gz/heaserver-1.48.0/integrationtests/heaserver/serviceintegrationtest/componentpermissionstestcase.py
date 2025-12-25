"""
Creates a test case class for use with the unittest library that is built into Python.
"""

from heaserver.service.testcase.dockermongo import MockDockerMongoManager
from heaserver.service.testcase.microservicetestcase import get_test_case_cls_default
from heaserver.service.testcase import expectedvalues, TEST_USER
from . import service
from heaobject.user import NONE_USER
from heaobject.root import Permission, HEAObjectDict
from heaobject.volume import DEFAULT_FILE_SYSTEM
from typing import Dict, List
from datetime import datetime, timezone


fixtures: Dict[str, List[HEAObjectDict]] = {
    service.MONGODB_COMPONENT_COLLECTION: [
        # No permissions
        {
            'id': '666f6f2d6261722d71757578',
            'created': datetime(2022, 6, 13, 19, 49, 21, 534455, tzinfo=timezone.utc),
            'derived_by': None,
            'derived_from': ['foo', 'bar'],
            'description': None,
            'display_name': 'Luximus',
            'invites': [],
            'modified': datetime(2022, 6, 13, 19, 49, 21, 534455, tzinfo=timezone.utc),
            'name': 'luximus',
            'owner': NONE_USER,
            'shares': [],
            'source': None,
            'source_detail': None,
            'type': 'heaobject.registry.Component',
            'base_url': 'http://localhost',
            'resources': [{
                'type': 'heaobject.registry.Resource',
                'resource_type_name': 'heaobject.folder.Folder',
                'base_path': 'folders',
                'file_system_name': DEFAULT_FILE_SYSTEM,
                'file_system_type': 'heaobject.volume.MongoDBFileSystem',
                'resource_collection_type_display_name': 'heaobject.folder.Folder',
                'display_in_system_menu': False,
                'display_in_user_menu': False,
                'collection_mime_type': 'application/x.collection'
            },
            {
                'type': 'heaobject.registry.Resource',
                'resource_type_name': 'heaobject.folder.Item',
                'base_path': 'items',
                'file_system_name': DEFAULT_FILE_SYSTEM,
                'file_system_type': 'heaobject.volume.MongoDBFileSystem',
                'resource_collection_type_display_name': 'heaobject.folder.Item',
                'display_in_system_menu': False,
                'display_in_user_menu': False,
                'collection_mime_type': 'application/x.collection'
            }],
            'super_admin_default_permissions': [Permission.VIEWER.name, Permission.EDITOR.name],
            'dynamic_permission_supported': False
        },
        # Viewer permission only
        {
            'id': '0123456789ab0123456789ab',
            'created': datetime(2022, 6, 13, 19, 49, 21, 534455, tzinfo=timezone.utc),
            'derived_by': None,
            'derived_from': ['foo', 'bar'],
            'description': None,
            'display_name': 'Reximus',
            'invites': [],
            'modified': datetime(2022, 6, 13, 19, 49, 21, 534455, tzinfo=timezone.utc),
            'name': 'reximus',
            'owner': NONE_USER,
            'shares': [{
                'type': 'heaobject.root.ShareImpl',
                'invite': None,
                'user': TEST_USER,
                'permissions': [Permission.VIEWER.name]
            }],
            'user_shares': [{
                'type': 'heaobject.root.ShareImpl',
                'invite': None,
                'user': TEST_USER,
                'permissions': [Permission.VIEWER.name]
            }],
            'group_shares': [],
            'source': None,
            'source_detail': None,
            'type': 'heaobject.registry.Component',
            'base_url': 'http://localhost',
            'resources': [{
                'type': 'heaobject.registry.Resource',
                'resource_type_name': 'heaobject.folder.Folder',
                'base_path': 'folders',
                'file_system_name': DEFAULT_FILE_SYSTEM,
                'file_system_type': 'heaobject.volume.MongoDBFileSystem',
                'resource_collection_type_display_name': 'heaobject.folder.Folder',
                'display_in_system_menu': False,
                'display_in_user_menu': False,
                'collection_mime_type': 'application/x.collection'
            },
                {
                    'type': 'heaobject.registry.Resource',
                    'resource_type_name': 'heaobject.folder.Item',
                    'base_path': 'items',
                    'file_system_name': DEFAULT_FILE_SYSTEM,
                    'file_system_type': 'heaobject.volume.MongoDBFileSystem',
                    'resource_collection_type_display_name': 'heaobject.folder.Item',
                    'display_in_system_menu': False,
                    'display_in_user_menu': False,
                    'collection_mime_type': 'application/x.collection'
                }
            ],
            'super_admin_default_permissions': [Permission.VIEWER.name, Permission.EDITOR.name],
            'dynamic_permission_supported': False
        }
    ]
}

content = {
    service.MONGODB_COMPONENT_COLLECTION: {
        '666f6f2d6261722d71757578': b'The quick brown fox jumps over the lazy dog',
        '0123456789ab0123456789ab': b''
    }
}


ComponentPermissionsTestCase = \
    get_test_case_cls_default(coll=service.MONGODB_COMPONENT_COLLECTION, fixtures=fixtures,
                              duplicate_action_name='component-duplicate-form',
                              db_manager_cls=MockDockerMongoManager,
                              wstl_package=service.__package__, content=content, content_type='text/plain',
                              put_content_status=204,
                              href='http://localhost:8080/components/',
                              get_actions=[expectedvalues.Action(name='component-get-properties',
                                                                 rel=['hea-properties']),
                                           expectedvalues.Action(name='component-get-open-choices',
                                                                 url='http://localhost:8080/components/{id}/opener',
                                                                 rel=['hea-opener-choices']),
                                           expectedvalues.Action(name='component-duplicate',
                                                                 url='http://localhost:8080/components/{id}/duplicator',
                                                                 rel=['hea-duplicator'])],
                              get_all_actions=[
                                  expectedvalues.Action(name='component-get-properties',
                                                        rel=['hea-properties']),
                                  expectedvalues.Action(name='component-get-open-choices',
                                                        url='http://localhost:8080/components/{id}/opener',
                                                        rel=['hea-opener-choices']),
                                  expectedvalues.Action(name='component-duplicate',
                                                        url='http://localhost:8080/components/{id}/duplicator',
                                                        rel=['hea-duplicator'])],
                              expected_opener=expectedvalues.Link(
                                  url=f'http://localhost:8080/components/{fixtures[service.MONGODB_COMPONENT_COLLECTION][0]["id"]}/content',
                                  rel=['hea-default', 'hea-opener', 'text/plain']), sub=TEST_USER)
