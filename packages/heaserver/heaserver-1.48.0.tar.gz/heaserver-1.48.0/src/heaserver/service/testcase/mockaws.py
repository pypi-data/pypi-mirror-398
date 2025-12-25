"""
Classes and functions for mocking Amazon S3 buckets.

This module assumes the moto package is installed. Do not import it into environments where moto will
not be available, for example, in any code that needs to run outside automated testing.
"""
from contextlib import AbstractContextManager
from typing import Optional, cast

from aiohttp import web
from heaobject.registry import Property
from heaobject.folder import AWSS3Folder
from heaobject.data import AWSS3FileObject
from heaobject.user import AWS_USER
from heaobject.source import AWS

from heaserver.service.config import Configuration

from ..db.database import query_fixtures

from ..db.aws import S3, S3Manager, create_client
from ..db.mongo import Mongo
from heaobject.keychain import CredentialTypeVar, AWSCredentials
from heaobject.volume import AWSFileSystem, Volume, FileSystem
from heaobject.root import DesktopObjectDict, DesktopObject
from heaobject.account import AWSAccount
from heaobject.bucket import AWSBucket
from heaobject.awss3key import decode_key
from aiohttp.web import Request

import boto3
from mypy_boto3_s3.literals import StorageClassType
from moto import mock_aws

from .util import freeze_time

from ..db.database import query_content, CollectionKey
from .mockmongo import MockMongo, MockMongoManager
from .mockdatabase import MockDatabase
from collections.abc import Sequence, AsyncIterator, Mapping, Callable
from io import BytesIO
import logging


class MockS3(S3, MockDatabase):
    """
    Overrides the S3 class' methods use moto instead of actual AWS. It mocks calls to get file system and credentials
    information.
    """

    async def get_file_system_and_credentials_from_volume(self, request: Request, volume_id: str) -> tuple[
        AWSFileSystem, CredentialTypeVar | None]:
        """
        Gets a file system and credentials using the provided volume id.

        :returns: a tuple with an AWSFileSystem instance and None.
        """
        return AWSFileSystem(), None

    async def get_credentials_from_volume(self, request: Request, volume_id: str) -> AWSCredentials | None:
        """
        Gets a credentials object using the provided volume id.

        :returns: None.
        """
        return AWSCredentials()

    async def get_account(self, request: Request, volume_id: str) -> AWSAccount | None:
        """
        Gets a mock AWS account.

        :return: a mock AWSAccount object.
        """
        return _get_account(request, volume_id)

    async def get_accounts(self, request: Request, volume_ids: Sequence[str]) -> AsyncIterator[tuple[AWSAccount, str]]:
        for volume_id in volume_ids:
            acct = await self.get_account(request, volume_id)
            if acct:
                yield acct, volume_id

    async def elevate_privileges(self, request: Request, credentials: AWSCredentials, lifespan: int | None = None) -> AWSCredentials:
        return AWSCredentials()


class MockS3WithMongo(S3, MockDatabase, Mongo):
    """
    Overrides the S3 class' methods use moto instead of actual AWS. It also stores volume and filesystem desktop
    objects in a mongo database. Moto is documented at https://github.com/spulec/moto.
    """

    async def generate_cloud_credentials(self, request: Request, arn: str, session_name: str,
                                         duration: int | None = None) -> AWSCredentials:
        """
        Create temporary credentials and return a newly created AWSCredentials object.

        :param request: the HTTP request (required).
        :param arn: The aws role arn that to be assumed (required).
        :param session_name: the session name to pass into AWS (required; typically is the user sub).
        :param duration: the time in seconds to assume the role. If None, it uses a default value, MIN_DURATION_SECONDS
        if the user is system|credentialsmanager, otherwise MAX_DURATION_SECONDS. The minimum is MIN_DURATION_SECONDS.
        :returns: an AWSCredentials object with the generated credentials.
        :raises ValueError: if an error occurs generating cloud credentials.
        """
        cred_dict_list: list[DesktopObjectDict] = []
        async for cred_dict in self.get_all(request, 'credentials'):
            cred_dict_list.append(cred_dict)
        cred = None
        if cred_dict_list and len(cred_dict_list) > 1:
            cred_dict = cred_dict_list[1]
            cred = AWSCredentials()
            cred.from_dict(cred_dict)
        elif cred_dict_list and len(cred_dict_list) == 1:
            cred_dict = cred_dict_list[0]
            cred = AWSCredentials()
            cred.from_dict(cred_dict)
        if cred is None:
            raise ValueError('No credentials')
        return cred

    async def get_account(self, request: Request, volume_id: str) -> AWSAccount | None:
        """
        Gets a mock AWS account.

        :param request: the HTTP request (required).
        :param volume_id: the volume id.
        :return: a mock AWSAccount object.
        """
        return _get_account(request, volume_id)


