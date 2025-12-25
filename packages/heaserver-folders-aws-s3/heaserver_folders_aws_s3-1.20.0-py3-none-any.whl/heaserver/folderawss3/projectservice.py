import asyncio
from functools import partial
from itertools import chain
import logging
from heaserver.service.runner import routes
from heaserver.service import response
from aiohttp import web, hdrs
from heaserver.service.wstl import action
from heaserver.service.db import mongo, aws
from heaserver.service.db.awsservicelib import http_error_message
from heaserver.service.activity import DesktopObjectActionLifecycle
from heaserver.service.sources import AWS_S3
from heaserver.service.messagebroker import publish_desktop_object
from heaserver.service.heaobjectsupport import new_heaobject_from_type, desktop_object_type_or_type_name_to_type
from heaserver.service.oidcclaimhdrs import SUB
from heaserver.service.appproperty import HEA_BACKGROUND_TASKS, HEA_CACHE, HEA_MESSAGE_BROKER_PUBLISHER
from heaserver.service.customhdrs import PREFER, PREFERENCE_RESPOND_ASYNC
from heaserver.service.util import queued_processing
from heaserver.service.backgroundtasks import BackgroundTasks
from heaobject.root import DesktopObjectDict, ViewerPermissionContext, PermissionContext
from heaobject.awss3key import encode_key, split, KeyDecodeException, join, decode_key, is_object_in_folder, parent, display_name
from heaobject.activity import Status, Activity
from heaobject.folder import AWSS3ItemInFolder, AWSS3Folder
from heaobject.project import AWSS3Project
from heaobject.data import AWSS3FileObject, ClipboardData, get_type_display_name
from heaobject.user import NONE_USER, AWS_USER
from heaobject.error import DeserializeException
from heaobject.aws import S3StorageClass
from heaobject.root import DesktopObject, Permission, is_desktop_object_type, to_dict
from heaobject.mimetype import guess_mime_type
from heaobject.util import parse_bool, now
from botocore.exceptions import ClientError as BotoClientError, ParamValidationError
from mypy_boto3_s3 import S3Client
from mypy_boto3_s3.type_defs import ListObjectsV2OutputTypeDef
from typing import Any, cast
from datetime import datetime
from json import JSONDecodeError
from yarl import URL

from heaserver.folderawss3.util import get_description, delete_folder
from .util import client_line_ending, response_folder_as_zip, set_s3_storage_status, get_result_or_see_other, \
    MONGODB_AWS_S3_FOLDER_METADATA_COLLECTION, move, rename, copy, create_presigned_url_credentials, \
    when_object_not_found, extract_expiration, path_iter, invalidate_cache
from . import awsservicelib

_status_id = 0

@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{folder_id}/items')
@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{folder_id}/items/')
@action(name='heaserver-awss3folders-item-get-actual-container', rel='hea-actual hea-actual-container',
        path='{+actual_object_uri}',
        itemif="actual_object_type_name == AWSS3Project.get_type_name() or actual_object_type_name == AWSS3Folder.get_type_name()")
@action(name='heaserver-awss3folders-item-get-actual-not-container', rel='hea-actual',
        path='{+actual_object_uri}',
        itemif="actual_object_type_name != AWSS3Project.get_type_name() and actual_object_type_name != AWSS3Folder.get_type_name()")
async def get_items(request: web.Request) -> web.Response:
    """
    Gets the project's items with the specified id.
    :param request: the HTTP request.
    :return: the requested items, or Not Found if the project was not found.
    ---
    summary: All items in a project.
    tags:
        - heaserver-awss3folders-project-items
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
        - name: folder_id
          in: path
          required: true
          description: The id of the project to retrieve.
          schema:
            type: string
          examples:
            example:
              summary: A folder id
              value: root
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    responses:
      '200':
        $ref: '#/components/responses/200'
      '403':
        $ref: '#/components/responses/403'
    """
    logger = logging.getLogger(__name__)

    volume_id = request.match_info['volume_id']
    bucket_name = request.match_info['bucket_id']
    folder_id_ = request.match_info['folder_id']
    try:
        folder_key = decode_key(folder_id_)
    except KeyDecodeException:
        return response.status_not_found()

    if not awsservicelib.is_folder(folder_key) or not await _is_project(request, volume_id, bucket_name, folder_id_):
        return response.status_not_found()

    logger = logging.getLogger(__name__)
    sub = request.headers.get(SUB, NONE_USER)
    async def coro(app: web.Application):
        folder_key = awsservicelib.decode_folder(folder_id_)
        loop = asyncio.get_running_loop()
        try:
            if folder_key is None:
                # We couldn't decode the folder_id, and we need to check if the user can access the bucket in order to
                # decide which HTTP status code to respond with (Forbidden vs Not Found).
                async with aws.S3ClientContext(request=request, volume_id=volume_id) as s3:
                    return await awsservicelib.return_bucket_status_or_not_found(bucket_name, loop, s3)
            logger.debug('Getting all items in project %s in bucket %s', folder_key, bucket_name)
            actual_object_uri_base = URL('volumes') / volume_id / 'buckets' / bucket_name
            owner = AWS_USER
            file_type_name = AWSS3FileObject.get_type_name()
        except BotoClientError as e:
            return http_error_message(awsservicelib.handle_client_error(e), bucket_name, folder_key)
        except ParamValidationError as e:
            return response.status_bad_request(str(e))
        async with DesktopObjectActionLifecycle(request,
                                                code='hea-get',
                                                description=f'Listing all items in {awsservicelib.s3_object_message_display_name(bucket_name, folder_key)}',
                                                activity_cb=publish_desktop_object) as activity:
            cache_key = (sub, volume_id, bucket_name, folder_id_, None, 'items')
            cached_value = request.app[HEA_CACHE].get(cache_key)
            if cached_value:
                data = cached_value[0]
                permissions: list[list[Permission]] = cached_value[1]
                attribute_permissions: list[dict[str, list[Permission]]] = cached_value[2]
                logger.debug('Getting cached value for %s: %s', cache_key, data)
                return await response.get_all(request, data, permissions=permissions,
                                              attribute_permissions=attribute_permissions)
            else:
                async with mongo.MongoContext(request=request) as mongo_client:
                    try:
                        folders: list[DesktopObjectDict] = []
                        folders_actual_object_uri_base = actual_object_uri_base / 'awss3folders'
                        projects_actual_object_uri_base = actual_object_uri_base / 'awss3projects'
                        files_actual_object_uri_base = actual_object_uri_base / 'awss3files'
                        item: AWSS3ItemInFolder = AWSS3ItemInFolder()
                        async def get_metadata() -> dict[str, DesktopObjectDict]:
                            metadata = dict[str, DesktopObjectDict]()
                            gen_ = mongo_client.get_all_admin(MONGODB_AWS_S3_FOLDER_METADATA_COLLECTION, {'bucket_id': bucket_name, 'parent_encoded_key': folder_id_,
                                                                                                          '$or': [{'deleted': False}, {'deleted': {'$exists': False}}]})
                            try:
                                async for item_ in gen_:
                                    key_ = item_['encoded_key']
                                    assert key_ is not None, 'encoded_key is missing in metadata'
                                    metadata[str(key_)] = item_
                                return metadata
                            finally:
                                await gen_.aclose()
                        metadata_task = asyncio.create_task(get_metadata())
                        context = ViewerPermissionContext(sub)
                        permissions = []
                        attribute_permissions = []
                        async with aws.S3ClientContext(request=request, volume_id=volume_id) as s3:
                            async for obj in awsservicelib.list_objects(s3, bucket_id=bucket_name, prefix=folder_key, loop=loop, delimiter='/', include_restore_status=True):
                                key = obj['Key'] if 'Key' in obj else obj['Prefix']
                                key_ = key.removeprefix(folder_key)
                                try:
                                    if key_ == '':  # The folder
                                        continue
                                    actual_key = key_[:key_.index('/') + 1]  # A folder
                                    is_folder_ = True
                                except ValueError:
                                    actual_key = key_  # Not a folder
                                    is_folder_ = False

                                actual_id = encode_key(folder_key + actual_key)
                                logger.debug('Found item %s in bucket %s', actual_key, bucket_name)
                                item.id = actual_id
                                if not is_folder_:
                                    item.modified = obj.get('LastModified')
                                    item.created = obj.get('LastModified')
                                item.owner = owner
                                item.actual_object_id = actual_id
                                item.folder_id = folder_id_
                                item.bucket_id = bucket_name
                                item.volume_id = volume_id
                                if not is_folder_:
                                    item.actual_object_uri = str(files_actual_object_uri_base / item.actual_object_id)
                                    item.actual_object_type_name = file_type_name
                                    item.size = obj['Size']
                                    set_s3_storage_status(obj, item)
                                    item.mime_type = guess_mime_type(item.display_name)
                                    item.type_display_name = get_type_display_name(item.mime_type)
                                else:
                                    metadata = await metadata_task
                                    if item_metadata := metadata.get(item.actual_object_id):
                                        aotn = item_metadata.get('actual_object_type_name')
                                    else:
                                        aotn = None
                                    if aotn is None or aotn == AWSS3Folder.get_type_name():
                                        item.actual_object_uri = str(folders_actual_object_uri_base / item.actual_object_id)
                                        item.actual_object_type_name = AWSS3Folder.get_type_name()
                                        item.type_display_name = 'Folder'
                                    elif aotn == AWSS3Project.get_type_name():
                                        item.actual_object_type_name = AWSS3Project.get_type_name()
                                        item.actual_object_uri = str(projects_actual_object_uri_base / item.actual_object_id)
                                        item.type_display_name = 'Project'
                                    else:
                                        item.actual_object_type_name = None
                                        item.actual_object_uri = None
                                        item.type_display_name = None  # type:ignore[assignment]
                                    item.size = None
                                    item.storage_class = None
                                    item.source = AWS_S3
                                    item.source_detail = AWS_S3
                                share = await item.get_permissions_as_share(context)
                                item.add_user_share(share)
                                permissions.append(share.permissions)
                                attribute_permissions.append(await item.get_all_attribute_permissions(context))
                                folders.append(to_dict(item))
                        _, description = await asyncio.gather(metadata_task, get_description(sub, s3, bucket_name, folder_key))
                        activity.new_object_uri = f'volumes/{volume_id}/buckets/{bucket_name}/awss3projects/{folder_id_}'
                        activity.new_object_type_name = AWSS3Project.get_type_name()
                        activity.new_volume_id = volume_id
                        activity.new_object_id = folder_id_
                        activity.new_object_display_name = split(folder_key)[1].removesuffix('/')
                        activity.new_object_description = description
                        if 'path' in request.url.query:
                            activity.new_context_dependent_object_path = request.url.query.getall('path')
                        request.app[HEA_CACHE][cache_key] = (folders, permissions, attribute_permissions)
                        for folder_item_dict, perms, attr_perms in zip(folders, permissions, attribute_permissions):
                            request.app[HEA_CACHE][(sub, volume_id, bucket_name, folder_id_, folder_item_dict['id'], 'items')] = (folder_item_dict, perms, attr_perms)
                        return await response.get_all(request, folders, permissions=permissions,
                                                      attribute_permissions=attribute_permissions)
                    except BotoClientError as e:
                        activity.status = Status.FAILED
                        return awsservicelib.handle_client_error(e)
                    except ParamValidationError as e:
                        activity.status = Status.FAILED
                        return response.status_bad_request(str(e))
    async_requested = PREFERENCE_RESPOND_ASYNC in request.headers.get(PREFER, [])
    if async_requested:
        logger.debug('Asynchronous get-all')
        global _status_id
        status_location = f'{str(request.url).rstrip("/")}asyncstatus{_status_id}'
        _status_id += 1
        task_name = f'{sub}^{status_location}'
        background_tasks = cast(BackgroundTasks, request.app[HEA_BACKGROUND_TASKS])
        await background_tasks.add(coro, task_name)  # type:ignore
        return await get_result_or_see_other(background_tasks, task_name, status_location)
    else:
        logger.debug('Synchronous get-all')
        return await coro(request.app)

@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{folder_id}/items/{id}')
@action(name='heaserver-awss3folders-item-get-actual-container', rel='hea-actual hea-actual-container',
        path='{+actual_object_uri}',
        itemif="actual_object_type_name == AWSS3Project.get_type_name() or actual_object_type_name == AWSS3Folder.get_type_name()")
@action(name='heaserver-awss3folders-item-get-actual-not-container', rel='hea-actual',
        path='{+actual_object_uri}',
        itemif="actual_object_type_name != AWSS3Project.get_type_name() and actual_object_type_name != AWSS3Folder.get_type_name()")
