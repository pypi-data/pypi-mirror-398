from .componenttestcase import ComponentTestCase, ComponentTestCase2, ComponentTestCase3
from heaserver.service.testcase.mixin import GetAllMixin


class TestGetAllRootItems(ComponentTestCase, GetAllMixin):  # type: ignore
    pass


class TestGetAllRootItems2(ComponentTestCase2, GetAllMixin):  # type: ignore
    pass


class TestGetAllRootItems3(ComponentTestCase3, GetAllMixin):  # type: ignore
    pass
