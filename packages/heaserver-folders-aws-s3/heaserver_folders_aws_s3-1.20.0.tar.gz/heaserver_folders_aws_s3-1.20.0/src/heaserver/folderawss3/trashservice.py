"""
The HEA Trash Microservice provides deleted file management.
"""

import asyncio
from functools import partial
import itertools

from heaobject.keychain import AWSCredentials
from heaserver.service import response
from heaobject.data import AWSS3FileObject, get_type_display_name
from heaobject.folder import AWSS3Folder
from heaobject.trash import AWSS3FolderFileTrashItem
from heaobject.mimetype import guess_mime_type
from heaobject.aws import S3StorageClass
from heaobject.awss3key import decode_key, encode_key, KeyDecodeException, is_folder, display_name, parent
from heaobject.user import NONE_USER
from heaobject.root import ViewerPermissionContext, Permission, to_dict
from heaobject.project import AWSS3Project
from heaobject.activity import DesktopObjectSummaryView
from heaserver.service.db import aws
from heaserver.service.runner import init_cmd_line, routes, start, web
from heaserver.service.db.aws import S3Manager, S3ClientContext
from heaserver.service.db.mongo import MongoContext, Mongo
from heaserver.service.db.awsservicelib import activity_object_display_name, handle_client_error
from heaserver.service.wstl import builder_factory, action, add_run_time_action
from heaserver.service.appproperty import HEA_BACKGROUND_TASKS, HEA_DB, HEA_CACHE
from heaserver.service.oidcclaimhdrs import SUB
from heaserver.service.sources import AWS_S3
from heaserver.service.wstl import action
from heaserver.service.activity import DesktopObjectActionLifecycle
from heaserver.service.messagebroker import publish_desktop_object
from heaserver.service import client
from heaserver.service.heaobjectsupport import type_to_resource_url
from heaserver.service.customhdrs import PREFER, PREFERENCE_RESPOND_ASYNC
from heaserver.service.util import LockManager
from aiohttp import web, ClientResponseError
import logging
from typing import AsyncIterator, Any, cast
from mypy_boto3_s3 import S3Client
from mypy_boto3_s3.type_defs import ListObjectVersionsOutputTypeDef, DeleteMarkerEntryTypeDef, ObjectVersionTypeDef
from botocore.exceptions import ClientError
from yarl import URL
from .util import BucketAndKey, TrashItemPermissionContext, desktop_object_type_or_type_name_to_path_part, get_desktop_object_summary, \
    get_type_name_from_metadata, path_iter, invalidate_cache
from . import awsservicelib
from collections.abc import Sequence

TRASHAWSS3_COLLECTION = 'awss3trashitems'
MAX_VERSIONS_TO_RETRIEVE = 50000
MONGODB_AWS_S3_FOLDER_METADATA_COLLECTION = 'awss3foldersmetadata'


_status_id = 0

@routes.route('OPTIONS', '/volumes/{volume_id}/buckets/{bucket_id}/awss3trash/{id}')
async def get_item_options(request: web.Request) -> web.Response:
    """
    Gets the allowed HTTP methods for a trash item.

    :param request: a HTTP request (required).
    :return: the HTTP response.
    ---
    summary: Allowed HTTP methods.
    tags:
        - heaserver-trash-aws-s3
    parameters:
        - name: volume_id
          in: path
          required: true
          description: The id of the volume to retrieve.
          schema:
            type: string
          examples:
            example:
              summary: A volume id
              value: 666f6f2d6261722d71757578
        - name: bucket_id
          in: path
          required: true
          description: The id of the bucket to retrieve.
          schema:
            type: string
          examples:
            example:
              summary: A bucket id
              value: my-bucket
        - $ref: '#/components/parameters/id'
    responses:
      '200':
        description: Expected response to a valid request.
        content:
            text/plain:
                schema:
                    type: string
                    example: "200: OK"
      '403':
        $ref: '#/components/responses/403'
      '404':
        $ref: '#/components/responses/404'
    """
    return await response.get_options(request, ['GET', 'HEAD', 'OPTIONS'])


@routes.route('OPTIONS', '/volumes/{volume_id}/buckets/{bucket_id}/awss3trash/{id}/opener')
async def get_item_opener_options(request: web.Request) -> web.Response:
    """
    Gets the allowed HTTP methods for a trash item opener.

    :param request: a HTTP request (required).
    :return: the HTTP response.
    ---
    summary: Allowed HTTP methods.
    tags:
        - heaserver-trash-aws-s3
    parameters:
        - name: volume_id
          in: path
          required: true
          description: The id of the volume to retrieve.
          schema:
            type: string
          examples:
            example:
              summary: A volume id
              value: 666f6f2d6261722d71757578
        - name: bucket_id
          in: path
          required: true
          description: The id of the bucket to retrieve.
          schema:
            type: string
          examples:
            example:
              summary: A bucket id
              value: my-bucket
        - $ref: '#/components/parameters/id'
    responses:
      '200':
        description: Expected response to a valid request.
        content:
            text/plain:
                schema:
                    type: string
                    example: "200: OK"
      '403':
        $ref: '#/components/responses/403'
      '404':
        $ref: '#/components/responses/404'
    """
    return await response.get_options(request, ['GET', 'HEAD', 'OPTIONS'])


@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3trash/{id}')
@action(name='heaserver-awss3trash-item-get-open-choices',
        rel='hea-opener-choices hea-context-menu',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3trash/{id}/opener',
        itemif='actual_object_type_name == "heaobject.folder.AWSS3Folder"')
@action(name='heaserver-awss3trash-item-get-properties',
        rel='hea-properties hea-context-menu')
