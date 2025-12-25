"""
The HEA Settings Service manages user and system settings.
"""

from heaserver.service import response, client
from heaserver.service.runner import init_cmd_line, routes, start, web
from heaserver.service.db import mongo, mongoservicelib
from heaserver.service.wstl import builder_factory, action
from heaserver.service.oidcclaimhdrs import SUB
from heaserver.service.appproperty import HEA_DB
from heaserver.service.heaobjectsupport import type_to_resource_url
from heaserver.service.config import Configuration
from heaobject.settings import SettingsObject
from heaobject.root import DesktopObjectDict, Permission, PermissionContext, to_dict
from heaobject.user import NONE_USER
from heaobject.person import Person, Role, Group
from heaobject.registry import Collection
from heaobject.keychain import CredentialsView
from copy import deepcopy
from yarl import URL
import logging


MONGODB_SETTINGS_COLLECTION = 'settings'

DEFAULT_SETTINGS_OBJECT_TEMPLATES: dict[str, DesktopObjectDict] = {
    'heasettings|profile': {
        'name': 'heasettings|profile',
        'display_name': 'Profile',
        'type': SettingsObject.get_type_name(),
        'owner': NONE_USER,
        'user_shares': [{
            'invite': None,
            'type': 'heaobject.root.ShareImpl',
            'type_display_name': 'heaobject.root.ShareImpl',
            'permissions': [Permission.VIEWER.name]
        }],
        'actual_object_type_name': Person.get_type_name(),
        'actual_object_uri': 'people/me',
        'actual_object_id': 'me'
    },
    'heasettings|credentials': {
        'name': 'heasettings|credentials',
        'display_name': 'Credentials',
        'type': SettingsObject.get_type_name(),
        'owner': NONE_USER,
        'user_shares': [{
            'invite': None,
            'type': 'heaobject.root.ShareImpl',
            'type_display_name': 'heaobject.root.ShareImpl',
            'permissions': [Permission.VIEWER.name]
        }],
        'actual_object_type_name': Collection.get_type_name(),
        'actual_object_uri': f'collections/{CredentialsView.get_type_name()}',
        'actual_object_id': CredentialsView.get_type_name()
    },
    'heasettings|people': {
        'name': 'heasettings|people',
        'display_name': 'People',
        'type': SettingsObject.get_type_name(),
        'owner': NONE_USER,
        'user_shares': [{
            'invite': None,
            'type': 'heaobject.root.ShareImpl',
            'type_display_name': 'heaobject.root.ShareImpl',
            'permissions': [Permission.VIEWER.name]
        }],
        'actual_object_type_name': Collection.get_type_name(),
        'actual_object_uri': f'collections/{Person.get_type_name()}',
        'actual_object_id': Person.get_type_name()
    },
    'heasettings|roles': {
        'name': 'heasettings|roles',
        'display_name': 'Roles',
        'type': SettingsObject.get_type_name(),
        'owner': NONE_USER,
        'user_shares': [{
            'invite': None,
            'type': 'heaobject.root.ShareImpl',
            'type_display_name': 'heaobject.root.ShareImpl',
            'permissions': [Permission.VIEWER.name]
        }],
        'actual_object_type_name': Collection.get_type_name(),
        'actual_object_uri': f'collections/{Role.get_type_name()}',
        'actual_object_id': Role.get_type_name()
    },
    'heasettings|groups': {
        'name': 'heasettings|groups',
        'display_name': 'Groups',
        'type': SettingsObject.get_type_name(),
        'owner': NONE_USER,
        'user_shares': [{
            'invite': None,
            'type': 'heaobject.root.ShareImpl',
            'type_display_name': 'heaobject.root.ShareImpl',
            'permissions': [Permission.VIEWER.name]
        }],
        'actual_object_type_name': Collection.get_type_name(),
        'actual_object_uri': f'collections/{Group.get_type_name()}',
        'actual_object_id': Group.get_type_name()
    },
    'heasettings|collections': {
        'name': 'heasettings|collections',
        'display_name': 'Collections',
        'type': SettingsObject.get_type_name(),
        'owner': NONE_USER,
        'user_shares': [{
            'invite': None,
            'type': 'heaobject.root.ShareImpl',
            'type_display_name': 'heaobject.root.ShareImpl',
            'permissions': [Permission.VIEWER.name]
        }],
        'actual_object_type_name': Collection.get_type_name(),
        'actual_object_uri': f'collections/{Collection.get_type_name()}',
        'actual_object_id': Collection.get_type_name()
    }
}


@routes.get('/settingsping')
async def ping(request: web.Request) -> web.Response:
    """
    Checks if this service is running.

    :param request: the HTTP request.
    :return: the HTTP response.
    """
    return await mongoservicelib.ping(request)


