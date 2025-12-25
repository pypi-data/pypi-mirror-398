from .folderawss3testcase import AWSS3ItemTestCase, AWSS3FolderTestCase
from .projectawss3testcase import AWSS3ProjectTestCase
from heaserver.service.testcase.mixin import DeleteMixin, GetAllMixin, GetOneMixin, PutMixin, PostMixin
from heaobject.awss3key import encode_key
from heaserver.service.representor import nvpjson
from aiohttp import hdrs



class TestGetFolders(AWSS3FolderTestCase, GetAllMixin):
    async def test_options_status(self):
        """Checks if an OPTIONS request for all the folders succeeds with status 200."""
        obj = await self.client.request('OPTIONS',
                                        (self._href / '').path,
                                        headers=self._headers)
        self.assertEqual(200, obj.status)

    async def test_options(self):
        """
        Checks if the "Allow" header in a response to an OPTIONS request for all the folders contains GET, POST,
        HEAD, and OPTIONS and contains neither PUT nor DELETE.
        """
        obj = await self.client.request('OPTIONS',
                                        (self._href / '').path,
                                        headers=self._headers)
        if not obj.ok:
            self.fail(f'OPTIONS request failed: {await obj.text()}')
        if allow_hdr := obj.headers.get(hdrs.ALLOW):
            allow = {method.strip() for method in allow_hdr.split(',')}
        else:
            self.fail('No allow header')
        self.assertEqual({'GET', 'DELETE', 'HEAD', 'OPTIONS'}, allow)

    async def test_methods_not_allowed(self) -> None:
        """
        Checks if all the methods not in the "Allow" header in a response to an OPTIONS request for all the folders
        fail with status 405.
        """
        obj = await self.client.request('OPTIONS',
                                        (self._href / '').path,
                                        headers=self._headers)
        if not obj.ok:
            self.fail(f'OPTIONS request failed: {await obj.text()}')
        if allow_hdr := obj.headers.get(hdrs.ALLOW):
            allowed_methods = {method.strip() for method in allow_hdr.split(',')}
        else:
            self.fail('No allow header')
        all_methods = {'HEAD', 'OPTIONS', 'PUT', 'GET', 'DELETE'}
        prohibited_methods = all_methods - allowed_methods
        resps = {}
        for prohibited in prohibited_methods:
            obj = await self.client.request(prohibited,
                                            (self._href / '').path,
                                            headers=self._headers)
            resps |= {prohibited: obj.status}
        self.assertEqual(dict(zip(prohibited_methods, [405] * len(prohibited_methods))), resps)


