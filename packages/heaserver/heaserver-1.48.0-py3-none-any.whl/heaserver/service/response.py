"""
This module defines functions that create HTTP responses.

All GET responses except for OPTIONS include Cache-Control, Pragma, and Expires headers to request no caching.
"""
from aiohttp import web, hdrs
from aiohttp.client_exceptions import ClientResponseError
from aiohttp.helpers import ETag
from aiohttp.typedefs import LooseHeaders
from hashlib import md5
from heaobject.user import NONE_USER
from datetime import datetime
from .representor.factory import formats_from_request
from . import requestproperty, appproperty
from .appproperty import HEA_BACKGROUND_TASKS
from .oidcclaimhdrs import SUB
from .representor.representor import Link
from yarl import URL
import logging
from typing import Union, Optional, Any, Protocol
from collections.abc import Iterable, Mapping, Sequence
from .aiohttp import SupportsAsyncRead
from .wstl import RuntimeWeSTLDocumentBuilder
from heaobject.root import DesktopObjectDict, Permission
from multidict import istr, CIMultiDict
from .caching_strategy import CachingStrategy
from .util import to_http_date


TEXT_PLAIN_HTTP_HEADERS: Mapping[Union[str, istr], str] = CIMultiDict({hdrs.CONTENT_TYPE: 'text/plain; charset=UTF-8'})
NO_CACHE_HEADERS = CIMultiDict({hdrs.CACHE_CONTROL: 'no-cache, no-store, must-revalidate', hdrs.PRAGMA: 'no-cache', hdrs.EXPIRES: '0'})
DEFAULT_CONTENT_TYPE = 'application/json'


def status_generic(status: int, body: Optional[Union[bytes, str]] = None,
                   headers: LooseHeaders | None = None) -> web.Response:
    """
    Returns a newly created HTTP response object. This object is not an exception. To return an error response that
    can be raised as an exception, use status_generic_error().

    :param status: an HTTP status code (required).
    :param body: the response body (optional).
    :param headers: optional headers.
    :return: an HTTP response.
    """
    body_ = body.encode() if isinstance(body, str) else body
    return web.Response(status=status, body=body_, headers=headers)


def status_generic_error(status: int, body: Optional[Union[bytes, str]] = None,
                         headers: LooseHeaders | None = None) -> web.HTTPError:
    """
    Returns a newly created HTTP error response object. This object is an exception.

    :param status: an HTTP status code (required).
    :param body: the response body (optional).
    :param headers: optional headers.
    :return: an HTTPError that can be used a HTTP response or an exception.
    """
    if status < 400:
        raise ValueError(f'status must be an error code >=400 but was {status}')
    body_ = body.encode() if isinstance(body, str) else body
    class HTTPGenericError(web.HTTPError):
        status_code = status
    return HTTPGenericError(body=body_, headers=headers)


def status_not_found(body: Optional[Union[bytes, str]] = None,
                     headers: LooseHeaders | None = None) -> web.HTTPNotFound:
    """
    Returns a newly created HTTP response object with status code 404 and an optional body.

    :param body: the body of the message, typically an explanation of what was not found.  If a string, this function
    will encode it to bytes using UTF-8 encoding.
    :param headers: any headers that you want to add to the response. In addition, the response will have a
    Content-Type header that should not be overridden.
    :return: aiohttp.web.Response with a 404 status code.
    """
    if headers and 'Content-Type' in headers:
        raise ValueError('The Content-Type header cannot be overridden')
    headers_: CIMultiDict[str] = CIMultiDict(headers) if headers is not None else CIMultiDict()
    if isinstance(body, str):
        headers_.update(TEXT_PLAIN_HTTP_HEADERS)
    return web.HTTPNotFound(body=body.encode() if isinstance(body, str) else body, headers=headers_)


