from json import JSONDecodeError
from heaobject.data import AWSS3FileObject, ClipboardData
from heaobject.user import AWS_USER, NONE_USER
from heaobject.aws import S3StorageClass, S3Version
from heaobject.awss3key import KeyDecodeException, decode_key, encode_key, is_root, parent, split, is_folder, display_name
from heaobject.root import DesktopObjectDict, Tag, Permission, to_dict
from heaobject.activity import Status
from heaobject.util import now
from heaserver.service.util import to_http_date
from heaserver.service.activity import DesktopObjectActionLifecycle
from heaserver.service.oidcclaimhdrs import SUB
from heaserver.service.heaobjectsupport import new_heaobject_from_type
from heaserver.service.appproperty import HEA_COMPONENT, HEA_CACHE
from heaserver.service.runner import init_cmd_line, routes, start
from heaserver.service.db.aws import S3Manager, S3ClientContext, S3ObjectPermissionContext
from heaserver.service.db.mongo import MongoContext
from heaserver.service.wstl import builder_factory, action
from heaserver.service.messagebroker import publisher_cleanup_context_factory, publish_desktop_object
from heaserver.service import response
from heaobject.mimetype import guess_mime_type
from heaserver.service.aiohttp import RequestFileLikeWrapper, extract_sort, SortOrder
from aiohttp import web, hdrs, client_exceptions
from aiohttp.helpers import ETag
import logging
from typing import Any
from functools import partial
import asyncio
from botocore.exceptions import ClientError as BotoClientError
from mypy_boto3_s3.client import S3Client
from mypy_boto3_s3.type_defs import TagTypeDef
from collections.abc import Mapping, Coroutine
from .util import S3ObjectVersionPermissionContext, clear_target_in_cache, move, create_presigned_url_credentials, when_object_not_found, get_database, \
extract_expiration, rename, invalidate_cache, set_s3_storage_status
from . import awsservicelib
from yarl import URL


@routes.route('OPTIONS', '/volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id}')
async def get_file_options(request: web.Request) -> web.Response:
    """
    Gets the allowed HTTP methods for a file resource.

    :param request: the HTTP request (required).
    :return: the HTTP response.
    ---
    summary: Allowed HTTP methods.
    tags:
        - heaserver-files-aws-s3
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


@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id}/duplicator')
@action(name='heaserver-awss3files-file-duplicate-form')
@action('heaserver-awss3files-file-get-self', rel='self', path='volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id}')
async def get_file_duplicator(request: web.Request) -> web.Response:
    """
    Gets a form template for duplicating the requested file.

    :param request: the HTTP request. Required.
    :return: the requested form, or Not Found if the requested file was not found.
    """
    logger = logging.getLogger(__name__)
    try:
        return await _get_file(request)
    except KeyDecodeException as e:
        logger.exception('Error getting parent key')
        return response.status_bad_request(f'Error getting parent folder: {e}')


@routes.post('/volumes/{volume_id}/buckets/{bucket_id}/awss3files')
@routes.post('/volumes/{volume_id}/buckets/{bucket_id}/awss3files/')
async def post_file(request: web.Request) -> web.Response:
    """
    Creates a new file.

    :param request: the HTTP request. The body of the request is expected to be a file.
    :return: the response, with a 201 status code if a file was created or a 400 if not. If a folder was created, the
    Location header will contain the URL of the created file.
    ---
    summary: A specific file.
    tags:
        - heaserver-folders-folders
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
    resp = await awsservicelib.create_object(request, AWSS3FileObject)
    if resp.status == 201:
        request.app[HEA_CACHE].clear()
    return resp


