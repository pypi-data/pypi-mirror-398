from typing import Any
from heaserver.service.db.mongo import MongoManager, Mongo
from heaserver.service import appproperty, response
from heaserver.service.client import get_property
from heaserver.service.oidcclaimhdrs import SUB
from heaserver.service.util import queued_processing
from heaserver.service.heaobjectsupport import HEAServerPermissionContext
from heaserver.service.config import Configuration
from heaserver.service.crypt import SecretDecryption
from heaobject.person import Person, Role, get_system_person, get_system_people, Group, GroupType, AccessToken, \
    decode_role, encode_role
from heaobject.user import NONE_USER, ALL_USERS, is_system_user, CREDENTIALS_MANAGER_USER
from heaobject.root import Share, ShareImpl, Permission
from heaobject.util import parse_bool, system_timezone
from aiohttp import ClientResponseError
from aiohttp.web import Request, Application
from aiohttp import hdrs
from yarl import URL
import logging
from pathlib import Path
from datetime import datetime, timedelta
from enum import Enum
from functools import partial
from asyncio import gather
from cachetools import TTLCache
from copy import deepcopy
from collections.abc import Sequence, Mapping, AsyncIterator
from collections import deque
from asyncio import Lock
import urllib


KEYCLOAK_QUERY_ADMIN_SECRET = 'KEYCLOAK_QUERY_ADMIN_SECRET'
DEFAULT_CLIENT_ID = 'hea'
DEFAULT_ADMIN_CLIENT_ID = 'admin-cli'
DEFAULT_REALM = 'hea'
DEFAULT_HOST = 'https://localhost:8444'
DEFAULT_SECRET_FILE = '.secret'
DEFAULT_VERIFY_SSL = True

CONFIG_SECTION = 'Keycloak'
KEYCLOAK_TEST_IMAGE = 'quay.io/keycloak/keycloak:15.0.2'

_ACCESS_TOKEN_LOCK = Lock()


class KeycloakCompatibility(Enum):
    """Keycloak compatibility levels:
        FIFTEEN: APIs prior to version 19. We have only tested with 15.
        NINETEEN: APIs for version 19 and later.
    """
    FIFTEEN = "15"
    NINETEEN = "19"

DEFAULT_KEYCLOAK_COMPATIBILITY = KeycloakCompatibility.FIFTEEN


class PeopleServicePermissionContext(HEAServerPermissionContext):
    """
    A permission context for the HEA server. It is used to check permissions for the HEA server. It overrides methods
    of HEAServerPermissionContext that query the people service via its REST APIs. It instead queries the Keycloak
    server directly.
    """

    def __init__(self, request: Request, keycloak_mongo: 'KeycloakMongo'):
        """
        Initializes the permission context.

        :param keycloak_mongo: the KeycloakMongo object.
        """
        sub = request.headers.get(SUB, NONE_USER)
        super().__init__(sub, request)
        self.__keycloak_mongo = keycloak_mongo
        self.__group_ids: list[str] | None = None

    async def get_permissions(self, obj) -> list[Permission]:
        """
        Gets the permissions for the given object. A user never gets the DELETER permission for their own Person
        object.

        :param obj: the object to get permissions for.
        :return: a list of Permission objects.
        """
        candidate_perms = await super().get_permissions(obj)
        if isinstance(obj, Person) and self.sub == obj.id:
            return list(p for p in candidate_perms if p not in (Permission.DELETER, Permission.COOWNER))
        else:
            return candidate_perms

    async def get_groups(self) -> list[str]:
        if self.__group_ids is None:
            groups = await self.__keycloak_mongo.get_user_groups(self.request, self.sub)
            assert all(group.id is not None for group in groups), f'One or more groups in {groups} has no id'
            self.__group_ids = [group.id for group in groups if group.id is not None]
        return self.__group_ids

    async def group_id_from(self, group: str) -> str:
        group_ = await self.__keycloak_mongo.get_group_by_group(self.request, group)
        if not group_:
            raise ValueError(f'Group {group} not found')
        assert group_.id is not None, f'Group {group} has no id'
        return group_.id


