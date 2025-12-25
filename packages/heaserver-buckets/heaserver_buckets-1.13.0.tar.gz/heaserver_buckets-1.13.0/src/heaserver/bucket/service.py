"""
The HEA Server Buckets Microservice provides ...
"""
import logging

from heaserver.service import response, client
from heaserver.service.runner import init_cmd_line, routes, start, web
from heaserver.service.db import awsservicelib, aws
from heaserver.service.db.database import get_credentials_from_volume
from heaserver.service.wstl import builder_factory, action
from heaobject.folder import AWSS3BucketItem, Folder, AWSS3Folder, AWSS3Item
from heaobject.project import AWSS3Project
from heaobject.keychain import AWSCredentials, CredentialsView
from heaobject.bucket import AWSBucket, BucketCollaborators
from heaobject.error import DeserializeException
from heaobject.root import Tag, ViewerPermissionContext, Permission, ShareImpl, DesktopObjectDict, PermissionContext, \
    AbstractDesktopObject, AbstractMemberObject, json_dumps, to_dict
from heaobject.attribute import SimpleAttribute, ListAttribute
from heaobject.activity import Status
from heaobject.user import NONE_USER, AWS_USER, CREDENTIALS_MANAGER_USER
from heaobject.util import parse_bool
from heaobject.person import Role, Group, Person, encode_group, encode_role
from heaobject.collaborator import AWSAddingCollaborator, AWSRemovingCollaborator
from heaobject.account import AWSAccount
from heaobject.volume import Volume, AWSFileSystem
from heaobject.organization import Organization
from heaserver.service.appproperty import HEA_CACHE, HEA_DB
from heaserver.service.oidcclaimhdrs import SUB
from heaserver.service.heaobjectsupport import new_heaobject_from_type, type_to_resource_url
from heaserver.service.sources import AWS_S3
from heaserver.service.messagebroker import publish_desktop_object, publisher_cleanup_context_factory
from heaserver.service.activity import DesktopObjectActionLifecycle
from heaserver.service.wstl import RuntimeWeSTLDocumentBuilder
from heaserver.service.uritemplate import tvars
from heaserver.service.requestproperty import HEA_WSTL_BUILDER
from heaserver.service.config import Configuration
from botocore.exceptions import ClientError as BotoClientError
import asyncio
from typing import Any, Coroutine, cast, Literal
from yarl import URL
from mypy_boto3_s3.client import S3Client
from mypy_boto3_s3.type_defs import PublicAccessBlockConfigurationTypeDef, VersioningConfigurationTypeDef, \
    TagTypeDef, BucketTypeDef
from mypy_boto3_iam.client import IAMClient
from mypy_boto3_iam.type_defs import PolicyDocumentTypeDef, PolicyDocumentDictTypeDef, PolicyTypeDef
from functools import partial
from aiohttp.client_exceptions import ClientError, ClientResponseError
from aiohttp import hdrs
from datetime import datetime
from .context import S3BucketPermissionsContext
import orjson
from collections.abc import AsyncIterator, Collection, AsyncGenerator, Iterator, Sequence
from itertools import chain
import re
from dataclasses import dataclass

MONGODB_BUCKET_COLLECTION = 'buckets'

ISS = 'OIDC_CLAIM_iss'
AZP = 'OIDC_CLAIM_azp'

_update_collaborators_lock = asyncio.Lock()


class PreflightFormData(AbstractDesktopObject):
    def __init__(self) -> None:
        super().__init__()


@routes.get('/preflights/buckets/delete')
@action(name='heaserver-buckets-bucket-delete-get-preflight-form')
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
    def __init__(self) -> None:
        super().__init__()
    display_name = SimpleAttribute(str, 'Untitled')
    bucket_id = SimpleAttribute(str, None)


class PreflightConfirmationData(AbstractDesktopObject):
    """
    Data for the preflight confirmation form.
    """
    def __init__(self) -> None:
        super().__init__()
    warning_message = SimpleAttribute(str, None)
    objects_to_delete = ListAttribute[PreflightObjectListItem]()
    delete_confirmation = SimpleAttribute(str, None)


