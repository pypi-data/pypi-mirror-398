from copy import deepcopy
from heaserver.service.representor import cj
from heaserver.service.representor import wstljson
from .fileawss3testcase import AWSS3FileTestCase
from .filemimetypetestcase import AWSS3FileContentTypeTestCase, db_values
from heaserver.service.testcase.mixin import DeleteMixin, GetAllMixin, GetOneMixin, _ordered
from heaserver.service.db.database import get_collection_key_from_name
from aiohttp import hdrs
import os


def _version_info_removed(data):
    result = deepcopy(data)
    for item in result[0]['collection']['items']:
        item['data'] = [d for d in item['data'] if d['name'] != 'version']
    return result


def _version_info_removed_wstl(data):
    result = deepcopy(data)
    for data_ in result[0]['wstl']['data']:
        if 'version' in data_:
            del data_['version']
    return result


class TestDeleteFile(AWSS3FileTestCase, DeleteMixin):
    pass


class TestGetFiles(AWSS3FileTestCase, GetAllMixin):

    async def test_get_all_json(self) -> None:
        """
        Checks if a GET request for all the items as JSON succeeds and returns the expected value
        (``_expected_all``).
        """
        if 'XDG_DATA_HOME' not in os.environ:
            self.skipTest("Mimetype DB only works in Linux Environments")
        async with self.client.request('GET',
                                       (self._href / '').path,
                                       headers=self._headers) as obj:
            self.assertEqual(_ordered(_version_info_removed(self._expected_all)), _ordered(_version_info_removed(await obj.json())))

    async def test_get_all_wstl(self) -> None:
        """
        Checks if a GET request for all the items as WeSTL JSON succeeds and returns the expected value
        (``_expected_all_wstl``). The test is skipped if the expected WeSTL JSON (``_expected_all_wstl``) is not
        defined.
        """

        if 'XDG_DATA_HOME' not in os.environ:
            self.skipTest("Mimetype DB only works in Linux Environments")
        if not self._expected_all_wstl:
            self.skipTest('self._expected_all_wstl is not defined')
        async with self.client.request('GET',
                                       (self._href / '').path,
                                       headers={**self._headers, hdrs.ACCEPT: wstljson.MIME_TYPE}) as obj:
            self.assertEqual(_ordered(_version_info_removed_wstl(self._expected_all_wstl)), _ordered(_version_info_removed_wstl(await obj.json())))


class TestGetFile(AWSS3FileTestCase, GetOneMixin):
    # Currently backs 200 because it uses the same request handler as the normal get
    # async def test_get_status_opener_choices(self) -> None:
    #     """Checks if a GET request for the opener for a file succeeds with status 300."""
    #     obj = await self.client.request('GET',
    #                                     (self._href / self._id() / 'opener').path,
    #                                     headers=self._headers)
    #     self.assertEqual(300, obj.status)

    async def test_get_status_opener_hea_default_exists(self) -> None:
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

    async def test_get(self) -> None:
        """Checks if a GET request succeeds and returns the expected JSON (``_expected_one``)."""
        if 'XDG_DATA_HOME' not in os.environ:
            self.skipTest("Mimetype DB only works in Linux Environments")
        async with self.client.request('GET',
                                       (self._href / self._id()).path,
                                       headers=self._headers) as obj:
            self._assert_equal_ordered(_version_info_removed(self._expected_one), _version_info_removed(await obj.json()))

    async def test_get_by_name(self):
        """
        Checks if a GET request for the object with the expected name in ``_expected_one_wstl`` succeeds and returns the
        expected data. The test is skipped if the object doesn't have a name.
        """
        if 'XDG_DATA_HOME' not in os.environ:
            self.skipTest("Mimetype DB only works in Linux Environments")
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
        if 'XDG_DATA_HOME' not in os.environ:
            self.skipTest("Mimetype DB only works in Linux Environments")
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
        if 'XDG_DATA_HOME' not in os.environ:
            self.skipTest("Mimetype DB only works in Linux Environments")
        if not self._expected_one_duplicate_form:
            self.skipTest('self._expected_one_duplicate_wstl is not defined')
        async with self.client.request('GET',
                                       (self._href / self._id() / 'duplicator').path,
                                       headers=self._headers) as obj:
            self._assert_equal_ordered(_version_info_removed(self._expected_one_duplicate_form), _version_info_removed(await obj.json()))


class TestGetFileCheckContentType(AWSS3FileContentTypeTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ids = {'.' + x['display_name'].split('.', maxsplit=1)[-1]: x['id'] for x in db_values[self._coll]}

    def setUp(self):
        super().setUp()

        if 'XDG_DATA_HOME' not in os.environ:
            self.skipTest("Mimetype DB only works in Linux Environments")

    async def test_get_content_type_fastq(self) -> None:
        """
        Checks if the response to a GET request for the content of an AWS S3 File object with the file extension
        ".fastq" has the Content-Type header equal "application/x.fastq".
        """
        async with self.client.request('GET',
                                       (self._href / self.ids['.fastq'] / 'content').path,
                                       headers=self._headers) as resp:
            self.assertEqual('application/x-fastq', resp.headers.get(hdrs.CONTENT_TYPE))

    async def test_get_content_type_fasta(self) -> None:
        """
        Checks if the response to a GET request for the content of an AWS S3 File object with the file extension
        ".ffn" has the Content-Type header equal "application/x.fasta".
        """
        async with self.client.request('GET',
                                       (self._href / self.ids['.ffn'] / 'content').path,
                                       headers=self._headers) as resp:
            self.assertEqual('application/x-fasta', resp.headers.get(hdrs.CONTENT_TYPE))

    # mimetypes does not support double file extensions
    # async def test_get_content_type_bambai(self) -> None:
    #     """
    #     Checks if the response to a GET request for the content of an AWS S3 File object with the file extension
    #     ".bam.bai" has the Content-Type header equal "application/x.bambai".
    #     """
    #     async with self.client.request('GET',
    #                                    (self._href / self.ids['.bam.bai'] / 'content').path,
    #                                    headers=self._headers) as resp:
    #         self.assertEqual('application/x.bambai', resp.headers.get(hdrs.CONTENT_TYPE))

    async def test_get_content_type_no_file_extension(self) -> None:
        """
        Checks if the response to a GET request for the content of an AWS S3 File object with no file extension has
        the Content-Type header equal "application/octet-stream".
        """
        async with self.client.request('GET',
                                       (self._href / self.ids['.nofileextension'] / 'content').path,
                                       headers=self._headers) as resp:
            self.assertEqual('application/octet-stream', resp.headers.get(hdrs.CONTENT_TYPE))
