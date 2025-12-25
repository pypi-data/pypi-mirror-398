#!/usr/bin/env python3
from heaserver.service.testcase import swaggerui
from heaserver.service.testcase.docker import MicroserviceContainerConfig
from heaserver.service.testcase.collection import CollectionKey
from heaserver.service.testcase.awsdockermongo import S3WithDockerMongoManager
from heaserver.service.testcase.dockermongo import DockerMongoManager
from heaserver.service.wstl import builder_factory
from aiohttp.web import get, post, delete, view, options
from heaobject.registry import Resource
from heaobject.volume import DEFAULT_FILE_SYSTEM
from heaobject.volume import AWSFileSystem
from heaobject import user
import logging

from src.heaserver.folderawss3 import service

logging.basicConfig(level=logging.DEBUG)

db_values = {
    CollectionKey(name='components', db_manager_cls=DockerMongoManager): [
        {
            'id': '666f6f2d6261722d71757578',
            'created': None,
            'derived_by': None,
            'derived_from': [],
            'description': None,
            'display_name': 'Reximus',
            'invited': [],
            'modified': None,
            'name': 'reximus',
            'owner': user.NONE_USER,
            'shared_with': [],
            'source': None,
            'type': 'heaobject.registry.Component',
            'version': None,
            'base_url': 'http://localhost:8080',
            'resources': [{'type': 'heaobject.registry.Resource', 'resource_type_name': 'heaobject.folder.AWSS3Folder',
                           'base_path': 'volumes/666f6f2d6261722d71757578/buckets/arp-scale-2-cloud-bucket-with-tags11/awss3folders'},
                          {'type': 'heaobject.registry.Resource', 'resource_type_name': 'heaobject.folder.AWSS3Item',
                           'base_path': 'items'}]
        }
    ],
    CollectionKey(name='filesystems', db_manager_cls=DockerMongoManager): [{
        'id': '666f6f2d6261722d71757578',
        'created': None,
        'derived_by': None,
        'derived_from': [],
        'description': None,
        'display_name': 'Amazon Web Services',
        'invited': [],
        'modified': None,
        'name': 'amazon_web_services',
        'owner': user.NONE_USER,
        'shared_with': [],
        'source': None,
        'type': 'heaobject.volume.AWSFileSystem',
        'version': None
    }],
    CollectionKey(name='volumes', db_manager_cls=DockerMongoManager): [{
        'id': '666f6f2d6261722d71757578',
        'created': None,
        'derived_by': None,
        'derived_from': [],
        'description': None,
        'display_name': 'My Amazon Web Services',
        'invited': [],
        'modified': None,
        'name': 'amazon_web_services',
        'owner': user.NONE_USER,
        'shared_with': [],
        'source': None,
        'type': 'heaobject.volume.Volume',
        'version': None,
        'file_system_name': 'amazon_web_services',
        'file_system_type': 'heaobject.volume.AWSFileSystem',
        'credential_id': None  # Let boto3 try to find the user's credentials.
    }
    ]

}

HEASERVER_REGISTRY_IMAGE = 'registry.gitlab.com/huntsman-cancer-institute/risr/hea/heaserver-registry:1.0.0'
HEASERVER_VOLUMES_IMAGE = 'registry.gitlab.com/huntsman-cancer-institute/risr/hea/heaserver-volumes:1.0.0'
HEASERVER_BUCKETS_IMAGE = 'registry.gitlab.com/huntsman-cancer-institute/risr/hea/heaserver-buckets:1.0.0'