class TestGetFolder(AWSS3FolderTestCase, GetOneMixin):
    async def test_options_status(self):
        """Checks if an OPTIONS request for a single folder succeeds with status 200."""
        obj = await self.client.request('OPTIONS',
                                        (self._href / self._id()).path,
                                        headers=self._headers)
        self.assertEqual(200, obj.status)

    async def test_options(self):
        """
        Checks if the "Allow" header in a response to an OPTIONS request for a single folder contains GET, POST,
        HEAD, and OPTIONS and contains neither PUT nor DELETE.
        """
        obj = await self.client.request('OPTIONS',
                                        (self._href / self._id()).path,
                                        headers=self._headers)
        if not obj.ok:
            self.fail(f'OPTIONS request failed: {await obj.text()}')
        if allow_hdr := obj.headers.get(hdrs.ALLOW):
            allow = {method.strip() for method in allow_hdr.split(',')}
        else:
            self.fail('No allow header')
        self.assertEqual({'GET', 'PUT', 'DELETE', 'HEAD', 'OPTIONS'}, allow)

    async def test_methods_not_allowed(self) -> None:
        """
        Checks if all the methods not in the "Allow" header in a response to an OPTIONS request for a single folder
        fail with status 405.
        """
        obj = await self.client.request('OPTIONS',
                                        (self._href / self._id()).path,
                                        headers=self._headers)
        if not obj.ok:
            self.fail(f'OPTIONS request failed: {await obj.text()}')
        if allow_hdr := obj.headers.get(hdrs.ALLOW):
            allowed_methods = {method.strip() for method in allow_hdr.split(',')}
        else:
            self.fail('No allow header')
        all_methods = {'HEAD', 'OPTIONS', 'POST', 'PUT', 'GET', 'DELETE'}
        prohibited_methods = all_methods - allowed_methods
        resps = {}
        for prohibited in prohibited_methods:
            obj = await self.client.request(prohibited,
                                            (self._href / self._id()).path,
                                            headers=self._headers)
            resps |= {prohibited: obj.status}
        self.assertEqual(dict(zip(prohibited_methods, [405] * len(prohibited_methods))), resps)

    async def test_copy_status(self):
        href = f'/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3folders/{encode_key("TestFolder/")}/duplicator'
        body = {'template':
            {'data': [
                {'name': 'target',
                 'value': f'http://localhost:8080/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3folders/{encode_key("TestFolder2/")}'}]}}
        async with self.client.post(href, json=body) as resp:
            self.assertEqual(201, resp.status, await resp.text())

    async def test_copy_async_status(self):
        href = f'/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3folders/{encode_key("TestFolder/")}/duplicatorasync'
        body = {'template':
            {'data': [
                {'name': 'target',
                 'value': f'http://localhost:8080/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3folders/{encode_key("TestFolder2/")}'}]}}
        async with self.client.post(href, json=body) as resp:
            status = resp.status
            url = resp.url
            while status == 202:
                async with self.client.get(url.path) as resp2:
                    status = resp2.status
            self.assertEqual(201, status, await resp.text())

    async def test_copy(self):
        href = f'/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3folders/{encode_key("TestFolder/")}/duplicator'
        body = {'template':
            {'data': [
                {'name': 'target',
                 'value': f'http://localhost:8080/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3folders/{encode_key("TestFolder2/")}'}]}}
        async with self.client.post(href, json=body) as resp:
            if resp.status != 201:
                self.fail(await resp.text())

        href2 = f'/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3folders/{encode_key("TestFolder2/TestFolder/")}'
        async with self.client.get(href2, headers={hdrs.ACCEPT: nvpjson.MIME_TYPE}) as resp:
            expected = [{'bucket_id': 'arp-scale-2-cloud-bucket-with-tags11', 'created': None,
                         'derived_by': None, 'derived_from': [], 'description': None, 'display_name': 'TestFolder',
                         'id': 'VGVzdEZvbGRlcjIvVGVzdEZvbGRlci8=', 'invites': [],
                         'instance_id': 'heaobject.folder.AWSS3Folder^VGVzdEZvbGRlcjIvVGVzdEZvbGRlci8=',
                         'key': 'TestFolder2/TestFolder/', 'mime_type': 'application/x.folder',
                         'modified': None, 'name': 'VGVzdEZvbGRlcjIvVGVzdEZvbGRlci8=',
                         'owner': 'system|aws',
                         'path': '/arp-scale-2-cloud-bucket-with-tags11/TestFolder2/TestFolder/',
                         's3_uri': 's3://arp-scale-2-cloud-bucket-with-tags11/TestFolder2/TestFolder/',
                         'source': 'AWS S3',
                         'source_detail': 'AWS S3',
                         'type': 'heaobject.folder.AWSS3Folder',
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
                        'type_display_name': 'Folder',
                        'resource_type_and_id': 'arp-scale-2-cloud-bucket-with-tags11/TestFolder2/TestFolder/',
                        'super_admin_default_permissions': [],
                        'dynamic_permission_supported': False}]
            self._assert_equal_ordered(expected, await resp.json())

    async def test_copy_async(self):
        href = f'/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3folders/{encode_key("TestFolder/")}/duplicatorasync'
        body = {'template':
            {'data': [
                {'name': 'target',
                 'value': f'http://localhost:8080/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3folders/{encode_key("TestFolder2/")}'}]}}
        async with self.client.post(href, json=body) as resp:
            status = resp.status
            url = resp.url
            while status == 202:
                async with self.client.get(url.path) as resp2:
                    status = resp2.status
            if status != 201:
                self.fail(await resp.text())

        href2 = f'/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3folders/{encode_key("TestFolder2/TestFolder/")}'
        async with self.client.get(href2, headers={hdrs.ACCEPT: nvpjson.MIME_TYPE}) as resp:
            expected = [{'bucket_id': 'arp-scale-2-cloud-bucket-with-tags11', 'created': None,
                         'derived_by': None, 'derived_from': [], 'description': None, 'display_name': 'TestFolder',
                         'id': 'VGVzdEZvbGRlcjIvVGVzdEZvbGRlci8=', 'invites': [],
                         'instance_id': 'heaobject.folder.AWSS3Folder^VGVzdEZvbGRlcjIvVGVzdEZvbGRlci8=',
                         'key': 'TestFolder2/TestFolder/', 'mime_type': 'application/x.folder',
                         'modified': None, 'name': 'VGVzdEZvbGRlcjIvVGVzdEZvbGRlci8=',
                         'owner': 'system|aws',
                         'path': '/arp-scale-2-cloud-bucket-with-tags11/TestFolder2/TestFolder/',
                         's3_uri': 's3://arp-scale-2-cloud-bucket-with-tags11/TestFolder2/TestFolder/',
                         'source': 'AWS S3',
                         'source_detail': 'AWS S3',
                         'type': 'heaobject.folder.AWSS3Folder',
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
                         'type_display_name': 'Folder',
                         'resource_type_and_id': 'arp-scale-2-cloud-bucket-with-tags11/TestFolder2/TestFolder/',
                         'super_admin_default_permissions': [],
                         'dynamic_permission_supported': False
                         }]
            self._assert_equal_ordered(expected, await resp.json())


