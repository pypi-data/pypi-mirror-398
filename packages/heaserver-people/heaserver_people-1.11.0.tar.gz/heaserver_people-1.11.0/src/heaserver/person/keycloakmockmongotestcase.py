from aiohttp.web import Request

from aiohttp.web_request import Request
from heaobject.person import Person, AccessToken
from heaobject.user import ALL_USERS
from heaserver.service.oidcclaimhdrs import SUB
from heaserver.service.testcase.mockmongo import MockMongo, MockMongoManager
from heaserver.service.config import Configuration

from heaserver.person.keycloakmongo import DEFAULT_CLIENT_ID, DEFAULT_REALM, DEFAULT_HOST, DEFAULT_SECRET_FILE, \
    CONFIG_SECTION, DEFAULT_VERIFY_SSL
from heaserver.person.testcasedata import person1, person2


class KeycloakMockMongo(MockMongo):
    def __init__(self, config: Configuration | None = None,
                 client_id: str | None = DEFAULT_CLIENT_ID,
                 realm: str | None = DEFAULT_REALM,
                 host: str | None = DEFAULT_HOST,
                 alt_host: str | None = None,
                 secret: str | None = None,
                 secret_file: str | None = DEFAULT_SECRET_FILE,
                 verify_ssl: bool = False):
        super().__init__(config)
        if config and CONFIG_SECTION in config.parsed_config:
            _section = config.parsed_config[CONFIG_SECTION]
            self.__realm = str(_section.get('Realm', realm) or DEFAULT_REALM)
            self.__verify_ssl = _section.getboolean('VerifySSL', verify_ssl if verify_ssl is not None else DEFAULT_VERIFY_SSL)
            self.__host = str(_section.get('Host', host) or DEFAULT_HOST)
            self.__alt_host = str(_section.get('AltHost', alt_host))
            _secret = _section.get('Secret', secret)
            self.__secret = str(_secret) if _secret else None
            _secret_file = _section.get('SecretFile', secret_file)
            self.__secret_file = str(_secret_file) if _secret_file else None
        else:
            self.__realm = str(realm) if realm else DEFAULT_REALM
            self.__verify_ssl = bool(verify_ssl) if verify_ssl is not None else DEFAULT_VERIFY_SSL
            self.__host = str(host) if host else DEFAULT_HOST
            self.__alt_host = str(alt_host) if alt_host else self.__host
            self.__secret = str(secret) if secret else None
            self.__secret_file = str(secret_file) if secret_file else None


        self.__client_id = str(client_id) if client_id else DEFAULT_CLIENT_ID

    @property
    def client_id(self) -> str:
        return self.__client_id

    @property
    def realm(self) -> str:
        return self.__realm

    @property
    def host(self) -> str:
        return self.__host

    @property
    def secret(self) -> str | None:
        return self.__secret

    @property
    def secret_file(self) -> str | None:
        return self.__secret_file

    @property
    def verify_ssl(self) -> bool:
        return self.__verify_ssl

    async def get_keycloak_access_token(self, request: Request) -> AccessToken:
        access_token_obj = AccessToken()
        access_token_obj.id = '12345678'
        return access_token_obj

    async def get_users(self, request: Request, params: dict[str, str] | None = None) -> list[Person]:
        persons = []
        for r in (person1, person2):
            if params is None or all(hasattr(r, k) and v == getattr(r, k) for k, v in params.items()):
                persons.append(r)
        return persons

    async def get_user(self, request: Request, id_: str) -> Person | None:
        """
        Gets the user from Keycloak with the given id using the '/auth/admin/realms/{realm}/users/{id}' REST API call.

        :param request: the HTTP request (required).
        :param access_token: the access token to use (required).
        :param id_: the user id (required).
        :return: a Person object.
        :raises ClientResponseError if an error occurred or the person was not found.
        """
        match id_:
            case 'system|none':
                return person1 if _has_permission(request, person1) else None
            case 'system|test':
                return person2 if _has_permission(request, person2) else None
            case _:
                return None


class KeycloakMockMongoManager(MockMongoManager):

    def get_database(self) -> KeycloakMockMongo:
        return KeycloakMockMongo(self.config)

def _has_permission(request: Request, person: Person) -> bool:
    return request.headers[SUB] == person.owner or person.owner == ALL_USERS
