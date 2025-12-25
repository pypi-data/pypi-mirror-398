from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import partial
from aiohttp.web import Request
from aiohttp import ClientResponseError
import boto3
import botocore
from aiohttp import hdrs, web
from botocore.exceptions import ClientError, ParamValidationError
from mypy_boto3_iam import IAMClient
from mypy_boto3_iam.type_defs import PolicyDocumentDictTypeDef
from mypy_boto3_s3 import S3Client
from mypy_boto3_sqs import SQSClient
from mypy_boto3_sts import STSClient
from mypy_boto3_account import AccountClient
from mypy_boto3_organizations import OrganizationsClient

from heaserver.service.config import Configuration
from ..appproperty import HEA_DB
from .database import DatabaseContextManager, MicroserviceDatabaseManager, get_credentials_from_volume, Database
from .mongo import Mongo
from ..oidcclaimhdrs import SUB
from ..sources import AWS as AWS_SOURCE
from heaobject.root import Permission, Share, ShareImpl, DesktopObject
from heaobject.aws import S3Object, AWSDesktopObject, AmazonResourceName
from heaobject.account import AWSAccount, AWSAccountCollaborators
from heaobject.keychain import AWSCredentials, Credentials
from heaobject.registry import Property
from heaobject.volume import AWSFileSystem, FileSystem
from heaobject.user import AWS_USER, CREDENTIALS_MANAGER_USER, NONE_USER
from heaobject.person import Person, AccessToken
from ..heaobjectsupport import type_to_resource_url, HEAServerPermissionContext
from ..util import async_retry, now, LockManager
from ..aiohttp import extract_sub
from .. import client
from yarl import URL
from typing import Optional, TypeVar, cast, overload, Literal, TypedDict, NotRequired, Unpack
import asyncio
from threading import Lock
from collections.abc import AsyncGenerator, Iterable, Sequence, AsyncIterator
from copy import copy, deepcopy
from .awsaction import *
from cachetools import TTLCache
from datetime import timedelta
from base64 import urlsafe_b64encode
from cachetools import TTLCache
from collections import defaultdict
import logging

CLIENT_ERROR_NO_SUCH_BUCKET = 'NoSuchBucket'
CLIENT_ERROR_ACCESS_DENIED = 'AccessDenied'
CLIENT_ERROR_ACCESS_DENIED2 = 'AccessDeniedException'
CLIENT_ERROR_FORBIDDEN = '403'
CLIENT_ERROR_404 = '404'
CLIENT_ERROR_ALL_ACCESS_DISABLED = 'AllAccessDisabled'
CLIENT_ERROR_NO_SUCH_KEY = 'NoSuchKey'
CLIENT_ERROR_INVALID_OBJECT_STATE = 'InvalidObjectState'
CLIENT_ERROR_NO_SUCH_ENTITY = 'NoSuchEntity'
CLIENT_ERROR_ENTITY_ALREADY_EXISTS = 'EntityAlreadyExists'
CLIENT_ERROR_BUCKET_NOT_EMPTY = 'BucketNotEmpty'
CLIENT_ERROR_RESTORE_ALREADY_IN_PROGRESS = 'RestoreAlreadyInProgress'

ServiceName = Literal['s3', 'iam', 'sts', 'account', 'organizations', 'sqs']

_boto3_client_lock = Lock()
_boto3_client_config = botocore.config.Config(max_pool_connections=25, retries={'max_attempts': 10, 'mode': 'adaptive'})

_permission_for = {
    S3_GET_OBJECT: Permission.VIEWER,
    S3_PUT_OBJECT: Permission.EDITOR,
    S3_DELETE_OBJECT: Permission.DELETER,
    S3_GET_OBJECT_TAGGING: Permission.VIEWER,
    S3_PUT_OBJECT_TAGGING: Permission.EDITOR,
    S3_LIST_BUCKET: Permission.VIEWER,
    S3_CREATE_BUCKET: Permission.EDITOR,
    S3_DELETE_BUCKET: Permission.DELETER,
    S3_GET_BUCKET_TAGGING: Permission.VIEWER,
    S3_PUT_BUCKET_TAGGING: Permission.EDITOR,
    S3_LIST_OBJECT_VERSIONS: Permission.VIEWER,
    S3_DELETE_OBJECT_VERSION: Permission.DELETER
}

AWSDesktopObjectTypeVar = TypeVar('AWSDesktopObjectTypeVar', bound=AWSDesktopObject)
AWSDesktopObjectTypeVar_cov = TypeVar('AWSDesktopObjectTypeVar_cov', bound=AWSDesktopObject, covariant=True)
S3ObjectTypeVar = TypeVar('S3ObjectTypeVar', bound=S3Object)

class CreatorKwargs(TypedDict):
    region_name: NotRequired[str | None]
    aws_access_key_id: NotRequired[str | None]
    aws_secret_access_key: NotRequired[str | None]
    aws_session_token: NotRequired[str | None]


