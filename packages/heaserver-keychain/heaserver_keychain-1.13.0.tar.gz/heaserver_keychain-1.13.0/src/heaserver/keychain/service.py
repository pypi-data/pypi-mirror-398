"""
The HEA Keychain manages credentials for connecting to networked services and resources.

AWS credentials endpoints provide functionality specific to AWS:
* Long-term credentials: An access key and secret that do not expire.  These credentials are typically owned by the 
user.
* Temporary credentials: Temporary credentials created using the user's HEA JWT token. The user is granted a short-term
access key and secret with a 12 hour lifespan that HEA refreshes automatically and in the background. Temporary
credentials are owned by the system|credentialsmanager user and shared with the requester. The requester is given 
VIEWER permissions.
* Secure managed credentials: starting from a user's temporary credentials, these endpoints create a permanent AWS
credential that is invalidated and deleted by this microservice after a defined lifespan. Secure managed credentials
are owned by the system|credentialsmanager user and shared with the requester. The requester is given VIEWER 
permissions. Secure managed credentials are created behind the scenes as part of presigned URL requests because 
otherwise the URLs would stop working as soon as the user's temporary credentials expire or are refreshed. They are
also created when a user requests a CLI credentials file, and the user can request a credentials lifespan of up to 72 
hours. Users can request to extend the lifespan by up to another 72 hours as many times as is needed.
"""
from datetime import timedelta
from functools import partial
from aiohttp import hdrs
from heaobject.activity import Status
from heaobject.data import ClipboardData
from heaobject.root import Share, ShareImpl, Permission, ViewerPermissionContext, PermissionContext, \
    desktop_object_type_for_name, json_dumps, to_dict
from heaobject.encryption import Encryption
from heaserver.service import response, appproperty, client
from heaserver.service.activity import DesktopObjectActionLifecycle
from heaserver.service.oidcclaimhdrs import SUB
from heaobject.user import NONE_USER, CREDENTIALS_MANAGER_USER
from heaserver.service.runner import routes, start, web, scheduled_cleanup_ctx_factory
from heaserver.service.config import Configuration
from heaserver.service.db import mongoservicelib, aws, mongo
from heaserver.service.wstl import builder_factory, action
from heaserver.service.messagebroker import publisher_cleanup_context_factory, publish_desktop_object
from heaserver.service.util import now
from heaserver.service.crypt import get_attribute_encryption_from_request
from heaobject.keychain import Credentials, AWSCredentials, CredentialsView
from heaobject.awss3key import display_name, is_folder
import asyncio
from heaserver.service.appproperty import HEA_DB
from botocore.exceptions import ClientError
from heaobject.error import DeserializeException
from collections.abc import Collection
import logging

from mypy_boto3_iam import IAMClient
from mypy_boto3_iam.type_defs import ListAttachedRolePoliciesResponseTypeDef
from yarl import URL
from typing import Any, Literal
import uuid


_logger = logging.getLogger(__name__)
MONGODB_CREDENTIALS_COLLECTION = 'credentials'


@routes.get('/credentialsping')
async def ping(request: web.Request) -> web.Response:
    """
    Checks if this service is running.

    :param request: the HTTP request.
    :return: the HTTP response.
    """
    return await mongoservicelib.ping(request)


@routes.get('/credentials/{id}')
@action('heaserver-keychain-credentials-get-properties', rel='hea-properties hea-context-menu')
@action('heaserver-keychain-credentials-get-self', rel='self', path='credentials/{id}')
async def get_credentials(request: web.Request) -> web.Response:
    """
    Gets the credentials with the specified id.

    :param request: the HTTP request.
    :return: the requested credentials or Not Found.
    ---
    summary: A specific credentials.
    tags:
        - heaserver-keychain-get-credentials
    parameters:
        - $ref: '#/components/parameters/id'
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    responses:
      '200':
        $ref: '#/components/responses/200'
      '404':
        $ref: '#/components/responses/404'
    """
    _logger.debug('Requested credentials by id %s' % request.match_info["id"])
    
    cred_dict = await mongoservicelib.get_dict(request, MONGODB_CREDENTIALS_COLLECTION)
    if cred_dict and cred_dict['type'] == Credentials.get_type_name():
        sub = request.headers.get(SUB, NONE_USER)
        context = PermissionContext(sub)
        credentials: Credentials = Credentials()
        credentials.from_dict(cred_dict)
        share = await credentials.get_permissions_as_share(context)
        credentials.add_user_share(share)
        attr_perms = await credentials.get_all_attribute_permissions(context)
        return await response.get(request, cred_dict, permissions=share.permissions, attribute_permissions=attr_perms)
    else:
        return response.status_not_found()


@routes.get('/awscredentials/{id}')
@action('heaserver-keychain-awscredentials-get-properties', rel='hea-properties hea-context-menu')
@action(name='heaserver-keychain-generate-awscredentials-file',
        rel='hea-dynamic-clipboard hea-generate-clipboard-icon hea-context-menu',
        path='awscredentials/{id}/climanagedcredentialscreator',
        itemif='temporary')
@action(name='heaserver-keychain-generate-awscredentials-file-managed',
        rel='hea-dynamic-clipboard hea-retrieve-clipboard-icon hea-context-menu',
        path='awscredentials/{id}/clicredentialsfile',
        itemif='not temporary and not for_presigned_url')
@action(name='heaserver-keychain-update-awscredentials-file',
        rel='hea-dynamic-standard hea-generate-clipboard-icon hea-context-menu',
        path='awscredentials/{id}/expirationextender',
        itemif='managed and not for_presigned_url')
@action('heaserver-keychain-credentials-get-self', rel='self', path='awscredentials/{id}')
async def get_aws_credentials(request: web.Request) -> web.Response:
    """
    Gets the AWS credentials with the specified id.

    :param request: the HTTP request.
    :return: the requested credentials or Not Found.
    ---
    summary: A specific credentials.
    tags:
        - heaserver-keychain-get-credentials
    parameters:
        - $ref: '#/components/parameters/id'
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    responses:
      '200':
        $ref: '#/components/responses/200'
      '404':
        $ref: '#/components/responses/404'
    """
    _logger.debug('Requested AWS credentials by id %s' % request.match_info["id"])
    return await _get_aws_credentials(request)
    


@routes.get('/awscredentials/{id}/climanagedcredentialscreator')
@action(name="heaserver-keychain-generate-awscredentials-file-form")
async def get_aws_cli_credential_form(request: web.Request) -> web.Response:
    """
    Gets a form template for creating or extending a managed AWSCredentials object. Managed credentials have a defined 
    lifespan, and HEA deletes them after they have expired. Submitting this form will create a managed AWSCredentials
    object with the specified lifespan for the user and AWS account associated with the temporary AWSCredentials with 
    the given id. The HTTP request must either have no Accept header or an Accept header with a representor mimetype 
    that supports form templates.

    :param request: the HTTP request (required).
    :return: the requested form template.
    """
    return await _get_aws_credentials(request)

@routes.get('/awscredentials/{id}/clicredentialsfile')
@action(name="heaserver-keychain-generate-awscredentials-file-form-managed")
async def get_aws_cli_managed_credential_form(request: web.Request) -> web.Response:
    """
    Gets a form template for creating or extending a managed AWSCredentials object. Managed credentials have a defined 
    lifespan, and HEA deletes them after they have expired. Submitting this form will create a managed AWSCredentials
    object with the specified lifespan for the user and AWS account associated with the temporary AWSCredentials with 
    the given id. The HTTP request must either have no Accept header or an Accept header with a representor mimetype 
    that supports form templates.

    :param request: the HTTP request (required).
    :return: the requested form template.
    """
    return await _get_aws_credentials(request)


