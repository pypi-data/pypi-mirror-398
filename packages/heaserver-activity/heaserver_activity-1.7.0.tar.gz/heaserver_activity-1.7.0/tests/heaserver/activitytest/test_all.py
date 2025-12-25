from aiohttp import hdrs
from heaserver.service.representor import nvpjson

from .testcase import TestCase
from heaserver.service.testcase.mixin import GetOneMixin, GetAllMixin
from heaobject.user import NONE_USER
from heaobject.project import AWSS3Project
from heaobject.root import Permission
from heaobject.activity import Status


class TestGet(TestCase, GetOneMixin):
    pass


class TestGetAll(TestCase, GetAllMixin):
    async def test_get_all_no_hea_get_json(self) -> None:
        """
        Checks if a GET request for all the items as JSON succeeds and returns the expected value
        (``_expected_all``).
        """
        async with self.client.request('GET',
                                       (self._href / '').with_query({'excludecode': 'hea-get'}).path_qs,
                                       headers={**self._headers, hdrs.ACCEPT: nvpjson.MIME_TYPE}) as obj:
            self.assertEqual([{
                'id': '666f6f2d6261722d71757578',
                'instance_id': 'heaobject.activity.DesktopObjectAction^666f6f2d6261722d71757578',
                'created': None,
                'derived_by': None,
                'derived_from': [],
                'description': None,
                'display_name': 'Reximus',
                'invites': [],
                'modified': None,
                'name': 'reximus',
                'owner': NONE_USER,
                'shares': [],
                'user_shares': [],
                'group_shares': [],
                'status': Status.SUCCEEDED.name,
                'user_id': 'user-a',
                'source': None,
                'source_detail': None,
                'type': 'heaobject.activity.DesktopObjectAction',
                'old_object_uri': None,
                'new_object_uri': 'awss3projects/666f6f2d6261722d71757578',
                'old_object_type_name': None,
                'new_object_type_name': AWSS3Project.get_type_name(),
                'old_object_id': None,
                'new_object_id': '666f6f2d6261722d71757578',
                'application_id': None,
                'code': None,
                'duration': 64800,
                'ended': '2022-05-17T00:00:00+00:00',
                'human_readable_duration': '6 hours',
                'mime_type': 'application/x.desktopobjectaction',
                'new_volume_id': None,
                'old_volume_id': None,
                'requested': '2022-05-17T00:00:00-06:00',
                'status_updated': '2022-05-17T00:00:00+00:00',
                'began': '2022-05-17T00:00:00-06:00',
                'type_display_name': 'Desktop Object Action',
                'request_url': None,
                'context': None,
                'old_context_dependent_object_path': None,
                'new_context_dependent_object_path': None,
                'old_object_description': None,
                'new_object_description': None,
                'old_object_display_name': None,
                'new_object_display_name': None,
                'dynamic_permission_supported': False,
                'super_admin_default_permissions': [p.name for p in Permission if p is not Permission.CREATOR]
            }], await obj.json())
