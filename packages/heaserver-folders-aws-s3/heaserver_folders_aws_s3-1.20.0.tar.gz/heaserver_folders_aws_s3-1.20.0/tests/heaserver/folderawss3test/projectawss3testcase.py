"""
Runs integration tests for the HEA folder service.

Note that each test opens an aiohttp server listening on port 8080.
"""

from heaserver.service.testcase import expectedvalues, microservicetestcase
from heaserver.folderawss3 import service
from heaserver.service.testcase.mockaws import MockS3WithMockMongoManager
from heaobject import user
from heaobject.project import AWSS3Project
from heaobject.root import DesktopObjectDict, DesktopObject
from base64 import b64encode
from collections.abc import Callable, Iterable
import boto3


class MyManager(MockS3WithMockMongoManager):

    @classmethod
    def get_desktop_object_inserters(cls) -> dict[str, Callable[[list[DesktopObjectDict]], None]]:
        d = super().get_desktop_object_inserters()
        def project_inserter(objs: Iterable[DesktopObject]):
            client = boto3.client('s3')
            for obj in objs:
                awss3file = AWSS3Project()
                awss3file.from_dict(obj)
                client.put_object(Bucket=awss3file.bucket_id, Key=awss3file.key)
        d['awss3projects'] = project_inserter
        return d


