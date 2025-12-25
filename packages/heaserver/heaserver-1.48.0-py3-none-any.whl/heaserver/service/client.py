from aiohttp import ClientResponse, ClientResponseError, hdrs, web, ClientSession
from aiohttp.client_exceptions import ClientConnectionError
from aiohttp.typedefs import LooseHeaders
from heaobject import root
from heaobject.root import DesktopObjectTypeVar, DesktopObjectDict
from heaobject.registry import Component, Property, Resource
from heaserver.service.util import async_retry_context_manager
from . import appproperty, response
from .aiohttp import StreamReaderWrapper, SupportsAsyncRead
from .representor import nvpjson
from yarl import URL
from typing import Optional, Union, Type, Mapping, AsyncIterator, Sequence, Any, cast
from multidict import CIMultiDict
from cachetools import TTLCache
import logging


async def get_streaming(request: web.Request, url: Union[str, URL],
                        headers: LooseHeaders | None = None,
                        client_session: ClientSession | None = None) -> web.StreamResponse:
    """
    Co-routine that gets data from a HEA service as a stream. It retries when connection errors occur.

    :param request: the HTTP request (required).
    :param url: The URL (str or URL) of the resource (required).
    :param headers: optional dict of headers.
    :param client_session: a client session. If None, the default session will be used.
    :return: the HEAObject populated with the resource's content, None if no such resource exists, or another HTTP
    status code if an error occurred.
    :raises aiohttp.client_exceptions.ClientResponseError: if the response's status code was unexpected.
    :raises aiohttp.client_exceptions.ClientConnectionError: if a connection to the service could not be established.
    """
    _logger = logging.getLogger(__name__)
    session = client_session if client_session is not None else _client_session(request.app)
    _logger.debug('Getting streaming content at %s with headers %s', url, headers)
    session_get_with_retry = async_retry_context_manager(ClientConnectionError, retries=5, cooldown=5)(session.get)
    async with session_get_with_retry(url, headers=headers, raise_for_status=False) as response_:
        if response_.status == 200:
            content_type = response_.headers.get(hdrs.CONTENT_TYPE, response.DEFAULT_CONTENT_TYPE)
            return await response.get_streaming(request, StreamReaderWrapper(response_.content),
                                                content_type=content_type)
        elif response_.status == 404:
            return response.status_not_found()
        else:
            return web.Response(status=response_.status)


async def put_streaming(request: web.Request, url: Union[str, URL], data: SupportsAsyncRead,
                        headers: Mapping[str, str] | None = None,
                        client_session: ClientSession | None = None) -> None:
    """
    Co-routine that updates data in a HEA service. The data is provided as a stream.

    :param app: the aiohttp application context (required).
    :param url: The URL (str or URL) of the resource (required).
    :param data: the data as a stream.
    :param headers: optional headers.
    :param client_session: a client session. If None, the default session will be used.
    """
    session = client_session if client_session is not None else _client_session(request.app)
    async with session.put(url, data=data, headers=headers):
        pass


async def get_dict(app: web.Application, url,
                   headers: Mapping[str, str] | None = None,
                   client_session: ClientSession | None = None) -> Optional[DesktopObjectDict]:
    """
    Co-routine that gets a dict from a HEA service that returns JSON. It retries when connection errors occur. Will
    return Collection+JSON by default, and you can use the headers parameter to set the Accept header to
    application/json (plain name-value pair JSON), application/vnd.wstl+json (WeSTL), or
    application/vnd.collection+json (Collection+JSON).

    :param app: the aiohttp application context (required).
    :param url: The URL (str or URL) of the resource (required).
    :param headers: optional Mapping of headers.
    :param client_session: a client session. If None, the default session will be used.
    :return: the dict populated with the resource's content, None if no such resource exists, or another HTTP
    status code if an error occurred.
    :raises aiohttp.client_exceptions.ClientResponseError: if the response's status code was unexpected.
    :raises aiohttp.client_exceptions.ClientConnectionError: if a connection to the service could not be established.
    """
    _logger = logging.getLogger(__name__)
    session = client_session if client_session is not None else _client_session(app)
    _logger.debug('Getting dict at %s with headers %s', url, headers)
    session_get_with_retry = async_retry_context_manager(ClientConnectionError, retries=5, cooldown=5)(session.get)
    async with session_get_with_retry(url, headers=headers, raise_for_status=False) as response_:
        if response_.status == 404:
            return None
        else:
            if response_.status != 200:
                await _raise_client_response_error(response_)
            result = await response_.json()
            _logger.debug('Client returning %s', result)
            result_len = len(result)
            if result_len != 1:
                raise ValueError(f'Result from {url} has {result_len} values')
            return result[0] if isinstance(result, list) else result