@action(name='heaserver-awss3folders-item-get-volume', rel='hea-volume', path='volumes/{volume_id}')
async def get_item(request: web.Request) -> web.Response:
    """
    Gets the requested item from the given project.

    :param request: the HTTP request. Required.
    :return: the requested item, or Not Found if it was not found.
    ---
    summary: A specific project item.
    tags:
        - heaserver-awss3folders-project-items
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
        - name: folder_id
          in: path
          required: true
          description: The id of the folder to retrieve.
          schema:
            type: string
          examples:
            example:
              summary: A folder id
              value: root
        - $ref: '#/components/parameters/id'
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    responses:
      '200':
        $ref: '#/components/responses/200'
      '403':
        $ref: '#/components/responses/403'
      '404':
        $ref: '#/components/responses/404'
    """
    logger = logging.getLogger(__name__)
    sub = request.headers.get(SUB, NONE_USER)
    volume_id = request.match_info['volume_id']
    folder_id_ = request.match_info['folder_id']
    bucket_name = request.match_info['bucket_id']
    id_ = request.match_info['id']

    decoded_folder_key, decoded_key, folder_or_item_not_found = _check_folder_and_object_keys(folder_id_, request)
    if decoded_key is None:
        return response.status_not_found()
    actual_object_uri_base = URL('volumes') / volume_id / 'buckets' / bucket_name

    async with DesktopObjectActionLifecycle(request=request,
                                            code='hea-get',
                                            description=f'Getting item {awsservicelib.s3_object_message_display_name(bucket_name, decoded_key)}',
                                            activity_cb=publish_desktop_object) as activity:
        cache_key = (sub, volume_id, bucket_name, folder_id_, id_, 'items')
        if cache_value := request.app[HEA_CACHE].get(cache_key):
            item_dict, permissions, attribute_perms = cache_value
            return await response.get(request, item_dict, permissions=permissions,
                                      attribute_permissions=attribute_perms)
        else:
            async with mongo.MongoContext(request=request) as mongo_client:
                async with aws.S3ClientContext(request=request, volume_id=volume_id) as s3:
                    try:
                        loop = asyncio.get_running_loop()

                        if folder_or_item_not_found:
                            activity.status = Status.FAILED
                            return await awsservicelib.return_bucket_status_or_not_found(bucket_name, loop, s3)

                        logger.debug('Getting item %s in folder %s in bucket %s', decoded_key, decoded_folder_key, bucket_name)
                        response_ = await loop.run_in_executor(None, partial(s3.list_objects_v2, Bucket=bucket_name, Prefix=decoded_key,
                                                                            MaxKeys=1, Delimiter='/', OptionalObjectAttributes=['RestoreStatus']))
                        context = ViewerPermissionContext(sub)
                        for obj in chain(response_.get('CommonPrefixes', []), response_.get('Contents', [])):
                            # obj is either an ObjectTypeDef or a CommonPrefixTypeDef, and TypeDefs can't be used in
                            # isinstance nor issubclass, so instead we ignore the type checker in a few places where
                            # the key is found in one but not the other.
                            id_ = obj['Key'] if 'Key' in obj else obj['Prefix']  # type:ignore[misc]
                            is_folder_ = awsservicelib.is_folder(id_)
                            id_encoded = encode_key(id_)
                            logger.debug('Found item %s in bucket %s', id_, bucket_name)

                            item: AWSS3ItemInFolder = AWSS3ItemInFolder()
                            item.id = id_encoded
                            if not is_folder_:
                                item.modified = obj.get('LastModified')  # type:ignore[assignment]
                                item.created = obj.get('LastModified')  # type:ignore[assignment]
                            item.owner = AWS_USER
                            item.folder_id = folder_id_
                            item.actual_object_id = id_encoded
                            item.bucket_id = bucket_name
                            item.volume_id = volume_id
                            share_ = await item.get_permissions_as_share(context)
                            item.add_user_share(share_)
                            permissions = share_.permissions
                            attribute_perms = await item.get_all_attribute_permissions(context)
                            if is_folder_:
                                metadata_dict = await awsservicelib.get_metadata(mongo_client, bucket_name, id_encoded)
                                if not metadata_dict or metadata_dict['actual_object_type_name'] == AWSS3Folder.get_type_name():
                                    item.actual_object_uri = str(actual_object_uri_base / 'awss3folders' / id_encoded)
                                    item.actual_object_type_name = AWSS3Folder.get_type_name()
                                    item.type_display_name = 'Folder'
                                elif metadata_dict['actual_object_type_name'] == AWSS3Project.get_type_name():
                                    item.actual_object_type_name = AWSS3Project.get_type_name()
                                    item.actual_object_uri = str(actual_object_uri_base / 'awss3projects' / id_encoded)
                                    item.type_display_name = 'Project'
                                item.source = AWS_S3
                                item.source_detail = AWS_S3
                            else:
                                item.actual_object_uri = str(actual_object_uri_base / 'awss3files' / id_encoded)
                                item.actual_object_type_name = AWSS3FileObject.get_type_name()
                                item.size = obj['Size']  # type:ignore[misc]
                                set_s3_storage_status(obj, item)
                                item.mime_type = guess_mime_type(item.display_name)
                                item.type_display_name = get_type_display_name(item.mime_type)
                            activity.new_object_id = id_encoded
                            activity.new_object_uri = f'volumes/{volume_id}/buckets/{bucket_name}/awss3projects/{folder_id_}/items/{id_encoded}'
                            activity.new_object_type_name = AWSS3ItemInFolder.get_type_name()
                            activity.new_volume_id = volume_id
                            activity.new_object_display_name = item.display_name
                            activity.new_object_description = item.description
                            if 'path' in request.url.query:
                                activity.new_context_dependent_object_path = request.url.query.getall('path')
                            item_dict = item.to_dict()
                            request.app[HEA_CACHE][cache_key] = (item_dict, permissions, attribute_perms)
                            return await response.get(request, item_dict, permissions=permissions,
                                                      attribute_permissions=attribute_perms)
                        return await response.get(request, None)
                    except BotoClientError as e:
                        activity.status = Status.FAILED
                        return awsservicelib.handle_client_error(e)

@routes.route('OPTIONS', '/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{folder_id}/items/{id}')
async def get_item_options(request: web.Request) -> web.Response:
    """
    ---
    summary: Allowed HTTP methods.
    tags:
        - heaserver-awss3folders-project-items
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
        - name: folder_id
          in: path
          required: true
          description: The id of the folder to retrieve.
          schema:
            type: string
          examples:
            example:
              summary: A folder id
              value: root
        - $ref: '#/components/parameters/id'
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
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
    return await response.get_options(request, ['GET', 'DELETE', 'HEAD', 'OPTIONS'])


@routes.route('OPTIONS', '/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{folder_id}/items')
@routes.route('OPTIONS', '/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{folder_id}/items/')
async def get_items_options(request: web.Request) -> web.Response:
    """
    Gets the allowed HTTP methods for a project items resource.

    :param request: the HTTP request (required).
    :return: the HTTP response.
    ---
    summary: Allowed HTTP methods.
    tags:
        - heaserver-awss3folders-project-items
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
        - name: folder_id
          in: path
          required: true
          description: The id of the folder to retrieve.
          schema:
            type: string
          examples:
            example:
              summary: A folder id
              value: root
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
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
    return await response.get_options(request, ['GET', 'POST', 'DELETE', 'HEAD', 'OPTIONS'])

@routes.route('OPTIONS', '/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}')
async def get_project_options(request: web.Request) -> web.Response:
    """
    Gets the allowed HTTP methods for a project resource.

    :param request: the HTTP request (required).
    :return: the HTTP response.
    ---
    summary: Allowed HTTP methods.
    tags:
        - heaserver-awss3folders-projects
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
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    responses:
      '200':
        description: Expected response to a valid request.
        content:
            text/plain:
                schema:
                    type: string
                    example: "200: OK"
      '404':
        $ref: '#/components/responses/404'
    """
    return await response.get_options(request, ['GET', 'PUT', 'DELETE', 'HEAD', 'OPTIONS'])

@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/duplicator')
@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/duplicatorasync')
@action(name='heaserver-awss3folders-project-duplicate-form')
@action(name='heaserver-awss3folders-project-get-self', rel='self hea-self-container',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}')
async def get_project_duplicator(request: web.Request) -> web.Response:
    """
    Gets a form template for duplicating the requested project.

    :param request: the HTTP request. Required.
    :return: the requested form, or Not Found if the requested project was not found.
    ---
    summary: A project to duplicate.
    tags:
        - heaserver-awss3folders-projects
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
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    responses:
      '200':
        $ref: '#/components/responses/200'
      '404':
        $ref: '#/components/responses/404'
    """
    return await _get_project_move_template(request)

@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/archive')
@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/archiveasync')
@action(name='heaserver-awss3folders-project-archive-form')
@action(name='heaserver-awss3folders-project-get-self', rel='self hea-self-container',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}')
async def get_project_archive(request: web.Request) -> web.Response:
    """
    Gets a form template for archiving the requested project.

    :param request: the HTTP request. Required.
    :return: the requested form, or Not Found if the requested project was not found.
    ---
    summary: A specific project to be archived.
    tags:
        - heaserver-awss3folders-projects
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
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    responses:
      '204':
        $ref: '#/components/responses/204'
      '400':
        $ref: '#/components/responses/400'
      '404':
        $ref: '#/components/responses/404'
    """
    return await _get_project_move_template(request)

@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/unarchive')
@action(name='heaserver-awss3folders-project-unarchive-form')
@action(name='heaserver-awss3folders-project-get-self', rel='self hea-self-container',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}')
async def get_project_unarchive(request: web.Request) -> web.Response:
    """
    Gets a form template for unarchiving the requested project.

    :param request: the HTTP request. Required.
    :return: the requested form, or Not Found if the requested project was not found.
    ---
    summary: A specific project to be archived.
    tags:
        - heaserver-awss3folders-projects
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
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    responses:
      '204':
        $ref: '#/components/responses/204'
      '400':
        $ref: '#/components/responses/400'
      '404':
        $ref: '#/components/responses/404'
    """
    return await _get_project_move_template(request)


@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/mover')
@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/moverasync')
@action(name='heaserver-awss3folders-project-move-form')
@action(name='heaserver-awss3folders-project-get-self', rel='self hea-self-container',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}')
async def get_project_mover(request: web.Request) -> web.Response:
    """
    Gets a form template for moving the requested project.

    :param request: the HTTP request. Required.
    :return: the requested form, or Not Found if the requested project was not found.
    ---
    summary: A project to move.
    tags:
        - heaserver-awss3folders-projects
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
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    responses:
      '200':
        $ref: '#/components/responses/200'
      '404':
        $ref: '#/components/responses/404'
    """
    return await _get_project_move_template(request)


@routes.post('/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/archive')
async def post_project_archive(request: web.Request) -> web.Response:
    """
    Posts the provided project to archive it.

    :param request: the HTTP request.
    :return: a Response object with a status of No Content.
    ---
    summary: A specific project to be archived.
    tags:
        - heaserver-awss3folders-projects
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
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    requestBody:
        description: The new name of the project and target for archiving it.
        required: true
        content:
            application/vnd.collection+json:
              schema:
                type: object
              examples:
                example:
                  summary: The name of the storage class to archive the projects to
                  value: {
                    "template": {
                      "data": [
                      {
                        "name": "storage_class",
                        "value": "DEEP_ARCHIVE"
                      }
                      ]
                    }
                  }
            application/json:
              schema:
                type: object
              examples:
                example:
                  summary: The new name of the project and target for moving it.
                  value: {
                    "target": "http://localhost:8080/volumes/666f6f2d6261722d71757578/buckets/my-bucket/awss3projects/"
                  }
    responses:
      '204':
        $ref: '#/components/responses/204'
      '400':
        $ref: '#/components/responses/400'
      '404':
        $ref: '#/components/responses/404'
    """
    sub = request.headers.get(SUB, NONE_USER)
    id_ = request.match_info['id']
    volume_id = request.match_info['volume_id']
    bucket_name = request.match_info['bucket_id']
    key = awsservicelib.decode_folder(id_)
    if key is None:
        return await response.get(request, None)

    if not awsservicelib.is_folder(key):
        return await response.get(request, None)
    if not await _is_project(request, volume_id, bucket_name, id_):
        return response.status_not_found()
    try:
        return await awsservicelib.archive_object(request, activity_cb=publish_desktop_object)
    finally:
        logging.getLogger(__name__).debug('Cache before: %s', request.app[HEA_CACHE])
        request.app[HEA_CACHE].pop((sub, volume_id, bucket_name, None, 'actual'), None)
        request.app[HEA_CACHE].pop((sub, volume_id, bucket_name, id_, 'actual'), None)
        request.app[HEA_CACHE].pop((sub, volume_id, bucket_name, id_, None, 'items'), None)
        for key_ in tuple(request.app[HEA_CACHE].keys()):
            if key_[0:3] == (sub, volume_id, bucket_name) and key_[3] not in (None, 'root') and decode_key(key_[3]).startswith(key):
                request.app[HEA_CACHE].pop(key_, None)
        logging.getLogger(__name__).debug('Cache after: %s', request.app[HEA_CACHE])


