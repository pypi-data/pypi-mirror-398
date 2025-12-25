from .componenttestcase import ComponentTestCase
from heaserver.service.testcase.mixin import PutMixin


class TestPutComponent(ComponentTestCase, PutMixin):  # type: ignore

    async def test_put_status_invalid_base_url(self):
        await self._test_invalid({'base_url': 2})

    async def test_put_status_invalid_resource(self):
        await self._test_invalid({'resources': [2]})



