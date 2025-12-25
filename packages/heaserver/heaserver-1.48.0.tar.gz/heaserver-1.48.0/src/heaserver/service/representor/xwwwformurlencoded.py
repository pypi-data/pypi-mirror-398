"""
Form data representor. It only supports the parse method (form data to NVPJSON), and it does not support data values
with nested JSON objects.
"""

from urllib.parse import parse_qs
from .error import ParseException
from .representor import Representor, Link
from aiohttp.web import Request
from typing import Any, Union
from collections.abc import Iterable, Callable, Mapping
from heaobject.root import json_dumps
import logging


MIME_TYPE = 'application/x-www-form-urlencoded'


class XWWWFormURLEncoded(Representor):
    MIME_TYPE = MIME_TYPE

    async def formats(self, request: Request,
                      wstl_obj: Union[Iterable[Mapping[str, Any]], Mapping[str, Any]],
                      dumps=json_dumps,
                      link_callback: Callable[[int, Link], None] | None = None,
                      include_data=True) -> bytes:
        """
        Not implemented.
        """
        raise NotImplementedError

    async def parse(self, request: Request) -> dict[str, Any]:
        """
        Parses an HTTP POST request containing form data into a name-value pair dict-like object.

        :param request: the HTTP request. Cannot be None.
        :return: the data section of the Collection+JSON document transformed into a dict.
        """
        _logger = logging.getLogger(__name__)
        try:
            txt = await request.text()
            _logger.debug('Parsing %s', txt)
            result = parse_qs(txt, strict_parsing=True)
            _logger.debug('Parsed to %s', result)
            d = {k: (v if len(v) > 1 else v[0]) for k, v in result.items()}
            _logger.debug('Returning %s', d)
            return d
        except ValueError as e:
            raise ParseException from e