@routes.post('/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/archiveasync')
async def post_project_archive_async(request: web.Request) -> web.Response:
    """
    Posts the provided project to archive it.

    :param request: the HTTP request.
    :return: a Response object with a status of No Content.
    ---
    summary: A specific project to be archived.
    tags:
        - heaserver-awss3folders-projects
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
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    requestBody:
        description: The new name of the project and target for archiving it.
        required: true
        content:
            application/vnd.collection+json:
              schema:
                type: object
              examples:
                example:
                  summary: The name of the storage class to archive the projects to
                  value: {
                    "template": {
                      "data": [
                      {
                        "name": "storage_class",
                        "value": "DEEP_ARCHIVE"
                      }
                      ]
                    }
                  }
            application/json:
              schema:
                type: object
              examples:
                example:
                  summary: The new name of the project and target for moving it.
                  value: {
                    "target": "http://localhost:8080/volumes/666f6f2d6261722d71757578/buckets/my-bucket/awss3projects/"
                  }
    responses:
      '204':
        $ref: '#/components/responses/204'
      '400':
        $ref: '#/components/responses/400'
      '404':
        $ref: '#/components/responses/404'
    """
    sub = request.headers.get(SUB, NONE_USER)
    id_ = request.match_info['id']
    volume_id = request.match_info['volume_id']
    bucket_name = request.match_info['bucket_id']
    key = awsservicelib.decode_folder(id_)
    if key is None:
        return await response.get(request, None)

    if not awsservicelib.is_folder(key):
        return await response.get(request, None)
    if not await _is_project(request, volume_id, bucket_name, id_):
        return response.status_not_found()
    async def publish_desktop_object_and_clear_cache(app: web.Application, desktop_object: DesktopObject,
                                 appproperty_=HEA_MESSAGE_BROKER_PUBLISHER):
        if isinstance(desktop_object, Activity):
            logging.getLogger(__name__).debug('Cache before: %s', request.app[HEA_CACHE])
            request.app[HEA_CACHE].pop((sub, volume_id, bucket_name, None, 'actual'), None)
            request.app[HEA_CACHE].pop((sub, volume_id, bucket_name, id_, 'actual'), None)
            request.app[HEA_CACHE].pop((sub, volume_id, bucket_name, id_, None, 'items'), None)
            for key_ in tuple(request.app[HEA_CACHE].keys()):
                if key_[0:3] == (sub, volume_id, bucket_name) and key_[3] not in (None, 'root') and decode_key(key_[3]).startswith(key):
                    request.app[HEA_CACHE].pop(key_, None)
            logging.getLogger(__name__).debug('Cache after: %s', request.app[HEA_CACHE])
        await publish_desktop_object(app, desktop_object, appproperty_)
    path = f'{request.url.path}status'
    return await awsservicelib.archive_object_async(request, request.url.with_path(path), activity_cb=publish_desktop_object_and_clear_cache)


@routes.post('/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/unarchive')
async def unarchive_project(request: web.Request) -> web.Response:
    """

    :param request:
    :return: a Response object with status 202 Accept

    ---
    summary: A specific project.
    tags:
        - heaserver-awss3folders-projects
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
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    responses:
      '201':
        $ref: '#/components/responses/201'
      '400':
        $ref: '#/components/responses/400'
      '404':
        $ref: '#/components/responses/404'
    """
    id_ = request.match_info['id']
    volume_id = request.match_info['volume_id']
    bucket_name = request.match_info['bucket_id']
    key = awsservicelib.decode_folder(id_)
    if key is None:
        return await response.get(request, None)

    if not awsservicelib.is_folder(key):
        return await response.get(request, None)
    if await _is_project(request, volume_id, bucket_name, id_):
        try:
            return await awsservicelib.unarchive_object(request=request, activity_cb=publish_desktop_object,
                                                        skip_restore_already_in_progress=True)
        finally:
            sub = request.headers.get(SUB, NONE_USER)
            request.app[HEA_CACHE].pop((sub, volume_id, bucket_name, None, 'actual'), None)
            request.app[HEA_CACHE].pop((sub, volume_id, bucket_name, id_, 'actual'), None)
            request.app[HEA_CACHE].pop((sub, volume_id, bucket_name, id_, None, 'items'), None)
            for key_ in tuple(request.app[HEA_CACHE].keys()):
                if key_[0:3] == (sub, volume_id, bucket_name) and key_[3] not in (None, 'root') and decode_key(key_[3]).startswith(key):
                    request.app[HEA_CACHE].pop(key_, None)
    else:
        return await response.get(request, None)


@routes.post('/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/mover')
async def post_project_mover(request: web.Request) -> web.Response:
    """
    Posts the provided project to move it.

    :param request: the HTTP request.
    :return: a Response object with a status of No Content.
    ---
    summary: A specific project.
    tags:
        - heaserver-awss3folders-projects
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
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    requestBody:
        description: The new name of the project and target for moving it.
        required: true
        content:
            application/vnd.collection+json:
              schema:
                type: object
              examples:
                example:
                  summary: The new name of the project and target for moving it.
                  value: {
                    "template": {
                      "data": [
                      {
                        "name": "target",
                        "value": "http://localhost:8080/volumes/666f6f2d6261722d71757578/buckets/my-bucket/awss3projects/"
                      }]
                    }
                  }
            application/json:
              schema:
                type: object
              examples:
                example:
                  summary: The new name of the project and target for moving it.
                  value: {
                    "target": "http://localhost:8080/volumes/666f6f2d6261722d71757578/buckets/my-bucket/awss3projects/"
                  }
    responses:
      '204':
        $ref: '#/components/responses/204'
      '400':
        $ref: '#/components/responses/400'
      '404':
        $ref: '#/components/responses/404'
    """
    sub = request.headers.get(SUB, NONE_USER)
    volume_id = request.match_info['volume_id']
    bucket_id = request.match_info['bucket_id']
    id_ = request.match_info['id']
    key = awsservicelib.decode_folder(id_)
    if key is None:
        return response.status_not_found()
    if not awsservicelib.is_folder(key):
        return response.status_not_found()
    return await _do_move(request, sub, volume_id, bucket_id, id_, key)


_move_lock = asyncio.Lock()

@routes.post('/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/moverasync')
async def post_project_mover_async(request: web.Request) -> web.Response:
    """
    Posts the provided project to move it.

    :param request: the HTTP request.
    :return: a Response object with a status of No Content.
    ---
    summary: A specific project.
    tags:
        - heaserver-awss3folders-projects
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
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    requestBody:
        description: The new name of the project and target for moving it.
        required: true
        content:
            application/vnd.collection+json:
              schema:
                type: object
              examples:
                example:
                  summary: The new name of the project and target for moving it.
                  value: {
                    "template": {
                      "data": [
                      {
                        "name": "target",
                        "value": "http://localhost:8080/volumes/666f6f2d6261722d71757578/buckets/my-bucket/awss3projects/"
                      }]
                    }
                  }
            application/json:
              schema:
                type: object
              examples:
                example:
                  summary: The new name of the project and target for moving it.
                  value: {
                    "target": "http://localhost:8080/volumes/666f6f2d6261722d71757578/buckets/my-bucket/awss3projects/"
                  }
    responses:
      '204':
        $ref: '#/components/responses/204'
      '400':
        $ref: '#/components/responses/400'
      '404':
        $ref: '#/components/responses/404'
    """
    sub = request.headers.get(SUB, NONE_USER)
    volume_id = request.match_info['volume_id']
    bucket_id = request.match_info['bucket_id']
    id_ = request.match_info['id']
    key = awsservicelib.decode_folder(id_)
    if key is None:
        return response.status_not_found()
    if not awsservicelib.is_folder(key):
        return response.status_not_found()

    async def coro(app: web.Application):
        return await _do_move(request, sub, volume_id, bucket_id, id_, key)
    path = f'{request.url.path}status'
    status_location = request.url.with_path(path)
    task_name = f'{sub}^{status_location}'
    async with _move_lock:
        if request.app[HEA_BACKGROUND_TASKS].in_progress(task_name):
            return response.status_conflict(f'A move of {awsservicelib.s3_object_message_display_name(bucket_id, key)} is already in progress')
        await request.app[HEA_BACKGROUND_TASKS].add(coro, name=task_name)
    return response.status_see_other(status_location)


async def _do_move(request: web.Request, sub: str, volume_id: str, bucket_id: str, id_: str, key: str) -> web.Response:
    try:
        _, target_bucket_id, target_key_parent, new_volume_id, target_path = await awsservicelib._copy_object_extract_target(await request.json())
    except web.HTTPBadRequest as e:
        return e
    async with DesktopObjectActionLifecycle(request=request,
                                            code='hea-move',
                                            description=f'Moving {awsservicelib.s3_object_message_display_name(bucket_id, key)} to {awsservicelib.s3_object_message_display_name(target_bucket_id, target_key_parent)}',
                                            activity_cb=publish_desktop_object) as activity:
        async with mongo.MongoContext(request) as mongo_client:
            metadata_dict = await awsservicelib.get_metadata(mongo_client, bucket_id, id_)
            if not metadata_dict or metadata_dict['actual_object_type_name'] != AWSS3Project.get_type_name():
                return response.status_not_found()
            return await move(activity, request, mongo_client, sub, volume_id, bucket_id, id_, key,
                              new_volume_id, target_bucket_id, target_key_parent, AWSS3Project, target_path)


@routes.post('/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/duplicator')
async def post_project_duplicator(request: web.Request) -> web.Response:
    """
    Posts the provided project for duplication.

    :param request: the HTTP request.
    :return: a Response object with a status of Created and the object's URI in the
    ---
    summary: A specific folder item.
    tags:
        - heaserver-awss3folders-projects
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
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    requestBody:
        description: The target folder or project.
        required: true
        content:
            application/vnd.collection+json:
              schema:
                type: object
              examples:
                example:
                  summary: The target folder or project.
                  value: {
                    "template": {
                      "data": [
                      {
                        "name": "target",
                        "value": "http://localhost:8080/volumes/666f6f2d6261722d71757578/buckets/my-bucket"
                      }]
                    }
                  }
            application/json:
              schema:
                type: object
              examples:
                example:
                  summary: The target folder or project.
                  value: {
                    "target": "http://localhost:8080/volumes/666f6f2d6261722d71757578/buckets/my-bucket"
                  }
    responses:
      '201':
        $ref: '#/components/responses/201'
      '400':
        $ref: '#/components/responses/400'
      '404':
        $ref: '#/components/responses/404'
    """
    bucket_id = request.match_info['bucket_id']
    id_ = request.match_info['id']
    try:
        key = awsservicelib.decode_folder(id_)
    except KeyDecodeException as e:
        return response.status_not_found()
    if not awsservicelib.is_folder(key):
        return response.status_not_found()

    async with mongo.MongoContext(request) as mongo_client:
        metadata_dict = await awsservicelib.get_metadata(mongo_client, bucket_id, id_)
        if not metadata_dict or metadata_dict['actual_object_type_name'] != AWSS3Project.get_type_name():
            return response.status_not_found()

        _, _, target_key_parent, new_volume_id, target_path = await awsservicelib._copy_object_extract_target(await request.json())

        return await copy(request, mongo_client, target_key_parent, new_volume_id, target_path=target_path)


