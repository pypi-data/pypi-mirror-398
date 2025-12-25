"""
Test HEA service.
"""
from heaobject.account import AWSAccount
from heaobject.organization import Organization

from heaserver.service import response, appproperty
from heaserver.service.runner import routes, web
from heaserver.service.db import mongoservicelib
from heaserver.service.wstl import action
from heaobject.registry import Component
from heaobject.volume import DEFAULT_FILE_SYSTEM, MongoDBFileSystem

MONGODB_COMPONENT_COLLECTION = 'components'
MONGODB_ORGANIZATION_COLLECTION = 'organizations'


@routes.get('/components/{id}')
@action('component-get-properties', rel='hea-properties')
@action('component-get-open-choices', rel='hea-opener-choices', path='components/{id}/opener')  # only add if the object is openable
@action('component-duplicate', rel='hea-duplicator', path='components/{id}/duplicator')
async def get_component(request: web.Request) -> web.Response:
    """
    Gets the component with the specified id.
    :param request: the HTTP request.
    :return: the requested component or Not Found.
    """
    return await mongoservicelib.get(request, MONGODB_COMPONENT_COLLECTION)


@routes.get('/components/byname/{name}')
async def get_component_by_name(request: web.Request) -> web.Response:
    """
    Gets the component with the specified name.
    :param request: the HTTP request.
    :return: the requested component or Not Found.
    """
    return await mongoservicelib.get_by_name(request, MONGODB_COMPONENT_COLLECTION)


@routes.get('/components/bytype/{type}')
@routes.get('/components/bytype/{type}/byfilesystemtype/{filesystemtype}')
@routes.get('/components/bytype/{type}/byfilesystemtype/{filesystemtype}/byfilesystemname/{filesystemname}')
async def get_components_by_type(request: web.Request) -> web.Response:
    """
    Gets the component that serves resources of the specified HEA object type.
    :param request: the HTTP request.
    :return: the requested component or Not Found.
    """
    if 'filesystemname' in request.match_info:
        file_system_name = request.match_info['filesystemname']
    else:
        file_system_name = DEFAULT_FILE_SYSTEM
    if file_system_name == DEFAULT_FILE_SYSTEM:
        query_clause = {
            '$or': [{'file_system_name': {'$exists': False}}, {'file_system_name': {'$in': [file_system_name, None]}}]}
    else:
        query_clause = {'file_system_name': {'$eq': file_system_name}}
    if 'filesystemtype' in request.match_info:
        file_system_type = request.match_info['filesystemtype']
    else:
        file_system_type = MongoDBFileSystem.get_type_name()
    if file_system_type == MongoDBFileSystem.get_type_name():
        query_clause.update({'$or': [{'file_system_type': {'$exists': False}},
                                     {'file_system_type': {'$in': [file_system_type, None]}}]})
    else:
        query_clause.update({'file_system_type': {'$eq': file_system_type}})
    mongo_attributes = {'resources': {
        '$elemMatch': {
            'resource_type_name': {'$eq': request.match_info['type']},
            **query_clause
        }}}
    result = await request.app[appproperty.HEA_DB].get(request,
                                                       MONGODB_COMPONENT_COLLECTION,
                                                       mongoattributes=mongo_attributes)
    return await response.get(request, result)


@routes.get('/components')
@routes.get('/components/')
@action('component-get-properties', rel='hea-properties')
@action('component-get-open-choices', rel='hea-opener-choices', path='components/{id}/opener')  # only add if the object is openable
@action('component-duplicate', rel='hea-duplicator', path='components/{id}/duplicator')
async def get_all_components(request: web.Request) -> web.Response:
    """
    Gets all components.
    :param request: the HTTP request.
    :return: all components.
    """
    return await mongoservicelib.get_all(request, MONGODB_COMPONENT_COLLECTION)


@routes.get('/components/{id}/duplicator')
@action(name='component-duplicate-form')
async def get_component_duplicator(request: web.Request) -> web.Response:
    """
    Gets a form template for duplicating the requested component.

    :param request: the HTTP request. Required.
    :return: the requested form, or Not Found if the requested component was not found.
    """
    return await mongoservicelib.get(request, MONGODB_COMPONENT_COLLECTION)


@routes.post('/components/duplicator')
async def post_component_duplicator(request: web.Request) -> web.Response:
    """
    Posts the provided component for duplication.
    :param request: the HTTP request.
    :return: a Response object with a status of Created and the object's URI in the
    """
    return await mongoservicelib.post(request, MONGODB_COMPONENT_COLLECTION, Component)


@routes.get('/components/{id}/opener')
@action('component-open-default', rel='hea-default hea-opener text/plain', path='components/{id}/content')
async def get_component_opener(request: web.Request) -> web.Response:
    """
    Opens the component. We wouldn't ordinarily open a component because there's nothing to open.

    :param request: the HTTP request. Required.
    :return: the requested form, or Not Found if the requested component was not found.
    """
    return await mongoservicelib.opener(request, MONGODB_COMPONENT_COLLECTION)


@routes.get('/components/{id}/content')
async def get_component_content(request: web.Request) -> web.Response:
    """
    Gets the component's content. Registry components have no content; this is just for testing purposes.

    :param request: the HTTP request. Required.
    :return: the requested content.
    """
    return await mongoservicelib.get_content(request, MONGODB_COMPONENT_COLLECTION)


@routes.post('/components')
@routes.post('/components/')
async def post_component(request: web.Request) -> web.Response:
    """
    Posts the provided component.
    :param request: the HTTP request.
    :return: a Response object with a status of Created and the object's URI in the
    """
    return await mongoservicelib.post(request, MONGODB_COMPONENT_COLLECTION, Component)


