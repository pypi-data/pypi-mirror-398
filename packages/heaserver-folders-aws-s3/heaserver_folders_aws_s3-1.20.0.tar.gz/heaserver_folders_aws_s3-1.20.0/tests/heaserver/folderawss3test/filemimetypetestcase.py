from heaserver.service.testcase import microservicetestcase, expectedvalues
from heaserver.service.testcase.mockaws import MockS3WithMockMongoManager
from heaserver.folderawss3 import fileservice
from heaobject.data import AWSS3FileObject
import importlib.resources as pkg_resources
from heaobject import user
from . import files

db_values = {
    'volumes': [{
        'id': '666f6f2d6261722d71757578',
        'created': None,
        'derived_by': None,
        'derived_from': [],
        'description': None,
        'display_name': 'My Amazon Web Services',
        'invites': [],
        'modified': None,
        'name': 'amazon_web_services',
        'owner': user.NONE_USER,
        'shared_with': [],
        'source': None,
        'type': 'heaobject.volume.Volume',
        'version': None,
        'file_system_name': 'amazon_web_services',
        'file_system_type': 'heaobject.volume.AWSFileSystem',
        'credential_id': None  # Let boto3 try to find the user's credentials.
    }],
    'buckets': [{
        "arn": None,
        "created": '2022-05-17T00:00:00+00:00',
        "derived_by": None,
        "derived_from": [],
        "description": None,
        "display_name": "arp-scale-2-cloud-bucket-with-tags11",
        "encrypted": True,
        "id": "arp-scale-2-cloud-bucket-with-tags11",
        "invites": [],
        "locked": False,
        "mime_type": "application/x.awsbucket",
        "modified": '2022-05-17T00:00:00+00:00',
        "name": "arp-scale-2-cloud-bucket-with-tags11",
        "object_count": None,
        "owner": "system|none",
        "permission_policy": None,
        "region": "us-west-2",
        "s3_uri": "s3://arp-scale-2-cloud-bucket-with-tags11/",
        "presigned_url": None,
        "shares": [],
        "size": None,
        "source": None,
        "tags": [],
        "type": "heaobject.bucket.AWSBucket",
        "version": None,
        "versioned": False
    }],
    'awss3files': [{
        'created': '2022-05-17T00:00:00+00:00',
        'derived_by': None,
        'derived_from': [],
        'description': None,
        'display_name': 'testfile.fastq',
        'id': 'dGVzdGZpbGUuZmFzdHE=',
        'invites': [],
        'modified': '2022-05-17T00:00:00+00:00',
        'name': 'dGVzdGZpbGUuZmFzdHE=',
        'owner': user.AWS_USER,
        'shares': [{
            'invite': None,
            'permissions': ['COOWNER'],
            'type': 'heaobject.root.ShareImpl',
            'user': 'system|all'
        }],
        'source': 'AWS S3 (Standard)',
        'source_detail': 'AWS S3 (Standard)',
        'storage_class': 'STANDARD',
        'type': AWSS3FileObject.get_type_name(),
        'bucket_id': 'arp-scale-2-cloud-bucket-with-tags11',
        's3_uri': 's3://arp-scale-2-cloud-bucket-with-tags11/testfile.fastq',
        'presigned_url': None,
        'version': None,
        'size': 136,
        'human_readable_size': '136 Bytes'
    },
        {
            'created': '2022-05-17T00:00:00+00:00',
            'derived_by': None,
            'derived_from': [],
            'description': None,
            'display_name': 'testfile.ffn',
            'id': 'dGVzdGZpbGUuZmZu',
            'invites': [],
            'modified': '2022-05-17T00:00:00+00:00',
            'name': 'dGVzdGZpbGUuZmZu',
            'owner': user.AWS_USER,
            'shares': [{
                'invite': None,
                'permissions': ['COOWNER'],
                'type': 'heaobject.root.ShareImpl',
                'user': 'system|all'
            }],
            'source': 'AWS S3 (Standard)',
            'source_detail': 'AWS S3 (Standard)',
            'storage_class': 'STANDARD',
            'type': AWSS3FileObject.get_type_name(),
            'bucket_id': 'arp-scale-2-cloud-bucket-with-tags11',
            's3_uri': 's3://arp-scale-2-cloud-bucket-with-tags11/testfile.ffn',
            'presigned_url': None,
            'version': None,
            'size': 361,
            'human_readable_size': '361 Bytes'
        },
        {
            'created': '2022-05-17T00:00:00+00:00',
            'derived_by': None,
            'derived_from': [],
            'description': None,
            'display_name': 'testfile.bam.bai',
            'id': 'dGVzdGZpbGUuYmFtLmJhaQ==',
            'invites': [],
            'modified': '2022-05-17T00:00:00+00:00',
            'name': 'dGVzdGZpbGUuYmFtLmJhaQ==',
            'owner': user.AWS_USER,
            'shares': [{
                'invite': None,
                'permissions': ['COOWNER'],
                'type': 'heaobject.root.ShareImpl',
                'user': 'system|all'
            }],
            'source': 'AWS S3 (Standard)',
            'source_detail': 'AWS S3 (Standard)',
            'storage_class': 'STANDARD',
            'type': AWSS3FileObject.get_type_name(),
            'bucket_id': 'arp-scale-2-cloud-bucket-with-tags11',
            's3_uri': 's3://arp-scale-2-cloud-bucket-with-tags11/testfile.bam.bai',
            'presigned_url': None,
            'version': None,
            'size': 0,
            'human_readable_size': '0 Bytes'
        },
        {
            'created': '2022-05-17T00:00:00+00:00',
            'derived_by': None,
            'derived_from': [],
            'description': None,
            'display_name': 'nofileextension',
            'id': 'bm9maWxlZXh0ZW5zaW9u',
            'invites': [],
            'modified': '2022-05-17T00:00:00+00:00',
            'name': 'bm9maWxlZXh0ZW5zaW9u',
            'owner': user.AWS_USER,
            'shares': [{
                'invite': None,
                'permissions': ['COOWNER'],
                'type': 'heaobject.root.ShareImpl',
                'user': 'system|all'
            }],
            'source': 'AWS S3 (Standard)',
            'source_detail': 'AWS S3 (Standard)',
            'storage_class': 'STANDARD',
            'type': AWSS3FileObject.get_type_name(),
            'bucket_id': 'arp-scale-2-cloud-bucket-with-tags11',
            's3_uri': 's3://arp-scale-2-cloud-bucket-with-tags11/nofileextension',
            'presigned_url': None,
            'version': None,
            'size': 41,
            'human_readable_size': '41 Bytes'
        },
    ]
}

