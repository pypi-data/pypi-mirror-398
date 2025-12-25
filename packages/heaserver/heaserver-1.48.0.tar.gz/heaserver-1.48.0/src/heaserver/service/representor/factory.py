"""
A factory for getting a representor object from the heaserver.service.representor package for a provided mimetype. A
representor formats WeSTL documents into one of various output formats, and it may provide for parsing data represented
in the format into name-value pair (NVP) JSON. Supported mimetypes are application/vnd.wstl+json (WeSTL),
application/json (name-value pair JSON), and application/vnd.collection+json (Collection+JSON).
"""
from aiohttp import hdrs
from aiohttp.web import Request
import logging
from collections.abc import Iterable, Callable
from . import wstljson, nvpjson, cj, xwwwformurlencoded, representor
from accept_types import get_best_match
from typing import Any, Optional, Mapping, Type
from enum import Enum


# Priority-ordered mapping of mime types to representor implementation. The priority ordering is used by
# get_from_accepts_header() to select a representor when multiple candidate mime types are found in the Accepts header.
# Python dicts have guaranteed insertion order since version 3.7.
_mime_type_to_representor: Mapping[str, Type[representor.Representor]] = {
    cj.MIME_TYPE: cj.CJ,
    wstljson.MIME_TYPE: wstljson.WeSTLJSON,
    nvpjson.MIME_TYPE: nvpjson.NVPJSON,
    xwwwformurlencoded.MIME_TYPE: xwwwformurlencoded.XWWWFormURLEncoded
}


DEFAULT_REPRESENTOR = cj.CJ


class AcceptHeaderFilter(Enum):
    ANY = 1
    SUPPORTS_LINKS = 2


def from_mime_type(mime_type: str | None) -> representor.Representor | None:
    """
    Gets the representor supporting the given mime type.
    :param mime_type: the mime type, or None to return the default representor.
    :return: the chosen representor, or None if no representor corresponds to the given mime type.
    """
    if mime_type is None:
        return DEFAULT_REPRESENTOR()
    else:
        res = _mime_type_to_representor.get(mime_type)
        if res is None:
            return None
        else:
            return res()


def from_accept_header(accept: Optional[str], accept_header_filter: Optional[AcceptHeaderFilter] = None) -> representor.Representor | None:
    """
    Selects a representor from the contents of a HTTP Accept header.

    :param accept: an Accept header string.
    :param accept_header_filter: whether to consider only representors that support HTML links. None is equivalent to
    AcceptsHeaderFilter.ANY.
    :return: An object that implements the representor interface, described in the heaserver.service.representor
    package documentation. It will return a representor for Collection+JSON if the provided mimetype is None.
    If the Accept header doesn't match any of the support response content types, None will be returned.
    """
    def predicate(representor_: Type[representor.Representor]):
        if accept_header_filter in (None, AcceptHeaderFilter.ANY):
            return True
        if accept_header_filter == AcceptHeaderFilter.SUPPORTS_LINKS and representor_.supports_links():
            return True
        return False
    if accept is None:
        return DEFAULT_REPRESENTOR() if predicate(DEFAULT_REPRESENTOR) else None
    result = get_best_match(accept.lower(), (k for k, v in _mime_type_to_representor.items() if predicate(v)))
    if result is None:
        return None
    else:
        return _mime_type_to_representor[result]()


def from_content_type_header(content_type: Optional[str]) -> representor.Representor:
    """
    Selects a representor from the contents of a HTTP Content-Type header.

    :param content_type: the Content-Type header string.
    :return: An object that implements the representor interface, described in the heaserver.service.representor
    package documentation. It will return a representor for Collection+JSON if the provided mimetype is None or unknown.
    """
    if not content_type:
        return DEFAULT_REPRESENTOR()
    return _mime_type_to_representor.get(content_type.split(';')[0].strip().lower(), DEFAULT_REPRESENTOR)()


async def formats_from_request(request: Request,
                               run_time_docs: Iterable[Mapping[str, Any]] | Mapping[str, Any],
                               link_callback: Callable[[int, representor.Link], None] | None = None,
                               include_data = True) -> tuple[bytes, str]:
    """
    Renders the data from the run-time WeSTL documents as a list of objects formatted in the representor format
    specified in the request's Accept header.

    :param request: the HTTP request (required).
    :param run_time_docs: a list of run-time WeSTL documents, or a single run-time WeSTL document.
    :param link_callback: a callable that will be invoked whenever a link is created from a WeSTL action in the
    wstl_obj. Links can be specific to a data item in the wstl_obj's data list or "global" to the entire data list.
    The first parameter contains the index of the data item, or None if the link is global. The second
    parameter contains the link as a heaserver.service.representor.Link object. The purpose of this
    callback is to access parameterized links after their parameters have been filled in.
    :param include_data: whether to include the data in the response. If False, and the data parameter is not None
    and a non-empty dictionary, a 200 status code is returned and the data is omitted, but links are included in
    the response body. Ensure that the request parameters and data parameter contain any information needed to
    generate the links.
    :return: a two-tuple containing the data in a representor format and the format's mime type.
    :raises ValueError: if the request's Accept header doesn't request a representor mime type.
    """
    _logger = logging.getLogger(__name__)
    accept_header = request.headers.get(hdrs.ACCEPT, None)
    representor = from_accept_header(accept_header)
    if representor is None:
        raise ValueError(f'Invalid representor format in Accept header {accept_header}')
    _logger.debug('Using %s output format', representor)
    return await representor.formats(request, run_time_docs, link_callback=link_callback, include_data=include_data), representor.MIME_TYPE


async def formats_from_mime_type(mime_type: str | None, request: Request,
                                 run_time_docs: Iterable[Mapping[str, Any]] | Mapping[str, Any],
                                 link_callback: Callable[[int, representor.Link], None] | None = None) -> bytes:
    """
    Renders the data from the run-time WeSTL documents as a list of objects formatted in the representor format
    specified with the mime type.

    :param mime_type: the mime type. If None, the default format will be used (Collection+JSON).
    :param request: the HTTP request (required).
    :param run_time_docs: a list of run-time WeSTL documents, or a single run-time WeSTL document.
    :param link_callback: a callable that will be invoked whenever a link is created from a WeSTL action in the
    wstl_obj. Links can be specific to a data item in the wstl_obj's data list or "global" to the entire data list.
    The first parameter contains the index of the data item, or None if the link is global. The second
    parameter contains the link as a heaserver.service.representor.Link object. The purpose of this
    callback is to access parameterized links after their parameters have been filled in.
    :return: he data in a representor format.
    :raises ValueError: if the mime type is not a representor mime type.
    """
    representor = from_mime_type(mime_type)
    if representor is None:
        raise ValueError(f'Invalid representor mime type {mime_type}')
    return await representor.formats(request, run_time_docs, link_callback=link_callback)
