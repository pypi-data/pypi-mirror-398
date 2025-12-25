"""
The HEA Server AWS Accounts Microservice provides ...
"""
import json
import logging
import time
from asyncio import Queue
from datetime import date, datetime
from functools import partial
from urllib.parse import unquote_plus

import orjson
from aiohttp.hdrs import AUTHORIZATION
from heaobject import awss3key
from heaobject.awss3key import decode_key, encode_key
from heaobject.data import AWSS3FileObject
from heaobject.folder import AWSS3Item, AWSS3ItemInFolder, AWSS3SearchItemInFolder, AWSS3BucketItem, AWSS3Folder
from heaobject.project import AWSS3Project
from heaserver.service.db.opensearchlib import search_dict, search

from heaserver.service.heaobjectsupport import type_to_resource_url
from heaserver.service.oidcclaimhdrs import SUB
from heaserver.service.runner import init_cmd_line, routes, start, web, scheduled_cleanup_ctx, wait_on_coro_cleanup_ctx
from heaserver.service.db import aws, awsservicelib, opensearch, opensearchlib
from heaserver.service.wstl import builder_factory, action
from heaserver.service import response, client, appproperty
from heaserver.service.appproperty import HEA_DB, HEA_CACHE
from heaserver.service.heaobjectsupport import new_heaobject_from_type
from heaserver.service.wstl import add_run_time_action
from heaserver.service.config import Configuration
from heaobject.account import AWSAccount, AccountView
from heaobject.keychain import AWSCredentials
from heaobject.bucket import AWSBucket
from heaobject.storage import AWSS3Storage
from heaobject.root import Permission, DesktopObjectDict, ViewerPermissionContext, ViewerPermissionContext, Share, \
    DesktopObject, json_loads, DesktopObjectTypeVar, to_dict
from heaobject.volume import AWSFileSystem, Volume
from heaobject.user import NONE_USER, AWS_USER, CREDENTIALS_MANAGER_USER
from heaobject.util import parse_bool, now
from heaobject.aws import AWSDesktopObject
from heaserver.service.sources import AWS as AWS_SOURCE
from mypy_boto3_sqs.type_defs import DeleteMessageBatchRequestEntryTypeDef
from opensearchpy import NotFoundError
from yarl import URL
from aiohttp.web import Request, Response
from botocore.exceptions import ClientError as BotoClientError
from aiohttp.client_exceptions import ClientError, ClientResponseError
from heaserver.service.activity import DesktopObjectActionLifecycle, Status
from heaserver.service.messagebroker import publish_desktop_object, publisher_cleanup_context_factory
from collections.abc import Sequence
from heaserver.service.db.aws import AWSPermissionContext, SQSClientContext
from .context import AWSAccountPermissionContext
from mypy_boto3_organizations.literals import IAMUserAccessToBillingType
from typing import get_args, TypeGuard, cast, Any
import asyncio


@routes.get('/ping')
async def ping(request: web.Request) -> web.Response:
    """
    For testing whether the service is up.

    :param request: the HTTP request.
    :return: Always returns status code 200.
    """
    return response.status_ok(None)

@routes.get('/accounts/{id}')
@action(name='heaserver-accounts-account-get-actual', rel='hea-actual hea-actual-container', path='{+actual_object_uri}')
async def get_account_id(request: web.Request) -> web.Response:
    """
    Gets an AccountView with the given id.

    :param request: the HTTP request. The Authorization header must be present unless the OIDC_CLAIM_sub is the
    system|credentialsmanager user.
    :return: a Response object with the requested AWS account or Not Found.
    ---
    summary: The user's account.
    tags:
        - heaserver-accounts-account
    parameters:
        - $ref: '#/components/parameters/id'
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
        - $ref: '#/components/parameters/Authorization'
    responses:
      '200':
        $ref: '#/components/responses/200'
      '404':
        $ref: '#/components/responses/404'
    """
    id_ = request.match_info['id']
    async with DesktopObjectActionLifecycle(request=request,
                                            code='hea-get',
                                            description=f'Getting account {id_}',
                                            activity_cb=publish_desktop_object) as activity:
        sub = request.headers.get(SUB, NONE_USER)
        cache_key = (sub, f'accountid^{id_}')
        if (cached_value:=request.app[HEA_CACHE].get(cache_key)) is not None:
            av_dict, permissions, attribute_permissions = cached_value
        else:
            try:
                aws_account, volume_id = await _get_awsaccount_by_aws_account_id(request, id_.split('^')[1])
            except IndexError:
                raise response.status_bad_request(f'Invalid account id {id_}')
            if aws_account is None:
                raise response.status_not_found()
            else:
                context = ViewerPermissionContext(sub)
                av: AccountView = AccountView()
                av.actual_object_id = aws_account.id
                av.actual_object_type_name = aws_account.type
                av.actual_object_uri = f'awsaccounts/{aws_account.id}'
                av.display_name = aws_account.display_name
                av.owner = aws_account.owner
                av.created = aws_account.created
                av.modified = aws_account.modified
                av.name = aws_account.name
                av.type_display_name = aws_account.type_display_name
                av.file_system_type = aws_account.file_system_type
                av.file_system_name = aws_account.file_system_name
                share = await av.get_permissions_as_share(context)
                permissions = share.permissions
                av.add_user_share(share)
                av_dict = av.to_dict()
                attribute_permissions = await av.get_all_attribute_permissions(context)
                activity.new_object_type_name = AccountView.get_type_name()
                activity.new_object_id = id_
                activity.new_object_uri = f'accounts/{id_}'
                activity.new_volume_id = volume_id
                request.app[HEA_CACHE][cache_key] = (av_dict, permissions, attribute_permissions)
        return await response.get(request, av_dict, permissions=permissions,
                                    attribute_permissions=attribute_permissions)

@routes.get('/accounts')
@routes.get('/accounts/')
@action(name='heaserver-accounts-account-get-actual', rel='hea-actual hea-actual-container', path='{+actual_object_uri}')
async def get_accounts(request: web.Request) -> web.Response:
    """
    Gets all accounts accessible to the user as AccountView objects.

    :param request: the HTTP request. The Authorization header must be present unless the OIDC_CLAIM_sub is the
    system|credentialsmanager user.
    :return: a Response object with the requested accounts.
    ---
    summary: The user's accounts.
    tags:
        - heaserver-accounts-account
    parameters:
        - $ref: '#/components/parameters/id'
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
        - $ref: '#/components/parameters/Authorization'
    responses:
      '200':
        $ref: '#/components/responses/200'
    """
    async with DesktopObjectActionLifecycle(request=request,
                                                code='hea-get',
                                                description=f'Getting all accounts',
                                                activity_cb=publish_desktop_object) as activity:
        logger = logging.getLogger(__name__)
        sub = request.headers.get(SUB, NONE_USER)
        account_ids = request.query.getall('account_id', [])
        cache_key = (sub, 'allaccountids')
        if not account_ids and (cached_value:=request.app[HEA_CACHE].get(cache_key)) is not None:
            account_view_dicts: list[DesktopObjectDict] = cached_value[0]
            volume_ids: list[str] = cached_value[1]
            permissions: list[list[Permission]] = cached_value[2]
            attribute_permissions: list[dict[str, list[Permission]]] = cached_value[3]
        else:
            volume_url = await type_to_resource_url(request, Volume)
            volumes = await client.get_all_list(request.app, volume_url, Volume, headers={SUB: sub})
            activity.new_object_type_name = AccountView.get_type_name()
            activity.new_object_uri = 'accounts/'
            account_views: list[AccountView] = []
            context = ViewerPermissionContext(sub)
            permissions = []
            attribute_permissions = []
            volume_ids = []
            for volume in volumes:
                account_id = volume.account_id
                if account_id is None or (account_ids and account_id not in account_ids):
                    continue
                av: AccountView = AccountView()
                assert volume.id is not None, 'volume.id cannot be None'
                volume_ids.append(volume.id)
                av.id = account_id
                type_, id_ = account_id.split('^')
                av.actual_object_id = id_
                av.actual_object_type_name = type_
                if type_ == AWSAccount.get_type_name():
                    av.display_name = f'AWS Account {id_}'
                    av.actual_object_uri = f'awsaccounts/{id_}'
                    av.type_display_name = 'AWS Account'
                av.owner = AWS_USER
                av.name = volume.name
                av.file_system_type = volume.file_system_type
                av.file_system_name = volume.file_system_name
                av.source = AWS_SOURCE
                av.source_detail = AWS_SOURCE
                share, attr_perms = await asyncio.gather(av.get_permissions_as_share(context),
                                                         av.get_all_attribute_permissions(context))
                av.add_user_share(share)
                permissions.append(share.permissions)
                attribute_permissions.append(attr_perms)
                account_views.append(av)
            account_view_dicts = [to_dict(a) for a in account_views]
            if not account_ids:
                request.app[HEA_CACHE][cache_key] = (account_view_dicts, volume_ids, permissions, attribute_permissions)
            for account_view_dict, perms, attr_perms in zip(account_view_dicts, permissions, attribute_permissions):
                request.app[HEA_CACHE][(sub, f'accountid^{account_view_dict["id"]}')] = (account_view_dict, perms, attr_perms)
        return await response.get_all(request, account_view_dicts,
                                    permissions=permissions,
                                    attribute_permissions=attribute_permissions)