class AWSPermissionContext(HEAServerPermissionContext, ABC):
    """
    Helper class for desktop objects' permissions-related methods that require external information, such as the
    current user.
    """

    def __init__(self, request: Request, actions: Sequence[str], **kwargs):
        """
        Accepts an HTTP Request, a volume id, and actions to check. Any additional keyword
        arguments will be passed onto the next class in the method resolution order.

        :param request: the HTTP request (required). It may have a volume_id path parameter.  The OIDC_CLAIM_sub header
        must be present, and the Authorization header must also be present unless the OIDC_CLAIM_sub is the
        system|credentialsmanager user.
        :param actions: the actions to check.
        """
        if request is None:
            raise ValueError('request is required')
        volume_id = request.match_info.get('volume_id')
        sub = request.headers.get(SUB, NONE_USER)
        super().__init__(sub=sub, request=request, **kwargs)
        self.__volume_id = str(volume_id) if volume_id is not None else None
        self.__actions = copy(actions)
        self.__credentials: AWSCredentials | None = None
        self.__is_account_owner: bool | None = None
        self.__cache: TTLCache[str, list[Permission]] = TTLCache(maxsize=128, ttl=30)
        self.__credentials_lock = asyncio.Lock()
        self.__get_perms_locks: LockManager[str] = LockManager()

    @property
    def volume_id(self) -> str | None:
        """The id of the volume, if it was a path parameter in the request."""
        return self.__volume_id

    async def credentials(self) -> AWSCredentials | None:
        """
        Returns the credentials corresponding to the volume id in the path parameter in the request, if found.

        :return: an AWSCredentials object.
        """
        if (volume_id := self.volume_id) is None:
            return None
        async with self.__credentials_lock:
            if self.__credentials is None:
                logger = logging.getLogger(__name__)
                logger.debug('Getting credentials to check permissions')
                s3_db = cast(S3, self.request.app[HEA_DB])
                aws_creds = await s3_db.get_credentials_from_volume(self.request, volume_id)
                self.__credentials = cast(AWSCredentials, aws_creds)
            return deepcopy(self.__credentials)

    async def is_account_owner(self) -> bool:
        """
        Returns whether the user who submitted the request is the owner of the AWS account associated with the volume.

        :return: True or False.
        """
        if self.__is_account_owner is None:
            self.__is_account_owner = await cast(S3, self.request.app[HEA_DB]).is_account_owner(self.request, credentials=await self.credentials())
        return self.__is_account_owner

    async def get_permissions(self, obj: DesktopObject) -> list[Permission]:
        """
        Gets the user's permissions for a desktop object. For AWS objects, is determines permissions by calling AWS
        SimulatePrincipalPolicy. The object's ARN is passed into SimulatePrincipalPolicy, and this method must only be
        called after the attributes needed to create the ARN are populated.

        :param obj: the desktop object (required).
        :return: a list of Permissions, or the empty list if there is none.
        """
        logger = logging.getLogger(__name__)
        if not isinstance(obj, AWSDesktopObject):
            logger.debug('Not an AWS object; delegating: %r', obj)
            return await super().get_permissions(obj)
        # While we don't require that an object has been persisted to get its permissions, per the docstring the
        # instance_id attribute will be non-None when the attributes needed to compute an ARN are populated.
        obj_str = obj.instance_id
        if not obj_str:
            raise ValueError('obj.instance_id cannot be None')
        async with self.__get_perms_locks.lock(obj_str):  # don't need to cache on sub because the sub can't be changed.
            perms = self.__cache.get(obj_str)
            if perms is None:
                if not await self.is_account_owner():
                    perms = await self._simulate_perms(obj, self.__actions)
                else:
                    perms = [Permission.COOWNER]
                self.__cache[obj_str] = perms
            logger.debug('AWS permission context got permissions %s for desktop object %r', perms, obj)
            return copy(perms)

    async def _simulate_perms(self, obj: AWSDesktopObject, actions: Sequence[str]) -> list[Permission]:
        """
        Calls SimulatePrincipalPolicy with the provided object's ARN and the specified actions, calling
        heaserver.service.db.aws.S3.elevate_privileges() to pass suitable credentials to AWS. The object's ARN is
        passed into SimulatePrincipalPolicy, and this method should only be called after the attributes needed to
        create the ARN are populated.

        :param obj: the desktop object to check (required).
        :param actions: the actions to check (required).
        :return: the requester's permissions for the provided desktop object. If there was no volume in the request's
        path parameters, it returns the empty list.
        """
        logger = logging.getLogger(__name__)
        credentials = await self.credentials()
        if not credentials:
            return []
        try:
            logger.debug('Elevating privileges to check permissions for desktop object %r', obj)
            admin_credentials = await self.request.app[HEA_DB].elevate_privileges(self.request, credentials)
        except ValueError:
            logger.exception("Error getting elevated privileges, will fall back to the user's privileges")
            admin_credentials = credentials
        logger.debug('Privileges for simulating permissions are %r for desktop object %r', admin_credentials, obj)
        perms: list[Permission] = []
        async with IAMClientContext(request=self.request, credentials=admin_credentials) as iam_client:
            loop = asyncio.get_running_loop()
            try:
                assert credentials.role is not None, 'role attribute cannot be None'
                caller_arn = self._caller_arn(obj)
                logger.debug('Checking permissions for caller ARN %s for policy source ARN %s and actions %s', caller_arn, credentials.role, actions)
                response_ = await loop.run_in_executor(None, partial(iam_client.simulate_principal_policy,
                                                                     PolicySourceArn=credentials.role,
                                                                     ActionNames=actions,
                                                                     ResourceArns=[caller_arn] if not caller_arn.endswith('/') else [caller_arn + '*']))
                logger.debug('Response for checking %s: %s', actions, response_)
                for results in response_['EvaluationResults']:
                    if results['EvalDecision'] == 'allowed':
                        if perm := _permission_for.get(results['EvalActionName']):
                            perms.append(perm)
            except ClientError as e:
                status, _ = client_error_status(e)
                if status == 403:
                    logger.exception("Access denied simulating the user's privileges; falling back to pretending the user has full access "
                                     "(AWS will deny them when they try to do something they lack permission to do)")
                    perms.extend([Permission.VIEWER, Permission.EDITOR, Permission.DELETER])
                else:
                    raise e
        return perms

    @abstractmethod
    def _caller_arn(self, obj: AWSDesktopObject) -> str:
        """
        Returns a desktop object's ARN.

        :param obj: the desktop object (required).
        :return: the ARN.
        """
        pass


class S3ObjectPermissionContext(AWSPermissionContext):
    """
    AWS S3 object permission context. It sets attribute permissions on S3 objects and provides an object ARN.
    """

    def __init__(self, request: Request, **kwargs):
        """
        Creates a permission context from the provided HTTP request.

        :param request: the HTTP request (required). It must have a volume_id path parameter.
        """
        actions = [S3_GET_OBJECT, S3_PUT_OBJECT, S3_DELETE_OBJECT]
        super().__init__(request=request, actions=actions, **kwargs)

    async def get_permissions(self, obj: DesktopObject) -> list[Permission]:
        """
        Gets the user's permissions for a desktop object by calling AWS SimulatePrincipalPolicy. The object's ARN is
        passed into SimulatePrincipalPolicy, and this method should only be called after the attributes needed to
        create the ARN are populated. If not an S3 object, this class delegates to the AWS permission context.

        :param obj: the object (required).
        :return: a list of Permissions, or the empty list if there is none.
        """
        logger = logging.getLogger(__name__)
        logger.debug('S3 object permission context getting permissions for desktop object %r', obj)
        if logger.isEnabledFor(logging.DEBUG) and not isinstance(obj, S3Object):
            logger.debug('Not an S3 object: %r', obj)
        return await super().get_permissions(obj)

    async def get_attribute_permissions(self, obj: DesktopObject, attr: str) -> list[Permission]:
        """
        Dynamically sets permissions for the tags and display_name attributes based on the user's account ownership,
        simulated AWS permissions, and archived status, otherwise it returns default attribute permissions based on
        object-level permissions.

        :param obj: the object (required).
        :param attr: the attribute to check (required).
        :return: the permissions for the given object attribute.
        """
        if not isinstance(obj, S3Object):
            return []
        if attr == 'tags' and not await self.is_account_owner():
            return await self._simulate_perms(obj, [S3_GET_OBJECT_TAGGING, S3_PUT_OBJECT_TAGGING])
        elif attr == 'display_name' and (((retrievable := getattr(obj, 'retrievable', None)) is not None and not retrievable) or \
                (Permission.DELETER not in await self._simulate_perms(obj, [S3_DELETE_OBJECT_VERSION]))):
            # Archived objects and objects in the process of being restored can only be viewed. For objects where the
            # archive status is unknown, we fall back to the default permissions, which is appropriate for folders, for
            # which archive status does not apply. This could result in a file's display_name getting write permissions
            # when it should not if the archive status is erroneously left unset, but AWS will reject attempts to
            # delete an archived object, renaming an S3 object involves a copy followed by a delete, and our move code
            # checks archive status during preflight.
            return [Permission.VIEWER]
        else:
            return await super().get_attribute_permissions(obj, attr)

    def _caller_arn(self, obj: AWSDesktopObject) -> str:
        """
        The object's Amazon Resource Name (ARN).

        :param obj: the object (required).
        :return: the ARN.
        """
        return f'arn:aws:s3:::{obj.resource_type_and_id}'

