"""
Functions for interacting with Amazon Web Services.

This module supports management of AWS accounts, S3 buckets, and objects in S3 buckets. It uses Amazon's boto3 library
behind the scenes.

In order for HEA to access AWS accounts, buckets, and objects, there must be a volume accessible to the user through
the volumes microservice with an AWSFileSystem for its file system. Additionally, credentials must either be stored
in the keychain microservice and associated with the volume through the volume's credential_id attribute,
or stored on the server's file system in a location searched by the AWS boto3 library. Users can only see the
accounts, buckets, and objects to which the provided AWS credentials allow access, and HEA may additionally restrict
the returned objects as documented in the functions below. The purpose of volumes in this case is to supply credentials
to AWS service calls. Support for boto3's built-in file system search for credentials is only provided for testing and
should not be used in a production setting. This module is designed to pass the current user's credentials to AWS3, not
to have application-wide credentials that everyone uses.

The request argument to these functions is expected to have a OIDC_CLAIM_sub header containing the user id for
permissions checking. No results will be returned if this header is not provided or is empty.

In general, there are two flavors of functions for getting accounts, buckets, and objects. The first expects the id
of a volume as described above. The second expects the id of an account, bucket, or bucket and object. The latter
attempts to match the request up to any volumes with an AWSFileSystem that the user has access to for the purpose of
determine what AWS credentials to use. They perform the
same except when the user has access to multiple such volumes, in which case supplying the volume id avoids a search
through the user's volumes.
"""
import asyncio
import re
from datetime import datetime, timezone

import orjson
import logging
from enum import Enum, auto
from aiohttp import web, hdrs
from heaobject.aws import S3StorageClass

from heaobject.awss3key import KeyDecodeException, decode_key, is_folder, split, replace_parent_folder, parent, display_name, is_object_in_folder

from heaserver.service.util import queued_processing
from heaserver.service import response
from heaserver.service.heaobjectsupport import RESTPermissionGroup, new_heaobject_from_type
from heaserver.service.oidcclaimhdrs import SUB
from heaserver.service.appproperty import HEA_BACKGROUND_TASKS
from heaserver.service.uritemplate import tvars
from typing import Any, Optional, Callable, AsyncIterator, NamedTuple, cast, TypedDict
from collections import defaultdict
from collections.abc import Awaitable, Collection, Mapping, Iterable, Iterator
from aiohttp.web import Request, Response, Application, HTTPError
from heaobject.user import NONE_USER, ALL_USERS
from heaobject.root import Share, ShareImpl
from heaobject.folder import Folder, AWSS3Folder
from heaobject.project import AWSS3Project
from heaserver.service.activity import DesktopObjectActionLifecycle
from heaobject.activity import DesktopObjectAction
from heaobject.aws import S3Object
from heaobject.error import DeserializeException
from heaobject.activity import Status
from heaobject.awss3key import encode_key, join
from heaobject.data import AWSS3FileObject
from asyncio import AbstractEventLoop
from functools import partial
from urllib.parse import unquote
from botocore.exceptions import ClientError as BotoClientError, ParamValidationError
from heaserver.service.aiohttp import SortOrder
from heaserver.service.sources import HEA
from heaserver.service.db.awsservicelib import s3_object_message_display_name, \
    handle_client_error as _handle_client_error
from heaserver.service.db import aws
from heaserver.service.db.mongo import Mongo
from mypy_boto3_s3.client import S3Client
from mypy_boto3_s3.type_defs import ObjectVersionTypeDef, DeleteMarkerEntryTypeDef, ListObjectVersionsOutputTypeDef
from heaserver.service.db.aws import S3ClientContext, client_error_status, CLIENT_ERROR_404, \
    CLIENT_ERROR_RESTORE_ALREADY_IN_PROGRESS, client_error_code
from aiohttp.web import HTTPException
from yarl import URL
from io import BytesIO
from cachetools import TTLCache
from base64 import urlsafe_b64encode, urlsafe_b64decode
from itertools import chain, groupby
from operator import itemgetter

from heaserver.folderawss3 import awsservicelib


MONGODB_AWS_S3_FOLDER_METADATA_COLLECTION = 'awss3foldersmetadata'
MAX_FOLDER_DOWNLOAD_SIZE = 10 * 1024 * 1024 * 1024  # 10 GB

"""
Available functions
AWS object
- get_account
- post_account                    NOT TESTED
- put_account                     NOT TESTED
- delete_account                  CANT https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_accounts_close.html
                                  One solution would be to use beautiful soup : https://realpython.com/beautiful-soup-web-scraper-python/

- users/policies/roles : https://www.learnaws.org/2021/05/12/aws-iam-boto3-guide/

- change_storage_class            TODO
- copy_object
- delete_bucket_objects
- delete_bucket
- delete_folder
- delete_object
- download_object
- download_archive_object         TODO
- generate_presigned_url
- get_object_meta
- get_object_content
- get_all_buckets
- get all
- opener                          TODO -> return file format -> returning metadata containing list of links following collection + json format
-                                         need to pass back collection - json format with link with content type, so one or more links, most likely
- post_bucket
- post_folder
- post_object
- post_object_archive             TODO
- put_bucket
- put_folder
- put_object
- put_object_archive              TODO
- transfer_object_within_account
- transfer_object_between_account TODO
- rename_object
- update_bucket_policy            TODO

TO DO
- accounts?
"""
MONGODB_BUCKET_COLLECTION = 'buckets'

ROOT_FOLDER: Folder = Folder()
ROOT_FOLDER.id = 'root'
ROOT_FOLDER.name = 'root'
ROOT_FOLDER.display_name = 'Root'
ROOT_FOLDER.description = "The root folder for an AWS S3 bucket's objects."
_root_share: Share = ShareImpl()
_root_share.user = ALL_USERS
_root_share.permissions = RESTPermissionGroup.POSTER_PERMS.perms
ROOT_FOLDER.add_user_share(_root_share)
ROOT_FOLDER.source = HEA


async def create_object(request: web.Request, type_: type[S3Object] | None = None, activity_cb: Optional[
                            Callable[[Application, DesktopObjectAction], Awaitable[None]]] = None) -> web.Response:
    """
    Creates a new file or folder in a bucket. The volume id must be in the volume_id entry of the request.match_info
    dictionary. The bucket id must be in the bucket_id entry of request.match_info. The folder or file id must be in
    the id entry of request.match_info. The body must contain a heaobject.folder.AWSS3Folder or
    heaobject.data.AWSS3FileObject dict.

    :param request: the HTTP request (required).
    :param type_: the expected type of S3Object, or None if it should just parse the type that it finds.
    :param activity_cb: optional coroutine that is called when potentially relevant activity occurred.
    :return: the HTTP response, with a 201 status code if successful with the URL to the new item in the Location
    header,
    :raises HTTPException: with status 403 if access was denied, 404 if the volume or bucket could not be found, or 500
    if an internal error occurred.
    """
    try:
        try:
            folder_or_file: S3Object = await new_heaobject_from_type(request, type_ or S3Object)
        except TypeError:
            return response.status_bad_request(f'Expected type {type_ or S3Object}; actual object was {await request.text()}')
    except (DeserializeException, TypeError) as e:
        return response.status_bad_request(f'Invalid new object: {e}')

    try:
        volume_id = request.match_info['volume_id']
        bucket_id = request.match_info['bucket_id']
    except KeyError as e:
        return response.status_bad_request(f'{e} is required')
    folder_or_file_key = folder_or_file.key
    if folder_or_file_key is None:
        return response.status_bad_request(f'The object {folder_or_file.display_name} must have a key')

    async with DesktopObjectActionLifecycle(request=request,
                                            code='hea-create',
                                            description=f'Creating {s3_object_message_display_name(bucket_id, folder_or_file_key)}',
                                            activity_cb=activity_cb) as activity:
        async with S3ClientContext(request=request, volume_id=volume_id) as s3_client:
            response_ = await _create_object(s3_client, bucket_id, folder_or_file_key)

            def type_part():
                if isinstance(folder_or_file, AWSS3Folder):
                    return 'awss3folders'
                elif isinstance(folder_or_file, AWSS3Project):
                    return 'awss3projects'
                else:
                    return 'awss3files'

            if response_.status == 201:
                activity.new_volume_id = volume_id
                activity.new_object_id = folder_or_file.id
                activity.new_object_display_name = folder_or_file.display_name
                activity.new_object_type_name = folder_or_file.get_type_name()
                activity.new_object_uri = f'volumes/{volume_id}/buckets/{bucket_id}/{type_part()}/{folder_or_file.id}'
                if 'path' in request.url.query:
                    activity.new_context_dependent_object_path = request.url.query.getall('path')
                return await response.post(request, folder_or_file.id, f'volumes/{volume_id}/buckets/{bucket_id}/{type_part()}')
            elif response_.status < 300:
                raise ValueError
            return response_


