"""
The HEA Registry Service provides a table of all currently active HEA microservices. Microservices each have an unique
component name field, and the name may be used to get other information about the microservice including its base URL
to make REST API calls.
"""
from heaserver.service import response, appproperty
from heaserver.service.runner import routes, start, web
from heaserver.service.db import mongo, mongoservicelib
from heaserver.service.wstl import builder_factory, action
from heaserver.service.oidcclaimhdrs import SUB
from heaserver.service.heaobjectsupport import HEAServerPermissionContext
from heaobject.registry import Component, Property, Collection
from heaobject.root import Share, ShareImpl, Permission, DesktopObjectDict, DefaultPermissionGroup, DesktopObject, \
    desktop_object_from_dict, to_dict
from heaobject.user import NONE_USER
from heaserver.service.config import Configuration
import logging

MONGODB_COMPONENT_COLLECTION = 'components'
MONGODB_PROPERTIES_COLLECTION = 'properties'
MONGODB_COLLECTION_COLLECTION = 'collection'


class RegistryServicePermissionContext(HEAServerPermissionContext):
    """
    The HEA Registry Service permission context.
    """

    def __init__(self, request: web.Request) -> None:
        sub = request.headers.get(SUB, NONE_USER)
        super().__init__(sub, request)

    async def can_create(self, desktop_object_type: type[DesktopObject]) -> bool:
        """
        This method checks if the user can create a new object of the specified type. This implementation checks the
        mongo database directly rather than going through the REST APIs.

        :param desktop_object_type: the type of the object to check.
        :return: True if the user can create the object, False otherwise."""
        type_name = desktop_object_type.get_type_name()
        result_dict = await _get_component_by_type(self.request, type_name)
        component = desktop_object_from_dict(result_dict, type_=Component) if result_dict is not None else None
        if component is None or (resource := component.get_resource(type_name)) is None:
            raise ValueError(f'Invalid desktop object type {desktop_object_type}')
        return resource.manages_creators and await resource.is_creator(self)


class RegistryMongo(mongo.Mongo):
    def get_default_permission_context(self, request):
        return RegistryServicePermissionContext(request)


class RegistryMongoManager(mongo.MongoManager):
    def get_database(self) -> RegistryMongo:
        return RegistryMongo(config=self.config, managed=True)


@routes.get('/componentsping')
async def ping(request: web.Request) -> web.Response:
    """
    Checks if this service is running.

    :param request: the HTTP request.
    :return: the HTTP response.
    """
    return await mongoservicelib.ping(request)


@routes.get('/components/{id}')
@action('heaserver-registry-component-get-properties', rel='hea-properties')
@action(name='heaserver-registry-component-get-self', rel='self', path='components/{id}')
async def get_component(request: web.Request) -> web.Response:
    """
    Gets the component with the specified id.
    :param request: the HTTP request.
    :return: the requested component or Not Found.
    ---
    summary: A specific component, by id.
    tags:
        - heaserver-registry-component
    parameters:
        - $ref: '#/components/parameters/id'
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    responses:
      '200':
        $ref: '#/components/responses/200'
      '404':
        $ref: '#/components/responses/404'
    """
    async with mongo.MongoContext(request) as mongo_:
        obj = await mongoservicelib.get_desktop_object(request, MONGODB_COMPONENT_COLLECTION,
                                                       type_=Component, mongo=mongo_)
        if obj is None:
            return await response.get(request, None)
        context = mongo_.get_default_permission_context(request)
        return await response.get(request, to_dict(obj), permissions=await obj.get_permissions(context),
                                  attribute_permissions=await obj.get_all_attribute_permissions(context))


