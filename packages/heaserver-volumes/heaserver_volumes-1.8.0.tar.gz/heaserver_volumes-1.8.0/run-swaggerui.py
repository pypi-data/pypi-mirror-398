#!/usr/bin/env python3

from heaserver.volume import service
from heaserver.service.testcase.mockaws import S3Manager
from heaserver.service.testcase import swaggerui
from heaserver.service.testcase.testenv import MicroserviceContainerConfig
from heaserver.service.wstl import builder_factory
from heaserver.service.testcase.dockermongo import DockerMongoManager
from heaobject.registry import Resource
from integrationtests.heaserver.volumeintegrationtest.testcase import db_store
from heaserver.service.testcase.testenv import DockerVolumeMapping
from aiohttp.web import get, delete, post, put, view
from pathlib import Path
import logging


logging.basicConfig(level=logging.DEBUG)

HEASERVER_REGISTRY_IMAGE = 'registry.gitlab.com/huntsman-cancer-institute/risr/hea/heaserver-registry:1.0.0'
HEASERVER_FOLDER_IMAGE = 'registry.gitlab.com/huntsman-cancer-institute/risr/hea/heaserver-folders:1.0.0a36'
HEASERVER_TRASH_IMAGE = 'registry.gitlab.com/huntsman-cancer-institute/risr/hea/heaserver-trash-aws-s3:1.0.0b15'

if __name__ == '__main__':
    swaggerui.run(project_slug='heaserver-volumes', desktop_objects=db_store,
                  wstl_builder_factory=builder_factory(service.__package__),
                  routes=[(get, '/volumes/{id}', service.get_volume),
                          (get, '/volumes/byname/{name}', service.get_volume_by_name),
                          (get, '/volumes/', service.get_all_volumes),
                          (get, '/volumes/{id}/trash', service.get_trash),
                          (get, '/volumes/{id}/content', service.get_volume_content),
                          (post, '/volumes', service.post_volume),
                          (put, '/volumes/{id}', service.put_volume),
                          (delete, '/volumes/{id}', service.delete_volume),
                          (view, '/volumes/{id}/opener', service.get_volume_opener),
                          (get, '/volumes/byfilesystemtype/{type}/',
                           service.get_volumes_by_file_system_type),
                          (get,
                           '/volumes/byfilesystemtype/{type}/byfilesystemname/{name}/',
                           service.get_volumes_by_file_system_type_and_name),
                          (get, '/filesystems/{id}', service.get_file_system),
                          (get, '/filesystems/bytype/{type}/byname/{name}',
                           service.get_file_system_by_type_and_name),
                          (get, '/filesystems/', service.get_all_file_systems),
                          (post, '/filesystems', service.post_file_system),
                          (put, '/filesystems/{id}', service.put_file_system),
                          (delete, '/filesystems/{id}', service.delete_file_system)
                          ],
                  registry_docker_image=HEASERVER_REGISTRY_IMAGE,
                  other_docker_images=[MicroserviceContainerConfig(image=HEASERVER_FOLDER_IMAGE,
                                                                   port=8086,
                                                                   check_path='/folders/root/items',
                                                                   db_manager_cls=DockerMongoManager,
                                                                   resources=[Resource(
                                                                       resource_type_name='heaobject.folder.Folder',
                                                                       base_path='folders')]),
                                       MicroserviceContainerConfig(image=HEASERVER_TRASH_IMAGE,
                                                                   port=8080,
                                                                   check_path='/ping',
                                                                   db_manager_cls=S3Manager,
                                                                   resources=[Resource(
                                                                        resource_type_name='heaobject.trash.AWSS3FolderFileTrashItem',
                                                                        base_path='volumes/{id}/awss3trash')],
                                                                   volumes=[DockerVolumeMapping(
                                                                       host=str(Path.home() / '.aws'),
                                                                       container='/home/app/.aws')])
                                       ])
