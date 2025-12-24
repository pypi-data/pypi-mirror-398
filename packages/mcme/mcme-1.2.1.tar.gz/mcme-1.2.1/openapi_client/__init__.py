# coding: utf-8

# flake8: noqa

"""
    Meshcapade Me API

    Welcome to the age of Avatars, introducing the Meshcapade Me API. The no-friction avatar-creation platform for all your avatar needs. Create accurate digital doubles from any source of data in a unified 3D body format for every industry. Built on our <a href=\"https://meshcapade.com/SMPL\" target=\"_blank\">patented avatar</a> technology, our API allows you to create and edit avatars from images, videos, measurements, scans, and more. # Introduction The Meshcapade Me API is a RESTful API that allows you to create and edit avatars from images, measurements, scans, and more. All API replies adhere to the  <a href=\"https://jsonapi.org/format/\" target=\"_blank\">JSON:API</a> schema guidelines. Currently the API is in beta and is subject to change. Thus, not all ways to create avatars are available yet. We are working hard to add more ways to create avatars and will update this documentation accordingly. The API allows you to create avatars from: </br> - <a href=\"#post-/avatars/create/from-images\" target=\"_blank\">images</a> </br> - <a href=\"#post-/avatars/create/from-video\" target=\"_blank\">video</a> </br> - <a href=\"#post-/avatars/create/from-scans\" target=\"_blank\">3D scans</a> </br> - <a href=\"#post-/avatars/create/from-measurements\" target=\"_blank\">measurements</a> </br> # Quickstart To get started, sign up for a free account at <a href=\"https://me.meshcapade.com\" target=\"_blank\">me.meshcapade.com</a></br> We recommend using our <a href=\"https://www.postman.com/downloads/\" target=\"_blank\">Postman</a> collection to conveniently explore the API. </br> <div style=\"margin-top: 16px;\"><a href=\"https://www.postman.com/cloudy-meadow-883625/workspace/meshcapade/overview\"><img src=\"https://run.pstmn.io/button.svg\" alt=\"Run in Postman\"></a></div></br>  # How-To <a href=\"https://medium.com/meshcapade/streamline-avatar-creation-with-meshcapade-me-api-from-one-image-to-an-accurate-avatar-in-seconds-b8ca4f15b9a8\" target=\"_blank\">Create an avatar from a single image (Medium)</a> </br> <a href=\"https://medium.com/meshcapade/measurements-meet-imagination-creating-accurate-3d-avatars-with-meshcapades-api-9a6ec5029793\" target=\"_blank\">Create an avatar from measurements (Medium)</a> # API Categories The API is organized into the following main categories: - <strong>Assets</strong>: Endpoint for listing assets of multiple types. - <strong>Avatars</strong>: Endpoints for listing, downloading, and deleting avatars. - <strong>Mesh</strong>: Endpoints for listing, downloading, and deleting exported meshes. - <strong>Images</strong>: Endpoints for listing, uploading, and deleting images related to avatars. - <strong>Create Avatar from images</strong>: Endpoints to initiate and complete avatar creation from images. - <strong>Create Avatar from measurements</strong>: Endpoint to initiate avatar creation from body measurements. - <strong>Create Avatar from scans</strong>: Endpoints to initiate and complete avatar creation from 3d body scans. - <strong>Create Avatar from betas</strong>: Endpoint to create an avatar from SMPL based beta shape parameters. # Error codes When something goes wrong, the API replies with an additional error code  - `asset_not_found` The requested asset either does not exist, or is not owned by the user (404)  </br> - `too_many_images` The image limit that can be uploaded for avatars from images as been exceeded. (400) </br> - `already_started` A process that already has been requested cannot be started again. (400) </br> - `no_images`  [POST /avatars/create/from-images](#post-/avatars/create/from-images) can only be started with at least one image uploaded  (400) </br> - `inputs_not_ready` Running `/avatars/create/xxxx` endpoint require the inputs to be uploaded (400) </br> - `uuid_invalid_format` Asset ID is in a non-UUID format (400) </br> - ` missing_parameters` Not all required parameters have been supplied for the request (400) </br> - `unauthorized` Trying to access an asset the user does not own, or endpoints that the user is not authorized to call (400) </br> - `too_many_builds` User processing rate has been exceeded. Only one computation heavy process can be started at a time (429) </br> - `asset_not_ready` Cannot call request on an asset which is not in a READY state (400) </br>  # Integration When integrating with our API, you may encounter Cross-Origin Resource Sharing (CORS) issues during deployment. </br> For security reasons, our API does not support direct communication from your frontend. </br> Instead, we recommend that you connect to api.meshcapade through your own backend server. </br> This approach not only mitigates CORS-related challenges but also enhances the overall security of your application. </br> By handling API requests server-side, you can ensure smoother and safer integration. </br> If you encounter any issues during integration, please reach out to us at: support@meshcapade.com </br>  # noqa: E501

    The version of the OpenAPI document: v1.24
    Contact: support@meshcapade.com
    Generated by OpenAPI Generator (https://openapi-generator.tech)

    Do not edit the class manually.
"""