@routes.post('/preflights/buckets/delete')
async def post_delete_preflight(request: web.Request) -> web.Response:
    """
    Preflight check for DELETE requests to buckets. A template is expected in the request body with a
    desktop_object_urls property containing a list of URLs for the objects to delete. If the template does not contain
    a confirmed property, the response will be a form that asks the user to confirm the deletion. The form may be
    submitted to this endpoint again with the confirmed property set to True or False. If set to True, preflight
    checking is performed, and if deletion is approved, a 204 status code is returned to indicate that the deletion may
    proceed. If confirmed is set to False, or preflight checking fails, an error status code is returned.

    :param request: the HTTP request.
    :return: Always returns status code 204.
    """
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
        url_template = 'http{prefix}/volumes/{volume_id}/buckets/{bucket_id}'
        tvars_l = list[dict[str, Any]]()
        for url in desktop_object_urls:
            tvars_l.append(tvars(url_template, str(URL(url).with_query({}).with_fragment(None))))
        p: PreflightConfirmationData = PreflightConfirmationData()
        objects_to_delete: list[PreflightObjectListItem] = []
        for i, url in enumerate(desktop_object_urls):
            tvars_ = tvars_l[i]
            preflight_obj: PreflightObjectListItem = PreflightObjectListItem()
            preflight_obj.display_name = str(tvars_['bucket_id'])
            preflight_obj.bucket_id = str(tvars_['bucket_id'])
            objects_to_delete.append(preflight_obj)
        p.objects_to_delete = objects_to_delete
        if len(objects_to_delete) == 1:
            object_summary = f'bucket {objects_to_delete[0].bucket_id}'
        elif len(objects_to_delete) == 2:
            object_summary = f'buckets {objects_to_delete[0].bucket_id} and ' \
                f'{objects_to_delete[1].bucket_id}'
        elif len(objects_to_delete) == 3:
            object_summary = f'buckets {objects_to_delete[0].bucket_id} and ' \
                f'{objects_to_delete[1].bucket_id}, and 1 more bucket'
        else:
            object_summary = f'buckets {objects_to_delete[0].bucket_id} and ' \
                f'{objects_to_delete[1].bucket_id}, and ' \
                f'{len(objects_to_delete) - 2} more buckets'
        msg_value = f'Are you sure you want to delete {object_summary}? This action cannot be undone.'
        p.warning_message = msg_value
        wstl_doc.add_design_time_action({
            'name': 'heaserver-buckets-bucket-delete-preflight-confirmation',
            'description': 'Preflight check for AWS S3 bucket delete requests.',
            'type': 'safe',
            'action': 'read',
            'target': 'item cj-template',
            'prompt': 'S3 bucket delete confirmation',
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
        wstl_doc.add_run_time_action(name='heaserver-buckets-bucket-delete-preflight-confirmation',
                                     rel='hea-message-warning')
        return await response.get(request, to_dict(p))
    elif parse_bool(confirmed):
        return response.status_no_content()
    else:
        return response.status_bad_request('Deletion request was rejected')

@routes.get('/volumes/{volume_id}/buckets/{id}')
@action('heaserver-buckets-bucket-get-open-choices', rel='hea-opener-choices hea-context-menu hea-downloader',
        path='volumes/{volume_id}/buckets/{id}/opener')
@action(name='heaserver-buckets-bucket-get-properties', rel='hea-properties hea-context-menu')
@action(name='heaserver-buckets-bucket-get-create-choices', rel='hea-creator-choices hea-context-menu',
        path='volumes/{volume_id}/buckets/{id}/creator')
@action(name='heaserver-buckets-bucket-get-trash', rel='hea-trash hea-context-menu', path='volumes/{volume_id}/awss3trash')
@action(name='heaserver-buckets-bucket-get-self', rel='self hea-self-container', path='volumes/{volume_id}/buckets/{id}')
@action(name='heaserver-buckets-bucket-get-volume', rel='hea-volume', path='volumes/{volume_id}')
@action(name='heaserver-buckets-bucket-get-awsaccount', rel='hea-account', path='volumes/{volume_id}/awsaccounts/me')
@action(name='heaserver-buckets-bucket-get-uploader', rel='hea-uploader', path='volumes/{volume_id}/buckets/{id}/awss3folders/root/uploader')
@action(name='heaserver-buckets-bucket-get-delete-preflight-url', rel='hea-delete-preflight',
        path='preflights/buckets/delete')
async def get_bucket(request: web.Request) -> web.Response:
    """
    Gets the bucket with the specified id.
    :param request: the HTTP request.
    :return: the requested bucket or Not Found.
    ---
    summary: A specific bucket.
    tags:
        - heaserver-buckets
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
        - $ref: '#/components/parameters/id'
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
        - name: data
          in: query
          required: false
          description: Whether to include the bucket data in the response. If omitted, assumed to be true.
          schema:
            type: boolean
          examples:
            example:
              summary: Include data
              value: true
    responses:
      '200':
        description: Expected response to a valid request.
        content:
            application/json:
                schema:
                    type: array
                    items:
                        type: object
            application/vnd.collection+json:
                schema:
                    type: array
                    items:
                        type: object
            application/vnd.wstl+json:
                schema:
                    type: array
                    items:
                        type: object
      '404':
        $ref: '#/components/responses/404'
    """
    return await _get_bucket(request, S3BucketPermissionsContext(request))


@routes.get('/volumes/{volume_id}/buckets/byname/{bucket_name}')
@action(name='heaserver-buckets-bucket-get-self', rel='self hea-self-container', path='volumes/{volume_id}/buckets/{id}')
@action(name='heaserver-buckets-bucket-get-volume', rel='hea-volume', path='volumes/{volume_id}')
@action(name='heaserver-buckets-bucket-get-awsaccount', rel='hea-account', path='volumes/{volume_id}/awsaccounts/me')
async def get_bucket_by_name(request: web.Request) -> web.Response:
    """
    Gets the bucket with the specified name.
    :param request: the HTTP request.
    :return: the requested bucket or Not Found.
    ---
    summary: A specific bucket.
    tags:
        - heaserver-buckets
    parameters:
        - name: bucket_name
          in: path
          required: true
          description: The name of the bucket to retrieve.
          schema:
            type: string
          examples:
            example:
              summary: Name of the bucket
              value: hci-foundation
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
    responses:
      '200':
        description: Expected response to a valid request.
        content:
            application/json:
                schema:
                    type: array
                    items:
                        type: object
            application/vnd.collection+json:
                schema:
                    type: array
                    items:
                        type: object
            application/vnd.wstl+json:
                schema:
                    type: array
                    items:
                        type: object
      '404':
        $ref: '#/components/responses/404'
    """
    return await _get_bucket(request, S3BucketPermissionsContext(request))


@routes.get('/volumes/{volume_id}/buckets/{id}/opener')
@action('heaserver-buckets-bucket-open-content', rel=f'hea-opener hea-context-aws hea-default {Folder.get_mime_type()} hea-container',
        path='volumes/{volume_id}/buckets/{id}/awss3folders/root/items/')
@action(name='heaserver-buckets-bucket-open-as-zip',
        rel='hea-opener hea-downloader hea-default-downloader application/zip',
        path='volumes/{volume_id}/buckets/{id}/awss3folders/root/content')
async def get_bucket_opener(request: web.Request) -> web.Response:
    """
    Gets bucket opener choices.

    :param request: the HTTP Request.
    :return: A Response object with a status of Multiple Choices or Not Found.
    ---
    summary: Bucket opener choices
    tags:
        - heaserver-buckets
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
        - $ref: '#/components/parameters/id'
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    responses:
      '300':
        $ref: '#/components/responses/300'
      '404':
        $ref: '#/components/responses/404'
    """
    return await _bucket_opener(request)


@routes.get('/volumes/{volume_id}/buckets/{id}/creator')
@action('heaserver-buckets-bucket-create-folder', rel='hea-creator hea-default application/x.folder',
        path='volumes/{volume_id}/buckets/{id}/newfolder')
@action('heaserver-buckets-bucket-create-project', rel='hea-creator hea-default application/x.project',
        path='volumes/{volume_id}/buckets/{id}/newproject')
async def get_bucket_creator(request: web.Request) -> web.Response:
    """
    Gets bucket creator choices.

    :param request: the HTTP Request.
    :return: A Response object with a status of Multiple Choices or Not Found.
    ---
    summary: Bucket creator choices
    tags:
        - heaserver-buckets
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
    responses:
      '300':
        $ref: '#/components/responses/300'
      '404':
        $ref: '#/components/responses/404'
    """
    return await _bucket_opener(request)


@routes.get('/volumes/{volume_id}/buckets/{id}/newfolder')
@routes.get('/volumes/{volume_id}/buckets/{id}/newfolder/')
@action('heaserver-buckets-bucket-new-folder-form')
async def get_new_folder_form(request: web.Request) -> web.Response:
    """
    Gets form for creating a new folder within this bucket.

    :param request: the HTTP request. Required.
    :return: the current folder, with a template for creating a child folder or Not Found if the requested item does not
    exist.
    ---
    summary: A folder.
    tags:
        - heaserver-buckets
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
    responses:
      '200':
        $ref: '#/components/responses/200'
      '404':
        $ref: '#/components/responses/404'
    """
    return await _get_bucket(request)

@routes.get('/volumes/{volume_id}/buckets/{id}/newproject')
@routes.get('/volumes/{volume_id}/buckets/{id}/newproject/')
@action('heaserver-buckets-bucket-new-project-form')
async def get_new_project_form(request: web.Request) -> web.Response:
    """
    Gets form for creating a new project within this bucket.

    :param request: the HTTP request. Required.
    :return: the current project, with a template for creating a child project or Not Found if the requested item does not
    exist.
    ---
    summary: A folder.
    tags:
        - heaserver-buckets
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
    responses:
      '200':
        $ref: '#/components/responses/200'
      '404':
        $ref: '#/components/responses/404'
    """
    return await _get_bucket(request)


@routes.post('/volumes/{volume_id}/buckets/{bucket_id}/newfolder')
@routes.post('/volumes/{volume_id}/buckets/{bucket_id}/newfolder/')
async def post_new_folder(request: web.Request) -> web.Response:
    """
    Gets form for creating a new folder within this bucket.

    :param request: the HTTP request. Required.
    :return: the current folder, with a template for creating a child folder or Not Found if the requested item does not
    exist.
    ---
    summary: A folder.
    tags:
        - heaserver-buckets
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
    volume_id = request.match_info['volume_id']
    bucket_id = request.match_info['bucket_id']
    folder_url = await type_to_resource_url(request, AWSS3Folder)
    if folder_url is None:
        raise ValueError('No AWSS3Folder service registered')
    headers = {SUB: request.headers[SUB]} if SUB in request.headers else None
    resource_base = str(URL(folder_url) / volume_id / 'buckets' / bucket_id / 'awss3folders' / 'root' / 'newfolder')
    folder = await new_heaobject_from_type(request, type_=AWSS3Folder)
    try:
        id_ = await client.post(request.app, resource_base, data=folder, headers=headers)
        return await response.post(request, id_, resource_base)
    except ClientResponseError as e:
        return response.status_generic_error(status=e.status, body=e.message)
    except ClientError as e:
        return response.status_generic(status=500, body=str(e))

@routes.post('/volumes/{volume_id}/buckets/{bucket_id}/newproject')
@routes.post('/volumes/{volume_id}/buckets/{bucket_id}/newproject/')
async def post_new_project(request: web.Request) -> web.Response:
    """
    Gets form for creating a new project within this bucket.

    :param request: the HTTP request. Required.
    :return: the current project, with a template for creating a child project or Not Found if the requested item does not
    exist.
    ---
    summary: A project.
    tags:
        - heaserver-buckets
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
        description: A new project.
        required: true
        content:
            application/vnd.collection+json:
              schema:
                type: object
              examples:
                example:
                  summary: Project example
                  value: {
                    "template": {
                      "data": [
                      {
                        "name": "display_name",
                        "value": "Bob"
                      },
                      {
                        "name": "type",
                        "value": "heaobject.project.AWSS3Project"
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
                    "type": "heaobject.project.AWSS3Project"
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
    project_url = await type_to_resource_url(request, AWSS3Project)
    if project_url is None:
        raise ValueError('No AWSS3Project service registered')
    headers = {SUB: request.headers[SUB]} if SUB in request.headers else None
    resource_base = str(URL(project_url) / volume_id / 'buckets' / bucket_id / 'awss3projects')
    project = await new_heaobject_from_type(request, type_=AWSS3Project)
    try:
        id_ = await client.post(request.app, resource_base, data=project, headers=headers)
        return await response.post(request, id_, resource_base)
    except ClientResponseError as e:
        return response.status_generic_error(status=e.status, body=e.message)
    except ClientError as e:
        return response.status_generic(status=500, body=str(e))


@routes.get('/volumes/{volume_id}/buckets')
@routes.get('/volumes/{volume_id}/buckets/')
@action('heaserver-buckets-bucket-get-open-choices', rel='hea-opener-choices hea-context-menu hea-downloader',
        path='volumes/{volume_id}/buckets/{id}/opener')
@action(name='heaserver-buckets-bucket-get-properties', rel='hea-properties hea-context-menu')
@action(name='heaserver-buckets-bucket-get-create-choices', rel='hea-creator-choices hea-context-menu',
        path='volumes/{volume_id}/buckets/{id}/creator')
@action(name='heaserver-buckets-bucket-get-trash', rel='hea-trash hea-context-menu', path='volumes/{volume_id}/awss3trash')
@action(name='heaserver-buckets-bucket-get-self', rel='self hea-self-container', path='volumes/{volume_id}/buckets/{id}')
@action(name='heaserver-buckets-bucket-get-uploader', rel='hea-uploader', path='volumes/{volume_id}/buckets/{id}/awss3folders/root/uploader')
@action(name='heaserver-buckets-bucket-get-delete-preflight-url', rel='hea-delete-preflight',
        path='preflights/buckets/delete')
async def get_all_buckets(request: web.Request) -> web.Response:
    """
    Gets all buckets.
    :param request: the HTTP request.
    :return: all buckets.
    ---
    summary: get all buckets for a hea-volume associate with account.
    tags:
        - heaserver-buckets
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
        description: Expected response to a valid request.
        content:
            application/json:
                schema:
                    type: array
                    items:
                        type: object
            application/vnd.collection+json:
                schema:
                    type: array
                    items:
                        type: object
            application/vnd.wstl+json:
                schema:
                    type: array
                    items:
                        type: object
      '404':
        $ref: '#/components/responses/404'
    """
    sub = request.headers.get(SUB, NONE_USER)
    volume_id = request.match_info.get("volume_id", None)
    if not volume_id:
        return web.HTTPBadRequest(body="volume_id is required")
    loop = asyncio.get_running_loop()
    cache_key = (sub, volume_id, None, 'actual')
    cache_value = request.app[HEA_CACHE].get(cache_key)
    context = S3BucketPermissionsContext(request)
    if cache_value is not None:
        bucket_dict_list: Sequence[DesktopObjectDict] = cache_value[0]
        perms: Sequence[Sequence[Permission]] =  cache_value[1]
        attribute_perms: Sequence[dict[str, Sequence[Permission]]] = cache_value[2]
    else:
        async with DesktopObjectActionLifecycle(request=request,
                                                    code='hea-get',
                                                    description=f'Getting all buckets',
                                                    activity_cb=publish_desktop_object) as activity:
            try:
                credentials = await request.app[HEA_DB].get_credentials_from_volume(request, volume_id)
            except ValueError:
                return web.HTTPBadRequest(body=f'No volume with id {volume_id} exists')
            async with aws.S3ClientContext(request=request, credentials=credentials) as s3_client:
                try:
                    resp = await loop.run_in_executor(None, s3_client.list_buckets)
                    bucket_coros: list[asyncio.Task[tuple[AWSBucket, dict[str, list[Permission]]]]] = []
                    access_checks = [asyncio.create_task(asyncio.to_thread(_check_bucket_access, bucket["Name"], s3_client)) for bucket in resp['Buckets']]
                    for i, bucket in enumerate(resp['Buckets']):
                        # filter out inaccessible buckets
                        if not await access_checks[i]:
                            continue

                        bucket_coro = __get_bucket(request, volume_id, s3_client, request.app[HEA_CACHE],
                                                   context,
                                                   bucket_name=bucket["Name"],
                                                   creation_date=bucket['CreationDate'],
                                                   sub=request.headers.get(SUB, NONE_USER),
                                                   credentials=credentials)
                        if bucket_coro is not None:
                            bucket_coros.append(asyncio.create_task(bucket_coro))

                    buck_list = await asyncio.gather(*bucket_coros)
                    activity.new_object_uri = f'volumes/{volume_id}/buckets/'
                    activity.new_object_type_name = AWSBucket.get_type_name()
                    activity.new_volume_id = volume_id
                except BotoClientError as e:
                    activity.status = Status.FAILED
                    return awsservicelib.handle_client_error(e)
                else:
                    perms, attribute_perms, bucket_dict_list = \
                        zip(*((buck.shares[0].permissions, attr_perms, buck.to_dict())
                              for buck, attr_perms in buck_list))
                    request.app[HEA_CACHE][cache_key] = (bucket_dict_list, perms, attribute_perms)
                    for buck_dict in bucket_dict_list:
                        request.app[HEA_CACHE][(sub, volume_id, buck_dict['id'], 'head')] = buck_dict['id']
                        request.app[HEA_CACHE][(sub, volume_id, buck_dict['id'], 'actual')] = (buck_dict, perms, attribute_perms)
    return await response.get_all(request, bucket_dict_list,
                                  permissions=perms,
                                  attribute_permissions=attribute_perms)


@routes.get('/volumes/{volume_id}/bucketitems')
@routes.get('/volumes/{volume_id}/bucketitems/')
@action(name='heaserver-buckets-item-get-actual', rel='hea-actual hea-actual-container', path='{+actual_object_uri}')
@action(name='heaserver-buckets-item-get-volume', rel='hea-volume', path='volumes/{volume_id}')
async def get_all_bucketitems(request: web.Request) -> web.Response:
    """
    Gets all buckets.
    :param request: the HTTP request.
    :return: all buckets.
    ---
    summary: get all bucket items for a hea-volume associate with account.
    tags:
        - heaserver-buckets
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
    responses:
      '200':
        description: Expected response to a valid request.
        content:
            application/json:
                schema:
                    type: array
                    items:
                        type: object
            application/vnd.collection+json:
                schema:
                    type: array
                    items:
                        type: object
            application/vnd.wstl+json:
                schema:
                    type: array
                    items:
                        type: object
      '404':
        $ref: '#/components/responses/404'
    """
    volume_id = request.match_info["volume_id"]
    sub = request.headers.get(SUB, NONE_USER)

    async with DesktopObjectActionLifecycle(request=request,
                                                code='hea-get',
                                                description=f'Getting all buckets',
                                                activity_cb=publish_desktop_object) as activity:
        cache_key = (sub, volume_id, None, 'items')
        cached_value = request.app[HEA_CACHE].get(cache_key)
        if cached_value is not None:
            result_dict: Sequence[DesktopObjectDict] = cached_value[0]
            permissions: Sequence[Sequence[Permission]] = cached_value[1]
            attribute_permissions: Sequence[dict[str, Sequence[Permission]]] = cached_value[2]
        else:
            async with aws.S3ClientContext(request=request, volume_id=volume_id) as s3_client:
                try:
                    resp = await asyncio.get_running_loop().run_in_executor(None, s3_client.list_buckets)
                    bucket_url = URL('volumes') / volume_id / 'buckets'
                    bucket_type = AWSBucket.get_type_name()
                    context = ViewerPermissionContext(sub)
                    async def head_and_bucket_gen() -> AsyncIterator[BucketTypeDef]:
                        has_access = await asyncio.gather(*(asyncio.to_thread(_check_bucket_access, bucket['Name'], s3_client) for bucket in resp['Buckets']))
                        for bucket, access in zip(resp['Buckets'], has_access):
                            if access:
                                yield bucket
                    async def bucket_item_gen() -> AsyncIterator[tuple[asyncio.Task[dict[str, list[Permission]]], AWSS3BucketItem]]:
                        async for bucket in head_and_bucket_gen():
                            bucket_name = bucket['Name']
                            bucket_item: AWSS3BucketItem = AWSS3BucketItem()
                            bucket_item.bucket_id = bucket_name
                            creation_date = bucket['CreationDate']
                            bucket_item.modified = creation_date
                            bucket_item.created = creation_date
                            bucket_item.actual_object_type_name = bucket_type
                            bucket_item.actual_object_id = bucket_name
                            bucket_item.actual_object_uri = str(bucket_url / bucket_name)
                            bucket_item.source = AWS_S3
                            bucket_item.source_detail = AWS_S3
                            async def calc_perms(bucket_item: AWSS3BucketItem) -> dict[str, list[Permission]]:
                                share = await bucket_item.get_permissions_as_share(context)
                                bucket_item.add_share(share)
                                return await bucket_item.get_all_attribute_permissions(context)
                            yield asyncio.create_task(calc_perms(bucket_item)), bucket_item
                    permissions, result_dict, perm_tasks = \
                        zip(*((bucket_item.shares[0].permissions, bucket_item.to_dict(), perm_task)
                              for perm_task, bucket_item in [
                                  (perm_task, bucket_item) async for perm_task, bucket_item in bucket_item_gen()
                              ]))
                    attribute_permissions = await asyncio.gather(*perm_tasks)
                    activity.new_object_uri = f'volumes/{volume_id}/bucketitems/'
                    activity.new_object_type_name = AWSS3BucketItem.get_type_name()
                    activity.new_volume_id = volume_id

                    # Update cache and response
                    request.app[HEA_CACHE][cache_key] = (result_dict, permissions, attribute_permissions)

                    for buck in result_dict:
                        request.app[HEA_CACHE][(sub, volume_id, buck['id'], 'head')] = buck['id']
                except BotoClientError as e:
                    activity.status = Status.FAILED
                    return awsservicelib.handle_client_error(e)

        return await response.get_all(request, result_dict, permissions=permissions,
                                      attribute_permissions=attribute_permissions)


@routes.get('/volumes/{volume_id}/bucketcollaborators')
@routes.get('/volumes/{volume_id}/bucketcollaborators/')
@action(name='heaserver-buckets-item-get-actual', rel='hea-actual hea-actual-container', path='{+actual_object_uri}')
@action(name='heaserver-buckets-item-get-volume', rel='hea-volume', path='volumes/{volume_id}')
async def get_all_bucket_collaborators(request: web.Request) -> web.Response:
    """
    Gets all bucket collaborators for the account represented by the volume in the request URL.

    :param request: the HTTP request.
    :return: all bucket collaborators.
    ---
    summary: get all bucket collaborators for the account represented by the volume in the request URL.
    tags:
        - heaserver-buckets
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
    responses:
      '200':
        description: Expected response to a valid request.
        content:
            application/json:
                schema:
                    type: array
                    items:
                        type: object
            application/vnd.collection+json:
                schema:
                    type: array
                    items:
                        type: object
            application/vnd.wstl+json:
                schema:
                    type: array
                    items:
                        type: object
      '404':
        $ref: '#/components/responses/404'
    """
    volume_id = request.match_info.get("volume_id", None)
    if not volume_id:
        return web.HTTPBadRequest(body="volume_id is required")
    loop = asyncio.get_running_loop()
    async with DesktopObjectActionLifecycle(request=request,
                                                code='hea-get',
                                                description=f'Getting all bucket collaborators',
                                                activity_cb=publish_desktop_object) as activity:
        try:
            credentials = await request.app[HEA_DB].get_credentials_from_volume(request, volume_id)
        except ValueError:
            return web.HTTPBadRequest(body=f'No volume with id {volume_id} exists')
        async with aws.S3ClientContext(request=request, credentials=credentials) as s3_client:
            try:
                resp = await loop.run_in_executor(None, s3_client.list_buckets)
                bucket_coros: list[asyncio.Task[tuple[BucketCollaborators, dict[str, list[Permission]]]]] = []
                access_checks = [asyncio.create_task(asyncio.to_thread(_check_bucket_access, bucket["Name"], s3_client)) for bucket in resp['Buckets']]
                for i, bucket in enumerate(resp['Buckets']):
                    # filter out inaccessible buckets
                    if not await access_checks[i]:
                        continue

                    bucket_coro = __get_bucket_collaborators(request, volume_id, s3_client, request.app[HEA_CACHE],
                                                bucket_name=bucket["Name"],
                                                creation_date=bucket['CreationDate'],
                                                credentials=credentials)
                    if bucket_coro is not None:
                        bucket_coros.append(asyncio.create_task(bucket_coro))

                buck_list = await asyncio.gather(*bucket_coros)
                activity.new_object_uri = f'volumes/{volume_id}/buckets/'
                activity.new_object_type_name = AWSBucket.get_type_name()
                activity.new_volume_id = volume_id
            except BotoClientError as e:
                activity.status = Status.FAILED
                return awsservicelib.handle_client_error(e)
            else:
                perms, attribute_perms, bucket_dict_list = \
                    zip(*((buck.shares[0].permissions, attr_perms, buck.to_dict())
                            for buck, attr_perms in buck_list))
    return await response.get_all(request, bucket_dict_list,
                                  permissions=perms,
                                  attribute_permissions=attribute_perms)


@routes.get('/volumes/{volume_id}/bucketcollaborators/{id}')
@action(name='heaserver-buckets-item-get-actual', rel='hea-actual hea-actual-container', path='{+actual_object_uri}')
@action(name='heaserver-buckets-item-get-volume', rel='hea-volume', path='volumes/{volume_id}')
async def get_bucket_collaborators(request: web.Request) -> web.Response:
    """
    Gets all buckets.
    :param request: the HTTP request.
    :return: all buckets.
    ---
    summary: get bucket collaborators for a hea-volume associate with bucket.
    tags:
        - heaserver-buckets
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
    responses:
      '200':
        description: Expected response to a valid request.
        content:
            application/json:
                schema:
                    type: array
                    items:
                        type: object
            application/vnd.collection+json:
                schema:
                    type: array
                    items:
                        type: object
            application/vnd.wstl+json:
                schema:
                    type: array
                    items:
                        type: object
      '404':
        $ref: '#/components/responses/404'
    """
    volume_id = request.match_info["volume_id"]
    bucket_id = request.match_info["id"]
    loop = asyncio.get_running_loop()
    async with DesktopObjectActionLifecycle(request=request,
                                                code='hea-get',
                                                description=f'Getting bucket collaborators',
                                                activity_cb=publish_desktop_object) as activity:
        try:
            credentials = await request.app[HEA_DB].get_credentials_from_volume(request, volume_id)
        except ValueError:
            return web.HTTPBadRequest(body=f'No volume with id {volume_id} exists')
        async with aws.S3ClientContext(request=request, credentials=credentials) as s3_client:
            try:
                resp = await loop.run_in_executor(None, s3_client.list_buckets)
                access_checks = next((asyncio.create_task(asyncio.to_thread(_check_bucket_access, bucket["Name"], s3_client)) for bucket in resp['Buckets'] if bucket["Name"] == bucket_id), None)
                for bucket in resp['Buckets']:
                    if bucket["Name"] != bucket_id and (not access_checks or not await access_checks):
                        continue

                    buck = await __get_bucket_collaborators(request, volume_id, s3_client, request.app[HEA_CACHE],
                                                             bucket_name=bucket["Name"],
                                                             creation_date=bucket['CreationDate'],
                                                             credentials=credentials)
                    activity.new_object_uri = f'volumes/{volume_id}/buckets/{bucket_id}'
                    activity.new_object_type_name = AWSBucket.get_type_name()
                    activity.new_volume_id = volume_id
                    perms, attribute_perms, bucket_dict = buck[0].shares[0].permissions, buck[1], to_dict(buck[0])
                    return await response.get(request, bucket_dict,
                                            permissions=perms, attribute_permissions=attribute_perms)
                else:
                    return await response.get(request, None)
            except BotoClientError as e:
                raise awsservicelib.handle_client_error(e)




@routes.route('OPTIONS', '/volumes/{volume_id}/buckets/{id}')
async def get_bucket_options(request: web.Request) -> web.Response:
    """
    ---
    summary: Allowed HTTP methods.
    tags:
        - heaserver-buckets
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
    return await response.get_options(request, ['GET', 'DELETE', 'HEAD', 'OPTIONS', 'PUT'])


@routes.route('OPTIONS', '/volumes/{volume_id}/buckets')
@routes.route('OPTIONS', '/volumes/{volume_id}/buckets/')
async def get_buckets_options(request: web.Request) -> web.Response:
    """
    ---
    summary: Allowed HTTP methods.
    tags:
        - heaserver-buckets
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
    return await response.get_options(request, ['GET', 'HEAD', 'POST', 'OPTIONS'])


@routes.route('OPTIONS', '/volumes/{volume_id}/bucketitems')
@routes.route('OPTIONS', '/volumes/{volume_id}/bucketitems/')
async def get_bucketitems_options(request: web.Request) -> web.Response:
    """
    ---
    summary: Allowed HTTP methods.
    tags:
        - heaserver-buckets
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
    return await response.get_options(request, ['GET', 'HEAD', 'OPTIONS'])


@routes.get('/ping')
async def ping(request: web.Request) -> web.Response:
    """
    For testing whether the service is up.

    :param request: the HTTP request.
    :return: Always returns status code 200.
    """
    return response.status_ok(None)


@routes.post('/volumes/{volume_id}/buckets')
@routes.post('/volumes/{volume_id}/buckets/')
async def post_bucket(request: web.Request) -> web.Response:
    """
    Posts the provided bucket.
    :param request: the HTTP request.
    :return: a Response object with a status of Created and the object's URI in the
    ---
    summary: Bucket Creation
    tags:
        - heaserver-buckets
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
    requestBody:
      description: Attributes of new Bucket.
      required: true
      content:
        application/vnd.collection+json:
          schema:
            type: object
          examples:
            example:
              summary: Bucket example
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
                    "value": "hci-test-bucket"
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
                    "value": "hci-test-bucket"
                  },
                  {
                    "name": "owner",
                    "value": "system|none"
                  },
                  {
                    "name": "shared_with",
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
                    "name": "encrypted",
                    "value": true
                  },
                  {
                    "name": "versioned",
                    "value": false
                  },
                  {
                    "name": "locked",
                    "value": false
                  },
                  {
                    "name": "tags",
                    "value": []
                  },
                  {
                    "name": "region",
                    "value": us-west-2
                  },
                  {
                    "name": "permission_policy",
                    "value": null
                  },
                  {
                    "name": "type",
                    "value": "heaobject.bucket.AWSBucket"
                  }]
                }
              }
        application/json:
          schema:
            type: object
          examples:
            example:
              summary: Bucket example
              value: {
                "created": null,
                "derived_by": null,
                "derived_from": [],
                "description": "This is a description",
                "display_name": "hci-test-bucket",
                "invited": [],
                "modified": null,
                "name": "hci-test-bucket",
                "owner": "system|none",
                "shared_with": [],
                "source": null,
                "type": "heaobject.bucket.AWSBucket",
                "version": null,
                encrypted: true,
                versioned: false,
                locked: false,
                tags: [],
                region: "us-west-2",
                permission_policy: null
              }
    responses:
      '201':
        $ref: '#/components/responses/201'
      '400':
        $ref: '#/components/responses/400'
      '404':
        $ref: '#/components/responses/404'
    """
    return await _post_bucket(request=request)


@routes.put('/volumes/{volume_id}/buckets/{id}')
async def put_bucket(request: web.Request) -> web.Response:
    """
    Updates the provided bucket. Only the tags may be updated.

    :param request: the HTTP request.
    :return: a Response object with a status of No Content, or Not Found if no
    bucket exists with that name, or Bad Request if there is a problem with the
    request.
    ---
    summary: Bucket update.
    tags:
        - heaserver-buckets
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
        - $ref: '#/components/parameters/id'
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    requestBody:
      description: Attributes of the bucket.
      required: true
      content:
        application/vnd.collection+json:
          schema:
            type: object
          examples:
            example:
              summary: Bucket example
              value: {
                "template": {
                  "data": [
                  {
                    "name": "id",
                    "value": "hci-test-bucket"
                  },
                  {
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
                    "value": "hci-test-bucket"
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
                    "value": "hci-test-bucket"
                  },
                  {
                    "name": "owner",
                    "value": "system|none"
                  },
                  {
                    "name": "shared_with",
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
                    "name": "encrypted",
                    "value": true
                  },
                  {
                    "name": "versioned",
                    "value": false
                  },
                  {
                    "name": "locked",
                    "value": false
                  },
                  {
                    "name": "tags",
                    "value": []
                  },
                  {
                    "name": "region",
                    "value": us-west-2
                  },
                  {
                    "name": "permission_policy",
                    "value": null
                  },
                  {
                    "name": "type",
                    "value": "heaobject.bucket.AWSBucket"
                  }]
                }
              }
        application/json:
          schema:
            type: object
          examples:
            example:
              summary: Bucket example
              value: {
                "created": null,
                "derived_by": null,
                "derived_from": [],
                "description": "This is a description",
                "display_name": "hci-test-bucket",
                "invited": [],
                "modified": null,
                "name": "hci-test-bucket",
                "owner": "system|none",
                "shared_with": [],
                "source": null,
                "type": "heaobject.bucket.AWSBucket",
                "version": null,
                encrypted: true,
                versioned: false,
                locked: false,
                tags: [],
                region: "us-west-2",
                permission_policy: null
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
    bucket_name = request.match_info['id']
    credentials = await request.app[HEA_DB].get_credentials_from_volume(request, volume_id)
    async with aws.S3ClientContext(request, credentials=credentials) as s3_client:
        loop = asyncio.get_running_loop()
        try:
            await loop.run_in_executor(None, partial(s3_client.head_bucket, Bucket=bucket_name))
        except BotoClientError as e:
            return awsservicelib.handle_client_error(e);

        try:
            b = await new_heaobject_from_type(request=request, type_=AWSBucket)
            if not b:
                return web.HTTPBadRequest(body=f"Put body is not a {AWSBucket.get_type_name()}")
            if not b.name:
                return web.HTTPBadRequest(body="Bucket name is required in the body")
            if b.name != bucket_name:
                return web.HTTPBadRequest(body='Bucket name in URL does not match bucket in body')
        except DeserializeException as e:
            return web.HTTPBadRequest(body=str(e))

        async with DesktopObjectActionLifecycle(request=request,
                                                    code='hea-update',
                                                    description=f'Updating {bucket_name}',
                                                    activity_cb=publish_desktop_object) as activity:
            activity.old_object_id = bucket_name
            activity.old_object_uri = f'volumes/{volume_id}/buckets/{bucket_name}'
            activity.old_object_type_name = AWSBucket.get_type_name()
            activity.old_volume_id = volume_id
            # We only support changing the bucket tags and collaborators.
            try:
                await _put_bucket_tags(s3_client, request, volume_id, bucket_name, b.tags)
            except BotoClientError as e:
                activity.status = Status.FAILED
                return awsservicelib.handle_client_error(e)
            activity.new_object_id = bucket_name
            activity.new_object_uri = f'volumes/{volume_id}/buckets/{bucket_name}'
            activity.new_object_type_name = AWSBucket.get_type_name()
            activity.new_volume_id = volume_id
            request.app[HEA_CACHE].pop((sub, volume_id, None, 'items'), None)
            request.app[HEA_CACHE].pop((sub, volume_id, None, 'actual'), None)
            request.app[HEA_CACHE].pop((sub, volume_id, bucket_name, 'head'), None)
            request.app[HEA_CACHE].pop((sub, volume_id, bucket_name, 'actual'), None)

            elevated_credentials = await request.app[HEA_DB].elevate_privileges(request, credentials)
            async with aws.IAMClientContext(request=request, credentials=elevated_credentials) as iam_client:
                old_collaborator_id_to_collaborator = {old_collaborator.collaborator_id: old_collaborator for old_collaborator in await _get_collaborators(b.name, iam_client)}
                new_collaborator_ids = b.collaborator_ids
                coros: list[Coroutine[Any, Any, None]] = []
                for collaborator_id in set(old_collaborator_id_to_collaborator.keys()).difference(new_collaborator_ids):
                    coros.append(_delete_collaborator(request, b.name, old_collaborator_id_to_collaborator[collaborator_id], s3_client, iam_client))
                await asyncio.gather(*coros)
                coros.clear()
                for collaborator_id in set(new_collaborator_ids).difference(old_collaborator_id_to_collaborator.keys()):
                    coros.append(_put_collaborator(request, volume_id, b.name, collaborator_id, iam_client))
                await asyncio.gather(*coros)
            return await response.put(True)




@routes.delete('/volumes/{volume_id}/buckets/{id}')
async def delete_bucket(request: web.Request) -> web.Response:
    """
    Deletes the bucket with the specified id. The bucket must be empty. If the bucket is versioned, then there can be
    no objects with delete markers in the bucket either. Setting the deletecontents query parameter to y, yes, or true
    will delete the bucket's contents, including any deleted versions, and then delete the bucket.

    :param request: the HTTP request.
    :return: No Content or Not Found.
    ---
    summary: A specific bucket.
    tags:
        - heaserver-buckets
    parameters:
        - name: id
          in: path
          required: true
          description: The id of the bucket to delete.
          schema:
            type: string
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
        - name: deletecontents
          in: query
          description: flag whether to delete the bucket's contents before deleting the bucket.
          schema:
            type: boolean
          examples:
            example:
              summary: The default value
              value: false
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    responses:
      '200':
        description: Expected response to a valid request.
        content:
            application/json:
                schema:
                    type: array
                    items:
                        type: object
            application/vnd.collection+json:
                schema:
                    type: array
                    items:
                        type: object
            application/vnd.wstl+json:
                schema:
                    type: array
                    items:
                        type: object
      '404':
        $ref: '#/components/responses/404'
    """
    sub = request.headers.get(SUB, NONE_USER)
    volume_id = request.match_info.get("volume_id", None)
    bucket_id = request.match_info.get("id", None)
    delete_contents = parse_bool(request.query.get('deletecontents', 'no'))
    if not volume_id:
        return web.HTTPBadRequest(body="volume_id is required")
    if not bucket_id:
        return web.HTTPBadRequest(body="bucket_id is required")
    loop = asyncio.get_running_loop()
    async with DesktopObjectActionLifecycle(request=request,
                                                code='hea-delete',
                                                description=f'Deleting {bucket_id}',
                                                activity_cb=publish_desktop_object) as activity:
        activity.old_object_id = bucket_id
        activity.old_object_uri = f'volumes/{volume_id}/buckets/{bucket_id}'
        activity.old_object_type_name = AWSBucket.get_type_name()
        activity.old_volume_id = volume_id
        try:
            credentials = await request.app[HEA_DB].get_credentials_from_volume(request, volume_id)
        except ValueError as e:
            return web.HTTPBadRequest(body=f'No volume with id {volume_id} exists')
        async with aws.S3ClientContext(request=request, credentials=credentials) as s3_client:
            try:
                if delete_contents:
                    object_url = await type_to_resource_url(request, AWSS3Item)
                    await client.delete(request.app, URL(object_url) / volume_id / 'buckets' / bucket_id / 'awss3folders/root/items?delete_versions=y', headers={SUB: sub})
                await loop.run_in_executor(None, partial(s3_client.delete_bucket, Bucket=bucket_id))
                request.app[HEA_CACHE].pop((sub, volume_id, bucket_id, 'head'), None)
                request.app[HEA_CACHE].pop((sub, volume_id, None, 'items'), None)
                request.app[HEA_CACHE].pop((sub, volume_id, None, 'actual'), None)
                request.app[HEA_CACHE].pop((sub, volume_id, bucket_id, 'actual'), None)
                return web.HTTPNoContent()
            except BotoClientError as e:
                activity.status = Status.FAILED
                if aws.client_error_code(e) == aws.CLIENT_ERROR_BUCKET_NOT_EMPTY:
                    raise response.status_bad_request(body=f'Bucket {bucket_id} is not empty. You must permanently delete all versions of all objects in the bucket, including objects in the Trash, before deleting it.')
                return awsservicelib.handle_client_error(e)
        elevated_credentials = await request.app[HEA_DB].elevate_privileges(request, credentials)
        async with aws.IAMClientContext(request=request, credentials=elevated_credentials) as iam_client:
            coros: list[Coroutine[Any, Any, None]] = []
            for retval in await _get_collaborators(request, bucket_id, iam_client):
                coros.append(_delete_collaborator(request, bucket_id, retval, s3_client, iam_client))
            await asyncio.gather(*coros)


def start_service(config: Configuration) -> None:
    start(package_name='heaserver-buckets', db=aws.S3Manager,
          wstl_builder_factory=builder_factory(__package__),
          cleanup_ctx=[publisher_cleanup_context_factory(config)],
          config=config)


async def _get_bucket(request: web.Request, permission_context: PermissionContext | None = None) -> web.Response:
    """
    List a single bucket's attributes

    :param request: the aiohttp Request (required).
    :return:  return the single bucket object requested or HTTP Error Response
    """
    logger = logging.getLogger(__name__)
    sub = request.headers.get(SUB, NONE_USER)
    try:
        volume_id = request.match_info['volume_id']
        bucket_name = request.match_info.get('id')
        if bucket_name is None:
            bucket_name = request.match_info['bucket_name']
    except KeyError as e:
        raise ValueError(str(e))

    async with DesktopObjectActionLifecycle(request=request,
                                                code='hea-get',
                                                description=f'Getting {bucket_name}',
                                                activity_cb=publish_desktop_object) as activity:
        cache_key = (sub, volume_id, bucket_name, 'actual')
        cache_value = request.app[HEA_CACHE].get(cache_key)
        include_data = parse_bool(request.query.get('data') or 'true')
        if permission_context and cache_value:
            bucket_dict, perms, attribute_perms = cache_value
            return await response.get(request=request, data=bucket_dict,
                                      permissions=perms, attribute_permissions=attribute_perms,
                                      include_data=include_data)
        else:
            try:
                credentials = await request.app[HEA_DB].get_credentials_from_volume(request, volume_id)
            except ValueError:
                raise web.HTTPBadRequest(body=f'No volume with id {volume_id} exists')

            async with aws.S3ClientContext(request=request, credentials=credentials) as s3_client:
                if include_data:
                    try:
                        bucket_result, attribute_perms = await __get_bucket(request, volume_id, s3_client, request.app[HEA_CACHE],
                                                        permission_context,
                                                        bucket_name=bucket_name, bucket_id=bucket_name,
                                                        sub=request.headers.get(SUB, NONE_USER),
                                                        credentials=credentials)
                        if bucket_result is not None:
                            activity.new_object_id = bucket_name
                            activity.new_object_uri = f'volumes/{volume_id}/buckets/{bucket_name}'
                            activity.new_object_type_name = AWSBucket.get_type_name()
                            activity.new_volume_id = volume_id
                            perms = bucket_result.shares[0].permissions if bucket_result.shares else None
                            bucket_dict = bucket_result.to_dict()
                            if permission_context:
                                request.app[HEA_CACHE][(sub, volume_id, bucket_dict['id'], 'actual')] = (bucket_dict, perms, attribute_perms)
                            return await response.get(request=request, data=bucket_dict,
                                                    permissions=perms,
                                                    attribute_permissions=attribute_perms, include_data=True)
                        activity.status = Status.FAILED
                        return await response.get(request, data=None)
                    except BotoClientError as e:
                        activity.status = Status.FAILED
                        return awsservicelib.http_error_message(awsservicelib.handle_client_error(e), bucket_name, None)
                else:
                    loop = asyncio.get_running_loop()
                    try:
                        await loop.run_in_executor(None, partial(s3_client.head_bucket, Bucket=bucket_name))
                        bucket_dict_: DesktopObjectDict | None = {'id': bucket_name, 'type': AWSBucket.get_type_name()}
                    except BotoClientError as e:
                        code, _ = aws.client_error_status(e)
                        if code == 404:
                            bucket_dict_ = None
                        else:
                            return awsservicelib.http_error_message(awsservicelib.handle_client_error(e), bucket_name, None)
                    return await response.get(request=request, data=bucket_dict_, include_data=False)


async def __get_bucket(request: web.Request, volume_id: str, s3_client: S3Client, cache,
                       context: PermissionContext | None,
                       bucket_name: str | None = None, bucket_id: str | None = None,
                       creation_date: datetime | None = None,
                       sub: str | None = None, credentials: AWSCredentials | None = None) -> tuple[AWSBucket, dict[str, list[Permission]]]:
    """
    Creates and returns an AWSBucket object and the object's attribute-level permissions.

    :param request: the HTTP request.
    :param volume_id: the volume id
    :param s3_client:  the boto3 client.
    :param cache: the cache object.
    :param context: the permission context.
    :param bucket_name: str the bucket name (optional)
    :param bucket_id: str the bucket id (optional)
    :param creation_date: str the bucket creation date (optional)
    :param sub: str the user's sub (optional)
    :param credentials: the AWS credentials (optional). Used to get collaborators who have access to the bucket.
    :return: Returns either the AWSBucket or None for Not Found or Forbidden, else raises ClientError
    """
    logger = logging.getLogger(__name__)
    loop = asyncio.get_running_loop()
    if not volume_id or (not bucket_id and not bucket_name):
        raise ValueError("volume_id is required and either bucket_name or bucket_id")

    b: AWSBucket = AWSBucket()
    b.name = bucket_id if bucket_id else bucket_name
    b.id = bucket_id if bucket_id else bucket_name
    if bucket_id is not None:
        b.display_name = bucket_id
    elif bucket_name is not None:
        b.display_name = bucket_name
    async_bucket_methods: list[Coroutine[Any, Any, None]] = []
    b.bucket_id = b.name
    b.source = AWS_S3
    b.source_detail = AWS_S3
    b.arn = f'arn:aws:s3::{b.id}'
    b.owner = AWS_USER
    attr_perms: dict[str, list[Permission]] = {}

    if creation_date:
        b.created = creation_date
    elif cached_value := cache.get((sub, volume_id, None, 'items')):
        bucket, _, _ = cached_value
        b.created = next((bucket_['created'] for bucket_ in bucket if bucket_['name'] == b.name), None)
    else:
        async def _get_creation_date(b: AWSBucket):
            logger.debug('Getting creation date of bucket %s', b.name)
            try:
                creation_date = next((bucket_['CreationDate'] for bucket_ in (await loop.run_in_executor(None, s3_client.list_buckets))['Buckets'] if bucket_['Name'] == b.name), None)
                b.created = creation_date
            except BotoClientError as ce:
                logger.exception('Error getting the creation date of bucket %s', b.name)
                raise ce

        async_bucket_methods.append(_get_creation_date(b))

    if context:
        async def _get_perms(b: AWSBucket):
            nonlocal attr_perms
            share = await b.get_permissions_as_share(context)
            b.add_user_share(share)
            attr_perms = await b.get_all_attribute_permissions(context)
        async_bucket_methods.append(_get_perms(b))

    async def _get_version_status(b: AWSBucket):
        logger.debug('Getting version status of bucket %s', b.name)
        try:
            assert b.name is not None, 'b.name cannot be None'
            bucket_versioning = await loop.run_in_executor(None,
                                                            partial(s3_client.get_bucket_versioning, Bucket=b.name))
            logger.debug('bucket_versioning=%s', bucket_versioning)
            if 'Status' in bucket_versioning:
                b.versioned = bucket_versioning['Status'] == 'Enabled'
            else:
                b.versioned = False
        except BotoClientError as ce:
            logger.exception('Error getting the version status of bucket %s', b.name)
            raise ce

    async_bucket_methods.append(_get_version_status(b))

    async def _get_region(b: AWSBucket):
        logger.debug('Getting region of bucket %s', b.name)
        try:
            assert b.name is not None, 'b.name cannot be None'
            loc = await loop.run_in_executor(None, partial(s3_client.get_bucket_location, Bucket=b.name))
            b.region = loc['LocationConstraint'] or 'us-east-1'
        except BotoClientError as ce:
            logging.exception('Error getting the region of bucket %s', b.name)
            raise ce
        logger.debug('Got region of bucket %s successfully', b.name)

    async_bucket_methods.append(_get_region(b))

    # todo how to find partition dynamically. The format is arn:PARTITION:s3:::NAME-OF-YOUR-BUCKET
    # b.arn = "arn:"+"aws:"+":s3:::"

    async def _get_tags(b: AWSBucket):
        logger.debug('Getting tags of bucket %s', b.name)
        try:
            assert b.name is not None, 'b.name cannot be None'
            tagging = await loop.run_in_executor(None, partial(s3_client.get_bucket_tagging, Bucket=b.name))
            b.tags = _from_aws_tags(aws_tags=tagging['TagSet'])
        except BotoClientError as ce:
            if ce.response['Error']['Code'] != 'NoSuchTagSet':
                logging.exception('Error getting the tags of bucket %s', b.name)
                raise ce
        logger.debug('Got tags of bucket %s successfully', b.name)

    async_bucket_methods.append(_get_tags(b))

    async def _get_encryption_status(b: AWSBucket):
        logger.debug('Getting encryption status of bucket %s', b.name)
        try:
            assert b.name is not None, 'b.name cannot be None'
            encrypt = await loop.run_in_executor(None, partial(s3_client.get_bucket_encryption, Bucket=b.name))
            rules: list = encrypt['ServerSideEncryptionConfiguration']['Rules']
            b.encrypted = len(rules) > 0
        except BotoClientError as e:
            if e.response['Error']['Code'] == 'ServerSideEncryptionConfigurationNotFoundError':
                b.encrypted = False
            else:
                logger.exception('Error getting the encryption status of bucket %s', b.name)
                raise e
        logger.debug('Got encryption status of bucket %s successfully', b.name)

    async_bucket_methods.append(_get_encryption_status(b))

    async def _get_collaborators_for_bucket(b: AWSBucket):
        assert b.name is not None, 'b.name cannot be None'
        elevated_credentials = await request.app[HEA_DB].elevate_privileges(request, credentials) if credentials is not None else None
        async with aws.IAMClientContext(request, credentials=elevated_credentials) as iam_client:
            b.collaborator_ids = [r.collaborator_id for r in await _get_collaborators(b.name, iam_client)]
    async_bucket_methods.append(_get_collaborators_for_bucket(b))

    async def _get_bucket_lock_status(b: AWSBucket):
        logger.debug('Getting bucket lock status of bucket %s', b.name)
        try:
            assert b.name is not None, 'b.name cannot be None'
            lock_config = await loop.run_in_executor(None, partial(s3_client.get_object_lock_configuration,
                                                                    Bucket=b.name))
            b.locked = lock_config['ObjectLockConfiguration']['ObjectLockEnabled'] == 'Enabled'
        except BotoClientError as e:
            if e.response['Error']['Code'] != 'ObjectLockConfigurationNotFoundError':
                logger.exception('Error getting the lock status of bucket %s', b.name)
                raise e
            b.locked = False
        logger.debug('Got bucket lock status of bucket %s successfully', b.name)

    async_bucket_methods.append(_get_bucket_lock_status(b))

    # todo need to lazy load this these metrics
    total_size = None
    obj_count = None
    mod_date = None
    # FIXME need to calculate this metric data in a separate call. Too slow
    # s3bucket = s3_resource.Bucket(b.name)
    # for obj in s3bucket.objects.all():
    #     total_size += obj.size
    #     obj_count += 1
    #     mod_date = obj.last_modified if mod_date is None or obj.last_modified > mod_date else mod_date
    b.size = total_size
    b.object_count = obj_count
    b.modified = mod_date
    await asyncio.gather(*async_bucket_methods)
    return b, attr_perms


async def __get_bucket_collaborators(request: web.Request, volume_id: str, s3_client: S3Client, cache,
                       bucket_name: str | None = None, bucket_id: str | None = None,
                       creation_date: datetime | None = None,
                       credentials: AWSCredentials | None = None) -> tuple[BucketCollaborators, dict[str, list[Permission]]]:
    """
    Creates and returns a BucketCollaborators object and the object's attribute-level permissions.

    :param request: the HTTP request.
    :param volume_id: the volume id
    :param s3_client:  the boto3 client.
    :param cache: the cache object.
    :param context: the permission context.
    :param bucket_name: str the bucket name (optional)
    :param bucket_id: str the bucket id (optional)
    :param creation_date: str the bucket creation date (optional)
    :param sub: str the user's sub (optional)
    :param credentials: the AWS credentials (optional). Used to get collaborators who have access to the bucket.
    :return: Returns either the BucketCollaborators or None for Not Found or Forbidden, else raises ClientError
    """
    logger = logging.getLogger(__name__)
    sub = request.headers.get(SUB, NONE_USER)
    loop = asyncio.get_running_loop()
    if not volume_id or (not bucket_id and not bucket_name):
        raise ValueError("volume_id is required and either bucket_name or bucket_id")

    b: BucketCollaborators = BucketCollaborators()
    b.name = bucket_id if bucket_id else bucket_name
    b.id = bucket_id if bucket_id else bucket_name
    if bucket_id is not None:
        b.display_name = bucket_id
    elif bucket_name is not None:
        b.display_name = bucket_name
    async_bucket_methods: list[Coroutine[Any, Any, None]] = []
    b.bucket_id = b.name
    b.source = AWS_S3
    b.source_detail = AWS_S3
    b.arn = f'arn:aws:s3::{b.id}'
    b.owner = AWS_USER
    attr_perms: dict[str, list[Permission]] = {}

    if creation_date:
        b.created = creation_date
    elif cached_value := cache.get((sub, volume_id, None, 'items')):
        bucket, _, _ = cached_value
        b.created = next((bucket_['created'] for bucket_ in bucket if bucket_['name'] == b.name), None)
    else:
        async def _get_creation_date(b: BucketCollaborators):
            logger.debug('Getting creation date of bucket %s', b.name)
            try:
                creation_date = next((bucket_['CreationDate'] for bucket_ in (await loop.run_in_executor(None, s3_client.list_buckets))['Buckets'] if bucket_['Name'] == b.name), None)
                b.created = creation_date
            except BotoClientError as ce:
                logger.exception('Error getting the creation date of bucket %s', b.name)
                raise ce

        async_bucket_methods.append(_get_creation_date(b))

    context = ViewerPermissionContext(sub=sub)
    async def _get_perms(b: BucketCollaborators):
        nonlocal attr_perms
        share = await b.get_permissions_as_share(context)
        b.add_user_share(share)
        attr_perms = await b.get_all_attribute_permissions(context)
    async_bucket_methods.append(_get_perms(b))

    async def _get_collaborators_for_bucket(b: BucketCollaborators):
        assert b.name is not None, 'b.name cannot be None'
        elevated_credentials = await request.app[HEA_DB].elevate_privileges(request, credentials) if credentials is not None else None
        async with aws.IAMClientContext(request, credentials=elevated_credentials) as iam_client:
            b.collaborator_ids = [r.collaborator_id for r in await _get_collaborators(b.name, iam_client)]
    async_bucket_methods.append(_get_collaborators_for_bucket(b))

    await asyncio.gather(*async_bucket_methods)
    return b, attr_perms


@dataclass
class _GetCollaboratorRetval:
    collaborator_id: str
    other_bucket_names: list[str]


async def _get_collaborators(bucket_name: str, iam_client: IAMClient) -> list[_GetCollaboratorRetval]:
    logger = logging.getLogger(__name__)
    logger.debug('Getting collaborators for bucket %s', bucket_name)
    try:
        assert bucket_name is not None, 'bucket_name cannot be None'
        return [_GetCollaboratorRetval(collaborator_id=policy_info.user_id, other_bucket_names=list(policy_info.bucket_names - set([bucket_name]))) \
                async for policy_info in _all_collaborator_policies_gen(iam_client) if bucket_name in policy_info.bucket_names]
    except BotoClientError as e:
        if e.response['Error']['Code'] != 'NoSuchBucketPolicy':
            logging.exception('Error getting collaborators for bucket %s', bucket_name)
            raise e
        return []



def _from_aws_tags(aws_tags: list[TagTypeDef]) -> list[Tag]:
    """
    :param aws_tags: Tags obtained from boto3 Tags api
    :return: List of HEA Tags
    """
    hea_tags = []
    for t in aws_tags:
        tag = Tag()
        tag.key = t['Key']
        tag.value = t['Value']
        hea_tags.append(tag)
    return hea_tags


async def _bucket_opener(request: web.Request) -> web.Response:
    """
    Returns links for opening the bucket. The volume id must be in the volume_id entry of the request's
    match_info dictionary. The bucket id must be in the id entry of the request's match_info dictionary.

    :param request: the HTTP request (required).
    :return: the HTTP response with a 200 status code if the bucket exists and a Collection+JSON document in the body
    containing an heaobject.bucket.AWSBucket object and links, 403 if access was denied, 404 if the bucket
    was not found, or 500 if an internal error occurred.
    """
    try:
        volume_id = request.match_info['volume_id']
        bucket_id = request.match_info['id']
    except KeyError as e:
        return response.status_bad_request(str(e))
    sub = request.headers.get(SUB, NONE_USER)
    loop = asyncio.get_running_loop()

    async with DesktopObjectActionLifecycle(request=request,
                                            code='hea-get',
                                            description=f'Accessing bucket {bucket_id}',
                                            activity_cb=publish_desktop_object) as activity:
        head_cache_key = (sub, volume_id, bucket_id, 'head')
        actual_cache_key = (sub, volume_id, bucket_id, 'actual')
        if head_cache_key not in request.app[HEA_CACHE] and actual_cache_key not in request.app[HEA_CACHE]:
            async with aws.S3ClientContext(request, volume_id) as s3_client:
                try:
                    await loop.run_in_executor(None, partial(s3_client.head_bucket, Bucket=bucket_id))
                    activity.new_object_id = bucket_id
                    activity.new_object_type_name = AWSBucket.get_type_name()
                    activity.new_object_uri = f'volumes/{volume_id}/buckets/{bucket_id}'
                    activity.new_volume_id = volume_id
                    request.app[HEA_CACHE][head_cache_key] = bucket_id
                except BotoClientError as e:
                    raise awsservicelib.handle_client_error(e)
        return await response.get_multiple_choices(request)


async def _post_bucket(request: web.Request):
    """
    Create an S3 bucket in a specified region. Will fail if the bucket with the given name already exists.
    If a region is not specified, the bucket is created in the S3 default region (us-east-1).

    The request must have either a volume id, which is the id string of the volume representing the user's AWS account,
    or an id, which is the account id.

    :param request: the aiohttp Request (required). A volume_id must be specified in its match info. The AWSBucket
    in the body of the request must have a name.
    """
    logger = logging.getLogger(__name__)
    sub = request.headers.get(SUB, NONE_USER)
    bucket_already_exists_msg = "A bucket named {} already exists"

    volume_id = request.match_info.get('volume_id', None)
    if not volume_id:
        volume_id = await awsservicelib.get_volume_id_for_account_id(request)
        if not volume_id:
            return web.HTTPBadRequest(body="either id or volume_id is required")
    try:
        b = await new_heaobject_from_type(request=request, type_=AWSBucket)
        if not b:
            return web.HTTPBadRequest(body="Post body is not an HEAObject AWSBUCKET")
        if not b.name:
            return web.HTTPBadRequest(body="Bucket name is required")
    except DeserializeException as e:
        return response.status_bad_request(str(e))

    if b.collaborator_ids and sub is not CREDENTIALS_MANAGER_USER and hdrs.AUTHORIZATION not in request.headers and 'access_token' not in request.query:
        # See docs for heaserver.service.db.aws.S3.elevate_privileges() for more information.
        return response.status_bad_request('Cannot set collaborators because no Authorization header nor access_token query parameter was found')

    loop = asyncio.get_running_loop()
    credentials = await request.app[HEA_DB].get_credentials_from_volume(request, volume_id)
    async with aws.S3ClientContext(request, credentials=credentials) as s3_client:
        try:
            await loop.run_in_executor(None, partial(s3_client.head_bucket, Bucket=b.name))  # check if bucket exists, if not throws an exception
            return web.HTTPConflict(body=bucket_already_exists_msg.format(b.display_name))
        except BotoClientError as e:
            loop = asyncio.get_running_loop()
            try:
                # todo this is a privileged actions need to check if authorized
                error_code = e.response['Error']['Code']

                if error_code == '404':  # bucket doesn't exist
                    create_bucket_params: dict[str, Any] = {'Bucket': b.name}
                    put_bucket_policy_params: PublicAccessBlockConfigurationTypeDef = {
                        'BlockPublicAcls': True,
                        'IgnorePublicAcls': True,
                        'BlockPublicPolicy': True,
                        'RestrictPublicBuckets': True
                    }
                    if b.region and b.region != 'us-east-1':
                        create_bucket_params['CreateBucketConfiguration'] = {'LocationConstraint': b.region}
                    if b.locked:
                        create_bucket_params['ObjectLockEnabledForBucket'] = True

                    await loop.run_in_executor(None, partial(s3_client.create_bucket, **create_bucket_params))
                    # make private bucket
                    await loop.run_in_executor(None, partial(s3_client.put_public_access_block, Bucket=b.name,
                                                            PublicAccessBlockConfiguration=put_bucket_policy_params))

                    await _put_bucket_encryption(b, loop, s3_client)
                    # todo this is a privileged action need to check if authorized ( may only be performed by bucket owner)

                    await _put_bucket_versioning(bucket_name=b.name, s3_client=s3_client,
                                                 new_versioning_status=bool(b.versioned))

                    await _put_bucket_tags(s3_client, request=request, volume_id=volume_id,
                                        bucket_name=b.name, new_tags=b.tags)
                    if b.collaborator_ids:
                        elevated_credentials = await request.app[HEA_DB].elevate_privileges(request, credentials) if credentials is not None else None
                        async with aws.IAMClientContext(request=request, credentials=elevated_credentials) as iam_client:
                            coros: list[Coroutine[Any, Any, None]] = []
                            for collaborator_id in b.collaborator_ids:
                                coros.append(_put_collaborator(request=request, volume_id=volume_id, bucket_name=b.name,
                                                            collaborator_id=collaborator_id, iam_client=iam_client))
                            await asyncio.gather(*coros)
                elif error_code == '403':  # already exists but the user doesn't have access to it
                    logger.exception(bucket_already_exists_msg, b.display_name)
                    return response.status_bad_request(bucket_already_exists_msg.format(b.display_name))
                else:
                    logger.exception(str(e))
                    return response.status_bad_request(str(e))
            except BotoClientError as e2:
                logger.exception(str(e2))
                try:
                    await loop.run_in_executor(None, partial(s3_client.head_bucket, Bucket=b.name))
                    del_bucket_result = await loop.run_in_executor(None, partial(s3_client.delete_bucket, Bucket=b.name))
                    logger.debug("deleted failed bucket %s details: %s", b, del_bucket_result)
                except BotoClientError:  # bucket doesn't exist so no clean up needed
                    pass
                return web.HTTPBadRequest(body=e2.response['Error'].get('Message'))
            request.app[HEA_CACHE].pop((sub, volume_id, None, 'items'), None)
            request.app[HEA_CACHE].pop((sub, volume_id, None, 'actual'), None)
            return await response.post(request, b.name, f'volumes/{volume_id}/buckets')


async def _put_bucket_encryption(b, loop, s3_client):
    if b.encrypted:
        SSECNF = 'ServerSideEncryptionConfigurationNotFoundError'
        try:
            await loop.run_in_executor(None, partial(s3_client.get_bucket_encryption, Bucket=b.name))
        except BotoClientError as e:
            if e.response['Error']['Code'] == SSECNF:
                config = \
                    {'Rules': [{'ApplyServerSideEncryptionByDefault':
                                    {'SSEAlgorithm': 'AES256'}, 'BucketKeyEnabled': False}]}
                await loop.run_in_executor(None, partial(s3_client.put_bucket_encryption, Bucket=b.name,
                                                         ServerSideEncryptionConfiguration=config))
            else:
                logging.error(e.response['Error']['Code'])
                raise e


async def _put_bucket_versioning(bucket_name: str, new_versioning_status: bool, s3_client: S3Client,
                                 updating_bucket = False):
    """
    Turns on or off bucket versioning. If an existing bucket is being updated, the versioning status is set to Enabled
    or Suspended. If creating a new bucket, the versioning status is set to Enabled or Disabled.

    Note that if the Object Lock is turned on for the bucket you can't change these settings.

    :param bucket_name: The bucket name (required).
    :param new_versioning_status: Whether bucket versioning should be enabled (required).
    :param s3_client: Pass the active client if exists (required)
    :param updating_bucket: Whether we're updating an existing bucket (True) or creating a new one (False).
    :raises BotoClientError: if an error occurred setting version information.
    """
    logger = logging.getLogger(__name__)
    loop = asyncio.get_running_loop()
    def versioning_status() -> Literal['Enabled', 'Suspended'] | None:
        if new_versioning_status:
            return 'Enabled'
        elif updating_bucket:
            return 'Suspended'
        else:
            return None
    if new_versioning_str := versioning_status():
        vconfig: VersioningConfigurationTypeDef = {
            'MFADelete': 'Disabled',
            'Status': new_versioning_str,
        }
        vresp = await loop.run_in_executor(None, partial(s3_client.put_bucket_versioning, Bucket=bucket_name,
                                                        VersioningConfiguration=vconfig))
        logger.debug('Versioning set to %s', vresp)


async def _put_bucket_tags(s3_client: S3Client, request: web.Request, volume_id: str, bucket_name: str,
                           new_tags: list[Tag] | None):
    """
    Creates or adds to a tag list for bucket

    :param request: the aiohttp Request (required).
    :param volume_id: the id string of the volume representing the user's AWS account (required).
    :param bucket_name: The bucket (required).
    :param new_tags: new tags to be added tag list on specified bucket. Pass in the empty list or None to clear out
    the bucket's tags.
    :raises BotoClientError: if an error occurs interacting with S3.
    """
    if request is None:
        raise ValueError('request is required')
    if volume_id is None:
        raise ValueError('volume_id is required')
    if bucket_name is None:
        raise ValueError('bucket_name is required')

    loop = asyncio.get_running_loop()
    def delete_and_put():
        s3_client.delete_bucket_tagging(Bucket=bucket_name)
        s3_client.put_bucket_tagging(Bucket=bucket_name, Tagging={'TagSet': _to_aws_tags(new_tags or [])})
    await loop.run_in_executor(None, delete_and_put)


async def _delete_collaborator(request: web.Request, bucket_name: str, collaborator: _GetCollaboratorRetval,
                               s3_client: S3Client, iam_client: IAMClient):
    logger = logging.getLogger(__name__)
    loop = asyncio.get_running_loop()
    sub = request.headers.get(SUB, NONE_USER)
    sub_headers = {SUB: sub}
    collaborator_id = collaborator.collaborator_id
    collab_sub_headers = {SUB: collaborator_id}
    cred_man_sub_headers = {SUB: CREDENTIALS_MANAGER_USER}
    policy_arn, policy = await _get_policy_by(iam_client, collaborator_id)
    policy_stmts = policy['Statement']
    assert not isinstance(policy_stmts, str), 'policy_stmt must not be a string'
    role_name = _role_template.format(user_id=collaborator_id)
    await _remove_bucket_from_policy_or_delete_policy(bucket_name, collaborator_id, iam_client, role_name)
    if await _remove_not_found_buckets_from_policy(collaborator, s3_client, iam_client, collaborator_id, role_name):
        logger.debug('User %s has access to other buckets in this account, so not deleting Keycloak groups and role, '
                     'and not sending notification to the organization service that the user is no longer a '
                     'collaborator', collaborator_id)
        return

    account_id = _extract_account_id_from(policy_arn)
    # Delete group and role from keycloak (may need to detach group from user first)
    group_url = await type_to_resource_url(request, Group)
    group_name = f'/Collaborators/AWS Accounts/{account_id}/{collaborator_id}'
    try:
        await client.delete(request.app, URL(group_url) / 'internal' / 'byname' / encode_group(group_name))
        logger.debug('Group %s successfully deleted', group_name)
    except ClientResponseError as e:
        if e.status == 404:
            logger.debug('Group %s already deleted from people service', group_name)
        else:
            raise e

    role_arn = _role_arn_template.format(account_id=account_id, user_id=collaborator_id)
    role_url = await type_to_resource_url(request, Role)
    try:
        await client.delete(request.app, URL(role_url) / 'internal' / 'byname' / encode_role(role_arn))
        logger.debug('Role %s successfully deleted', role_name)
    except ClientResponseError as e:
        if e.status == 404:
            logger.debug('Role %s already deleted from people service', role_name)
        else:
            raise e

    def role_deleter():
        try:
            logger.debug(f'Deleting role %s', role_name)
            iam_client.delete_role(RoleName=role_name)
            logger.debug('Role deletion successful')
        except BotoClientError as e:
            if aws.client_error_code(e) == aws.CLIENT_ERROR_NO_SUCH_ENTITY:
                logger.debug(f'Role {role_name} already deleted from AWS')
            else:
                raise e
    await loop.run_in_executor(None, role_deleter)

    person_url = await type_to_resource_url(request, Person)
    person = await client.get(request.app, URL(person_url) / collaborator_id, Person, headers=sub_headers)
    assert person is not None, f'Person {collaborator_id} disappeared'
    logger.debug('Person %s retrieved successfully', collaborator_id)

    volume_url = await type_to_resource_url(request, Volume)
    volume_name = f'{account_id}_Collaborator_{collaborator_id}'
    logger.debug('Getting volume %s', volume_name)
    volume = await client.get(request.app, URL(volume_url) / 'byname' / volume_name, Volume, headers=collab_sub_headers)
    logger.debug('Got volume %r', volume)
    if volume is not None:
        assert volume.id is not None, 'volume.id cannot be None'
        try:
            logger.debug('Deleting volume %s', volume.id)
            await client.delete(request.app, URL(volume_url) / volume.id, headers=cred_man_sub_headers)
            logger.debug('Volume %s deleted successfully', volume.id)
        except ClientResponseError as e:
            if e.status == 404:
                logger.debug('Volume %s not found', volume.id)
            else:
                raise e
        credentials_view_id = volume.credentials_id
        if credentials_view_id is not None:
            credentials_view_url = await type_to_resource_url(request, CredentialsView)
            creds_view = await client.get(request.app, URL(credentials_view_url) / credentials_view_id,
                                          CredentialsView, headers=collab_sub_headers)
            assert creds_view is not None, f'CredentialsView {credentials_view_id} must not be None'
            assert creds_view.actual_object_id is not None, 'creds_view.actual_object_id must not be None'
            assert creds_view.actual_object_type_name is not None, 'creds_view.actual_object_type_name must not be None'
            logger.debug('Deleting credentials %r', creds_view)
            credential_url = await type_to_resource_url(request, creds_view.actual_object_type_name)
            try:
                await client.delete(request.app, URL(credential_url) / creds_view.actual_object_id,
                                    headers=cred_man_sub_headers)
                logger.debug('Credentials %r deleted successfully', creds_view)
            except ClientResponseError as e:
                if e.status == 404:
                    logger.debug('Credentials %r not found', creds_view)
                else:
                    raise e

    logger.debug('Getting AWS account %s', account_id)
    aws_account_url = await type_to_resource_url(request, AWSAccount)
    account_headers = dict(sub_headers)
    if hdrs.AUTHORIZATION in request.headers:
        account_headers[hdrs.AUTHORIZATION] = request.headers[hdrs.AUTHORIZATION]
    aws_account = await client.get(request.app, URL(aws_account_url) / account_id, AWSAccount, headers=account_headers)
    assert aws_account is not None, f'AWS account {account_id} disappeared'
    logger.debug('AWS account %r retrieved successfully', aws_account)

    organization_url = await type_to_resource_url(request, Organization)
    assert aws_account.instance_id is not None, 'aws_account.instance_id must not be None'
    async with _update_collaborators_lock:
        organization = await client.get(request.app, URL(organization_url) / 'byaccountid' / aws_account.instance_id,
                                        Organization, headers=sub_headers)
        logger.debug('Found organization %r', organization)
        if organization is not None:
            logger.debug('Removing collaborator %r from organization %s', person, organization.id)
            removing_collaborator: AWSRemovingCollaborator = AWSRemovingCollaborator(person=person,
                                                                                     account=aws_account,
                                                                                     organization=organization)
            removing_collaborator.bucket_id = bucket_name
            removing_collaborator.actual_object_uri = f'people/{person.id}'
            logger.debug('Preparing to publish desktop object %r successfully', removing_collaborator)
            await publish_desktop_object(request.app, removing_collaborator)
            logger.debug('Published desktop object %r successfully', removing_collaborator)

async def _remove_not_found_buckets_from_policy(collaborator: _GetCollaboratorRetval, s3_client: S3Client,
                                                iam_client: IAMClient, collaborator_id: str,
                                                role_name: str) -> set[str]:
    """Removes any buckets from the policy that no longer exist in S3, returning the remaining bucket names.

    :param collaborator: The collaborator whose policy is being checked.
    :param s3_client: The S3 client to check bucket existence.
    :param iam_client: The IAM client to modify the policy.
    :param collaborator_id: The ID of the collaborator.
    :param role_name: The name of the IAM role associated with the collaborator.
    :return: A set of remaining bucket names that still exist in S3.
    :raises BotoClientError: If there is an error checking bucket existence or modifying the policy.
    """
    logger = logging.getLogger(__name__)
    result: set[str] = set(collaborator.other_bucket_names)
    for other_bucket_name in collaborator.other_bucket_names:
        try:
            await asyncio.to_thread(s3_client.head_bucket, Bucket=other_bucket_name)
        except BotoClientError as e:
            if aws.client_error_code(e) == aws.CLIENT_ERROR_404:
                logger.debug('Bucket %s not found, removing from policy', other_bucket_name)
                await _remove_bucket_from_policy_or_delete_policy(other_bucket_name, collaborator_id, iam_client, role_name)
                result.remove(other_bucket_name)
            else:
                raise
    return result

async def _detach_and_delete_policy(iam_client: IAMClient, policy_arn: str):
    logger = logging.getLogger(__name__)
    loop = asyncio.get_running_loop()
    def policy_detacher():
        policy_attachments = iam_client.list_entities_for_policy(PolicyArn=policy_arn)
        for policy_role in policy_attachments['PolicyRoles']:
            logger.debug('Detaching policy %s from role %s', policy_arn, policy_role['RoleName'])
            iam_client.detach_role_policy(RoleName=policy_role['RoleName'], PolicyArn=policy_arn)
            logger.debug('Role detachment successful')
        for policy_user in policy_attachments['PolicyUsers']:
            logger.warning('Detaching policy %s from user %s', policy_arn, policy_user['UserName'])
            iam_client.detach_user_policy(UserName=policy_user['UserName'], PolicyArn=policy_arn)
            logger.warning('User detachment successful')
        for policy_group in policy_attachments['PolicyGroups']:
            logger.warning('Detaching policy %s from group %s', policy_arn, policy_group['GroupName'])
            iam_client.detach_group_policy(GroupName=policy_group['GroupName'], PolicyArn=policy_arn)
            logger.warning('Group detachment successful')
    def policy_deleter():
        try:
            logger.debug(f'Deleting policy %s', policy_arn)
            iam_client.delete_policy(PolicyArn=policy_arn)
            logger.debug('Policy deletion successful')
        except BotoClientError as e:
            if e.response['Error']['Code'] == 'NoSuchEntity':
                logger.debug(f'Policy {policy_arn} already deleted')
            elif e.response['Error']['Code'] == 'DeleteConflict':
                logger.debug('Policy is still attached to %s', iam_client.list_entities_for_policy(PolicyArn=policy_arn))
                raise e
            else:
                raise e
    logger.debug('Detaching and deleting policy %s', policy_arn)
    await loop.run_in_executor(None, policy_detacher)
    await loop.run_in_executor(None, policy_deleter)

def _extract_account_id_from(arn: str) -> str:
    return arn.split(':')[4]

async def _get_policy_by(iam_client: IAMClient, user_id: str) -> tuple[str, PolicyDocumentDictTypeDef]:
    logger = logging.getLogger(__name__)
    logger.debug('Getting collaborator policy for user %s', user_id)
    loop = asyncio.get_running_loop()
    response_ = (await loop.run_in_executor(None, partial(iam_client.get_account_authorization_details,
                                                                     Filter=['LocalManagedPolicy'])))
    logger.debug('Account authorization details: %s', response_)
    for policy in response_['Policies']:
        logger.debug('Policy detail: %s', policy)
        if policy['PolicyName'] == _collaborator_policy_name_template.format(user_id=user_id):
            for version in policy['PolicyVersionList']:
                if version['IsDefaultVersion']:
                    pol_doc = version['Document']
                    logger.debug('Returning policy doc from policy %s for user %s: %s', policy, user_id, pol_doc)
                    assert not isinstance(pol_doc, str), 'pol_doc unexpected type'
                    return policy['Arn'], pol_doc
    raise ValueError(f'Policy for user {user_id} not found')

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

async def _put_collaborator(request: web.Request, volume_id: str, bucket_name: str, collaborator_id: str, iam_client: IAMClient):
    logger = logging.getLogger(__name__)
    loop = asyncio.get_running_loop()
    sub = request.headers.get(SUB, NONE_USER)
    sub_headers = {SUB: sub}
    collab_sub_headers = {SUB: collaborator_id}
    cred_man_sub_headers = {SUB: CREDENTIALS_MANAGER_USER}
    person_url = await type_to_resource_url(request, Person)

    logger.debug('Getting person %s', collaborator_id)
    person_url = await type_to_resource_url(request, Person)
    person = await client.get(request.app, URL(person_url) / collaborator_id, Person, headers=sub_headers)
    assert person is not None, f'Person {collaborator_id} disappeared'
    logger.debug('Person %s retrieved successfully', collaborator_id)

    logger.debug('Getting AWS account for volume %s', volume_id)
    aws_account = cast(AWSAccount, await request.app[HEA_DB].get_account(request, volume_id))
    assert aws_account is not None, f'AWS account for volume {volume_id} disappeared'
    account_id = aws_account.id
    assert account_id is not None, f'aws_account.account_id cannot be None for account {aws_account}'
    logger.debug('AWS account %r retrieved successfully', aws_account)

    volume_url = await type_to_resource_url(request, Volume)
    volume_name = f'{aws_account.id}_Collaborator_{collaborator_id}'
    async def get_volume() -> Volume | None:
        assert aws_account.instance_id is not None, 'aws_account.instance_id cannot be None'
        assert person is not None, 'person cannot be None'
        logger.debug('Checking if user %s already has access to account %s', collaborator_id, aws_account.id)
        user_volumes_gen = client.get_all(request.app, URL(volume_url).with_query([('account_id', aws_account.instance_id)]), Volume, headers=collab_sub_headers)
        volume_: Volume | None = None
        async for volume in user_volumes_gen:
            logger.debug('Checking volume %r', volume)
            if volume.owner == CREDENTIALS_MANAGER_USER:
                if volume.name != f'{aws_account.id}_Collaborator_{person.id}':
                    raise response.status_conflict(f'{person.display_name} already has access to this AWS account')
                elif volume.name == volume_name:
                    volume_ = volume
        return volume_
    volume_ = await get_volume()

    policy = await _add_bucket_to_policy(bucket_name, collaborator_id, iam_client)
    policy_arn = policy['Arn']
    logger.debug("Created policy %s", policy)
    oidc_provider_url = request.headers[ISS].removeprefix('https://')
    logger.debug('OIDC provider URL is %s', oidc_provider_url)
    id_provider_arn = f"arn:aws:iam::{account_id}:oidc-provider/{oidc_provider_url}"
    # AWS seems to use the azp claim (client id) rather than the actual aud claim (intended user).
    oidc_aud = request.headers.get(AZP, 'hea')
    assume_role_policy_doc = orjson.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Federated": id_provider_arn
                },
                "Action": "sts:AssumeRoleWithWebIdentity",
                "Condition": {
                    "StringEquals": {
                        f"{oidc_provider_url}:aud": oidc_aud
                    }
                }
            }
        ]
    }).decode('utf-8')
    logger.debug('Assume role policy document is %s', assume_role_policy_doc)
    role_name = _role_template.format(user_id=collaborator_id)
    role_arn = _role_arn_template.format(account_id=account_id, user_id=collaborator_id)

    # Create role in keycloak, create group in keycloak with role, and add user to group.
    role = Role()
    role.role = role_arn
    role_url = await type_to_resource_url(request, Role)
    try:
        logger.debug('Creating role %r', role)
        try:
            role_location_url = await client.post(request.app, URL(role_url) / 'internal', role)
            role.id = role_location_url.rsplit('/', maxsplit=1)[1]
            logger.debug('Role created successfully')
        except ClientResponseError as e:
            if e.status == 409:
                logger.debug('Role %r already exists', role)
                role_from_server = await client.get(request.app, URL(role_url) / 'byname' / encode_role(role_arn), Role)
                assert role_from_server is not None, 'role_from_server is not None'
                role = role_from_server
            else:
                raise e
        assert role.id is not None, 'role.id cannot be None'
        group_url_ = await type_to_resource_url(request, Group)
        group: Group = Group()
        group.group = f'/Collaborators/AWS Accounts/{account_id}/{collaborator_id}'
        group.role_ids = [role.id]
        logger.debug('Creating group %r', group)
        try:
            group_url = await client.post(request.app, URL(group_url_) / 'internal', group)
            group.id = group_url.rsplit('/', maxsplit=1)[1]
            group_id: str | None = group.id
            logger.debug('Group %s created successfully', group)
        except ClientResponseError as e:
            if e.status == 409:
                logger.debug('Group %r already exists', group)
                group_ = await client.get(request.app, URL(group_url_) / 'byname' / encode_group(group.group), Group)
                assert group_ is not None, 'group cannot be None'
                group = group_
                group_id = group.id
            else:
                raise e
        assert group_id is not None, 'group.id cannot be None'
        logger.debug('Adding user %s to group %r', collaborator_id, group)
        await client.post(request.app, URL(person_url) / collaborator_id / 'groups', data=group,
                          headers=cred_man_sub_headers)
        logger.debug('User added successfully, creating role %s in AWS', role_name)
        try:
            await loop.run_in_executor(None, partial(iam_client.create_role, RoleName=role_name, Path='/',
                                                     AssumeRolePolicyDocument=assume_role_policy_doc,
                                                     MaxSessionDuration=aws.S3.MAX_DURATION_SECONDS))
            logger.debug('AWS role created successfully, attaching policy %s to role %s', policy_arn, role_name)
        except BotoClientError as e:
            if e.response['Error']['Code'] == 'EntityAlreadyExists':
                logger.debug('AWS role %s already exists', role_name)
            else:
                raise e
        await loop.run_in_executor(None, partial(iam_client.attach_role_policy, RoleName=role_name, PolicyArn=policy_arn))
        logger.debug('AWS role attached successfully')

        # Create and post AWSCredentials object, then create and post Volume object.
        person.add_group_id(group_id)
        logger.debug('Creating new credentials for account %r, person %r, and group %r', aws_account, person, group)
        new_credentials = aws_account.new_credentials(person, [group])
        assert new_credentials is not None, 'AWS credentials is unexpectedly None'
        new_credentials.display_name = f'Collaborator on AWS account {account_id}'
        new_credentials.owner = CREDENTIALS_MANAGER_USER
        share: ShareImpl = ShareImpl()
        share.user = collaborator_id
        share.permissions = [Permission.VIEWER]
        new_credentials.add_share(share)
        assert new_credentials.name is not None, 'new_credentials.name cannot be None'

        # Get volume for account, and if there is a volume that isn't a collaborator volume, error out.
        # The organizations microservice just overwrites the volume info since it's by definition higher access.
        logger.debug('User %s can be a collaborator', collaborator_id)
        if volume_ is not None:
            logger.debug('Volume %s found', volume_name)
            volume: Volume = volume_
        else:
            logger.debug('Volume %s not found, so creating a new volume', volume_name)
            volume = Volume()
            volume.name = volume_name
            volume.file_system_type = AWSFileSystem.get_type_name()
        volume.account_id = aws_account.instance_id
        volume.owner = CREDENTIALS_MANAGER_USER
        volume.add_share(share)
        volume.display_name = f'AWS Account {account_id}'

        aws_credentials_url = await type_to_resource_url(request, AWSCredentials)
        try:
            logger.debug('Trying to post a credentials object: %r', new_credentials)
            new_credentials_url = await client.post(request.app, aws_credentials_url, new_credentials,
                                                    headers=cred_man_sub_headers)
            credential_id = new_credentials_url[new_credentials_url.rindex('/') + 1:]
            new_credentials.id = credential_id
            volume.credentials_id = new_credentials.instance_id
        except ClientResponseError as e:
            if e.status == 409:
                logger.debug('Existing credentials object %r; getting existing one', new_credentials)
                credentials_by_name = await client.get(request.app,
                                                    URL(aws_credentials_url) / 'byname' / new_credentials.name,
                                                    AWSCredentials, headers=collab_sub_headers)
                logger.debug('Got existing credentials %r', credentials_by_name)
                assert credentials_by_name is not None, 'credentials_by_name cannot be None'
                assert credentials_by_name.id is not None, 'credentials_by_name.id cannot be None'
                credentials_by_name.temporary = True
                credentials_by_name.expiration = None  # force existing temporary credentials to refresh.
                logger.debug('Updating existing credentials %r', credentials_by_name)
                await client.put(request.app, URL(aws_credentials_url) / credentials_by_name.id, credentials_by_name,
                                 headers=cred_man_sub_headers)
                volume.credentials_id = credentials_by_name.instance_id
                logger.debug('Updating existing credentials successfully')
            else:
                raise e

        if volume_ is not None:
            logger.debug('Updating volume %r', volume)
            assert volume.id is not None, 'volume.id cannot be None'
            await client.put(request.app, URL(volume_url) / volume.id, volume, headers=cred_man_sub_headers)
            logger.debug('Updated volume successfully')
        else:
            logger.debug('Creating volume %r', volume)
            await client.post(request.app, volume_url, volume, headers=cred_man_sub_headers)
            logger.debug('Created volume successfully')

        organization_url = await type_to_resource_url(request, Organization)
        assert aws_account.instance_id is not None, 'aws_account.instance_id cannot be None'

        async with _update_collaborators_lock:
            organization = await client.get(request.app, URL(organization_url) / 'byaccountid' / aws_account.instance_id,
                                            Organization, headers=sub_headers)
            logger.debug('Found organization %r', organization)
            if organization is not None and person.id not in organization.collaborator_ids:
                collaborator: AWSAddingCollaborator = AWSAddingCollaborator(person=person, account=aws_account,
                                                                            organization=organization)
                collaborator.bucket_id = bucket_name
                collaborator.actual_object_uri = f'people/{person.id}'
                logger.debug('Preparing to publish desktop object %r successfully', collaborator)
                await publish_desktop_object(request.app, collaborator)
                logger.debug('Published desktop object %r successfully', collaborator)
    except ClientResponseError as e:
        if e.status == 409:
            raise response.status_conflict()
        else:
            raise response.status_internal_error()

