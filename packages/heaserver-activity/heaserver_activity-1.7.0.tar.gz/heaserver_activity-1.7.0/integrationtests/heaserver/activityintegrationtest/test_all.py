from .testcase import RecentlyAccessedViewsByTypeTestCase, DesktopObjectSummaryViewsByTypeTestCase
from heaserver.service.testcase.mixin import GetAllMixin, _ordered

class TestRecentlyAccessedGetAll(RecentlyAccessedViewsByTypeTestCase, GetAllMixin):
    async def test_get_all_object_uri(self) -> None:
        """Checks if a GET request for all the items succeeds with status 200."""
        async with self.client.request('GET',
                                       (self._href / '').with_query({'object_uri': 'awss3projects/666f6f2d6261722d71757578'}).path_qs,
                                       headers=self._headers) as obj:
            expected = [{'collection': {'version': '1.0', 'href':
                                        'http://localhost:8080/recentlyaccessedviews/bytype/heaobject.project.AWSS3Project/?object_uri=awss3projects/666f6f2d6261722d71757578',
                                        'permissions': [['VIEWER', 'EDITOR', 'SHARER', 'COOWNER', 'DELETER']],
                                        'items': [
                                            {'data': [
                                                {'name': 'accessed', 'value': '2022-05-17T00:00:00-06:00', 'prompt': 'accessed', 'display': True},
                                                {'name': 'actual_object_id', 'value': '666f6f2d6261722d71757578', 'prompt': 'actual_object_id', 'display': True},
                                                {'name': 'actual_object_type_name', 'value': 'heaobject.project.AWSS3Project', 'prompt': 'actual_object_type_name', 'display': True},
                                                {'name': 'actual_object_uri', 'value': 'awss3projects/666f6f2d6261722d71757578', 'prompt': 'actual_object_uri', 'display': True},
                                                {'name': 'context', 'value': None, 'prompt': 'context', 'display': True},
                                                {'name': 'context_dependent_object_path', 'value': None, 'prompt': 'context_dependent_object_path', 'display': True},
                                                {'name': 'created', 'value': None, 'prompt': 'created', 'display': True},
                                                {'name': 'derived_by', 'value': None, 'prompt': 'derived_by', 'display': True},
                                                {'name': 'derived_from', 'value': [], 'prompt': 'derived_from', 'display': True},
                                                {'name': 'description', 'value': None, 'prompt': 'description', 'display': True},
                                                {'name': 'display_name', 'value': 'Reximus', 'prompt': 'display_name', 'display': True},
                                                {'name': 'id', 'value': '666f6f2d6261722d71757578', 'prompt': 'id', 'display': False},
                                                {'name': 'instance_id', 'value': 'heaobject.activity.RecentlyAccessedView^666f6f2d6261722d71757578', 'prompt': 'instance_id', 'display': True},
                                                {'name': 'invites', 'value': [], 'prompt': 'invites', 'display': True},
                                                {'name': 'modified', 'value': None, 'prompt': 'modified', 'display': True},
                                                {'name': 'name', 'value': None, 'prompt': 'name', 'display': True},
                                                {'name': 'owner', 'value': 'system|none', 'prompt': 'owner', 'display': True},
                                                {'name': 'shares', 'value': [], 'prompt': 'shares', 'display': True},
                                                {'name': 'user_shares', 'value': [], 'prompt': 'user_shares', 'display': True},
                                                {'name': 'group_shares', 'value': [], 'prompt': 'group_shares', 'display': True},
                                                {'name': 'source', 'value': None, 'prompt': 'source', 'display': True},
                                                {'name': 'source_detail', 'value': None, 'prompt': 'source_detail', 'display': True},
                                                {'name': 'type', 'value': 'heaobject.activity.RecentlyAccessedView', 'prompt': 'type', 'display': True},
                                                {'name': 'type_display_name', 'value': 'Recently Accessed View', 'prompt': 'type_display_name', 'display': True},
                                                {'name': 'dynamic_permission_supported', 'value': False, 'prompt': 'dynamic_permission_supported', 'display': True},
                                                {'name': 'super_admin_default_permissions', 'value': [], 'prompt': 'super_admin_default_permissions', 'display': True}
                                            ],
                                            'links': [{'prompt': 'Get actual', 'rel': 'hea-actual', 'href': 'http://localhost:8080/awss3projects/666f6f2d6261722d71757578'}]
                                            }
                                        ]}}]
            actual = await obj.json()
            self.assertEqual(_ordered(expected), _ordered(actual))