@routes.put('/volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id}')
async def put_file(request: web.Request) -> web.Response:
    """
    Updates file metadata.

    :param request: the HTTP request. The body of the request is expected to be a file.
    :return: the response, with a 201 status code if a file was created or a 400 if not. If a folder was created, the
    Location header will contain the URL of the created file.
    ---
    summary: A specific file.
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
        - $ref: '#/components/parameters/id'
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    requestBody:
        description: A new file object.
        required: true
        content:
            application/vnd.collection+json:
              schema:
                type: object
              examples:
                example:
                  summary: File example
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
                        "value": "heaobject.data.AWSS3FileObject"
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
                    "tags": [],
                    "version": null
                  }
    responses:
      '204':
        $ref: '#/components/responses/204'
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
        return response.status_bad_request(f'Invalid id {id_}')

    try:
        file = await new_heaobject_from_type(request, AWSS3FileObject)
    except TypeError:
        return response.status_bad_request(f'Expected type {AWSS3FileObject}; actual object was {await request.text()}')
    if file.key is None:
        return response.status_bad_request(f'file.key cannot be None')

    async with DesktopObjectActionLifecycle(request=request,
                                            code='hea-update',
                                            description=f'Updating {awsservicelib.s3_object_message_display_name(bucket_id, key)}',
                                            activity_cb=publish_desktop_object) as activity:
        activity.old_object_id = id_
        activity.old_object_type_name = AWSS3FileObject.get_type_name()
        activity.old_volume_id = volume_id
        activity.old_object_uri = f'volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id_}'
        activity.old_object_display_name = split(key)[1]
        if 'path' in request.url.query:
            activity.old_context_dependent_object_path = request.url.query.getall('path')
        async with S3ClientContext(request=request, volume_id=volume_id) as s3_client:
            try:
                loop = asyncio.get_running_loop()
                sub = request.headers.get(SUB, NONE_USER)
                if key != file.key:
                    if (response_ := await rename(activity, request, None, sub, volume_id, bucket_id, id_, key, file, AWSS3FileObject, request.url.query.getall('path'))).status != 204:
                        activity.status = Status.FAILED
                        return response_
                parent_key = parent(key)
                folder_id = 'root' if is_root(parent_key) else encode_key(parent_key)
                await loop.run_in_executor(None, partial(s3_client.delete_object_tagging, Bucket=bucket_id, Key=file.key))
                await loop.run_in_executor(None, partial(s3_client.put_object_tagging, Bucket=bucket_id, Key=file.key, Tagging={'TagSet': await _to_aws_tags(file.tags)}))
                request.app[HEA_CACHE].pop((sub, volume_id, bucket_id, folder_id, id_, 'items'), None)
                request.app[HEA_CACHE].pop((sub, volume_id, bucket_id, folder_id, None, 'items'), None)
                request.app[HEA_CACHE].pop((sub, volume_id, bucket_id, id_, 'actual'), None)
                request.app[HEA_CACHE].pop((sub, volume_id, bucket_id, None, 'actual'), None)
                activity.new_object_id = id_
                activity.new_object_type_name = AWSS3FileObject.get_type_name()
                activity.new_volume_id = volume_id
                activity.new_object_uri = f'volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id_}'
                activity.new_context_dependent_object_path = activity.old_context_dependent_object_path
                activity.new_object_display_name = file.display_name
            except BotoClientError as e:
                activity.status = Status.FAILED
                return awsservicelib.handle_client_error(e)

    return await response.put(True)


@routes.post('/volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id}/archive')
async def post_file_archive(request: web.Request) -> web.Response:
    """
    Posts the provided file to archive it.

    :param request: the HTTP request.
    :return: a Response object with a status of No Content.
    ---
    summary: A specific file.
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
        - $ref: '#/components/parameters/id'
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    requestBody:
        description: The new name of the file and target for archiving it.
        required: true
        content:
            application/vnd.collection+json:
              schema:
                type: object
              examples:
                example:
                  summary: The new name of the file and target for archiving it.
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
                  summary: The storage class to archive object to.
                  value: {
                    "storage_class": "DEEP_ARCHIVE"
                  }
    responses:
      '204':
        $ref: '#/components/responses/204'
      '400':
        $ref: '#/components/responses/400'
      '404':
        $ref: '#/components/responses/404'
    """
    try:
        return await awsservicelib.archive_object(request)
    finally:
        id_ = request.match_info['id']
        volume_id = request.match_info['volume_id']
        bucket_id = request.match_info['bucket_id']
        sub = request.headers.get(SUB, NONE_USER)
        try:
            key: str | None = decode_key(id_)
        except KeyDecodeException:
            return response.status_not_found()
        parent_key = parent(key)
        folder_id = 'root' if is_root(parent_key) else encode_key(parent_key)
        request.app[HEA_CACHE].pop((sub, volume_id, bucket_id, folder_id, id_, 'items'), None)
        request.app[HEA_CACHE].pop((sub, volume_id, bucket_id, folder_id, None, 'items'), None)
        request.app[HEA_CACHE].pop((sub, volume_id, bucket_id, id_, 'actual'), None)
        request.app[HEA_CACHE].pop((sub, volume_id, bucket_id, None, 'actual'), None)


@routes.post('/volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id}/mover')
async def post_file_mover(request: web.Request) -> web.Response:
    """
    Posts the provided file to move it.

    :param request: the HTTP request.
    :return: a Response object with a status of No Content.
    ---
    summary: A specific file.
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
        - $ref: '#/components/parameters/id'
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    requestBody:
        description: The new name of the file and target for moving it.
        required: true
        content:
            application/vnd.collection+json:
              schema:
                type: object
              examples:
                example:
                  summary: The new name of the file and target for moving it.
                  value: {
                    "template": {
                      "data": [
                      {
                        "name": "target",
                        "value": "http://localhost:8080/volumes/666f6f2d6261722d71757578/buckets/my-bucket/awss3files/"
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
    volume_id = request.match_info['volume_id']
    bucket_id = request.match_info['bucket_id']
    id_ = request.match_info['id']
    target_url, target_bucket_name, target_key_parent, target_volume_id, _ = await awsservicelib._copy_object_extract_target(await request.json())
    sub = request.headers.get(SUB, NONE_USER)
    try:
        key = decode_key(id_)
    except KeyDecodeException as e:
        return response.status_bad_request(f'Invalid id {id_}')

    async with DesktopObjectActionLifecycle(request=request,
                                            code='hea-move',
                                            description=f'Moving {awsservicelib.s3_object_message_display_name(bucket_id, key)} to {awsservicelib.s3_object_message_display_name(target_bucket_name, target_key_parent)}',
                                            activity_cb=publish_desktop_object) as activity:
        parent_key = parent(key)
        try:
            if 'path' in (target_url_:=URL(target_url)).query:
                target_path: list[str] | None = target_url_.query.getall('path')
            else:
                target_path = None
            return await move(activity, request, None, sub, volume_id, bucket_id, id_, key, target_volume_id,
                              target_bucket_name, target_key_parent, AWSS3FileObject, target_path)
        except:
            logging.exception('Error moving file %s to %s', key, target_key_parent)
            raise
        finally:
            await clear_target_in_cache(request)
            folder_id = 'root' if is_root(parent_key) else encode_key(parent_key)
            request.app[HEA_CACHE].pop((sub, volume_id, bucket_id, None, 'actual'), None)
            request.app[HEA_CACHE].pop((sub, volume_id, bucket_id, id_, 'actual'), None)
            request.app[HEA_CACHE].pop((sub, volume_id, bucket_id, folder_id, None, 'items'), None)
            request.app[HEA_CACHE].pop((sub, volume_id, bucket_id, folder_id, id_, 'items'), None)

@routes.post('/volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id}/unarchive')
async def unarchive_file(request: web.Request) -> web.Response:
    """

    :param request:
    :return: a Response object with status 202 Accept

    ---
    summary: A specific file.
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
    try:
        return await awsservicelib.unarchive_object(request=request, activity_cb=publish_desktop_object,
                                                    error_if_not_restorable=True)
    finally:
        id_ = request.match_info['id']
        volume_id = request.match_info['volume_id']
        bucket_id = request.match_info['bucket_id']
        sub = request.headers.get(SUB, NONE_USER)
        try:
            key: str | None = decode_key(id_)
        except KeyDecodeException:
            return response.status_not_found()
        parent_key = parent(key)
        folder_id = 'root' if is_root(parent_key) else encode_key(parent_key)
        request.app[HEA_CACHE].pop((sub, volume_id, bucket_id, folder_id, id_, 'items'), None)
        request.app[HEA_CACHE].pop((sub, volume_id, bucket_id, folder_id, None, 'items'), None)
        request.app[HEA_CACHE].pop((sub, volume_id, bucket_id, id_, 'actual'), None)
        request.app[HEA_CACHE].pop((sub, volume_id, bucket_id, None, 'actual'), None)


@routes.post('/volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id}/duplicator')
async def post_file_duplicator(request: web.Request) -> web.Response:
    """
    Posts the provided file for duplication.

    :param request: the HTTP request.
    :return: a Response object with a status of Created and the object's URI in the
    ---
    summary: A specific file.
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
        - $ref: '#/components/parameters/id'
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    requestBody:
        description: The new name of the file and target for duplicating it.
        required: true
        content:
            application/vnd.collection+json:
              schema:
                type: object
              examples:
                example:
                  summary: The new name of the file and target for duplicating it.
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
                  summary: The new name of the file and target for moving it.
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
    try:
        return await awsservicelib.copy_object(request, activity_cb=publish_desktop_object)
    finally:
        await clear_target_in_cache(request)


@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id}/mover')
@action(name='heaserver-awss3files-file-move-form')
@action('heaserver-awss3files-file-get-self', rel='self', path='volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id}')
async def get_file_mover(request: web.Request) -> web.Response:
    """
    Gets a form template for moving the requested file.

    :param request: the HTTP request. Required.
    :return: the requested form, or Not Found if the requested file was not found.
    ---
    summary: A specific file.
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
    return await _get_file_move_template(request)


@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id}/archive')
@action(name='heaserver-awss3files-file-archive-form')
@action('heaserver-awss3files-file-get-self', rel='self', path='volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id}')
async def get_file_archive(request: web.Request) -> web.Response:
    """
    Gets a form template for archiving the requested file.

    :param request: the HTTP request. Required.
    :return: the requested form, or Not Found if the requested file was not found.
    ---
    summary: A specific file.
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
    return await _get_file_move_template(request)


@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id}/unarchive')
@action(name='heaserver-awss3files-file-unarchive-form-glacier', itemif='storage_class == "GLACIER"')
@action(name='heaserver-awss3files-file-unarchive-form-deep-archive', itemif='storage_class == "DEEP_ARCHIVE"')
@action('heaserver-awss3files-file-get-self', rel='self', path='volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id}')
async def get_file_unarchive_form(request: web.Request) -> web.Response:
    """
    Gets a form template for unarchiving the requested file.

    :param request: the HTTP request. Required.
    :return: the requested form, or Not Found if the requested file was not found.
    ---
    summary: Get a specific file to unarchive.
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
    return await _get_file_move_template(request, include_data=False)


@routes.put('/volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id}/content')
async def put_file_content(request: web.Request) -> web.Response:
    """
    Updates the content of the requested file.
    :param request: the HTTP request. Required.
    :return: a Response object with the value No Content or Not Found.
    ---
    summary: File content
    tags:
        - heaserver-files-aws-s3
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
        description: File contents.
        required: true
        content:
            application/octet-stream:
                schema:
                    type: string
                    format: binary
    responses:
      '204':
        $ref: '#/components/responses/204'
      '404':
        $ref: '#/components/responses/404'
    """
    return await _put_object_content(request)


@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id}/content')
async def get_file_content(request: web.Request) -> web.StreamResponse:
    """
    :param request:
    :return:
    ---
    summary: File content
    tags:
        - heaserver-files-aws-s3
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
    logger = logging.getLogger(__name__)
    volume_id = request.match_info['volume_id']
    bucket_name = request.match_info['bucket_id']
    file_name = request.match_info['id']

    try:
        key: str | None = decode_key(file_name)
        if awsservicelib.is_folder(key):
            key = None
    except KeyDecodeException:
        # Let the bucket query happen so that we consistently return Forbidden if the user lacks permissions
        # for the bucket.
        key = None

    async with DesktopObjectActionLifecycle(request=request,
                                            code='hea-get',
                                            description=f'Getting {awsservicelib.s3_object_message_display_name(bucket_name, key)} content',
                                            activity_cb=publish_desktop_object) as activity:
        async with S3ClientContext(request=request, volume_id=volume_id) as s3_client:
            loop = asyncio.get_running_loop()
            try:
                if key is None:
                    # We couldn't decode the file_id, and we need to check if the user can access the bucket in order to
                    # decide which HTTP status code to respond with (Forbidden vs Not Found).
                    await loop.run_in_executor(None, partial(s3_client.head_bucket, Bucket=bucket_name))
                    raise response.status_not_found()
                logger.debug('Checking storage class')
                resp = await loop.run_in_executor(None, partial(s3_client.head_object, Bucket=bucket_name, Key=key))
                logger.debug('Got response from head_object: %s', resp)
                storage_class = resp.get('StorageClass', S3StorageClass.STANDARD.name)
                if storage_class in (S3StorageClass.DEEP_ARCHIVE.name, S3StorageClass.GLACIER.name) and ((restore := resp.get('Restore')) is None or 'expiry-date' not in restore):
                    raise response.status_internal_error(f'Cannot access {awsservicelib.s3_object_message_display_name(bucket_name, key)} because it is archived in {S3StorageClass[storage_class].display_name}. Unarchive it and try again.')
                etag = resp['ETag'].strip('"')
                last_modified = resp['LastModified']
                if request.if_none_match and ETag(etag) in request.if_none_match:
                    return web.HTTPNotModified()
                if request.if_modified_since and last_modified and request.if_modified_since >= last_modified:
                    return web.HTTPNotModified()
                mode = request.url.query.get('mode', 'download')
                if mode not in ('download', 'open'):
                    raise response.status_bad_request(f'Invalid mode {mode}')
                logger.debug('Getting content of object %s', resp)
                mime_type = guess_mime_type(key)
                if mime_type is None:
                    mime_type = 'application/octet-stream'
                response_ = web.StreamResponse(status=200, reason='OK',
                                               headers={hdrs.CONTENT_DISPOSITION: f'{"attachment" if mode == "download" else "inline"}; filename={key.split("/")[-1]}',
                                                        hdrs.CONTENT_TYPE: mime_type,
                                                        hdrs.LAST_MODIFIED: to_http_date(last_modified),
                                                        # hdrs.CONTENT_LENGTH: str(resp['ContentLength']),
                                                        hdrs.ETAG: etag})

                await response_.prepare(request)
                logger.debug('After initialize')
                obj_getter = s3_client.get_object(Bucket=bucket_name, Key=key)
                body = obj_getter['Body']
                try:
                    while True:
                        chunk = await loop.run_in_executor(None, body.read, 1024*10)
                        if not chunk:
                            break
                        await response_.write(chunk)
                    await response_.write_eof()
                except client_exceptions.ClientConnectionResetError:
                    logger.info('Lost connection with the browser downloading %s, probably because the user closed/refreshed their tab or lost their internet connection', key)
                finally:
                    body.close()
                logger.debug('Content length is %s bytes', response_.content_length)
                return response_
            except BotoClientError as e:
                raise awsservicelib.handle_client_error(e)


@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id}')
@action('heaserver-awss3files-file-get-open-choices', rel='hea-opener-choices hea-context-menu hea-downloader',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id}/opener',
        itemif='retrievable == True')
