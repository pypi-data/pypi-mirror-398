#!/usr/bin/env python3
from heaobject.registry import Resource
from heaobject import user

from heaserver.bucket import service
from heaserver.service.testcase import swaggerui
from heaserver.service.wstl import builder_factory
from heaserver.service.testcase.dockermongo import DockerMongoManager
from heaserver.service.testcase.awsdockermongo import S3WithDockerMongoManager
from aiohttp.web import get, delete, post, view, options, put
from heaserver.service.testcase.testenv import MicroserviceContainerConfig
from integrationtests.heaserver.bucketintegrationtest.testcase import db_store
import logging
from heaobject.volume import DEFAULT_FILE_SYSTEM

logging.basicConfig(level=logging.DEBUG)

HEASERVER_REGISTRY_IMAGE = 'registry.gitlab.com/huntsman-cancer-institute/risr/hea/heaserver-registry:1.0.0'
HEASERVER_VOLUMES_IMAGE = 'registry.gitlab.com/huntsman-cancer-institute/risr/hea/heaserver-volumes:1.0.0'
HEASERVER_KEYCHAIN_IMAGE = 'registry.gitlab.com/huntsman-cancer-institute/risr/hea/heaserver-keychain:1.0.0'
HEASERVER_AWSS3FOLDER_IMAGE = 'registry.gitlab.com/huntsman-cancer-institute/risr/hea/heaserver-folders-aws-s3:1.0.0b2'

if __name__ == '__main__':
    volume_microservice = MicroserviceContainerConfig(image=HEASERVER_VOLUMES_IMAGE, port=8080, check_path='/volumes',
                                                      resources=[Resource(resource_type_name='heaobject.volume.Volume',
                                                                          base_path='volumes',
                                                                          file_system_name=DEFAULT_FILE_SYSTEM),
                                                                 Resource(
                                                                     resource_type_name='heaobject.volume.FileSystem',
                                                                     base_path='filesystems',
                                                                     file_system_name=DEFAULT_FILE_SYSTEM)],
                                                      db_manager_cls=DockerMongoManager)
    keychain_microservice = MicroserviceContainerConfig(image=HEASERVER_KEYCHAIN_IMAGE, port=8080,
                                                        check_path='/credentials',
                                                        resources=[
                                                            Resource(
                                                                resource_type_name='heaobject.keychain.Credentials',
                                                                base_path='credentials',
                                                                file_system_name=DEFAULT_FILE_SYSTEM)],
                                                        db_manager_cls=DockerMongoManager)
    # folder_microservice = MicroserviceContainerConfig(image=HEASERVER_AWSS3FOLDER_IMAGE, port=8080,
    #                                                   check_path='/volumes', db_manager_cls=DockerMongoManager,
    #                                                   resources=[Resource(resource_type_name='heaobject.folder.AWSS3Folder',
    #                                                                       base_path='/volumes',
    #                                                                       file_system_name=DEFAULT_FILE_SYSTEM)])
    swaggerui.run(project_slug='heaserver-buckets', desktop_objects=db_store,
                  wstl_builder_factory=builder_factory(service.__package__),
                  routes=[(get, '/volumes/{volume_id}/buckets/{id}', service.get_bucket),
                          (get, '/volumes/{volume_id}/buckets', service.get_all_buckets),
                          (get, '/volumes/{volume_id}/bucketitems', service.get_all_bucketitems),
                          (get, '/volumes/{volume_id}/buckets/byname/{bucket_name}', service.get_bucket_by_name),
                          (post, '/volumes/{volume_id}/buckets', service.post_bucket),
                          (put, '/volumes/{volume_id}/buckets/{id}', service.put_bucket),
                          (view, '/volumes/{volume_id}/buckets/{id}/opener', service.get_bucket_opener),
                          (delete, '/volumes/{volume_id}/buckets/{id}', service.delete_bucket),
                          (options, '/volumes/{volume_id}/buckets', service.get_buckets_options),
                          (options, '/volumes/{volume_id}/bucketitems', service.get_bucketitems_options),
                          (options, '/volumes/{volume_id}/buckets/{id}', service.get_bucket_options),
                          (view, '/volumes/{volume_id}/buckets/{id}/creator', service.get_bucket_creator),
                          (get, '/volumes/{volume_id}/buckets/{id}/newfolder', service.get_new_folder_form),
                          (post, '/volumes/{volume_id}/buckets/{bucket_id}/newfolder/', service.post_new_folder)
                          ],
                  registry_docker_image=HEASERVER_REGISTRY_IMAGE,
                  other_docker_images=[keychain_microservice, volume_microservice#, folder_microservice
                                       ],
                  db_manager_cls=S3WithDockerMongoManager)