@routes.get('/settings/{id}')
@action('heaserver-settings-settings-object-get-properties', rel='hea-properties')
@action('heaserver-settings-settings-object-get-open-choices', rel='hea-opener-choices', path='settings/{id}/opener')
@action('heaserver-settings-settings-object-get-self', rel='self', path='settings/{id}')
@action('heaserver-settings-settings-object-get-actual', rel='hea-actual', path='{+actual_object_uri}')
async def get_settings_object(request: web.Request) -> web.Response:
    """
    Gets the settings object with the specified id.
    :param request: the HTTP request.
    :return: the requested settings object or Not Found.
    ---
    summary: A specific settings object, by id.
    tags:
        - heaserver-settings
    parameters:
        - $ref: '#/components/parameters/id'
    responses:
      '200':
        $ref: '#/components/responses/200'
      '404':
        $ref: '#/components/responses/404'
    """
    return await _get_settings_object(request)


@routes.get('/settings/byname/{name}')
@action('heaserver-settings-settings-object-get-self', rel='self', path='settings/{id}')
async def get_settings_object_by_name(request: web.Request) -> web.Response:
    """
    Gets the settings object with the specified id.
    :param request: the HTTP request.
    :return: the requested settings object or Not Found.
    ---
    summary: A specific settings object, by name.
    tags:
        - heaserver-settings
    parameters:
        - name: name
          in: path
          required: true
          description: The name of the settings object.
          schema:
            type: string
          examples:
            example:
              summary: A settings object name
              value: heasettings|credentials
    responses:
      '200':
        $ref: '#/components/responses/200'
      '404':
        $ref: '#/components/responses/404'
    """
    sub = request.headers.get(SUB, NONE_USER)
    obj_dict = await mongoservicelib.get_by_name_dict(request, MONGODB_SETTINGS_COLLECTION)
    if obj_dict is None:
        obj_dict = await _default_settings_object_by_name(request, request.match_info['name'])
        if obj_dict is None:
            return await response.get(request, None)
    obj = SettingsObject()
    obj.from_dict(obj_dict)
    context = PermissionContext(sub)
    return await response.get(request, to_dict(obj),
                              permissions=await obj.get_permissions(context),
                              attribute_permissions=await obj.get_all_attribute_permissions(context))


@routes.get('/settings')
@routes.get('/settings/')
@action('heaserver-settings-settings-object-get-properties', rel='hea-properties')
@action('heaserver-settings-settings-object-get-open-choices', rel='hea-opener-choices', path='settings/{id}/opener')
@action('heaserver-settings-settings-object-get-self', rel='self', path='settings/{id}')
@action('heaserver-settings-settings-object-get-actual', rel='hea-actual', path='{+actual_object_uri}')
async def get_all_settings_objects(request: web.Request) -> web.Response:
    """
    Gets all settings objects.
    :param request: the HTTP request.
    :return: all settings objects.
    ---
    summary: All settings objects.
    tags:
        - heaserver-settings
    responses:
      '200':
        $ref: '#/components/responses/200'
    """
    logger = logging.getLogger(__name__)
    sub = request.headers.get(SUB, NONE_USER)
    obj_dicts = await mongoservicelib.get_all_dict(request, MONGODB_SETTINGS_COLLECTION)
    logger.debug('settings objects in the database: %s', obj_dicts)
    missing = set(DEFAULT_SETTINGS_OBJECT_TEMPLATES.keys()).difference(obj_dict.get('name') for obj_dict in obj_dicts)
    if missing:
        obj_dicts_ = list(obj_dicts)
        for m in missing:
            if m in DEFAULT_SETTINGS_OBJECT_TEMPLATES:
                obj_dict = DEFAULT_SETTINGS_OBJECT_TEMPLATES.get(m)
                assert obj_dict is not None, 'obj_dict cannot be None'
                if (actual_object_type_name := obj_dict['actual_object_type_name']) is None:
                    raise ValueError('actual_object_type_name in obj_dict cannot be None')
                component = await client.get_component(request.app, str(actual_object_type_name))
                assert component is not None, 'component cannot be None'
                assert component.base_url is not None, 'component.base_url cannot be None'
                if (actual_object_uri := obj_dict['actual_object_uri']) is None:
                    raise ValueError('actual_object_uri in obj_dict cannot be None')
                if await client.has(request.app, URL(component.base_url) / str(actual_object_uri), headers={SUB: sub}):
                    settings_obj_dict = await _default_settings_object_by_name(request, m)
                    assert settings_obj_dict is not None, 'settings_obj_dict cannot be None'
                    obj_dicts_.append(settings_obj_dict)
    else:
        obj_dicts_ = obj_dicts
    objs: list[SettingsObject] = []
    context = PermissionContext(sub)
    for obj_dict in obj_dicts_:
        obj = SettingsObject()
        obj.from_dict(obj_dict)
        assert obj.actual_object_type_name is not None, 'obj.actual_object_type_name cannot be None'
        resource_url = await type_to_resource_url(request, obj.actual_object_type_name)
        # Change to use obj.actual_object_uri in the future after the resource metadata is changed.
        logger.debug('Checking resource URL %s and id %s', resource_url, obj.actual_object_id)
        assert obj.actual_object_id is not None, 'obj.actual_object_id cannot be None'
        if await client.has(request.app, URL(resource_url) / obj.actual_object_id, headers={SUB: sub}):
            objs.append(obj)
    return await response.get_all(request, [to_dict(obj) for obj in objs],
                                  permissions=[await obj.get_permissions(context) for obj in objs],
                                  attribute_permissions=[await obj.get_all_attribute_permissions(context) for obj in objs])


