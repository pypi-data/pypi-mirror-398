from copy import deepcopy
from aiohttp import hdrs
from heaserver.service.representor import cj

from .fileawss3testcase import AWSS3FileTestCase
from heaserver.service.representor import wstljson
from heaserver.service.testcase.mixin import DeleteMixin, GetAllMixin, GetOneMixin, PutMixin, _ordered
from heaserver.service.db.database import get_collection_key_from_name
from heaserver.service.representor import nvpjson
from heaobject.awss3key import encode_key
from heaobject import user
from heaobject.data import AWSS3FileObject
import os


def _version_info_removed(data):
    result = deepcopy(data)
    for item in result[0]['collection']['items']:
        item['data'] = [d for d in item['data'] if d['name'] not in('version', 'versions') and d.get('section') != 'versions']
    return result


def _version_info_removed_wstl(data):
    result = deepcopy(data)
    for data_ in result[0]['wstl']['data']:
        if 'version' in data_:
            del data_['version']
        if 'versions' in data_:
            del data_['versions']
    return result


class TestGetFiles(AWSS3FileTestCase, GetAllMixin):
    async def test_options_status_files(self):
        """Checks if an OPTIONS request for all the files succeeds with status 200."""
        obj = await self.client.request('OPTIONS',
                                        (self._href / '').path,
                                        headers=self._headers)
        self.assertEqual(200, obj.status)

    async def test_options_files(self):
        """
        Checks if the "Allow" header in a response to an OPTIONS request for all the files contains GET, DELETE, HEAD,
        and OPTIONS and contains neither POST nor PUT.
        """
        obj = await self.client.request('OPTIONS',
                                        (self._href / '').path,
                                        headers=self._headers)
        if not obj.ok:
            self.fail(f'OPTIONS request failed: {await obj.text()}')
        allow = {method.strip() for method in obj.headers.get(hdrs.ALLOW).split(',')}
        self.assertEqual({'GET', 'DELETE', 'HEAD', 'OPTIONS', 'POST'}, allow)

    async def test_methods_not_allowed(self) -> None:
        """
        Checks if all the methods (except POST) not in the "Allow" header in a response to an OPTIONS request for all
        the files fail with status 405.
        """
        obj = await self.client.request('OPTIONS',
                                        (self._href / '').path,
                                        headers=self._headers)
        if not obj.ok:
            self.fail(f'OPTIONS request failed: {await obj.text()}')
        allowed_methods = {method.strip() for method in obj.headers[hdrs.ALLOW].split(',')}
        all_methods = {'HEAD', 'OPTIONS', 'PUT', 'GET', 'DELETE'}
        prohibited_methods = all_methods - allowed_methods
        resps = {}
        for prohibited in prohibited_methods:
            obj = await self.client.request(prohibited,
                                            (self._href / '').path,
                                            headers=self._headers)
            resps |= {prohibited: obj.status}
        self.assertEqual(dict(zip(prohibited_methods, [405] * len(prohibited_methods))), resps)

    async def test_get_all_wstl(self) -> None:
        """
        Checks if a GET request for all the items as WeSTL JSON succeeds and returns the expected value
        (``_expected_all_wstl``). The test is skipped if the expected WeSTL JSON (``_expected_all_wstl``) is not
        defined.
        """
        if not self._expected_all_wstl:
            self.skipTest('self._expected_all_wstl is not defined')
        async with self.client.request('GET',
                                       (self._href / '').path,
                                       headers={**self._headers, hdrs.ACCEPT: wstljson.MIME_TYPE}) as obj:
            self.assertEqual(_ordered(_version_info_removed_wstl(self._expected_all_wstl)), _ordered(_version_info_removed_wstl(await obj.json())))

    async def test_get_all_json(self) -> None:
        """
        Checks if a GET request for all the items as JSON succeeds and returns the expected value
        (``_expected_all``).
        """
        async with self.client.request('GET',
                                       (self._href / '').path,
                                       headers=self._headers) as obj:
            self.assertEqual(_ordered(_version_info_removed(self._expected_all)), _ordered(_version_info_removed(await obj.json())))