@routes.options('/awsaccounts/{id}')
async def get_awsaccount_options(request: web.Request) -> web.Response:
    """
    ---
    summary: Allowed HTTP methods.
    tags:
        - heaserver-accounts-awsaccount
    parameters:
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
    return await response.get_options(request, ['GET', 'HEAD', 'OPTIONS', 'PUT', 'DELETE'])


@routes.get('/awsaccounts/{id}')
@action('heaserver-accounts-awsaccount-get-open-choices', rel='hea-opener-choices hea-context-menu', path='awsaccounts/{id}/opener')
@action('heaserver-accounts-awsaccount-get-properties', rel='hea-properties hea-context-menu')
@action('heaserver-accounts-awsaccount-get-create-choices', rel='hea-creator-choices hea-context-menu', path='awsaccounts/{id}/creator')
@action('heaserver-accounts-awsaccount-get-trash', rel='hea-trash hea-context-menu', path='volumes/{volume_id}/awss3trash')
@action('heaserver-accounts-awsaccount-get-searchitem', rel='hea-search', path='awsaccounts/{id}/search')
@action('heaserver-accounts-awsaccount-get-self', rel='self hea-account hea-self-container', path='awsaccounts/{id}')
@action(name='heaserver-accounts-awsaccount-get-volume', rel='hea-volume', path='volumes/{volume_id}')
async def get_awsaccount(request: web.Request) -> web.Response:
    """
    Gets the AWS account with the given id. If no AWS credentials can be found, it uses any credentials found by the
    AWS boto3 library.

    :param request: the HTTP request. The Authorization header must be present unless the OIDC_CLAIM_sub is the
    system|credentialsmanager user.
    :return: a Response object with the requested AWS account or Not Found.
    ---
    summary: The user's AWS account.
    tags:
        - heaserver-accounts-awsaccount
    parameters:
        - $ref: '#/components/parameters/id'
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
        - $ref: '#/components/parameters/Authorization'
    responses:
      '200':
        $ref: '#/components/responses/200'
      '404':
        $ref: '#/components/responses/404'
    """
    logger = logging.getLogger(__name__)
    id_ = request.match_info['id']
    async with DesktopObjectActionLifecycle(request=request,
                                                code='hea-get',
                                                description=f'Getting AWS account {id_}',
                                                activity_cb=publish_desktop_object) as activity:
        sub = request.headers.get(SUB, NONE_USER)
        cache_key = (sub, f'id^{request.match_info["id"]}')
        cached_value = request.app[HEA_CACHE].get(cache_key)
        include_data = True
        if cached_value is not None:
            account_dict, volume_id, permissions, attribute_permissions = cached_value
        else:
            if include_data := parse_bool(request.query.get('data') or 'true'):
                account, volume_id = await _get_awsaccount_by_aws_account_id(request, id_)
                logger.debug('Got account %s and volume %s', account, volume_id)
                if account is None:
                    raise response.status_not_found()
                context = AWSAccountPermissionContext(request, volume_id)
                share = await account.get_permissions_as_share(context)
                permissions = share.permissions
                attribute_permissions = await account.get_all_attribute_permissions(context)
                account.add_user_share(share)
                account_dict = account.to_dict()
                request.app[HEA_CACHE][cache_key] = (account_dict, volume_id, permissions, attribute_permissions)
                request.app[HEA_CACHE][(sub, f'volume_id^{volume_id}')] = (account_dict, volume_id, permissions, attribute_permissions)
            else:
                volume_id = await _get_volume_id_by_aws_account_id(request, id_)
                account_dict = {'id': id_, 'type': AWSAccount.get_type_name()}
                permissions = None
                attribute_permissions = None
        request.match_info['volume_id'] = volume_id
        activity.new_object_type_name = AWSAccount.get_type_name()
        activity.new_object_id = id_
        activity.new_object_uri = f'awsaccounts/{id_}'
        activity.new_volume_id = volume_id
        return await response.get(request, account_dict,
                                  permissions=permissions,
                                  attribute_permissions=attribute_permissions,
                                  include_data=include_data)


@routes.get('/awsaccounts/byname/{name}')
@action('heaserver-accounts-awsaccount-get-self', rel='self hea-account hea-self-container', path='awsaccounts/{id}')
@action(name='heaserver-accounts-awsaccount-get-volume', rel='hea-volume', path='volumes/{volume_id}')
async def get_awsaccount_by_name(request: web.Request) -> web.Response:
    """
    Gets the AWS account with the given id. If no AWS credentials can be found, it uses any credentials found by the
    AWS boto3 library.

    :param request: the HTTP request. The Authorization header must be present unless the OIDC_CLAIM_sub is the
    system|credentialsmanager user.
    :return: a Response object with the requested AWS account or Not Found.
    ---
    summary: The user's AWS account.
    tags:
        - heaserver-accounts-awsaccount
    parameters:
        - $ref: '#/components/parameters/name'
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
        - $ref: '#/components/parameters/Authorization'
    responses:
      '200':
        $ref: '#/components/responses/200'
      '404':
        $ref: '#/components/responses/404'
    """
    name = request.match_info['name']
    sub = request.headers.get(SUB, NONE_USER)

    async with DesktopObjectActionLifecycle(request=request,
                                                    code='hea-get',
                                                    description=f'Getting AWS account {name}',
                                                    activity_cb=publish_desktop_object) as activity:
        cache_key = (sub, f'id^{name}')
        cached_value = request.app[HEA_CACHE].get(cache_key)
        if cached_value is not None:
            account, volume_id, permissions, attribute_permissions = cached_value
        else:
            account, volume_id = await _get_account_by_name(request)
            request.match_info['volume_id'] = volume_id
            if account is None:
                raise response.status_not_found()
            context = AWSAccountPermissionContext(request, volume_id)
            share = await account.get_permissions_as_share(context)
            permissions = share.permissions
            attribute_permissions = await account.get_all_attribute_permissions(context)
            account.add_user_share(share)
            request.app[HEA_CACHE][cache_key] = (account, volume_id, permissions, attribute_permissions)
            request.app[HEA_CACHE][(sub, f'volume_id^{volume_id}')] = (account, volume_id, permissions, attribute_permissions)
        activity.new_object_type_name = AWSAccount.get_type_name()
        activity.new_object_id = name
        activity.new_object_uri = f'awsaccounts/{name}'
        activity.new_volume_id = volume_id
    return await response.get(request, account.to_dict(), permissions=permissions, attribute_permissions=attribute_permissions)


@routes.get('/awsaccounts/{account_id}/search/{id}')
@action(name='heaserver-accounts-awsaccount-get-searchitem-self', rel='self hea-self-container', path='awsaccounts/{account_id}/search/{id}')
async def get_awsaccount_search_item(request: web.Request) -> web.Response:
    """
    Gets a single search item associated with an AWS account.

    :param request: the HTTP request.
    :return: a Response object with the requested AWS Search Item or Not Found.
    ---
    summary: Get a specific AWS search item.
    tags:
        - heaserver-accounts-awsaccount
    parameters:
        - $ref: '#/components/parameters/account_id'
        - $ref: '#/components/parameters/id'
    responses:
      '200':
        $ref: '#/components/responses/200'
      '404':
        $ref: '#/components/responses/404'
    """
    logger = logging.getLogger(__name__)
    account_id = request.match_info.get('account_id', '')
    item_id = request.match_info.get('id', '')
    if not account_id or not item_id:
        return response.status_bad_request("Required route params missing (account_id, item_id)")

    sub = request.headers.get(SUB, NONE_USER)
    context: ViewerPermissionContext = ViewerPermissionContext(sub)


    logger.debug(f"getting volume_id from account: {account_id}")
    volume_id = await _get_volume_id_by_aws_account_id(request, account_id)
    logger.debug(f"Got volume_id: {volume_id}")
    if volume_id is None:
        logger.debug(f'Volume not found for account {account_id}')
        return response.status_not_found()

    try:
        aws_folder_base = await type_to_resource_url(request, AWSS3Folder)
        search_item = await opensearchlib.get(request, item_id, search_item_type=AWSS3SearchItemInFolder)
        if search_item is None:
            logger.debug(f'Search item not found for id {item_id}')
            return response.status_not_found()
        if not search_item.bucket_id or not search_item.id or not search_item.path:
            logger.debug(f'Search item is missing required fields (bucket_id, id, path)')
            return response.status_bad_request(body="Search item found but is missing required fields (bucket_id, id, path")

        internal_url = URL(aws_folder_base) / volume_id / "buckets"/ search_item.bucket_id

        share, attr_perms = await asyncio.gather(
            search_item.get_permissions_as_share(context),
            search_item.get_all_attribute_permissions(context)
        )
        item_dict = to_dict(search_item)
        item_dict['shares'] = [to_dict(share)] # type: ignore
        item_dict['actual_object_id'] = item_id

        external_base = request.app[appproperty.HEA_COMPONENT]
        account_url = str(URL(external_base) / 'awsaccounts' / account_id)
        actual_object_bucket_uri = URL('volumes') / volume_id / 'buckets' / search_item.bucket_id
        external_base_url = f"{external_base}/{str(actual_object_bucket_uri)}"
        path = search_item.path[len(f"/{search_item.bucket_id}/"):] if search_item.bucket_id in search_item.path else None
        if not path:
            raise ValueError('Invalid path, malformed index data')

        urls = await _get_context_path(request, path, str(internal_url), external_base_url)
        ext_urls = []
        for i in range(len(urls)):
            external, internal_id, type_ = urls[i]
            if i == len(urls) - 1:
                item_dict['actual_object_uri'] = str(actual_object_bucket_uri / internal_id)
                item_dict['actual_object_type_name'] = type_
            ext_urls.append(external)

        cxt_paths = [account_url, external_base_url] + ext_urls
        item_dict['context_dependent_object_path'] = [encode_key(c) for c in cxt_paths]

        return await response.get(request=request, data=item_dict, permissions=share.permissions, attribute_permissions=attr_perms)

    except ClientResponseError as cre:
        logger.error(str(cre))
        return response.status_generic(status=cre.status, body=cre.message)
    except ClientError as ce:
        logger.error(str(ce))
        return response.status_generic(status=500, body=str(ce))
    except Exception as e:
        logger.error(str(e))
        return response.status_generic(status=500, body=str(e))


@routes.get('/awsaccounts/{id}/search')
@routes.get('/awsaccounts/{id}/search/')
@action(name='heaserver-accounts-awsaccount-get-searchitem-self', rel='self',path='awsaccounts/{account_id}/search/{id}')
async def search_awsaccounts(request: web.Request) -> web.Response:
    """
    Searches index with objects associated the given account id.

    :param request: the HTTP request.
    :return: a Response object with the requested AWS Search Item or Not Found.
    ---
    summary: The user's AWS account.
    tags:
        - heaserver-accounts-awsaccount
    parameters:
        - $ref: '#/components/parameters/id'
    responses:
      '200':
        $ref: '#/components/responses/200'
      '404':
        $ref: '#/components/responses/404'
    """
    logger = logging.getLogger(__name__)
    id_ = request.match_info['id']

    sub = request.headers.get(SUB, NONE_USER)
    auth = request.headers.get(AUTHORIZATION, '')
    headers = {SUB: sub, AUTHORIZATION: auth }
    context: ViewerPermissionContext = ViewerPermissionContext(sub)
    cache_key = (sub, f'id^{request.match_info["id"]}^search')
    cached_value = request.app[HEA_CACHE].get(cache_key)
    if cached_value is not None:
        volume_id = cached_value
    else:
        volume_id = await _get_volume_id_by_aws_account_id(request, id_)
        request.app[HEA_CACHE][cache_key] = (volume_id)
    if volume_id is None:
        logger.debug(f'Volume not found for account {id_}')
        return response.status_not_found()

    permissions: list[list[Permission]] = []
    attribute_permissions: list[dict[str, list[Permission]]] = []

    async with DesktopObjectActionLifecycle(request=request,
                                            code='hea-get',
                                            description=f'Getting AWS account\'s {id_} search items ',
                                            activity_cb=publish_desktop_object) as activity:
        try:
            bucket_base = await type_to_resource_url(request, AWSBucket)
            aws_folder_base = await type_to_resource_url(request, AWSS3Folder)
            bucket_names = [b_item.bucket_id for b_item in await client.get_all_list(request.app,
                                                                                     URL(bucket_base)/volume_id/'bucketitems',
                                                                    type_=AWSS3BucketItem,
                                                                    headers=headers) if b_item.bucket_id]
            external_base = request.app[appproperty.HEA_COMPONENT]
            search_items = await search_dict(request=request,search_item_type=AWSS3SearchItemInFolder, perm_context={'bucket_id.keyword': bucket_names })
            filtered_items = [sr_dict for sr_dict in search_items if not sr_dict['is_delete_marker']]


            async def process_search_item(sr_dict, external_base_, aws_folder_base_):
                sr = AWSS3SearchItemInFolder()
                share, attr_perms = await asyncio.gather(
                    sr.get_permissions_as_share(context),
                    sr.get_all_attribute_permissions(context)
                )
                sr_dict['shares'] = [share.to_dict()]
                permissions.append(share.permissions)
                attribute_permissions.append(attr_perms)

                if sr_dict.get('bucket_id') and sr_dict.get('id') and sr_dict.get('path'):
                    actual_object_bucket_uri = URL('volumes') / volume_id / 'buckets' / sr_dict['bucket_id']
                    internal_url = URL(aws_folder_base_) / volume_id / "buckets" / sr_dict['bucket_id']
                    path = sr_dict['path'][len(f"/{sr_dict['bucket_id']}/"):] if sr_dict['bucket_id'] in sr_dict['path'] else []

                    external_base_url = f"{external_base_}/{str(actual_object_bucket_uri)}"
                    external, internal_id, type_ = await _build_hierarchical_path(
                        request, path, internal_url, external_base_url, True
                    )
                    sr_dict['actual_object_uri'] = str(actual_object_bucket_uri / internal_id)
                    sr_dict['actual_object_type_name'] = type_
                else:
                    raise ValueError('Required bucket_id and search_item are not present')

            await asyncio.gather(*[process_search_item(sr_dict, external_base, aws_folder_base) for sr_dict in filtered_items],
                                 return_exceptions=False)
        except ClientResponseError as cre:
            logger.error(str(cre))
            activity.status = Status.FAILED
            return response.status_generic(status=cre.status, body=cre.message)
        except ClientError as ce:
            logger.error(str(ce))
            activity.status = Status.FAILED
            return response.status_generic(status=500, body=str(ce))
        except Exception as e:
            logger.error(str(e))
            activity.status = Status.FAILED
            return response.status_generic(status=500, body=str(e))

    return await response.get_all(request=request, data=filtered_items, permissions=permissions, attribute_permissions=attribute_permissions)

@routes.get('/awsaccounts')
@routes.get('/awsaccounts/')
@action('heaserver-accounts-awsaccount-get-open-choices', rel='hea-opener-choices hea-context-menu', path='awsaccounts/{id}/opener')
@action('heaserver-accounts-awsaccount-get-properties', rel='hea-properties hea-context-menu')
@action('heaserver-accounts-awsaccount-get-create-choices', rel='hea-creator-choices hea-context-menu', path='awsaccounts/{id}/creator')
@action('heaserver-accounts-awsaccount-get-searchitem', rel='hea-search', path='awsaccounts/{id}/search')
@action('heaserver-accounts-awsaccount-get-self', rel='self hea-account hea-self-container', path='awsaccounts/{id}')
async def get_awsaccounts(request: web.Request) -> web.Response:
    """
    Gets all AWS accounts. If no AWS credentials can be found, it uses any credentials found by the AWS boto3 library.

    :param request: the HTTP request. The Authorization header must be present unless the OIDC_CLAIM_sub is the
    system|credentialsmanager user.
    :return: a Response object with the requested AWS accounts or the empty list
    ---
    summary: The user's AWS accounts.
    tags:
        - heaserver-accounts-awsaccount
    parameters:
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
        - $ref: '#/components/parameters/Authorization'
    responses:
      '200':
        $ref: '#/components/responses/200'
    """
    async with DesktopObjectActionLifecycle(request=request,
                                                code='hea-get',
                                                description=f'Getting all AWS accounts',
                                                activity_cb=publish_desktop_object) as activity:
        account_ids: list[str] = request.query.getall('account_id', [])
        accounts, _, permissions, attribute_permissions = await _aws_account_ids_to_aws_accounts(request, account_ids)
        activity.new_object_type_name = AWSAccount.get_type_name()
        activity.new_object_uri = 'awsaccounts/'
        return await response.get_all(request, [to_dict(a) for a in accounts],
                                      permissions=permissions,
                                      attribute_permissions=attribute_permissions)


@routes.get('/volumes/{volume_id}/awsaccounts/me')
@action('heaserver-accounts-awsaccount-get-open-choices', rel='hea-opener-choices hea-context-menu',
        path='volumes/{volume_id}/awsaccounts/me/opener')
@action('heaserver-accounts-awsaccount-get-properties', rel='hea-properties hea-context-menu')
@action('heaserver-accounts-awsaccount-get-create-choices', rel='hea-creator-choices hea-context-menu', path='awsaccounts/{id}/creator')
@action('heaserver-accounts-awsaccount-get-trash', rel='hea-trash hea-context-menu', path='volumes/{volume_id}/awss3trash')
@action('heaserver-accounts-awsaccount-get-self', rel='self hea-account hea-self-container', path='awsaccounts/{id}')
@action(name='heaserver-accounts-awsaccount-get-volume', rel='hea-volume', path='volumes/{volume_id}')
async def get_awsaccount_by_volume_id(request: web.Request) -> web.Response:
    """
    Gets the AWS account associated with the given volume id. If the volume's credentials are None, it uses any
    credentials found by the AWS boto3 library.

    :param request: the HTTP request. The Authorization header must be present unless the OIDC_CLAIM_sub is the
    system|credentialsmanager user.
    :return: the requested AWS account or Not Found.
    ---
    summary: The user's AWS account.
    tags:
        - heaserver-accounts-awsaccount
    parameters:
        - name: volume_id
          in: path
          required: true
          description: The id of the user's AWS volume.
          schema:
            type: string
          examples:
            example:
              summary: A volume id
              value: 666f6f2d6261722d71757578
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
        - $ref: '#/components/parameters/Authorization'
    responses:
      '200':
        $ref: '#/components/responses/200'
      '404':
        $ref: '#/components/responses/404'
    """
    async with DesktopObjectActionLifecycle(request=request,
                                                code='hea-get',
                                                description=f'Getting my AWS account',
                                                activity_cb=publish_desktop_object) as activity:
        volume_id = request.match_info['volume_id']
        sub = request.headers.get(SUB, NONE_USER)
        cache_key = (sub, f'volume_id^{volume_id}')
        cached_value = request.app[HEA_CACHE].get(cache_key)
        if cached_value is not None:
            account, volume_id, permissions, attribute_permissions = cached_value
        else:
            account = await _get_awsaccount_by_volume_id(request, volume_id)
            if account is None:
                raise response.status_not_found()
            context = AWSAccountPermissionContext(request, volume_id)
            share = await account.get_permissions_as_share(context)
            permissions = share.permissions
            attribute_permissions = await account.get_all_attribute_permissions(context)
            account.add_user_share(share)
            request.app[HEA_CACHE][cache_key] = (account, volume_id, permissions, attribute_permissions)
            request.app[HEA_CACHE][(sub, f'id^{account.id}')] = (account, volume_id, permissions, attribute_permissions)
        activity.new_object_type_name = AWSAccount.get_type_name()
        activity.new_volume_id = volume_id
        activity.new_object_uri = f'volumes/{account.id}'
        activity.new_object_id = account.id
        return await response.get(request, account.to_dict(), permissions=permissions,
                                  attribute_permissions=attribute_permissions)


@routes.get('/awsaccounts/{id}/opener')
@action('heaserver-accounts-awsaccount-open-buckets',
        rel=f'hea-opener hea-context-aws hea-default {AWSBucket.get_mime_type()} hea-container', path='volumes/{volume_id}/bucketitems/')
@action('heaserver-accounts-awsaccount-open-storage',
        rel=f'hea-opener hea-context-aws {AWSS3Storage.get_mime_type()}', path='volumes/{volume_id}/awss3storage/')
async def get_awsaccount_opener(request: web.Request) -> web.Response:
    """
    Gets choices for opening an AWS account.

    :param request: the HTTP Request.
    :return: A Response object with a status of Multiple Choices or Not Found.
    ---
    summary: AWS account opener choices
    tags:
        - heaserver-accounts-awsaccount
    parameters:
        - $ref: '#/components/parameters/id'
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    responses:
      '300':
        $ref: '#/components/responses/300'
      '404':
        $ref: '#/components/responses/404'
    """
    id_ = request.match_info['id']
    sub = request.headers.get(SUB, NONE_USER)
    cache_key = (sub, f'id^{id_}')
    cached_value = request.app[HEA_CACHE].get(cache_key)
    async with DesktopObjectActionLifecycle(request=request,
                                                    code='hea-get',
                                                    description=f'Accessing AWS account {id_}',
                                                    activity_cb=publish_desktop_object) as activity:
        if cached_value is not None:
            _, volume_id, _, _ = cached_value
        else:
            volume_id = await _get_volume_id_by_aws_account_id(request, id_)
            if volume_id is None:
                raise response.status_not_found()
        request.match_info['volume_id'] = volume_id  # Needed to make the actions work.
        activity.new_object_type_name = AWSAccount.get_type_name()
        activity.new_object_uri = f'awsaccounts/{id_}'
        activity.new_object_id = id_
        activity.new_volume_id = volume_id
        return await response.get_multiple_choices(request)


@routes.get('/volumes/{volume_id}/awsaccounts/me/opener')
@action('heaserver-accounts-awsaccount-open-buckets',
        rel=f'hea-opener hea-context-aws hea-default {AWSBucket.get_mime_type()} hea-container', path='volumes/{volume_id}/bucketitems/')
@action('heaserver-accounts-awsaccount-open-storage',
        rel=f'hea-opener hea-context-aws {AWSS3Storage.get_mime_type()}', path='volumes/{volume_id}/awss3storage/')
async def get_awsaccount_opener_by_volume_id(request: web.Request) -> web.Response:
    """
    Gets choices for opening an AWS account.

    :param request: the HTTP Request.
    :return: A Response object with a status of Multiple Choices or Not Found.
    ---
    summary: AWS account opener choices
    tags:
        - heaserver-accounts-awsaccount
    parameters:
        - name: volume_id
          in: path
          required: true
          description: The id of the user's AWS volume.
          schema:
            type: string
          examples:
            example:
              summary: A volume id
              value: 666f6f2d6261722d71757578
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
        - $ref: '#/components/parameters/Authorization'
    responses:
      '300':
        $ref: '#/components/responses/300'
      '404':
        $ref: '#/components/responses/404'
    """
    volume_id = request.match_info['volume_id']
    id_ = request.match_info['id']
    sub = request.headers.get(SUB, NONE_USER)

    async with DesktopObjectActionLifecycle(request=request,
                                                    code='hea-get',
                                                    description=f'Getting my AWS account',
                                                    activity_cb=publish_desktop_object) as activity:
        cache_key = (sub, f'id^{id_}')
        cached_value = request.app[HEA_CACHE].get(cache_key)
        if cached_value is not None:
            account, volume_id, _, _ = cached_value
        else:
            account = await _get_awsaccount_by_volume_id(request, volume_id)
            if account is None:
                raise response.status_not_found()
        activity.new_object_type_name = AWSAccount.get_type_name()
        activity.new_object_uri = f'awsaccounts/{account.id}'
        activity.new_volume_id = volume_id
        activity.new_object_id = account.id
        return await response.get_multiple_choices(request)


# @routes.post('/volumes/{volume_id}/awsaccounts/me')
# async def post_account_awsaccounts(request: web.Request) -> web.Response:
#     """
#     Posts the awsaccounts information given the correct access key and secret access key.
#
#     :param request: the HTTP request.
#     :return: the requested awsaccounts or Not Found.
#
#     FIXME: should only be permitted by an AWS organization administrator, I would think. Need to sort out what the call looks like.
#     """
#     return await awsservicelib.post_account(request)


