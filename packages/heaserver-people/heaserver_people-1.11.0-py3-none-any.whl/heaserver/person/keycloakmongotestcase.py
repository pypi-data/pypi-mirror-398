import logging
import os
from contextlib import ExitStack

import requests
from aiohttp.web_request import Request
from docker.errors import APIError
from heaobject.person import Person, AccessToken
from heaserver.service import appproperty
from heaserver.service.testcase.docker import start_other_container
from heaserver.service.testcase.dockermongo import DockerMongoManager
from heaserver.service.testcase.testenv import DockerContainerConfig, DockerVolumeMapping
from heaserver.service.util import retry
from heaserver.service.config import Configuration
from yarl import URL
from heaserver.person.keycloakmongo import KEYCLOAK_TEST_IMAGE, DEFAULT_CLIENT_ID, DEFAULT_REALM, DEFAULT_SECRET_FILE, \
    KeycloakMongo
from abc import ABC
from datetime import datetime


class AbstractKeycloakMongoManagerForTesting(DockerMongoManager, ABC):
    KEYCLOAK_CONTAINER_CONFIG = DockerContainerConfig(image=KEYCLOAK_TEST_IMAGE,
                                                      ports=[8080, 8443],
                                                      volumes=[
                                                          DockerVolumeMapping(host=f'{os.getcwd()}/keycloak',
                                                                              container='/tmp')
                                                      ],
                                                      check_path='/auth/',
                                                      env_vars={
                                                          'KEYCLOAK_USER': 'admin',
                                                          'KEYCLOAK_PASSWORD': 'admin',
                                                          'KEYCLOAK_IMPORT': '/tmp/hea-export.json'
                                                      })

    def __init__(self,
                 client_id: str | None = None,
                 realm: str | None = None,
                 secret: str | None = None,
                 secret_file: str | None = None,
                 verify_ssl: bool = True):
        super().__init__()
        self.__client_id = str(client_id) if client_id is not None else DEFAULT_CLIENT_ID
        self.__realm = str(realm) if realm is not None else DEFAULT_REALM
        self.__secret: str | None = str(secret) if secret is not None else None
        self.__secret_file: str | None = str(secret_file) if secret_file is not None else DEFAULT_SECRET_FILE
        self.__verify_ssl: bool = bool(verify_ssl)
        from testcontainers.core.container import DockerContainer
        self.__keycloak: DockerContainer | None = None
        self.__keycloak_external_url: str | None = None

    @property
    def client_id(self) -> str:
        return self.__client_id

    @client_id.setter
    def client_id(self, client_id: str):
        self.__client_id = str(client_id) if client_id is not None else DEFAULT_CLIENT_ID

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

    @retry(APIError)
    def start_database(self, context_manager: ExitStack):
        """
        Starts the database container, using the image defined in DockerImages.MONGODB. This must be called prior to
        calling get_config_file_section().

        :param context_manager: the context manager to which to attach this container. The container will shut down
        automatically when the context manager is closed.
        """
        self.__keycloak, self.__keycloak_external_url = start_other_container(type(self).KEYCLOAK_CONTAINER_CONFIG,
                                                                              context_manager)
        super().start_database(context_manager)

    @classmethod
    def database_types(cls) -> list[str]:
        return ['system|keycloak']

class KeycloakMongoManagerForTesting(AbstractKeycloakMongoManagerForTesting):
    def __init__(self):
        super().__init__()

    def get_database(self) -> KeycloakMongo:
        logger = logging.getLogger(__name__)
        mongo = KeycloakMongoForTesting(config=self.config, host=self.keycloak_external_url)
        users = [{
            'username': 'reximus',
            'firstName': 'Reximus',
            'lastName': 'Max',
            'email': 'reximus.max@example.com',
            'emailVerified': True,
            'credentials': [{
                'value': 'reximus',
                'temporary': False
            }],
            'enabled': True
        },
        {
            'username': 'luximus',
            'firstName': 'Luximus',
            'lastName': 'Max',
            'email': 'luximus.max@example.com',
            'emailVerified': True,
            'credentials': [{
                'value': 'luximus',
                'temporary': False
            }],
            'enabled': True
        }]
        for user in users:
            response = requests.post(mongo.token_url, data=mongo.token_body)
            response.raise_for_status()
            logger.debug('Got token request %s', response)
            access_token = response.json()['access_token']
            response = requests.post(str(URL(mongo.host) / 'auth' / 'admin' / 'realms' / mongo.realm / 'users'),
                                     json=user, headers={'Authorization': f'Bearer {access_token}'})
            response.raise_for_status()
            logger.debug('New user %s requested, got response %s', user, response)

        return mongo