class S3(Database):
    """
    Connectivity to AWS (not just S3!) for HEA microservices.
    """
    # this is the buffer we give to refresh credentials in minutes on our end before they expire on aws
    MAX_EXPIRATION_LIMIT = 540
    MIN_EXPIRATION_LIMIT = 11

    # Min and max durations for assuming a role, such as in privilege elevation.
    MAX_DURATION_SECONDS = 43200
    MIN_DURATION_SECONDS = 900

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.__temp_cred_locks: LockManager[str | None] = LockManager()
        self.__elev_priv_locks: LockManager[tuple[str, str]] = LockManager()
        self.__admin_creds: TTLCache[tuple[str, str], AWSCredentials] = TTLCache(maxsize=128, ttl=self.MIN_DURATION_SECONDS)  # (sub, role arn) -> AWSCredentials.
        self.__account_cache: TTLCache[tuple[str, str], AWSAccount] = TTLCache(maxsize=128, ttl=30)  # (sub, volume_id) -> AWSAccount.
        self.__sts_client: STSClient | None = None  # Global STS client for assuming roles.
        self.__sts_client_asyncio_lock = asyncio.Lock()
        self.__temp_cred_session_cache: TTLCache[str, boto3.session.Session] = TTLCache(maxsize=128, ttl=30)
        # Sub and volume-id -> credentials. We include the sub to preserve permissions.
        self.__volume_id_to_credentials: TTLCache[tuple[str, str], Credentials | None] = TTLCache(maxsize=128, ttl=30)
        self.__is_account_owner: bool | None = None

    @property
    def file_system_type(self) -> type[FileSystem]:
        return AWSFileSystem

    async def get_credentials_from_volume(self, request: web.Request, volume_id: str) -> Credentials | None:
        sub = extract_sub(request)
        if (credentials := self.__volume_id_to_credentials.get((sub, volume_id))) is not None:
            return credentials
        else:
            # mypy can't seem to distinguish between this method and the module-level function.
            credentials = await get_credentials_from_volume(request, volume_id, AWSCredentials)  # type:ignore[func-returns-value]
            self.__volume_id_to_credentials[(sub, volume_id)] = credentials
            return credentials

    async def is_account_owner(self, request: web.Request, credentials: AWSCredentials | None = None) -> bool:
        """
        Returns whether the user who submitted the request is the owner of the AWS account associated with the volume.

        :return: True or False.
        """
        if self.__is_account_owner is None:
            self.__is_account_owner = await is_account_owner(request, credentials=credentials)
        return self.__is_account_owner

    async def update_credentials(self, request: Request, credentials: AWSCredentials) -> None:
        """
        Obtains the keychain microservice's url from the registry and executes a PUT call to update the credentials
        object. It executes the PUT call as the system|awscredentialsmanager user.

        :param request: the HTTP request (required).
        :param credentials: the AWS credentials to update (required). It must have been previously persisted.
        :raises ValueError: if there was a problem accessing the registry service or the credentials service was not
        found.
        :raises ClientResponseError: if there was a problem making the PUT request.
        """
        if credentials.id is None:
            raise ValueError(f'credentials must have a non-None id attribute')
        resource_url = await type_to_resource_url(request, AWSCredentials)
        headers = {SUB: CREDENTIALS_MANAGER_USER}
        try:
            await client.put(app=request.app, url=URL(resource_url) / credentials.id, data=credentials,
                            headers=headers)
        except ClientResponseError as e:
            raise ValueError(f'Updating credentials failed: {e}') from e

    @overload
    async def get_client(self, request: Request, service_name: Literal['s3'], volume_id: str | None = None,
                         credentials: AWSCredentials | None = None) -> S3Client:
        ...

    @overload
    async def get_client(self, request: Request, service_name: Literal['iam'], volume_id: str | None = None,
                         credentials: AWSCredentials | None = None) -> IAMClient:
        ...

    @overload
    async def get_client(self, request: Request, service_name: Literal['sts'], volume_id: str | None = None,
                         credentials: AWSCredentials | None = None) -> STSClient:
        ...

    @overload
    async def get_client(self, request: Request, service_name: Literal['account'], volume_id: str | None = None,
                         credentials: AWSCredentials | None = None) -> AccountClient:
        ...

    @overload
    async def get_client(self, request: Request, service_name: Literal['organizations'], volume_id: str | None = None,
                         credentials: AWSCredentials | None = None) -> OrganizationsClient:
        ...

    @overload
    async def get_client(self, request: Request, service_name: Literal['sqs'], volume_id: str | None = None,
                         credentials: AWSCredentials | None = None) -> SQSClient:
        ...

    async def get_client(self, request: Request, service_name: ServiceName, volume_id: str | None = None,
                         credentials: AWSCredentials | None = None) -> S3Client | IAMClient | STSClient | AccountClient | OrganizationsClient | SQSClient:
        """
        Gets an AWS service client.  If the volume has no credentials, it uses the boto3 library to try and find them.
        This method is not designed to be overridden.

        :param request: the HTTP request (required). The request must have a valid OIDC_CLAIM_sub header, and if using
        temporary credentials, it must also have a valid Authorization header unless the OIDC_CLAIM_sub is the
        system|credentialsmanager user.
        :param service_name: AWS service name (required).
        :param volume_id: the id string of a volume (required unless you pass a credentials object or you intend for
        boto3 to look up credentials information).
        :return: a Mongo client for the file system specified by the volume's file_system_name attribute. If no volume_id
        was provided, the return value will be the "default" Mongo client for the microservice found in the HEA_DB
        application-level property.
        :param credentials: optional AWSCredentials. If none is provided, boto3 will be used to look up credentials
        information.
        :raise ValueError: if there is no volume with the provided volume id, the volume's file system does not exist,
        the volume's credentials were not found, or a necessary service is not registered.

        TODO: need a separate exception thrown for when a service is not registered (so that the server can respond with a 500 error).
        TODO: need to lock around client creation because it's not threadsafe, manifested by sporadic KeyError: 'endpoint_resolver'.
        """
        if credentials is None and volume_id is not None:
            credentials_ = await self.get_credentials_from_volume(request, volume_id)
            if credentials_ is not None and not isinstance(credentials_, AWSCredentials):
                raise ValueError(f'Credentials for volume {volume_id} not an AWSCredentials object')
            credentials = credentials_
        match service_name:
            case 's3':
                return await self.__get_resource_or_client(request, 's3', credentials)
            case 'iam':
                return await self.__get_resource_or_client(request, 'iam', credentials)
            case 'sts':
                return await self.__get_resource_or_client(request, 'sts', credentials)
            case 'account':
                return await self.__get_resource_or_client(request, 'account', credentials)
            case 'organizations':
                return await self.__get_resource_or_client(request, 'organizations', credentials)
            case 'sqs':
                return await self.__get_resource_or_client(request, 'sqs', credentials)
            case _:
                raise ValueError(f'Unexpected service_name {service_name}')

    async def has_account(self, request: Request, volume_id: str) -> bool:
        """
        Return whether the current user can access the AWS accounts associated with the provided volume_id.

        :param request: the HTTP request object (required).
        :param volume_id: the volume id (required).
        :return: True or False.
        :raises ValueError: if an error occured getting account information.
        """
        sub = request.headers.get(SUB, NONE_USER)
        key = (sub, volume_id)
        account = self.__account_cache.get(key)
        if account is None:
            try:
                async with STSClientContext(request, volume_id=volume_id) as sts_client:
                    account = await self._get_basic_account_info(sts_client)
            except ClientError as e:
                raise ValueError(f'Unexpected error getting account information for volume {volume_id}') from e
        return account is not None

    async def get_account(self, request: Request, volume_id: str) -> AWSAccount | None:
        """
        Gets the current user's AWS account associated with the provided volume_id. The returned account has an owner
        but no assigned invites nor shares.

        :param request: the HTTP request object (required). The request must have valid OIDC_CLAIM_sub header, and
        unless the OIDC_CLAIM_sub is the system|credentialsmanager user, it must also have a valid Authorization
        header.
        :param volume_id: the volume id (required).
        :return: the AWS account, or None if not found.
        :raises ValueError: if an error occurred getting account information.
        """
        logger = logging.getLogger(__name__)
        loop = asyncio.get_running_loop()
        credentials = await self.get_credentials_from_volume(request, volume_id)
        if credentials is not None and not isinstance(credentials, AWSCredentials):
            raise ValueError(f'Credentials for volume {volume_id} not an AWSCredentials object')
        logger.debug('Got credentials %s for volume %s', credentials, volume_id)
        sub = request.headers.get(SUB, NONE_USER)
        key = (sub, volume_id)
        account = self.__account_cache.get(key)

        if account is None:
            try:
                async with STSClientContext(request, credentials=credentials) as sts_client:
                    account = await self._get_basic_account_info(sts_client)
                    aid = account.id
                async with S3ClientContext(request, credentials=credentials) as s3_client:
                    buckets = await asyncio.to_thread(s3_client.list_buckets)
                elevated_credentials = await request.app[HEA_DB].elevate_privileges(request, credentials) if credentials is not None else None
                async with IAMClientContext(request, credentials=elevated_credentials) as iam_client:
                    bucket_names = (bucket_info['Name'] for bucket_info in buckets.get('Buckets', []))
                    async for bucket_name, collaborator_ids in _get_bucket_collaborators(iam_client, bucket_names):
                        account.add_collaborators_to(AWSAccountCollaborators(bucket_id=bucket_name,
                                                                              collaborator_ids=collaborator_ids))
                self.__account_cache[key] = account
            except ClientError:
                logger.debug(f'Error getting account for volume {volume_id}', exc_info=True)
                return None
        else:
            return deepcopy(account)

        async def populate_contact_info():
            try:
                async with AccountClientContext(request, credentials=credentials) as account_client:
                    contact_info = await loop.run_in_executor(None, partial(account_client.get_contact_information, AccountId=aid))
                    account.full_name = contact_info.get('FullName')
                    account.phone_number = contact_info.get('PhoneNumber')
            except ClientError as e:
                code = e.response['Error']['Code']
                if code != 'AccessDeniedException':
                    logger.exception('Client error %s', code)
                    raise ValueError(f'Unexpected error getting contact information for account') from e
                logger.debug('Account is not authorized to access contact information')

        async def populate_organization_info():
            try:
                async with OrganizationsClientContext(request, credentials=credentials) as org_client:
                    account_info = await loop.run_in_executor(None, partial(org_client.describe_account, AccountId=aid))
                    account_info_ = account_info['Account']
                    account.name = account_info_.get('Name')
                    account.email_address = account_info_.get('Email')
            except ParamValidationError:
                logger.debug('Account %s is not part of an organization', aid, exc_info=True)
            except ClientError as e:
                code = e.response['Error']['Code']
                if code != 'AccessDeniedException':
                    logger.exception('Client error %s', code)
                    raise ValueError(f'Unexpected error getting organization-level information for account') from e
                logger.debug('Account is not authorized to access organization-level account information')

        await asyncio.gather(populate_contact_info(), populate_organization_info())

        # account.created = user['CreateDate']
        # FIXME this info coming from Alternate Contact(below) gets 'permission denied' with IAMUser even with admin level access
        # not sure if only root account user can access. This is useful info need to investigate different strategy
        # alt_contact_resp = account_client.get_alternate_contact(AccountId=account.id, AlternateContactType='BILLING' )
        # alt_contact =  alt_contact_resp.get("AlternateContact ", None)
        # if alt_contact:
        # account.full_name = alt_contact.get("Name", None)

        return account

    async def get_accounts(self, request: Request, volume_ids: Sequence[str]) -> AsyncIterator[tuple[AWSAccount, str]]:
        """
        Gets the AWS accounts associated with the provided volume ids.

        :param request: the HTTP request object (required). The request must have a valid OIDC_CLAIM_sub header, and
        unless the OIDC_CLAIM_sub is the system|credentialsmanager user, it must also have a valid Authorization
        header.
        :param volume_ids: the volume ids (required).
        :return: an async iterator of tuples containing the AWS accounts and corresponding volume ids.
        """
        logger = logging.getLogger(__name__)

        async def execute(volume_id: str) -> tuple[AWSAccount | None, str]:
            return await self.get_account(request, volume_id), volume_id

        for i, acct_vol in enumerate(await asyncio.gather(*(execute(volume_id) for volume_id in volume_ids),
                                                                return_exceptions=True)):
            if not isinstance(acct_vol, tuple):
                if isinstance(acct_vol, ValueError):
                    logger.error('Error getting account for volume %s', volume_ids[i], exc_info=acct_vol)
                    continue
                else:
                    raise acct_vol
            acct, vol = acct_vol
            if acct is not None:
                yield acct, vol

    async def generate_cloud_credentials(self, request: Request, arn: str, session_name: str,
                                         duration: int | None = None) -> AWSCredentials:
        """
        Create temporary credentials and return a newly created AWSCredentials object. If the user who made the request
        is system|credentialsmanager, which can only happen in internal calls between microservices where the only
        available Authorization header would be from the logged-in user, a token is requested from the people service
        to use for assuming an AWS role. Otherwise, the Bearer token passed in the request in the Authorization header
        or the access_token query parameter is used to assume the role.

        :param request: the HTTP request (required). The request must have a valid OIDC_CLAIM_sub header, and it must
        also have a valid Authorization header unless the OIDC_CLAIM_sub is the system|credentialsmanager user.
        :param arn: The aws role arn that to be assumed (required).
        :param session_name: the session name to pass into AWS (required; typically is the user sub).
        :param duration: the time in seconds to assume the role. If None, it uses a default value, MIN_DURATION_SECONDS
        if the user is system|credentialsmanager, otherwise MAX_DURATION_SECONDS. The minimum is MIN_DURATION_SECONDS.
        :returns: an AWSCredentials object with the generated credentials.
        :raises ValueError: if an error occurs generating cloud credentials.
        """
        logger = logging.getLogger(__name__)
        sub = request.headers.get(SUB, None)
        if duration is None:
            duration = self.MIN_DURATION_SECONDS if sub == CREDENTIALS_MANAGER_USER else self.MAX_DURATION_SECONDS

        logger.debug("In generate_credentials sub is %s" % sub)
        if sub is None:
            raise ValueError('OIDC SUB header is required')
        if not arn:
            raise ValueError('Cannot get credentials arn which is required')

        logger.debug('Getting credentials for user %s with role %s...', sub, arn)
        try:
            if sub == CREDENTIALS_MANAGER_USER:
                resource_url = await type_to_resource_url(request, Person)
                logger.debug("url for token for people: %s" % (URL(resource_url) / 'internal' / 'token'))
                token_obj = await client.get(app=request.app, type_or_obj=AccessToken,
                                            url=URL(resource_url) / 'internal' / 'token',
                                            headers=request.headers)
                if token_obj is None:
                    raise ValueError('Internal token not found')
                if token_obj.auth_scheme is None:
                    raise ValueError("Internal token's auth_scheme cannot be None")
                if token_obj.id is None:
                    raise ValueError("Internal token's id cannot be None")
                auth_token = [token_obj.auth_scheme, token_obj.id]
            else:
                auth = request.headers.get(hdrs.AUTHORIZATION, '')
                auth_token = auth.split(' ')
                if len(auth_token) != 2:
                    access_token = request.query.get('access_token')
                    if access_token:
                        auth_token = ['Bearer', access_token]

            if len(auth_token) != 2:
                raise ValueError(f"Authorization token is required but was {auth_token}")

            logger.debug('User %s has role %s', sub, arn)
            loop = asyncio.get_running_loop()

            @async_retry(ClientError)
            async def call_assume_role_with_web_identity():
                sts_client = await self.__get_sts_client(loop)
                logger.debug('Assuming role %s for duration %s', arn, duration)
                return await loop.run_in_executor(None, partial(sts_client.assume_role_with_web_identity,
                                                                WebIdentityToken=auth_token[1],
                                                                RoleArn=arn,
                                                                RoleSessionName=urlsafe_b64encode(session_name.encode('utf-8')).decode('utf-8'),
                                                                DurationSeconds=duration))
            creds = AWSCredentials()
            creds.temporary = True
            # Don't use the expiration from the AWS response. If the AWS time is slightly off compared to our server time,
            # the AWS response expiration could appear to be too far in the future, and setting the credentials' expiration
            # would raise a ValueError. Similarly, if the AWS time is earlier than our server time, the credentials could
            # expire before we expect them to.
            #
            # We extend the expiration here, which could result in an expiration that is slightly shorter than the AWS
            # expiration, but we want to err on the side of a too short expiration.
            creds.extend(duration)
            assumed_role_object = await call_assume_role_with_web_identity()
            creds_dict = assumed_role_object.get('Credentials')
            if not creds_dict:
                raise ValueError('No credentials returned from AWS')

            creds.account = creds_dict['AccessKeyId']
            creds.password = creds_dict['SecretAccessKey']
            creds.session_token = creds_dict['SessionToken']
            creds.role = arn
            return creds
        except ClientError as ce:
            raise ValueError(f'User {sub} does not have role {arn}') from ce
        except ClientResponseError as cre:
            raise ValueError('Token cannot be obtained') from cre
        except Exception as e:
            raise ValueError('Error generating cloud credentials') from e

    def really_close(self):
        super().really_close()
        if self.__sts_client is not None:
            self.__sts_client.close()

    def close(self):
        super().close()
        if self.__sts_client is not None and not self.managed:
            self.__sts_client.close()

    async def elevate_privileges(self, request: web.Request, credentials: AWSCredentials,
                                 lifespan: int | None = None) -> AWSCredentials:
        """
        Returns an ephemeral credentials object with admin-level privileges for the same account as the given user
        credentials object. It relies on the registry service's AWS_ADMIN_ROLE property being set to the AWS admin
        role, otherwise this method will raise a ValueError. After generating the credentials, it will return the same
        credentials until close to its expiration.

        If the user who made the request is system|credentialsmanager, which can only happen in internal calls between
        microservices where the only available Authorization header would be from the logged-in user, a token is
        requested from the people service to use for assuming an AWS role. Otherwise, the Bearer token passed in the
        request in the Authorization header or the access_token query parameter is used to assume the role.

        :param request: the HTTP request (required). The request must have a valid OIDC_CLAIM_sub header, and it must
        also have a valid Authorization header unless the OIDC_CLAIM_sub is the system|credentialsmanager user.
        :param aws_cred: the user's AWS credentials.
        :param lifespan: the length of privilege elevation in seconds. If None, a default value is used,
        MIN_DURATION_SECONDS. The minimum value is MIN_DURATION_SECONDS.
        :return: the account id and an ephemeral credentials object. The credentials object's role attribute cannot be
        None.
        :raises ValueError: if privilege elevation failed.
        """
        sub = request.headers.get(SUB, NONE_USER)
        if lifespan is None:
            lifespan = self.MIN_DURATION_SECONDS
        assert credentials.role is not None, 'credentials.role cannot be None'
        admin_role = await self.__get_admin_aws_role_arn(request, credentials.role)
        key = (sub, admin_role)
        async with self.__elev_priv_locks.lock(key):
            admin_cred = self.__admin_creds.get(key)
            if admin_cred is None or admin_cred.has_expired(1):
                admin_cred = await self.generate_cloud_credentials(request, admin_role, sub, duration=lifespan)
                self.__admin_creds[key] = admin_cred
                admin_cred.expiration = now() + timedelta(seconds=lifespan)
            return deepcopy(admin_cred)

    def get_default_permission_context(self, request: web.Request) -> S3ObjectPermissionContext:
        return S3ObjectPermissionContext(request)


    @staticmethod
    async def _get_basic_account_info(sts_client: STSClient) -> AWSAccount:
        """
        Gets basic account info from AWS. Assigns an owner but not any invites nor shares.

        :param sts_client: the STS client to use.
        :return: the AWS account.
        :raises ClientError: if there was an error getting the account info.
        """
        loop = asyncio.get_running_loop()
        identity = await loop.run_in_executor(None, sts_client.get_caller_identity)
        logger = logging.getLogger(__name__)
        logger.debug('Caller identity: %s', identity)
        # user_future = loop.run_in_executor(None, iam_client.get_user)
        # await asyncio.wait([identity_future])  # , user_future])
        aid = identity['Account']
        # aws_object_dict['alias'] = next(iam_client.list_account_aliases()['AccountAliases'], None)  # Only exists for IAM accounts.
        # user = user_future.result()['User']
        # aws_object_dict['account_name'] = user.get('UserName')  # Only exists for IAM accounts.
        account: AWSAccount = AWSAccount()
        account.id = aid
        account.name = aid
        account.display_name = f'AWS Account {aid}'
        account.owner = AWS_USER
        account.source = AWS_SOURCE
        account.source_detail = AWS_SOURCE
        account.type_display_name
        account.file_system_type = AWSFileSystem.get_type_name()
        account.credential_type_name = AWSCredentials.get_type_name()
        return account

    async def __get_resource_or_client(self, request: Request, service_name: ServiceName,
                                       credentials: AWSCredentials | None) -> S3Client | IAMClient | STSClient | AccountClient | OrganizationsClient | SQSClient:
        """
        Gets an S3 resource or client.

        :param request: the HTTP request (required). The request must have a valid OIDC_CLAIM_sub header, and for
        temporary credentials it must also have a valid Authorization header unless the OIDC_CLAIM_sub is the
        system|credentialsmanager user.
        :param service_name: the name of the S3 service (required).
        :param creator: the function for creating the resource or client (create_resource or create_client).
        :param credentials: the AWSCredentials object, or None to let boto3 find the credentials.

        :raises ValueError: if updating temporary credentials failed.
        """
        logger = logging.getLogger(__name__)
        logger.debug("credentials retrieved from database checking if expired: %r", credentials)
        loop = asyncio.get_running_loop()
        if not credentials:  # delegate to boto3 to find the credentials
            return await loop.run_in_executor(None, partial(boto3.client, service_name, config=_boto3_client_config))
        elif credentials.temporary:
            return await self.__get_temporary_credentials(request=request,
                                                            credentials=credentials,
                                                            service_name=service_name)
        else:  # for permanent credentials
            return await loop.run_in_executor(None, partial(boto3.client, service_name,
                                                            region_name=credentials.where,
                                                            aws_access_key_id=credentials.account,
                                                            aws_secret_access_key=credentials.password,
                                                            config=_boto3_client_config))

    @overload
    async def __get_temporary_credentials(self, request: web.Request, credentials: AWSCredentials,
                                          service_name: Literal['organizations']) -> OrganizationsClient:
        pass

    @overload
    async def __get_temporary_credentials(self, request: web.Request, credentials: AWSCredentials,
                                          service_name: Literal['account']) -> AccountClient:
        pass

    @overload
    async def __get_temporary_credentials(self, request: web.Request, credentials: AWSCredentials,
                                          service_name: Literal['sts']) -> STSClient:
        pass

    @overload
    async def __get_temporary_credentials(self, request: web.Request, credentials: AWSCredentials,
                                          service_name: Literal['iam']) -> IAMClient:
        pass

    @overload
    async def __get_temporary_credentials(self, request: web.Request, credentials: AWSCredentials,
                                          service_name: Literal['s3']) -> S3Client:
        pass

    @overload
    async def __get_temporary_credentials(self, request: web.Request, credentials: AWSCredentials,
                                          service_name: Literal['sqs']) -> SQSClient:
        pass

    async def __get_temporary_credentials(self, request: web.Request, credentials: AWSCredentials,
                                          service_name: ServiceName) -> S3Client | IAMClient | STSClient | AccountClient | OrganizationsClient | SQSClient:
        """
        Assumes the provided temporary credentials' role and returns an AWS client. If the temporary credentials have
        expired, it updates them. If the temporary credentials were previously persisted, it persists the updates.

        If the user who made the request is system|credentialsmanager, which can only happen in internal calls between
        microservices where the only available Authorization header would be from the logged-in user, a token is
        requested from the people service to use for assuming an AWS role. Otherwise, the Bearer token passed in the
        request in the Authorization header or the access_token query parameter is used to assume the role.

        :param request: the HTTP request (required). The request must have a valid OIDC_CLAIM_sub header, and it must
        also have a valid Authorization header unless the OIDC_CLAIM_sub is the system|credentialsmanager user.
        :param credentials: the aws credentials.
        :param creator: a callable that invokes either the boto3.get_client or boto3.get_resource functions and returns
        the client.
        :param service_name: The type of client to return
        :return: the boto3 client provided with credentials
        :raise ValueError if no previously saved credentials it raises ValueError
        """
        logger = logging.getLogger(__name__)
        assert credentials.role is not None, 'credentials must have a non-None role attribute'
        loop = asyncio.get_running_loop()
        sub = request.headers.get(SUB, NONE_USER)

        async with self.__temp_cred_locks.lock(credentials.id):
            logger.debug("checking if AWS credentials for service %s %r for user %s need to be refreshed, right before", service_name, credentials, sub)
            if credentials.has_expired(1):
                logger.debug("AWS credentials for service %s %r need to be refreshed", service_name, credentials)
                cloud_creds = await self.generate_cloud_credentials(request, credentials.role, sub)
                logger.debug("AWS Credentials for service %s successfully obtained from cloud: %r", service_name, cloud_creds)
                credentials.account = cloud_creds.account
                credentials.password = cloud_creds.password
                credentials.session_token = cloud_creds.session_token
                credentials.expiration = cloud_creds.expiration
                if credentials.id is not None:
                    update_task: asyncio.Task[None] | None = asyncio.create_task(self.update_credentials(request=request, credentials=credentials))
                else:
                    update_task = None
                logger.debug("AWS Credentials %r updated in the database", credentials)
            else:
                update_task = None
            assert credentials.account is not None, 'credentials.account is None unexpectedly'
            if (session := self.__temp_cred_session_cache.get(credentials.account)) is None:
                session = boto3.session.Session(region_name=credentials.where, aws_access_key_id=credentials.account,
                                                aws_secret_access_key=credentials.password,
                                                aws_session_token=credentials.session_token)
                self.__temp_cred_session_cache[credentials.account] = session
            client_ = await loop.run_in_executor(None, partial(session.client, service_name, config=_boto3_client_config))
            if update_task is not None:
                await update_task
            return client_

    async def __get_admin_aws_role_arn(self, request: web.Request, arn: str) -> str:
        """
        Generates an admin role ARN from the current user's role ARN, replacing the role part of the ARN with the value of
        the AWS_ADMIN_ROLE property in the heaserver-registry service.

        :param request: the HTTP request.
        :param arn: the current user's role ARN.
        :return: an admin role ARN for that account.
        :raises ValueError: if no AWS_ADMIN_ROLE property was found.
        :raises IndexError: if the input arn is malformed.
        """
        admin_role_prop: Optional[Property] = await self.get_property(app=request.app, name="AWS_ADMIN_ROLE")
        if not admin_role_prop or not admin_role_prop.value:
            raise ValueError("Admin role property not found")
        admin_role_name = admin_role_prop.value
        r_index = arn.rindex('/') + 1
        arn_prefix = arn[:r_index]

        return f"{arn_prefix}{admin_role_name}"

    async def __get_sts_client(self, loop: asyncio.AbstractEventLoop | None = None):
        logger = logging.getLogger(__name__)
        logger.debug('Getting sts client')
        async with self.__sts_client_asyncio_lock:
            logger.debug('Passed asyncio lock')
            try:
                if self.__sts_client is None:
                    logger.debug('Attempting to get sts client')
                    loop_ = asyncio.get_running_loop() if loop is None else loop
                    def get_client():
                        with _boto3_client_lock:
                            return boto3.client('sts', config=_boto3_client_config)
                    self.__sts_client = await loop_.run_in_executor(None, get_client)
                logger.debug('Returning sts client')
                return self.__sts_client
            except ClientError as e:
                self.__sts_client = None
                raise e
            except:
                logger.exception('Got exception attempting to create sts client')
                raise