@routes.get('/awscredentials/{id}/expirationextender')
@action(name="heaserver-keychain-extend-expiration-form")
async def get_credentials_extender_form(request: web.Request) -> web.Response:
    """
    Gets a form template for extending the expiration of a managed AWSCredentials object. Submitting this form updates
    the expiration of the credentials. The HTTP request must either have no Accept header or an Accept header with a r
    epresentor mimetype that supports form templates.

    :param request: the HTTP request (required).
    :return: the requested form template.
    """
    return await _get_aws_credentials(request)


@routes.get('/credentials/byname/{name}')
async def get_credentials_by_name(request: web.Request) -> web.Response:
    """
    Gets the credentials with the specified name.

    :param request: the HTTP request.
    :return: the requested credentials or Not Found.
    ---
    summary: Specific credentials queried by name.
    tags:
        - heaserver-keychain-get-credentials-by-name
    parameters:
        - $ref: '#/components/parameters/name'
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    responses:
      '200':
        $ref: '#/components/responses/200'
      '404':
        $ref: '#/components/responses/404'
    """
    _logger.debug('Requested credentials by name %s' % request.match_info["name"])
    sub = request.headers.get(SUB, NONE_USER)
    cred_dict = await mongoservicelib.get_by_name_dict(request, MONGODB_CREDENTIALS_COLLECTION)
    if cred_dict and cred_dict['type'] == Credentials.get_type_name():
        context = PermissionContext(sub)
        credentials: Credentials = Credentials()
        credentials.from_dict(cred_dict)
        share = await credentials.get_permissions_as_share(context)
        credentials.add_user_share(share)
        attr_perms = await credentials.get_all_attribute_permissions(context)
        return await response.get(request, cred_dict, permissions=share.permissions, attribute_permissions=attr_perms)
    else:
        return response.status_not_found()


@routes.get('/awscredentials/byname/{name}')
async def get_aws_credentials_by_name(request: web.Request) -> web.Response:
    """
    Gets the AWS credentials with the specified name.

    :param request: the HTTP request.
    :return: the requested credentials or Not Found.
    ---
    summary: Specific credentials queried by name.
    tags:
        - heaserver-keychain-get-credentials-by-name
    parameters:
        - $ref: '#/components/parameters/name'
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    responses:
      '200':
        $ref: '#/components/responses/200'
      '404':
        $ref: '#/components/responses/404'
    """
    _logger.debug('Requested AWS credentials by name %s' % request.match_info["name"])
    sub = request.headers.get(SUB, NONE_USER)
    cred_dict = await mongoservicelib.get_by_name_dict(request, MONGODB_CREDENTIALS_COLLECTION)
    if cred_dict and cred_dict['type'] == AWSCredentials.get_type_name():
        context = PermissionContext(sub)
        aws_credentials: AWSCredentials = AWSCredentials()
        aws_credentials.from_dict(cred_dict)
        share = await aws_credentials.get_permissions_as_share(context)
        aws_credentials.add_user_share(share)
        attr_perms = await aws_credentials.get_all_attribute_permissions(context)
        return await response.get(request, cred_dict, permissions=share.permissions, attribute_permissions=attr_perms)
    else:
        return response.status_not_found()


@routes.get('/awscredentials')
@routes.get('/awscredentials/')
@action('heaserver-keychain-awscredentials-get-properties', rel='hea-properties hea-context-menu')
@action(name='heaserver-keychain-generate-awscredentials-file',
        rel='hea-dynamic-clipboard hea-generate-clipboard-icon hea-context-menu',
        path='awscredentials/{id}/climanagedcredentialscreator',
        itemif='temporary')
@action(name='heaserver-keychain-generate-awscredentials-file-managed',
        rel='hea-dynamic-clipboard hea-retrieve-clipboard-icon hea-context-menu',
        path='awscredentials/{id}/clicredentialsfile',
        itemif='not temporary and not for_presigned_url')
@action(name='heaserver-keychain-update-awscredentials-file',
        rel='hea-dynamic-standard hea-generate-clipboard-icon hea-context-menu',
        path='awscredentials/{id}/expirationextender',
        itemif='managed and not for_presigned_url')
@action('heaserver-keychain-credentials-get-self', rel='self', path='awscredentials/{id}')
async def get_all_aws_credentials(request: web.Request) -> web.Response:
    return await mongoservicelib.get_all(request, MONGODB_CREDENTIALS_COLLECTION, 
                                         mongoattributes={'type': AWSCredentials.get_type_name()})


@routes.get('/credentials')
@routes.get('/credentials/')
@action('heaserver-keychain-credentials-get-properties', rel='hea-properties hea-context-menu')
@action('heaserver-keychain-credentials-get-self', rel='self', path='credentials/{id}')
async def get_all_credentials(request: web.Request) -> web.Response:
    return await mongoservicelib.get_all(request, MONGODB_CREDENTIALS_COLLECTION, 
                                         mongoattributes={'type': Credentials.get_type_name()})


@routes.get('/credentialsviews')
@routes.get('/credentialsviews/')
@action('heaserver-keychain-credentialsviews-get-actual', rel='hea-actual', path='{+actual_object_uri}')
async def get_all_credentials_views(request: web.Request) -> web.Response:
    """
    Gets all credentials.

    :param request: the HTTP request.
    :return: all credentials.

    ---
    summary: All credentials.
    tags:
        - heaserver-keychain-get-all-credentials
    parameters:
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    responses:
      '200':
        $ref: '#/components/responses/200'
    """
    sub = request.headers.get(SUB, NONE_USER)
    context = ViewerPermissionContext(sub)
    views: list[CredentialsView] = []
    permissions: list[list[Permission]] = []
    attribute_permissions: list[dict[str, list[Permission]]] = []
    for credentials_dict in await mongoservicelib.get_all_dict(request, MONGODB_CREDENTIALS_COLLECTION):
        view, perms, attr_perms = await _new_credentials_view(context, credentials_dict)
        views.append(view)
        permissions.append(perms)
        attribute_permissions.append(attr_perms)
    view_dicts = [to_dict(v) for v in views]
    return await response.get_all(request, view_dicts, permissions, attribute_permissions)


@routes.get('/credentialsviews/{id}')
@action('heaserver-keychain-credentialsviews-get-actual', rel='hea-actual', path='{+actual_object_uri}')
async def get_credentials_view(request: web.Request) -> web.Response:
    """
    Gets credentials.

    :param request: the HTTP request.
    :return: all credentials.

    ---
    summary: All credentials.
    tags:
        - heaserver-keychain-get-credentials
    parameters:
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    responses:
      '200':
        $ref: '#/components/responses/200'
    """
    sub = request.headers.get(SUB, NONE_USER)
    context = ViewerPermissionContext(sub)
    the_id = request.match_info['id'].split('^', 1)
    logging.getLogger(__name__).debug("Getting credentials view for id %r", the_id)
    if len(the_id) != 2:
        return response.status_not_found()
    type_, id_ = the_id
    if not issubclass(desktop_object_type_for_name(type_), Credentials):
        return response.status_not_found()
    async with mongo.MongoContext(request) as mongo_:
        credentials_dict = await mongo_.get(request, MONGODB_CREDENTIALS_COLLECTION, 
                                            mongoattributes={'id': id_},
                                            context=context)
        if credentials_dict is not None:
            view, perms, attr_perms = await _new_credentials_view(context, credentials_dict)
            return await response.get(request, to_dict(view), perms, attr_perms)
        else:
            return response.status_not_found()


