from .componenttestcase import ComponentTestCase, ComponentTestCase2
from .collectiontestcase import CollectionTestCase
from heaserver.service.testcase.mixin import GetOneMixin, GetAllMixin, PostMixin, PutMixin, DeleteMixin, _ordered
from heaserver.service.oidcclaimhdrs import SUB
from heaserver.service.db.database import get_collection_key_from_name
from heaserver.service.representor import nvpjson
from heaobject.user import NONE_USER
from heaobject.root import copy_heaobject_dict_with, Permission
from aiohttp import hdrs


class TestGetComponent(ComponentTestCase, GetOneMixin):
    pass


class TestGetAllComponents(ComponentTestCase, GetAllMixin):
    pass


class TestPostComponent(ComponentTestCase, PostMixin):

    async def test_post_status_invalid_base_url(self):
        await self._test_invalid({"base_url": 2})

    async def test_post_status_invalid_resource(self):
        await self._test_invalid({"resources": [2]})

    async def test_post_status_invalid_resources_list(self):
        await self._test_invalid({"resources": 2})


class TestPutComponent(ComponentTestCase, PutMixin):

    async def test_put_status_invalid_base_url(self):
        await self._test_invalid({"base_url": 2})

    async def test_put_status_invalid_resource(self):
        await self._test_invalid({"resources": [2]})


class TestDeleteComponent(ComponentTestCase, DeleteMixin):
    pass


