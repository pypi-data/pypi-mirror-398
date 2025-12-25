"""
Manages folders stored in Amazon Simple Storage Service (S3) buckets.

Technically, folders do not exist in S3. Instead, S3 objects have a key with forward slashes that acts like a path.
Calls to get a folder will return a folder object if there exists at least one S3 object with that folder in its
key/path. Creating a folder will create a content-less S3 object, just so the other folder APIs work.
"""
from asyncio import Lock
from datetime import datetime
from json import JSONDecodeError
from heaobject.activity import Status
from heaobject import awss3key
from heaobject.keychain import AWSCredentials
from heaobject.registry import Property
from heaserver.service.db.aws import S3ClientContext
from mypy_boto3_s3 import S3Client
from mypy_boto3_s3.type_defs import DeleteTypeDef, ListObjectsV2OutputTypeDef, ObjectIdentifierTypeDef, \
    GetBucketVersioningOutputTypeDef
from heaserver.service.runner import init_cmd_line, routes, start
from heaserver.service.db import aws, mongo, opensearch, opensearchlib
from heaserver.service.db.awsservicelib import http_error_message
from heaserver.service.wstl import builder_factory, action, RuntimeWeSTLDocumentBuilder
from heaserver.service import response, appproperty, client
from heaserver.service.heaobjectsupport import new_heaobject_from_type
from heaserver.service.messagebroker import publisher_cleanup_context_factory, subscriber_cleanup_context_factory, publish_desktop_object
from heaserver.service.db.opensearchlib import search_dict, get
from heaserver.service.oidcclaimhdrs import SUB
from heaserver.service.appproperty import HEA_BACKGROUND_TASKS, HEA_CACHE, HEA_MESSAGE_BROKER_PUBLISHER, HEA_DB
from heaserver.service.requestproperty import HEA_WSTL_BUILDER
from heaserver.service.sources import AWS_S3
from heaserver.service.activity import DesktopObjectActionLifecycle
from heaserver.service.util import queued_processing, LockManager
from heaserver.service.uritemplate import tvars
from heaserver.service.backgroundtasks import BackgroundTasks
from heaobject.awss3key import KeyDecodeException, decode_key, encode_key, join, is_object_in_folder
from heaobject.bucket import AWSBucket
from heaobject.folder import AWSS3ItemInFolder, AWSS3Folder, AWSS3SearchItemInFolder, AWSS3Item
from heaobject.project import AWSS3Project
from heaobject.data import AWSS3FileObject, ClipboardData, get_type_display_name
from heaobject.attribute import SimpleAttribute, ListAttribute
from heaobject.user import NONE_USER, AWS_USER, CREDENTIALS_MANAGER_USER
from heaobject.aws import S3StorageClass
from heaobject.awss3key import parent, split, display_name
from heaobject.error import DeserializeException
from heaobject.root import ViewerPermissionContext, DesktopObjectDict, DesktopObject, Permission, PermissionContext, \
    AbstractDesktopObject, AbstractMemberObject, json_dumps, to_dict
from heaobject.activity import Activity
from heaobject.mimetype import guess_mime_type
from heaobject.util import parse_bool, now
from aiohttp import web, ClientResponseError
from typing import Any, cast
from aiohttp import hdrs
from botocore.exceptions import ParamValidationError, ClientError as BotoClientError
from yarl import URL
from functools import partial
import logging
import asyncio
from collections.abc import Mapping, AsyncIterator
from collections import defaultdict
from heaserver.folderawss3 import awsservicelib
from heaserver.folderawss3.awsservicelib import fail_if_too_big
from heaserver.folderawss3.util import extract_expiration, delete_folder as util_delete_folder, get_result_or_see_other, MONGODB_AWS_S3_FOLDER_METADATA_COLLECTION
from .util import response_folder_as_zip, rename, client_line_ending, set_s3_storage_status, move, copy, get_description, \
    create_presigned_url_credentials, when_object_not_found, path_iter, invalidate_cache
from heaserver.service.customhdrs import PREFER, PREFERENCE_RESPOND_ASYNC
from . import projectservice, fileservice, trashservice, storageservice  # Needed for all REST APIs to work.
from itertools import chain
from . import awsservicelib
from heaserver.service.config import Configuration

_status_id = 0

_message_broker_failed = False
_put_lock = Lock()


@routes.get('/ping')
async def ping(request: web.Request) -> web.Response:
    """
    For testing whether the service is up.

    :param request: the HTTP request.
    :return: Always returns status code 200.
    """
    if _message_broker_failed:
        return response.status_internal_error('Message broker connection lost')
    else:
        return response.status_ok()


class PreflightFormData(AbstractDesktopObject):
    def __init__(self) -> None:
        super().__init__()


@routes.get('/preflights/awss3objects/delete')
@action(name='heaserver-awss3folders-delete-get-preflight-form')
async def get_delete_preflight_form(request: web.Request) -> web.Response:
    """
    Preflight check for DELETE requests to folders.

    :param request: the HTTP request.
    :return: Always returns status code 200 and a form template.
    """
    p: PreflightFormData = PreflightFormData()
    context = ViewerPermissionContext(request.headers.get(SUB, NONE_USER))
    p.owner = NONE_USER
    p.add_share(await context.get_permissions_as_share(p))
    p.display_name = 'S3 objects preflight object'
    return await response.get(request, to_dict(p),
                              permissions=await p.get_permissions(context),
                              attribute_permissions=await p.get_all_attribute_permissions(context))


class PreflightObjectListItem(AbstractMemberObject):
    display_name = SimpleAttribute(str, 'Untitled')
    bucket_id = SimpleAttribute(str, None)

    def __init__(self) -> None:
        super().__init__()


class PreflightConfirmationData(AbstractDesktopObject):
    """
    Data for the preflight confirmation form.
    """
    warning_message = SimpleAttribute(str, None)
    objects_to_delete = ListAttribute[PreflightObjectListItem]()
    delete_confirmation = SimpleAttribute(str, None)

    def __init__(self) -> None:
        super().__init__()


@routes.post('/preflights/awss3objects/delete')
async def post_delete_preflight(request: web.Request) -> web.Response:
    """
    Preflight check for DELETE requests to folders. A template is expected in the request body with a
    desktop_object_urls property containing a list of URLs for the objects to delete. If the template does not contain
    a confirmed property, the response will be a form that asks the user to confirm the deletion. The form may be
    submitted to this endpoint again with the confirmed property set to True or False. If set to True, preflight
    checking is performed, and if deletion is approved, a 204 status code is returned to indicate that the deletion may
    proceed. If confirmed is set to False, or preflight checking fails, an error status code is returned.

    :param request: the HTTP request.
    :return: Always returns status code 204.
    """
    logger = logging.getLogger(__name__)
    json = await request.json()
    if not (json_template := json.get('template')):
        raise response.status_bad_request('Invalid request: missing template.')
    if not (json_template_data := json_template.get('data')):
        raise response.status_bad_request('Invalid request: missing data in template.')
    if not (desktop_object_urls := next((data_.get('value') for data_ in json_template_data if data_.get('name') == 'desktop_object_urls'), None)):
        raise response.status_bad_request('Invalid request: empty desktop_object_urls.')
    confirmed = next((data_.get('value') for data_ in json_template_data if data_.get('name') == 'confirmed'), None)
    if confirmed is None:
        wstl_doc = cast(RuntimeWeSTLDocumentBuilder, request[HEA_WSTL_BUILDER])
        url_template = 'http{prefix}/volumes/{volume_id}/buckets/{bucket_id}/{objtype}/{id}'
        bucket_names = set[str]()
        tvars_l = list[dict[str, Any]]()
        for url in desktop_object_urls:
            tvars_l.append(tvars(url_template, str(URL(url).with_query({}).with_fragment(None))))
        def extract_volume_and_bucket_info() -> dict[str, set[str]]:
            volume_id_to_bucket_names: dict[str, set[str]] = defaultdict(set)
            for i, url in enumerate(desktop_object_urls):
                tvars_ = tvars_l[i]
                logger.debug('Extracting volume and bucket info from URL %s: %s', url, tvars_)
                if 'volume_id' not in tvars_:
                    raise response.status_bad_request(f'Invalid URL: {url} does not contain a volume_id.')
                if 'bucket_id' not in tvars_:
                    raise response.status_bad_request(f'Invalid URL: {url} does not contain a bucket_id.')
                if bucket_name := str(tvars_.get('bucket_id', None)):
                    if volume_id := str(tvars_.get('volume_id', None)):
                        if bucket_name not in bucket_names:
                            bucket_names.add(bucket_name)
                            volume_id_to_bucket_names[volume_id].add(bucket_name)
            return volume_id_to_bucket_names
        async def count_versioned_and_unversioned_buckets() -> tuple[int, int]:
            count_versioned_buckets = count_unversioned_buckets = 0
            for volume_id, bucket_names_ in extract_volume_and_bucket_info().items():
                async with S3ClientContext(request=request, volume_id=volume_id) as s3:
                    async def itr() -> AsyncIterator[GetBucketVersioningOutputTypeDef]:
                        try:
                            for bucket_name in bucket_names_:
                                yield await asyncio.to_thread(s3.get_bucket_versioning, Bucket=bucket_name)
                        except BotoClientError as e:
                            raise response.status_bad_request(f'Error getting bucket versioning status: {e}') from e
                    async def item_processor(bucket_version_metadata: GetBucketVersioningOutputTypeDef) -> None:
                        nonlocal count_versioned_buckets, count_unversioned_buckets
                        if bucket_version_metadata.get('Status') == 'Enabled':
                            count_versioned_buckets += 1
                        else:
                            count_unversioned_buckets += 1
                    await queued_processing(itr(), item_processor)
            return count_versioned_buckets, count_unversioned_buckets
        count_versioned_buckets, count_unversioned_buckets = await count_versioned_and_unversioned_buckets()
        p: PreflightConfirmationData = PreflightConfirmationData()
        objects_to_delete: list[PreflightObjectListItem] = []
        for i, url in enumerate(desktop_object_urls):
            tvars_ = tvars_l[i]
            preflight_obj: PreflightObjectListItem = PreflightObjectListItem()
            preflight_obj.display_name = display_name(decode_key(str(tvars_['id'])))
            preflight_obj.bucket_id = str(tvars_['bucket_id'])
            objects_to_delete.append(preflight_obj)
        p.objects_to_delete = objects_to_delete
        if len(objects_to_delete) == 1:
            object_summary = f'{objects_to_delete[0].display_name} in bucket {objects_to_delete[0].bucket_id}'
        elif len(objects_to_delete) == 2:
            object_summary = f'{objects_to_delete[0].display_name} in bucket {objects_to_delete[0].bucket_id} and ' \
                f'{objects_to_delete[1].display_name} in bucket {objects_to_delete[1].bucket_id}'
        else:
            more_objects = len(objects_to_delete) - 2
            object_summary = f'{objects_to_delete[0].display_name} in bucket {objects_to_delete[0].bucket_id}, ' \
                f'{objects_to_delete[1].display_name} in bucket {objects_to_delete[1].bucket_id}, and ' \
                f'{more_objects} more object{"s" if more_objects > 1 else ""}'
        if count_versioned_buckets and count_unversioned_buckets:
            msg_value = f'You have requested deletion of {object_summary}.' \
                'Objects in unversioned buckets will be deleted permanently and cannot be recovered. Objects ' \
                'in versioned buckets will be marked for deletion and and permanently removed after 7 days. ' \
                'They can be recovered from the Trash.'
        elif count_versioned_buckets:
            msg_value = f'{object_summary} will be marked for deletion and permanently removed after 7 days. ' \
                f'You may restore {"them" if count_versioned_buckets > 1 else "it"} from the Trash during this grace period.'
        elif count_unversioned_buckets:
            msg_value = f'{object_summary} will be deleted permanently and cannot be recovered.'
        p.warning_message = msg_value
        wstl_doc.add_design_time_action({
            'name': 'heaserver-awss3folders-delete-preflight-confirmation',
            'description': 'Preflight check for AWS S3 object delete requests.',
            'type': 'safe',
            'action': 'read',
            'target': 'item cj-template',
            'prompt': 'S3 object delete confirmation',
            'inputs': [{
                            "name": "warning_message",
                            "hea": {
                                "type": "text-display"
                            }
                        },
                        {
                            "name": "desktop_object_urls",
                            "value": json_dumps(desktop_object_urls),
                            "readOnly": True,
                            "required": True,
                            "hea": {
                                "display": False
                            }
                        },
                        {
                            "name": "confirmed",
                            "value": "true",
                            "readOnly": True,
                            "required": True,
                            "hea": {
                                "display": False
                            }
                        },
                        {
                            "name": "delete_confirmation",
                            "prompt": "Type 'delete' to confirm",
                            "required": True,
                            "pattern": "delete"
                        }],
        })
        wstl_doc.add_run_time_action(name='heaserver-awss3folders-delete-preflight-confirmation',
                                    rel='hea-message-warning')


        return await response.get(request, to_dict(p))
    elif parse_bool(confirmed):
        return response.status_no_content()
    else:
        return response.status_bad_request('Deletion request was rejected')


