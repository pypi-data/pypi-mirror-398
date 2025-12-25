from .componenttestcase import ComponentTestCase
from heaserver.service.testcase.mixin import PutMixin
from .organizationtestcase import OrganizationTestCase


class TestPutOrganization(OrganizationTestCase, PutMixin):  # type: ignore
    pass