class MockS3WithMockMongo(S3, MockMongo):
    """
    Overrides the S3 class' methods use moto instead of actual AWS. It also stores volume and filesystem desktop
    objects in an in-memory data structure and mocks AWS microservices' attempts to access the file system and volumes
    microservices while requesting a boto3/moto client. Moto is documented at https://github.com/spulec/moto.
    """

    def __init__(self, config: Optional[Configuration], mongo: MockMongo | None = None, **kwargs):
        super().__init__(config=config, mongo=mongo, **kwargs)
        section = super().get_config_section()
        if config and section in config.parsed_config:
            database_section = config.parsed_config[section]
            self.__region_name: Optional[str] = database_section.get('RegionName', None)
            self.__aws_access_key_id: Optional[str] = database_section.get('AWSAccessKeyId', None)
            self.__aws_secret_access_key: Optional[str] = database_section.get('AWSSecretAccessKey', None)
            self.__expiration: Optional[str] = database_section.get('Expiration', None)
            self.__session_token: Optional[str] = database_section.get('SessionToken', None)
        else:
            self.__region_name = None
            self.__aws_access_key_id = None
            self.__aws_secret_access_key = None
            self.__expiration = None
            self.__session_token = None

    async def get_file_system_and_credentials_from_volume(self, request: Request, volume_id: str) -> tuple[
        AWSFileSystem, AWSCredentials | None]:
        """
        Gets an AWSFileSystem object and a credentials object either using the configuration passed into the
        constructor, or if not provided, the mock mongo in-memory database. If no credentials object is found, the
        AWSFileSystem and None are returned.

        :param request: the HTTP request (required).
        :param volume_id: the volume_id.
        :return: a tuple containing the file system and the credential object if found.
        """

        if self.__aws_secret_access_key is not None or self.__aws_access_key_id is not None:
            creds_ = AWSCredentials()
            creds_.where = self.__region_name
            creds_.account = self.__aws_access_key_id
            creds_.password = self.__aws_secret_access_key
            creds_.expiration = self.__expiration  # type:ignore[assignment]
            creds: AWSCredentials | None = creds_
        elif volume_id is None:
            creds = None
        else:
            creds = self._get_credential_by_volume(volume_id=volume_id)
        return AWSFileSystem(), creds

    async def get_credentials_from_volume(self, request: Request, volume_id: str | None) -> AWSCredentials | None:
        """
        Gets a credentials object either using the configuration passed into the constructor, or if not provided, the
        mock mongo in-memory database. If no credentials object is found, None is returned.

        :param request: the HTTP request (required).
        :param volume_id: the volume_id.
        :return: the credential object if found.
        """
        if self.__aws_secret_access_key is not None or self.__aws_access_key_id is not None:
            creds_ = AWSCredentials()
            creds_.where = self.__region_name
            creds_.account = self.__aws_access_key_id
            creds_.password = self.__aws_secret_access_key
            creds_.expiration = self.__expiration  # type:ignore[assignment]
            creds: AWSCredentials | None = creds_
        elif volume_id is None:
            creds = None
        else:
            creds = self._get_credential_by_volume(volume_id=volume_id)
        return creds

    async def get_volumes(self, request: Request, file_system_type_or_type_name: str | type[FileSystem],
                          account_ids: Sequence[str] | None = None) -> AsyncIterator[Volume]:
        """
        An asynchronous iterator of the volumes to which the user has access, retrieved from the mock mongo in-memory
        database.

        :param request: the HTTP request (required).
        :param file_system_type_or_type_name: filter by a file system type or type name (required).
        :return: an asynchronous iterator of Volume objects.
        """
        if isinstance(file_system_type_or_type_name, type) and issubclass(file_system_type_or_type_name, DesktopObject):
            file_system_type_name_ = file_system_type_or_type_name.get_type_name()
        else:
            file_system_type_name_ = str(file_system_type_or_type_name)
        for volume_dict in self.get_desktop_objects_by_collection('volumes'):
            if volume_dict.get('file_system_type', AWSFileSystem.get_type_name()) == file_system_type_name_:
                volume = Volume()
                volume.from_dict(volume_dict)
                if not account_ids or volume.account_id in account_ids:
                    yield volume

    async def get_property(self, app: web.Application, name: str) -> Property | None:
        """
        Gets the value of the requested property from the mock mongo in-memory database.

        :param app: the aiohttp web.Application object (required).
        :param name: the name of the property (required).
        :return: a Property object or None if not found.
        """
        prop_dict_list = [prop_dict for prop_dict in self.get_desktop_objects_by_collection('properties')
                          if prop_dict.get('name', None) == name]
        prop = None
        if prop_dict_list and len(prop_dict_list) > 0:
            prop_dict = prop_dict_list[0]
            prop = Property()
            prop.from_dict(prop_dict)
        return prop if prop else None

    async def update_credentials(self, request: Request, credentials: AWSCredentials) -> None:
        """
        This method is for updating the provided credentials object in the database, but this implementation does
        nothing.

        :param request: the HTTP request (required).
        :param credentials: the AWSCredentials to update (required).
        """
        pass

    async def get_account(self, request: Request, volume_id: str) -> AWSAccount | None:
        """
        Gets a mock AWS account.

        :return: a mock AWSAccount object.
        """
        return _get_account(request, volume_id)

    async def elevate_privileges(self, request: Request, credentials: AWSCredentials, lifespan: int | None = None) -> AWSCredentials:
        return AWSCredentials()

    def _get_credential_by_volume(self, volume_id: str) -> Optional[AWSCredentials]:
        volume_dict = self.get_desktop_object_by_collection_and_id('volumes', volume_id)
        if volume_dict is None:
            raise ValueError(f'No volume found with id {volume_id}')
        volume: Volume = Volume()
        volume.from_dict(volume_dict)
        if volume.credentials_id is None:
            creds: AWSCredentials | None = None
        else:
            credentials_dict = self.get_desktop_object_by_collection_and_id('credentials', volume.credentials_id)
            if credentials_dict is None:
                raise ValueError(f'No credentials with id {volume.credentials_id}')
            creds = AWSCredentials()
            creds.from_dict(credentials_dict)
        return creds


