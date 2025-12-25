#!/usr/bin/env python3

from heaserver.keychain import service
from heaserver.service.testcase import swaggerui
from heaserver.service.wstl import builder_factory
from integrationtests.heaserver.keychainintegrationtest.testcase import db_store
from aiohttp.web import get, post, put, delete
import logging

logging.basicConfig(level=logging.DEBUG)

if __name__ == '__main__':
    swaggerui.run(project_slug='heaserver-keychain', desktop_objects=db_store,
                  wstl_builder_factory=builder_factory(service.__package__),
                  routes=[(get, '/credentials/{id}', service.get_credentials),
                          (get, '/credentials/byname/{name}', service.get_credentials_by_name),
                          (get, '/credentials/', service.get_all_credentials),
                          (post, '/credentials/', service.post_credentials),
                          (post, '/credentials/{id}/managedawscredential', service.post_aws_credentials_form),
                          (put, '/credentials/{id}', service.put_credentials),
                          (delete, '/credentials/{id}', service.delete_credentials)])
