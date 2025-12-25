

from collections.abc import Mapping, Callable, Awaitable, Iterator, Sequence, AsyncIterator, Generator
from datetime import datetime, timezone
import logging
from typing import Any, NamedTuple, cast
from uuid import uuid4
from aiohttp import hdrs, web, client_exceptions
from heaobject.aws import S3ArchiveDetailState, S3StorageClass, S3Object, AWSDesktopObject, S3Version
from heaobject.awss3key import display_name, encode_key, is_folder, is_root, join, split, parent, suffix
from heaobject.root import DesktopObject
from heaobject.user import NONE_USER
from heaobject.activity import Activity, DesktopObjectSummaryView
from heaobject.folder import AWSS3Folder, AWSS3ItemInFolder
from heaobject.data import AWSS3FileObject
from heaobject.project import AWSS3Project
from heaobject.root import desktop_object_type_for_name, Permission
from heaobject.trash import AWSS3FolderFileTrashItem
from heaobject.keychain import AWSCredentials
from heaserver.service.appproperty import HEA_CACHE, HEA_MESSAGE_BROKER_PUBLISHER, HEA_DB
from heaserver.service.backgroundtasks import BackgroundTasks
from heaserver.service.customhdrs import PREFER, PREFERENCE_RESPOND_ASYNC
from heaserver.service.db import aws, mongo, awsaction
from heaserver.service import client, response
from heaserver.service.heaobjectsupport import type_to_resource_url
from heaserver.service.oidcclaimhdrs import SUB
from heaserver.service.messagebroker import publish_desktop_object
from heaserver.service.representor import cj
from heaserver.service.util import queued_processing
from humanize import naturaldelta
from mypy_boto3_s3 import S3Client
from mypy_boto3_s3.type_defs import ObjectTypeDef, CommonPrefixTypeDef, ObjectVersionTypeDef
import asyncio
from zipfile import ZipFile, ZipInfo
from functools import partial
from botocore.exceptions import ClientError as BotoClientError
from heaserver.service.activity import DesktopObjectAction, DesktopObjectActionLifecycle
from yarl import URL
import time
import io
import threading
import sys
from base64 import urlsafe_b64encode, urlsafe_b64decode
from asyncio import AbstractEventLoop
from heaserver.folderawss3 import awsservicelib
from heaserver.folderawss3.awsservicelib import get_description, MONGODB_AWS_S3_FOLDER_METADATA_COLLECTION, SortOrder  # Keep
from . import awsservicelib
from enum import Enum


async def response_folder_as_zip(s3_client: S3Client, request: web.Request, bucket_name: str, folder_key: str | None) -> web.StreamResponse:
    """
    Creates a HTTP streaming response with the contents of all S3 objects with the given prefix packaged into a ZIP
    file. S3 allows folders to have no name (just a slash), and for maximum compatibility with operating systems like
    Windows that do not, such folders are replaced in the zip file with "No name <random string>". The resulting ZIP
    files are uncompressed, but this may change in the future. Files that cannot be downloaded are returned as zero
    byte files. Objects in an incompatible storage class are skipped.

    :param s3_client: the S3Client (required).
    :param request: the HTTP request (required).
    :param bucket_name: the bucket name (required).
    :param folder_key: the folder key. If None, the entire bucket is zipped.
    :return: the HTTP response.
    """
    logger = logging.getLogger(__name__)
    folder_display_name = display_name(folder_key or bucket_name)
    if not folder_display_name:
        folder_display_name = 'archive'

    response_ = web.StreamResponse(status=200, reason='OK',
                                               headers={hdrs.CONTENT_DISPOSITION: f'attachment; filename={folder_display_name}.zip',
                                                        hdrs.CONTENT_TYPE: 'application/zip'})
    await response_.prepare(request)
    class FixedSizeBuffer:
        def __init__(self, size: int) -> None:
            self.size = size
            self.buffer = io.BytesIO()
            self.condition = threading.Condition()
            self.length = 0  # length of current content
            self.eof = False
            self.closed = False

        def write(self, b: bytes | bytearray) -> int:
            if not isinstance(b, (bytes, bytearray)):
                raise TypeError(f"a bytes-like object is required, not '{type(b).__name__}'")
            with self.condition:
                if self.eof:
                    raise ValueError('Cannot write to buffer after EOF has been set')
                while not self.closed and len(b) > self.size - self.length:
                    self.condition.wait()  # Wait until there is enough space
                self.buffer.seek(self.length % self.size)
                written = self.buffer.write(b)
                self.length += written
                self.condition.notify_all()  # Notify any waiting threads
                return written

        def read(self, size: int = -1) -> bytes:
            with self.condition:
                while not self.closed and self.length == 0:
                    if self.eof:
                        logger.debug('Reading empty bytes due to EOF')
                        return b''
                    self.condition.wait()  # Wait until there is data to read

                if size == -1 or size > self.length:
                    size = self.length

                self.buffer.seek((self.length - size) % self.size)
                result = self.buffer.read(size)
                self.length -= size
                self.condition.notify_all()  # Notify any waiting threads
                return result

        def truncate(self, size: int | None = None) -> int:
            with self.condition:
                if size is None:
                    size = self.buffer.tell()
                self.buffer.truncate(size)
                logger.debug('Truncated')
                self.length = min(self.length, size)
                self.condition.notify_all()
                return size

        def flush(self) -> None:
            with self.condition:
                self.buffer.flush()
                logger.debug('Flushed')

        def set_eof(self) -> None:
            logger.debug('Waiting to set EOF')
            with self.condition:
                logger.debug('Setting EOF')
                self.eof = True
                self.condition.notify_all()

        def close(self) -> None:
            with self.condition:
                self.buffer.close()
                logger.debug('Closed')
                self.closed = True
                self.condition.notify_all()


    fileobj = FixedSizeBuffer(1024*10)
    def list_objects(s3: S3Client,
                    bucket_id: str,
                    prefix: str | None = None,
                    max_keys: int | None = None,
                    delimiter: str | None = None,
                    include_restore_status: bool | None = None) -> Iterator[ObjectTypeDef | CommonPrefixTypeDef]:
        list_partial = partial(s3.get_paginator('list_objects_v2').paginate, Bucket=bucket_id)
        if max_keys is not None:
            list_partial = partial(list_partial, PaginationConfig={'MaxItems': max_keys})
        if prefix is not None:  # Boto3 will raise an exception if Prefix is set to None.
            list_partial = partial(list_partial, Prefix=prefix)
        if delimiter is not None:
            list_partial = partial(list_partial, Delimiter=delimiter)
        if include_restore_status is not None and include_restore_status:
            list_partial = partial(list_partial, OptionalObjectAttributes=['RestoreStatus'])
        pages = iter(list_partial())
        while (page := next(pages, None)) is not None:
            for common_prefix in page.get('CommonPrefixes', []):
                yield common_prefix
            for content in page.get('Contents', []):
                yield content

    import queue
    q: queue.Queue[Exception] = queue.Queue()
    def zip_all(q):
        try:
            logger.debug('Starting zip...')
            #with ZipFile(fileobj, mode='w', compression=ZIP_DEFLATED) as zf:
            with ZipFile(fileobj, mode='w') as zf:
                for obj in list_objects(s3_client, bucket_name, folder_key, include_restore_status=True):
                    try:
                        folder = obj['Key'].removeprefix(folder_key or '')
                        if not folder:
                            continue
                        if obj['StorageClass'] in (S3StorageClass.STANDARD.name, S3StorageClass.GLACIER_IR.name)\
                            or ((restore:= obj.get('RestoreStatus')) and restore.get('RestoreExpiryDate')):
                            filename = _fill_in_folders_with_no_name(folder)
                            zinfo = ZipInfo(filename=filename, date_time=obj['LastModified'].timetuple()[:6])
                            zinfo.file_size = obj['Size']
                            # zinfo.compress_type = ZIP_DEFLATED  # Causes downloads to hang, possibly because something gets confused about file size.
                            if zinfo.is_dir():  # Zip also denotes a folders as names ending with a slash.
                                zf.writestr(zinfo, '')
                            else:
                                logger.debug('Zipping %s', obj['Key'])
                                with zf.open(zinfo, mode='w') as dest:
                                    body = s3_client.get_object(Bucket=bucket_name, Key=obj['Key'])['Body']
                                    try:
                                        while True:
                                            data = body.read(1024 * 10)
                                            if not data:
                                                break
                                            dest.write(data)
                                    finally:
                                        body.close()
                                logger.debug('Zipping %s complete', filename)
                    except BotoClientError as e:
                        logger.warning('Error downloading %s in bucket %s: %s', obj['Key'], bucket_name, e)
                logger.debug('All files zipped')
            logger.debug('Entire zipfile generated')
            fileobj.set_eof()
            logger.debug('Sent EOF')
        except Exception as e:
            q.put(e)
    thread = threading.Thread(target=zip_all, args=(q,))
    thread.start()
    try:
        loop = asyncio.get_running_loop()
        while True:
            while True:
                if not q.empty():
                    raise q.get()
                try:
                    data = await asyncio.wait_for(loop.run_in_executor(None, fileobj.read, 1024 * 10), timeout=1)
                    break
                except TimeoutError:
                    continue
            if not data:
                break
            await response_.write(data)
        await response_.write_eof()
        if not q.empty():
            raise q.get()
    except client_exceptions.ClientConnectionResetError:
        logger.info('Lost connection with the browser making zipfile %s, probably because the user closed/refreshed their tab or lost their internet connection', folder_key)
    finally:
        fileobj.close()
        thread.join()

    logger.debug('Done writing Zipfile to response stream')
    return response_