@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{folder_id}/items')
@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{folder_id}/items/')
@action(name='heaserver-awss3folders-item-get-actual-container', rel='hea-actual hea-actual-container',
        path='{+actual_object_uri}',
        itemif="actual_object_type_name == AWSS3Project.get_type_name() or actual_object_type_name == AWSS3Folder.get_type_name()")
@action(name='heaserver-awss3folders-item-get-actual-not-container', rel='hea-actual',
        path='{+actual_object_uri}',
        itemif="actual_object_type_name != AWSS3Project.get_type_name() and actual_object_type_name != AWSS3Folder.get_type_name()")
async def get_items(request: web.Request) -> web.Response:
    """
    Gets the items of the folder with the specified id.
    :param request: the HTTP request.
    :return: the requested items, or Not Found if the folder was not found.
    ---
    summary: All items in a folder.
    tags:
        - heaserver-awss3folders-folder-items
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
        $ref: '#/components/responses/200'
      '403':
        $ref: '#/components/responses/403'
    """
    volume_id = request.match_info['volume_id']
    bucket_name = request.match_info['bucket_id']
    folder_id_ = request.match_info['folder_id']

    try:
        folder_key = awsservicelib.decode_folder(folder_id_)
    except KeyDecodeException:
        return response.status_not_found()

    if not awsservicelib.is_folder(folder_key) or not await _is_folder(request, volume_id, bucket_name, folder_id_):
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
            logger.debug('Getting all items in folder %s in bucket %s', folder_key, bucket_name)
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
                        folder_type_name = AWSS3Folder.get_type_name()
                        project_type_name = AWSS3Project.get_type_name()
                        item: AWSS3ItemInFolder = AWSS3ItemInFolder()

                        async def get_metadata(bid, fid) -> dict[str, DesktopObjectDict]:
                            logger.debug('Getting metadata for bucket %s and folder %s', bid, fid)
                            metadata: dict[str, DesktopObjectDict] = {}
                            gen_ = mongo_client.get_all_admin(MONGODB_AWS_S3_FOLDER_METADATA_COLLECTION,
                                                              {'bucket_id': bid,
                                                               'parent_encoded_key': fid,
                                                               '$or': [{'deleted': False}, {'deleted': {'$exists': False}}]})
                            try:
                                async for item_ in gen_:
                                    key_ = item_['encoded_key']
                                    assert key_ is not None, 'encoded_key is missing in metadata'
                                    metadata[str(key_)] = item_
                                return metadata
                            finally:
                                await gen_.aclose()

                        metadata_task = asyncio.create_task(get_metadata(bucket_name, folder_id_))
                        context = ViewerPermissionContext(sub)
                        permissions = []
                        attribute_permissions = []
                        async with aws.S3ClientContext(request=request, volume_id=volume_id) as s3:
                            async for obj in awsservicelib.list_objects(s3, bucket_id=bucket_name, prefix=folder_key,
                                                                        loop=loop, delimiter='/',
                                                                        include_restore_status=True):
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
                                else:
                                    item.modified = None
                                    item.created = None
                                item.owner = owner
                                item.actual_object_id = actual_id
                                item.folder_id = folder_id_
                                item.bucket_id = bucket_name
                                item.volume_id = volume_id
                                share = await item.get_permissions_as_share(context)
                                item.add_user_share(share)
                                permissions.append(share.permissions)
                                attribute_permissions.append(await item.get_all_attribute_permissions(context))
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
                                    if aotn is None or aotn == folder_type_name:
                                        item.actual_object_uri = str(
                                            folders_actual_object_uri_base / item.actual_object_id)
                                        item.actual_object_type_name = folder_type_name
                                        item.type_display_name = 'Folder'
                                    elif aotn == project_type_name:
                                        item.actual_object_type_name = project_type_name
                                        item.actual_object_uri = str(
                                            projects_actual_object_uri_base / item.actual_object_id)
                                        item.type_display_name = 'Project'
                                    else:
                                        item.actual_object_type_name = None
                                        item.actual_object_uri = None
                                        item.type_display_name = None  # type:ignore[assignment]
                                    item.size = None
                                    item.storage_class = None
                                    item.source = AWS_S3
                                    item.source_detail = AWS_S3
                                folders.append(to_dict(item))
                        await metadata_task
                        activity.new_object_uri = f'volumes/{volume_id}/buckets/{bucket_name}/awss3folders/{folder_id_}'
                        activity.new_object_type_name = folder_type_name
                        activity.new_volume_id = volume_id
                        activity.new_object_id = folder_id_
                        activity.new_object_display_name = split(folder_key)[1].removesuffix('/')
                        if 'path' in request.url.query:
                            activity.new_context_dependent_object_path = request.url.query.getall('path')
                        request.app[HEA_CACHE][cache_key] = (folders, permissions, attribute_permissions)
                        for folder_item_dict, perms, attr_perms in zip(folders, permissions, attribute_permissions):
                            request.app[HEA_CACHE][(sub, volume_id, bucket_name, folder_id_, folder_item_dict['id'],
                                                    'items')] = (folder_item_dict, perms, attr_perms)
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


@routes.route('OPTIONS', '/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{folder_id}/items/{id}')
async def get_item_options(request: web.Request) -> web.Response:
    """
    ---
    summary: Allowed HTTP methods.
    tags:
        - heaserver-awss3folders-folder-items
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


@routes.route('OPTIONS', '/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{folder_id}/items')
@routes.route('OPTIONS', '/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{folder_id}/items/')
async def get_items_options(request: web.Request) -> web.Response:
    """
    Gets the allowed HTTP methods for a folder items resource.

    :param request: the HTTP request (required).
    :return: the HTTP response.
    ---
    summary: Allowed HTTP methods.
    tags:
        - heaserver-awss3folders-folder-items
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


@routes.route('OPTIONS', '/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}')
async def get_folder_options(request: web.Request) -> web.Response:
    """
    Gets the allowed HTTP methods for a folder resource.

    :param request: the HTTP request (required).
    :return: the HTTP response.
    ---
    summary: Allowed HTTP methods.
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


@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{folder_id}/items/{id}')
@action(name='heaserver-awss3folders-item-get-actual-container', rel='hea-actual hea-actual-container',
        path='{+actual_object_uri}',
        itemif="actual_object_type_name == AWSS3Project.get_type_name() or actual_object_type_name == AWSS3Folder.get_type_name()")
@action(name='heaserver-awss3folders-item-get-actual-not-container', rel='hea-actual',
        path='{+actual_object_uri}',
        itemif="actual_object_type_name != AWSS3Project.get_type_name() and actual_object_type_name != AWSS3Folder.get_type_name()")
@action(name='heaserver-awss3folders-item-get-volume', rel='hea-volume', path='volumes/{volume_id}')
async def get_item(request: web.Request) -> web.Response:
    """
    Gets the requested item from the given folder.

    :param request: the HTTP request. Required.
    :return: the requested item, or Not Found if it was not found.
    ---
    summary: A specific folder item.
    tags:
        - heaserver-awss3folders-folder-items
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
        if cached_value := request.app[HEA_CACHE].get(cache_key):
            item_dict, permissions, attribute_perms = cached_value
            return await response.get(request, cached_value, permissions=permissions,
                                      attribute_permissions=attribute_perms)
        else:
            context = ViewerPermissionContext(sub)
            async with mongo.MongoContext(request=request) as mongo_client:
                async with aws.S3ClientContext(request=request, volume_id=volume_id) as s3:
                    try:
                        loop = asyncio.get_running_loop()

                        if folder_or_item_not_found:
                            activity.status = Status.FAILED
                            return await awsservicelib.return_bucket_status_or_not_found(bucket_name, loop, s3)

                        logger.debug('Getting item %s in folder %s in bucket %s', decoded_key, decoded_folder_key,
                                     bucket_name)
                        response_ = await loop.run_in_executor(None, partial(s3.list_objects_v2, Bucket=bucket_name,
                                                                             Prefix=decoded_key,
                                                                             MaxKeys=1, Delimiter='/',
                                                                             OptionalObjectAttributes=[
                                                                                 'RestoreStatus']))
                        for obj in chain(iter(response_.get('Contents', [])),
                                         iter(response_.get('CommonPrefixes', []))):
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
                            share = await item.get_permissions_as_share(context)
                            item.add_user_share(share)
                            permissions = share.permissions
                            attribute_perms = await item.get_all_attribute_permissions(context)
                            if is_folder_:
                                metadata_dict = await awsservicelib.get_metadata(mongo_client, bucket_name, id_encoded)
                                if not metadata_dict or metadata_dict[
                                    'actual_object_type_name'] == AWSS3Folder.get_type_name():
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
                                # Anything that's not a folder must be an ObjectTypeDef, so it has a Size, StorageClass, etc.
                                item.actual_object_uri = str(actual_object_uri_base / 'awss3files' / id_encoded)
                                item.actual_object_type_name = AWSS3FileObject.get_type_name()
                                item.size = obj['Size']  # type:ignore[misc]
                                item.mime_type = guess_mime_type(item.display_name)
                                item.type_display_name = get_type_display_name(item.mime_type)
                                set_s3_storage_status(obj, item)
                            activity.new_object_id = id_encoded
                            activity.new_object_uri = f'volumes/{volume_id}/buckets/{bucket_name}/awss3projects/{folder_id_}/items/{id_encoded}'
                            activity.new_object_type_name = AWSS3ItemInFolder.get_type_name()
                            activity.new_volume_id = volume_id
                            activity.new_object_display_name = item.display_name
                            if 'path' in request.url.query:
                                activity.new_context_dependent_object_path = request.url.query.getall('path')
                            item_dict = item.to_dict()
                            request.app[HEA_CACHE][cache_key] = item_dict, permissions, attribute_perms
                            return await response.get(request, item_dict, permissions=permissions,
                                                      attribute_permissions=attribute_perms)
                        return await response.get(request, None)
                    except BotoClientError as e:
                        activity.status = Status.FAILED
                        return awsservicelib.handle_client_error(e)