async def _add_bucket_to_policy(bucket_name: str, collaborator_id: str, iam_client: IAMClient) -> PolicyTypeDef:
    logger = logging.getLogger(__name__)
    loop = asyncio.get_running_loop()
    policy_name = _collaborator_policy_name_template.format(user_id=collaborator_id)
    try:
        policy_arn, policy_doc = await _get_policy_by(iam_client, collaborator_id)
        await _detach_and_delete_policy(iam_client, policy_arn)
        policy_doc = _new_policy_doc(set(_get_buckets_from(policy_doc) + [bucket_name]))
    except ValueError:
        policy_doc = _new_policy_doc([bucket_name])
    logger.debug('Creating policy with policy document %s', policy_doc)
    return (await loop.run_in_executor(None, partial(iam_client.create_policy,
                                                     PolicyName=policy_name,
                                                     Path=_collab_policy_path, PolicyDocument=orjson.dumps(policy_doc).decode('utf-8'))))['Policy']


async def _remove_bucket_from_policy_or_delete_policy(bucket_name: str, collaborator_id: str, iam_client: IAMClient, role_name: str):
    logger = logging.getLogger(__name__)
    loop = asyncio.get_running_loop()
    policy_name = _collaborator_policy_name_template.format(user_id=collaborator_id)
    try:
        policy_arn, policy_doc = await _get_policy_by(iam_client, collaborator_id)
        await _detach_and_delete_policy(iam_client, policy_arn)
        new_bucket_set = set(bucket_nm for bucket_nm in _get_buckets_from(policy_doc) if bucket_nm != bucket_name)
        if new_bucket_set:
            policy_doc = _new_policy_doc(new_bucket_set)
            logger.debug('Creating policy with policy document %s', policy_doc)
            policy = (await loop.run_in_executor(None, partial(iam_client.create_policy,
                                                               PolicyName=policy_name,
                                                               Path=_collab_policy_path, PolicyDocument=orjson.dumps(policy_doc).decode('utf-8'))))['Policy']
            await loop.run_in_executor(None, partial(iam_client.attach_role_policy, RoleName=role_name, PolicyArn=policy['Arn']))
    except ValueError:
        pass
    except BotoClientError as e:
        if aws.client_error_code(e) == aws.CLIENT_ERROR_NO_SUCH_ENTITY:
            logger.debug('Policy or role already deleted')
        else:
            raise e