class TestGetItems(AWSS3ItemTestCase, GetAllMixin):
    async def test_options_status(self):
        """Checks if an OPTIONS request for all the folder items succeeds with status 200."""
        obj = await self.client.request('OPTIONS',
                                        (self._href / '').path,
                                        headers=self._headers)
        self.assertEqual(200, obj.status)

    async def test_options(self):
        """
        Checks if the "Allow" header in a response to an OPTIONS request for all the folder items contains GET, POST,
        HEAD, and OPTIONS and contains neither PUT nor DELETE.
        """
        obj = await self.client.request('OPTIONS',
                                        (self._href / '').path,
                                        headers=self._headers)
        if not obj.ok:
            self.fail(f'OPTIONS request failed: {await obj.text()}')
        if allow_hdr := obj.headers.get(hdrs.ALLOW):
            allow = {method.strip() for method in allow_hdr.split(',')}
        else:
            self.fail('No allow header')
        self.assertEqual({'GET', 'POST', 'DELETE', 'HEAD', 'OPTIONS'}, allow)

    async def test_methods_not_allowed(self) -> None:
        """
        Checks if all the methods not in the "Allow" header in a response to an OPTIONS request for all the folder
        items fail with status 405.
        """
        obj = await self.client.request('OPTIONS',
                                        (self._href / '').path,
                                        headers=self._headers)
        if not obj.ok:
            self.fail(f'OPTIONS request failed: {await obj.text()}')
        if allow_hdr := obj.headers.get(hdrs.ALLOW):
            allowed_methods = {method.strip() for method in allow_hdr.split(',')}
        else:
            self.fail('No allow header')
        all_methods = {'HEAD', 'OPTIONS', 'POST', 'PUT', 'GET', 'DELETE'}
        prohibited_methods = all_methods - allowed_methods
        resps = {}
        for prohibited in prohibited_methods:
            obj = await self.client.request(prohibited,
                                            (self._href / '').path,
                                            headers=self._headers)
            resps |= {prohibited: obj.status}
        self.assertEqual(dict(zip(prohibited_methods, [405] * len(prohibited_methods))), resps)