async def get(app: web.Application, url: Union[URL, str],
              type_or_obj: DesktopObjectTypeVar | type[DesktopObjectTypeVar],
              query_params: Optional[Mapping[str, str]] = None,
              headers: LooseHeaders | None = None,
              client_session: ClientSession | None = None) -> DesktopObjectTypeVar | None:
    """
    Co-routine that gets a HEA desktop object from a HEA service. It retries when connection errors occur.

    :param app: the aiohttp application context (required).
    :param url: The URL (str or URL) of the resource (required).
    :param type_or_obj: the expected HEA desktop object type, or a desktop object instance to populate with content. If a
    type, this function will attempt to create an instance using the type's no-arg constructor.
    :param query_params: optional Mapping, iterable of tuple of key/value pairs or string to be sent as parameters in the query string of the new request.
    :param headers: optional dict or MultiDict of headers. Attempts to set the Accept header will be ignored. The
    service will always receive Accepts: application/json.
    :param client_session: a client session. If None, the default session will be used.
    :return: the HEAObject populated with the resource's content, None if no such resource exists, or another HTTP
    status code if an error occurred.
    :raises aiohttp.client_exceptions.ClientResponseError: if the response's status code was unexpected.
    :raises aiohttp.client_exceptions.ClientConnectionError: if a connection to the service could not be established.
    """
    _logger = logging.getLogger(__name__)
    _logger.debug("about to make the GET client call ")
    if isinstance(type_or_obj, type) and issubclass(type_or_obj, root.DesktopObject):
        obj_ = type_or_obj()
    elif isinstance(type_or_obj, root.DesktopObject):
        obj_ = type_or_obj
    else:
        raise TypeError('obj must be a DesktopObject instance or a DesktopObject type')
    headers_ = CIMultiDict(headers) if headers is not None else CIMultiDict()
    headers_[hdrs.ACCEPT] = nvpjson.MIME_TYPE

    session = client_session if client_session is not None else _client_session(app)
    _logger.debug('Getting content at %s with headers %s', url, headers_)
    session_get_with_retry = async_retry_context_manager(ClientConnectionError, retries=5, cooldown=5)(session.get)
    async with session_get_with_retry(url, headers=headers_, params=query_params,
                           raise_for_status=False) as response_:
        if response_.status == 404:
            return None
        else:
            if response_.status != 200:
                await _raise_client_response_error(response_)
            result = await response_.json()
            _logger.debug('Client returning %s', result)
            result_len = len(result)
            if result_len != 1:
                raise ValueError(f'Result from {url} has {result_len} values')
            obj_.from_dict(result[0])
            _logger.debug('Got desktop object %s', obj_)
            return obj_