def status_multiple_choices(default_url: Union[URL, str], body: Optional[Union[bytes, str]] = None,
                            content_type: str = DEFAULT_CONTENT_TYPE) -> web.HTTPMultipleChoices:
    """
    Returns a newly created HTTP response object with status code 300. This is for implementing client-side content
    negotiation, described at https://developer.mozilla.org/en-US/docs/Web/HTTP/Content_negotiation.

    :param default_url: the URL of the default choice. Required.
    :param body: content with link choices.  If a string, this function will encode it to bytes using UTF-8 encoding.
    :param content_type: optional content_type (defaults to DEFAULT_CONTENT_TYPE). Cannot be None.
    :return: aiohttp.web.Response object with a 300 status code.
    """
    body_ = body.encode() if isinstance(body, str) else body
    return web.HTTPMultipleChoices(str(default_url),
                                   body=body_,
                                   headers={hdrs.CONTENT_TYPE: content_type,
                                            hdrs.LOCATION: str(default_url if default_url else '#')})


def status_moved(location: str | URL) -> web.HTTPMovedPermanently:
    """
    Returns a newly created HTTP response object with status code 301.

    :param location: the URL for the client to redirect to.
    :return: aiohttp.web.Response object with a 301 status code.
    """
    return web.HTTPMovedPermanently(location=str(location))


def status_bad_request(body: Optional[Union[bytes, str]] = None) -> web.HTTPBadRequest:
    """
    Returns a newly created HTTP response object with status code 400 and an optional body.

    :param body: the body of the message, typically an explanation of why the request is bad.  If a string, this
    function will encode it to bytes using UTF-8 encoding.
    :return: aiohttp.web.Response with a 400 status code.
    """
    body_ = body.encode() if isinstance(body, str) else body
    headers = TEXT_PLAIN_HTTP_HEADERS if isinstance(body, str) else None
    return web.HTTPBadRequest(body=body_, headers=headers)


def status_created(base_url: Union[URL, str], resource_base: str, inserted_id: str) -> web.HTTPCreated:
    """
    Returns a newly created HTTP response object with status code 201 and the Location header set.

    :param base_url: the service's base URL (required).
    :param resource_base: the common base path fragment for all resources of this type (required).
    :param inserted_id: the id of the newly created object (required).

    :return: aiohttp.web.Response with a 201 status code and the Location header set to the URL of the created object.
    """
    if inserted_id is None:
        raise ValueError('inserted_id cannot be None')
    return web.HTTPCreated(headers={hdrs.LOCATION: str(URL(base_url) / resource_base / str(inserted_id))})


def status_ok(body: Optional[Union[bytes, str]] = None, content_type: str = DEFAULT_CONTENT_TYPE,
              headers: LooseHeaders | None = None) -> web.HTTPOk:
    """
    Returns a newly created HTTP response object with status code 201, the provided Content-Type header, and the
    provided body.

    :param body: the body of the response. If a string, this function will encode it to bytes using UTF-8 encoding.
    :param content_type: the content type of the response (default is application/json).
    :param headers: any headers that you want to add to the response, in addition to the content type. If the content
    type is also in this dictionary, then its value will override that of the content_type argument. If the body is
    a string and no content type header is specified in either the content_type or headers argument, a default value
    for the content type will be used.
    :return: aiohttp.web.Response object with a 200 status code.
    """
    if isinstance(body, str):
        body_: bytes | None = body.encode()
    else:
        body_ = body
    headers_ = CIMultiDict(headers or {})
    if content_type is not None:
        headers_.update({hdrs.CONTENT_TYPE: content_type})
    if isinstance(body, str) and hdrs.CONTENT_TYPE not in headers_:
        headers_.update(TEXT_PLAIN_HTTP_HEADERS)
    return web.HTTPOk(headers=headers_, body=body_)


def status_no_content() -> web.HTTPNoContent:
    """
    Returns a newly created HTTP response object with status code 204.

    :return: aiohttp.web.Response object with a 204 status code.
    """
    return web.HTTPNoContent()


def status_not_acceptable(body: Optional[Union[bytes, str]] = None) -> web.HTTPNotAcceptable:
    """
    Returns a newly created HTTP response object with status code 406.

    :param body: the body of the message, typically an explanation of why the request is bad.  If a string, this
    function will encode it to bytes using UTF-8 encoding.
    :return: aiohttp.web.Response object with a 406 status code.
    """
    body_ = body.encode() if isinstance(body, str) else body
    return web.HTTPNotAcceptable(body=body_)


