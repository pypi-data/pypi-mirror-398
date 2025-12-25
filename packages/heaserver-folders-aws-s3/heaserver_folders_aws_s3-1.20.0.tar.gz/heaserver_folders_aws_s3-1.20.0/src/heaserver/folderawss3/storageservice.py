"""
The HEA Server storage Microservice provides ...
"""

from heaserver.service import response, client
from heaserver.service.runner import init_cmd_line, routes, start, web
from heaserver.service.db import aws
from heaserver.service.wstl import builder_factory, action
from heaserver.service.appproperty import HEA_BACKGROUND_TASKS
from heaserver.service.sources import AWS_S3
from heaserver.service.oidcclaimhdrs import SUB
from heaserver.service.customhdrs import PREFER, PREFERENCE_RESPOND_ASYNC
from heaserver.service.util import now, filter_mapping, queued_processing
from heaserver.service.heaobjectsupport import type_to_resource_url
from heaobject.user import NONE_USER, AWS_USER
from heaobject.root import PermissionContext, ViewerPermissionContext, Share, ShareImpl, Permission, to_dict
from heaobject.storage import AWSS3Storage
from heaobject.bucket import AWSBucket
from heaobject.folder import AWSS3BucketItem
from botocore.exceptions import ClientError
from collections import defaultdict
from collections.abc import Mapping, Iterable, Iterator, AsyncIterator
from datetime import datetime
from dataclasses import dataclass, field
from typing import Callable, Coroutine, Any, TypeVar
import logging
import asyncio
from yarl import URL
from mypy_boto3_s3 import S3Client
from mypy_boto3_s3.type_defs import ListObjectVersionsOutputTypeDef
from .awsservicelib import handle_client_error
from functools import partial
from operator import itemgetter
from aiohttp import ClientResponseError, hdrs


_get_storage_lock = asyncio.Lock()

@routes.get('/volumes/{volume_id}/awss3storage')
@routes.get('/volumes/{volume_id}/awss3storage/')
@action(name='heaserver-storage-storage-get-properties', rel='hea-properties')
async def get_all_storage(request: web.Request) -> web.Response:
    """
    Gets all the storage of the volume id that associate with the AWS account.
    :param request: the HTTP request.
    :return: A list of the account's storage or an empty array if there's no any objects data under the AWS account.
    ---
    summary: get all storage for a hea-volume associate with account.
    tags:
        - heaserver-storage-storage-get-account-storage
    parameters:
        - name: volume_id
          in: path
          required: true
          description: The id of the user's AWS volume.
          schema:
            type: string
          examples:
            example:
              summary: A volume id
              value: 666f6f2d6261722d71757578
        - $ref: '#/components/parameters/Authorization'
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    responses:
      '200':
        description: Expected response to a valid request.
        content:
            application/json:
                schema:
                    type: array
                    items:
                        type: object
            application/vnd.collection+json:
                schema:
                    type: array
                    items:
                        type: object
            application/vnd.wstl+json:
                schema:
                    type: array
                    items:
                        type: object
    """
    sub = request.headers.get(SUB, NONE_USER)
    async_requested = PREFERENCE_RESPOND_ASYNC in request.headers.get(PREFER, [])
    if async_requested:
        status_location = f'{str(request.url).rstrip("/")}asyncstatus'
        task_name = f'{sub}^{status_location}'
        async with _get_storage_lock:
            if not request.app[HEA_BACKGROUND_TASKS].in_progress(task_name):
                await request.app[HEA_BACKGROUND_TASKS].add(_get_all_storage(request), name=task_name)
        return response.status_see_other(status_location)
    else:
        storage_coro = _get_all_storage(request)
        return await storage_coro(request.app)


@routes.get('/volumes/{volume_id}/awss3storageasyncstatus')
async def get_storage_async_status(request: web.Request) -> web.Response:
    return response.get_async_status(request)


def main() -> None:
    config = init_cmd_line(description='a service for managing storage and their data within the cloud',
                           default_port=8080)
    start(package_name='heaserver-storage', db=aws.S3Manager, wstl_builder_factory=builder_factory(__package__), config=config)


@dataclass
class _StorageMetadata:
    total_size: int = 0
    object_count: int = 0
    first_modified: datetime | None = None
    last_modified: datetime | None = None
    object_total_duration: float = 0.0
    all_objects: dict[str, list[tuple[bool, datetime]]] = field(default_factory=lambda: defaultdict(list))

    def object_average_duration(self) -> float | None:
        return self.object_total_duration / self.object_count if self.object_count > 0 else None