async def has(app: web.Application, url: Union[URL, str],
              type_or_obj: root.DesktopObject | type[root.DesktopObject] | None = None,
              query_params: Optional[Mapping[str, str]] = None,
              headers: LooseHeaders | None = None,
              client_session: ClientSession | None = None) -> bool:
    """
    Co-routine that checks whether a requested HEA desktop object exists. It retries when connection errors occur.

    :param app: the aiohttp application context (required).
    :param url: The URL (str or URL) of the resource (required).
    :param type_or_obj: the HEA desktop object type to populate with the resource's content, or a desktop object instance. If a
    type, this function will attempt to create an instance using the type's no-arg constructor.
    :param query_params: optional Mapping, iterable of tuple of key/value pairs or string to be sent as parameters in the query string of the new request.
    :param headers: optional dict or MultiDict of headers. Attempts to set the Accept header will be ignored. The
    service will always receive Accepts: application/json.
    :param client_session: a client session. If None, the default session will be used.
    :return: True or False.
    :raises aiohttp.client_exceptions.ClientResponseError: if the response's status code was unexpected.
    :raises aiohttp.client_exceptions.ClientConnectionError: if a connection to the service could not be established.
    """
    _logger = logging.getLogger(__name__)
    _logger.debug("about to make the GET client call ")
    if type_or_obj is None:
        pass
    elif isinstance(type_or_obj, type) and issubclass(type_or_obj, root.DesktopObject):
        pass
    elif isinstance(type_or_obj, root.DesktopObject):
        pass
    else:
        raise TypeError('obj must be an HEAObject instance or an HEAObject type')
    headers_ = CIMultiDict(headers) if headers is not None else CIMultiDict()
    headers_[hdrs.ACCEPT] = nvpjson.MIME_TYPE

    session = client_session if client_session is not None else _client_session(app)
    _logger.debug('Getting content at %s with headers %s', url, headers_)
    session_head_with_retry = async_retry_context_manager(ClientConnectionError, retries=5, cooldown=5)(session.head)
    async with session_head_with_retry(url, headers=headers_, params=query_params,
                                       raise_for_status=False) as response_:
        if response_.status == 404:
            return False
        else:
            if response_.status != 200:
                await _raise_client_response_error(response_)
            return True


async def get_all(app: web.Application, url: Union[URL, str], type_: Type[DesktopObjectTypeVar],
                  query_params: Optional[Mapping[str, str]] = None,
                  headers: LooseHeaders | None = None,
                  client_session: ClientSession | None = None) -> AsyncIterator[DesktopObjectTypeVar]:
    """
    Returns an iterator of the requested desktop objects. It retries when connection errors occur.

    :param app: the aiohttp application context (required).
    :param url: The URL (str or URL) of the resource (required).
    :param type_: the expected type of desktop object in the iterator.
    :param query_params: optional Mapping, iterable of tuple of key/value pairs or string to be sent as parameters in
    the query string of the new request.
    :param headers: optional dict or MultiDict of headers. Attempts to set the Accept header will be ignored. The
    service will always receive Accepts: application/json.
    :param client_session: a client session. If None, the default session will be used.
    :raises ClientResponseError: if the response's status code was unexpected.
    :raises ClientConnectionError: if a connection to the service could not be established.
    """
    _logger = logging.getLogger(__name__)
    if isinstance(type_, type) and issubclass(type_, root.DesktopObject):
        obj___ = type_
    else:
        raise TypeError('obj must be an HEAObject instance or an HEAObject type')
    headers_ = CIMultiDict(headers) if headers is not None else CIMultiDict()
    headers_[hdrs.ACCEPT] = nvpjson.MIME_TYPE

    session = client_session if client_session is not None else _client_session(app)
    _logger.debug('Getting content at %s with headers %s', url, headers_)
    session_get_with_retry = async_retry_context_manager(ClientConnectionError, retries=5, cooldown=5)(session.get)
    async with session_get_with_retry(url, params=query_params, headers=headers_, raise_for_status=False) as response_:
        if response_.status != 200:
            await _raise_client_response_error(response_)
        result = await response_.json()
        _logger.debug('Client returning %s', result)
        for r in result:
            obj__ = obj___()
            obj__.from_dict(r)
            yield obj__


