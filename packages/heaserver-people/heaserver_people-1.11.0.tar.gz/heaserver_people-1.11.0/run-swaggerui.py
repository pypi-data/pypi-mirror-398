#!/usr/bin/env python3

from heaserver.person import service
from heaserver.service.testcase import swaggerui
from heaserver.service.wstl import builder_factory
from heaserver.person.keycloakmongotestcase import KeycloakMongoManagerForTesting
from aiohttp.web import get
from integrationtests.heaserver.personintegrationtest.testcase import db_store
import logging

logging.basicConfig(level=logging.DEBUG)


if __name__ == '__main__':
    swaggerui.run(project_slug='heaserver-people', desktop_objects=db_store,
                  db_manager_cls=KeycloakMongoManagerForTesting,
                  wstl_builder_factory=builder_factory(service.__package__), routes=[
                    (get, '/people/{id}', service.get_person),
                    (get, '/people/byname/{name}', service.get_person_by_name),
                    (get, '/people/', service.get_all_persons),
                    (get, '/people/me', service.get_me),
                    (get, '/roles', service.get_current_user_roles),
                    (get, '/ping', service.ping)
                  ])