class TestGetItem(AWSS3ItemTestCase, GetOneMixin):
    async def test_options_status(self):
        """Checks if an OPTIONS request for a single folder item succeeds with status 200."""
        obj = await self.client.request('OPTIONS',
                                        (self._href / self._id()).path,
                                        headers=self._headers)
        self.assertEqual(200, obj.status)

    async def test_options(self):
        """
        Checks if the "Allow" header in a response to an OPTIONS request for a single folder item contains GET, POST,
        HEAD, and OPTIONS and contains neither PUT nor DELETE.
        """
        obj = await self.client.request('OPTIONS',
                                        (self._href / self._id()).path,
                                        headers=self._headers)
        if not obj.ok:
            self.fail(f'OPTIONS request failed: {await obj.text()}')
        if allow_hdr := obj.headers.get(hdrs.ALLOW):
            allow = {method.strip() for method in allow_hdr.split(',')}
        else:
            self.fail('No allow header')
        self.assertEqual({'GET', 'DELETE', 'HEAD', 'OPTIONS'}, allow)

    async def test_methods_not_allowed(self) -> None:
        """
        Checks if all the methods not in the "Allow" header in a response to an OPTIONS request for a single folder item
        fail with status 405.
        """
        obj = await self.client.request('OPTIONS',
                                        (self._href / self._id()).path,
                                        headers=self._headers)
        if not obj.ok:
            self.fail(f'OPTIONS request failed: {await obj.text()}')
        if allow_hdr := obj.headers.get(hdrs.ALLOW):
            allowed_methods = {method.strip() for method in allow_hdr.split(',')}
        else:
            self.fail('No allow header')
        all_methods = {'HEAD', 'OPTIONS', 'POST', 'PUT', 'GET', 'DELETE'}
        prohibited_methods = all_methods - allowed_methods
        resps = {}
        for prohibited in prohibited_methods:
            obj = await self.client.request(prohibited,
                                            (self._href / self._id()).path,
                                            headers=self._headers)
            resps |= {prohibited: obj.status}
        self.assertEqual(dict(zip(prohibited_methods, [405] * len(prohibited_methods))), resps)

    async def test_get_by_name(self) -> None:
        self.skipTest('folder items do not support get by name')

    async def test_get_by_name_invalid_name(self):
        self.skipTest('GET by name not supported for AWS S3 folder items')


class TestGetProjects(AWSS3ProjectTestCase, GetAllMixin):
    async def test_options_status(self):
        """Checks if an OPTIONS request for all the folders succeeds with status 200."""
        obj = await self.client.request('OPTIONS',
                                        (self._href / '').path,
                                        headers=self._headers)
        self.assertEqual(200, obj.status)

    async def test_options(self):
        """
        Checks if the "Allow" header in a response to an OPTIONS request for all the folders contains GET, POST,
        HEAD, and OPTIONS and contains neither PUT nor DELETE.
        """
        obj = await self.client.request('OPTIONS',
                                        (self._href / '').path,
                                        headers=self._headers)
        if not obj.ok:
            self.fail(f'OPTIONS request failed: {await obj.text()}')
        if allow_hdr := obj.headers.get(hdrs.ALLOW):
            allow = {method.strip() for method in allow_hdr.split(',')}
        else:
            self.fail('No allow header')
        self.assertEqual({'GET', 'DELETE', 'HEAD', 'OPTIONS'}, allow)

    async def test_methods_not_allowed(self) -> None:
        """
        Checks if all the methods not in the "Allow" header in a response to an OPTIONS request for all the folders
        fail with status 405.
        """
        obj = await self.client.request('OPTIONS',
                                        (self._href / '').path,
                                        headers=self._headers)
        if not obj.ok:
            self.fail(f'OPTIONS request failed: {await obj.text()}')
        if allow_hdr := obj.headers.get(hdrs.ALLOW):
            allowed_methods = {method.strip() for method in allow_hdr.split(',')}
        else:
            self.fail('No allow header')
        all_methods = {'HEAD', 'OPTIONS', 'PUT', 'GET', 'DELETE'}
        prohibited_methods = all_methods - allowed_methods
        resps = {}
        for prohibited in prohibited_methods:
            obj = await self.client.request(prohibited,
                                            (self._href / '').path,
                                            headers=self._headers)
            resps |= {prohibited: obj.status}
        self.assertEqual(dict(zip(prohibited_methods, [405] * len(prohibited_methods))), resps)