content = {
    'awss3files': {
        'dGVzdGZpbGUuZmFzdHE=': b'arp-scale-2-cloud-bucket-with-tags11|' + pkg_resources.read_binary(files, 'testfile.fastq'),
        'dGVzdGZpbGUuZmZu': b'arp-scale-2-cloud-bucket-with-tags11|' + pkg_resources.read_binary(files, 'testfile.ffn'),
        'dGVzdGZpbGUuYmFtLmJhaQ==': b'arp-scale-2-cloud-bucket-with-tags11|' + pkg_resources.read_binary(files, 'testfile.bam.bai'),
        'bm9maWxlZXh0ZW5zaW9u': b'arp-scale-2-cloud-bucket-with-tags11|' + pkg_resources.read_binary(files, 'nofileextension')
    }
}


AWSS3FileContentTypeTestCase = \
    microservicetestcase.get_test_case_cls_default(
        href='http://localhost:8080/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3files/',
        wstl_package=fileservice.__package__,
        coll='awss3files',
        fixtures=db_values,
        content=content,
        db_manager_cls=MockS3WithMockMongoManager,
        get_all_actions=[
            expectedvalues.Action(
                name='heaserver-awss3files-file-get-properties',
                rel=['hea-properties']),
            expectedvalues.Action(
                name='heaserver-awss3files-file-get-open-choices',
                url='http://localhost:8080/volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id}/opener',
                rel=['hea-opener-choices']),
            expectedvalues.Action(
                name='heaserver-awss3files-file-duplicate',
                url='http://localhost:8080/volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id}/duplicator',
                rel=['hea-duplicator']),
            expectedvalues.Action(
                name='heaserver-awss3files-file-get-self',
                url='http://localhost:8080/volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id}',
                rel=['self']),
            expectedvalues.Action(
                name='heaserver-awss3files-file-get-trash',
                url='http://localhost:8080/volumes/666f6f2d6261722d71757578/awss3trash',
                wstl_url='http://localhost:8080/volumes/{volume_id}/awss3trash',
                rel=['hea-trash', 'hea-context-menu'])],
        get_actions=[
            expectedvalues.Action(
                name='heaserver-awss3files-file-get-properties',
                rel=['hea-properties']),
            expectedvalues.Action(
                name='heaserver-awss3files-file-get-open-choices',
                url='http://localhost:8080/volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id}/opener',
                rel=['hea-opener-choices']),
            expectedvalues.Action(
                name='heaserver-awss3files-file-duplicate',
                url='http://localhost:8080/volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id}/duplicator',
                rel=['hea-duplicator']),
            expectedvalues.Action(
                name='heaserver-awss3files-file-get-self',
                url='http://localhost:8080/volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id}',
                rel=['self']),
            expectedvalues.Action(
                name='heaserver-awss3files-file-get-volume',
                url='http://localhost:8080/volumes/{volume_id}',
                rel=['hea-volume']),
            expectedvalues.Action(
                name='heaserver-awss3files-file-get-trash',
                url='http://localhost:8080/volumes/{volume_id}/awss3trash',
                rel=['hea-trash', 'hea-context-menu'])],
        duplicate_action_name='heaserver-awss3files-file-duplicate-form',
        put_content_status=204,
        exclude=['body_post', 'body_put']
    )