@action('heaserver-awss3trash-item-restore',
        rel='hea-trash-restore-confirmer hea-context-menu hea-confirm-prompt',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3trash/{id}/restorer')
@action('heaserver-awss3trash-item-permanently-delete',
        rel='hea-trash-delete-confirmer hea-context-menu hea-confirm-prompt',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3trash/{id}/deleter',
        itemif='has_deleter_permission()')
@action('heaserver-awss3trash-item-get-self', rel='self',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3trash/{id}')
@action('heaserver-awss3trash-item-get-volume',
        rel='hea-volume',
        path='volumes/{volume_id}')
@action('heaserver-awss3trash-item-get-awsaccount',
        rel='hea-account',
        path='volumes/{volume_id}/awsaccounts/me')
@action('heaserver-awss3trash-item-get-parent', rel='hea-parent', path='{+parent_uris}')
async def get_deleted_item(request: web.Request) -> web.Response:
    """
    Gets the requested trash item. Trash items are views of a version of an S3 object immediately prior to a delete
    marker chronologically.

    :param request: the HTTP request.
    :return the deleted item in a list, or Not Found.
    ---
    summary: A deleted item.
    tags:
        - heaserver-trash-aws-s3
    parameters:
        - name: volume_id
          in: path
          required: true
          description: The id of the volume.
          schema:
            type: string
          examples:
            example:
              summary: A volume id
              value: 666f6f2d6261722d71757578
        - name: bucket_id
          in: path
          required: true
          description: The id of the bucket.
          schema:
            type: string
          examples:
            example:
              summary: A bucket id
              value: my-bucket
        - $ref: '#/components/parameters/id'
    responses:
      '200':
        $ref: '#/components/responses/200'
      '404':
        $ref: '#/components/responses/404'
    """
    context = TrashItemPermissionContext(request)
    result = await _get_deleted_item(request, context)
    if result is None:
        return await response.get(request, None)
    else:
        return await response.get(request, to_dict(result),
                                  permissions=await result.get_permissions(context),
                                  attribute_permissions=await result.get_all_attribute_permissions(context))


@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3trash/')
@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3trash')
@action(name='heaserver-awss3trash-item-get-open-choices',
        rel='hea-opener-choices hea-context-menu',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3trash/{id}/opener',
        itemif='isheaobject(heaobject.folder.AWSS3Folder)')
@action('heaserver-awss3trash-item-get-properties',
        rel='hea-properties hea-context-menu')
@action('heaserver-awss3trash-item-restore',
        rel='hea-trash-restore-confirmer hea-context-menu hea-confirm-prompt',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3trash/{id}/restorer')
@action('heaserver-awss3trash-item-permanently-delete',
        rel='hea-trash-delete-confirmer hea-context-menu hea-confirm-prompt',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3trash/{id}/deleter',
        itemif='has_deleter_permission()')
@action('heaserver-awss3trash-item-get-self', rel='self',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3trash/{id}')
@action('heaserver-awss3trash-do-empty-trash', rel='hea-trash-emptier',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3trashemptier')
@action('heaserver-awss3trash-item-get-parent', rel='hea-parent', path='{+parent_uris}')
async def get_all_deleted_items(request: web.Request) -> web.Response:
    """
    Gets all trash items in a volume and bucket. Trash items are views of a version of an S3 object immediately prior
    to a delete marker chronologically.

    :param request: the HTTP request.
    :return: the list of items with delete markers or the requested bucket, Not
    Found.
    ---
    summary: Gets a list of all deleted items.
    tags:
        - heaserver-trash-aws-s3
    parameters:
        - name: volume_id
          in: path
          required: true
          description: The id of the volume to check for deleted files.
          schema:
            type: string
          examples:
            example:
              summary: A volume id
              value: 666f6f2d6261722d71757578
        - name: bucket_id
          in: path
          required: true
          description: The id of the bucket to retrieve.
          schema:
            type: string
          examples:
            example:
              summary: A bucket id
              value: my-bucket
    responses:
      '200':
        $ref: '#/components/responses/200'
      '404':
        $ref: '#/components/responses/404'
    """
    logger = logging.getLogger(__name__)
    sub = request.headers.get(SUB, NONE_USER)

    async def coro(app: web.Application):
        logger.debug('Getting deleted items...')
        result: list[AWSS3FolderFileTrashItem] = []
        context = TrashItemPermissionContext(request)
        async for i in _get_deleted_items(request, context):
            logger.debug('Got item %s', i)
            result.append(i)
        perms = []
        attr_perms = []
        for r in result:
            logger.debug('Getting permissions for %s...', r)
            perms.append(await r.get_permissions(context))
            attr_perms.append(await r.get_all_attribute_permissions(context))
        logger.debug('Generating response...')
        return await response.get_all(request, tuple(to_dict(r) for r in result),
                                      permissions=perms, attribute_permissions=attr_perms)
    async_requested = PREFERENCE_RESPOND_ASYNC in request.headers.get(PREFER, [])
    if async_requested:
        logger.debug('Asynchronous get all trash')

        global _status_id
        status_location = f'{str(request.url).rstrip("/")}asyncstatus{_status_id}'
        _status_id += 1
        task_name = f'{sub}^{status_location}'
        await request.app[HEA_BACKGROUND_TASKS].add(coro, task_name)
        return response.status_see_other(status_location)
    else:
        logger.debug('Synchronous get all trash')
        return await coro(request.app)




@routes.get('/volumes/{volume_id}/awss3trash/')
@routes.get('/volumes/{volume_id}/awss3trash')
@action(name='heaserver-awss3trash-item-get-open-choices',
        rel='hea-opener-choices hea-context-menu',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3trash/{id}/opener',
        itemif='isheaobject(heaobject.folder.AWSS3Folder)')
@action('heaserver-awss3trash-item-get-properties',
        rel='hea-properties hea-context-menu')
@action('heaserver-awss3trash-item-restore',
        rel='hea-trash-restore-confirmer hea-context-menu hea-confirm-prompt',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3trash/{id}/restorer')
@action('heaserver-awss3trash-item-permanently-delete',
        rel='hea-trash-delete-confirmer hea-context-menu hea-confirm-prompt',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3trash/{id}/deleter',
        itemif='has_deleter_permission()')
@action('heaserver-awss3trash-item-get-self', rel='self',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3trash/{id}')
@action('heaserver-awss3trash-do-empty-trash', rel='hea-trash-emptier',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3trashemptier')
@action('heaserver-awss3trash-item-get-parent', rel='hea-parent', path='{+parent_uris}')
async def get_all_deleted_items_all_buckets(request: web.Request) -> web.Response:
    """
    Gets all trash items in a volume. Trash items are views of a version of an S3 object immediately prior to a delete
    marker chronologically.

    :param request: the HTTP request.
    :return: the list of items with delete markers.
    ---
    summary: Gets a list of all deleted items.
    tags:
        - heaserver-trash-aws-s3
    parameters:
        - name: volume_id
          in: path
          required: true
          description: The id of the volume to check for deleted files.
          schema:
            type: string
          examples:
            example:
              summary: A volume id
              value: 666f6f2d6261722d71757578
    responses:
      '200':
        $ref: '#/components/responses/200'
      '404':
        $ref: '#/components/responses/404'
    """
    logger = logging.getLogger(__name__)
    sub = request.headers.get(SUB, NONE_USER)
    try:
        volume_id = request.match_info['volume_id']
    except KeyError as e:
        return response.status_bad_request(str(e))
    loop = asyncio.get_running_loop()

    async def coro(app: web.Application) -> web.Response:
        async with S3ClientContext(request, volume_id) as s3:
            async with MongoContext(request) as mongo:
                asyncgens: list[asyncio.Task[Any]] = []
                try:
                    resp_ = await loop.run_in_executor(None, s3.list_buckets)
                    result: list[AWSS3FolderFileTrashItem] = []
                    perms: list[list[Permission]] = []
                    attr_perms: list[dict[str, list[Permission]]] = []
                    context = TrashItemPermissionContext(request)
                    for bucket in resp_.get('Buckets', []):
                        async def asyncgen(volume_id: str, bucket_id: str, sub: str | None):
                                logger.debug('Getting delete items for bucket %s', bucket_id)
                                metadata_dict = await _get_deleted_version_metadata(mongo, bucket_id)
                                nd_metadata_dict = await _get_not_deleted_version_metadata(mongo, bucket_id)
                                logger.debug('Getting actual items...')
                                async for item in _get_deleted_items_private(
                                    s3, volume_id, bucket_id, context, prefix=None, sub_user=sub, metadata_dict=metadata_dict,
                                    nd_metadata_dict=nd_metadata_dict
                                ):
                                    logger.debug('Got item %s', item)
                                    result.append(item)
                                    logger.debug('Getting permissions for %s', item)
                        bucket_id = bucket['Name']
                        logger.debug('Creating task for getting deleted items for bucket %s', bucket_id)
                        asyncgens.append(asyncio.create_task(asyncgen(volume_id, bucket_id, request.headers.get(SUB))))
                    await asyncio.gather(*asyncgens)
                    logger.debug('Generating response...')
                    for r in result:
                        perms.append(await r.get_permissions(context))
                        attr_perms.append(await r.get_all_attribute_permissions(context))
                    return await response.get_all(request, tuple(to_dict(r) for r in result),
                                                permissions=perms, attribute_permissions=attr_perms)
                except ValueError as e:
                    return response.status_forbidden(str(e))
    async_requested = PREFERENCE_RESPOND_ASYNC in request.headers.get(PREFER, [])
    if async_requested:
        logger.debug('Asynchronous get all trash')
        global _status_id
        status_location = f'{str(request.url).rstrip("/")}asyncstatus{_status_id}'
        _status_id += 1
        task_name = f'{sub}^{status_location}'
        await request.app[HEA_BACKGROUND_TASKS].add(coro, task_name)
        return response.status_see_other(status_location)
    else:
        logger.debug('Synchronous get all trash')
        return await coro(request.app)

@routes.get('/volumes/{volume_id}/awss3trashasyncstatus{status_id}')
@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3trashasyncstatus{status_id}')
async def get_trash_async_status(request: web.Request) -> web.Response:
    return response.get_async_status(request)


@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3trashemptier')
async def do_empty_trash(request: web.Request) -> web.Response:
    """
    Empties a version-enabled bucket's trash.

    :param request: the HTTP request.
    :return: No Content or Not Found.
    ---
    summary: Empties the bucket's trash.
    tags:
        - heaserver-trash-aws-s3
    parameters:
        - name: volume_id
          in: path
          required: true
          description: The id of the volume.
          schema:
            type: string
          examples:
            example:
              summary: A volume id
              value: 666f6f2d6261722d71757578
        - name: bucket_id
          in: path
          required: true
          description: The id of the bucket.
          schema:
            type: string
          examples:
            example:
              summary: A bucket id
              value: my-bucket
    responses:
      '204':
        $ref: '#/components/responses/204'
      '404':
        $ref: '#/components/responses/404'
    """
    return await _do_empty_trash(request)


@routes.delete('/volumes/{volume_id}/buckets/{bucket_id}/awss3trash/{id}')
@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3trash/{id}/deleter')
async def permanently_delete_object_with_delete(request: web.Request) -> web.Response:
    """
    Deletes the requested trash item permanently. Trash items are views of a heaobject.aws.S3Object representing a
    chronological grouping of S3 object versions with the same key between delete markers or between the earliest
    delete marker and the beginning of the object's version history. Deleting a trash item results in deletion of the
    delete marker and any delete markers immediately after it with the same key, and deletion of the versions in the
    grouping.

    :param request: the HTTP request.
    :return: No Content or Not Found.
    ---
    summary: Permanent object deletion
    tags:
        - heaserver-trash-aws-s3
    parameters:
        - name: volume_id
          in: path
          required: true
          description: The id of the volume containing the object.
          schema:
            type: string
          examples:
            example:
              summary: A volume id
              value: 666f6f2d6261722d71757578
        - name: bucket_id
          in: path
          required: true
          description: The id of the bucket containing the object.
          schema:
            type: string
          examples:
            example:
              summary: A bucket id
              value: my-bucket
        - $ref: '#/components/parameters/id'
    responses:
      '204':
        $ref: '#/components/responses/204'
      '404':
        $ref: '#/components/responses/404'
    """
    return await _permanently_delete_object(request)


_restore_metadata_lock_manager = LockManager[BucketAndKey]()

@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3trash/{id}/restorer')
async def restore_object(request: web.Request) -> web.Response:
    """
    Removes the delete marker for a specified file

    :param request: the HTTP request.
    :return: No Content or Not Found.
    ---
    summary: File deletion
    tags:
        - heaserver-trash-aws-s3
    parameters:
        - name: volume_id
          in: path
          required: true
          description: The id of the volume to retrieve.
          schema:
            type: string
          examples:
            example:
              summary: A volume id
              value: 666f6f2d6261722d71757578
        - name: bucket_id
          in: path
          required: true
          description: The id of the bucket to retrieve.
          schema:
            type: string
          examples:
            example:
              summary: A bucket id
              value: my-bucket
        - $ref: '#/components/parameters/id'
    responses:
      '204':
        $ref: '#/components/responses/204'
      '404':
        $ref: '#/components/responses/404'
    """
    logger = logging.getLogger(__name__)
    sub = request.headers.get(SUB, NONE_USER)
    try:
        volume_id = request.match_info['volume_id']
        bucket_name = request.match_info['bucket_id']
        item: AWSS3FolderFileTrashItem = AWSS3FolderFileTrashItem()
        item.id = request.match_info['id']
        key_ = item.key
        assert key_ is not None, 'key_ cannot be None'
    except KeyError as e:
        return response.status_bad_request(f'{e} is required')
    except KeyDecodeException as e:
        return response.status_bad_request(f'{e}')

    loop = asyncio.get_running_loop()

    try:
        async with DesktopObjectActionLifecycle(request=request,
                                                code='hea-undelete',
                                                description=f'Restoring {activity_object_display_name(bucket_name, key_)}',
                                                activity_cb=publish_desktop_object) as activity:
            if not await _get_deleted_item(request, TrashItemPermissionContext(request)):
                return response.status_not_found(f'Object {display_name(key_)} is not in the trash')
            activity.new_object_id = encode_key(key_)
            activity.new_object_display_name = display_name(key_)
            activity.new_volume_id = volume_id


            # Elevate privileges to delete the delete marker if the user does not otherwise have delete version
            # permissions. The code prevents a restore when there's already a non-deleted version of the object, which
            # is the only situation where the user could perform a destructive action here. A caveat: theoretically,
            # it's possible for a user to upload a new version of the object between the preflight and the actual
            # restore, though in a versioned bucket the uploaded version would be hidden not deleted.
            aws_cred: AWSCredentials = await request.app[HEA_DB].get_credentials_from_volume(request, volume_id)
            try:
                aws_cred = await request.app[HEA_DB].elevate_privileges(request, aws_cred)
            except ValueError:
                logger.warning('Privilege elevation is not configured, so the user must have delete version '
                               'permissions to restore from the Trash')

            async with S3ClientContext(request=request, credentials=aws_cred) as s3_client:
                async with MongoContext(request) as mongo:
                    async for response_ in _get_version_objects(s3_client, bucket_name, key_, loop):
                        keyfunc = lambda x: x['Key']

                        # Preflight
                        def dms_vers():
                            return cast(itertools.chain[DeleteMarkerEntryTypeDef | ObjectVersionTypeDef],
                                        itertools.chain((dms for dms in response_['DeleteMarkers']),
                                                        (vers for vers in response_.get('Versions', []))))
                        for key, versions in itertools.groupby(sorted(dms_vers(), key=keyfunc), key=keyfunc):
                            resps_preflight = sorted(versions, key=lambda x: x['LastModified'], reverse=True)
                            if resps_preflight and 'Size' in resps_preflight[0]:
                                if not is_folder(resps_preflight[0]['Key']):
                                    return response.status_bad_request(f'Object {display_name(key)} has been overwritten')

                        # Actual
                        activity_url = await type_to_resource_url(request, DesktopObjectSummaryView)
                        key_to_version: dict[str, str | None] = {}
                        for key, versions in itertools.groupby(sorted(dms_vers(), key=keyfunc), key=keyfunc):
                            resps = sorted(versions, key=lambda x: x['LastModified'], reverse=True)
                            async with DesktopObjectActionLifecycle(request=request,
                                                code='hea-undelete-part',
                                                description=f'Restoring {activity_object_display_name(bucket_name, key)}',
                                                activity_cb=publish_desktop_object) as activity_part:
                                the_delete_markers = list[DeleteMarkerEntryTypeDef]()
                                the_versions = list[ObjectVersionTypeDef]()
                                first = True
                                archived = False
                                for resp_ in resps:
                                    if 'Size' not in resp_:
                                        if the_versions:
                                            break
                                        the_delete_markers.append(resp_)
                                        continue
                                    else:
                                        if resp_['VersionId'] == item.version:
                                            key_to_version[key] = resp_['VersionId']
                                            the_versions.append(resp_)
                                        else:
                                            if the_versions:
                                                the_versions.append(resp_)
                                            else:
                                                the_delete_markers.clear()
                                                first = False
                                if any(S3StorageClass[vers['StorageClass']].archive_storage_class for vers in the_versions):
                                    archived = True
                                if not archived or first:
                                    for the_delete_marker in the_delete_markers:
                                        await loop.run_in_executor(None, partial(s3_client.delete_object,
                                                                                 Bucket=bucket_name, Key=the_delete_marker['Key'],
                                                                                 VersionId=the_delete_marker['VersionId']))
                                    if not first:
                                        for versions_to_move in reversed(the_versions):
                                            def mover():
                                                s3_client.copy_object(Bucket=bucket_name,
                                                                    CopySource={'Bucket': bucket_name,
                                                                                'Key': versions_to_move['Key'],
                                                                                'VersionId': versions_to_move['VersionId']},
                                                                    Key=versions_to_move['Key'],
                                                                    StorageClass=versions_to_move['StorageClass'])
                                                s3_client.delete_object(Bucket=bucket_name, Key=versions_to_move['Key'],
                                                                        VersionId=versions_to_move['VersionId'])
                                            await loop.run_in_executor(None, mover)
                                else:
                                    raise response.status_bad_request(awsservicelib.s3_object_message_display_name(bucket_name,key) +
                                                                      'cannot be restored because one or more of its '
                                                                      'versions is archived and there are more recent '
                                                                      'versions of the object.')

                                activity_part.new_object_id = encode_key(key)
                                activity_part.new_volume_id = volume_id
                                metadata_dict = await awsservicelib.get_metadata(mongo, bucket_name, activity_part.new_object_id)
                                type_name = get_type_name_from_metadata(metadata_dict, key)
                                activity_part.new_object_type_name = type_name
                                type_part = desktop_object_type_or_type_name_to_path_part(type_name)
                                object_uri = f'volumes/{volume_id}/buckets/{bucket_name}/{type_part}/{encode_key(key)}'
                                activity_part.new_object_uri = object_uri
                                desktop_object_summary = await get_desktop_object_summary(request, object_uri)
                                if desktop_object_summary is not None:
                                    activity_part.new_object_description = desktop_object_summary.description
                                    activity_part.new_context_dependent_object_path = desktop_object_summary.context_dependent_object_path
                        path = key_
                        while path:
                            if is_folder(path):
                                async with DesktopObjectActionLifecycle(request=request,
                                                code='hea-undelete-part',
                                                description=f'Restoring {activity_object_display_name(bucket_name, path)}',
                                                activity_cb=publish_desktop_object) as activity_part:
                                    if logger.getEffectiveLevel() == logging.DEBUG:
                                        logger.debug('Checking for metadata for %s version %s', path, key_to_version.get(path))
                                    async with _restore_metadata_lock_manager.lock(BucketAndKey(bucket_name, path)):
                                        metadata = await mongo.get_admin_nondesktop_object(MONGODB_AWS_S3_FOLDER_METADATA_COLLECTION,
                                                                                           mongoattributes={'bucket_id': bucket_name,
                                                                                                            'encoded_key': encode_key(path),
                                                                                                            'version': key_to_version.get(path)})
                                        if metadata is not None:
                                            metadata['deleted'] = False
                                            metadata['version'] = None
                                            logger.debug('Updating metadata %s for %s', metadata, path)
                                            activity_part_type_name = metadata['actual_object_type_name']
                                            if path == key_:
                                                activity.new_object_type_name = activity_part_type_name
                                            await mongo.update_admin_nondesktop_object(metadata, MONGODB_AWS_S3_FOLDER_METADATA_COLLECTION)
                                        else:
                                            activity_part_type_name = AWSS3Folder.get_type_name()
                                            if path == key_:
                                                activity.new_object_type_name =activity_part_type_name
                                    type_part = desktop_object_type_or_type_name_to_path_part(activity_part_type_name)
                                    object_uri = f'volumes/{volume_id}/buckets/{bucket_name}/{type_part}/{encode_key(path)}'
                                    desktop_object_summary = await anext(client.get_all(request.app, activity_url, DesktopObjectSummaryView,
                                                                              query_params={'begin': str(0), 'end': str(1), 'object_uri': object_uri},
                                                                              headers={SUB: sub}), None)

                                    activity_part.new_object_id = encode_key(path)
                                    activity_part.new_object_type_name = activity_part_type_name
                                    activity_part.new_object_display_name = display_name(path)
                                    activity_part.new_volume_id = volume_id
                                    activity_part.new_object_uri = object_uri
                                    if desktop_object_summary is not None:
                                        activity_part.new_object_description = desktop_object_summary.description
                                        activity_part.new_context_dependent_object_path = desktop_object_summary.context_dependent_object_path
                            elif path == key_:
                                object_uri = f'volumes/{volume_id}/buckets/{bucket_name}/awss3files/{encode_key(path)}'
                                desktop_object_summary = await anext(client.get_all(request.app, activity_url, DesktopObjectSummaryView,
                                                                              query_params={'begin': str(0), 'end': str(1), 'object_uri': object_uri},
                                                                              headers={SUB: sub}), None)
                            if path == key_:
                                activity.new_object_uri = object_uri
                                if desktop_object_summary is not None:
                                    activity.new_object_description = desktop_object_summary.description
                                    activity.new_context_dependent_object_path = desktop_object_summary.context_dependent_object_path
                            path = parent(path)
    except ClientError as e:
        return awsservicelib.handle_client_error(e)
    finally:
        invalidate_cache(request.app[HEA_CACHE], sub, key_, volume_id, bucket_name)
    return response.status_no_content()

@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3trash/{id}/opener')
@action('heaserver-awss3trash-item-open-default',
        rel='hea-opener hea-default application/x.item',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3trashfolders/{id}/items/',
        itemif='isheaobject(heaobject.folder.AWSS3Folder)')
async def get_trash_item_opener(request: web.Request) -> web.Response:
    """
    Opens the requested trash forder.

    :param request: the HTTP request. Required.
    :return: the opened folder, or Not Found if the requested item does not exist.
    ---
    summary: Folder opener choices
    tags:
        - heaserver-trash-aws-s3
    parameters:
        - name: volume_id
          in: path
          required: true
          description: The id of the volume to retrieve.
          schema:
            type: string
          examples:
            example:
              summary: A volume id
              value: 666f6f2d6261722d71757578
        - name: bucket_id
          in: path
          required: true
          description: The id of the bucket to retrieve.
          schema:
            type: string
          examples:
            example:
              summary: A bucket id
              value: my-bucket
        - $ref: '#/components/parameters/id'
    responses:
      '300':
        $ref: '#/components/responses/300'
      '404':
        $ref: '#/components/responses/404'
    """
    result = await _get_deleted_item(request, TrashItemPermissionContext(request))
    if result is None:
        return await response.get_multiple_choices(request, None)
    else:
        return await response.get_multiple_choices(request, to_dict(result))


def main() -> None:
    config = init_cmd_line(description='Deleted file management',
                           default_port=8080)
    start(package_name='heaserver-trash-aws-s3', db=S3Manager,
          wstl_builder_factory=builder_factory(__package__), config=config)


async def _get_version_objects(s3: S3Client, bucket_id: str, prefix: str | None,
                              loop: asyncio.AbstractEventLoop | None = None) -> AsyncIterator[ListObjectVersionsOutputTypeDef]:
    logger = logging.getLogger(__name__)
    if not loop:
        loop_ = asyncio.get_running_loop()
    else:
        loop_ = loop
    try:
        paginate_partial = partial(s3.get_paginator('list_object_versions').paginate, Bucket=bucket_id)
        if prefix is not None:
            paginate_partial = partial(paginate_partial, Prefix=prefix)
        pages = await loop_.run_in_executor(None, lambda: iter(paginate_partial()))
        while (page := await loop_.run_in_executor(None, next, pages, None)) is not None:
            logger.debug('page %s', page)
            yield page
    except ClientError as e:
        raise awsservicelib.handle_client_error(e)



async def _get_deleted_item(request: web.Request, context: TrashItemPermissionContext) -> AWSS3FolderFileTrashItem | None:
    logger = logging.getLogger(__name__)
    try:
        volume_id = request.match_info['volume_id']
        bucket_id = request.match_info['bucket_id']
    except KeyError as e:
        raise response.status_bad_request(str(e))
    try:
        item: AWSS3FolderFileTrashItem = AWSS3FolderFileTrashItem()
        item.id = request.match_info['id']
        key_ = item.key
    except ValueError as e:
        return None
    async with MongoContext(request) as mongo:
        metadata_dict = await _get_deleted_version_metadata(mongo, bucket_id, id_=item.id, version=item.version)
        def extract_id(uri: str) -> str:
            i = uri.index('awss3folders/')
            if i >= 0:
                i = i + len('awss3folders/')
            else:
                i = uri.index('awss3projects/')
                if i >= 0:
                    i = i + len('awss3projects/')
            assert i >= 0, f'Could not find awss3folders or awss3projects in {uri}'
            return uri[i:]
        not_deleted_metadata_dict = await _get_not_deleted_version_metadata(mongo, bucket_id, ids=[extract_id(uri) for uri in item.parent_uris])
    try:
        async with S3ClientContext(request, volume_id) as s3:
            async for deleted_item in _get_deleted_items_private(s3, volume_id, bucket_id, context, key_, request.headers.get(SUB),
                                                                version=item.version, recursive=False,
                                                                metadata_dict=metadata_dict,
                                                                nd_metadata_dict=not_deleted_metadata_dict):
                return deleted_item
    except ValueError as e:
        logger.exception('Error getting deleted items')
    return None


async def _get_deleted_version_metadata(mongo: Mongo, bucket_id: str, id_: str | None = None, version: str | None = None) -> dict:
    metadata_dict = {}
    filter = {
        'bucket_id': bucket_id,
        'deleted': True,
    }
    if id_ is not None:
        filter['encoded_key'] = id_
    if version is not None:
        filter['version'] = version
    gen_ = mongo.get_all_admin(MONGODB_AWS_S3_FOLDER_METADATA_COLLECTION, filter)
    try:
        async for metadata in gen_:
            metadata_dict[(metadata['bucket_id'], metadata['encoded_key'], metadata['actual_object_type_name'], metadata.get('version'))] = metadata
    finally:
        await gen_.aclose()
    return metadata_dict


async def _get_not_deleted_version_metadata(mongo: Mongo, bucket_id: str, ids: Sequence[str] | None = None) -> dict:
    metadata_dict = {}
    filter = {
        'bucket_id': bucket_id,
        'deleted': False,
    }
    if ids:
        filter['encoded_key'] = {'$in': ids}
    gen_ = mongo.get_all_admin(MONGODB_AWS_S3_FOLDER_METADATA_COLLECTION, filter)
    try:
        async for metadata in gen_:
            metadata_dict[(metadata['bucket_id'], metadata['encoded_key'], metadata['actual_object_type_name'], metadata.get('version'))] = metadata
    finally:
        await gen_.aclose()
    return metadata_dict


async def _get_deleted_items(request: web.Request, context: TrashItemPermissionContext, recursive=True) -> AsyncIterator[AWSS3FolderFileTrashItem]:
    """
    Gets all deleted items (with a delete marker) in a volume and bucket.
    The request's match_info is expected to have volume_id and bucket_id keys
    containing the volume id and bucket name, respectively. It can optionally
    contain a folder_id or trash_folder_id, which will restrict returned items
    to a folder or trash folder, respectively.

    :param request: the HTTP request (required).
    :return: an asynchronous iterator of AWSS3FolderFileItems.
    :raises HTTPBadRequest: if the request doesn't have a volume id or bucket
    name.
    """
    try:
        volume_id = request.match_info['volume_id']
        bucket_id = request.match_info['bucket_id']
    except KeyError as e:
        raise response.status_bad_request(str(e))
    folder_id = request.match_info.get('folder_id', None)
    trash_folder_id = request.match_info.get('trash_folder_id', None)
    try:
        if folder_id:
            prefix: str | None = decode_key(folder_id) if folder_id != 'root' else ''
        elif trash_folder_id:
            if trash_folder_id != 'root':
                item = AWSS3FolderFileTrashItem()
                item.id = trash_folder_id
                prefix = item.key
            else:
                prefix = ''
        else:
            prefix = None

        async with S3ClientContext(request, volume_id) as s3:
            async with MongoContext(request) as mongo:
                metadata_dict = await _get_deleted_version_metadata(mongo, bucket_id)
                not_deleted_metadata_dict = await _get_not_deleted_version_metadata(mongo, bucket_id)
            async for item in _get_deleted_items_private(s3, volume_id, bucket_id, context, prefix,
                                                         request.headers.get(SUB), recursive=recursive,
                                                         metadata_dict=metadata_dict,
                                                         nd_metadata_dict=not_deleted_metadata_dict):
                yield item
    except (KeyDecodeException, ValueError) as e:
        raise response.status_not_found()


async def _get_deleted_items_private(s3: S3Client, volume_id: str, bucket_id: str, context: TrashItemPermissionContext,
                                     prefix: str | None = None,
                                     sub_user: str | None = None, version: str | None = None, recursive=True,
                                     metadata_dict: dict | None = None,
                                     nd_metadata_dict: dict | None = None) -> AsyncIterator[AWSS3FolderFileTrashItem]:
    logger = logging.getLogger(__name__)
    folder_url = URL('volumes') / volume_id / 'buckets' / bucket_id / 'awss3folders'
    project_url = URL('volumes') / volume_id / 'buckets' / bucket_id / 'awss3projects'
    file_url = URL('volumes') / volume_id / 'buckets' / bucket_id / 'awss3files'
    try:
        async for delete_marker, version_ in awsservicelib.list_deleted_object_versions(s3, bucket_id,
                                                                                        prefix if prefix else '',
                                                                                        include_restore_status=True):
            logger.debug('Found version %s with delete marker %s', version_, delete_marker)
            if version and version_['VersionId'] != version:
                continue
            logger.debug('Creating item for version %s', version_)
            item: AWSS3FolderFileTrashItem = AWSS3FolderFileTrashItem()
            item.bucket_id = bucket_id
            key = version_['Key']
            item.key = key
            item.version = version_['VersionId']
            item.modified = version_['LastModified']
            item.created = version_['LastModified']
            item.deleted = delete_marker['LastModified']
            item.owner = (sub_user if sub_user is not None else NONE_USER) if recursive else NONE_USER
            item.volume_id = volume_id
            item.source = AWS_S3
            item.storage_class = S3StorageClass[version_['StorageClass']]
            item.size = version_['Size']
            item.add_share(await item.get_permissions_as_share(context))
            encoded_key = encode_key(key)
            parent_key = parent(key)
            def parent_uri() -> str:
                if parent_key:
                    parent_metadata = nd_metadata_dict.get((bucket_id, encode_key(parent_key), AWSS3Project.get_type_name(), None)) if nd_metadata_dict else None
                    if not parent_metadata:
                        return str(folder_url / encode_key(parent_key))
                    else:
                        return str(project_url / encode_key(parent_key))
                else:
                    return str(URL('volumes') / volume_id / 'buckets' / bucket_id)
            if is_folder(key):
                metadata = metadata_dict.get((bucket_id, encode_key(key), AWSS3Project.get_type_name(), version_['VersionId'])) if metadata_dict else None
                if metadata is not None:
                    item.actual_object_uri = str(project_url / encoded_key)
                    item.actual_object_type_name = AWSS3Project.get_type_name()
                    item.type_display_name = 'Project'

                else:
                    item.actual_object_uri = str(folder_url / encoded_key)
                    item.actual_object_type_name = AWSS3Folder.get_type_name()
                    item.type_display_name = 'Folder'
            else:
                item.actual_object_uri = str(file_url / encoded_key)
                item.actual_object_type_name = AWSS3FileObject.get_type_name()
                item.type_display_name = get_type_display_name(guess_mime_type(display_name(key)))
            item.parent_uris = [parent_uri()]
            logger.debug('Created version item %s', item)
            yield item
    except ClientError as e:
        if aws.client_error_code(e) == aws.CLIENT_ERROR_ACCESS_DENIED:
            logger.debug('Bucket inaccessible %s skipping...', bucket_id)
        else:
            raise handle_client_error(e)


async def _permanently_delete_object(request: web.Request) -> web.Response:
    """
    Makes the specified version the current version by deleting all recent versions
    The volume id must be in the volume_id entry of the
    request's match_info dictionary. The bucket id must be in the bucket_id entry of the request's match_info
    dictionary. The file id must be in the id entry of the request's match_info dictionary.
    And the version_id must be in the version id entry of the request's match_info dictionary.

    :param request: the aiohttp Request (required).
    :return: the HTTP response with a 204 status code if the file was successfully deleted, 403 if access was denied,
    404 if the file was not found, 405 if delete marker doesn't have the latest modified time or 500 if an internal
    error occurred.
    """
    logger = logging.getLogger(__name__)

    try:
        volume_id = request.match_info['volume_id']
        bucket_name = request.match_info['bucket_id']
        item: AWSS3FolderFileTrashItem = AWSS3FolderFileTrashItem()
        item.id = request.match_info['id']
        key = item.key
        assert key is not None, 'key cannot be None'
        version = item.version
    except KeyError as e:
        return response.status_bad_request(f'{e} is required')
    except (ValueError, KeyDecodeException) as e:
        return response.status_not_found()

    loop = asyncio.get_running_loop()

    try:
        async with S3ClientContext(request, volume_id) as s3_client:
            async with MongoContext(request) as mongo:
                from operator import itemgetter
                from itertools import groupby
                async for page in awsservicelib.list_object_versions_and_delete_markers(s3_client, bucket_name, prefix=key, loop=loop):
                    # Delete the delete markers preceding the requested version, delete the requested version, and
                    # also delete all versions prior to another delete marker. However, don't delete folder contents
                    # because folders don't really exist in S3.
                    for key_, group in groupby(awsservicelib._ordered_object_versions_and_delete_markers(page, sort=awsservicelib.SortOrder.DESC),
                                               key=itemgetter('Key')):
                        if key == key_:
                            delete_markers = []
                            version_to_delete = None
                            for v_or_d in group:
                                if 'Size' not in v_or_d:
                                    version_to_delete = None
                                    delete_markers.append(v_or_d)
                                    continue
                                if v_or_d['VersionId'] == version:
                                    if delete_markers:
                                        version_to_delete = v_or_d
                                    else:
                                        raise response.status_not_found()
                                if 'Size' in v_or_d and version_to_delete is None:
                                    delete_markers.clear()
                                if version_to_delete:
                                    while delete_markers:
                                        delete_marker = delete_markers.pop()
                                        await loop.run_in_executor(None, partial(s3_client.delete_object,
                                                                                 Bucket=bucket_name, Key=key,
                                                                                 VersionId=delete_marker['VersionId']))
                                    await loop.run_in_executor(None, partial(s3_client.delete_object,
                                                                             Bucket=bucket_name, Key=key,
                                                                             VersionId=v_or_d['VersionId']))
                                    await mongo.delete_admin(MONGODB_AWS_S3_FOLDER_METADATA_COLLECTION,
                                                             mongoattributes={'bucket_id': bucket_name,
                                                                              'encoded_key': item.id,
                                                                              'version': v_or_d['VersionId']})

                # Check if the parent folders/projects have a non-deleted object associated with them. If not,
                # delete the metadata.
                logger.debug('About to check for %s', key)
                for path in path_iter(key):
                    logger.debug('Checking for %s', path)
                    async for _ in awsservicelib.list_objects(s3_client, bucket_name, prefix=path, max_keys=1):
                        logger.debug('Found object at %s', path)
                        break
                    else:
                        logger.debug('Nothing found for %s', path)
                        # Only delete something without a version (indicating it is not deleted).
                        await mongo.delete_admin(MONGODB_AWS_S3_FOLDER_METADATA_COLLECTION,
                                                    mongoattributes={'bucket_id': bucket_name,
                                                                    'encoded_key': encode_key(path), 'version': None})
                        continue
                    break

    except ClientError as e:
        return awsservicelib.handle_client_error(e)

    return response.status_no_content()


async def _do_empty_trash(request: web.Request) -> web.Response:
    """
    Makes the specified version the current version by deleting all recent versions
    The volume id must be in the volume_id entry of the
    request's match_info dictionary. The bucket id must be in the bucket_id entry of the request's match_info
    dictionary. The file id must be in the id entry of the request's match_info dictionary.
    And the version_id must be in the version id entry of the request's match_info dictionary.

    :param request: the aiohttp Request (required).
    :return: the HTTP response with a 204 status code if the file was successfully deleted, 403 if access was denied,
    404 if the file was not found, 405 if delete marker doesn't have the latest modified time or 500 if an internal error occurred.
    """
    logger = logging.getLogger(__name__)

    try:
        volume_id = request.match_info['volume_id']
        bucket_name = request.match_info['bucket_id']
    except KeyError as e:
        return response.status_bad_request(f'{e} is required')

    loop = asyncio.get_running_loop()

    try:
        async with S3ClientContext(request, volume_id) as s3_client:
            async with MongoContext(request) as mongo:
                async for response_ in _get_version_objects(s3_client, bucket_name, None, loop):
                    keyfunc = lambda x: x['Key']
                    for key, versions in itertools.groupby(sorted((resp for resp in itertools.chain((vers for vers in response_.get('DeleteMarkers', [])), (vers for vers in response_.get('Versions', [])))), key=keyfunc), key=keyfunc):
                        delete_markers_to_delete = []
                        versions_to_delete = []
                        delete_markers = True
                        for resp_ in sorted((resp for resp in versions), key=lambda x: x['LastModified'], reverse=True):
                            if delete_markers and 'Size' not in resp_:
                                delete_markers_to_delete.append(resp_)
                            elif 'Size' in resp_ and delete_markers_to_delete:
                                delete_markers = False
                                versions_to_delete.append(resp_)
                            else:
                                break
                        for version_to_delete in itertools.chain(versions_to_delete, delete_markers_to_delete):
                            await loop.run_in_executor(None, partial(s3_client.delete_object, Bucket=bucket_name, Key=key, VersionId=version_to_delete['VersionId']))
                            await mongo.delete_admin(MONGODB_AWS_S3_FOLDER_METADATA_COLLECTION, mongoattributes={'bucket_id': bucket_name, 'encoded_key': encode_key(key), 'version': version_to_delete['VersionId']})

    except ClientError as e:
        return awsservicelib.handle_client_error(e)

    return response.status_no_content()