async def get_all_list(app: web.Application, url: Union[URL, str], type_: Type[DesktopObjectTypeVar],
                       query_params: Optional[Mapping[str, str]] = None,
                       headers: LooseHeaders | None = None,
                       client_session: ClientSession | None = None) -> list[DesktopObjectTypeVar]:
    """
    Returns the requested desktop objects in a list. It retries when connection errors occur.

    :param app: the aiohttp application context (required).
    :param url: The URL (str or URL) of the resource (required).
    :param type_: the type to populate with the resource's content.
    :param query_params: optional Mapping, iterable of tuple of key/value pairs or string to be sent as parameters in the query string of the new request.
    :param headers: optional dict or MultiDict of headers. Attempts to set the Accept header will be ignored. The
    service will always receive Accepts: application/json.
    :param client_session: a client session. If None, the default session will be used.
    :return: a list of desktop objects with the provided type_.
    :raises ClientResponseError: if the response's status code was unexpected.
    :raises ClientConnectionError: if a connection to the service could not be established.
    """
    result: list[DesktopObjectTypeVar] = []
    async for obj in get_all(app, url, type_, query_params, headers, client_session):
        result.append(obj)
    return result


async def post(app: web.Application, url: Union[URL, str], data: root.DesktopObject | root.DesktopObjectDict,
               headers: LooseHeaders | None = None,
               client_session: ClientSession | None = None) -> str:
    """
    Coroutine that posts a HEAObject to a HEA service.

    :param app: the aiohttp application context (required).
    :param url: the The URL (str or URL) of the resource (required).
    :param data: the DesktopObject or DesktopObjectDict (required).
    :param headers: optional dict or MultiDict of headers. The Content-Type header is set to application/json,
    regardless of what it was set to in the passed-in headers.
    :param client_session: a client session. If None, the default session will be used.
    :return: the URL string in the response's Location header.
    :raises ClientResponseError: if the response's status code was unexpected.
    :raises TypeError: if the headers argument is not a MultiDict and cannot be pickled.
    """
    session = client_session if client_session is not None else _client_session(app)
    headers_ = CIMultiDict(headers) if headers is not None else CIMultiDict()
    headers_[hdrs.CONTENT_TYPE] = nvpjson.MIME_TYPE
    async with session.post(url, json=data, headers=headers_, raise_for_status=False) as response_:
        if response_.status != 201:
            await _raise_client_response_error(response_)
        return response_.headers['Location']


async def post_data_create(app: web.Application, url: Union[URL, str], data: dict[str, Any],
                           headers: LooseHeaders | None = None,
                           client_session: ClientSession | None = None) -> str:
    """
    Coroutine that posts JSON data to a HEA service that creates a new desktop object.

    :param app: the aiohttp application context (required).
    :param url: the The URL (str or URL) of the resource (required).
    :param data: the data to post (required).
    :param headers: optional dict or MultiDict of headers. The Content-Type header is set to application/json,
    regardless of what it was set to in the passed-in headers.
    :param client_session: a client session. If None, the default session will be used.
    :return: the id of the created object.
    :raises ClientResponseError: if the response's status code was unexpected.
    :raises TypeError: if the headers argument is not a MultiDict and cannot be pickled.
    :raises KeyError: if the response's Location header is missing.
    """
    session = client_session if client_session is not None else _client_session(app)
    headers_ = CIMultiDict(headers) if headers is not None else CIMultiDict()
    headers_[hdrs.CONTENT_TYPE] = nvpjson.MIME_TYPE
    async with session.post(url, json=data, headers=headers_, raise_for_status=False) as response_:
        if response_.status != 201:
            await _raise_client_response_error(response_)
        loc = response_.headers['Location']
        return loc.rsplit('/', 1)[1]


