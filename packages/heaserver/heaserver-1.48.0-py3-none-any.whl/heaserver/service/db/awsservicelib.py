"""
Functions for interacting with Amazon Web Services.

This module supports management of AWS accounts, S3 buckets, and objects in S3 buckets. It uses Amazon's boto3 library
behind the scenes.

In order for HEA to access AWS accounts, buckets, and objects, there must be a volume accessible to the user through
the volumes microservice with an AWSFileSystem for its file system. Additionally, credentials must either be stored
in the keychain microservice and associated with the volume through the volume's credential_id attribute,
or stored on the server's file system in a location searched by the AWS boto3 library. Users can only see the
accounts, buckets, and objects to which the provided AWS credentials allow access, and HEA may additionally restrict
the returned objects as documented in the functions below. The purpose of volumes in this case is to supply credentials
to AWS service calls. Support for boto3's built-in file system search for credentials is only provided for testing and
should not be used in a production setting. This module is designed to pass the current user's credentials to AWS3, not
to have application-wide credentials that everyone uses.

The request argument to these functions is expected to have a OIDC_CLAIM_sub header containing the user id for
permissions checking. No results will be returned if this header is not provided or is empty.

In general, there are two flavors of functions for getting accounts, buckets, and objects. The first expects the id
of a volume as described above. The second expects the id of an account, bucket, or bucket and object. The latter
attempts to match the request up to any volumes with an AWSFileSystem that the user has access to for the purpose of
determine what AWS credentials to use. They perform the
same except when the user has access to multiple such volumes, in which case supplying the volume id avoids a search
through the user's volumes.
"""
import logging
from aiohttp import web
from heaobject.awss3key import display_name
from .. import response
from ..appproperty import HEA_DB
from aiohttp.web import HTTPError
from heaobject.volume import AWSFileSystem
from heaserver.service import aiohttp
from asyncio import gather
from botocore.exceptions import ClientError as BotoClientError
from .aws import client_error_status


async def get_volume_id_for_account_id(request: web.Request) -> str | None:
    """
    Gets the id of the volume associated with an AWS account. The account id is expected to be in the request object's
    match_info mapping, with key 'id'. The account is fetched from AWS during this operation.

    :param request: an aiohttp Request object (required).
    :return: a volume id string, or None if no volume was found associated with the AWS account or the account does not
    exist.
    """
    async def get_one(request, volume_id):
        return volume_id, await request.app[HEA_DB].get_account(request, volume_id)
    return next((volume_id for (volume_id, a) in await gather(
        *[get_one(request, v.id) async for v in request.app[HEA_DB].get_volumes(request, AWSFileSystem)])
                 if
                 a.id == request.match_info['id']), None)


def handle_client_error(e: BotoClientError) -> HTTPError:
    """
    Translates a boto3 client error into an appropriate HTTP response.

    :param e: a boto3 client error (required).
    :return: an HTTP response with status code >=400 that can be raised as an exception.
    """
    status, msg = client_error_status(e)
    logger = logging.getLogger(__name__)
    logger.debug('Boto3 client error: %s, %s', status, msg, exc_info=e)
    return response.status_generic_error(status=status, body=msg)


def s3_object_message_display_name(bucket_name: str, key: str | None) -> str:
    """
    Function for use with heaserver.service.aiohttp.http_error_message() to generate names of S3 buckets and objects
    for use in info, warning, error, and other messages.

    :param bucket_name: the name of an S3 bucket (required).
    :param key: an optional key for objects in a bucket.
    """
    return f'{display_name(key) or ""} in bucket {bucket_name}' if key is not None else bucket_name


def http_error_message(http_error: web.HTTPError, bucket_name: str, key: str | None) -> web.HTTPError:
    """
    If the HTTPError object has an empty body, it will try filling in the body with a message appropriate for the given
    status code for operations on desktop objects from AWS. Uses s3_object_display_name() to generate the message.

    :param http_error: the HTTPError (required).
    :param bucket_name: the bucket name (required).
    :param key: the key.
    :return: the updated HTTPError.
    """
    return aiohttp.http_error_message(http_error, s3_object_message_display_name, bucket_name, key)


def _activity_object_display_name(bucket_name: str, key: str | None) -> str:
    return s3_object_message_display_name(bucket_name, key)
activity_object_display_name = _activity_object_display_name