def _fill_in_folders_with_no_name(filename: str) -> str:
    """
    S3 allows folders to have no name (just a slash). This function replaces those "empty" names with a randomly
    generated name.

    :param filename: the filename.
    :return: the filename with empty names replaced.
    """
    logger = logging.getLogger(__name__)
    def split_and_rejoin(fname_: str) -> str:
        return '/'.join(part if part else f'No name {str(uuid4())}' for part in fname_.split('/'))
    if is_folder(filename):
        filename = split_and_rejoin(filename.rstrip('/')) + '/'
    else:
        filename = split_and_rejoin(filename)
    logger.debug('filename to download %s', filename)
    return filename


async def move_object(s3_client: S3Client, source_bucket_id: str, source_key: str, target_bucket_id: str, target_key: str,
               move_started_cb: Callable[[str, str, str | None, str, str], Awaitable[None]] | None = None,
               move_completed_cb: Callable[[str, str, str | None, str, str, str | None], Awaitable[None]] | None = None):
    """
    Moves object with source_key and in source_bucket_id to target_bucket_id and target_key. A preflight process
    checks whether the object (or for a folder, every object in the folder) is movable.

    :param s3_client: the S3 client (required).
    :param source_bucket_id: the source bucket name (required).
    :param source_key: the key of the object to move (required).
    :param target_bucket_id: the name of the target bucket (required).
    :param target_key: the key of the target object (required).
    :param move_started_cb: a callback that is invoked before attempting to move an object (optional). For folders,
    this function is invoked separately for every object within the folder. The callback is expected to accept the
    following parameters: the s3 client, the original object's bucket, the original object's key, the version of the
    original object, the new bucket, the target folder's key, and the new version.
    :param move_completed_cb: a callback that is invoked upon successfully moving an object (optional). For folders,
    this function is invoked separately for every object within the folder. The callback is expected to accept the
    following parameters: the s3 client, the original object's bucket, the original object's key, the version of the
    original object, the new bucket, the target folder's key, and the new version.
    :raises HTTPBadRequest: if preflight fails.
    :raises BotoClientError: if an error occurs while attempting to move the object (or for folders, the folder's
    contents).
    """
    logger = logging.getLogger(__name__)
    loop = asyncio.get_running_loop()
    def copy_and_delete(source_key, source_version_id: str, target_key_: str) -> str | None:
        """
        Copies and then deletes an S3 object, returning metadata about the copy.

        :param source_key: the original object's key.
        :param version_id: the version of the original object.
        :param target_key_: the copy's key.
        :return: the version id of the moved object, or None if the object is not in a versioned bucket.
        :raises BotoClientError: if the copy or delete fails. If the copy fails, the object is not deleted.
        """
        copy_out = s3_client.copy_object(CopySource={'Bucket': source_bucket_id,
                                                     'Key': source_key, 'VersionId': source_version_id},
                                         Bucket=target_bucket_id, Key=target_key_)
        s3_client.delete_object(Bucket=source_bucket_id, Key=source_key, VersionId=source_version_id)
        return copy_out.get('VersionId')
    async def gen() -> AsyncIterator[ObjectVersionTypeDef]:
        # Preflight
        cached_values: list[ObjectVersionTypeDef] = []
        logger.debug('Preflighting %s %s', source_bucket_id, source_key)
        source_key_is_folder = is_folder(source_key)
        async for obj in awsservicelib.list_object_versions(s3_client, source_bucket_id, source_key, max_keys=1000,
                                                            loop=loop, include_restore_status=True, sort=SortOrder.ASC):
            if source_key_is_folder or obj['Key'] == source_key:
                logger.debug('Checking %s %s: %s', source_bucket_id, source_key, obj)
                if obj['StorageClass'] in (S3StorageClass.DEEP_ARCHIVE.name, S3StorageClass.GLACIER.name) and \
                    not ((restore := obj.get('RestoreStatus')) and restore.get('RestoreExpiryDate')):
                    if source_key_is_folder:
                        raise response.status_bad_request(f'{awsservicelib.s3_object_message_display_name(source_bucket_id, source_key)} contains archived objects')
                    else:
                        raise response.status_bad_request(f'{awsservicelib.s3_object_message_display_name(source_bucket_id, source_key)} is archived')
                elif len(cached_values) < 1000:
                    cached_values.append(obj)
            else:
                break
        if len(cached_values) <= 1000:
            for val in cached_values:
                yield val
        else:
            async for obj in awsservicelib.list_object_versions(s3_client, source_bucket_id, source_key, max_keys=1000,
                                                                loop=loop, sort=SortOrder.ASC):
                if source_key_is_folder or obj['Key'] == source_key:
                    yield obj
                else:
                    break
    source_key_folder = parent(source_key)
    async def obj_processor(obj: ObjectVersionTypeDef):
        source_key_ = obj['Key']
        logger.debug('Move data %s %s %s', target_key, source_key_folder, source_key_)
        if is_folder(target_key):
            suffix_ = suffix(source_key_folder, source_key_)
            assert suffix_ is not None, 'suffix_ cannot be None'
            target_key_ = join(target_key, '/'.join(suffix_.split('/')[1:]))
        else:
            target_key_ = target_key
        logger.debug('Moving %s/%s to %s/%s', source_bucket_id, source_key_, target_bucket_id, target_key_)
        if move_started_cb:
            await move_started_cb(source_bucket_id, source_key_, obj.get('VersionId'), target_bucket_id, target_key_)
        target_version_id = await loop.run_in_executor(None, partial(copy_and_delete, source_key_, obj['VersionId'],
                                                                     target_key_))
        if move_completed_cb:
            await move_completed_cb(source_bucket_id, source_key_, obj.get('VersionId'), target_bucket_id, target_key_,
                                    target_version_id)
    await queued_processing(gen(), obj_processor)


