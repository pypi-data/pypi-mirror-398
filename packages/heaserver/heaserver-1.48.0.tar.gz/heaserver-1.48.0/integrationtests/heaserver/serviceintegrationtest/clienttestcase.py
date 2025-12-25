from . import service
from heaserver.service.testcase.microservicetestcase import get_test_case_cls_default
from heaserver.service.testcase.expectedvalues import Action, Link
from heaserver.service.testcase.dockermongo import MockDockerMongoManager

from typing import Dict, List, Any
from heaserver.service.testcase import TEST_USER
from heaobject.volume import DEFAULT_FILE_SYSTEM
from heaobject.user import ALL_USERS, NONE_USER
from heaobject.root import Permission
from heaserver.service.testcase.dockermongo import RealRegistryContainerConfig

fixtures: Dict[str, List[Dict[str, Any]]] = {
    service.MONGODB_COMPONENT_COLLECTION: [{
        'id': '666f6f2d6261722d71757578',
        'created': None,
        'derived_by': None,
        'derived_from': ['foo', 'bar'],
        'description': 'Description of Reximus',
        'display_name': 'Reximus',
        'invites': [],
        'modified': None,
        'name': 'reximus',
        'owner': NONE_USER,
        'shares': [{
            'type': 'heaobject.root.ShareImpl',
            'invite': None,
            'user': ALL_USERS,
            'permissions': [Permission.COOWNER.name],
            'type_display_name': 'Share',
            'group': NONE_USER,
            'basis': 'USER'
        }],
        # 'user_shares': [{
        #     'type': 'heaobject.root.ShareImpl',
        #     'invite': None,
        #     'user': ALL_USERS,
        #     'permissions': [Permission.COOWNER.name],
        #     'type_display_name': 'Share',
        #     'group': NONE_USER,
        #     'basis': 'USER'
        # }],
        # 'group_shares': [],
        'source': None,
        'source_detail': None,
        'type': 'heaobject.registry.Component',
        'base_url': 'http://localhost/foo',
        'resources': [{
            'type': 'heaobject.registry.Resource',
            'resource_type_name': 'heaobject.folder.Folder',
            'base_path': 'folders',
            'file_system_name': DEFAULT_FILE_SYSTEM,
            'file_system_type': 'heaobject.volume.MongoDBFileSystem',
            'resource_collection_type_display_name': 'heaobject.folder.Folder'
        }],
        'super_admin_has_all_permissions': True,
        'dynamic_permission_supported': False
    },
        {
            'id': '0123456789ab0123456789ab',
            'created': None,
            'derived_by': None,
            'derived_from': ['oof', 'rab'],
            'description': 'Description of Luximus',
            'display_name': 'Luximus',
            'invites': [],
            'modified': None,
            'name': 'heaserver-registry',
            'owner': TEST_USER,
            'source': None,
            'source_detail': None,
            'type': 'heaobject.registry.Component',
            'base_url': 'http://localhost/foo',
            'resources': [{
                'type': 'heaobject.registry.Resource',
                'resource_type_name': 'heaobject.registry.Component',
                'base_path': 'components',
                'file_system_name': DEFAULT_FILE_SYSTEM,
                'file_system_type': 'heaobject.volume.MongoDBFileSystem',
                'resource_collection_type_display_name': 'heaobject.registry.Component'
            }],
            'shares': [{
                'type': 'heaobject.root.ShareImpl',
                'invite': None,
                'user': ALL_USERS,
                'permissions': [Permission.COOWNER.name],
                'type_display_name': 'Share',
                'group': NONE_USER,
                'basis': 'USER'
            }],
            # 'user_shares': [{
            #     'type': 'heaobject.root.ShareImpl',
            #     'invite': None,
            #     'user': ALL_USERS,
            #     'permissions': [Permission.COOWNER.name],
            #     'type_display_name': 'Share',
            #     'group': NONE_USER,
            #     'basis': 'USER'
            # }],
            # 'group_shares': []
            'super_admin_default_permissions': [Permission.VIEWER.name, Permission.EDITOR.name],
            'dynamic_permission_supported': False
        }
    ]}

content = {
    service.MONGODB_COMPONENT_COLLECTION: {
        '666f6f2d6261722d71757578': b'The quick brown fox jumps over the lazy dog'
    }
}

HEASERVER_REGISTRY_IMAGE = 'registry.gitlab.com/huntsman-cancer-institute/risr/hea/heaserver-registry:1.4.0'

ClientTestCase = get_test_case_cls_default(coll=service.MONGODB_COMPONENT_COLLECTION, fixtures=fixtures,
                                              duplicate_action_name='component-duplicate-form',
                                              db_manager_cls=MockDockerMongoManager, wstl_package=service.__package__,
                                              content=content, content_type='text/plain', put_content_status=204,
                                              href='http://localhost:8080/components/',
                                              get_actions=[Action(name='component-get-properties',
                                                                  rel=['hea-properties']),
                                                           Action(name='component-get-open-choices',
                                                                  url='http://localhost:8080/components/{id}/opener',
                                                                  rel=['hea-opener-choices']),
                                                           Action(name='component-duplicate',
                                                                  url='http://localhost:8080/components/{id}/duplicator',
                                                                  rel=['hea-duplicator'])],
                                              get_all_actions=[Action(name='component-get-properties',
                                                                      rel=['hea-properties']),
                                                               Action(name='component-get-open-choices',
                                                                      url='http://localhost:8080/components/{id}/opener',
                                                                      rel=['hea-opener-choices']),
                                                               Action(name='component-duplicate',
                                                                      url='http://localhost:8080/components/{id}/duplicator',
                                                                      rel=['hea-duplicator'])],
                                              registry_docker_image=RealRegistryContainerConfig(HEASERVER_REGISTRY_IMAGE),
                                              expected_opener=Link(
                                                  url=f'http://localhost:8080/components/{fixtures[service.MONGODB_COMPONENT_COLLECTION][0]["id"]}/content',
                                                  rel=['hea-default', 'hea-opener', 'text/plain']), sub=TEST_USER)