class S3WithMongo(S3, Mongo):
    def __init__(self, config: Optional[Configuration], **kwargs):
        super().__init__(config, **kwargs)


class S3Manager(MicroserviceDatabaseManager):
    """
    Database manager for mock Amazon Web Services S3 buckets. It will not make any calls to actual S3 buckets. This
    class is not designed to be subclassed.
    """

    def get_database(self) -> S3:
        return S3(self.config, managed=True)

    @classmethod
    def database_types(self) -> list[str]:
        return ['system|awss3']


class S3WithMongoManager(S3Manager):

    def get_database(self) -> S3:
        return S3WithMongo(self.config, managed=True)


class S3ClientContext(DatabaseContextManager[S3Client, AWSCredentials]):  # Go into db package?
    """
    Provides an S3 client.
    """

    def __init__(self, request: web.Request, volume_id: str | None = None, credentials: AWSCredentials | None = None):
        """
        Creates an object for getting an S3 client. Either a volume_id or a credentials object must be provided. If a
        volume_id is provided but not a credentials object, the credentials object will be retrieved from the keychain
        microservice.

        :param request: the HTTP request (required).
        :param volume_id: a volume id. Either a volume id or a credentials object must be provided.
        :param credentials: an AWS credentials object. Either a volume_id or a credentials object must be provided.
        """
        super().__init__(request, volume_id, credentials)

    async def connection(self) -> S3Client:
        return await cast(S3, self.request.app[HEA_DB]).get_client(self.request, 's3', self.volume_id,
                                                                   self.credentials)


