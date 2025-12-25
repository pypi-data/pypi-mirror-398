from aiohttp import hdrs
import aiohttp.client_exceptions
from datetime import date
from yarl import URL
from heaserver.service.oidcclaimhdrs import SUB
from heaserver.service.aiohttp import client_session
from heaserver.service.db.database import get_collection_key_from_name
from heaobject.user import NONE_USER
from heaobject.root import deepcopy_heaobject_dict_with, deepcopy_heaobject_dict_with_deletions
from ..representor import wstljson, cj, nvpjson, xwwwformurlencoded
from urllib.parse import urlencode
from typing import TYPE_CHECKING, Callable, Awaitable, Any
from .microservicetestcase import MicroserviceTestCase
from .. import jsonschemavalidator
from ..util import async_retry
from collections.abc import Mapping, Sequence
from copy import deepcopy
from contextlib import closing
import logging

if TYPE_CHECKING:
    _Base = MicroserviceTestCase
else:
    _Base = object


class PostMixin(_Base):
    """Tester mixin for POST requests."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def test_post(self) -> None:
        """
        Checks if a POST request succeeds with a Collection+JSON template. The test is skipped if the body to POST
        (``_body_post``) is not defined.
        """
        if not self._body_post:
            self.skipTest('_body_post not defined')
        async with self.client.request('POST',
                                       (self._href / '').path,
                                       json=self._body_post,
                                       headers={**self._headers, hdrs.CONTENT_TYPE: cj.MIME_TYPE}) as obj:
            self.assertEqual('201: Created', await obj.text())

    async def test_post_nvpjson(self) -> None:
        """
        Checks if a POST request succeeds with a name-value-pair JSON template. The test is skipped if the body to POST
        (``_body_post``) is not defined.
        """
        if self._body_post is not None:
            async with self.client.request('POST',
                                           (self._href / '').path,
                                           json=cj.to_nvpjson(self._body_post),
                                           headers={**self._headers, hdrs.CONTENT_TYPE: nvpjson.MIME_TYPE}) as obj:
                self.assertEqual('201: Created', await obj.text())
        else:
            self.skipTest('_body_post not defined')

    async def test_post_xwwwformurlencoded(self) -> None:
        """
        Checks if a POST request succeeds with encoded form data. The test is skipped if either the body to POST
        (``_body_post``) is not defined or cannot be converted to encoded form data.
        """
        if not self._body_post:
            self.skipTest('_body_post not defined')
        try:
            data_ = self._post_data()
        except jsonschemavalidator.ValidationError:
            self.skipTest('_body_post cannot be converted xwwwformurlencoded form')
        async with self.client.request('POST',
                                       (self._href / '').path,
                                       data=data_,
                                       headers={**self._headers,
                                                hdrs.CONTENT_TYPE: xwwwformurlencoded.MIME_TYPE}) as obj:
            self.assertEqual('201: Created', await obj.text())

    async def test_post_status(self) -> None:
        """
        Checks if a POST request succeeds with status 201 when the request body is in Collection+JSON form. The
        test is skipped if the body to POST (``_body_post``) is not defined.
        """
        if not self._body_post:
            self.skipTest('_body_post not defined')
        async with self.client.request('POST',
                                       (self._href / '').path,
                                       json=self._body_post,
                                       headers={**self._headers, hdrs.CONTENT_TYPE: cj.MIME_TYPE}) as obj:
            self.assertEqual(201, obj.status)

    async def test_post_status_nvpjson(self) -> None:
        """
        Checks if a POST request succeeds with status 201 when the request body is in name-value-pair JSON form.
        The test is skipped if the body to POST (``_body_post``) is not defined.
        """
        if self._body_post is not None:
            async with self.client.request('POST',
                                           (self._href / '').path,
                                           json=cj.to_nvpjson(self._body_post),
                                           headers={**self._headers, hdrs.CONTENT_TYPE: nvpjson.MIME_TYPE}) as obj:
                self.assertEqual(201, obj.status)
        else:
            self.skipTest('_body_post not defined')

    async def test_post_status_xwwwformurlencoded(self) -> None:
        """
        Checks if a POST request succeeds with status 201 when the request body is encoded form data. The test is
        skipped if either the body to POST (``_body_post``) is not defined or cannot be converted to encoded form data.
        """
        if not self._body_post:
            self.skipTest('_body_post not defined')
        try:
            data_ = self._post_data()
        except jsonschemavalidator.ValidationError:
            self.skipTest('_body_post cannot be converted to xwwwformurlencoded form')
        async with self.client.request('POST',
                                       (self._href / '').path,
                                       data=data_,
                                       headers={**self._headers,
                                                hdrs.CONTENT_TYPE: xwwwformurlencoded.MIME_TYPE}) as obj:
            self.assertEqual(201, obj.status)

    async def test_post_then_get_status(self) -> None:
        """
        Checks if a GET request after a POST request succeeds with status 200 when the POST request body is in
        Collection+JSON form. The test is skipped if the body to POST (``_body_post``) is not defined.
        """
        if self._body_post is not None:
            async with self.client.request('POST',
                                           (self._href / '').path,
                                           json=self._body_post,
                                           headers={**self._headers, hdrs.CONTENT_TYPE: cj.MIME_TYPE}) as response:
                loc = response.headers.get(hdrs.LOCATION)
                if loc is None:
                    self.fail('no location header returned')
            async with self.client.request('GET',
                                           URL(loc).path,
                                           headers=self._headers) as response2:
                self.assertEqual(200, response2.status)
        else:
            self.skipTest('_body_post not defined')

    async def test_post_then_get_status_nvpjson(self) -> None:
        """
        Checks if a GET request after a POST request succeeds with status 200 when the POST request body is in
        name-value-pair JSON form. The test is skipped if the body to POST (``_body_post``) is not defined.
        """
        if self._body_post is not None:
            async with self.client.request('POST',
                                           (self._href / '').path,
                                           json=cj.to_nvpjson(self._body_post),
                                           headers={**self._headers, hdrs.CONTENT_TYPE: nvpjson.MIME_TYPE}) as response:
                loc = response.headers.get(hdrs.LOCATION)
                if loc is None:
                    self.fail('no location header returned')
            async with self.client.request('GET',
                                           URL(loc).path,
                                           headers=self._headers) as response2:
                self.assertEqual(200, response2.status)
        else:
            self.skipTest('_body_post not defined')

    async def test_post_then_get_status_xwwwformurlencoded(self) -> None:
        """
        Checks if a GET request after a POST request succeeds with status 200 when the POST request body is encoded form
        data. The test is skipped if either the body to POST (``_body_post``) is not defined or cannot be converted to
        encoded form data.
        """
        if self._body_post is not None:
            try:
                data_ = self._post_data()
            except jsonschemavalidator.ValidationError:
                self.skipTest('_body_post cannot be converted xwwwformurlencoded form')
                return
            async with self.client.request('POST',
                                           (self._href / '').path,
                                           data=data_,
                                           headers={**self._headers,
                                                    hdrs.CONTENT_TYPE: xwwwformurlencoded.MIME_TYPE}) as response:
                loc = response.headers.get(hdrs.LOCATION)
                if loc is None:
                    self.fail('no location header returned')
            async with self.client.request('GET',
                                           URL(loc).path,
                                           headers=self._headers) as response2:
                self.assertEqual(200, response2.status)
        else:
            self.skipTest('_body_post not defined')

    async def test_post_then_get(self) -> None:
        """
        Checks if the response body of a GET request after a POST request reflects the POST request body when the POST
        request body is in Collection+JSON form. The test is skipped if the body to POST (``_body_post``) is not
        defined.
        """
        if self._body_post:
            async with self.client.request('POST',
                                           (self._href / '').path,
                                           json=self._body_post,
                                           headers={**self._headers, hdrs.CONTENT_TYPE: cj.MIME_TYPE}) as response:
                loc = response.headers.get(hdrs.LOCATION)
                if loc is None:
                    self.fail('no location header returned')
            async with self.client.request('GET',
                                           URL(loc).path,
                                           headers={**self._headers, hdrs.ACCEPT: nvpjson.MIME_TYPE}) as response2:
                body_post = cj.to_nvpjson(self._body_post)
                for k, v in body_post.items():
                    if isinstance(v, date):
                        body_post[k] = v.isoformat()
                try:
                    received_json = next(iter(await response2.json()))
                    self.assertEqual(body_post, {k: v for k, v in received_json.items() if k in body_post})
                except aiohttp.client_exceptions.ContentTypeError as e:
                    raise AssertionError(f'POST did not post, so GET failed: {e}') from e
        else:
            self.skipTest('_body_post not defined')

    async def test_post_then_get_nvpjson(self) -> None:
        """
        Checks if the response body of a GET request after a POST request reflects the POST request body when the POST
        request body is in name-value-pair JSON form. The test is skipped if the body to POST (``_body_post``) is
        not defined.
        """
        if self._body_post:
            body_post = cj.to_nvpjson(self._body_post)
            async with self.client.request('POST',
                                           (self._href / '').path,
                                           json=body_post,
                                           headers={**self._headers, hdrs.CONTENT_TYPE: nvpjson.MIME_TYPE}) as response:
                loc = response.headers.get(hdrs.LOCATION)
                if loc is None:
                    self.fail('no location header returned')
            async with self.client.request('GET',
                                           URL(loc).path,
                                           headers={**self._headers, hdrs.ACCEPT: nvpjson.MIME_TYPE}) as response2:
                for k, v in body_post.items():
                    if isinstance(v, date):
                        body_post[k] = v.isoformat()
                try:
                    received_json = next(iter(await response2.json()))
                    self.assertEqual(body_post, {k: v for k, v in received_json.items() if k in body_post})
                except aiohttp.client_exceptions.ContentTypeError as e:
                    raise AssertionError(f'POST did not post, so GET failed: {e}') from e
        else:
            self.skipTest('_body_post not defined')

    async def test_post_then_get_xwwwformurlencoded(self) -> None:
        """
        Checks if the response body of a GET request after a POST request reflects the POST request body when the
        POST request body is encoded form data. The test is skipped if either the body to POST (``_body_post``) is
        not defined or cannot be converted to encoded form data.
        """
        if self._body_post:
            try:
                data_ = self._post_data()
            except jsonschemavalidator.ValidationError:
                self.skipTest('_body_post cannot be converted xwwwformurlencoded form')
            async with self.client.request('POST',
                                           (self._href / '').path,
                                           data=data_,
                                           headers={**self._headers,
                                                    hdrs.CONTENT_TYPE: xwwwformurlencoded.MIME_TYPE}) as response:
                loc = response.headers.get(hdrs.LOCATION)
                if loc is None:
                    self.fail('no location header returned')
            async with self.client.request('GET',
                                           URL(loc).path,
                                           headers={**self._headers, hdrs.ACCEPT: nvpjson.MIME_TYPE}) as response2:
                body_post = cj.to_nvpjson(self._body_post)
                for k, v in body_post.items():
                    if isinstance(v, date):
                        body_post[k] = v.isoformat()
                try:
                    received_json = next(iter(await response2.json()))
                    self.assertEqual(body_post, {k: v for k, v in received_json.items() if k in body_post})
                except aiohttp.client_exceptions.ContentTypeError as e:
                    raise AssertionError(f'POST did not post, so GET failed: {e}') from e
        else:
            self.skipTest('_body_post not defined')

    async def test_post_status_wrong_format_nvpjson_cj(self) -> None:
        """
        Checks if a POST request fails with status 400 when the request body is name-value-pair JSON but the content
        type is Collection+JSON. The test is skipped if the body to POST (``_body_post``) is not defined.
        """
        if not self._body_post:
            self.skipTest('_body_post not defined')
        else:
            async with self.client.request('POST',
                                           (self._href / '').path,
                                           json=cj.to_nvpjson(self._body_post),
                                           headers={**self._headers, hdrs.CONTENT_TYPE: cj.MIME_TYPE}) as obj:
                self.assertEqual(400, obj.status)

    async def test_post_status_wrong_format_xwwwformurlencoded_nvpjson(self) -> None:
        """
        Checks if a POST request fails with status 400 when the request body is encoded form data but the content type
        is name-value-pair JSON. The test is skipped if either the body to POST (``_body_post``) is not defined or the
        data cannot be converted to encoded form data.
        """
        if self._body_post is not None:
            try:
                data_ = self._post_data()
            except jsonschemavalidator.ValidationError:
                self.skipTest('_body_post cannot be converted to xwwwformurlencoded form')
                return
            async with self.client.request('POST',
                                           (self._href / '').path,
                                           data=data_,
                                           headers={**self._headers, hdrs.CONTENT_TYPE: nvpjson.MIME_TYPE}) as obj:
                self.assertEqual(400, obj.status)
        else:
            self.skipTest('_body_post not defined')

    async def test_post_status_wrong_format_cj_xwwwformurlencoded(self) -> None:
        """
        Checks if a POST request fails with status 400 when the request body is in Collection+JSON but the content type
        is encoded form data. The test is skipped if the body to POST (``_body_post``) is not defined.
        """
        if not self._body_post:
            self.skipTest('_body_post not defined')
        async with self.client.request('POST',
                                       (self._href / '').path,
                                       json=self._body_post,
                                       headers={**self._headers,
                                                hdrs.CONTENT_TYPE: xwwwformurlencoded.MIME_TYPE}) as obj:
            self.assertEqual(400, obj.status)

    async def test_post_status_wrong_format_xwwwformurlencoded_cj(self) -> None:
        """
        Checks if a POST request fails with status 400 when the request body is encoded form data but the content
        type is Collection+JSON. The test is skipped if either the body to POST (``_body_post``) is not defined or the
        data cannot be converted to encoded form data.
        """
        if not self._body_post:
            self.skipTest('_body_post not defined')
        try:
            data_ = self._post_data()
        except jsonschemavalidator.ValidationError:
            self.skipTest('_body_post cannot be converted to xwwwformurlencoded form')
            return
        async with self.client.request('POST',
                                       (self._href / '').path,
                                       data=data_,
                                       headers={**self._headers, hdrs.CONTENT_TYPE: cj.MIME_TYPE}) as obj:
            self.assertEqual(400, obj.status)

    async def test_post_status_wrong_format_cj_nvpjson(self) -> None:
        """
        Checks if a POST request fails with status 400 when the request body is in Collection+JSON but the content type
        is name-value-pair JSON. The test is skipped if either the body to POST (``_body_post``) is not defined or the
        data cannot be converted to encoded form data.
        """
        if not self._body_post:
            self.skipTest('_body_post not defined')
        async with self.client.request('POST',
                                       (self._href / '').path,
                                       json=self._body_post,
                                       headers={**self._headers, hdrs.CONTENT_TYPE: nvpjson.MIME_TYPE}) as obj:
            self.assertEqual(400, obj.status)

    async def test_post_status_wrong_format_nvpjson_xwwwformurlencoded(self) -> None:
        """
        Checks if a POST request fails with status 400 when the request body is name-value-pair JSON but the content
        type is encoded form data. The test is skipped if the body to POST (``_body_post``) is not defined.
        """
        if not self._body_post:
            self.skipTest('_body_post not defined')
        else:
            async with self.client.request('POST',
                                           (self._href / '').path,
                                           json=cj.to_nvpjson(self._body_post),
                                           headers={**self._headers,
                                                    hdrs.CONTENT_TYPE: xwwwformurlencoded.MIME_TYPE}) as obj:
                self.assertEqual(400, obj.status)

    async def test_post_empty_body(self) -> None:
        """
        Checks if a GET all request after a POST request whose request body MIME type is declared to be
        Collection+JSON shows that the POST request failed when the POST request body was empty. This test may falsely
        pass if a good POST request also does not post anything.
        """
        async with self.client.request('POST',
                                       (self._href / '').path,
                                       headers={**self._headers, hdrs.CONTENT_TYPE: cj.MIME_TYPE}):
            pass
        async with self.client.request('GET',
                                       (self._href / '').path,
                                       headers={**self._headers, hdrs.ACCEPT: nvpjson.MIME_TYPE}) as response:
            self.assertEqual(2, len(await response.json()), 'POST posted something')

    async def test_post_empty_body_nvpjson(self) -> None:
        """
        Checks if a GET all request after a POST request whose request body MIME type is declared to be
        name-value-pair JSON shows that the POST request failed when the POST request body was empty. This test may
        falsely pass if a good POST request also does not post anything.
        """
        async with self.client.request('POST',
                                       (self._href / '').path,
                                       headers={**self._headers, hdrs.CONTENT_TYPE: nvpjson.MIME_TYPE}):
            pass
        async with self.client.request('GET',
                                       (self._href / '').path,
                                       headers={**self._headers, hdrs.ACCEPT: nvpjson.MIME_TYPE}) as response:
            self.assertEqual(2, len(await response.json()), 'POST posted something')

    async def test_post_empty_body_xwwwformurlencoded(self) -> None:
        """
        Checks if a GET all request after a POST request whose request body MIME type is declared to be encoded form
        data shows that the POST request failed when the POST request body was empty. This test may falsely pass if a
        good POST request also does not post anything.
        """
        async with self.client.request('POST',
                                       (self._href / '').path,
                                       headers={**self._headers, hdrs.CONTENT_TYPE: xwwwformurlencoded.MIME_TYPE}):
            pass
        async with self.client.request('GET',
                                       (self._href / '').path,
                                       headers={**self._headers, hdrs.ACCEPT: nvpjson.MIME_TYPE}) as response:
            self.assertEqual(2, len(await response.json()), 'POST posted something')

    async def test_post_status_empty_body(self) -> None:
        """
        Checks if a POST request fails with status 400 when the request body is declared with type Collection+JSON but
        actually is empty. The test is skipped if the body that would normally be POSTed (``_body_post``) is not
        defined.
        """
        if not self._body_post:
            self.skipTest('_body_post not defined')
        async with self.client.request('POST',
                                       (self._href / '').path,
                                       headers={**self._headers, hdrs.CONTENT_TYPE: cj.MIME_TYPE}) as obj:
            self.assertEqual(400, obj.status)

    async def test_post_status_empty_body_nvpjson(self) -> None:
        """
        Checks if a POST request fails with status 400 when the request body is declared with type name-value-pair JSON
        but actually is empty. The test is skipped if the body that would normally be POSTed (``_body_post``) is not
        defined.
        """
        if not self._body_post:
            self.skipTest('_body_post not defined')
        async with self.client.request('POST',
                                       (self._href / '').path,
                                       headers={**self._headers, hdrs.CONTENT_TYPE: nvpjson.MIME_TYPE}) as obj:
            self.assertEqual(400, obj.status)

    async def test_post_status_empty_body_xwwwformurlencoded(self) -> None:
        """
        Checks if a POST request fails with status 400 when the request body is declared as encoded form data but
        actually is empty. The test is skipped if the body that would normally be POSTed (``_body_post``) is not
        defined.
        """
        if not self._body_post:
            self.skipTest('_body_post not defined')
        async with self.client.request('POST',
                                       (self._href / '').path,
                                       headers={**self._headers,
                                                hdrs.CONTENT_TYPE: xwwwformurlencoded.MIME_TYPE}) as obj:
            self.assertEqual(400, obj.status)

    async def test_post_status_invalid_type(self) -> None:
        """
        Checks if a POST request fails with status 400 when the declared type is invalid. The test is skipped if the
        unmodified body to POST (``_body_post``) is not defined.
        """
        if not self._body_post:
            self.skipTest('_body_post not defined')
        await self._test_invalid({'type': 'foo.bar'})

    async def test_post_status_invalid_created_datetime_string(self) -> None:
        """
        Checks if a POST request fails with status 400 when the ``created`` field has an invalid ISO-8601 datetime
        string. The test is skipped if the unmodified body to POST (``_body_post``) is not defined.
        """
        if not self._body_post:
            self.skipTest('_body_post not defined')
        await self._test_invalid({'created': 'not a time string'})

    async def test_post_status_invalid_created_type(self) -> None:
        """
        Checks if a POST request fails with status 400 when the ``created`` field is of an invalid type. The test is
        skipped if the unmodified body to POST (``_body_post``) is not defined.
        """
        if not self._body_post:
            self.skipTest('_body_post not defined')
        await self._test_invalid({'created': 2})

    async def test_post_status_invalid_modified_datetime_string(self) -> None:
        """
        Checks if a POST request fails with status 400 when the ``modified`` field has an invalid ISO-8601 datetime
        string. The test is skipped if the unmodified body to POST (``_body_post``) is not defined.
        """
        if not self._body_post:
            self.skipTest('_body_post not defined')
        await self._test_invalid({'modified': 'not a time string'})

    # Will be resolved later
    # async def test_post_status_invalid_derived_from_none(self) -> None:
    #     """
    #     Checks if a POST request fails with status 400 when the ``derived_from`` field is passed ``None``. The test is
    #     skipped if the unmodified body to POST (``_body_post``) is not defined.
    #     """
    #     if not self._body_post:
    #         self.skipTest('_body_post not defined')
    #     await self._test_invalid({'derived_from': None})
    #
    # async def test_post_status_valid_derived_from_missing(self) -> None:
    #     """
    #     Checks if a POST request succeeds with status 201 when the ``derived_from`` field is missing (it should be
    #     assigned a default value). The test is skipped if the unmodified body to POST (``_body_post``) is not
    #     defined.
    #     """
    #     if not self._body_post:
    #         self.skipTest('_body_post not defined')
    #     await self._test_valid_with_deletions(['derived_from'])
    #
    # async def test_post_status_invalid_derived_from_item_type(self) -> None:
    #     """
    #     Checks if a POST request fails with status 400 when the ``derived_from`` field is passed an iterable that
    #     contains an object that is not a string. The test is skipped if the unmodified body to POST
    #     (``_body_post``) is not defined.
    #     """
    #     if not self._body_post:
    #         self.skipTest('_body_post not defined')
    #     await self._test_invalid({'derived_from': ['1', 2, '3']})
    #
    # async def test_post_status_invalid_derived_from_iterable_type(self) -> None:
    #     """
    #     Checks if a POST request fails with status 400 when the ``derived_from`` field is not passed an iterable. The
    #     test is skipped if the unmodified body to POST (``_body_post``) is not defined.
    #     """
    #     if not self._body_post:
    #         self.skipTest('_body_post not defined')
    #     await self._test_invalid({'derived_from': 2})

    async def test_post_status_valid_invites_none(self) -> None:
        """
        Checks if a POST request succeeds with status 201 when the ``invites`` field is passed ``None``. The test is
        skipped if the unmodified body to POST (``_body_post``) is not defined.
        """
        if not self._body_post:
            self.skipTest('_body_post not defined')
        else:
            changed = deepcopy_heaobject_dict_with(cj.to_nvpjson(self._body_post), {'invites': None})
            async with self.client.request('POST',
                                           (self._href / '').path,
                                           json=changed,
                                           headers={**self._headers, hdrs.CONTENT_TYPE: nvpjson.MIME_TYPE}) as obj:
                self.assertEqual(201, obj.status)

    async def test_post_status_valid_invites_missing(self) -> None:
        """
        Checks if a POST request succeeds with status 201 when the ``invites`` field is missing (it should be
        assigned a default value). The test is skipped if the unmodified body to POST (``_body_post``) is not
        defined.
        """
        if not self._body_post:
            self.skipTest('_body_post not defined')
        await self._test_valid_with_deletions(['invites'])

    async def test_post_status_invalid_invites_item_type(self) -> None:
        """
        Checks if a POST request fails with status 400 when the ``invites`` field is passed an iterable that contains
        an object that is not a ``heaobject.root.Invite``. The test is skipped if the unmodified body to POST
        (``_body_post``) is not defined.
        """
        if not self._body_post:
            self.skipTest('_body_post not defined')
        await self._test_invalid({'invites': ['lonely']})

    async def test_post_status_invalid_invites_iterable_type(self) -> None:
        """
        Checks if a POST request fails with status 400 when the ``invites`` field is not passed an iterable. The test
        is skipped if the unmodified body to POST (``_body_post``) is not defined.
        """
        if not self._body_post:
            self.skipTest('_body_post not defined')
        await self._test_invalid({'invites': 2})

    async def test_post_status_invalid_shares_item_type(self) -> None:
        """
        Checks if a POST request fails with status 400 when the ``shares`` field is passed an iterable that contains an
        object that is not a ``heaobject.root.Share``. The test is skipped if the unmodified body to POST
        (``_body_post``) is not defined.
        """
        if not self._body_post:
            self.skipTest('_body_post not defined')
        await self._test_invalid({'user_shares': ['lonely']})

    async def test_post_status_invalid_shares_iterable_type(self) -> None:
        """
        Checks if a POST request fails with status 400 when the ``shares`` field is not passed an iterable. The test
        is skipped if the unmodified body to POST (``_body_post``) is not defined.
        """
        if not self._body_post:
            self.skipTest('_body_post not defined')
        await self._test_invalid({'user_shares': 2})

    async def test_post_then_get_invalid_type(self) -> None:
        """
        Checks if a GET all request after a bad POST request does not demonstrate that the POST request succeeded
        when the declared type is invalid. The test is skipped if the unmodified body to POST (``_body_post``)
        is not defined. This test may falsely pass if a good POST request also does not post anything.
        """
        if not self._body_post:
            self.skipTest('_body_post not defined')
        await self._test_post_then_get_invalid({'type': 'foo.bar'})

    async def test_post_then_get_invalid_created_datetime_string(self) -> None:
        """
        Checks if a GET all request after a bad POST request does not demonstrate that the POST request succeeded
        when the ``created`` field has an invalid ISO-8601 datetime string. The test is skipped if the
        unmodified body to POST (``_body_post``) is not defined. This test may falsely pass if a good POST request
        also does not post anything.
        """
        if not self._body_post:
            self.skipTest('_body_post not defined')
        await self._test_post_then_get_invalid({'created': 'not a datetime string'})

    async def test_post_then_get_invalid_created_type(self) -> None:
        """
        Checks if a GET all request after a bad POST request does not demonstrate that the POST request succeeded
        when the ``created`` field is of an invalid type. The test is skipped if the unmodified body to POST
        (``_body_post``) is not defined. This test may falsely pass if a good POST request also does not post anything.
        """
        if not self._body_post:
            self.skipTest('_body_post not defined')
        await self._test_post_then_get_invalid({'created': 2})

    async def test_post_then_get_invalid_modified_datetime_string(self) -> None:
        """
        Checks if a GET all request after a bad POST request does not demonstrate that the POST request succeeded
        when the ``modified`` field has an invalid ISO-8601 datetime string. The test is skipped if the
        unmodified body to POST (``_body_post``) is not defined. This test may falsely pass if a good POST request
        also does not post anything.
        """
        if not self._body_post:
            self.skipTest('_body_post not defined')
        await self._test_post_then_get_invalid({'modified': 'not a datetime string'})

    # Will be resolved later
    # async def test_post_then_get_invalid_derived_from_none(self) -> None:
    #     """
    #     Checks if a GET all request after a bad POST request does not demonstrate that the POST request succeeded
    #     when the ``derived_from`` field is passed ``None``. The test is skipped if the unmodified body to POST
    #     (``_body_post``) is not defined. This test may falsely pass if a good POST request also does not post anything.
    #     """
    #     if not self._body_post:
    #         self.skipTest('_body_post not defined')
    #     await self._test_post_then_get_invalid({'derived_from': None})
    #
    # async def test_post_then_get_invalid_derived_from_item_type(self) -> None:
    #     """
    #     Checks if a GET all request after a bad POST request does not demonstrate that the POST request succeeded
    #     when the ``derived_from`` field is passed an iterable that contains an object that is not a string. The test
    #     is skipped if the unmodified body to POST (``_body_post``) is not defined. This test may falsely pass if
    #     a good POST request also does not post anything.
    #     """
    #     if not self._body_post:
    #         self.skipTest('_body_post not defined')
    #     await self._test_post_then_get_invalid({'derived_from': ['1', 2, '3']})
    #
    # async def test_post_then_get_invalid_derived_from_iterable_type(self) -> None:
    #     """
    #     Checks if a GET all request after a bad POST request does not demonstrate that the POST request succeeded
    #     when the ``derived_from`` field is not passed an iterable. The test is skipped if the unmodified body to
    #     POST (``_body_post``) is not defined. This test may falsely pass if a good POST request also does not post
    #     anything.
    #     """
    #     if not self._body_post:
    #         self.skipTest('_body_post not defined')
    #     await self._test_post_then_get_invalid({'derived_from': 2})

    async def test_post_then_get_valid_invites_none(self) -> None:
        """
        Checks if a GET request after a POST request succeeds and returns the expected data when the ``invites``
        field is passed ``None``. The test is skipped if the unmodified body to POST (``_body_post``) is not
        defined.
        """
        if not self._body_post:
            self.skipTest('_body_post not defined')
        else:
            body_post = deepcopy_heaobject_dict_with(cj.to_nvpjson(self._body_post), {'invites': None})
            async with self.client.request('POST',
                                           (self._href / '').path,
                                           json=body_post,
                                           headers={**self._headers, hdrs.CONTENT_TYPE: nvpjson.MIME_TYPE}) as response:
                pass
            async with await self.client.request('GET',
                                                 URL(response.headers[hdrs.LOCATION]).path,
                                                 headers={**self._headers, hdrs.ACCEPT: nvpjson.MIME_TYPE}) as response2:
                try:
                    expected_post = deepcopy_heaobject_dict_with(cj.to_nvpjson(self._body_post), {'invites': []})
                except TypeError as e:
                    raise AssertionError(f'POST did not post, so the GET call cannot be made: {e}') from e
                for k, v in expected_post.items():
                    if isinstance(v, date):
                        expected_post[k] = v.isoformat()
                try:
                    received_json = next(iter(await response2.json()))
                    if 'id' in received_json:
                        del received_json['id']
                    self.assertEqual(expected_post, {k: v for k, v in received_json.items() if k in expected_post})
                except aiohttp.client_exceptions.ContentTypeError as e:
                    raise AssertionError(f'POST did not post, so GET failed: {e}') from e

    async def test_post_then_get_invalid_invites_item_type(self) -> None:
        """
        Checks if a GET all request after a bad POST request does not demonstrate that the POST request succeeded
        when the ``invites`` field is passed an iterable that contains an object that is not a
        ``heaobject.root.Invite``. The test is skipped if the unmodified body to POST (``_body_post``) is not
        defined. This test may falsely pass if a good POST request also does not post anything.
        """
        if not self._body_post:
            self.skipTest('_body_post not defined')
        await self._test_post_then_get_invalid({'invites': ['lonely']})

    async def test_post_then_get_invalid_invites_iterable_type(self) -> None:
        """
        Checks if a GET all request after a bad POST request does not demonstrate that the POST request succeeded
        when the ``invites`` field is not passed an iterable. The test is skipped if the unmodified body to POST
        (``_body_post``) is not defined. This test may falsely pass if a good POST request also does not post anything.
        """
        if not self._body_post:
            self.skipTest('_body_post not defined')
        await self._test_post_then_get_invalid({'invites': 2})

    async def test_post_then_get_invalid_shares_item_type(self) -> None:
        """
        Checks if a GET all request after a bad POST request does not demonstrate that the POST request succeeded
        when the ``shares`` field is passed an iterable that contains an object that is not a
        ``heaobject.root.Share``. The test is skipped if the unmodified body to POST (``_body_post``) is not
        defined. This test may falsely pass if a good POST request also does not post anything.
        """
        if not self._body_post:
            self.skipTest('_body_post not defined')
        await self._test_post_then_get_invalid({'user_shares': ['lonely']})

    async def test_post_then_get_invalid_shares_iterable_type(self) -> None:
        """
        Checks if a GET all request after a bad POST request does not demonstrate that the POST request succeeded
        when the ``shares`` field is not passed an iterable. The test is skipped if the unmodified body to POST
        (``_body_post``) is not defined. This test may falsely pass if a good POST request also does not post anything.
        """
        if not self._body_post:
            self.skipTest('_body_post not defined')
        await self._test_post_then_get_invalid({'user_shares': 2})

    async def test_invalid_url(self) -> None:
        """
        Checks if a POST request fails with status 405 when the URL has a desktop object ID. The test is skipped
        if the body to POST (``_body_post``) is not defined.
        """
        if not self._body_post:
            self.skipTest('_body_post not defined')
        async with self.client.request('POST',
                                       (self._href / '1').path,
                                       json=self._body_post,
                                       headers={**self._headers, hdrs.CONTENT_TYPE: cj.MIME_TYPE}) as obj:
            self.assertEqual(405, obj.status)

    async def _test_invalid(self, changes) -> None:
        """
        Checks if a POST request with the given change(s) fails with status 400. The test raises an
        ``AssertionError`` if the unmodified body to POST (``_body_post``) is not defined.

        This test is used for body validation.

        :param changes: The change(s) to be made to ``_body_post``
        :except AssertionError: if the unmodified body to POST (``_body_post``) is not defined
        """
        assert self._body_post is not None
        changed = deepcopy_heaobject_dict_with(cj.to_nvpjson(self._body_post), changes)
        async with self.client.request('POST',
                                       (self._href / '').path,
                                       json=changed,
                                       headers={**self._headers, hdrs.CONTENT_TYPE: nvpjson.MIME_TYPE}) as obj:
            self.assertEqual(400, obj.status)

    async def _test_valid_with_deletions(self, deletions) -> None:
        """
        Checks if a POST request with the given deletion(s) succeeds with status 201. The test raises an
        ``AssertionError`` if the unmodified body to POST (``_body_post``) is not defined.

        This test is used for body validation.

        :param deletions: The deletion(s) to be made to ``_body_post``
        :except AssertionError: if the unmodified body to POST (``_body_post``) is not defined
        """
        assert self._body_post is not None
        changed = deepcopy_heaobject_dict_with_deletions(cj.to_nvpjson(self._body_post), deletions)
        async with self.client.request('POST',
                                       (self._href / '').path,
                                       json=changed,
                                       headers={**self._headers, hdrs.CONTENT_TYPE: nvpjson.MIME_TYPE}) as obj:
            self.assertEqual(201, obj.status)

    async def _test_post_then_get_invalid(self, changes) -> None:
        """
        Checks if a GET all request after a POST request with the given change(s) does not demonstrate that the POST
        request posted something. The test raises an ``AssertionError`` if the unmodified body to POST
        (``_body_post``) is not defined.

        This test is used for body validation.

        :param changes: The change(s) to be made to ``_body_post``
        :except AssertionError: if the unmodified body to POST (``_body_post``) is not defined
        """
        assert self._body_post is not None
        changed = deepcopy_heaobject_dict_with(cj.to_nvpjson(self._body_post), changes)
        async with self.client.request('POST',
                                       (self._href / '').path,
                                       json=changed,
                                       headers={**self._headers, hdrs.CONTENT_TYPE: nvpjson.MIME_TYPE}):
            pass
        async with self.client.request('GET',
                                       (self._href / '').path,
                                       headers={**self._headers, hdrs.ACCEPT: nvpjson.MIME_TYPE}) as response:
            self.assertEqual(2, len(await response.json()), 'POST posted something')

    def _post_data(self):
        """Converts the POST body to encoded form data."""
        return _to_xwwwformurlencoded_data(self._body_post)