class TestGetResource(ComponentTestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._headers = {SUB: NONE_USER, hdrs.X_FORWARDED_HOST: "localhost:8080"}
        desktop_objects = getattr(self, "_MicroserviceTestCase__desktop_objects")
        coll = get_collection_key_from_name(desktop_objects, self._coll)
        del desktop_objects[coll][0]["resources"][0]["file_system_type"]
        del desktop_objects[coll][1]["resources"][0]["file_system_name"]
        del desktop_objects[coll][1]["resources"][0]["file_system_type"]

    async def test_no_file_system(self):
        expected = [{"collection": {
            "version": "1.0",
            "href": "http://localhost:8080/components/bytype/heaobject.folder.Folder",
            "permissions": [[p.name for p in Permission.non_creator_permissions()]],
            "items": [{
                "data": [
                    {
                        "name": "id",
                        "value": "666f6f2d6261722d71757578",
                        "prompt": "id",
                        "display": False},
                    {
                        "name": "instance_id",
                        "value": "heaobject.registry.Component^666f6f2d6261722d71757578",
                        "prompt": "instance_id",
                        "display": True},
                    {
                        "name": "created",
                        "value": '2022-05-17T00:00:00+00:00',
                        "prompt": "created",
                        "display": True},
                    {
                        "name": "derived_by",
                        "value": None,
                        "prompt": "derived_by",
                        "display": True},
                    {
                        "name": "derived_from",
                        "value": [],
                        "prompt": "derived_from",
                        "display": True},
                    {
                        "name": "description",
                        "value": None,
                        "prompt": "description",
                        "display": True},
                    {
                        "name": "display_name",
                        "value": "Reximus",
                        "prompt": "display_name",
                        "display": True},
                    {
                        "name": "invites",
                        "prompt": "invites",
                        "value": [],
                        "display": True
                    },
                    {
                        "name": "shares",
                        "prompt": "shares",
                        "value": [],
                        "display": True
                    },
                    {
                        "name": "user_shares",
                        "prompt": "user_shares",
                        "value": [],
                        "display": True
                    },
                    {
                        "name": "group_shares",
                        "prompt": "group_shares",
                        "value": [],
                        "display": True
                    },
                    {
                        "name": "modified",
                        "value": '2022-05-17T00:00:00+00:00',
                        "prompt": "modified",
                        "display": True},
                    {
                        "name": "name",
                        "value": "reximus",
                        "prompt": "name",
                        "display": True},
                    {
                        "name": "owner",
                        "value": "system|none",
                        "prompt": "owner",
                        "display": True},
                    {
                        "name": "type",
                        "value": "heaobject.registry.Component",
                        "prompt": "type",
                        "display": True
                    },
                    {
                        "name": "source",
                        "value": None,
                        "prompt": "source",
                        "display": True
                    },
                    {
                        "name": "source_detail",
                        "value": None,
                        "prompt": "source_detail",
                        "display": True
                    },
                    {
                        "name": "base_url",
                        "value": "http://localhost/foo",
                        "prompt": "base_url",
                        "display": True
                    },
                    {
                        "name": "external_base_url",
                        "value": None,
                        "prompt": "external_base_url",
                        "display": True
                    },
                    {
                        "name": "type_display_name",
                        "value": "Registry Component",
                        "prompt": "type_display_name",
                        "display": True
                    },
                    {
                        "section": "resources",
                        "index": 0,
                        "name": "resource_type_name",
                        "value": "heaobject.folder.Folder",
                        "prompt":
                            "resource_type_name",
                        "display": True
                    },
                    {
                        "section": "resources",
                        "index": 0,
                        "name": "base_path",
                        "value": "folders",
                        "prompt": "base_path",
                        "display": True
                    },
                    {
                        "section": "resources",
                        "index": 0,
                        "name": "file_system_name",
                        "value": "DEFAULT_FILE_SYSTEM",
                        "prompt": "file_system_name",
                        "display": True
                    },
                    {
                        "section": "resources",
                        "index": 0,
                        "name": "type",
                        "value": "heaobject.registry.Resource",
                        "prompt": "type",
                        "display": True
                    },
                    {
                        "section": "resources",
                        "index": 0,
                        "name": "resource_collection_type_display_name",
                        "value": "heaobject.folder.Folder",
                        "prompt": "resource_collection_type_display_name",
                        "display": True
                    },
                    {
                        "display": True,
                        "index": 0,
                        "name": "collection_accessor_users",
                        "prompt": "collection_accessor_users",
                        "section": "resources",
                        "value": ["system|all"]
                    },
                    {
                        "display": True,
                        "index": 0,
                        "name": "collection_accessor_groups",
                        "prompt": "collection_accessor_groups",
                        "section": "resources",
                        "value": []
                    },
                    {
                        "display": True,
                        "index": 0,
                        "name": "creator_users",
                        "prompt": "creator_users",
                        "section": "resources",
                        "value": []
                    },
                    {
                        "display": True,
                        "index": 0,
                        "name": "creator_groups",
                        "prompt": "creator_groups",
                        "section": "resources",
                        "value": []
                    },
                    {
                        "display": True,
                        "index": 0,
                        "name": "default_shares",
                        "prompt": "default_shares",
                        "section": "resources",
                        "value": []
                    },
                    {
                        "section": "resources",
                        "index": 0,
                        "name": "file_system_type",
                        "value": "heaobject.volume.MongoDBFileSystem",
                        "prompt": "file_system_type",
                        "display": True
                    },
                    {
                        "section": "resources",
                        "index": 0,
                        "name": "type_display_name",
                        "value": "Resource",
                        "prompt": "type_display_name",
                        "display": True
                    },
                    {
                        "section": "resources",
                        "index": 0,
                        "name": "manages_creators",
                        "value": False,
                        "prompt": "manages_creators",
                        "display": True
                    },
                    {
                        "section": "resources",
                        "index": 0,
                        "name": "display_in_system_menu",
                        "value": False,
                        "prompt": "display_in_system_menu",
                        "display": True
                    },
                    {
                        "section": "resources",
                        "index": 0,
                        "name": "display_in_user_menu",
                        "value": False,
                        "prompt": "display_in_user_menu",
                        "display": True
                    },
                    {
                        "section": "resources",
                        "index": 0,
                        "name": "collection_mime_type",
                        "value": 'application/x.collection',
                        "prompt": "collection_mime_type",
                        "display": True
                    },
                    {'name': 'super_admin_default_permissions',
                     'value': [Permission.VIEWER.name, Permission.EDITOR.name],
                     'prompt': 'super_admin_default_permissions',
                     'display': True,
                    },
                    {
                        'name': 'dynamic_permission_supported',
                        'value': False,
                        'prompt': 'dynamic_permission_supported',
                        'display': True
                    }],
                "links": []}]}}]
        obj = await self.client.request("GET",
                                        (self._href / "bytype" / "heaobject.folder.Folder").path,
                                        headers=self._headers)
        self.assertEqual(_ordered(expected), _ordered(await obj.json()))

    async def test_no_file_system_status(self):
        obj = await self.client.request("GET",
                                        (self._href / "bytype" / "heaobject.folder.Folder").path,
                                        headers=self._headers)
        self.assertEqual(200, obj.status)

class TestGetResource2(ComponentTestCase2):
    _headers = {SUB: NONE_USER, hdrs.X_FORWARDED_HOST: "localhost:8080"}

    async def test_no_file_system(self):
        expected = [{"collection": {
            "version": "1.0",
            "href": "http://localhost:8080/components/bytype/heaobject.folder.Folder",
            "permissions": [[p.name for p in Permission.non_creator_permissions()]],
            "items": [{
                "data": [
                    {
                        "name": "id",
                        "value": "666f6f2d6261722d71757578",
                        "prompt": "id",
                        "display": False},
                    {
                        "name": "instance_id",
                        "value": "heaobject.registry.Component^666f6f2d6261722d71757578",
                        "prompt": "instance_id",
                        "display": True},
                    {
                        "name": "type_display_name",
                        "value": "Registry Component",
                        "prompt": "type_display_name",
                        "display": True
                    },
                    {
                        "name": "invites",
                        "value": [],
                        "prompt": "invites",
                        "display": True
                    },
                    {
                        "name": "external_base_url",
                        "value": None,
                        "prompt": "external_base_url",
                        "display": True
                    },
                    {
                        "name": "created",
                        "value": None,
                        "prompt": "created",
                        "display": True},
                    {
                        "name": "derived_by",
                        "value": None,
                        "prompt": "derived_by",
                        "display": True},
                    {
                        "name": "derived_from",
                        "value": [],
                        "prompt": "derived_from",
                        "display": True},
                    {
                        "name": "description",
                        "value": None,
                        "prompt": "description",
                        "display": True},
                    {
                        "name": "display_name",
                        "value": "Reximus",
                        "prompt": "display_name",
                        "display": True},
                    {
                        "name": "invite",
                        "index": 0,
                        "section": "shares",
                        "prompt": "invite",
                        "value": None,
                        "display": True
                    },
                    {
                        "name": "permissions",
                        "index": 0,
                        "section": "shares",
                        "prompt": "permissions",
                        "value": ["DELETER", "EDITOR", "VIEWER"],
                        "display": True
                    },
                    {
                        "name": "user",
                        "index": 0,
                        "section": "shares",
                        "prompt": "user",
                        "value": "system|test",
                        "display": True
                    },
                    {
                        "name": "group",
                        "index": 0,
                        "section": "shares",
                        "prompt": "group",
                        "value": "system|none",
                        "display": True
                    },
                    {
                        "name": "basis",
                        "index": 0,
                        "section": "shares",
                        "prompt": "basis",
                        "value": "USER",
                        "display": True
                    },
                    {
                        "name": "type",
                        "index": 0,
                        "section": "shares",
                        "prompt": "type",
                        "value": "heaobject.root.ShareImpl",
                        "display": True
                    },
                    {
                        "name": "type_display_name",
                        "index": 0,
                        "section": "shares",
                        "prompt": "type_display_name",
                        "value": "Share",
                        "display": True
                    },
                    {
                        "name": "invite",
                        "index": 0,
                        "section": "user_shares",
                        "prompt": "invite",
                        "value": None,
                        "display": True
                    },
                    {
                        "name": "permissions",
                        "index": 0,
                        "section": "user_shares",
                        "prompt": "permissions",
                        "value": ["DELETER", "EDITOR", "VIEWER"],
                        "display": True
                    },
                    {
                        "name": "user",
                        "index": 0,
                        "section": "user_shares",
                        "prompt": "user",
                        "value": "system|test",
                        "display": True
                    },
                    {
                        "name": "group",
                        "index": 0,
                        "section": "user_shares",
                        "prompt": "group",
                        "value": "system|none",
                        "display": True
                    },
                    {
                        "name": "basis",
                        "index": 0,
                        "section": "user_shares",
                        "prompt": "basis",
                        "value": "USER",
                        "display": True
                    },
                    {
                        "name": "type",
                        "index": 0,
                        "section": "user_shares",
                        "prompt": "type",
                        "value": "heaobject.root.ShareImpl",
                        "display": True
                    },
                    {
                        "name": "type_display_name",
                        "index": 0,
                        "section": "user_shares",
                        "prompt": "type_display_name",
                        "value": "Share",
                        "display": True
                    },
                    {
                        "name": "group_shares",
                        "prompt": "group_shares",
                        "value": [],
                        "display": True
                    },
                    {
                        "name": "modified",
                        "value": None,
                        "prompt": "modified",
                        "display": True},
                    {
                        "name": "name",
                        "value": "reximus",
                        "prompt": "name",
                        "display": True},
                    {
                        "name": "owner",
                        "value": "system|none",
                        "prompt": "owner",
                        "display": True},
                    {
                        "name": "source",
                        "value": None,
                        "prompt": "source",
                        "display": True},
                    {
                        "name": "source_detail",
                        "value": None,
                        "prompt": "source_detail",
                        "display": True
                    },
                    {
                        "name": "type",
                        "value": "heaobject.registry.Component",
                        "prompt": "type",
                        "display": True
                    },
                    {
                        "name": "base_url",
                        "value": "http://localhost/foo",
                        "prompt": "base_url",
                        "display": True},
                    {
                        "section": "resources",
                        "index": 0,
                        "name": "resource_type_name",
                        "value": "heaobject.folder.Folder",
                        "prompt":
                            "resource_type_name",
                        "display": True},
                    {
                        "section": "resources",
                        "index": 0,
                        "name": "base_path",
                        "value": "folders",
                        "prompt": "base_path",
                        "display": True},
                    {
                        "section": "resources",
                        "index": 0,
                        "name": "file_system_name",
                        "value": "DEFAULT_FILE_SYSTEM",
                        "prompt": "file_system_name",
                        "display": True},
                    {
                        "section": "resources",
                        "index": 0,
                        "name": "type",
                        "value": "heaobject.registry.Resource",
                        "prompt": "type",
                        "display": True
                    },
                    {
                        "section": "resources",
                        "index": 0,
                        "name": "resource_collection_type_display_name",
                        "value": "heaobject.folder.Folder",
                        "prompt": "resource_collection_type_display_name",
                        "display": True
                    },
                    {
                        "section": "resources",
                        "index": 0,
                        "name": "file_system_type",
                        "value": "heaobject.volume.MongoDBFileSystem",
                        "prompt": "file_system_type",
                        "display": True
                    },
                    {
                        "section": "resources",
                        "index": 0,
                        "name": "type_display_name",
                        "value": "Resource",
                        "prompt": "type_display_name",
                        "display": True
                    },
                    {
                        "section": "resources",
                        "index": 0,
                        "name": "collection_accessor_users",
                        "value": [],
                        "prompt": "collection_accessor_users",
                        "display": True
                    },
                    {
                        "section": "resources",
                        "index": 0,
                        "name": "collection_accessor_groups",
                        "value": [],
                        "prompt": "collection_accessor_groups",
                        "display": True
                    },
                    {
                        "section": "resources",
                        "index": 0,
                        "name": "creator_users",
                        "value": [],
                        "prompt": "creator_users",
                        "display": True
                    },
                    {
                        "section": "resources",
                        "index": 0,
                        "name": "creator_groups",
                        "value": [],
                        "prompt": "creator_groups",
                        "display": True
                    },
                    {
                        "section": "resources",
                        "index": 0,
                        "name": "default_shares",
                        "value": [],
                        "prompt": "default_shares",
                        "display": True
                    },
                    {
                        "section": "resources",
                        "index": 0,
                        "name": "manages_creators",
                        "value": False,
                        "prompt": "manages_creators",
                        "display": True
                    },
                    {
                        "section": "resources",
                        "index": 0,
                        "name": "display_in_system_menu",
                        "value": False,
                        "prompt": "display_in_system_menu",
                        "display": True
                    },
                    {
                        "section": "resources",
                        "index": 0,
                        "name": "display_in_user_menu",
                        "value": False,
                        "prompt": "display_in_user_menu",
                        "display": True
                    },
                    {
                        "section": "resources",
                        "index": 0,
                        "name": "collection_mime_type",
                        "value": 'application/x.collection',
                        "prompt": "collection_mime_type",
                        "display": True
                    },
                    {'name': 'super_admin_default_permissions',
                     'value': [Permission.VIEWER.name, Permission.EDITOR.name],
                     'prompt': 'super_admin_default_permissions',
                     'display': True,
                    },
                    {
                        'name': 'dynamic_permission_supported',
                        'value': False,
                        'prompt': 'dynamic_permission_supported',
                        'display': True
                    }
                    ],
                "links": []}]}}]
        obj = await self.client.request('GET',
                                        (self._href / 'bytype' / 'heaobject.folder.Folder').path,
                                        headers=TestGetResource2._headers)
        self.assertEqual(_ordered(expected), _ordered(await obj.json()))

    async def test_no_file_system_status(self):
        obj = await self.client.request('GET',
                                        (self._href / 'bytype' / 'heaobject.folder.Folder').path,
                                        headers=TestGetResource2._headers)
        self.assertEqual(200, obj.status)


class TestGetCollection(CollectionTestCase, GetOneMixin):
    pass


class TestGetAllCollections(CollectionTestCase, GetAllMixin):
    pass


class TestDeleteCollection(CollectionTestCase):
    async def test_delete_then_get(self) -> None:
        """Tries to delete a collection, which should fail."""
        async with self.client.delete((self._href / self.expected_one_id()).path,
                                       headers=self._headers) as resp:
            self.assertEqual(405, resp.status)

class TestPutCollection(CollectionTestCase):
    async def test_attempt_put(self):
        changed = copy_heaobject_dict_with(self._body_put, {'uri': 2})
        async with self.client.put((self._href / self.body_put_id()).path,
                                       json=changed,
                                       headers={**self._headers, hdrs.CONTENT_TYPE: nvpjson.MIME_TYPE}) as obj:
            self.assertEqual(405, obj.status)

class TestPostCollection(CollectionTestCase):
    async def test_attempt_put(self):
        changed = copy_heaobject_dict_with(self._body_post, {'id': None, 'name': 'foobar'})
        async with self.client.post((self._href / self.body_put_id()).path,
                                       json=changed,
                                       headers={**self._headers, hdrs.CONTENT_TYPE: nvpjson.MIME_TYPE}) as obj:
            self.assertEqual(405, obj.status)
