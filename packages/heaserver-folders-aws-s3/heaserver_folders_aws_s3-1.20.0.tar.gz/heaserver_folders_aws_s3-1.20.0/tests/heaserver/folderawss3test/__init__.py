from heaserver.service import heaobjectsupport
from aiohttp import web, ClientSession
from aiohttp.typedefs import LooseHeaders
from typing import Union, Optional
from collections.abc import Mapping, Sequence, AsyncIterator
from heaobject.root import DesktopObject, DesktopObjectTypeVar, Permission, PermissionContext
actual_get_attribute_permissions = PermissionContext.get_attribute_permissions
async def mock_get_attribute_permissions(self, obj: DesktopObject, attr: str) -> list[Permission]:
    return [Permission.VIEWER] if attr == 'display_name' else await actual_get_attribute_permissions(self, obj, attr)

PermissionContext.get_attribute_permissions = mock_get_attribute_permissions
from heaobject.person import Group
from heaobject.group import SUPERADMIN_GROUP
from heaobject.activity import DesktopObjectSummaryView
from heaobject.bucket import AWSBucket
from yarl import URL
async def _mock_type_to_resource_url(request: web.Request, type_or_type_name: Union[str, type[DesktopObject]],
                                     parameters: Optional[Mapping[str, Union[Sequence[Union[int, float, complex, str]], Mapping[str, Union[int, float, complex, str]], tuple[str, Union[int, float, complex, str]], int, float, complex, str]]] = None,
                                     **kwargs: Union[Sequence[Union[int, float, complex, str]], Mapping[str, Union[int, float, complex, str]], tuple[str, Union[int, float, complex, str]], int, float, complex, str]) -> str:
    if type_or_type_name in (DesktopObjectSummaryView, DesktopObjectSummaryView.get_type_name()):
        return 'http://localhost:8080/desktopobjectsummaryviews'
    elif type_or_type_name in (AWSBucket, AWSBucket.get_type_name()):
        return 'http://localhost:8080/volumes'
    elif type_or_type_name in (Group, Group.get_type_name()):
        return 'http://localhost:8080/groups'
    else:
        raise ValueError(f'Unexpected type {type_or_type_name}')
heaobjectsupport.type_to_resource_url = _mock_type_to_resource_url
from heaserver.service import client
async def _mock_get_all(app: web.Application, url: Union[URL, str], type_: type[DesktopObjectTypeVar],
                        query_params: Optional[Mapping[str, str]] = None,
                        headers: LooseHeaders | None = None,
                        client_session: ClientSession | None = None) -> AsyncIterator[DesktopObjectTypeVar]:
    url_str = str(url)
    if url_str.startswith('http://localhost:8080/desktopobjectsummaryviews'):
        view: DesktopObjectSummaryView = DesktopObjectSummaryView()
        view.id = '1'
        view.name = 'test1'
        yield view
    elif url_str.startswith('http://localhost:8080/volumes'):
        bucket: AWSBucket = AWSBucket()
        bucket.id = 'hci-foundation-1'
        bucket.name = 'hci-foundation-1'
        yield bucket
    elif url_str.startswith('http://localhost:8080/groups'):
        group: Group = Group()
        group.id = '1'
        group.group = SUPERADMIN_GROUP
        yield group
    else:
        raise ValueError(f'Unexpected URL {url}')
client.get_all = _mock_get_all

async def _mock_get(app: web.Application, url: Union[URL, str],
              type_or_obj: DesktopObjectTypeVar | type[DesktopObjectTypeVar],
              query_params: Optional[Mapping[str, str]] = None,
              headers: LooseHeaders | None = None,
              client_session: ClientSession | None = None) -> DesktopObjectTypeVar | None:
    url_str = str(url)
    if url_str.startswith('http://localhost:8080/groups'):
        group: Group = Group()
        group.id = '1'
        group.group = SUPERADMIN_GROUP
        return group
    raise ValueError(f'Unexpected URL {url}')
client.get = _mock_get