async def clear_target_in_cache(request, invalidate_ancestors = False):
    logger = logging.getLogger(__name__)
    logger.debug('clearing target in cache')
    sub = request.headers.get(SUB, NONE_USER)
    _, target_bucket_name, target_folder_name, target_volume_id, _ = await awsservicelib._copy_object_extract_target(
            await request.json())
    logger.debug('Target bucket %s, folder %s, volume %s', target_bucket_name, target_folder_name, target_volume_id)
    invalidate_cache(request.app[HEA_CACHE], sub, target_folder_name, target_volume_id, target_bucket_name,
                     invalidate_ancestors=invalidate_ancestors)


def client_line_ending(request: web.Request) -> str:
    """
    Returns the web client's line ending.

    :return: the web client's line ending.
    """
    user_agent = request.headers.get(hdrs.USER_AGENT, 'Windows')
    return '\r\n' if 'Windows' in user_agent else '\n'


async def get_result_or_see_other(background_tasks: BackgroundTasks, task_name: str, status_location: str) -> web.Response:
    start_time = time.time()
    await asyncio.sleep(0)
    while (time.time() - start_time < 30) and not background_tasks.done(task_name):
        await asyncio.sleep(.1)
    if background_tasks.done(task_name):
        error = background_tasks.error(task_name)
        if error:
            background_tasks.remove(task_name)
            # In case we get an exception other than an HTTPException, raise it so it gets wrapped in an internal server
            # error response.
            raise error
        else:
            resp = background_tasks.result(task_name)
            background_tasks.remove(task_name)
            return resp
    else:
        return response.status_see_other(status_location)


class _MoveRename(Enum):
    MOVE = 'move'
    RENAME = 'rename'


async def move(activity: DesktopObjectAction, request: web.Request, mongo_client: mongo.Mongo | None, sub: str,
               volume_id: str, bucket_id: str, id_: str, key: str, target_volume_id: str, target_bucket_id,
               target_key_parent: str, type_: type[S3Object], target_path: Sequence[str] | None) -> web.Response:
    target_key = join(target_key_parent, split(key)[1])
    return await _move_rename(activity, request, mongo_client, sub, volume_id, bucket_id, id_, key, type_,
                              target_bucket_id, target_key, target_volume_id, target_path, _MoveRename.MOVE)


async def rename(activity: DesktopObjectAction, request: web.Request, mongo_client: mongo.Mongo | None, sub: str,
                 volume_id: str, bucket_id: str, id_: str, old_key: str, s3_object:
                 S3Object, type_: type[S3Object], target_path: Sequence[str] | None) -> web.Response:
    if not s3_object.key:
        return response.status_bad_request(f'Invalid project key {s3_object.key}')
    if old_key != s3_object.key:
        if bucket_id != s3_object.bucket_id:
            return response.status_bad_request(f"The project's bucket id was {s3_object.bucket_id} but the URL's bucket id was {bucket_id}")

    return await _move_rename(activity, request, mongo_client, sub, volume_id, bucket_id, id_, old_key, type_,
                            bucket_id, s3_object.key, volume_id, target_path, _MoveRename.RENAME)


