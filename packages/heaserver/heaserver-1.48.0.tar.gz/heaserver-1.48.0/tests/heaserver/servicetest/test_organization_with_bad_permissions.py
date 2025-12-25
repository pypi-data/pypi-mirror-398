from .organizationpermissionstestcase import OrganizationPermissionsTestCase
from heaserver.service.testcase.mixin import PermissionsPostMixin, PermissionsPutMixin, PermissionsGetOneMixin, \
    PermissionsGetAllMixin


class TestPostOrganizationWithBadPermissions(OrganizationPermissionsTestCase, PermissionsPostMixin):
    """A test case class for testing POST requests with bad permissions."""
    pass


class TestPutOrganizationWithBadPermissions(OrganizationPermissionsTestCase, PermissionsPutMixin):
    """A test case class for testing PUT requests with bad permissions."""
    pass


class TestGetOneOrganizationWithBadPermissions(OrganizationPermissionsTestCase, PermissionsGetOneMixin):
    """A test case class for testing GET one requests with bad permissions."""
    pass


class TestGetAllOrganizationsWithBadPermissions(OrganizationPermissionsTestCase, PermissionsGetAllMixin):
    """A test case class for testing GET all requests with bad permissions."""
    pass