def status_internal_error(body: Optional[Union[bytes, str]] = None) -> web.HTTPInternalServerError:
    """
    Returns a newly created HTTP response object with status code 500.

    :param body: the body of the message, typically an explanation of why the request is bad.  If a string, this
    function will encode it to bytes using UTF-8 encoding.
    :return: aiohttp.web.Response object with a 500 status code.
    """
    body_ = body.encode() if isinstance(body, str) else body
    return web.HTTPInternalServerError(body=body_)


def status_from_exception(e: ClientResponseError) -> web.HTTPError:
    """
    Generates a response from an aiohttp ClientResponseError, using the status code and message from the ClientResponse
    object.

    :param e: a ClientResponseError object.
    :return: an web.HTTPError object with the ClientResponseError's status code and message.
    """
    return status_generic_error(status=e.status, body=e.message)


def status_forbidden(body: Optional[Union[bytes, str]] = None) -> web.HTTPForbidden:
    """
    Returns a newly created HTTP response object with status code 403.

    :param body: the body of the message, typically an explanation of why the request is bad.  If a string, this
    function will encode it to bytes using UTF-8 encoding.
    :return: aiohttp.web.Response object with a 403 status code.
    """
    body_ = body.encode() if isinstance(body, str) else body
    return web.HTTPForbidden(body=body_)


def status_see_other(location: URL | str) -> web.Response:
    return web.HTTPSeeOther(location)


def status_accepted() -> web.Response:
    return web.HTTPAccepted()


def status_conflict(body: Optional[Union[bytes, str]] = None) -> web.HTTPConflict:
    """
    Returns a newly created HTTP response object with status code 409.

    :param body: the body of the message, typically an explanation of why the request is in conflict.  If a string,
    this function will encode it to bytes using UTF-8 encoding.
    :return: aiohttp.web.Response object with a 409 status code.
    """
    body_ = body.encode() if isinstance(body, str) else body
    return web.HTTPConflict(body=body_)


def status_service_unavailable(body: Optional[Union[bytes, str]] = None, retry_after_seconds: int | None = None,
                               retry_after_date: datetime | None = None) -> web.HTTPServiceUnavailable:
    """
    Returns a newly created HTTP response object with status code 503.

    :param body: the body of the message, typically an explanation of why the request is in conflict.  If a string,
    this function will encode it to bytes using UTF-8 encoding.
    :param retry_after_seconds: the number of seconds to wait before retrying the request. If both this and
    retry_after_date are provided, this takes precedence.
    :param retry_after_date: the date to wait until before retrying the request. If both this and retry_after_seconds
    are provided, retry_after_seconds takes precedence.
    :return: aiohttp.web.Response object with a 503 status code.
    """
    body_ = body.encode() if isinstance(body, str) else body
    retry_after_val: str | None = None
    if retry_after_seconds is not None:
        retry_after_val = str(retry_after_seconds)
    elif retry_after_date is not None:
        retry_after_val = to_http_date(retry_after_date)
    headers = {hdrs.RETRY_AFTER: retry_after_val} if retry_after_val else None
    return web.HTTPServiceUnavailable(body=body_, headers=headers)

def status_precondition_required(body: Union[bytes, str] | None = None, content_type: str = DEFAULT_CONTENT_TYPE,
                                 headers: LooseHeaders | None = None) -> web.HTTPPreconditionRequired:
    """
    Returns a newly created HTTP response object with status code 428.

    :param body: the body of the message, typically a JSON-encoded object with the missing preconditions.
    :param content_type: the content type of the response (default is application/json).
    :param headers: any headers that you want to add to the response, in addition to the content type. If the content
    type is also in this dictionary, then its value will override that of the content_type argument. If the body is
    a string and no content type header is specified in either the content_type or headers argument, a default value
    for the content type will be used.
    :return: aiohttp.web.Response object with a 428 status code.
    """
    body_ = body.encode() if isinstance(body, str) else body
    headers_ = CIMultiDict(headers or {})
    if content_type is not None:
        headers_.update({hdrs.CONTENT_TYPE: content_type})
    if isinstance(body, str) and hdrs.CONTENT_TYPE not in headers_:
        headers_.update(TEXT_PLAIN_HTTP_HEADERS)
    return web.HTTPPreconditionRequired(headers=headers_, body=body_)