async def _move_rename(activity: DesktopObjectAction, request: web.Request, mongo_client: mongo.Mongo | None,
                       sub: str, volume_id: str, bucket_id: str, id_: str, key: str, type_: type[S3Object],
                       target_bucket_id: str, target_key: str, new_volume_id: str, target_path: Sequence[str] | None,
                       action: _MoveRename) -> web.Response:
    """
    :param activity: the desktop object action for the overall move/rename (required).
    :param request: the HTTP request (required).
    :param mongo_client: a MongoDB client. If provided, metadata is updated in the database (optional).
    :param sub: the user requesting the move/rename (required).
    :param volume_id: the volume id of the original S3 object.
    :param bucket_id: the original object's bucket name (required).
    :param id_: the original object's encoded key (required).
    :param key: the original object's key (required).
    :param type_: the original object's type (required).
    :param target_: the original object's type.
    :param target_bucket_id: the bucket to which to move the object. For a rename, this is the same as the original
    object's bucket.
    :param target_key: the folder/file to move or rename appended to a target path.
    :param new_volume_id: the volume id representing the AWS account to move the object to.
    :param target_path: the path of the folder to which the object is to be moved.
    """
    logger = logging.getLogger(__name__)
    activity.old_object_id = id_
    activity.old_object_type_name = type_.get_type_name()
    if activity.old_object_type_name == AWSS3Project.get_type_name():
        path_part_ = 'awss3projects'
    elif activity.old_object_type_name == AWSS3Folder.get_type_name():
        path_part_ = 'awss3folders'
    else:
        path_part_ = 'awss3files'
    activity.old_object_uri = f'volumes/{volume_id}/buckets/{bucket_id}/{path_part_}/{id_}'
    activity.old_volume_id = volume_id
    activity.old_object_display_name = display_name(key)
    activity.new_context_dependent_object_path = list(target_path) if target_path is not None else None
    if 'path' in request.query:
        activity.old_context_dependent_object_path = request.query.getall('path')

    async with aws.S3ClientContext(request=request, volume_id=volume_id) as s3_client:
        # First, make sure the source exists.
        if not await awsservicelib._object_exists_with_prefix(s3_client, bucket_id, key):
            raise response.status_bad_request(f'Source {display_name(key)} does not exist in bucket {bucket_id}')

        # Next, make sure the target folder exists
        if parent(target_key) and not await awsservicelib._object_exists_with_prefix(s3_client, target_bucket_id, parent(target_key)):
            raise response.status_bad_request(f'Target {display_name(parent(target_key))} does not exist in bucket {target_bucket_id}')

        # Next check if we would clobber something in the target location.
        logger.debug('Checking if we would clobber something: %s %s', target_bucket_id, target_key)
        if await awsservicelib._object_exists_with_prefix(s3_client, target_bucket_id, target_key):
            raise response.status_bad_request(f'Target {display_name(target_key)} already exists in bucket {target_bucket_id}')

        # Next make sure that a target folder is not a subfolder of the source folder.
        if bucket_id == target_bucket_id and is_folder(target_key) and (target_key or '').startswith(key or ''):
            raise response.status_bad_request(f'Target folder {display_name(target_key)} is a subfolder of {display_name(key)}')

        # Finally make sure we have permission to delete the old versions of the object.
        version_perm_context = S3ObjectVersionPermissionContext(request)
        fake_obj: S3Object = type_()
        fake_obj.bucket_id = bucket_id
        fake_obj.key = key
        if Permission.DELETER not in await version_perm_context.get_permissions(fake_obj):
            raise response.status_forbidden(f'You have insufficient permissions to {"move" if action == _MoveRename.MOVE else "rename"} {awsservicelib.s3_object_message_display_name(bucket_id, key)}')
        try:
            if issubclass(type_, AWSS3Project):
                activity.old_object_description = await get_description(sub, s3_client, bucket_id, key)
            target_id = encode_key(target_key)
            original_object_is_versioned = await awsservicelib.is_versioning_enabled(s3_client, bucket_id)
            processed_keys: set[str] = set()
            processed_keys_lock = asyncio.Lock()
            metadata_cache: dict[tuple[str, str, str | None], dict[str, Any] | None] = {}
            lifecycle_cache: dict[tuple[str, str, str | None], DesktopObjectActionLifecycle] = {}
            part_activity_cache: dict[tuple[str, str, str | None], DesktopObjectAction] = {}

            async def move_started(source_bucket_id: str, source_key_: str, source_version: str | None, target_bucket_id_: str, target_key_: str):
                """
                :param source_bucket_id: the object's bucket before the move.
                :param source_key_: the object's key before the move.
                :param source_version: the version of the object before the move, if applicable.
                :param target_bucket_id_: the object's expected bucket after the move.
                :param target_key_: the object's expected key after the move.
                """
                lifecycle = DesktopObjectActionLifecycle(request=request, code='hea-move-part',
                                                         description=f'Moving {awsservicelib.s3_object_message_display_name(source_bucket_id, source_key_)} to {awsservicelib.s3_object_message_display_name(target_bucket_id_, target_key_)}',
                                                         activity_cb=publish_desktop_object)
                lifecycle_cache[(source_bucket_id, source_key_, source_version)] = lifecycle
                part_activity = await lifecycle.__aenter__()
                # Metadata for the original object. It's updated at the end of the while block.
                if mongo_client is not None:
                    metadata_ = await awsservicelib.get_metadata(mongo_client, source_bucket_id, encode_key(source_key_))
                    metadata_cache[(source_bucket_id, source_key_, source_version)] = metadata_
                    logger.debug('move_started: metadata_ for bucket %s and key %s (version %s): %s', source_bucket_id, source_key_, source_version, metadata_)
                else:
                    metadata_ = None
                part_activity.old_volume_id = volume_id
                part_activity.old_object_id = encode_key(source_key_)
                if metadata_ is not None:
                    part_activity.old_object_type_name = str(metadata_['actual_object_type_name'])
                if part_activity.old_object_type_name is None:
                    if is_folder(source_key_):
                        part_activity.old_object_type_name = AWSS3Folder.get_type_name()
                    else:
                        part_activity.old_object_type_name = AWSS3FileObject.get_type_name()
                path_part = desktop_object_type_or_type_name_to_path_part(part_activity.old_object_type_name)
                part_activity.old_object_display_name = display_name(source_key_)
                part_activity.old_object_description = await get_description(sub, s3_client, source_bucket_id, source_key_) \
                    if part_activity.old_object_type_name and issubclass(desktop_object_type_for_name(part_activity.old_object_type_name), AWSS3Project) else None
                part_activity.old_object_uri = f'volumes/{volume_id}/buckets/{bucket_id}/{path_part}/{part_activity.old_object_id}'
                if activity.old_context_dependent_object_path:
                    prefix_url = urlsafe_b64decode(activity.old_context_dependent_object_path[-1]).decode('utf-8')
                    rest_of_path = await extend_path(source_bucket_id, key, source_key_, prefix_url[:prefix_url.index('/buckets/')])
                    part_activity.old_context_dependent_object_path = activity.old_context_dependent_object_path + rest_of_path
                else:
                    part_activity.old_context_dependent_object_path = activity.old_context_dependent_object_path
                part_activity_cache[(source_bucket_id, source_key_, source_version)] = part_activity

            async def extend_path(bucket_name_: str, base_key: str, key_: str, base: str) -> list[str]:
                remainder = key_
                keys: list[str] = []
                while len(remainder) > len(base_key):
                    remainder = parent(remainder)
                    #if remainder not in processed_keys:
                    keys.append(remainder)
                rest_of_path: list[str] = []
                for k in reversed(keys):
                    if mongo_client is not None:
                        k_metadata = await awsservicelib.get_metadata(mongo_client, bucket_name_, encode_key(key_))
                    else:
                        k_metadata = None
                    type_part = 'awss3projects' if k_metadata is not None and k_metadata['actual_object_type_name'] == AWSS3Project.get_type_name() else 'awss3folders'
                    rest_of_path.append(urlsafe_b64encode((base + f'/buckets/{bucket_name_}/{type_part}/{encode_key(k)}').encode('utf-8')).decode('utf-8'))
                return rest_of_path


            async def move_completed(source_bucket_id: str, source_key_: str, source_version: str | None,
                                     target_bucket_id_: str, target_key_: str, target_version: str | None):
                """
                The moved S3 object has a key like a path, and ancestors may not have S3 objects associated with them
                yet have metadata, so we need check and update the metadata. If mongo_client is not None, we update the
                metadata.

                :param source_bucket_id: the original object's bucket name.
                :param source_key_: the original object's key.
                :param source_version: the version of the original object, if applicable.
                :param target_bucket_id_: the moved object's bucket name.
                :param target_key_: the moved object's key.
                :param target_version: the version of the moved object, if applicable.
                """
                async with processed_keys_lock:
                    part_activity = part_activity_cache[(source_bucket_id, source_key_, source_version)]
                    logger.debug('move_completed: part_activity for bucket %s and key %s (version %s) to target bucket %s and key %s (version %s): %r',
                                 source_bucket_id, source_key_, source_version, target_bucket_id_, target_key_, target_version, part_activity)
                    lifecycle = lifecycle_cache[(source_bucket_id, source_key_, source_version)]
                    path = source_key_
                    target_key__ = target_key_
                    if mongo_client is not None:
                        metadata_ = metadata_cache[(source_bucket_id, source_key_, source_version)]
                    else:
                        metadata_ = None
                    try:
                        parent_key = parent(key)
                        while path:
                            logger.debug('move_completed: metadata_ for bucket %s and key %s (version %s) to target bucket %s and key %s (version %s): %r',
                                        source_bucket_id, path, source_version, target_bucket_id_, target_key__, target_version, metadata_)
                            if path not in processed_keys:
                                if mongo_client is not None and metadata_ is not None:
                                    if original_object_is_versioned:
                                        # Mark the original object as deleted in the metadata.
                                        metadata_['deleted'] = True
                                        metadata_['version'] = source_version
                                        logger.debug('Updating metadata %s', metadata_)
                                        await mongo_client.update_admin_nondesktop_object(metadata_, MONGODB_AWS_S3_FOLDER_METADATA_COLLECTION)
                                    else:
                                        # Delete metadata for the original object.
                                        await mongo_client.delete_admin(MONGODB_AWS_S3_FOLDER_METADATA_COLLECTION,
                                                                        mongoattributes={'bucket_id': source_bucket_id,
                                                                                        'encoded_key': encode_key(path),
                                                                                        '$or': [{'deleted': False}, {'deleted': {'$exists': False}}]})

                                    # Update or create metadata for the moved object. If the target bucket is not versioned,
                                    # there should not be any metadata because the move would have failed and this callback
                                    # would never have been invoked.
                                    new_metadata: dict[str, Any] = {}
                                    new_metadata['bucket_id'] = target_bucket_id
                                    new_metadata['encoded_key'] = encode_key(target_key__)
                                    if not (parent_encoded_key := encode_key(parent(target_key__))):
                                        parent_encoded_key = 'root'
                                    new_metadata['parent_encoded_key'] = parent_encoded_key
                                    new_metadata['deleted'] = False
                                    new_metadata['version'] = None
                                    new_metadata['actual_object_type_name'] = metadata_['actual_object_type_name']
                                    logger.debug('Upserting metadata: %s', new_metadata)
                                    await mongo_client.upsert_admin_nondesktop_object(new_metadata,
                                                                                        MONGODB_AWS_S3_FOLDER_METADATA_COLLECTION,
                                                                                        {'bucket_id': target_bucket_id,
                                                                                         'encoded_key': encode_key(target_key__)})
                                if path != source_key_:
                                    async with DesktopObjectActionLifecycle(request=request,
                                                            code='hea-move-part',
                                                            description=f'Updating metadata for {awsservicelib.s3_object_message_display_name(source_bucket_id, path)} (moving to {awsservicelib.s3_object_message_display_name(target_bucket_id_, target_key__)})',
                                                            activity_cb=publish_desktop_object) as part_activity_:
                                        part_activity_.old_volume_id = volume_id
                                        part_activity_.old_object_id = encode_key(path)
                                        part_activity_.old_object_type_name = metadata_['actual_object_type_name'] if metadata_ is not None else AWSS3Folder.get_type_name()
                                        if part_activity_.old_object_type_name == AWSS3Folder.get_type_name():
                                            uri_path_part = 'awss3folders'
                                        else:
                                            uri_path_part = 'awss3projects'
                                        part_activity_.old_object_uri = f'volumes/{volume_id}/buckets/{bucket_id}/{uri_path_part}/{part_activity_.old_object_id}'
                                        part_activity_.old_object_display_name = display_name(path)
                                        if issubclass(desktop_object_type_for_name(part_activity_.old_object_type_name), AWSS3Project):
                                            part_activity_.old_object_description = await get_description(sub, s3_client, source_bucket_id, path)
                                        if activity.old_context_dependent_object_path:
                                            prefix_url = urlsafe_b64decode(activity.old_context_dependent_object_path[-1]).decode('utf-8')
                                            rest_of_path = await extend_path(source_bucket_id, key, path, prefix_url[:prefix_url.index('/buckets/')])
                                            part_activity_.old_context_dependent_object_path = activity.old_context_dependent_object_path + rest_of_path
                                        else:
                                            part_activity_.old_context_dependent_object_path = activity.old_context_dependent_object_path
                                        part_activity_.new_volume_id = new_volume_id
                                        part_activity_.new_object_id = encode_key(target_key__)
                                        part_activity_.new_object_type_name = part_activity_.old_object_type_name
                                        part_activity_.new_object_uri = f'volumes/{new_volume_id}/buckets/{target_bucket_id_}/{uri_path_part}/{part_activity_.new_object_id}'
                                        part_activity_.new_object_display_name = display_name(target_key__)
                                        part_activity_.new_object_description = part_activity_.old_object_description
                                        if activity.new_context_dependent_object_path:
                                            prefix_url = urlsafe_b64decode(activity.new_context_dependent_object_path[-1]).decode('utf-8')
                                            rest_of_path = await extend_path(target_bucket_id_, target_key, target_key__, prefix_url[:prefix_url.index('/buckets/')])
                                            part_activity_.new_context_dependent_object_path = activity.new_context_dependent_object_path + rest_of_path
                                        else:
                                            part_activity_.new_context_dependent_object_path = activity.new_context_dependent_object_path
                                processed_keys.add(path)
                            path = parent(path)
                            target_key__ = parent(target_key__)
                            logger.debug('checking path %s, key %s', path, key)
                            if len(path) <= len(parent_key):
                                break
                            elif mongo_client is not None:
                                metadata_ = await awsservicelib.get_metadata(mongo_client, source_bucket_id, encode_key(path))
                                logger.debug('Updated metadata_ for bucket %s and key %s: %s', source_bucket_id, path, metadata_)
                        assert part_activity is not None, 'part_activity should exist already'
                        part_activity.new_object_display_name = display_name(target_key_)
                        part_activity.new_object_description = part_activity.old_object_description
                        part_activity.new_volume_id = new_volume_id
                        part_activity.new_object_id = encode_key(target_key_)
                        assert part_activity.old_object_type_name is not None, 'old_object_type_name should not be None'
                        part_activity.new_object_type_name = part_activity.old_object_type_name
                        path_part = desktop_object_type_or_type_name_to_path_part(part_activity.new_object_type_name)
                        part_activity.new_object_uri = f'volumes/{new_volume_id}/buckets/{target_bucket_id_}/{path_part}/{part_activity.new_object_id}'
                        if activity.new_context_dependent_object_path is not None:
                            prefix_url = urlsafe_b64decode(activity.new_context_dependent_object_path[-1]).decode('utf-8')
                            rest_of_path = await extend_path(target_bucket_id_, target_key, target_key_, prefix_url[:prefix_url.index('/buckets/')])
                            part_activity.new_context_dependent_object_path = activity.new_context_dependent_object_path + rest_of_path
                        else:
                            part_activity.new_context_dependent_object_path = activity.new_context_dependent_object_path
                    finally:
                        if part_activity is not None:
                            exc_type, exc_value, exc_traceback = sys.exc_info()
                            assert lifecycle is not None, 'lifecycle should have been created by now'
                            await lifecycle.__aexit__(exc_type, exc_value, exc_traceback)
                        del lifecycle_cache[(source_bucket_id, source_key_, source_version)]
                        del part_activity_cache[(source_bucket_id, source_key_, source_version)]
                        if mongo_client is not None:
                            del metadata_cache[(source_bucket_id, source_key_, source_version)]

            await move_object(s3_client=s3_client, source_bucket_id=bucket_id, source_key=key,
                    target_bucket_id=target_bucket_id, target_key=target_key,
                    move_started_cb=move_started, move_completed_cb=move_completed)
            invalidate_cache(request.app[HEA_CACHE], sub, key, volume_id, bucket_id, invalidate_ancestors=True)
            activity.new_volume_id = new_volume_id
            activity.new_object_type_name = activity.old_object_type_name
            activity.new_object_id = target_id
            activity.new_object_uri = f'volumes/{volume_id}/buckets/{target_bucket_id}/{path_part_}/{target_id}'
            activity.new_object_display_name = display_name(target_key)
            activity.new_object_description = activity.old_object_description
            return response.status_no_content()
        except BotoClientError as e:
            raise awsservicelib.handle_client_error(e)
        except ValueError as e:
            raise response.status_internal_error(str(e))