class PutMixin(_Base):
    """Tester mixin for PUT requests."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def test_put(self) -> None:
        """
        Checks if a PUT request with a Collection+JSON request body succeeds when the target has the same format. The
        test is skipped if the body to PUT (``_body_put``) is not defined.
        """
        if not self._body_put:
            self.skipTest('_body_put not defined')
        async with self.client.request('PUT',
                                       (self._href / self._id()).path,
                                       json=self._body_put,
                                       headers={**self._headers, hdrs.CONTENT_TYPE: cj.MIME_TYPE}) as obj:
            self.assertEqual('', await obj.text())

    async def test_put_nvpjson(self) -> None:
        """
        Checks if a PUT request with a name-value-pair JSON request body succeeds when the target has the same format.
        The test is skipped if the body to PUT (``_body_put``) is not defined.
        """
        if not self._body_put:
            self.skipTest('_body_put not defined')
        async with self.client.request('PUT',
                                       (self._href / self._id()).path,
                                       json=cj.to_nvpjson(self._body_put) if self._body_put is not None else None,
                                       headers={**self._headers, hdrs.CONTENT_TYPE: nvpjson.MIME_TYPE}) as obj:
            self.assertEqual('', await obj.text())

    async def test_put_xwwwformurlencoded(self) -> None:
        """
        Checks if a PUT request with encoded form data succeeds when the target has the same format. The test is
        skipped if the body to PUT (``_body_put``) is not defined.
        """
        if not self._body_put:
            self.skipTest('_body_put not defined')
        try:
            data_ = self._put_data()
        except jsonschemavalidator.ValidationError:
            self.skipTest('_body_put cannot be converted to xwwwformurlencoded form')
        else:
            async with self.client.request('PUT',
                                           (self._href / self._id()).path,
                                           data=data_,
                                           headers={**self._headers,
                                                    hdrs.CONTENT_TYPE: xwwwformurlencoded.MIME_TYPE}) as obj:
                self.assertEqual('', await obj.text())

    async def test_put_then_get(self) -> None:
        """
        Checks if the response body of a GET request after a PUT request reflects the PUT request body when the PUT
        request body is in Collection+JSON form. The test is skipped if the body to PUT (``_body_put``) is not
        defined.
        """
        if self._body_put:
            async with self.client.request('PUT',
                                           (self._href / self._id()).path,
                                           json=self._body_put,
                                           headers={**self._headers, hdrs.CONTENT_TYPE: cj.MIME_TYPE}):
                pass
            async with self.client.request('GET',
                                           (self._href / self._id()).path,
                                           headers={**self._headers, hdrs.ACCEPT: nvpjson.MIME_TYPE}) as response2:
                body_put = cj.to_nvpjson(self._body_put)
                for k, v in body_put.items():
                    if isinstance(v, date):
                        body_put[k] = v.isoformat()
                received_json = next(iter(await response2.json()))
                self.assertEqual(body_put, {k: v for k, v in received_json.items() if k in body_put})
        else:
            self.skipTest('_body_put not defined')

    async def test_put_then_get_nvpjson(self) -> None:
        """
        Checks if the response body of a GET request after a PUT request reflects the PUT request body when the PUT
        request body is in name-value-pair JSON form. The test is skipped if the body to PUT (``_body_put``) is not
        defined.
        """
        if self._body_put:
            body_put = cj.to_nvpjson(self._body_put)
            async with self.client.request('PUT',
                                           (self._href / self._id()).path,
                                           json=body_put,
                                           headers={**self._headers, hdrs.CONTENT_TYPE: nvpjson.MIME_TYPE}):
                pass
            async with self.client.request('GET',
                                           (self._href / self._id()).path,
                                           headers={**self._headers, hdrs.ACCEPT: nvpjson.MIME_TYPE}) as response2:
                for k, v in body_put.items():
                    if isinstance(v, date):
                        body_put[k] = v.isoformat()
                received_json = next(iter(await response2.json()))
                self.assertEqual(body_put, {k: v for k, v in received_json.items() if k in body_put})
        else:
            self.skipTest('_body_put not defined')

    async def test_put_status(self) -> None:
        """
        Checks if a PUT request with a Collection+JSON request body succeeds with status 204. The test is skipped if
        the body to PUT (``_body_put``) is not defined.
        """
        if not self._body_put:
            self.skipTest('_body_put not defined')
        async with self.client.request('PUT',
                                       (self._href / self._id()).path,
                                       json=self._body_put,
                                       headers={**self._headers, hdrs.CONTENT_TYPE: cj.MIME_TYPE}) as obj:
            self.assertEqual(204, obj.status)

    async def test_put_status_nvpjson(self) -> None:
        """
        Checks if a PUT request with a name-value-pair JSON request body succeeds with status 204. The test is
        skipped if the body to PUT (``_body_put``) is not defined.
        """
        if not self._body_put:
            self.skipTest('_body_put not defined')
        else:
            async with self.client.request('PUT',
                                           (self._href / self._id()).path,
                                           json=cj.to_nvpjson(self._body_put),
                                           headers={**self._headers, hdrs.CONTENT_TYPE: nvpjson.MIME_TYPE}) as obj:
                self.assertEqual(204, obj.status)

    async def test_put_status_xwwwformurlencoded(self) -> None:
        """
        Checks if a PUT request with encoded form data succeeds with status 204. The test is skipped if either the
        body to PUT (``_body_put``) is not defined or the data cannot be converted to encoded form data.
        """
        if not self._body_put:
            self.skipTest('_body_put not defined')
        try:
            data_ = self._put_data()
        except jsonschemavalidator.ValidationError:
            self.skipTest('_body_put cannot be converted to xwwwformurlencoded form')
        else:
            async with self.client.request('PUT',
                                           (self._href / self._id()).path,
                                           data=data_,
                                           headers={**self._headers,
                                                    hdrs.CONTENT_TYPE: xwwwformurlencoded.MIME_TYPE}) as obj:
                self.assertEqual(204, obj.status)

    async def test_put_status_wrong_format_nvpjson_cj(self) -> None:
        """
        Checks if a PUT request fails with status 400 when the request body is in name-value-pair JSON but the content
        type is Collection+JSON. The test is skipped if the body to PUT (``_body_put``) is not defined.
        """
        if not self._body_put:
            self.skipTest('_body_put not defined')
        else:
            async with self.client.request('PUT',
                                           (self._href / self._id()).path,
                                           json=cj.to_nvpjson(self._body_put),
                                           headers={**self._headers, hdrs.CONTENT_TYPE: cj.MIME_TYPE}) as obj:
                self.assertEqual(400, obj.status)

    async def test_put_status_wrong_format_xwwwformurlencoded_nvpjson(self) -> None:
        """
        Checks if a PUT request fails with status 400 when the request body is encoded form data but the content type
        is name-value-pair JSON. The test is skipped if either the body to PUT (``_body_put``) is not defined or the
        data cannot be converted to encoded form data.
        """
        if not self._body_put:
            self.skipTest('_body_put not defined')
        try:
            data_ = self._put_data()
        except jsonschemavalidator.ValidationError:
            self.skipTest('_body_put cannot be converted to xwwwformurlencoded form')
        else:
            async with self.client.request('PUT',
                                           (self._href / self._id()).path,
                                           data=data_,
                                           headers={**self._headers, hdrs.CONTENT_TYPE: nvpjson.MIME_TYPE}) as obj:
                self.assertEqual(400, obj.status)

    async def test_put_status_wrong_format_cj_xwwwformurlencoded(self) -> None:
        """
        Checks if a PUT request fails with status 400 when the request body is in Collection+JSON but the content type
        is encoded form data. The test is skipped if the body to PUT (``_body_put``) is not defined.
        """
        if not self._body_put:
            self.skipTest('_body_put not defined')
        async with self.client.request('PUT',
                                       (self._href / self._id()).path,
                                       json=self._body_put,
                                       headers={**self._headers,
                                                hdrs.CONTENT_TYPE: xwwwformurlencoded.MIME_TYPE}) as obj:
            self.assertEqual(400, obj.status)

    async def test_put_status_wrong_format_xwwwformurlencoded_cj(self) -> None:
        """
        Checks if a PUT request fails with status 400 when the request body is encoded form data but the content type
        is Collection+JSON. The test is skipped if either the body to PUT (``_body_put``) is not defined or the data
        cannot be converted to encoded form data.
        """
        if not self._body_put:
            self.skipTest('_body_put not defined')
        try:
            data_ = self._put_data()
        except jsonschemavalidator.ValidationError:
            self.skipTest('_body_put cannot be converted to xwwwformurlencoded form')
        else:
            async with self.client.request('PUT',
                                           (self._href / self._id()).path,
                                           data=data_,
                                           headers={**self._headers, hdrs.CONTENT_TYPE: cj.MIME_TYPE}) as obj:
                self.assertEqual(400, obj.status)

    async def test_put_status_wrong_format_cj_nvpjson(self) -> None:
        """
        Checks if a PUT request fails with status 400 when the request body is in Collection+JSON but the content
        type is name-value-pair JSON. The test is skipped if the body to PUT (``_body_put``) is not defined.
        """
        if not self._body_put:
            self.skipTest('_body_put not defined')
        async with self.client.request('PUT',
                                       (self._href / self._id()).path,
                                       json=self._body_put,
                                       headers={**self._headers, hdrs.CONTENT_TYPE: nvpjson.MIME_TYPE}) as obj:
            self.assertEqual(400, obj.status)

    async def test_put_status_wrong_format_nvpjson_xwwwformurlencoded(self) -> None:
        """
        Checks if a PUT request fails with status 400 when the request body is name-value-pair JSON but the content
        type is encoded form data. The test is skipped if the body to PUT (``_body_put``) is not defined.
        """
        if not self._body_put:
            self.skipTest('_body_put not defined')
        else:
            async with self.client.request('PUT',
                                           (self._href / self._id()).path,
                                           json=cj.to_nvpjson(self._body_put),
                                           headers={**self._headers,
                                                    hdrs.CONTENT_TYPE: xwwwformurlencoded.MIME_TYPE}) as obj:
                self.assertEqual(400, obj.status)

    async def test_put_status_empty_body(self) -> None:
        """
        Checks if a PUT request whose request body MIME type is declared to be Collection+JSON fails with status 400
        when the body is empty. The test is skipped if the body that would normally be PUT (``_body_put``) is not
        defined.
        """
        if not self._body_put:
            self.skipTest('_body_put not defined')
        async with self.client.request('PUT',
                                       (self._href / self._id()).path,
                                       headers={**self._headers, hdrs.CONTENT_TYPE: cj.MIME_TYPE}) as obj:
            self.assertEqual(400, obj.status)

    async def test_put_status_empty_body_nvpjson(self) -> None:
        """
        Checks if a PUT request whose request body MIME type is declared to be name-value-pair JSON fails with status
        400 when the body is empty. The test is skipped if the body that would normally be PUT (``_body_put``) is not
        defined.
        """
        if not self._body_put:
            self.skipTest('_body_put not defined')
        async with self.client.request('PUT',
                                       (self._href / self._id()).path,
                                       headers={**self._headers, hdrs.CONTENT_TYPE: nvpjson.MIME_TYPE}) as obj:
            self.assertEqual(400, obj.status)

    async def test_put_status_empty_body_xwwwformurlencoded(self) -> None:
        """
        Checks if a PUT request whose request body MIME type is declared to be encoded form data fails with status 400
        when the body is empty. The test is skipped if the body that would normally be PUT (``_body_put``) is not
        defined.
        """
        if not self._body_put:
            self.skipTest('_body_put not defined')
        async with self.client.request('PUT',
                                       (self._href / self._id()).path,
                                       headers={**self._headers,
                                                hdrs.CONTENT_TYPE: xwwwformurlencoded.MIME_TYPE}) as obj:
            self.assertEqual(400, obj.status)

    async def test_put_empty_body(self) -> None:
        """
        Checks if a GET request after a PUT request whose request body MIME type is declared to be Collection+JSON
        shows that the PUT request failed when the PUT request body was empty. The test is skipped if the body that
        would normally be PUT (``_body_put``) is not defined. This test may falsely pass if a good PUT request also
        does not put anything.
        """
        if not self._body_put:
            self.skipTest('_body_put not defined')
        else:
            async with self.client.request('PUT',
                                           (self._href / self._id()).path,
                                           headers={**self._headers, hdrs.CONTENT_TYPE: cj.MIME_TYPE}):
                pass
            async with self.client.request('GET',
                                           (self._href / self._id()).path,
                                           headers={**self._headers, hdrs.ACCEPT: nvpjson.MIME_TYPE}) as response:
                body_put = cj.to_nvpjson(self._body_put)
                for k, v in body_put.items():
                    if isinstance(v, date):
                        body_put[k] = v.isoformat()
                self.assertNotEqual(body_put, next(iter(await response.json()), None))

    async def test_put_empty_body_nvpjson(self) -> None:
        """
        Checks if a GET request after a PUT request whose request body MIME type is declared to be name-value-pair
        JSON shows that the PUT request failed when the PUT request body was empty. The test is skipped if the body
        that would normally be PUT (``_body_put``) is not defined. This test may falsely pass if a good PUT request
        also does not put anything.
        """
        if not self._body_put:
            self.skipTest('_body_put not defined')
        else:
            async with self.client.request('PUT',
                                           (self._href / self._id()).path,
                                           headers={**self._headers, hdrs.CONTENT_TYPE: nvpjson.MIME_TYPE}):
                pass
            async with self.client.request('GET',
                                           (self._href / self._id()).path,
                                           headers={**self._headers, hdrs.ACCEPT: nvpjson.MIME_TYPE}) as response:
                body_put = cj.to_nvpjson(self._body_put)
                for k, v in body_put.items():
                    if isinstance(v, date):
                        body_put[k] = v.isoformat()
                self.assertNotEqual(body_put, next(iter(await response.json()), None))

    async def test_put_empty_body_xwwwformurlencoded(self) -> None:
        """
        Checks if a GET request after a PUT request whose request body MIME type is declared to be encoded form data
        shows that the PUT request failed when the PUT request body was empty. The test is skipped if the body that
        would normally be PUT (``_body_put``) is not defined. This test may falsely pass if a good PUT request also
        does not put anything.
        """
        if not self._body_put:
            self.skipTest('_body_put not defined')
        else:
            async with self.client.request('PUT',
                                           (self._href / self._id()).path,
                                           headers={**self._headers, hdrs.CONTENT_TYPE: xwwwformurlencoded.MIME_TYPE}):
                pass
            async with self.client.request('GET',
                                           (self._href / self._id()).path,
                                           headers={**self._headers, hdrs.ACCEPT: nvpjson.MIME_TYPE}) as response:
                body_put = cj.to_nvpjson(self._body_put)
                for k, v in body_put.items():
                    if isinstance(v, date):
                        body_put[k] = v.isoformat()
                self.assertNotEqual(body_put, next(iter(await response.json()), None))

    async def test_put_status_missing_id(self) -> None:
        """
        Checks if a PUT request with a Collection+JSON request body fails with status 405 when the URL contains no ID.
        The test is skipped if the body to PUT (``_body_put``) is not defined.
        """
        if not self._body_put:
            self.skipTest('_body_put not defined')
        async with self.client.request('PUT',
                                       self._href.path,
                                       json=self._body_put,
                                       headers={**self._headers, hdrs.CONTENT_TYPE: cj.MIME_TYPE}) as obj:
            self.assertEqual(405, obj.status)

    async def test_put_status_missing_id_nvpjson(self) -> None:
        """
        Checks if a PUT request with a name-value-pair JSON request body fails with status 405 when the URL contains no
        ID. The test is skipped if the body to PUT (``_body_put``) _body_put is not defined.
        """
        if not self._body_put:
            self.skipTest('_body_put not defined')
        else:
            async with self.client.request('PUT',
                                           self._href.path,
                                           json=cj.to_nvpjson(self._body_put),
                                           headers={**self._headers, hdrs.CONTENT_TYPE: nvpjson.MIME_TYPE}) as obj:
                self.assertEqual(405, obj.status)

    async def test_put_status_missing_id_xwwwformurlencoded(self) -> None:
        """
        Checks if a PUT request with a name-value-pair JSON request body fails with status 405 when the URL contains
        no ID. The test is skipped if either the body to PUT (``_body_put``) is not defined or the data cannot be
        converted to encoded form data.
        """
        if not self._body_put:
            self.skipTest('_body_put not defined')
        try:
            data_ = self._put_data()
        except jsonschemavalidator.ValidationError:
            self.skipTest('_body_put cannot be converted to xwwwformurlencoded form')
        async with self.client.request('PUT',
                                       self._href.path,
                                       data=data_,
                                       headers={**self._headers,
                                                hdrs.CONTENT_TYPE: xwwwformurlencoded.MIME_TYPE}) as obj:
            self.assertEqual(405, obj.status)

    async def test_put_status_missing_target(self) -> None:
        """
        Checks if a PUT request with a Collection+JSON request body fails with status 404 when the URL target does not
        exist. The test is skipped if the body to PUT (``_body_put``) is not defined.
        """
        if not self._body_put:
            self.skipTest('_body_put not defined')
        async with self.client.request('PUT',
                                       (self._href / '1').path,
                                       json=self._body_put,
                                       headers={**self._headers, hdrs.CONTENT_TYPE: cj.MIME_TYPE}) as obj:
            self.assertEqual(404, obj.status)

    async def test_put_status_invalid_type(self) -> None:
        """
        Checks if a PUT request with a name-value-pair JSON request body fails with status 405 when the object in the
        request body has an invalid type. The test is skipped if the body (without modification) to PUT (``_body_put``)
        is not defined.
        """
        if not self._body_put:
            self.skipTest('_body_put not defined')
        await self._test_invalid({'type': 'foo.bar'})

    async def test_put_status_invalid_created_datetime_string(self) -> None:
        """
        Checks if a PUT request fails with status 400 when the ``created`` field has an invalid ISO-8601 datetime
        string. The test is skipped if the unmodified body to PUT (``_body_put``) is not defined.
        """
        if not self._body_put:
            self.skipTest('_body_put not defined')
        await self._test_invalid({'created': 'not a time string'})

    async def test_put_status_invalid_created_type(self) -> None:
        """
        Checks if a PUT request fails with status 400 when the ``created`` field is of an invalid type. The test is
        skipped if the unmodified body to PUT (``_body_put``) is not defined.
        """
        if not self._body_put:
            self.skipTest('_body_put not defined')
        await self._test_invalid({'created': 2})

    async def test_put_status_invalid_modified_datetime_string(self) -> None:
        """
        Checks if a PUT request fails with status 400 when the ``modified`` field has an invalid ISO-8601 datetime
        string. The test is skipped if the unmodified body to PUT (``_body_put``) is not defined.
        """
        if not self._body_put:
            self.skipTest('_body_put not defined')
        await self._test_invalid({'modified': 'not a time string'})

    # Will be resolved later
    # async def test_put_status_invalid_derived_from_none(self) -> None:
    #     """
    #     Checks if a PUT request fails with status 400 when the ``derived_from`` field is passed ``None``. The test is
    #     skipped if the unmodified body to PUT (``_body_put``) is not defined.
    #     """
    #     if not self._body_put:
    #         self.skipTest('_body_put not defined')
    #     await self._test_invalid({'derived_from': None})
    #
    # async def test_put_status_valid_derived_from_missing(self) -> None:
    #     """
    #     Checks if a PUT request succeeds with status 201 when the ``derived_from`` field is missing (it should be
    #     assigned a default value). The test is skipped if the unmodified body to PUT (``_body_put``) is not
    #     defined.
    #     """
    #     if not self._body_put:
    #         self.skipTest('_body_put not defined')
    #     await self._test_valid_with_deletions(['derived_from'])
    #
    # async def test_put_status_invalid_derived_from_item_type(self) -> None:
    #     """
    #     Checks if a PUT request fails with status 400 when the ``derived_from`` field is passed an iterable that
    #     contains an object that is not a string. The test is skipped if the unmodified body to PUT (``_body_put``)
    #     is not defined.
    #     """
    #     if not self._body_put:
    #         self.skipTest('_body_put not defined')
    #     await self._test_invalid({'derived_from': ['1', 2, '3']})
    #
    # async def test_put_status_invalid_derived_from_iterable_type(self) -> None:
    #     """
    #     Checks if a PUT request fails with status 400 when the ``derived_from`` field is not passed an iterable. The
    #     test is skipped if the unmodified body to PUT (``_body_put``) is not defined.
    #     """
    #     if not self._body_put:
    #         self.skipTest('_body_put not defined')
    #     await self._test_invalid({'derived_from': 2})
    #

    async def test_put_status_valid_invites_none(self) -> None:
        """
        Checks if a PUT request succeeds with status 204 when the ``invites`` field is passed ``None``. The test is
        skipped if the unmodified body to PUT (``_body_put``) is not defined.
        """
        if not self._body_put:
            self.skipTest('_body_put not defined')
        else:
            changed = deepcopy_heaobject_dict_with(cj.to_nvpjson(self._body_put), {'invites': None})
            async with self.client.request('PUT',
                                           (self._href / self._id()).path,
                                           json=changed,
                                           headers={**self._headers, hdrs.CONTENT_TYPE: nvpjson.MIME_TYPE}) as obj:
                self.assertEqual(204, obj.status)

    async def test_put_status_valid_invites_missing(self) -> None:
        """
        Checks if a PUT request succeeds with status 201 when the ``invites`` field is missing (it should be assigned a
        default value). The test is skipped if the unmodified body to PUT (``_body_put``) is not defined.
        """
        if not self._body_put:
            self.skipTest('_body_put not defined')
        await self._test_valid_with_deletions(['invites'])

    async def test_put_status_invalid_invites_item_type(self) -> None:
        """
        Checks if a PUT request fails with status 400 when the ``invites`` field is passed an iterable that contains an
        object that is not a ``heaobject.root.Invite``. The test is skipped if the unmodified body to PUT
        (``_body_put``) is not defined.
        """
        if not self._body_put:
            self.skipTest('_body_put not defined')
        await self._test_invalid({'invites': ['lonely']})

    async def test_put_status_invalid_invites_iterable_type(self) -> None:
        """
        Checks if a PUT request fails with status 400 when the ``invites`` field is not passed an iterable. The test
        is skipped if the unmodified body to PUT (``_body_put``) is not defined.
        """
        if not self._body_put:
            self.skipTest('_body_put not defined')
        await self._test_invalid({'invites': 2})

    async def test_put_status_invalid_shares_item_type(self) -> None:
        """
        Checks if a PUT request fails with status 400 when the ``shares`` field is passed an iterable that contains an
        object that is not a ``heaobject.root.Share``. The test is skipped if the unmodified body to PUT
        (``_body_put``) is not defined.
        """
        if not self._body_put:
            self.skipTest('_body_put not defined')
        await self._test_invalid({'user_shares': ['lonely']})

    async def test_put_status_invalid_shares_iterable_type(self) -> None:
        """
        Checks if a PUT request fails with status 400 when the ``shares`` field is not passed an iterable. The test
        is skipped if the unmodified body to PUT (``_body_put``) is not defined.
        """
        if not self._body_put:
            self.skipTest('_body_put not defined')
        await self._test_invalid({'user_shares': 2})

    async def test_put_then_get_invalid_type(self) -> None:
        """
        Checks if a GET request after a bad PUT request does not show any changes when the declared type is invalid.
        The test is skipped if the body (without modification) to PUT (``_body_put``) is not defined. This test may
        falsely pass if a good PUT request also does not put anything.
        """
        if not self._body_put:
            self.skipTest('_body_put not defined')
        await self._test_put_then_get_invalid({'type': 'foo.bar'})

    async def test_put_then_get_invalid_created_datetime_string(self) -> None:
        """
        Checks if a GET request after a bad PUT request does not show any changes when the ``created`` field has an
        invalid ISO-8601 datetime string. The test is skipped if the unmodified body to PUT (``_body_put``) is
        not defined. This test may falsely pass if a good PUT request also does not put anything.
        """
        if not self._body_put:
            self.skipTest('_body_put not defined')
        await self._test_put_then_get_invalid({'created': 'not a time string'})

    async def test_put_then_get_invalid_created_type(self) -> None:
        """
        Checks if a GET request after a bad PUT request does not show any changes when the ``created`` field is of an
        invalid type. The test is skipped if the unmodified body to PUT (``_body_put``) is not defined. This
        test may falsely pass if a good PUT request also does not put anything.
        """
        if not self._body_put:
            self.skipTest('_body_put not defined')
        await self._test_put_then_get_invalid({'created': 2})

    async def test_put_then_get_invalid_modified_datetime_string(self) -> None:
        """
        Checks if a GET request after a bad PUT request does not show any changes when the ``modified`` field has an
        invalid ISO-8601 datetime string. The test is skipped if the unmodified body to PUT (``_body_put``) is
        not defined. This test may falsely pass if a good PUT request also does not put anything.
        """
        if not self._body_put:
            self.skipTest('_body_put not defined')
        await self._test_put_then_get_invalid({'modified': 'not a time string'})

    # Will be resolved later
    # async def test_put_then_get_invalid_derived_from_none(self) -> None:
    #     """
    #     Checks if a GET request after a bad PUT request does not show any changes when the ``derived_from`` field is
    #     passed ``None``. The test is skipped if the unmodified body to PUT (``_body_put``) is not defined. This
    #     test may falsely pass if a good PUT request also does not put anything.
    #     """
    #     if not self._body_put:
    #         self.skipTest('_body_put not defined')
    #     await self._test_put_then_get_invalid({'derived_from': None})
    #
    # async def test_put_then_get_invalid_derived_from_item_type(self) -> None:
    #     """
    #     Checks if a GET request after a bad PUT request does not show any changes when the ``derived_from`` field is
    #     passed an iterable that contains an object that is not a string. The test is skipped if the unmodified
    #     body to PUT (``_body_put``) is not defined.  This test may falsely pass if a good PUT request also does not
    #     put anything.
    #     """
    #     if not self._body_put:
    #         self.skipTest('_body_put not defined')
    #     await self._test_put_then_get_invalid({'derived_from': ['1', 2, '3']})
    #
    # async def test_put_then_get_invalid_derived_from_iterable_type(self) -> None:
    #     """
    #     Checks if a GET request after a bad PUT request does not show any changes when the ``derived_from`` field is
    #     not passed an iterable. The test is skipped if the unmodified body to PUT (``_body_put``) is not
    #     defined. This test may falsely pass if a good PUT request also does not put anything.
    #     """
    #     if not self._body_put:
    #         self.skipTest('_body_put not defined')
    #     await self._test_put_then_get_invalid({'derived_from': 2})

    async def test_put_then_get_valid_invites_none(self) -> None:
        """
        Checks if a GET request after a PUT request shows that the appropriate change was made when the ``invites``
        field is passed ``None`` (it should be set to the empty list). The test is skipped if the unmodified
        body to PUT (``_body_put``) is not defined. This test may falsely pass if a good PUT request also does not
        put anything.
        """
        if not self._body_put:
            self.skipTest('_body_put not defined')
        else:
            async with self.client.request('PUT',
                                           (self._href / self._id()).path,
                                           json=self._body_put,
                                           headers={**self._headers, hdrs.CONTENT_TYPE: cj.MIME_TYPE}):
                pass
            async with self.client.request('GET',
                                           (self._href / self._id()).path,
                                           headers={**self._headers, hdrs.ACCEPT: nvpjson.MIME_TYPE}) as response:
                body_put = cj.to_nvpjson(self._body_put)
                for k, v in body_put.items():
                    if isinstance(v, date):
                        body_put[k] = v.isoformat()
                received_json = next(iter(await response.json()))
                self.assertEqual(body_put, {k: v for k, v in received_json.items() if k in body_put})

    async def test_put_then_get_invalid_invites_item_type(self) -> None:
        """
        Checks if a GET request after a bad PUT request does not show any changes when the ``invites`` field is
        passed an iterable that contains an object that is not a ``heaobject.root.Invite``. The test is skipped
        if the unmodified body to PUT (``_body_put``) is not defined. This test may falsely pass if a good PUT
        request also does not put anything.
        """
        if not self._body_put:
            self.skipTest('_body_put not defined')
        await self._test_put_then_get_invalid({'invites': ['lonely']})

    async def test_put_then_get_invalid_invites_iterable_type(self) -> None:
        """
        Checks if a GET request after a bad PUT request does not show any changes when the ``invites`` field is not
        passed an iterable. The test is skipped if the unmodified body to PUT (``_body_put``) is not defined.
        This test may falsely pass if a good PUT request also does not put anything.
        """
        if not self._body_put:
            self.skipTest('_body_put not defined')
        await self._test_put_then_get_invalid({'invites': 2})

    async def test_put_then_get_invalid_shares_item_type(self) -> None:
        """
        Checks if a GET request after a bad PUT request does not show any changes when the ``shares`` field is passed
        an iterable that contains an object that is not a ``heaobject.root.Share``. The test is skipped if the
        unmodified body to PUT (``_body_put``) is not defined.  This test may falsely pass if a good PUT request also
        does not put anything.
        """
        if not self._body_put:
            self.skipTest('_body_put not defined')
        await self._test_put_then_get_invalid({'user_shares': ['lonely']})

    async def test_put_then_get_invalid_shares_iterable_type(self) -> None:
        """
        Checks if a GET request after a bad PUT request does not show any changes when the ``shares`` field is not
        passed an iterable. The test is skipped if the unmodified body to PUT (``_body_put``) is not defined.
        This test may falsely pass if a good PUT request also does not put anything.
        """
        if not self._body_put:
            self.skipTest('_body_put not defined')
        await self._test_put_then_get_invalid({'user_shares': 2})

    async def test_put_content(self) -> None:
        """
        Checks if a PUT request to plaintext content succeeds with the correct status (``_put_content_status``). The
        test is skipped if either the desired status (``_put_content_status``) is not defined or the content ID
        (``_content_id``) is not defined.
        """
        if self._put_content_status is None:
            self.skipTest('_put_content_status not defined')
        elif self._content_id is None:
            self.skipTest('_content_id not defined')
        else:
            async with self.client.request('PUT',
                                           (self._href / self._content_id / 'content').path,
                                           data='The quick brown fox jumps over the lazy dog',
                                           headers={**self._headers, hdrs.CONTENT_TYPE: 'text/plain'}) as obj:
                self.assertEqual(self._put_content_status, obj.status)

    async def test_put_then_get_content_status(self) -> None:
        """
        Checks if a GET request after a PUT request to plaintext content succeeds with status 200. The test is
        skipped if either the desired status (``_put_content_status``) is not 204 or the content ID (``_content_id``)
        is not defined.
        """
        if self._put_content_status != 204:
            self.skipTest('_put_content_status is not 204')
        elif self._content_id is None:
            self.skipTest('_content_id not defined')
        else:
            async with self.client.request('PUT',
                                           (self._href / self._content_id / 'content').path,
                                           data='The quick brown fox jumps over the lazy dog',
                                           headers={**self._headers, hdrs.CONTENT_TYPE: 'text/plain'}):
                pass
            async with self.client.request('GET',
                                           (self._href / self._content_id / 'content').path,
                                           headers={**self._headers, hdrs.ACCEPT: 'text/plain'}) as response:
                self.assertEqual(200, response.status)

    async def test_put_then_get_content(self) -> None:
        """
        Checks if a GET request after a PUT request to plaintext content returns the expected plaintext. The test is
        skipped if either the desired status (``_put_content_status``) is not 204 or the content ID (``_content_id``)
        is not defined.
        """
        if self._put_content_status != 204:
            self.skipTest('_put_content_status is not 204')
        elif self._content_id is None:
            self.skipTest('_content_id not defined')
        else:
            async with self.client.request('PUT',
                                           (self._href / self._content_id / 'content').path,
                                           data='The quick brown fox jumps over the lazy dog',
                                           headers={**self._headers, hdrs.CONTENT_TYPE: 'text/plain'}):
                pass
            async with self.client.request('GET',
                                           (self._href / self._content_id / 'content').path,
                                           headers={**self._headers, hdrs.ACCEPT: 'text/plain'}) as response:
                self.assertEqual(b'The quick brown fox jumps over the lazy dog', await response.read())

    async def _test_invalid(self, changes) -> None:
        """
        Checks if a PUT request with a name-value-pair JSON request body (``_body_put``) with the given change(s) fails
        with status 400.

        This test is used for body validation.

        :param changes: The changes made, expressed as a dictionary
        """
        if 'type' not in changes:
            changes['type'] = self._type()
        assert self._body_put is not None, 'self._body_put cannot be None'
        changed = deepcopy_heaobject_dict_with(cj.to_nvpjson(self._body_put), changes)
        async with self.client.request('PUT',
                                       (self._href / self._id()).path,
                                       json=changed,
                                       headers={**self._headers, hdrs.CONTENT_TYPE: nvpjson.MIME_TYPE}) as obj:
            self.assertEqual(400, obj.status)

    async def _test_valid_with_deletions(self, deletions) -> None:
        """
        Checks if a PUT request with the given deletion(s) succeeds with status 201. The test raises an
        ``AssertionError`` if the unmodified body to PUT (``_body_put``) is not defined.

        This test is used for body validation.

        :param deletions: The deletion(s) to be made to ``_body_put``
        :except AssertionError: if the unmodified body to PUT (``_body_put``) is not defined
        """
        assert self._body_put is not None
        changed = deepcopy_heaobject_dict_with_deletions(cj.to_nvpjson(self._body_put), deletions)
        async with self.client.request('PUT',
                                       (self._href / self._id()).path,
                                       json=changed,
                                       headers={**self._headers, hdrs.CONTENT_TYPE: nvpjson.MIME_TYPE}) as obj:
            self.assertEqual(204, obj.status)

    async def _test_put_then_get_invalid(self, changes) -> None:
        """
        Checks if a GET request after a PUT request with the given change(s) demonstrates that the PUT request did
        not modify its target. The test raises an ``AssertionError`` if the unmodified body to PUT
        (``_body_put``) is not defined.

        This test is used for body validation.

        :param changes: The change(s) to be made to ``_body_put``
        :except AssertionError: if the unmodified body to POST (``_body_put``) is not defined
        """
        assert self._body_put is not None
        changed = deepcopy_heaobject_dict_with(cj.to_nvpjson(self._body_put), changes)
        async with self.client.request('PUT',
                                       (self._href / self._id()).path,
                                       json=self._body_put,
                                       headers={**self._headers, hdrs.CONTENT_TYPE: cj.MIME_TYPE}):
            pass
        async with self.client.request('GET',
                                       (self._href / self._id()).path,
                                       headers={**self._headers, hdrs.ACCEPT: nvpjson.MIME_TYPE}) as response:
            for k, v in changed.items():
                if isinstance(v, date):
                    changed[k] = v.isoformat()
            self.assertNotEqual(changed, next(iter(await response.json()), None))

    def _put_data(self):
        """Converts the PUT request body to encoded form data."""
        return _to_xwwwformurlencoded_data(self._body_put)

    def _id(self):
        """Gets the ID of the target of the PUT request, determined by the value of the template ``_body_put``."""
        logging.getLogger(__name__).debug('Template is %s', self._body_put)
        for e in self._body_put['template']['data']:
            if e['name'] == 'id':
                return e.get('value')

    def _type(self):
        logging.getLogger(__name__).debug('Template is %s', self._body_put)
        for e in self._body_put['template']['data']:
            if e['name'] == 'type':
                return e.get('value')