@action(name='heaserver-awss3files-file-get-properties', rel='hea-properties hea-context-menu')
@action(name='heaserver-awss3files-file-duplicate', rel='hea-dynamic-standard hea-icon-duplicator hea-context-menu',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id}/duplicator')
@action(name='heaserver-awss3files-file-move', rel='hea-dynamic-standard hea-icon-mover hea-context-menu',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id}/mover')
@action(name='heaserver-awss3files-file-unarchive', rel='hea-dynamic-standard hea-unarchive hea-context-menu',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id}/unarchive', itemif="archive_detail_state == 'ARCHIVED' and not retrievable")
@action(name='heaserver-awss3files-file-archive', rel='hea-dynamic-standard hea-archive hea-context-menu',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id}/archive', itemif="not archive_storage_class")
@action(name='heaserver-awss3files-file-get-trash', rel='hea-trash hea-context-menu',
        path='volumes/{volume_id}/awss3trash')
@action(name='heaserver-awss3files-file-get-presigned-url', rel='hea-dynamic-clipboard hea-icon-for-clipboard hea-context-menu',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id}/presignedurl', itemif="retrievable == True")
@action(name='heaserver-awss3files-file-get-versions', rel='hea-versions hea-context-menu', itemif="version is not None",
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id}/versions/?sort=desc')
@action('heaserver-awss3files-file-get-self', rel='self', path='volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id}')
@action(name='heaserver-awss3files-file-get-volume', rel='hea-volume', path='volumes/{volume_id}')
@action(name='heaserver-awss3files-file-get-awsaccount', rel='hea-account', path='volumes/{volume_id}/awsaccounts/me')
@action(name='heaserver-awss3folders-file-get-component', rel='hea-component',
        path='components/bytype/heaobject.data.AWSS3FileObject')
@action(name='heaserver-awss3folders-get-delete-preflight-url', rel='hea-delete-preflight',
        path='preflights/awss3objects/delete')
async def get_file(request: web.Request) -> web.Response:
    """
    Gets the file with the specified id.

    :param request: the HTTP request.
    :return: the requested file or Not Found.
    ---
    summary: A specific file.
    tags:
        - heaserver-files-aws-s3
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
    return await _get_file(request)


@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3files/byname/{name}')
@action('heaserver-awss3files-file-get-self', rel='self', path='volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id}')
@action(name='heaserver-awss3files-file-get-volume', rel='hea-volume', path='volumes/{volume_id}')
@action(name='heaserver-awss3files-file-get-awsaccount', rel='hea-account', path='volumes/{volume_id}/awsaccounts/me')
async def get_file_by_name(request: web.Request) -> web.Response:
    """
    Gets the file with the specified name.

    :param request: the HTTP request.
    :return: the requested file or Not Found.
    ---
    summary: A specific file.
    tags:
        - heaserver-files-aws-s3
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
    return await _get_file_by_name(request)


@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3files')
@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3files/')
@action('heaserver-awss3files-file-get-open-choices', rel='hea-opener-choices hea-context-menu hea-downloader',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id}/opener',
        itemif='retrievable == True')
@action(name='heaserver-awss3files-file-get-properties', rel='hea-properties hea-context-menu')
@action(name='heaserver-awss3files-file-duplicate', rel='hea-dynamic-standard hea-icon-duplicator hea-context-menu',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id}/duplicator')
@action(name='heaserver-awss3files-file-move', rel='hea-dynamic-standard hea-icon-mover hea-context-menu',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id}/mover')
@action(name='heaserver-awss3files-file-unarchive', rel='hea-dynamic-standard hea-unarchive hea-context-menu',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id}/unarchive', itemif="archive_detail_state == 'ARCHIVED' and not retrievable")
@action(name='heaserver-awss3files-file-archive', rel='hea-dynamic-standard hea-archive hea-context-menu',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id}/archive', itemif="not archive_storage_class")
@action(name='heaserver-awss3files-file-get-trash', rel='hea-trash hea-context-menu',
        path='volumes/{volume_id}/awss3trash')