@routes.get('/components/byname/{name}')
async def get_component_by_name(request: web.Request) -> web.Response:
    """
    Gets the component with the specified id.
    :param request: the HTTP request.
    :return: the requested component or Not Found.
    ---
    summary: A specific component, by name.
    tags:
        - heaserver-registry-component
    parameters:
        - $ref: '#/components/parameters/name'
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    responses:
      '200':
        $ref: '#/components/responses/200'
      '404':
        $ref: '#/components/responses/404'
    """
    async with mongo.MongoContext(request) as mongo_:
        obj = await mongoservicelib.get_by_name_desktop_object(request, MONGODB_COMPONENT_COLLECTION,
                                                               type_=Component, mongo=mongo_)
        if obj is None:
            return await response.get(request, None)
        context = mongo_.get_default_permission_context(request)
        return await response.get(request, to_dict(obj), permissions=await obj.get_permissions(context),
                                  attribute_permissions=await obj.get_all_attribute_permissions(context))


@routes.get('/components/bytype/{type}')
async def get_component_by_type(request: web.Request) -> web.Response:
    """
    Gets the component that serves resources of the specified HEA object type.

    :param request: the HTTP request.
    :return: the requested component or Not Found.
    ---
    summary: A specific component, by type and file system.
    tags:
        - heaserver-registry-component
    parameters:
        - name: type
          in: path
          required: true
          description: The type of the component to retrieve.
          schema:
            type: string
          examples:
            example:
              summary: A component type
              value: heaobject.folder.Folder
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    responses:
      '200':
        $ref: '#/components/responses/200'
      '404':
        $ref: '#/components/responses/404'
    """
    sub = request.headers.get(SUB, NONE_USER)
    type_ = request.match_info['type']
    cache_key = (sub, MONGODB_COMPONENT_COLLECTION, f'type^{type_}')
    result = request.app[appproperty.HEA_CACHE].get(cache_key)
    if result is None:
        async with mongo.MongoContext(request) as mongo_:
            result_dict = await _get_component_by_type(request, type_, mongo_=mongo_)
            if result_dict is None:
                return await response.get(request, None)
            component: Component = Component()
            component.from_dict(result_dict)
            result_dict_ = to_dict(component)
            context = mongo_.get_default_permission_context(request)
            permissions = await component.get_permissions(context)
            attr_perms = await component.get_all_attribute_permissions(context)
            request.app[appproperty.HEA_CACHE][cache_key] = (result_dict_, permissions, attr_perms)
            return await response.get(request, result_dict_, permissions=permissions, attribute_permissions=attr_perms)
    else:
        return await response.get(request, result[0], permissions=result[1], attribute_permissions=result[2])


@routes.get('/components')
@routes.get('/components/')
@action('heaserver-registry-component-get-properties', rel='hea-properties')
@action(name='heaserver-registry-component-get-self', rel='self', path='components/{id}')
async def get_all_components(request: web.Request) -> web.Response:
    """
    Gets all components.
    :param request: the HTTP request.
    :return: all components.
    ---
    summary: All components.
    tags:
        - heaserver-registry-component
    parameters:
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
        - name: sort
          in: query
          description: Sort order for components, in the same order as the sort_attr parameter.
          schema:
            type: array
            items:
              type: string
              enum: [asc, desc]
          examples:
            example:
              summary: Sort in ascending order.
              value: asc
        - name: sort_attr
          in: query
          description: Attributes to sort by, in the same order as as the sort parameter. If not specified, defaults to sorting by display_name.
          schema:
            type: array
            items:
              type: string
          examples:
            example:
              summary: Sort by display name.
              value: display_name
    responses:
      '200':
        $ref: '#/components/responses/200'
    """
    logger = logging.getLogger(__name__)
    sub = request.headers.get(SUB, NONE_USER)
    sort = mongoservicelib.MongoSortOrder.from_request_dict_raises_http_error(request, 'display_name')
    logger.debug('sort is %s', sort)
    if not request.query:
        cache_key = (sub, MONGODB_COMPONENT_COLLECTION, None,
                     mongoservicelib.sort_dict_to_cache_key(sort))
        cached_value = request.app[appproperty.HEA_CACHE].get(cache_key)
    else:
        cached_value = None
    if cached_value is not None:
        return await response.get_all(request, data=cached_value[0], permissions=cached_value[1],
                                      attribute_permissions=cached_value[2])
    else:
        objs: list[DesktopObject] = []
        l: list[DesktopObjectDict] = []
        async with mongo.MongoContext(request) as mongo_:
            context = mongo_.get_default_permission_context(request)
            gen = mongoservicelib.get_all_desktop_objects_gen(request, MONGODB_COMPONENT_COLLECTION, sort=sort,
                                              mongo=mongo_, context=context)
            try:
                async for obj in gen:
                    objs.append(obj)
                    l.append(to_dict(obj))
                perms: list[list[Permission]] = []
                attr_perms: list[dict[str, list[Permission]]] = []
                for obj in objs:
                    perms.append(await obj.get_permissions(context))
                    attr_perms.append(await obj.get_all_attribute_permissions(context))
                if not request.query:
                    request.app[appproperty.HEA_CACHE][cache_key] = (l, perms, attr_perms)
                return await response.get_all(request, l, permissions=perms, attribute_permissions=attr_perms)
            finally:
                await gen.aclose()