class GetOneNoNameCheckMixin(_Base):
    """Tester mixin for GET requests that request a single object. It is missing checks for a by name GET call. To
    get those, use GetOneMixin instead."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def test_get(self) -> None:
        """Checks if a GET request succeeds and returns the expected JSON (``_expected_one``)."""
        async with self.client.request('GET',
                                       (self._href / self._id()).path,
                                       headers=self._headers) as obj:
            self._assert_equal_ordered(self._expected_one, await obj.json())

    async def test_get_status(self) -> None:
        """Checks if a GET request succeeds with status 200."""
        async with self.client.request('GET',
                                       (self._href / self._id()).path,
                                       headers=self._headers) as obj:
            self.assertEqual(200, obj.status)

    async def test_get_wstl(self) -> None:
        """
        Checks if a GET request for WeSTL data succeeds and returns the expected JSON (``_expected_one_wstl``). The
        test is skipped if the expected WeSTL data (``_expected_one_wstl``) is not defined.
        """
        if not self._expected_one_wstl:
            self.skipTest('self._expected_one_wstl is not defined')
        async with self.client.request('GET',
                                       (self._href / self._id()).path,
                                       headers={**self._headers, hdrs.ACCEPT: wstljson.MIME_TYPE}) as obj:
            self._assert_equal_ordered(self._expected_one_wstl, await obj.json())

    async def test_get_not_acceptable(self) -> None:
        """
        Checks if a GET request fails with status 406 when an unacceptable ACCEPT header is provided. The test is
        skipped if the expected WeSTL data (``_expected_one_wstl``) is not defined.
        """
        if not self._expected_one_wstl:
            self.skipTest('self._expected_one_wstl is not defined')
        async with self.client.request('GET',
                                       (self._href / self._id()).path,
                                       headers={**self._headers, hdrs.ACCEPT: 'application/msword'}) as obj:
            self.assertEqual(406, obj.status)

    async def test_get_duplicate_form(self) -> None:
        """
        Checks if a GET request for a copy of WeSTL data from the duplicator succeeds and returns the expected data
        (``_expected_one_wstl_duplicate_form``). The test is skipped if the expected WeSTL data
        (``_expected_one_wstl_duplicate_form``) is not defined.
        """
        if not self._expected_one_duplicate_form:
            self.skipTest('self._expected_one_duplicate_wstl is not defined')
        async with self.client.request('GET',
                                       (self._href / self._id() / 'duplicator').path,
                                       headers=self._headers) as obj:
            self._assert_equal_ordered(self._expected_one_duplicate_form, await obj.json())

    async def test_opener_header(self) -> None:
        """
        Checks if a GET request for the opener for the data succeeds and has the expected LOCATION header
        (``_expected_opener``). The test is skipped if the expected header value (``_expected_opener``) is not
        defined.
        """
        if not self._expected_opener:
            self.skipTest('self._expected_opener is not defined')
        async with self.client.request('GET',
                                       (self._href / self._id() / 'opener').path,
                                       headers=self._headers) as obj:
            self.assertEqual(self._expected_opener, obj.headers[hdrs.LOCATION])

    async def test_opener_body(self) -> None:
        """
        Checks if a GET request for the opener for the data succeeds and has the expected body
        (``_expected_opener_body``). The test is skipped if the expected body (``_expected_opener_body``) is not
        defined.
        """
        if not self._expected_opener_body:
            self.skipTest('self._expected_opener_body is not defined')
        async with self.client.request('GET',
                                       (self._href / self._id() / 'opener').path,
                                       headers=self._headers) as obj:
            expected = deepcopy(self._expected_opener_body)
            for doc in expected:
                for item in doc['collection'].get('items') or []:
                    item.pop('data', None)
                doc['collection']['permissions'] = [[]]
            self._assert_equal_ordered(expected, await obj.json())

    async def test_get_content(self) -> None:
        """
        Checks if a GET request for the content succeeds and returns the expected data (in ``_content``). The test is
        skipped if either the expected content (``_content``) or the collection name (``_coll``) is not defined.
        """
        if not self._content:
            self.skipTest('self._content is not defined')
        elif not self._coll:
            self.skipTest('self._coll is not defined')
        else:
            async with self.client.request('GET',
                                           (self._href / self._id() / 'content').path,
                                           headers=self._headers) as resp:
                collection_key = get_collection_key_from_name(self._content, self._coll)
                if collection_key is None:
                    raise ValueError(f'Invalid collection name {self._coll}')
                expected = self._content[collection_key][self._id()]
                if isinstance(expected, (dict, list)):
                    self.assertEqual(_ordered(expected), _ordered(await resp.json()))
                elif isinstance(expected, str):
                    self.assertEqual(expected, await resp.text())
                else:
                    self.assertEqual(expected, await resp.read())

    async def test_get_content_type(self) -> None:
        """
        Checks if a GET request for the content succeeds and returns the expected content type. The test is skipped
        if either the expected content (``_content``) or the content type (``_content_type``) is not defined.
        """
        if not self._content:
            self.skipTest('self._content is not defined')
        if not self._content_type:
            self.skipTest('self._content_type is not defined')
        async with self.client.request('GET',
                                       (self._href / self._id() / 'content').path,
                                       headers=self._headers) as obj:
            with closing(obj) as obj:
                self.assertEqual(self._content_type, obj.headers.get(hdrs.CONTENT_TYPE))

    def _assert_equal_ordered(self, obj1, obj2):
        """Checks if two objects are equal, regardless of order."""
        self.assertEqual(_ordered(obj1), _ordered(obj2))

    def _id(self) -> str:
        """Get the ID for the expected JSON. Skips the test if self._expected_one is None or has no elements.

        :return: the id value of the first element of self._expected_one.
        :raises ValueError: if the first element of self._expected_one has no id field, or it is not a string.
        """
        if self._expected_one is None or len(self._expected_one) < 1:
            self.skipTest('self._expected_one is None')
            raise AssertionError('never reached')
        else:
            logging.getLogger(__name__).debug('Collection is %s', self._body_put)
            for e in self._expected_one[0]['collection']['items'][0]['data']:
                if e['name'] == 'id':
                    result = e.get('value')
                    if not isinstance(result, str):
                        raise ValueError(f"id is not a string: {self._expected_one[0]['collection']['items'][0]['data']}")
                    return e.get('value')
            raise ValueError(f"No id in {self._expected_one[0]['collection']['items'][0]['data']}")


class GetOneMixin(GetOneNoNameCheckMixin):
    """Tester mixin for GET requests that request a single object."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def test_get_by_name(self):
        """
        Checks if a GET request for the object with the expected name in ``_expected_one_wstl`` succeeds and returns the
        expected data. The test is skipped if the object doesn't have a name.
        """
        name = self._expected_one_wstl[0]['wstl']['data'][0].get('name', None)
        if name is not None:
            async with self.client.request('GET',
                                           (self._href / 'byname' / name).path,
                                           headers={**self._headers, hdrs.ACCEPT: cj.MIME_TYPE}) as response:
                self._assert_equal_ordered(self._expected_one[0]['collection']['items'][0]['data'],
                                           (await response.json())[0]['collection']['items'][0]['data'])
        else:
            self.skipTest('the expected object does not have a name')

    async def test_get_by_name_invalid_name(self):
        """Checks if a GET request for the object with the name 'foobar' fails with status 404."""
        async with self.client.request('GET',
                                       (self._href / 'byname' / 'foobar').path,
                                       headers={**self._headers, hdrs.ACCEPT: cj.MIME_TYPE}) as response:
            self.assertEqual(404, response.status)


