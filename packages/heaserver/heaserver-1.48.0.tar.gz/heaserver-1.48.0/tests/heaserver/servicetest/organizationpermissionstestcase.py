"""
Creates a test case class for use with the unittest library that is built into Python.
"""
from heaobject.root import Permission

from . import service
from heaserver.service.testcase.microservicetestcase import get_test_case_cls_default
from heaobject.user import NONE_USER, TEST_USER, ALL_USERS
from heaserver.service.testcase.expectedvalues import Action, Link
from datetime import datetime

db_store = {
    service.MONGODB_ORGANIZATION_COLLECTION: [
        {
            "id": "666f6f2d6261722d71757578",
            "source": None,
            "source_detail": None,
            "name": "Bob",
            "display_name": "Bob",
            "description": "Description of Bob",
            "owner": NONE_USER,
            "created": datetime(2021, 12, 2, 17, 31, 15, 630000),
            "modified": datetime(2021, 12, 2, 17, 31, 15, 630000),
            "invites": [],
            "shares": [],
            "user_shares": [],
            "group_shares": [],
            "derived_by": None,
            "derived_from": [],
            "account_ids": [],
            "principal_investigator_id": "23423DAFSDF12adfasdf3",
            "manager_ids": [],
            "member_ids": [],
            'type': 'heaobject.organization.Organization',
            'admin_ids': [],
            'admin_group_ids': [],
            'manager_group_ids': [],
            'member_group_ids': [],
            'super_admin_default_permissions': [p.name for p in Permission],
            'dynamic_permission_supported': True
        },
        {
            "id": "0123456789ab0123456789ab",
            "source": None,
            "source_detail": None,
            "name": "Reximus",
            "display_name": "Reximus",
            "description": "Description of Reximus",
            "owner": NONE_USER,
            "created": datetime(2021, 12, 2, 17, 31, 15, 630000),
            "modified": datetime(2021, 12, 2, 17, 31, 15, 630000),
            "invites": [],
            "shares": [
                {
                    'type': 'heaobject.root.ShareImpl',
                    'invite': None,
                    'user': TEST_USER,
                    'permissions': [Permission.VIEWER.name]
                }
            ],
            "user_shares": [
                {
                    'type': 'heaobject.root.ShareImpl',
                    'invite': None,
                    'user': TEST_USER,
                    'permissions': [Permission.VIEWER.name]
                }
            ],
            "group_shares": [],
            "derived_by": None,
            "derived_from": [],
            "account_ids": [],
            "principal_investigator_id": "11234867890b0123a56789ab",
            "manager_ids": [],
            "member_ids": [],
            'type': 'heaobject.organization.Organization',
            'admin_ids': [],
            'admin_group_ids': [],
            'manager_group_ids': [],
            'member_group_ids': [],
            'super_admin_default_permissions': [p.name for p in Permission],
            'dynamic_permission_supported': True
        }
    ]}

content = {
    service.MONGODB_ORGANIZATION_COLLECTION: {
        '666f6f2d6261722d71757578': b'The quick brown fox jumps over the lazy dog',
        '0123456789ab0123456789ab': b''
    }
}

OrganizationPermissionsTestCase = \
    get_test_case_cls_default(coll=service.MONGODB_ORGANIZATION_COLLECTION,
                              wstl_package=service.__package__,
                              href='http://localhost:8080/organizations',
                              fixtures=db_store,
                              content=content,
                              get_actions=[Action(
                                  name='heaserver-organizations-organization-get-properties',
                                  rel=['properties']),
                                  Action(
                                      name='heaserver-organizations-organization-get-open-choices',
                                      url='/organizations/{id}/opener',
                                      rel=['hea-opener-choices']),
                                  Action(
                                      name='heaserver-organizations-organization-duplicate',
                                      url='/organizations/{id}/duplicator',
                                      rel=['duplicator'])
                              ],
                              get_all_actions=[Action(
                                  name='heaserver-organizations-organization-get-properties',
                                  rel=['properties']),
                                  Action(
                                      name='heaserver-organizations-organization-get-open-choices',
                                      url='/organizations/{id}/opener',
                                      rel=['hea-opener-choices']),
                                  Action(
                                      name='heaserver-organizations-organization-duplicate',
                                      url='/organizations/{id}/duplicator',
                                      rel=['duplicator'])],
                              expected_opener=Link(
                                  url=f'http://localhost:8080/organizations/{db_store[service.MONGODB_ORGANIZATION_COLLECTION][0]["id"]}/content',
                                  rel=['hea-default', 'hea-opener', 'text/plain']),
                              duplicate_action_name='heaserver-organizations-organization-duplicate-form',
                              put_content_status=204, sub=TEST_USER)
