# coding: utf-8

"""
    Meshcapade Me API

    Welcome to the age of Avatars, introducing the Meshcapade Me API. The no-friction avatar-creation platform for all your avatar needs. Create accurate digital doubles from any source of data in a unified 3D body format for every industry. Built on our <a href=\"https://meshcapade.com/SMPL\" target=\"_blank\">patented avatar</a> technology, our API allows you to create and edit avatars from images, videos, measurements, scans, and more. # Introduction The Meshcapade Me API is a RESTful API that allows you to create and edit avatars from images, measurements, scans, and more. All API replies adhere to the  <a href=\"https://jsonapi.org/format/\" target=\"_blank\">JSON:API</a> schema guidelines. Currently the API is in beta and is subject to change. Thus, not all ways to create avatars are available yet. We are working hard to add more ways to create avatars and will update this documentation accordingly. The API allows you to create avatars from: </br> - <a href=\"#post-/avatars/create/from-images\" target=\"_blank\">images</a> </br> - <a href=\"#post-/avatars/create/from-video\" target=\"_blank\">video</a> </br> - <a href=\"#post-/avatars/create/from-scans\" target=\"_blank\">3D scans</a> </br> - <a href=\"#post-/avatars/create/from-measurements\" target=\"_blank\">measurements</a> </br> # Quickstart To get started, sign up for a free account at <a href=\"https://me.meshcapade.com\" target=\"_blank\">me.meshcapade.com</a></br> We recommend using our <a href=\"https://www.postman.com/downloads/\" target=\"_blank\">Postman</a> collection to conveniently explore the API. </br> <div style=\"margin-top: 16px;\"><a href=\"https://www.postman.com/cloudy-meadow-883625/workspace/meshcapade/overview\"><img src=\"https://run.pstmn.io/button.svg\" alt=\"Run in Postman\"></a></div></br>  # How-To <a href=\"https://medium.com/meshcapade/streamline-avatar-creation-with-meshcapade-me-api-from-one-image-to-an-accurate-avatar-in-seconds-b8ca4f15b9a8\" target=\"_blank\">Create an avatar from a single image (Medium)</a> </br> <a href=\"https://medium.com/meshcapade/measurements-meet-imagination-creating-accurate-3d-avatars-with-meshcapades-api-9a6ec5029793\" target=\"_blank\">Create an avatar from measurements (Medium)</a> # API Categories The API is organized into the following main categories: - <strong>Assets</strong>: Endpoint for listing assets of multiple types. - <strong>Avatars</strong>: Endpoints for listing, downloading, and deleting avatars. - <strong>Mesh</strong>: Endpoints for listing, downloading, and deleting exported meshes. - <strong>Images</strong>: Endpoints for listing, uploading, and deleting images related to avatars. - <strong>Create Avatar from images</strong>: Endpoints to initiate and complete avatar creation from images. - <strong>Create Avatar from measurements</strong>: Endpoint to initiate avatar creation from body measurements. - <strong>Create Avatar from scans</strong>: Endpoints to initiate and complete avatar creation from 3d body scans. - <strong>Create Avatar from betas</strong>: Endpoint to create an avatar from SMPL based beta shape parameters. # Error codes When something goes wrong, the API replies with an additional error code  - `asset_not_found` The requested asset either does not exist, or is not owned by the user (404)  </br> - `too_many_images` The image limit that can be uploaded for avatars from images as been exceeded. (400) </br> - `already_started` A process that already has been requested cannot be started again. (400) </br> - `no_images`  [POST /avatars/create/from-images](#post-/avatars/create/from-images) can only be started with at least one image uploaded  (400) </br> - `inputs_not_ready` Running `/avatars/create/xxxx` endpoint require the inputs to be uploaded (400) </br> - `uuid_invalid_format` Asset ID is in a non-UUID format (400) </br> - ` missing_parameters` Not all required parameters have been supplied for the request (400) </br> - `unauthorized` Trying to access an asset the user does not own, or endpoints that the user is not authorized to call (400) </br> - `too_many_builds` User processing rate has been exceeded. Only one computation heavy process can be started at a time (429) </br> - `asset_not_ready` Cannot call request on an asset which is not in a READY state (400) </br>  # Integration When integrating with our API, you may encounter Cross-Origin Resource Sharing (CORS) issues during deployment. </br> For security reasons, our API does not support direct communication from your frontend. </br> Instead, we recommend that you connect to api.meshcapade through your own backend server. </br> This approach not only mitigates CORS-related challenges but also enhances the overall security of your application. </br> By handling API requests server-side, you can ensure smoother and safer integration. </br> If you encounter any issues during integration, please reach out to us at: support@meshcapade.com </br>  # noqa: E501

    The version of the OpenAPI document: v1.24
    Contact: support@meshcapade.com
    Generated by OpenAPI Generator (https://openapi-generator.tech)

    Do not edit the class manually.
"""