@routes.post('/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/duplicatorasync')
async def post_project_duplicator_async(request: web.Request) -> web.Response:
    """
    Posts the provided project for duplication.

    :param request: the HTTP request.
    :return: a Response object with a status of Created and the object's URI in the
    ---
    summary: A specific folder item.
    tags:
        - heaserver-awss3folders-projects
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
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    requestBody:
        description: The target folder or project.
        required: true
        content:
            application/vnd.collection+json:
              schema:
                type: object
              examples:
                example:
                  summary: The target folder or project.
                  value: {
                    "template": {
                      "data": [
                      {
                        "name": "target",
                        "value": "http://localhost:8080/volumes/666f6f2d6261722d71757578/buckets/my-bucket"
                      }]
                    }
                  }
            application/json:
              schema:
                type: object
              examples:
                example:
                  summary: The target folder or project.
                  value: {
                    "target": "http://localhost:8080/volumes/666f6f2d6261722d71757578/buckets/my-bucket"
                  }
    responses:
      '201':
        $ref: '#/components/responses/201'
      '400':
        $ref: '#/components/responses/400'
      '404':
        $ref: '#/components/responses/404'
    """
    bucket_id = request.match_info['bucket_id']
    id_ = request.match_info['id']
    try:
        key = awsservicelib.decode_folder(id_)
    except KeyDecodeException as e:
        return response.status_not_found()
    if not awsservicelib.is_folder(key):
        return response.status_not_found()

    global _status_id
    path = f'{request.url.path}status{_status_id}'
    status_location = str(request.url.with_path(path))  # Don't keep query params.
    _status_id += 1
    async with mongo.MongoContext(request) as mongo_client:
        metadata_dict = await awsservicelib.get_metadata(mongo_client, bucket_id, id_)
        if not metadata_dict or metadata_dict['actual_object_type_name'] != AWSS3Project.get_type_name():
            return response.status_not_found()
        _, _, target_key_parent, new_volume_id, target_path = await awsservicelib._copy_object_extract_target(await request.json())
        return await copy(request, mongo_client, target_key_parent, new_volume_id, status_location, target_path)


@routes.post('/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/uploader')
@routes.post('/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/uploader/')
async def post_project_uploader(request: web.Request) -> web.Response:
    """
    Uploads file to a target project.

    :param request: the HTTP request. The body of the request is expected to be an item or an actual object.
    :return: the response, with a 204 status code if an item was created or a 400 if not. If an item was created, the
    Location header will contain the URL of the created item.
    ---
    summary: A upload to a specific folder item.
    tags:
        - heaserver-awss3folders-projects
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
        - name: id
          in: path
          required: true
          description: The id of the folder.
          schema:
            type: string
          examples:
            example:
              summary: A folder id
              value: root
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    requestBody:
        description: A new folder item object.
        required: true
        content:
            application/vnd.collection+json:
              schema:
                type: object
              examples:
                example:
                  summary: Item example
                  value: {
                    "template": {
                      "data": [{
                        "name": "created",
                        "value": null
                      },
                      {
                        "name": "derived_by",
                        "value": null
                      },
                      {
                        "name": "derived_from",
                        "value": []
                      },
                      {
                        "name": "description",
                        "value": null
                      },
                      {
                        "name": "display_name",
                        "value": "Bob"
                      },
                      {
                        "name": "invited",
                        "value": []
                      },
                      {
                        "name": "modified",
                        "value": null
                      },
                      {
                        "name": "name",
                        "value": "bob"
                      },
                      {
                        "name": "owner",
                        "value": "system|none"
                      },
                      {
                        "name": "shares",
                        "value": []
                      },
                      {
                        "name": "source",
                        "value": null
                      },
                      {
                        "name": "version",
                        "value": null
                      },
                      {
                        "name": "actual_object_id",
                        "value": "666f6f2d6261722d71757578"
                      },
                      {
                        "name": "actual_object_type_name",
                        "value": "heaobject.data.AWSS3FileObject"
                      },
                      {
                        "name": "actual_object_uri",
                        "value": "/volumes/666f6f2d6261722d71757578/buckets/my-bucket/folders/666f6f2d6261722d71757578"
                      },
                      {
                        "name": "type",
                        "value": "heaobject.folder.AWSS3ItemInFolder"
                      }]
                    }
                  }
            application/json:
              schema:
                type: object
              examples:
                example:
                  summary: Item example
                  value: {
                    "created": null,
                    "derived_by": null,
                    "derived_from": [],
                    "description": null,
                    "display_name": "Joe",
                    "invited": [],
                    "modified": null,
                    "name": "joe",
                    "owner": "system|none",
                    "shares": [],
                    "source": null,
                    "type": "heaobject.folder.AWSS3Item",
                    "version": null,
                    "folder_id": "root",
                    "actual_object_id": "666f6f2d6261722d71757578",
                    "actual_object_type_name": "heaobject.registry.Component",
                    "actual_object_uri": "/volumes/666f6f2d6261722d71757578/buckets/my-bucket/folders/666f6f2d6261722d71757578"
                  }
    responses:
      '201':
        $ref: '#/components/responses/201'
      '400':
        $ref: '#/components/responses/400'
      '404':
        $ref: '#/components/responses/404'
    """
    logger = logging.getLogger(__name__)
    sub = request.headers.get(SUB, NONE_USER)
    try:
        obj = await new_heaobject_from_type(request, AWSS3FileObject)
    except DeserializeException as e:
        return response.status_bad_request(str(e).encode())

    if obj is None:
        return response.status_bad_request('The request body must have a desktop object')
    if obj.display_name is None:
        return response.status_bad_request("display_name is required")
    if obj.name is None:
        return response.status_bad_request("name cannot be None")
    if obj.storage_class is None:
        return response.status_bad_request('storage_class is required')
    if '/' in obj.display_name:
        return response.status_bad_request(f"The item's display name may not have slashes in it")
    assert obj.key is not None, 'key is required'

    logger.debug("the obj's name and display_name %s, %s", obj.name, obj.display_name)
    volume_id = request.match_info['volume_id']
    bucket_id = request.match_info['bucket_id']
    folder_id = request.match_info['id']

    try:
        # if folder id is root let it decode to '' otherwise if its not a Folder set it to None
        decoded_folder_id = awsservicelib.decode_folder(folder_id)
        if folder_id != awsservicelib.ROOT_FOLDER.id and not awsservicelib.is_folder(decoded_folder_id):
            decoded_folder_id = None
    except KeyDecodeException:
        decoded_folder_id = None
    if not await _is_project(request, volume_id, bucket_id, folder_id):
        return response.status_not_found()

    async with DesktopObjectActionLifecycle(request=request,
                                            code='hea-create',
                                            description=f'Uploading {obj.display_name} into bucket {bucket_id}',
                                            activity_cb=publish_desktop_object) as activity:
        async with aws.S3ClientContext(request=request, volume_id=volume_id) as s3_client:
            loop = asyncio.get_running_loop()
            try:
                if decoded_folder_id is None:
                    await loop.run_in_executor(None, partial(s3_client.head_bucket, Bucket=bucket_id))
                    raise response.status_not_found()
            except BotoClientError as e:
                if e.response['Error']['Code'] == aws.CLIENT_ERROR_NO_SUCH_BUCKET:
                    raise response.status_not_found()
                else:
                    raise response.status_bad_request(str(e))
            url = f"volumes/{request.match_info['volume_id']}/buckets/{request.match_info['bucket_id']}/awss3files"
            obj_name = f'{decoded_folder_id}{decode_key(obj.name)}'
            try:
                if await loop.run_in_executor(None, partial(s3_client.head_object, Bucket=bucket_id, Key=obj.key)):
                    activity.old_volume_id = volume_id
                    activity.old_object_id = obj.id
                    activity.old_object_type_name = obj.type
                    activity.old_object_uri = '/'.join([f'volumes/{volume_id}', f'buckets/{bucket_id}', f'awss3folders/{folder_id}'])
                    activity.old_object_display_name = obj.display_name
                    if 'path' in request.url.query:
                        activity.old_context_dependent_object_path = request.url.query.getall('path')
                content_id = f"{encode_key(obj_name)}/content"
                # check if item exists, if not throws an exception
                await loop.run_in_executor(None, partial(s3_client.head_object, Bucket=bucket_id, Key=obj_name))
                activity.new_volume_id = volume_id
                activity.new_object_id = obj.id
                activity.new_object_type_name = obj.type
                activity.new_object_uri = '/'.join([f'volumes/{volume_id}', f'buckets/{bucket_id}', f'awss3folders/{folder_id}'])
                activity.new_object_display_name = obj.display_name
                if 'path' in request.url.query:
                    activity.old_context_dependent_object_path = request.url.query.getall('path')
                return response.status_ok(headers={hdrs.LOCATION: f"/{url}/{content_id}"})
            except BotoClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == aws.CLIENT_ERROR_404:  # file metadata doesn't exist
                    try:
                        await loop.run_in_executor(None, partial(s3_client.put_object, Bucket=bucket_id, Key=obj_name))
                        request.app[HEA_CACHE].pop((sub, volume_id, bucket_id, folder_id, None, 'items'), None)
                        request.app[HEA_CACHE].pop((sub, volume_id, bucket_id, folder_id, obj.id, 'items'), None)
                        request.app[HEA_CACHE].pop((sub, volume_id, bucket_id, None, 'actual'), None)
                        request.app[HEA_CACHE].pop((sub, volume_id, bucket_id, obj.id, 'actual'), None)
                        return await response.post(request, f"{encode_key(obj_name)}/content", url)
                    except BotoClientError as e2:
                        raise awsservicelib.handle_client_error(e2)
                else:
                    activity.status = Status.FAILED
                    return response.status_bad_request(str(e))


