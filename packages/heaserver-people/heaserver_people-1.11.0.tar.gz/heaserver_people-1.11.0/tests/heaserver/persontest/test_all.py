from heaserver.service import heaobjectsupport
from aiohttp import hdrs, web
from typing import Union, Type, Optional
from collections.abc import Mapping, Sequence
from heaobject.root import DesktopObject
async def _mock_type_to_resource_url(request: web.Request, type_or_type_name: Union[str, Type[DesktopObject]],
                                     parameters: Optional[Mapping[str, Union[Sequence[Union[int, float, complex, str]], Mapping[str, Union[int, float, complex, str]], tuple[str, Union[int, float, complex, str]], int, float, complex, str]]] = None,
                                     **kwargs: Union[Sequence[Union[int, float, complex, str]], Mapping[str, Union[int, float, complex, str]], tuple[str, Union[int, float, complex, str]], int, float, complex, str]) -> str:
    if type_or_type_name in (Collection, Collection.get_type_name()):
        return 'http://localhost:8080/collections'
    elif type_or_type_name in (Group, Group.get_type_name()):
         return 'http://localhost:8080/groups'
    else:
        raise ValueError(f'Unexpected type {type_or_type_name}')
heaobjectsupport.type_to_resource_url = _mock_type_to_resource_url
from heaserver.service import client
from heaobject.keychain import CredentialsView
from heaobject.settings import SettingsObject
async def _mock_get_all(app, url, type_or_type_name, headers=None):
    coll: Collection = Collection()
    coll.collection_type_name = CredentialsView.get_type_name()
    yield coll
    coll1: Collection = Collection()
    coll1.collection_type_name = SettingsObject.get_type_name()
    yield coll1
client.get_all = _mock_get_all
async def _mock_get_one(app, url, type_or_obj, query_params = None, headers = None, client_session = None):
    g: Group = Group()
    g.id = '0123456789ab0123456789ab'
    g.group = SUPERADMIN_GROUP
    return g
client.get = _mock_get_one
from .testcase import TestCase
from .permissionstestcase import PermissionsTestCase
from heaserver.service.testcase.mixin import GetOneMixin, GetAllMixin, PermissionsGetOneMixin, PermissionsGetAllMixin
from heaserver.service.representor import nvpjson
from heaobject.user import NONE_USER
from heaobject.group import SUPERADMIN_GROUP
from heaobject.registry import Collection
from heaobject.person import Group


class TestGet(TestCase, GetOneMixin):

    async def test_get_me(self):
        async with self.client.get((self._href / 'me').path,
                                           headers={**self._headers, hdrs.ACCEPT: nvpjson.MIME_TYPE}) as response:
                self.assertEqual(NONE_USER, (await response.json())[0]['id'])

    async def test_get_me_status(self):
        async with self.client.get((self._href / 'me').path,
                                           headers={**self._headers, hdrs.ACCEPT: nvpjson.MIME_TYPE}) as response:
                self.assertEqual(200, response.status)


class TestGetAll(TestCase, GetAllMixin):
    pass


class TestGetOneWithBadPermissions(PermissionsTestCase, PermissionsGetOneMixin):
    """A test case class for testing GET one requests with bad permissions."""
    pass


class TestGetAllWithBadPermissions(PermissionsTestCase, PermissionsGetAllMixin):
    """A test case class for testing GET all requests with bad permissions."""
    pass

