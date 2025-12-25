#!/usr/bin/env python3

from heaserver.settings import service
from heaserver.service.testcase import swaggerui
from heaserver.service.wstl import builder_factory
from integrationtests.heaserver.settingsintegrationtest.settingsobjecttestcase import db_store
from aiohttp.web import get, delete, post, put, view
import logging


logging.basicConfig(level=logging.DEBUG)

if __name__ == '__main__':
    swaggerui.run(project_slug='heaserver-settings', desktop_objects=db_store,
                  wstl_builder_factory=builder_factory(service.__package__),
                  routes=[(get, '/settings/{id}', service.get_settings_object),
                          (get, '/settings/byname/{name}', service.get_settings_object_by_name),
                          (get, '/settings/', service.get_all_settings_objects),
                          (post, '/settings', service.post_settings_object),
                          (put, '/settings/{id}', service.put_settings_object),
                          (delete, '/settings/{id}', service.delete_settings_object),
                          (get, '/settings/{id}/opener', service.get_settings_object_opener)
                          ])