@routes.get('/components/{id}/duplicator')
@action(name='heaserver-registry-component-duplicate-form')
async def get_component_duplicator(request: web.Request) -> web.Response:
    """
    Gets a form template for duplicating the requested component.

    :param request: the HTTP request. Required.
    :return: the requested form, or Not Found if the requested component was not found.
    ---
    summary: A specific component, by id.
    tags:
        - heaserver-registry-component
    parameters:
        - $ref: '#/components/parameters/id'
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    responses:
      '200':
        $ref: '#/components/responses/200'
      '404':
        $ref: '#/components/responses/404'
    """
    return await mongoservicelib.get(request, MONGODB_COMPONENT_COLLECTION)


@routes.post('/components/duplicator')
async def post_component_duplicator(request: web.Request) -> web.Response:
    """
    Posts the provided component for duplication.
    :param request: the HTTP request.
    :return: a Response object with a status of Created and the object's URI in the Location header.
    ---
    summary: Component duplication.
    tags:
        - heaserver-registry-component
    parameters:
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    requestBody:
      description: A duplicate component object.
      required: true
      content:
        application/vnd.collection+json:
          schema:
            type: object
          examples:
            example:
              summary: Component example
              value: {
                "template": {
                  "data": [{
                    "name": "created",
                    "value": null
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
                    "name": "type",
                    "value": "heaobject.registry.Component"
                  }]
                }
              }
        application/json:
          schema:
            type: object
          examples:
            example:
              summary: Component example
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
                "type": "heaobject.registry.Component",
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
      '201':
        $ref: '#/components/responses/201'
      '400':
        $ref: '#/components/responses/400'
      '404':
        $ref: '#/components/responses/404'

    """
    return await mongoservicelib.post(request, MONGODB_COMPONENT_COLLECTION, Component)


@routes.post('/components')
@routes.post('/components/')
async def post_component(request: web.Request) -> web.Response:
    """
    Posts the provided component.
    :param request: the HTTP request.
    :return: a Response object with a status of Created and the object's URI in the Location header.
    ---
    summary: Component creation
    tags:
        - heaserver-registry-component
    parameters:
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    requestBody:
      description: A new component object.
      required: true
      content:
        application/vnd.collection+json:
          schema:
            type: object
          examples:
            example:
              summary: Component example
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
                    "name": "type",
                    "value": "heaobject.registry.Component"
                  }]
                }
              }
        application/json:
          schema:
            type: object
          examples:
            example:
              summary: Component example
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
                "type": "heaobject.registry.Component",
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
      '201':
        $ref: '#/components/responses/201'
      '400':
        $ref: '#/components/responses/400'
      '404':
        $ref: '#/components/responses/404'
    """
    return await mongoservicelib.post(request, MONGODB_COMPONENT_COLLECTION, Component)