__version__ = "1.0.0"

# import apis into sdk package
from openapi_client.api.assets_api import AssetsApi
from openapi_client.api.avatars_api import AvatarsApi
from openapi_client.api.blend_motions_api import BlendMotionsApi
from openapi_client.api.create_avatar_from_images_api import CreateAvatarFromImagesApi
from openapi_client.api.create_avatar_from_scans_api import CreateAvatarFromScansApi
from openapi_client.api.create_avatar_from_video_api import CreateAvatarFromVideoApi
from openapi_client.api.create_avatar_from_measurements_api import CreateAvatarFromMeasurementsApi
from openapi_client.api.create_avatars_from_betas_api import CreateAvatarsFromBetasApi
from openapi_client.api.create_scene_from_video_api import CreateSceneFromVideoApi
from openapi_client.api.helpers_api import HelpersApi
from openapi_client.api.images_api import ImagesApi
from openapi_client.api.info_api import InfoApi
from openapi_client.api.measure_avatar_api import MeasureAvatarApi
from openapi_client.api.mesh_api import MeshApi
from openapi_client.api.motions_api import MotionsApi
from openapi_client.api.scenes_api import ScenesApi
from openapi_client.api.search_motions_api import SearchMotionsApi
from openapi_client.api.subscription_api import SubscriptionApi
from openapi_client.api.teams_api import TeamsApi
from openapi_client.api.user_api import UserApi
from openapi_client.api.videos_api import VideosApi

# import ApiClient
from openapi_client.api_response import ApiResponse
from openapi_client.api_client import ApiClient
from openapi_client.configuration import Configuration
from openapi_client.exceptions import OpenApiException
from openapi_client.exceptions import ApiTypeError
from openapi_client.exceptions import ApiValueError
from openapi_client.exceptions import ApiKeyError
from openapi_client.exceptions import ApiAttributeError
from openapi_client.exceptions import ApiException