class KeycloakMongoManagerForPyTest(AbstractKeycloakMongoManagerForTesting):

    def get_database(self) -> KeycloakMongo:
        logger = logging.getLogger(__name__)
        mongo = KeycloakMongoForPyTest(config=self.config, host=self.keycloak_external_url)
        response = requests.post(mongo.token_url, data=mongo.token_body)
        response.raise_for_status()
        logger.debug('Got token request %s', response)
        access_token = response.json()['access_token']
        users = [{
            'username': 'reximus',
            'firstName': 'Reximus',
            'lastName': 'Max',
            'email': 'reximus.max@example.com',
            'emailVerified': True,
            'credentials': [{
                'value': 'reximus',
                'temporary': False
            }],
            'enabled': True
        },
        {
            'username': 'luximus',
            'firstName': 'Luximus',
            'lastName': 'Max',
            'email': 'luximus.max@example.com',
            'emailVerified': True,
            'credentials': [{
                'value': 'luximus',
                'temporary': False
            }],
            'enabled': True
        }]
        for user in users:
            @retry(OSError, retries=3, cooldown=5)
            def post_with_retry():
                return requests.post(str(URL(mongo.host) / 'auth' / 'admin' / 'realms' / mongo.realm / 'users'),
                                     json=user, headers={'Authorization': f'Bearer {access_token}'})
            response = post_with_retry()
            response.raise_for_status()
            logger.debug('New user %s requested, got response %s', user, response)

        return mongo


class KeycloakMongoForTesting(KeycloakMongo):
    def __init__(self, config: Configuration | None = None, host: str | None = None, request: Request | None = None):
        super().__init__(config=config, host=host, request=request, verify_ssl=True)

    @property
    def token_url(self) -> str:
        return str(URL(self.host) / 'auth' / 'realms' / 'master' / 'protocol' / 'openid-connect' / 'token')

    @property
    def token_body(self) -> dict[str, str]:
        return {
            'username': 'admin',
            'password': 'admin',
            'client_id': 'admin-cli',
            'grant_type': 'password'
        }

    async def get_keycloak_access_token(self, request: Request) -> AccessToken:
        """
        Request an access token from Keycloak.

        :param request: the HTTP request (required).
        :return: the access token or None if not found.
        """
        session = request.app[appproperty.HEA_CLIENT_SESSION]
        logger = logging.getLogger(__name__)
        logger.debug('Requesting new access token using credentials')

        async with session.post(self.token_url, data=self.token_body, verify_ssl=self.verify_ssl) as response_:
            content = await response_.json()
            logging.getLogger(__name__).debug(f'content {content}')
            access_token = content['access_token']
            access_token_obj = AccessToken()
            access_token_obj.id = access_token
        return access_token_obj

    async def get_keycloak_alt_access_token(self,  request: Request) -> AccessToken:
        """
        Request an access token from Keycloak.

        :param request: the HTTP request (required).
        :return: the access token or None if not found.
        """
        session = request.app[appproperty.HEA_CLIENT_SESSION]
        logger = logging.getLogger(__name__)
        logger.debug('Requesting new access token using credentials')

        async with session.post(self.token_url, data=self.token_body, verify_ssl=self.verify_ssl) as response_:
            content = await response_.json()
            logging.getLogger(__name__).debug(f'content {content}')
            access_token = content['access_token']
            access_token_obj = AccessToken()
            access_token_obj.id = access_token
        return access_token_obj

class KeycloakMongoForPyTest(KeycloakMongoForTesting):
    async def get_users(self, request: Request, params: dict[str, str] | None = None) -> \
            list[Person]:
        users = await super().get_users(request, params)
        for user in users:
            match user.name:
                case 'reximus':
                    user.id = '666f6f2d6261722d71757578'
                case 'luximus':
                    user.id = '0123456789ab0123456789ab'
            user.created = None
            user.modified = None
        return users