class GetAllMixin(_Base):
    """Tester mixin for GET requests that request all the objects in some path."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def test_get_all(self) -> None:
        """Checks if a GET request for all the items succeeds with status 200."""
        async with self.client.request('GET',
                                       (self._href / '').path,
                                       headers=self._headers) as obj:
            self.assertEqual(200, obj.status)

    async def test_get_all_json(self) -> None:
        """
        Checks if a GET request for all the items as JSON succeeds and returns the expected value
        (``_expected_all``).
        """
        async with self.client.request('GET',
                                       (self._href / '').path,
                                       headers=self._headers) as obj:
            self.assertEqual(_ordered(self._expected_all), _ordered(await obj.json()))

    async def test_get_all_wstl(self) -> None:
        """
        Checks if a GET request for all the items as WeSTL JSON succeeds and returns the expected value
        (``_expected_all_wstl``). The test is skipped if the expected WeSTL JSON (``_expected_all_wstl``) is not
        defined.
        """
        if not self._expected_all_wstl:
            self.skipTest('self._expected_all_wstl is not defined')
        async with self.client.request('GET',
                                       (self._href / '').path,
                                       headers={**self._headers, hdrs.ACCEPT: wstljson.MIME_TYPE}) as obj:
            self.assertEqual(_ordered(self._expected_all_wstl), _ordered(await obj.json()))

    async def test_get_all_bad_content_type(self) -> None:
        """Checks if a GET request for all the items fails with status 406 when an invalid content type is provided."""
        async with self.client.request('GET',
                                       (self._href / '').path,
                                       headers={**self._headers, hdrs.ACCEPT: 'foo/bar'}) as obj:
            self.assertEqual(406, obj.status)


class _CheckerMixin(_Base):
    """
    Abstract base class for checking a service other than the one being tested for data.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def _check(self, image_substring: str, path: str,
                     check_fn=Callable[[aiohttp.ClientResponse], Awaitable[bool]]):
        """
        Check the service running in the container with the provided image name substring for a value. The provided
        path is appended to the container's external hostname and port, and the check function accepts a ClientResponse
        parameter and returns True to indicate that the data is present, otherwise False. If the data is not found
        after three tries, the test will fail.

        :param image_substring: a substring that will uniquely identify the container of interest.
        :param path: the path of the service call.
        :param check_fn: the check function.
        """
        container_ports = next((c for c in self._docker_container_ports if image_substring in c.image))

        # We need our own session because the TestClient's built-in session doesn't expect absolute URLs.
        async with client_session() as session:
            @async_retry(ValueError, retries=3, cooldown=10)
            async def check():
                url = URL(container_ports.external_url) / path
                async with session.get(url, headers=self._headers) as obj:
                    if not await check_fn(obj):
                        raise ValueError

            try:
                await check()
            except ValueError:
                self.fail(f'Nothing from {image_substring} found')