# import models into sdk package
from openapi_client.models.docschemas_doc_afi_inputs import DocschemasDocAFIInputs
from openapi_client.models.docschemas_doc_afs_inputs import DocschemasDocAFSInputs
from openapi_client.models.docschemas_doc_afv_inputs import DocschemasDocAFVInputs
from openapi_client.models.docschemas_doc_asset_response import DocschemasDocAssetResponse
from openapi_client.models.docschemas_doc_avatar_attributes import DocschemasDocAvatarAttributes
from openapi_client.models.docschemas_doc_avatar_link import DocschemasDocAvatarLink
from openapi_client.models.docschemas_doc_avatar_metadata import DocschemasDocAvatarMetadata
from openapi_client.models.docschemas_doc_avatar_relationships import DocschemasDocAvatarRelationships
from openapi_client.models.docschemas_doc_avatar_relationships_exported_mesh import DocschemasDocAvatarRelationshipsExportedMesh
from openapi_client.models.docschemas_doc_avatar_relationships_exported_mesh_data_inner import DocschemasDocAvatarRelationshipsExportedMeshDataInner
from openapi_client.models.docschemas_doc_base_jsonapi_response import DocschemasDocBaseJSONAPIResponse
from openapi_client.models.docschemas_doc_base_mesh_no_includes_response import DocschemasDocBaseMeshNoIncludesResponse
from openapi_client.models.docschemas_doc_base_single_jsonapi_response import DocschemasDocBaseSingleJSONAPIResponse
from openapi_client.models.docschemas_doc_body_shape import DocschemasDocBodyShape
from openapi_client.models.docschemas_doc_build_attributes import DocschemasDocBuildAttributes
from openapi_client.models.docschemas_doc_build_jsonapi_response import DocschemasDocBuildJSONAPIResponse
from openapi_client.models.docschemas_doc_build_link import DocschemasDocBuildLink
from openapi_client.models.docschemas_doc_build_response import DocschemasDocBuildResponse
from openapi_client.models.docschemas_doc_create_from_smpl_request import DocschemasDocCreateFromSMPLRequest
from openapi_client.models.docschemas_doc_create_team_inputs import DocschemasDocCreateTeamInputs
from openapi_client.models.docschemas_doc_error_response import DocschemasDocErrorResponse
from openapi_client.models.docschemas_doc_export_inputs import DocschemasDocExportInputs
from openapi_client.models.docschemas_doc_invalidate_team_invite_inputs import DocschemasDocInvalidateTeamInviteInputs
from openapi_client.models.docschemas_doc_invite_to_team_inputs import DocschemasDocInviteToTeamInputs
from openapi_client.models.docschemas_doc_kick_from_team_inputs import DocschemasDocKickFromTeamInputs
from openapi_client.models.docschemas_doc_mesh_attributes import DocschemasDocMeshAttributes
from openapi_client.models.docschemas_doc_mesh_link import DocschemasDocMeshLink
from openapi_client.models.docschemas_doc_mesh_measurements import DocschemasDocMeshMeasurements
from openapi_client.models.docschemas_doc_mesh_metadata import DocschemasDocMeshMetadata
from openapi_client.models.docschemas_doc_mesh_no_relation_response import DocschemasDocMeshNoRelationResponse
from openapi_client.models.docschemas_doc_mesh_response import DocschemasDocMeshResponse
from openapi_client.models.docschemas_doc_motion import DocschemasDocMotion
from openapi_client.models.docschemas_doc_motion_options import DocschemasDocMotionOptions
from openapi_client.models.docschemas_doc_motion_result import DocschemasDocMotionResult
from openapi_client.models.docschemas_doc_patch_team_inputs import DocschemasDocPatchTeamInputs
from openapi_client.models.docschemas_doc_scene_from_video_inputs import DocschemasDocSceneFromVideoInputs
from openapi_client.models.docschemas_doc_subscription_attributes import DocschemasDocSubscriptionAttributes
from openapi_client.models.docschemas_doc_team_attributes import DocschemasDocTeamAttributes
from openapi_client.models.docschemas_doc_team_invite_or_user_attributes import DocschemasDocTeamInviteOrUserAttributes
from openapi_client.models.docschemas_doc_team_invites_and_users_response import DocschemasDocTeamInvitesAndUsersResponse
from openapi_client.models.docschemas_doc_team_jsonapi_response import DocschemasDocTeamJSONAPIResponse
from openapi_client.models.docschemas_doc_team_response import DocschemasDocTeamResponse
from openapi_client.models.docschemas_doc_user_attributes import DocschemasDocUserAttributes
from openapi_client.models.docschemas_doc_user_jsonapi_response import DocschemasDocUserJSONAPIResponse
from openapi_client.models.docschemas_doc_user_response import DocschemasDocUserResponse
from openapi_client.models.docschemas_doc_user_team_details_attributes import DocschemasDocUserTeamDetailsAttributes
from openapi_client.models.docschemas_doc_user_team_details_response import DocschemasDocUserTeamDetailsResponse
from openapi_client.models.enums_gender import EnumsGender
from openapi_client.models.enums_model_version import EnumsModelVersion
from openapi_client.models.mesherr_mesh_err import MesherrMeshErr
from openapi_client.models.postgresql_asset_state import PostgresqlAssetState
from openapi_client.models.postgresql_asset_type import PostgresqlAssetType
from openapi_client.models.postgresql_build_method import PostgresqlBuildMethod
from openapi_client.models.postgresql_build_state import PostgresqlBuildState
from openapi_client.models.postgresql_file_source import PostgresqlFileSource
from openapi_client.models.schemas_betas_avatar_request import SchemasBetasAvatarRequest
from openapi_client.models.schemas_image_tag_links import SchemasImageTagLinks
from openapi_client.models.schemas_measurement_avatar_request import SchemasMeasurementAvatarRequest
from openapi_client.models.schemas_motion_blend_motion import SchemasMotionBlendMotion
from openapi_client.models.schemas_motion_blend_request import SchemasMotionBlendRequest
from openapi_client.models.schemas_url_response import SchemasURLResponse
from openapi_client.models.services_search_motions_options import ServicesSearchMotionsOptions