@routes.put('/components/{id}')
async def put_component(request: web.Request) -> web.Response:
    """
    Updates the component with the specified id.
    :param request: the HTTP request.
    :return: a Response object with a status of No Content or Not Found.
    """
    return await mongoservicelib.put(request, MONGODB_COMPONENT_COLLECTION, Component)


@routes.put('/components/{id}/content')
async def put_component_content(request: web.Request) -> web.Response:
    """
    Updates the component's content. Registry components have no content; this is just for testing purposes. There is
    no corresponding POST call because the content's initial creation happens automatically when a POST call to
    /components/ is sent.

    :param request: the HTTP request. Required.
    :return: the requested content.
    """
    return await mongoservicelib.put_content(request, MONGODB_COMPONENT_COLLECTION, Component)


@routes.delete('/components/{id}')
async def delete_component(request: web.Request) -> web.Response:
    """
    Deletes the component with the specified id.
    :param request: the HTTP request.
    :return: No Content or Not Found.
    """
    return await mongoservicelib.delete(request, MONGODB_COMPONENT_COLLECTION)


@routes.get('/organizations/{id}')
@action('heaserver-organizations-organization-get-properties', rel='properties')
@action('heaserver-organizations-organization-get-open-choices', rel='hea-opener-choices',
        path='organizations/{id}/opener')
@action('heaserver-organizations-organization-duplicate', rel='duplicator', path='organizations/{id}/duplicator')
async def get_organization(request: web.Request) -> web.Response:
    """
    Gets the organization with the specified id.
    :param request: the HTTP request.
    :return: the requested organization or Not Found.
    ---
    summary: A specific organization.
    tags:
        - heaserver-organizations-get-organization
    parameters:
        - $ref: '#/components/parameters/id'
    responses:
      '200':
        $ref: '#/components/responses/200'
      '404':
        $ref: '#/components/responses/404'
    """
    return await mongoservicelib.get(request, MONGODB_ORGANIZATION_COLLECTION)


@routes.get('/organizations/byname/{name}')
async def get_organization_by_name(request: web.Request) -> web.Response:
    """
    Gets the organization with the specified id.
    :param request: the HTTP request.
    :return: the requested organization or Not Found.
    ---
    summary: A specific organization, by name.
    tags:
        - heaserver-organizations-get-organization-by-name
    parameters:
        - $ref: '#/components/parameters/name'
    responses:
      '200':
        $ref: '#/components/responses/200'
      '404':
        $ref: '#/components/responses/404'
    """
    return await mongoservicelib.get_by_name(request, MONGODB_ORGANIZATION_COLLECTION)


@routes.get('/organizations/{id}/duplicator')
@action(name='heaserver-organizations-organization-duplicate-form', path='organizations/{id}')
async def get_organization_duplicate_form(request: web.Request) -> web.Response:
    """
    Gets a form template for duplicating the requested organization.

    :param request: the HTTP request. Required.
    :return: the requested form, or Not Found if the requested organization was not found.
    """
    return await mongoservicelib.get(request, MONGODB_ORGANIZATION_COLLECTION)


@routes.get('/organizations/{id}/opener')
@action('heaserver-organizations-organization-open-aws-accounts', rel='hea-default hea-opener text/plain',
        path='organizations/{id}/content')
async def get_organization_opener(request: web.Request) -> web.Response:
    """

    :param request: the HTTP Request.
    :return: A Response object with a status of Multiple Choices or Not Found.
    ---
    summary: Organization opener choices
    tags:
        - heaserver-organizations-organization-get-open-choices
    parameters:
        - $ref: '#/components/parameters/id'
    responses:
      '300':
        $ref: '#/components/responses/300'
      '404':
        $ref: '#/components/responses/404'
    """
    return await mongoservicelib.opener(request, MONGODB_ORGANIZATION_COLLECTION)


@routes.get('/organizations')
@routes.get('/organizations/')
@action('heaserver-organizations-organization-get-properties', rel='properties')
@action('heaserver-organizations-organization-get-open-choices', rel='hea-opener-choices',
        path='organizations/{id}/opener')
@action('heaserver-organizations-organization-duplicate', rel='duplicator', path='organizations/{id}/duplicator')
async def get_all_organizations(request: web.Request) -> web.Response:
    """
    Gets all organizations.
    :param request: the HTTP request.
    :return: all organizations.
    ---
    summary: All organizations.
    tags:
        - heaserver-organizations-get-all-organizations
    responses:
      '200':
        $ref: '#/components/responses/200'
    """
    return await mongoservicelib.get_all(request, MONGODB_ORGANIZATION_COLLECTION)


@routes.get('/organizations/{id}/content')
async def get_organization_content(request: web.Request) -> web.Response:
    """
    Gets the component's content. Registry components have no content; this is just for testing purposes.

    :param request: the HTTP request. Required.
    :return: the requested content.
    """
    return await mongoservicelib.get_content(request, MONGODB_ORGANIZATION_COLLECTION)


@routes.put('/organizations/{id}')
async def put_organization(request: web.Request) -> web.Response:
    """
    Updates the organization with the specified id.
    :param request: the HTTP request.
    :return: a Response object with a status of No Content or Not Found.
    """
    return await mongoservicelib.put(request, MONGODB_ORGANIZATION_COLLECTION, Organization)


@routes.put('/organizations/{id}/content')
async def put_organization_content(request: web.Request) -> web.Response:
    """
    Updates the component's content. Registry components have no content; this is just for testing purposes. There is
    no corresponding POST call because the content's initial creation happens automatically when a POST call to
    /components/ is sent.

    :param request: the HTTP request. Required.
    :return: the requested content.
    """
    return await mongoservicelib.put_content(request, MONGODB_ORGANIZATION_COLLECTION, Organization)