class GetterSuccessResponseFactory(Protocol):
    """
    Protocol for a function that creates a response object to a GET call that indicates success. The function takes as
    arguments the body, the content type, and optionally the caching strategy.
    """
    def __call__(self, body: bytes, mime_type: str,
                 caching_strategy: CachingStrategy | None = None) -> web.Response: ...


async def get(request: web.Request, data: Optional[DesktopObjectDict], permissions: Sequence[Permission] | None = None,
              attribute_permissions: Mapping[str, Sequence[Permission]] | None = None,
              include_data = True) -> web.Response:
    """
    Create and return a HTTP response object in response to a GET request for one or more HEA desktop object resources.
    The request headers are used to select a format for including the data and associated metadata such as links and
    permissions in the response body. See the wstl module and representor package for details.

    :param request: the HTTP request (required).
    :param data: a HEA desktop object dict. If None or an empty dictionary, the response will have a 404 Not Found
    status code.
    :param permissions: the object-level permissions for the desktop object. None or empty means that the permissions
    for the desktop object are unknown.
    :param attribute_permissions: the attribute-level permissions for the desktop object. None or empty means that the
    permissions for the desktop object are unknown.
    :param include_data: whether to include the data in the response. If False, and the data parameter is not None and
    a non-empty dictionary, a 200 status code is returned and the data is omitted, but links are included in the
    response body. Ensure that the request parameters and data parameter contain any information needed to generate the
    links. If include_data is False, the permissions and attribute_permissions parameters are ignored and should be
    omitted.
    :return: aiohttp.web.Response object, with status code 200, containing a body with the HEA desktop object, or
    status code 404 if the data argument is None.
    """
    if data:
        return await _handle_get_result(request, data,
                                        [permissions] if permissions is not None else None,
                                        [attribute_permissions] if attribute_permissions is not None else None,
                                        include_data=include_data)
    else:
        return web.HTTPNotFound()


async def get_multiple_choices(request: web.Request,
                               result: DesktopObjectDict | None = None,
                               caching_strategy: CachingStrategy | None = None) -> web.Response:
    """
    Create and return a HTTP response to a GET request with available links for opening the requested desktop
    object. Unlike with typical GET requests, this function generates a successful response with status code 300 to
    indicate that the endpoint is for the purpose of client-side content negotiation. More information about content
    negotiation is available from https://developer.mozilla.org/en-US/docs/Web/HTTP/Content_negotiation.

    The format of the links in the response body depends on the the result of server-side content negotiation using the
    request's Accept header and the REST endpoint's supported content types. The default content type is
    Collection+JSON.

    Multiple choice REST endpoints defining actions that have parameters not found in the endpoint's route require
    passing a desktop object into this function's result parameter. Failing to provide a desktop object for an endpoint
    requiring one has undefined behavior. For endpoints that do not require a desktop object, omitting one for an
    otherwise correct request will result in a successful response with a 300 status code and the options for opening
    the requested object, depending on the response body format negotiated between the client and server. To return an
    error status code, use the status_not_found() call or similar instead of this function.

    :param request: the HTTP request (required). If an Accepts header is provided, MIME types that do not support
    links will be ignored.
    :param result: a HEA desktop object dict (optional). As described above, some REST endpoints require this
    parameter to have a non-None value, otherwise the behavior is undefined. For REST endpoints that do not require
    a non-None value, a successful response should have a 300 status code.
    :param caching_strategy: the caching strategy to use. If None, then response headers are sent to request no caching.
    :return: aiohttp.web.Response object with status code 300, and a body containing the links representing possible
    choices for opening the HEA desktop object; status code 404 if no HEA desktop object dict was provided; or status
    code 406 if content negotiation failed to determine an acceptable content type.
    """
    _logger = logging.getLogger(__name__)
    wstl_builder: RuntimeWeSTLDocumentBuilder = request[requestproperty.HEA_WSTL_BUILDER]
    wstl_builder.href = str(request.url)

    default_url: Optional[Union[URL, str]] = None

    def link_callback(action_index: int, link: Link):
        nonlocal default_url
        if default_url is None or 'default' in link.rel:
            default_url = link.href
    try:
        body, mime_type = await wstl_builder.represent_from_request(request,
                                                                    [result] if result else None,
                                                                    link_callback=link_callback,
                                                                    include_data=False)
        _logger.debug('Response body is %s', body)
        etag = _compute_etag(body)
        if request.if_none_match and etag in request.if_none_match:
            return web.HTTPNotModified()
        response = status_multiple_choices(default_url=default_url if default_url else '#', body=body,
                                           content_type=mime_type)
        if caching_strategy:
            response.etag = etag
        else:
            response.headers.update(NO_CACHE_HEADERS)
        return response
    except ValueError as e:
        return status_not_acceptable(str(e))


