from .permissionstestcase import PermissionsTestCase
from heaserver.service.testcase.mixin import PermissionsPostMixin, PermissionsPutMixin, PermissionsGetOneMixin, \
    PermissionsGetAllMixin, PermissionsDeleteMixin


class TestPostWithBadPermissions(PermissionsTestCase, PermissionsPostMixin):
    """A test case class for testing POST requests with bad permissions."""
    pass


class TestPutWithBadPermissions(PermissionsTestCase, PermissionsPutMixin):
    """A test case class for testing PUT requests with bad permissions."""
    pass


class TestGetOneWithBadPermissions(PermissionsTestCase, PermissionsGetOneMixin):
    """A test case class for testing GET one requests with bad permissions."""
    pass


class TestGetAllWithBadPermissions(PermissionsTestCase, PermissionsGetAllMixin):
    """A test case class for testing GET all requests with bad permissions."""
    pass


class TestDeleteWithBadPermissions(PermissionsTestCase, PermissionsDeleteMixin):
    """A test case class for testing DELETE requests with bad permissions."""
    pass