# @routes.put('/volumes/{volume_id}/awsaccounts/me')
# async def put_account_awsaccounts(request: web.Request) -> web.Response:
#     """
#     Puts the awsaccounts information given the correct access key and secret access key.

#     :param request: the HTTP request.
#     :return: the requested awsaccounts or Not Found.
#     """
#     volume_id = request['volume_id']
#     alt_contact_type = request.match_info.get("alt_contact_type", None)
#     email_address = request.match_info.get("email_address", None)
#     name = request.match_info.get("name", None)
#     phone = request.match_info.get("phone", None)
#     title = request.match_info.get("title", None)

#     async with DesktopObjectActionLifecycle(request=request,
#                                                 code='hea-delete',
#                                                 description=f'Updating my AWS account',
#                                                 activity_cb=publish_desktop_object) as activity:
#         activity.old_object_type_name = AWSAccount.get_type_name()
#         activity.old_object_uri = f'volumes/{volume_id}/awsaccounts/me'
#         activity.old_volume_id = volume_id
#         try:
#             async with aws.AccountClientContext(request, volume_id) as acc_client:
#                 async with aws.STSClientContext(request, volume_id) as sts_client:
#                     def do() -> str:
#                         account_id = sts_client.get_caller_identity().get('Account')
#                         acc_client.put_alternate_contact(AccountId=account_id, AlternateContactType=alt_contact_type,
#                                                         EmailAddress=email_address, Name=name, PhoneNumber=phone, Title=title)
#                         return account_id
#                     account_id = await get_running_loop().run_in_executor(None, do)
#                     sub = request.headers.get(SUB, NONE_USER)
#                     request.app[HEA_CACHE].pop((sub, f'volume_id^{volume_id}'), None)
#                     request.app[HEA_CACHE].pop((sub, f'id^{account_id}'), None)
#                     keys_to_delete = []
#                     for key in request.app[HEA_CACHE]:
#                         if key[1] is None:
#                             keys_to_delete.append(key)
#                     for key in keys_to_delete:
#                         request.app[HEA_CACHE].pop(key, None)
#                     activity.new_object_type_name = AWSAccount.get_type_name()
#                     activity.new_object_uri = f'volumes/{volume_id}/awsaccounts/me'
#                     activity.new_volume_id = volume_id
#             return web.HTTPNoContent()
#         except BotoClientError as e:
#             activity.status = Status.FAILED
#             return web.HTTPBadRequest()


