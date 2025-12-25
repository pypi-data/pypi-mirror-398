"""
Creates a test case class for use with the unittest library that is built into Python.
"""

from heaserver.service.testcase.microservicetestcase import get_test_case_cls_default
from heaserver.person import service
from heaobject.user import NONE_USER, TEST_USER
from heaobject.root import Permission
from heaserver.service.testcase.expectedvalues import Action
from heaserver.person.keycloakmockmongotestcase import KeycloakMockMongoManager

db_store = {
    service.MONGODB_PERSON_COLLECTION: [{
        'id': '666f6f2d6261722d71757578',
        'created': None,
        'derived_by': None,
        'derived_from': [],
        'description': None,
        'display_name': 'Reximus Texamus',
        'invites': [],
        'modified': None,
        'name': 'reximus',
        'owner': NONE_USER,
        'shares': [],
        'source': None,
        'source_detail': None,
        'first_name': 'Reximus',
        'last_name': 'Texamus',
        'type': 'heaobject.person.Person',
        'type_display_name': 'Person',
        'super_admin_default_permissions': [p.name for p in Permission if p is not Permission.CREATOR],
        'dynamic_permission_supported': False
    },
        {
            'id': '0123456789ab0123456789ab',
            'created': None,
            'derived_by': None,
            'derived_from': [],
            'description': None,
            'display_name': 'Luximus Tuxamus',
            'invites': [],
            'modified': None,
            'name': 'luximus',
            'owner': NONE_USER,
            'shares': [{
                'type': 'heaobject.root.ShareImpl',
                'invite': None,
                'user': TEST_USER,
                'permissions': [Permission.VIEWER.name]
            }],
            'source': None,
            'source_detail': None,
            'first_name': 'Luximus',
            'last_name': 'Tuxamus',
            'type': 'heaobject.person.Person',
            'type_display_name': 'Person',
            'super_admin_default_permissions': [p.name for p in Permission if p is not Permission.CREATOR],
            'dynamic_permission_supported': False
        }]}

PermissionsTestCase = \
    get_test_case_cls_default(coll=service.MONGODB_PERSON_COLLECTION,
                              wstl_package=service.__package__,
                              db_manager_cls=KeycloakMockMongoManager,
                              href='http://localhost:8080/people',
                              fixtures=db_store,
                              get_actions=[Action(name='heaserver-people-person-get-properties',
                                                  rel=['hea-properties']),
                                           Action(name='heaserver-people-person-open',
                                                  url='http://localhost:8080/people/{id}/opener',
                                                  rel=['hea-opener']),
                                           Action(name='heaserver-people-person-duplicate',
                                                  url='http://localhost:8080/people/{id}/duplicator',
                                                  rel=['hea-duplicator'])
                                           ],
                              get_all_actions=[Action(name='heaserver-people-person-get-properties',
                                                      rel=['hea-properties']),
                                               Action(name='heaserver-people-person-open',
                                                      url='http://localhost:8080/people/{id}/opener',
                                                      rel=['hea-opener']),
                                               Action(name='heaserver-people-person-duplicate',
                                                      url='http://localhost:8080/people/{id}/duplicator',
                                                      rel=['hea-duplicator'])],
                              duplicate_action_name='heaserver-people-person-duplicate-form',
                              put_content_status=404,
                              sub=TEST_USER,
                              exclude=['body_put', 'body_post', 'expected_one']
)