db_values = {'awss3projects_items': [
    {
        'created': None,
        'derived_by': None,
        'derived_from': [],
        'description': None,
        'display_name': 'TestProject',
        'id': 'VGVzdFByb2plY3Qv',
        'instance_id': 'heaobject.folder.AWSS3ItemInFolder^VGVzdFByb2plY3Qv',
        'invites': [],
        'modified': None,
        'mime_type': 'application/octet-stream',
        'name': 'VGVzdFByb2plY3Qv',
        'owner': user.AWS_USER,
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
        'source_detail': 'AWS S3',
        'type': 'heaobject.folder.AWSS3ItemInFolder',
        'actual_object_type_name': 'heaobject.project.AWSS3Project',
        'actual_object_id': 'VGVzdFByb2plY3Qv',
        'actual_object_uri': 'volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3projects/VGVzdFByb2plY3Qv',
        's3_uri': 's3://arp-scale-2-cloud-bucket-with-tags11/TestProject/',
        'storage_class': None,
        'size': None,
        'human_readable_size': None,
        'volume_id': '666f6f2d6261722d71757578',
        'folder_id': 'root',
        'bucket_id': 'arp-scale-2-cloud-bucket-with-tags11',
        'key': 'TestProject/',
        'path': '/arp-scale-2-cloud-bucket-with-tags11/TestProject/',
        'type_display_name': 'Project',
        'retrievable': None,
        'human_readable_archive_detail_state': 'Undefined',
        'archive_detail_state': None,
        'archive_storage_class': None,
        'available_until': None,
        'super_admin_default_permissions': [],
        'dynamic_permission_supported': False
    },
    {
        'created': None,
        'derived_by': None,
        'derived_from': [],
        'description': None,
        'display_name': 'TestProject2',
        'id': 'VGVzdFByb2plY3QyLw==',
        'instance_id': 'heaobject.folder.AWSS3ItemInFolder^VGVzdFByb2plY3QyLw==',
        'invites': [],
        'modified': None,
        'name': 'VGVzdFByb2plY3QyLw==',
        'owner': user.AWS_USER,
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
        'source_detail': 'AWS S3',
        'type': 'heaobject.folder.AWSS3ItemInFolder',
        'actual_object_type_name': 'heaobject.project.AWSS3Project',
        'actual_object_id': 'VGVzdFByb2plY3QyLw==',
        'actual_object_uri': 'volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3projects/VGVzdFByb2plY3QyLw==',
        's3_uri': 's3://arp-scale-2-cloud-bucket-with-tags11/TestProject2/',
        'storage_class': None,
        'size': None,
        'human_readable_size': None,
        'volume_id': '666f6f2d6261722d71757578',
        'folder_id': 'root',
        'bucket_id': 'arp-scale-2-cloud-bucket-with-tags11',
        'key': 'TestProject2/',
        'path': '/arp-scale-2-cloud-bucket-with-tags11/TestProject2/',
        'mime_type': 'application/octet-stream',
        'type_display_name': 'Project',
        'retrievable': None,
        'human_readable_archive_detail_state': 'Undefined',
        'archive_detail_state': None,
        'archive_storage_class': None,
        'available_until': None,
        'super_admin_default_permissions': [],
        'dynamic_permission_supported': False
    }
],
    'components': [
        {
            'id': '666f6f2d6261722d71757578',
            'created': None,
            'derived_by': None,
            'derived_from': [],
            'description': None,
            'display_name': 'Reximus',
            'invited': [],
            'modified': None,
            'name': 'reximus',
            'owner': user.NONE_USER,
            'shares': [],
            'user_shares': [],
            'group_shares': [],
            'source': None,
            'type': 'heaobject.registry.Component',
            'base_url': 'http://localhost:8080',
            'resources': [{'type': 'heaobject.registry.Resource', 'resource_type_name': 'heaobject.folder.AWSS3Folder',
                           'base_path': 'volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3folders'},
                          {'type': 'heaobject.registry.Resource', 'resource_type_name': 'heaobject.project.AWSS3Project',
                           'base_path': 'volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3projects'},
                          {'type': 'heaobject.registry.Resource', 'resource_type_name': 'heaobject.folder.AWSS3ItemInFolder',
                           'base_path': 'items'}]
        }
    ],
    'filesystems': [{
        'id': '666f6f2d6261722d71757578',
        'created': None,
        'derived_by': None,
        'derived_from': [],
        'description': None,
        'display_name': 'Amazon Web Services',
        'invited': [],
        'modified': None,
        'name': 'DEFAULT_FILE_SYSTEM',
        'owner': user.NONE_USER,
        'shares': [],
        'user_shares': [],
        'group_shares': [],
        'source': None,
        'type': 'heaobject.volume.AWSFileSystem'
    },
    {
        'id': '666f6f2d6261722d71757577',
        'created': None,
        'derived_by': None,
        'derived_from': [],
        'description': None,
        'display_name': 'My MongoDB',
        'invited': [],
        'modified': None,
        'name': 'DEFAULT_FILE_SYSTEM',
        'owner': user.NONE_USER,
        'shares': [],
        'user_shares': [],
        'group_shares': [],
        'source': None,
        'type': 'heaobject.volume.MongoDBFileSystem'
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
        'owner': user.NONE_USER,
        'shares': [],
        'user_shares': [],
        'group_shares': [],
        'source': None,
        'type': 'heaobject.volume.Volume',
        'file_system_name': 'DEFAULT_FILE_SYSTEM',
        'file_system_type': 'heaobject.volume.AWSFileSystem',
        'credential_id': None  # Let boto3 try to find the user's credentials.
    },
    {
        'id': '666f6f2d6261722d71757577',
        'created': None,
        'derived_by': None,
        'derived_from': [],
        'description': None,
        'display_name': 'My MongoDB',
        'invited': [],
        'modified': None,
        'name': 'amazon_web_services',
        'owner': user.NONE_USER,
        'shares': [],
        'user_shares': [],
        'group_shares': [],
        'source': None,
        'type': 'heaobject.volume.Volume',
        'file_system_name': 'DEFAULT_FILE_SYSTEM',
        'file_system_type': 'heaobject.volume.MongoDBFileSystem',
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
        'shares': [],
        'user_shares': [],
        'group_shares': [],
        "size": None,
        "source": None,
        "tags": [],
        "type": "heaobject.bucket.AWSBucket",
        "versioned": False
    }],
    'awsaccounts': [
        {
            'email_address': 'no-reply@example.com',
            'alternate_contact_name': None,
            "alternate_email_address": None,
            "alternate_phone_number": None,
            "created": '2022-05-17T00:00:00+00:00',
            "derived_by": None,
            "derived_from": [],
            "description": None,
            "display_name": "311813441058",
            "full_name": None,
            "id": "311813441058",
            "invites": [],
            "mime_type": "application/x.awsaccount",
            "modified": '2022-05-17T00:00:00+00:00',
            "name": "311813441058",
            "owner": "system|none",
            "phone_number": None,
            'shares': [],
            'user_shares': [],
            'group_shares': [],
            "source": None,
            "type": "heaobject.account.AWSAccount"
        }
    ],
    'awss3foldersmetadata': [{
        'id': '1',
        'encoded_key': 'VGVzdFByb2plY3Qv',
        'bucket_id': 'arp-scale-2-cloud-bucket-with-tags11',
        'actual_object_type_name': AWSS3Project.get_type_name(),
        #'parent_encoded_key': folder_id
    },
    {
        'id': '2',
        'encoded_key': 'VGVzdFByb2plY3QyLw==',
        'bucket_id': 'arp-scale-2-cloud-bucket-with-tags11',
        'actual_object_type_name': AWSS3Project.get_type_name(),
        #'parent_encoded_key': folder_id
    }],
    'awss3projects': [{
        'created': None,
        'derived_by': None,
        'derived_from': [],
        'description': None,
        'display_name': 'TestProject',
        'id': 'VGVzdFByb2plY3Qv',
        'instance_id': 'heaobject.project.AWSS3Project^VGVzdFByb2plY3Qv',
        'invites': [],
        'modified': None,
        'name': 'VGVzdFByb2plY3Qv',
        'owner': user.AWS_USER,
        'shares': [{
            'invite': None,
            'permissions': ['COOWNER'],
            'type': 'heaobject.root.ShareImpl',
            'user': 'system|none',
            'group': 'system|none',
            'type_display_name': 'Share',
            'basis': 'USER'
        }],
        'user_shares': [{
            'invite': None,
            'permissions': ['COOWNER'],
            'type': 'heaobject.root.ShareImpl',
            'user': 'system|none',
            'group': 'system|none',
            'type_display_name': 'Share',
            'basis': 'USER'
        }],
        'group_shares': [],
        'source': 'AWS S3',
        'source_detail': 'AWS S3',
        'type': 'heaobject.project.AWSS3Project',
        'mime_type': 'application/x.project',
        's3_uri': 's3://arp-scale-2-cloud-bucket-with-tags11/TestProject/',
        'bucket_id': 'arp-scale-2-cloud-bucket-with-tags11',
        'key': 'TestProject/',
        'type_display_name': 'Project',
        'resource_type_and_id': 'arp-scale-2-cloud-bucket-with-tags11/TestProject/',
        'super_admin_default_permissions': [],
        'dynamic_permission_supported': False
    },
        {
            'created': None,
            'derived_by': None,
            'derived_from': [],
            'description': None,
            'display_name': 'TestProject2',
            'id': 'VGVzdFByb2plY3QyLw==',
            'instance_id': 'heaobject.project.AWSS3Project^VGVzdFByb2plY3QyLw==',
            'invites': [],
            'modified': None,
            'name': 'VGVzdFByb2plY3QyLw==',
            'owner': user.AWS_USER,
            'shares': [{
                'invite': None,
                'permissions': ['COOWNER'],
                'type': 'heaobject.root.ShareImpl',
                'user': 'system|none',
                'group': 'system|none',
                'type_display_name': 'Share',
                'basis': 'USER'
            }],
            'user_shares': [{
                'invite': None,
                'permissions': ['COOWNER'],
                'type': 'heaobject.root.ShareImpl',
                'user': 'system|none',
                'group': 'system|none',
                'type_display_name': 'Share',
                'basis': 'USER'
            }],
            'group_shares': [],
            'source': 'AWS S3',
            'source_detail': 'AWS S3',
            'type': 'heaobject.project.AWSS3Project',
            'mime_type': 'application/x.project',
            's3_uri': 's3://arp-scale-2-cloud-bucket-with-tags11/TestProject2/',
            'bucket_id': 'arp-scale-2-cloud-bucket-with-tags11',
            'key': 'TestProject2/',
            'type_display_name': 'Project',
            'resource_type_and_id': 'arp-scale-2-cloud-bucket-with-tags11/TestProject2/',
            'super_admin_default_permissions': [],
            'dynamic_permission_supported': False
        }
    ]

}