@routes.post('/settings')
@routes.post('/settings/')
async def post_settings_object(request: web.Request) -> web.Response:
    """
    Posts the provided settings object.
    :param request: the HTTP request.
    :return: a Response object with a status of Created and the object's URI in the Location header.
    ---
    summary: Settings object creation
    tags:
        - heaserver-settings
    requestBody:
      description: A new settings object.
      required: true
      content:
        application/vnd.collection+json:
          schema:
            type: object
          examples:
            example:
              summary: Settings object example
              value: {
                "template": {
                  "data": [{
                    "name": "created",
                    "value": null
                  },
                  {
                    "name": "derived_by",
                    "value": null
                  },
                  {
                    "name": "derived_from",
                    "value": []
                  },
                  {
                    "name": "description",
                    "value": null
                  },
                  {
                    "name": "display_name",
                    "value": "Joe"
                  },
                  {
                    "name": "modified",
                    "value": null
                  },
                  {
                    "name": "name",
                    "value": "joe"
                  },
                  {
                    "name": "owner",
                    "value": "system|none"
                  },
                  {
                    "name": "shares",
                    "value": []
                  },
                  {
                    "name": "source",
                    "value": null
                  },
                  {
                    "name": "type",
                    "value": "heaobject.settings.SettingsObject"
                  }]
                }
              }
        application/json:
          schema:
            type: object
          examples:
            example:
              summary: Settings object example
              value: {
                "created": null,
                "derived_by": null,
                "derived_from": [],
                "description": null,
                "display_name": "Joe",
                "modified": null,
                "name": "joe",
                "owner": "system|none",
                "shares": [],
                "source": null,
                "type": "heaobject.settings.SettingsObject"
              }
    responses:
      '201':
        $ref: '#/components/responses/201'
      '400':
        $ref: '#/components/responses/400'
      '404':
        $ref: '#/components/responses/404'
    """
    return await mongoservicelib.post(request, MONGODB_SETTINGS_COLLECTION, SettingsObject)