def _to_aws_tags(hea_tags: list[Tag]) -> list[dict[str, str | None]]:
    """
    :param hea_tags: HEA tags to converted to aws tags compatible with boto3 api
    :return: aws tags
    """
    aws_tag_dicts = []
    for hea_tag in hea_tags:
        aws_tag_dict = {}
        aws_tag_dict['Key'] = hea_tag.key
        aws_tag_dict['Value'] = hea_tag.value
        aws_tag_dicts.append(aws_tag_dict)
    return aws_tag_dicts


_role_template = 'aws-Collaborator.Role_{user_id}'
_collaborator_policy_name_prefix = 'aws-Collaborator.Policy_'
_collaborator_policy_name_template = _collaborator_policy_name_prefix + '{user_id}'
_role_arn_template = 'arn:aws:iam::{account_id}:role/aws-Collaborator.Role_{user_id}'
_collab_policy_path = '/heainternal/collaborators/'
_policy_arn_template = 'arn:aws:iam::{account_id}:policy' + _collab_policy_path + _collaborator_policy_name_template
_arn_pattern = re.compile("[:/]")

def _new_policy_doc(bucket_names: Collection[str]) -> PolicyDocumentDictTypeDef:
    resources = list(chain.from_iterable((f"arn:aws:s3:::{bucket_name}", f"arn:aws:s3:::{bucket_name}/*") for bucket_name in bucket_names))
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "HEA0",
                "Effect": "Allow",
                "Action": [
                    "s3:GetBucketTagging",
                    "s3:GetObjectRetention",
                    "s3:ListBucketVersions",
                    "s3:RestoreObject",
                    "s3:ListBucket",
                    "s3:GetBucketVersioning",
                    "s3:GetBucketPolicy",
                    "s3:GetBucketObjectLockConfiguration",
                    "s3:GetObject",
                    "s3:GetEncryptionConfiguration",
                    "s3:GetObjectTagging",
                    "s3:GetBucketLocation",
                    "s3:GetObjectVersion"
                ],
                "Resource": resources
            },
            {
                "Sid": "HEA1",
                "Effect": "Allow",
                "Action": "s3:ListAllMyBuckets",
                "Resource": "*"
            }
        ]
    }

def _get_buckets_from(policy_doc: PolicyDocumentTypeDef | PolicyDocumentDictTypeDef) -> list[str]:
    assert not isinstance(policy_doc, str), 'Unexpected str'
    stmt = policy_doc['Statement']
    assert not isinstance(stmt, str), 'Unexpected str'
    resource = stmt[0]['Resource']
    if isinstance(resource, str):
        return [_arn_pattern.split(resource)[5]]
    else:
        return [_arn_pattern.split(arn)[5] for arn in resource]


# Define a function to check the bucket's head
def _check_bucket_access(bucket_name: str, s3_client: S3Client) -> bool:
    logger = logging.getLogger(__name__)
    try:
        # Perform the head_bucket call
        s3_client.head_bucket(Bucket=bucket_name)
        return True  # Return the name if access is granted
    except BotoClientError as e:
        if aws.client_error_code(e) == aws.CLIENT_ERROR_FORBIDDEN:
            logger.debug("The bucket %s is not accessible", bucket_name, exc_info=True)
            return False  # Return None if access is denied
        else:
            raise  # Reraise if it's a different error