# @routes.delete('/volumes/{volume_id}/awsaccounts/me')
# async def delete_account_awsaccounts(request: web.Request) -> web.Response:
#     """
#     Deletes the awsaccounts information given the correct access key and secret access key.

#     :param request: the HTTP request.
#     :return: the requested awsaccounts or Not Found.

#     FIXME: should only be permitted by an AWS organization administrator, I would think. Need to sort out what the call looks like.
#     """
#     return response.status_not_found()


@routes.get('/awsaccounts/{id}/creator')
async def get_account_creator(request: web.Request) -> web.Response:
    """
        Gets account creator choices.

        :param request: the HTTP Request.
        :return: A Response object with a status of Multiple Choices or Not Found.
        ---
        summary: Account creator choices
        tags:
            - heaserver-accounts-awsaccount
        parameters:
            - $ref: '#/components/parameters/id'
            - $ref: '#/components/parameters/OIDC_CLAIM_sub'
        responses:
          '300':
            $ref: '#/components/responses/300'
          '404':
            $ref: '#/components/responses/404'
        """
    id_ = request.match_info['id']
    async with DesktopObjectActionLifecycle(request=request,
                                                code='hea-get',
                                                description=f'Getting AWS account {id_}',
                                                activity_cb=publish_desktop_object) as activity:
        sub = request.headers.get(SUB, NONE_USER)
        cache_key = (sub, f'id^{request.match_info["id"]}')
        cached_value = request.app[HEA_CACHE].get(cache_key)
        if cached_value is None:
            volume_id = await awsservicelib.get_volume_id_for_account_id(request)
        else:
            _, volume_id, _, _ = cached_value
        if volume_id is None:
            raise response.status_not_found()
        activity.new_object_id = id_
        activity.new_object_type_name = AWSAccount.get_type_name()
        activity.new_object_uri = f'awsaccounts/{id_}'
        activity.new_volume_id = volume_id
        await _add_create_bucket_action(request, volume_id)
        return await response.get_multiple_choices(request)