class DeleteMixin(_Base):
    """Tester mixin for DELETE requests."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def test_delete_success(self) -> None:
        """Checks if a DELETE request for the expected GET target succeeds with status 204."""
        async with self.client.request('DELETE',
                                       (self._href / self.expected_one_id()).path,
                                       headers=self._headers) as obj:
            self.assertEqual(204, obj.status)

    async def test_delete_fail(self) -> None:
        """Checks if a DELETE request for a target with an invalid ID fails with status 404."""
        async with self.client.request('DELETE',
                                       (self._href / '3').path,
                                       headers=self._headers) as obj:
            self.assertEqual(404, obj.status)

    async def test_delete_then_get(self) -> None:
        """Checks if a GET request to an object that was DELETEd previously fails with status 404."""
        async with self.client.request('DELETE',
                                       (self._href / self.expected_one_id()).path,
                                       headers=self._headers):
            pass
        async with self.client.request('GET',
                                       (self._href / self.expected_one_id()).path,
                                       headers=self._headers) as response:
            self.assertEqual(404, response.status)

    async def test_delete_then_get_all(self) -> None:
        """
        Checks if a GET all request to a directory where all the items were deleted by DELETE request returns no
        results. The test is skipped if either GET all requests do not work or there are no objects in the directory.
        """
        async with self.client.request('GET',
                                       (self._href / '').path,
                                       headers={**self._headers, hdrs.ACCEPT: nvpjson.MIME_TYPE}) as objs:
            if not objs.ok:
                self.skipTest(f'GET all requests are not working: {await objs.text()}')
            num_objects = len(await objs.json())
            if num_objects == 0:
                self.skipTest('there are no objects')
        async with self.client.request('DELETE',
                                       (self._href / self.expected_one_id()).path,
                                       headers=self._headers):
            pass
        async with self.client.request('GET',
                                       (self._href / '').path,
                                       headers=self._headers) as get2_resp:
            if not get2_resp.ok:
                self.skipTest(f'GET all requests are not working: {await get2_resp.text()}')
            self.assertEqual(num_objects - 1, len(await get2_resp.json()))

    async def test_delete_all_fail(self) -> None:
        """Checks if a DELETE request to delete everything in the directory fails with status 405."""
        async with self.client.request('DELETE',
                                       (self._href / '').path,
                                       headers=self._headers) as response:
            self.assertEqual(405, response.status)

    async def test_get_all_no_results(self) -> None:
        """
        Checks if doing a GET all request after all the items were deleted with DELETE requests returns the empty list.
        """
        to_delete: list[str] = []
        async with self.client.request('GET',
                                       (self._href / '').path,
                                       headers={**self._headers, hdrs.ACCEPT: nvpjson.MIME_TYPE}) as objs:
            if not objs.ok:
                self.skipTest('GET all requests are not working')
            for obj in await objs.json():

                if (id_ := obj.get('id')) is not None:
                    to_delete.append(id_)
                else:
                    self.skipTest(f'id not defined for object {obj}')
        failed: list[str] = []
        for id_ in to_delete:
            async with self.client.request('DELETE',
                                        (self._href / id_).path,
                                        headers=self._headers) as delete_resp:
                if delete_resp.status != 204:
                    self.fail(f'DELETE request did not work: {delete_resp.status} {await delete_resp.text()}')
                else:
                    async with self.client.request('GET',
                                                (self._href / id_).path,
                                                headers={**self._headers, hdrs.ACCEPT: nvpjson.MIME_TYPE}) as response:
                        if response.status != 404:
                            failed.append(id_)
        self.assertEqual([], failed)


class PermissionsPostMixin(_Base):
    """Tester for POST requests, assuming bad permissions."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    # None are passing because POST permissions haven't been implemented yet

    # async def test_post_bad_permissions_status(self) -> None:
    #     """
    #     Checks if a POST request fails with status 405 when the permissions do not allow the user to POST. The test
    #     is skipped if the unmodified body to POST (``_body_post``) is not defined.
    #     """
    #     if self._body_post:
    #         async with self.client.request('POST',
    #                                              (self._href / '').path,
    #                                              json=cj.to_nvpjson(self._body_post),
    #                                              headers={**self._headers, hdrs.CONTENT_TYPE: nvpjson.MIME_TYPE}) as response:
    #             self.assertEqual(405, response.status)
    #     else:
    #         self.skipTest('_body_post not defined')
    #
    # async def test_post_bad_permissions(self) -> None:
    #     """
    #     Checks if a GET all request returns the empty list when the permissions do not allow the user to POST. The test
    #     is skipped if the unmodified body to POST (``_body_post``) is not defined. The test may falsely pass if
    #     POSTing does not actually post anything; refer to ``PostMixin.test_post_then_get_status``.
    #     """
    #     if self._body_post:
    #         async with self.client.request('POST',
    #                                   (self._href / '').path,
    #                                   json=cj.to_nvpjson(self._body_post),
    #                                   headers={**self._headers, hdrs.CONTENT_TYPE: nvpjson.MIME_TYPE}):
    #             pass
    #         async with self.client.request('GET',  # Using a GET all request instead
    #                                              (self._href / '').path,
    #                                              headers={**self._headers, hdrs.ACCEPT: nvpjson.MIME_TYPE,
    #                                                       SUB: NONE_USER}) as response:
    #           self.assertEqual(2, len(await response.json()), 'POST posted something')
    #     else:
    #         self.skipTest('_body_post not defined')