import re  # noqa: F401
import io
import warnings

from pydantic import validate_arguments, ValidationError
from typing_extensions import Annotated

from typing_extensions import Annotated
from pydantic import Field, StrictStr, conint

from typing import Optional

from openapi_client.models.docschemas_doc_base_jsonapi_response import DocschemasDocBaseJSONAPIResponse
from openapi_client.models.docschemas_doc_base_mesh_no_includes_response import DocschemasDocBaseMeshNoIncludesResponse
from openapi_client.models.docschemas_doc_base_single_jsonapi_response import DocschemasDocBaseSingleJSONAPIResponse
from openapi_client.models.docschemas_doc_export_inputs import DocschemasDocExportInputs

from openapi_client.api_client import ApiClient
from openapi_client.api_response import ApiResponse
from openapi_client.exceptions import (  # noqa: F401
    ApiTypeError,
    ApiValueError
)


class ScenesApi(object):
    """NOTE: This class is auto generated by OpenAPI Generator
    Ref: https://openapi-generator.tech

    Do not edit the class manually.
    """

    def __init__(self, api_client=None):
        if api_client is None:
            api_client = ApiClient.get_default()
        self.api_client = api_client

    @validate_arguments
    def cancel_build_by_scene(self, asset_id : Annotated[StrictStr, Field(..., description="ID of scene to cancel")], **kwargs) -> None:  # noqa: E501
        """Cancels a build process of a scene  # noqa: E501

        Cancels a running build of a scene, stopping the process from incurring any credit charges.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.cancel_build_by_scene(asset_id, async_req=True)
        >>> result = thread.get()

        :param asset_id: ID of scene to cancel (required)
        :type asset_id: str
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: None
        """
        kwargs['_return_http_data_only'] = True
        if '_preload_content' in kwargs:
            raise ValueError("Error! Please call the cancel_build_by_scene_with_http_info method with `_preload_content` instead and obtain raw data from ApiResponse.raw_data")
        return self.cancel_build_by_scene_with_http_info(asset_id, **kwargs)  # noqa: E501

    @validate_arguments
    def cancel_build_by_scene_with_http_info(self, asset_id : Annotated[StrictStr, Field(..., description="ID of scene to cancel")], **kwargs) -> ApiResponse:  # noqa: E501
        """Cancels a build process of a scene  # noqa: E501

        Cancels a running build of a scene, stopping the process from incurring any credit charges.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.cancel_build_by_scene_with_http_info(asset_id, async_req=True)
        >>> result = thread.get()

        :param asset_id: ID of scene to cancel (required)
        :type asset_id: str
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _preload_content: if False, the ApiResponse.data will
                                 be set to none and raw_data will store the 
                                 HTTP response body without reading/decoding.
                                 Default is True.
        :type _preload_content: bool, optional
        :param _return_http_data_only: response data instead of ApiResponse
                                       object with status code, headers, etc
        :type _return_http_data_only: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the authentication
                              in the spec for a single request.
        :type _request_auth: dict, optional
        :type _content_type: string, optional: force content-type for the request
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: None
        """

        _params = locals()

        _all_params = [
            'asset_id'
        ]
        _all_params.extend(
            [
                'async_req',
                '_return_http_data_only',
                '_preload_content',
                '_request_timeout',
                '_request_auth',
                '_content_type',
                '_headers'
            ]
        )

        # validate the arguments
        for _key, _val in _params['kwargs'].items():
            if _key not in _all_params:
                raise ApiTypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method cancel_build_by_scene" % _key
                )
            _params[_key] = _val
        del _params['kwargs']

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params['asset_id']:
            _path_params['assetID'] = _params['asset_id']


        # process the query parameters
        _query_params = []
        # process the header parameters
        _header_params = dict(_params.get('_headers', {}))
        # process the form parameters
        _form_params = []
        _files = {}
        # process the body parameter
        _body_params = None
        # authentication setting
        _auth_settings = ['OAuth2Password', 'Bearer']  # noqa: E501

        _response_types_map = {}

        return self.api_client.call_api(
            '/scenes/{assetID}/build/cancel', 'POST',
            _path_params,
            _query_params,
            _header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            response_types_map=_response_types_map,
            auth_settings=_auth_settings,
            async_req=_params.get('async_req'),
            _return_http_data_only=_params.get('_return_http_data_only'),  # noqa: E501
            _preload_content=_params.get('_preload_content', True),
            _request_timeout=_params.get('_request_timeout'),
            collection_formats=_collection_formats,
            _request_auth=_params.get('_request_auth'))

    @validate_arguments
    def describe_scene(self, asset_id : Annotated[StrictStr, Field(..., description="Scene ID")], include : Annotated[Optional[StrictStr], Field(description="Comma separated tags to include as relationships")] = None, **kwargs) -> DocschemasDocBaseSingleJSONAPIResponse:  # noqa: E501
        """List one scene  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.describe_scene(asset_id, include, async_req=True)
        >>> result = thread.get()

        :param asset_id: Scene ID (required)
        :type asset_id: str
        :param include: Comma separated tags to include as relationships
        :type include: str
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: DocschemasDocBaseSingleJSONAPIResponse
        """
        kwargs['_return_http_data_only'] = True
        if '_preload_content' in kwargs:
            raise ValueError("Error! Please call the describe_scene_with_http_info method with `_preload_content` instead and obtain raw data from ApiResponse.raw_data")
        return self.describe_scene_with_http_info(asset_id, include, **kwargs)  # noqa: E501

    @validate_arguments
    def describe_scene_with_http_info(self, asset_id : Annotated[StrictStr, Field(..., description="Scene ID")], include : Annotated[Optional[StrictStr], Field(description="Comma separated tags to include as relationships")] = None, **kwargs) -> ApiResponse:  # noqa: E501
        """List one scene  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.describe_scene_with_http_info(asset_id, include, async_req=True)
        >>> result = thread.get()

        :param asset_id: Scene ID (required)
        :type asset_id: str
        :param include: Comma separated tags to include as relationships
        :type include: str
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _preload_content: if False, the ApiResponse.data will
                                 be set to none and raw_data will store the 
                                 HTTP response body without reading/decoding.
                                 Default is True.
        :type _preload_content: bool, optional
        :param _return_http_data_only: response data instead of ApiResponse
                                       object with status code, headers, etc
        :type _return_http_data_only: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the authentication
                              in the spec for a single request.
        :type _request_auth: dict, optional
        :type _content_type: string, optional: force content-type for the request
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: tuple(DocschemasDocBaseSingleJSONAPIResponse, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = [
            'asset_id',
            'include'
        ]
        _all_params.extend(
            [
                'async_req',
                '_return_http_data_only',
                '_preload_content',
                '_request_timeout',
                '_request_auth',
                '_content_type',
                '_headers'
            ]
        )

        # validate the arguments
        for _key, _val in _params['kwargs'].items():
            if _key not in _all_params:
                raise ApiTypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method describe_scene" % _key
                )
            _params[_key] = _val
        del _params['kwargs']

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params['asset_id']:
            _path_params['assetID'] = _params['asset_id']


        # process the query parameters
        _query_params = []
        if _params.get('include') is not None:  # noqa: E501
            _query_params.append(('include', _params['include']))

        # process the header parameters
        _header_params = dict(_params.get('_headers', {}))
        # process the form parameters
        _form_params = []
        _files = {}
        # process the body parameter
        _body_params = None
        # set the HTTP header `Accept`
        _header_params['Accept'] = self.api_client.select_header_accept(
            ['application/json'])  # noqa: E501

        # authentication setting
        _auth_settings = ['OAuth2Password', 'Bearer']  # noqa: E501

        _response_types_map = {
            '200': "DocschemasDocBaseSingleJSONAPIResponse",
            '404': "MesherrMeshErr",
        }

        return self.api_client.call_api(
            '/scenes/{assetID}', 'GET',
            _path_params,
            _query_params,
            _header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            response_types_map=_response_types_map,
            auth_settings=_auth_settings,
            async_req=_params.get('async_req'),
            _return_http_data_only=_params.get('_return_http_data_only'),  # noqa: E501
            _preload_content=_params.get('_preload_content', True),
            _request_timeout=_params.get('_request_timeout'),
            collection_formats=_collection_formats,
            _request_auth=_params.get('_request_auth'))

    @validate_arguments
    def export_scene(self, asset_id : Annotated[StrictStr, Field(..., description="Scene ID")], input : Annotated[DocschemasDocExportInputs, Field(..., description="Request parameters")], **kwargs) -> DocschemasDocBaseMeshNoIncludesResponse:  # noqa: E501
        """Download scene  # noqa: E501

        This endpoint exports scenes from the SMPL representationx glb format. Upon requesting this endpoint, an export job is triggered which completes after a short period of time. Once the export job is ready, the exported avatar can be downloaded by reading the url attribute and requesting the file from the specified URL. </br> The request returns a Mesh Asset with the status attribute `EMPTY`, `PENDING`, `PROCESSING` or `READY` </br> Use the `self` link of the returned asset to request the status of the export job. `GET /meshes/{meshID}` \\ Once the export job is ready, you can download the exported avatar by reading out the `url` attribute and request the file from the url within. Alternatively, you can check the status of the export job by calling the same `POST /scenes/{sceneID}/export` endpoint with the same body parameters until the `status` attribute is `READY`.</br> Possible values for `format` are `FBX`, `USD` and `GLB` For GLB export we <b>only</b> support exporting avatars created from video at the moment! Only `anim=SCAN` is supported when setting the output to `format=GLB` When exporting to FBX you can specify the `avatarSceneIndex` parameter to export a specific avatar from a scene with multiple avatars. Set the value to `-1` to export all avatars. Defaults to `-1`.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.export_scene(asset_id, input, async_req=True)
        >>> result = thread.get()

        :param asset_id: Scene ID (required)
        :type asset_id: str
        :param input: Request parameters (required)
        :type input: DocschemasDocExportInputs
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: DocschemasDocBaseMeshNoIncludesResponse
        """
        kwargs['_return_http_data_only'] = True
        if '_preload_content' in kwargs:
            raise ValueError("Error! Please call the export_scene_with_http_info method with `_preload_content` instead and obtain raw data from ApiResponse.raw_data")
        return self.export_scene_with_http_info(asset_id, input, **kwargs)  # noqa: E501

    @validate_arguments
    def export_scene_with_http_info(self, asset_id : Annotated[StrictStr, Field(..., description="Scene ID")], input : Annotated[DocschemasDocExportInputs, Field(..., description="Request parameters")], **kwargs) -> ApiResponse:  # noqa: E501
        """Download scene  # noqa: E501

        This endpoint exports scenes from the SMPL representationx glb format. Upon requesting this endpoint, an export job is triggered which completes after a short period of time. Once the export job is ready, the exported avatar can be downloaded by reading the url attribute and requesting the file from the specified URL. </br> The request returns a Mesh Asset with the status attribute `EMPTY`, `PENDING`, `PROCESSING` or `READY` </br> Use the `self` link of the returned asset to request the status of the export job. `GET /meshes/{meshID}` \\ Once the export job is ready, you can download the exported avatar by reading out the `url` attribute and request the file from the url within. Alternatively, you can check the status of the export job by calling the same `POST /scenes/{sceneID}/export` endpoint with the same body parameters until the `status` attribute is `READY`.</br> Possible values for `format` are `FBX`, `USD` and `GLB` For GLB export we <b>only</b> support exporting avatars created from video at the moment! Only `anim=SCAN` is supported when setting the output to `format=GLB` When exporting to FBX you can specify the `avatarSceneIndex` parameter to export a specific avatar from a scene with multiple avatars. Set the value to `-1` to export all avatars. Defaults to `-1`.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.export_scene_with_http_info(asset_id, input, async_req=True)
        >>> result = thread.get()

        :param asset_id: Scene ID (required)
        :type asset_id: str
        :param input: Request parameters (required)
        :type input: DocschemasDocExportInputs
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _preload_content: if False, the ApiResponse.data will
                                 be set to none and raw_data will store the 
                                 HTTP response body without reading/decoding.
                                 Default is True.
        :type _preload_content: bool, optional
        :param _return_http_data_only: response data instead of ApiResponse
                                       object with status code, headers, etc
        :type _return_http_data_only: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the authentication
                              in the spec for a single request.
        :type _request_auth: dict, optional
        :type _content_type: string, optional: force content-type for the request
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: tuple(DocschemasDocBaseMeshNoIncludesResponse, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = [
            'asset_id',
            'input'
        ]
        _all_params.extend(
            [
                'async_req',
                '_return_http_data_only',
                '_preload_content',
                '_request_timeout',
                '_request_auth',
                '_content_type',
                '_headers'
            ]
        )

        # validate the arguments
        for _key, _val in _params['kwargs'].items():
            if _key not in _all_params:
                raise ApiTypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method export_scene" % _key
                )
            _params[_key] = _val
        del _params['kwargs']

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params['asset_id']:
            _path_params['assetID'] = _params['asset_id']


        # process the query parameters
        _query_params = []
        # process the header parameters
        _header_params = dict(_params.get('_headers', {}))
        # process the form parameters
        _form_params = []
        _files = {}
        # process the body parameter
        _body_params = None
        if _params['input'] is not None:
            _body_params = _params['input']

        # set the HTTP header `Accept`
        _header_params['Accept'] = self.api_client.select_header_accept(
            ['application/json'])  # noqa: E501

        # set the HTTP header `Content-Type`
        _content_types_list = _params.get('_content_type',
            self.api_client.select_header_content_type(
                ['application/json']))
        if _content_types_list:
                _header_params['Content-Type'] = _content_types_list

        # authentication setting
        _auth_settings = ['OAuth2Password', 'Bearer']  # noqa: E501

        _response_types_map = {
            '200': "DocschemasDocBaseMeshNoIncludesResponse",
        }

        return self.api_client.call_api(
            '/scenes/{assetID}/export', 'POST',
            _path_params,
            _query_params,
            _header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            response_types_map=_response_types_map,
            auth_settings=_auth_settings,
            async_req=_params.get('async_req'),
            _return_http_data_only=_params.get('_return_http_data_only'),  # noqa: E501
            _preload_content=_params.get('_preload_content', True),
            _request_timeout=_params.get('_request_timeout'),
            collection_formats=_collection_formats,
            _request_auth=_params.get('_request_auth'))

    @validate_arguments
    def list_scenes(self, include : Annotated[Optional[StrictStr], Field(description="Comma separated tags to include as relationships")] = None, limit : Annotated[Optional[conint(strict=True, ge=1)], Field(description="Paginated scenes limit amount (Default 20)")] = None, page : Annotated[Optional[conint(strict=True, ge=1)], Field(description="Pagination")] = None, filter_field : Annotated[Optional[StrictStr], Field(description="Filter by field")] = None, **kwargs) -> DocschemasDocBaseJSONAPIResponse:  # noqa: E501
        """List all Scenes  # noqa: E501

        Lists all scenes the user owns. Use `include` query parameter string to include assets that have a relationship to the listed scenes. Related assets can be preview images that have been generated or alternate preview images  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.list_scenes(include, limit, page, filter_field, async_req=True)
        >>> result = thread.get()

        :param include: Comma separated tags to include as relationships
        :type include: str
        :param limit: Paginated scenes limit amount (Default 20)
        :type limit: int
        :param page: Pagination
        :type page: int
        :param filter_field: Filter by field
        :type filter_field: str
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: DocschemasDocBaseJSONAPIResponse
        """
        kwargs['_return_http_data_only'] = True
        if '_preload_content' in kwargs:
            raise ValueError("Error! Please call the list_scenes_with_http_info method with `_preload_content` instead and obtain raw data from ApiResponse.raw_data")
        return self.list_scenes_with_http_info(include, limit, page, filter_field, **kwargs)  # noqa: E501

    @validate_arguments
    def list_scenes_with_http_info(self, include : Annotated[Optional[StrictStr], Field(description="Comma separated tags to include as relationships")] = None, limit : Annotated[Optional[conint(strict=True, ge=1)], Field(description="Paginated scenes limit amount (Default 20)")] = None, page : Annotated[Optional[conint(strict=True, ge=1)], Field(description="Pagination")] = None, filter_field : Annotated[Optional[StrictStr], Field(description="Filter by field")] = None, **kwargs) -> ApiResponse:  # noqa: E501
        """List all Scenes  # noqa: E501

        Lists all scenes the user owns. Use `include` query parameter string to include assets that have a relationship to the listed scenes. Related assets can be preview images that have been generated or alternate preview images  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.list_scenes_with_http_info(include, limit, page, filter_field, async_req=True)
        >>> result = thread.get()

        :param include: Comma separated tags to include as relationships
        :type include: str
        :param limit: Paginated scenes limit amount (Default 20)
        :type limit: int
        :param page: Pagination
        :type page: int
        :param filter_field: Filter by field
        :type filter_field: str
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _preload_content: if False, the ApiResponse.data will
                                 be set to none and raw_data will store the 
                                 HTTP response body without reading/decoding.
                                 Default is True.
        :type _preload_content: bool, optional
        :param _return_http_data_only: response data instead of ApiResponse
                                       object with status code, headers, etc
        :type _return_http_data_only: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the authentication
                              in the spec for a single request.
        :type _request_auth: dict, optional
        :type _content_type: string, optional: force content-type for the request
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: tuple(DocschemasDocBaseJSONAPIResponse, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = [
            'include',
            'limit',
            'page',
            'filter_field'
        ]
        _all_params.extend(
            [
                'async_req',
                '_return_http_data_only',
                '_preload_content',
                '_request_timeout',
                '_request_auth',
                '_content_type',
                '_headers'
            ]
        )

        # validate the arguments
        for _key, _val in _params['kwargs'].items():
            if _key not in _all_params:
                raise ApiTypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method list_scenes" % _key
                )
            _params[_key] = _val
        del _params['kwargs']

        _collection_formats = {}

        # process the path parameters
        _path_params = {}

        # process the query parameters
        _query_params = []
        if _params.get('include') is not None:  # noqa: E501
            _query_params.append(('include', _params['include']))

        if _params.get('limit') is not None:  # noqa: E501
            _query_params.append(('limit', _params['limit']))

        if _params.get('page') is not None:  # noqa: E501
            _query_params.append(('page', _params['page']))

        if _params.get('filter_field') is not None:  # noqa: E501
            _query_params.append(('filter[field]', _params['filter_field']))

        # process the header parameters
        _header_params = dict(_params.get('_headers', {}))
        # process the form parameters
        _form_params = []
        _files = {}
        # process the body parameter
        _body_params = None
        # set the HTTP header `Accept`
        _header_params['Accept'] = self.api_client.select_header_accept(
            ['application/json'])  # noqa: E501

        # authentication setting
        _auth_settings = ['OAuth2Password', 'Bearer']  # noqa: E501

        _response_types_map = {
            '200': "DocschemasDocBaseJSONAPIResponse",
            '400': "DocschemasDocErrorResponse",
            '401': "DocschemasDocErrorResponse",
            '404': "DocschemasDocErrorResponse",
        }

        return self.api_client.call_api(
            '/scenes', 'GET',
            _path_params,
            _query_params,
            _header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            response_types_map=_response_types_map,
            auth_settings=_auth_settings,
            async_req=_params.get('async_req'),
            _return_http_data_only=_params.get('_return_http_data_only'),  # noqa: E501
            _preload_content=_params.get('_preload_content', True),
            _request_timeout=_params.get('_request_timeout'),
            collection_formats=_collection_formats,
            _request_auth=_params.get('_request_auth'))

    @validate_arguments
    def upload_preview_image_to_scene(self, asset_id : Annotated[StrictStr, Field(..., description="Scene ID")], **kwargs) -> None:  # noqa: E501
        """Request upload URL for preview image  # noqa: E501

        Requests upload URL for a preview image. Links the preview image asset up with the scene asset The upload URL is a presigned PUT URL that can be used to upload the file to the server..  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.upload_preview_image_to_scene(asset_id, async_req=True)
        >>> result = thread.get()

        :param asset_id: Scene ID (required)
        :type asset_id: str
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: None
        """
        kwargs['_return_http_data_only'] = True
        if '_preload_content' in kwargs:
            raise ValueError("Error! Please call the upload_preview_image_to_scene_with_http_info method with `_preload_content` instead and obtain raw data from ApiResponse.raw_data")
        return self.upload_preview_image_to_scene_with_http_info(asset_id, **kwargs)  # noqa: E501

    @validate_arguments
    def upload_preview_image_to_scene_with_http_info(self, asset_id : Annotated[StrictStr, Field(..., description="Scene ID")], **kwargs) -> ApiResponse:  # noqa: E501
        """Request upload URL for preview image  # noqa: E501

        Requests upload URL for a preview image. Links the preview image asset up with the scene asset The upload URL is a presigned PUT URL that can be used to upload the file to the server..  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.upload_preview_image_to_scene_with_http_info(asset_id, async_req=True)
        >>> result = thread.get()

        :param asset_id: Scene ID (required)
        :type asset_id: str
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _preload_content: if False, the ApiResponse.data will
                                 be set to none and raw_data will store the 
                                 HTTP response body without reading/decoding.
                                 Default is True.
        :type _preload_content: bool, optional
        :param _return_http_data_only: response data instead of ApiResponse
                                       object with status code, headers, etc
        :type _return_http_data_only: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the authentication
                              in the spec for a single request.
        :type _request_auth: dict, optional
        :type _content_type: string, optional: force content-type for the request
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: None
        """

        _params = locals()

        _all_params = [
            'asset_id'
        ]
        _all_params.extend(
            [
                'async_req',
                '_return_http_data_only',
                '_preload_content',
                '_request_timeout',
                '_request_auth',
                '_content_type',
                '_headers'
            ]
        )

        # validate the arguments
        for _key, _val in _params['kwargs'].items():
            if _key not in _all_params:
                raise ApiTypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method upload_preview_image_to_scene" % _key
                )
            _params[_key] = _val
        del _params['kwargs']

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params['asset_id']:
            _path_params['assetID'] = _params['asset_id']


        # process the query parameters
        _query_params = []
        # process the header parameters
        _header_params = dict(_params.get('_headers', {}))
        # process the form parameters
        _form_params = []
        _files = {}
        # process the body parameter
        _body_params = None
        # authentication setting
        _auth_settings = ['Bearer']  # noqa: E501

        _response_types_map = {}

        return self.api_client.call_api(
            '/scenes/{assetID}/preview', 'POST',
            _path_params,
            _query_params,
            _header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            response_types_map=_response_types_map,
            auth_settings=_auth_settings,
            async_req=_params.get('async_req'),
            _return_http_data_only=_params.get('_return_http_data_only'),  # noqa: E501
            _preload_content=_params.get('_preload_content', True),
            _request_timeout=_params.get('_request_timeout'),
            collection_formats=_collection_formats,
            _request_auth=_params.get('_request_auth'))
