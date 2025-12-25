"""
Creates a test case class for use with the unittest library that is built into Python.
"""

from heaserver.service.testcase.microservicetestcase import get_test_case_cls_default
from heaserver.person import service
from heaserver.service.testcase.dockermongo import RealRegistryContainerConfig
from heaserver.person.keycloakmongotestcase import KeycloakMongoManagerForPyTest
from heaobject.user import NONE_USER, ALL_USERS, CREDENTIALS_MANAGER_USER
from heaobject.person import Person, get_system_people
from heaobject.root import Permission
from heaserver.service.testcase.expectedvalues import Action
from heaserver.service.testcase.collection import CollectionKey
from datetime import datetime


db_store = {
    CollectionKey(name=service.MONGODB_PERSON_COLLECTION, db_manager_cls=KeycloakMongoManagerForPyTest): [{
        'id': '666f6f2d6261722d71757578',
        'instance_id': f'{Person.get_type_name()}^666f6f2d6261722d71757578',
        'created': None,  # KeycloakMongoForPyTest sets created to None, overriding what comes back from Keycloak because we can't control it.
        'derived_by': None,
        'derived_from': [],
        'description': None,
        'display_name': 'Reximus Max',
        'invites': [],
        'modified': None,
        'name': 'reximus',
        'owner': NONE_USER,
        'shares': [{
            'invite': None,
            'permissions': ['VIEWER'],
            'type': 'heaobject.root.ShareImpl',
            'user': ALL_USERS,
            'group': NONE_USER,
            'type_display_name': 'Share',
            'basis': 'USER'
        }, {
            'invite': None,
            'permissions': ['EDITOR'],
            'type': 'heaobject.root.ShareImpl',
            'user': CREDENTIALS_MANAGER_USER,
            'group': NONE_USER,
            'type_display_name': 'Share',
            'basis': 'USER'
        }],
        'user_shares': [{
            'invite': None,
            'permissions': ['VIEWER'],
            'type': 'heaobject.root.ShareImpl',
            'user': ALL_USERS,
            'group': NONE_USER,
            'type_display_name': 'Share',
            'basis': 'USER'
        }, {
            'invite': None,
            'permissions': ['EDITOR'],
            'type': 'heaobject.root.ShareImpl',
            'user': CREDENTIALS_MANAGER_USER,
            'group': NONE_USER,
            'type_display_name': 'Share',
            'basis': 'USER'
        }],
        'group_shares': [],
        'source': 'Keycloak',
        'source_detail': None,
        'first_name': 'Reximus',
        'last_name': 'Max',
        'full_name': 'Reximus Max',
        'type': Person.get_type_name(),
        'phone_number': None,
        'preferred_name': None,
        'email': 'reximus.max@example.com',
        'title': None,
        'type_display_name': 'Person',
        'group_ids': [],
        'super_admin_default_permissions': [p.name for p in Permission if p is not Permission.CREATOR],
        'dynamic_permission_supported': False
    },
        {
            'id': '0123456789ab0123456789ab',
            'instance_id': f'{Person.get_type_name()}^0123456789ab0123456789ab',
            'created': None,
            'derived_by': None,
            'derived_from': [],
            'description': None,
            'display_name': 'Luximus Max',
            'invites': [],
            'modified': None,
            'name': 'luximus',
            'owner': NONE_USER,
            'shares': [{
                'invite': None,
                'permissions': ['VIEWER'],
                'type': 'heaobject.root.ShareImpl',
                'user': ALL_USERS,
                'group': NONE_USER,
                'type_display_name': 'Share',
                'basis': 'USER'
            }, {
                'invite': None,
                'permissions': ['EDITOR'],
                'type': 'heaobject.root.ShareImpl',
                'user': CREDENTIALS_MANAGER_USER,
                'group': NONE_USER,
                'type_display_name': 'Share',
                'basis': 'USER'
            }],
            'user_shares': [{
                'invite': None,
                'permissions': ['VIEWER'],
                'type': 'heaobject.root.ShareImpl',
                'user': ALL_USERS,
                'group': NONE_USER,
                'type_display_name': 'Share',
                'basis': 'USER'
            }, {
                'invite': None,
                'permissions': ['EDITOR'],
                'type': 'heaobject.root.ShareImpl',
                'user': CREDENTIALS_MANAGER_USER,
                'group': NONE_USER,
                'type_display_name': 'Share',
                'basis': 'USER'
            }],
            'group_shares': [],
            'source': 'Keycloak',
            'source_detail': None,
            'first_name': 'Luximus',
            'last_name': 'Max',
            'full_name': 'Luximus Max',
            'type': Person.get_type_name(),
            'phone_number': None,
            'preferred_name': None,
            'email': 'luximus.max@example.com',
            'title': None,
            'type_display_name': 'Person',
            'group_ids': [],
            'super_admin_default_permissions': [p.name for p in Permission if p is not Permission.CREATOR],
            'dynamic_permission_supported': False
        }] + [system_person.to_dict() for system_person in get_system_people()]}

