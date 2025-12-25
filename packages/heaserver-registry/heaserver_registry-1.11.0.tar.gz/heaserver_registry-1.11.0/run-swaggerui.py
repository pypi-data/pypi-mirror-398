#!/usr/bin/env python3

from heaserver.registry import service
from heaserver.service.testcase import swaggerui
from heaserver.service.wstl import builder_factory
from integrationtests.heaserver.registryintegrationtest.componenttestcase import db_store_2 as components
from heaobject.user import NONE_USER
from aiohttp.web import get, delete, post, put, view
import logging


properties = {
    service.MONGODB_PROPERTIES_COLLECTION: [{
        'id': '666f6f2d6261722d71757578',
        'display_name': 'Application Name',
        'name': 'applicationName',
        'value': 'HEA',
        'owner': NONE_USER,
        'type': 'heaobject.registry.Property'
    },
        {
            'id': '0123456789ab0123456789ab',
            'display_name': 'Foo Bar',
            'modified': None,
            'name': 'fooBar',
            'value': 'foobar',
            'owner': NONE_USER,
            'type': 'heaobject.registry.Property'
        }]}


logging.basicConfig(level=logging.DEBUG)

logging.debug(components | properties)

if __name__ == '__main__':
    swaggerui.run(project_slug='heaserver-registry', desktop_objects=components | properties,
                  wstl_builder_factory=builder_factory(service.__package__),
                  routes=[(get, '/components/{id}', service.get_component),
                          (get, '/components/byname/{name}', service.get_component_by_name),
                          (get,
                           '/components/bytype/{type}/byfilesystemtype/{filesystemtype}/byfilesystemname/{filesystemname}',
                           service.get_component_by_type),
                          (get, '/components/', service.get_all_components),
                          (get, '/components/{id}/duplicator', service.get_component_duplicator),
                          (post, '/components', service.post_component),
                          (post, '/components/duplicator', service.post_component_duplicator),
                          (put, '/components/{id}', service.put_component),
                          (delete, '/components/{id}', service.delete_component),
                          (get, '/properties/{id}', service.get_property),
                          (get, '/properties/byname/{name}', service.get_property_by_name),
                          (get, '/properties/', service.get_all_properties),
                          (post, '/properties', service.post_property),
                          (put, '/properties/{id}', service.put_property),
                          (delete, '/properties/{id}', service.delete_property),
                          (get, '/collections/{id}', service.get_collection),
                          (get, '/collections/', service.get_all_collections),
                          (get, '/collections/byname/{name}', service.get_collection_by_name),
                          (get, '/collections/{id}/opener', service.get_collection_opener)
                          ])
