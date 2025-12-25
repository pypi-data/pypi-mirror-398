"""
Creates a test case class for use with the unittest library that is build into Python.
"""

from heaserver.service.testcase.microservicetestcase import get_test_case_cls_default
from heaserver.registry import service
from heaobject.user import NONE_USER, TEST_USER, ALL_USERS
from heaobject.root import Permission, ShareImpl
from heaobject.folder import Folder, Item
from heaobject.volume import DEFAULT_FILE_SYSTEM, MongoDBFileSystem
from heaobject.registry import Collection
from heaserver.service.testcase.expectedvalues import Action
from heaserver.service.testcase.dockermongo import DockerMongoManager, DockerMongoManagerWithNoDatabaseManager
from heaserver.service.db.database import NoDatabaseManager
from heaserver.service.testcase.collection import CollectionKey

db_store = {
    CollectionKey(name=service.MONGODB_COLLECTION_COLLECTION, db_manager_cls=NoDatabaseManager): [{
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
            'type_display_name': 'Share'
        }],
        'source': None,
        'source_detail': None,
        'type': 'heaobject.registry.Collection',
        'url': 'folders',
        'mime_type': 'application/x.collection',
        'collection_type_name': Item.get_type_name(),
        'file_system_name': DEFAULT_FILE_SYSTEM,
        'file_system_type': MongoDBFileSystem.get_type_name(),
        'type_display_name': 'Collection'
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
                'type_display_name': 'Share'
            }],
            'source': None,
            'source_detail': None,
            'type': 'heaobject.registry.Collection',
            'url': 'folders',
            'mime_type': 'application/x.collection',
            'collection_type_name': Folder.get_type_name(),
            'file_system_name': DEFAULT_FILE_SYSTEM,
            'file_system_type': MongoDBFileSystem.get_type_name(),
            'type_display_name': 'Collection'
        }],
        CollectionKey(name=service.MONGODB_COMPONENT_COLLECTION, db_manager_cls=DockerMongoManager): [
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
                'permissions': [Permission.COOWNER.name]
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
                'file_system_name': 'DEFAULT_FILE_SYSTEM',
                'resource_collection_type_display_name': 'heaobject.folder.Item',
                'collection_accessor_users': [ALL_USERS],
                'creator_users': [],
                'default_shares': []
            }]
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
                'permissions': [Permission.VIEWER.name, Permission.EDITOR.name, Permission.DELETER.name]
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
                'resource_collection_type_display_name': 'heaobject.folder.Folder',
                'collection_accessor_users': [ALL_USERS],
                'creator_users': [],
                'default_shares': []
            }]
        }]}


CollectionTestCase = get_test_case_cls_default(coll=service.MONGODB_COLLECTION_COLLECTION,
                                               href='http://localhost:8080/collections/',
                                               wstl_package=service.__package__,
                                               fixtures=db_store,
                                               db_manager_cls=DockerMongoManagerWithNoDatabaseManager,
                                               get_actions=[
                                                   Action(name='heaserver-registry-collection-get-properties',
                                                          rel=['hea-properties']),
                                                   Action(
                                                          name='heaserver-registry-collection-get-open-choices',
                                                          url='http://localhost:8080/collections/{id}/opener',
                                                          rel=['hea-opener-choices']),
                                                   Action(name='heaserver-registry-collection-get-self',
                                                          url='http://localhost:8080/collections/{id}',
                                                          rel=['self'])],
                                               get_all_actions=[
                                                   Action(name='heaserver-registry-collection-get-properties',
                                                          rel=['hea-properties']),
                                                   Action(
                                                          name='heaserver-registry-collection-get-open-choices',
                                                          url='http://localhost:8080/collections/{id}/opener',
                                                          rel=['hea-opener-choices']),
                                                   Action(name='heaserver-registry-collection-get-self',
                                                          url='http://localhost:8080/collections/{id}',
                                                          rel=['self'])],
                                               sub=TEST_USER)