class IAMClientContext(DatabaseContextManager[IAMClient, AWSCredentials]):  # Go into db package?
    """
    Provides an IAM client.
    """

    def __init__(self, request: web.Request, volume_id: str | None = None, credentials: AWSCredentials | None = None):
        """
        Creates an object for getting an IAM client. Either a volume_id or a credentials object must be provided. If a
        volume_id is provided but not a credentials object, the credentials object will be retrieved from the keychain
        microservice.

        :param request: the HTTP request (required).
        :param volume_id: a volume id. Either a volume id or a credentials object must be provided.
        :param credentials: an AWS credentials object. Either a volume_id or a credentials object must be provided.
        """
        super().__init__(request, volume_id, credentials)

    async def connection(self) -> IAMClient:
        """
        Returns an IAM client.

        :return: an IAM client.
        """
        return await cast(S3, self.request.app[HEA_DB]).get_client(self.request, 'iam', self.volume_id,
                                                                   self.credentials)


class STSClientContext(DatabaseContextManager[STSClient, AWSCredentials]):  # Go into db package?
    """
    Provides an STS client.
    """

    def __init__(self, request: web.Request, volume_id: str | None = None, credentials: AWSCredentials | None = None):
        """
        Creates an object for getting an STS client. Either a volume_id or a credentials object must be provided. If a
        volume_id is provided but not a credentials object, the credentials object will be retrieved from the keychain
        microservice.

        :param request: the HTTP request (required).
        :param volume_id: a volume id. Either a volume id or a credentials object must be provided.
        :param credentials: an AWS credentials object. Either a volume_id or a credentials object must be provided.
        """
        super().__init__(request, volume_id, credentials)

    async def connection(self) -> STSClient:
        """
        Returns an STS client.

        :return: an STS client.
        """
        return await cast(S3, self.request.app[HEA_DB]).get_client(self.request, 'sts', self.volume_id,
                                                                   self.credentials)