class PermissionsPutMixin(_Base):
    """Tester for PUT requests, assuming bad permissions."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def test_put_bad_permissions(self) -> None:
        """
        Checks if a GET request after a PUT request shows that no changes were made when the user lacks editor
        permissions. The test is skipped if the unmodified body to PUT (``_body_put``) is not defined. The test may
        falsely pass if PUTing does not actually put anything; refer to ``PutMixin.test_put_then_get_status``.
        """
        if self._body_put:
            body_put = cj.to_nvpjson(self._body_put)
            async with self.client.request('PUT',
                                           (self._href / self.body_put_id()).path,
                                           json=body_put,
                                           headers={**self._headers, hdrs.CONTENT_TYPE: nvpjson.MIME_TYPE}):
                pass
            async with self.client.request('GET',
                                           (self._href / self.body_put_id()).path,
                                           headers={**self._headers, hdrs.ACCEPT: nvpjson.MIME_TYPE}) as response:
                for k, v in body_put.items():
                    if isinstance(v, date):
                        body_put[k] = v.isoformat()
                self.assertNotEqual(body_put, next(iter(await response.json()), None))
        else:
            self.skipTest('_body_put not defined')

    async def test_put_no_permissions_status(self) -> None:
        """
        Checks if a PUT request fails with status 404 when the user cannot view the target of the PUT request. The test
        is skipped if the unmodified body to PUT (``_body_put``) is not defined.
        """
        if self._body_put:
            changed = deepcopy_heaobject_dict_with(cj.to_nvpjson(self._body_put),
                                                   {'id': self.expected_one_id(), 'user_shares': []})
            async with self.client.request('PUT',
                                           (self._href / self.expected_one_id()).path,
                                           json=changed,
                                           headers={**self._headers, hdrs.CONTENT_TYPE: nvpjson.MIME_TYPE}) as response:
                self.assertEqual(404, response.status)
        else:
            self.skipTest('_body_put not defined')

    async def test_put_some_permissions_status(self) -> None:
        """
        Checks if a PUT request fails with status 403 when the user can view but not edit the target of the PUT
        request. The test is skipped if the unmodified body to PUT (``_body_put``) is not defined.
        """
        if self._body_put:
            async with self.client.request('PUT',
                                           (self._href / self.body_put_id()).path,
                                           json=cj.to_nvpjson(self._body_put),
                                           headers={**self._headers, hdrs.CONTENT_TYPE: nvpjson.MIME_TYPE}) as response:
                self.assertEqual(403, response.status)
        else:
            self.skipTest('_body_put not defined')

    async def test_put_content_bad_permissions(self) -> None:
        """
        Checks if a GET request after a PUT request to plaintext content shows that no changes were made when the
        user lacks editor permissions. The test is skipped if either the content ID (``_content_id``) is not defined
        or the put_content_status is 404 or 405. The test may falsely pass if PUTing does not actually put anything; refer
        to ``PutMixin.test_put_then_get_content_status``.
        """
        if self._content_id is None:
            self.skipTest('_content_id not defined')
        elif self._put_content_status in (404, 405):
            self.skipTest('PUT content is not defined for this microservice')
        else:
            async with self.client.request('PUT',
                                           (self._href / self._content_id / 'content').path,
                                           data='The quick brown fox jumps over the lazy dog',
                                           headers={**self._headers, hdrs.CONTENT_TYPE: 'text/plain'}):
                pass
            async with self.client.request('GET',
                                           (self._href / self._content_id / 'content').path,
                                           headers={**self._headers, hdrs.ACCEPT: 'text/plain'}) as response:
                self.assertEqual(b'', await response.read())

    async def test_put_content_no_permissions_status(self) -> None:
        """
        Checks if a PUT request to plaintext content fails with status 403 when the user cannot view the target of
        the PUT request. The test is skipped if the put_content_status is 404 or 405.
        """
        if self._put_content_status in (404, 405):
            self.skipTest('PUT content is not defined for this microservice')
        async with self.client.request('PUT',
                                       (self._href / self.expected_one_id() / 'content').path,
                                       data='The quick brown fox jumps over the lazy dog',
                                       headers={**self._headers, hdrs.CONTENT_TYPE: 'text/plain'}) as obj:
            self.assertEqual(404, obj.status)

    async def test_put_content_some_permissions_status(self) -> None:
        """
        Checks if a PUT request to plaintext content fails with status 403 when the user has viewer permissions but
        not editor permissions. The test is skipped if either the content ID (``_content_id``) is not defined or the
        put_content_status is 404 or 405.
        """
        if self._content_id is None:
            self.skipTest('_content_id not defined')
        elif self._put_content_status in (404, 405):
            self.skipTest('PUT content is not defined for this microservice')
        else:
            async with self.client.request('PUT',
                                           (self._href / self._content_id / 'content').path,
                                           data='The quick brown fox jumps over the lazy dog',
                                           headers={**self._headers, hdrs.CONTENT_TYPE: 'text/plain'}) as obj:
                self.assertEqual(403, obj.status)


class PermissionsGetOneMixin(_Base):
    """Tester for GET one requests, assuming bad permissions."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def test_get_bad_permissions(self) -> None:
        """Checks if a GET request fails with status 404 when the user does not have permissions to view the target."""
        async with self.client.request('GET',
                                       (self._href / self._id()).path,
                                       headers={**self._headers, hdrs.ACCEPT: nvpjson.MIME_TYPE}) as obj:
            self.assertEqual(b'404: Not Found', await obj.read())

    async def test_get_bad_permissions_status(self) -> None:
        """Checks if a GET request fails with status 404 when the user does not have permissions to view the target."""
        async with self.client.request('GET',
                                       (self._href / self._id()).path,
                                       headers={**self._headers, hdrs.ACCEPT: nvpjson.MIME_TYPE}) as obj:
            self.assertEqual(404, obj.status)

    async def test_get_content_bad_permissions(self) -> None:
        """
        Checks if a GET request for plaintext content fails when the user does not have viewer permissions. The test
        is skipped if the content id (``_content_id``) is not defined (this test uses the first fixture,
        this skip condition confirms that there is content).
        """
        if self._content_id is None:
            self.skipTest('GET content is not defined for this microservice')
        async with self.client.request('GET',
                                       (self._href / self._id() / 'content').path,
                                       headers={**self._headers, hdrs.ACCEPT: nvpjson.MIME_TYPE}) as obj:
            self.assertEqual(b'404: Not Found', await obj.read())

    async def test_get_content_bad_permissions_status(self) -> None:
        """
        Checks if a GET request for plaintext content fails with status 404 when the user does not have viewer
        permissions. The test is skipped if the content id (``_content_id``) is not defined (this test uses the first
        fixture, this skip condition confirms that there is content).
        """
        if self._content_id is None:
            self.skipTest('GET content is not defined for this microservice')
        async with self.client.request('GET',
                                       (self._href / self._id() / 'content').path,
                                       headers={**self._headers, hdrs.ACCEPT: nvpjson.MIME_TYPE}) as obj:
            self.assertEqual(404, obj.status)

    async def test_get_opener_bad_permissions(self) -> None:
        """Checks if a GET request for an object's opener fails when the user does not have viewer permissions."""
        async with self.client.request('GET',
                                       (self._href / self._id() / 'opener').path,
                                       headers={**self._headers, hdrs.ACCEPT: nvpjson.MIME_TYPE}) as obj:
            self.assertEqual(b'404: Not Found', await obj.read())

    async def test_get_opener_bad_permissions_status(self) -> None:
        """
        Checks if a GET request for an object's opener fails with status 404 when the user does not have viewer
        permissions.
        """
        async with self.client.request('GET',
                                       (self._href / self._id() / 'opener').path,
                                       headers={**self._headers, hdrs.ACCEPT: nvpjson.MIME_TYPE}) as obj:
            self.assertEqual(404, obj.status)

    async def test_get_duplicator_bad_permissions(self) -> None:
        """Checks if a GET request for an object's duplicator fails when the user does not have viewer permissions."""
        async with self.client.request('GET',
                                       (self._href / self._id() / 'duplicator').path,
                                       headers={**self._headers, hdrs.ACCEPT: nvpjson.MIME_TYPE}) as obj:
            self.assertEqual(b'404: Not Found', await obj.read())

    async def test_get_duplicator_bad_permissions_status(self) -> None:
        """
        Checks if a GET request for an object's duplicator fails with status 404 when the user does not have viewer
        permissions.
        """
        async with self.client.request('GET',
                                       (self._href / self._id() / 'duplicator').path,
                                       headers={**self._headers, hdrs.ACCEPT: nvpjson.MIME_TYPE}) as obj:
            self.assertEqual(404, obj.status)

    def _id(self):
        """Gets the ID of the target of a GET request."""
        return self.expected_one_id()