@routes.get('/volumes/{volume_id}/awsaccounts/me/creator')
async def get_account_creator_by_volume_id(request: web.Request) -> web.Response:
    """
    Gets account creator choices.

    :param request: the HTTP Request.
    :return: A Response object with a status of Multiple Choices or Not Found.
    ---
    summary: Account creator choices
    tags:
        - heaserver-accounts-awsaccount
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
        - $ref: '#/components/parameters/id'
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
        - $ref: '#/components/parameters/Authorization'
    responses:
      '300':
        $ref: '#/components/responses/300'
      '404':
        $ref: '#/components/responses/404'
    """
    async with DesktopObjectActionLifecycle(request=request,
                                                code='hea-get',
                                                description=f'Getting my AWS account',
                                                activity_cb=publish_desktop_object) as activity:
        volume_id = request.match_info["volume_id"]
        async with DesktopObjectActionLifecycle(request=request,
                                                code='hea-get',
                                                description="Getting user's AWS account",
                                                activity_cb=publish_desktop_object) as activity:
            sub = request.headers.get(SUB, NONE_USER)
            cache_key = (sub, f'volume_id^{volume_id}')
            cached_value = request.app[HEA_CACHE].get(cache_key)
            if cached_value is not None:
                account, _, _, _ = cached_value
            else:
                account = await _get_awsaccount_by_volume_id(request, volume_id)
                if account is None:
                    raise response.status_not_found()
            activity.new_object_type_name = AWSAccount.get_type_name()
            activity.new_object_uri = f'awsaccounts/{account.id}'
            activity.new_volume_id = volume_id
            activity.new_object_id = account.id
            await _add_create_bucket_action(request, volume_id)
            return await response.get_multiple_choices(request)


@routes.get('/volumes/{volume_id}/awsaccounts/me/newbucket')
@routes.get('/volumes/{volume_id}/awsaccounts/me/newbucket/')
@action('heaserver-accounts-awsaccount-new-bucket-form')
async def get_new_bucket_form_by_volume_id(request: web.Request) -> web.Response:
    """
    Gets form for creating a new bucket in this account.

    :param request: the HTTP request. Required.
    :return: the current bucket, with a template for creating a child folder or Not Found if the requested item does not
    exist.
    ---
    summary: An account.
    tags:
        - heaserver-accounts-awsaccount
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
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
        - $ref: '#/components/parameters/Authorization'
    responses:
      '200':
        $ref: '#/components/responses/200'
      '404':
        $ref: '#/components/responses/404'
    """
    volume_id = request.match_info["volume_id"]
    async with DesktopObjectActionLifecycle(request=request,
                                            code='hea-get',
                                            description="Getting user's AWS account",
                                            activity_cb=publish_desktop_object) as activity:
        sub = request.headers.get(SUB, NONE_USER)
        cache_key = (sub, f'volume_id^{volume_id}')
        cached_value = request.app[HEA_CACHE].get(cache_key)
        if cached_value is not None:
            account_dict, _, permissions, attribute_permissions = cached_value
        else:
            account = await _get_awsaccount_by_volume_id(request, volume_id)
            if account is None:
                return response.status_not_found()
            context = AWSAccountPermissionContext(request, volume_id)
            share = await account.get_permissions_as_share(context)
            permissions = share.permissions
            attribute_permissions = await account.get_all_attribute_permissions(context)
            account_dict = account.to_dict()
            request.app[HEA_CACHE][cache_key] = (account_dict, volume_id, permissions, attribute_permissions)
            request.app[HEA_CACHE][(sub, f'id^{account.id}')] = (account_dict, volume_id, permissions, attribute_permissions)
        activity.new_object_id = account_dict['id']
        activity.new_object_type_name = AWSAccount.get_type_name()
        activity.new_volume_id = volume_id
        activity.new_object_uri = f'awsaccounts/{account_dict["id"]}'
        bucket = AWSBucket()
        return await response.get(request, to_dict(bucket),
                                  permissions=[Permission.CREATOR])


@routes.get('/awsaccounts/{id}/newbucket')
@routes.get('/awsaccounts/{id}/newbucket/')
@action('heaserver-accounts-awsaccount-new-bucket-form')
async def get_new_bucket_form(request: web.Request) -> web.Response:
    """
    Gets form for creating a new bucket in this account.

    :param request: the HTTP request. Required.
    :return: the current bucket, with a template for creating a child folder or Not Found if the requested item does not
    exist.
    ---
    summary: An account.
    tags:
        - heaserver-accounts-awsaccount
    parameters:
        - $ref: '#/components/parameters/id'
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
        - $ref: '#/components/parameters/Authorization'
    responses:
      '200':
        $ref: '#/components/responses/200'
      '404':
        $ref: '#/components/responses/404'
    """
    id_ = request.match_info['id']
    async with DesktopObjectActionLifecycle(request=request,
                                                code='hea-get',
                                                description=f'Getting AWS account {id_}',
                                                activity_cb=publish_desktop_object) as activity:
        sub = request.headers.get(SUB, NONE_USER)
        cache_key = (sub, f'id^{request.match_info["id"]}')
        cached_value = request.app[HEA_CACHE].get(cache_key)
        if cached_value is not None:
            account, volume_id, permissions, attribute_permissions = cached_value
        else:
            account, volume_id = await _get_awsaccount_by_aws_account_id(request, id_)
            if account is None:
                return response.status_not_found()
            context = AWSAccountPermissionContext(request, volume_id)
            share = await account.get_permissions_as_share(context)
            account.add_user_share(share)
            permissions = share.permissions
            attribute_permissions = await account.get_all_attribute_permissions(context)
            request.app[HEA_CACHE][cache_key] = (account, volume_id, permissions, attribute_permissions)
        activity.new_object_id = id_
        activity.new_object_type_name = AWSAccount.get_type_name()
        activity.new_object_uri = f'awsaccounts/{id_}'
        activity.new_volume_id = volume_id
        bucket = AWSBucket()
        return await response.get(request, to_dict(bucket), permissions=[Permission.CREATOR])


