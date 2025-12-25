from .componentpermissionstestcase import ComponentPermissionsTestCase
from heaserver.service.testcase.mixin import PermissionsPostMixin, PermissionsPutMixin, PermissionsGetOneMixin, \
    PermissionsGetAllMixin, PermissionsDeleteMixin


class TestPostComponentWithBadPermissions(ComponentPermissionsTestCase, PermissionsPostMixin):
    """A test case class for testing POST requests with bad permissions."""
    pass


class TestPutComponentWithBadPermissions(ComponentPermissionsTestCase, PermissionsPutMixin):
    """A test case class for testing PUT requests with bad permissions."""
    pass


class TestGetOneComponentWithBadPermissions(ComponentPermissionsTestCase, PermissionsGetOneMixin):
    """A test case class for testing GET one requests with bad permissions."""
    pass


class TestGetAllComponentsWithBadPermissions(ComponentPermissionsTestCase, PermissionsGetAllMixin):
    """A test case class for testing GET all requests with bad permissions."""
    pass


class TestDeleteComponentsWithBadPermissions(ComponentPermissionsTestCase, PermissionsDeleteMixin):
    """A test case class for testing DELETE requests with bad permissions."""
    pass