content_ = [{'collection': {'version': '1.0', 'href': 'http://localhost:8080/folders/root/items/', 'items': [{'data': [
    {'name': 'created', 'value': None, 'prompt': 'created', 'display': True},
    {'name': 'derived_by', 'value': None, 'prompt': 'derived_by', 'display': True},
    {'name': 'derived_from', 'value': [], 'prompt': 'derived_from', 'display': True},
    {'name': 'description', 'value': None, 'prompt': 'description', 'display': True},
    {'name': 'display_name', 'value': 'Reximus', 'prompt': 'display_name', 'display': True},
    {'name': 'id', 'value': '666f6f2d6261722d71757578', 'prompt': 'id', 'display': False},
    {'name': 'invites', 'value': [], 'prompt': 'invites', 'display': True},
    {'name': 'modified', 'value': None, 'prompt': 'modified', 'display': True},
    {'name': 'name', 'value': 'reximus', 'prompt': 'name', 'display': True},
    {'name': 'owner', 'value': 'system|none', 'prompt': 'owner', 'display': True},
    {'name': 'shares', 'value': [], 'prompt': 'shares', 'display': True},
    {'name': 'source', 'value': None, 'prompt': 'source', 'display': True},
    {'name': 'version', 'value': None, 'prompt': 'version', 'display': True},
    {'name': 'actual_object_type_name', 'value': 'heaobject.folder.Folder', 'prompt': 'actual_object_type_name',
     'display': True},
    {'name': 'actual_object_id', 'value': '666f6f2d6261722d71757579', 'prompt': 'actual_object_id', 'display': True},
    {'name': 'folder_id', 'value': 'root', 'prompt': 'folder_id', 'display': True},
    {'name': 'bucket_id', 'value': 'arp-scale-2-cloud-bucket-with-tags11', 'prompt': 'bucket_id', 'display': True},
    {'name': 'key', 'value': 'Reximus/', 'prompt': 'key', 'display': True},
    {'section': 'actual_object', 'name': 'created', 'value': None, 'prompt': 'created', 'display': True},
    {'section': 'actual_object', 'name': 'derived_by', 'value': None, 'prompt': 'derived_by', 'display': True},
    {'section': 'actual_object', 'name': 'derived_from', 'value': [], 'prompt': 'derived_from', 'display': True},
    {'section': 'actual_object', 'name': 'description', 'value': None, 'prompt': 'description', 'display': True},
    {'section': 'actual_object', 'name': 'display_name', 'value': 'Reximus', 'prompt': 'display_name', 'display': True},
    {'section': 'actual_object', 'name': 'id', 'value': '666f6f2d6261722d71757579', 'prompt': 'id', 'display': False},
    {'section': 'actual_object', 'name': 'invites', 'value': [], 'prompt': 'invites', 'display': True},
    {'section': 'actual_object', 'name': 'modified', 'value': None, 'prompt': 'modified', 'display': True},
    {'section': 'actual_object', 'name': 'name', 'value': 'reximus', 'prompt': 'name', 'display': True},
    {'section': 'actual_object', 'name': 'owner', 'value': 'system|none', 'prompt': 'owner', 'display': True},
    {'section': 'actual_object', 'name': 'shares', 'value': [], 'prompt': 'shares', 'display': True},
    {'section': 'actual_object', 'name': 'source', 'value': None, 'prompt': 'source', 'display': True},
    {'section': 'actual_object', 'name': 'version', 'value': None, 'prompt': 'version', 'display': True}], 'links': [{'prompt': 'Move', 'rel': 'mover',
                                   'href': 'http://localhost:8080/folders/root/items/666f6f2d6261722d71757578/mover'},
                                  {'prompt': 'Open', 'rel': 'hea-opener-choices',
                                   'href': 'http://localhost:8080/folders/root/items/666f6f2d6261722d71757578/opener'},
                                  {'prompt': 'Duplicate', 'rel': 'duplicator',
                                   'href': 'http://localhost:8080/folders/root/items/666f6f2d6261722d71757578/duplicator'}]}],
                            'template': {'prompt': 'Properties', 'rel': 'properties', 'data': [
                                {'name': 'id', 'value': '666f6f2d6261722d71757578', 'prompt': 'Id', 'required': True,
                                 'readOnly': True, 'pattern': ''},
                                {'name': 'source', 'value': None, 'prompt': 'Source', 'required': False,
                                 'readOnly': False, 'pattern': ''},
                                {'name': 'version', 'value': None, 'prompt': 'Version', 'required': False,
                                 'readOnly': False, 'pattern': ''},
                                {'name': 'display_name', 'value': 'Reximus', 'prompt': 'Name', 'required': True,
                                 'readOnly': False, 'pattern': ''},
                                {'name': 'description', 'value': None, 'prompt': 'Description', 'required': False,
                                 'readOnly': False, 'pattern': ''},
                                {'name': 'owner', 'value': 'system|none', 'prompt': 'Owner', 'required': False,
                                 'readOnly': False, 'pattern': ''},
                                {'name': 'created', 'value': None, 'prompt': 'Created', 'required': False,
                                 'readOnly': True, 'pattern': ''},
                                {'name': 'modified', 'value': None, 'prompt': 'Modified', 'required': False,
                                 'readOnly': True, 'pattern': ''},
                                {'name': 'invites', 'value': [], 'prompt': 'Share invites', 'required': False,
                                 'readOnly': True, 'pattern': ''},
                                {'name': 'shares', 'value': [], 'prompt': 'Shared with', 'required': False,
                                 'readOnly': False, 'pattern': ''},
                                {'name': 'derived_by', 'value': None, 'prompt': 'Derived by', 'required': False,
                                 'readOnly': True, 'pattern': ''},
                                {'name': 'derived_from', 'value': [], 'prompt': 'Derived from', 'required': False,
                                 'readOnly': True, 'pattern': ''},
                                {'name': 'items', 'value': None, 'prompt': 'Items', 'required': False, 'readOnly': True,
                                 'pattern': ''}]}}}, {
                'collection': {'version': '1.0', 'href': 'http://localhost:8080/folders/root/items/', 'items': [{
                    'data': [
                        {
                            'name': 'created',
                            'value': None,
                            'prompt': 'created',
                            'display': True},
                        {
                            'name': 'derived_by',
                            'value': None,
                            'prompt': 'derived_by',
                            'display': True},
                        {
                            'name': 'derived_from',
                            'value': [],
                            'prompt': 'derived_from',
                            'display': True},
                        {
                            'name': 'description',
                            'value': None,
                            'prompt': 'description',
                            'display': True},
                        {
                            'name': 'display_name',
                            'value': 'Reximus',
                            'prompt': 'display_name',
                            'display': True},
                        {
                            'name': 'id',
                            'value': '0123456789ab0123456789ab',
                            'prompt': 'id',
                            'display': False},
                        {
                            'name': 'invites',
                            'value': [],
                            'prompt': 'invites',
                            'display': True},
                        {
                            'name': 'modified',
                            'value': None,
                            'prompt': 'modified',
                            'display': True},
                        {
                            'name': 'name',
                            'value': 'reximus',
                            'prompt': 'name',
                            'display': True},
                        {
                            'name': 'owner',
                            'value': 'system|none',
                            'prompt': 'owner',
                            'display': True},
                        {
                            'name': 'shares',
                            'value': [],
                            'prompt': 'shares',
                            'display': True},
                        {
                            'name': 'source',
                            'value': None,
                            'prompt': 'source',
                            'display': True},
                        {
                            'name': 'version',
                            'value': None,
                            'prompt': 'version',
                            'display': True},
                        {
                            'name': 'actual_object_type_name',
                            'value': 'heaobject.folder.Folder',
                            'prompt': 'actual_object_type_name',
                            'display': True},
                        {
                            'name': 'actual_object_id',
                            'value': '0123456789ab0123456789ac',
                            'prompt': 'actual_object_id',
                            'display': True},
                        {
                            'name': 'folder_id',
                            'value': 'root',
                            'prompt': 'folder_id',
                            'display': True},
                        {
                            'section': 'actual_object',
                            'name': 'created',
                            'value': None,
                            'prompt': 'created',
                            'display': True},
                        {
                            'section': 'actual_object',
                            'name': 'derived_by',
                            'value': None,
                            'prompt': 'derived_by',
                            'display': True},
                        {
                            'section': 'actual_object',
                            'name': 'derived_from',
                            'value': [],
                            'prompt': 'derived_from',
                            'display': True},
                        {
                            'section': 'actual_object',
                            'name': 'description',
                            'value': None,
                            'prompt': 'description',
                            'display': True},
                        {
                            'section': 'actual_object',
                            'name': 'display_name',
                            'value': 'Reximus',
                            'prompt': 'display_name',
                            'display': True},
                        {
                            'section': 'actual_object',
                            'name': 'id',
                            'value': '0123456789ab0123456789ac',
                            'prompt': 'id',
                            'display': False},
                        {
                            'section': 'actual_object',
                            'name': 'invites',
                            'value': [],
                            'prompt': 'invites',
                            'display': True},
                        {
                            'section': 'actual_object',
                            'name': 'modified',
                            'value': None,
                            'prompt': 'modified',
                            'display': True},
                        {
                            'section': 'actual_object',
                            'name': 'name',
                            'value': 'reximus',
                            'prompt': 'name',
                            'display': True},
                        {
                            'section': 'actual_object',
                            'name': 'owner',
                            'value': 'system|none',
                            'prompt': 'owner',
                            'display': True},
                        {
                            'section': 'actual_object',
                            'name': 'shares',
                            'value': [],
                            'prompt': 'shares',
                            'display': True},
                        {
                            'section': 'actual_object',
                            'name': 'source',
                            'value': None,
                            'prompt': 'source',
                            'display': True},
                        {
                            'section': 'actual_object',
                            'name': 'version',
                            'value': None,
                            'prompt': 'version',
                            'display': True},
                        {'name': 'bucket_id', 'value': 'arp-scale-2-cloud-bucket-with-tags11', 'prompt': 'bucket_id',
                         'display': True},
                        {'name': 'key', 'value': 'Reximus/', 'prompt': 'key', 'display': True}
                    ],
                    'links': [
                        {
                            'prompt': 'Move',
                            'rel': 'mover',
                            'href': 'http://localhost:8080/folders/root/items/0123456789ab0123456789ab/mover'},
                        {
                            'prompt': 'Open',
                            'rel': 'hea-opener-choices',
                            'href': 'http://localhost:8080/folders/root/items/0123456789ab0123456789ab/opener'},
                        {
                            'prompt': 'Duplicate',
                            'rel': 'duplicator',
                            'href': 'http://localhost:8080/folders/root/items/0123456789ab0123456789ab/duplicator'}]}],
                               'template': {'prompt': 'Properties', 'rel': 'properties', 'data': [
                                   {'name': 'id', 'value': '0123456789ab0123456789ab', 'prompt': 'Id', 'required': True,
                                    'readOnly': True, 'pattern': ''},
                                   {'name': 'source', 'value': None, 'prompt': 'Source', 'required': False,
                                    'readOnly': False, 'pattern': ''},
                                   {'name': 'version', 'value': None, 'prompt': 'Version', 'required': False,
                                    'readOnly': False, 'pattern': ''},
                                   {'name': 'display_name', 'value': 'Reximus', 'prompt': 'Name', 'required': True,
                                    'readOnly': False, 'pattern': ''},
                                   {'name': 'description', 'value': None, 'prompt': 'Description', 'required': False,
                                    'readOnly': False, 'pattern': ''},
                                   {'name': 'owner', 'value': 'system|none', 'prompt': 'Owner', 'required': False,
                                    'readOnly': False, 'pattern': ''},
                                   {'name': 'created', 'value': None, 'prompt': 'Created', 'required': False,
                                    'readOnly': True, 'pattern': ''},
                                   {'name': 'modified', 'value': None, 'prompt': 'Modified', 'required': False,
                                    'readOnly': True, 'pattern': ''},
                                   {'name': 'invites', 'value': [], 'prompt': 'Share invites', 'required': False,
                                    'readOnly': True, 'pattern': ''},
                                   {'name': 'shares', 'value': [], 'prompt': 'Shared with', 'required': False,
                                    'readOnly': False, 'pattern': ''},
                                   {'name': 'derived_by', 'value': None, 'prompt': 'Derived by', 'required': False,
                                    'readOnly': True, 'pattern': ''},
                                   {'name': 'derived_from', 'value': [], 'prompt': 'Derived from', 'required': False,
                                    'readOnly': True, 'pattern': ''},
                                   {'name': 'items', 'value': None, 'prompt': 'Items', 'required': False,
                                    'readOnly': True, 'pattern': ''}]}}}]