async def copy(request: web.Request, mongo_client: mongo.Mongo, target_key: str, new_volume_id: str,
               status_location: str | URL | None = None, target_path: Sequence[str] | None = None) -> web.Response:
    """
    :param target_key: the target folder/project.
    :param status_location: if provided, will cause the response to be 303 with this location in the Location header,
    and the copy will be performed asynchronously. Otherwise, the copy will happen synchronously with a 201 response
    success status code or an error status.
    """
    logger = logging.getLogger(__name__)
    try:
        processed_keys: set[str] = set()
        processed_keys_lock = asyncio.Lock()
        async def copy_completed(source_bucket_id: str, source_key_: str, target_bucket_id: str, target_key_: str):
            async with processed_keys_lock:
                logger.debug('Copy completed %s, %s, %s, %s', source_bucket_id, source_key_, target_bucket_id, target_key_)
                path = source_key_
                parent_key = parent(target_key)
                target_key__ = target_key_
                metadata_ = await awsservicelib.get_metadata(mongo_client, source_bucket_id, encode_key(path))
                while path:
                    if path not in processed_keys:
                        logger.debug('Has metadata %s', metadata_)
                        if metadata_ is not None:
                            logger.debug('Updating metadata for %s %s', path, target_key__)
                            new_metadata: dict[str, Any] = {}
                            new_metadata['bucket_id'] = target_bucket_id
                            new_metadata['encoded_key'] = encode_key(target_key__)
                            if not (parent_encoded_key := encode_key(parent(target_key__))):
                                parent_encoded_key = 'root'
                            new_metadata['parent_encoded_key'] = parent_encoded_key
                            new_metadata['deleted'] = False
                            new_metadata['actual_object_type_name'] = metadata_['actual_object_type_name']

                            await mongo_client.upsert_admin_nondesktop_object(new_metadata,
                                                                              MONGODB_AWS_S3_FOLDER_METADATA_COLLECTION,
                                                                              {'bucket_id': target_bucket_id,
                                                                               'encoded_key': encode_key(target_key__)})
                        processed_keys.add(path)
                    path = parent(path)
                    target_key__ = parent(target_key__)
                    if len(path) < len(parent_key):
                        break
                    else:
                        metadata_ = await awsservicelib.get_metadata(mongo_client, source_bucket_id, encode_key(path))
        async def publish_desktop_object_and_clear_cache(app: web.Application, desktop_object: DesktopObject,
                                                    appproperty_=HEA_MESSAGE_BROKER_PUBLISHER):
            if isinstance(desktop_object, Activity):
                await clear_target_in_cache(request)
            await publish_desktop_object(app, desktop_object, appproperty_)

        if status_location:
            return await awsservicelib.copy_object_async(request, status_location,
                                                        activity_cb=publish_desktop_object_and_clear_cache,
                                                        copy_object_completed_cb=copy_completed)
        else:
            return await awsservicelib.copy_object(request, activity_cb=publish_desktop_object_and_clear_cache,
                                                   copy_object_completed_cb=copy_completed)
    except BotoClientError as e:
        raise awsservicelib.handle_client_error(e)
    except ValueError as e:
        raise response.status_internal_error(str(e))