HEASERVER_REGISTRY_IMAGE = 'registry.gitlab.com/huntsman-cancer-institute/risr/hea/heaserver-registry:1.0.0'


TestCase = get_test_case_cls_default(coll=service.MONGODB_PERSON_COLLECTION,
                                     href='http://localhost:8080/people/',
                                     wstl_package=service.__package__,
                                     db_manager_cls=KeycloakMongoManagerForPyTest,
                                     fixtures=db_store,
                                     get_actions=[Action(name='heaserver-people-person-get-properties',
                                                         rel=['hea-properties']),
                                                  Action(name='heaserver-people-person-get-self',
                                                         url='http://localhost:8080/people/{id}',
                                                         rel=['self']),
                                                #   Action(name='heaserver-people-person-get-settings',
                                                #          url='http://localhost:8080/collections/heaobject.settings.SettingsObject',
                                                #          rel=['hea-system-menu-item', 'hea-user-menu-item', 'application/x.settingsobject', 'application/x.collection']),
                                                  # Action(name='heaserver-people-person-get-organization-collection',
                                                  #        url='http://localhost:8080/collections/heaobject.organization.Organization',
                                                  #        rel=['hea-system-menu-item', 'application/x.collection']),
                                                #   Action(name='heaserver-people-person-get-volumes-collection',
                                                #          url='http://localhost:8080/collections/heaobject.volume.Volume',
                                                #          rel=['hea-system-menu-item', 'application/x.collection']),
                                                  Action(name='heaserver-people-person-get-organizations',
                                                         url='http://localhost:8080/organizations/',
                                                         rel=['application/x.organization']),
                                                  Action(name='heaserver-people-person-get-volumes',
                                                         url='http://localhost:8080/volumes/',
                                                         rel=['application/x.volume']),
                                                  Action(name='heaserver-people-person-get-desktop-object-actions',
                                                         url='http://localhost:8080/desktopobjectactions/',
                                                         rel=['application/x.desktopobjectaction']),
                                                #   Action(name='heaserver-people-person-get-credential-collection',
                                                #          url='http://localhost:8080/collections/heaobject.keychain.CredentialsView',
                                                #          rel=['hea-system-menu-item', 'application/x.collection'])
                                                  ],
                                     get_all_actions=[Action(name='heaserver-people-person-get-properties',
                                                             rel=['hea-properties']),
                                                      Action(name='heaserver-people-person-get-self',
                                                             url='http://localhost:8080/people/{id}',
                                                             rel=['self']),
                                                    #   Action(name='heaserver-people-person-get-settings',
                                                    #          url='http://localhost:8080/collections/heaobject.settings.SettingsObject',
                                                    #          rel=['hea-system-menu-item', 'hea-user-menu-item', 'application/x.settingsobject', 'application/x.collection']),
                                                      # Action(name='heaserver-people-person-get-organization-collection',
                                                      #        url='http://localhost:8080/collections/heaobject.organization.Organization',
                                                      #        rel=['hea-system-menu-item', 'application/x.collection']),
                                                    #   Action(name='heaserver-people-person-get-volumes-collection',
                                                    #      url='http://localhost:8080/collections/heaobject.volume.Volume',
                                                    #      rel=['hea-system-menu-item', 'application/x.collection']),
                                                      Action(name='heaserver-people-person-get-organizations',
                                                             url='http://localhost:8080/organizations/',
                                                             rel=['application/x.organization']),
                                                      Action(name='heaserver-people-person-get-volumes',
                                                             url='http://localhost:8080/volumes/',
                                                             rel=['application/x.volume']),
                                                      Action(name='heaserver-people-person-get-desktop-object-actions',
                                                             url='http://localhost:8080/desktopobjectactions/',
                                                             rel=['application/x.desktopobjectaction']),
                                                    #   Action(name='heaserver-people-person-get-credential-collection',
                                                    #          url='http://localhost:8080/collections/heaobject.keychain.CredentialsView',
                                                    #          rel=['hea-system-menu-item', 'application/x.collection'])
                                                      ],
                                     registry_docker_image=RealRegistryContainerConfig(HEASERVER_REGISTRY_IMAGE),
                                     duplicate_action_name='heaserver-people-person-duplicate-form',
                                     exclude=['body_put', 'body_post'])
