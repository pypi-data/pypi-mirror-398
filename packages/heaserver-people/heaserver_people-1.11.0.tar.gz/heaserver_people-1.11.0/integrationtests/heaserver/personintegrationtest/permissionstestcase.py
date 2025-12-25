"""
Creates a test case class for use with the unittest library that is built into Python.
"""

from heaserver.service.testcase.microservicetestcase import get_test_case_cls_default
from heaserver.person import service
from heaobject.user import NONE_USER, TEST_USER, ALL_USERS
from heaobject.registry import Property
from heaobject.person import Person
from heaobject.root import Permission
from heaserver.service.testcase.expectedvalues import Action
from heaserver.person.keycloakmongo import KEYCLOAK_QUERY_ADMIN_SECRET
from heaserver.service.testcase.collection import CollectionKey
from heaserver.service.testcase.dockermongo import RealRegistryContainerConfig, DockerMongoManager
from heaserver.person.keycloakmongotestcase import KeycloakMongoManagerForPyTest


db_store = {
    CollectionKey(name='properties', db_manager_cls=DockerMongoManager): [{
        'id': '666f6f2d6261722d71757578',
        'name': KEYCLOAK_QUERY_ADMIN_SECRET,
        'value': None,
        'owner': NONE_USER,
        'type': Property.get_type_name()
    }],
    CollectionKey(name=service.MONGODB_PERSON_COLLECTION, db_manager_cls=KeycloakMongoManagerForPyTest): [{
        'id': '666f6f2d6261722d71757578',
        'created': None,
        'derived_by': None,
        'derived_from': [],
        'description': None,
        'display_name': 'Reximus Max',
        'invites': [],
        'modified': None,
        'name': 'reximusmax',
        'owner': NONE_USER,
        'shares': [{
            'invite': None,
            'permissions': ['VIEWER'],
            'type': 'heaobject.root.ShareImpl',
            'user': ALL_USERS
        }],
        'source': None,
        'source_detail': None,
        'first_name': 'Reximus',
        'last_name': 'Max',
        'type': Person.get_type_name(),
        'phone_number': None,
        'preferred_name': None,
        'email': None,
        'title': None,
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
            'display_name': 'Luximus Max',
            'invites': [],
            'modified': None,
            'name': 'luximusmax',
            'owner': NONE_USER,
            'shares': [{
                'invite': None,
                'permissions': ['VIEWER'],
                'type': 'heaobject.root.ShareImpl',
                'user': ALL_USERS
            }],
            'source': None,
            'source_detail': None,
            'first_name': 'Luximus',
            'last_name': 'Max',
            'type': Person.get_type_name(),
            'phone_number': None,
            'preferred_name': None,
            'email': None,
            'title': None,
            'type_display_name': 'Person',
            'super_admin_default_permissions': [p.name for p in Permission if p is not Permission.CREATOR],
            'dynamic_permission_supported': False
        }]}

HEASERVER_REGISTRY_IMAGE = 'registry.gitlab.com/huntsman-cancer-institute/risr/hea/heaserver-registry:1.0.0'


PermissionsTestCase = \
    get_test_case_cls_default(coll=service.MONGODB_PERSON_COLLECTION,
                              wstl_package=service.__package__,
                              href='http://localhost:8080/people',
                              fixtures=db_store,
                              db_manager_cls=KeycloakMongoManagerForPyTest,
                              get_actions=[Action(name='heaserver-people-person-get-properties',
                                                  rel=['hea-properties']),
                                           Action(name='heaserver-people-person-get-self',
                                                  url='http://localhost:8080/people/{id}',
                                                  rel=['self'])
                                           ],
                              get_all_actions=[Action(name='heaserver-people-person-get-properties',
                                                      rel=['hea-properties']),
                                               Action(name='heaserver-people-person-get-self',
                                                      url='http://localhost:8080/people/{id}',
                                                      rel=['self'])],
                              duplicate_action_name='heaserver-people-person-duplicate-form',
                              registry_docker_image=RealRegistryContainerConfig(HEASERVER_REGISTRY_IMAGE),
                              put_content_status=404,
                              sub=TEST_USER,
                              exclude=['body_put', 'body_post']
                              )