async def copy_object(request: Request,
                      activity_cb: Callable[[Application, DesktopObjectAction], Awaitable[None]] | None = None,
                      copy_object_completed_cb: Callable[[str, str, str, str], Awaitable[None]] | None = None) -> Response:
    """
    copy/paste (duplicate), throws error if destination exists, this so an overwrite isn't done
    throws another error is source doesn't exist
    https://medium.com/plusteam/move-and-rename-objects-within-an-s3-bucket-using-boto-3-58b164790b78
    https://stackoverflow.com/questions/47468148/how-to-copy-s3-object-from-one-bucket-to-another-using-python-boto3

    :param request: the aiohttp Request, with the body containing the target bucket and key, and the match_info
    containing the source volume, bucket, and key (required). The key may be a file or a folder, and in the latter
    case the entire folder's contents are copied.
    :param activity_cb: optional coroutine that is called when potentially relevant activity occurred.
    :param copy_object_completed_cb: called after successfully completing the copy of each object (optional). The
    callable must be reentrant. Its four parameters are source bucket name, source key, target bucket name, and target
    key.
    :return: the HTTP response. If successful, the response will have status code 201, and a Location header will be
    set with the URL for the copy target.
    :raises HTTPBadRequest: if preflight fails.
    """
    logger = logging.getLogger(__name__)
    volume_id = request.match_info['volume_id']
    sub = request.headers.get(SUB, NONE_USER)
    try:
        source_bucket_name, source_key = await _extract_source(request.match_info)
        if 'path' in request.url.query:
            source_path: list[str] | None = request.url.query.getall('path')
        else:
            source_path = None
        source_volume_id = volume_id
        target_url, target_bucket_name, target_folder_key, target_volume_id, target_path = await _copy_object_extract_target(await request.json())
    except (web.HTTPBadRequest, orjson.JSONDecodeError, ValueError) as e:
        logger.exception(e)
        return response.status_bad_request(str(e))

    async with DesktopObjectActionLifecycle(request=request,
                                            code='hea-duplicate',
                                            description=f'Copying {s3_object_message_display_name(source_bucket_name, source_key)} to {s3_object_message_display_name(target_bucket_name, target_folder_key)}',
                                            activity_cb=activity_cb) as activity:
        async with S3ClientContext(request=request, volume_id=volume_id) as s3_client:
            logger.debug('Copy requested from %s/%s to %s/%s', source_bucket_name, source_key, target_bucket_name,
                         target_folder_key)
            activity.old_context_dependent_object_path = source_path
            activity.old_object_id = encode_key(source_key)
            type_path_part = _type_path_part_from_request_path(request, activity)
            activity.old_object_display_name = display_name(source_key)
            activity.old_volume_id = source_volume_id
            activity.old_object_uri = f'volumes/{source_volume_id}/buckets/{source_bucket_name}/{type_path_part}/{activity.old_object_id}'
            if type_path_part == 'awss3projects':
                activity.old_object_description = await get_description(sub, s3_client, source_bucket_name, source_key)
            resp = await _copy_object(s3_client, source_bucket_name, source_key, target_bucket_name,
                                      target_folder_key, copy_completed_cb=copy_object_completed_cb)
            if resp.status == 201:
                target_id = encode_key(replace_parent_folder(source_key, target_folder_key, parent(source_key)))
                activity.new_context_dependent_object_path = target_path
                activity.new_object_id = target_id
                activity.new_object_type_name = activity.old_object_type_name
                activity.new_object_uri = f'volumes/{target_volume_id}/buckets/{target_bucket_name}/{type_path_part}/{target_id}'
                activity.new_object_display_name = display_name(activity.old_object_display_name)
                activity.new_object_description = activity.old_object_description
                activity.new_volume_id = target_volume_id
                resp.headers[hdrs.LOCATION] = target_url
            else:
                activity.status = Status.FAILED
            return resp

def _type_path_part_from_request_path(request: Request, activity: DesktopObjectAction) -> str:
    request_path = request.url.path
    if '/awss3files/' in request_path:
        activity.old_object_type_name = AWSS3FileObject.get_type_name()
        type_path_part = 'awss3files'
    elif '/awss3folders/' in request_path:
        activity.old_object_type_name = AWSS3Folder.get_type_name()
        type_path_part = 'awss3folders'
    else:
        assert '/awss3projects/' in request_path, f'Unexpected path {request_path}'
        activity.old_object_type_name = AWSS3Project.get_type_name()
        type_path_part = 'awss3projects'
    return type_path_part

async def copy_object_async(request: Request, status_location: URL | str,
                            activity_cb: Callable[[Application, DesktopObjectAction], Awaitable[None]] | None = None,
                            done_cb: Callable[[Response], Awaitable[None]] | None = None,
                            copy_object_completed_cb: Callable[[str, str, str, str], Awaitable[None]] | None = None) -> Response:
    """
    copy/paste (duplicate), throws error if destination exists, this so an overwrite isn't done
    throws another error is source doesn't exist
    https://medium.com/plusteam/move-and-rename-objects-within-an-s3-bucket-using-boto-3-58b164790b78
    https://stackoverflow.com/questions/47468148/how-to-copy-s3-object-from-one-bucket-to-another-using-python-boto3

    :param request: the aiohttp Request, with the body containing the target bucket and key, and the match_info
    containing the source volume, bucket, and key. (required).
    :param activity_cb: optional coroutine that is called when potentially relevant activity occurred.
    :param done_cb: called after successfully completing the entire copy operation (optional).
    :param copy_object_completed_cb: called after successfully completing the copy of each object (optional). The
    callable must be reentrant. Its four parameters are source bucket name, source key, target bucket name, and target
    key.
    :return: the HTTP response.
    """
    sub = request.headers.get(SUB, NONE_USER)
    logger = logging.getLogger(__name__)
    volume_id = request.match_info['volume_id']
    try:
        source_bucket_name, source_key_name = await _extract_source(request.match_info)
        if 'path' in request.url.query:
            source_path: list[str] | None = request.url.query.getall('path')
        else:
            source_path = None
        target_url, target_bucket_name, target_folder_key, target_volume_id, target_path = await _copy_object_extract_target(await request.json())
    except (web.HTTPBadRequest, orjson.JSONDecodeError, ValueError) as e:
        logger.exception(e)
        return response.status_bad_request(str(e))

    if status_location is None:
        raise ValueError('status_location cannot be None')

    async def coro(app: Application):
        async with DesktopObjectActionLifecycle(request=request,
                                                code='hea-duplicate',
                                                user_id=sub,
                                                description=f'Copying {s3_object_message_display_name(source_bucket_name, source_key_name)} to {s3_object_message_display_name(target_bucket_name, target_folder_key)}',
                                                activity_cb=activity_cb) as activity:
            async with S3ClientContext(request=request, volume_id=volume_id) as s3_client:
                logger.debug('Copy requested from %s/%s to %s/%s', source_bucket_name, source_key_name, target_bucket_name,
                             target_folder_key)
                activity.old_context_dependent_object_path = source_path
                activity.old_object_id = encode_key(source_key_name)
                request_path = request.url.path
                if '/awss3files/' in request_path:
                    activity.old_object_type_name = AWSS3FileObject.get_type_name()
                    type_path_part = 'awss3files'
                elif '/awss3folders/' in request_path:
                    activity.old_object_type_name = AWSS3Folder.get_type_name()
                    type_path_part = 'awss3folders'
                else:
                    assert '/awss3projects/' in request_path, f'Unexpected path {request_path}'
                    activity.old_object_type_name = AWSS3Project.get_type_name()
                    type_path_part = 'awss3projects'
                activity.old_object_display_name = display_name(source_key_name)
                activity.old_volume_id = volume_id
                activity.old_object_uri = f'volumes/{volume_id}/buckets/{source_bucket_name}/{type_path_part}/{activity.old_object_id}'
                if type_path_part == 'awss3projects':
                    activity.old_object_description = await get_description(sub, s3_client, source_bucket_name, source_key_name)
                resp = await _copy_object(s3_client, source_bucket_name, source_key_name, target_bucket_name,
                                          target_folder_key, copy_completed_cb=copy_object_completed_cb)
                if resp.status == 201:
                    target_id = encode_key(replace_parent_folder(source_key_name, target_folder_key, parent(source_key_name)))
                    activity.new_context_dependent_object_path = target_path
                    activity.new_object_id = target_id
                    activity.new_object_type_name = activity.old_object_type_name
                    activity.new_object_uri = f'volumes/{target_volume_id}/buckets/{target_bucket_name}/{type_path_part}/{target_id}'
                    activity.new_object_display_name = display_name(activity.old_object_display_name)
                    activity.new_object_description = activity.old_object_description
                    activity.new_volume_id = target_volume_id
                    resp.headers[hdrs.LOCATION] = target_url
                else:
                    activity.status = Status.FAILED
                try:
                    if done_cb:
                        await done_cb(resp)
                except:
                    logger.exception('done_cb raised exception')
                return resp
    task_name = f'{sub}^{status_location}'
    await request.app[HEA_BACKGROUND_TASKS].add(coro, name=task_name)
    return response.status_see_other(status_location)


async def archive_object(request: Request,
                         activity_cb: Optional[Callable[[Application, DesktopObjectAction], Awaitable[None]]] = None) -> web.Response:
    """
    Archives object by performing a copy and changing storage class. This function is synchronous.
    :param request:
    :param activity_cb: optional coroutine that is called when potentially relevant activity occurred.
    :return: The HTTP response. If successful, the response will have a 201 status code, and a Location header will be
    set with the URL of the archived object.
    """
    logger = logging.getLogger(__name__)
    volume_id = request.match_info['volume_id']
    sub = request.headers.get(SUB, NONE_USER)
    try:
        source_bucket_name, source_key = await _extract_source(request.match_info)
        request_json = await request.json()
        storage_class = S3StorageClass[next(item['value'] for item in request_json['template']['data'] if item['name'] == 'storage_class')]
    except (web.HTTPBadRequest, orjson.JSONDecodeError, KeyError, ValueError) as e:
        logger.exception(e)
        return response.status_bad_request(str(e))

    async with DesktopObjectActionLifecycle(request,
                                            code='hea-archive',
                                            description=f'Archiving {s3_object_message_display_name(source_bucket_name, source_key)} to {storage_class.name}',
                                            activity_cb=activity_cb) as activity:
        activity.old_volume_id = volume_id
        activity.old_object_id = encode_key(source_key)
        activity.old_object_display_name = display_name(source_key)
        type_path_part = _type_path_part_from_request_path(request, activity)
        activity.old_object_uri = f'volumes/{volume_id}/buckets/{source_bucket_name}/{type_path_part}/{activity.old_object_id}'
        if 'path' in request.url.query:
            activity.old_context_dependent_object_path = request.url.query.getall('path')
        async with S3ClientContext(request=request, volume_id=volume_id) as s3_client:
            if type_path_part == 'awss3projects':
                activity.old_object_description = await get_description(sub, s3_client, source_bucket_name, source_key)
            resp = await _archive_object(s3_client, source_bucket_name, source_key, storage_class.name)
            if resp.status != 201:
                activity.status = Status.FAILED
            else:
                resp.headers[hdrs.LOCATION] = str(request.url)
                activity.new_volume_id = activity.old_volume_id
                activity.new_object_id = activity.old_object_id
                activity.new_object_description = activity.old_object_description
                activity.new_object_display_name = activity.old_object_display_name
                activity.new_object_type_name = activity.old_object_type_name
                activity.new_object_uri = activity.old_object_uri
                activity.new_context_dependent_object_path = activity.old_context_dependent_object_path
            return resp