def _get_all_storage(request: web.Request) -> Callable[[web.Application | None], Coroutine[Any, Any, web.Response]]:
    """
    List available storage classes by name

    :param request: the aiohttp Request (required).
    :return: (list) list of available storage classes
    """
    async def coro(app: web.Application | None) -> web.Response:
        logger = logging.getLogger(__name__)
        sub = request.headers.get(SUB, NONE_USER)
        volume_id = request.match_info.get("volume_id", None)
        bucket_id = request.match_info.get('id', None)
        bucket_name = request.match_info.get('bucket_name', None)
        if not volume_id:
            return web.HTTPBadRequest(body="volume_id is required")
        async with aws.S3ClientContext(request, volume_id) as s3_client:
            try:
                groups: dict[str, _StorageMetadata] = defaultdict(_StorageMetadata)
                coro_list = []
                bucket_url = await type_to_resource_url(request, AWSBucket)
                async for bucket in client.get_all(request.app, URL(bucket_url) / volume_id / 'bucketitems', AWSS3BucketItem,
                                                   headers=dict(filter_mapping(request.headers, (SUB, hdrs.AUTHORIZATION)))):
                    if (bucket_id is None and bucket_name is None) or (bucket.bucket_id in (bucket_id, bucket_name)):
                        assert bucket.bucket_id is not None, "bucket.bucket_id is required"
                        # S3 docs claim that list_object_versions is only for versioned buckets, but it works for
                        # non-versioned buckets too, and then there are buckets that were versioned and are not longer
                        # versioned that have old versions, so just use list_object_versions for everything.
                        coro_list.append(_list_object_versions(s3_client, groups, bucket.bucket_id))
                await asyncio.gather(*coro_list)

                storage_class_list = []
                perms = []
                attr_perms = []
                context = ViewerPermissionContext(sub)
                for item_key, item_values in groups.items():
                    storage_class = _get_storage_class(volume_id=volume_id, item_key=item_key, item_values=item_values)
                    storage_class_list.append(storage_class)
                    perms.append(await storage_class.get_permissions(context))
                    attr_perms.append(await storage_class.get_all_attribute_permissions(context))
                return await response.get_all(request, [to_dict(o) for o in storage_class_list],
                                            permissions=perms, attribute_permissions=attr_perms)
            except ClientError as e:
                logger.exception('Boto3 ClientError calculating storage classes')
                return handle_client_error(e)
            except ClientResponseError as e:
                logger.exception('Aiohttp ClientResponseError getting buckets')
                return response.status_from_exception(e)
    return coro


async def _list_object_versions(s3_client: S3Client, groups: Mapping[str, _StorageMetadata], bucket_name: str):
    loop = asyncio.get_event_loop()
    async def list_object_versions() -> AsyncIterator[ListObjectVersionsOutputTypeDef]:
        pages = iter(await loop.run_in_executor(None, partial(s3_client.get_paginator('list_object_versions').paginate, Bucket=bucket_name)))
        while (page := await loop.run_in_executor(None, next, pages, None)) is not None:
            yield page

    async def do_process(obj: ListObjectVersionsOutputTypeDef) -> None:
        for obj_ in obj.get('Versions', []):
            metadata = groups[obj_['StorageClass']]
            metadata.all_objects[obj_['Key']].append((False, obj_['LastModified']))
            metadata.total_size += obj_['Size']
        await asyncio.sleep(0)

        metadata = groups['STANDARD']
        for delete_obj_ in obj.get('DeleteMarkers', []):
            metadata.all_objects[delete_obj_['Key']].append((True, delete_obj_['LastModified']))
            metadata.total_size += len(delete_obj_['Key'].encode('utf-8'))  # https://docs.aws.amazon.com/AmazonS3/latest/userguide/DeleteMarker.html
        await asyncio.sleep(0)

    await queued_processing(list_object_versions(), do_process)

    def is_delete_marker(obj: tuple[bool, datetime]) -> bool:
        return obj[0]

    now_ = now()
    for metadata in groups.values():
        for versions in metadata.all_objects.values():
            versions_sorted = sorted(versions, key=itemgetter(1))
            first_version = versions_sorted[0][1]
            if not (metadata_fm := metadata.first_modified) or first_version < metadata_fm:
                metadata.first_modified = first_version
            last_version = versions_sorted[-1][1]
            if not (metadata_lm := metadata.last_modified) or last_version > metadata_lm:
                metadata.last_modified = last_version
            versions_ = iter(versions_sorted)
            while True:
                versions_part = tuple(_takewhile_inclusive(lambda x: not is_delete_marker(x), versions_))
                if versions_part:
                    if len(versions_part) > 1 and is_delete_marker(versions_part[-1]):
                        metadata.object_total_duration += (versions_part[0][1] - versions_part[-1][1]).total_seconds()
                    elif not versions_part[0][0]:
                        metadata.object_total_duration += (now_ - versions_part[0][1]).total_seconds()
                    metadata.object_count += 1
                else:
                    break


_T = TypeVar('_T')

def _takewhile_inclusive(predicate: Callable[[_T], bool], iterable: Iterable[_T]) -> Iterator[_T]:
    """
    Returns all the elements of the iterable that satisfy the predicate, including the last element that does not.

    :param predicate: the test condition.
    :param iterable: the iterable to filter. If an iterator, this function will consume it.
    :return: an iterator of the elements that satisfy the predicate, including the last element that does not
    """
    for x in iterable:
        yield x
        if not predicate(x):
            break


def _get_storage_class(volume_id: str, item_key: str, item_values: _StorageMetadata) -> AWSS3Storage:
    """
    :param item_key: the item_key
    :param item_values:  item_values
    :return: Returns the AWSStorage
    """
    logger = logging.getLogger(__name__)

    assert volume_id is not None, "volume_id is required"
    assert item_key is not None, "item_key is required"
    assert item_values is not None, "item_values is required"

    s: AWSS3Storage = AWSS3Storage()
    s.name = item_key
    s.id = item_key
    s.display_name = item_key
    s.object_earliest_created = item_values.first_modified
    s.object_last_modified = item_values.last_modified
    s.size = item_values.total_size
    s.object_count = item_values.object_count
    s.object_average_duration = item_values.object_average_duration()
    s.created = now()
    s.modified = now()
    s.volume_id = volume_id
    s.set_storage_class_from_str(item_key)
    s.source = AWS_S3
    s.owner = AWS_USER
    share: Share = ShareImpl()
    share.user = NONE_USER
    share.permissions = [Permission.VIEWER]
    s.add_user_share(share)
    return s