@routes.get('/credentialsviews/byname/{name}')
async def get_credentials_view_by_name(request: web.Request) -> web.Response:
    """
    Gets credentials.

    :param request: the HTTP request.
    :return: all credentials.

    ---
    summary: All credentials.
    tags:
        - heaserver-keychain-get-credentials
    parameters:
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    responses:
      '200':
        $ref: '#/components/responses/200'
    """
    sub = request.headers.get(SUB, NONE_USER)
    context = ViewerPermissionContext(sub)
    the_name = request.match_info['name']
    async with mongo.MongoContext(request) as mongo_:
        credentials_dict = await mongo_.get(request, MONGODB_CREDENTIALS_COLLECTION, 
                                            mongoattributes={'name': the_name},
                                            context=context)
        if credentials_dict is not None:
            view, perms, attr_perms = await _new_credentials_view(context, credentials_dict)
            return await response.get(request, to_dict(view), perms, attr_perms)
        else:
            return response.status_not_found()


@routes.post('/credentials')
@routes.post('/credentials/')
async def post_credentials(request: web.Request) -> web.Response:
    """
    Posts the provided credentials.

    :param request: the HTTP request.
    :return: a Response object with a status of Created and the object's URI in the Location header.
    ---
    summary: Credentials creation
    tags:
        - heaserver-keychain-post-credentials
    parameters:
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    requestBody:
      description: A new credentials object.
      required: true
      content:
        application/vnd.collection+json:
          schema:
            type: object
          examples:
            example:
              summary: Credentials
              value: {
                "template": {
                  "data": [
                    {
                      "name": "created",
                      "value": null,
                      "prompt": "created",
                      "display": true
                    },
                    {
                      "name": "derived_by",
                      "value": null,
                      "prompt": "derived_by",
                      "display": true
                    },
                    {
                      "name": "derived_from",
                      "value": [],
                      "prompt": "derived_from",
                      "display": true
                    },
                    {
                      "name": "description",
                      "value": null,
                      "prompt": "description",
                      "display": true
                    },
                    {
                      "name": "display_name",
                      "value": "Joe",
                      "prompt": "display_name",
                      "display": true
                    },
                    {
                      "name": "invites",
                      "value": [],
                      "prompt": "invites",
                      "display": true
                    },
                    {
                      "name": "modified",
                      "value": null,
                      "prompt": "modified",
                      "display": true
                    },
                    {
                      "name": "name",
                      "value": "joe",
                      "prompt": "name",
                      "display": true
                    },
                    {
                      "name": "owner",
                      "value": "system|none",
                      "prompt": "owner",
                      "display": true
                    },
                    {
                      "name": "shares",
                      "value": [],
                      "prompt": "shares",
                      "display": true
                    },
                    {
                      "name": "source",
                      "value": null,
                      "prompt": "source",
                      "display": true
                    },
                    {
                      "name": "version",
                      "value": null,
                      "prompt": "version",
                      "display": true
                    },
                    {
                      "name": "type",
                      "value": "heaobject.keychain.Credentials"
                    }
                  ]
                }
              }
        application/json:
          schema:
            type: object
          examples:
            example:
              summary: Credentials
              value: {
                "created": null,
                "derived_by": null,
                "derived_from": [],
                "description": null,
                "display_name": "Joe",
                "invites": [],
                "modified": null,
                "name": "joe",
                "owner": "system|none",
                "shares": [],
                "source": null,
                "type": "heaobject.keychain.Credentials",
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
    return await mongoservicelib.post(request, MONGODB_CREDENTIALS_COLLECTION, Credentials)


@routes.post('/awscredentials')
@routes.post('/awscredentials/')
async def post_aws_credentials(request: web.Request) -> web.Response:
    """
    Posts the provided AWS credentials.

    :param request: the HTTP request.
    :return: a Response object with a status of Created and the object's URI in the Location header.
    ---
    summary: Credentials creation
    tags:
        - heaserver-keychain-post-credentials
    parameters:
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    requestBody:
      description: A new credentials object.
      required: true
      content:
        application/vnd.collection+json:
          schema:
            type: object
          examples:
            example:
              summary: Credentials
              value: {
                "template": {
                  "data": [
                    {
                      "name": "created",
                      "value": null,
                      "prompt": "created",
                      "display": true
                    },
                    {
                      "name": "derived_by",
                      "value": null,
                      "prompt": "derived_by",
                      "display": true
                    },
                    {
                      "name": "derived_from",
                      "value": [],
                      "prompt": "derived_from",
                      "display": true
                    },
                    {
                      "name": "description",
                      "value": null,
                      "prompt": "description",
                      "display": true
                    },
                    {
                      "name": "display_name",
                      "value": "Joe",
                      "prompt": "display_name",
                      "display": true
                    },
                    {
                      "name": "invites",
                      "value": [],
                      "prompt": "invites",
                      "display": true
                    },
                    {
                      "name": "modified",
                      "value": null,
                      "prompt": "modified",
                      "display": true
                    },
                    {
                      "name": "name",
                      "value": "joe",
                      "prompt": "name",
                      "display": true
                    },
                    {
                      "name": "owner",
                      "value": "system|none",
                      "prompt": "owner",
                      "display": true
                    },
                    {
                      "name": "shares",
                      "value": [],
                      "prompt": "shares",
                      "display": true
                    },
                    {
                      "name": "source",
                      "value": null,
                      "prompt": "source",
                      "display": true
                    },
                    {
                      "name": "version",
                      "value": null,
                      "prompt": "version",
                      "display": true
                    },
                    {
                      "name": "type",
                      "value": "heaobject.keychain.AWSCredentials"
                    }
                  ]
                }
              }
        application/json:
          schema:
            type: object
          examples:
            example:
              summary: Credentials
              value: {
                "created": null,
                "derived_by": null,
                "derived_from": [],
                "description": null,
                "display_name": "Joe",
                "invites": [],
                "modified": null,
                "name": "joe",
                "owner": "system|none",
                "shares": [],
                "source": null,
                "type": "heaobject.keychain.AWSCredentials",
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
    # If managed credentials are being created, then create the credentials in AWS first.
    return await mongoservicelib.post(request, MONGODB_CREDENTIALS_COLLECTION, AWSCredentials, resource_base='awscredentials')


_UniqueAttributes = Literal['OIDC_CLAIM_sub', 'account_id', 'key_lifespan']


@routes.post('/awscredentials/{id}/expirationextender')
async def post_credentials_extender_form(request: web.Request) -> web.Response:
    aws_cred = await _get_aws_cred(request)
    if aws_cred is None:
        return response.status_not_found("Could not get credential")
    if not aws_cred.managed:
        return response.status_bad_request('Cannot extend expiration of non-managed credentials')
    else:
        async with mongo.MongoContext(request) as mongo_client:
            existing_creds = aws_cred
            existing_creds.extend()
            existing_creds.modified = now()
            encryption = get_attribute_encryption_from_request(request)
            result = await mongo_client.update_admin(existing_creds, MONGODB_CREDENTIALS_COLLECTION, 
                                                     encryption=encryption)
            if result is not None and result.matched_count:
                to_delete = []
                for cache_key in request.app[appproperty.HEA_CACHE]:
                    if cache_key[1] == MONGODB_CREDENTIALS_COLLECTION and cache_key[2] in (None, f"id^{request.match_info['id']}"):
                        to_delete.append(cache_key)
                for cache_key in to_delete:
                    request.app[appproperty.HEA_CACHE].pop(cache_key, None)
            return response.status_no_content()


@routes.post('/awscredentials/internal/{id}/presignedurlcredentialscreator')
async def post_presigned_url_credentials_creator(request: web.Request) -> web.Response:
    """
    Posts a template for requesting the generation of managed credentials for a collection of presigned URLs. Returns
    the created credentials' URL in the response's Location header.

    :param request: the HTTP request.
    :return: No Content or Not Found.
    ---
    summary: Managed credentials url
    tags:
        - heaserver-keychain
    parameters:
        - $ref: '#/components/parameters/id'
        - name: Authorization
          type: header
          required: true
          description: The Authorization header value.
          schema:
            type: string
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
        - $ref: '#/components/parameters/Authorization'
    requestBody:
        description: The expiration time for the presigned URL.
        required: true
        content:
            application/vnd.collection+json:
              schema:
                type: object
              examples:
                example:
                  summary: The time before the key expires in hours
                  value:
                    "template": {
                      "data": [
                      {
                        "name": "key_lifespan",
                        "value": 24
                      },{
                        "name": "keys",
                        "value": [
                          'foo/bar/baz',
                          'foo/bar/baz2'
                        ]
                      }]
                    }
            application/json:
              schema:
                type: object
    """
    credential_id = request.match_info['id']
    # request for admin
    auth_header_value = request.headers.get(hdrs.AUTHORIZATION)
    if auth_header_value is None:
        return response.status_bad_request('No Authorization header value')
    req = request.clone(headers={hdrs.CONTENT_TYPE: 'application/json',
                                 SUB: CREDENTIALS_MANAGER_USER,
                                 hdrs.AUTHORIZATION: auth_header_value
                                 })
    try:
        attr_values = await _extract_attribute_values(await request.json())
    except Exception as e:
        return response.status_bad_request(body=f"Invalid template: {e}")
    
    # This code is needed so that the activity description can refer to the credentials display name.
    try:
        aws_cred = await _get_aws_cred(request)
    except Exception as e:
        aws_cred_exception: Exception | None = e
        aws_cred = None
    else:
        aws_cred_exception = None
    async with DesktopObjectActionLifecycle(request=request,
                                            code='hea-create',
                                            description=f'Creating AWS presigned URL credentials from {aws_cred if aws_cred is not None else credential_id}',
                                            activity_cb=publish_desktop_object) as activity:
        if aws_cred is None:
            raise aws_cred_exception if aws_cred_exception is not None else response.status_not_found()
        if aws_cred is not None and aws_cred.role is None:
            raise response.status_bad_request('Cannot create managed credentials from these credentials: No role is defined')
        admin_cred = await request.app[HEA_DB].elevate_privileges(request, aws_cred)
        async with aws.IAMClientContext(request=req, credentials=admin_cred) as iam_admin_client:
            try:
                aws_cred = await _get_presigned_url_user_credentials(request, aws_cred, iam_admin_client, 
                                                           key_lifespan=attr_values['key_lifespan'],
                                                           keys=attr_values['keys'],
                                                           bucket=attr_values['bucket'])
                _logger.debug("aws_cred ready to post: %r", aws_cred)
            except KeyError as ke:
                raise response.status_bad_request(f"Managed credentials were not created: {ke}") from ke
            except _BadRequestException as e:
                raise response.status_bad_request(f"Managed credentials were not created: {e}") from e
        return await response.post(request, aws_cred.id, 'awscredentials')


@routes.post('/awscredentials/{id}/climanagedcredentialscreator')
async def post_aws_credentials_form(request: web.Request) -> web.Response:
    """
    Posts a template for requesting the generation of managed credentials, and returns the managed credentials as
    a ClipboardData object. The request will fail if the given credentials are not temporary.

    :param request: the HTTP request.
    :return: No Content or Not Found.
    ---
    summary: Managed credentials url
    tags:
        - heaserver-keychain
    parameters:
        - name: id
          in: path
          required: true
          description: The id of the credentials.
          schema:
            type: string
          examples:
            example:
              summary: A credential id
              value: 666f6f2d6261722d71757578
        - $ref: '#/components/parameters/id'
        - name uniqueattribute
          in: query
          required: false
          description: Fail if the specified form template attributes are not unique. The sum of the lengths of the 
          attribute values may not be longer than 58 characters.
          schema:
            type: array
          examples:
            example:
              summary: A unique attribute
              value: 
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
        - $ref: '#/components/parameters/Authorization'
    requestBody:
        description: The expiration time for the presigned URL.
        required: true
        content:
            application/vnd.collection+json:
              schema:
                type: object
              examples:
                example:
                  summary: The time before the key expires in hours
                  value: {
                    "template": {
                      "data": [
                      {
                        "name": "key_lifespan",
                        "value": 72
                      }]
                    }
                  }
            application/json:
              schema:
                type: object
              examples:
                example:
                  summary: The time before the key expires in hours
                  value: {
                    "key_lifespan": 72
                  }
    responses:
      '200':
        $ref: '#/components/responses/200'
      '403':
        $ref: '#/components/responses/403'
      '404':
        $ref: '#/components/responses/404'
    """
    credential_id = request.match_info.get('id', None)
    uniqueattributes: dict[Literal['OIDC_CLAIM_sub', 'account_id', 'key_lifespan'], None] = {'OIDC_CLAIM_sub': None, 'account_id': None, 'key_lifespan': None}
    # request for admin
    auth_header_value = request.headers.get(hdrs.AUTHORIZATION)
    if auth_header_value is None:
        return response.status_bad_request('No Authorization header value')
    req = request.clone(headers={hdrs.CONTENT_TYPE: 'application/json',
                                 SUB: CREDENTIALS_MANAGER_USER,
                                 hdrs.AUTHORIZATION: auth_header_value
                                 })
    if not credential_id:
        return response.status_bad_request(body="credential id is required")

    try:
        attr_values = await _extract_attribute_values(await request.json())
    except Exception as e:
        return response.status_bad_request(body=f"Invalid template: {e}")
    
    # This code is needed so that the activity description can refer to the credentials display name.
    try:
        aws_cred = await _get_aws_cred(request)
    except Exception as e:
        aws_cred_exception: Exception | None = e
        aws_cred = None
    else:
        aws_cred_exception = None

    async with DesktopObjectActionLifecycle(request=request,
                                            code='hea-create',
                                            description=f'Creating Managed AWS CLI credentials from {aws_cred.display_name if aws_cred is not None else credential_id}',
                                            activity_cb=publish_desktop_object) as activity:
        if aws_cred is None:
            raise aws_cred_exception if aws_cred_exception is not None else response.status_not_found()
        if aws_cred is not None:
            if aws_cred.role is None:
                raise response.status_bad_request('Cannot create managed credentials from these credentials: No role is defined')
            if not aws_cred.temporary:
                raise response.status_bad_request('Cannot create managed credentials from these credentials: They are not temporary')
        admin_cred = await request.app[HEA_DB].elevate_privileges(request, aws_cred)
        async with aws.IAMClientContext(request=req, credentials=admin_cred) as iam_admin_client:
            try:
                aws_cred = await _get_managed_user_credentials(request, aws_cred, iam_admin_client, 
                                                               uniqueattributes, **attr_values)
                _logger.debug("aws_cred ready to post: %r", aws_cred)
            except _BadRequestException as e:
                raise response.status_bad_request(f"Managed credentials were not created: {e}") from e
        data = ClipboardData()
        data.mime_type = 'text/plain;encoding=utf-8'
        data.created = now()
        data.display_name = f'AWS CLI credentials file for {aws_cred.display_name}'
        data.data = aws_cred.to_credentials_file_str()
        return await response.get(request, to_dict(data))


@routes.post('/awscredentials/{id}/clicredentialsfile')
async def post_aws_managed_credentials_form(request: web.Request) -> web.Response:
    """
    Posts a template for requesting previously generated credentials in file format, returned as a ClipboardData 
    object.

    :param request: the HTTP request.
    :return: 200 status code and the ClipboardData object in the response body.
    ---
    summary: Managed credential url
    tags:
        - heaserver-keychain
    parameters:
        - name: id
          in: path
          required: true
          description: The id of the credential.
          schema:
            type: string
          examples:
            example:
              summary: A credential id
              value: 666f6f2d6261722d71757578
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
    aws_cred = await _get_aws_cred(request)
    if aws_cred is None:
        return response.status_not_found("Could not get credentials")
    data = ClipboardData()
    data.mime_type = 'text/plain;encoding=utf-8'
    data.created = now()
    data.display_name = f'AWS CLI credentials file for {aws_cred.display_name}'
    data.data = aws_cred.to_credentials_file_str()
    return await response.get(request, to_dict(data))


@routes.put('/credentials/{id}')
async def put_credentials(request: web.Request) -> web.Response:
    """
    Updates the credentials with the specified id.
    :param request: the HTTP request.
    :return: a Response object with a status of No Content or Not Found.
    ---
    summary: Credentials updates
    tags:
        - heaserver-keychain-put-credentials
    parameters:
        - $ref: '#/components/parameters/id'
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    requestBody:
      description: An updated credentials object.
      required: true
      content:
        application/vnd.collection+json:
          schema:
            type: object
          examples:
            example:
              summary: Credentials
              value: {
                "template": {
                  "data": [
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
                      "name": "name",
                      "value": "reximus"
                    },
                    {
                      "name": "description",
                      "value": null
                    },
                    {
                      "name": "display_name",
                      "value": "Reximus Max"
                    },
                    {
                      "name": "invites",
                      "value": []
                    },
                    {
                      "name": "modified",
                      "value": null
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
                      "name": "id",
                      "value": "666f6f2d6261722d71757578"
                    },
                    {
                      "name": "type",
                      "value": "heaobject.keychain.Credentials"
                    }
                  ]
                }
              }
        application/json:
          schema:
            type: object
          examples:
            example:
              summary: An updated credentials object
              value: {
                "created": None,
                "derived_by": None,
                "derived_from": [],
                "name": "reximus",
                "description": None,
                "display_name": "Reximus Max",
                "invites": [],
                "modified": None,
                "owner": NONE_USER,
                "shares": [],
                "source": None,
                "type": "heaobject.keychain.Credentials",
                "version": None,
                "id": "666f6f2d6261722d71757578"
              }
    responses:
      '204':
        $ref: '#/components/responses/204'
      '400':
        $ref: '#/components/responses/400'
      '404':
        $ref: '#/components/responses/404'
    """
    return await mongoservicelib.put(request, MONGODB_CREDENTIALS_COLLECTION, Credentials)


@routes.put('/awscredentials/{id}')
async def put_aws_credentials(request: web.Request) -> web.Response:
    """
    Updates the credentials with the specified id.
    :param request: the HTTP request.
    :return: a Response object with a status of No Content or Not Found.
    ---
    summary: Credentials updates
    tags:
        - heaserver-keychain-put-credentials
    parameters:
        - $ref: '#/components/parameters/id'
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    requestBody:
      description: An updated credentials object.
      required: true
      content:
        application/vnd.collection+json:
          schema:
            type: object
          examples:
            example:
              summary: Credentials
              value: {
                "template": {
                  "data": [
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
                      "name": "name",
                      "value": "reximus"
                    },
                    {
                      "name": "description",
                      "value": null
                    },
                    {
                      "name": "display_name",
                      "value": "Reximus Max"
                    },
                    {
                      "name": "invites",
                      "value": []
                    },
                    {
                      "name": "modified",
                      "value": null
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
                      "name": "id",
                      "value": "666f6f2d6261722d71757578"
                    },
                    {
                      "name": "type",
                      "value": "heaobject.keychain.AWSCredentials"
                    }
                  ]
                }
              }
        application/json:
          schema:
            type: object
          examples:
            example:
              summary: An updated credentials object
              value: {
                "created": None,
                "derived_by": None,
                "derived_from": [],
                "name": "reximus",
                "description": None,
                "display_name": "Reximus Max",
                "invites": [],
                "modified": None,
                "owner": NONE_USER,
                "shares": [],
                "source": None,
                "type": "heaobject.keychain.AWSCredentials",
                "version": None,
                "id": "666f6f2d6261722d71757578"
              }
    responses:
      '204':
        $ref: '#/components/responses/204'
      '400':
        $ref: '#/components/responses/400'
      '404':
        $ref: '#/components/responses/404'
    """
    # If managed credentials are being updated, we need to check if the expiration datetime is being changed. If so, then
    # update the managed credentials on AWS with the new expiration datetime.
    async def _update_managed_aws_credentials(request: web.Request, aws_cred: AWSCredentials):
        old_aws_cred = await mongoservicelib.get_desktop_object(request, MONGODB_CREDENTIALS_COLLECTION, type_=AWSCredentials)
        if old_aws_cred is not None:
            if aws_cred.managed and not old_aws_cred.managed:  # Newly managed, so create the AWS user/creds.
                pass
            elif old_aws_cred.managed and not aws_cred.managed:  # Not managed anymore, so delete the AWS user/creds.
                pass
    return await mongoservicelib.put(request, MONGODB_CREDENTIALS_COLLECTION, AWSCredentials,
                                     pre_save_hook=_update_managed_aws_credentials)


@routes.delete('/credentials/{id}')
async def delete_credentials(request: web.Request) -> web.Response:
    """
    Deletes the credentials with the specified id.
    
    :param request: the HTTP request.
    :return: No Content or Not Found.
    ---
    summary: Credentials deletion
    tags:
        - heaserver-keychain-delete-credentials
    parameters:
        - $ref: '#/components/parameters/id'
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    responses:
      '204':
        $ref: '#/components/responses/204'
      '404':
        $ref: '#/components/responses/404'
    """
    cred = await _get_cred(request)
    id_ = request.match_info['id']
    async with DesktopObjectActionLifecycle(request=request,
                                            code='hea-delete',
                                            description=f"Deleting credential {cred.display_name if cred else 'with id ' + id_}",
                                            activity_cb=publish_desktop_object) as activity:
        activity.old_object_id = id_
        activity.old_object_type_name = Credentials.get_type_name()
        activity.old_object_uri = f'credentials/{id_}'
        if cred is None:
            raise response.status_not_found()
        resp = await mongoservicelib.delete(request, MONGODB_CREDENTIALS_COLLECTION)  # we do this first to make sure the user has delete permissions.
        if resp.status != 204:
            activity.status = Status.FAILED
        return resp


@routes.delete('/awscredentials/{id}')
async def delete_awscredentials(request: web.Request) -> web.Response:
    """
    Deletes the AWS credentials with the specified id, as well as any AWS policies and users that were created for it.
    
    :param request: the HTTP request.
    :return: No Content or Not Found.
    ---
    summary: AWS Credentials deletion
    tags:
        - heaserver-keychain-delete-awscredentials
    parameters:
        - $ref: '#/components/parameters/id'
        - $ref: '#/components/parameters/OIDC_CLAIM_sub'
    responses:
      '204':
        $ref: '#/components/responses/204'
      '404':
        $ref: '#/components/responses/404'
    """
    id_ = request.match_info['id']

    # This code is needed so that the activity description can refer to the credentials display name.
    try:
        aws_cred = await _get_aws_cred(request)
    except Exception as e:
        aws_cred_exception: Exception | None = e
        aws_cred = None
    else:
        aws_cred_exception = None
    async with DesktopObjectActionLifecycle(request=request,
                                            code='hea-delete',
                                            description=f"Deleting AWS credential {aws_cred.display_name if aws_cred else 'with id ' + id_}",
                                            activity_cb=publish_desktop_object) as activity:
        activity.old_object_id = id_
        activity.old_object_type_name = AWSCredentials.get_type_name()
        activity.old_object_uri = f'awscredentials/{id_}'

        if aws_cred is None:
            raise aws_cred_exception if aws_cred_exception is not None else response.status_not_found()
        
        resp = await mongoservicelib.delete(request, MONGODB_CREDENTIALS_COLLECTION)

        if resp.status != 204:
            if isinstance(resp, web.HTTPError):
                raise resp
            else:
                raise response.status_internal_error()

        if aws_cred.managed:
            try:
                await _cleanup_deleted_managed_aws_credential(request, aws_cred)
            except (ValueError, ClientError) as e:
                raise response.status_bad_request(f"Unable to delete AWS managed credentials: {e}")
        
        return response.status_no_content()


async def _cleanup_deleted_managed_aws_credential(request: web.Request, aws_cred: AWSCredentials):
    """
    Deletes all the managed credentials that were generated using the AWS credentials with the given ID. The passed in
    credentials must have non-None aws_role_name and name attributes. This function involves privilege elevation. This 
    function attempts to cleanup any partial user and access key information that may have been created in AWS IAM.

    :param request: the HTTP request (required).
    :param aws_cred: a managed AWS credentials object (required).
    :raises ValueError: if an error occurred getting elevated privileges. 
    :raises ClientError: if an error occurred contacting AWS. NoSuchEntity errors are not raised, as they may occur 
    when the information to delete has been previously deleted or is otherwise missing.
    """
    assert aws_cred.aws_role_name is not None, 'aws_cred cannot have a None role'
    assert aws_cred.name is not None, 'aws_cred.name cannot be None'

    admin_cred = await request.app[HEA_DB].elevate_privileges(request, aws_cred)
    async with aws.IAMClientContext(request=request, credentials=admin_cred) as iam_admin_client:
        async with _managed_credentials_lock:
            try:
                r_policies = await asyncio.to_thread(iam_admin_client.list_attached_role_policies,
                                                     RoleName=aws_cred.aws_role_name)
                await _delete_managed_user(iam_client=iam_admin_client, username=aws_cred.name, policies=r_policies)
            except ClientError as e:
                if aws.client_error_code(e) != aws.CLIENT_ERROR_NO_SUCH_ENTITY:
                    raise e


async def _create_or_get_managed_user(iam_client: IAMClient, username: str,
                                policies: ListAttachedRolePoliciesResponseTypeDef | None = None,
                                inline_policy: dict | None = None):
    """
    Creates a managed user in AWS IAM with the attached user policies, and creates an access key.
    
    :param iam_client: the IAM client.
    :param username: the username of the managed user. Must be 20-64 characters long.
    :param policies: the policies attached to the managed user.
    :param inline_policy:
    :return: the access key response.
    :raises ClientError: if an error occurred creating the user, attaching the policies, or creating an access key.
    :raise ValueError: if the user already exists but has no access key.
    """
    use_inline = inline_policy is not None

    # Initialize for MyPy
    inline_policy_doc: dict | None = None
    legacy_policies: ListAttachedRolePoliciesResponseTypeDef | None = None

    # Normalize policy input
    if use_inline:
        inline_policy_doc = inline_policy
    else:
        if policies is None:
            raise ValueError("Policies must be provided when inline_policy is not used")
        legacy_policies = policies   # <-- no type annotation here

    # Create / recreate loop
    while True:
        try:
            await asyncio.to_thread(iam_client.create_user, UserName=username)
            break
        except ClientError as e:
            if aws.client_error_code(e) == "EntityAlreadyExists":
                await _delete_managed_user(iam_client, username, policies)
            else:
                raise

    # Apply policies
    if use_inline:
        # inline_policy_doc is guaranteed non-None in this branch
        await asyncio.to_thread(
            iam_client.put_user_policy,
            UserName=username,
            PolicyName="PresignedURLAccess",
            PolicyDocument=json_dumps(inline_policy_doc),
        )
    else:
        # legacy_policies is guaranteed non-None in this branch
        assert legacy_policies is not None
        for policy in legacy_policies["AttachedPolicies"]:
                await asyncio.to_thread(
                    iam_client.attach_user_policy,
                    UserName=username,
                    PolicyArn=policy["PolicyArn"],
                )

    # Create and return access key
    return (
        await asyncio.to_thread(iam_client.create_access_key, UserName=username)
    )["AccessKey"]

async def _delete_managed_user(iam_client: IAMClient, username: str,
                               policies: ListAttachedRolePoliciesResponseTypeDef | None = None):
    """
    Deletes the managed user in AWS IAM.
    
    :param iam_client: the IAM client.
    :param username: the username of the managed user. Must be 20-64 characters long.
    :param policies: the policies attached to the managed user.
    :return: the response from the delete user operation.
    """
    if policies:
        for policy in policies['AttachedPolicies']:
            try:
                await asyncio.to_thread(iam_client.detach_user_policy, UserName=username, PolicyArn=policy['PolicyArn'])
            except ClientError as e:
                if aws.client_error_code(e) != aws.CLIENT_ERROR_NO_SUCH_ENTITY:
                    raise e
    for policy_name in (await asyncio.to_thread(iam_client.list_user_policies, UserName=username))['PolicyNames']:
        await asyncio.to_thread(iam_client.delete_user_policy, UserName=username, PolicyName=policy_name)
    access_keys = (await asyncio.to_thread(iam_client.list_access_keys, UserName=username))['AccessKeyMetadata']
    for metadata in access_keys:
        await asyncio.to_thread(iam_client.delete_access_key, UserName=username, AccessKeyId=metadata['AccessKeyId'])
    await asyncio.to_thread(iam_client.delete_user, UserName=username)


_managed_credentials_lock = asyncio.Lock()

async def _delete_managed_coro(app: web.Application):
    _logger.debug("entering _delete_managed_coro")
    session = app[appproperty.HEA_CLIENT_SESSION]
    if not session:
        _logger.debug("session does not exist ")
        return

    headers_ = {SUB: CREDENTIALS_MANAGER_USER}
    component = await client.get_component_by_name(app, 'heaserver-keychain', client_session=session)
    assert component is not None, 'registry entry for heaserver-keychain not found'
    assert component.base_url is not None, 'registry entry for heaserver-keychain has no base_url'
    async with _managed_credentials_lock:
        coros_to_gather = []
        async for cred in client.get_all(app=app, url=URL(component.base_url) / 'awscredentials',
                                        type_=AWSCredentials, headers=headers_):
            if cred.managed and cred.has_expired():
                assert cred.id is not None, 'exp_cred.id cannot be None'
                coros_to_gather.append(client.delete(app, URL(component.base_url) / 'awscredentials' / cred.id, headers_))
        await asyncio.gather(*coros_to_gather)


async def _get_aws_cred(request: web.Request) -> AWSCredentials | None:
    """
    Retrieves the AWS credentials from the database, returning None if the credentials could not be found.

    :param request: the HTTP request.
    :return: the AWS credentials or None.
    """
    try:
        cred_dict = await mongoservicelib.get_dict(request, MONGODB_CREDENTIALS_COLLECTION)
        if cred_dict is None:
            return None
        aws_cred = AWSCredentials()
        aws_cred.from_dict(cred_dict)
        return aws_cred
    except DeserializeException:
        return None


async def _get_cred(request: web.Request) -> Credentials | None:
    """
    Retrieves the credentials from the database, returning None if the credentials could not be found.

    :param request: the HTTP request.
    :return: the credentials or None.
    """
    try:
        cred_dict = await mongoservicelib.get_dict(request, MONGODB_CREDENTIALS_COLLECTION)
        if cred_dict is None:
            return None
        cred = Credentials()
        cred.from_dict(cred_dict)
        return cred
    except DeserializeException:
        return None


async def _extract_attribute_values(body: dict[str, Any]) -> dict[str, Any]:
    """
    Extracts the target URL and expiration time in hours for a presigned URL request. It un-escapes them as needed.

    :param body: a Collection+JSON template dict.
    :return: a three-tuple containing the target URL and the un-escaped expiration time in hours.
    :raises web.HTTPBadRequest: if the given body is invalid.
    """
    try:
        return {item['name']: item['value'] for item in body['template']['data']}
    except (KeyError, ValueError) as e:
        raise web.HTTPBadRequest(body=f'Invalid template: {e}') from e


async def _get_managed_user_credentials(request: web.Request, aws_cred: AWSCredentials, iam_admin_client: IAMClient,
                                       unique_attributes: dict[_UniqueAttributes, None] | None = None,
                                       OIDC_CLAIM_sub: str | None = None, 
                                       account_id: str | None = None, key_lifespan: str = '12') -> AWSCredentials:
    """
    Gets managed user credentials for the given user for use with AWS CLI, creating the credentials if necessary. The 
    name of the credentials is constructed from the sub, the given credentials' account id, and the given unique_id. If 
    the unique_id is None, a UUID will be generated for the unique value.

    :param request: the HTTP request.
    :param aws_cred: the user's credentials.
    :param iam_admin_client: an IAM client with elevated privileges.
    :param unique_attributes: which subset of sub, account_id, and key_lifespan to use for checking for managed
    credentials uniqueness. If empty, no uniqueness check is performed. If populated, this function will raise
    _BadRequestException if a managed credentials object with the same unique values already exists.
    :return: the managed user credentials.
    :raises _BadRequestException: if an error occurred creating the managed user credentials due to user input.
    """
    parameters = {k: v for k, v in locals().items() if k in unique_attributes.keys()} if unique_attributes is not None else None
    sub_from_request = request.headers.get(SUB, NONE_USER)
    key_lifespan_ = int(key_lifespan)
    if key_lifespan_ not in (12, 24, 36, 48, 72):
        raise _BadRequestException('Key lifespan must be one of 12, 24, 36, 48, or 72')
    
    if not parameters:
        unique_value_ = f'auto_{uuid.uuid1()}'
    else:
        if OIDC_CLAIM_sub is not None and OIDC_CLAIM_sub != sub_from_request:
            raise _BadRequestException('sub must be the requesting username')
        unique_value_ = 'man_' + '_'.join(parameters.values())
        # unique_value_ can be max 64 characters long because AWS usernames can be max 64 characters long.
        assert len(unique_value_) <= 64, 'The sum of the lengths of the unique attribute values is too long'
    return await _get_managed_user_credentials_0(request, sub_from_request, key_lifespan_, aws_cred, iam_admin_client, unique_value_,
                                                  f"{aws_cred.display_name} Managed {key_lifespan}hr")


def _build_presigned_url_inline_policy(bucket: str | None, keys: Collection[str] | None) -> dict:
    if not bucket or not keys:
        raise ValueError("Bucket and keys must be provided to build an inline policy")


    resources = [
        f"arn:aws:s3:::{bucket}/{key}{'*'if is_folder(key) else ''}"
        for key in keys
    ]

    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "PresignedURLAccess",
                "Effect": "Allow",
                "Action": ["s3:GetObject", "s3:GetObjectVersion"],
                "Resource": resources
            }
        ]
    }


async def _get_presigned_url_user_credentials(request: web.Request, aws_cred: AWSCredentials, 
                                              iam_admin_client: IAMClient, key_lifespan: str = '24',
                                              bucket: str | None = None,
                                              keys: Collection[str] | None = None,
                                              ) -> AWSCredentials:
    """
    Gets managed user credentials for the given user for use with AWS CLI, creating the credentials if necessary. The 
    name of the credentials is constructed from the sub, the given credentials' account id, and the given unique_id. If 
    the unique_id is None, a UUID will be generated for the unique value.

    :param request: the HTTP request.
    :param aws_cred: the user's credentials.
    :param iam_admin_client: an IAM client with elevated privileges.
    :param key_lifespan: the requested lifespan in hours (up to one week). Default is 24 hours.
    :param bucket: the bucket to use in constructing arn
    :param keys: the keys of the S3 objects in the presigned URL request. Used for setting the credentials' display 
    name.
    :return: the managed user credentials.
    :raises _BadRequestException: if an error occurred creating the user credentials due to user input.
    """
    sub = request.headers.get(SUB, NONE_USER)
    key_lifespan_ = int(key_lifespan)
    if key_lifespan_ not in (24, 72, 168):
        raise _BadRequestException('Key lifespan must be one of 24, 72, 168')
    if keys is None:
        keys_str = ''
    elif len(keys) == 1:
        keys_str = f' for {display_name(next(iter(keys)))}'
    else:
        keys_str = f's for {display_name(next(iter(keys)))} and More'

    usr_policy = _build_presigned_url_inline_policy(bucket=bucket, keys=keys)
    return await _get_managed_user_credentials_0(request, sub, key_lifespan_, aws_cred, iam_admin_client, 
                                                 f'presignedurl_{uuid.uuid1()}', 
                                                 f"{aws_cred.display_name} Presigned URL{keys_str} {key_lifespan_}hr",
                                                 inline_policy=usr_policy,
                                                 )




async def _get_managed_user_credentials_0(request: web.Request, sub: str, key_lifespan: int, aws_cred: AWSCredentials, 
                                          iam_admin_client: IAMClient, name: str, display_name: str,
                                          inline_policy: dict | None = None, ) -> AWSCredentials:
    """
    Gets managed user credentials for the given user, creating credentials if necessary. If you supply managed
    credentials in the aws_cred argument, this function returns a copy of the credentials back. If you supply temporary
    credentials, this function will create managed credentials from them. If you supply non-managed, non-temporary
    credentials, this function will raise an error.

    :param request: the HTTP request.
    :param sub: the requesting username.
    :param key_lifespan: the requested lifespan in hours (up to 72).
    :param aws_cred: the user's credentials.
    :param iam_admin_client: an IAM client with elevated privileges.
    :param name: the name to use for the managed credentials. Max 64 characters long.
    :param display_name: the display name to use for the managed credentials.
    :return: the managed user credentials, with its id set from when it was persisted.
    :raises _BadRequestException: if an error occurred creating the managed user credentials due to user input.
    """
    if len(name) > 64:
        raise ValueError('name is too long; can be at most 64 characters in length')
    if not aws_cred.temporary:
        raise _BadRequestException('These credentials are not temporary')

    async with mongo.MongoContext(request) as mongo_client:
        async with _managed_credentials_lock:
            aws_cred_: AWSCredentials = AWSCredentials()
            try:
                role_name = aws_cred.aws_role_name
                if not role_name:
                    raise _BadRequestException('No role is defined')

                loop = asyncio.get_running_loop()
                context = mongo_client.get_default_permission_context(request)

                #Load existing managed credentials (if any)
                aws_cred_old = await mongo_client.get(request, MONGODB_CREDENTIALS_COLLECTION,
                    mongoattributes={'name': name},
                    context=context
                )

                # If we have an inline_policy (presigned URL case),
                # we ALWAYS enforce our own policy, regardless of aws_cred_old.
                share: Share = ShareImpl()
                if inline_policy is not None:
                    access_key = await _create_or_get_managed_user(iam_client=iam_admin_client,username=name,
                                                                   inline_policy=inline_policy)

                    #If the user existed, we STILL overwrite all fields
                    aws_cred_.account = access_key['AccessKeyId']
                    aws_cred_.password = access_key['SecretAccessKey']
                    aws_cred_.created = access_key['CreateDate']
                    aws_cred_.modified = access_key['CreateDate']
                    aws_cred_.session_token = None
                    aws_cred_.temporary = False
                    aws_cred_.managed = True
                    aws_cred_.display_name = display_name
                    aws_cred_.name = name
                    aws_cred_.owner = CREDENTIALS_MANAGER_USER
                    aws_cred_.role = aws_cred.role
                    aws_cred_.lifespan = timedelta(hours=key_lifespan).total_seconds()

                    share.user = sub
                    share.permissions = [Permission.VIEWER, Permission.DELETER]
                    aws_cred_.add_user_share(share)

                else:
                    # If no inline policy, use role policies (legacy path)
                    if aws_cred_old is None:
                        r_policies = await loop.run_in_executor(None,
                            partial(
                                iam_admin_client.list_attached_role_policies,
                                RoleName=role_name,
                            ),
                        )
                        access_key = await _create_or_get_managed_user(iam_client=iam_admin_client,username=name,policies=r_policies,)
                        aws_cred_.account = access_key['AccessKeyId']
                        aws_cred_.password = access_key['SecretAccessKey']
                        aws_cred_.created = access_key['CreateDate']
                        aws_cred_.modified = access_key['CreateDate']
                        aws_cred_.session_token = None
                        aws_cred_.temporary = False
                        aws_cred_.managed = True
                        aws_cred_.display_name = display_name
                        aws_cred_.name = name
                        aws_cred_.role = None
                        share.user = sub
                        share.permissions = [Permission.VIEWER, Permission.DELETER]
                        aws_cred_.add_user_share(share)

                    else:
                        #Existing managed credentials → reuse normally
                        aws_cred_.from_dict(aws_cred_old)

                # 🔵 Normalize timestamps, propagate shares, etc.
                aws_cred_.extend()
                encryption = get_attribute_encryption_from_request(request)
                if (id_ := await mongo_client.upsert_admin(aws_cred_, MONGODB_CREDENTIALS_COLLECTION, 
                                                           mongoattributes={'name': name},
                                                           encryption=encryption)) is None:
                    raise ValueError('Failed to create managed credentials object in the database')
                to_delete = []
                for cache_key in request.app[appproperty.HEA_CACHE]:
                    if cache_key[1] == MONGODB_CREDENTIALS_COLLECTION and cache_key[2] is None:
                        to_delete.append(cache_key)
                for cache_key in to_delete:
                    request.app[appproperty.HEA_CACHE].pop(cache_key, None)
                aws_cred_.id = id_
            except ClientError as ce:
                raise ValueError(str(ce)) from ce
            return aws_cred_



async def _get_aws_credentials(request: web.Request) -> web.Response:
    obj = await mongoservicelib.get_desktop_object(request, MONGODB_CREDENTIALS_COLLECTION, type_=AWSCredentials)
    if obj is not None:
        sub = request.headers.get(SUB, NONE_USER)
        context = PermissionContext(sub)
        perms = await obj.get_permissions(context)
        attr_perms = await obj.get_all_attribute_permissions(context)
        obj_dict = to_dict(obj)
        return await response.get(request, obj_dict, permissions=perms, attribute_permissions=attr_perms)
    else:
        return response.status_not_found()


class _BadRequestException(Exception):
    pass


async def _new_credentials_view(context: PermissionContext, credentials_dict: dict) -> tuple[CredentialsView, list[Permission], dict[str, list[Permission]]]:
    aws_credentials_type_name = AWSCredentials.get_type_name()
    credentials_type_name = Credentials.get_type_name()
    view: CredentialsView = CredentialsView()
    id_ = credentials_dict['id']
    view.actual_object_id = id_
    view.actual_object_type_name = credentials_dict['type']
    if (display_name := credentials_dict.get('display_name')) is not None:
        view.display_name = display_name
    match credentials_dict_type_name := credentials_dict['type']:
        case aws_credentials_type_name if credentials_dict_type_name == aws_credentials_type_name:
            view.actual_object_uri = f'awscredentials/{id_}'
        case credentials_type_name if credentials_dict_type_name == credentials_type_name:
            view.actual_object_uri = f'credentials/{id_}'
        case _:
            raise ValueError(f'Unexpected desktop object type {credentials_dict_type_name}')
    view.id = f'{credentials_dict_type_name}^{id_}'
    share, attr_perms = await asyncio.gather(view.get_permissions_as_share(context),
                                                 view.get_all_attribute_permissions(context))
    view.add_user_share(share)
    perms = share.permissions
    attr_perms = attr_perms
    return view, perms, attr_perms


def start_with(config: Configuration) -> None:
    start(package_name='heaserver-keychain', db=aws.S3WithMongoManager,
          wstl_builder_factory=builder_factory(__package__),
          cleanup_ctx=[publisher_cleanup_context_factory(config),
                       scheduled_cleanup_ctx_factory(coro=_delete_managed_coro, delay=3600)],
          config=config)