_archive_lock = asyncio.Lock()
async def archive_object_async(request: Request, status_location: URL | str,
                               activity_cb: Optional[Callable[[Application, DesktopObjectAction], Awaitable[None]]] = None) -> web.Response:
    """
    Archives object by performing a copy and changing storage class. This function is synchronous.
    :param request:
    :param activity_cb: optional coroutine that is called when potentially relevant activity occurred.
    :return: The HTTP response. If successful, the response will have a 201 status code, and a Location header will be
    set with the URL of the archived object.
    """
    logger = logging.getLogger(__name__)
    sub = request.headers.get(SUB, NONE_USER)
    volume_id = request.match_info['volume_id']
    try:
        source_bucket_name, source_key = await _extract_source(request.match_info)
        request_json = await request.json()
        storage_class = next(
            item['value'] for item in request_json['template']['data'] if item['name'] == 'storage_class')

        if storage_class is None:
            raise ValueError('Null value recieved - storage_class must be a string')
        if not isinstance(storage_class, str):
            raise ValueError('storage_class must be a string')

    except (web.HTTPBadRequest, orjson.JSONDecodeError, KeyError, ValueError) as e:
        logger.exception(e)
        return response.status_bad_request(str(e))

    if status_location is None:
        raise ValueError('status_location cannot be None')

    task_name = f'{sub}^{status_location}'

    async def coro(app: Application):
        async with DesktopObjectActionLifecycle(request,
                                                code='hea-archive',
                                                description=f'Archiving {s3_object_message_display_name(source_bucket_name, source_key)} to {storage_class}',
                                                activity_cb=activity_cb) as activity:
            activity.old_volume_id = volume_id
            activity.old_object_id = encode_key(source_key)
            activity.old_object_display_name = display_name(source_key)
            type_path_part = _type_path_part_from_request_path(request, activity)
            activity.old_object_uri = f'volumes/{volume_id}/buckets/{source_bucket_name}/{type_path_part}/{activity.old_object_id}'
            if 'path' in request.url.query:
                activity.old_context_dependent_object_path = request.url.query.getall('path')
            async with S3ClientContext(request=request, volume_id=volume_id) as s3_client:
                if type_path_part == 'awss3projects':
                    activity.old_object_description = await get_description(sub, s3_client, source_bucket_name, source_key)
                resp = await _archive_object(s3_client, source_bucket_name, source_key, storage_class)
                if resp.status != 201:
                    activity.status = Status.FAILED
                else:
                    resp.headers[hdrs.LOCATION] = str(request.url)
                    activity.new_volume_id = activity.old_volume_id
                    activity.new_object_id = activity.old_object_id
                    activity.new_object_description = activity.old_object_description
                    activity.new_object_display_name = activity.old_object_display_name
                    activity.new_object_type_name = activity.old_object_type_name
                    activity.new_object_uri = activity.old_object_uri
                    activity.new_context_dependent_object_path = activity.old_context_dependent_object_path
                return resp
    async with _archive_lock:
        if request.app[HEA_BACKGROUND_TASKS].in_progress(task_name):
            return response.status_conflict(f'Archiving {s3_object_message_display_name(source_bucket_name, source_key)} is already in progress')
        await request.app[HEA_BACKGROUND_TASKS].add(coro, name=task_name)
    return response.status_see_other(status_location)


async def unarchive_object(request: Request,
                           activity_cb: Optional[Callable[[Application, DesktopObjectAction], Awaitable[None]]] = None,
                           skip_restore_already_in_progress=False,
                           error_if_not_restorable=False) -> web.Response:
    """
    This method will initiate the restoring of object to s3 and copy it back into s3. This function is asynchronous

    :param request: The aiohttp web request. It's expected to have the volume_id, bucket_id, and id in the match_info
    dictionary.
    :param activity_cb: optional coroutine that is called when potentially relevant activity occurred.
    :param skip_restore_already_in_progress: if True, will skip objects that are already in the process of being
    restored. If False, an error response will be returned in that case.
    :param error_if_not_restorable: if True, will return an error response if any object is not in a storage class that
    requires restoration. If False, such objects will be skipped.
    :return: the HTTP response.
    """
    logger = logging.getLogger(__name__)
    volume_id = request.match_info['volume_id']
    bucket_name = request.match_info['bucket_id']
    source_key_name = decode_key(request.match_info['id'])
    unarchive_info = await _extract_unarchive_params(await request.json())
    sub = request.headers.get(SUB, NONE_USER)
    async with DesktopObjectActionLifecycle(request=request,
                                            code='hea-unarchive',
                                            description=f'Requested unarchiving {s3_object_message_display_name(bucket_name, source_key_name)}',
                                            activity_cb=activity_cb) as activity:
        activity.old_volume_id = volume_id
        activity.old_object_id = encode_key(source_key_name)
        activity.old_object_display_name = display_name(source_key_name)
        type_path_part = _type_path_part_from_request_path(request, activity)
        activity.old_object_uri = f'volumes/{volume_id}/buckets/{bucket_name}/{type_path_part}/{activity.old_object_id}'
        if 'path' in request.url.query:
            activity.old_context_dependent_object_path = request.url.query.getall('path')
        async with S3ClientContext(request=request, volume_id=volume_id) as s3_client:
            if type_path_part == 'awss3projects':
                activity.old_object_description = await get_description(sub, s3_client, bucket_name, source_key_name)
            try:
                loop = asyncio.get_running_loop()

                async def gen():
                    async for obj_sum in list_objects(s3_client, bucket_id=bucket_name, prefix=source_key_name):
                        if obj_sum['Key'].endswith('/'):
                            continue
                        if obj_sum['StorageClass'] in (S3StorageClass.GLACIER.name, S3StorageClass.DEEP_ARCHIVE.name) and obj_sum.get('RestoreStatus') is None:
                            yield obj_sum
                        elif error_if_not_restorable:
                            raise response.status_bad_request(f"{s3_object_message_display_name(bucket_name, obj_sum['Key'])} is in a storage class that does not require restoration")

                async def item_processor(obj_sum):
                    logger.debug('Initiating restore of obj: %s', obj_sum['Key'])
                    r_params = {'Days': unarchive_info.days if unarchive_info.days else 7,
                                'GlacierJobParameters': {
                                    'Tier': unarchive_info.restore_tier.name if unarchive_info.restore_tier else 'Standard'}}
                    try:
                        p = partial(s3_client.restore_object, Bucket=bucket_name, Key=obj_sum['Key'], RestoreRequest=r_params)
                        async def is_restore_underway() -> bool:
                            obj_meta = await asyncio.to_thread(s3_client.head_object, Bucket=bucket_name, Key=obj_sum['Key'])
                            logger.debug('Object %s restore status: %s', obj_sum['Key'], obj_meta.get('Restore'))
                            return obj_meta.get('Restore') is not None
                        await loop.run_in_executor(None, p)
                        while not await is_restore_underway():
                            await asyncio.sleep(1)
                    except BotoClientError as e:
                        if skip_restore_already_in_progress and client_error_code(e) == CLIENT_ERROR_RESTORE_ALREADY_IN_PROGRESS:
                            logger.debug('Restore already in progress for %s', obj_sum['Key'])
                        else:
                            raise
                await queued_processing(gen(), item_processor)
            except BotoClientError as e:
                activity.status = Status.FAILED
                return response.status_bad_request(str(e))
        activity.new_volume_id = activity.old_volume_id
        activity.new_object_id = activity.old_object_id
        activity.new_object_description = activity.old_object_description
        activity.new_object_display_name = activity.old_object_display_name
        activity.new_object_type_name = activity.old_object_type_name
        activity.new_object_uri = activity.old_object_uri
        activity.new_context_dependent_object_path = activity.old_context_dependent_object_path
    return web.HTTPAccepted()


