from heaobject.person import Person
from heaobject.user import NONE_USER, ALL_USERS, CREDENTIALS_MANAGER_USER
from heaobject.root import DesktopObjectDict
from datetime import datetime

person1 = Person()
person2 = Person()
person1_dict: DesktopObjectDict = {
    'id': 'system|none',
    'created': None,  # KeycloakMongoForPyTest sets created to None, overriding what comes back from Keycloak because we can't control it.
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
        'user': ALL_USERS,
        'group': NONE_USER,
        'basis': 'USER'
    }, {
        'invite': None,
        'permissions': ['EDITOR'],
        'type': 'heaobject.root.ShareImpl',
        'user': CREDENTIALS_MANAGER_USER,
        'group': NONE_USER,
        'basis': 'USER'
    }],
    'user_shares': [{
        'invite': None,
        'permissions': ['VIEWER'],
        'type': 'heaobject.root.ShareImpl',
        'user': ALL_USERS,
        'group': NONE_USER,
        'basis': 'USER'
    }, {
        'invite': None,
        'permissions': ['EDITOR'],
        'type': 'heaobject.root.ShareImpl',
        'user': CREDENTIALS_MANAGER_USER,
        'group': NONE_USER,
        'basis': 'USER'
    }],
    'group_shares': [],
    'source': None,
    'first_name': 'Reximus',
    'last_name': 'Max',
    'type': 'heaobject.person.Person',
    'version': None,
    'title': None,
    'phone_number': None,
    'preferred_name': None,
    'id_labs_collaborator': None,
    'id_labs_manage': None,
    'id_labs_member': None,
    'id_projects_collaborator': None,
    'email': None
}
person1.from_dict(person1_dict)

person2_dict: DesktopObjectDict = {
    'id': 'system|test',
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
        'user': ALL_USERS,
        'group': NONE_USER,
        'basis': 'USER'
    }, {
        'invite': None,
        'permissions': ['EDITOR'],
        'type': 'heaobject.root.ShareImpl',
        'user': CREDENTIALS_MANAGER_USER,
        'group': NONE_USER,
        'basis': 'USER'
    }],
    'user_shares': [{
        'invite': None,
        'permissions': ['VIEWER'],
        'type': 'heaobject.root.ShareImpl',
        'user': ALL_USERS,
        'group': NONE_USER,
        'basis': 'USER'
    }, {
        'invite': None,
        'permissions': ['EDITOR'],
        'type': 'heaobject.root.ShareImpl',
        'user': CREDENTIALS_MANAGER_USER,
        'group': NONE_USER,
        'basis': 'USER'
    }],
    'group_shares': [],
    'source': None,
    'first_name': 'Luximus',
    'last_name': 'Max',
    'type': 'heaobject.person.Person',
    'version': None,
    'title': None,
    'phone_number': None,
    'preferred_name': None,
    'id_labs_collaborator': None,
    'id_labs_manage': None,
    'id_labs_member': None,
    'id_projects_collaborator': None,
    'email': None
}
person2.from_dict(person2_dict)
