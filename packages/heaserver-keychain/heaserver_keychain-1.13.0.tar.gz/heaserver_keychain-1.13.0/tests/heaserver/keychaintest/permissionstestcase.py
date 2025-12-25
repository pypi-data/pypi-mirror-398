"""
Creates a test case class for use with the unittest library that is built into Python.
"""

from heaserver.service.testcase.microservicetestcase import get_test_case_cls_default
from heaserver.keychain import service
from heaobject.user import NONE_USER, TEST_USER
from heaobject.root import Permission
from heaserver.service.testcase.expectedvalues import Action

db_store = {
    service.MONGODB_CREDENTIALS_COLLECTION: [{
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
        'user_shares': [],
        'group_shares': [],
        'source': None,
        'source_detail': None,
        'type': 'heaobject.keychain.Credentials',
        'version': None,
        'role': None,
        'dynamic_permission_supported': False
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
                'permissions': [Permission.VIEWER.name],
                'group': NONE_USER,
                'basis': 'USER'
            }],
            'user_shares': [{
                'type': 'heaobject.root.ShareImpl',
                'invite': None,
                'user': TEST_USER,
                'permissions': [Permission.VIEWER.name],
                'group': NONE_USER,
                'basis': 'USER'
            }],
            'group_shares': [],
            'source': None,
            'source_detail': None,
            'type': 'heaobject.keychain.Credentials',
            'version': None,
            'role': None,
            'dynamic_permission_supported': False
        }]}

PermissionsTestCase = \
    get_test_case_cls_default(coll=service.MONGODB_CREDENTIALS_COLLECTION,
                              wstl_package=service.__package__,
                              href='http://localhost:8080/credentials/',
                              fixtures=db_store,
                              get_actions=[Action(name='heaserver-keychain-credentials-get-properties',
                                                  rel=['hea-properties']),
                                           # Action(name='heaserver-keychain-credentials-open-choices',
                                           #        url='http://localhost:8080/credentials/{id}/opener',
                                           #        rel=['hea-opener']),
                                           # Action(name='heaserver-keychain-credentials-duplicate',
                                           #        url='http://localhost:8080/credentials/{id}/duplicator',
                                           #        rel=['hea-duplicator'])
                                           ],
                              get_all_actions=[Action(name='heaserver-keychain-credentials-get-properties',
                                                      rel=['hea-properties']),
                                               # Action(name='heaserver-keychain-credentials-open-choices',
                                               #        url='http://localhost:8080/credentials/{id}/opener',
                                               #        rel=['hea-opener']),
                                               # Action(name='heaserver-keychain-credentials-duplicate',
                                               #        url='http://localhost:8080/credentials/{id}/duplicator',
                                               #        rel=['hea-duplicator'])
                                               ],
                              #duplicate_action_name='heaserver-keychain-credentials-duplicate-form',
                              put_content_status=404,
                              sub=TEST_USER)