async def delete_object(mongo_client: Mongo, request: Request, recursive=False,
                        activity_cb: Callable[[Application, DesktopObjectAction], Awaitable[None]] | None = None,
                        delete_completed_cb: Callable[[str, str, str | None], Awaitable[None]] | None = None) -> Response:
    """
    Deletes a single object. The volume id must be in the volume_id entry of the request's match_info dictionary. The
    bucket id must be in the bucket_id entry of the request's match_info dictionary. The item id must be in the id
    entry of the request's match_info dictionary. An optional folder id may be passed in the folder_id entry of the
    request's match_info_dictinary.

    :param request: the aiohttp Request (required).
    :param object_type: only delete the requested object only if it is a file or only if it is a folder. Pass in
    ObjectType.ANY or None (the default) to signify that it does not matter.
    :param recursive: if True, and the object is a folder, this function will delete the folder and all of its
    contents, otherwise it will return a 400 error if the folder is not empty. If the object to delete is not a folder,
    this flag will have no effect.
    :param activity_cb: optional awaitable that is called when potentially relevant activity occurred.
    :param delete_completed_cb: optional awaitable that is called upon successful deletion of an object. The callback
    must accept three positional parameters: bucket name, object key, and object version if applicable.
    :return: the HTTP response with a 204 status code if the item was successfully deleted, 403 if access was denied,
    404 if the item was not found, or 500 if an internal error occurred.
    """
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.delete_object
    # TODO: bucket.object_versions.filter(Prefix="myprefix/").delete()     add versioning option like in the delete bucket?
    if 'volume_id' not in request.match_info:
        return response.status_bad_request('volume_id is required')
    if 'bucket_id' not in request.match_info:
        return response.status_bad_request('bucket_id is required')
    if 'id' not in request.match_info:
        return response.status_bad_request('id is required')
    sub = request.headers.get(SUB, NONE_USER)
    bucket_name = request.match_info['bucket_id']
    encoded_key = request.match_info['id']
    volume_id = request.match_info['volume_id']
    encoded_folder_key = request.match_info.get('folder_id', None)
    try:
        key = decode_key(encoded_key)
    except KeyDecodeException:
        return response.status_not_found()

    async with S3ClientContext(request=request, volume_id=volume_id) as s3_client:
        folder_key = decode_folder(encoded_folder_key) if encoded_folder_key is not None else None
        if folder_key is None and encoded_folder_key is not None:
            return response.status_bad_request(f'Invalid folder_id {encoded_folder_key}')
        async with DesktopObjectActionLifecycle(request=request,
                                                code='hea-delete',
                                                description=f'Deleting {s3_object_message_display_name(bucket_name, key)}',
                                                activity_cb=activity_cb) as activity:
            if encoded_folder_key is not None and not is_object_in_folder(key, folder_key):
                loop = asyncio.get_running_loop()
                return await return_bucket_status_or_not_found(bucket_name, loop, s3_client)
            activity.old_volume_id = volume_id
            activity.old_object_id = encoded_key
            activity.old_object_display_name = display_name(key)
            type_path_part = _type_path_part_from_request_path(request, activity)
            if 'path' in request.url.query:
                activity.old_context_dependent_object_path = request.url.query.getall('path')
            activity.old_object_uri = f'volumes/{volume_id}/buckets/{bucket_name}/{type_path_part}/{encoded_key}'
            _delete_object_coro = _delete_object(request, s3_client, mongo_client, volume_id, bucket_name, key, recursive, activity_cb=activity_cb,
                                                 delete_completed_cb=delete_completed_cb)
            if type_path_part == 'awss3projects':
                resp, desc = await asyncio.gather(_delete_object_coro, get_description(sub, s3_client, bucket_name, key))
                activity.old_object_description = desc
            else:
                resp = await _delete_object_coro
            if resp.status != 204:
                activity.status = Status.FAILED
            return resp

_delete_lock = asyncio.Lock()
async def delete_object_async(mongo_client: Mongo, request: Request, status_location: URL | str, recursive=False,
                              activity_cb: Optional[
                                  Callable[[Application, DesktopObjectAction], Awaitable[None]]] = None,
                              done_cb: Callable[[Response], Awaitable[None]] | None = None,
                              delete_completed_cb: Callable[[str, str, str | None], Awaitable[None]] | None = None) -> Response:
    """
    Deletes a single object. The volume id must be in the volume_id entry of the request's match_info dictionary. The
    bucket id must be in the bucket_id entry of the request's match_info dictionary. The item id must be in the id
    entry of the request's match_info dictionary. An optional folder id may be passed in the folder_id entry of the
    request's match_info_dictinary.

    :param request: the aiohttp Request (required).
    :param object_type: only delete the requested object only if it is a file or only if it is a folder. Pass in
    ObjectType.ANY or None (the default) to signify that it does not matter.
    :param recursive: if True, and the object is a folder, this function will delete the folder and all of its
    contents, otherwise it will return a 400 error if the folder is not empty. If the object to delete is not a folder,
    this flag will have no effect.
    :param activity_cb: optional awaitable that is called when potentially relevant activity occurred.
    :param done_cb: optional awaitable that is called after successful completion of this operation.
    :param delete_completed_cb: optional awaitable that is called upon successful deletion of an object. The callback
    must accept three positional parameters: bucket name, object key, and object version if applicable.
    :return: the HTTP response with a 204 status code if the item was successfully deleted, 403 if access was denied,
    404 if the item was not found, or 500 if an internal error occurred.
    """
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.delete_object
    # TODO: bucket.object_versions.filter(Prefix="myprefix/").delete()     add versioning option like in the delete bucket?
    logger = logging.getLogger(__name__)
    sub = request.headers.get(SUB, NONE_USER)
    if 'volume_id' not in request.match_info:
        return response.status_bad_request('volume_id is required')
    if 'bucket_id' not in request.match_info:
        return response.status_bad_request('bucket_id is required')
    if 'id' not in request.match_info:
        return response.status_bad_request('id is required')

    bucket_name = request.match_info['bucket_id']
    encoded_key = request.match_info['id']
    volume_id = request.match_info['volume_id']
    encoded_folder_key = request.match_info.get('folder_id', None)
    try:
        key = decode_key(encoded_key)
    except KeyDecodeException:
        return response.status_not_found()


    async with S3ClientContext(request=request, volume_id=volume_id) as s3_client:
        folder_key = decode_folder(encoded_folder_key) if encoded_folder_key is not None else None
        if folder_key is not None and not is_object_in_folder(key, folder_key):
            loop = asyncio.get_running_loop()
            return await return_bucket_status_or_not_found(bucket_name, loop, s3_client)

    async def coro(app: Application):
        async with DesktopObjectActionLifecycle(request=request,
                                                code='hea-delete',
                                                description=f'Deleting {s3_object_message_display_name(bucket_name, key)}',
                                                activity_cb=activity_cb) as activity:
            activity.old_volume_id = volume_id
            activity.old_object_id = encoded_key
            activity.old_object_display_name = display_name(key)
            if 'path' in request.query:
                activity.old_context_dependent_object_path = request.query.getall('path')
            type_path_part = _type_path_part_from_request_path(request, activity)
            async with S3ClientContext(request=request, volume_id=volume_id) as s3_client:
                if 'path' in request.url.query:
                    activity.old_context_dependent_object_path = request.url.query.getall('path')
                activity.old_object_uri = f'volumes/{volume_id}/buckets/{bucket_name}/{type_path_part}/{encoded_key}'

                _delete_object_coro = _delete_object(request, s3_client, mongo_client, volume_id, bucket_name, key, recursive,
                                                     activity_cb=activity_cb, delete_completed_cb=delete_completed_cb)
                if type_path_part == 'awss3projects':
                    resp, desc = await asyncio.gather(_delete_object_coro, get_description(sub, s3_client, bucket_name, key))
                    activity.old_object_description = desc
                else:
                    resp = await _delete_object_coro
                if resp.status != 204:
                    activity.status = Status.FAILED
                try:
                    if done_cb:
                        await done_cb(resp)
                except:
                    logger.exception('done_cb raised exception')
                return resp
    task_name = f'{sub}^{status_location}'
    async with _delete_lock:
        if request.app[HEA_BACKGROUND_TASKS].in_progress(task_name):
            return response.status_conflict(f'Deleting {s3_object_message_display_name(bucket_name, key)} is already in progress')
        await request.app[HEA_BACKGROUND_TASKS].add(coro, name=task_name)
    return response.status_see_other(status_location)


# def transfer_object_between_account():
#     """
#     https://markgituma.medium.com/copy-s3-bucket-objects-across-separate-aws-accounts-programmatically-323862d857ed
#     """
#     # TODO: use update_bucket_policy to set up "source" bucket policy correctly
#     """
#     {
#     "Version": "2012-10-17",
#     "Id": "Policy1546558291129",
#     "Statement": [
#         {
#             "Sid": "Stmt1546558287955",
#             "Effect": "Allow",
#             "Principal": {
#                 "AWS": "arn:aws:iam::<AWS_IAM_USER>"
#             },
#             "Action": [
#               "s3:ListBucket",
#               "s3:GetObject"
#             ],
#             "Resource": "arn:aws:s3:::<SOURCE_BUCKET>/",
#             "Resource": "arn:aws:s3:::<SOURCE_BUCKET>/*"
#         }
#     ]
#     }
#     """
#     # TODO: use update_bucket_policy to set up aws "destination" bucket policy
#     """
#     {
#     "Version": "2012-10-17",
#     "Id": "Policy22222222222",
#     "Statement": [
#         {
#             "Sid": "Stmt22222222222",
#             "Effect": "Allow",
#             "Principal": {
#                 "AWS": [
#                   "arn:aws:iam::<AWS_IAM_DESTINATION_USER>",
#                   "arn:aws:iam::<AWS_IAM_LAMBDA_ROLE>:role/
#                 ]
#             },
#             "Action": [
#                 "s3:ListBucket",
#                 "s3:PutObject",
#                 "s3:PutObjectAcl"
#             ],
#             "Resource": "arn:aws:s3:::<DESTINATION_BUCKET>/",
#             "Resource": "arn:aws:s3:::<DESTINATION_BUCKET>/*"
#         }
#     ]
#     }
#     """
#     # TODO: code
#     source_client = boto3.client('s3', "SOURCE_AWS_ACCESS_KEY_ID", "SOURCE_AWS_SECRET_ACCESS_KEY")
#     source_response = source_client.get_object(Bucket="SOURCE_BUCKET", Key="OBJECT_KEY")
#     destination_client = boto3.client('s3', "DESTINATION_AWS_ACCESS_KEY_ID", "DESTINATION_AWS_SECRET_ACCESS_KEY")
#     destination_client.upload_fileobj(source_response['Body'], "DESTINATION_BUCKET",
#                                       "FOLDER_LOCATION_IN_DESTINATION_BUCKET")


# async def rename_object(request: Request, volume_id: str, object_path: str, new_name: str):
#     """
#     BOTO3, the copy and rename is the same
#     https://medium.com/plusteam/move-and-rename-objects-within-an-s3-bucket-using-boto-3-58b164790b78
#     https://stackoverflow.com/questions/47468148/how-to-copy-s3-object-from-one-bucket-to-another-using-python-boto3
#
#     :param request: the aiohttp Request (required).
#     :param volume_id: the id string of the volume representing the user's AWS account.
#     :param object_path: (str) path to object, includes both bucket and key values
#     :param new_name: (str) value to rename the object as, will only replace the name not the path. Use transfer object for that
#     """
#     # TODO: check if ACL stays the same and check existence
#     try:
#         s3_resource = await request.app[HEA_DB].get_resource(request, 's3', volume_id)
#         copy_source = {'Bucket': object_path.partition("/")[0], 'Key': object_path.partition("/")[2]}
#         bucket_name = object_path.partition("/")[0]
#         old_name = object_path.rpartition("/")[2]
#         s3_resource.meta.client.copy(copy_source, bucket_name,
#                                      object_path.partition("/")[2].replace(old_name, new_name))
#     except ClientError as e:
#         logging.error(e)