class AccountClientContext(DatabaseContextManager[AccountClient, AWSCredentials]):
    """
    Provides an Account client.
    """

    def __init__(self, request: web.Request, volume_id: str | None = None, credentials: AWSCredentials | None = None):
        """
        Creates an object for getting an Account client. Either a volume_id or a credentials object must be provided.
        If a volume_id is provided but not a credentials object, the credentials object will be retrieved from the
        keychain microservice.

        :param request: the HTTP request (required).
        :param volume_id: a volume id. Either a volume id or a credentials object must be provided.
        :param credentials: an AWS credentials object. Either a volume_id or a credentials object must be provided.
        """
        super().__init__(request, volume_id, credentials)

    async def connection(self) -> AccountClient:
        """
        Returns an Account client.

        :return: an Account client.
        """
        return await cast(S3, self.request.app[HEA_DB]).get_client(self.request, 'account', self.volume_id,
                                                                   self.credentials)


class OrganizationsClientContext(DatabaseContextManager[OrganizationsClient, AWSCredentials]):
    """
    Provides an Organizations client.
    """

    def __init__(self, request: web.Request, volume_id: str | None = None, credentials: AWSCredentials | None = None):
        """
        Creates an object for getting an Organization client. Either a volume_id or a credentials object must be
        provided. If a volume_id is provided but not a credentials object, the credentials object will be retrieved
        from the keychain microservice.

        :param request: the HTTP request (required).
        :param volume_id: a volume id. Either a volume id or a credentials object must be provided.
        :param credentials: an AWS credentials object. Either a volume_id or a credentials object must be provided.
        """
        super().__init__(request, volume_id, credentials)

    async def connection(self) -> OrganizationsClient:
        """
        Returns an Organization client.

        :return: an Organization client.
        """
        return await cast(S3, self.request.app[HEA_DB]).get_client(self.request, 'organizations', self.volume_id,
                                                                   self.credentials)