class TestSummaryViewGetAll(DesktopObjectSummaryViewsByTypeTestCase, GetAllMixin):
    async def test_get_all_object_uri(self) -> None:
        """Checks if a GET request for all the items succeeds with status 200."""
        async with self.client.request('GET',
                                       (self._href / '').with_query({'object_uri': 'awss3projects/666f6f2d6261722d71757578'}).path_qs,
                                       headers=self._headers) as obj:
            expected = [{'collection': {'version': '1.0', 'href':
                                        'http://localhost:8080/desktopobjectsummaryviews/bytype/heaobject.project.AWSS3Project/?object_uri=awss3projects/666f6f2d6261722d71757578',
                                        'permissions': [['VIEWER', 'EDITOR', 'SHARER', 'COOWNER', 'DELETER']],
                                        'items': [
                                            {'data': [
                                                {'name': 'accessed', 'value': '2022-05-17T00:00:00-06:00', 'prompt': 'accessed', 'display': True},
                                                {'name': 'actual_object_id', 'value': '666f6f2d6261722d71757578', 'prompt': 'actual_object_id', 'display': True},
                                                {'name': 'actual_object_type_name', 'value': 'heaobject.project.AWSS3Project', 'prompt': 'actual_object_type_name', 'display': True},
                                                {'name': 'actual_object_uri', 'value': 'awss3projects/666f6f2d6261722d71757578', 'prompt': 'actual_object_uri', 'display': True},
                                                {'name': 'context', 'value': None, 'prompt': 'context', 'display': True},
                                                {'name': 'context_dependent_object_path', 'value': None, 'prompt': 'context_dependent_object_path', 'display': True},
                                                {'name': 'created', 'value': None, 'prompt': 'created', 'display': True},
                                                {'name': 'derived_by', 'value': None, 'prompt': 'derived_by', 'display': True},
                                                {'name': 'derived_from', 'value': [], 'prompt': 'derived_from', 'display': True},
                                                {'name': 'description', 'value': None, 'prompt': 'description', 'display': True},
                                                {'name': 'display_name', 'value': 'Reximus', 'prompt': 'display_name', 'display': True},
                                                {'name': 'id', 'value': '666f6f2d6261722d71757578', 'prompt': 'id', 'display': False},
                                                {'name': 'instance_id', 'value': 'heaobject.activity.DesktopObjectSummaryView^666f6f2d6261722d71757578', 'prompt': 'instance_id', 'display': True},
                                                {'name': 'invites', 'value': [], 'prompt': 'invites', 'display': True},
                                                {'name': 'modified', 'value': None, 'prompt': 'modified', 'display': True},
                                                {'name': 'name', 'value': None, 'prompt': 'name', 'display': True},
                                                {'name': 'owner', 'value': 'system|none', 'prompt': 'owner', 'display': True},
                                                {'name': 'shares', 'value': [], 'prompt': 'shares', 'display': True},
                                                {'name': 'user_shares', 'value': [], 'prompt': 'user_shares', 'display': True},
                                                {'name': 'group_shares', 'value': [], 'prompt': 'group_shares', 'display': True},
                                                {'name': 'source', 'value': None, 'prompt': 'source', 'display': True},
                                                {'name': 'source_detail', 'value': None, 'prompt': 'source_detail', 'display': True},
                                                {'name': 'status', 'value': 'PRESENT', 'prompt': 'status', 'display': True},
                                                {'name': 'type', 'value': 'heaobject.activity.DesktopObjectSummaryView', 'prompt': 'type', 'display': True},
                                                {'name': 'type_display_name', 'value': 'Desktop Object Summary View', 'prompt': 'type_display_name', 'display': True},
                                                {'name': 'dynamic_permission_supported', 'value': False, 'prompt': 'dynamic_permission_supported', 'display': True},
                                                {'name': 'super_admin_default_permissions', 'value': [], 'prompt': 'super_admin_default_permissions', 'display': True}
                                            ],
                                            'links': [{'prompt': 'Get actual', 'rel': 'hea-actual', 'href': 'http://localhost:8080/awss3projects/666f6f2d6261722d71757578'}]
                                            }
                                        ]}}]
            actual = await obj.json()
            self.assertEqual(_ordered(expected), _ordered(actual))