@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/duplicator')
@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/duplicatorasync')
@action(name='heaserver-awss3folders-folder-duplicate-form')
@action(name='heaserver-awss3folders-folder-get-self', rel='self hea-self-container',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}')
async def get_folder_duplicator(request: web.Request) -> web.Response:
    """
    Gets a form template for duplicating the requested folder.

    :param request: the HTTP request. Required.
    :return: the requested form, or Not Found if the requested folder was not found.
    ---
    summary: A folder to duplicate.
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
      '404':
        $ref: '#/components/responses/404'
    """
    return await _get_folder_move_template(request)


@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/unarchive')
@action(name='heaserver-awss3folders-folder-unarchive-form')
@action(name='heaserver-awss3folders-folder-get-self', rel='self',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}')
async def get_folder_unarchive_form(request: web.Request) -> web.Response:
    """
    Gets a form template for unarchiving the requested folder.

    :param request: the HTTP request. Required.
    :return: the requested form, or Not Found if the requested folder was not found.
    ---
    summary: Get a specific folder to unarchive.
    tags:
        - heaserver-folders-aws-s3
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
    return await _get_folder_move_template(request)


@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/archive')
@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/archiveasync')
@action(name='heaserver-awss3folders-folder-archive-form')
@action(name='heaserver-awss3folders-folder-get-self', rel='self',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}')
async def get_folder_archive(request: web.Request) -> web.Response:
    """
    Gets a form template for archiving the requested folder.

    :param request: the HTTP request. Required.
    :return: the requested form, or Not Found if the requested folder was not found.
    ---
    summary: A specific folder to be archived.
    tags:
        - heaserver-awss3folders-folders
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
    return await _get_folder_move_template(request)