class TestGetProject(AWSS3ProjectTestCase, GetOneMixin):
    async def test_options_status(self):
        """Checks if an OPTIONS request for a single folder succeeds with status 200."""
        obj = await self.client.request('OPTIONS',
                                        (self._href / self._id()).path,
                                        headers=self._headers)
        self.assertEqual(200, obj.status)

    async def test_options(self):
        """
        Checks if the "Allow" header in a response to an OPTIONS request for a single folder contains GET, POST,
        HEAD, and OPTIONS and contains neither PUT nor DELETE.
        """
        obj = await self.client.request('OPTIONS',
                                        (self._href / self._id()).path,
                                        headers=self._headers)
        if not obj.ok:
            self.fail(f'OPTIONS request failed: {await obj.text()}')
        if allow_hdr := obj.headers.get(hdrs.ALLOW):
            allow = {method.strip() for method in allow_hdr.split(',')}
        else:
            self.fail('No allow header')
        self.assertEqual({'GET', 'PUT', 'DELETE', 'HEAD', 'OPTIONS'}, allow)

    async def test_methods_not_allowed(self) -> None:
        """
        Checks if all the methods not in the "Allow" header in a response to an OPTIONS request for a single folder
        fail with status 405.
        """
        obj = await self.client.request('OPTIONS',
                                        (self._href / self._id()).path,
                                        headers=self._headers)
        if not obj.ok:
            self.fail(f'OPTIONS request failed: {await obj.text()}')
        if allow_hdr := obj.headers.get(hdrs.ALLOW):
            allowed_methods = {method.strip() for method in allow_hdr.split(',')}
        else:
            self.fail('No allow header')
        all_methods = {'HEAD', 'OPTIONS', 'POST', 'PUT', 'GET', 'DELETE'}
        prohibited_methods = all_methods - allowed_methods
        resps = {}
        for prohibited in prohibited_methods:
            obj = await self.client.request(prohibited,
                                            (self._href / self._id()).path,
                                            headers=self._headers)
            resps |= {prohibited: obj.status}
        self.assertEqual(dict(zip(prohibited_methods, [405] * len(prohibited_methods))), resps)

    async def test_copy_status(self):
        href = f'/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3projects/{encode_key("TestFolder/TestProject/")}/duplicator'
        body = {'template':
            {'data': [
                {'name': 'target',
                 'value': f'http://localhost:8080/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3projects/{encode_key("TestFolder/TestProject2/")}'}]}}
        async with self.client.post(href, json=body) as resp:
            self.assertEqual(201, resp.status, await resp.text())

    async def test_copy(self):
        href = f'/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3projects/{encode_key("TestFolder/TestProject/")}/duplicator'
        body = {'template':
            {'data': [
                {'name': 'target',
                 'value': f'http://localhost:8080/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3projects/{encode_key("TestFolder/TestProject2/")}'}]}}
        async with self.client.post(href, json=body) as resp:
            if resp.status != 201:
                self.fail(await resp.text())

        href2 = f'/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3projects/{encode_key("TestFolder/TestProject2/")}'
        async with self.client.get(href2, headers={hdrs.ACCEPT: nvpjson.MIME_TYPE}) as resp:
            expected = [{'bucket_id': 'arp-scale-2-cloud-bucket-with-tags11', 'created': None,
                         'derived_by': None, 'derived_from': [], 'description': None, 'display_name': 'TestProject2',
                         'id': 'VGVzdEZvbGRlci9UZXN0UHJvamVjdDIv', 'invites': [],
                         'instance_id': 'heaobject.project.AWSS3Project^VGVzdEZvbGRlci9UZXN0UHJvamVjdDIv',
                         'key': 'TestFolder/TestProject2/', 'mime_type': 'application/x.project',
                         'modified': None, 'name': 'VGVzdEZvbGRlci9UZXN0UHJvamVjdDIv',
                         'owner': 'system|aws',
                         's3_uri': 's3://arp-scale-2-cloud-bucket-with-tags11/TestFolder/TestProject2/',
                         'source': 'AWS S3', 'source_detail': 'AWS S3', 'type': 'heaobject.project.AWSS3Project',
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
                        'type_display_name': 'Project',
                        'resource_type_and_id': 'arp-scale-2-cloud-bucket-with-tags11/TestFolder/TestProject2/',
                        'super_admin_default_permissions': [],
                        'dynamic_permission_supported': False}]
            self._assert_equal_ordered(expected, await resp.json())

    async def test_not_folder(self):
        href = f'/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3folders/{encode_key("TestFolder/TestProject/")}'
        async with self.client.get(href) as resp:
            self.assertEqual(404, resp.status)

    async def test_not_project(self):
        href = f'/volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3projects/{encode_key("TestFolder/")}'
        async with self.client.get(href) as resp:
            self.assertEqual(404, resp.status)


# class TestGetProjectItems(AWSS3ProjectItemTestCase, GetAllMixin):
#     async def test_options_status(self):
#         """Checks if an OPTIONS request for all the folder items succeeds with status 200."""
#         obj = await self.client.request('OPTIONS',
#                                         (self._href / '').path,
#                                         headers=self._headers)
#         self.assertEqual(200, obj.status)