content = {
    'awss3folders': {
        '666f6f2d6261722d71757579': content_
    }
}

class AWSS3ProjectTestCase(microservicetestcase.get_test_case_cls_default(
        href='http://localhost:8080/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3projects/',
        wstl_package=service.__package__,
        coll='awss3projects',
        fixtures=db_values,
        db_manager_cls=MyManager,
        get_all_actions=[
            expectedvalues.Action(
                name='heaserver-awss3folders-project-get-open-choices',
                url='http://localhost:8080/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/opener',
                rel=['hea-opener-choices', 'hea-context-menu', 'hea-downloader']),
            expectedvalues.Action(
                name='heaserver-awss3folders-project-duplicate',
                url='http://localhost:8080/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/duplicatorasync',
                rel=['hea-dynamic-standard', 'hea-icon-duplicator', 'hea-context-menu']),
            expectedvalues.Action(
                name='heaserver-awss3folders-project-move',
                url='http://localhost:8080/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/moverasync',
                rel=['hea-dynamic-standard', 'hea-icon-mover', 'hea-context-menu']),
            expectedvalues.Action(
                name='heaserver-awss3folders-project-get-properties',
                rel=['hea-properties', 'hea-context-menu']),
            expectedvalues.Action(
                name='heaserver-awss3folders-project-archive',
                url='http://localhost:8080/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/archiveasync',
                rel=['hea-dynamic-standard', 'hea-archive', 'hea-context-menu']
            ),
            expectedvalues.Action(
                name='heaserver-awss3folders-project-unarchive',
                url='http://localhost:8080/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/unarchive',
                rel=['hea-dynamic-standard', 'hea-unarchive', 'hea-context-menu']
            ),
             expectedvalues.Action(
                name='heaserver-awss3folders-item-upload',
                url='http://localhost:8080/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/uploader',
                rel=['hea-uploader']
            ),
            expectedvalues.Action(name='heaserver-awss3folders-project-get-self',
                url='http://localhost:8080/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}',
                rel=['self', 'hea-self-container']),
            expectedvalues.Action(
                name='heaserver-awss3folders-project-get-create-choices',
                url='http://localhost:8080/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/creator',
                rel=['hea-creator-choices', 'hea-context-menu']),
            expectedvalues.Action(
                name='heaserver-awss3folders-project-get-trash',
                url='http://localhost:8080/volumes/666f6f2d6261722d71757578/awss3trash',
                wstl_url='http://localhost:8080/volumes/{volume_id}/awss3trash',
                rel=['hea-trash', 'hea-context-menu']),
            expectedvalues.Action(
                name='heaserver-awss3folders-project-get-presigned-url',
                url='http://localhost:8080/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/presignedurl',
                rel=['hea-dynamic-clipboard', 'hea-context-menu', 'hea-icon-for-clipboard']),
            expectedvalues.Action(
                name='heaserver-awss3folders-project-get-component',
                url='http://localhost:8080/components/bytype/heaobject.project.AWSS3Project',
                rel=['hea-component']),
            expectedvalues.Action(
                name='heaserver-awss3folders-get-delete-preflight-url',
                rel=['hea-delete-preflight'],
                url='http://localhost:8080/preflights/awss3objects/delete')
        ],
        duplicate_action_actions=[
            expectedvalues.Action(name='heaserver-awss3folders-project-get-self',
                url='http://localhost:8080/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}',
                rel=['self', 'hea-self-container'])
        ],
        get_actions=[
            expectedvalues.Action(
                name='heaserver-awss3folders-project-get-open-choices',
                url='http://localhost:8080/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/opener',
                rel=['hea-opener-choices', 'hea-context-menu', 'hea-downloader']),
            expectedvalues.Action(
                name='heaserver-awss3folders-project-get-properties',
                rel=['hea-properties', 'hea-context-menu']),
            expectedvalues.Action(
                name='heaserver-awss3folders-project-duplicate',
                url='http://localhost:8080/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/duplicatorasync',
                rel=['hea-dynamic-standard', 'hea-icon-duplicator', 'hea-context-menu']),
            expectedvalues.Action(
                name='heaserver-awss3folders-project-move',
                url='http://localhost:8080/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/moverasync',
                rel=['hea-dynamic-standard', 'hea-icon-mover', 'hea-context-menu']),
            expectedvalues.Action(
                name='heaserver-awss3folders-project-archive',
                url='http://localhost:8080/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/archiveasync',
                rel=['hea-dynamic-standard', 'hea-archive', 'hea-context-menu']
            ),
            expectedvalues.Action(
                name='heaserver-awss3folders-project-unarchive',
                url='http://localhost:8080/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/unarchive',
                rel=['hea-dynamic-standard', 'hea-unarchive', 'hea-context-menu']
            ),
            expectedvalues.Action(
                name='heaserver-awss3folders-item-upload',
                url='http://localhost:8080/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/uploader',
                rel=['hea-uploader']
            ),
            expectedvalues.Action(name='heaserver-awss3folders-project-get-self',
                url='http://localhost:8080/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}',
                rel=['self', 'hea-self-container']),
            expectedvalues.Action(name='heaserver-awss3folders-project-get-volume',
                url='http://localhost:8080/volumes/{volume_id}',
                rel=['hea-volume']),
            expectedvalues.Action(name='heaserver-awss3folders-project-get-awsaccount',
                                  url='http://localhost:8080/volumes/{volume_id}/awsaccounts/me',
                                  rel=['hea-account']),
            expectedvalues.Action(
                name='heaserver-awss3folders-project-get-create-choices',
                url='http://localhost:8080/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/creator',
                rel=['hea-creator-choices', 'hea-context-menu']),
            expectedvalues.Action(
                name='heaserver-awss3folders-project-get-trash',
                url='http://localhost:8080/volumes/{volume_id}/awss3trash',
                rel=['hea-trash', 'hea-context-menu']),
            expectedvalues.Action(
                name='heaserver-awss3folders-project-get-presigned-url',
                url='http://localhost:8080/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/presignedurl',
                rel=['hea-dynamic-clipboard', 'hea-context-menu', 'hea-icon-for-clipboard']),
            expectedvalues.Action(
                name='heaserver-awss3folders-project-get-component',
                url='http://localhost:8080/components/bytype/heaobject.project.AWSS3Project',
                rel=['hea-component']),
            expectedvalues.Action(
                name='heaserver-awss3folders-get-delete-preflight-url',
                rel=['hea-delete-preflight'],
                url='http://localhost:8080/preflights/awss3objects/delete')
        ],
        exclude=['body_put'],
        duplicate_action_name='heaserver-awss3folders-project-duplicate-form')):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self._body_post:
            encoded = b64encode(b'Tritimus/').decode('utf-8')
            modified_data = {**db_values[self._coll][0],
                             'display_name': 'Tritimus',
                             'name': encoded,
                             's3_uri': '/'.join(db_values[self._coll][0]['s3_uri'].split('/')[:-2] + ['Tritimus', '']),
                             'key': 'Tritimus/',
                             'instance_id': 'heaobject.project.AWSS3Project^VHJpdGltdXMv',
                             'resource_type_and_id': 'arp-scale-2-cloud-bucket-with-tags11/Tritimus/'}
            if 'id' in modified_data:
                del modified_data['id']
            self._body_post = expectedvalues._create_template(modified_data)


