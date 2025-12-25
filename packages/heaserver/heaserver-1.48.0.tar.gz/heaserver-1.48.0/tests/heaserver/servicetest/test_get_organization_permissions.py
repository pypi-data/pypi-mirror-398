from .organizationtestcase import OrganizationTestCase
from heaserver.service.testcase.mixin import GetOneMixin



class TestGetOrganization(OrganizationTestCase, GetOneMixin):  # type: ignore
    pass