class KeycloakMongo(Mongo):
    """
    Database object for accessing a keycloak server. It subclasses Mongo so that some user data that Keycloak does not
    support might be stored in Mongo.
    """

    _all_groups_lock = Lock()

    def __init__(self, config: Configuration | None = None,
                 client_id: str | None = DEFAULT_CLIENT_ID,
                 admin_client_id: str | None = DEFAULT_ADMIN_CLIENT_ID,
                 realm: str | None = DEFAULT_REALM,
                 host: str | None = DEFAULT_HOST,
                 alt_host: str | None = None,
                 secret: str | None = None,
                 secret_file: str | None = DEFAULT_SECRET_FILE,
                 verify_ssl: bool = DEFAULT_VERIFY_SSL,
                 keycloak_compatibility: KeycloakCompatibility | None = KeycloakCompatibility.FIFTEEN,
                 request: Request | None = None):
        """
        Initializes Keycloak access with a configparser object or manually set configuration parameters. For all
        manually set configuration parameters, the empty string is treated the same as None.

        :param config: a Configuration object, which should have a Keycloak section with the following properties:

            Realm = the Keycloak realm.
            VerifySSL = whether to verify SSL certificates (defaults to yes).
            Host = the host part of the base URL string to use in constructing URLs to query Keycloak's REST APIs
            (defaults to https://localhost:8444).
            AltHost = the alternate host for getting the alt access token. Defaults to the value of host if
            unspecified.
            Secret = the secret for accessing keycloak.
            SecretFile = alternatively, a file with one line containing the secret.
            Compatibility = 15 or 19 denoting Keycloak 15-18 versus >= 19. The default is 15.
            ClientId = the client id to use. The default is hea.
            AdminClientId = the admin client id to use. The default is admin-cli.

        :param client_id: the client id to use. The default is hea.
        :param admin_client_id: the admin client id to use. The default is admin-cli.
        :param realm: the realm to use if there is no config file or the config file does not specify one. The default
        is hea.
        :param host: the host part of the base URL string to use in constructing URLs to query Keycloak's REST APIs. If
        a configparser.ConfigParser object is provided and has a Host value, this parameter is ignored. The default is
        https://localhost:8444.
        :param alt_host: the alternate hostname for getting the alt access token. If a configparser.ConfigParser object
        is provided and has an AltHost value, this parameter is ignored. Defaults to the value of host if unspecified
        in the config or this parameter.
        :param secret: the secret to use if there is no config file or the config file does not specify one.
        :param secret_file: the path of a file with one line containing the secret if there is no config file or the
        config file does not specify one. There must be either a secret or a secret file.
        :param verify_ssl: whether to verify Keycloak's SSL certificate. The default value is True.
        :param keycloak_compatibility: the compatibility level if there is no config file or the config file does not
        specify one. Defaults to FIFTEEN.
        """
        super().__init__(config, request=request)
        self.__ttl_cache: TTLCache[tuple, Any] = TTLCache(maxsize=128, ttl=30)
        self.__config = config
        if config and CONFIG_SECTION in config.parsed_config:
            _section = config.parsed_config[CONFIG_SECTION]
            _realm = _section.get('Realm', realm)
            self.__realm = str(_realm) if _realm is not None else DEFAULT_REALM
            self.__verify_ssl = _section.getboolean('VerifySSL',
                                                    verify_ssl if verify_ssl is not None else DEFAULT_VERIFY_SSL)
            self.__host = str(_section.get('Host', host) or DEFAULT_HOST)
            self.__alt_host = str(_section.get('AltHost', alt_host) or self.__host)
            _secret = _section.get('Secret', secret)
            self.__secret = _secret if _secret else None
            _secret_file = _section.get('SecretFile', secret_file)
            self.__secret_file = _secret_file if _secret_file else None
            compat = _section.get('Compatibility',
                                  None) or keycloak_compatibility or DEFAULT_KEYCLOAK_COMPATIBILITY.value
            self.__keycloak_compatibility = KeycloakCompatibility(compat)
            _client_id = _section.get('ClientId', client_id)
            self.__client_id = str(_client_id) if _client_id is not None else DEFAULT_CLIENT_ID
            _admin_client_id = _section.get('AdminClientId', admin_client_id)
            self.__admin_client_id = str(_admin_client_id) if _admin_client_id is not None else DEFAULT_ADMIN_CLIENT_ID
        else:
            self.__realm = str(realm) if realm is not None else DEFAULT_REALM
            self.__verify_ssl = bool(verify_ssl) if verify_ssl is not None else DEFAULT_VERIFY_SSL
            self.__host = str(host) if host is not None else DEFAULT_HOST
            self.__alt_host = str(alt_host) if alt_host is not None else self.__host
            self.__secret = str(secret) if secret is not None else None
            self.__secret_file = str(secret_file) if secret_file is not None else None
            if keycloak_compatibility is not None and not isinstance(keycloak_compatibility, KeycloakCompatibility):
                raise ValueError(
                    f'Keycloak_compatibility must be a KeycloakCompatibility enum value or None but was {keycloak_compatibility}')
            self.__keycloak_compatibility = keycloak_compatibility or DEFAULT_KEYCLOAK_COMPATIBILITY
            self.__client_id = str(client_id) if client_id is not None else DEFAULT_CLIENT_ID
            self.__admin_client_id = str(admin_client_id) if admin_client_id is not None else DEFAULT_ADMIN_CLIENT_ID
        if self.keycloak_compatibility == KeycloakCompatibility.FIFTEEN:
            self.__base_url = URL(self.host) / 'auth'
            self.__alt_base_url = URL(self.alt_host) / 'auth' if self.__alt_host else self.__base_url
        else:
            self.__base_url = URL(self.host)
            self.__alt_base_url = URL(self.alt_host) if self.__alt_host else self.__base_url
        logger = logging.getLogger(__name__)
        logger.info('Using Keycloak %s mode', self.__keycloak_compatibility.value)
        if self.__host is None:
            raise ValueError
        logger.debug('host is %s', self.__host)
        self.__expiry: datetime | None = None
        self.__access_token: AccessToken | None = None
        self.__client_uuid: str | None = None

    @property
    def client_id(self) -> str:
        """The Keycloak client id. The default is hea."""
        return self.__client_id

    @property
    def admin_client_id(self) -> str:
        """The Keycloak admin client id. The default is admin-cli."""
        return self.__admin_client_id

    @property
    def realm(self) -> str:
        return self.__realm

    @property
    def host(self) -> str:
        """The url string specified in the Host property in the HEA config file, passed into the object's constructor,
        or the default value of https://localhost:8444."""
        return self.__host

    @property
    def alt_host(self) -> str:
        """The alternate hostname for getting the alt access token. Defaults to the value of host if unspecified in the
        config or this parameter."""
        return self.__alt_host

    async def get_secret(self, request: Request | None = None, app: Application | None = None) -> str | None:
        """The Keycloak secret specified in the Secret property in the HEA config file, the file specified in the HEA
        config, passed into the object's constructor, or obtained from a HEA property. The secret is decrypted on the
        fly if necessary.

        :param request: the HTTP request (optional). If not provided, the request passed into the constructor is used,
        if any. If neither is provided, the secret is obtained only from the secret file, config, or constructor.
        :param app: the application (optional). Used if no request is provided.
        :return: the secret or None if not found."""
        logger = logging.getLogger(__name__)
        _request = request or self.request
        secret: str | None = None
        if self.secret_file and (secret_file_path := Path(self.secret_file)).exists():
            secret = secret_file_path.read_text(encoding='utf-8')
            logger.debug('Read secret from file')
        elif self.__secret is not None:
            secret = self.__secret
            logger.debug('Read secret from config or constructor')
        elif _request and (secret_property := await get_property(_request.app, KEYCLOAK_QUERY_ADMIN_SECRET)):
            secret = secret_property.value
            logger.debug('Read secret from registry service')
        elif app and (secret_property := await get_property(app, KEYCLOAK_QUERY_ADMIN_SECRET)):
            secret = secret_property.value
            logger.debug('Read secret from registry service')
        if _request:
            secret_decryption = SecretDecryption.from_request(_request)
        elif app:
            secret_decryption = SecretDecryption.from_app(app)
        else:
            secret_decryption = self.__config.get_secret_decryption() if self.__config else None
        if secret and secret_decryption:
            return secret_decryption.decrypt_config_property(secret)
        return secret

    @property
    def secret_file(self) -> str | None:
        return self.__secret_file

    @property
    def verify_ssl(self) -> bool:
        return self.__verify_ssl

    @property
    def keycloak_compatibility(self) -> KeycloakCompatibility:
        return self.__keycloak_compatibility

    @property
    def base_url(self) -> URL:
        """The host URL plus /auth or not depending on whether keycloak compatibility is set to 15 or 19."""
        return self.__base_url

    def get_default_permission_context(self, request: Request) -> PeopleServicePermissionContext:
        return PeopleServicePermissionContext(request, self)

    async def get_keycloak_access_token(self, request: Request) -> AccessToken | None:
        """
        Request an access token from Keycloak. It tries obtaining a secret from the following places, in order:
        1) The secret parameter of this class' constructor, or the Secret property of the Keycloak section of the HEA
        config file.
        2) A file whose name is passed into the constructor, or provided in the SecretFile property of the Keycloak
        section of the HEA config file. The file must contain one line with the secret.
        3) The KEYCLOAK_QUERY_ADMIN_SECRET registry property.

        :param use_alt_base_url:
        :param request: the HTTP request (request).
        :return: the access token or None if not found.
        """
        async with _ACCESS_TOKEN_LOCK:
            if self.__expiry and self.__expiry >= datetime.now() + timedelta(minutes=1):
                return self.__access_token
            else:
                session = request.app[appproperty.HEA_CLIENT_SESSION]
                logger = logging.getLogger(__name__)

                token_url = self.__base_url / 'realms' / self.realm / 'protocol' / 'openid-connect' / 'token'
                logger.debug('Requesting new access token using credentials')
                if secret := await self.get_secret(request):
                    pass
                else:
                    raise ValueError('No secret defined')
                token_body = {
                    'client_secret': secret,
                    'client_id': self.admin_client_id,
                    'grant_type': 'client_credentials'
                }
                logger.debug('Going to verify ssl? %r', self.verify_ssl)
                async with session.post(token_url, data=token_body, verify_ssl=self.verify_ssl) as response_:
                    content = await response_.json()
                    logger.debug('content %s', content)
                    access_token = content['access_token']
                    self.__expiry = datetime.now() + timedelta(seconds=int(content['expires_in']))
                    access_token_obj = AccessToken()
                    access_token_obj.id = access_token
                    self.__access_token = access_token_obj
                return access_token_obj

    async def get_keycloak_alt_access_token(self, request: Request) -> AccessToken:
        """
        Request an access token from Keycloak with alternate path. It tries obtaining a secret from the following places, in order:
        1) The secret parameter of this class' constructor, or the Secret property of the Keycloak section of the HEA
        config file.
        2) A file whose name is passed into the constructor, or provided in the SecretFile property of the Keycloak
        section of the HEA config file. The file must contain one line with the secret.
        3) The KEYCLOAK_QUERY_ADMIN_SECRET registry property.

        :param request: the HTTP request (request).
        :return: the access token or None if not found.
        """
        async with _ACCESS_TOKEN_LOCK:
            session = request.app[appproperty.HEA_CLIENT_SESSION]
            logger = logging.getLogger(__name__)

            token_url = self.__alt_base_url / 'realms' / self.realm / 'protocol' / 'openid-connect' / 'token'
            logger.debug('Requesting new access token using credentials')
            if secret := await self.get_secret(request):
                pass
            else:
                raise ValueError('No secret defined')
            token_body = {
                'client_secret': secret,
                'client_id': self.admin_client_id,
                'grant_type': 'client_credentials'
            }
            logger.debug('Going to verify ssl? %r', self.verify_ssl)
            async with session.post(token_url, data=token_body, verify_ssl=self.verify_ssl) as response_:
                content = await response_.json()
                logger.debug('content %s', content)
                access_token = content['access_token']
                access_token_obj = AccessToken()
                access_token_obj.id = access_token
            return access_token_obj

    async def get_users(self, request: Request, params: dict[str, str] | None = None) -> list[Person]:
        """
        Gets a list of users from Keycloak using the '/auth/admin/realms/{realm}/users' REST API call.

        :param request: the HTTP request (required).
        :param params: any query parameters to add to the users request.
        :return: a list of Person objects, or the empty list if there are none.
        """
        logger = logging.getLogger(__name__)
        exclude_system_users = parse_bool(request.query.get('excludesystem', 'no'))
        cached_val = self.__ttl_cache.get(('all_users', exclude_system_users, None))
        if cached_val is not None:
            return list(cached_val)
        else:
            access_token_obj = await self.get_keycloak_access_token(request)
            assert access_token_obj is not None, 'access_token_obj cannot be None'
            access_token = access_token_obj.id
            session = request.app[appproperty.HEA_CLIENT_SESSION]
            async with session.get(self.__base_url / 'admin' / 'realms' / self.realm / 'users' / 'count',
                                   headers={'Authorization': f'Bearer {access_token}'},
                                   verify_ssl=self.verify_ssl) as count_result:
                count = int(await count_result.text())
            logger.debug('number of users %d', count)
            step = 100
            users_url = self.__base_url / 'admin' / 'realms' / self.realm / 'users'
            params_ = {}
            for k, v in (params or {}).items():
                match k:
                    case 'name':
                        params_['username'] = v
                    case 'first_name':
                        params_['firstName'] = v
                    case 'last_name':
                        params_['lastName'] = v
                    case _:
                        params_[k] = v
            if exclude_system_users:
                persons: list[Person] = []
            else:
                persons = [system_person for system_person in get_system_people() if not params or params.get('name') == system_person.name]
            person_ids = set(p.id for p in persons)
            for i in range(0, count, step):
                users_url_ = users_url.with_query(params_ | {'first': i, 'max': step})
                logger.debug('Getting users from URL %s', users_url_)
                async with session.get(users_url_,
                                    headers={'Authorization': f'Bearer {access_token}'},
                                    verify_ssl=self.verify_ssl) as response_:
                    async def get_groups(user_json: Mapping[str, Any]) -> list[dict[str, Any]]:
                        group_dicts: list[dict[str, Any]] = []
                        async for group_dict in self.__get_user_groups_json(request, user_json['id']):
                            group_dicts.append(group_dict)
                        return group_dicts
                    async def worker(user_json: Mapping[str, Any]):
                        person = self.__keycloak_user_to_person(user_json, await get_groups(user_json))
                        if not params or all(p for p in params.keys() if getattr(person, p) == params[p]):
                            persons.append(person)
                    async def user_iterator() -> AsyncIterator[dict[str, Any]]:
                        for user_json in await response_.json():
                            if user_json['id'] not in person_ids:
                                person_ids.add(user_json['id'])
                                yield user_json
                    await queued_processing(user_iterator(), worker)
            self.__ttl_cache[('all_users', exclude_system_users, None)] = persons
            for person in persons:
                self.__ttl_cache[('one_user', person.id)] = person
            return deepcopy(persons)

    async def get_user(self, request: Request, id_: str) -> Person | None:
        """
        Gets the user from Keycloak with the given id using the '/auth/admin/realms/{realm}/users/{id}' REST API call.

        :param request: the HTTP request (required).
        :param id_: the user id (required).
        :return: a Person object.
        :raises ClientResponseError if an error occurred or the person was not found.
        """
        logger = logging.getLogger(__name__)
        logger.debug('getting user %s', id_)
        cached_val = self.__ttl_cache.get(('one_user', id_))
        if cached_val is not None:
            return deepcopy(cached_val)
        elif all_users := self.__ttl_cache.get(('all_users', False, None)):
            try:
                person = next(p for p in all_users if p.id == id_)
                self.__ttl_cache[('one_user', id_)] = person
                return deepcopy(person)
            except StopIteration:
                return None
        if is_system_user(id_):
            person = get_system_person(id_)
            self.__ttl_cache[('one_user', id_)] = person
            return person
        else:
            access_token_obj = await self.get_keycloak_access_token(request)
            assert access_token_obj is not None, 'access_token_obj cannot be None'
            access_token = access_token_obj.id
            session = request.app[appproperty.HEA_CLIENT_SESSION]
            user_url = self.__base_url / 'admin' / 'realms' / self.realm / 'users' / id_
            async with session.get(user_url,
                                headers={'Authorization': f'Bearer {access_token}'},
                                verify_ssl=self.verify_ssl) as response_:
                user_json = await response_.json()
                logger.debug('Response was %s', user_json)
                if 'error' in user_json:
                    if user_json['error'] == 'User not found':
                        return None
                    else:
                        raise ValueError(user_json['error'])
            group_dicts: list[dict[str, Any]] = []
            async for group_dict in self.__get_user_groups_json(request, id_):
                group_dicts.append(group_dict)
            person = self.__keycloak_user_to_person(user_json, group_dicts)
            self.__ttl_cache[('one_user', id_)] = person
            return deepcopy(person)

    async def get_current_user_roles(self, request: Request) -> list[Role]:
        """
        Gets the current user's roles.

        :param request: the HTTP request (required).
        :returns: a list of Role objects.
        :raises ClientResponseError: if something went wrong getting role information.
        :raises ValueError: if something went wrong getting role information.

        """
        logger = logging.getLogger(__name__)
        sub = request.headers.get(SUB, NONE_USER)
        cached_val = self.__ttl_cache.get(('my_roles', sub))
        if cached_val is not None:
            return cached_val
        else:
            values = [self.__new_role(sub, role_json) async for role_json in self.__get_my_roles_json(request)]
            self.__ttl_cache[('my_roles', sub)] = values
            return values

    async def has_role_current_user(self, request: Request, role_name: str) -> bool:
        """
        Returns whether the current user has the given role.

        :param request: the HTTP request (required).
        :param role_name: the role to check (required).
        :returns: True or False.
        :raises ClientResponseError: if something went wrong getting role information.
        :raises ValueError: if something went wrong getting role information due to an internal server error.
        """
        for role in await self.get_current_user_roles(request):
            if role.role == role_name:
                return True
        else:
            return False

    async def get_user_groups(self, request: Request, sub: str) -> list[Group]:
        """
        Gets the current user's groups.

        :param request: the HTTP request (required).
        :returns: a list of Group objects.
        :raises ClientResponseError: if something went wrong getting group information.
        :raises ValueError: if something went wrong getting group information due to an internal server error.

        """
        logger = logging.getLogger(__name__)
        async with self._all_groups_lock:
            cached_val = self.__ttl_cache.get(('my_groups', sub))
            if cached_val is not None:
                return cached_val
            else:
                groups = [self.__new_group(sub, group_json) async for group_json in self.__get_user_groups_json(request, sub)]
                access_token_obj = await self.get_keycloak_access_token(request)
                assert access_token_obj is not None, 'access_token_obj cannot be None'
                access_token = access_token_obj.id
                session = request.app[appproperty.HEA_CLIENT_SESSION]
                role_base_url = self.base_url / 'admin' / 'realms' / self.realm
                session_get = partial(session.get,
                                        headers={'Authorization': f'Bearer {access_token}'},
                                        verify_ssl=self.verify_ssl)
                for group in groups:
                    try:
                        assert group.id is not None, 'group.id cannot be None'
                        async with session_get(role_base_url / 'groups' / group.id / 'role-mappings') as response_:
                            logger.debug('role mappings for group %s: %s', group.id, await response_.json())
                            for role_dict in (await response_.json()).get('clientMappings', {}).get(self.client_id, {}).get('mappings', []):
                                role = self.__new_role(sub, role_dict)
                                assert role.id is not None, 'role.id cannot be None'
                                group.add_role_id(role.id)
                    except ClientResponseError as e:
                        raise ValueError(f'Error getting role mapping information for group {group.group}') from e
                await self.__add_roles_to_groups(request, sub, groups)
                self.__ttl_cache[('my_groups', sub)] = groups
                return groups

    async def get_current_user_groups(self, request: Request) -> list[Group]:
        """
        Gets the current user's groups.

        :param request: the HTTP request (required).
        :returns: a list of Group objects.
        :raises ClientResponseError: if something went wrong getting group information.
        :raises ValueError: if something went wrong getting group information due to an internal server error.

        """
        async with self._all_groups_lock:
            return await self.__get_current_user_groups(request)

    async def get_all_groups(self, request: Request) -> list[Group]:
        """
        Returns all groups known to Keycloak.

        :param request: the HTTP request (required).
        :return: a list of Group objects.
        :raises ClientResponseError: if something went wrong getting group information.
        :raises ValueError if an error occurred getting the groups due an internal server error.
        """
        async with self._all_groups_lock:
            return await self.__get_all_groups(request)

    async def get_all_roles(self, request: Request) -> list[Role]:
        sub = request.headers.get(SUB, NONE_USER)
        cached_val = self.__ttl_cache.get(('all_roles', sub))
        if cached_val is not None:
            return cached_val
        else:
            values = [self.__new_role(sub, role_json) async for role_json in self.__get_all_roles_json(request)]
            self.__ttl_cache[('all_roles', sub)] = values
            return values

    async def create_role(self, request: Request, name: str) -> str:
        sub = request.headers.get(SUB, NONE_USER)
        location = await self.__create_role(request, name)
        self.__ttl_cache.pop(('all_roles', sub), None)
        self.__ttl_cache.pop(('my_roles', sub), None)
        return location

    async def delete_role(self, request: Request, name: str):
        sub = request.headers.get(SUB, NONE_USER)
        await self.__delete_role(request, name)
        self.__ttl_cache.pop(('all_roles', sub), None)
        self.__ttl_cache.pop(('my_roles', sub), None)

    async def create_group(self, request: Request, group: Group):
        sub = request.headers.get(SUB, NONE_USER)
        async with self._all_groups_lock:
            location = await self.__create_group(request, group)
            self.__ttl_cache.pop(('all_groups', None), None)
            self.__ttl_cache.pop(('my_groups', sub), None)
        return location

    async def delete_group(self, request: Request, name: str):
        logger = logging.getLogger(__name__)
        sub = request.headers.get(SUB, NONE_USER)
        logger.debug('Deleting group %s', name)
        async with self._all_groups_lock:
            groups = {group['name']: group async for group in self.__get_all_groups_json(request)}
            for group_key in reversed(name.split('/')[1:]):
                group_ = groups.get(group_key)
                if group_ is not None:
                    id_ = group_['id']
                    assert id_ is not None, 'id_ cannot be None'
                    if not any((path_split := group['path'].split('/')) and \
                            id_ in path_split and len(path_split) > 1 and \
                                (i := path_split.index(id_)) and i < len(path_split) - 1 for group in groups.values()):
                        await self.__delete_group(request, id_)
                    else:
                        logger.debug('Not deleting group %s because it has children', id_)
            self.__ttl_cache.pop(('all_groups', sub), None)
            self.__ttl_cache.pop(('all_groups', None), None)
            self.__ttl_cache.pop(('my_groups', sub), None)

    async def has_group_current_user(self, request: Request, group: str) -> bool:
        """
        Returns whether the current user has the given group.

        :param request: the HTTP request (required).
        :param group_name: the group to check (required).
        :returns: True or False.
        :raises ClientResponseError: if something went wrong getting group information.
        :raises ValueError: if something went wrong getting group information.
        """
        async with self._all_groups_lock:
            async for group_json in self.__get_my_groups_json(request):
                if group_json['name'] == group:
                    return True
            else:
                return False

    async def get_current_user_group_by_group(self, request: Request, group: str) -> Group | None:
        async with self._all_groups_lock:
            return await self.__get_current_user_group_by_group(request, group)

    async def add_current_user_to_group(self, request: Request, id_: str):
        logger = logging.getLogger(__name__)
        sub = request.headers.get(SUB, NONE_USER)
        await self.add_user_to_group(request, sub, id_)

    async def add_user_to_group(self, request: Request, sub: str, id_: str):
        logger = logging.getLogger(__name__)
        actual_sub = request.headers.get(SUB, NONE_USER)
        if actual_sub not in (sub, CREDENTIALS_MANAGER_USER):
            raise response.status_not_found()
        access_token_obj = await self.get_keycloak_access_token(request)
        assert access_token_obj is not None, 'access_token_obj cannot be None'
        access_token = access_token_obj.id
        session = request.app[appproperty.HEA_CLIENT_SESSION]
        group_base_url = self.base_url / 'admin' / 'realms' / self.realm / 'users' / sub / 'groups'
        session_put = partial(session.put,
                            headers={'Authorization': f'Bearer {access_token}'},
                            verify_ssl=self.verify_ssl)
        try:
            logger.debug('Adding user %s to group %s', sub, id_)
            async with self._all_groups_lock:
                async with session_put(group_base_url / id_) as response_:
                    self.__ttl_cache.pop(('my_groups', sub), None)
                    self.__ttl_cache.pop(('all_users', True, None), None)
                    self.__ttl_cache.pop(('all_users', False, None), None)
                    self.__ttl_cache.pop(('one_user', sub), None)
                    self.__ttl_cache.pop(('my_roles', sub), None)
        except ClientResponseError as e:
            raise response.status_generic_error(status=e.status, body=e.message)

    async def remove_current_user_group(self, request: Request, id_: str) -> bool:
        sub = request.headers.get(SUB, NONE_USER)
        return await self.remove_user_group(request, sub, id_)

    async def remove_user_group(self, request: Request, sub: str, id_: str) -> bool:
        async with self._all_groups_lock:
            return await self.__remove_user_group(request, sub, id_)

    async def remove_current_user_group_by_group(self, request: Request, group: str) -> bool:
        sub = request.headers.get(SUB, NONE_USER)
        async with self._all_groups_lock:
            if (group_obj := await self.__get_current_user_group_by_group(request, group)) is None:
                return False
            assert group_obj.id is not None, 'group_obj.id cannot be None'
            return await self.__remove_user_group(request, sub, group_obj.id)

    async def remove_user_group_by_group(self, request: Request, sub: str, group: str) -> bool:
        async with self._all_groups_lock:
            if (group_obj := await self.__get_group_by_group(request, group)) is None:
                return False
            assert group_obj.id is not None, 'group_obj.id cannot be None'
            return await self.__remove_user_group(request, sub, group_obj.id)

    async def get_group_by_group(self, request: Request, group: str) -> Group | None:
        async with self._all_groups_lock:
            try:
                return next(g for g in await self.__get_all_groups(request) if g.group == group)
            except StopIteration:
                return None

    async def __remove_user_group(self, request: Request, sub: str, id_: str) -> bool:
        actual_sub = request.headers.get(SUB, NONE_USER)
        if actual_sub not in (sub, CREDENTIALS_MANAGER_USER):
            return False
        access_token_obj = await self.get_keycloak_access_token(request)
        assert access_token_obj is not None, 'access_token_obj cannot be None'
        access_token = access_token_obj.id
        session = request.app[appproperty.HEA_CLIENT_SESSION]

        role_base_url = self.base_url / 'admin' / 'realms' / self.realm / 'users' / sub / 'groups'
        session_delete = partial(session.delete,
                            headers={'Authorization': f'Bearer {access_token}'},
                            verify_ssl=self.verify_ssl, raise_for_status=False)
        async with session_delete(role_base_url / id_) as response_:
            if response_.status == 404:
                return False
            if response_.status != 204:
                raise ValueError('Adding user to group failed')
            self.__ttl_cache.pop(('my_groups', sub), None)
            self.__ttl_cache.pop(('all_users', True, None), None)
            self.__ttl_cache.pop(('all_users', False, None), None)
            self.__ttl_cache.pop(('one_user', sub), None)
            self.__ttl_cache.pop(('my_roles', sub), None)
            return True

    async def __get_current_user_group_by_group(self, request: Request, group: str) -> Group | None:
        try:
            return next(g for g in await self.__get_current_user_groups(request) if g.group == group)
        except StopIteration:
            return None

    async def __get_current_user_groups(self, request: Request) -> list[Group]:
        """
        Gets the current user's groups.

        :param request: the HTTP request (required).
        :returns: a list of Group objects.
        :raises ClientResponseError: if something went wrong getting group information.
        :raises ValueError: if something went wrong getting group information due to an internal server error.

        """
        logger = logging.getLogger(__name__)
        sub = request.headers.get(SUB, NONE_USER)
        cached_val = self.__ttl_cache.get(('my_groups', sub))
        if cached_val is not None:
            return cached_val
        else:
            groups = [self.__new_group(sub, group_json) async for group_json in self.__get_my_groups_json(request)]
            access_token_obj = await self.get_keycloak_access_token(request)
            assert access_token_obj is not None, 'access_token_obj cannot be None'
            access_token = access_token_obj.id
            session = request.app[appproperty.HEA_CLIENT_SESSION]
            role_base_url = self.base_url / 'admin' / 'realms' / self.realm
            session_get = partial(session.get,
                                    headers={'Authorization': f'Bearer {access_token}'},
                                    verify_ssl=self.verify_ssl)
            for group in groups:
                try:
                    assert group.id is not None, 'group.id cannot be None'
                    async with session_get(role_base_url / 'groups' / group.id / 'role-mappings') as response_:
                        for role_dict in await response_.json():
                            role = self.__new_role(sub, role_dict)
                            assert role.id is not None, 'role.id cannot be None'
                            group.add_role_id(role.id)
                except ClientResponseError as e:
                    raise ValueError(f'Error getting role mapping information for group {group.group}') from e
            await self.__add_roles_to_groups(request, sub, groups)
            self.__ttl_cache[('my_groups', sub)] = groups
            return groups

    async def __get_group_by_group(self, request: Request, group: str) -> Group | None:
        try:
            return next(g for g in await self.__get_all_groups(request) if g.group == group)
        except StopIteration:
            return None

    async def __get_all_groups(self, request: Request) -> list[Group]:
        """
        Returns all groups known to Keycloak.

        :param request: the HTTP request (required).
        :return: a list of Group objects.
        :raises ClientResponseError: if something went wrong getting group information.
        :raises ValueError if an error occurred getting the groups due an internal server error.
        """
        logger = logging.getLogger(__name__)
        sub = request.headers.get(SUB, NONE_USER)
        cached_val = self.__ttl_cache.get(('all_groups', None))
        if cached_val is not None:
            logger.debug('Getting cached groups %s', cached_val)
            return cached_val
        else:
            groups = [self.__new_group(sub, group_json) async for group_json in self.__get_all_groups_json(request)]

            await self.__add_roles_to_groups(request, sub, groups)
            self.__ttl_cache[('all_groups', None)] = groups
            logger.debug('Getting groups %s', groups)
            return groups

    def __new_role(self, sub: str, role_dict: dict[str, Any]) -> Role:
        """
        Returns a Role object from Keycloak role json.

        :param sub: the user id (required).
        :param role_dict: the role json (required).
        :return: a newly Role object.
        """
        role: Role = Role()
        role.role = role_dict['name']
        role.description = role_dict.get('description')
        role.owner = NONE_USER
        share1: Share = ShareImpl()
        share1.user = ALL_USERS
        share1.permissions = [Permission.VIEWER]
        role.user_shares = [share1]
        return role

    async def __get_client_uuid(self, request: Request) -> str:
         if self.__client_uuid is not None:
            return self.__client_uuid
         else:
            session = request.app[appproperty.HEA_CLIENT_SESSION]
            role_base_url = self.base_url / 'admin' / 'realms' / self.realm
            access_token_obj = await self.get_keycloak_access_token(request)
            assert access_token_obj is not None, 'access_token_obj cannot be None'
            access_token = access_token_obj.id
            session_get = partial(session.get,
                                headers={'Authorization': f'Bearer {access_token}'},
                                verify_ssl=self.verify_ssl)
            async with session_get(role_base_url / 'clients') as response_:
                for client_ in await response_.json():
                    if client_['clientId'] == self.client_id:
                        self.__client_uuid = client_['id']
                        return self.__client_uuid
                else:
                    raise ValueError(f'No client with id {self.client_id}')

    async def __get_my_roles_json(self, request: Request) -> AsyncIterator[dict[str, Any]]:
        logger = logging.getLogger(__name__)
        sub = request.headers.get(SUB, NONE_USER)
        access_token_obj = await self.get_keycloak_access_token(request)
        assert access_token_obj is not None, 'access_token_obj cannot be None'
        access_token = access_token_obj.id
        session = request.app[appproperty.HEA_CLIENT_SESSION]

        role_base_url = self.base_url / 'admin' / 'realms' / self.realm
        session_get = partial(session.get,
                            headers={'Authorization': f'Bearer {access_token}'},
                            verify_ssl=self.verify_ssl)
        roles = {}
        client_id_ = await self.__get_client_uuid(request)
        async def one():
            async with session_get(role_base_url / 'users' / sub / 'role-mappings' / 'clients' / client_id_ / 'composite') as response_:
                for role_dict in await response_.json():
                    roles[role_dict['name']] = role_dict
        async def two():
            async with session_get(role_base_url / 'users' / sub / 'role-mappings' / 'clients' / client_id_) as response_:
                for role_dict in await response_.json():
                    roles[role_dict['name']] = role_dict
        await gather(one(), two())
        logger.debug('roles are %s', roles)
        for role_ in roles.values():
            yield role_

    async def __get_all_roles_json(self, request: Request) -> AsyncIterator[dict[str, Any]]:
        logger = logging.getLogger(__name__)
        sub = request.headers.get(SUB, NONE_USER)
        access_token_obj = await self.get_keycloak_access_token(request)
        assert access_token_obj is not None, 'access_token_obj cannot be None'
        access_token = access_token_obj.id

        session = request.app[appproperty.HEA_CLIENT_SESSION]

        role_base_url = self.base_url / 'admin' / 'realms' / self.realm
        session_get = partial(session.get,
                            headers={'Authorization': f'Bearer {access_token}'},
                            verify_ssl=self.verify_ssl)
        roles = {}
        async with session_get(role_base_url / 'clients') as response_:
            for client_ in await response_.json():
                if client_['clientId'] == self.client_id:
                    client_id_ = client_['id']
                    break
            else:
                raise ValueError(f'No client with id {self.client_id}')

        async with session_get(role_base_url / 'clients' / client_id_ / 'roles') as response_:
            for role_dict in await response_.json():
                roles[role_dict['name']] = role_dict

        logger.debug('roles are %s', roles)
        for role_ in roles.values():
            yield role_

    async def __create_role(self, request: Request, name: str) -> str:
        logger = logging.getLogger(__name__)
        access_token_obj = await self.get_keycloak_access_token(request)
        assert access_token_obj is not None, 'access_token_obj cannot be None'
        access_token = access_token_obj.id
        session = request.app[appproperty.HEA_CLIENT_SESSION]
        role_base_url = self.base_url / 'admin' / 'realms' / self.realm
        session_get = partial(session.get,
                              headers={'Authorization': f'Bearer {access_token}'},
                              verify_ssl=self.verify_ssl)
        async with session_get(role_base_url / 'clients') as response_:
            for client_ in await response_.json():
                if client_['clientId'] == self.client_id:
                    client_id_ = client_['id']
                    break
            else:
                raise ValueError(f'No client with id {self.client_id}')
        session_post = partial(session.post,
                               headers={'Authorization': f'Bearer {access_token}',
                                        hdrs.CONTENT_TYPE: 'application/json'},
                               verify_ssl=self.verify_ssl)
        logger.debug('Creating role %s for client %s', name, client_id_)
        try:
            async with session_post(role_base_url / 'clients' / client_id_ / 'roles', json={'name': name}) as response_:
                return str(URL(request.app[appproperty.HEA_COMPONENT]) / 'roles' / encode_role(name))
        except ClientResponseError as e:
            raise response.status_generic_error(status=e.status, body=e.message)

    async def __delete_role(self, request: Request, name: str):
        access_token_obj = await self.get_keycloak_access_token(request)
        assert access_token_obj is not None, 'access_token_obj cannot be None'
        access_token = access_token_obj.id
        session = request.app[appproperty.HEA_CLIENT_SESSION]
        role_base_url = self.base_url / 'admin' / 'realms' / self.realm
        session_get = partial(session.get,
                              headers={'Authorization': f'Bearer {access_token}'},
                              verify_ssl=self.verify_ssl)
        async with session_get(role_base_url / 'clients') as response_:
            for client_ in await response_.json():
                if client_['clientId'] == self.client_id:
                    client_id_ = client_['id']
                    break
            else:
                raise ValueError(f'No client with id {self.client_id}')
        session_delete = partial(session.delete,
                               headers={'Authorization': f'Bearer {access_token}',
                                        hdrs.CONTENT_TYPE: 'application/json'},
                               verify_ssl=self.verify_ssl)
        try:
            async with session_delete(role_base_url / 'clients' / client_id_ / 'roles' / name) as response_:
                pass
        except ClientResponseError as e:
            raise response.status_generic_error(status=e.status, body=e.message)

    async def __create_group(self, request: Request, group: Group) -> str:
        logger = logging.getLogger(__name__)
        logger.debug('Creating group %r', group)
        name = group.group
        assert name is not None, 'group.group cannot be None'
        logger.debug('group path: %s', name)
        access_token_obj = await self.get_keycloak_access_token(request)
        assert access_token_obj is not None, 'access_token_obj cannot be None'
        access_token = access_token_obj.id
        session = request.app[appproperty.HEA_CLIENT_SESSION]
        group_base_url = self.base_url / 'admin' / 'realms' / self.realm
        session_post = partial(session.post,
                               headers={hdrs.AUTHORIZATION: f'Bearer {access_token}',
                                        hdrs.CONTENT_TYPE: 'application/json'},
                               verify_ssl=self.verify_ssl)
        session_get = partial(session.get,
                               headers={hdrs.AUTHORIZATION: f'Bearer {access_token}'},
                               verify_ssl=self.verify_ssl)
        parent_id: str | None = None
        parent_name: str | None = None
        last: str = ''

        for group_name in name.split('/')[1:]:
            logger.debug('group: %s', group_name)
            data = {'name': group_name}
            if parent_id is None:
                try:
                    async with session_post(group_base_url / 'groups', json=data) as response_:
                        id_ = response_.headers[hdrs.LOCATION].rsplit('/', maxsplit=1)[1]
                        logger.debug(f'Group {group_name} created successfully')
                except ClientResponseError as e:
                    if e.status != 409:
                        raise response.status_generic_error(status=e.status, body=e.message)
                    else:
                        logger.debug('Group %s already exists', group_name)
                        group_ = await self.__get_group_by_group(request, name[:name.index(group_name)] + group_name)
                        assert group_ is not None, 'group cannot be None'
                        id_ = group_.id
                        assert id_ is not None, 'id_ cannot be None'
                parent_id = id_
                parent_name = group_name
                last = str(URL(request.app[appproperty.HEA_COMPONENT]) / 'groups' / id_)
            else:
                logger.debug('Making %s a child of %s (%s)', group_name, parent_name, parent_id)
                try:
                    async with session_post(group_base_url / 'groups' / parent_id / 'children', json={'name': group_name}) as response_:
                        logger.debug('Group %s made a child of %s (%s) successfully', group_name, parent_name, parent_id)
                        parent_id = response_.headers[hdrs.LOCATION].rsplit('/', maxsplit=1)[1]
                        assert parent_id is not None, 'parent_id cannot be None'
                        last = str(URL(request.app[appproperty.HEA_COMPONENT]) / 'groups' / parent_id)
                        parent_name = group_name
                except ClientResponseError as e:
                    if e.status != 409:
                        raise response.status_generic_error(status=e.status, body=e.message)
                    else:
                        logger.debug('Group %s is already a child of %s', group_name, parent_name)
                        parent_name = group_name
                        group_ = await self.__get_group_by_group(request, name[:name.index(group_name)] + group_name)
                        assert group_ is not None, 'group_ cannot be None'
                        parent_id = group_.id
        logger.debug('Parent set to %s', parent_name)
        client_uuid = await self.__get_client_uuid(request)
        for role_name in group.role_ids:
            role_name_decoded = decode_role(role_name)
            logger.debug('Adding role %s to client %s', role_name_decoded, self.client_id)
            role_id: str | None = None
            try:
                async with session_post(group_base_url / 'clients' / client_uuid / 'roles', json={'name': role_name_decoded}) as response_:
                    role_id = response_.headers[hdrs.LOCATION].rsplit('/', maxsplit=1)[1]
            except ClientResponseError as e:
                if e.status == 409:
                    logger.debug('Role %s already exists', role_name_decoded)
                    # yarl messes up the path part escaping here, probably because the role name may have a slash in it.
                    async with session_get(f'{group_base_url}/clients/{client_uuid}/roles/{urllib.parse.quote_plus(role_name_decoded)}') as response_:
                        role_id = (await response_.json())['id']
                else:
                    raise e
            assert role_id is not None, 'role_id cannot be None'
            logger.debug('Role %s has id %s', role_name_decoded, role_id)
            try:
                async with session_post(group_base_url / 'groups' / last.rsplit('/', maxsplit=1)[1] / 'role-mappings' / 'clients' / client_uuid,
                                        json=[{'id': role_id, 'name': role_name_decoded, 'composite': False, 'clientRole': True}]) as response_:
                    pass
            except ClientResponseError as e:
                if e.status == 409:
                    logger.debug('Role %s already exists', role_name_decoded)
                else:
                    raise e
        return last

    async def __delete_group(self, request: Request, id_: str):
        access_token_obj = await self.get_keycloak_access_token(request)
        assert access_token_obj is not None, 'access_token_obj cannot be None'
        access_token = access_token_obj.id
        session = request.app[appproperty.HEA_CLIENT_SESSION]
        group_base_url = self.base_url / 'admin' / 'realms' / self.realm
        session_delete = partial(session.delete,
                               headers={'Authorization': f'Bearer {access_token}',
                                        hdrs.CONTENT_TYPE: 'application/json'},
                               verify_ssl=self.verify_ssl)
        try:
            async with session_delete(group_base_url / 'groups' / id_) as response_:
                pass
        except ClientResponseError as e:
            raise response.status_generic_error(status=e.status, body=e.message)

    def __new_group(self, sub: str, group_dict: Mapping[str, Any]) -> Group:
        """
        Returns a Group object from Keycloak group json.

        :param sub: the user id (required).
        :param group_dict: the group json (required).
        :return: a newly Group object.
        """
        group: Group = Group()
        group.id = group_dict['id']
        group.group = group_dict['path']
        group.owner = NONE_USER
        share1: Share = ShareImpl()
        share1.user = ALL_USERS
        share1.permissions = [Permission.VIEWER]
        group.user_shares = [share1]
        group.group_type = GroupType.ADMIN if group_dict['path'].startswith('/*') else GroupType.ORGANIZATION
        return group

    async def __get_my_groups_json(self, request: Request) -> AsyncIterator[dict[str, Any]]:
        sub = request.headers.get(SUB, NONE_USER)
        if not is_system_user(sub):
            async for group_dict in self.__get_user_groups_json(request, sub):
                yield group_dict

    async def __get_user_groups_json(self, request: Request, sub: str) -> AsyncIterator[dict[str, Any]]:
        logger = logging.getLogger(__name__)
        access_token_obj = await self.get_keycloak_access_token(request)
        assert access_token_obj is not None, 'access_token_obj cannot be None'
        access_token = access_token_obj.id

        session = request.app[appproperty.HEA_CLIENT_SESSION]

        group_base_url = self.base_url / 'admin' / 'realms' / self.realm
        session_get = partial(session.get,
                            headers={'Authorization': f'Bearer {access_token}'},
                            verify_ssl=self.verify_ssl)
        if not is_system_user(sub):
            async with session_get(group_base_url / 'users' / sub / 'groups') as response_:
                for group_dict in await response_.json():
                    logger.debug('Returning group %s', group_dict)
                    yield group_dict

    async def __get_all_groups_json(self, request: Request) -> AsyncIterator[dict[str, Any]]:
        logger = logging.getLogger(__name__)
        access_token_obj = await self.get_keycloak_access_token(request)
        assert access_token_obj is not None, 'access_token_obj cannot be None'
        access_token = access_token_obj.id

        session = request.app[appproperty.HEA_CLIENT_SESSION]

        group_base_url = self.base_url / 'admin' / 'realms' / self.realm
        session_get = partial(session.get,
                            headers={'Authorization': f'Bearer {access_token}'},
                            verify_ssl=self.verify_ssl)
        async with session_get((group_base_url / 'groups').with_query({'q': '*'})) as response_:
            q: deque[dict[str, Any]] = deque()
            for group_dict in await response_.json():
                q.append(group_dict)
            while len(q) > 0:
                group_dict = q.popleft()
                for subGroup in group_dict['subGroups']:
                    q.append(subGroup)
                logger.debug('Returning group %s', group_dict)
                yield group_dict

    async def __add_roles_to_groups(self, request: Request, sub: str, groups: Sequence[Group]):
        """
        Adds roles to the given groups.

        :param request: the HTTP request (required).
        :param sub: the username (required).
        :param groups: the groups (required). Assumes the groups have all been persisted.
        :raises ValueError if an error occurred adding the roles due an internal server error.
        """
        logger = logging.getLogger(__name__)
        access_token_obj = await self.get_keycloak_access_token(request)
        assert access_token_obj is not None, 'access_token_obj cannot be None'
        access_token = access_token_obj.id

        session = request.app[appproperty.HEA_CLIENT_SESSION]

        session_get = partial(session.get,
                                headers={'Authorization': f'Bearer {access_token}'},
                                verify_ssl=self.verify_ssl)
        role_base_url = self.base_url / 'admin' / 'realms' / self.realm
        for group in groups:
            try:
                assert group.id is not None, 'group.id cannot be None'
                async with session_get(role_base_url / 'groups' / group.id / 'role-mappings') as response_:
                    response_json = await response_.json()
                    logger.debug('role mappings json for group %s: %s', group, response_json)
                    role_mappings = response_json.get('clientMappings', {}).get(self.client_id, {}).get('mappings', [])
                    for role_dict in role_mappings:
                        role = self.__new_role(sub, role_dict)
                        assert role.id is not None, 'role.id cannot be None'
                        group.add_role_id(role.id)
            except ClientResponseError as e:
                raise ValueError(f'Error getting role mapping information for group {group.group}') from e

    def __keycloak_user_to_person(self, user: Mapping[str, Any], groups: Sequence[Mapping[str, Any]]) -> Person:
        """
        Converts a user JSON object from Keycloak to a HEA Person object.

        :param user: a Keycloak user object as a JSON dict.
        :return: a Person object.
        """
        person: Person = Person()
        person.id = user['id']
        person.name = user['username']
        person.first_name = user.get('firstName')
        person.last_name = user.get('lastName')
        person.email = user.get('email')
        person.created = datetime.fromtimestamp(user['createdTimestamp'] / 1000.0, tz=system_timezone())
        person.owner = NONE_USER
        person.source = 'Keycloak';
        share1: Share = ShareImpl()
        share1.user = ALL_USERS
        share1.permissions = [Permission.VIEWER]
        share2: Share = ShareImpl()
        share2.user = CREDENTIALS_MANAGER_USER
        share2.permissions = [Permission.EDITOR]
        person.user_shares = [share1, share2]
        group_ids = [self.__new_group(ALL_USERS, group).id for group in groups]
        assert all(group_id is not None for group_id in group_ids), 'group_ids cannot be None'
        person.group_ids = group_ids  # type:ignore[assignment]
        return person