class TestGetFile(AWSS3FileTestCase, GetOneMixin):
    async def test_options_status_file(self):
        """Checks if an OPTIONS request for a single file succeeds with status 200."""
        obj = await self.client.request('OPTIONS',
                                        (self._href / self._id()).path,
                                        headers=self._headers)
        self.assertEqual(200, obj.status)

    async def test_options_file(self):
        """
        Checks if the "Allow" header in a response to an OPTIONS request for a single file contains GET, POST, DELETE,
        HEAD, and OPTIONS and does not contain PUT.
        """
        obj = await self.client.request('OPTIONS',
                                        (self._href / self._id()).path,
                                        headers=self._headers)
        if not obj.ok:
            self.fail(f'OPTIONS request failed: {await obj.text()}')
        allow = {method.strip() for method in obj.headers.get(hdrs.ALLOW).split(',')}
        self.assertEqual({'GET', 'DELETE', 'HEAD', 'OPTIONS', 'PUT'}, allow)

    async def test_methods_not_allowed(self) -> None:
        """
        Checks if all the methods not in the "Allow" header in a response to an OPTIONS request for a single file
        fail with status 405.
        """
        obj = await self.client.request('OPTIONS',
                                        (self._href / self._id()).path,
                                        headers=self._headers)
        if not obj.ok:
            self.fail(f'OPTIONS request failed: {await obj.text()}')
        allowed_methods = {method.strip() for method in obj.headers.get(hdrs.ALLOW).split(',')}
        all_methods = {'HEAD', 'OPTIONS', 'POST', 'PUT', 'GET', 'DELETE'}
        prohibited_methods = all_methods - allowed_methods
        resps = {}
        for prohibited in prohibited_methods:
            obj = await self.client.request(prohibited,
                                            (self._href / self._id()).path,
                                            headers=self._headers)
            resps |= {prohibited: obj.status}
        self.assertEqual(dict(zip(prohibited_methods, [405] * len(prohibited_methods))), resps)

    # Currently backs 200 because it uses the same request handler as the normal get
    # async def test_get_status_opener_choices(self) -> None:
    #     """Checks if a GET request for the opener for a file succeeds with status 300."""
    #     obj = await self.client.request('GET',
    #                                     (self._href / self._id() / 'opener').path,
    #                                     headers=self._headers)
    #     self.assertEqual(300, obj.status)

    async def test_get_opener_hea_default_exists(self) -> None:
        """
        Checks if a GET request for the opener for a file succeeds and returns JSON that contains a
        Collection+JSON object with a rel property in its links that contains 'hea-default'.
        """
        obj = await self.client.request('GET',
                                        (self._href / self._id() / 'opener').path,
                                        headers={**self._headers, hdrs.ACCEPT: cj.MIME_TYPE})
        if not obj.ok:
            self.fail(f'GET request failed: {await obj.text()}')
        received_json = await obj.json()
        rel = received_json[0]['collection']['links'][0]['rel']
        self.assertIn('hea-default', rel)

    async def test_get_content(self):
        async with self.client.request('GET',
                                       (self._href / self._id() / 'content').path,
                                       headers=self._headers) as resp:
            collection_key = get_collection_key_from_name(self._content, self._coll)
            expected = self._content[collection_key][self._id()]
            bucket, content = expected.split(b'|')
            if isinstance(content, str):
                self.assertEqual(content, await resp.text())
            else:
                self.assertEqual(content, await resp.read())

    async def test_copy_status(self):
        href = f'/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3files/{encode_key("TextFileUTF8.txt")}/duplicator'
        body = {'template':
            {'data': [
                {'name': 'target',
                 'value': f'http://localhost:8080/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3folders/{encode_key("TestFolder/")}'}]}}
        async with self.client.post(href, json=body) as resp:
            self.assertEqual(201, resp.status, await resp.text())


    async def test_copy(self):
        if 'XDG_DATA_HOME' in os.environ:
            mime_type = 'text/plain'
            type_display_name = 'Plain Text Document'
        else:
            mime_type = 'application/octet-stream'
            type_display_name = 'Data File'
        href = f'/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3files/{encode_key("TextFileUTF8.txt")}/duplicator'
        body = {'template':
            {'data': [
                {'name': 'target',
                 'value': f'http://localhost:8080/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3folders/{encode_key("TestFolder/")}'}]}}
        async with self.client.post(href, json=body) as resp:
            if resp.status != 201:
                self.fail(await resp.text())

        href2 = f'/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3files/{encode_key("TestFolder/TextFileUTF8.txt")}'
        async with self.client.get(href2, headers={hdrs.ACCEPT: nvpjson.MIME_TYPE}) as resp:
            expected = [{'bucket_id': 'arp-scale-2-cloud-bucket-with-tags11',
                         'created': '2022-05-17T00:00:00+00:00',
                         'derived_by': None,
                         'derived_from': [],
                         'description': None,
                         'display_name': 'TextFileUTF8.txt',
                         'id': 'VGVzdEZvbGRlci9UZXh0RmlsZVVURjgudHh0',
                         'instance_id': 'heaobject.data.AWSS3FileObject^VGVzdEZvbGRlci9UZXh0RmlsZVVURjgudHh0',
                         'invites': [],
                         'key': 'TestFolder/TextFileUTF8.txt',
                         'mime_type': mime_type,
                         'modified': '2022-05-17T00:00:00+00:00',
                         'name': 'VGVzdEZvbGRlci9UZXh0RmlsZVVURjgudHh0',
                         'owner': 'system|aws',
                         's3_uri': 's3://arp-scale-2-cloud-bucket-with-tags11/TestFolder/TextFileUTF8.txt',
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
                         'source': 'AWS S3 (Standard)',
                         'source_detail': 'AWS S3 (Standard)',
                         'storage_class': 'STANDARD',
                         'retrievable': True,
                         'human_readable_archive_detail_state': 'Not Archived',
                         'archive_detail_state': 'NOT_ARCHIVED',
                         'archive_storage_class': False,
                         'available_until': None,
                         'type': 'heaobject.data.AWSS3FileObject',
                         'human_readable_size': '1.3 MB',
                         'size': 1253915,
                         'tags': [],
                         'type_display_name': type_display_name,
                         'resource_type_and_id': 'arp-scale-2-cloud-bucket-with-tags11/TestFolder/TextFileUTF8.txt',
                         'super_admin_default_permissions': [],
                         'dynamic_permission_supported': False}]
            actual = await resp.json()
            if 'version' in actual[0]:
                del actual[0]['version']
            if 'versions' in actual[0]:
                del actual[0]['versions']
            self._assert_equal_ordered(expected, actual)

    async def test_copy_to_root_status(self):
        if 'XDG_DATA_HOME' in os.environ:
            mime_type = 'text/plain'
        else:
            mime_type = 'application/octet-stream'
        href_to_add = f'/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3files/'
        body_to_add = {
                'created': '2022-05-17T00:00:00+00:00',
                'derived_by': None,
                'derived_from': [],
                'description': None,
                'display_name': 'TextFileUTF8-2.txt',
                'id': 'VGVzdEZvbGRlcjIvVGV4dEZpbGVVVEY4LTIudHh0',
                'instance_id': 'heaobject.data.AWSS3FileObject^VGVzdEZvbGRlci9UZXh0RmlsZVVURjgudHh0',
                'invites': [],
                'modified': '2022-05-17T00:00:00+00:00',
                'name': 'VGVzdEZvbGRlcjIvVGV4dEZpbGVVVEY4LTIudHh0',
                'owner': user.NONE_USER,
                'shares': [{
                    'invite': None,
                    'permissions': ['COOWNER'],
                    'type': 'heaobject.root.ShareImpl',
                    'user': 'system|all',
                    'group': 'system|none',
                    'basis': 'USER'
                }],
                'user_shares': [{
                    'invite': None,
                    'permissions': ['COOWNER'],
                    'type': 'heaobject.root.ShareImpl',
                    'user': 'system|all',
                    'group': 'system|none',
                    'basis': 'USER'
                }],
                'group_shares': [],
                'source': 'AWS S3 (Standard)',
                'source_detail': 'AWS S3 (Standard)',
                'storage_class': 'STANDARD',
                'type': AWSS3FileObject.get_type_name(),
                's3_uri': 's3://arp-scale-2-cloud-bucket-with-tags11/TestFolder2/TextFileUTF8-2.txt',
                'version': None,
                'versions': [],
                'mime_type': mime_type,
                'size': 1253915,
                'human_readable_size': '1.3 MB',
                'bucket_id': 'arp-scale-2-cloud-bucket-with-tags11',
                'key': 'TestFolder2/TextFileUTF8-2.txt',
                'resource_type_and_id': 'arp-scale-2-cloud-bucket-with-tags11/TestFolder2/TextFileUTF8-2.txt',
                'super_admin_default_permissions': [],
                'dynamic_permission_supported': False
            }
        async with self.client.post(href_to_add, json=body_to_add) as resp:
            if resp.status != 201:
                self.fail(await resp.text())
        href = f'/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3files/{encode_key("TestFolder2/TextFileUTF8-2.txt")}/duplicator'
        body = {'template':
            {'data': [
                {'name': 'target',
                 'value': f'http://localhost:8080/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3folders/'}]}}
        async with self.client.post(href, json=body) as resp:
            self.assertEqual(201, resp.status, await resp.text())

    async def test_copy_to_root_status_2(self):
        if 'XDG_DATA_HOME' in os.environ:
            mime_type = 'text/plain'
        else:
            mime_type = 'application/octet-stream'
        href_to_add = f'/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3files/'
        body_to_add = {
            'created': '2022-05-17T00:00:00+00:00',
            'derived_by': None,
            'derived_from': [],
            'description': None,
            'display_name': 'TextFileUTF8-2.txt',
            'id': 'VGVzdEZvbGRlcjIvVGV4dEZpbGVVVEY4LTIudHh0',
            'invites': [],
            'modified': '2022-05-17T00:00:00+00:00',
            'name': 'VGVzdEZvbGRlcjIvVGV4dEZpbGVVVEY4LTIudHh0',
            'owner': user.NONE_USER,
            'shares': [{
                'invite': None,
                'permissions': ['COOWNER'],
                'type': 'heaobject.root.ShareImpl',
                'user': 'system|all',
                'group': 'system|none',
                'basis': 'USER'
            }],
            'user_shares': [{
                'invite': None,
                'permissions': ['COOWNER'],
                'type': 'heaobject.root.ShareImpl',
                'user': 'system|all',
                'group': 'system|none',
                'basis': 'USER'
            }],
            'group_shares': [],
            'source': 'AWS S3 (Standard)',
            'source_detail': 'AWS S3 (Standard)',
            'storage_class': 'STANDARD',
            'type': AWSS3FileObject.get_type_name(),
            's3_uri': 's3://arp-scale-2-cloud-bucket-with-tags11/TestFolder2/TextFileUTF8-2.txt',
            'version': None,
            'versions': [],
            'mime_type': mime_type,
            'size': 1253915,
            'human_readable_size': '1.3 MB',
            'bucket_id': 'arp-scale-2-cloud-bucket-with-tags11',
            'key': 'TestFolder2/TextFileUTF8-2.txt',
            'resource_type_and_id': 'arp-scale-2-cloud-bucket-with-tags11/TestFolder2/TextFileUTF8-2.txt',
            'super_admin_default_permissions': [],
            'dynamic_permission_supported': False
        }
        async with self.client.post(href_to_add, json=body_to_add) as resp:
            if resp.status != 201:
                self.fail(await resp.text())
        href = f'/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3files/{encode_key("TestFolder2/TextFileUTF8-2.txt")}/duplicator'
        body = {'template':
            {'data': [
                {'name': 'target',
                 'value': f'http://localhost:8080/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/'}]}}
        async with self.client.post(href, json=body) as resp:
            self.assertEqual(201, resp.status, await resp.text())

    async def test_get(self) -> None:
        """Checks if a GET request succeeds and returns the expected JSON (``_expected_one``)."""
        async with self.client.request('GET',
                                       (self._href / self._id()).path,
                                       headers=self._headers) as obj:
            self._assert_equal_ordered(_version_info_removed(self._expected_one), _version_info_removed(await obj.json()))

    async def test_get_by_name(self):
        """
        Checks if a GET request for the object with the expected name in ``_expected_one_wstl`` succeeds and returns the
        expected data. The test is skipped if the object doesn't have a name.
        """
        name = self._expected_one_wstl[0]['wstl']['data'][0].get('name', None)
        if name is not None:
            async with self.client.request('GET',
                                           (self._href / 'byname' / name).path,
                                           headers={**self._headers, hdrs.ACCEPT: cj.MIME_TYPE}) as response:
                self._assert_equal_ordered([d for d in self._expected_one[0]['collection']['items'][0]['data'] if d['name'] not in('version', 'versions') and d.get('section') != 'versions'],
                                           [d for d in (await response.json())[0]['collection']['items'][0]['data'] if d['name'] not in('version', 'versions') and d.get('section') != 'versions'])

        else:
            self.skipTest('the expected object does not have a name')

    async def test_get_wstl(self) -> None:
        """
        Checks if a GET request for WeSTL data succeeds and returns the expected JSON (``_expected_one_wstl``). The
        test is skipped if the expected WeSTL data (``_expected_one_wstl``) is not defined.
        """
        if not self._expected_one_wstl:
            self.skipTest('self._expected_one_wstl is not defined')
        async with self.client.request('GET',
                                       (self._href / self._id()).path,
                                       headers={**self._headers, hdrs.ACCEPT: wstljson.MIME_TYPE}) as obj:
            self._assert_equal_ordered(_version_info_removed_wstl(self._expected_one_wstl), _version_info_removed_wstl(await obj.json()))

    async def test_get_duplicate_form(self) -> None:
        """
        Checks if a GET request for a copy of WeSTL data from the duplicator succeeds and returns the expected data
        (``_expected_one_wstl_duplicate_form``). The test is skipped if the expected WeSTL data
        (``_expected_one_wstl_duplicate_form``) is not defined.
        """
        if not self._expected_one_duplicate_form:
            self.skipTest('self._expected_one_duplicate_wstl is not defined')
        async with self.client.request('GET',
                                       (self._href / self._id() / 'duplicator').path,
                                       headers=self._headers) as obj:
            self._assert_equal_ordered(_version_info_removed(self._expected_one_duplicate_form), _version_info_removed(await obj.json()))