@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/unarchive')
@action(name='heaserver-awss3folders-folder-unarchive-form')
@action(name='heaserver-awss3folders-folder-get-self', rel='self',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}')
async def get_folder_unarchive(request: web.Request) -> web.Response:
    """
    Gets a form template for unarchiving the requested folder.

    :param request: the HTTP request. Required.
    :return: the requested form, or Not Found if the requested folder was not found.
    ---
    summary: A specific folder to be archived.
    tags:
        - heaserver-awss3folders-folders
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
    return await _get_folder_move_template(request)


@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/mover')
@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/moverasync')
@action(name='heaserver-awss3folders-folder-move-form')
@action(name='heaserver-awss3folders-folder-get-self', rel='self',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}')
async def get_folder_mover(request: web.Request) -> web.Response:
    """
    Gets a form template for moving the requested folder.

    :param request: the HTTP request. Required.
    :return: the requested form, or Not Found if the requested folder was not found.
    ---
    summary: A folder to move.
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
      '404':
        $ref: '#/components/responses/404'
    """
    return await _get_folder_move_template(request)


@routes.post('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/archive')
async def post_folder_archive(request: web.Request) -> web.Response:
    """
    Posts the provided folder to archive it.

    :param request: the HTTP request.
    :return: a Response object with a status of No Content.
    ---
    summary: A specific folder to be archived.
    tags:
        - heaserver-awss3folders-folders
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
        description: The new name of the folder and target for archiving it.
        required: true
        content:
            application/vnd.collection+json:
              schema:
                type: object
              examples:
                example:
                  summary: The name of the storage class to arhive the files to
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
                  summary: The new name of the file and target for moving it.
                  value: {
                    "target": "http://localhost:8080/volumes/666f6f2d6261722d71757578/buckets/my-bucket/awss3files/"
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
    try:
        key = decode_key(id_)
    except KeyDecodeException as e:
        return await response.get(request, None)

    if not awss3key.is_folder(key):
        return await response.get(request, None)
    if not await _is_folder(request, volume_id, bucket_name, id_):
        return response.status_not_found()
    try:
        return await awsservicelib.archive_object(request, activity_cb=publish_desktop_object)
    finally:
        request.app[HEA_CACHE].pop((sub, volume_id, bucket_name, None, 'actual'), None)
        request.app[HEA_CACHE].pop((sub, volume_id, bucket_name, id_, 'actual'), None)
        request.app[HEA_CACHE].pop((sub, volume_id, bucket_name, id_, None, 'items'), None)
        for key_ in tuple(request.app[HEA_CACHE].keys()):
            if key_[0:3] == (sub, volume_id, bucket_name) and key_[3] not in (None, 'root') and decode_key(key_[3]).startswith(key):
                request.app[HEA_CACHE].pop(key_, None)


@routes.post('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/archiveasync')
async def post_folder_archive_async(request: web.Request) -> web.Response:
    """
    Posts the provided folder to archive it.

    :param request: the HTTP request.
    :return: a Response object with a status of No Content.
    ---
    summary: A specific folder to be archived.
    tags:
        - heaserver-awss3folders-folders
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
        description: The new name of the folder and target for archiving it.
        required: true
        content:
            application/vnd.collection+json:
              schema:
                type: object
              examples:
                example:
                  summary: The name of the storage class to arhive the files to
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
                  summary: The new name of the file and target for moving it.
                  value: {
                    "target": "http://localhost:8080/volumes/666f6f2d6261722d71757578/buckets/my-bucket/awss3files/"
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
    try:
        key = decode_key(id_)
    except KeyDecodeException as e:
        return await response.get(request, None)

    if not awss3key.is_folder(key):
        return await response.get(request, None)
    if not await _is_folder(request, volume_id, bucket_name, id_):
        return response.status_not_found()

    async def publish_desktop_object_and_clear_cache(app: web.Application, desktop_object: DesktopObject,
                                                     appproperty_=HEA_MESSAGE_BROKER_PUBLISHER):
        if isinstance(desktop_object, Activity):
            request.app[HEA_CACHE].pop((sub, volume_id, bucket_name, None, 'actual'), None)
            request.app[HEA_CACHE].pop((sub, volume_id, bucket_name, id_, 'actual'), None)
            request.app[HEA_CACHE].pop((sub, volume_id, bucket_name, id_, None, 'items'), None)
            for key_ in tuple(request.app[HEA_CACHE].keys()):
                if key_[0:3] == (sub, volume_id, bucket_name) and key_[3] not in (None, 'root') and decode_key(key_[3]).startswith(key):
                    request.app[HEA_CACHE].pop(key_, None)
        await publish_desktop_object(app, desktop_object, appproperty_)
    path = f'{request.url.path}status'
    return await awsservicelib.archive_object_async(request, request.url.with_path(path),   # Don't keep query params.
                                                    activity_cb=publish_desktop_object_and_clear_cache)


@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/archiveasyncstatus')
@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/duplicatorasyncstatus{status_id}')
@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/moverasyncstatus')
@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/deleterasyncstatus')
@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/updaterasyncstatus{status_id}')
async def get_folder_async_status(request: web.Request) -> web.Response:
    return response.get_async_status(request)


@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{folder_id}/items/{id}/deleterasyncstatus')
@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{folder_id}/itemsasyncstatus{status_id}')
async def get_item_async_status(request: web.Request) -> web.Response:
    return response.get_async_status(request)


@routes.post('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/unarchive')
async def unarchive_folder(request: web.Request) -> web.Response:
    """

    :param request:
    :return: a Response object with status 202 Accept

    ---
    summary: A specific Folder.
    tags:
        - heaserver-awss3folders-folders
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
        description: The new name of the folder and target for archiving it.
        required: true
        content:
            application/vnd.collection+json:
              schema:
                type: object
              examples:
                example:
                  summary: The parameters for temporarily restoring your archived object
                  value: {
                    "template": {
                      "data": [
                              {
                                "name": "restore_tier",
                                "value": "Bulk"
                              },
                              {
                               "name": "days",
                                "value": "3"
                              }
                      ]
                    }
                  }
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
    try:
        key = decode_key(id_)
    except KeyDecodeException as e:
        return await response.get(request, None)

    if not awsservicelib.is_folder(key):
        return await response.get(request, None)
    if await _is_folder(request, volume_id, bucket_name, id_):
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


@routes.post('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/mover')
async def post_folder_mover(request: web.Request) -> web.Response:
    """
    Posts the provided folder to move it.

    :param request: the HTTP request.
    :return: a Response object with a status of No Content.
    ---
    summary: A specific folder.
    tags:
        - heaserver-awss3folders-folders
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
        description: The new name of the folder and target for moving it.
        required: true
        content:
            application/vnd.collection+json:
              schema:
                type: object
              examples:
                example:
                  summary: The new name of the folder and target for moving it.
                  value: {
                    "template": {
                      "data": [
                      {
                        "name": "target",
                        "value": "http://localhost:8080/volumes/666f6f2d6261722d71757578/buckets/my-bucket/awss3folders/"
                      }]
                    }
                  }
            application/json:
              schema:
                type: object
              examples:
                example:
                  summary: The new name of the folder and target for moving it.
                  value: {
                    "target": "http://localhost:8080/volumes/666f6f2d6261722d71757578/buckets/my-bucket/awss3folders/"
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
    try:
        key = decode_key(id_)
    except KeyDecodeException as e:
        return response.status_not_found()
    if not awsservicelib.is_folder(key):
        return response.status_not_found()
    return await _do_move(request, sub, volume_id, bucket_id, id_, key)


_move_lock = asyncio.Lock()


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
            return await move(activity, request, mongo_client, sub, volume_id, bucket_id, id_, key,
                              new_volume_id, target_bucket_id, target_key_parent, AWSS3Folder, target_path)


@routes.post('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/moverasync')
async def post_folder_mover_async(request: web.Request) -> web.Response:
    """
    Posts the provided folder to move it.

    :param request: the HTTP request.
    :return: a Response object with a status of No Content.
    ---
    summary: A specific folder.
    tags:
        - heaserver-awss3folders-folders
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
        description: The new name of the folder and target for moving it.
        required: true
        content:
            application/vnd.collection+json:
              schema:
                type: object
              examples:
                example:
                  summary: The new name of the folder and target for moving it.
                  value: {
                    "template": {
                      "data": [
                      {
                        "name": "target",
                        "value": "http://localhost:8080/volumes/666f6f2d6261722d71757578/buckets/my-bucket/awss3folders/"
                      }]
                    }
                  }
            application/json:
              schema:
                type: object
              examples:
                example:
                  summary: The new name of the folder and target for moving it.
                  value: {
                    "target": "http://localhost:8080/volumes/666f6f2d6261722d71757578/buckets/my-bucket/awss3folders/"
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
    try:
        key = decode_key(id_)
    except KeyDecodeException as e:
        return response.status_not_found()
    if not awsservicelib.is_folder(key):
        return response.status_not_found()

    async def coro(app: web.Application):
        return await _do_move(request, sub, volume_id, bucket_id, id_, key)
    path = f'{request.url.path}status'
    status_location = request.url.with_path(path)   # Don't keep query params.
    task_name = f'{sub}^{status_location}'
    async with _move_lock:
        if request.app[HEA_BACKGROUND_TASKS].in_progress(task_name):
            return response.status_conflict(
                f'A move of {awsservicelib.s3_object_message_display_name(bucket_id, key)} is already in progress')
        await request.app[HEA_BACKGROUND_TASKS].add(coro, name=task_name)
    return response.status_see_other(status_location)


@routes.post('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/duplicator')
async def post_folder_duplicator(request: web.Request) -> web.Response:
    """
    Posts the provided folder for duplication.

    :param request: the HTTP request.
    :return: a Response object with a status of Created and the object's URI in the
    ---
    summary: A specific folder.
    tags:
        - heaserver-awss3folders-folders
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
    volume_id = request.match_info['volume_id']
    bucket_id = request.match_info['bucket_id']
    id_ = request.match_info['id']
    try:
        key = decode_key(id_)
    except KeyDecodeException as e:
        return response.status_not_found()
    if not awsservicelib.is_folder(key):
        return response.status_not_found()
    if not await _is_folder(request, volume_id, bucket_id, id_):
        return response.status_not_found()
    _, _, target_key_parent, new_volume_id, target_path = await awsservicelib._copy_object_extract_target(await request.json())
    async with mongo.MongoContext(request) as mongo_client:
        return await copy(request, mongo_client, target_key_parent, new_volume_id, target_path=target_path)

@routes.post('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/duplicatorasync')
async def post_folder_duplicator_async(request: web.Request) -> web.Response:
    """
    Posts the provided folder for duplication.

    :param request: the HTTP request.
    :return: a Response object with a status of Created and the object's URI in the
    ---
    summary: A specific folder.
    tags:
        - heaserver-awss3folders-folders
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
    volume_id = request.match_info['volume_id']
    bucket_id = request.match_info['bucket_id']
    id_ = request.match_info['id']
    try:
        key = decode_key(id_)
    except KeyDecodeException as e:
        return response.status_not_found()
    if not awsservicelib.is_folder(key):
        return response.status_not_found()
    if not await _is_folder(request, volume_id, bucket_id, id_):
        return response.status_not_found()
    global _status_id
    path = f'{request.url.path}status{_status_id}'
    status_location = str(request.url.with_path(path))  # Don't keep query params.
    _status_id += 1

    async with mongo.MongoContext(request) as mongo_client:
        _, _, target_key_parent, new_volume_id, target_path = await awsservicelib._copy_object_extract_target(await request.json())

        return await copy(request, mongo_client, target_key_parent, new_volume_id, status_location, target_path)


@routes.post('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/uploader')
@routes.post('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/uploader/')
async def post_folder_uploader(request: web.Request) -> web.Response:
    """
    Uploads file to a target folder.

    :param request: the HTTP request. The body of the request is expected to be an item or an actual object.
    :return: the response, with a 204 status code if an item was created or a 400 if not. If an item was created, the
    Location header will contain the URL of the created item.
    ---
    summary: A upload to a specific folder item.
    tags:
        - heaserver-awss3folders-folders
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
        return response.status_bad_request('obj is a required field')
    if obj.display_name is None:
        return response.status_bad_request("display_name is required")
    if obj.name is None:
        return response.status_bad_request('name is required')
    if obj.storage_class is None:
        return response.status_bad_request('storage_class is required')
    if '/' in obj.display_name:
        return response.status_bad_request(f"The item's display name may not have slashes in it")
    assert obj.key is not None, 'key is required'

    logger.debug("the obj's name and display_name %s, %s", obj.name, obj.display_name)
    volume_id = request.match_info['volume_id']
    bucket_id = request.match_info['bucket_id']
    folder_id = request.match_info['id']
    if '/' in obj.display_name:
        return response.status_bad_request(f"The item's display name may not have slashes in it")
    try:
        # if folder id is root let it decode to '' otherwise if its not a Folder set it to None
        decoded_folder_id = awsservicelib.decode_folder(folder_id)
        if folder_id != awsservicelib.ROOT_FOLDER.id and not awsservicelib.is_folder(decoded_folder_id):
            decoded_folder_id = None
    except KeyDecodeException:
        decoded_folder_id = None
    if not await _is_folder(request, volume_id, bucket_id, folder_id):
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
            obj_name = f'{decoded_folder_id}{decode_key(obj.name)}'
            url = f"volumes/{request.match_info['volume_id']}/buckets/{request.match_info['bucket_id']}/awss3files"
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
                        await loop.run_in_executor(None, partial(s3_client.put_object, Bucket=bucket_id,
                                                                Key=obj_name, StorageClass=obj.storage_class.name))  # type:ignore[arg-type]
                        request.app[HEA_CACHE].pop((sub, volume_id, bucket_id, folder_id, None, 'items'), None)
                        request.app[HEA_CACHE].pop((sub, volume_id, bucket_id, folder_id, obj.id, 'items'), None)
                        request.app[HEA_CACHE].pop((sub, volume_id, bucket_id, None, 'actual'), None)
                        request.app[HEA_CACHE].pop((sub, volume_id, bucket_id, obj.id, 'actual'), None)
                        return await response.post(request, f"{encode_key(obj_name)}/content", url)
                    except BotoClientError as e2:
                        raise awsservicelib.handle_client_error(e2)
                else:
                    raise response.status_bad_request(str(e))


@routes.post('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{folder_id}/items')
@routes.post('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{folder_id}/items/')
async def post_item_in_folder(request: web.Request) -> web.Response:
    """
    Creates a new folder item.

    :param request: the HTTP request. The body of the request is expected to be an item or an actual object.
    :return: the response, with a 204 status code if an item was created or a 400 if not. If an item was created, the
    Location header will contain the URL of the created item.
    ---
    summary: A specific folder item.
    tags:
        - heaserver-awss3folders-folder-items
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
    try:
        # if folder id is root let it decode to '' otherwise if its not a Folder set it to None
        folder_key = awsservicelib.decode_folder(folder_id)

        if folder_id != awsservicelib.ROOT_FOLDER.id and not awsservicelib.is_folder(folder_key):
            folder_key = None
    except KeyDecodeException:
        folder_key = None

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
                    return response.status_bad_request(
                        f'Unsupported actual_object_type_name {item.actual_object_type_name}')
                response_ = await loop.run_in_executor(None, partial(s3_client.head_object, Bucket=bucket_id,
                                                                     Key=item_name))  # check if item exists, if not throws an exception
                logger.debug('Result of post_object: %s', response_)
                activity.status = Status.FAILED
                return response.status_bad_request(body=f"Item {item_name} already exists")
            except BotoClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == aws.CLIENT_ERROR_404:  # folder doesn't exist
                    await loop.run_in_executor(None, partial(s3_client.put_object, Bucket=bucket_id, Key=item_name))
                    if item.actual_object_type_name == AWSS3Project.get_type_name():
                        async with mongo.MongoContext(request) as mongo_client:
                            metadata = {
                                'bucket_id': bucket_id,
                                'encoded_key': item.id,
                                'actual_object_type_name': AWSS3Project.get_type_name(),
                                'parent_encoded_key': folder_id
                            }
                            await mongo_client.upsert_admin_nondesktop_object(metadata, MONGODB_AWS_S3_FOLDER_METADATA_COLLECTION,
                                                            mongoattributes={'bucket_id': bucket_id,
                                                                             'encoded_key': item.id})
                    activity.new_object_id = encode_key(item_name)
                    activity.new_object_type_name = AWSS3ItemInFolder.get_type_name()
                    activity.new_volume_id = request.match_info['volume_id']
                    activity.new_object_uri = f"volumes/{activity.new_volume_id}/buckets/{request.match_info['bucket_id']}/awss3folders/{folder_id}/items/{activity.new_object_id}"
                    activity.new_object_display_name = item.display_name
                    activity.new_object_description = item.description
                    request.app[HEA_CACHE].pop((sub, volume_id, bucket_id, folder_id, None, 'items'), None)
                    request.app[HEA_CACHE].pop((sub, volume_id, bucket_id, None, 'actual'), None)
                    return await response.post(request, encode_key(item_name),
                                               f"volumes/{request.match_info['volume_id']}/buckets/{request.match_info['bucket_id']}/awss3folders/{folder_id}/items")
                elif error_code == aws.CLIENT_ERROR_NO_SUCH_BUCKET:
                    activity.status = Status.FAILED
                    return response.status_not_found()
                else:
                    activity.status = Status.FAILED
                    return response.status_bad_request(str(e))


@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/convertertoproject')
@action(name='heaserver-awss3folders-folder-convert-to-project-form')
@action(name='heaserver-awss3folders-folder-get-self', rel='self hea-self-container',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}')
async def get_convert_to_project(request: web.Request) -> web.Response:
    context = aws.S3ObjectPermissionContext(request)
    return await _get_folder(request, context)


@routes.post('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/convertertoproject')
async def post_convert_to_project(request: web.Request) -> web.Response:
    sub = request.headers.get(SUB, NONE_USER)
    volume_id = request.match_info['volume_id']
    bucket_name = request.match_info['bucket_id']
    folder_id = request.match_info['id']
    folder_key = decode_key(folder_id)

    async with mongo.MongoContext(request=request) as mongo_client:
        async with DesktopObjectActionLifecycle(request=request,
                                                code='hea-create',
                                                description=f'Converting {awsservicelib.s3_object_message_display_name(bucket_name, folder_id)} to a project',
                                                activity_cb=publish_desktop_object) as activity:
            activity.old_object_id = folder_id
            activity.old_volume_id = volume_id
            activity.old_object_type_name = AWSS3Folder.get_type_name()
            activity.old_object_uri = f'volumes/{volume_id}/buckets/{bucket_name}/awss3folders/{folder_id}'
            activity.old_object_display_name = display_name(folder_key)
            if 'path' in request.url.query:
                activity.old_context_dependent_object_path = request.url.query.getall('path')
            async with aws.S3ClientContext(request=request, volume_id=volume_id) as s3_client:
                try:
                    folder = await _get_folder_helper(s3_client, request)
                    assert folder.id is not None, 'folder.id cannot be None'
                    if not await _is_folder(request, volume_id, bucket_name, folder.id):
                        return await response.get(request, None)
                    parent_folder_key = parent(folder.key)
                    parent_encoded_key = encode_key(parent_folder_key) if parent_folder_key else 'root'
                    metadata = {
                        'bucket_id': bucket_name,
                        'encoded_key': folder.id,
                        'actual_object_type_name': AWSS3Project.get_type_name(),
                        'parent_encoded_key': parent_encoded_key,
                        'deleted': False,
                        'version': None
                    }
                    _, description = await asyncio.gather(mongo_client.upsert_admin_nondesktop_object(metadata,
                                                        MONGODB_AWS_S3_FOLDER_METADATA_COLLECTION,
                                                        mongoattributes={'bucket_id': bucket_name,
                                                                        'encoded_key': folder.id}),
                                                    get_description(sub, s3_client, bucket_name, folder_key))
                    activity.new_object_id = folder_id
                    activity.new_volume_id = volume_id
                    activity.new_object_type_name = AWSS3Project.get_type_name()
                    activity.new_object_uri = f'volumes/{volume_id}/buckets/{bucket_name}/awss3projects/{folder_id}'
                    activity.new_object_display_name = activity.old_object_display_name
                    activity.new_context_dependent_object_path = activity.old_context_dependent_object_path
                    activity.new_object_description = description
                    request.app[HEA_CACHE].pop((sub, volume_id, bucket_name, folder_id, None, 'items'), None)
                    request.app[HEA_CACHE].pop((sub, volume_id, bucket_name, parent_encoded_key, folder.id, 'items'),
                                               None)
                    request.app[HEA_CACHE].pop((sub, volume_id, bucket_name, parent_encoded_key, None, 'items'),
                                               None)
                    request.app[HEA_CACHE].pop((sub, volume_id, bucket_name, folder_id, 'actual'), None)
                    request.app[HEA_CACHE].pop((sub, volume_id, bucket_name, None, 'actual'), None)
                    return await response.post(request, folder.id,
                                               resource_base=f'volumes/{volume_id}/buckets/{bucket_name}/awss3projects/')
                except BotoClientError as e:
                    activity.status = Status.FAILED
                    return awsservicelib.handle_client_error(e)


@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}')
@action(name='heaserver-awss3folders-folder-get-open-choices', rel='hea-opener-choices hea-context-menu hea-downloader',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/opener')
@action(name='heaserver-awss3folders-folder-get-properties', rel='hea-properties hea-context-menu')
@action(name='heaserver-awss3folders-folder-duplicate', rel='hea-dynamic-standard hea-icon-duplicator hea-context-menu',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/duplicatorasync')
@action(name='heaserver-awss3folders-folder-move', rel='hea-dynamic-standard hea-icon-mover hea-context-menu',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/moverasync')
@action(name='heaserver-awss3folders-folder-get-create-choices', rel='hea-creator-choices hea-context-menu',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/creator')
@action(name='heaserver-awss3folders-folder-get-trash', rel='hea-trash hea-context-menu',
        path='volumes/{volume_id}/awss3trash')
@action(name='heaserver-awss3folders-folder-archive', rel='hea-dynamic-standard hea-archive hea-context-menu',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/archiveasync')
@action(name='heaserver-awss3folders-folder-unarchive', rel='hea-dynamic-standard hea-unarchive hea-context-menu',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/unarchive')
@action(name='heaserver-awss3folders-folder-get-presigned-url',
        rel='hea-dynamic-clipboard hea-icon-for-clipboard hea-context-menu',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/presignedurl')
@action(name='heaserver-awss3folders-folder-convert-to-project', rel='hea-dynamic-standard hea-context-menu',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/convertertoproject')
@action(name='heaserver-awss3folders-folder-get-self', rel='self hea-self-container',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}')
@action(name='heaserver-awss3folders-folder-get-volume', rel='hea-volume', path='volumes/{volume_id}')
@action(name='heaserver-awss3folders-folder-get-awsaccount', rel='hea-account',
        path='volumes/{volume_id}/awsaccounts/me')
@action(name='heaserver-awss3folders-item-upload', rel='hea-uploader',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/uploader')
@action(name='heaserver-awss3folders-folder-get-component', rel='hea-component',
        path='components/bytype/heaobject.folder.AWSS3Folder')
@action(name='heaserver-awss3folders-get-delete-preflight-url', rel='hea-delete-preflight',
        path='preflights/awss3objects/delete')
async def get_folder(request: web.Request) -> web.Response:
    """
    Gets the folder with the specified id.

    :param request: the HTTP request.
    :return: the requested folder or Not Found.
    ---
    summary: A specific folder.
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
      '404':
        $ref: '#/components/responses/404'
    """
    context = aws.S3ObjectPermissionContext(request)
    return await _get_folder(request, context)


@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/byname/{name}')
@action(name='heaserver-awss3folders-folder-get-self', rel='self hea-self-container',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}')
@action(name='heaserver-awss3folders-folder-get-volume', rel='hea-volume', path='volumes/{volume_id}')
@action(name='heaserver-awss3folders-folder-get-awsaccount', rel='hea-account',
        path='volumes/{volume_id}/awsaccounts/me')
@action(name='heaserver-awss3folders-folder-get-component', rel='hea-component',
        path='components/bytype/heaobject.folder.AWSS3Folder')
async def get_folder_by_name(request: web.Request) -> web.Response:
    """
    Gets the folder with the specified name.

    :param request: the HTTP request.
    :return: the requested folder or Not Found.
    ---
    summary: A specific folder.
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
        - $ref: '#/components/parameters/name'
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    responses:
      '200':
        $ref: '#/components/responses/200'
      '404':
        $ref: '#/components/responses/404'
    """
    context = aws.S3ObjectPermissionContext(request)
    return await _get_folder(request, context)


@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/content')
async def get_folder_contents_as_zip_file(request: web.Request) -> web.StreamResponse:
    """
    Gets the contents of all objects within the folder with the specified id.

    :param request: the HTTP request.
    :return: the requested folder or Not Found.
    """
    logger = logging.getLogger(__name__)
    logger.debug('Getting folder from request %s', request)
    volume_id = request.match_info['volume_id']
    bucket_name = request.match_info['bucket_id']
    folder_name = request.match_info['id']

    try:
        folder_key = decode_key(folder_name) if folder_name != awsservicelib.ROOT_FOLDER.id else None
    except KeyDecodeException:
        logger.debug('No folder with id or name %s', folder_name, exc_info=True)
        raise response.status_not_found()

    async with DesktopObjectActionLifecycle(request=request,
                                            code='hea-get',
                                            description=f'Downloading {awsservicelib.s3_object_message_display_name(bucket_name, folder_key)}',
                                            activity_cb=publish_desktop_object) as activity:
        async with aws.S3ClientContext(request=request, volume_id=volume_id) as s3_client:
            try:
                folder, is_folder = await asyncio.gather(_has_folder_helper(s3_client, request),
                                                         _is_folder(request, volume_id, bucket_name, folder_name))
                if not folder or not is_folder:
                    logger.debug('Not a folder: %s', folder_name)
                    raise response.status_not_found()

                await fail_if_too_big(bucket_name, folder_key, activity, s3_client)

                response_ = await response_folder_as_zip(s3_client, request, bucket_name, folder_key)

                if folder_key:
                    activity.new_volume_id = volume_id
                    activity.new_object_id = folder_name
                    activity.new_object_type_name = AWSS3Folder.get_type_name()
                    activity.new_object_uri = f'volumes/{volume_id}/buckets/{bucket_name}/awss3folders/{folder_name}'
                    activity.new_object_display_name = split(folder_key)[1].removesuffix('/')
                else:
                    activity.new_volume_id = volume_id
                    activity.new_object_id = bucket_name
                    activity.new_object_type_name = AWSBucket.get_type_name()
                    activity.new_object_uri = f'volumes/{volume_id}/buckets/{bucket_name}'
                    activity.new_object_display_name = bucket_name
                if 'path' in request.url.query:
                    activity.new_context_dependent_object_path = request.url.query.getall('path')
                return response_
            except BotoClientError as e:
                activity.status = Status.FAILED
                return awsservicelib.handle_client_error(e)

@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/presignedurl')
@action(name='heaserver-awss3folders-folder-get-presigned-url-form')
@action(name='heaserver-awss3folders-folder-get-self', rel='self hea-self-container',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}')
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
    return await _get_folder(request, context)


@routes.post('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/presignedurl')
async def post_presigned_url_form(request: web.Request) -> web.Response:
    """
    Posts a template for requesting the generation of a presigned URL.

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
        activity.new_object_id = object_id
        activity.new_object_type_name = AWSS3Folder.get_type_name()
        activity.new_volume_id = volume_id
        activity.new_object_uri = f'volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{object_id}'
        if 'path' in request.url.query:
            activity.new_context_dependent_object_path = request.url.query.getall('path')
        if not await _is_folder(request, volume_id, bucket_id, object_id):
            object_key = None
        if object_key is None:
            async with aws.S3ClientContext(request, volume_id=volume_id) as s3_client:
                raise await when_object_not_found(s3_client, bucket_id)
        activity.new_object_display_name = display_name(object_key)
        presigned_creds = await create_presigned_url_credentials(request, volume_id, expiration_hours, object_key,bucket_id)
        async with aws.S3ClientContext(request=request, credentials=presigned_creds) as presigned_s3_client:
            try:
                loop = asyncio.get_running_loop()
                urls: list[str] = []

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
                raise response.status_bad_request(
                    'There are no files in this folder, or all are in archived storage.')
            # The response contains the presigned URL
            data: ClipboardData = ClipboardData()
            data.mime_type = 'text/plain;encoding=utf-8'
            data.data = client_line_ending(request).join(urls)
            data.created = now()
            f: AWSS3FileObject = AWSS3FileObject()
            f.bucket_id = bucket_id
            f.id = object_id
            data.display_name = f'Presigned URL for {f.display_name}'
            activity.new_object_id = object_id
            activity.new_object_type_name = AWSS3Folder.get_type_name()
            activity.new_volume_id = volume_id
            activity.new_object_uri = f'volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{object_id}'
            activity.new_object_display_name = f.display_name
            if 'path' in request.url.query:
                activity.new_context_dependent_object_path = request.url.query.getall('path')
            return await response.get(request, to_dict(data))


@routes.post('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders')
@routes.post('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/')
async def post_folder(request: web.Request) -> web.Response:
    """
    Creates a new folder.

    :param request: the HTTP request. The body of the request is expected to be a folder.
    :return: the response, with a 204 status code if a folder was created or a 400 if not. If a folder was created, the
    Location header will contain the URL of the created folder.
    ---
    summary: A specific folder.
    tags:
        - heaserver-awss3folders-folders
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
        description: A new folder object.
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
                    "type": "heaobject.folder.AWSS3Folder",
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
    bucket_id = request.match_info['bucket_id']
    volume_id = request.match_info['volume_id']
    resp = await awsservicelib.create_object(request, AWSS3Folder)
    id_ = resp.headers[hdrs.LOCATION].rsplit('/', 1)[-1]
    if not (folder_id := encode_key(parent(decode_key(id_)))):
        folder_id = 'root'
    request.app[HEA_CACHE].pop((sub, volume_id, bucket_id, folder_id, None, 'items'), None)
    request.app[HEA_CACHE].pop((sub, volume_id, bucket_id, None, 'actual'), None)
    async with mongo.MongoContext(request) as mongo_client:
        await mongo_client.delete_admin(MONGODB_AWS_S3_FOLDER_METADATA_COLLECTION,
                                        mongoattributes={'bucket_id': bucket_id, 'encoded_key': id_})
    return resp


@routes.put('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}')
async def put_folder(request: web.Request) -> web.Response:
    logger = logging.getLogger(__name__)
    sub = request.headers.get(SUB, NONE_USER)
    volume_id = request.match_info['volume_id']
    bucket_id = request.match_info['bucket_id']
    old_id = request.match_info['id']

    try:
        old_key = decode_key(old_id)
    except KeyDecodeException as e:
        return response.status_not_found()
    if not awsservicelib.is_folder(old_key):
        return response.status_not_found()

    async def coro(app: web.Application):
        async with mongo.MongoContext(request) as mongo_client:
            try:
                folder = await new_heaobject_from_type(request, AWSS3Folder)
            except TypeError:
                return response.status_bad_request(f'Expected type {AWSS3Folder}; actual object was {await request.text()}')
            except DeserializeException as e:
                return response.status_bad_request(str(e))
            async with DesktopObjectActionLifecycle(request,
                                            code='hea-update',
                                            description=f'Renaming {awsservicelib.s3_object_message_display_name(bucket_id, old_key)} to {folder.display_name}',
                                            activity_cb=publish_desktop_object) as activity:
                if 'path' in request.url.query:
                    target_path: list[str] | None = request.url.query.getall('path')
                else:
                    target_path = None
                resp = await rename(activity, request, mongo_client, sub, volume_id, bucket_id, old_id, old_key, folder, AWSS3Folder, target_path)
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


@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders')
@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/')
@action('heaserver-awss3folders-folder-get-open-choices', rel='hea-opener-choices hea-context-menu hea-downloader',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/opener')
@action(name='heaserver-awss3folders-folder-get-properties', rel='hea-properties hea-context-menu')
@action(name='heaserver-awss3folders-folder-duplicate', rel='hea-dynamic-standard hea-icon-duplicator hea-context-menu',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/duplicatorasync')
@action(name='heaserver-awss3folders-folder-move', rel='hea-dynamic-standard hea-icon-mover hea-context-menu',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/moverasync')
@action(name='heaserver-awss3folders-folder-get-create-choices', rel='hea-creator-choices hea-context-menu',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/creator')
@action(name='heaserver-awss3folders-folder-archive', rel='hea-dynamic-standard hea-archive hea-context-menu',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/archiveasync')
@action(name='heaserver-awss3folders-folder-unarchive', rel='hea-dynamic-standard hea-unarchive hea-context-menu',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/unarchive')
@action(name='heaserver-awss3folders-folder-get-trash', rel='hea-trash hea-context-menu',
        path='volumes/{volume_id}/awss3trash')
@action(name='heaserver-awss3folders-folder-get-presigned-url',
        rel='hea-dynamic-clipboard hea-icon-for-clipboard hea-context-menu',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/presignedurl')
@action(name='heaserver-awss3folders-folder-convert-to-project',
        rel='hea-dynamic-standard hea-context-menu',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/convertertoproject')
@action(name='heaserver-awss3folders-folder-get-self', rel='self hea-self-container',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}')
@action(name='heaserver-awss3folders-item-upload', rel='hea-uploader',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/uploader')
@action(name='heaserver-awss3folders-folder-get-component', rel='hea-component',
        path='components/bytype/heaobject.folder.AWSS3Folder')
@action(name='heaserver-awss3folders-get-delete-preflight-url', rel='hea-delete-preflight',
        path='preflights/awss3objects/delete')
async def get_folders(request: web.Request) -> web.Response:
    """
    Gets all folders in the bucket.

    :param request: the HTTP request.
    :return: the requested folder or Not Found.
    ---
    summary: All folders.
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
                                                description=f'Listing all folders in bucket {bucket_name}',
                                                activity_cb=publish_desktop_object) as activity:
            cache_key = (sub, volume_id, bucket_name, None, 'actual')
            if cached_value := request.app[HEA_CACHE].get(cache_key):
                data = cached_value[0]
                permissions: list[list[Permission]] = cached_value[1]
                attr_perms: list[dict[str, list[Permission]]] = cached_value[2]
                return await response.get_all(request, data, permissions=permissions, attribute_permissions=attr_perms)
            else:
                context = aws.S3ObjectPermissionContext(request)
                async with aws.S3ClientContext(request=request, volume_id=volume_id) as s3:
                    try:
                        loop = asyncio.get_running_loop()
                        logger.debug('Getting all folders from bucket %s', bucket_name)

                        folders: list[AWSS3Folder] = []
                        async for obj in awsservicelib.list_objects(s3, bucket_name, loop=loop):
                            key = obj['Key']
                            if awsservicelib.is_folder(key):
                                encoded_key = encode_key(key)
                                if logger.getEffectiveLevel() == logging.DEBUG:
                                    logger.debug('Found possible folder %s in bucket %s', key[:-1], bucket_name)
                                folder = _new_folder(bucket_name, obj, encoded_key, request)
                                folders.append(folder)
                        folder_metadata = {}
                        gen_ = mongo_client.get_all_admin(MONGODB_AWS_S3_FOLDER_METADATA_COLLECTION,
                                                          {'bucket_id': bucket_name})
                        try:
                            async for metadata_dict in gen_:
                                folder_metadata[metadata_dict['encoded_key']] = metadata_dict
                        finally:
                            await gen_.aclose()
                        permissions = []
                        attr_perms = []
                        real_folder_dicts: list[DesktopObjectDict] = []
                        for folder in folders:
                            if (obj_metadata_ := folder_metadata.get(folder.id)) is None or \
                                obj_metadata_['actual_object_type_name'] == AWSS3Folder.get_type_name():
                                share = await folder.get_permissions_as_share(context)
                                folder.add_user_share(share)
                                permissions.append(share.permissions)
                                attr_perms.append(await folder.get_all_attribute_permissions(context))
                                real_folder_dicts.append(to_dict(folder))
                        activity.new_object_uri = f'volumes/{volume_id}/buckets/{bucket_name}/awss3folders/'
                        activity.new_volume_id = volume_id
                        activity.new_object_type_name = AWSS3Folder.get_type_name()
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


@routes.route('OPTIONS', '/volumes/{volume_id}/buckets/{bucket_id}/awss3folders')
@routes.route('OPTIONS', '/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/')
async def get_folders_options(request: web.Request) -> web.Response:
    """
    Gets the allowed HTTP methods for a folders resource.

    :param request: the HTTP request (required).
    :response: the HTTP response.
    ---
    summary: Allowed HTTP methods.
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


@routes.delete('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}')
async def delete_folder(request: web.Request) -> web.Response:
    """
    Deletes the folder with the specified id.

    :param request: the HTTP request.
    :return: No Content or Not Found.
    ---
    summary: Folder deletion
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
      '204':
        $ref: '#/components/responses/204'
      '404':
        $ref: '#/components/responses/404'
    """
    sub = request.headers.get(SUB, NONE_USER)
    volume_id = request.match_info['volume_id']
    bucket_id = request.match_info['bucket_id']
    id_ = request.match_info['id']
    try:
        key_ = decode_key(id_)
    except KeyDecodeException:
        return response.status_not_found()
    if not awss3key.is_folder(key_):
        return response.status_not_found()
    if not await _is_folder(request, volume_id, bucket_id, id_):
        return response.status_not_found()
    loop = asyncio.get_running_loop()

    async def publish_desktop_object_and_clear_cache(app: web.Application, desktop_object: DesktopObject,
                                                     appproperty_=HEA_MESSAGE_BROKER_PUBLISHER):
        invalidate_cache(request.app[HEA_CACHE], sub, key_, volume_id, bucket_id, invalidate_ancestors=True)
        await publish_desktop_object(app, desktop_object, appproperty_)
    return await util_delete_folder(request, volume_id, bucket_id, key_, loop, publish_desktop_object_and_clear_cache)


@routes.delete('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/root/items')
@routes.delete('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/root/items/')
async def delete_all_items_in_bucket(request: web.Request) -> web.Response:
    """
    Deletes all items in the specified bucket.

    :param request: the HTTP request.
    :return: No Content or Not Found.
    ---
    summary: All items deletion
    tags:
        - heaserver-files-aws-s3
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
        - name: delete_versions
          in: query
          required: false
          description: Also delete all versions.
          schema:
            type: boolean
          examples:
            example:
              summary: Delete all versions
              value: true
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    responses:
      '204':
        $ref: '#/components/responses/204'
      '404':
        $ref: '#/components/responses/404'
    """
    bucket_id = request.match_info['bucket_id']
    volume_id = request.match_info['volume_id']
    delete_versions = parse_bool(request.url.query.get('delete_versions', 'n'))
    async with DesktopObjectActionLifecycle(request=request,
                                            code='hea-delete',
                                            description=f'Deleting {bucket_id}',
                                            activity_cb=publish_desktop_object) as activity:
        async with S3ClientContext(request=request, volume_id=volume_id) as s3_client:
            try:
                await _delete_bucket_objects(s3_client, bucket_id, delete_versions=delete_versions)
                return await response.delete(True)
            except BotoClientError as e:
                raise awsservicelib.handle_client_error(e)

@routes.post('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/newfolder')
@routes.post('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/newfolder/')
async def post_new_folder(request: web.Request) -> web.Response:
    """
    Posts form for creating a new folder within this one.

    :param request: the HTTP request. Required.
    :return: the current folder, with a template for creating a child folder or Not Found if the requested item does not
    exist.
    ---
    summary: A folder.
    tags:
        - heaserver-awss3folders-folders
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
        return response.status_bad_request('folder is a required field')
    if folder.display_name is None:
        return response.status_bad_request("display_name is required")
    if '/' in folder.display_name:
        return response.status_bad_request(f"The item's display name may not have slashes in it")

    volume_id = request.match_info['volume_id']
    bucket_id = request.match_info['bucket_id']
    id_ = request.match_info['id']

    if id_ == awsservicelib.ROOT_FOLDER.id:
        item_folder_id = ''
    else:
        try:
            item_folder_id = decode_key(id_)
            if not awsservicelib.is_folder(item_folder_id):
                item_folder_id = None
        except KeyDecodeException:
            item_folder_id = None
    item_name = join(item_folder_id, folder.display_name)

    async with DesktopObjectActionLifecycle(request=request,
                                            code='hea-create',
                                            description=f'Creating folder {folder.display_name} in bucket {bucket_id}',
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
                raise response.status_bad_request(
                    body=f"{awsservicelib.s3_object_message_display_name(bucket_id, item_name)} already exists")
            except BotoClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == aws.CLIENT_ERROR_404:  # folder doesn't exist
                    try:
                        await loop.run_in_executor(None, partial(s3_client.put_object, Bucket=bucket_id, Key=item_name))
                        logger.debug('Added folder %s', item_name)
                        # Remove any stale metadata for the folder.
                        async with mongo.MongoContext(request) as mongo_client:
                            await mongo_client.delete_admin(MONGODB_AWS_S3_FOLDER_METADATA_COLLECTION,
                                                            mongoattributes={'bucket_id': bucket_id, 'encoded_key': encode_key(item_name)})
                        sub = request.headers.get(SUB, NONE_USER)
                        request.app[HEA_CACHE].pop((sub, volume_id, bucket_id, None, 'actual'), None)
                        if not (folder_id := encode_key(parent(item_name))):
                            folder_id = 'root'
                        request.app[HEA_CACHE].pop((sub, volume_id, bucket_id, folder_id, None, 'items'), None)
                        activity.new_volume_id = volume_id
                        activity.new_object_type_name = AWSS3Folder.get_type_name()
                        activity.new_object_id = encode_key(item_name)
                        activity.new_object_uri = f'volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{activity.new_object_id}'
                        activity.new_object_display_name = folder.display_name
                        if 'path' in request.url.query:
                            activity.new_context_dependent_object_path = request.url.query.getall('path')
                        return await response.post(request, encode_key(item_name),
                                                f"volumes/{volume_id}/buckets/{bucket_id}/awss3folders")
                    except BotoClientError as e2:
                        raise awsservicelib.handle_client_error(e2)
                elif error_code == aws.CLIENT_ERROR_NO_SUCH_BUCKET:
                    raise response.status_not_found()
                else:
                    raise response.status_bad_request(str(e))



@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/uploader')
@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/uploader/')
@action('heaserver-awss3folders-folder-upload-form')
@action(name='heaserver-awss3folders-folder-get-self', rel='self hea-self-container',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}')
async def get_folder_uploader_form(request: web.Request) -> web.Response:
    """
    Gets blank form for uploading to folder. Accepts "root" for the folder id, in which case you'll get a form for
    uploading to the root of the bucket.

    :param request: the HTTP request. Required.
    :return: a blank form for uploading a folder item or Not Found if the requested item does not
    exist.
    """
    context = aws.S3ObjectPermissionContext(request)
    if request.match_info['id'] == awsservicelib.ROOT_FOLDER.id:
        bucket: AWSBucket = AWSBucket()
        bucket.name = request.match_info['bucket_id']
        return await response.get(request, to_dict(bucket))
    else:
        return await _get_folder(request, context)


@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/newfolder')
@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/newfolder/')
@action('heaserver-awss3folders-folder-new-form')
@action(name='heaserver-awss3folders-folder-get-self', rel='self hea-self-container',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}')
async def get_new_folder_form(request: web.Request) -> web.Response:
    """
    Gets form for creating a new folder within this one.

    :param request: the HTTP request. Required.
    :return: the current folder, with a template for creating a child folder or Not Found if the requested item does not
    exist.
    ---
    summary: A folder.
    tags:
        - heaserver-awss3folders-folders
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
    return await _get_folder(request)


@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/creator')
@action('heaserver-awss3folders-folder-create-folder', rel='hea-creator hea-default application/x.folder',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/newfolder')
async def get_folder_creator(request: web.Request) -> web.Response:
    """
    Opens the requested folder.

    :param request: the HTTP request. Required.
    :return: the opened folder, or Not Found if the requested item does not exist.
    ---
    summary: Folder creator choices
    tags:
        - heaserver-awss3folders-folders
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
        folder_key = decode_key(folder_name)
    except KeyDecodeException as e:
        return response.status_not_found()

    async with DesktopObjectActionLifecycle(request=request,
                                            code='hea-get',
                                            description=f'Accessing {awsservicelib.s3_object_message_display_name(bucket_name, folder_key)}',
                                            activity_cb=publish_desktop_object) as activity:
        async with aws.S3ClientContext(request=request, volume_id=volume_id) as s3_client:
            try:
                folder = await _get_folder_helper(s3_client, request)
                if folder is None or not await _is_folder(request, volume_id, bucket_name, folder_name):
                    return response.status_not_found()
                activity.new_object_uri = f'volumes/{volume_id}/buckets/{bucket_name}/awss3folders/{folder_name}'
                activity.new_object_id = folder_name
                activity.new_object_type_name = AWSS3Folder.get_type_name()
                activity.new_volume_id = volume_id
                activity.new_object_display_name = display_name(folder_key)
                if 'path' in request.url.query:
                    activity.new_context_dependent_object_path = request.url.query.getall('path')
                return await response.get_multiple_choices(request)
            except BotoClientError as e:
                activity.status = Status.FAILED
                return awsservicelib.handle_client_error(e)
            except web.HTTPClientError as e:
                activity.status = Status.FAILED
                return e


@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/opener')
@action('heaserver-awss3folders-folder-open-default', rel='hea-opener hea-default application/x.folder',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/items/')
@action(name='heaserver-awss3folders-folder-open-as-zip',
        rel='hea-opener hea-downloader hea-default-downloader application/zip',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/content')
async def get_folder_opener(request: web.Request) -> web.Response:
    """
    Opens the requested folder.

    :param request: the HTTP request. Required.
    :return: the opened folder, or Not Found if the requested item does not exist.
    ---
    summary: Folder opener choices
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
      '300':
        $ref: '#/components/responses/300'
      '404':
        $ref: '#/components/responses/404'
    """
    logger = logging.getLogger(__name__)
    sub = request.headers.get(SUB, NONE_USER)
    volume_id = request.match_info['volume_id']
    bucket_name = request.match_info['bucket_id']
    folder_id = request.match_info['id']
    try:
        folder_key = decode_key(folder_id)
    except KeyDecodeException as e:
        return response.status_not_found()

    async with DesktopObjectActionLifecycle(request=request,
                                            code='hea-get',
                                            description=f'Accessing {awsservicelib.s3_object_message_display_name(bucket_name, folder_key)}',
                                            activity_cb=publish_desktop_object) as activity:
        cache_key = (sub, volume_id, bucket_name, folder_id, 'actual')
        cached_value = request.app[HEA_CACHE].get(cache_key)

        if cached_value:
            logger.debug('Getting cached value for %s: %s', cache_key, cached_value)
            activity.new_object_uri = f'volumes/{volume_id}/buckets/{bucket_name}/awss3folders/{folder_id}'
            activity.new_object_type_name = AWSS3Folder.get_type_name()
            activity.new_volume_id = volume_id
            activity.new_object_id = folder_id
            activity.new_object_display_name = display_name(folder_key)
            if 'path' in request.url.query:
                activity.new_context_dependent_object_path = request.url.query.getall('path')
            return await response.get_multiple_choices(request)
        else:
            logger.debug('Going to S3 for %s', cache_key)
            async with aws.S3ClientContext(request=request, volume_id=volume_id) as s3_client:
                try:
                    folder, is_folder = await asyncio.gather(_has_folder_helper(s3_client, request),
                                                             _is_folder(request, volume_id, bucket_name, folder_id))
                    if not folder or not is_folder:
                        return response.status_not_found()

                    activity.new_object_uri = f'volumes/{volume_id}/buckets/{bucket_name}/awss3folders/{folder_id}'
                    activity.new_object_type_name = AWSS3Folder.get_type_name()
                    activity.new_volume_id = volume_id
                    activity.new_object_id = folder_id
                    activity.new_object_display_name = display_name(folder_key)
                    if 'path' in request.url.query:
                        activity.new_context_dependent_object_path = request.url.query.getall('path')

                    return await response.get_multiple_choices(request)
                except BotoClientError as e:
                    activity.status = Status.FAILED
                    return awsservicelib.handle_client_error(e)
                except web.HTTPClientError as e:
                    activity.status = Status.FAILED
                    return e


async def message_broker_connection_failed(exc_info: Exception):
    global _message_broker_failed
    logger = logging.getLogger(__name__)
    logger.error('Message broker connection failed', exc_info=exc_info)
    _message_broker_failed = True


def start_with(config: Configuration):
    start(package_name='heaserver-folders-aws-s3',
          db=opensearch.S3MongoOpenSearchMananger, wstl_builder_factory=builder_factory(__package__),
          cleanup_ctx=[publisher_cleanup_context_factory(config),
                       subscriber_cleanup_context_factory(message_body_cb=search_item_cb, config=config,
                                                          topics=[AWSS3SearchItemInFolder.get_type_name()])],
          config=config)



async def search_item_cb(app: web.Application, desktop_object: DesktopObject):
    async with _put_lock:
        logger = logging.getLogger(__name__)
        headers_ = {SUB: CREDENTIALS_MANAGER_USER}
        session = app[appproperty.HEA_CLIENT_SESSION]
        if not session:
            logger.error("session does not exist ")
            return
        if isinstance(desktop_object, AWSS3SearchItemInFolder):
            s3_item = cast(AWSS3SearchItemInFolder, desktop_object)
            search_item_id = desktop_object.id
            obj_path = desktop_object.path
        if search_item_id is None:
            raise ValueError('search__id cannot be None')


        try:
            # Assumes path is like "/bucket-name/path/to/object"
            if obj_path is None:
                raise ValueError("obj_path cannot be None")

            bucket_id = s3_item.bucket_id
            component = await client.get_component_by_name(app, 'heaserver-folders-aws-s3', client_session=session)
            assert component is not None, 'registry entry for heaserver-folders-aws-s3 not found'
            assert component.base_url is not None, 'registry entry for heaserver-folders-aws-s3 has no base_url'

            if not s3_item or not s3_item.account_id or not s3_item.id or not bucket_id:
                raise ValueError(" account_id or s3_item.id or bucket_name  cannot be None")
            await client.delete(app, URL(component.base_url)/'awsaccounts'/s3_item.account_id /'buckets' /bucket_id /'s3keys'/s3_item.id/ 'internal', headers=headers_)

        except ClientResponseError as e:
            if e.status == 404:
                logger.debug("search item will not be deleted")
        except Exception as ex:
            logger.error("Unexpected error ", exc_info=ex)
            raise ex



@routes.delete('/awsaccounts/{account_id}/buckets/{bucket_id}/s3keys/{id}/internal')
async def _delete_object_index_doc(request: web.Request) -> web.Response:
    logger = logging.getLogger(__name__)

    try:
        account_id = request.match_info['account_id']
        bucket_name = request.match_info['bucket_id']
        obj_id = request.match_info['id']
    except KeyError as e:
        return response.status_bad_request(str(e))

    try:
        obj_key: str | None = decode_key(obj_id).removeprefix(f"/{bucket_name}/")
    except KeyDecodeException:
        logger.debug('Unable to decode key: %s', obj_id)
        return response.status_not_found()

    try:
        # account_prop: Property = await request.app[HEA_DB].get_property(app=request.app, name="AWS_ROOT_ACCOUNT")
        role_arn = f"arn:aws:iam::{account_id}:role/"
        aws_cred = AWSCredentials()
        aws_cred.role = role_arn
        admin_cred: AWSCredentials = await request.app[HEA_DB].elevate_privileges(request, aws_cred)

        async with aws.S3ClientContext(request=request, credentials=admin_cred) as s3_client:
            try:
                versions = None
                if obj_key:
                    versions = await asyncio.get_running_loop().run_in_executor(
                        None, lambda: s3_client.list_object_versions(Bucket=bucket_name, Prefix=obj_key)
                    )
                object_versions = versions.get("Versions", []) if versions else []
                if not object_versions:
                    logger.debug("No versions found for key %s deleting record in index", obj_key)
                    if await opensearchlib.delete(request=request, item_id = obj_id):
                        logger.debug("Deleted key %s", obj_key)
                        return response.status_no_content()

                return response.status_not_found()  # 200 with no content

            except BotoClientError as e:
                logger.error("S3 client error: %s", str(e))
                return awsservicelib.handle_client_error(e)

    except ClientResponseError as ce:
        logger.error("Client response error: %s", str(ce))
        return response.status_generic(status=ce.status, body=str(ce))
    except Exception as e:
        logger.exception("Unexpected error while checking S3 object existence")
        return response.status_generic(500, "Internal error")


async def _get_folder(request: web.Request, context: PermissionContext | None = None) -> web.Response:
    """
    Gets the folder with the specified id.

    :param request: the HTTP request.
    :return: the requested folder or Not Found.
    """
    logger = logging.getLogger(__name__)
    logger.debug('Getting folder from request %s', request)
    sub = request.headers.get(SUB, NONE_USER)
    try:
        volume_id = request.match_info['volume_id']
        bucket_name = request.match_info['bucket_id']
        folder_id = request.match_info['id'] if 'id' in request.match_info else request.match_info['name']
    except KeyError as e:
        return response.status_bad_request(str(e))

    try:
        folder_key: str | None = decode_key(folder_id)
    except KeyDecodeException as e:
        logger.debug('No folder with id or name %s', folder_id)
        folder_key = None

    async with DesktopObjectActionLifecycle(request=request,
                                            code='hea-get',
                                            description=f'Accessing {awsservicelib.s3_object_message_display_name(bucket_name, folder_key or 'an object')}',
                                            activity_cb=publish_desktop_object) as activity:
        if folder_key is None:
            async with aws.S3ClientContext(request=request, volume_id=volume_id) as s3_client:
                raise await when_object_not_found(s3_client, bucket_name)
        include_data = parse_bool(request.url.query.get('data') or 'true')
        cache_key = (sub, volume_id, bucket_name, folder_id, 'actual')
        if context and (cached_value := request.app[HEA_CACHE].get(cache_key)):
            logger.debug('Getting cached value for %s', cache_key)
            data, perms, attr_perms = cached_value
            activity.new_volume_id = volume_id
            activity.new_object_id = folder_id
            activity.new_object_type_name = AWSS3Folder.get_type_name()
            activity.new_object_uri = f'volumes/{volume_id}/buckets/{bucket_name}/awss3folders/{folder_id}'
            activity.new_object_display_name = display_name(folder_key)
            if 'path' in request.url.query:
                activity.new_context_dependent_object_path = request.url.query.getall('path')
            return await response.get(request, data, permissions=perms, attribute_permissions=attr_perms,
                                      include_data=include_data)
        else:
            if include_data:
                async with aws.S3ClientContext(request=request, volume_id=volume_id) as s3_client:
                    try:
                        folder, is_folder = await asyncio.gather(_get_folder_helper(s3_client, request),
                                                                _is_folder(request, volume_id, bucket_name, folder_id))
                        if not is_folder:
                            logger.debug('No folder with id or name %s', folder_id)
                            activity.status = Status.FAILED
                            return await response.get(request, None)

                        activity.new_volume_id = volume_id
                        activity.new_object_id = folder_id
                        activity.new_object_type_name = AWSS3Folder.get_type_name()
                        activity.new_object_uri = f'volumes/{volume_id}/buckets/{bucket_name}/awss3folders/{folder_id}'
                        activity.new_object_display_name = display_name(folder_key)
                        if 'path' in request.url.query:
                            activity.new_context_dependent_object_path = request.url.query.getall('path')
                        if context:
                            share = await folder.get_permissions_as_share(context)
                            folder.add_user_share(share)
                            attr_perms = await folder.get_all_attribute_permissions(context)
                            perms = share.permissions
                        else:
                            perms = attr_perms = None
                        folder_dict = to_dict(folder)
                        logger.debug('Setting cache for %s', cache_key)
                        if context:
                            request.app[HEA_CACHE][cache_key] = (folder_dict, perms, attr_perms)
                        return await response.get(request, folder_dict,
                                                  permissions=perms, attribute_permissions=attr_perms,
                                                  include_data=True)
                    except BotoClientError as e:
                        activity.status = Status.FAILED
                        return awsservicelib.handle_client_error(e)
                    except web.HTTPClientError as e:
                        activity.status = Status.FAILED
                        return e
            else:
                if await _is_folder(request, volume_id, bucket_name, folder_id):
                    folder_dict_: DesktopObjectDict | None = {'id': folder_id, 'type': AWSS3Folder.get_type_name()}
                else:
                    folder_dict_ = None
                return await response.get(request, folder_dict_, include_data=False)


def _new_folder(bucket_name: str, obj: Mapping[str, Any], encoded_key: str,
                request: web.Request, sub = NONE_USER) -> AWSS3Folder:
    folder = AWSS3Folder()
    folder.id = encoded_key
    folder.owner = AWS_USER
    folder.bucket_id = bucket_name
    folder.source = AWS_S3
    folder.source_detail = AWS_S3
    return folder


async def _get_folder_helper(s3_client: S3Client, request: web.Request) -> AWSS3Folder:
    logger = logging.getLogger(__name__)
    try:
        bucket_name = request.match_info['bucket_id']
        folder_id = request.match_info['id'] if 'id' in request.match_info else request.match_info['name']
    except KeyError as e:
        raise ValueError(str(e))

    try:
        folder_key: str | None = decode_key(folder_id)
        if not awsservicelib.is_folder(folder_key):
            folder_key = None
    except KeyDecodeException:
        # Let the bucket query happen so that we consistently return Forbidden if the user lacks permissions
        # for the bucket.
        folder_key = None
    loop = asyncio.get_running_loop()
    def get_object() -> ListObjectsV2OutputTypeDef:
        if folder_key is None:
            logger.debug('folder_key is None')
            # We couldn't decode the folder_id, and we need to check if the user can access the bucket in order to
            # decide which HTTP status code to respond with (Forbidden vs Not Found).
            s3_client.head_bucket(Bucket=bucket_name)
            raise web.HTTPNotFound
        return s3_client.list_objects_v2(Bucket=bucket_name, Prefix=folder_key, MaxKeys=1)
    response_ = await loop.run_in_executor(None, get_object)
    logging.debug('Result of list_objects_v2: %s', response_)
    if folder_key is None or response_['KeyCount'] == 0:
        raise web.HTTPNotFound
    contents = response_['Contents'][0]
    encoded_key = encode_key(response_['Prefix'])
    return _new_folder(bucket_name, contents, encoded_key, request)


async def _has_folder_helper(s3_client: S3Client, request: web.Request) -> bool:
    logger = logging.getLogger(__name__)
    try:
        bucket_name = request.match_info['bucket_id']
        folder_id = request.match_info['id'] if 'id' in request.match_info else request.match_info['name']
    except KeyError as e:
        raise ValueError(str(e))

    try:
        folder_key: str | None = decode_key(folder_id)
        if not awsservicelib.is_folder(folder_key):
            folder_key = None
    except KeyDecodeException:
        # Let the bucket query happen so that we consistently return Forbidden if the user lacks permissions
        # for the bucket.
        folder_key = None
    loop = asyncio.get_running_loop()
    def get_object() -> ListObjectsV2OutputTypeDef:
        if folder_key is None and folder_id != awsservicelib.ROOT_FOLDER.id:
            logger.debug('folder_key is None')
            # We couldn't decode the folder_id, and we need to check if the user can access the bucket in order to
            # decide which HTTP status code to respond with (Forbidden vs Not Found).
            s3_client.head_bucket(Bucket=bucket_name)
            raise response.status_not_found()
        return s3_client.list_objects_v2(Bucket=bucket_name, Prefix=folder_key or '', MaxKeys=1)
    response_ = await loop.run_in_executor(None, get_object)
    logging.debug('Result of list_objects_v2: %s', response_)
    if folder_key is None and folder_id != awsservicelib.ROOT_FOLDER.id:
        return False
    return True


def _check_folder_and_object_keys(folder_id_: str, request: web.Request) -> tuple[str | None, str | None, bool]:
    folder_or_item_not_found = False
    decoded_folder_key = awsservicelib.decode_folder(folder_id_)
    if decoded_folder_key is None:
        folder_or_item_not_found = True
    try:
        decoded_key = decode_key(request.match_info['id'])
        if not is_object_in_folder(decoded_key, decoded_folder_key):
            folder_or_item_not_found = True
    except KeyDecodeException as e:
        decoded_key = None
        folder_or_item_not_found = True

    return decoded_folder_key, decoded_key, folder_or_item_not_found


async def _get_folder_move_template(request: web.Request) -> web.Response:
    context = aws.S3ObjectPermissionContext(request)
    return await _get_folder(request, context)


async def _is_folder(request: web.Request, volume_id: str, bucket_id: str, encoded_key: str):
    async with mongo.MongoContext(request=request) as mongo_client:
        metadata_dict = await awsservicelib.get_metadata(mongo_client, bucket_id, encoded_key)
        if metadata_dict and metadata_dict['actual_object_type_name'] != AWSS3Folder.get_type_name():
            return False
    return True


async def _delete_bucket_objects(s3_client: S3Client, bucket_name: str, delete_versions=False) -> None:
    """
    Deletes all objects inside a bucket, assuming the bucket exists.

    :param request: the aiohttp Request (required).
    :param volume_id: the id string of the volume representing the user's AWS account.
    :param bucket_name: Bucket to delete
    :param delete_versions: Boolean indicating if the versioning should be deleted as well, defaults to False. For
    versioned buckets, this flag must be set to True or subsequently attempting to delete the bucket will fail.
    :raises BotoClientError: if the bucket does not exist, or another error occurred while deleting the bucket's
    contents.
    """
    loop = asyncio.get_running_loop()
    if delete_versions:
        bucket_versioning = await loop.run_in_executor(None, partial(s3_client.get_bucket_versioning, Bucket=bucket_name))
        if bucket_versioning['Status'] in ('Enabled', 'Suspended'):
            delete_marker_list: list[ObjectIdentifierTypeDef] = []
            version_list: list[ObjectIdentifierTypeDef] = []
            async for page in awsservicelib.list_object_versions_and_delete_markers(s3_client, bucket_name):
                if 'DeleteMarkers' in page:
                    for delete_marker in page['DeleteMarkers']:
                        delete_marker_list.append({'Key': delete_marker['Key'], 'VersionId': delete_marker['VersionId']})

                if 'Versions' in page:
                    for version in page['Versions']:
                        version_list.append({'Key': version['Key'], 'VersionId': version['VersionId']})

            for i in range(0, len(delete_marker_list), 1000):
                await loop.run_in_executor(None, partial(s3_client.delete_objects,
                    Bucket=bucket_name,
                    Delete={
                        'Objects': delete_marker_list[i:i+1000],
                        'Quiet': True
                    }
                ))

            for i in range(0, len(version_list), 1000):
                await loop.run_in_executor(None, partial(s3_client.delete_objects,
                    Bucket=bucket_name,
                    Delete={
                        'Objects': version_list[i:i+1000],
                        'Quiet': True
                    }
                ))
        else:
            object_list: list[ObjectIdentifierTypeDef] = []
            async for object in awsservicelib.list_objects(s3_client, bucket_name):
                object_list.append({'Key': object['Key']})
            for i in range(0, len(object_list), 1000):
                delete_: DeleteTypeDef = {
                    'Objects': object_list[i:i+1000],
                    'Quiet': True
                }
                await loop.run_in_executor(None, partial(s3_client.delete_objects, Bucket=bucket_name, Delete=delete_))
    else:
        object_list = []
        async for object in awsservicelib.list_objects(s3_client, bucket_name):
            object_list.append({'Key': object['Key']})
        for i in range(0, len(object_list), 1000):
            delete_ = {
                'Objects': object_list[i:i+1000],
                'Quiet': True
            }
            await loop.run_in_executor(None, partial(s3_client.delete_objects, Bucket=bucket_name, Delete=delete_))
