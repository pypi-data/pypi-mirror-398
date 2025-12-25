"""
Creates a test case class for use with the unittest library that is built into Python.
"""

from .testcase import get_test_case_cls
from heaserver.service.testcase import expectedvalues
from heaserver.service.testcase.dockermongo import MockDockerMongoManager
from heaserver.volume import service
from heaobject.user import NONE_USER, TEST_USER
from heaobject.root import Permission
from heaserver.service.testcase.expectedvalues import Action

db_store = {
    service.MONGODB_VOLUME_COLLECTION: [{
        'id': '666f6f2d6261722d71757578',
        'created': None,
        'derived_by': None,
        'derived_from': [],
        'description': None,
        'display_name': 'Reximus',
        'invites': [],
        'modified': None,
        'name': 'heaobject.volume.MongoDBFileSystem^DEFAULT_FILE_SYSTEM',
        'owner': NONE_USER,
        'source': None,
        'source_detail': None,
        'type': 'heaobject.volume.Volume',
        'file_system_type': 'heaobject.volume.MongoDBFileSystem',
        'file_system_name': 'DEFAULT_FILE_SYSTEM',
        'account': None,
        'shares': [],
        'user_shares': [],
        'group_shares': []
    },
        {
            'id': '0123456789ab0123456789ab',
            'created': None,
            'derived_by': None,
            'derived_from': [],
            'description': None,
            'display_name': 'heaobject.volume.AWSFileSystem^DEFAULT_FILE_SYSTEM',
            'invites': [],
            'shares': [{
                'type': 'heaobject.root.ShareImpl',
                'invite': None,
                'user': TEST_USER,
                'group': NONE_USER,
                'permissions': [Permission.VIEWER.name],
                'basis': 'USER'
            }],
            'user_shares': [{
                'type': 'heaobject.root.ShareImpl',
                'invite': None,
                'user': TEST_USER,
                'group': NONE_USER,
                'permissions': [Permission.VIEWER.name],
                'basis': 'USER'
            }],
            'group_shares': [],
            'modified': None,
            'name': 'luximus',
            'owner': NONE_USER,
            'source': None,
            'source_detail': None,
            'type': 'heaobject.volume.Volume',
            'file_system_type': 'heaobject.volume.AWSFileSystem',
            'file_system_name': 'DEFAULT_FILE_SYSTEM',
            'account': None
        }
    ],
    service.MONGODB_FILE_SYSTEM_COLLECTION: [{
        'id': '666f6f2d6261722d71757578',
        'created': None,
        'derived_by': None,
        'derived_from': [],
        'description': 'Access to Amazon Web Services (AWS)',
        'display_name': 'Amazon Web Services',
        'invites': [],
        'modified': None,
        'name': 'DEFAULT_FILE_SYSTEM',
        'owner': NONE_USER,
        'source': None,
        'source_detail': None,
        'type': 'heaobject.volume.AWSFileSystem',
        'shares': [],
        'user_shares': [],
        'group_shares': []
    },
        {
            'id': '0123456789ab0123456789ab',
            'created': None,
            'derived_by': None,
            'derived_from': [],
            'description': None,
            'display_name': 'Local MongoDB instance',
            'invites': [],
            'shares': [{
                'type': 'heaobject.root.ShareImpl',
                'invite': None,
                'user': TEST_USER,
                'group': NONE_USER,
                'permissions': [Permission.VIEWER.name],
                'basis': 'USER'
            }],
            'user_shares': [{
                'type': 'heaobject.root.ShareImpl',
                'invite': None,
                'user': TEST_USER,
                'group': NONE_USER,
                'permissions': [Permission.VIEWER.name],
                'basis': 'USER'
            }],
            'group_shares': [],
            'modified': None,
            'name': 'local_mongodb_file_system',
            'owner': NONE_USER,
            'source': None,
            'source_detail': None,
            'type': 'heaobject.volume.MongoDBFileSystem',
            'database_name': 'hea',
            'connection_string': 'mongodb://heauser:heauser@localhost:27017/hea'
        }]
}

VolumePermissionsTestCase = \
    get_test_case_cls(coll=service.MONGODB_VOLUME_COLLECTION,
                      wstl_package=service.__package__,
                      href='http://localhost:8080/volumes',
                      db_manager_cls=MockDockerMongoManager,
                      fixtures=db_store,
                      get_actions=[Action(name='heaserver-volumes-volume-get-properties',
                                          rel=['hea-properties']),
                                   Action(name='heaserver-volumes-volume-get-open-choices',
                                          url='http://localhost:8080/volumes/{id}/opener',
                                          rel=['hea-opener-choices']),
                                   Action(name='heaserver-volumes-volume-duplicate',
                                          url='http://localhost:8080/volumes/{id}/duplicator',
                                          rel=['hea-duplicator'])
                                   ],
                      get_all_actions=[Action(name='heaserver-volumes-volume-get-properties',
                                              rel=['hea-properties']),
                                       Action(name='heaserver-volumes-volume-get-open-choices',
                                              url='http://localhost:8080/volumes/{id}/opener',
                                              rel=['hea-opener-choices']),
                                       Action(name='heaserver-volumes-volume-duplicate',
                                              url='http://localhost:8080/volumes/{id}/duplicator',
                                              rel=['hea-duplicator'])],
                      expected_opener=expectedvalues.Link(
                          url=f'http://localhost:8080/volumes/{db_store[service.MONGODB_VOLUME_COLLECTION][0]["id"]}/content',
                          rel=['hea-opener', 'hea-default', 'application/x.folder']),
                      duplicate_action_name='heaserver-volumes-volume-duplicate-form',
                      put_content_status=405,
                      sub=TEST_USER)

FileSystemPermissionsTestCase = \
    get_test_case_cls(coll=service.MONGODB_FILE_SYSTEM_COLLECTION,
                      wstl_package=service.__package__,
                      href='http://localhost:8080/filesystems',
                      db_manager_cls=MockDockerMongoManager,
                      fixtures=db_store,
                      get_actions=[Action(name='heaserver-volumes-file-system-get-properties',
                                          rel=['hea-properties']),
                                   Action(name='heaserver-volumes-file-system-duplicate',
                                          url='http://localhost:8080/filesystems/{id}/duplicator',
                                          rel=['hea-duplicator'])
                                   ],
                      get_all_actions=[
                          Action(name='heaserver-volumes-file-system-get-properties',
                                 rel=['hea-properties']),
                          Action(name='heaserver-volumes-file-system-duplicate',
                                 url='http://localhost:8080/filesystems/{id}/duplicator',
                                 rel=['hea-duplicator'])],
                      duplicate_action_name='heaserver-volumes-file-system-duplicate-form',
                      put_content_status=404,
                      sub=TEST_USER)