handle_client_error = _handle_client_error


async def list_objects(s3: S3Client,
                       bucket_id: str,
                       prefix: str | None = None,
                       max_keys: int | None = None,
                       loop: AbstractEventLoop | None = None,
                       delimiter: str | None = None,
                       include_restore_status: bool | None = None) -> AsyncIterator[Mapping[str, Any]]:
    if not loop:
        loop_ = asyncio.get_running_loop()
    else:
        loop_ = loop
    list_partial = partial(s3.get_paginator('list_objects_v2').paginate, Bucket=bucket_id)
    if max_keys is not None:
        list_partial = partial(list_partial, PaginationConfig={'MaxItems': max_keys})
    if prefix is not None:  # Boto3 will raise an exception if Prefix is set to None.
        list_partial = partial(list_partial, Prefix=prefix)
    if delimiter is not None:
        list_partial = partial(list_partial, Delimiter=delimiter)
    if include_restore_status is not None and include_restore_status:
        list_partial = partial(list_partial, OptionalObjectAttributes=['RestoreStatus'])
    pages = await loop_.run_in_executor(None, lambda: iter(list_partial()))
    while (page := await loop_.run_in_executor(None, next, pages, None)) is not None:
        for common_prefix in page.get('CommonPrefixes', []):
            yield common_prefix
        for content in page.get('Contents', []):
            yield content


async def list_unarchived_objects(request: web.Request, volume_id: str, bucket_id: str, prefix: str,
                                  loop: asyncio.AbstractEventLoop | None = None) -> AsyncIterator[Mapping[str, Any]]:
    """
    Lists all unarchived objects in the given bucket with the given prefix, ignoring folder objects.

    :param request: the aiohttp Request (required).
    :param volume_id: the id of the volume representing the user's AWS account (required).
    :param bucket_id: the id of the bucket to list objects from (required).
    :param prefix: the key of the object to list versions for (required).
    :param loop: the event loop to use (optional).
    :return: an async iterator over the archived objects.
    """
    async with aws.S3ClientContext(request=request, volume_id=volume_id) as s3_client:
        async for obj in list_objects(s3_client, bucket_id, prefix=prefix, loop=loop, include_restore_status=True):
            if not is_folder(obj['Key']) and not is_archived(obj):
                yield obj


async def list_object_versions_and_delete_markers(s3: S3Client, bucket_id: str, prefix: str | None = None,
                               loop: asyncio.AbstractEventLoop | None = None,
                               max_keys: int | None = None,
                               include_restore_status: bool | None = None,
                               delimiter: str | None = None) -> AsyncIterator[ListObjectVersionsOutputTypeDef]:
    if not loop:
        loop_ = asyncio.get_running_loop()
    else:
        loop_ = loop
    list_partial = partial(s3.get_paginator('list_object_versions').paginate, Bucket=bucket_id)
    if max_keys is not None:
        list_partial = partial(list_partial, PaginationConfig={'MaxItems': max_keys})
    if prefix is not None:  # Boto3 will raise an exception if Prefix is set to None.
        list_partial = partial(list_partial, Prefix=prefix)
    if delimiter is not None:
        list_partial = partial(list_partial, Delimiter=delimiter)
    if include_restore_status is not None and include_restore_status:
        list_partial = partial(list_partial, OptionalObjectAttributes=['RestoreStatus'])
    pages = await loop_.run_in_executor(None, lambda: iter(list_partial()))
    while (page := await loop_.run_in_executor(None, next, pages, None)) is not None:
        yield page


async def list_object_versions(s3: S3Client, bucket_id: str, prefix: str | None = None,
                               loop: asyncio.AbstractEventLoop | None = None,
                               max_keys: int | None = None,
                               include_restore_status: bool | None = None,
                               delimiter: str | None = None,
                               sort: SortOrder | None = None) -> AsyncIterator[ObjectVersionTypeDef]:
    """
    Gets all versions of non-deleted objects with the given prefix, up to that object's first delete marker, in the
    specified order.

    :param s3: an S3 client (required).
    :param bucket_id: the bucket id (required).
    :param prefix: the key prefix. Will get all keys in the bucket if unspecified.
    :param loop: the event loop. Will use the current running loop if unspecified.
    :param max_keys: the maximum number of keys to return. If None, will return 1000 keys.
    :param include_restore_status: if True, will include the restore status of the objects in the response.
    :param delimiter: if specified, will only return objects with the given delimiter in their key
    :param sort: a sort order for returned values, if desired. None means undefined sort order.
    :return: an asynchronous iterator of dicts with the following shape:
            'ETag': 'string',
            'ChecksumAlgorithm': [
                'CRC32'|'CRC32C'|'SHA1'|'SHA256',
            ],
            'Size': 123,
            'StorageClass': 'STANDARD',
            'Key': 'string',
            'VersionId': 'string',
            'IsLatest': True|False,
            'LastModified': datetime(2015, 1, 1),
            'Owner': {
                'DisplayName': 'string',
                'ID': 'string'
            }
    """
    logger = logging.getLogger(__name__)
    logger.debug('Listing object versions for bucket %s with prefix %s', bucket_id, prefix)
    async for page in list_object_versions_and_delete_markers(s3, bucket_id=bucket_id, prefix=prefix, loop=loop,
                                                              max_keys=max_keys,
                                                              include_restore_status=include_restore_status,
                                                              delimiter=delimiter):
        # Assumes that all versions and delete markers for a key are in a single page. This seems to be the case, but
        # there is no documentation to confirm it, so this may need to change. Dealing with multiple pages would be
        # extremely resource intensive, so hopefully we will not have to do that.
        def iterable() -> Iterator[ObjectVersionTypeDef]:
            for _, group in groupby(_ordered_object_versions_and_delete_markers(page, sort=SortOrder.DESC),
                                    key=itemgetter('Key')):
                prev: ObjectVersionTypeDef | None = None
                for v_or_d in group:
                    if prev is not None:
                        yield prev
                        prev = None
                    if 'Size' in v_or_d:  # This is an object version.
                        prev = cast(ObjectVersionTypeDef, v_or_d)
                    else:
                        break
                else:
                    if prev:
                        yield prev
        if sort == SortOrder.DESC:
            for obj in iterable():
                yield obj
        else:
            for obj in sorted(iterable(), key=itemgetter('Key', 'LastModified')):
                yield obj


async def list_deleted_object_versions(s3: S3Client, bucket_id: str, prefix: str | None = None,
                                       loop: asyncio.AbstractEventLoop | None = None,
                                       max_keys: int | None = None,
                                       include_restore_status: bool | None = None,
                                       delimiter: str | None = None,
                                       sort: SortOrder | None = None) -> AsyncIterator[tuple[DeleteMarkerEntryTypeDef, ObjectVersionTypeDef]]:
    """
    Returns all object versions immediately followed by a delete marker.

    :param s3: an S3 client (required).
    :param bucket_id: the bucket id (required).
    :param prefix: the key prefix. Will get all keys in the bucket if unspecified.
    :param loop: the event loop. Will use the current running loop if unspecified.
    :param max_keys: the maximum number of keys to return. If None, will return 1000 keys.
    :param include_restore_status: whether to include the restore status of deleted objects.
    :param delimiter: the delimiter to use for grouping keys.
    :param sort: the sort order to use for the results.
    :return: an asynchronous iterator of tuples, where each tuple contains a delete marker and the first object version
    before it.
    """
    logger = logging.getLogger(__name__)
    logger.debug('Listing object versions for bucket %s with prefix %s', bucket_id, prefix)
    async for page in list_object_versions_and_delete_markers(s3, bucket_id=bucket_id, prefix=prefix, loop=loop,
                                                              max_keys=max_keys,
                                                              include_restore_status=include_restore_status,
                                                              delimiter=delimiter):
        # Assumes that all versions and delete markers for a key are in a single page. This seems to be the case, but
        # there is no documentation to confirm it, so this may need to change. Dealing with multiple pages would be
        # extremely resource intensive, so hopefully we will not have to do that.
        def iterable() -> Iterator[tuple[DeleteMarkerEntryTypeDef, ObjectVersionTypeDef]]:
            for _, group in groupby(_ordered_object_versions_and_delete_markers(page, sort=SortOrder.DESC),
                                    key=itemgetter('Key')):
                deleted: DeleteMarkerEntryTypeDef | None = None
                for v_or_d in group:
                    if deleted and 'Size' in v_or_d:
                        yield (deleted, v_or_d)  # type: ignore[misc]
                        deleted = None  # Only yield the first version after the delete marker.
                    if 'Size' not in v_or_d:
                        deleted = cast(DeleteMarkerEntryTypeDef, v_or_d)
        if sort == SortOrder.DESC:
            for obj in iterable():
                yield obj
        else:
            for obj in sorted(iterable(), key=lambda x: (x[1]['Key'], x[1]['LastModified'])):
                yield obj

def _object_versions_and_delete_markers(page: ListObjectVersionsOutputTypeDef) -> Iterable[ObjectVersionTypeDef | DeleteMarkerEntryTypeDef]:
    """
    Returns the object versions and delete markers. They can be distinguished by checking the 'Size' key: if it is
    not present, the entry is a delete marker. If it is present, the entry is a version.

    :param page: the page of object versions and delete markers.
    :return: an iterable of object versions and delete markers.
    """
    versions = page.get('Versions', [])
    delete_markers = page.get('DeleteMarkers', [])
    return chain(versions, delete_markers)


