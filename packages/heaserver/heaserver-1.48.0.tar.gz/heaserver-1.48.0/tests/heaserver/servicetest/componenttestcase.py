"""
Creates a test case class for use with the unittest library that is build into Python.
"""
from heaserver.service.db.database import CollectionKey
import heaserver.service.testcase.mockmongo
from heaserver.service.db.database import query_fixture_collection
from heaserver.service.testcase.microservicetestcase import get_test_case_cls_default
from heaserver.service.testcase import expectedvalues, TEST_USER
from heaserver.service.testcase.mockmongo import MockMongoManager
from . import service
from heaobject.user import NONE_USER, ALL_USERS
from heaobject.group import NONE_GROUP
from heaobject.root import Permission, HEAObjectDict
from heaobject.volume import DEFAULT_FILE_SYSTEM
from typing import Dict, List
from datetime import datetime, timezone

##
## The first set of desktop objects is for testing the following:
##
## 1) Running as the TEST_USER user, with shares that grant the test user access.
## 2) The heaserver.service.testcase.collection.CollectionKey class.
##

fixtures1: dict[str | CollectionKey, list[HEAObjectDict]] = {
    CollectionKey(name=service.MONGODB_COMPONENT_COLLECTION): [{
        'id': '666f6f2d6261722d71757578',
        'instance_id': 'heaobject.registry.Component^666f6f2d6261722d71757578',
        'created': datetime(2022, 5, 17, 0, 0, 0, 0, tzinfo=timezone.utc),
        'derived_by': None,
        'derived_from': ['foo', 'bar'],
        'description': None,
        'display_name': 'Reximus',
        'invites': [],
        'modified': datetime(2022, 5, 17, 0, 0, 0, 0, tzinfo=timezone.utc),
        'name': 'reximus',
        'owner': TEST_USER,
        'shares': [{
            'type': 'heaobject.root.ShareImpl',
            'invite': None,
            'user': ALL_USERS,
            'permissions': [Permission.COOWNER.name],
            'type_display_name': 'Share',
            'group': NONE_GROUP,
            'basis': 'USER'
        }],
        'user_shares': [{
            'type': 'heaobject.root.ShareImpl',
            'invite': None,
            'user': ALL_USERS,
            'permissions': [Permission.COOWNER.name],
            'type_display_name': 'Share',
            'group': NONE_GROUP,
            'basis': 'USER'
        }],
        'group_shares': [],
        'source': None,
        'source_detail': None,
        'type': 'heaobject.registry.Component',
        'base_url': 'http://localhost',
        'external_base_url': None,
        'type_display_name': 'Registry Component',
        'resources': [{
            'type': 'heaobject.registry.Resource',
            'resource_type_name': 'heaobject.folder.Folder',
            'base_path': 'folders',
            'file_system_name': DEFAULT_FILE_SYSTEM,
            'file_system_type': 'heaobject.volume.MongoDBFileSystem',
            'resource_collection_type_display_name': 'heaobject.folder.Folder',
            'collection_accessor_users': [],
            'collection_accessor_groups': [],
            'creator_users': [],
            'creator_groups': [],
            'default_shares': [],
            'type_display_name': 'Resource',
            'manages_creators': False,
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
                'collection_accessor_users': [],
                'collection_accessor_groups': [],
                'creator_users': [],
                'creator_groups': [],
                'default_shares': [],
                'type_display_name': 'Resource',
                'manages_creators': False,
                'display_in_system_menu': False,
                'display_in_user_menu': False,
                'collection_mime_type': 'application/x.collection'
            }
        ],
        'super_admin_default_permissions': [Permission.VIEWER.name, Permission.EDITOR.name],
        'dynamic_permission_supported': False
    },
        {
            'id': '0123456789ab0123456789ab',
            'instance_id': 'heaobject.registry.Component^0123456789ab0123456789ab',
            'created': datetime(2022, 5, 17, 0, 0, 0, 0, tzinfo=timezone.utc),
            'derived_by': None,
            'derived_from': ['oof', 'rab'],
            'description': None,
            'display_name': 'Luximus',
            'invites': [],
            'modified': datetime(2022, 5, 17, 0, 0, 0, 0, tzinfo=timezone.utc),
            'name': 'luximus',
            'owner': NONE_USER,
            'shares': [{
                'type': 'heaobject.root.ShareImpl',
                'invite': None,
                'user': ALL_USERS,
                'permissions': [Permission.COOWNER.name],
                'type_display_name': 'Share',
                'group': NONE_GROUP,
                'basis': 'USER'
            }],
            'user_shares': [{
                'type': 'heaobject.root.ShareImpl',
                'invite': None,
                'user': ALL_USERS,
                'permissions': [Permission.COOWNER.name],
                'type_display_name': 'Share',
                'group': NONE_GROUP,
                'basis': 'USER'
            }],
            'group_shares': [],
            'source': None,
            'source_detail': None,
            'type': 'heaobject.registry.Component',
            'base_url': 'http://localhost/foo',
            'external_base_url': None,
            'type_display_name': 'Registry Component',
            'resources': [{
                'type': 'heaobject.registry.Resource',
                'resource_type_name': 'heaobject.folder.Folder',
                'base_path': 'folders',
                'file_system_name': DEFAULT_FILE_SYSTEM,
                'file_system_type': 'heaobject.volume.MongoDBFileSystem',
                'resource_collection_type_display_name': 'heaobject.folder.Folder',
                'collection_accessor_users': [],
                'collection_accessor_groups': [],
                'creator_users': [],
                'creator_groups': [],
                'default_shares': [],
                'type_display_name': 'Resource',
                'manages_creators': False,
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
                    'collection_accessor_users': [],
                    'collection_accessor_groups': [],
                    'creator_users': [],
                    'creator_groups': [],
                    'default_shares': [],
                    'type_display_name': 'Resource',
                    'manages_creators': False,
                    'display_in_system_menu': False,
                    'display_in_user_menu': False,
                    'collection_mime_type': 'application/x.collection'
                }],
            'super_admin_default_permissions': [Permission.VIEWER.name, Permission.EDITOR.name],
            'dynamic_permission_supported': False
        }
    ]}