class PermissionsGetAllMixin(_Base):
    """Tester for GET all requests, assuming bad permissions."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def test_get_all_bad_permissions(self) -> None:
        """Checks if a GET all request does not back something to which the user does not have permissions."""
        if self._expected_one is None:
            self.skipTest('self._expected_one is None')
        else:
            async with self.client.request('GET',
                                           (self._href / '').path,
                                           headers={**self._headers, hdrs.ACCEPT: cj.MIME_TYPE}) as obj:
                result = await obj.json()
                self.assertNotIn(self._expected_one[0], result)

    async def test_get_all_bad_permissions_count(self) -> None:
        """
        Checks if a GET all request only backs one object when the user has access to one object but not the other.
        """
        async with self.client.request('GET',
                                       (self._href / '').path,
                                       headers={**self._headers, hdrs.ACCEPT: cj.MIME_TYPE}) as obj:
            result = await obj.json()
            self.assertEqual(1, len(result))


class PermissionsDeleteMixin(_Base):
    """Tester for DELETE requests, assuming bad permissions."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def test_delete_no_permissions(self) -> None:
        """
        Checks if a GET request after a DELETE request succeeds with status 200 when the user does not have the
        permissions to view the object.
        """
        async with self.client.request('DELETE',
                                       (self._href / self._get_id()).path,
                                       headers=self._headers):
            pass
        async with self.client.request('GET',
                                       (self._href / self._get_id()).path,
                                       headers={**self._headers, SUB: NONE_USER}) as response:
            self.assertEqual(200, response.status)

    async def test_delete_no_permissions_status(self) -> None:
        """
        Checks if a DELETE request fails with status 404 when the user does not have the permissions to view the
        object.
        """
        async with self.client.request('DELETE',
                                       (self._href / self._get_id()).path,
                                       headers=self._headers) as response:
            self.assertEqual(404, response.status)

    async def test_delete_some_permissions(self) -> None:
        """
        Checks if a GET request after a DELETE request succeeds with status 200 when the user does not have the
        permissions to delete the object but does have the permissions to view the object. The test is skipped if the
        body used in a PUT test (``_body_put``) is not defined.
        """
        if self._body_put is None:
            self.skipTest('body_put is not defined')
        async with self.client.request('DELETE',
                                       (self._href / self._put_id()).path,
                                       headers=self._headers):
            pass
        async with self.client.request('GET',
                                       (self._href / self._put_id()).path,
                                       headers={**self._headers, SUB: NONE_USER}) as response:
            self.assertEqual(200, response.status)

    async def test_delete_some_permissions_status(self) -> None:
        """
        Checks if a DELETE request fails with status 403 when the user does not have the permissions to delete the
        object but does have the permissions to view the object. The test is skipped if the body used in a PUT test
        (``_body_put``) is not defined.
        """
        if self._body_put is None:
            self.skipTest('body_put is not defined')
        async with self.client.request('DELETE',
                                       (self._href / self._put_id()).path,
                                       headers=self._headers) as response:
            self.assertEqual(403, response.status)

    def _put_id(self):
        """Gets the ID of the target of a PUT request, determined by the value of the template ``_body_put``."""
        logging.getLogger(__name__).debug('Template is %s', self._body_put)
        for e in self._body_put['template']['data']:
            if e['name'] == 'id':
                return e.get('value')

    def _get_id(self):
        """Gets the ID of the target of a GET request."""
        logging.getLogger(__name__).debug('Collection is %s', self._body_put)
        for e in self._expected_one[0]['collection']['items'][0]['data']:
            if e['name'] == 'id':
                return e.get('value')