class KeycloakMongoManager(MongoManager):
    """
    Keycloak database manager object. It subclasses the Mongo database manager so that user data that Keycloak does not
    support can be stored in Mongo.
    """
    def __init__(self, config: Configuration | None = None,
                 client_id: str | None = DEFAULT_CLIENT_ID,
                 admin_client_id: str | None = DEFAULT_ADMIN_CLIENT_ID,
                 realm: str | None = None,
                 secret: str | None = None,
                 secret_file: str | None = None,
                 verify_ssl: bool = True):
        super().__init__(config)
        self.__client_id = str(client_id) if client_id is not None else DEFAULT_CLIENT_ID
        self.__admin_client_id = str(admin_client_id) if admin_client_id is not None else DEFAULT_ADMIN_CLIENT_ID
        self.__realm = str(realm) if realm is not None else DEFAULT_REALM
        self.__secret: str | None = str(secret) if secret is not None else None
        self.__secret_file: str | None = str(secret_file) if secret_file is not None else DEFAULT_SECRET_FILE
        self.__verify_ssl: bool = bool(verify_ssl)
        self.__keycloak_external_url: str | None = None

    @property
    def client_id(self) -> str:
        return self.__client_id

    @client_id.setter
    def client_id(self, client_id: str):
        self.__client_id = str(client_id) if client_id is not None else DEFAULT_CLIENT_ID

    @property
    def admin_client_id(self) -> str:
        return self.__admin_client_id

    @admin_client_id.setter
    def admin_client_id(self, admin_client_id: str):
        self.__admin_client_id = str(admin_client_id) if admin_client_id is not None else DEFAULT_ADMIN_CLIENT_ID

    @property
    def realm(self) -> str:
        return self.__realm

    @realm.setter
    def realm(self, realm: str):
        self.__realm = str(realm) if realm is not None else DEFAULT_REALM

    @property
    def secret(self) -> str | None:
        return self.__secret

    @secret.setter
    def secret(self, secret: str | None):
        self.__secret = str(secret) if secret is not None else None

    @property
    def secret_file(self) -> str | None:
        return self.__secret_file

    @secret_file.setter
    def secret_file(self, secret_file: str | None):
        self.__secret_file = str(secret_file) if secret_file is not None else None

    @property
    def verify_ssl(self) -> bool:
        return self.__verify_ssl

    @verify_ssl.setter
    def verify_ssl(self, verify_ssl: bool):
        self.__verify_ssl = bool(verify_ssl)

    @property
    def keycloak_external_url(self) -> str | None:
        return self.__keycloak_external_url

    def get_database(self) -> KeycloakMongo:
        return KeycloakMongo(config=self.config,
                            client_id=self.client_id,
                            admin_client_id=self.admin_client_id,
                            realm=self.realm,
                            host=self.keycloak_external_url,
                            secret=self.secret,
                            secret_file=self.secret_file,
                            verify_ssl=self.verify_ssl)
