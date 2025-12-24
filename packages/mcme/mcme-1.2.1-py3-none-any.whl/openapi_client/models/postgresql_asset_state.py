# coding: utf-8

"""
    Meshcapade Me API

    Welcome to the age of Avatars, introducing the Meshcapade Me API. The no-friction avatar-creation platform for all your avatar needs. Create accurate digital doubles from any source of data in a unified 3D body format for every industry. Built on our <a href=\"https://meshcapade.com/SMPL\" target=\"_blank\">patented avatar</a> technology, our API allows you to create and edit avatars from images, videos, measurements, scans, and more. # Introduction The Meshcapade Me API is a RESTful API that allows you to create and edit avatars from images, measurements, scans, and more. All API replies adhere to the  <a href=\"https://jsonapi.org/format/\" target=\"_blank\">JSON:API</a> schema guidelines. Currently the API is in beta and is subject to change. Thus, not all ways to create avatars are available yet. We are working hard to add more ways to create avatars and will update this documentation accordingly. The API allows you to create avatars from: </br> - <a href=\"#post-/avatars/create/from-images\" target=\"_blank\">images</a> </br> - <a href=\"#post-/avatars/create/from-video\" target=\"_blank\">video</a> </br> - <a href=\"#post-/avatars/create/from-scans\" target=\"_blank\">3D scans</a> </br> - <a href=\"#post-/avatars/create/from-measurements\" target=\"_blank\">measurements</a> </br> # Quickstart To get started, sign up for a free account at <a href=\"https://me.meshcapade.com\" target=\"_blank\">me.meshcapade.com</a></br> We recommend using our <a href=\"https://www.postman.com/downloads/\" target=\"_blank\">Postman</a> collection to conveniently explore the API. </br> <div style=\"margin-top: 16px;\"><a href=\"https://www.postman.com/cloudy-meadow-883625/workspace/meshcapade/overview\"><img src=\"https://run.pstmn.io/button.svg\" alt=\"Run in Postman\"></a></div></br>  # How-To <a href=\"https://medium.com/meshcapade/streamline-avatar-creation-with-meshcapade-me-api-from-one-image-to-an-accurate-avatar-in-seconds-b8ca4f15b9a8\" target=\"_blank\">Create an avatar from a single image (Medium)</a> </br> <a href=\"https://medium.com/meshcapade/measurements-meet-imagination-creating-accurate-3d-avatars-with-meshcapades-api-9a6ec5029793\" target=\"_blank\">Create an avatar from measurements (Medium)</a> # API Categories The API is organized into the following main categories: - <strong>Assets</strong>: Endpoint for listing assets of multiple types. - <strong>Avatars</strong>: Endpoints for listing, downloading, and deleting avatars. - <strong>Mesh</strong>: Endpoints for listing, downloading, and deleting exported meshes. - <strong>Images</strong>: Endpoints for listing, uploading, and deleting images related to avatars. - <strong>Create Avatar from images</strong>: Endpoints to initiate and complete avatar creation from images. - <strong>Create Avatar from measurements</strong>: Endpoint to initiate avatar creation from body measurements. - <strong>Create Avatar from scans</strong>: Endpoints to initiate and complete avatar creation from 3d body scans. - <strong>Create Avatar from betas</strong>: Endpoint to create an avatar from SMPL based beta shape parameters. # Error codes When something goes wrong, the API replies with an additional error code  - `asset_not_found` The requested asset either does not exist, or is not owned by the user (404)  </br> - `too_many_images` The image limit that can be uploaded for avatars from images as been exceeded. (400) </br> - `already_started` A process that already has been requested cannot be started again. (400) </br> - `no_images`  [POST /avatars/create/from-images](#post-/avatars/create/from-images) can only be started with at least one image uploaded  (400) </br> - `inputs_not_ready` Running `/avatars/create/xxxx` endpoint require the inputs to be uploaded (400) </br> - `uuid_invalid_format` Asset ID is in a non-UUID format (400) </br> - ` missing_parameters` Not all required parameters have been supplied for the request (400) </br> - `unauthorized` Trying to access an asset the user does not own, or endpoints that the user is not authorized to call (400) </br> - `too_many_builds` User processing rate has been exceeded. Only one computation heavy process can be started at a time (429) </br> - `asset_not_ready` Cannot call request on an asset which is not in a READY state (400) </br>  # Integration When integrating with our API, you may encounter Cross-Origin Resource Sharing (CORS) issues during deployment. </br> For security reasons, our API does not support direct communication from your frontend. </br> Instead, we recommend that you connect to api.meshcapade through your own backend server. </br> This approach not only mitigates CORS-related challenges but also enhances the overall security of your application. </br> By handling API requests server-side, you can ensure smoother and safer integration. </br> If you encounter any issues during integration, please reach out to us at: support@meshcapade.com </br>  # noqa: E501

    The version of the OpenAPI document: v1.24
    Contact: support@meshcapade.com
    Generated by OpenAPI Generator (https://openapi-generator.tech)

    Do not edit the class manually.
"""


import json
import pprint
import re  # noqa: F401
from aenum import Enum, no_arg




enumtype = str

class PostgresqlAssetState(str, Enum):
    """
    PostgresqlAssetState
    """

    """
    allowed enum values
    """
    if enumtype == str:
        EMPTY = 'EMPTY'
        READY = 'READY'
        ERROR = 'ERROR'
        AWAITING_AFI_INPUT = 'AWAITING_AFI_INPUT'
        PROCESSING = 'PROCESSING'
        AWAITING_PROCESSING = 'AWAITING_PROCESSING'
        AWAITING_UPLOAD = 'AWAITING_UPLOAD'
        AWAITING_AFS_INPUT = 'AWAITING_AFS_INPUT'
        AWAITING_AFV_INPUT = 'AWAITING_AFV_INPUT'
        CANCELED = 'CANCELED'
    else:
        AssetStateEMPTY = "AssetStateEMPTY"
        AssetStateREADY = "AssetStateREADY"
        AssetStateERROR = "AssetStateERROR"
        AssetStateAWAITINGAFIINPUT = "AssetStateAWAITINGAFIINPUT"
        AssetStatePROCESSING = "AssetStatePROCESSING"
        AssetStateAWAITINGPROCESSING = "AssetStateAWAITINGPROCESSING"
        AssetStateAWAITINGUPLOAD = "AssetStateAWAITINGUPLOAD"
        AssetStateAWAITINGAFSINPUT = "AssetStateAWAITINGAFSINPUT"
        AssetStateAWAITINGAFVINPUT = "AssetStateAWAITINGAFVINPUT"
        AssetStateCANCELED = "AssetStateCANCELED"

    @classmethod
    def from_json(cls, json_str: str) -> PostgresqlAssetState:
        """Create an instance of PostgresqlAssetState from a JSON string"""
        return PostgresqlAssetState(json.loads(json_str))


    def enum_values():
        return [c.value for c in PostgresqlAssetState]
