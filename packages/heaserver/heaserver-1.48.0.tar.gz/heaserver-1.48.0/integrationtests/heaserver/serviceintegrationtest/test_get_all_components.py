from .componenttestcase import ComponentTestCase
from heaserver.service.testcase.mixin import GetAllMixin


class TestGetAllItems(ComponentTestCase, GetAllMixin):  # type: ignore
    pass