@action(name='heaserver-awss3files-file-get-presigned-url', rel='hea-dynamic-clipboard hea-icon-for-clipboard hea-context-menu',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id}/presignedurl', itemif="retrievable == True")
@action(name='heaserver-awss3files-file-get-versions', itemif="version is not None", rel='hea-versions hea-context-menu',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id}/versions/?sort=desc')
@action('heaserver-awss3files-file-get-self', rel='self', path='volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id}')
@action(name='heaserver-awss3folders-file-get-component', rel='hea-component',
        path='components/bytype/heaobject.data.AWSS3FileObject')
@action(name='heaserver-awss3folders-get-delete-preflight-url', rel='hea-delete-preflight',
        path='preflights/awss3objects/delete')
async def get_files(request: web.Request) -> web.Response:
    """
    Gets the file with the specified id.

    :param request: the HTTP request.
    :return: the requested file or Not Found.
    ---
    summary: A specific file.
    tags:
        - heaserver-files-aws-s3
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
    return await _get_all_files(request)


@routes.route('OPTIONS', '/volumes/{volume_id}/buckets/{bucket_id}/awss3files')
@routes.route('OPTIONS', '/volumes/{volume_id}/buckets/{bucket_id}/awss3files/')
async def get_files_options(request: web.Request) -> web.Response:
    """
    Gets the allowed HTTP methods for a files resource.

    :param request: the HTTP request (required).
    :response: the HTTP response.
    ---
    summary: Allowed HTTP methods.
    tags:
        - heaserver-files-aws-s3
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
    return await response.get_options(request, ['GET', 'DELETE', 'HEAD', 'OPTIONS', 'POST'])


