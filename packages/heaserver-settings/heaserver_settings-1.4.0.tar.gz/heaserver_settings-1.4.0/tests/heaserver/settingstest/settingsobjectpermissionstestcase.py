"""
Creates a test case class for use with the unittest library that is build into Python.
"""

from heaserver.service.testcase.microservicetestcase import get_test_case_cls_default
from heaserver.settings import service
from heaobject.user import NONE_USER, TEST_USER
from heaobject.root import Permission
from heaobject.keychain import Credentials
from heaobject.registry import Collection
from heaserver.service.testcase.expectedvalues import Action

db_store = {
    service.MONGODB_SETTINGS_COLLECTION: [{
        'id': '666f6f2d6261722d71757578',
        'created': None,
        'derived_by': None,
        'derived_from': [],
        'description': None,
        'display_name': 'Reximus',
        'invites': [],
        'modified': None,
        'name': 'reximus',
        'owner': NONE_USER,
        'shares': [],
        'user_shares': [],
        'group_shares': [],
        'source': None,
        'type': 'heaobject.settings.SettingsObject',
        'actual_object_type_name': Collection.get_type_name(),
        'actual_object_uri': f'collections/{Credentials.get_type_name()}',
        'actual_object_id': Credentials.get_type_name(),
        'super_admin_default_permissions': [p.name for p in Permission.non_creator_permissions()]
    },
        {
            'id': '0123456789ab0123456789ab',
            'created': None,
            'derived_by': None,
            'derived_from': [],
            'description': None,
            'display_name': 'Luximus',
            'invites': [],
            'modified': None,
            'name': 'luximus',
            'owner': NONE_USER,
            'shares': [{
                'type': 'heaobject.root.ShareImpl',
                'invite': None,
                'user': TEST_USER,
                'group': NONE_USER,
                'permissions': [Permission.VIEWER.name],
                'type_display_name': 'Share',
                'basis': 'USER'
            }],
            'user_shares': [{
                'type': 'heaobject.root.ShareImpl',
                'invite': None,
                'user': TEST_USER,
                'group': NONE_USER,
                'permissions': [Permission.VIEWER.name],
                'type_display_name': 'Share',
                'basis': 'USER'
            }],
            'group_shares': [],
            'source': None,
            'type': 'heaobject.settings.SettingsObject',
            'actual_object_type_name': Collection.get_type_name(),
            'actual_object_uri': f'collections/{Credentials.get_type_name()}',
            'actual_object_id': Credentials.get_type_name(),
            'super_admin_default_permissions': [p.name for p in Permission.non_creator_permissions()]
        }]}


SettingsObjectPermissionsTestCase = \
    get_test_case_cls_default(coll=service.MONGODB_SETTINGS_COLLECTION,
                              href='http://localhost:8080/settings',
                              wstl_package=service.__package__,
                              fixtures=db_store,
                              get_actions=[
                                  Action(name='heaserver-settings-settings-object-get-properties',
                                         rel=['hea-properties'])],
                              get_all_actions=[
                                  Action(name='heaserver-settings-settings-object-get-properties',
                                         rel=['hea-properties'])],
                              put_content_status=404,
                              sub=TEST_USER)
