from heaserver.service import client
from aiohttp import web, ClientSession, typedefs
from heaobject import root
from heaobject.registry import Component, Collection
from heaobject.person import Person
from typing import Union, Optional
from collections.abc import Mapping
from yarl import URL
async def custom_has(app: web.Application, url: Union[URL, str],
              type_or_obj: root.DesktopObject | type[root.DesktopObject] | None = None,
              query_params: Optional[Mapping[str, str]] = None,
              headers: typedefs.LooseHeaders | None = None,
              client_session: ClientSession | None = None) -> bool:
    return True
client.has = custom_has
async def custom_get_component(app: web.Application, type_or_type_name: Union[str, type[root.DesktopObject]],
                               client_session: ClientSession | None = None) -> Component | None:
    if type_or_type_name == Collection.get_type_name():
        component: Component | None = Component()
        component.name = 'heaserver|registry'
        component.base_url = 'http://heaserver-registry:8080'
    elif type_or_type_name == Person.get_type_name():
        component = Component()
        component.name = 'heaserver|person'
        component.base_url = 'http://heaserver-people:8080'
    else:
        component = None
    return component
client.get_component = custom_get_component

from .settingsobjectpermissionstestcase import SettingsObjectPermissionsTestCase
from heaserver.service.testcase.mixin import PermissionsPostMixin, PermissionsPutMixin, PermissionsGetOneMixin, \
    PermissionsGetAllMixin, PermissionsDeleteMixin


class TestPostSettingsObjectWithBadPermissions(SettingsObjectPermissionsTestCase, PermissionsPostMixin):
    """A test case class for testing POST requests with bad permissions."""
    pass


class TestPutSettingsObjectWithBadPermissions(SettingsObjectPermissionsTestCase, PermissionsPutMixin):
    """A test case class for testing PUT requests with bad permissions."""
    pass


class TestGetOneSettingsObjectWithBadPermissions(SettingsObjectPermissionsTestCase, PermissionsGetOneMixin):
    """A test case class for testing GET one requests with bad permissions."""
    async def test_get_content_bad_permissions(self) -> None:
        self.skipTest('GET content not defined')

    async def test_get_content_bad_permissions_status(self) -> None:
        self.skipTest('GET content not defined')


class TestGetAllSettingsObjectsWithBadPermissions(SettingsObjectPermissionsTestCase, PermissionsGetAllMixin):
    """A test case class for testing GET all requests with bad permissions."""
    pass


class TestDeleteComponentsWithBadPermissions(SettingsObjectPermissionsTestCase, PermissionsDeleteMixin):
    """A test case class for testing DELETE requests with bad permissions."""
    pass