@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3files/{file_id}/versions')
@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3files/{file_id}/versions/')
@action(name='heaserver-awss3files-file-make-current-version', rel='hea-current-version-maker', itemif="not current",
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3files/{file_id}/versions/{id}/currentmaker')
@action(name='heaserver-awss3files-file-version-get-self', rel='self',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3files/{file_id}/versions/{id}')
@action(name='heaserver-awss3files-file-version-delete', rel='hea-deleter',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3files/{file_id}/versions/{id}/deleter',
        itemif="has_deleter_permission()")
async def get_versions(request: web.Request) -> web.Response:
    """
    Gets all the versions of a file.

    :param request: the HTTP request.
    :return: the requested file or Not Found.
    ---
    summary: A file's versions.
    tags:
        - heaserver-files-aws-s3
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
        - name: file_id
          in: path
          required: true
          description: The id of the file.
          schema:
            type: string
          examples:
            example:
              summary: A file id
              value: my-file
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    responses:
      '200':
        $ref: '#/components/responses/200'
      '404':
        $ref: '#/components/responses/404'
    """
    try:
        volume_id = request.match_info['volume_id']
        bucket_name = request.match_info['bucket_id']
        file_id = request.match_info['file_id']
    except KeyError as e:
        return response.status_bad_request(str(e))

    try:
        key: str | None = decode_key(file_id)
        if awsservicelib.is_folder(key):
            return response.status_bad_request(f'Object with id {file_id} is not a file')
    except KeyDecodeException:
        return response.status_bad_request(f'Invalid id {file_id}')

    async with DesktopObjectActionLifecycle(request=request,
                                                code='hea-get',
                                                description=f'Getting {awsservicelib.s3_object_message_display_name(bucket_name, key)} versions',
                                                activity_cb=publish_desktop_object) as activity:
        async with S3ClientContext(request=request, volume_id=volume_id) as s3_client:
            try:
                versions: list[S3Version] = []
                if await awsservicelib.is_versioning_enabled(s3_client, bucket_name):
                    permission_context = S3ObjectVersionPermissionContext(request=request)
                    async for aws_version_dict in awsservicelib.list_object_versions(s3_client, bucket_name, key,
                                                                                     sort=extract_sort(request)):
                        if aws_version_dict['Key'] == key:
                            # needs to stop the loop if the version is a delete marker
                            version: S3Version = S3Version()
                            version.id = aws_version_dict['VersionId']
                            version.display_name = f'Version {aws_version_dict["VersionId"]}'
                            version.modified = aws_version_dict['LastModified']
                            version.current = aws_version_dict['IsLatest']
                            version.set_storage_class_from_str(aws_version_dict['StorageClass'])
                            version.version_of_id = file_id
                            version.bucket_id = bucket_name
                            version.add_share(await permission_context.get_permissions_as_share(version))
                            versions.append(version)
                activity.new_object_id = file_id
                activity.new_object_type_name = AWSS3FileObject.get_type_name()
                activity.new_volume_id = volume_id
                activity.new_object_uri = f'volumes/{volume_id}/buckets/{bucket_name}/awss3files/{file_id}'
                activity.new_object_display_name = split(key)[1]
                permissions = [await version.get_permissions(permission_context) for version in versions]
                attribute_permissions = [await version.get_all_attribute_permissions(permission_context) for version in versions]
                if 'path' in request.url.query:
                    activity.new_context_dependent_object_path = request.url.query.getall('path')
                return await response.get_all(request, [to_dict(version) for version in versions],
                                              permissions=permissions,
                                              attribute_permissions=attribute_permissions)
            except BotoClientError as e:
                activity.status = Status.FAILED
                return awsservicelib.handle_client_error(e)


@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3files/{file_id}/versions/{id}')
@action(name='heaserver-awss3files-file-make-current-version', rel='hea-current-version-maker', itemif="not current",
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3files/{file_id}/versions/{id}/currentmaker')
@action(name='heaserver-awss3files-file-version-get-self', rel='self',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3files/{file_id}/versions/{id}')
@action(name='heaserver-awss3files-file-version-delete', rel='hea-deleter',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3files/{file_id}/versions/{id}/deleter',
        itemif="has_deleter_permission()")
async def get_version(request: web.Request) -> web.Response:
    """
    Gets the version with the specified id.

    :param request: the HTTP request.
    :return: the requested version or Not Found.
    ---
    summary: A specific version of a file.
    tags:
        - heaserver-files-aws-s3
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
        - name: file_id
          in: path
          required: true
          description: The id of the file.
          schema:
            type: string
          examples:
            example:
              summary: A file id
              value: my-file
        - $ref: '#/components/parameters/id'
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    responses:
      '200':
        $ref: '#/components/responses/200'
      '404':
        $ref: '#/components/responses/404'
    """
    try:
        volume_id = request.match_info['volume_id']
        bucket_name = request.match_info['bucket_id']
        file_id = request.match_info['file_id']
        id_ = request.match_info['id']
    except KeyError as e:
        return response.status_bad_request(str(e))

    try:
        key: str | None = decode_key(file_id)
        if awsservicelib.is_folder(key):
            return response.status_bad_request(f'Object with id {file_id} is not a file')
    except KeyDecodeException:
        return response.status_bad_request(f'Invalid id {file_id}')

    async with DesktopObjectActionLifecycle(request=request,
                                                code='hea-get',
                                                description=f'Getting {awsservicelib.s3_object_message_display_name(bucket_name, key)} version {id_}',
                                                activity_cb=publish_desktop_object) as activity:
        async with S3ClientContext(request=request, volume_id=volume_id) as s3_client:
            try:
                if await awsservicelib.is_versioning_enabled(s3_client, bucket_name):
                    permission_context = S3ObjectVersionPermissionContext(request=request)
                    async for aws_version_dict in awsservicelib.list_object_versions(s3_client, bucket_name, key, sort=SortOrder.DESC):
                        if key == aws_version_dict['Key'] and id_ == aws_version_dict['VersionId']:
                            version: S3Version = S3Version()
                            version.id = id_
                            version.modified = aws_version_dict['LastModified']
                            version.current = aws_version_dict['IsLatest']
                            version.set_storage_class_from_str(aws_version_dict['StorageClass'])
                            version.bucket_id = bucket_name
                            share = await permission_context.get_permissions_as_share(version)
                            version.add_share(share)
                            version.version_of_id = file_id
                            activity.new_object_id = file_id
                            activity.new_object_type_name = AWSS3FileObject.get_type_name()
                            activity.new_volume_id = volume_id
                            activity.new_object_uri = f'volumes/{volume_id}/buckets/{bucket_name}/awss3files/{file_id}'
                            activity.new_object_display_name = split(key)[1]
                            if 'path' in request.url.query:
                                activity.new_context_dependent_object_path = request.url.query.getall('path')
                            return await response.get(request, to_dict(version),
                                                      permissions=await version.get_permissions(permission_context),
                                                      attribute_permissions=await version.get_all_attribute_permissions(permission_context))
                activity.status = Status.FAILED
                return await response.get(request, None)
            except BotoClientError as e:
                activity.status = Status.FAILED
                return awsservicelib.handle_client_error(e)



@routes.delete('/volumes/{volume_id}/buckets/{bucket_id}/awss3files/{file_id}/versions/{id}')
@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3files/{file_id}/versions/{id}/deleter')
async def delete_version(request: web.Request) -> web.Response:
    """
    Deletes the version with the specified id.

    :param request: the HTTP request.
    :return: No Content or Not Found.
    ---
    summary: Version deletion
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
        - name: file_id
          in: path
          required: true
          description: The id of the file.
          schema:
            type: string
          examples:
            example:
              summary: A file id
              value: my-file
        - $ref: '#/components/parameters/id'
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    responses:
      '204':
        $ref: '#/components/responses/204'
      '404':
        $ref: '#/components/responses/404'
    """
    volume_id = request.match_info['volume_id']
    bucket_name = request.match_info['bucket_id']
    file_id = request.match_info['file_id']
    id_ = request.match_info['id']
    sub = request.headers.get(SUB, NONE_USER)

    try:
        key = decode_key(file_id)
        if awsservicelib.is_folder(key):
            return response.status_bad_request(f'Object with id {file_id} is not a file')
    except KeyDecodeException:
        return response.status_bad_request(f'Invalid id {file_id}')

    async with DesktopObjectActionLifecycle(request=request,
                                                code='hea-delete',
                                                description=f'Deleting {awsservicelib.s3_object_message_display_name(bucket_name, key)}',
                                                activity_cb=publish_desktop_object) as activity:
        activity.old_object_display_name = display_name(key)
        activity.old_object_id = file_id
        activity.old_object_type_name = AWSS3FileObject.get_type_name()
        activity.old_volume_id = volume_id
        activity.old_object_uri = f'volumes/{volume_id}/buckets/{bucket_name}/awss3files/{file_id}'
        if 'path' in request.url.query:
            activity.old_context_dependent_object_path = request.url.query.getall('path')
        async with S3ClientContext(request=request, volume_id=volume_id) as s3_client:
            try:
                delete_response = s3_client.delete_object(Bucket=bucket_name, Key=key, VersionId=id_)
                if delete_response.get('VersionId'):
                    invalidate_cache(request.app[HEA_CACHE], sub, key, volume_id, bucket_name, invalidate_ancestors=True)
                    return await response.delete(True)
                else:
                    activity.status = Status.FAILED
                    return await response.delete(False)
            except BotoClientError as e:
                activity.status = Status.FAILED
                return awsservicelib.handle_client_error(e)


@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3files/{file_id}/versions/{id}/currentmaker')
async def make_current_version(request: web.Request) -> web.Response:
    """
    Makes the specified version the current one.

    :param request: the HTTP request.
    :return: the response, with a 201 status code if the current version successfully changed, or a 400 if not. If
    successfully changed, the Location header will be set to the URL of the newly created version.
    ---
    summary: A specific version of a file.
    tags:
        - heaserver-files-aws-s3
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
        - name: file_id
          in: path
          required: true
          description: The id of the file.
          schema:
            type: string
          examples:
            example:
              summary: A file id
              value: my-file
        - $ref: '#/components/parameters/id'
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    responses:
      '200':
        $ref: '#/components/responses/200'
      '404':
        $ref: '#/components/responses/404'
    """
    volume_id = request.match_info['volume_id']
    bucket_name = request.match_info['bucket_id']
    file_id = request.match_info['file_id']
    id_ = request.match_info['id']
    sub = request.headers.get(SUB, NONE_USER)

    try:
        key = decode_key(file_id)
        if awsservicelib.is_folder(key):
            return response.status_bad_request(f'Object with id {file_id} is not a file')
    except KeyDecodeException:
        return response.status_bad_request(f'Invalid id {file_id}')

    async with DesktopObjectActionLifecycle(request=request,
                                                code='hea-update',
                                                description=f'Making version {id_} of {awsservicelib.s3_object_message_display_name(bucket_name, key)} the current version',
                                                activity_cb=publish_desktop_object) as activity:
        activity.old_object_display_name = display_name(key)
        activity.old_object_id = file_id
        activity.old_object_type_name = AWSS3FileObject.get_type_name()
        activity.old_volume_id = volume_id
        activity.old_object_uri = f'volumes/{volume_id}/buckets/{bucket_name}/awss3files/{file_id}'
        if 'path' in request.url.query:
            activity.old_context_dependent_object_path = request.url.query.getall('path')
        async with S3ClientContext(request=request, volume_id=volume_id) as s3_client:
            try:
                copy_response = await asyncio.to_thread(s3_client.copy_object, Bucket=bucket_name,
                                                        CopySource={'Bucket': bucket_name, 'Key': key,
                                                                    'VersionId': id_},
                                                        Key=key)
                new_version = copy_response.get('VersionId')
                if new_version is None:
                    activity.status = Status.FAILED
                    return response.status_internal_error('Operation failed')
                await asyncio.to_thread(s3_client.delete_object, Bucket=bucket_name, Key=key, VersionId=id_)
                invalidate_cache(request.app[HEA_CACHE], sub, key, volume_id, bucket_name)
                activity.new_context_dependent_object_path = activity.old_context_dependent_object_path
                activity.new_object_display_name = activity.old_object_display_name
                activity.new_object_id = activity.old_object_id
                activity.new_object_type_name = activity.old_object_type_name
                activity.new_object_uri = activity.old_object_uri
                activity.new_volume_id = activity.old_volume_id
                return response.status_created(request.app[HEA_COMPONENT],
                                            f'volumes/{volume_id}/buckets/{bucket_name}/awss3files/{file_id}/versions',
                                            new_version)
            except BotoClientError as e:
                activity.status = Status.FAILED
                return awsservicelib.handle_client_error(e)


@routes.options('/volumes/{volume_id}/buckets/{bucket_id}/awss3files/{file_id}/versions/{id}')
async def get_version_options(request: web.Request) -> web.Response:
    """
    Gets the allowed HTTP methods for a file's versions.

    :param request: the HTTP request (required).
    :response: the HTTP response.
    ---
    summary: Allowed HTTP methods.
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
        - name: file_id
          in: path
          required: true
          description: The id of the file.
          schema:
            type: string
          examples:
            example:
              summary: A file id
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
      '403':
        $ref: '#/components/responses/403'
      '404':
        $ref: '#/components/responses/404'
    """
    return await response.get_options(request, ['GET', 'DELETE', 'HEAD', 'OPTIONS'])


@routes.delete('/volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id}')
async def delete_file(request: web.Request) -> web.Response:
    """
    Deletes the file with the specified id.

    :param request: the HTTP request.
    :return: No Content or Not Found.
    ---
    summary: File deletion
    tags:
        - heaserver-files-aws-s3
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
    try:
        async with MongoContext(request) as mongo_client:
            return await awsservicelib.delete_object(mongo_client, request, activity_cb=publish_desktop_object)
    finally:
        id_ = request.match_info['id']
        volume_id = request.match_info['volume_id']
        bucket_id = request.match_info['bucket_id']
        sub = request.headers.get(SUB, NONE_USER)
        try:
            key = decode_key(id_)
        except KeyDecodeException:
            return response.status_not_found()
        invalidate_cache(request.app[HEA_CACHE], sub, key, volume_id, bucket_id, invalidate_ancestors=True)


@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id}/opener')
@action('heaserver-awss3files-file-open-default', rel='hea-opener hea-default',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id}/content?mode=open')
@action('heaserver-awss3files-file-download-default', rel='hea-opener hea-downloader hea-default-downloader',
        path='volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id}/content?mode=download')
async def get_file_opener(request: web.Request) -> web.Response:
    """
    Opens the requested file.

    :param request: the HTTP request. Required.
    :return: the opened file, or Not Found if the requested file does not exist.
    ---
    summary: File opener choices
    tags:
        - heaserver-files-aws-s3
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
    id_ = request.match_info['id']
    try:
        key: str | None = decode_key(id_)
        if awsservicelib.is_folder(key):
            key = None
    except KeyDecodeException:
        # Let the bucket query happen so that we consistently return Forbidden if the user lacks permissions
        # for the bucket.
        key = None

    async with DesktopObjectActionLifecycle(request=request,
                                            code='hea-get',
                                            description=f'Accessing {awsservicelib.s3_object_message_display_name(bucket_name, key or "an object")}',
                                            activity_cb=publish_desktop_object) as activity:
        file_dict_and_perms = request.app[HEA_CACHE].get((sub, volume_id, bucket_name, id_, 'actual'))
        if file_dict_and_perms is not None:
            return await response.get_multiple_choices(request)
        else:
            async with S3ClientContext(request=request, volume_id=volume_id) as s3_client:
                try:
                    logger.debug('About to get file %s', key)
                    if key is None:
                        raise await when_object_not_found(s3_client, bucket_name)
                    response_ = await asyncio.to_thread(s3_client.head_object, Bucket=bucket_name, Key=key)
                    logger.debug('Result of get_file: %s', response_)
                    activity.new_object_id = id_
                    activity.new_object_type_name = AWSS3FileObject.get_type_name()
                    activity.new_volume_id = volume_id
                    activity.new_object_uri = f'volumes/{volume_id}/buckets/{bucket_name}/awss3files/{id_}'
                    activity.new_object_display_name = split(key)[1]
                    if 'path' in request.url.query:
                        activity.new_context_dependent_object_path = request.url.query.getall('path')
                    return await response.get_multiple_choices(request)
                except BotoClientError as e:
                    raise awsservicelib.handle_client_error(e)


@routes.get('/volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id}/presignedurl')
@action(name='heaserver-awss3files-file-get-presigned-url-form')
@action('heaserver-awss3files-file-get-self', rel='self', path='volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id}')
async def get_presigned_url_form(request: web.Request) -> web.Response:
    """
    Returns a template for requesting the generation of a presigned URL.

    :param request: the HTTP request.
    :return: No Content or Not Found.
    ---
    summary: Presigned url for file
    tags:
        - heaserver-files-aws-s3
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
    return await _get_file(request)


@routes.post('/volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id}/presignedurl')
async def post_presigned_url_form(request: web.Request) -> web.Response:
    """
    Posts a template for requesting the generation of a presigned URL.

    :param request: the HTTP request.
    :return: No Content or Not Found.
    ---
    summary: Presigned url for file
    tags:
        - heaserver-files-aws-s3
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
                                            description=f'Generating pre-signed URL for {awsservicelib.s3_object_message_display_name(bucket_id, object_key or 'an object')}',
                                            activity_cb=publish_desktop_object) as activity:
        activity.old_object_id = object_id
        activity.old_object_type_name = AWSS3FileObject.get_type_name()
        activity.old_volume_id = volume_id
        activity.old_object_uri = f'volumes/{volume_id}/buckets/{bucket_id}/awss3files/{object_id}'
        if 'path' in request.url.query:
            activity.old_context_dependent_object_path = request.url.query.getall('path')
        if is_folder(object_key):
            object_key = None
        async with S3ClientContext(request=request, volume_id=volume_id) as s3_client:
            if object_key is None:
                raise await when_object_not_found(s3_client, bucket_id)
            activity.old_object_display_name = display_name(object_key)
            presigned_creds = await create_presigned_url_credentials(request, volume_id, expiration_hours, object_key, bucket_id)
            async with S3ClientContext(request=request, credentials=presigned_creds) as presigned_s3_client:
                try:
                    loop = asyncio.get_running_loop()
                    obj_metadata = await loop.run_in_executor(None, partial(s3_client.head_object, Bucket=bucket_id, Key=object_key))
                    if awsservicelib.is_archived_head(obj_metadata):
                        raise response.status_bad_request(f'{awsservicelib.s3_object_message_display_name(bucket_id, object_key)} is archived and cannot be accessed with a presigned URL. Restore it first.')
                    url = await loop.run_in_executor(None, partial(presigned_s3_client.generate_presigned_url, 'get_object',
                                                                Params={'Bucket': bucket_id, 'Key': object_key},
                                                                ExpiresIn=(expiration_hours * 60 * 60) if expiration_hours is not None else 259200))
                    data: ClipboardData = ClipboardData()
                    data.mime_type = 'text/plain;encoding=utf-8'
                    data.data = url
                    data.created = now()
                    f: AWSS3FileObject = AWSS3FileObject()
                    f.bucket_id = bucket_id
                    f.id = object_id
                    data.display_name = f'Presigned URL for {f.display_name}'
                    activity.new_object_id = activity.old_object_id
                    activity.new_object_type_name = activity.old_object_type_name
                    activity.new_object_display_name = activity.old_object_display_name
                    activity.new_volume_id = activity.old_volume_id
                    activity.new_object_uri = activity.old_object_uri
                    activity.new_context_dependent_object_path = activity.old_context_dependent_object_path
                    return await response.get(request, to_dict(data))
                except BotoClientError as e:
                    raise awsservicelib.handle_client_error(e)


def main():
    config = init_cmd_line(description='Repository of files in AWS S3 buckets', default_port=8080)
    start(package_name='heaserver-files-aws-s3', db=S3Manager,
          wstl_builder_factory=builder_factory(__package__),
          cleanup_ctx=[publisher_cleanup_context_factory(config)],
          config=config)


async def _get_file(request: web.Request, include_data = True, get_tags = True) -> web.Response:
    """
    Gets the requested file. The volume id must be in the volume_id entry of the request's match_info dictionary.
    The bucket id must be in the bucket_id entry of the request's match_info dictionary. The file id must be in
    the id entry of the request's match_info dictionary, or the file name must be in the name entry of the request's
    match_info dictionary.

    :param request: the HTTP request (required).
    :param include_data: whether to include the file data in the response (optional, default True).
    :param get_tags: whether to retrieve tags (optional, default is True).
    :return: the HTTP response containing a heaobject.data.AWSS3FileObject object in the body.
    """
    logger = logging.getLogger(__name__)
    if 'volume_id' not in request.match_info:
        return response.status_bad_request('volume_id is required')
    if 'bucket_id' not in request.match_info:
        return response.status_bad_request('bucket_id is required')
    if 'id' not in request.match_info and 'name' not in request.match_info:
        return response.status_bad_request('either id or name is required')
    sub = request.headers.get(SUB, NONE_USER)
    volume_id = request.match_info['volume_id']
    bucket_name = request.match_info['bucket_id']
    id_ = request.match_info['id'] if 'id' in request.match_info else request.match_info['name']
    try:
        file_name: str | None = decode_key(id_)
        if awsservicelib.is_folder(file_name):
            file_name = None
    except KeyDecodeException:
        # Let the bucket query happen so that we consistently return Forbidden if the user lacks permissions
        # for the bucket.
        file_name = None

    async with DesktopObjectActionLifecycle(request=request,
                                            code='hea-get',
                                            description=f'Getting {awsservicelib.s3_object_message_display_name(bucket_name, file_name or 'an object')}',
                                            activity_cb=publish_desktop_object) as activity:
        file_dict_and_perms = request.app[HEA_CACHE].get((sub, volume_id, bucket_name, id_, 'actual'))
        if file_dict_and_perms is not None:
            file_dict, perms, attr_perms = file_dict_and_perms
            return await response.get(request, file_dict, permissions=perms, attribute_permissions=attr_perms)
        else:
            async with S3ClientContext(request=request, volume_id=volume_id) as s3_client:
                try:
                    logger.debug('About to get file %s', file_name)
                    if file_name is None:
                        raise await when_object_not_found(s3_client, bucket_name)
                    loop = asyncio.get_running_loop()
                    response_ = await loop.run_in_executor(None, partial(s3_client.list_objects_v2, Bucket=bucket_name,
                                                                        Prefix=file_name, MaxKeys=1,
                                                                        OptionalObjectAttributes=['RestoreStatus'] if include_data else []))
                    logger.debug('Result of get_file: %s', response_)
                    if file_name is None or response_['KeyCount'] == 0:
                        logger.debug('Returning not found 2')
                        activity.status = Status.FAILED
                        return response.status_not_found()
                    contents = response_['Contents'][0]
                    key = contents['Key']
                    encoded_key = encode_key(key)
                    display_name = key[key.rfind('/', 1) + 1:]
                    logger.debug('Creating file %s', file_name)
                    context = S3ObjectPermissionContext(request) if include_data else None
                    file, attr_perms = await _new_file(s3_client, bucket_name, contents, display_name, key,
                                                       encoded_key, context, get_tags=get_tags)
                    activity.new_object_id = id_
                    activity.new_object_type_name = AWSS3FileObject.get_type_name()
                    activity.new_volume_id = volume_id
                    activity.new_object_uri = f'volumes/{volume_id}/buckets/{bucket_name}/awss3files/{id_}'
                    activity.new_object_display_name = split(key)[1]
                    if 'path' in request.url.query:
                        activity.new_context_dependent_object_path = request.url.query.getall('path')
                    file_dict, perms, attr_perms = file.to_dict(), file.shares[0].permissions if include_data else None, attr_perms if include_data else None
                    if include_data:
                        request.app[HEA_CACHE][(sub, volume_id, bucket_name, id_, 'actual')] = (file_dict, perms, attr_perms)
                    return await response.get(request, file_dict, permissions=perms, attribute_permissions=attr_perms, include_data=include_data)
                except BotoClientError as e:
                    activity.status = Status.FAILED
                    return awsservicelib.handle_client_error(e)


async def _new_file(s3: S3Client, bucket_name: str, contents: Mapping[str, Any], display_name: str, key: str, encoded_key: str,
                    context: S3ObjectPermissionContext | None,
                    get_tags = True) -> tuple[AWSS3FileObject, dict[str, list[Permission]]]:
    """
    Creates a new AWSS3FileObject from the specified S3 object contents.

    :param s3: the S3 client (required).
    :param bucket_name: the S3 bucket name (required).
    :param contents: the S3 object contents (required).
    :param display_name: the display name for the file (required).
    :param key: the S3 object key (required).
    :param encoded_key: the encoded S3 object key (required).
    :param context: the permission context (optional).
    :param get_tags: whether to retrieve tags (optional, default is True).
    :return: the new AWSS3FileObject and its attribute permissions. If context is None, the object's permissions and
    tags are not retrieved."""
    file: AWSS3FileObject = AWSS3FileObject()
    file.id = encoded_key
    file.name = encoded_key
    file.display_name = display_name
    file.modified = contents['LastModified']
    file.created = contents['LastModified']
    file.owner = AWS_USER
    file.mime_type = guess_mime_type(display_name)
    file.size = contents['Size']
    set_s3_storage_status(contents, file)
    file.bucket_id = bucket_name
    file.key = key
    version_dict = await awsservicelib.get_latest_object_version(s3, bucket_name, key)
    file.version = version_dict['VersionId'] if version_dict is not None else None
    loop = asyncio.get_running_loop()
    coros: list[Coroutine[Any, Any, None]] = []
    attr_perms: dict[str, list[Permission]] = {}
    if get_tags:
        async def _get_object_tagging():
            object_tagging = await loop.run_in_executor(None, partial(s3.get_object_tagging, Bucket=bucket_name, Key=key))
            tags = []
            for aws_tag in object_tagging.get('TagSet', []):
                tag = Tag()
                tag.key = aws_tag['Key']
                tag.value = aws_tag['Value']
                tags.append(tag)
            file.tags = tags
        coros.append(_get_object_tagging())
    if context:
        async def _get_permissions_as_share():
            file.add_user_share(await context.get_permissions_as_share(file))
        coros.append(_get_permissions_as_share())
        async def _get_attr_perms():
            nonlocal attr_perms
            attr_perms = await file.get_all_attribute_permissions(context)
        coros.append(_get_attr_perms())
    await asyncio.gather(*coros)
    return file, attr_perms

async def _get_all_files(request: web.Request) -> web.Response:
    """
    Gets all files in a bucket. The volume id must be in the volume_id entry of the request's
    match_info dictionary. The bucket id must be in the bucket_id entry of the request's match_info dictionary.

    :param request: the HTTP request (required).
    :return: the HTTP response with a 200 status code if the bucket exists and a Collection+JSON document in the body
    containing any heaobject.data.AWSS3FileObject objects, 403 if access was denied, or 500 if an internal error occurred. The
    body's format depends on the Accept header in the request.
    """
    logger = logging.getLogger(__name__)
    if 'volume_id' not in request.match_info:
        return response.status_bad_request('volume_id is required')
    if 'bucket_id' not in request.match_info:
        return response.status_bad_request('bucket_id is required')
    sub = request.headers.get(SUB, NONE_USER)
    volume_id = request.match_info['volume_id']
    bucket_name = request.match_info['bucket_id']

    async with DesktopObjectActionLifecycle(request=request,
                                            code='hea-get',
                                            description=f'Getting all folders in bucket {bucket_name}',
                                            activity_cb=publish_desktop_object) as activity:
        async with S3ClientContext(request=request, volume_id=volume_id) as s3:
            loop = asyncio.get_running_loop()
            try:
                logger.debug('Getting all files from bucket %s', bucket_name)
                files: list[DesktopObjectDict] = []
                permissions: list[list[Permission]] = []
                attribute_permissions: list[dict[str, list[Permission]]] = []
                context = S3ObjectPermissionContext(request)
                async for obj in awsservicelib.list_objects(s3, bucket_id=bucket_name, loop=loop,
                                                            include_restore_status=True):
                    key = obj['Key']
                    if not awsservicelib.is_folder(key):
                        encoded_key = encode_key(key)
                        logger.debug('Found file %s in bucket %s', key, bucket_name)
                        display_name = key.split('/')[-1]
                        file, attr_perms = await _new_file(s3, bucket_name, obj, display_name, key, encoded_key, context)
                        permissions.append(file.shares[0].permissions)
                        attribute_permissions.append(attr_perms)
                        files.append(to_dict(file))
                activity.new_object_type_name = AWSS3FileObject.get_type_name()
                activity.new_volume_id = volume_id
                activity.new_object_uri = f'volumes/{volume_id}/buckets/{bucket_name}/awss3files/'
                if 'path' in request.url.query:
                    activity.new_context_dependent_object_path = request.url.query.getall('path')
                return await response.get_all(request, files,
                                              permissions=permissions,
                                              attribute_permissions=attribute_permissions)
            except BotoClientError as e:
                activity.status = Status.FAILED
                return awsservicelib.handle_client_error(e)


async def _get_file_by_name(request: web.Request) -> web.Response:
    """
    Gets the requested file. The volume id must be in the volume_id entry of the request's match_info dictionary.
    The bucket id must be in the bucket_id entry of the request's match_info dictionary. The file name must be in the
    name entry of the request's match_info dictionary.

    :param request: the HTTP request (required).
    :return: the HTTP response with a 200 status code if the bucket exists and the heaobject.data.AWSS3FileObject in the body,
    403 if access was denied, 404 if no such file was found, or 500 if an internal error occurred. The body's format
    depends on the Accept header in the request.
    """
    return await _get_file(request)


async def _has_file(request: web.Request) -> web.Response:
    """
    Checks for the existence of the requested file object. The volume id must be in the volume_id entry of the
    request's match_info dictionary. The bucket id must be in the bucket_id entry of the request's match_info
    dictionary. The file id must be in the id entry of the request's match_info dictionary.

    :param request: the HTTP request (required).
    :return: the HTTP response with a 200 status code if the file exists, 403 if access was denied, or 500 if an
    internal error occurred.
    """
    logger = logging.getLogger(__name__)

    if 'volume_id' not in request.match_info:
        return response.status_bad_request('volume_id is required')
    if 'bucket_id' not in request.match_info:
        return response.status_bad_request('bucket_id is required')
    if 'id' not in request.match_info:
        return response.status_bad_request('id is required')

    volume_id = request.match_info['volume_id']
    bucket_name = request.match_info['bucket_id']

    s3 = await get_database(request).get_client(request, 's3', volume_id)

    try:
        file_id: str | None = decode_key(request.match_info['id'])
        if awsservicelib.is_folder(file_id):
            file_id = None
    except KeyDecodeException:
        # Let the bucket query happen so that we consistently return Forbidden if the user lacks permissions
        # for the bucket.
        file_id = None
    loop = asyncio.get_running_loop()
    try:
        if file_id is None:
            # We couldn't decode the file_id, and we need to check if the user can access the bucket in order to
            # decide which HTTP status code to respond with (Forbidden vs Not Found).
            await loop.run_in_executor(None, partial(s3.head_bucket, Bucket=bucket_name))
            return response.status_not_found()
        logger.debug('Checking if file %s in bucket %s exists', file_id, bucket_name)
        response_ = await loop.run_in_executor(None, partial(s3.list_objects_v2, Bucket=bucket_name, Prefix=file_id,
                                                             MaxKeys=1))
        if response_['KeyCount'] > 0:
            return response.status_ok()
        return await response.get(request, None)
    except BotoClientError as e:
        return awsservicelib.handle_client_error(e)
    except KeyDecodeException:
        return response.status_not_found()


async def _put_object_content(request: web.Request) -> web.Response:
    """
    Upload a file to an S3 bucket. Will fail if the file already exists.
    See https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-uploading-files.html for more information.

    The following information must be specified in request.match_info:
    volume_id (str): the id of the target volume,
    bucket_id (str): the name of the target bucket,
    id (str): the name of the file.

    :param request: the aiohttp Request (required).
    :return: the HTTP response, with a 204 status code if successful, 400 if one of the above values was not specified,
    403 if uploading access was denied, 404 if the volume or bucket could not be found, or 500 if an internal error
    occurred.
    """
    logger = logging.getLogger(__name__)
    if 'volume_id' not in request.match_info:
        return response.status_bad_request("volume_id is required")
    if 'bucket_id' not in request.match_info:
        return response.status_bad_request("bucket_id is required")
    if 'id' not in request.match_info:
        return response.status_bad_request('id is required')
    volume_id = request.match_info['volume_id']
    bucket_name = request.match_info['bucket_id']
    file_name = request.match_info['id']
    try:
        storage_class = request.url.query.get('storage_class', 'STANDARD')
    except KeyError:
        return response.status_bad_request(f"Invalid storage_class type")

    try:
        file_id: str | None = decode_key(file_name)
        if awsservicelib.is_folder(file_id):
            file_id = None
    except KeyDecodeException:
        # Let the bucket query happen so that we consistently return Forbidden if the user lacks permissions
        # for the bucket.
        file_id = None

    loop = asyncio.get_running_loop()

    try:
        s3_client = await get_database(request).get_client(request, 's3', volume_id)
        if file_id is None:
            # We couldn't decode the file_id, and we need to check if the user can access the bucket in order to
            # decide which HTTP status code to respond with (Forbidden vs Not Found).
            await loop.run_in_executor(None, partial(s3_client.head_bucket, Bucket=bucket_name))
            return response.status_not_found()
    except BotoClientError as e:
        return awsservicelib.handle_client_error(e)

    async with DesktopObjectActionLifecycle(request=request,
                                            code='hea-update',
                                            description=f'Upload {awsservicelib.s3_object_message_display_name(bucket_name, file_id)}',
                                            activity_cb=publish_desktop_object) as activity:
        async with S3ClientContext(request=request, volume_id=volume_id) as s3_client:
            try:
                await loop.run_in_executor(None, partial(s3_client.head_object, Bucket=bucket_name, Key=file_id))
                fileobj = RequestFileLikeWrapper(request)
                done = False
                try:
                    fileobj.initialize()

                    p = partial(s3_client.upload_fileobj, Fileobj=fileobj, Bucket=bucket_name, Key=file_id,  # type: ignore[arg-type]
                                ExtraArgs={'StorageClass': storage_class})
                    await loop.run_in_executor(None, p)
                    fileobj.close()
                    done = True
                except Exception as e:
                    if not done:
                        try:
                            fileobj.close()
                        except:
                            pass
                        done = True
                        raise e
                return response.status_no_content()
            except BotoClientError as e:
                activity.status = Status.FAILED
                return awsservicelib.handle_client_error(e)


async def _get_file_move_template(request: web.Request, include_data: bool = True) -> web.Response:
    logger = logging.getLogger(__name__)
    try:
        return await _get_file(request, include_data=include_data)
    except KeyDecodeException as e:
        logger.exception('Error getting parent key')
        return response.status_bad_request(f'Error getting parent folder: {e}')


async def _to_aws_tags(hea_tags: list[Tag]) -> list[TagTypeDef]:
    """
    :param hea_tags: HEA tags to converted to aws tags compatible with boto3 api
    :return: aws tags
    """
    aws_tag_dicts: list[TagTypeDef] = []
    for hea_tag in hea_tags:
        if hea_tag.key is None:
            raise ValueError("A tag's key cannot be None")
        if hea_tag.value is None:
            raise ValueError("A tag's value cannot be None")
        aws_tag_dict: TagTypeDef = {
            'Key': hea_tag.key,
            'Value': hea_tag.value
        }
        aws_tag_dicts.append(aws_tag_dict)
    return aws_tag_dicts