@routes.put('/components/{id}')
async def put_component(request: web.Request) -> web.Response:
    """
    Updates the component with the specified id.
    :param request: the HTTP request.
    :return: a Response object with a status of No Content or Not Found.
    ---
    summary: Component updates
    tags:
        - heaserver-registry-component
    parameters:
        - $ref: '#/components/parameters/id'
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    requestBody:
      description: An updated component object.
      required: true
      content:
        application/vnd.collection+json:
          schema:
            type: object
          examples:
            example:
              summary: Component example
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
                  "value": "heaobject.registry.Component"
                  }]
                }
              }
        application/json:
          schema:
            type: object
          examples:
            example:
              summary: Component example
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
                "type": "heaobject.registry.Component",
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
    return await mongoservicelib.put(request, MONGODB_COMPONENT_COLLECTION, Component)


@routes.delete('/components/{id}')
async def delete_component(request: web.Request) -> web.Response:
    """
    Deletes the component with the specified id.
    :param request: the HTTP request.
    :return: No Content or Not Found.
    ---
    summary: Component deletion
    tags:
        - heaserver-registry-component
    parameters:
        - $ref: '#/components/parameters/id'
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    responses:
      '204':
        $ref: '#/components/responses/204'
      '404':
        $ref: '#/components/responses/404'
    """
    return await mongoservicelib.delete(request, MONGODB_COMPONENT_COLLECTION)


@routes.get('/properties/{id}')
@action('heaserver-registry-property-get-properties', rel='hea-properties')
@action(name='heaserver-registry-property-get-self', rel='self', path='properties/{id}')
async def get_property(request: web.Request) -> web.Response:
    """
    Gets the property with the specified id.
    :param request: the HTTP request.
    :return: the requested property or Not Found.
    ---
    summary: A specific property, by id.
    tags:
        - heaserver-registry-property
    parameters:
        - $ref: '#/components/parameters/id'
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    responses:
      '200':
        $ref: '#/components/responses/200'
      '404':
        $ref: '#/components/responses/404'
    """
    return await mongoservicelib.get(request, MONGODB_PROPERTIES_COLLECTION)


@routes.get('/properties/byname/{name}')
async def get_property_by_name(request: web.Request) -> web.Response:
    """
    Gets the property with the specified id.
    :param request: the HTTP request.
    :return: the requested property or Not Found.
    ---
    summary: A specific property, by name.
    tags:
        - heaserver-registry-property
    parameters:
        - name: name
          in: path
          required: true
          description: The name of the property.
          schema:
            type: string
          examples:
            example:
              summary: A property name
              value: applicationName
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'

    responses:
      '200':
        $ref: '#/components/responses/200'
      '404':
        $ref: '#/components/responses/404'
    """
    return await mongoservicelib.get_by_name(request, MONGODB_PROPERTIES_COLLECTION)


@routes.get('/properties')
@routes.get('/properties/')
@action('heaserver-registry-property-get-properties', rel='hea-properties')
@action(name='heaserver-registry-property-get-self', rel='self', path='properties/{id}')
async def get_all_properties(request: web.Request) -> web.Response:
    """
    Gets all properties.
    :param request: the HTTP request.
    :return: all properties.
    ---
    summary: All properties.
    tags:
        - heaserver-registry-property
    parameters:
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
        - name: sort
          in: query
          description: Sort order for properties, in the same order as the sort_attr parameter.
          schema:
            type: array
            items:
              type: string
              enum: [asc, desc]
          examples:
            example:
              summary: Sort in ascending order.
              value: asc
        - name: sort_attr
          in: query
          description: Attributes to sort by, in the same order as as the sort parameter. If not specified, defaults to sorting by display_name.
          schema:
            type: array
            items:
              type: string
          examples:
            example:
              summary: Sort by display name.
              value: display_name
    responses:
      '200':
        $ref: '#/components/responses/200'
    """
    sort = mongoservicelib.MongoSortOrder.from_request_dict_raises_http_error(request, 'display_name')
    return await mongoservicelib.get_all(request, MONGODB_PROPERTIES_COLLECTION, sort=sort)


@routes.post('/properties')
@routes.post('/properties/')
async def post_property(request: web.Request) -> web.Response:
    """
    Posts the provided property.
    :param request: the HTTP request.
    :return: a Response object with a status of Created and the object's URI in the Location header.
    ---
    summary: Property creation
    tags:
        - heaserver-registry-property
    parameters:
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    requestBody:
      description: A new property object.
      required: true
      content:
        application/vnd.collection+json:
          schema:
            type: object
          examples:
            example:
              summary: Property example
              value: {
                "template": {
                  "data": [
                    {"name": "name", "value": "exampleProperty"},
                    {"name": "value", "value": "some value"},
                    {"name": "display_name", "value": "Example Property"},
                    {"name": "type", "value": "heaobject.registry.Property"}
                  ]
                }
              }
        application/json:
          schema:
            type: object
          examples:
            example:
              summary: Property example
              value: {
                "name": "exampleProperty",
                "value": "some value",
                "display_name": "Example Property",
                "type": "heaobject.registry.Property"
              }
    responses:
      '201':
        $ref: '#/components/responses/201'
      '400':
        $ref: '#/components/responses/400'
      '404':
        $ref: '#/components/responses/404'
    """
    return await mongoservicelib.post(request, MONGODB_PROPERTIES_COLLECTION, Property)


@routes.put('/properties/{id}')
async def put_property(request: web.Request) -> web.Response:
    """
    Updates the property with the specified id.
    :param request: the HTTP request.
    :return: a Response object with a status of No Content or Not Found.
    ---
    summary: Property updates
    tags:
        - heaserver-registry-property
    parameters:
        - $ref: '#/components/parameters/id'
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    requestBody:
      description: An updated property object.
      required: true
      content:
        application/vnd.collection+json:
          schema:
            type: object
          examples:
            example:
              summary: A property example
              value: {
                "template": {
                  "data": [
                    {
                      "name": "name",
                      "value": "HEA"
                    },
                    {
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
                      "value": "Reximus"
                    },
                    {
                      "name": "modified",
                      "value": null
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
                      "value": "heaobject.folder.Folder"
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
                      "value": "heaobject.registry.Property"
                    }
                  ]
                }
              }
        application/json:
          schema:
            type: object
          examples:
            example:
              summary: A property example
              value: {
                "created": null,
                "derived_by": null,
                "derived_from": [],
                "description": null,
                "display_name": "Untitled Property",
                "id": "618da15104811d77ca7221fd",
                "invites": [],
                "modified": null,
                "name": "applicationName",
                "owner": "system|none",
                "shares": [],
                "source": null,
                "type": "heaobject.registry.Property",
                "value": "HEA",
                "version": null
              }
    responses:
      '204':
        $ref: '#/components/responses/204'
      '400':
        $ref: '#/components/responses/400'
      '404':
        $ref: '#/components/responses/404'
    """
    return await mongoservicelib.put(request, MONGODB_PROPERTIES_COLLECTION, Property)


@routes.delete('/properties/{id}')
async def delete_property(request: web.Request) -> web.Response:
    """
    Deletes the property with the specified id.
    :param request: the HTTP request.
    :return: No Content or Not Found.
    ---
    summary: Property deletion
    tags:
        - heaserver-registry-property
    parameters:
        - $ref: '#/components/parameters/id'
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    responses:
      '204':
        $ref: '#/components/responses/204'
      '404':
        $ref: '#/components/responses/404'
    """
    return await mongoservicelib.delete(request, MONGODB_PROPERTIES_COLLECTION)


@routes.get('/collections')
@routes.get('/collections/')
@action(name='heaserver-registry-collection-get-open-choices', rel='hea-opener-choices', path='collections/{id}/opener')
@action(name='heaserver-registry-collection-get-properties', rel='hea-properties')
@action(name='heaserver-registry-collection-get-self', rel='self hea-self-container', path='collections/{id}')
async def get_all_collections(request: web.Request) -> web.Response:
    """
    Gets all collections.

    :param request: the HTTP request.
    :return: all collections.
    ---
    summary: All collections.
    tags:
        - heaserver-registry-collection
    parameters:
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
        - name: sort
          in: query
          description: Sort order for collections, in the same order as the sort_attr parameter.
          schema:
            type: array
            items:
              type: string
              enum: [asc, desc]
          examples:
            example:
              summary: Sort in ascending order.
              value: asc
        - name: sort_attr
          in: query
          description: Attributes to sort by, in the same order as as the sort parameter. If not specified, defaults to sorting by display_name.
          schema:
            type: array
            items:
              type: string
          examples:
            example:
              summary: Sort by display name.
              value: display_name
    responses:
      '200':
        $ref: '#/components/responses/200'
    """
    sub = request.headers.get(SUB, NONE_USER)
    collections: list[DesktopObjectDict] = []
    permissions: list[list[Permission]] = []
    attribute_permissions: list[dict[str, list[Permission]]] = []
    context = request.app[appproperty.HEA_DB].get_default_permission_context(request)
    logger = logging.getLogger(__name__)
    sort = mongoservicelib.MongoSortOrder.from_request_dict_raises_http_error(request, 'display_name')
    async for obj in mongoservicelib.get_all_desktop_objects_gen(request, MONGODB_COMPONENT_COLLECTION,
                                                                 type_=Component, sort=sort):
        for resource in obj.resources:
            coll: Collection = Collection()
            coll.id = resource.resource_type_name
            coll.name = resource.resource_type_name
            coll.display_name = resource.resource_collection_type_display_name
            coll.collection_type_name = resource.resource_type_name
            coll.url = resource.base_path
            coll.display_in_system_menu = resource.display_in_system_menu
            coll.display_in_user_menu = resource.display_in_user_menu
            coll.mime_type = resource.collection_mime_type
            shares_by_user = dict[str, Share]()
            for user in resource.collection_accessor_users:
                share: Share = ShareImpl()
                share.user = user
                share.permissions = [Permission.VIEWER]
                shares_by_user[user] = share
                coll.add_share(share)
            for user in resource.creator_users:
                if share_ := shares_by_user.get(user):
                    share_.add_permission(Permission.CREATOR)
            shares_by_group = dict[str, Share]()
            for group in resource.collection_accessor_groups:
                share__: Share = ShareImpl()
                share__.group = group
                share__.permissions = [Permission.VIEWER]
                shares_by_group[group] = share__
                coll.add_share(share__)
            for group in resource.creator_groups:
                if share___ := shares_by_group.get(group):
                    share___.add_permission(Permission.CREATOR)
            logger.debug('Checking permissions of %r for user %s', coll, sub)
            if await DefaultPermissionGroup.ACCESSOR_PERMS.has_any(coll, context):
                logger.debug('User %s has permission to see %r', sub, coll)
                collections.append(to_dict(coll))
                permissions.append(await coll.get_permissions(context))
                attribute_permissions.append(await coll.get_all_attribute_permissions(context))
    logger.debug('collections: %r', collections)
    return await response.get_all(request, collections, permissions=permissions, attribute_permissions=attribute_permissions)


@routes.get('/collections/{id}')
@action(name='heaserver-registry-collection-get-open-choices', rel='hea-opener-choices', path='collections/{id}/opener')
@action(name='heaserver-registry-collection-get-properties', rel='hea-properties')
@action(name='heaserver-registry-collection-get-self', rel='self hea-self-container', path='collections/{id}')
async def get_collection(request: web.Request) -> web.Response:
    """
    Gets a collection.

    :param request: the HTTP Request.
    :return: A Response object with a status of Multiple Choices or Not Found.
    ---
    summary: Collection
    tags:
        - heaserver-registry-collection
    parameters:
        - name: id
          in: path
          required: true
          description: The id of the collection.
          schema:
            type: string
          examples:
            example:
              summary: A collection id
              value: heaobject.folder.Item
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    responses:
      '200':
        $ref: '#/components/responses/200'
      '404':
        $ref: '#/components/responses/404'
    """
    return await _get_collection(request)


@routes.get('/collections/byname/{name}')
@action(name='heaserver-registry-collection-get-self', rel='self', path='collections/{id}')
async def get_collection_by_name(request: web.Request) -> web.Response:
    """
    Gets a collection by name.

    :param request: the HTTP Request.
    :return: A Response object with a status of Multiple Choices or Not Found.
    ---
    summary: Collection
    tags:
        - heaserver-registry-collection
    parameters:
        - name: name
          in: path
          required: true
          description: The name of the collection.
          schema:
            type: string
          examples:
            example:
              summary: A collection name
              value: heaobject.folder.Item
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    responses:
      '200':
        $ref: '#/components/responses/200'
      '404':
        $ref: '#/components/responses/404'
    """
    request.match_info['id'] = request.match_info['name']
    return await _get_collection(request)

@routes.get('/collections/{id}/opener')
@action('heaserver-registry-collection-open', rel=f'hea-opener hea-self-container hea-default', path='{+url}')
async def get_collection_opener(request: web.Request) -> web.Response:
    """
    Gets a collection with a default link to open it, if the format in the Accept header supports links.

    :param request: the HTTP Request.
    :return: A Response object with a status of Multiple Choices or Not Found.
    ---
    summary: Collection opener choices
    tags:
        - heaserver-registry-collection
    parameters:
        - name: id
          in: path
          required: true
          description: The id of the collection.
          schema:
            type: string
          examples:
            example:
              summary: A collection id
              value: heaobject.folder.Item
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    responses:
      '300':
        $ref: '#/components/responses/300'
      '404':
        $ref: '#/components/responses/404'
    """
    return await _get_collection(request)


def start_with(config: Configuration) -> None:
    start(db=RegistryMongoManager,
          wstl_builder_factory=builder_factory(__package__), config=config)


async def _get_collection(request: web.Request) -> web.Response:
    mongo_attributes = {'resources': {
        '$elemMatch': {
            'resource_type_name': {'$eq': request.match_info['id']},
        }}}
    context = request.app[appproperty.HEA_DB].get_default_permission_context(request)
    async for obj in mongoservicelib.get_all_desktop_objects_gen(request, MONGODB_COMPONENT_COLLECTION,
                                                                 mongoattributes=mongo_attributes, type_=Component):
        for resource in (r for r in obj.resources if r.resource_type_name == request.match_info['id']):
            c: Collection = Collection()
            c.id = resource.resource_type_name
            c.name = resource.resource_type_name
            c.display_name = resource.resource_collection_type_display_name
            c.collection_type_name = resource.resource_type_name
            c.file_system_name = resource.file_system_name
            c.file_system_type = resource.file_system_type
            c.url = resource.base_path
            c.display_in_system_menu = resource.display_in_system_menu
            c.display_in_user_menu = resource.display_in_user_menu
            c.mime_type = resource.collection_mime_type
            creator_users_set = set(resource.creator_users)
            for collection_accessor_user in resource.collection_accessor_users:
                share: Share = ShareImpl()
                share.user = collection_accessor_user
                share.permissions = [Permission.VIEWER]
                if collection_accessor_user in creator_users_set:
                    share.add_permission(Permission.CREATOR)
                c.add_user_share(share)
            creator_groups_set = set(resource.creator_groups)
            for collection_accessor_group in resource.collection_accessor_groups:
                share = ShareImpl()
                share.group = collection_accessor_group
                share.permissions = [Permission.VIEWER]
                if collection_accessor_group in creator_groups_set:
                    share.add_permission(Permission.CREATOR)
                c.add_group_share(share)
            if await DefaultPermissionGroup.ACCESSOR_PERMS.has_any(c, context):
                return await response.get(request, to_dict(c), await c.get_permissions(context), await c.get_all_attribute_permissions(context))
            else:
                return await response.get(request, None)
    return await response.get(request, None)


async def _get_component_by_type(request: web.Request, type_name: str, mongo_: mongo.Mongo | None = None) -> DesktopObjectDict | None:
    """
    Gets the registry component that is responsible for the specified type.

    :param request: the HTTP request (required).
    :param type_name: the name of the type (required).
    :param mongo: the mongo connection (optional). If not provided, a new connection will be created.
    :return: the component as a desktop object dict, or None if not found.
    """
    mongo_attrs = {'resources': {
            '$elemMatch': {
                'resource_type_name': {'$eq': type_name}
            }}}
    if mongo_:
        return await mongo_.get(request, MONGODB_COMPONENT_COLLECTION, mongoattributes=mongo_attrs)
    else:
        async with mongo.MongoContext(request) as mongo__:
            return await mongo__.get(request, MONGODB_COMPONENT_COLLECTION, mongoattributes=mongo_attrs)