@routes.post('/volumes/{volume_id}/awsaccounts/me/newbucket')
@routes.post('/volumes/{volume_id}/awsaccounts/me/newbucket/')
async def post_new_bucket_by_volume_id(request: web.Request) -> web.Response:
    """
    Gets form for creating a new bucket in this account.

    :param request: the HTTP request. Required.
    :return: the current account, with a template for creating a bucket or Not Found if the requested account does not
    exist.
    ---
    summary: An account.
    tags:
        - heaserver-accounts-awsaccount
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
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    requestBody:
        description: A new bucket.
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
                        "value": "my-bucket"
                      },
                      {
                        "name": "type",
                        "value": "heaobject.bucket.AWSBucket"
                      },
                      {
                        "name": "region",
                        "value": "us-west-1"
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
                    "display_name": "my-bucket",
                    "type": "heaobject.bucket.AWSBucket",
                    "region": "us-west-1"
                  }
    responses:
      '201':
        $ref: '#/components/responses/201'
      '400':
        $ref: '#/components/responses/400'
      '404':
        $ref: '#/components/responses/404'
    """
    async with DesktopObjectActionLifecycle(request=request,
                                            code='hea-create',
                                            description=f'Creating a new bucket in my AWS account',
                                            activity_cb=publish_desktop_object) as activity:
        volume_id = request.match_info['volume_id']
        bucket_url = await type_to_resource_url(request, AWSBucket)
        if bucket_url is None:
            raise ValueError('No AWSBucket service registered')
        headers = {SUB: request.headers[SUB]} if SUB in request.headers else None
        resource_base = str(URL(bucket_url) / volume_id / 'buckets')
        bucket = await new_heaobject_from_type(request, type_=AWSBucket)
        try:
            id_ = await client.post(request.app, resource_base, data=bucket, headers=headers)
            keys_to_delete = []
            for key in request.app[HEA_CACHE]:
                if key[1] is None:
                    keys_to_delete.append(key)
            for key in keys_to_delete:
                request.app[HEA_CACHE].pop(key, None)
            activity.new_object_id = id_
            activity.new_object_type_name = AWSBucket.get_type_name()
            activity.new_volume_id = volume_id
            activity.new_object_uri = f'volumes/{volume_id}/buckets/{id_}'
            return await response.post(request, id_, resource_base)
        except ClientResponseError as e:
            raise response.status_from_exception(e) from e
        except ClientError as e:
            raise response.status_internal_error(str(e)) from e



