"""
Creates a test case class for use with the unittest library that is built into Python.
"""
from heaobject.activity import Status
from heaserver.service.testcase.microservicetestcase import get_test_case_cls_default
from heaserver.service.testcase.dockermongo import MockDockerMongoManager
from heaserver.activity import service
from heaobject.user import NONE_USER, TEST_USER
from heaobject.root import Permission
from heaserver.service.testcase.expectedvalues import Action

db_store = {
    service.MONGODB_DESKTOP_OBJECT_ACTION_COLLECTION: [{
        'id': '666f6f2d6261722d71757578',
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
        'action': 'GET',
        'status': Status.SUCCEEDED.name,
        'arn': 'a:1323444',
        'user_id': 'user-a',
        'source': None,
        'source_detail': None,
        'type': 'heaobject.activity.DesktopObjectAction',
        'old_object_uri': None,
        'new_object_uri': None,
        'dynamic_permission_supported': False,
        'super_admin_default_permissions': [p.name for p in Permission.non_creator_permissions()]
    },
        {
            'id': '0123456789ab0123456789ab',
            'created': None,
            'derived_by': None,
            'derived_from': [],
            'description': None,
            'display_name': 'Luximus',
            'invites': [],
            'modified': None,
            'name': 'luximus',
            'owner': NONE_USER,
            'shares': [{
                'type': 'heaobject.root.ShareImpl',
                'invite': None,
                'user': TEST_USER,
                'permissions': [Permission.VIEWER.name]
            }],
            'user_shares': [{
                'type': 'heaobject.root.ShareImpl',
                'invite': None,
                'user': TEST_USER,
                'permissions': [Permission.VIEWER.name]
            }],
            'action': 'GET',
            'status': Status.IN_PROGRESS.name,
            'arn': 'a:1323444',
            'user_id': 'user-a',
            'source': None,
            'source_detail': None,
            'type': 'heaobject.activity.DesktopObjectAction',
            'old_object_uri': None,
            'new_object_uri': None,
            'dynamic_permission_supported': False,
            'super_admin_default_permissions': [p.name for p in Permission.non_creator_permissions()]
        }]}


PermissionsTestCase = \
    get_test_case_cls_default(coll=service.MONGODB_DESKTOP_OBJECT_ACTION_COLLECTION,
                              wstl_package=service.__package__,
                              href='http://localhost:8080/desktopobjectactions',
                              fixtures=db_store,
                              db_manager_cls=MockDockerMongoManager,
                              get_actions=[Action(name='heaserver-activity-desktopobjectaction-get-properties',
                                                         rel=['hea-properties']),
                                                  Action(name='heaserver-activity-desktopobjectaction-get-self',
                                                         url='http://localhost:8080/desktopobjectactions/{id}',
                                                         rel=['self']),
                                                  Action(name='heaserver-activity-desktopobjectaction-get-old-object-uri',
                                                         url='http://localhost:8080{+old_object_uri}',
                                                         rel=['hea-desktop-object'],
                                                         itemif='old_object_uri is not None and new_object_uri is None'),
                                                  Action(name='heaserver-activity-desktopobjectaction-get-new-object-uri',
                                                         url='http://localhost:8080{+new_object_uri}',
                                                         rel=['hea-desktop-object'],
                                                         itemif='new_object_uri is not None')
                                                  ],
                              get_all_actions=[Action(name='heaserver-activity-desktopobjectaction-get-properties',
                                                             rel=['hea-properties']),
                                                      Action(name='heaserver-activity-desktopobjectaction-get-self',
                                                             url='http://localhost:8080/desktopobjectactions/{id}',
                                                             rel=['self']),
                                                      Action(name='heaserver-activity-desktopobjectaction-get-old-object-uri',
                                                             url='http://localhost:8080{+old_object_uri}',
                                                             rel=['hea-desktop-object'],
                                                             itemif='old_object_uri is not None and new_object_uri is None'),
                                                      Action(name='heaserver-activity-desktopobjectaction-get-new-object-uri',
                                                             url='http://localhost:8080{+new_object_uri}',
                                                             rel=['hea-desktop-object'],
                                                             itemif='new_object_uri is not None')],
                              sub=TEST_USER)
