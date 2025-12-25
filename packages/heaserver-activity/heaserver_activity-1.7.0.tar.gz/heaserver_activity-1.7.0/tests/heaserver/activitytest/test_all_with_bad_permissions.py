from .permissionstestcase import PermissionsTestCase
from heaserver.service.testcase.mixin import PermissionsGetOneMixin, PermissionsGetAllMixin


class TestGetWithBadPermissions(PermissionsTestCase, PermissionsGetOneMixin):
    pass


class TestGetAllWithBadPermissions(PermissionsTestCase, PermissionsGetAllMixin):
    pass