if __name__ == '__main__':
    volume_microservice = MicroserviceContainerConfig(image=HEASERVER_VOLUMES_IMAGE, port=8080, check_path='volumes',
                                                      resources=[Resource(resource_type_name='heaobject.volume.Volume',
                                                                          base_path='volumes',
                                                                          file_system_name=DEFAULT_FILE_SYSTEM),
                                                                 Resource(
                                                                     resource_type_name='heaobject.volume.FileSystem',
                                                                     base_path='filesystems',
                                                                     file_system_name=DEFAULT_FILE_SYSTEM)],
                                                      db_manager_cls=DockerMongoManager)
    bucket_microservice = MicroserviceContainerConfig(image=HEASERVER_BUCKETS_IMAGE, port=8080, check_path='ping',
                                                      resources=[Resource(resource_type_name='heaobject.folder.Folder',
                                                                          base_path='volumes',
                                                                          file_system_type=AWSFileSystem.get_type_name(),
                                                                          file_system_name=DEFAULT_FILE_SYSTEM)],
                                                      db_manager_cls=DockerMongoManager,
                                                      env_vars={'HEA_MESSAGE_BROKER_ENABLED': 'false'})
    swaggerui.run(project_slug='heaserver-folders-aws-s3', desktop_objects=db_values,
                  wstl_builder_factory=builder_factory(service.__package__),
                  routes=[# Folders
                          (get, '/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{folder_id}/items/{id}',
                           service.get_item),
                          (options, '/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{folder_id}/items/{id}',
                           service.get_item_options),
                          (options, '/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{folder_id}/items',
                           service.get_items_options),
                          (get, '/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{folder_id}/items',
                           service.get_items),
                          (post, '/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{folder_id}/items',
                           service.post_item_in_folder),
                          (delete, '/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{folder_id}/items/{id}',
                           service.delete_item),
                          (get, '/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}', service.get_folder),
                          (options, '/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}',
                           service.get_folder_options),
                          (get, '/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/', service.get_folders),
                          (get, '/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/byname/{name}',
                           service.get_folder_by_name),
                          (get, '/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/presignedurl', service.get_presigned_url_form),
                          (post, '/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/presignedurl', service.post_presigned_url_form),
                          (post, '/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/', service.post_folder),
                          (view, '/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/opener',
                           service.get_folder_opener),
                          (view, '/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/creator',
                           service.get_folder_creator),
                          (get, '/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/newfolder',
                           service.get_new_folder_form),
                          (post, '/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/newfolder',
                           service.post_new_folder),
                          (options, '/volumes/{volume_id}/buckets/{bucket_id}/awss3folders',
                           service.get_folders_options),
                          (delete, '/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}', service.delete_folder),
                          (get, '/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/duplicator',
                           service.get_folder_duplicator),
                          (post, '/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/duplicator',
                           service.post_folder_duplicator),
                          (get, '/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/mover',
                           service.get_folder_mover),
                          (post, '/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/mover',
                           service.post_folder_mover),
                          (get, '/volumes/{volume_id}/buckets/{bucket_id}/awss3files/{id}/unarchive', service.get_folder_unarchive_form),
                          (post, '/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/unarchive', service.unarchive_folder),
                          (get, '/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/archive', service.get_folder_archive),
                          (post, '/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/archive', service.post_folder_archive),
                          (post, '/volumes/{volume_id}/buckets/{bucket_id}/awss3folders/{id}/uploader', service.post_folder_uploader),
                          # Projects
                          (get, '/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{folder_id}/items/{id}',
                           service.projectservice.get_item),
                          (options, '/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{folder_id}/items/{id}',
                           service.projectservice.get_item_options),
                          (options, '/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{folder_id}/items',
                           service.projectservice.get_items_options),
                          (get, '/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{folder_id}/items',
                           service.projectservice.get_items),
                          (post, '/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{folder_id}/items',
                           service.projectservice.post_item_in_project),
                          (delete, '/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{folder_id}/items/{id}',
                           service.projectservice.delete_item),
                          (get, '/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}', service.projectservice.get_project),
                          (options, '/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}',
                           service.projectservice.get_project_options),
                          (get, '/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/', service.projectservice.get_projects),
                          (get, '/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/byname/{name}',
                           service.projectservice.get_project_by_name),
                          (get, '/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/presignedurl', service.projectservice.get_presigned_url_form),
                          (post, '/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/presignedurl', service.projectservice.post_presigned_url_form),
                          (post, '/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/', service.projectservice.post_project),
                          (view, '/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/opener',
                           service.projectservice.get_project_opener),
                          (view, '/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/creator',
                           service.projectservice.get_project_creator),
                          (get, '/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/newfolder',
                           service.projectservice.get_new_folder_form),
                          (post, '/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/newfolder',
                           service.projectservice.post_new_folder),
                          (options, '/volumes/{volume_id}/buckets/{bucket_id}/awss3projects',
                           service.projectservice.get_projects_options),
                          (delete, '/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}', service.projectservice.delete_project),
                          (get, '/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/duplicator',
                           service.projectservice.get_project_duplicator),
                          (post, '/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/duplicator',
                           service.projectservice.post_project_duplicator),
                          (get, '/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/mover',
                           service.projectservice.get_project_mover),
                          (post, '/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/mover',
                           service.projectservice.post_project_mover),
                          (get, '/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/unarchive', service.projectservice.get_project_unarchive),
                          (post, '/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/unarchive', service.projectservice.unarchive_project),
                          (get, '/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/archive', service.projectservice.get_project_archive),
                          (post, '/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/archive', service.projectservice.post_project_archive),
                          (post, '/volumes/{volume_id}/buckets/{bucket_id}/awss3projects/{id}/uploader', service.projectservice.post_project_uploader)
                          ], registry_docker_image=HEASERVER_REGISTRY_IMAGE,
                  other_docker_images=[volume_microservice, bucket_microservice],
                  db_manager_cls=S3WithDockerMongoManager)