async def delete_folder(request: web.Request, volume_id: str, bucket_id: str, key_: str, loop: AbstractEventLoop | None = None,
                        publish_desktop_object_and_clear_cache: Callable[[web.Application, DesktopObjectAction], Awaitable[None]] | None = None):
    logger = logging.getLogger(__name__)
    if loop is None:
        loop = asyncio.get_running_loop()
    async with aws.S3ClientContext(request=request, volume_id=volume_id) as s3_client:
        versioning = await awsservicelib.is_versioning_enabled(s3_client, bucket_id)
        async with mongo.MongoContext(request) as mongo_client:
            processed_keys: set[str] = set()
            delete_metadata_lock = asyncio.Lock()
            async def delete_metadata(bucket_name: str, key: str, version_id: str | None):
                """
                Delete metadata in non-versioned buckets, and mark metadata as deleted in versioned buckets. The key
                parameter is an actual S3 object. We also walk through parent folders within the original folder being
                deleted (key_ argument), inclusive, and update their metadata in case they are not actual S3 objects
                but have metadata.

                In the scenario where an object is deleted and its folder not longer exists because the folder is not
                an actual S3 object, future GET requests for the folder should result in the its metadata if any being
                deleted or marked as deleted.

                :param bucket_name: the bucket name (required).
                :param key: the key (required).
                """
                async with delete_metadata_lock:
                    metadata_ = await awsservicelib.get_metadata(mongo_client, bucket_name, encode_key(key), include_deleted=True)
                    logger.debug('Got initial metadata for bucket %s and key %s: %s', bucket_name, key, metadata_)
                    # Loop through all the folders and subfolders and objects and update all the metadata. Folders may or
                    # may not correspond to actual S3 objects, in which case we can set its deleted property to True, but
                    # there is no version information.
                    #
                    # Folder metadata only has a version set if it is deleted and it corresponds to an actual S3 object.
                    path = key
                    while path:
                        logger.debug('Updating metadata for bucket %s and path %s and key %s: %s', bucket_name, path, key, metadata_)
                        # metadata_ must have had its deleted property set to False, so there is no need to check.
                        if metadata_ is not None:
                            if versioning:
                                metadata_['deleted'] = True
                                if path == key:
                                    # The path corresponds to an actual S3 object, so we have version info, and we can
                                    # set the version.
                                    logger.debug('Setting version of path %s in bucket %s to %s', path, bucket_name, version_id)
                                    metadata_['version'] = version_id
                                    await mongo_client.update_admin_nondesktop_object(metadata_, MONGODB_AWS_S3_FOLDER_METADATA_COLLECTION)
                                elif path not in processed_keys and metadata_ and not metadata_.get('version'):
                                    # We can update the path's metadata because it has not been updated with its version
                                    # information yet, or it has no version info because it does not correspond to an
                                    # actual S3 object.
                                    await mongo_client.update_admin_nondesktop_object(metadata_, MONGODB_AWS_S3_FOLDER_METADATA_COLLECTION)
                            elif path not in processed_keys:
                                await mongo_client.delete_admin(MONGODB_AWS_S3_FOLDER_METADATA_COLLECTION,
                                                                mongoattributes={'bucket_id': bucket_name, 'encoded_key': encode_key(path),
                                                                                '$or': [{'deleted': False}, {'deleted': {'$exists': False}}]})
                        processed_keys.add(path)  # Don't process this path again unless it's in a versioned bucket and we have version metadata.
                        path = parent(path)
                        if len(path) < len(key_) or path in processed_keys:
                            # We're in a parent of the folder being deleted, or we already processed these objects, so stop looping.
                            break
                        else:
                            # We may process a folder twice, once in this loop and once as the key argument to
                            # delete_metadata, so the metadata may already have its deleted property set to True.
                            metadata_ = await awsservicelib.get_metadata(mongo_client, bucket_name, encode_key(path), include_deleted=True)
                            logger.debug('Got path metadata for bucket %s and key %s: %s', bucket_name, path, metadata_)
            async_requested = PREFERENCE_RESPOND_ASYNC in request.headers.get(PREFER, [])
            if async_requested:
                path = f'{request.url.path}/deleterasyncstatus'
                status_location = request.url.with_path(path)  # Don't keep query params.
                response_ = await awsservicelib.delete_object_async(mongo_client, request, status_location, recursive=True,
                                                                    activity_cb=publish_desktop_object_and_clear_cache,
                                                                    delete_completed_cb=delete_metadata)
            else:
                response_ = await awsservicelib.delete_object(mongo_client, request, recursive=True,
                                                            activity_cb=publish_desktop_object_and_clear_cache,
                                                            delete_completed_cb=delete_metadata)

    return response_


