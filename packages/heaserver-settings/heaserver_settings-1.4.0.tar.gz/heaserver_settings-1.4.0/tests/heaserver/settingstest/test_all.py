from heaserver.service import heaobjectsupport
async def _mock_type_to_resource_url(request, type_or_type_name) -> str:
    return 'http://localhost:8080'
heaobjectsupport.type_to_resource_url = _mock_type_to_resource_url
from heaserver.service import client
async def _mock_has(*args, **kwargs):
    return True
client.has = _mock_has
from heaserver.service.testcase.mixin import GetOneMixin, GetAllMixin, PostMixin, PutMixin
from .settingsobjecttestcase import SettingsObjectTestCase

class TestGetSettingsObject(SettingsObjectTestCase, GetOneMixin):
    pass


class TestGetAllSettingsObjects(SettingsObjectTestCase, GetAllMixin):
    pass


class TestPutSettingsObject(SettingsObjectTestCase, PutMixin):
    pass


class TestDeleteSettingsObject(SettingsObjectTestCase):
    async def test_delete_then_get(self) -> None:
        """Tries to delete a settings object, which should succeed (and it resets the object)."""
        async with self.client.request('DELETE',
                                       (self._href / self.expected_one_id()).path,
                                       headers=self._headers) as resp:
            self.assertEqual(204, resp.status)

