"""
Creates a test case class for use with the unittest library that is build into Python.
"""

from heaserver.service.testcase.microservicetestcase import get_test_case_cls_default
from heaserver.registry import service
from heaobject.user import NONE_USER, TEST_USER
from heaobject.root import Permission
from heaserver.service.testcase.expectedvalues import Action

db_store = {
    service.MONGODB_COMPONENT_COLLECTION: [{
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
            'resource_collection_type_display_name': 'heaobject.folder.Folder'
        }],
        'super_admin_default_permissions': [Permission.VIEWER.name, Permission.EDITOR.name],
        'dynamic_permission_supported': False
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
                'permissions': [Permission.VIEWER.name]
            }],
            'user_shares': [{
                'type': 'heaobject.root.ShareImpl',
                'invite': None,
                'user': TEST_USER,
                'permissions': [Permission.VIEWER.name]
            }],
            'group_shares': [],
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
                'resource_collection_type_display_name': 'heaobject.folder.Item'
            }],
            'super_admin_default_permissions': [Permission.VIEWER.name, Permission.EDITOR.name],
            'dynamic_permission_supported': False
        }]}


ComponentPermissionsTestCase = \
    get_test_case_cls_default(coll=service.MONGODB_COMPONENT_COLLECTION,
                              href='http://localhost:8080/components',
                              wstl_package=service.__package__,
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
                              duplicate_action_name='heaserver-registry-component-duplicate-form',
                              put_content_status=404,
                              sub=TEST_USER)
