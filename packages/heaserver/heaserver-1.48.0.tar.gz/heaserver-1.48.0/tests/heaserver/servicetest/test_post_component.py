from .componenttestcase import ComponentTestCase
from heaserver.service.testcase.mixin import PostMixin


class TestPostComponent(ComponentTestCase, PostMixin):  # type: ignore

    async def test_post_status_invalid_base_url(self):
        """
        Checks if a POST request fails with status 400 when the ``base_url`` field is passed a value not of type
        ``str``.
        """
        await self._test_invalid({'base_url': 2})

    async def test_post_status_invalid_resource(self):
        """
        Checks if a POST request fails with status 400 when the ``resources`` field is passed an iterable that contains
        a value not of type ``heaobject.registry.Resource``.
        """
        await self._test_invalid({'resources': [2]})

    async def test_post_status_invalid_resources_list(self):
        """
        Checks if a POST request fails with status 400 when the ``resources`` field is not passed an iterable.
        """
        await self._test_invalid({'resources': 2})

    async def test_post_status_invalid_resources_none(self):
        """
        Checks if a POST request fails with status 400 when the ``resources`` field is passed ``None``.
        """
        await self._test_invalid({'resources': None})