def _ordered_object_versions_and_delete_markers(page: ListObjectVersionsOutputTypeDef, sort: SortOrder | None) -> Iterable[ObjectVersionTypeDef | DeleteMarkerEntryTypeDef]:
    """
    Orders the object versions and delete markers in timestamped order. They can be distinguished by checking
    the 'Size' key: if it is not present, the entry is a delete marker. If it is present, the entry is a version.

    :param page: the page of object versions and delete markers.
    :param sort: a sort order for returned values, if desired. None means undefined sort order.
    :return: a list of object versions and delete markers in the requested order.
    """
    # sorted won't touch the order of items that seem already ordered, even to reverse them. So, we get everything into
    # the reverse order in which the versions and delete markers were returned, and then reverse them if ascending
    # order is requested.
    reverse = bool(sort.reverse() if sort else None)
    sorted_ = sorted(_object_versions_and_delete_markers(page), key=itemgetter('LastModified'), reverse=reverse)
    sorted_.sort(key=itemgetter('Key'))
    return sorted_


async def get_latest_object_version(s3: S3Client, bucket_id: str, key: str,
                                    loop: asyncio.AbstractEventLoop | None = None) -> ObjectVersionTypeDef | None:
    """
    Gets the latest version of an object in the given bucket with the given key.

    :param s3: an S3 client (required).
    :param bucket_id: the bucket id (required).
    :param key: the key of the object (required).
    :param loop: the event loop. Will use the current running loop if unspecified.
    :return: the latest version of the object, or None if the object does not exist.
    """
    list_object_versions_ = partial(list_object_versions, s3, bucket_id=bucket_id, prefix=key,
                                    loop=loop, max_keys=1, sort=SortOrder.DESC)
    return await anext((obj async for obj in list_object_versions_() if obj['IsLatest']), None)


def decode_folder(folder_id_: str) -> str | None:
    """
    Decodes a folder id to an S3 key.

    :param folder_id_: the folder id. A value of 'root' is decoded to the empty string.
    :return: the folder's key, or None if the id is invalid.
    """
    if folder_id_ == ROOT_FOLDER.id:
        folder_id = ''
    else:
        try:
            folder_id = decode_key(folder_id_)
            if not is_folder(folder_id):
                folder_id = None
        except KeyDecodeException:
            # Let the bucket query happen so that we consistently return Forbidden if the user lacks permissions
            # for the bucket.
            folder_id = None
    return folder_id


async def return_bucket_status_or_not_found(bucket_name: str, loop: AbstractEventLoop, s3: S3Client) -> HTTPException:
    """
    Checks for the bucket's existence for the purpose of determining which HTTP response to send if an object was not
    found. If the bucket does not exist, or the bucket exists and the user has access to it, return a 404 response. If
    the bucket exists but attempting to access it failed, return a response with an appropriate status code.

    :param bucket_name: the bucket's name.
    :param loop: optional loop, otherwise the currently running loop is used.
    :param s3: an S3 client.
    :return: an HTTP exception.
    """
    if loop is None:
        loop = asyncio.get_running_loop()
    try:
        await loop.run_in_executor(None, partial(s3.head_bucket, Bucket=bucket_name))
        return response.status_not_found()
    except BotoClientError as e:
        return handle_client_error(e)


async def is_versioning_enabled(s3: S3Client, bucket_id: str,
                                loop: asyncio.AbstractEventLoop | None = None) -> bool:
    """
    Returns true if versioning is either enabled or suspended. In other words, this function returns True if there
    may be versions to retrieve.

    :param s3: the S3 client (required).
    :param loop: optional event loop. If None or unspecified, the running loop will be used.
    :return: True if versioning is enabled or suspended, False otherwise.
    """
    if not loop:
        loop_ = asyncio.get_running_loop()
    else:
        loop_ = loop
    response = await loop_.run_in_executor(None, partial(s3.get_bucket_versioning, Bucket=bucket_id))
    return 'Status' in response


_description_cache = TTLCache[tuple[str, str, str | None], str](maxsize=1000, ttl=30)
_description_locks = defaultdict[str, asyncio.Lock](asyncio.Lock)

async def get_description(sub: str, s3_client: S3Client, bucket_name: str, project_key: str | None, ignore_cache=False) -> str | None:
    if project_key is None:
        return None
    async with _description_locks[sub]:
        cache_key = (sub, bucket_name, project_key)
        cached_value = _description_cache.get(cache_key)
        if cached_value and not ignore_cache:
            return cached_value
        else:
            loop = asyncio.get_running_loop()
            def download_readme():
                readme_key = join(project_key, 'README')
                with BytesIO() as fd:
                    s3_client.download_fileobj(Bucket=bucket_name, Key=readme_key, Fileobj=fd)
                    return fd.getvalue().decode()
            try:
                desc = await loop.run_in_executor(None, download_readme)
                _description_cache[cache_key] = desc
                return desc
            except BotoClientError as e:
                match client_error_status(e)[0]:
                    case 400:
                        return 'Description is unavailable because the project\'s README is archived.'
                    case 404:
                        return None
                    case _:
                        raise e


async def get_metadata(mongo_client: Mongo, bucket_name: str, id_: str, include_deleted=False) -> dict[str, Any] | None:
    if include_deleted:
        return await mongo_client.get_admin_nondesktop_object(MONGODB_AWS_S3_FOLDER_METADATA_COLLECTION, {'bucket_id': bucket_name, 'encoded_key': id_})
    else:
        return await mongo_client.get_admin_nondesktop_object(MONGODB_AWS_S3_FOLDER_METADATA_COLLECTION, {'bucket_id': bucket_name, 'encoded_key': id_,
                                                                                                        '$or': [{'deleted': False}, {'deleted': {'$exists': False}}]})

async def extend_path(mongo_client: Mongo, bucket_name_: str, base_key: str, key_: str, base: str) -> list[str]:
    remainder = key_
    keys: list[str] = []
    while len(remainder) > len(base_key):
        remainder = parent(remainder)
        #if remainder not in processed_keys:
        keys.append(remainder)
    rest_of_path: list[str] = []
    for k in reversed(keys):
        if mongo_client is not None:
            k_metadata = await get_metadata(mongo_client, bucket_name_, encode_key(key_))
        else:
            k_metadata = None
        type_part = 'awss3projects' if k_metadata is not None and k_metadata['actual_object_type_name'] == AWSS3Project.get_type_name() else 'awss3folders'
        rest_of_path.append(urlsafe_b64encode((base + f'/buckets/{bucket_name_}/{type_part}/{encode_key(k)}').encode('utf-8')).decode('utf-8'))
    return rest_of_path


def is_archived(obj: Mapping[str, Any]) -> bool:
    """
    Returns True if the object is archived, False otherwise.

    :param obj: the object to check.
    :return: True if the object is archived, False otherwise.
    """
    return obj.get('StorageClass') in (S3StorageClass.DEEP_ARCHIVE.name, S3StorageClass.GLACIER.name) and not (
        (restore := obj.get('RestoreStatus')) and restore.get('RestoreExpiryDate'))

def is_archived_head(obj: Mapping[str, Any]) -> bool:
    """
    Returns True if the object is archived when doing a head_object (not currently restored),
    False otherwise.
    """
    storage_class = obj.get("StorageClass")

    if storage_class not in (S3StorageClass.DEEP_ARCHIVE.name, S3StorageClass.GLACIER.name):
        return False

    restore_header = obj.get("Restore")

    if not restore_header:
        # No restore info → fully archived
        return True

    # Parse restore header
    ongoing_match = re.search(r'ongoing-request="(true|false)"', restore_header)
    expiry_match = re.search(r'expiry-date="([^"]+)"', restore_header)

    ongoing = ongoing_match and ongoing_match.group(1) == "true"
    expiry_str = expiry_match.group(1) if expiry_match else None

    if ongoing:
        return True

    if expiry_str:
        try:
            # Parse date in RFC 1123 / GMT format and make it timezone-aware
            expiry_dt = datetime.strptime(expiry_str, "%a, %d %b %Y %H:%M:%S %Z")
            if expiry_dt.tzinfo is None:
                expiry_dt = expiry_dt.replace(tzinfo=timezone.utc)
        except ValueError:
            expiry_dt = datetime.strptime(expiry_str, "%a, %d %b %Y %H:%M:%S")
            expiry_dt = expiry_dt.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        return expiry_dt < now  # Archived again if expired

    # If restore complete but no expiry date, treat as archived
    return True


async def fail_if_too_big(bucket_name: str, folder_key: str | None, activity: DesktopObjectAction,
                                     s3_client: S3Client):
    """
    Checks the size of the folder or bucket to ensure it does not exceed the maximum download size (5 GB).
    If the size exceeds the limit, raises a BadRequest error.

    :param bucket_name: the name of the S3 bucket (required).
    :param folder_key: the key of the folder to check. If None, checks the entire bucket.
    :param activity: the desktop object action to update with the status.
    :param s3_client: the S3 client to use for listing objects (required).
    :raises BadRequest: if the folder or bucket size exceeds the maximum download size.
    """
    preflight_size_in_bytes = 0
    async for obj in awsservicelib.list_objects(s3_client, bucket_name, folder_key):
        if not is_archived(obj) and (size := obj.get('Size', 0)):
            preflight_size_in_bytes += size
            if preflight_size_in_bytes > awsservicelib.MAX_FOLDER_DOWNLOAD_SIZE:
                activity.status = Status.FAILED
                raise response.status_bad_request(
                                f'{awsservicelib.s3_object_message_display_name(bucket_name, folder_key)} '
                                f'contains too many objects or is too big to download as a zip file. '
                                f'Please use the AWS S3 console to perform the download.')


async def _type_name_from_metadata(mongo_client: Mongo, bucket_name: str, id_: str) -> str:
    metadata = await get_metadata(mongo_client, bucket_name, id_)
    if metadata is not None:
        return metadata['actual_object_type_name']
    elif is_folder(id_):
        return AWSS3Folder.get_type_name()
    else:
        return AWSS3FileObject.get_type_name()