class AWSS3ProjectItemTestCase(
    microservicetestcase.get_test_case_cls_default(
        href='http://localhost:8080/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3folders/root/items',
        wstl_package=service.__package__,
        coll='awss3projects_items',
        fixtures=db_values,
        db_manager_cls=MyManager,
        get_all_actions=[
            expectedvalues.Action(
                name='heaserver-awss3folders-item-get-actual-container',
                url='http://localhost:8080/{+actual_object_uri}',
                rel=['hea-actual', 'hea-actual-container'],
                itemif="actual_object_type_name == AWSS3Project.get_type_name() or actual_object_type_name == AWSS3Folder.get_type_name()"),
            expectedvalues.Action(
                name='heaserver-awss3folders-item-get-actual-not-container',
                url='http://localhost:8080/{+actual_object_uri}',
                rel=['hea-actual'],
                itemif="actual_object_type_name != AWSS3Project.get_type_name() and actual_object_type_name != AWSS3Folder.get_type_name()")
        ],
        get_actions=[
            expectedvalues.Action(
                name='heaserver-awss3folders-item-get-actual-container',
                url='http://localhost:8080/{+actual_object_uri}',
                rel=['hea-actual', 'hea-actual-container'],
                itemif="actual_object_type_name == AWSS3Project.get_type_name() or actual_object_type_name == AWSS3Folder.get_type_name()"),
            expectedvalues.Action(
                name='heaserver-awss3folders-item-get-actual-not-container',
                url='http://localhost:8080/{+actual_object_uri}',
                rel=['hea-actual'],
                itemif="actual_object_type_name != AWSS3Project.get_type_name() and actual_object_type_name != AWSS3Folder.get_type_name()"),
            expectedvalues.Action(name='heaserver-awss3folders-item-get-volume',
                url='http://localhost:8080/volumes/{volume_id}',
                rel=['hea-volume'])
        ],
        exclude=['body_put'])
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self._body_post:
            encoded = b64encode(b'Tritimus/').decode('utf-8')
            modified_data = {**db_values[self._coll][0],
                             'display_name': 'Tritimus',
                             'actual_object_id': encoded,
                             'actual_object_uri': '/'.join(
                                 db_values[self._coll][0]['actual_object_uri'].split('/')[:-1] + [encoded]),
                             'name': encoded,
                             's3_uri': '/'.join(db_values[self._coll][0]['s3_uri'].split('/')[:-2] + ['Tritimus', '']),
                             'key': 'Tritimus/',
                             'path': '/arp-scale-2-cloud-bucket-with-tags11/Tritimus/',
                             'instance_id': 'heaobject.folder.AWSS3ItemInFolder^VHJpdGltdXMv'}
            if 'id' in modified_data:
                del modified_data['id']
            self._body_post = expectedvalues._create_template(modified_data)