def desktop_object_type_or_type_name_to_path_part(type_or_type_name: type[DesktopObject] | str | None, default: type[DesktopObject] | None = None) -> str:
    type_ = to_desktop_object_type(type_or_type_name) if type_or_type_name else default

    if type_ is AWSS3Project:
        return 'awss3projects'
    elif type_ is AWSS3Folder:
        return 'awss3folders'
    elif type_ is AWSS3FileObject:
        return 'awss3files'
    else:
        raise ValueError(f'Unsupported type {type_}')


def get_type_name_from_metadata(metadata: dict[str, Any] | None, key: str) -> str:
    """
    Infers the type name of an object from its metadata, or if the metadata is absent or incomplete, from the given
    key.

    :param metadata: the metadata of the object.
    :param key: the key of the object.
    :return: the type name of the object.
    """
    def fallback():
        if is_folder(key):
            return AWSS3Folder.get_type_name()
        else:
            return AWSS3FileObject.get_type_name()
    return (metadata and metadata.get('actual_object_type_name')) or fallback()



def to_desktop_object_type(type_: type[DesktopObject] | str) -> type[DesktopObject]:
    if isinstance(type_, type) and issubclass(type_, DesktopObject):
        return type_
    else:
        return desktop_object_type_for_name(str(type_))


async def get_desktop_object_summary(request: web.Request, object_uri: str) -> DesktopObjectSummaryView | None:
    sub = request.headers.get(SUB, NONE_USER)
    activity_url = await type_to_resource_url(request, DesktopObjectSummaryView)
    return await anext(client.get_all(request.app, activity_url, DesktopObjectSummaryView,
                                      query_params={'begin': str(0), 'end': str(1), 'object_uri': object_uri},
                                      headers={SUB: sub}), None)


async def create_presigned_url_credentials(request: web.Request, volume_id: str, expiration_hours: int, key: str, bucket_id: str) -> AWSCredentials:
    sub = request.headers.get(SUB, NONE_USER)
    creds = await get_database(request).get_credentials_from_volume(request, volume_id)
    if creds is None:
        raise response.status_not_found()
    assert creds.id is not None, 'creds.id cannot be None'
    auth_header_value = request.headers.get(hdrs.AUTHORIZATION)
    if auth_header_value is None:
        raise response.status_bad_request('No Authorization header value')
    keychain_url = await type_to_resource_url(request, AWSCredentials)
    id_ = await client.post_data_create(request.app,
                                        URL(keychain_url) / 'internal' / creds.id / 'presignedurlcredentialscreator',
                                        {'template': {'data': [
                                                              {'name': 'key_lifespan',
                                                                'value': expiration_hours},
                                                               {'name': 'keys', 'value': [key]},
                                                               {'name': 'bucket', 'value': bucket_id},
                                                               ]}},
                                            headers={SUB: sub, hdrs.CONTENT_TYPE: cj.MIME_TYPE, hdrs.AUTHORIZATION: auth_header_value})
    presigned_creds = await client.get(request.app, URL(keychain_url) / id_, AWSCredentials,
                                       headers={SUB: sub})
    if presigned_creds is None:
        raise response.status_internal_error('Failed to create presigned URL credentials')
    return presigned_creds


async def when_object_not_found(s3_client: S3Client, bucket_name: str) -> web.HTTPError:
    """
    Raise HTTPNotFOund if the bucket is found or BotoClientError if the bucket is not found.

    :param s3_client: the S3 client (required).
    :param bucket_name: the bucket name (required).
    :return: the exception to raise.
    """
    loop = asyncio.get_running_loop()
    try:
        await loop.run_in_executor(None, partial(s3_client.head_bucket, Bucket=bucket_name))
        return response.status_not_found()
    except BotoClientError as e:
        return awsservicelib.handle_client_error(e)


def get_database(request: web.Request) -> aws.S3WithMongo:
    """
    Returns the HEA_DB app property value.

    :param request: the HTTP request (required).
    :return: the HEA_DB app property value.
    """
    return cast(aws.S3WithMongo, request.app[HEA_DB])


async def extract_expiration(body: dict[str, Any]) -> int:
    """
    Extracts the target URL and expiration time for a presigned URL request. It un-escapes them
    as needed.

    :param body: a Collection+JSON template dict.
    :return:  expiration time in hours.
    :raises web.HTTPBadRequest: if the given body is invalid.
    """
    try:
        return next(
            int(item['value']) for item in body['template']['data'] if item['name'] == 'link_expiration')
    except (KeyError, ValueError, StopIteration) as e:
        raise web.HTTPBadRequest(body=f'Invalid template: {e}') from e


class BucketAndKey(NamedTuple):
    bucket: str
    key: str


def path_iter(key: str | None) -> Generator[str, None, None]:
    """
    Generator of the path parts of a key in reverse order from key to root.

    :param key: the key to get the parent folders/projects for.
    :return: a generator of parent folders/project keys.
    """
    while path := parent(key):
        yield path
        key = path


def invalidate_cache(cache: dict[tuple, Any], sub: str, key: str, volume_id: str, bucket_id: str,
                     invalidate_ancestors=False):
    """
    Invalidates the cache for the given key, its descendants, and optionally its ancestors.

    :param cache: the cache to invalidate.
    :param sub: the user requesting the invalidation.
    :param key: the key to invalidate.
    :param volume_id: the volume id.
    :param bucket_id: the bucket id.
    :param invalidate_ancestors: whether to invalidate the ancestors of the key.
    """
    logger = logging.getLogger(__name__)
    logger.debug('invalidate_cache: sub %s, key %s, volume_id %s, bucket_id %s, invalidate_ancestors %s', sub, key, volume_id, bucket_id, invalidate_ancestors)
    parent_key = parent(key)
    folder_id = 'root' if is_root(parent_key) else encode_key(parent_key)
    id_ = encode_key(key)
    cache.pop((sub, volume_id, bucket_id, folder_id, id_, 'items'), None)
    cache.pop((sub, volume_id, bucket_id, folder_id, None, 'items'), None)
    cache.pop((sub, volume_id, bucket_id, id_, None, 'items'), None)
    cache.pop((sub, volume_id, bucket_id, id_, 'actual'), None)
    cache.pop((sub, volume_id, bucket_id, None, 'actual'), None)
    def process_children(id__: str):
        if is_folder(id__):
            for cache_key in list(cache.keys()):
                if cache_key[0] == sub and cache_key[1] == volume_id and cache_key[2] == bucket_id and cache_key[3] == id__:
                    cache.pop(cache_key, None)
                if cache_key[4]:
                    process_children(cache_key[4])
    process_children(id_)
    for path in path_iter(key) if invalidate_ancestors else []:
        invalidate_cache(cache, sub, path, volume_id, bucket_id, invalidate_ancestors=True)


