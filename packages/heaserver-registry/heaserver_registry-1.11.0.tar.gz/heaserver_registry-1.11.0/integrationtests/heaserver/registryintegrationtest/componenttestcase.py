"""
Creates a test case class for use with the unittest library that is build into Python.
"""

from heaserver.service.testcase.microservicetestcase import get_test_case_cls_default
from heaserver.service.testcase.dockermongo import MockDockerMongoManager
from heaserver.registry import service
from heaobject.user import NONE_USER, TEST_USER, ALL_USERS
from heaobject.root import Permission
from heaobject.registry import Component
from heaserver.service.testcase.expectedvalues import Action

db_store = {
    service.MONGODB_COMPONENT_COLLECTION: [{
        'id': '666f6f2d6261722d71757578',
        'instance_id': f'{Component.get_type_name()}^666f6f2d6261722d71757578',
        'created': '2022-05-17T00:00:00+00:00',
        'derived_by': None,
        'derived_from': [],
        'description': None,
        'display_name': 'Reximus',
        'invites': [],
        'modified': '2022-05-17T00:00:00+00:00',
        'name': 'reximus',
        'owner': NONE_USER,
        'shares': [],
        'source': None,
        'source_detail': None,
        'type': 'heaobject.registry.Component',
        'base_url': 'http://localhost/foo',
        'external_base_url': None,
        'resources': [{
            'type': 'heaobject.registry.Resource',
            'resource_type_name': 'heaobject.folder.Folder',
            'base_path': 'folders',
            'file_system_name': 'DEFAULT_FILE_SYSTEM',
            'file_system_type': 'heaobject.volume.DefaultFileSystem',
            'resource_collection_type_display_name': 'heaobject.folder.Folder',
            'collection_accessor_users': [ALL_USERS],
            'collection_accessor_groups': [],
            'creator_groups': [],
            'creator_users': [],
            'default_shares': [],
            'type_display_name': 'Resource',
            'manages_creators': False
        }],
        'type_display_name': 'Registry Component'
    },
        {
            'id': '0123456789ab0123456789ab',
            'instance_id': f'{Component.get_type_name()}^0123456789ab0123456789ab',
            'created': '2022-05-17T00:00:00+00:00',
            'derived_by': None,
            'derived_from': [],
            'description': None,
            'display_name': 'Luximus',
            'invites': [],
            'modified': '2022-05-17T00:00:00+00:00',
            'name': 'luximus',
            'owner': NONE_USER,
            'shares': [],
            'source': None,
            'source_detail': None,
            'type': 'heaobject.registry.Component',
            'base_url': 'http://localhost/foo',
            'external_base_url': None,
            'resources': [{
                'type': 'heaobject.registry.Resource',
                'resource_type_name': 'heaobject.folder.Item',
                'base_path': 'folders',
                'file_system_name': 'DEFAULT_FILE_SYSTEM',
                'file_system_type': 'heaobject.volume.DefaultFileSystem',
                'resource_collection_type_display_name': 'heaobject.folder.Item',
                'collection_accessor_users': [ALL_USERS],
                'collection_accessor_groups': [],
                'creator_groups': [],
                'creator_users': [],
                'default_shares': [],
                'type_display_name': 'Resource',
                'manages_creators': False
            }],
            'type_display_name': 'Registry Component'
        }]}

db_store_2 = {
    service.MONGODB_COMPONENT_COLLECTION: [
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
                'permissions': [Permission.COOWNER.name],
                'group': NONE_USER,
                'basis': 'USER'
            }],
            'source': None,
            'source_detail': None,
            'type': 'heaobject.registry.Component',
            'base_url': 'http://localhost/foo',
            'external_base_url': None,
            'resources': [{
                'type': 'heaobject.registry.Resource',
                'resource_type_name': 'heaobject.folder.Item',
                'base_path': 'folders',
                'resource_collection_type_display_name': 'heaobject.folder.Item',
                'collection_accessor_users': [ALL_USERS],
                'collection_accessor_groups': [],
                'creator_users': [],
                'creator_groups': [],
                'default_shares': [],
                'type_display_name': 'Resource'
            }],
            'type_display_name': 'Registry Component'
        },
        {
            'id': '666f6f2d6261722d71757578',
            'created': None,
            'derived_by': None,
            'derived_from': ['foo', 'bar'],
            'description': None,
            'display_name': 'Reximus',
            'invites': [],
            'modified': None,
            'name': 'reximus',
            'owner': NONE_USER,
            'shares': [{
                'type': 'heaobject.root.ShareImpl',
                'invite': None,
                'user': TEST_USER,
                'permissions': [Permission.VIEWER.name, Permission.EDITOR.name, Permission.DELETER.name],
                'group': NONE_USER,
                'basis': 'USER'
            }],
            'source': None,
            'source_detail': None,
            'type': 'heaobject.registry.Component',
            'base_url': 'http://localhost/foo',
            'external_base_url': None,
            'resources': [{
                'type': 'heaobject.registry.Resource',
                'resource_type_name': 'heaobject.folder.Folder',
                'base_path': 'folders',
                'file_system_name': 'DEFAULT_FILE_SYSTEM',
                'file_system_type': 'heaobject.volume.MongoDBFileSystem',
                'resource_collection_type_display_name': 'heaobject.folder.Folder',
                'collection_accessor_users': [ALL_USERS],
                'collection_accessor_groups': [],
                'creator_groups': [],
                'creator_users': [],
                'default_shares': [],
                'type_display_name': 'Resource'
            }],
            'type_display_name': 'Registry Component'
        }]}

ComponentTestCase = get_test_case_cls_default(coll=service.MONGODB_COMPONENT_COLLECTION,
                                              href='http://localhost:8080/components/',
                                              wstl_package=service.__package__,
                                              db_manager_cls=MockDockerMongoManager,
                                              fixtures=db_store,
                                              get_actions=[
                                                  Action(name='heaserver-registry-component-get-properties',
                                                         rel=['hea-properties']),
                                                  Action(name='heaserver-registry-component-get-self',
                                                         url='http://localhost:8080/components/{id}',
                                                         rel=['self'])],
                                              get_all_actions=[
                                                  Action(name='heaserver-registry-component-get-properties',
                                                         rel=['hea-properties']),
                                                  Action(name='heaserver-registry-component-get-self',
                                                         url='http://localhost:8080/components/{id}',
                                                         rel=['self'])],
                                              duplicate_action_name='heaserver-registry-component-duplicate-form')

ComponentTestCase2 = get_test_case_cls_default(coll=service.MONGODB_COMPONENT_COLLECTION,
                                               href='http://localhost:8080/components/',
                                               wstl_package=service.__package__,
                                               db_manager_cls=MockDockerMongoManager,
                                               fixtures=db_store_2,
                                               get_actions=[
                                                   Action(name='heaserver-registry-component-get-properties',
                                                          rel=['hea-properties']),
                                                   Action(name='heaserver-registry-component-get-self',
                                                         url='http://localhost:8080/components/{id}',
                                                         rel=['self'])
                                               ],
                                               get_all_actions=[
                                                   Action(name='heaserver-registry-component-get-properties',
                                                          rel=['hea-properties']),
                                                   Action(name='heaserver-registry-component-get-self',
                                                         url='http://localhost:8080/components/{id}',
                                                         rel=['self'])],
                                               duplicate_action_name='heaserver-registry-component-duplicate-form',
                                               sub=TEST_USER)