@routes.post('/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{folder_id}/items')
@routes.post('/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{folder_id}/items/')
async def post_item_in_project(request: web.Request) -> web.Response:
    """
    Creates a new item in a project.

    :param request: the HTTP request. The body of the request is expected to be an item or an actual object.
    :return: the response, with a 204 status code if an item was created or a 400 if not. If an item was created, the
    Location header will contain the URL of the created item.
    ---
    summary: A specific project item.
    tags:
        - heaserver-awss3folders-project-items
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
        - name: folder_id
          in: path
          required: true
          description: The id of the folder.
          schema:
            type: string
          examples:
            example:
              summary: A folder id
              value: root
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    requestBody:
        description: A new project item object.
        required: true
        content:
            application/vnd.collection+json:
              schema:
                type: object
              examples:
                example:
                  summary: Item example
                  value: {
                    "template": {
                      "data": [{
                        "name": "created",
                        "value": null
                      },
                      {
                        "name": "derived_by",
                        "value": null
                      },
                      {
                        "name": "derived_from",
                        "value": []
                      },
                      {
                        "name": "description",
                        "value": null
                      },
                      {
                        "name": "display_name",
                        "value": "Bob"
                      },
                      {
                        "name": "invited",
                        "value": []
                      },
                      {
                        "name": "modified",
                        "value": null
                      },
                      {
                        "name": "name",
                        "value": "bob"
                      },
                      {
                        "name": "owner",
                        "value": "system|none"
                      },
                      {
                        "name": "shares",
                        "value": []
                      },
                      {
                        "name": "source",
                        "value": null
                      },
                      {
                        "name": "version",
                        "value": null
                      },
                      {
                        "name": "actual_object_id",
                        "value": "666f6f2d6261722d71757578"
                      },
                      {
                        "name": "actual_object_type_name",
                        "value": "heaobject.data.AWSS3FileObject"
                      },
                      {
                        "name": "actual_object_uri",
                        "value": "/volumes/666f6f2d6261722d71757578/buckets/my-bucket/folders/666f6f2d6261722d71757578"
                      },
                      {
                        "name": "type",
                        "value": "heaobject.folder.AWSS3ItemInFolder"
                      }]
                    }
                  }
            application/json:
              schema:
                type: object
              examples:
                example:
                  summary: Item example
                  value: {
                    "created": null,
                    "derived_by": null,
                    "derived_from": [],
                    "description": null,
                    "display_name": "Joe",
                    "invited": [],
                    "modified": null,
                    "name": "joe",
                    "owner": "system|none",
                    "shares": [],
                    "source": null,
                    "type": "heaobject.folder.AWSS3Item",
                    "version": null,
                    "folder_id": "root",
                    "actual_object_id": "666f6f2d6261722d71757578",
                    "actual_object_type_name": "heaobject.registry.Component",
                    "actual_object_uri": "/volumes/666f6f2d6261722d71757578/buckets/my-bucket/folders/666f6f2d6261722d71757578"
                  }
    responses:
      '201':
        $ref: '#/components/responses/201'
      '400':
        $ref: '#/components/responses/400'
      '404':
        $ref: '#/components/responses/404'
    """
    sub = request.headers.get(SUB, NONE_USER)
    try:
        item = await new_heaobject_from_type(request, AWSS3ItemInFolder)
    except DeserializeException as e:
        return response.status_bad_request(str(e).encode())

    logger = logging.getLogger(__name__)
    if item.display_name is None:
        return response.status_bad_request("display_name is required")
    volume_id = request.match_info['volume_id']
    bucket_id = request.match_info['bucket_id']
    folder_id = request.match_info['folder_id']

    if item is None:
        return response.status_bad_request('item is a required field')

    if item.folder_id is not None and folder_id != item.folder_id:
        return response.status_bad_request(
            f'folder_id in object was {item.folder_id} but folder_id in URL was {folder_id}')
    if item.folder_id is not None and item.folder_id != folder_id:
        return response.status_bad_request(
            f'Inconsistent folder_id in URL versus item: {folder_id} vs {item.folder_id}')
    if '/' in item.display_name:
        return response.status_bad_request(f"The item's display name may not have slashes in it")

    folder_key = awsservicelib.decode_folder(folder_id)
    if folder_key is None:
        return response.status_not_found()

    if folder_id != awsservicelib.ROOT_FOLDER.id and not awsservicelib.is_folder(folder_key):
        return response.status_not_found()

    if not await _is_project(request, volume_id, bucket_id, folder_key):
        return response.status_not_found()

    async with DesktopObjectActionLifecycle(request=request,
                                            code='hea-create',
                                            description=f'Creating item {item.display_name} in bucket {bucket_id}',
                                            activity_cb=publish_desktop_object) as activity:
        async with aws.S3ClientContext(request=request, volume_id=volume_id) as s3_client:
            loop = asyncio.get_running_loop()
            try:
                if folder_key is None:
                    await loop.run_in_executor(None, partial(s3_client.head_bucket, Bucket=bucket_id))
                    activity.status = Status.FAILED
                    return response.status_not_found()
                item_name = f'{folder_key}{item.display_name}'
                if item.actual_object_type_name in (AWSS3Folder.get_type_name(), AWSS3Project.get_type_name()):
                    item_name += '/'
                elif item.actual_object_type_name == AWSS3FileObject.get_type_name():
                    pass
                else:
                    activity.status = Status.FAILED
                    return response.status_bad_request(f'Unsupported actual_object_type_name {item.actual_object_type_name}')
                response_ = await loop.run_in_executor(None, partial(s3_client.head_object, Bucket=bucket_id,
                                                                    Key=item_name))  # check if item exists, if not throws an exception
                logger.debug('Result of post_object: %s', response_)
                activity.status = Status.FAILED
                return response.status_bad_request(body=f"{awsservicelib.s3_object_message_display_name(bucket_id, item_name)} already exists")
            except BotoClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == aws.CLIENT_ERROR_404:  # folder doesn't exist
                    await loop.run_in_executor(None, partial(s3_client.put_object, Bucket=bucket_id, Key=item_name))
                    logger.info('Added item %s', item_name)
                    if item.actual_object_type_name == AWSS3Project.get_type_name():
                        async with mongo.MongoContext(request) as mongo_client:
                            metadata = {
                                'bucket_id': bucket_id,
                                'encoded_key': item.id,
                                'actual_object_type_name': AWSS3Project.get_type_name(),
                                'parent_encoded_key': folder_id
                            }
                            await mongo_client.upsert_admin_nondesktop_object(metadata, MONGODB_AWS_S3_FOLDER_METADATA_COLLECTION,
                                                                              mongoattributes={'bucket_id': bucket_id, 'encoded_key': item.id})
                    activity.new_object_id = encode_key(item_name)
                    activity.new_object_type_name = AWSS3ItemInFolder.get_type_name()
                    activity.new_volume_id = request.match_info['volume_id']
                    activity.new_object_uri = f"volumes/{activity.new_volume_id}/buckets/{request.match_info['bucket_id']}/awss3projects/{folder_id}/items/{activity.new_object_id}"
                    activity.new_object_display_name = item.display_name
                    activity.new_object_description = item.description
                    if 'path' in request.url.query:
                        activity.new_context_dependent_object_path = request.url.query.getall('path')
                    request.app[HEA_CACHE].pop((sub, volume_id, bucket_id, folder_id, None, 'items'), None)
                    request.app[HEA_CACHE].pop((sub, volume_id, bucket_id, None, 'actual'), None)
                    return await response.post(request, activity.new_object_id,
                                            f"volumes/{activity.new_volume_id}/buckets/{request.match_info['bucket_id']}/awss3projects/{folder_id}/items")
                elif error_code == aws.CLIENT_ERROR_NO_SUCH_BUCKET:
                    activity.status = Status.FAILED
                    return response.status_not_found()
                else:
                    activity.status = Status.FAILED
                    return response.status_bad_request(str(e))