async def put(app: web.Application, url: Union[URL, str], data: root.DesktopObject | root.DesktopObjectDict,
              headers: LooseHeaders | None = None,
              client_session: ClientSession | None = None) -> None:
    """
    Coroutine that updates a HEAObject.

    :param app: the aiohttp application context (required).
    :param url: the The URL (str or URL) of the resource (required).
    :param data: the DesktopObject or DesktopObjectDict (required).
    :param headers: optional dict or MultiDict of headers. The Content-Type header is set to application/json,
    regardless of what it was set to in the passed-in headers.
    :param client_session: a client session. If None, the default session will be used.
    :returns if successful it returns None else if it fails it will raise HttpError
    :raises ClientResponseError: if the response's status code was unexpected.
    """
    session = client_session if client_session is not None else _client_session(app)
    # You can pass a desktop object into the json parameter because the session object is configured with a custom
    # json encoder that handles HEAObject.
    headers_ = CIMultiDict(headers) if headers is not None else CIMultiDict()
    headers_[hdrs.CONTENT_TYPE] = nvpjson.MIME_TYPE
    async with session.put(url, json=data, headers=headers_, raise_for_status=False) as response_:
        if response_.status != 204:
            await _raise_client_response_error(response_)


async def delete(app: web.Application, url: Union[URL, str],
                 headers: LooseHeaders | None = None,
                 client_session: ClientSession | None = None) -> None:
    """
    Coroutine that deletes a HEAObject.

    :param app: the aiohttp application context (required).
    :param url: the URL (str or URL) of the resource (required).
    :param headers: optional dict of headers.
    :param client_session: a client session. If None, the default session will be used.
    :returns if successful it returns None else if it fails it will raise an exception.
    :raises aiohttp.client_exceptions.ClientResponseError: if the response's status code was unexpected.
    :raises aiohttp.client_exceptions.ClientConnectionError: if a connection to the service could not be established.
    """
    _logger = logging.getLogger(__name__)
    session = client_session if client_session is not None else _client_session(app)
    _logger.debug('Deleting %s', str(url))
    async with session.delete(url, headers=headers, raise_for_status=False) as response_:
        if response_.status != 204:
            await _raise_client_response_error(response_)


async def get_component_by_name(app: web.Application, name: str,
                 client_session: ClientSession | None = None) -> Optional[Component]:
    """
    Gets the Component with the given name from the HEA registry service. It retries when connection errors occur.

    :param app: the aiohttp app.
    :param name: the component's name.
    :return: a Component instance or None (if not found).
    """
    return await get(app, URL(app[appproperty.HEA_REGISTRY]) / 'components' / 'byname' / name, Component,
                     client_session=client_session)

_get_component_cache: TTLCache[str, Component | None] = TTLCache(maxsize=128, ttl=30)

async def get_component(app: web.Application, type_or_type_name: Union[str, Type[root.DesktopObject]],
                        client_session: ClientSession | None = None) -> Component | None:
    """
    Gets the component corresponding to the HEA object type from the HEA registry service. It retries when connection
    errors occur. The results are cached.

    :param app: the aiohttp app.
    :param type_or_type_name: the desktop object type or type name of the resource.
    :param client_session: a client session. If None, the default session will be used.
    :return: the Component, or None if not found.
    :raises aiohttp.client_exceptions.ClientResponseError: if the response's status code was unexpected.
    :raises aiohttp.client_exceptions.ClientConnectionError: if a connection to the service could not be established.
    """
    from .heaobjectsupport import type_or_type_name_to_type
    type_name_ = type_or_type_name_to_type(type_or_type_name).get_type_name()
    if (result := _get_component_cache.get(type_name_)) is not None:
        return result
    else:
        url = URL(app[appproperty.HEA_REGISTRY]) / 'components' / 'bytype' / type_name_
        result = await get(app, url, Component, client_session=client_session)
        _get_component_cache[type_name_] = result
        return result