#     async def test_options(self):
#         """
#         Checks if the "Allow" header in a response to an OPTIONS request for all the folder items contains GET, POST,
#         HEAD, and OPTIONS and contains neither PUT nor DELETE.
#         """
#         obj = await self.client.request('OPTIONS',
#                                         (self._href / '').path,
#                                         headers=self._headers)
#         if not obj.ok:
#             self.fail(f'OPTIONS request failed: {await obj.text()}')
#         if allow_hdr := obj.headers.get(hdrs.ALLOW):
#             allow = {method.strip() for method in allow_hdr.split(',')}
#         else:
#             self.fail('No allow header')
#         self.assertEqual({'GET', 'POST', 'DELETE', 'HEAD', 'OPTIONS'}, allow)

#     async def test_methods_not_allowed(self) -> None:
#         """
#         Checks if all the methods not in the "Allow" header in a response to an OPTIONS request for all the folder
#         items fail with status 405.
#         """
#         obj = await self.client.request('OPTIONS',
#                                         (self._href / '').path,
#                                         headers=self._headers)
#         if not obj.ok:
#             self.fail(f'OPTIONS request failed: {await obj.text()}')
#         if allow_hdr := obj.headers.get(hdrs.ALLOW):
#             allowed_methods = {method.strip() for method in allow_hdr.split(',')}
#         else:
#             self.fail('No allow header')
#         all_methods = {'HEAD', 'OPTIONS', 'POST', 'PUT', 'GET', 'DELETE'}
#         prohibited_methods = all_methods - allowed_methods
#         resps = {}
#         for prohibited in prohibited_methods:
#             obj = await self.client.request(prohibited,
#                                             (self._href / '').path,
#                                             headers=self._headers)
#             resps |= {prohibited: obj.status}
#         self.assertEqual(dict(zip(prohibited_methods, [405] * len(prohibited_methods))), resps)


# class TestGetProjectItem(AWSS3ProjectItemTestCase, GetOneMixin):
#     async def test_options_status(self):
#         """Checks if an OPTIONS request for a single folder item succeeds with status 200."""
#         obj = await self.client.request('OPTIONS',
#                                         (self._href / self._id()).path,
#                                         headers=self._headers)
#         self.assertEqual(200, obj.status)

#     async def test_options(self):
#         """
#         Checks if the "Allow" header in a response to an OPTIONS request for a single folder item contains GET, POST,
#         HEAD, and OPTIONS and contains neither PUT nor DELETE.
#         """
#         obj = await self.client.request('OPTIONS',
#                                         (self._href / self._id()).path,
#                                         headers=self._headers)
#         if not obj.ok:
#             self.fail(f'OPTIONS request failed: {await obj.text()}')
#         if allow_hdr := obj.headers.get(hdrs.ALLOW):
#             allow = {method.strip() for method in allow_hdr.split(',')}
#         else:
#             self.fail('No allow header')
#         self.assertEqual({'GET', 'DELETE', 'HEAD', 'OPTIONS'}, allow)

#     async def test_methods_not_allowed(self) -> None:
#         """
#         Checks if all the methods not in the "Allow" header in a response to an OPTIONS request for a single folder item
#         fail with status 405.
#         """
#         obj = await self.client.request('OPTIONS',
#                                         (self._href / self._id()).path,
#                                         headers=self._headers)
#         if not obj.ok:
#             self.fail(f'OPTIONS request failed: {await obj.text()}')
#         if allow_hdr := obj.headers.get(hdrs.ALLOW):
#             allowed_methods = {method.strip() for method in allow_hdr.split(',')}
#         else:
#             self.fail('No allow header')
#         all_methods = {'HEAD', 'OPTIONS', 'POST', 'PUT', 'GET', 'DELETE'}
#         prohibited_methods = all_methods - allowed_methods
#         resps = {}
#         for prohibited in prohibited_methods:
#             obj = await self.client.request(prohibited,
#                                             (self._href / self._id()).path,
#                                             headers=self._headers)
#             resps |= {prohibited: obj.status}
#         self.assertEqual(dict(zip(prohibited_methods, [405] * len(prohibited_methods))), resps)

#     async def test_get_by_name(self) -> None:
#         self.skipTest('Project items do not support get by name')

#     async def test_get_by_name_invalid_name(self):
#         self.skipTest('GET by name not supported for AWS S3 project items')


# class TestPostProjectItem(AWSS3ProjectItemTestCase, PostMixin):
#     pass


# class TestPutProjectItem(AWSS3ProjectItemTestCase, PutMixin):
#     pass
