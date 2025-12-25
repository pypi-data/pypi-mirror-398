from .folderawss3testcase import AWSS3FolderTestCase, AWSS3ItemTestCase
from .projectawss3testcase import AWSS3ProjectTestCase, AWSS3ProjectItemTestCase
from heaserver.service.testcase.mixin import GetOneMixin, GetAllMixin, PostMixin, PutMixin, DeleteMixin

# Folders
class TestGetAWSS3Folder(AWSS3FolderTestCase, GetOneMixin):  # type: ignore
    pass


class TestGetAllAWSS3Folders(AWSS3ItemTestCase, GetAllMixin):  # type: ignore
    pass


class TestPostAWSS3Folder(AWSS3FolderTestCase, PostMixin):  # type: ignore
    pass


class TestPutAWSS3Folder(AWSS3FolderTestCase, PutMixin):  # type: ignore
    pass


class TestDeleteAWSS3Folder(AWSS3FolderTestCase, DeleteMixin):  # type: ignore
    pass


class TestGetAWSS3Item(AWSS3ItemTestCase, GetOneMixin):  # type: ignore
    async def test_get_by_name(self) -> None:
        self.skipTest('folder items do not support get by name')

    async def test_get_by_name_invalid_name(self):
        self.skipTest('GET by name not supported for AWS S3 folder items')


class TestGetAllAWSS3Items(AWSS3ItemTestCase, GetAllMixin):  # type: ignore
    pass


class TestPostAWSS3Item(AWSS3ItemTestCase, PostMixin):  # type: ignore
    pass


class TestPutAWSS3Item(AWSS3ItemTestCase, PutMixin):  # type: ignore
    pass


# Projects
class TestGetAWSS3Project(AWSS3ProjectTestCase, GetOneMixin):  # type: ignore
    pass


class TestGetAllAWSS3Projects(AWSS3ProjectTestCase, GetAllMixin):  # type: ignore
    pass


class TestPostAWSS3Project(AWSS3ProjectTestCase, PostMixin):  # type: ignore
    pass


class TestPutAWSS3Project(AWSS3ProjectTestCase, PutMixin):  # type: ignore
    pass


class TestDeleteAWSS3Project(AWSS3ProjectTestCase, DeleteMixin):  # type: ignore
    pass


class TestGetAWSS3ProjectItem(AWSS3ProjectItemTestCase, GetOneMixin):  # type: ignore
    async def test_get_by_name(self) -> None:
        self.skipTest('folder items do not support get by name')

    async def test_get_by_name_invalid_name(self):
        self.skipTest('GET by name not supported for AWS S3 folder items')


class TestGetAllAWSS3ProjectItems(AWSS3ItemTestCase, GetAllMixin):  # type: ignore
    pass


class TestPostAWSS3ProjectItem(AWSS3ProjectItemTestCase, PostMixin):  # type: ignore
    pass


class TestPutAWSS3ProjectItem(AWSS3ProjectItemTestCase, PutMixin):  # type: ignore
    pass