@routes.post('/awsaccounts/{id}/newbucket')
@routes.post('/awsaccounts/{id}/newbucket/')
async def post_new_bucket(request: web.Request) -> web.Response:
    """
    Gets form for creating a new bucket in this account.

    :param request: the HTTP request. Required.
    :return: the current account, with a template for creating a bucket or Not Found if the requested account does not
    exist.
    ---
    summary: An account.
    tags:
        - heaserver-accounts-awsaccount
    parameters:
        - $ref: '#/components/parameters/id'
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    requestBody:
        description: A new bucket.
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
                        "value": "my-bucket"
                      },
                      {
                        "name": "type",
                        "value": "heaobject.bucket.AWSBucket"
                      },
                      {
                        "name": "region",
                        "value": "us-west-1"
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
                    "display_name": "my-bucket",
                    "type": "heaobject.bucket.AWSBucket",
                    "region": "us-west-1"
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
        id_ = request.match_info['id']
    except KeyError as e:
        return response.status_bad_request(str(e))
    async with DesktopObjectActionLifecycle(request=request,
                                                code='hea-create',
                                                description=f'Creating a new bucket in AWS account',
                                                activity_cb=publish_desktop_object) as activity:
        logger = logging.getLogger(__name__)
        volume_id = await awsservicelib.get_volume_id_for_account_id(request)
        if volume_id is None:
            activity.status = Status.FAILED
            return response.status_bad_request(f'Invalid account id {request.match_info["id"]}')
        bucket_url = await type_to_resource_url(request, AWSBucket)
        if bucket_url is None:
            raise ValueError('No AWSBucket service registered')
        headers = {SUB: request.headers[SUB]} if SUB in request.headers else None
        resource_base = str(URL(bucket_url) / volume_id / 'buckets')
        bucket = await new_heaobject_from_type(request, type_=AWSBucket)
        try:
            id_ = await client.post(request.app, resource_base, data=bucket, headers=headers)
            keys_to_delete = []
            for key in request.app[HEA_CACHE]:
                if key[1] is None:
                    keys_to_delete.append(key)
            for key in keys_to_delete:
                request.app[HEA_CACHE].pop(key, None)
            activity.new_object_id = id_
            activity.new_object_type_name = AWSBucket.get_type_name()
            activity.new_volume_id = volume_id
            activity.new_object_uri = f'volumes/{volume_id}/buckets/{id_}'
            return await response.post(request, id_, resource_base)
        except ClientResponseError as e:
            activity.status = Status.FAILED
            return response.status_generic(status=e.status, body=e.message)
        except ClientError as e:
            activity.status = Status.FAILED
            return response.status_generic(status=500, body=str(e))


def start_with(config: Configuration) -> None:
    start(package_name='heaserver-accounts', db=opensearch.S3WithOpenSearchManager,
          wstl_builder_factory=builder_factory(__package__),
          cleanup_ctx=[publisher_cleanup_context_factory(config),
              wait_on_coro_cleanup_ctx(coro=_listen_for_object_change, delay=30)], config=config)

async def _get_awsaccount_by_volume_id(request: Request, volume_id: str) -> AWSAccount:
    """
    Gets the AWS account associated with the provided volume id.

    Only get since you can't delete or put id information
    currently being accessed. If organizations get included, then the delete, put, and post will be added for name,
    phone, email, ,etc.
    NOTE: maybe get email from the login portion of the application?

    :param request: the aiohttp Request (required). The request must have valid OIDC_CLAIM_sub and Authorization
    headers.
    :param volume_id: the id string of the volume representing the user's AWS account.
    :return: an HTTP response with an AWSAccount object in the body.
    FIXME: a bad volume_id should result in a 400 status code; currently has status code 500.
    """
    return await request.app[HEA_DB].get_account(request, volume_id)


async def _get_awsaccount_by_aws_account_id(request: web.Request, aws_account_id: str) -> tuple[AWSAccount | None, str | None]:
    """
    Gets an account by its id and the account's volume id. The id is expected to be in the request object's match_info
    mapping, with key 'id'.

    :param request: an aiohttp Request object (required). The request must have valid OIDC_CLAIM_sub and Authorization
    headers.
    :return: a two-tuple containing an AWSAccount dict and volume id, or None if no account was found.
    """
    db = request.app[HEA_DB]
    volume_id = await _get_volume_id_by_aws_account_id(request, aws_account_id)
    if volume_id is not None:
        return await db.get_account(request, volume_id), volume_id
    return (None, None)


async def _get_volume_id_by_aws_account_id(request: web.Request, aws_account_id: str) -> str | None:
    """
    Gets an account's volume id. The id is expected to be in the request object's match_info mapping, with key 'id'.

    :param request: an aiohttp Request object (required).
    :return: the volume id, or None if no account was found.
    """
    db = request.app[HEA_DB]
    async for volume in db.get_volumes(request, AWSFileSystem, account_ids=[f'{AWSAccount.get_type_name()}^{aws_account_id}']):
        return volume.id
    return None



async def _get_account_by_name(request: web.Request) -> tuple[AWSAccount | None, str | None]:
    """
    Gets an account by its id and the account's volume id. The id is expected to be the request object's match_info
    mapping, with key 'id'.

    :param request: an aiohttp Request object (required). The request must have valid OIDC_CLAIM_sub and Authorization
    headers.
    :return: a two-tuple containing an AWSAccount and volume id, or None if no account was found.
    """
    db = request.app[HEA_DB]
    volume_ids = [volume.id async for volume in db.get_volumes(request, AWSFileSystem)]
    try:
        return await anext((a, v) async for a, v in db.get_accounts(request, volume_ids) if a.name == request.match_info['name'])
    except StopAsyncIteration:
        return (None, None)


async def _post_account(request: Request) -> Response:
    """
    Called this create since the put, get, and post account all handle information about accounts, while create and delete handle creating/deleting new accounts

    account_email (str)     : REQUIRED: The email address of the owner to assign to the new member account. This email address must not already be associated with another AWS account.
    account_name (str)      : REQUIRED: The friendly name of the member account.
    account_role (str)      : If you don't specify this parameter, the role name defaults to OrganizationAccountAccessRole
    access_to_billing (str) : If you don't specify this parameter, the value defaults to ALLOW

    source: https://github.com/aws-samples/account-factory/blob/master/AccountCreationLambda.py

    Note: Creates an AWS account that is automatically a member of the organization whose credentials made the request.
    This is an asynchronous request that AWS performs in the background. Because CreateAccount operates asynchronously,
    it can return a successful completion message even though account initialization might still be in progress.
    You might need to wait a few minutes before you can successfully access the account
    The user who calls the API to create an account must have the organizations:CreateAccount permission

    When you create an account in an organization using the AWS Organizations console, API, or CLI commands, the information required for the account to operate as a standalone account,
    such as a payment method and signing the end user license agreement (EULA) is not automatically collected. If you must remove an account from your organization later,
    you can do so only after you provide the missing information.
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/organizations.html#Organizations.Client.create_account

    You can only close an account from the Billing and Cost Management Console, and you must be signed in as the root user.
    """
    try:
        volume_id = request.match_info.get("volume_id", None)
        account_email = request.match_info.get("account_email", None)
        account_name = request.match_info.get("account_name", None)
        account_role = request.match_info.get("account_role", None)
        access_to_billing = request.match_info.get("access_to_billing", None)
        if not volume_id:
            return web.HTTPBadRequest(body="volume_id is required")
        if not account_email:
            return web.HTTPBadRequest(body="account_email is required")
        if not account_name:
            return web.HTTPBadRequest(body="account_name is required")
        if not account_role:
            return web.HTTPBadRequest(body="account_role is required")
        if not access_to_billing:
            return web.HTTPBadRequest(body="access_to_billing is required")

        def is_iam_user_access_to_billing_type(val: str) -> TypeGuard[IAMUserAccessToBillingType]:
            return val in get_args(IAMUserAccessToBillingType)
        if not is_iam_user_access_to_billing_type(access_to_billing):
            return web.HTTPBadRequest(body="access_to_billing may be ALLOW or DENY")

        async with aws.OrganizationsClientContext(request, volume_id) as org_client:
            org_client.create_account(Email=account_email, AccountName=account_name, RoleName=account_role,
                                      IamUserAccessToBilling=access_to_billing)
            return web.HTTPAccepted()
            # time.sleep(60)        # this is here as it  takes some time to create account, and the status would always be incorrect if it went immediately to next lines of code
            # account_status = org_client.describe_create_account_status(CreateAccountRequestId=create_account_response['CreateAccountStatus']['Id'])
            # if account_status['CreateAccountStatus']['State'] == 'FAILED':    # go to boto3 link above to see response syntax
            #     web.HTTPBadRequest()      # the response syntax contains reasons for failure, see boto3 link above to see possible reasons
            # else:
            #     return web.HTTPCreated()  # it may not actually be created, but it likely isn't a failure which means it will be created after a minute or two more, see boto3 docs
    except BotoClientError as e:
        return web.HTTPBadRequest()  # see boto3 link above to see possible  exceptions


async def _aws_account_ids_to_aws_accounts(request: web.Request, aws_account_ids: Sequence[str], calc_permissions=True) -> tuple[list[AWSAccount], list[str], list[list[Permission]], list[dict[str, list[Permission]]]]:
    logger = logging.getLogger(__name__)
    sub = request.headers.get(SUB, NONE_USER)
    cache_key = (sub, None, tuple(aws_account_ids), calc_permissions)
    cache_value = request.app[HEA_CACHE].get(cache_key) if aws_account_ids is None else None
    if cache_value is None:
        db = request.app[HEA_DB]
        accounts = []
        volume_ids = [volume.id async for volume in db.get_volumes(request, AWSFileSystem, account_ids=tuple(f'{AWSAccount.get_type_name()}^{a}' for a in aws_account_ids))]
        logger.debug('Checking volumes %s for accounts %s', volume_ids, aws_account_ids)
        account_id_to_account = {}
        permissions = []
        attribute_permissions = []
        async for aws_account, volume_id in db.get_accounts(request, volume_ids):
            if not aws_account_ids or aws_account.id in aws_account_ids:
                account_id_to_account[aws_account.id] = aws_account
                if calc_permissions:
                    context = AWSAccountPermissionContext(request, volume_id)
                    share = await aws_account.get_permissions_as_share(context)
                    aws_account.add_user_share(share)
                    permissions.append(share.permissions)
                    attribute_permissions_obj = await aws_account.get_all_attribute_permissions(context)
                    attribute_permissions.append(attribute_permissions_obj)
                    request.app[HEA_CACHE][(sub, f'id^{aws_account.id}')] = (aws_account, volume_id,
                                                                             permissions, attribute_permissions_obj)
        accounts = list(account_id_to_account.values())
        request.app[HEA_CACHE][cache_key] = (accounts, volume_ids, permissions, attribute_permissions)
    else:
        accounts, volume_ids, permissions, attribute_permissions = cache_value
    return accounts, volume_ids, permissions, attribute_permissions

from heaserver.service.db.awsaction import S3_CREATE_BUCKET

class _S3BucketPermissionContext(AWSPermissionContext):
    def __init__(self, request: Request, volume_id: str, **kwargs):
        if 'volume_id' not in request.match_info:
            request_cloned = request.clone()
            request_cloned.match_info['volume_id'] = volume_id
        super().__init__(request=request_cloned, actions=[S3_CREATE_BUCKET], **kwargs)


    async def can_create(self, desktop_object_type: type[DesktopObject]) -> bool:
        """
        Checks if the user can create a bucket of the given type, consulting AWS permissions.

        :param desktop_object_type: The type of the desktop object to check.
        :return: True if the user can create a bucket of the given type, False otherwise.
        """
        if not issubclass(desktop_object_type, AWSBucket):
            return False

        bucket = AWSBucket()
        bucket.id = 'cb-foo'  # Dummy id, unfortunately it seems required for the permission check, but what if we have a bucket name restriction?
        return Permission.EDITOR in await self.get_permissions(bucket)

    def _caller_arn(self, obj: AWSDesktopObject):
        return f'arn:aws:s3:::{obj.resource_type_and_id}'


async def _add_create_bucket_action(request: web.Request, volume_id: str):
    bucket_component = await client.get_component(request.app, AWSBucket)
    assert bucket_component is not None, 'bucket_component cannot be None'
    bucket_resource = bucket_component.get_resource(AWSBucket.get_type_name())
    assert bucket_resource is not None, 'bucket_resource cannot be None'
    context = _S3BucketPermissionContext(request, volume_id)
    if await context.can_create(AWSBucket):
        add_run_time_action(request, 'heaserver-accounts-awsaccount-create-bucket',
                                    rel='hea-creator hea-default application/x.bucket',
                                    path=f'volumes/{volume_id}/awsaccounts/me/newbucket')



async def _listen_for_object_change(app: web.Application):
    logger = logging.getLogger(__name__)
    session = app[appproperty.HEA_CLIENT_SESSION]
    if not session:
        logger.error("session does not exist ")
        return

    try:
        headers_ = {SUB: CREDENTIALS_MANAGER_USER}
        component = await client.get_component_by_name(app, 'heaserver-accounts', client_session=session)
        assert component is not None, 'registry entry for heaserver-accounts not found'
        assert component.base_url is not None, 'registry entry for heaserver-accounts has no base_url'
        await client.put(app, URL(component.base_url) / 'awsaccounts' / 'internal' / 's3event', data={}, headers=headers_)
    except asyncio.TimeoutError:
        logger.debug("Request timed out as expected")
    except ClientResponseError as e:
        if e.status == 404:
            logger.debug("S3 event listening was not found, probably because it is not configured")
        else:
            raise e
    except Exception as ex:
        logger.error("Background running s3event aborted", exc_info=ex)
        raise ex


async def _insert_s3_object_from_sqs(request: web.Request, messages: list[dict]) -> Response:
    logger = logging.getLogger(__name__)

    async def message_to_item_gen(messages: list[dict]):
        try:
            # helper to decide if an incoming event should be applied
            async def should_process_event(incoming, current):
                # no existing document — always process
                if not current:
                    return True

                # duplicate delivery: same version + same event
                if current.version_id == incoming.version_id and current.event_name == incoming.event_name:
                    return False

                # same version but different event type (e.g. DeleteMarkerCreated -> ObjectRemoved)
                if current.version_id == incoming.version_id and current.event_name != incoming.event_name:
                    return True

                # older event time → ignore
                try:
                    current_time = datetime.fromisoformat(current.modified)
                    incoming_time = datetime.fromisoformat(incoming.modified)
                    logger.debug(f"current_time {current_time} new event time {incoming_time}")
                    if incoming_time <= current_time:
                        logger.debug(f"Incoming event {incoming.event_name} for {incoming.path} is stale, skipping.")
                        return False
                except Exception:
                    # if parsing fails, fall back to process
                    pass

                return True

            for msg in messages:
                raw_body = msg.get('Body')
                if not raw_body:
                    continue

                body = json_loads(raw_body)
                if isinstance(body, dict) and 'Message' in body:
                    try:
                        message_data = json_loads(body['Message'])
                        records = message_data.get('Records', [])
                    except orjson.JSONDecodeError:
                        logger.debug("Failed to parse Message JSON string in SNS-style body.")
                        continue
                else:
                    #  S3 Event Notification structure (Body -> Records)
                    records = body.get('Records', [])

                for r in records:
                    try:
                        if not r.get('s3'):
                            continue

                        s3 = r['s3']
                        if 'bucket' not in s3 or 'object' not in s3:
                            continue

                        search_aws_obj = AWSS3SearchItemInFolder()
                        bucket = s3.get('bucket')
                        obj = s3.get('object')
                        inventory_event = 'inventory' in bucket.get('name', '')
                        config_ids = s3.get('configurationId', '').split("_")

                        # key is url-encoded, decoding..
                        unquote_key = unquote_plus(obj.get('key', ''))
                        if not bucket.get('name') or not unquote_key:
                            logger.debug('bucket.name or unquote_key missing, ignoring event')
                            continue

                        # populate the new item
                        search_aws_obj.bucket_id = bucket['name']
                        search_aws_obj.modified = r.get('eventTime', now())
                        search_aws_obj.path = f"/{bucket['name']}/{unquote_key}"
                        search_aws_obj.size = obj.get('size', 0)
                        search_aws_obj.version_id = obj.get('versionId', None)
                        search_aws_obj.id = encode_key(unquote_key)
                        search_aws_obj.event_name = r.get('eventName')
                        search_aws_obj.account_id = (
                            config_ids[1]
                            if not inventory_event and config_ids and len(config_ids) > 1
                            else None
                        )
                        search_aws_obj.is_delete_marker = (
                            "DeleteMarkerCreated" in search_aws_obj.event_name
                            if search_aws_obj.event_name else False
                        )

                        # get current doc if exists
                        current_doc = await opensearchlib.get(request, search_aws_obj.id, AWSS3SearchItemInFolder)

                        event_name = cast(str, search_aws_obj.event_name or "")

                        if not await should_process_event(search_aws_obj, current_doc):
                            continue

                        # --- handle deletes and restores ---
                        if "ObjectRemoved:Delete" == event_name:
                            if (current_doc and current_doc.is_delete_marker
                                and current_doc.version_id == search_aws_obj.version_id):
                                search_aws_obj.is_delete_marker = False
                                search_aws_obj.event_name = "ObjectCreated:Put"
                            else:
                                # otherwise, set to deleted state
                                await publish_desktop_object(request.app, search_aws_obj)
                                continue

                            yield search_aws_obj

                        elif "ObjectRemoved:DeleteMarkerCreated" == event_name:
                            search_aws_obj.is_delete_marker = True
                            yield search_aws_obj

                        else:
                            # all other events recorded if not delete marker or permanent delete
                            search_aws_obj.is_delete_marker = False
                            yield search_aws_obj


                    except Exception as e:
                        continue

        except orjson.JSONDecodeError as je:
            logger.debug('The queue message could not be deserialized')
            raise je

    return await opensearchlib.batch_insert(request=request, doc_gen=message_to_item_gen(messages))
# S3 event
@routes.put('/awsaccounts/internal/s3event')
async def s3_event_handler(request: web.Request) -> web.Response:
    logger = logging.getLogger(__name__)
    sub = request.headers.get(SUB, NONE_USER)
    loop = asyncio.get_running_loop()

    # TODO: get credentials from volume if index ends up using creds
    aws_cred: AWSCredentials = AWSCredentials()


    async with DesktopObjectActionLifecycle(request=request,
                                            code='hea-update-part',
                                            description=f'Received s3 object update for OpenSearch index',
                                            activity_cb=publish_desktop_object) as activity:
        try:
            root_account_prop, sqs_url_prop, pull_rate_prop = (prop.value for prop in await asyncio.gather(*[
                request.app[HEA_DB].get_property(app=request.app, name="AWS_ROOT_ACCOUNT"),
                request.app[HEA_DB].get_property(app=request.app, name="AWS_ROOT_SQS_URL"),
                request.app[HEA_DB].get_property(app=request.app, name="AWS_ROOT_SQS_PULL_RATE")
            ]))
        except AttributeError as e:
            logger.debug("S3 event listening is not configured", exc_info=True)
            raise response.status_not_found()
        try:
            if not root_account_prop or not sqs_url_prop:
                logger.warning("Missing account and SQS properties that are required.")
                return response.status_bad_request(body="Missing role and SQS properties that are required.")
            aws_cred.role = f"arn:aws:iam::{root_account_prop}:role/"
            admin_cred: AWSCredentials = await request.app[HEA_DB].elevate_privileges(request, aws_cred)
            admin_cred.where = 'us-east-1'
            async with SQSClientContext(request=request, credentials=admin_cred) as sqs_client:
                start = time.time()
                while True:
                    try:
                        resp = await loop.run_in_executor(None, partial(
                            sqs_client.receive_message,
                            QueueUrl=sqs_url_prop,
                            MaxNumberOfMessages=10,
                            WaitTimeSeconds=int(pull_rate_prop) if pull_rate_prop else 20
                        ))

                        messages_raw = resp.get('Messages', [])
                        if not messages_raw:
                            logger.debug("No messages received. Waiting...")
                            continue

                        messages = [dict(msg) for msg in messages_raw]

                        inserted = await _insert_s3_object_from_sqs(request, messages)
                        if inserted.status == 404:
                            logger.warning("Insert failed (404). Not deleting messages.")
                        else:
                            logger.info("Messages inserted successfully into index.")

                        delete_entries = [
                            DeleteMessageBatchRequestEntryTypeDef(
                                Id=cast(str, msg["MessageId"]),
                                ReceiptHandle=cast(str, msg["ReceiptHandle"])
                            ) for msg in messages
                        ]
                        try:
                            if delete_entries:
                                await loop.run_in_executor(None, partial(
                                    sqs_client.delete_message_batch,
                                    QueueUrl=sqs_url_prop,
                                    Entries=delete_entries
                                ))
                                logger.debug(f"Deleted {len(delete_entries)} messages.")
                        except BotoClientError as de:
                            logger.error(f"Failed to delete messages from SQS: {de}")
                            raise de

                    except BotoClientError as be:
                        if be.response['Error']['Code'] == 'ExpiredToken':
                            logger.debug("SQS client token expired. Re-authenticating.")
                            break  # or reinitialize creds if supported
                        logger.error(f"BotoClientError: {be}")
                        break
                    except Exception as e:
                        logger.exception(f"Unexpected error in SQS loop: {e}")
                        await asyncio.sleep(5)  # short pause before retry

                logger.debug("The timer took this many seconds: %s" % (time.time() - start) )

            return await response.put(True)

        except ClientResponseError as e:
            logging.error('Failed start sqs queue, %s' % str(e))
            activity.status = Status.FAILED
            return response.status_generic(status=e.status, body=str(e))
        except Exception as e:
            logging.error('Failed start sqs queue, %s' % str(e))
            activity.status = Status.FAILED
            return response.status_generic(status=500, body=str(e))

async def _get_context_path(request: web.Request, path: str, internal_url: str, external_url: str) \
    -> list[tuple[str, str, str]]:
    fragments = path.split("/") if path else []
    if not fragments:
        return []

    # Build all sub-paths, right to left
    joined_paths = []
    for i in range(len(fragments), 0, -1):
        current_path = '/'.join(fragments[:i])
        joined_paths.append(current_path)

    # First entry is top-level (possibly a file)
    tasks = [
        _build_hierarchical_path(request, p, internal_url, external_url, is_leaf=(i == 0))
        for i, p in enumerate(joined_paths)
    ]

    results = await asyncio.gather(*tasks)
    return list(reversed(results))


async def _build_hierarchical_path(
    request: web.Request,
    path_fragment: str,
    internal_url: str,
    external_url: str,
    is_leaf: bool
) -> tuple[str, str, str]:
    logger = logging.getLogger(__name__)
    sub = request.headers.get(SUB, NONE_USER)
    auth = request.headers.get(AUTHORIZATION, '')
    headers = {SUB: sub, AUTHORIZATION: auth}

    # Determine whether it’s a file or folder/project
    is_file = not path_fragment.endswith('/')

    if is_leaf and is_file:
        encoded_key = encode_key(path_fragment)
        key_name = 'awss3files'
        return (
            f"{external_url}/{key_name}/{encoded_key}",
            f"{key_name}/{encoded_key}",
            AWSS3FileObject.get_type_name()
        )

    encoded_key = encode_key(path_fragment + '/' if not path_fragment.endswith('/') else path_fragment)
    key_name = 'awss3projects'

    if await client.has(request.app, f"{internal_url}/{key_name}/{encoded_key}",
                        AWSS3Project, None, headers=headers):
        return (
            f"{external_url}/{key_name}/{encoded_key}",
            f"{key_name}/{encoded_key}",
            AWSS3Project.get_type_name()
        )
    else:
        key_name = 'awss3folders'
        return (
            f"{external_url}/{key_name}/{encoded_key}",
            f"{key_name}/{encoded_key}",
            AWSS3Folder.get_type_name()
        )

