"""
Creates a test case class for use with the unittest library that is built into Python.
"""
from heaserver.service.testcase.microservicetestcase import get_test_case_cls_default
from heaserver.service.testcase.mockaws import MockS3WithMockMongoManager
from heaserver.folderawss3 import storageservice as service
from heaobject.user import NONE_USER, AWS_USER
from heaobject.data import AWSS3FileObject
from heaserver.service.testcase.expectedvalues import Action
import importlib.resources as pkg_resources
from . import files

MONGODB_STORAGE_COLLECTION = 'storage'

db_store = {
    MONGODB_STORAGE_COLLECTION: [{
        'id': 'STANDARD',
        'instance_id': 'heaobject.storage.AWSS3Storage^STANDARD',
        'created': '2022-05-17T00:00:00+00:00',
        'derived_by': None,
        'derived_from': [],
        'description': None,
        'display_name': 'STANDARD',
        'invites': [],
        'modified': '2022-05-17T00:00:00+00:00',
        'name': 'STANDARD',
        'owner': AWS_USER,
        'shares': [{
            'invite': None,
            'permissions': ['VIEWER'],
            'type': 'heaobject.root.ShareImpl',
            'user': 'system|none',
            'group': 'system|none',
            'type_display_name': 'Share',
            'basis': 'USER'
        }],
        'user_shares': [{
            'invite': None,
            'permissions': ['VIEWER'],
            'type': 'heaobject.root.ShareImpl',
            'user': 'system|none',
            'group': 'system|none',
            'type_display_name': 'Share',
            'basis': 'USER'
        }],
        'group_shares': [],
        'source': 'AWS S3',
        'source_detail': None,
        'type': 'heaobject.storage.AWSS3Storage',
        'object_count': 2,
        'object_earliest_created': '2022-05-17T00:00:00+00:00',
        'object_last_modified': '2022-05-17T00:00:00+00:00',
        'volume_id': '666f6f2d6261722d71757578',
        'mime_type': 'application/x.awss3storage',
        'storage_class': 'STANDARD',
        'archive_storage_class': False,
        'type_display_name': 'Storage Summary',
        'human_readable_size': '9.9 MB',
        'object_average_duration': 0.0,
        'object_average_size': 4963519.0,
        'object_max_duration': 0.0,
        'object_min_duration': 0.0,
        'size': 9927038,
        'human_readable_min_duration': 'a moment',
        'human_readable_max_duration': 'a moment',
        'human_readable_average_duration': 'a moment',
        'super_admin_default_permissions': [],
        'dynamic_permission_supported': False
    }],
    'buckets': [{
        'id': 'hci-foundation-1',
        'created': '2022-05-17T00:00:00+00:00',
        'derived_by': None,
        'derived_from': [],
        'description': None,
        'object_count': None,
        'size': None,
        'display_name': 'hci-foundation-1',
        'invites': [],
        'modified': None,
        'name': 'hci-foundation-1',
        'owner': NONE_USER,
        'shares': [],
        'user_shares': [],
        'group_shares': [],
        'source': 'AWS Simple Cloud Storage (S3)',
        'type': 'heaobject.bucket.AWSBucket',
        'version': None,
        'arn': None,
        'versioned': None,
        'encrypted': False,
        'region': 'us-west-1',
        'permission_policy': None,
        'tags': [],
        's3_uri': 's3://hci-foundation-1/',
        'presigned_url': None,
        'locked': False,
        'mime_type': 'application/x.awsbucket',
        'bucket_id': 'hci-foundation-1'
    }],
    'awss3files': [{
        'created': '2022-05-17T00:00:00+00:00',
        'derived_by': None,
        'derived_from': [],
        'description': None,
        'display_name': 'TextFileUTF8.txt',
        'id': 'VGV4dEZpbGVVVEY4LnR4dA==',
        'invites': [],
        'modified': '2022-05-17T00:00:00+00:00',
        'name': 'VGV4dEZpbGVVVEY4LnR4dA==',
        'owner': NONE_USER,
        'shares': [],
        'user_shares': [],
        'group_shares': [],
        'source': 'AWS Simple Cloud Storage (S3)',
        'storage_class': 'STANDARD',
        'type': AWSS3FileObject.get_type_name(),
        's3_uri': 's3://hci-foundation-1/TextFileUTF8.txt',
        'presigned_url': None,
        'version': None,
        'mime_type': 'text/plain',
        'size': 1253952,
        'human_readable_size': '1.3 MB',
        'bucket_id': 'hci-foundation-1',
        'key': 'TextFileUTF8.txt'
    },
    {
        'created': '2022-05-17T00:00:00+00:00',
        'derived_by': None,
        'derived_from': [],
        'description': None,
        'display_name': 'BinaryFile',
        'id': 'QmluYXJ5RmlsZQ==',
        'invites': [],
        'modified': '2022-05-17T00:00:00+00:00',
        'name': 'QmluYXJ5RmlsZQ==',
        'owner': NONE_USER,
        'shares': [],
        'user_shares': [],
        'group_shares': [],
        'source': 'AWS Simple Cloud Storage (S3)',
        'storage_class': 'STANDARD',
        'type': AWSS3FileObject.get_type_name(),
        's3_uri': 's3://hci-foundation-1/BinaryFile',
        'presigned_url': None,
        'version': None,
        'mime_type': 'application/octet-stream',
        'size': 8673160,
        'human_readable_size': '8.7 MB',
        'bucket_id': 'hci-foundation-1',
        'key': 'BinaryFile'
    }],
    'filesystems': [{
        'id': '666f6f2d6261722d71757578',
        'created': None,
        'derived_by': None,
        'derived_from': [],
        'description': None,
        'display_name': 'Amazon Web Services',
        'invited': [],
        'modified': None,
        'name': 'amazon_web_services',
        'owner': NONE_USER,
        'shares': [],
        'user_shares': [],
        'group_shares': [],
        'source': None,
        'type': 'heaobject.volume.AWSFileSystem',
        'version': None
    }],
    'volumes': [{
        'id': '666f6f2d6261722d71757578',
        'created': None,
        'derived_by': None,
        'derived_from': [],
        'description': None,
        'display_name': 'My Amazon Web Services',
        'invited': [],
        'modified': None,
        'name': 'amazon_web_services',
        'owner': NONE_USER,
        'shares': [],
        'user_shares': [],
        'group_shares': [],
        'source': None,
        'type': 'heaobject.volume.Volume',
        'version': None,
        'file_system_name': 'amazon_web_services',
        'credential_id': None  # Let boto3 try to find the user's credentials.
    }]}

content = {
    'awss3files': {
        'VGV4dEZpbGVVVEY4LnR4dA==': b'hci-foundation-1|' + pkg_resources.read_text(files, 'TextFileUTF8.txt').encode(
            'utf-8'),
        'QmluYXJ5RmlsZQ==': b'hci-foundation-1|' + pkg_resources.read_binary(files, 'BinaryFile')
    }
}

TestCase = get_test_case_cls_default(coll=MONGODB_STORAGE_COLLECTION,
                                     wstl_package=service.__package__,
                                     href='http://localhost:8080/volumes/666f6f2d6261722d71757578/awss3storage/',
                                     fixtures=db_store,
                                     content=content,
                                     db_manager_cls=MockS3WithMockMongoManager,
                                     get_all_actions=[Action(name='heaserver-storage-storage-get-properties',
                                                             rel=['hea-properties'])],
                                     duplicate_action_name=None,
                                     exclude=['body_put', 'body_post'])