def _to_xwwwformurlencoded_data(template) -> str:
    """
    Converts data in the given template to encoded form data.

    :param template: The template that contains data that will be converted
    :return: The data from the template converted to encoded form data
    """
    _logger = logging.getLogger(__name__)
    _logger.debug('Encoding %s', template)
    e = {}
    jsonschemavalidator.CJ_TEMPLATE_SCHEMA_VALIDATOR.validate(template)
    for e_ in template['template']['data']:
        if 'section' in e_:
            raise jsonschemavalidator.ValidationError('XWWWFormUrlEncoded does not support the section property')
        if e_['value'] is not None:
            e[e_['name']] = e_['value']
    result = urlencode(e, doseq=True)
    _logger.debug('Returning %s', result)
    return result


def _ordered(obj: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None) -> Any:
    """
    Sorts the JSON dictionaries to ensure consistency when comparing values.

    :param obj: The JSON dictionary or list of dictionaries to be ordered.
    :return: The ordered object, for comparison with other ordered objects.
    :except TypeError: When the type of the contents of obj, if it is a list, cannot be sorted with ``sorted``
    """
    if isinstance(obj, dict):
        def _ordered_one(k, v):
            if k == 'rel' and isinstance(v, str):
                return k, ' '.join(sorted(v.split() if v else []))
            else:
                return k, _ordered(v)

        return sorted((_ordered_one(k, v) for k, v in obj.items()))
    if isinstance(obj, list):
        try:
            return sorted(_ordered(x) for x in obj)
        except TypeError as t:
            print('obj is {}'.format(obj))
            raise t
    elif isinstance(obj, date):
        return obj.isoformat()
    else:
        return str(obj)
