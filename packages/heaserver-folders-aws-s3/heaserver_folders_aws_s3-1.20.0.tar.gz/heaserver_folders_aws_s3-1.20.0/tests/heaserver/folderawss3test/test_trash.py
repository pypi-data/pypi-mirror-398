from .trashawss3testcase import db_store
from heaobject.awss3key import decode_key
from heaobject.user import NONE_USER
from heaserver.service.testcase.mixin import _ordered
import boto3
from heaserver.service.db.database import query_fixtures
from heaserver.folderawss3 import trashservice
from heaserver.service.testcase.aiohttptestcase import HEAAioHTTPTestCase
from heaserver.service.testcase.mockaws import MockS3WithMockMongoManager
from heaserver.service.representor import nvpjson
from moto import mock_aws
from freezegun import freeze_time
from aiohttp.web import Application
from aiohttp import hdrs
from heaserver.service import runner
from heaserver.service import wstl
from contextlib import ExitStack, closing
import logging
import os


class TestTrash(HEAAioHTTPTestCase):
    def run(self, result=None):
        with self._caplog.at_level(logging.DEBUG), mock_aws(), closing(MockS3WithMockMongoManager()) as db, ExitStack() as es, freeze_time("2022-05-17"):
            self.__db = db
            self.__db.start_database(es)
            self.__db.insert_desktop_objects(query_fixtures(
                fixtures=db_store, db_manager=self.__db, name='volumes'))
            self.__db.insert_desktop_objects(query_fixtures(
                fixtures=db_store, db_manager=self.__db, name='properties'))
            self.__db.insert_desktop_objects(query_fixtures(
                fixtures=db_store, db_manager=self.__db, name='buckets'))
            self.__db.insert_desktop_objects(query_fixtures(
                fixtures=db_store, db_manager=self.__db, name='awss3files'))
            s3 = boto3.client('s3')
            key1 = decode_key('VGV4dEZpbGVVVEY4LnR4dA==')
            with freeze_time('2022-05-18'):  # One day after the create date
                s3.delete_object(
                    Bucket='arp-scale-2-cloud-bucket-with-tags11', Key=key1)
            versions = s3.list_object_versions(
                Bucket='arp-scale-2-cloud-bucket-with-tags11', Prefix=key1)['Versions']
            self.__version1 = versions[0]['VersionId']
            key2 = decode_key('YWZvbGRlci9hbm90aGVyZm9sZGVyL0JpbmFyeUZpbGU=')
            with freeze_time('2022-05-18'):  # One day after the create date
                s3.delete_object(
                    Bucket='arp-scale-2-cloud-bucket-with-tags11', Key=key2)
            versions = s3.list_object_versions(
                Bucket='arp-scale-2-cloud-bucket-with-tags11', Prefix=key2)['Versions']
            self.__version2 = versions[0]['VersionId']

            self.maxDiff = None
            self.__app = runner.get_application(db=self.__db,
                                                wstl_builder_factory=wstl.builder_factory(package=trashservice.__package__,
                                                                                          href='http://localhost:8080/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3trash/'))
            return super().run(result)

    async def test_get_deleted_item_not_found(self):
        async with self.client.get(f'/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3trash/VGV4dEZpbGVVVEY4LnR4dA==%2C1') as resp:
            self.assertEqual(404, resp.status)

    async def test_get_deleted_item_bucket_not_found(self):
        async with self.client.get(f'/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags/awss3trash/VGV4dEZpbGVVVEY4LnR4dA==%2C{self.__version1}') as resp:
            self.assertEqual(404, resp.status)

    async def test_get_deleted_item_volume_not_found(self):
        async with self.client.get(f'/volumes/1/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3trash/VGV4dEZpbGVVVEY4LnR4dA==%2C{self.__version1}') as resp:
            self.assertEqual(404, resp.status)

    async def test_get_deleted_item_status(self):
        async with self.client.get(f'/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3trash/VGV4dEZpbGVVVEY4LnR4dA==%2C{self.__version1}') as resp:
            self.assertEqual(200, resp.status)

    async def test_get_deleted_item(self):
        if 'XDG_DATA_HOME' in os.environ:
            type_display_name = 'Plain Text Document'
        else:
            type_display_name = 'Data File'
        async with self.client.get(f'/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3trash/VGV4dEZpbGVVVEY4LnR4dA==%2C{self.__version1}') as resp:
            actual = [{'collection': {'version': '1.0',
                                      'href': f'http://127.0.0.1:{resp.url.port}/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3trash/VGV4dEZpbGVVVEY4LnR4dA==,{self.__version1}',
                                      'permissions': [['COOWNER', 'VIEWER']],
                                      'items': [
                                        {'data': [
                                            {'name': 'actual_object_id', 'value': 'VGV4dEZpbGVVVEY4LnR4dA==', 'prompt': 'actual_object_id', 'display': True},
                                            {'name': 'actual_object_type_name', 'value': 'heaobject.data.AWSS3FileObject', 'prompt': 'actual_object_type_name', 'display': True},
                                            {'name': 'actual_object_uri', 'value': 'volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3files/VGV4dEZpbGVVVEY4LnR4dA==', 'prompt': 'actual_object_uri', 'display': True},
                                            {'name': 'bucket_id', 'value': 'arp-scale-2-cloud-bucket-with-tags11', 'prompt': 'bucket_id', 'display': True},
                                            {'name': 'created', 'value': '2022-05-17T00:00:00+00:00', 'prompt': 'created', 'display': True}, {'name': 'derived_by', 'value': None, 'prompt': 'derived_by', 'display': True},
                                            {'name': 'derived_from', 'value': [], 'prompt': 'derived_from', 'display': True},
                                            {'name': 'description', 'value': None, 'prompt': 'description', 'display': True},
                                            {'name': 'display_name', 'value': 'TextFileUTF8.txt', 'prompt': 'display_name', 'display': True},
                                            {'name': 'human_readable_original_location', 'value': '/arp-scale-2-cloud-bucket-with-tags11/TextFileUTF8.txt', 'prompt': 'human_readable_original_location', 'display': True},
                                            {'name': 'human_readable_size', 'value': '0 Bytes', 'prompt': 'human_readable_size', 'display': True},
                                            {'name': 'id', 'value': f'VGV4dEZpbGVVVEY4LnR4dA==,{self.__version1}', 'prompt': 'id', 'display': False},
                                            {'name': 'instance_id', 'value': f'heaobject.trash.AWSS3FolderFileTrashItem^VGV4dEZpbGVVVEY4LnR4dA==,{self.__version1}', 'prompt': 'instance_id', 'display': True},
                                            {'name': 'invites', 'value': [], 'prompt': 'invites', 'display': True},
                                            {'name': 'key', 'value': 'TextFileUTF8.txt', 'prompt': 'key', 'display': True},
                                            {'name': 'modified', 'value': '2022-05-17T00:00:00+00:00', 'prompt': 'modified', 'display': True},
                                            {'name': 'deleted', 'value': '2022-05-18T00:00:00+00:00', 'prompt': 'deleted', 'display': True},
                                            {'name': 'name', 'value': f'VGV4dEZpbGVVVEY4LnR4dA==,{self.__version1}', 'prompt': 'name', 'display': True},
                                            {'name': 'original_location', 'value': '/arp-scale-2-cloud-bucket-with-tags11/TextFileUTF8.txt', 'prompt': 'original_location', 'display': True},
                                            {'name': 'owner', 'value': 'system|none', 'prompt': 'owner', 'display': True},
                                            {'name': 's3_uri', 'value': 's3://arp-scale-2-cloud-bucket-with-tags11/TextFileUTF8.txt', 'prompt': 's3_uri', 'display': True},
                                            {'name': 'group_shares', 'value': [], 'prompt': 'group_shares', 'display': True},
                                            {'name': 'size', 'value': 0, 'prompt': 'size', 'display': True},
                                            {'name': 'source', 'value': 'AWS S3', 'prompt': 'source', 'display': True},
                                            {'name': 'source_detail', 'value': None, 'prompt': 'source_detail', 'display': True},
                                            {'name': 'storage_class', 'value': 'STANDARD', 'prompt': 'storage_class', 'display': True},
                                            {'name': 'type', 'value': 'heaobject.trash.AWSS3FolderFileTrashItem', 'prompt': 'type', 'display': True},
                                            {'name': 'type_display_name', 'value': type_display_name, 'prompt': 'type_display_name', 'display': True},
                                            {'name': 'version', 'value': self.__version1, 'prompt': 'version', 'display': True},
                                            {'name': 'volume_id', 'value': '666f6f2d6261722d71757578', 'prompt': 'volume_id', 'display': True},
                                            {'name': 'archive_storage_class', 'value': False, 'prompt': 'archive_storage_class', 'display': True},
                                            {'name': 'super_admin_default_permissions', 'value': [], 'prompt': 'super_admin_default_permissions', 'display': True},
                                            {'name': 'dynamic_permission_supported', 'value': False, 'prompt': 'dynamic_permission_supported', 'display': True},
                                            {'name': 'parent_uris', 'value': ['volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11'], 'prompt': 'parent_uris', 'display': True},
                                            {'name': 'resource_type_and_id', 'value': 'arp-scale-2-cloud-bucket-with-tags11/TextFileUTF8.txt?versionId=' + self.__version1, 'prompt': 'resource_type_and_id', 'display': True},
                                            {'name': 'basis', 'section': 'user_shares', 'index': 0, 'value': 'USER', 'prompt': 'basis', 'display': True},
                                            {'name': 'group', 'section': 'user_shares', 'index': 0, 'value': NONE_USER, 'prompt': 'group', 'display': True},
                                            {'name': 'user', 'section': 'user_shares', 'index': 0, 'value': NONE_USER, 'prompt': 'user', 'display': True},
                                            {'name': 'invite', 'section': 'user_shares', 'index': 0, 'value': None, 'prompt': 'invite', 'display': True},
                                            {'name': 'type', 'section': 'user_shares', 'index': 0, 'prompt': 'type', 'value': 'heaobject.root.ShareImpl', 'display': True},
                                            {'name': 'type_display_name', 'section': 'user_shares', 'index': 0, 'prompt': 'type_display_name', 'value': 'Share', 'display': True},
                                            {'name': 'permissions', 'section': 'user_shares', 'index': 0, 'value': ['VIEWER', 'COOWNER'], 'prompt': 'permissions', 'display': True},
                                            {'name': 'basis', 'section': 'shares', 'index': 0, 'value': 'USER', 'prompt': 'basis', 'display': True},
                                            {'name': 'group', 'section': 'shares', 'index': 0, 'value': NONE_USER, 'prompt': 'group', 'display': True},
                                            {'name': 'user', 'section': 'shares', 'index': 0, 'value': NONE_USER, 'prompt': 'user', 'display': True},
                                            {'name': 'invite', 'section': 'shares', 'index': 0, 'value': None, 'prompt': 'invite', 'display': True},
                                            {'name': 'type', 'section': 'shares', 'index': 0, 'prompt': 'type', 'value': 'heaobject.root.ShareImpl', 'display': True},
                                            {'name': 'type_display_name', 'section': 'shares', 'index': 0, 'prompt': 'type_display_name', 'value': 'Share', 'display': True},
                                            {'name': 'permissions', 'section': 'shares', 'index': 0, 'value': ['VIEWER', 'COOWNER'], 'prompt': 'permissions', 'display': True}],
                                          'links': [
                                            {'prompt': 'Restore', 'rel': 'hea-trash-restore-confirmer hea-context-menu hea-confirm-prompt', 'href': f'/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3trash/VGV4dEZpbGVVVEY4LnR4dA%3D%3D%2C{self.__version1}/restorer'},
                                            {'prompt': 'Permanently delete', 'rel': 'hea-trash-delete-confirmer hea-context-menu hea-confirm-prompt', 'href': f'/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3trash/VGV4dEZpbGVVVEY4LnR4dA%3D%3D%2C{self.__version1}/deleter'},
                                            {'prompt': 'View', 'rel': 'self', 'href': f'/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3trash/VGV4dEZpbGVVVEY4LnR4dA%3D%3D%2C{self.__version1}'},
                                            {'prompt': 'View volume', 'rel': 'hea-volume', 'href': '/volumes/666f6f2d6261722d71757578'},
                                            {'prompt': 'View account', 'rel': 'hea-account', 'href': '/volumes/666f6f2d6261722d71757578/awsaccounts/me'},
                                            {'prompt': 'Open parent', 'rel': 'hea-parent', 'href': '/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11'}]}],
                                      'template': {'prompt': 'Properties', 'rel': 'hea-properties hea-context-menu',
                                                   'data': [
                                                        {'name': 'id', 'value': f'VGV4dEZpbGVVVEY4LnR4dA==,{self.__version1}', 'prompt': 'Id', 'required': False, 'readOnly': True, 'pattern': None},
                                                        {'name': 'display_name', 'value': 'TextFileUTF8.txt', 'prompt': 'Name', 'required': False, 'readOnly': True, 'pattern': None},
                                                        {'name': 'original_location', 'value': '/arp-scale-2-cloud-bucket-with-tags11/TextFileUTF8.txt', 'prompt': 'Original location', 'required': False, 'readOnly': True, 'pattern': None},
                                                        {'name': 'type', 'value': 'heaobject.trash.AWSS3FolderFileTrashItem', 'prompt': 'Type', 'required': False, 'readOnly': True, 'pattern': None},
                                                        {'name': 'description', 'value': None, 'prompt': 'Description', 'required': False, 'readOnly': True, 'pattern': None, 'type': 'textarea'},
                                                        {'name': 'size', 'value': 0, 'prompt': 'Size in bytes', 'required': False, 'readOnly': True, 'pattern': None, 'display': False},
                                                        {'name': 'human_readable_size', 'value': '0 Bytes', 'prompt': 'Size', 'required': False, 'readOnly': True, 'pattern': None},
                                                        {'name': 'storage_class', 'value': 'STANDARD', 'prompt': 'Storage class', 'required': False, 'readOnly': True, 'pattern': None},
                                                        {'name': 's3_uri', 'value': 's3://arp-scale-2-cloud-bucket-with-tags11/TextFileUTF8.txt', 'prompt': 'S3 URI', 'required': False, 'readOnly': True, 'pattern': None},
                                                        {'name': 'mime_type', 'value': None, 'prompt': 'MIME Type', 'required': False, 'readOnly': True, 'pattern': None},
                                                        {'name': 'owner', 'value': 'system|none', 'prompt': 'Owner', 'required': False, 'readOnly': True, 'pattern': None, 'type': 'select', 'options': {'href': '/people/', 'text': 'display_name', 'value': 'id'}},
                                                        {'name': 'created', 'value': '2022-05-17T00:00:00+00:00', 'prompt': 'Created', 'required': False, 'readOnly': True, 'pattern': None, 'type': 'datetime'},
                                                        {'name': 'modified', 'value': '2022-05-17T00:00:00+00:00', 'prompt': 'Modified', 'required': False, 'readOnly': True, 'pattern': None, 'type': 'datetime'},
                                                        {'name': 'deleted', 'value': '2022-05-18T00:00:00+00:00', 'prompt': 'Deleted', 'required': False, 'readOnly': True, 'pattern': None, 'type': 'datetime'},
                                                        {'name': 'source', 'value': 'AWS S3', 'prompt': 'Source', 'required': False, 'readOnly': True, 'pattern': None},
                                                        {'section': 'shares', 'index': -1, 'sectionPrompt': 'Shares', 'name': 'user', 'value': None, 'prompt': 'User', 'required': False, 'readOnly': True, 'pattern': None, 'type': 'select', 'options': {'href': '/people/', 'text': 'display_name', 'value': 'id'}},
                                                        {'section': 'shares', 'index': -1, 'name': 'permissions', 'value': None, 'prompt': 'Permissions', 'required': False, 'readOnly': True, 'pattern': None, 'type': 'select', 'cardinality': 'multiple', 'options': [{'value': 'COOWNER', 'text': 'Co-owner'}, {'value': 'CREATOR', 'text': 'Creator'}, {'value': 'DELETER', 'text': 'Deleter'}, {'value': 'EDITOR', 'text': 'Editor'}, {'value': 'SHARER', 'text': 'Sharer'}, {'value': 'VIEWER', 'text': 'Viewer'}]},
                                                        {'section': 'shares', 'index': 0, 'sectionPrompt': 'Shares', 'name': 'user', 'value': NONE_USER, 'prompt': 'User', 'required': False, 'readOnly': True, 'pattern': None, 'type': 'select', 'options': {'href': '/people/', 'text': 'display_name', 'value': 'id'}},
                                                        {'section': 'shares', 'index': 0, 'name': 'permissions', 'value': ['COOWNER', 'VIEWER'], 'prompt': 'Permissions', 'required': False, 'readOnly': True, 'pattern': None, 'type': 'select', 'cardinality': 'multiple', 'options': [{'value': 'COOWNER', 'text': 'Co-owner'}, {'value': 'CREATOR', 'text': 'Creator'}, {'value': 'DELETER', 'text': 'Deleter'}, {'value': 'EDITOR', 'text': 'Editor'}, {'value': 'SHARER', 'text': 'Sharer'}, {'value': 'VIEWER', 'text': 'Viewer'}]}
                                                    ]}}}]
            self.assertEqual(_ordered(actual), _ordered(await resp.json()))

    async def test_get_deleted_item_nvpjson(self):
        if 'XDG_DATA_HOME' in os.environ:
            type_display_name = 'Plain Text Document'
        else:
            type_display_name = 'Data File'
        async with self.client.get(f'/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3trash/VGV4dEZpbGVVVEY4LnR4dA==,{self.__version1}', headers={hdrs.ACCEPT: nvpjson.MIME_TYPE}) as resp:
            actual = [{'actual_object_id': 'VGV4dEZpbGVVVEY4LnR4dA==',
                       'actual_object_type_name':
                       'heaobject.data.AWSS3FileObject',
                       'actual_object_uri': 'volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3files/VGV4dEZpbGVVVEY4LnR4dA==',
                       'bucket_id': 'arp-scale-2-cloud-bucket-with-tags11',
                       'created': '2022-05-17T00:00:00+00:00',
                       'derived_by': None,
                       'derived_from': [],
                       'description': None,
                       'display_name': 'TextFileUTF8.txt',
                       'human_readable_original_location': '/arp-scale-2-cloud-bucket-with-tags11/TextFileUTF8.txt',
                       'human_readable_size': '0 Bytes',
                       'id': f'VGV4dEZpbGVVVEY4LnR4dA==,{self.__version1}',
                       'instance_id': f'heaobject.trash.AWSS3FolderFileTrashItem^VGV4dEZpbGVVVEY4LnR4dA==,{self.__version1}',
                       'invites': [],
                       'key': 'TextFileUTF8.txt',
                       'modified': '2022-05-17T00:00:00+00:00',
                       'deleted': '2022-05-18T00:00:00+00:00',
                       'name': f'VGV4dEZpbGVVVEY4LnR4dA==,{self.__version1}',
                       'original_location': '/arp-scale-2-cloud-bucket-with-tags11/TextFileUTF8.txt',
                       'owner': 'system|none',
                       's3_uri': 's3://arp-scale-2-cloud-bucket-with-tags11/TextFileUTF8.txt',
                       'shares': [{'basis': 'USER',
                                    'group': NONE_USER,
                                    'invite': None,
                                    'permissions': ['COOWNER', 'VIEWER'],
                                    'type': 'heaobject.root.ShareImpl',
                                    'type_display_name': 'Share',
                                    'user': NONE_USER}],
                       'user_shares': [{'basis': 'USER',
                                    'group': NONE_USER,
                                    'invite': None,
                                    'permissions': ['COOWNER', 'VIEWER'],
                                    'type': 'heaobject.root.ShareImpl',
                                    'type_display_name': 'Share',
                                    'user': NONE_USER}],
                       'group_shares': [],
                       'size': 0,
                       'source': 'AWS S3',
                       'source_detail': None,
                       'storage_class': 'STANDARD',
                       'type': 'heaobject.trash.AWSS3FolderFileTrashItem',
                       'parent_uris': ['volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11'],
                       'type_display_name': type_display_name,
                       'version': self.__version1,
                       'volume_id': '666f6f2d6261722d71757578',
                       'archive_storage_class': False,
                       'super_admin_default_permissions': [],
                       'dynamic_permission_supported': False,
                       'resource_type_and_id': 'arp-scale-2-cloud-bucket-with-tags11/TextFileUTF8.txt?versionId=' + self.__version1}]
            self.assertEqual(_ordered(actual), _ordered(await resp.json()))

    async def test_get_deleted_items_status(self):
        async with self.client.get('/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3trash') as resp:
            self.assertEqual(200, resp.status)

    async def test_get_deleted_items_nvpjson(self):
        if 'XDG_DATA_HOME' in os.environ:
            type_display_name = 'Plain Text Document'
        else:
            type_display_name = 'Data File'
        async with self.client.get('/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3trash', headers={hdrs.ACCEPT: nvpjson.MIME_TYPE}) as resp:
            actual = [{'actual_object_id': 'VGV4dEZpbGVVVEY4LnR4dA==',
                       'actual_object_type_name':
                       'heaobject.data.AWSS3FileObject',
                       'actual_object_uri': 'volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3files/VGV4dEZpbGVVVEY4LnR4dA==',
                       'bucket_id': 'arp-scale-2-cloud-bucket-with-tags11',
                       'created': '2022-05-17T00:00:00+00:00',
                       'derived_by': None,
                       'derived_from': [],
                       'description': None,
                       'display_name': 'TextFileUTF8.txt',
                       'human_readable_original_location': '/arp-scale-2-cloud-bucket-with-tags11/TextFileUTF8.txt',
                       'human_readable_size': '0 Bytes',
                       'id': f'VGV4dEZpbGVVVEY4LnR4dA==,{self.__version1}',
                       'instance_id': f'heaobject.trash.AWSS3FolderFileTrashItem^VGV4dEZpbGVVVEY4LnR4dA==,{self.__version1}',
                       'invites': [],
                       'key': 'TextFileUTF8.txt',
                       'modified': '2022-05-17T00:00:00+00:00',
                       'deleted': '2022-05-18T00:00:00+00:00',
                       'name': f'VGV4dEZpbGVVVEY4LnR4dA==,{self.__version1}',
                       'original_location': '/arp-scale-2-cloud-bucket-with-tags11/TextFileUTF8.txt',
                       'owner': 'system|none',
                       's3_uri': 's3://arp-scale-2-cloud-bucket-with-tags11/TextFileUTF8.txt',
                       'shares': [{'basis': 'USER',
                                    'group': NONE_USER,
                                    'invite': None,
                                    'permissions': ['COOWNER', 'VIEWER'],
                                    'type': 'heaobject.root.ShareImpl',
                                    'type_display_name': 'Share',
                                    'user': NONE_USER}],
                       'user_shares': [{'basis': 'USER',
                                    'group': NONE_USER,
                                    'invite': None,
                                    'permissions': ['COOWNER', 'VIEWER'],
                                    'type': 'heaobject.root.ShareImpl',
                                    'type_display_name': 'Share',
                                    'user': NONE_USER}],
                       'group_shares': [],
                       'size': 0,
                       'source': 'AWS S3',
                       'source_detail': None,
                       'storage_class': 'STANDARD',
                       'type': 'heaobject.trash.AWSS3FolderFileTrashItem',
                       'parent_uris': ['volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11'],
                       'type_display_name': type_display_name,
                       'version': self.__version1,
                       'volume_id': '666f6f2d6261722d71757578',
                       'archive_storage_class': False,
                       'super_admin_default_permissions': [],
                       'dynamic_permission_supported': False,
                       'resource_type_and_id': 'arp-scale-2-cloud-bucket-with-tags11/TextFileUTF8.txt?versionId=' + self.__version1},
                       {'actual_object_id': 'YWZvbGRlci9hbm90aGVyZm9sZGVyL0JpbmFyeUZpbGU=',
                       'actual_object_type_name': 'heaobject.data.AWSS3FileObject',
                       'actual_object_uri': 'volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3files/YWZvbGRlci9hbm90aGVyZm9sZGVyL0JpbmFyeUZpbGU=',
                       'bucket_id': 'arp-scale-2-cloud-bucket-with-tags11',
                       'created': '2022-05-17T00:00:00+00:00',
                       'derived_by': None,
                       'derived_from': [],
                       'description': None,
                       'display_name': 'BinaryFile',
                       'human_readable_original_location': '/arp-scale-2-cloud-bucket-with-tags11/afolder/anotherfolder/BinaryFile',
                       'human_readable_size': '0 Bytes',
                       'id': f'YWZvbGRlci9hbm90aGVyZm9sZGVyL0JpbmFyeUZpbGU=,{self.__version2}',
                       'instance_id': f'heaobject.trash.AWSS3FolderFileTrashItem^YWZvbGRlci9hbm90aGVyZm9sZGVyL0JpbmFyeUZpbGU=,{self.__version2}',
                       'invites': [],
                       'key': 'afolder/anotherfolder/BinaryFile',
                       'modified': '2022-05-17T00:00:00+00:00',
                       'deleted': '2022-05-18T00:00:00+00:00',
                       'name': f'YWZvbGRlci9hbm90aGVyZm9sZGVyL0JpbmFyeUZpbGU=,{self.__version2}',
                       'original_location': '/arp-scale-2-cloud-bucket-with-tags11/afolder/anotherfolder/BinaryFile',
                       'owner': 'system|none',
                       's3_uri': 's3://arp-scale-2-cloud-bucket-with-tags11/afolder/anotherfolder/BinaryFile',
                       'shares': [{'basis': 'USER',
                                    'group': NONE_USER,
                                    'invite': None,
                                    'permissions': ['COOWNER', 'VIEWER'],
                                    'type': 'heaobject.root.ShareImpl',
                                    'type_display_name': 'Share',
                                    'user': NONE_USER}],
                       'user_shares': [{'basis': 'USER',
                                    'group': NONE_USER,
                                    'invite': None,
                                    'permissions': ['COOWNER', 'VIEWER'],
                                    'type': 'heaobject.root.ShareImpl',
                                    'type_display_name': 'Share',
                                    'user': NONE_USER}],
                       'group_shares': [],
                       'size': 0,
                       'source': 'AWS S3',
                       'source_detail': None,
                       'storage_class': 'STANDARD',
                       'type': 'heaobject.trash.AWSS3FolderFileTrashItem',
                       'parent_uris': ['volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3folders/YWZvbGRlci9hbm90aGVyZm9sZGVyLw=='],
                       'type_display_name': 'Data File',
                       'version': self.__version2,
                       'volume_id': '666f6f2d6261722d71757578',
                       'archive_storage_class': False,
                       'super_admin_default_permissions': [],
                       'dynamic_permission_supported': False,
                       'resource_type_and_id': 'arp-scale-2-cloud-bucket-with-tags11/afolder/anotherfolder/BinaryFile?versionId=' + self.__version2}
                       ]
            self.assertEqual(_ordered(actual), _ordered(await resp.json()))

    async def test_get_deleted_items(self):
        if 'XDG_DATA_HOME' in os.environ:
            type_display_name = 'Plain Text Document'
        else:
            type_display_name = 'Data File'
        async with self.client.get('/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3trash') as resp:
            actual = [{
                'collection': {
                    'version': '1.0',
                    'href': f'http://127.0.0.1:{resp.url.port}/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3trash',
                    'permissions': [['COOWNER', 'VIEWER'], ['COOWNER', 'VIEWER']],
                    'items': [
                        {
                            'data': [
                                {'name': 'actual_object_id', 'value': 'VGV4dEZpbGVVVEY4LnR4dA==', 'prompt': 'actual_object_id', 'display': True},
                                {'name': 'actual_object_type_name', 'value': 'heaobject.data.AWSS3FileObject', 'prompt': 'actual_object_type_name', 'display': True},
                                {'name': 'actual_object_uri', 'value': 'volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3files/VGV4dEZpbGVVVEY4LnR4dA==', 'prompt': 'actual_object_uri', 'display': True},
                                {'name': 'bucket_id', 'value': 'arp-scale-2-cloud-bucket-with-tags11', 'prompt': 'bucket_id', 'display': True},
                                {'name': 'created', 'value': '2022-05-17T00:00:00+00:00', 'prompt': 'created', 'display': True},
                                {'name': 'derived_by', 'value': None, 'prompt': 'derived_by', 'display': True},
                                {'name': 'derived_from', 'value': [], 'prompt': 'derived_from', 'display': True},
                                {'name': 'description', 'value': None, 'prompt': 'description', 'display': True},
                                {'name': 'display_name', 'value': 'TextFileUTF8.txt', 'prompt': 'display_name', 'display': True},
                                {'name': 'human_readable_original_location', 'value': '/arp-scale-2-cloud-bucket-with-tags11/TextFileUTF8.txt', 'prompt': 'human_readable_original_location', 'display': True},
                                {'name': 'human_readable_size', 'value': '0 Bytes', 'prompt': 'human_readable_size', 'display': True},
                                {'name': 'id', 'value': f'VGV4dEZpbGVVVEY4LnR4dA==,{self.__version1}', 'prompt': 'id', 'display': False},
                                {'name': 'instance_id', 'value': f'heaobject.trash.AWSS3FolderFileTrashItem^VGV4dEZpbGVVVEY4LnR4dA==,{self.__version1}', 'prompt': 'instance_id', 'display': True},
                                {'name': 'invites', 'value': [], 'prompt': 'invites', 'display': True},
                                {'name': 'key', 'value': 'TextFileUTF8.txt', 'prompt': 'key', 'display': True},
                                {'name': 'modified', 'value': '2022-05-17T00:00:00+00:00', 'prompt': 'modified', 'display': True},
                                {'name': 'deleted', 'value': '2022-05-18T00:00:00+00:00', 'prompt': 'deleted', 'display': True},
                                {'name': 'name', 'value': f'VGV4dEZpbGVVVEY4LnR4dA==,{self.__version1}', 'prompt': 'name', 'display': True},
                                {'name': 'original_location', 'value': '/arp-scale-2-cloud-bucket-with-tags11/TextFileUTF8.txt', 'prompt': 'original_location', 'display': True},
                                {'name': 'owner', 'value': 'system|none', 'prompt': 'owner', 'display': True},
                                {'name': 's3_uri', 'value': 's3://arp-scale-2-cloud-bucket-with-tags11/TextFileUTF8.txt', 'prompt': 's3_uri', 'display': True},
                                {'name': 'group_shares', 'value': [], 'prompt': 'group_shares', 'display': True},
                                {'name': 'size', 'value': 0, 'prompt': 'size', 'display': True},
                                {'name': 'source', 'value': 'AWS S3', 'prompt': 'source', 'display': True},
                                {'name': 'source_detail', 'value': None, 'prompt': 'source_detail', 'display': True},
                                {'name': 'storage_class', 'value': 'STANDARD', 'prompt': 'storage_class', 'display': True},
                                {'name': 'type', 'value': 'heaobject.trash.AWSS3FolderFileTrashItem', 'prompt': 'type', 'display': True},
                                {'name': 'type_display_name', 'value': type_display_name, 'prompt': 'type_display_name', 'display': True},
                                {'name': 'version', 'value': self.__version1, 'prompt': 'version', 'display': True},
                                {'name': 'volume_id', 'value': '666f6f2d6261722d71757578', 'prompt': 'volume_id', 'display': True},
                                {'name': 'archive_storage_class', 'value': False, 'prompt': 'archive_storage_class', 'display': True},
                                {'name': 'super_admin_default_permissions', 'value': [], 'prompt': 'super_admin_default_permissions', 'display': True},
                                {'name': 'dynamic_permission_supported', 'value': False, 'prompt': 'dynamic_permission_supported', 'display': True},
                                {'name': 'parent_uris', 'value': ['volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11'], 'prompt': 'parent_uris', 'display': True},
                                {'name': 'resource_type_and_id', 'value': 'arp-scale-2-cloud-bucket-with-tags11/TextFileUTF8.txt?versionId=' + self.__version1, 'prompt': 'resource_type_and_id', 'display': True},
                                {'name': 'basis', 'section': 'user_shares', 'index': 0, 'value': 'USER', 'prompt': 'basis', 'display': True},
                                {'name': 'group', 'section': 'user_shares', 'index': 0, 'value': NONE_USER, 'prompt': 'group', 'display': True},
                                {'name': 'user', 'section': 'user_shares', 'index': 0, 'value': NONE_USER, 'prompt': 'user', 'display': True},
                                {'name': 'invite', 'section': 'user_shares', 'index': 0, 'value': None, 'prompt': 'invite', 'display': True},
                                {'name': 'type', 'section': 'user_shares', 'index': 0, 'prompt': 'type', 'value': 'heaobject.root.ShareImpl', 'display': True},
                                {'name': 'type_display_name', 'section': 'user_shares', 'index': 0, 'prompt': 'type_display_name', 'value': 'Share', 'display': True},
                                {'name': 'permissions', 'section': 'user_shares', 'index': 0, 'value': ['VIEWER', 'COOWNER'], 'prompt': 'permissions', 'display': True},
                                {'name': 'basis', 'section': 'shares', 'index': 0, 'value': 'USER', 'prompt': 'basis', 'display': True},
                                {'name': 'group', 'section': 'shares', 'index': 0, 'value': NONE_USER, 'prompt': 'group', 'display': True},
                                {'name': 'user', 'section': 'shares', 'index': 0, 'value': NONE_USER, 'prompt': 'user', 'display': True},
                                {'name': 'invite', 'section': 'shares', 'index': 0, 'value': None, 'prompt': 'invite', 'display': True},
                                {'name': 'type', 'section': 'shares', 'index': 0, 'prompt': 'type', 'value': 'heaobject.root.ShareImpl', 'display': True},
                                {'name': 'type_display_name', 'section': 'shares', 'index': 0, 'prompt': 'type_display_name', 'value': 'Share', 'display': True},
                                {'name': 'permissions', 'section': 'shares', 'index': 0, 'value': ['VIEWER', 'COOWNER'], 'prompt': 'permissions', 'display': True}
                            ],
                            'links': [
                                {'prompt': 'Restore', 'rel': 'hea-trash-restore-confirmer hea-context-menu hea-confirm-prompt', 'href': f'/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3trash/VGV4dEZpbGVVVEY4LnR4dA%3D%3D%2C{self.__version1}/restorer'},
                                {'prompt': 'Permanently delete', 'rel': 'hea-trash-delete-confirmer hea-context-menu hea-confirm-prompt', 'href': f'/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3trash/VGV4dEZpbGVVVEY4LnR4dA%3D%3D%2C{self.__version1}/deleter'},
                                {'prompt': 'View', 'rel': 'self', 'href': f'/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3trash/VGV4dEZpbGVVVEY4LnR4dA%3D%3D%2C{self.__version1}'},
                                {'prompt': 'Open parent', 'rel': 'hea-parent', 'href': '/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11'}
                            ]
                        },
                        {
                            'data': [
                                {'name': 'actual_object_id', 'value': 'YWZvbGRlci9hbm90aGVyZm9sZGVyL0JpbmFyeUZpbGU=', 'prompt': 'actual_object_id', 'display': True},
                                {'name': 'actual_object_type_name', 'value': 'heaobject.data.AWSS3FileObject', 'prompt': 'actual_object_type_name',  'display': True},
                                {'name': 'actual_object_uri', 'value': 'volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3files/YWZvbGRlci9hbm90aGVyZm9sZGVyL0JpbmFyeUZpbGU=', 'prompt': 'actual_object_uri', 'display': True},
                                {'name': 'bucket_id', 'value': 'arp-scale-2-cloud-bucket-with-tags11', 'prompt': 'bucket_id', 'display': True},
                                {'name': 'created', 'value': '2022-05-17T00:00:00+00:00', 'prompt': 'created', 'display': True},
                                {'name': 'derived_by', 'value': None, 'prompt': 'derived_by', 'display': True},
                                {'name': 'derived_from', 'value': [], 'prompt': 'derived_from', 'display': True},
                                {'name': 'description', 'value': None, 'prompt': 'description', 'display': True},
                                {'name': 'display_name', 'value': 'BinaryFile', 'prompt': 'display_name', 'display': True},
                                {'name': 'human_readable_original_location', 'value': '/arp-scale-2-cloud-bucket-with-tags11/afolder/anotherfolder/BinaryFile', 'prompt': 'human_readable_original_location', 'display': True},
                                {'name': 'human_readable_size', 'value': '0 Bytes', 'prompt': 'human_readable_size', 'display': True},
                                {'name': 'id', 'value': f'YWZvbGRlci9hbm90aGVyZm9sZGVyL0JpbmFyeUZpbGU=,{self.__version2}', 'prompt': 'id', 'display': False},
                                {'name': 'instance_id', 'value': f'heaobject.trash.AWSS3FolderFileTrashItem^YWZvbGRlci9hbm90aGVyZm9sZGVyL0JpbmFyeUZpbGU=,{self.__version2}', 'prompt': 'instance_id', 'display': True},
                                {'name': 'invites', 'value': [], 'prompt': 'invites', 'display': True},
                                {'name': 'key', 'value': 'afolder/anotherfolder/BinaryFile', 'prompt': 'key', 'display': True},
                                {'name': 'modified', 'value': '2022-05-17T00:00:00+00:00', 'prompt': 'modified', 'display': True},
                                {'name': 'deleted', 'value': '2022-05-18T00:00:00+00:00', 'prompt': 'deleted', 'display': True},
                                {'name': 'name', 'value': f'YWZvbGRlci9hbm90aGVyZm9sZGVyL0JpbmFyeUZpbGU=,{self.__version2}', 'prompt': 'name', 'display': True},
                                {'name': 'original_location', 'value': '/arp-scale-2-cloud-bucket-with-tags11/afolder/anotherfolder/BinaryFile', 'prompt': 'original_location', 'display': True},
                                {'name': 'owner', 'value': 'system|none', 'prompt': 'owner', 'display': True},
                                {'name': 's3_uri', 'value': 's3://arp-scale-2-cloud-bucket-with-tags11/afolder/anotherfolder/BinaryFile', 'prompt': 's3_uri', 'display': True},
                                {'name': 'size', 'value': 0, 'prompt': 'size', 'display': True},
                                {'name': 'group_shares', 'value': [], 'prompt': 'group_shares', 'display': True},
                                {'name': 'source', 'value': 'AWS S3', 'prompt': 'source', 'display': True},
                                {'name': 'source_detail', 'value': None, 'prompt': 'source_detail', 'display': True},
                                {'name': 'storage_class', 'value': 'STANDARD', 'prompt': 'storage_class', 'display': True},
                                {'name': 'type', 'value': 'heaobject.trash.AWSS3FolderFileTrashItem', 'prompt': 'type', 'display': True},
                                {'name': 'type_display_name', 'value': 'Data File', 'prompt': 'type_display_name', 'display': True},
                                {'name': 'version', 'value': self.__version2, 'prompt': 'version', 'display': True},
                                {'name': 'volume_id', 'value': '666f6f2d6261722d71757578', 'prompt': 'volume_id', 'display': True},
                                {'name': 'archive_storage_class', 'value': False, 'prompt': 'archive_storage_class', 'display': True},
                                {'name': 'super_admin_default_permissions', 'value': [], 'prompt': 'super_admin_default_permissions', 'display': True},
                                {'name': 'dynamic_permission_supported', 'value': False, 'prompt': 'dynamic_permission_supported', 'display': True},
                                {'name': 'parent_uris', 'value': ['volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3folders/YWZvbGRlci9hbm90aGVyZm9sZGVyLw=='], 'prompt': 'parent_uris', 'display': True},
                                {'name': 'resource_type_and_id', 'value': 'arp-scale-2-cloud-bucket-with-tags11/afolder/anotherfolder/BinaryFile?versionId=' + self.__version2, 'prompt': 'resource_type_and_id', 'display': True},
                                {'name': 'basis', 'section': 'user_shares', 'index': 0, 'value': 'USER', 'prompt': 'basis', 'display': True},
                                {'name': 'group', 'section': 'user_shares', 'index': 0, 'value': NONE_USER, 'prompt': 'group', 'display': True},
                                {'name': 'user', 'section': 'user_shares', 'index': 0, 'value': NONE_USER, 'prompt': 'user', 'display': True},
                                {'name': 'invite', 'section': 'user_shares', 'index': 0, 'value': None, 'prompt': 'invite', 'display': True},
                                {'name': 'type', 'section': 'user_shares', 'index': 0, 'prompt': 'type', 'value': 'heaobject.root.ShareImpl', 'display': True},
                                {'name': 'type_display_name', 'section': 'user_shares', 'index': 0, 'prompt': 'type_display_name', 'value': 'Share', 'display': True},
                                {'name': 'permissions', 'section': 'user_shares', 'index': 0, 'value': ['VIEWER', 'COOWNER'], 'prompt': 'permissions', 'display': True},
                                {'name': 'basis', 'section': 'shares', 'index': 0, 'value': 'USER', 'prompt': 'basis', 'display': True},
                                {'name': 'group', 'section': 'shares', 'index': 0, 'value': NONE_USER, 'prompt': 'group', 'display': True},
                                {'name': 'user', 'section': 'shares', 'index': 0, 'value': NONE_USER, 'prompt': 'user', 'display': True},
                                {'name': 'invite', 'section': 'shares', 'index': 0, 'value': None, 'prompt': 'invite', 'display': True},
                                {'name': 'type', 'section': 'shares', 'index': 0, 'prompt': 'type', 'value': 'heaobject.root.ShareImpl', 'display': True},
                                {'name': 'type_display_name', 'section': 'shares', 'index': 0, 'prompt': 'type_display_name', 'value': 'Share', 'display': True},
                                {'name': 'permissions', 'section': 'shares', 'index': 0, 'value': ['VIEWER', 'COOWNER'], 'prompt': 'permissions', 'display': True}
                            ],
                            'links': [
                                {'prompt': 'Restore', 'rel': 'hea-trash-restore-confirmer hea-context-menu hea-confirm-prompt', 'href': f'/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3trash/YWZvbGRlci9hbm90aGVyZm9sZGVyL0JpbmFyeUZpbGU%3D%2C{self.__version2}/restorer'},
                                {'prompt': 'Permanently delete', 'rel': 'hea-trash-delete-confirmer hea-context-menu hea-confirm-prompt', 'href': f'/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3trash/YWZvbGRlci9hbm90aGVyZm9sZGVyL0JpbmFyeUZpbGU%3D%2C{self.__version2}/deleter'},
                                {'prompt': 'View', 'rel': 'self', 'href': f'/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3trash/YWZvbGRlci9hbm90aGVyZm9sZGVyL0JpbmFyeUZpbGU%3D%2C{self.__version2}'},
                                {'prompt': 'Open parent', 'rel': 'hea-parent', 'href': '/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3folders/YWZvbGRlci9hbm90aGVyZm9sZGVyLw=='}
                            ]
                        }
                    ],
                    'template': {
                        'prompt': 'Properties',
                        'rel': 'hea-properties hea-context-menu',
                        'data': [
                            {'name': 'id', 'value': None, 'prompt': 'Id', 'required': False, 'readOnly': True, 'pattern': None},
                            {'name': 'display_name', 'value': None, 'prompt': 'Name', 'required': False, 'readOnly': True, 'pattern': None},
                            {'name': 'original_location', 'value': None, 'prompt': 'Original location', 'required': False, 'readOnly': True, 'pattern': None},
                            {'name': 'type', 'value': None, 'prompt': 'Type', 'required': False, 'readOnly': True, 'pattern': None},
                            {'name': 'description', 'value': None, 'prompt': 'Description', 'required': False, 'readOnly': True, 'pattern': None, 'type': 'textarea'},
                            {'name': 'size', 'value': None, 'prompt': 'Size in bytes', 'required': False, 'readOnly': True, 'pattern': None, 'display': False},
                            {'name': 'human_readable_size', 'value': None, 'prompt': 'Size', 'required': False, 'readOnly': True, 'pattern': None},
                            {'name': 'storage_class', 'value': None, 'prompt': 'Storage class', 'required': False, 'readOnly': True, 'pattern': None},
                            {'name': 's3_uri', 'value': None, 'prompt': 'S3 URI', 'required': False, 'readOnly': True, 'pattern': None},
                            {'name': 'mime_type', 'value': None, 'prompt': 'MIME Type', 'required': False, 'readOnly': True, 'pattern': None},
                            {'name': 'owner', 'value': None, 'prompt': 'Owner', 'required': False, 'readOnly': True, 'pattern': None, 'type': 'select', 'options': {'href': '/people/', 'text': 'display_name', 'value': 'id'}},
                            {'name': 'created', 'value': None, 'prompt': 'Created', 'required': False, 'readOnly': True, 'pattern': None, 'type': 'datetime'},
                            {'name': 'modified', 'value': None, 'prompt': 'Modified', 'required': False, 'readOnly': True, 'pattern': None, 'type': 'datetime'},
                            {'name': 'deleted', 'value': None, 'prompt': 'Deleted', 'required': False, 'readOnly': True, 'pattern': None, 'type': 'datetime'},
                            {'name': 'source', 'value': None, 'prompt': 'Source', 'required': False, 'readOnly': True, 'pattern': None},
                            {'section': 'shares', 'index': -1, 'sectionPrompt': 'Shares', 'name': 'user', 'value': None, 'prompt': 'User', 'required': False, 'readOnly': True, 'pattern': None, 'type': 'select', 'options': {'href': '/people/', 'text': 'display_name', 'value': 'id'}},
                            {'section': 'shares', 'index': -1, 'name': 'permissions', 'value': None, 'prompt': 'Permissions', 'required': False, 'readOnly': True, 'pattern': None, 'type': 'select', 'cardinality': 'multiple', 'options': [
                                {'value': 'COOWNER', 'text': 'Co-owner'},
                                {'value': 'CREATOR', 'text': 'Creator'},
                                {'value': 'DELETER', 'text': 'Deleter'},
                                {'value': 'EDITOR', 'text': 'Editor'},
                                {'value': 'SHARER', 'text': 'Sharer'},
                                {'value': 'VIEWER', 'text': 'Viewer'}
                            ]}
                        ]
                    }
                }
            }]
            self.assertEqual(_ordered(actual), _ordered(await resp.json()))

    async def test_do_empty_trash_status(self):
        async with self.client.get('/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3trashemptier') as resp:
            self.assertEqual(204, resp.status)

    async def test_do_empty_trash(self):
        async with self.client.get('/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3trashemptier') as resp:
            if resp.status != 204:
                self.fail(f'Trash emptier responded with wrong status code {resp.status}')

        async with self.client.get('/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3trash', headers={hdrs.ACCEPT: nvpjson.MIME_TYPE}) as resp:
            self.assertEqual([], await resp.json())

    async def test_permanently_delete_item_status(self):
        async with self.client.get(f'/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3trash/VGV4dEZpbGVVVEY4LnR4dA==%2C{self.__version1}/deleter') as resp:
            self.assertEqual(204, resp.status)

    async def test_permanently_delete_item(self):
        async with self.client.get(f'/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3trash/VGV4dEZpbGVVVEY4LnR4dA==%2C{self.__version1}/deleter') as resp:
            if resp.status != 204:
                self.fail(f'Permanent delete failed for item VGV4dEZpbGVVVEY4LnR4dA==%2C{self.__version1} with status code {resp.status}')

        async with self.client.get(f'/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3trash/VGV4dEZpbGVVVEY4LnR4dA==%2C{self.__version1}') as resp:
            self.assertEqual(404, resp.status)

    async def test_permanently_delete_item_status_delete(self):
        async with self.client.delete(f'/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3trash/VGV4dEZpbGVVVEY4LnR4dA==%2C{self.__version1}') as resp:
            self.assertEqual(204, resp.status)

    async def test_permanently_delete_item_delete(self):
        async with self.client.delete(f'/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3trash/VGV4dEZpbGVVVEY4LnR4dA==%2C{self.__version1}') as resp:
            if resp.status != 204:
                self.fail(f'Permanent delete failed for item VGV4dEZpbGVVVEY4LnR4dA==%2C{self.__version1} with status code {resp.status}')

        async with self.client.get(f'/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3trash/VGV4dEZpbGVVVEY4LnR4dA==%2C{self.__version1}') as resp:
            self.assertEqual(404, resp.status)

    async def test_restore_status(self):
        async with self.client.get(f'/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3trash/VGV4dEZpbGVVVEY4LnR4dA==%2C{self.__version1}/restorer') as resp:
            self.assertEqual(204, resp.status)

    async def test_restore_check_trash_item(self):
        async with self.client.get(f'/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3trash/VGV4dEZpbGVVVEY4LnR4dA==%2C{self.__version1}/restorer') as resp:
            if resp.status != 204:
                self.fail(f'Restore of item VGV4dEZpbGVVVEY4LnR4dA==%2C{self.__version1} failed with status code {resp.status}')

        async with self.client.get(f'/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3trash/VGV4dEZpbGVVVEY4LnR4dA==%2C{self.__version1}') as resp:
            self.assertEqual(404, resp.status)

    async def test_restore_check_trash_item_count(self):
        async with self.client.get(f'/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3trash/VGV4dEZpbGVVVEY4LnR4dA==%2C{self.__version1}/restorer', headers={hdrs.ACCEPT: nvpjson.MIME_TYPE}) as resp:
            if resp.status != 204:
                self.fail(f'Restore of item VGV4dEZpbGVVVEY4LnR4dA==%2C{self.__version1} failed with status code {resp.status}')

        async with self.client.get(f'/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3trash/') as resp:
            self.assertEqual(1, len(await resp.json()))

    async def test_restore_check_bucket(self):
        async with self.client.get(f'/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3trash/VGV4dEZpbGVVVEY4LnR4dA==%2C{self.__version1}/restorer') as resp:
            if resp.status != 204:
                self.fail(f'Restore of item VGV4dEZpbGVVVEY4LnR4dA==%2C{self.__version1} failed with status code {resp.status}')

        s3 = boto3.client('s3')
        from heaserver.folderawss3 import awsservicelib
        async for obj in awsservicelib.list_objects(s3, bucket_id='arp-scale-2-cloud-bucket-with-tags11'):
            if obj['Key'] == 'TextFileUTF8.txt':
                break
        else:
            self.fail('Object TextFileUTF8.txt not restored')

    async def test_trash_item_count(self):
        async with self.client.get('/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3trash/', headers={hdrs.ACCEPT: nvpjson.MIME_TYPE}) as resp:
            self.assertEqual(2, len(await resp.json()))

    async def get_application(self) -> Application:
        return self.__app