class SQSClientContext(DatabaseContextManager[SQSClient, AWSCredentials]):  # Go into db package?
    """
    Provides an SQS client.
    """

    def __init__(self, request: web.Request, volume_id: str | None = None, credentials: AWSCredentials | None = None):
        """
        Creates an object for getting an SQS client. Either a volume_id or a credentials object must be provided. If a
        volume_id is provided but not a credentials object, the credentials object will be retrieved from the keychain
        microservice.

        :param request: the HTTP request (required).
        :param volume_id: a volume id. Either a volume id or a credentials object must be provided.
        :param credentials: an AWS credentials object. Either a volume_id or a credentials object must be provided.
        """
        super().__init__(request, volume_id, credentials)

    async def connection(self) -> SQSClient:
        """
        Returns an SQS client.

        :return: an SQS client.
        """
        return await cast(S3, self.request.app[HEA_DB]).get_client(self.request, 'sqs', self.volume_id,
                                                                   self.credentials)


@overload
def create_client(service_name: Literal['s3'],
                  **kwargs: Unpack[CreatorKwargs]) -> S3Client:
    ...

@overload
def create_client(service_name: Literal['iam'],
                  **kwargs: Unpack[CreatorKwargs]) -> IAMClient:
    ...

@overload
def create_client(service_name: Literal['sts'],
                  **kwargs: Unpack[CreatorKwargs]) -> STSClient:
    ...


@overload
def create_client(service_name: Literal['account'],
                  **kwargs: Unpack[CreatorKwargs]) -> AccountClient:
    ...


@overload
def create_client(service_name: Literal['organizations'],
                  **kwargs: Unpack[CreatorKwargs]) -> OrganizationsClient:
    ...


@overload
def create_client(service_name: Literal['sqs'],
                  **kwargs: Unpack[CreatorKwargs]) -> SQSClient:
    ...


