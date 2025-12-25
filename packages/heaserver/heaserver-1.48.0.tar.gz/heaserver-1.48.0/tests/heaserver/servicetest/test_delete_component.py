from .componenttestcase import ComponentTestCase
from heaserver.service.testcase.mixin import DeleteMixin


class TestDeleteComponent(ComponentTestCase, DeleteMixin):  # type: ignore
    pass



