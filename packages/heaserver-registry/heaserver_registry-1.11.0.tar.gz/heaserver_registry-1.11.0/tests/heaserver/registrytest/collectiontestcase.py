"""
Creates a test case class for use with the unittest library that is build into Python.
"""

from heaserver.service.testcase.microservicetestcase import get_test_case_cls_default
from heaserver.registry import service
from heaobject.user import NONE_USER, TEST_USER, ALL_USERS
from heaobject.root import Permission, ShareImpl
from heaobject.folder import Folder, Item
from heaobject.volume import DEFAULT_FILE_SYSTEM, MongoDBFileSystem
from heaobject.registry import Resource, Collection
from heaserver.service.testcase.expectedvalues import Action

db_store = {
    service.MONGODB_COLLECTION_COLLECTION: [{
        'id': Item.get_type_name(),
        'instance_id': f'{Collection.get_type_name()}^{Item.get_type_name()}',
        'created': None,
        'derived_by': None,
        'derived_from': [],
        'description': None,
        'display_name': Item.get_type_name(),
        'invites': [],
        'modified': None,
        'name': Item.get_type_name(),
        'owner': NONE_USER,
        'shares': [{
            'user': ALL_USERS,
            'permissions': [Permission.VIEWER.name],
            'type': ShareImpl.get_type_name(),
            'invite': None,
            'type_display_name': 'Share',
            'group': NONE_USER,
            'basis': 'USER'
        }],
        'user_shares': [{
            'user': ALL_USERS,
            'permissions': [Permission.VIEWER.name],
            'type': ShareImpl.get_type_name(),
            'invite': None,
            'type_display_name': 'Share',
            'group': NONE_USER,
            'basis': 'USER'
        }],
        'group_shares': [],
        'source': None,
        'source_detail': None,
        'type': Collection.get_type_name(),
        'url': 'folders',
        'mime_type': 'application/x.collection',
        'collection_type_name': Item.get_type_name(),
        'file_system_name': DEFAULT_FILE_SYSTEM,
        'file_system_type': MongoDBFileSystem.get_type_name(),
        'type_display_name': 'Collection',
        'super_admin_default_permissions': [Permission.VIEWER.name, Permission.EDITOR.name, Permission.CREATOR.name],
        'display_in_system_menu': False,
        'display_in_user_menu': False,
        'dynamic_permission_supported': False
    },
        {
            'id': Folder.get_type_name(),
            'instance_id': f'{Collection.get_type_name()}^{Folder.get_type_name()}',
            'created': None,
            'derived_by': None,
            'derived_from': [],
            'description': None,
            'display_name': Folder.get_type_name(),
            'invites': [],
            'modified': None,
            'name': Folder.get_type_name(),
            'owner': NONE_USER,
            'shares': [{
                'user': ALL_USERS,
                'permissions': [Permission.VIEWER.name],
                'type': ShareImpl.get_type_name(),
                'invite': None,
                'type_display_name': 'Share',
                'group': NONE_USER,
                'basis': 'USER'
            }],
            'user_shares': [{
                'user': ALL_USERS,
                'permissions': [Permission.VIEWER.name],
                'type': ShareImpl.get_type_name(),
                'invite': None,
                'type_display_name': 'Share',
                'group': NONE_USER,
                'basis': 'USER'
            }],
            'group_shares': [],
            'source': None,
            'source_detail': None,
            'type': Collection.get_type_name(),
            'url': 'folders',
            'mime_type': 'application/x.collection',
            'collection_type_name': Folder.get_type_name(),
            'file_system_name': DEFAULT_FILE_SYSTEM,
            'file_system_type': MongoDBFileSystem.get_type_name(),
            'type_display_name': 'Collection',
            'super_admin_default_permissions': [Permission.VIEWER.name, Permission.EDITOR.name, Permission.CREATOR.name],
            'display_in_system_menu': False,
            'display_in_user_menu': False,
            'dynamic_permission_supported': False
        }],
        service.MONGODB_COMPONENT_COLLECTION: [
        {
            'id': '0123456789ab0123456789ab',
            'created': None,
            'derived_by': None,
            'derived_from': [],
            'description': None,
            'display_name': 'Luximus',
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
            'user_shares': [{
                'type': 'heaobject.root.ShareImpl',
                'invite': None,
                'user': TEST_USER,
                'permissions': [Permission.COOWNER.name],
                'group': NONE_USER,
                'basis': 'USER'
            }],
            'group_shares': [],
            'source': None,
            'type': 'heaobject.registry.Component',
            'base_url': 'http://localhost/foo',
            'external_base_url': None,
            'resources': [{
                'type': Resource.get_type_name(),
                'resource_type_name': Item.get_type_name(),
                'base_path': 'folders',
                'file_system_name': DEFAULT_FILE_SYSTEM,
                'file_system_type': MongoDBFileSystem.get_type_name(),
                'resource_collection_type_display_name': Item.get_type_name(),
                'collection_accessor_users': [ALL_USERS],
                'creator_users': [],
                'default_shares': [],
                'collection_accessor_groups': [],
                'creator_groups': [],
                'display_in_system_menu': False,
                'display_in_user_menu': False,
                'collection_mime_type': 'application/x.collection'
            }],
            'super_admin_default_permissions': [Permission.VIEWER.name, Permission.EDITOR.name],
            'dynamic_permission_supported': False
        },
        {
            'id': '666f6f2d6261722d71757578',
            'created': None,
            'derived_by': None,
            'derived_from': [],
            'description': None,
            'display_name': 'Reximus',
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
            'user_shares': [{
                'type': 'heaobject.root.ShareImpl',
                'invite': None,
                'user': TEST_USER,
                'permissions': [Permission.VIEWER.name, Permission.EDITOR.name, Permission.DELETER.name],
                'group': NONE_USER,
                'basis': 'USER'
            }],
            'group_shares': [],
            'source': None,
            'type': 'heaobject.registry.Component',
            'base_url': 'http://localhost/foo',
            'external_base_url': None,
            'resources': [{
                'type': 'heaobject.registry.Resource',
                'resource_type_name': Folder.get_type_name(),
                'base_path': 'folders',
                'file_system_name': DEFAULT_FILE_SYSTEM,
                'file_system_name': DEFAULT_FILE_SYSTEM,
                'file_system_type': MongoDBFileSystem.get_type_name(),
                'resource_collection_type_display_name': Folder.get_type_name(),
                'collection_accessor_users': [ALL_USERS],
                'collection_accessor_groups': [],
                'creator_groups': [],
                'creator_users': [],
                'default_shares': [],
                'display_in_system_menu': False,
                'display_in_user_menu': False,
                'collection_mime_type': 'application/x.collection'
            }],
            'super_admin_default_permissions': [Permission.VIEWER.name, Permission.EDITOR.name],
            'dynamic_permission_supported': False
        }]}


CollectionTestCase = get_test_case_cls_default(coll=service.MONGODB_COLLECTION_COLLECTION,
                                               href='http://localhost:8080/collections/',
                                               wstl_package=service.__package__,
                                               fixtures=db_store,
                                               get_actions=[
                                                   Action(name='heaserver-registry-collection-get-properties',
                                                          rel=['hea-properties']),
                                                   Action(
                                                          name='heaserver-registry-collection-get-open-choices',
                                                          url='http://localhost:8080/collections/{id}/opener',
                                                          rel=['hea-opener-choices']),
                                                   Action(name='heaserver-registry-collection-get-self',
                                                          url='http://localhost:8080/collections/{id}',
                                                          rel=['self', 'hea-self-container'])],
                                               get_all_actions=[
                                                   Action(name='heaserver-registry-collection-get-properties',
                                                          rel=['hea-properties']),
                                                   Action(name='heaserver-registry-collection-get-open-choices',
                                                          url='http://localhost:8080/collections/{id}/opener',
                                                          rel=['hea-opener-choices']),
                                                   Action(name='heaserver-registry-collection-get-self',
                                                          url='http://localhost:8080/collections/{id}',
                                                          rel=['self', 'hea-self-container'])],
                                               sub=TEST_USER)