content1 = {
    CollectionKey(name=service.MONGODB_COMPONENT_COLLECTION): {
        '666f6f2d6261722d71757578': b'The quick brown fox jumps over the lazy dog'
    }
}


def _test_case_generator(coll, fixtures, duplicate_action_name, content=None, sub=NONE_USER):
    return get_test_case_cls_default(coll=coll, fixtures=fixtures, duplicate_action_name=duplicate_action_name,
                                     db_manager_cls=heaserver.service.testcase.mockmongo.MockMongoManager,
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
                                         url=f'http://localhost:8080/components/{query_fixture_collection(fixtures, key=service.MONGODB_COMPONENT_COLLECTION, default_db_manager=MockMongoManager)[0]["id"]}/content',
                                         rel=['hea-default', 'hea-opener', 'text/plain']), sub=sub)


ComponentTestCase = _test_case_generator(coll=service.MONGODB_COMPONENT_COLLECTION, fixtures=fixtures1, content=content1,
                                         duplicate_action_name='component-duplicate-form', sub=TEST_USER)


##
## The second set of desktop objects is for testing the following:
##
## 1) Running as the default (NONE_USER) user, with objects that are owned by NONE_USER.
##

fixtures2: Dict[str, List[HEAObjectDict]] = {
    service.MONGODB_COMPONENT_COLLECTION: [{
        'id': '666f6f2d6261722d71757578',
        'instance_id': 'heaobject.registry.Component^666f6f2d6261722d71757578',
        'created': datetime(2021, 12, 2, 17, 31, 15, 630000, tzinfo=timezone.utc),
        'derived_by': None,
        'derived_from': ['foo', 'bar'],
        'description': None,
        'display_name': 'Reximus',
        'invites': [],
        'modified': datetime(2021, 12, 2, 17, 31, 15, 630000, tzinfo=timezone.utc),
        'name': 'reximus',
        'owner': NONE_USER,
        'shares': [],
        'user_shares': [],
        'group_shares': [],
        'source': None,
        'source_detail': None,
        'type': 'heaobject.registry.Component',
        'base_url': 'http://localhost',
        'external_base_url': None,
        'type_display_name': 'Registry Component',
        'resources': [{
            'type': 'heaobject.registry.Resource',
            'resource_type_name': 'heaobject.folder.Folder',
            'base_path': 'folders',
            'file_system_name': DEFAULT_FILE_SYSTEM,
            'file_system_type': 'heaobject.volume.MongoDBFileSystem',
            'resource_collection_type_display_name': 'heaobject.folder.Folder',
            'collection_accessor_users': [],
            'collection_accessor_groups': [],
            'creator_users': [],
            'creator_groups': [],
            'default_shares': [],
            'type_display_name': 'Resource',
            'manages_creators': False,
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
                'collection_accessor_users': [],
                'collection_accessor_groups': [],
                'creator_users': [],
                'creator_groups': [],
                'default_shares': [],
                'type_display_name': 'Resource',
                'manages_creators': False,
                'display_in_system_menu': False,
                'display_in_user_menu': False,
                'collection_mime_type': 'application/x.collection'
            }
        ],
        'super_admin_default_permissions': [Permission.VIEWER.name, Permission.EDITOR.name],
        'dynamic_permission_supported': False
    },
        {
            'id': '0123456789ab0123456789ab',
            'instance_id': 'heaobject.registry.Component^0123456789ab0123456789ab',
            'created': datetime(2021, 12, 2, 17, 31, 15, 630000, tzinfo=timezone.utc),
            'derived_by': None,
            'derived_from': ['oof', 'rab'],
            'description': None,
            'display_name': 'Luximus',
            'invites': [],
            'modified': datetime(2021, 12, 2, 17, 31, 15, 630000, tzinfo=timezone.utc),
            'name': 'luximus',
            'owner': NONE_USER,
            'shares': [],
            'user_shares': [],
            'group_shares': [],
            'source': None,
            'source_detail': None,
            'type': 'heaobject.registry.Component',
            'base_url': 'http://localhost/foo',
            'external_base_url': None,
            'type_display_name': 'Registry Component',
            'resources': [{
                'type': 'heaobject.registry.Resource',
                'resource_type_name': 'heaobject.folder.Folder',
                'base_path': 'folders',
                'file_system_name': DEFAULT_FILE_SYSTEM,
                'file_system_type': 'heaobject.volume.MongoDBFileSystem',
                'resource_collection_type_display_name': 'heaobject.folder.Folder',
                'collection_accessor_users': [],
                'collection_accessor_groups': [],
                'creator_users': [],
                'creator_groups': [],
                'default_shares': [],
                'type_display_name': 'Resource',
                'manages_creators': False,
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
                    'collection_accessor_users': [],
                    'collection_accessor_groups': [],
                    'creator_users': [],
                    'creator_groups': [],
                    'default_shares': [],
                    'type_display_name': 'Resource',
                    'manages_creators': False,
                    'display_in_system_menu': False,
                    'display_in_user_menu': False,
                    'collection_mime_type': 'application/x.collection'
                }],
            'super_admin_default_permissions': [Permission.VIEWER.name, Permission.EDITOR.name],
            'dynamic_permission_supported': False
        }
    ]}