@routes.put('/settings/{id}')
async def put_settings_object(request: web.Request) -> web.Response:
    """
    Updates the settings object with the specified id.
    :param request: the HTTP request.
    :return: a Response object with a status of No Content or Not Found.
    ---
    summary: Settings object updates
    tags:
        - heaserver-settings
    parameters:
        - $ref: '#/components/parameters/id'
    requestBody:
      description: An updated settings object.
      required: true
      content:
        application/vnd.collection+json:
          schema:
            type: object
          examples:
            example:
              summary: Settings object example
              value: {
                "template": {
                  "data": [{
                    "name": "created",
                    "value": null
                  },
                  {
                    "name": "derived_by",
                    "value": null
                  },
                  {
                    "name": "derived_from",
                    "value": []
                  },
                  {
                    "name": "description",
                    "value": null
                  },
                  {
                    "name": "display_name",
                    "value": "Reximus Max"
                  },
                  {
                    "name": "modified",
                    "value": null
                  },
                  {
                    "name": "name",
                    "value": "reximus"
                  },
                  {
                    "name": "owner",
                    "value": "system|none"
                  },
                  {
                    "name": "shares",
                    "value": []
                  },
                  {
                    "name": "source",
                    "value": null
                  },
                  {
                    "name": "version",
                    "value": null
                  },
                  {
                    "name": "base_url",
                    "value": "http://localhost/foo"
                  },
                  {
                    "section": "resources",
                    "index": 0,
                    "name": "resource_type_name",
                    "value": "heaobject.folder.Folder",
                  },
                  {
                    "section": "resources",
                    "index": 0,
                    "name": "type",
                    "value": "heaobject.registry.Resource",
                  },
                  {
                    "section": "resources",
                    "index": 0,
                    "name": "base_path",
                    "value": "/folders"
                  },
                  {
                   "section": "resources",
                    "index": 0,
                    "name": "file_system_name",
                    "value": "DEFAULT_MONGODB"
                  },
                  {
                  "name": "id",
                  "value": "666f6f2d6261722d71757578"
                  },
                  {
                  "name": "type",
                  "value": "heaobject.settings.SettingsObject"
                  }]
                }
              }
        application/json:
          schema:
            type: object
          examples:
            example:
              summary: Settings object example
              value: {
                "id": "666f6f2d6261722d71757578",
                "created": null,
                "derived_by": null,
                "derived_from": [],
                "description": null,
                "display_name": "Reximus Max",
                "modified": null,
                "name": "reximus",
                "owner": "system|none",
                "shares": [],
                "source": null,
                "type": "heaobject.settings.SettingsObject",
                "version": null,
                "base_url": "http://localhost/foo",
                "resources": [{
                    "type": "heaobject.registry.Resource",
                    "resource_type_name": "heaobject.folder.Folder",
                    "base_path": "/folders",
                    "file_system_name": "DEFAULT_MONGODB"
                }]
              }
    responses:
      '204':
        $ref: '#/components/responses/204'
      '400':
        $ref: '#/components/responses/400'
      '404':
        $ref: '#/components/responses/404'
    """
    return await mongoservicelib.put(request, MONGODB_SETTINGS_COLLECTION, SettingsObject)


@routes.delete('/settings/{id}')
async def delete_settings_object(request: web.Request) -> web.Response:
    """
    Deletes the settings object with the specified id.
    :param request: the HTTP request.
    :return: No Content or Not Found.
    ---
    summary: Settings object deletion
    tags:
        - heaserver-settings
    parameters:
        - $ref: '#/components/parameters/id'
    responses:
      '204':
        $ref: '#/components/responses/204'
      '404':
        $ref: '#/components/responses/404'
    """
    return await mongoservicelib.delete(request, MONGODB_SETTINGS_COLLECTION)


@routes.get('/settings/{id}/opener')
@action('heaserver-settings-settings-object-open', rel=f'hea-opener hea-default', path='{+actual_object_uri}')
async def get_settings_object_opener(request: web.Request) -> web.Response:
    """
    Gets a settings object with a default link to open it, if the format in the Accept header supports links.

    :param request: the HTTP Request.
    :return: A Response object with a status of Multiple Choices or Not Found.
    ---
    summary: Settings object opener choices
    tags:
        - heaserver-settings
    parameters:
        - $ref: '#/components/parameters/id'
    responses:
      '300':
        $ref: '#/components/responses/300'
      '404':
        $ref: '#/components/responses/404'
    """
    return await _get_settings_object(request)



def start_with(config: Configuration) -> None:
    start(package_name='heaserver-settings', db=mongo.MongoManager,
          wstl_builder_factory=builder_factory(__package__), config=config)

async def _default_settings_object_by_name(request: web.Request, name: str) -> DesktopObjectDict | None:
    obj_dict = deepcopy(DEFAULT_SETTINGS_OBJECT_TEMPLATES.get(name))
    if obj_dict is not None:
        obj: SettingsObject = SettingsObject()
        obj.from_dict(obj_dict)
        obj.user = request.headers.get(SUB, NONE_USER)
        obj.user_shares[0].user = obj.user
        obj_dict_ = to_dict(obj)
        id_ = await request.app[HEA_DB].insert_admin(obj_dict_, MONGODB_SETTINGS_COLLECTION)
        if id_ is None:
            raise IOError('Failed to insert default settings object into database')
        else:
            obj_dict_['id'] = id_
            obj_dict_['instance_id'] = f'{obj.type}^{id_}'
            return obj_dict_
    else:
        return None


async def _get_settings_object(request: web.Request) -> web.Response:
    sub = request.headers.get(SUB, NONE_USER)
    obj_dict = await mongoservicelib.get_dict(request, MONGODB_SETTINGS_COLLECTION)
    if obj_dict is None:
        obj_dict = await _default_settings_object_by_name(request, request.match_info['id'])
        if obj_dict is None:
            return await response.get(request, None)
    obj = SettingsObject()
    obj.from_dict(obj_dict)
    context = PermissionContext(sub)
    return await response.get(request, to_dict(obj),
                              permissions=await obj.get_permissions(context),
                              attribute_permissions=await obj.get_all_attribute_permissions(context))