async def get_from_wstl(request: web.Request, run_time_doc: dict[str, Any]) -> web.Response:
    """
    Handle a get request that returns a run-time WeSTL document. Any actions in the document are added to the
    request's run-time WeSTL documents, and the href of the action is prepended by the service's base URL. The actions
    in the provided run-time document are expected to have a relative href.

    :param request: the HTTP request (required).
    :param run_time_doc: a run-time WeSTL document containing data.
    :return: aiohttp.web.Response object with a body containing the object in a JSON array of objects.
    """
    return await _handle_get_result_from_wstl(request, [run_time_doc])


async def get_all_from_wstl(request: web.Request, run_time_docs: Iterable[dict[str, Any]]) -> web.Response:
    """
    Handle a get all request that returns one or more run-time WeSTL documents. Any actions in the documents are added
    to the request's run-time WeSTL documents, and the href of the action is prepended by the service's base URL. The
    actions in the provided run-time document are expected to have a relative href.

    :param request: the HTTP request (required).
    :param run_time_docs: a list of run-time WeSTL documents containing data.
    :return: aiohttp.web.Response object with a body containing the object in a JSON array of objects.
    """
    return await _handle_get_result_from_wstl(request, run_time_docs)


async def get_all(request: web.Request, data: Sequence[DesktopObjectDict],
                  permissions: Sequence[Sequence[Permission]] | None = None,
                  attribute_permissions: Sequence[Mapping[str, Sequence[Permission]]] | None = None) -> web.Response:
    """
    Create and return a Response object in response to a GET request for all HEA desktop object resources in a
    collection.

    :param request: the HTTP request (required).
    :param data: a list of HEA desktop object dicts.
    :return: aiohttp.web.Response object with a body containing the object in a JSON array of objects.
    """
    return await _handle_get_result(request, data, permissions, attribute_permissions)


async def get_options(request: web.Request, methods: Iterable[str]) -> web.Response:
    """
    Create and return a Response object in response to an OPTIONS request.

    :param request: the HTTP request (required).
    :param methods: the allowed HTTP methods.
    :return: an aiohttp.web.Response object with a 200 status code and an Allow header.
    """
    methods_ = ', '.join(methods)
    etag = _compute_etag(methods_)
    if request.if_none_match and etag in request.if_none_match:
        return web.HTTPNotModified()
    resp = web.HTTPOk()
    resp.headers[hdrs.ALLOW] = methods_
    return resp


async def get_streaming(request: web.Request, out: SupportsAsyncRead, content_type: str = DEFAULT_CONTENT_TYPE,
                        caching_strategy: CachingStrategy | None = None) -> web.StreamResponse:
    """
    Create and return a StreamResponse object in response to a GET request for the content associated with a HEA desktop
    object.

    :param request: the HTTP request (required).
    :param out: a file-like object with an asynchronous read() method (required). The stream is closed after all data
    is read from it.
    :param content_type: optional content type.
    :param caching_strategy: the caching strategy to employ. If unspecified, response headers are sent to request no
    caching.
    :return: aiohttp.web.StreamResponse object with status code 200.
    """
    logger = logging.getLogger(__name__)
    logger.debug('Getting content with content type %s', content_type)
    if content_type is not None:
        response_ = web.StreamResponse(status=200, reason='OK', headers={hdrs.CONTENT_TYPE: content_type})
    else:
        response_ = web.StreamResponse(status=200, reason='OK')
    await response_.prepare(request)
    try:
        while chunk := await out.read(1024):
            await response_.write(chunk)
    finally:
        out.close()

    await response_.write_eof()
    if not caching_strategy:
        response_.headers.update(NO_CACHE_HEADERS)
    return response_