def create_client(service_name: ServiceName,
                  **kwargs: Unpack[CreatorKwargs]) -> S3Client | IAMClient | STSClient | AccountClient | OrganizationsClient | SQSClient:
    """
    Thread-safe boto client creation. Once created, clients are generally thread-safe.

    :raises ValueError: if an error occurred getting the S3 client.
    """
    with _boto3_client_lock:
        return boto3.client(service_name,
                            region_name=kwargs.get('region_name'),
                            aws_access_key_id=kwargs.get('aws_access_key_id'),
                            aws_secret_access_key=kwargs.get('aws_secret_access_key'),
                            aws_session_token=kwargs.get('aws_session_token'),
                            config=_boto3_client_config)


async def is_account_owner(request: Request, volume_id: str | None = None, credentials: AWSCredentials | None = None) -> bool:
    """
    Convenience function for checking if the user who made the request is the owner of the AWS account associated with
    the given credentials or volume. Either a volume_id or a credentials object must be provided. If credentials are
    provided, the account associated with the credentials will be checked, otherwise the account associated with the
    volume_id will be checked.

    :param request: the HTTP request (required). It is expected to have the OIDC_claim_sub header, or system|none is
    assumed.
    :param volume_id: the volume id. Either a volume_id or credentials object must be provided.
    :param credentials: the AWS credentials. Either a volume_id or credentials object must be provided.
    :return: True if the user is the account owner, otherwise False.
    """
    logger = logging.getLogger(__name__)
    async with STSClientContext(request=request, volume_id=volume_id, credentials=credentials) as sts_client:
        caller_identity_resp = sts_client.get_caller_identity()
        logger.debug('caller identity: %s', caller_identity_resp)
        arn = AmazonResourceName.from_arn_str(caller_identity_resp['Arn'])
        return not arn.resource_type_and_id.startswith('assumed-role')


def client_error_status(e: ClientError) -> tuple[int, str]:
    """
    Translates a boto3 client error into an appropriate HTTP response status code.

    :param e: a boto3 client error (required).
    :return: a HTTP status code and a message.
    """
    logger = logging.getLogger(__name__)
    error_code = client_error_code(e)
    if error_code in (CLIENT_ERROR_404, CLIENT_ERROR_NO_SUCH_BUCKET, CLIENT_ERROR_NO_SUCH_KEY):  # folder doesn't exist
        return 404, ''
    elif error_code in (CLIENT_ERROR_ACCESS_DENIED, CLIENT_ERROR_ACCESS_DENIED2, CLIENT_ERROR_FORBIDDEN, CLIENT_ERROR_ALL_ACCESS_DISABLED):
        return 403, 'Access denied'
    elif error_code in (CLIENT_ERROR_INVALID_OBJECT_STATE, CLIENT_ERROR_BUCKET_NOT_EMPTY):
        return 400, str(e)
    else:
        logger.exception('Unexpected boto3 client error %s', error_code)
        return 500, str(e)


def client_error_code(e: ClientError) -> str:
    """
    Extracts and returns the error code from a boto3 client error. A subset of these codes are represented by the
    CLIENT_ERROR_* constants in this module.

    :param e: the boto3 client error (required).
    :return: the error code.
    """
    return e.response['Error']['Code']


def get_default_share(sub: str) -> Share:
    """
    Returns a default share for the given user, assuming access level to the AWS desktop object is unknown. The share
    includes all permissions.

    :param sub: the user requesting the desktop object.
    :return: the share.
    """
    share = ShareImpl()
    share.permissions = list(Permission)
    share.user = sub
    return share


def add_default_share_to_desktop_object(sub: str, obj: AWSDesktopObject):
    """
    Adds a default share to the desktop object, if the user is not system|none.

    :param sub: the user requesting the desktop object.
    :param obj: the desktop object.
    """
    if sub != NONE_USER:
        obj.add_share(get_default_share(sub))


@dataclass
class _GetCollaboratorRetval:
    bucket_name: str
    collaborator_id: str
    other_bucket_names: list[str]


async def _get_collaborators(iam_client: IAMClient, buckets: Iterable[str]) -> AsyncGenerator[tuple[str, _GetCollaboratorRetval], None]:
    logger = logging.getLogger(__name__)
    logger.debug('Getting collaborators')
    bucket_set = set(buckets)
    try:
        async for policy_info in _all_collaborator_policies_gen(iam_client):
            for bucket_name in policy_info.bucket_names:
                if bucket_name in bucket_set:
                    yield bucket_name, _GetCollaboratorRetval(bucket_name=bucket_name,
                                                            collaborator_id=policy_info.user_id,
                                                            other_bucket_names=list(policy_info.bucket_names - set([bucket_name])))
    except ClientError as e:
        if e.response['Error']['Code'] != 'NoSuchBucketPolicy':
            logging.exception('Error getting collaborators')
            raise e


async def _get_bucket_collaborators(iam_client: IAMClient, buckets: Iterable[str]) -> AsyncGenerator[tuple[str, list[str]], None]:
    bucket_to_collab = defaultdict[str, list[str]](list)
    async for _, collab_info in _get_collaborators(iam_client, buckets):
        bucket_to_collab[collab_info.bucket_name].append(collab_info.collaborator_id)
    for bucket_name, collab_ids in bucket_to_collab.items():
        yield bucket_name, collab_ids

import re
_collaborator_policy_name_prefix = 'aws-Collaborator.Policy_'
_arn_pattern = re.compile("[:/]")

@dataclass
class _PolicyInfo:
    user_id: str
    policy_arn: str
    bucket_names: set[str]
    policy_doc: PolicyDocumentDictTypeDef


async def _all_collaborator_policies_gen(iam_client: IAMClient) -> AsyncGenerator[_PolicyInfo, None]:
    logger = logging.getLogger(__name__)
    logger.debug('Getting collaborator policy')
    loop = asyncio.get_running_loop()
    response_ = (await loop.run_in_executor(None, partial(iam_client.get_account_authorization_details,
                                                                     Filter=['LocalManagedPolicy'])))
    logger.debug('Account authorization details: %s', response_)
    for policy in response_['Policies']:
        logger.debug('Policy detail: %s', policy)
        if policy['PolicyName'].startswith(_collaborator_policy_name_prefix):
            user_id = policy['PolicyName'].removeprefix(_collaborator_policy_name_prefix)
            logger.debug('User id %s', user_id)
            for version in policy['PolicyVersionList']:
                if version['IsDefaultVersion']:
                    pol_doc = version['Document']
                    assert not isinstance(pol_doc, str), 'Unexpected policy document type'
                    pol_doc_stmt = pol_doc['Statement']
                    assert not isinstance(pol_doc_stmt, str), 'Unexpected policy document statement type'
                    assert len(pol_doc_stmt) == 2, 'Unexpected number of policy statements'
                    bucket_names: set[str] = set()
                    for resource in pol_doc_stmt[0]['Resource']:
                        bucket_names.add(_arn_pattern.split(resource)[5])
                    logger.debug('Returning policy doc from policy %s for user %s with buckets %s', policy, pol_doc, bucket_names)
                    assert not isinstance(pol_doc, str), 'pol_doc unexpected type'
                    yield _PolicyInfo(user_id=user_id, policy_arn=policy['Arn'], bucket_names=bucket_names, policy_doc=pol_doc)