async def _delete_object(request: web.Request, s3_client: S3Client, mongo_client: Mongo, volume_id: str, bucket_name: str, key: str,
                         recursive: bool,
                         activity_cb: Callable[[Application, DesktopObjectAction], Awaitable[None]] | None = None,
                         delete_completed_cb: Callable[[str, str, str | None], Awaitable[None]] | None = None) -> Response:
    """
    Delete the object with the given key in the given bucket. If the key is a prefix, and recursive is True, delete
    all objects with the given prefix.

    :param s3_client: the S3 client (required).
    :param bucket_name: the bucket (required).
    :param key: the key or prefix (required).
    :param recursive: whether or not to treat the key as a prefix and delete all objects with the given prefix
    (required).
    :param delete_completed_cb: called upon successful deletion of an object. Must be reentrant. The callable must
    accept three positional parameters: bucket name, object key, and object version.
    :return: the HTTP response.
    """
    logger = logging.getLogger(__name__)
    logger.debug('Deleting key %s in bucket %s; recursively? %s', key, bucket_name, recursive)
    loop = asyncio.get_running_loop()
    sub = request.headers.get(SUB, NONE_USER)
    try:
        if key is None:
            return await return_bucket_status_or_not_found(bucket_name, loop, s3_client)

        class KeyAndVersion(NamedTuple):
            key: str
            version_id: str
        deleted_paths = set[str]()

        async def gen() -> AsyncIterator[KeyAndVersion]:
            root: KeyAndVersion | None = None
            key_is_folder = is_folder(key)
            async for obj in list_object_versions(s3_client, bucket_name, prefix=key, loop=loop, sort=SortOrder.DESC):
                logger.debug('Deleting %s: %s',obj['Key'], obj)
                if key_is_folder or key == obj['Key']:
                    if obj.get('IsLatest'):
                        if root is not None and not recursive:
                            raise response.status_bad_request(f'The folder {key} is not empty')
                        elif root is None:
                            root = KeyAndVersion(key=obj['Key'], version_id=obj['VersionId'])
                        else:
                            yield KeyAndVersion(key=obj['Key'], version_id=obj['VersionId'])
                else:
                    break
            if root is not None:
                yield root
            else:
                raise await return_bucket_status_or_not_found(bucket_name, loop, s3_client)

        async def item_processor(item: KeyAndVersion):

            async with DesktopObjectActionLifecycle(request=request,
                                            code='hea-delete-part',
                                            description=f'Deleting {s3_object_message_display_name(bucket_name, item.key)}',
                                            activity_cb=activity_cb) as activity:
                async def _populate_activity_fields():
                    activity.old_volume_id = volume_id
                    activity.old_object_id = encode_key(item.key)
                    activity.old_object_display_name = display_name(item.key)
                    activity.old_object_type_name = await _type_name_from_metadata(mongo_client, bucket_name, item.key)
                    if activity.old_object_type_name == AWSS3Project.get_type_name():
                        activity.old_object_description = await get_description(sub, s3_client, bucket_name, item.key)
                        type_path_part = 'awss3projects'
                    elif activity.old_object_type_name == AWSS3Folder.get_type_name():
                        type_path_part = 'awss3folders'
                    else:
                        type_path_part = 'awss3files'
                    activity.old_object_uri = f'volumes/{volume_id}/buckets/{bucket_name}/{type_path_part}/{activity.old_object_id}'
                    if 'path' in request.url.query:
                        activity.old_context_dependent_object_path = request.url.query.getall('path')
                await asyncio.gather(loop.run_in_executor(None, partial(s3_client.delete_object, Bucket=bucket_name, Key=item.key)),
                                     _populate_activity_fields())
                deleted_paths.add(item.key)
            path = item.key
            while path:
                if path not in deleted_paths:
                    async with DesktopObjectActionLifecycle(request=request,
                                                            code='hea-delete-part',
                                                            description=f'Deleting {s3_object_message_display_name(bucket_name, path)}',
                                                            activity_cb=activity_cb) as activity_part:
                        activity_part.old_volume_id = volume_id
                        activity_part.old_object_id = encode_key(path)
                        activity_part.old_object_display_name = display_name(path)
                        activity_part.old_object_type_name = await _type_name_from_metadata(mongo_client, bucket_name, activity_part.old_object_id)
                        if activity_part.old_object_type_name == AWSS3Project.get_type_name():
                            activity_part.old_object_description = await get_description(sub, s3_client, bucket_name, path)
                            type_path_part = 'awss3projects'
                        elif activity_part.old_object_type_name == AWSS3Folder.get_type_name():
                            type_path_part = 'awss3folders'
                        else:
                            type_path_part = 'awss3files'
                        activity_part.old_object_uri = f'volumes/{volume_id}/buckets/{bucket_name}/{type_path_part}/{activity_part.old_object_id}'
                        if activity.old_context_dependent_object_path:
                            prefix_url = urlsafe_b64decode(activity.old_context_dependent_object_path[-1]).decode('utf-8')
                            rest_of_path = await extend_path(mongo_client, bucket_name, key, path, prefix_url[:prefix_url.index('/buckets/')])
                            activity_part.old_context_dependent_object_path = activity.old_context_dependent_object_path + rest_of_path
                        else:
                            activity_part.old_context_dependent_object_path = activity.old_context_dependent_object_path
                        deleted_paths.add(path)
                path = parent(path)

            if delete_completed_cb:
                logger.debug('Calling delete_completed_cb for %s', item)
                await delete_completed_cb(bucket_name, item.key, item.version_id)
        await queued_processing(gen(), item_processor)
        return await response.delete(True)
    except BotoClientError as e:
        return handle_client_error(e)
    except HTTPException as e:
        # Return the exception/response rather than raise it.
        return e


async def _object_exists_with_prefix(s3_client: S3Client, bucket_name: str, prefix: str):
    """
    Return whether there are any objects with the given key prefix in the given bucket.

    :param s3_client: the S3 client (required).
    :param bucket_name: the bucket name (required).
    :param prefix: the key prefix (required).
    :raises BotoClientError: if an error occurs while checking the bucket and pre-existing objects.
    """
    # head_object doesn't 'see' folders, need to use list_objects to see if a folder exists.
    try:
        obj = await anext(list_objects(s3_client, bucket_id=bucket_name, prefix=prefix, max_keys=1), None)
        return obj is not None
    except BotoClientError as e:
        if aws.client_error_code(e) == aws.CLIENT_ERROR_NO_SUCH_BUCKET:
            return False
        else:
            raise


async def _object_exists(s3_client: S3Client, bucket_name: str, key: str):
    """
    Return whether there exists an object with the given key.

    :param s3_client: the S3 client (required).
    :param bucket_name: the bucket name (required).
    :param key: the key (required).
    :return: True if the object exists, False otherwise. If the bucket does not exist, returns False.
    :raises BotoClientError: if an error occurs while checking the bucket and object.
    """
    # head_object doesn't 'see' folders, need to use list_objects to see if a folder exists.
    try:
        obj = await anext(list_objects(s3_client, bucket_id=bucket_name, prefix=key, max_keys=1), None)
        return obj is not None and obj['Key'] == key
    except BotoClientError as e:
        if aws.client_error_code(e) == aws.CLIENT_ERROR_NO_SUCH_BUCKET:
            return False
        else:
            raise

async def _copy_object(s3_client: S3Client, source_bucket_name: str, source_key: str, target_bucket_name: str,
                       target_key: str,
                       copy_completed_cb: Callable[[str, str, str, str], Awaitable[None]] | None = None) -> web.Response:
    """
    :param s3_client: the s3 client to use (required).
    :param source_bucket_name: the original object's bucket (required).
    :param source_key: the original object's key (required).
    :param target_bucket_name: the copy's bucket (required).
    :param target_key: the expected key of the target's folder (required).
    :param copy_completed_cb: called after the object is successfully copied. For folders, it is called after each item
    in the folder is successfully copied. Accepts the following parameters: the original object's bucket, the original
    object's key, the copy's bucket, and the copy's key.
    """
    logger = logging.getLogger(__name__)

    # First, make sure the target is a folder
    if target_key and not is_folder(target_key):
        return response.status_bad_request(f'Target {display_name(target_key) or ""} is not a folder')

    # Next, make sure the source exists.
    if not await _object_exists_with_prefix(s3_client, source_bucket_name, source_key):
        return response.status_bad_request(f'Source {display_name(source_key) or ""} does not exist in bucket {source_bucket_name}')

    # Next make sure that the target folder exists.
    if target_key and not await _object_exists_with_prefix(s3_client, target_bucket_name, target_key):
        return response.status_bad_request(f'Target {display_name(target_key) or ""} does not exist in bucket {source_bucket_name}')

    # Next check if we would clobber something in the target location.
    key_to_check = replace_parent_folder(source_key, target_key, parent(source_key) if source_key else None)
    if await _object_exists_with_prefix(s3_client, target_bucket_name, key_to_check):
        return response.status_bad_request(
            f'{display_name(key_to_check) or ""} already exists in target bucket {target_bucket_name}')

    # Finally make sure that the target folder is not a subfolder of the source folder.
    if source_bucket_name == target_bucket_name and (target_key or '').startswith(source_key or ''):
        return response.status_bad_request(f'Target folder {display_name(target_key)} is a subfolder of {display_name(source_key)}')

    try:
        loop = asyncio.get_running_loop()

        async def _do_copy() -> AsyncIterator[asyncio.Future[None]]:
            source_key_folder = split(source_key)[0]
            def do_copy(source_key_, target_key_):
                s3_client.copy({'Bucket': source_bucket_name, 'Key': source_key_}, target_bucket_name, target_key_)
                return source_key_, target_key_
            logger.debug('Copying from bucket %s and prefix %s to bucket %s and target key %s', source_bucket_name, source_key, target_bucket_name, target_key)
            cached_values: list[Mapping[str, Any]] = []
            async for obj in list_objects(s3_client, source_bucket_name, prefix=source_key, include_restore_status=True):
                logger.debug('copy candidate: %s', obj)
                if is_archived(obj):
                    if is_folder(source_key):
                        raise response.status_bad_request(f'{s3_object_message_display_name(source_bucket_name, source_key)} contains archived objects')
                    else:
                        raise response.status_bad_request(f'{s3_object_message_display_name(source_bucket_name, source_key)} is archived')
                elif len(cached_values) < 1000:
                    cached_values.append(obj)
            if len(cached_values) <= 1000:
                for obj in cached_values:
                    source_key_ = obj['Key']
                    target_key_ = replace_parent_folder(source_key=source_key_, target_key=target_key, source_key_folder=source_key_folder)
                    logger.debug('Copying %s/%s to %s/%s', source_bucket_name, source_key_, target_bucket_name, target_key_)
                    yield loop.run_in_executor(None, do_copy, source_key_, target_key_)
            else:
                async for obj in list_objects(s3_client, source_bucket_name, prefix=source_key):
                    source_key_ = obj['Key']
                    target_key_ = replace_parent_folder(source_key=source_key_, target_key=target_key, source_key_folder=source_key_folder)
                    logger.debug('Copying %s/%s to %s/%s', source_bucket_name, source_key_, target_bucket_name, target_key_)
                    yield loop.run_in_executor(None, do_copy, source_key_, target_key_)

        async def process_item(item):
            source_key_, target_key_ = await item
            if copy_completed_cb:
                await copy_completed_cb(source_bucket_name, source_key_, target_bucket_name, target_key_)

        await queued_processing(_do_copy(), process_item)

        return web.HTTPCreated()
    except BotoClientError as e_:
        return handle_client_error(e_)
    except ValueError as e_:
        return response.status_internal_error(str(e_))