async def post(request: web.Request, result: Optional[str], resource_base: str) -> web.Response:
    """
    Create and return a Response object in response to a POST request to create a new HEA desktop object resource.

    :param request: the HTTP request (required).
    :param result: the id of the POST'ed HEA object, or None if the POST failed due to a bad request.
    :param resource_base: the common base path for all resources of this type (required).
    :return: aiohttp.web.Response with Created status code and the URL of the created object, or a Response with a Bad
    Request status code if the result is None.
    """
    logger = logging.getLogger(__name__)
    if result is not None:
        return await _handle_post_result(request, resource_base, result)
    else:
        logger.debug('No result for request %s', request.url)
        return web.HTTPBadRequest()


async def put(result: bool) -> web.Response:
    """
    Handle the result from a put request.

    :param result: whether any objects were updated.
    :return: aiohttp.web.Response object with status code 203 (No Content) or 404 (Not Found).
    """
    if result:
        return web.HTTPNoContent()
    else:
        return web.HTTPNotFound()


async def delete(result: bool) -> web.Response:
    """
    Handle the result from a delete request.

    :param result: whether any objects were deleted.
    :return: aiohttp.web.Response object with status code 203 (No Content) or 404 (Not Found).
    """
    if result:
        return web.HTTPNoContent()
    else:
        return web.HTTPNotFound()

def get_async_status(request: web.Request) -> web.Response:
    """
    Implements asynchronous API status checking.

    :param request: the HTTP request (required).
    :return: the HTTP response.
    """
    logger = logging.getLogger(__name__)
    sub = request.headers.get(SUB, NONE_USER)
    background_tasks = request.app[HEA_BACKGROUND_TASKS]
    logger.debug('background tasks: %s', background_tasks)
    task_name = f'{sub}^{request.url}'
    if not background_tasks.contains(task_name):
        return status_not_found()
    if not background_tasks.done(task_name):
        return status_accepted()
    error = background_tasks.error(task_name)
    if error:
        background_tasks.remove(task_name)
        # In case we get an exception other than an HTTPException, raise it so it gets wrapped in an internal server
        # error response.
        raise error
    else:
        resp = background_tasks.result(task_name)
        background_tasks.remove(task_name)
        return resp


async def _handle_get_result(request: web.Request, data: Union[DesktopObjectDict, Sequence[DesktopObjectDict]],
                             permissions: Sequence[Sequence[Permission]] | None = None,
                             attribute_permissions: Sequence[Mapping[str, Sequence[Permission]]] | None = None,
                             include_data = True) -> web.Response:
    """
    Handle the result from a get request. Returns a Response object, the body of which will always contain a list of
    JSON objects.

    :param request: the HTTP request object. Cannot be None.
    :param data: the retrieved HEA desktop objects as a dict or dicts, with each dict representing a desktop object
    with its attributes as name-value pairs.
    :param permissions: the object-level permissions for the desktop object. None or empty means that the permissions
    for the desktop object are unknown.
    :param attribute_permissions: the attribute-level permissions for the desktop object. None or empty means that the
    permissions for the desktop object are unknown.
    :param include_data: whether to include the data in the response. If False, and the data parameter is not None and
    a non-empty dictionary, a 200 status code is returned and the data is omitted, but links are included in the
    response body. Ensure that the request parameters and data parameter contain any information needed to generate the
    links. If include_data is False, the permissions and attribute_permissions parameters are ignored and should be
    omitted.
    :return: aiohttp.web.Response object, either a 200 status code and the requested JSON object in the body, status
    code 404 (Not Found), or 500 (Internal Server Error) if the data is invalid.
    """
    logger = logging.getLogger(__name__)
    if data is not None:
        wstl_builder = request[requestproperty.HEA_WSTL_BUILDER]
        wstl_builder.href = str(request.url)
        try:
            data_ = data if isinstance(data, Sequence) else [data]
            body, mime_type = await wstl_builder.represent_from_request(request, data_,
                                                                        permissions=permissions,
                                                                        attribute_permissions=attribute_permissions,
                                                                        include_data=include_data)
            return _to_response(request, body, mime_type)
        except ValueError as e:
            logger.exception('Invalid input data %s', wstl_builder)
            return status_not_acceptable(str(e))
    else:
        return status_not_found()