content2 = {
    service.MONGODB_COMPONENT_COLLECTION: {
        '666f6f2d6261722d71757578': b'The quick brown fox jumps over the lazy dog'
    }
}

ComponentTestCase2 = _test_case_generator(coll=service.MONGODB_COMPONENT_COLLECTION, fixtures=fixtures2,
                                          duplicate_action_name='component-duplicate-form', content=content2)

##
## The third set of desktop objects is for testing the following:
##
## 1) Proper handling of an omitted list property (shares, in this case).
##

fixtures3: Dict[str, List[HEAObjectDict]] = {
    service.MONGODB_COMPONENT_COLLECTION: [{
        'id': '666f6f2d6261722d71757578',
        'instance_id': 'heaobject.registry.Component^666f6f2d6261722d71757578',
        'created': datetime(2021, 12, 2, 17, 31, 15, 630000, tzinfo=timezone.utc),
        'derived_by': None,
        'derived_from': ['foo', 'bar'],
        'description': None,
        'display_name': 'Reximus',
        'invites': [],
        'modified': datetime(2021, 12, 2, 17, 31, 15, 630000, tzinfo=timezone.utc),
        'name': 'reximus',
        'owner': NONE_USER,
        'source': None,
        'source_detail': None,
        'shares': [],
        'user_shares': [],
        'group_shares': [],
        'type': 'heaobject.registry.Component',
        'base_url': 'http://localhost',
        'external_base_url': None,
        'type_display_name': 'Registry Component',
        'resources': [{
            'type': 'heaobject.registry.Resource',
            'resource_type_name': 'heaobject.folder.Folder',
            'base_path': 'folders',
            'file_system_name': DEFAULT_FILE_SYSTEM,
            'file_system_type': 'heaobject.volume.MongoDBFileSystem',
            'resource_collection_type_display_name': 'heaobject.folder.Folder',
            'collection_accessor_users': [],
            'collection_accessor_groups': [],
            'creator_users': [],
            'creator_groups': [],
            'default_shares': [],
            'type_display_name': 'Resource',
            'manages_creators': False,
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
                'collection_accessor_users': [],
                'collection_accessor_groups': [],
                'creator_users': [],
                'creator_groups': [],
                'default_shares': [],
                'type_display_name': 'Resource',
                'manages_creators': False,
                'display_in_system_menu': False,
                'display_in_user_menu': False,
                'collection_mime_type': 'application/x.collection'
            }
        ],
        'super_admin_default_permissions': [Permission.VIEWER.name, Permission.EDITOR.name],
        'dynamic_permission_supported': False
    },
        {
            'id': '0123456789ab0123456789ab',
            'instance_id': 'heaobject.registry.Component^0123456789ab0123456789ab',
            'created': datetime(2021, 12, 2, 17, 31, 15, 630000, tzinfo=timezone.utc),
            'derived_by': None,
            'derived_from': ['oof', 'rab'],
            'description': None,
            'display_name': 'Luximus',
            'invites': [],
            'modified': datetime(2021, 12, 2, 17, 31, 15, 630000, tzinfo=timezone.utc),
            'name': 'luximus',
            'owner': NONE_USER,
            'shares': [],
            'user_shares': [],
            'group_shares': [],
            'source': None,
            'source_detail': None,
            'type': 'heaobject.registry.Component',
            'base_url': 'http://localhost/foo',
            'external_base_url': None,
            'type_display_name': 'Registry Component',
            'resources': [{
                'type': 'heaobject.registry.Resource',
                'resource_type_name': 'heaobject.folder.Folder',
                'base_path': 'folders',
                'file_system_name': DEFAULT_FILE_SYSTEM,
                'file_system_type': 'heaobject.volume.MongoDBFileSystem',
                'resource_collection_type_display_name': 'heaobject.folder.Folder',
                'collection_accessor_users': [],
                'collection_accessor_groups': [],
                'creator_users': [],
                'creator_groups': [],
                'default_shares': [],
                'type_display_name': 'Resource',
                'manages_creators': False,
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
                    'collection_accessor_users': [],
                    'collection_accessor_groups': [],
                    'creator_users': [],
                    'creator_groups': [],
                    'default_shares': [],
                    'type_display_name': 'Resource',
                    'manages_creators': False,
                    'display_in_system_menu': False,
                    'display_in_user_menu': False,
                    'collection_mime_type': 'application/x.collection'
                }],
            'super_admin_default_permissions': [Permission.VIEWER.name, Permission.EDITOR.name],
            'dynamic_permission_supported': False
        }
    ]}

content3 = {
    service.MONGODB_COMPONENT_COLLECTION: {
        '666f6f2d6261722d71757578': b'The quick brown fox jumps over the lazy dog'
    }
}

ComponentTestCase3 = _test_case_generator(coll=service.MONGODB_COMPONENT_COLLECTION, fixtures=fixtures3,
                                          duplicate_action_name='component-duplicate-form', content=content3)