async def _archive_object(s3_client: S3Client, source_bucket_name: str, source_key_name: str,
                          storage_class: str) -> web.Response:
    logger = logging.getLogger(__name__)
    try:
        source_resp = s3_client.list_objects_v2(Bucket=source_bucket_name, Prefix=source_key_name.rstrip('/'),
                                                Delimiter="/")
        if not source_resp.get('CommonPrefixes', None):
            # key is either file or doesn't exist
            s3_client.head_object(Bucket=source_bucket_name,
                                  Key=source_key_name)  # check if source object exists, if not throws an exception
            source_key = source_key_name
        else:
            source_key = source_key_name if source_key_name.endswith('/') else f"{source_key_name}/"

        loop = asyncio.get_running_loop()

        async def _do_copy() -> AsyncIterator[asyncio.Future[None]]:
            async for obj in list_objects(s3_client, source_bucket_name, prefix=source_key):
                if obj['Key'].endswith("/") or S3StorageClass[obj['StorageClass']].archive_storage_class:
                    continue
                p = partial(s3_client.copy,
                            {'Bucket': source_bucket_name, 'Key': obj['Key']},
                            source_bucket_name, obj['Key'],
                            ExtraArgs={
                                'StorageClass': storage_class,
                                'MetadataDirective': 'COPY'
                            } if storage_class else None)
                logger.debug('Copying %s/%s to %s/%s', source_bucket_name, obj['Key'], source_bucket_name,
                             object)
                yield loop.run_in_executor(None, p)

        async def process_item(item):
            await item

        def exceptions_to_ignore(e: Exception) -> bool:
            if isinstance(e, BotoClientError):
                # For folders some objects could already be archived, if object already archived just skip.
                logger.debug('Error response while archiving (is ignored if the object is already archived)', exc_info=True)
                error = e.response['Error']
                logger.debug('error was %s', error)
                if error['Code'] == 'InvalidObjectState':
                    return True
            return False

        await queued_processing(_do_copy(), process_item, exceptions_to_ignore=exceptions_to_ignore)

        return web.HTTPCreated()
    except BotoClientError as e_:
        return handle_client_error(e_)


async def _extract_source(match_info: dict[str, Any]) -> tuple[str, str]:
    source_bucket_name = match_info['bucket_id']
    try:
        source_key_name = decode_key(match_info['id']) if 'id' in match_info else None
    except KeyDecodeException as e:
        raise web.HTTPBadRequest(body=str(e)) from e
    if source_bucket_name is None or source_key_name is None:
        raise web.HTTPBadRequest(body='Invalid request URL')
    return source_bucket_name, source_key_name


class _TargetInfo(NamedTuple):
    url: str
    bucket_name: str
    key: str
    volume_id: str
    target_path: list[str] | None


async def _copy_object_extract_target(body: dict[str, Any]) -> _TargetInfo:
    """
    Extracts the bucket name and folder key from the target property of a Collection+JSON template. It un-escapes them
    as needed.

    :param body: a Collection+JSON template dict.
    :return: a named tuple with the target URL (an absolute URL), the un-escaped bucket name, the folder key, and the volume id
    :raises web.HTTPBadRequest: if the given body is invalid.
    """
    try:
        target_url = next(
            item['value'] for item in body['template']['data'] if item['name'] == 'target')
        vars_ = tvars(route='http{prefix}/volumes/{volume_id}/buckets/{bucket_id}/{folderorproject}/{id}',
                      url=str(URL(target_url).with_query(None).with_fragment(None)))
        # FIXME: may need to fetch the target to see what it is to be maximally reliable and generalizable.
        if 'folderorproject' in vars_ and vars_['folderorproject'] not in ('awss3folders', 'awss3projects'):
            raise ValueError('Not a folder or project')
        bucket_id = vars_['bucket_id']
        assert isinstance(bucket_id, str), 'bucket_id not a str'
        target_bucket_name = unquote(bucket_id)
        id_ = vars_.get('id')
        assert isinstance(id_, (str, type(None))), 'id not a str nor None'
        target_folder_key = decode_key(unquote(id_)) if id_ is not None else ''
        if target_folder_key and not is_folder(target_folder_key):
            raise web.HTTPBadRequest(reason=f'Target {target_url} is not a folder')
        volume_id = vars_['volume_id']
        assert isinstance(volume_id, str), 'volume_id not a str'
        target_url_query = URL(target_url).query
        if 'path' in target_url_query:
            target_path = target_url_query.getall('path')
        else:
            target_path = None
        return _TargetInfo(url=target_url, bucket_name=target_bucket_name, key=target_folder_key, volume_id=volume_id, target_path=target_path)
    except (KeyError, ValueError, KeyDecodeException) as e:
        raise web.HTTPBadRequest(body=f'Invalid target: {e}') from e


class RestoreTier(Enum):
    Standard = auto(), {S3StorageClass.GLACIER, S3StorageClass.DEEP_ARCHIVE}
    Bulk = auto(), {S3StorageClass.GLACIER, S3StorageClass.DEEP_ARCHIVE}
    Expedited = auto(), {S3StorageClass.GLACIER}

    def __init__(self, _: Any, storage_classes: set[S3StorageClass]) -> None:
        self.__storage_classes = {sc: None for sc in storage_classes}

    def storage_classes(self) -> list[S3StorageClass]:
        return list(self.__storage_classes)

    def is_compatible_with(self, storage_class: S3StorageClass) -> bool:
        return storage_class in self.__storage_classes


class UnarchiveInfo:
    days: int
    restore_tier: RestoreTier


async def _extract_unarchive_params(body: dict[str, Any]) -> UnarchiveInfo:
    """
    Extracts the unarchived properties of a Collection+JSON template.

    :param body: a Collection+JSON template dict.
    :return: a Object UnarchiveInfo with days and restore_tier properties
    :raises web.HTTPBadRequest: if the given body is invalid.
    """
    try:
        unarchive_params_dict = {item['name']: item['value'] for item in body['template']['data']}
        unarchive_params = UnarchiveInfo()
        unarchive_params.days = int(unarchive_params_dict['days'])

        if unarchive_params_dict['restore_tier'] == RestoreTier.Standard.name:
            unarchive_params.restore_tier = RestoreTier.Standard
        elif unarchive_params_dict['restore_tier'] == RestoreTier.Expedited.name:
            unarchive_params.restore_tier = RestoreTier.Expedited
        elif unarchive_params_dict['restore_tier'] == RestoreTier.Bulk.name:
            unarchive_params.restore_tier = RestoreTier.Bulk
        else:
            raise ValueError(f"The value {unarchive_params_dict['restore_tier']} is not a valid Restore Tier")

        return unarchive_params
    except (KeyError, ValueError, KeyDecodeException) as e:
        raise web.HTTPBadRequest(body=f'Invalid Unarchive Params: {e}') from e


async def _create_object(s3_client: S3Client, bucket_name: str, key: str) -> web.Response:
    """
    Creates the requested S3 object.

    :param s3_client: the S3 client to use (required).
    :param bucket_name: the bucket name (required).
    :param key: the object key (required).
    :return: a response indicating a successful result.
    :raises HTTPException: if the object already exists, or an error occurred while creating the object.
    """
    if bucket_name is None:
        raise ValueError('bucket_name cannot be None')
    if key is None:
        raise ValueError('key cannot be None')
    logger = logging.getLogger(__name__)
    loop = asyncio.get_running_loop()
    try:
        response_ = await loop.run_in_executor(None, partial(s3_client.head_object, Bucket=bucket_name,
                                                             Key=key))  # check if object exists, if not throws an exception
        logger.debug('Result of creating object %s: %s', key, response_)
        raise response.status_bad_request(body=f"{s3_object_message_display_name(bucket_name, key)} already exists")
    except BotoClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == CLIENT_ERROR_404:  # folder doesn't exist
            try:
                await loop.run_in_executor(None, partial(s3_client.put_object, Bucket=bucket_name, Key=key))
                # Delete any stale metadata for the object.
                return web.HTTPCreated()
            except BotoClientError as e2:
                raise handle_client_error(e2)
        else:
            raise handle_client_error(e)
    except ParamValidationError as e:
        raise response.status_bad_request(str(e))
