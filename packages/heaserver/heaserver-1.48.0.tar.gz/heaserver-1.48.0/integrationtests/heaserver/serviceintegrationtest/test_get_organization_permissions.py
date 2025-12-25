from heaserver.service.testcase.mixin import GetOneMixin
from .organizationtestcase import OrganizationTestCase


class TestGetOrganization(OrganizationTestCase, GetOneMixin):  # type: ignore
    pass
