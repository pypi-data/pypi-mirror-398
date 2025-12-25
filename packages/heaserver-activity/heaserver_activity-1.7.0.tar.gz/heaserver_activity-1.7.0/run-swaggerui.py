#!/usr/bin/env python3

from heaserver.activity import service
from heaserver.service.testcase import swaggerui
from heaserver.service.wstl import builder_factory
from aiohttp.web import get
from integrationtests.heaserver.activityintegrationtest.testcase import db_store
import logging

logging.basicConfig(level=logging.DEBUG)

if __name__ == '__main__':
    swaggerui.run(project_slug='heaserver-activity', desktop_objects=db_store,
                  wstl_builder_factory=builder_factory(service.__package__),
                  routes=[
                      (get, '/desktopobjectactions/{id}', service.get_desktop_object_action),
                      (get, '/desktopobjectactions/byname/{name}', service.get_desktop_object_action_by_name),
                      (get, '/desktopobjectactions/', service.get_all_desktop_object_actions),
                      (get, '/recentlyaccessedviews/bytype/{type}', service.get_recently_accessed)
                  ])