@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}')
@action(name='heaserver-awss3folders-project-get-open-choices', rel='hea-opener-choices hea-context-menu hea-downloader',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/opener')
@action(name='heaserver-awss3folders-project-get-properties', rel='hea-properties hea-context-menu')
@action(name='heaserver-awss3folders-project-duplicate', rel='hea-dynamic-standard hea-icon-duplicator hea-context-menu',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/duplicatorasync')
@action(name='heaserver-awss3folders-project-move', rel='hea-dynamic-standard hea-icon-mover hea-context-menu',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/moverasync')
@action(name='heaserver-awss3folders-project-get-create-choices', rel='hea-creator-choices hea-context-menu',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/creator')
@action(name='heaserver-awss3folders-project-get-trash', rel='hea-trash hea-context-menu',
        path='volumes/{volume_id}/awss3trash')
@action(name='heaserver-awss3folders-project-archive', rel='hea-dynamic-standard hea-archive hea-context-menu',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/archiveasync')
@action(name='heaserver-awss3folders-project-unarchive', rel='hea-dynamic-standard hea-unarchive hea-context-menu',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/unarchive')
@action(name='heaserver-awss3folders-project-get-presigned-url',
        rel='hea-dynamic-clipboard hea-icon-for-clipboard hea-context-menu',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/presignedurl')
@action(name='heaserver-awss3folders-project-get-self', rel='self hea-self-container',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}')
@action(name='heaserver-awss3folders-project-get-volume', rel='hea-volume', path='volumes/{volume_id}')
@action(name='heaserver-awss3folders-project-get-awsaccount', rel='hea-account',
        path='volumes/{volume_id}/awsaccounts/me')
@action(name='heaserver-awss3folders-item-upload', rel='hea-uploader',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/uploader')
@action(name='heaserver-awss3folders-project-get-component', rel='hea-component',
        path='components/bytype/heaobject.project.AWSS3Project')
@action(name='heaserver-awss3folders-get-delete-preflight-url', rel='hea-delete-preflight',
        path='preflights/awss3objects/delete')
async def get_project(request: web.Request) -> web.Response:
    """
    Gets the project with the specified id.

    :param request: the HTTP request.
    :return: the requested project or Not Found.
    ---
    summary: A specific folder.
    tags:
        - heaserver-awss3folders-projects
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
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    responses:
      '200':
        $ref: '#/components/responses/200'
      '404':
        $ref: '#/components/responses/404'
    """
    context = aws.S3ObjectPermissionContext(request)
    return await _get_project(request, context)


@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/byname/{name}')
@action(name='heaserver-awss3folders-project-get-self', rel='self hea-self-container',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}')
@action(name='heaserver-awss3folders-project-get-volume', rel='hea-volume', path='volumes/{volume_id}')
@action(name='heaserver-awss3folders-project-get-awsaccount', rel='hea-account',
        path='volumes/{volume_id}/awsaccounts/me')
@action(name='heaserver-awss3folders-project-get-component', rel='hea-component',
        path='components/bytype/heaobject.project.AWSS3Project')
async def get_project_by_name(request: web.Request) -> web.Response:
    """
    Gets the project with the specified name.

    :param request: the HTTP request.
    :return: the requested project or Not Found.
    ---
    summary: A specific project.
    tags:
        - heaserver-awss3folders-projects
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
        - $ref: '#/components/parameters/name'
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    responses:
      '200':
        $ref: '#/components/responses/200'
      '404':
        $ref: '#/components/responses/404'
    """
    context = aws.S3ObjectPermissionContext(request)
    return await _get_project(request, context)

@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/content')
async def get_project_contents_as_zip_file(request: web.Request) -> web.StreamResponse:
    """
    Gets the contents of all objects within the project with the specified id.

    :param request: the HTTP request.
    :return: the requested project's content or Not Found.
    """
    logger = logging.getLogger(__name__)
    logger.debug('Getting project from request %s', request)
    volume_id = request.match_info['volume_id']
    bucket_name = request.match_info['bucket_id']
    project_name = request.match_info['id']
    sub = request.headers.get(SUB, NONE_USER)

    try:
        folder_key = decode_key(project_name)
    except KeyDecodeException as e:
        logger.debug('No project with id or name %s', project_name)
        return response.status_not_found()

    async with DesktopObjectActionLifecycle(request=request,
                                            code='hea-get',
                                            description=f'Downloading {awsservicelib.s3_object_message_display_name(bucket_name, folder_key)}',
                                            activity_cb=publish_desktop_object) as activity:
        async with aws.S3ClientContext(request=request, volume_id=volume_id) as s3_client:
            try:
                project, is_project = await asyncio.gather(_has_project_helper(s3_client, request),
                                                           _is_project(request, volume_id, bucket_name, project_name))
                if not project or not is_project:
                    logger.debug('No project with id or name %s', project_name)
                    activity.status = Status.FAILED
                    return await response.get(request, None)

                await awsservicelib.fail_if_too_big(bucket_name, folder_key, activity, s3_client)

                description, response_ = await asyncio.gather(get_description(sub, s3_client, bucket_name, folder_key),
                                                              response_folder_as_zip(s3_client, request, bucket_name, folder_key))
                activity.new_volume_id = volume_id
                activity.new_object_id = project_name
                activity.new_object_type_name = AWSS3Project.get_type_name()
                activity.new_object_uri = f'volumes/{volume_id}/buckets/{bucket_name}/awss3projects/{project_name}'
                activity.new_object_display_name = split(folder_key)[1].removesuffix('/')
                activity.new_object_description = description
                if 'path' in request.url.query:
                    activity.new_context_dependent_object_path = request.url.query.getall('path')
                return response_
            except BotoClientError as e:
                activity.status = Status.FAILED
                return awsservicelib.handle_client_error(e)

@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/presignedurl')
@action(name='heaserver-awss3folders-project-get-presigned-url-form')
@action(name='heaserver-awss3folders-project-get-self', rel='self hea-self-container',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}')
async def get_presigned_url_form(request: web.Request) -> web.Response:
    """
    Returns a template for requesting the generation of a presigned URL.

    :param request: the HTTP request.
    :return: No Content or Not Found.
    ---
    summary: Presigned url for folders
    tags:
        - heaserver-awss3folders-folders
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
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    responses:
      '200':
        $ref: '#/components/responses/200'
      '403':
        $ref: '#/components/responses/403'
      '404':
        $ref: '#/components/responses/404'
    """
    context = aws.S3ObjectPermissionContext(request)
    return await _get_project(request, context)

@routes.post('/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/presignedurl')
async def post_presigned_url_form(request: web.Request) -> web.Response:
    """
    Posts a template for requesting the generation of a presigned URL.

    :param request: the HTTP request.
    :return: No Content or Not Found.
    ---
    summary: Presigned url for projects
    tags:
        - heaserver-awss3folders-projects
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
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    requestBody:
        description: The expiration time for the presigned URL.
        required: true
        content:
            application/vnd.collection+json:
              schema:
                type: object
              examples:
                example:
                  summary: The expiration time for the presigned URL.
                  value: {
                    "template": {
                      "data": [
                      {
                        "name": "link_expiration",
                        "value": 259200
                      }]
                    }
                  }
            application/json:
              schema:
                type: object
              examples:
                example:
                  summary: The new name of the file and target for moving it.
                  value: {
                    "link_expiration": 259200
                  }
    responses:
      '200':
        $ref: '#/components/responses/200'
      '403':
        $ref: '#/components/responses/403'
      '404':
        $ref: '#/components/responses/404'
    """
    logger = logging.getLogger(__name__)
    sub = request.headers.get(SUB, NONE_USER)
    # Generate a presigned URL for the S3 object
    volume_id = request.match_info['volume_id']
    bucket_id = request.match_info['bucket_id']
    object_id = request.match_info['id']
    # three days default for expiration
    try:
        expiration_hours = await extract_expiration(await request.json())
    except JSONDecodeError as e:
        return response.status_bad_request(str(e))

    try:
        object_key: str | None = decode_key(object_id)
    except KeyDecodeException:
        object_key = None

    async with DesktopObjectActionLifecycle(request=request,
                                            code='hea-get',
                                            description=f'Generating presigned-URL(s) for {awsservicelib.s3_object_message_display_name(bucket_id, object_key or 'an object')}',
                                            activity_cb=publish_desktop_object) as activity:
        activity.old_object_id = object_id
        activity.old_object_uri = f'volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{object_id}'
        activity.old_object_type_name = AWSS3Project.get_type_name()
        activity.old_volume_id = volume_id
        if 'path' in request.url.query:
            activity.old_context_dependent_object_path = request.url.query.getall('path')
        async with aws.S3ClientContext(request, volume_id=volume_id) as s3_client:
            activity.old_object_description = await get_description(sub, s3_client, bucket_id, object_key)
            if not await _is_project(request, volume_id, bucket_id, object_id):
                object_key = None
            if object_key is None:
                raise await when_object_not_found(s3_client, bucket_id)
        activity.old_object_display_name = display_name(object_key)
        presigned_creds = await create_presigned_url_credentials(request, volume_id, expiration_hours, object_key, bucket_id)
        async with aws.S3ClientContext(request=request, credentials=presigned_creds) as presigned_s3_client:
            try:
                loop = asyncio.get_running_loop()
                urls = []

                async def get_links(obj):
                    url = await loop.run_in_executor(None, partial(presigned_s3_client.generate_presigned_url, 'get_object',
                                                                Params={'Bucket': bucket_id, 'Key': obj['Key']},
                                                                ExpiresIn=(expiration_hours * 60 * 60) if expiration_hours is not None else 259200))
                    urls.append(url)

                await queued_processing(awsservicelib.list_unarchived_objects(request, volume_id, bucket_id,
                                                                              object_key, loop),
                                        get_links)
            except BotoClientError as e:
                raise awsservicelib.handle_client_error(e)
            if not urls:
                raise response.status_bad_request('There are no files in this project, or all are in archived storage.')
            # The response contains the presigned URL
            data: ClipboardData = ClipboardData()
            data.mime_type = 'text/plain;encoding=utf-8'
            data.data = client_line_ending(request).join(urls)
            data.created = now()
            f: AWSS3FileObject = AWSS3FileObject()
            f.bucket_id = bucket_id
            f.id = object_id
            data.display_name = f'Presigned URL for {f.display_name}'
            activity.new_object_id = activity.old_object_id
            activity.new_object_uri = activity.old_object_uri
            activity.new_object_type_name = AWSS3Project.get_type_name()
            activity.new_volume_id = volume_id
            activity.new_object_display_name = activity.old_object_display_name
            activity.new_context_dependent_object_path = activity.old_context_dependent_object_path
            activity.new_object_description = activity.old_object_description
            return await response.get(request, to_dict(data))

@routes.post('/volumes/{volume_id}/buckets/{bucket_id}/awss3projects')
@routes.post('/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/')
async def post_project(request: web.Request) -> web.Response:
    """
    Creates a new project.

    :param request: the HTTP request. The body of the request is expected to be a project.
    :return: the response, with a 204 status code if a project was created. If a
    folder was created, the Location header will contain the URL of the created
    project.
    ---
    summary: A specific project.
    tags:
        - heaserver-awss3folders-projects
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
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    requestBody:
        description: A new project object.
        required: true
        content:
            application/vnd.collection+json:
              schema:
                type: object
              examples:
                example:
                  summary: Project example
                  value: {
                    "template": {
                      "data": [{
                        "name": "created",
                        "value": null
                      },
                      {
                        "name": "derived_by",
                        "value": null
                      },
                      {
                        "name": "derived_from",
                        "value": []
                      },
                      {
                        "name": "description",
                        "value": null
                      },
                      {
                        "name": "display_name",
                        "value": "Bob"
                      },
                      {
                        "name": "invited",
                        "value": []
                      },
                      {
                        "name": "modified",
                        "value": null
                      },
                      {
                        "name": "name",
                        "value": "bob"
                      },
                      {
                        "name": "owner",
                        "value": "system|none"
                      },
                      {
                        "name": "shares",
                        "value": []
                      },
                      {
                        "name": "source",
                        "value": null
                      },
                      {
                        "name": "version",
                        "value": null
                      },
                      {
                        "name": "type",
                        "value": "heaobject.project.AWSS3Project"
                      }]
                    }
                  }
            application/json:
              schema:
                type: object
              examples:
                example:
                  summary: Project example
                  value: {
                    "created": null,
                    "derived_by": null,
                    "derived_from": [],
                    "description": null,
                    "display_name": "Joe",
                    "invited": [],
                    "modified": null,
                    "name": "joe",
                    "owner": "system|none",
                    "shares": [],
                    "source": null,
                    "type": "heaobject.project.AWSS3Project",
                    "version": null
                  }
    responses:
      '201':
        $ref: '#/components/responses/201'
      '400':
        $ref: '#/components/responses/400'
      '404':
        $ref: '#/components/responses/404'
    """
    sub = request.headers.get(SUB, NONE_USER)
    volume_id = request.match_info['volume_id']
    bucket_id = request.match_info['bucket_id']

    try:
        project = await new_heaobject_from_type(request, AWSS3Project)
    except TypeError:
        return response.status_bad_request(f'Expected type {AWSS3Project}; actual object was {await request.text()}')
    except DeserializeException as e:
        return response.status_bad_request(str(e))
    response_ = await awsservicelib.create_object(request, AWSS3Project)
    assert project.key is not None, 'project.key cannot be None'
    parent_key = parent(project.key)
    if not (folder_id := encode_key(parent_key)):
        folder_id = 'root'
    request.app[HEA_CACHE].pop((sub, volume_id, bucket_id, folder_id, None, 'items'), None)
    request.app[HEA_CACHE].pop((sub, volume_id, bucket_id, None, 'actual'), None)
    if response_.status == 201:
        async with aws.S3ClientContext(request, volume_id) as s3_client:
            async with mongo.MongoContext(request) as mongo_client:

                metadata = {
                    'bucket_id': bucket_id,
                    'encoded_key': project.id,
                    'actual_object_type_name': AWSS3Project.get_type_name(),
                    'parent_encoded_key': folder_id,
                    'deleted': False,
                    'volume_id': volume_id
                }
                resp_ = await asyncio.get_running_loop().run_in_executor(None, partial(s3_client.head_object, Bucket=bucket_id, Key=project.key))
                metadata['version'] = resp_.get('VersionId')
            await mongo_client.upsert_admin_nondesktop_object(metadata,
                                            MONGODB_AWS_S3_FOLDER_METADATA_COLLECTION,
                                            mongoattributes={'bucket_id': bucket_id, 'encoded_key': project.id})
    return response_

@routes.put('/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}')
async def put_project(request: web.Request) -> web.Response:
    sub = request.headers.get(SUB, NONE_USER)
    volume_id = request.match_info['volume_id']
    bucket_id = request.match_info['bucket_id']
    old_id = request.match_info['id']
    old_key = awsservicelib.decode_folder(old_id)
    if old_key is None:
        return response.status_not_found()
    if not awsservicelib.is_folder(old_key) or not await _is_project(request, volume_id, bucket_id, old_id):
        return response.status_not_found()

    async def coro(app: web.Application):
        async with mongo.MongoContext(request) as mongo_client:
            try:
                project = await new_heaobject_from_type(request, AWSS3Project)
            except TypeError:
                return response.status_bad_request(f'Expected type {AWSS3Project}; actual object was {await request.text()}')
            except DeserializeException as e:
                return response.status_bad_request(str(e))
            async with DesktopObjectActionLifecycle(request,
                                            code='hea-update',
                                            description=f'Renaming {awsservicelib.s3_object_message_display_name(bucket_id, old_key)} to {project.display_name}',
                                            activity_cb=publish_desktop_object) as activity:
                metadata_dict = await awsservicelib.get_metadata(mongo_client, bucket_id, old_id)
                if metadata_dict and metadata_dict['actual_object_type_name'] != AWSS3Project.get_type_name():
                    return response.status_not_found()
                if 'path' in request.url.query:
                    target_path: list[str] | None = request.url.query.getall('path')
                else:
                    target_path = None
                resp = await rename(activity, request, mongo_client, sub, volume_id, bucket_id, old_id, old_key, project, AWSS3Project, target_path)
                if resp.status != 204:
                    activity.status = Status.FAILED
                return resp

    async_requested = PREFERENCE_RESPOND_ASYNC in request.headers.get(PREFER, [])
    if async_requested:
        sub = request.headers.get(SUB, NONE_USER)
        global _status_id
        path = f'{request.url.path}/updaterasyncstatus{_status_id}'
        status_location = request.url.with_path(path)  # Don't keep query params.
        _status_id += 1
        task_name = f'{sub}^{status_location}'
        await request.app[HEA_BACKGROUND_TASKS].add(coro, name=task_name)
        return response.status_see_other(status_location)
    else:
        return await coro(request.app)


@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3projects')
@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/')
@action('heaserver-awss3folders-project-get-open-choices', rel='hea-opener-choices hea-context-menu hea-downloader',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/opener')
@action(name='heaserver-awss3folders-project-get-properties', rel='hea-properties hea-context-menu')
@action(name='heaserver-awss3folders-project-duplicate', rel='hea-dynamic-standard hea-icon-duplicator hea-context-menu',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/duplicatorasync')
@action(name='heaserver-awss3folders-project-move', rel='hea-dynamic-standard hea-icon-mover hea-context-menu',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/moverasync')
@action(name='heaserver-awss3folders-project-get-create-choices', rel='hea-creator-choices hea-context-menu',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/creator')
@action(name='heaserver-awss3folders-project-archive', rel='hea-dynamic-standard hea-archive hea-context-menu',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/archiveasync')
@action(name='heaserver-awss3folders-project-unarchive', rel='hea-dynamic-standard hea-unarchive hea-context-menu',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/unarchive')
@action(name='heaserver-awss3folders-project-get-trash', rel='hea-trash hea-context-menu',
        path='volumes/{volume_id}/awss3trash')
@action(name='heaserver-awss3folders-project-get-presigned-url',
        rel='hea-dynamic-clipboard hea-icon-for-clipboard hea-context-menu',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/presignedurl')
@action(name='heaserver-awss3folders-project-get-self', rel='self hea-self-container',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}')
@action(name='heaserver-awss3folders-item-upload', rel='hea-uploader',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/uploader')
@action(name='heaserver-awss3folders-project-get-component', rel='hea-component',
        path='components/bytype/heaobject.project.AWSS3Project')
@action(name='heaserver-awss3folders-get-delete-preflight-url', rel='hea-delete-preflight',
        path='preflights/awss3objects/delete')
async def get_projects(request: web.Request) -> web.Response:
    """
    Gets all projects in a bucket.

    :param request: the HTTP request.
    :return: the requested projects or Not Found.
    ---
    summary: Gets all projects in a bucket.
    tags:
        - heaserver-awss3folders-projects
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
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    responses:
      '200':
        $ref: '#/components/responses/200'
      '404':
        $ref: '#/components/responses/404'
    """
    logger = logging.getLogger(__name__)
    sub = request.headers.get(SUB, NONE_USER)
    volume_id = request.match_info['volume_id']
    bucket_name = request.match_info['bucket_id']

    async with mongo.MongoContext(request) as mongo_client:
        async with DesktopObjectActionLifecycle(request=request,
                                                code='hea-get',
                                                description=f'Listing all projects in bucket {bucket_name}',
                                                activity_cb=publish_desktop_object) as activity:
            cache_key = (sub, volume_id, bucket_name, None, 'actual')
            if cached_value := request.app[HEA_CACHE].get(cache_key):
                data = cached_value[0]
                permissions: list[list[Permission]] = cached_value[1]
                attr_perms: list[dict[str, list[Permission]]] = cached_value[2]
                return await response.get_all(request, data, permissions=permissions,
                                              attribute_permissions=attr_perms)
            else:
                context = aws.S3ObjectPermissionContext(request)
                async with aws.S3ClientContext(request=request, volume_id=volume_id) as s3:
                    try:
                        loop = asyncio.get_running_loop()
                        logger.debug('Getting all projects from bucket %s', bucket_name)
                        folders: list[AWSS3Project] = []
                        async for obj in awsservicelib.list_objects(s3, bucket_name, loop=loop):
                            logger.debug('Checking possible project %s in bucket %s', obj, bucket_name)
                            key = obj['Key']
                            if awsservicelib.is_folder(key):
                                encoded_key = encode_key(key)
                                logger.debug('Project %s in bucket %s is a folder', key, bucket_name)
                                description = await get_description(sub, s3, bucket_name, key)
                                folder_ = _new_project(bucket_name, encoded_key, description=description)
                                folders.append(folder_)
                        folder_metadata = {}
                        get_all_admin_gen = mongo_client.get_all_admin(MONGODB_AWS_S3_FOLDER_METADATA_COLLECTION, {'bucket_id': bucket_name})
                        try:
                            async for metadata_dict in get_all_admin_gen:
                                folder_metadata[metadata_dict['encoded_key']] = metadata_dict
                        finally:
                            await get_all_admin_gen.aclose()
                        real_folder_dicts: list[DesktopObjectDict] = []
                        permissions = []
                        attr_perms = []
                        for folder_ in folders:
                            if (obj_metadata_ := folder_metadata.get(folder_.id)) is None or obj_metadata_['actual_object_type_name'] == AWSS3Project.get_type_name():
                                share = await folder_.get_permissions_as_share(context)
                                folder_.add_user_share(share)
                                permissions.append(share.permissions)
                                attr_perms.append(await folder_.get_all_attribute_permissions(context))
                                real_folder_dicts.append(to_dict(folder_))
                        activity.new_volume_id = volume_id
                        activity.new_object_type_name = AWSS3Project.get_type_name()
                        activity.new_object_uri = f'volumes/{volume_id}/buckets/{bucket_name}/awss3projects/'
                        request.app[HEA_CACHE][cache_key] = (real_folder_dicts, permissions, attr_perms)
                        for fd, perms_, attr_perms_ in zip(real_folder_dicts, permissions, attr_perms):
                            request.app[HEA_CACHE][(sub, volume_id, bucket_name, fd['id'], 'actual')] = fd, perms_, attr_perms_
                        return await response.get_all(request, real_folder_dicts, permissions=permissions,
                                                      attribute_permissions=attr_perms)
                    except BotoClientError as e:
                        activity.status = Status.FAILED
                        return awsservicelib.handle_client_error(e)
                    except ParamValidationError as e:
                        activity.status = Status.FAILED
                        return response.status_not_found()

@routes.route('OPTIONS', '/volumes/{volume_id}/buckets/{bucket_id}/awss3projects')
@routes.route('OPTIONS', '/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/')
async def get_projects_options(request: web.Request) -> web.Response:
    """
    Gets the allowed HTTP methods for the projects resource.

    :param request: the HTTP request (required).
    :response: the HTTP response.
    ---
    summary: Allowed HTTP methods.
    tags:
        - heaserver-awss3folders-projects
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
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
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
    return await response.get_options(request, ['GET', 'DELETE', 'HEAD', 'OPTIONS'])

@routes.delete('/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}')
async def delete_project(request: web.Request) -> web.Response:
    """
    Deletes the project with the specified id.

    :param request: the HTTP request.
    :return: No Content or Not Found.
    ---
    summary: Deletes the project with the specified id.
    tags:
        - heaserver-awss3folders-projects
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
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    responses:
      '204':
        $ref: '#/components/responses/204'
      '404':
        $ref: '#/components/responses/404'
    """
    sub = request.headers.get(SUB, NONE_USER)
    volume_id = request.match_info['volume_id']
    bucket_id = request.match_info['bucket_id']
    id_ = request.match_info['id']
    loop = asyncio.get_running_loop()
    try:
        key = awsservicelib.decode_folder(id_)
    except KeyDecodeException:
        return response.status_not_found()
    if key is None:
        return response.status_not_found()
    if not awsservicelib.is_folder(key) or not await _is_project(request, volume_id, bucket_id, id_):
        return response.status_not_found()
    async def publish_desktop_object_and_clear_cache(app: web.Application, desktop_object: DesktopObject,
                                 appproperty_=HEA_MESSAGE_BROKER_PUBLISHER):
        invalidate_cache(request.app[HEA_CACHE], sub, key, volume_id, bucket_id, invalidate_ancestors=True)
        await publish_desktop_object(app, desktop_object, appproperty_)
    return await delete_folder(request, volume_id, bucket_id, key, loop, publish_desktop_object_and_clear_cache)

@routes.post('/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/newfolder')
@routes.post('/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/newfolder/')
async def post_new_folder(request: web.Request) -> web.Response:
    """
    Creates a new folder within a project.

    :param request: the HTTP request. Required.
    :return: Status code 201 if successful, with the URL to the new folder in
    the Location header.
    ---
    summary: Creates a new folder within a project.
    tags:
        - heaserver-awss3folders-projects
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
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    requestBody:
        description: A new folder.
        required: true
        content:
            application/vnd.collection+json:
              schema:
                type: object
              examples:
                example:
                  summary: Folder example
                  value: {
                    "template": {
                      "data": [
                      {
                        "name": "display_name",
                        "value": "Bob"
                      },
                      {
                        "name": "type",
                        "value": "heaobject.folder.AWSS3Folder"
                      }]
                    }
                  }
            application/json:
              schema:
                type: object
              examples:
                example:
                  summary: Item example
                  value: {
                    "display_name": "Joe",
                    "type": "heaobject.folder.AWSS3Folder"
                  }
    responses:
      '201':
        $ref: '#/components/responses/201'
      '400':
        $ref: '#/components/responses/400'
      '404':
        $ref: '#/components/responses/404'
    """
    logger = logging.getLogger(__name__)

    try:
        folder = await new_heaobject_from_type(request, AWSS3Folder)
    except DeserializeException as e:
        return response.status_bad_request(f'Invalid new folder: {str(e)}')
    if folder is None:
        return response.status_bad_request('The request body must contain a folder')
    if folder.display_name is None:
        return response.status_bad_request("display_name is required")
    if '/' in folder.display_name:
        return response.status_bad_request("The folder's display name may not have slashes in it")
    volume_id = request.match_info['volume_id']
    bucket_id = request.match_info['bucket_id']
    id_ = request.match_info['id']

    if id_ == awsservicelib.ROOT_FOLDER.id:
        item_folder_id: str | None = ''
    else:
        try:
            item_folder_id = awsservicelib.decode_folder(id_)
            if not awsservicelib.is_folder(item_folder_id) or not await _is_project(request, volume_id, bucket_id, id_):
                item_folder_id = None
        except KeyDecodeException:
            item_folder_id = None
    item_name = join(item_folder_id, folder.display_name)

    async with DesktopObjectActionLifecycle(request=request,
                                            code='hea-create',
                                            description=f'Creating {awsservicelib.s3_object_message_display_name(bucket_id, folder.key)}',
                                            activity_cb=publish_desktop_object) as activity:
        async with aws.S3ClientContext(request=request, volume_id=volume_id) as s3_client:
            loop = asyncio.get_running_loop()
            try:
                if item_folder_id is None:
                    await loop.run_in_executor(None, partial(s3_client.head_bucket, Bucket=bucket_id))
                    raise response.status_not_found()
                if folder.type == AWSS3Folder.get_type_name():
                    item_name += '/'
                else:
                    raise response.status_bad_request(f'Unsupported type {folder.get_type_name()}')
                response_ = await loop.run_in_executor(None, partial(s3_client.head_object, Bucket=bucket_id,
                                                                    Key=item_name))  # check if folder exists, if not throws an exception
                logger.debug('Result of post_object: %s', response_)
                raise response.status_bad_request(body=f"{awsservicelib.s3_object_message_display_name(bucket_id, item_name)} already exists")
            except BotoClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == aws.CLIENT_ERROR_404:  # folder doesn't exist
                    try:
                        await loop.run_in_executor(None, partial(s3_client.put_object, Bucket=bucket_id, Key=item_name))
                        logger.debug('Added project %s', item_name)
                        sub = request.headers.get(SUB, NONE_USER)
                        # Remove any stale metadata for the folder.
                        async with mongo.MongoContext(request) as mongo_client:
                            await mongo_client.delete_admin(MONGODB_AWS_S3_FOLDER_METADATA_COLLECTION,
                                                            mongoattributes={'bucket_id': bucket_id, 'encoded_key': encode_key(item_name)})
                        request.app[HEA_CACHE].pop((sub, volume_id, bucket_id, None, 'actual'), None)
                        if not (folder_id := encode_key(parent(item_name))):
                            folder_id = 'root'
                        request.app[HEA_CACHE].pop((sub, volume_id, bucket_id, folder_id, None, 'items'), None)
                        activity.new_volume_id = volume_id
                        activity.new_object_type_name = AWSS3Project.get_type_name()
                        activity.new_object_id = encode_key(item_name)
                        activity.new_object_uri = f'volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{activity.new_object_id}'
                        activity.new_object_display_name = folder.display_name
                        if 'path' in request.url.query:
                            activity.new_context_dependent_object_path = request.url.query.getall('path')
                        return await response.post(request, activity.new_object_id,
                                                f"volumes/{volume_id}/buckets/{bucket_id}/awss3projects")
                    except BotoClientError as e2:
                        raise awsservicelib.handle_client_error(e2)
                elif error_code == aws.CLIENT_ERROR_NO_SUCH_BUCKET:
                    raise response.status_not_found()
                else:
                    raise response.status_bad_request(str(e))

@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/uploader')
@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/uploader/')
@action('heaserver-awss3folders-project-upload-form')
@action(name='heaserver-awss3folders-project-get-self', rel='self hea-self-container',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}')
async def get_project_uploader_form(request: web.Request) -> web.Response:
    """
    Gets a form template for uploading a file to a project

    :param request: the HTTP request. Required.
    :return: a blank form for uploading a file to a project or Not Found if the r
    equested project does not exist.
    """
    context = aws.S3ObjectPermissionContext(request)
    return await _get_project(request, context)

@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/newfolder')
@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/newfolder/')
@action('heaserver-awss3folders-folder-new-form')
@action(name='heaserver-awss3folders-project-get-self', rel='self hea-self-container',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}')
async def get_new_folder_form(request: web.Request) -> web.Response:
    """
    Gets form template for creating a new folder within a project.

    :param request: the HTTP request. Required.
    :return: a template for creating a folder or Not Found if the requested project does not exist.
    ---
    summary: A form template for creating a new folder within a projecct.
    tags:
        - heaserver-awss3folders-projects
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
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    responses:
      '200':
        $ref: '#/components/responses/200'
      '404':
        $ref: '#/components/responses/404'
    """
    return await _get_project(request)

@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/creator')
@action('heaserver-awss3folders-project-create-folder', rel='hea-creator hea-default application/x.folder',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/newfolder')
async def get_project_creator(request: web.Request) -> web.Response:
    """
    Opens the requested folder.

    :param request: the HTTP request. Required.
    :return: Opener choices, or Not Found if the requested project does not exist.
    ---
    summary: Project creator choices
    tags:
        - heaserver-awss3folders-projects
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
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    responses:
      '300':
        $ref: '#/components/responses/300'
      '404':
        $ref: '#/components/responses/404'
    """
    volume_id = request.match_info['volume_id']
    bucket_name = request.match_info['bucket_id']
    folder_name = request.match_info['id']
    try:
        folder_key = awsservicelib.decode_folder(folder_name)
    except KeyDecodeException as e:
        return response.status_not_found()

    async with DesktopObjectActionLifecycle(request=request,
                                            code='hea-get',
                                            description=f'Accessing {awsservicelib.s3_object_message_display_name(bucket_name, folder_key)}',
                                            activity_cb=publish_desktop_object) as activity:
        async with aws.S3ClientContext(request=request, volume_id=volume_id) as s3_client:
            try:
                folder, is_project = await asyncio.gather(_get_project_helper(s3_client, request),
                                                          _is_project(request, volume_id, bucket_name, folder_name))
                if not folder or not is_project:
                    return response.status_not_found()
                activity.new_object_id = folder_name
                activity.new_object_type_name = AWSS3Project.get_type_name()
                activity.new_volume_id = volume_id
                activity.new_object_uri = f'volumes/{volume_id}/buckets/{bucket_name}/awss3projects/{folder_name}'
                activity.new_object_display_name = folder.display_name
                activity.new_object_description = folder.description
                if 'path' in request.url.query:
                    activity.new_context_dependent_object_path = request.url.query.getall('path')
                return await response.get_multiple_choices(request)
            except BotoClientError as e:
                activity.status = Status.FAILED
                return awsservicelib.handle_client_error(e)
            except web.HTTPClientError as e:
                activity.status = Status.FAILED
                return e

@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/opener')
@action('heaserver-awss3folders-project-open-default', rel='hea-opener hea-default application/x.project',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/items/')
@action(name='heaserver-awss3folders-project-open-as-zip', rel='hea-opener hea-downloader hea-default-downloader application/zip',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/content')
async def get_project_opener(request: web.Request) -> web.Response:
    """
    Opens the requested project.

    :param request: the HTTP request. Required.
    :return: Opener choices, or Not Found if the requested project does not exist.
    ---
    summary: Project opener choices
    tags:
        - heaserver-awss3folders-projects
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
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    responses:
      '300':
        $ref: '#/components/responses/300'
      '404':
        $ref: '#/components/responses/404'
    """
    logger = logging.getLogger(__name__)
    sub = request.headers.get(SUB, NONE_USER)
    volume_id = request.match_info['volume_id']
    bucket_name = request.match_info['bucket_id']
    folder_name = request.match_info['id']
    try:
        folder_key = awsservicelib.decode_folder(folder_name)
    except KeyDecodeException as e:
        return response.status_not_found()
    assert folder_key is not None, 'folder_key cannot be None'

    async with DesktopObjectActionLifecycle(request=request,
                                            code='hea-get',
                                            description=f'Accessing {awsservicelib.s3_object_message_display_name(bucket_name, folder_key)}',
                                            activity_cb=publish_desktop_object) as activity:
        cache_key = (sub, volume_id, bucket_name, folder_name, 'actual')
        cached_value = request.app[HEA_CACHE].get(cache_key)
        if cached_value:
            logger.debug('Getting cached value for %s: %s', cache_key, cached_value)
            async with aws.S3ClientContext(request=request, volume_id=volume_id) as s3_client:
                activity.new_object_id = folder_name
                activity.new_object_type_name = AWSS3Project.get_type_name()
                activity.new_volume_id = volume_id
                activity.new_object_uri = f'volumes/{volume_id}/buckets/{bucket_name}/awss3projects/{folder_name}'
                activity.new_object_display_name = display_name(folder_key)
                activity.new_object_description = await get_description(sub, s3_client, bucket_name, folder_key)
                if 'path' in request.url.query:
                    activity.new_context_dependent_object_path = request.url.query.getall('path')
            return await response.get_multiple_choices(request)
        else:
            async with aws.S3ClientContext(request=request, volume_id=volume_id) as s3_client:
                try:
                    folder, is_folder = await asyncio.gather(_has_project_helper(s3_client, request),
                                                            _is_project(request, volume_id, bucket_name, folder_name))
                    if not folder or not is_folder:
                        return response.status_not_found()
                    activity.new_object_id = folder_name
                    activity.new_object_type_name = AWSS3Project.get_type_name()
                    activity.new_volume_id = volume_id
                    activity.new_object_uri = f'volumes/{volume_id}/buckets/{bucket_name}/awss3projects/{folder_name}'
                    activity.new_object_display_name = display_name(folder_key)
                    activity.new_object_description = await get_description(sub, s3_client, bucket_name, folder_key)
                    if 'path' in request.url.query:
                        activity.new_context_dependent_object_path = request.url.query.getall('path')
                    return await response.get_multiple_choices(request)
                except BotoClientError as e:
                    activity.status = Status.FAILED
                    return awsservicelib.handle_client_error(e)
                except web.HTTPClientError as e:
                    activity.status = Status.FAILED
                    return e


@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/archiveasyncstatus')
@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/duplicatorasyncstatus{status_id}')
@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/moverasyncstatus')
@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/deleterasyncstatus')
@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/updaterasyncstatus{status_id}')
async def get_project_async_status(request: web.Request) -> web.Response:
    return response.get_async_status(request)

@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{folder_id}/items/{id}/deleterasyncstatus')
@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{folder_id}/itemsasyncstatus{status_id}')
async def get_item_async_status(request: web.Request) -> web.Response:
    return response.get_async_status(request)


async def _get_project_move_template(request: web.Request) -> web.Response:
    logger = logging.getLogger(__name__)
    context = aws.S3ObjectPermissionContext(request)
    try:
        return await _get_project(request, context)
    except KeyDecodeException as e:
        logger.exception('Error getting parent key')
        return response.status_not_found()

async def _get_project(request: web.Request, context: PermissionContext | None = None) -> web.Response:
    """
    Gets the project with the specified id.

    :param request: the HTTP request.
    :return: the requested project or Not Found.
    """
    sub = request.headers.get(SUB, NONE_USER)
    try:
        volume_id = request.match_info['volume_id']
        bucket_name = request.match_info['bucket_id']
        project_id = request.match_info['id'] if 'id' in request.match_info else request.match_info['name']
    except KeyError as e:
        raise ValueError(str(e))
    try:
        project_key: str | None = decode_key(project_id)
    except KeyDecodeException as e:
        project_key = None

    async with DesktopObjectActionLifecycle(request=request,
                                            code='hea-get',
                                            description=f'Accessing {awsservicelib.s3_object_message_display_name(bucket_name, project_key or 'an object')}',
                                            activity_cb=publish_desktop_object) as activity:
        if project_key is None:
            async with aws.S3ClientContext(request=request, volume_id=volume_id) as s3_client:
                raise await when_object_not_found(s3_client, bucket_name)
        include_data = parse_bool(request.url.query.get('data') or 'true')
        if 'path' in request.query:
            path: list[str] | None = request.query.getall('path')
        else:
            path = None
        cache_key = (sub, volume_id, bucket_name, project_id, 'actual')
        if context and (cached_value := request.app[HEA_CACHE].get(cache_key)):
            data, perms, attr_perms = cached_value
            activity.new_object_id = project_id
            activity.new_object_type_name = AWSS3Project.get_type_name()
            activity.new_volume_id = volume_id
            activity.new_object_uri = f'volumes/{volume_id}/buckets/{bucket_name}/awss3projects/{project_id}'
            activity.new_object_display_name = display_name(project_key)
            async with aws.S3ClientContext(request=request, volume_id=volume_id) as s3_client:
                activity.new_object_description = await get_description(sub, s3_client, bucket_name, project_key)
            if path is not None:
                activity.new_context_dependent_object_path = path
            return await response.get(request, data, permissions=perms, attribute_permissions=attr_perms,
                                      include_data=include_data)
        else:
            if include_data:
                async with aws.S3ClientContext(request=request, volume_id=volume_id) as s3_client:
                    try:
                        is_project, project = await asyncio.gather(_is_project(request, volume_id, bucket_name, project_id),
                                                                    _get_project_helper(s3_client, request))
                        if not is_project or not project:
                            activity.status = Status.FAILED
                            return await response.get(request, None)
                        activity.new_object_id = project_id
                        activity.new_object_type_name = AWSS3Project.get_type_name()
                        activity.new_volume_id = volume_id
                        activity.new_object_uri = f'volumes/{volume_id}/buckets/{bucket_name}/awss3projects/{project_id}'
                        activity.new_object_display_name = project.display_name
                        activity.new_object_description = project.description
                        if path is not None:
                            activity.new_context_dependent_object_path = path
                        if context:
                            share = await project.get_permissions_as_share(context)
                            project.add_user_share(share)
                            attr_perms = await project.get_all_attribute_permissions(context)
                            perms = share.permissions
                        else:
                            perms = attr_perms = None
                        project_dict = to_dict(project)
                        if context:
                            request.app[HEA_CACHE][cache_key] = (project_dict, perms, attr_perms)
                        return await response.get(request, project_dict, permissions=perms,
                                                  attribute_permissions=attr_perms, include_data=True)
                    except BotoClientError as e:
                        raise awsservicelib.handle_client_error(e)
            else:
                if await _is_project(request, volume_id, bucket_name, project_id):
                    project_dict_: DesktopObjectDict | None = {'id': project_id, 'type': AWSS3Folder.get_type_name()}
                else:
                    project_dict_ = None
                return await response.get(request, project_dict_, include_data=False)

async def _get_project_helper(s3_client: S3Client, request: web.Request) -> AWSS3Project:
    try:
        bucket_name = request.match_info['bucket_id']
        project_id = request.match_info['id'] if 'id' in request.match_info else request.match_info['name']
    except KeyError as e:
        raise ValueError(str(e))
    sub = request.headers.get(SUB, NONE_USER)
    try:
        project_key: str | None = awsservicelib.decode_folder(project_id)
        if not awsservicelib.is_folder(project_key):
            project_key = None
    except KeyDecodeException:
        # Let the bucket query happen so that we consistently return Forbidden if the user lacks permissions
        # for the bucket.
        project_key = None
    loop = asyncio.get_running_loop()
    def get_object() -> ListObjectsV2OutputTypeDef:
        if project_key is None:
            # We couldn't decode the folder_id, and we need to check if the user can access the bucket in order to
            # decide which HTTP status code to respond with (Forbidden vs Not Found).
            s3_client.head_bucket(Bucket=bucket_name)
            raise web.HTTPNotFound
        return s3_client.list_objects_v2(Bucket=bucket_name, Prefix=project_key, MaxKeys=1, Delimiter='/')
    response_, description = await asyncio.gather(
        loop.run_in_executor(None, get_object),
        get_description(sub, s3_client, bucket_name, project_key, ignore_cache=True)
    )
    logging.debug('Result of getting project: %s', response_)

    if response_['KeyCount'] == 0 and len(response_.get('CommonPrefixes', [])) == 0:
        raise web.HTTPNotFound
    encoded_key = encode_key(response_['Prefix'])
    return _new_project(bucket_name, encoded_key, description=description)

async def _has_project_helper(s3_client: S3Client, request: web.Request) -> bool:
    try:
        bucket_name = request.match_info['bucket_id']
        project_id = request.match_info['id'] if 'id' in request.match_info else request.match_info['name']
    except KeyError as e:
        raise ValueError(str(e))

    try:
        project_key: str | None = awsservicelib.decode_folder(project_id)
        if not awsservicelib.is_folder(project_key):
            project_key = None
    except KeyDecodeException:
        # Let the bucket query happen so that we consistently return Forbidden if the user lacks permissions
        # for the bucket.
        project_key = None
    loop = asyncio.get_running_loop()
    def get_object() -> ListObjectsV2OutputTypeDef:
        if project_key is None:
            # We couldn't decode the folder_id, and we need to check if the user can access the bucket in order to
            # decide which HTTP status code to respond with (Forbidden vs Not Found).
            s3_client.head_bucket(Bucket=bucket_name)
            raise response.status_not_found()
        return s3_client.list_objects_v2(Bucket=bucket_name, Prefix=project_key, MaxKeys=1, Delimiter='/')
    response_ = await loop.run_in_executor(None, get_object)
    logging.debug('Result of getting project: %s', response_)

    if response_['KeyCount'] == 0 and len(response_.get('CommonPrefixes', [])) == 0:
        return False
    return True


async def _is_project(request: web.Request, volume_id: str, bucket_id: str, encoded_key: str):
    async with mongo.MongoContext(request=request) as mongo_client:
        metadata_dict = await awsservicelib.get_metadata(mongo_client, bucket_id, encoded_key)
        if not metadata_dict or \
            not is_desktop_object_type(metadata_dict['actual_object_type_name'], type_=AWSS3Project):
            return False
    return True

def _new_project(bucket_name: str, encoded_key: str, description: str | None = None) -> AWSS3Project:
    project = AWSS3Project()
    project.id = encoded_key
    project.owner = AWS_USER
    project.bucket_id = bucket_name
    project.source = AWS_S3
    project.source_detail = AWS_S3
    project.description = description
    return project


def _check_folder_and_object_keys(folder_id_: str | None, request: web.Request) -> tuple[str | None, str | None, bool]:
    """
    Decodes a folder id and the request object's id, and returns the folder key, the object key, and whether the
    requested object is in the folder. If either the id or the folder id is invalid, it will be returned as None, and
    the third element of the tuple will be False.

    :param folder_id_: the folder id.
    :param request: the request.
    :return a three-tuple containing the folder key, the requested object key, and whether the requested object is in
    the folder.
    """
    folder_or_item_not_found = False
    try:
        decoded_folder_key: str | None = decode_key(folder_id_) if folder_id_ is not None else ''
    except KeyDecodeException:
        folder_or_item_not_found = True
        decoded_folder_key = None
    try:
        decoded_key: str | None = decode_key(request.match_info['id'])
        if not is_object_in_folder(decoded_key, decoded_folder_key):
            folder_or_item_not_found = True
    except KeyDecodeException as e:
        decoded_key = None
        folder_or_item_not_found = True

    return decoded_folder_key, decoded_key, folder_or_item_not_found