async def get_resource(app: web.Application, type_or_type_name: str | type[root.DesktopObject],
                       client_session: ClientSession | None = None) -> Resource | None:
    """
    Gets the resource corresponding to the HEA object type from the HEA registry service. It retries when connection
    errors occur. The results are cached.

    :param app: the aiohttp app.
    :param type_or_type_name: the HEAObject type or type name of the resource.
    :param client_session: a client session. If None, the default session will be used.
    :return: the Resource, or None if not found.
    :raises aiohttp.client_exceptions.ClientResponseError: if the response's status code was unexpected.
    :raises aiohttp.client_exceptions.ClientConnectionError: if a connection to the service could not be established.
    """
    from .heaobjectsupport import type_or_type_name_to_type
    component = await get_component(app, type_or_type_name, client_session=client_session)
    if component is not None:
        type_name_ = type_or_type_name_to_type(type_or_type_name).get_type_name()
        return component.get_resource(type_name_)
    else:
        return None


async def get_resource_url(app: web.Application, type_or_type_name: Union[str, Type[root.DesktopObject]],
                           client_session: ClientSession | None = None,
                           parameters: Optional[Mapping[str, Union[Sequence[Union[int, float, complex, str]], Mapping[str, Union[int, float, complex, str]], tuple[str, Union[int, float, complex, str]], int, float, complex, str]]] = None,
                           **kwargs: Union[Sequence[Union[int, float, complex, str]], Mapping[str, Union[int, float, complex, str]], tuple[str, Union[int, float, complex, str]], int, float, complex, str]) -> str | None:
    """
    Gets the resource URL corresponding to the HEA object type from the HEA registry service. The URL is constructed by
    joining the component's base URL and the resource base path. It retries when connection errors occur. The result is
    cached to avoid unnecessary calls to the registry service.

    :param app: the aiohttp app.
    :param type_or_type_name: the HEAObject type or type name of the resource.
    :param client_session: a client session. If None, the default session will be used.
    :param parameters: for resource URLs with a URI template, the template parameters.
    :param kwargs: alternative way to provide template parameters.
    :return: a URL string or None if no such resource is found in the registry service.
    :raises ValueError: if there was a problem accessing the registry service.
    """
    from .heaobjectsupport import type_or_type_name_to_type
    logger = logging.getLogger(__name__)
    component = await get_component(app, type_or_type_name, client_session=client_session)
    logger.debug('Got component %s from registry', component)
    type_name_ = type_or_type_name_to_type(type_or_type_name).get_type_name()
    return component.get_resource_url(type_name_, parameters=parameters, **kwargs) if component is not None else None

async def get_collection(type_or_type_name: Union[str, Type[root.HEAObject]]):
    pass

_get_property_cache: TTLCache[str, Property | None] = TTLCache(maxsize=128, ttl=30)

async def get_property(app: web.Application, name: str,
                       client_session: ClientSession | None = None) -> Property | None:
    """
    Gets the Property with the given name from the HEA registry service.  It retries when connection errors occur. The
    results are cached.

    :param app: the aiohttp app.
    :param name: the property's name.
    :param client_session: a client session. If None, the default session will be used.
    :return: a Property instance or None (if not found).
    """
    if (result := _get_property_cache.get(name)) is not None:
        return result
    else:
        result = await get(app, URL(app[appproperty.HEA_REGISTRY]) / 'properties' / 'byname' / name,
                           Property,
                           client_session=client_session)
        _get_property_cache[name] = result
        return result


async def _raise_client_response_error(response_: ClientResponse):
    """
    An alternative to aiohttp's raise_for_status() that uses the client
    response's body as the message.

    :param response_: the client response (required).
    :raises ClientResponseError: always except when a bad argument is provided.
    """
    raise ClientResponseError(request_info=response_.request_info, history=(response_,),
                                      status=response_.status, message=await response_.text(),
                                      headers=response_.headers)


def _client_session(app: web.Application) -> ClientSession:
    return cast(ClientSession, app[appproperty.HEA_CLIENT_SESSION])
