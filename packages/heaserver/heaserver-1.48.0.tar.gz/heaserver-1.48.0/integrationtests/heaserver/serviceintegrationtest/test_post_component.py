from .componenttestcase import ComponentTestCase
from heaserver.service.testcase.mixin import PostMixin


class TestPostComponent(ComponentTestCase, PostMixin):  # type: ignore

    async def test_post_status_invalid_base_url(self):
        await self._test_invalid({'base_url': 2})

    async def test_post_status_invalid_resource(self):
        await self._test_invalid({'resources': [2]})

    async def test_post_status_invalid_resources_list(self):
        await self._test_invalid({'resources': 2})