def _to_response(request: web.Request, body: bytes, mime_type: str,
                 caching_strategy: CachingStrategy | None = None) -> web.Response:
    """
    Handle a get or get all request that returns one or more run-time WeSTL documents. Any actions in the documents are
    added to the request's run-time WeSTL documents, and the href of the action is prepended by the service's base URL.
    The actions in the provided run-time documents are expected to have a relative href.

    :param request: the HTTP request object (required).
    :param body: the response body (required).
    :param mime_type: the content type of the response (required).
    :param caching_strategy: what caching headers to send. By default, headers are generated to prevent caching.
    :return: aiohttp.web.Response object, with a 200 status code and the requested JSON objects in the body,
    status code 406 (Not Acceptable) if content negotiation failed to determine an acceptable content type, or status
    code 404 (Not Found).
    """
    _logger = logging.getLogger(__name__)
    _logger.debug('Run-time WeSTL document is %s', bytes)
    if caching_strategy:
        etag = _compute_etag(body)
        if request.if_none_match and etag in request.if_none_match:
            return web.HTTPNotModified()
    response = status_ok(body=body, content_type=mime_type, headers=NO_CACHE_HEADERS if not caching_strategy else None)
    if caching_strategy:
        response.etag = etag
    return response


async def _handle_get_result_from_wstl(request: web.Request,
                                       run_time_docs: Iterable[dict[str, Any]] | None,
                                       caching_strategy: CachingStrategy | None = None) -> web.Response:
    """
    Handle a get or get all request that returns one or more run-time WeSTL documents. Any actions in the documents are
    added to the request's run-time WeSTL documents, and the href of the action is prepended by the service's base URL.
    The actions in the provided run-time documents are expected to have a relative href.

    :param request: the HTTP request object. Cannot be None.
    :param run_time_docs: a list of run-time WeSTL documents containing data
    :param caching_strategy: what caching headers to send. By default, headers are generated to prevent caching.
    :return: aiohttp.web.Response object, with a 200 status code and the requested JSON objects in the body,
    status code 406 (Not Acceptable) if content negotiation failed to determine an acceptable content type, or status
    code 404 (Not Found).
    """
    _logger = logging.getLogger(__name__)
    _logger.debug('Run-time WeSTL document is %s', run_time_docs)
    if run_time_docs is not None:
        try:
            body, mime_type = await formats_from_request(request, run_time_docs)
            if caching_strategy:
                etag = _compute_etag(body)
                if request.if_none_match and etag in request.if_none_match:
                    return web.HTTPNotModified()
            response = status_ok(body=body, content_type=mime_type, headers=NO_CACHE_HEADERS if not caching_strategy else None)
            if caching_strategy:
                response.etag = etag
            return response
        except ValueError as e:
            return status_not_acceptable(str(e))
    else:
        return status_not_found()


async def _handle_post_result(request: web.Request, resource_base: str, inserted_id: str) -> web.Response:
    """
    Handle the result from a post request.

    :param request: the HTTP request object (required).
    :param resource_base: the common base path fragment for all resources of this type (required).
    :param inserted_id: the id of the newly created object (required).
    :return: aiohttp.web.Response object with status code 201 (Created).
    """
    return status_created(request.app[appproperty.HEA_COMPONENT], resource_base, inserted_id)


async def _get_options(methods: list[str]) -> web.Response:
    """
    Create and return a Response object in response to an OPTIONS request.

    :param methods: the allowed HTTP methods.
    :return: an aiohttp.web.Response object with a 200 status code and an Allow header.
    """
    resp = web.HTTPOk()
    resp.headers[hdrs.ALLOW] = ', '.join(methods)
    return resp


def _compute_etag(body: bytes | str, encoding='utf-8') -> ETag:
    """
    Computes an ETag from a bytes or str object.

    @param body: a bytes or str object.
    @param encoding: for bytes bodies, an optional encoding.
    @return: an ETag object.
    """
    if isinstance(body, str):
        body_ = body.encode(encoding)
    else:
        body_ = bytes(body)
    return ETag(md5(body_).hexdigest())