def set_s3_storage_status(obj: Mapping[str, Any], item: AWSS3FileObject | AWSS3ItemInFolder) -> bool:
    """
    The function sets the source, source_detail, storage_class, archive_detail_state, and available_until attributes of
    the S3 object. It currently only supports file objects but may support folders and projects backed by an actual
    object in the future.

    The function handles different states of the S3 object, in addition to setting the archive_detail_state
    accordingly:
    * If the object is being restored, it sets the source to "AWS S3 (Unarchiving...)" and includes a typical
      completion time in the source_detail.
    * If the object has been restored, it sets the source to "AWS S3 (Unarchived)" and includes an availability
      duration in the source_detail in addition to setting the availability_duration attribute.
    * If the object is neither being restored nor restored, it sets the source based on the storage class of the S3
      object.

    :param obj: A dictionary containing metadata of the S3 object.
    :param item: An instance of S3 object to be updated with source information.
    :return: whether the object is restoring/restored
    """
    item.storage_class = S3StorageClass[obj['StorageClass']]
    item.source = None
    item.source_detail = None
    retrieval = obj.get('RestoreStatus')
    if retrieval is not None:
        result = True
        if (retrieval.get("IsRestoreInProgress")):
            item.source = "AWS S3 (Unarchiving...)"
            item.source_detail = "Typically completes within 12 hours"
            item.archive_detail_state = S3ArchiveDetailState.RESTORING
        if (retrieval.get("RestoreExpiryDate") is not None):
            item.source = "AWS S3 (Unarchived)"
            temporarily_available_until = retrieval.get("RestoreExpiryDate")
            item.source_detail = f"Available for {naturaldelta(temporarily_available_until - datetime.now(timezone.utc))}"
            item.archive_detail_state = S3ArchiveDetailState.RESTORED
            item.available_until = temporarily_available_until
    else:
        result = False
    if item.archive_storage_class and not result:
        item.archive_detail_state = S3ArchiveDetailState.ARCHIVED
    if item.source is None:
        s = f'AWS S3 ({S3StorageClass[obj["StorageClass"]].display_name})'
        item.source = s
        item.source_detail = s
    return result


class S3ObjectVersionPermissionContext(aws.AWSPermissionContext):
    """
    AWS S3 object permission context. It sets attribute permissions on S3 objects and provides an object ARN.
    """

    def __init__(self, request: web.Request, **kwargs):
        """
        Creates a permission context from the provided HTTP request.

        :param request: the HTTP request (required). It must have a volume_id path parameter.
        """
        actions = [awsaction.S3_LIST_OBJECT_VERSIONS, awsaction.S3_DELETE_OBJECT_VERSION]
        super().__init__(request=request, actions=actions, **kwargs)

    async def get_permissions(self, obj: DesktopObject) -> list[Permission]:
        """
        Gets the user's permissions for a desktop object by calling AWS SimulatePrincipalPolicy. The object's ARN is
        passed into SimulatePrincipalPolicy, and this method should only be called after the attributes needed to
        create the ARN are populated. If not an S3 object, this class delegates to the AWS permission context.

        :param obj: the object (required).
        :return: a list of Permissions, or the empty list if there is none.
        """
        logger = logging.getLogger(__name__)
        logger.debug('S3 object permission context getting permissions for desktop object %r', obj)
        if logger.isEnabledFor(logging.DEBUG) and not isinstance(obj, S3Version):
            logger.debug('Not an S3 version: %r', obj)
        return await super().get_permissions(obj)

    async def get_attribute_permissions(self, obj: DesktopObject, attr: str) -> list[Permission]:
        """
        Dynamically sets permissions for the tags and display_name attributes based on the user's account ownership,
        simulated AWS permissions, and archived status, otherwise it returns default attribute permissions based on
        object-level permissions.

        :param obj: the object (required).
        :param attr: the attribute to check (required).
        :return: the permissions for the given object attribute.
        """
        if not isinstance(obj, S3Version):
            return []
        return [perm for perm in await self.get_permissions(obj) if perm == Permission.VIEWER]

    def _caller_arn(self, obj: AWSDesktopObject) -> str:
        """
        The object's Amazon Resource Name (ARN).

        :param obj: the object (required).
        :return: the ARN.
        """
        return f'arn:aws:s3:::{obj.resource_type_and_id}'


class TrashItemPermissionContext(aws.AWSPermissionContext):
    """
    AWS S3 trash item permission context. It sets attribute permissions and provides an object ARN.
    """

    def __init__(self, request: web.Request, **kwargs):
        """
        Creates a permission context from the provided HTTP request.

        :param request: the HTTP request (required). It must have a volume_id path parameter.
        """
        actions = [awsaction.S3_DELETE_OBJECT_VERSION]
        super().__init__(request=request, actions=actions, **kwargs)

    async def get_permissions(self, obj: DesktopObject) -> list[Permission]:
        """
        Gets the user's permissions for a desktop object by calling AWS SimulatePrincipalPolicy. The object's ARN is
        passed into SimulatePrincipalPolicy, and this method should only be called after the attributes needed to
        create the ARN are populated. If not an S3 object, this class delegates to the AWS permission context.

        :param obj: the object (required).
        :return: a list of Permissions, or the empty list if there is none.
        """
        logger = logging.getLogger(__name__)
        logger.debug('Trash item permission context getting permissions for desktop object %r', obj)
        if logger.isEnabledFor(logging.DEBUG) and not isinstance(obj, AWSS3FolderFileTrashItem):
            logger.debug('Not a trash item: %r', obj)
        perms = set(await super().get_permissions(obj))
        perms.add(Permission.VIEWER)
        return list(perms)

    async def get_attribute_permissions(self, obj: DesktopObject, attr: str) -> list[Permission]:
        """
        Dynamically sets permissions for the tags and display_name attributes based on the user's account ownership,
        simulated AWS permissions, and archived status, otherwise it returns default attribute permissions based on
        object-level permissions.

        :param obj: the object (required).
        :param attr: the attribute to check (required).
        :return: the permissions for the given object attribute.
        """
        if not isinstance(obj, AWSS3FolderFileTrashItem):
            return []
        return [perm for perm in await self.get_permissions(obj) if perm == Permission.VIEWER]

    def _caller_arn(self, obj: AWSDesktopObject) -> str:
        """
        The object's Amazon Resource Name (ARN).

        :param obj: the object (required).
        :return: the ARN.
        """
        return f'arn:aws:s3:::{obj.resource_type_and_id}'