class MockS3Manager(S3Manager):
    """
    Database manager for mocking AWS S3 buckets with moto. Mark test fixture data that is managed in S3 buckets with
    this database manager in testing environments. Furthermore, connections to boto3/moto clients normally require
    access to the registry and volume microservices. This database manager does not mock those connections, and actual
    registry and volume microservices need to be running, as is typical in integration testing environments. For unit
    testing, see MockS3ManagerWithMockMongo, which also mocks the connections to the registry and volume microservices.
    """

    @classmethod
    def get_environment_updates(cls) -> dict[str, str]:
        result = super().get_environment_updates()
        result.update({'AWS_ACCESS_KEY_ID': 'testing',
                       'AWS_SECRET_ACCESS_KEY': 'testing',
                       'AWS_SECURITY_TOKEN': 'testing',
                       'AWS_SESSION_TOKEN': 'testing',
                       'AWS_DEFAULT_REGION': 'us-east-1'
                       })
        return result

    @classmethod
    def get_context(cls) -> list[AbstractContextManager]:
        result = super().get_context()
        result.extend([mock_aws(), freeze_time()])
        return result

    def get_database(self) -> S3:
        return MockS3(self.config, managed=True)

    def insert_desktop_objects(self, desktop_objects: Optional[Mapping[CollectionKey, Sequence[DesktopObjectDict]]]):
        super().insert_desktop_objects(desktop_objects)
        logger = logging.getLogger(__name__)

        for coll, objs in query_fixtures(desktop_objects, db_manager=self).items():
            logger.debug('Inserting %s collection object %s', coll, objs)
            inserters = self.get_desktop_object_inserters()
            if coll in inserters:
                inserters[coll](objs)

    def insert_content(self, content: Optional[Mapping[CollectionKey, Mapping[str, bytes]]]):
        super().insert_content(content)
        if content is not None:
            client = create_client('s3')
            try:
                for key, contents in query_content(content, db_manager=self).items():
                    if key == 'awss3files':
                        for id_, content_ in contents.items():
                            bucket_, actual_content = content_.split(b'|', 1)
                            bucket = bucket_.decode('utf-8')
                            with BytesIO(actual_content) as f:
                                client.upload_fileobj(Fileobj=f, Bucket=bucket, Key=decode_key(id_))
                    else:
                        raise KeyError(f'Unexpected key {key}')
            finally:
                client.close()

    @classmethod
    def get_desktop_object_inserters(cls) -> dict[str, Callable[[list[DesktopObjectDict]], None]]:
        return {'buckets': cls.__bucket_inserter,
                'awss3folders': cls.__awss3folder_inserter,
                'awss3files': cls.__awss3file_inserter}

    @classmethod
    def __organization_inserter(cls):
        cls.__create_organization()

    @classmethod
    def __awsaccount_inserter(cls):
        pass  # moto automatically creates one account to use. Creating your own accounts doesn't seem to work.


    @classmethod
    def __awss3file_inserter(cls, v):
        for awss3file_dict in v:
            awss3file = AWSS3FileObject()
            awss3file.from_dict(awss3file_dict)
            cls.__create_awss3file(awss3file)

    @classmethod
    def __awss3folder_inserter(cls, v):
        for awss3folder_dict in v:
            awss3folder = AWSS3Folder()
            awss3folder.from_dict(awss3folder_dict)
            cls.__create_awss3folder(awss3folder)

    @classmethod
    def __bucket_inserter(cls, v):
        for bucket_dict in v:
            awsbucket = AWSBucket()
            awsbucket.from_dict(bucket_dict)
            cls.__create_bucket(awsbucket)

    @staticmethod
    def __create_organization():
        client = boto3.client('organizations')
        try:
            client.create_organization(FeatureSet='ALL')
        finally:
            client.close()

    @staticmethod
    def __create_bucket(bucket: AWSBucket):
        client = create_client('s3')
        try:
            if bucket is not None:
                if bucket.name is None:
                    raise ValueError('bucket.name cannot be None')
                else:
                    if bucket.region != 'us-east-1' and bucket.region:
                        client.create_bucket(Bucket=bucket.name,
                                            CreateBucketConfiguration={'LocationConstraint': bucket.region})
                    else:
                        client.create_bucket(Bucket=bucket.name)
                    client.put_bucket_versioning(Bucket=bucket.name,
                                                VersioningConfiguration={'MFADelete': 'Disabled', 'Status': 'Enabled'})
        finally:
            client.close()

    @staticmethod
    def __create_awss3folder(awss3folder: AWSS3Folder):
        assert awss3folder.bucket_id is not None, 'awss3file must have a non-None bucket_id attribute'
        assert awss3folder.key is not None, 'awss3file must have a non-None key attribute'
        client = create_client('s3')
        try:
            client.put_object(Bucket=awss3folder.bucket_id, Key=awss3folder.key, StorageClass='STANDARD')
        finally:
            client.close()

    @staticmethod
    def __create_awss3file(awss3file: AWSS3FileObject):
        assert awss3file.bucket_id is not None, 'awss3file must have a non-None bucket_id attribute'
        assert awss3file.key is not None, 'awss3file must have a non-None key attribute'
        assert awss3file.storage_class is not None and awss3file.storage_class.name is not None, 'awss3file must have a non-None storage_class with a non-None name attribute'
        client = create_client('s3')
        try:
            storage_class_name = cast(StorageClassType, awss3file.storage_class.name)
            client.put_object(Bucket=awss3file.bucket_id, Key=awss3file.key, StorageClass=storage_class_name)
        finally:
            client.close()



class MockS3WithMockMongoManager(MockS3Manager, MockMongoManager):
    """
    Database manager for mocking AWS S3 buckets with moto. Mark test fixture data that is managed in S3 buckets with
    this database manager in unit test environments. Furthermore, connections to boto3/moto clients normally require
    access to the registry and volume microservices. This database manager mocks those connections. Mark
    component, volume, and filesystem test collections with this database manager to make them available in unit
    testing environments. This class is not designed to be subclassed.
    """

    def get_database(self) -> MockS3WithMockMongo:
        return MockS3WithMockMongo(config=self.config, mongo=self.get_mongo(), managed=True)

    @classmethod
    def database_types(self) -> list[str]:
        return ['system|awss3', 'system|mongo']


def _get_account(request: Request, volume_id: str) -> AWSAccount | None:
    """
    Gets a mock AWS account.

    :return: a mock AWSAccount object.
    """
    account_id = '123456789012'
    a = AWSAccount()
    a.id = account_id
    a.display_name = account_id
    a.name = 'master'
    a.owner = AWS_USER
    a.source = AWS
    a.source_detail = AWS
    a.email_address = 'master@example.com'

    return a
