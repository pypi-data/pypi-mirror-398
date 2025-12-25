"""
This module contains an abstract base class for parsing and formatting WeSTL documents, the Representor class. Concrete
implementations of Representor must implement the formats and parse methods. The formats method formats a run-time
WeSTL document into a response body, and the parse method parses an HTTP request body into name-value pairs. An
implementation may raise NotImplementedError if it does not support either formats or parse, but it must support at
least one of them.
"""
from yarl import URL
from aiohttp.web import Request
from typing import Union, Any, Optional
from abc import ABC
from collections.abc import Sequence, Iterable, Callable, Mapping
import abc
from dataclasses import dataclass
from heaobject.root import json_dumps


@dataclass
class Link:
    """
    Represents a Link for the link_callback callback that may be passed into the Representor.formats method. The href
    must be encoded.
    """
    href: Union[URL, str]
    rel: Sequence[str]
    prompt: Optional[str] = None


class Representor(ABC):
    """
    Abstract base class for formatting WeSTL documents into a response body and parsing an HTTP request body into a
    name-value pair JSON dict.
    """
    MIME_TYPE: str = ''

    @classmethod
    def supports_links(cls) -> bool:
        """
        The default implementation returns False to indicate that the representor does not support HTML links.
        Subclasses should override this method to return True.

        :return: False
        """
        return False

    @abc.abstractmethod
    async def formats(self, request: Request,
                      wstl_obj: Union[Iterable[Mapping[str, Any]], Mapping[str, Any]],
                      dumps=json_dumps,
                      link_callback: Callable[[int, Link], None] | None = None,
                      include_data=True) -> bytes:
        """
        Formats a run-time WeSTL document into a response body. The response body may vary substantially depending on
        the representor implementation. The data in the WeSTL document is always be included in the formatted data. In
        addition, an implementation may format the WeSTL document's actions into links with templated URLs and/or form
        templates.

        When populating the URL templates, this method substitutes any template parameters enclosed by curly braces
        with the values of matching request URL path parameters. Next, it replaces template parameters with matching
        attribute values from the desktop object being formatted, overwriting any previous matches.

        For form templates, default values of form fields are populated from similar sources but in a different order:
        first desktop object attribute values, followed by path parameter values from the request URL, followed by
        request header values, each successive source overwriting matching parameters from the previous one.

        :param request: the HTTP request.
        :param wstl_obj: dict with run-time WeSTL JSON, or a list of run-time WeSTL JSON dicts. Actions' paths
        containing variables enclosed by curly braces are matched by this method to attributes of the HEA object being
        processed, and are replaced with their values by this method. Nested JSON objects are referred to using dot
        syntax just like in python. URI templating follows the URI Template standard, RFC 6570, available at
        https://datatracker.ietf.org/doc/html/rfc6570.
        :param dumps: any callable that accepts dict with JSON and outputs str. Cannot be None. By default, it uses
        the heaobject.root.json_dumps function, which dumps HEAObjects and their attributes to JSON objects. Cannot
        be None.
        :param link_callback: a callable that will be invoked whenever a link is created from a WeSTL action in the
        wstl_obj. Links can be specific to a data item in the wstl_obj's data list or "global" to the entire data list.
        The first parameter contains the index of the data item, or None if the link is global. The second
        parameter contains the link as a heaserver.service.representor.Link object. The purpose of this
        callback is to access parameterized links after their parameters have been filled in.
        :param include_data: whether to include the data from the WSTL document in the response. Links are included in
        the response body regardless if the representor implementation supports them. Ensure that the request
        parameters and the WSTL data contain any information needed to generate the links.
        :return: a bytes object containing the formatted data.
        :raises ValueError: if an error occurs formatting the WeSTL document.
        """
        pass

    @abc.abstractmethod
    async def parse(self, request: Request) -> dict[str, Any]:
        """
        Parses an HTTP request body into a name-value pair dict-like object.

        :param request: the HTTP request. Cannot be None.
        :return: a dict.
        """
        pass

