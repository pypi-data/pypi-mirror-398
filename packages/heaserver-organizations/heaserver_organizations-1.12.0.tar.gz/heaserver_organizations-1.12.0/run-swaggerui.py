#!/usr/bin/env python3
from heaserver.service.db.aws import S3Manager
from heaserver.service.testcase.collection import CollectionKey
from heaserver.service.db.database import query_fixture_collection, get_collection_key_from_name
from heaserver.organization import service
from heaserver.service.testcase import swaggerui
from heaserver.service.testcase.testenv import MicroserviceContainerConfig, DockerVolumeMapping
from heaserver.service.wstl import builder_factory
from heaserver.service.testcase.dockermongo import DockerMongoManager
from integrationtests.heaserver.organizationintegrationtest.testcase import db_store
from aiohttp.web import get, put, post, delete, view
from heaobject.registry import Resource
from heaobject.volume import AWSFileSystem
from heaobject.person import Person
from heaobject.account import AWSAccount
from pathlib import Path
import logging
from copy import deepcopy
import argparse

logging.basicConfig(level=logging.DEBUG)

HEASERVER_REGISTRY_IMAGE = 'registry.gitlab.com/huntsman-cancer-institute/risr/hea/heaserver-registry:1.0.0'
HEASERVER_VOLUMES_IMAGE = 'registry.gitlab.com/huntsman-cancer-institute/risr/hea/heaserver-volumes:1.0.0'
HEASERVER_PEOPLE_IMAGE = 'registry.gitlab.com/huntsman-cancer-institute/risr/hea/heaserver-people:1.0.0'
HEASERVER_ACCOUNTS_IMAGE = 'registry.gitlab.com/huntsman-cancer-institute/risr/hea/heaserver-accounts:1.0.0'

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Runs SwaggerUI with an optional AWS account id to add to organization 666f6f2d6261722d71757578.')
    parser.add_argument('-a', '--account', nargs='?', help='the AWS account id to add')
    args = parser.parse_args()
    db_store_ = deepcopy(db_store)
    db_store_[CollectionKey(name='awsaccounts', db_manager_cls=S3Manager)] = db_store_.pop(
        get_collection_key_from_name(db_store_, 'awsaccounts'))
    aws_account = args.account
    if aws_account is not None:
        my_org = next((org for org in query_fixture_collection(db_store_, 'organizations', strict=False) or [] if
                       org['id'] == '666f6f2d6261722d71757578'), None)
        if my_org is not None:
            my_org.setdefault('aws_account_ids', []).append(aws_account)
            print(f'Added AWS account id {aws_account} to organization 666f6f2d6261722d71757578: {my_org}')
    swaggerui.run(project_slug='heaserver-organizations', desktop_objects=db_store_, db_manager_cls=DockerMongoManager,
                  wstl_builder_factory=builder_factory(service.__package__), routes=[
            (get, '/organizations/{id}', service.get_organization),
            (get, '/organizations/{id}/memberseditor', service.get_organization_memberseditor),
            (get, '/organizations/byname/{name}', service.get_organization_by_name),
            (get, '/organizations/', service.get_all_organizations),
            (put, '/organizations/{id}', service.put_organization),
            (put, '/organizations/{id}/memberseditor', service.put_organization_memberseditor),
            (post, '/organizations/', service.post_organization),
            (delete, '/organizations/{id}', service.delete_organization),
            (get, '/organizations/{id}/members', service.get_organization_members),
            (view, '/organizations/{id}/opener', service.get_organization_opener),
            (get, '/organizations/{id}/awsaccounts/', service.get_organization_accounts)
        ], registry_docker_image=HEASERVER_REGISTRY_IMAGE,
                  other_docker_images=[MicroserviceContainerConfig(image=HEASERVER_ACCOUNTS_IMAGE,
                                                                   port=8080,
                                                                   check_path='/ping',
                                                                   db_manager_cls=S3Manager,
                                                                   # Change to DockerMongoManager for heaserver-accounts version 1.0.0a9 or earlier.
                                                                   resources=[Resource(
                                                                       resource_type_name=AWSAccount.get_type_name(),
                                                                       file_system_type=AWSFileSystem.get_type_name(),
                                                                       base_path='volumes')],
                                                                   volumes=[DockerVolumeMapping(
                                                                       host=str(Path.home() / '.aws'),
                                                                       container='/home/app/.aws')]),
                                       MicroserviceContainerConfig(image=HEASERVER_VOLUMES_IMAGE,
                                                                   port=8080,
                                                                   check_path='/volumes',
                                                                   db_manager_cls=DockerMongoManager,
                                                                   resources=[
                                                                       Resource(
                                                                           resource_type_name='heaobject.volume.Volume',
                                                                           base_path='volumes/'),
                                                                       Resource(
                                                                           resource_type_name='heaobject.volume.FileSystem',
                                                                           base_path='filesystems')
                                                                   ]),
                                       MicroserviceContainerConfig(image=HEASERVER_PEOPLE_IMAGE,
                                                                   port=8080,
                                                                   check_path='/ping',
                                                                   db_manager_cls=DockerMongoManager,
                                                                   resources=[Resource(
                                                                       resource_type_name=Person.get_type_name(),
                                                                       base_path='people')])]
                  )
