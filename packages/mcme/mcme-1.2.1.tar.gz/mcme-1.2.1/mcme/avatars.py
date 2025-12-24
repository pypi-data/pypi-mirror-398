from typing import Optional
import openapi_client as client
from openapi_client import PostgresqlAssetState as AssetState
from .helpers import Uploader
from .assets import CreateFromParametersMixin, ExportMixin, Asset, CreateFromSourceMixin
from .logger import log


class Avatar(CreateFromParametersMixin, CreateFromSourceMixin, ExportMixin, Asset):
    """Represents an avatar asset.

    This class inherits from Asset as well as from mixin classes to add functionality not unique to avatars.
    """

    asset_api = client.AvatarsApi
    list_method_name = "describe_avatar"
    list_all_method_name = "list_avatars"
    asset_api_instance: client.AvatarsApi

    def from_betas(
        self,
        gender: Optional[client.EnumsGender],
        betas: list[float],
        name: str,
        model_version: Optional[client.EnumsModelVersion],
        poseName: str,
    ):
        """Creates an avatar from betas."""
        from_betas_method = client.CreateAvatarsFromBetasApi(self.api_client).create_avatar_from_betas
        request_parameters = client.SchemasBetasAvatarRequest(
            betas=betas, gender=gender, name=name, modelVersion=model_version, poseName=poseName
        )
        self.set_name(name)
        self.create_from_parameters(method=from_betas_method, request_parameters=request_parameters, timeout=0)

    def from_measurements(
        self,
        measurements: dict[str, float],
        gender: Optional[client.EnumsGender],
        name: str,
        model_version: Optional[client.EnumsModelVersion],
        timeout: int,
    ):
        """Creates an avatar from measurements."""
        from_measurements_method = client.CreateAvatarFromMeasurementsApi(self.api_client).avatar_from_measurements
        request_parameters = client.SchemasMeasurementAvatarRequest(
            gender=gender, name=name, measurements=measurements, modelVersion=model_version
        )
        self.set_name(name)
        self.create_from_parameters(
            method=from_measurements_method, request_parameters=request_parameters, timeout=timeout
        )

    def from_images(
        self,
        gender: Optional[client.EnumsGender],
        name: str,
        input: str,
        height: int,
        weight: int,
        image_mode: str,
        uploader: Uploader,
        timeout: int,
    ):
        """Creates an avatar from an image."""
        from_images_api = client.CreateAvatarFromImagesApi(self.api_client)
        initialize_asset_method = from_images_api.create_avatar_from_images
        request_upload_method = from_images_api.upload_image_to_avatar
        fit_to_source_method = from_images_api.avatar_fit_to_images
        request_parameters = client.DocschemasDocAFIInputs(
            avatarname=name, gender=gender, height=height, weight=weight, imageMode=image_mode
        )
        self.set_name(name)
        self.create_from_source(
            initialize_asset_method=initialize_asset_method,
            request_upload_method=request_upload_method,
            fit_to_source_method=fit_to_source_method,
            input=input,
            request_parameters=request_parameters,
            uploader=uploader,
            timeout=timeout,
        )

    def from_scans(
        self,
        gender: Optional[client.EnumsGender],
        name: str,
        input: str,
        init_pose: str,
        up_axis: str,
        look_axis: str,
        input_units: str,
        uploader: Uploader,
        timeout: int,
    ):
        """Creates an avatar from a scan."""
        from_scans_api = client.CreateAvatarFromScansApi(self.api_client)
        initialize_asset_method = from_scans_api.create_avatar_from_scans
        request_upload_method = from_scans_api.upload_mesh_to_avatar
        fit_to_source_method = from_scans_api.avatar_fit_to_scans
        request_parameters = client.DocschemasDocAFSInputs(
            avatarname=name,
            gender=gender,
            initPose=init_pose,
            inputUnits=input_units,
            lookAxis=look_axis,
            upAxis=up_axis,
        )
        self.set_name(name)
        self.create_from_source(
            initialize_asset_method=initialize_asset_method,
            request_upload_method=request_upload_method,
            fit_to_source_method=fit_to_source_method,
            input=input,
            request_parameters=request_parameters,
            uploader=uploader,
            timeout=timeout,
        )

    def from_smpl(self, smpl_file: str, name: str, uploader: Uploader, timeout: int) -> None:
        """Creates an avatar from a .smpl file"""
        request_parameters = client.DocschemasDocCreateFromSMPLRequest(name=name)
        initialize_from_smpl_method = self.asset_api_instance.create_from_smpl
        self.request_asset_from_source(
            initialize_asset_method=initialize_from_smpl_method, request_parameters=request_parameters
        )
        self.set_name(name)
        # Upload .smpl file
        self.upload_source(smpl_file, uploader=uploader)

        # Wait for processing to finish
        self.wait_for_processing(timeout=timeout, desired_state=AssetState(AssetState.READY))

    def export_avatar(self, download_format: str, pose: str, animation: str, compatibility_mode: str, timeout: int):
        """Exports avatar. Sets download_url for later downloading."""
        export_parameters = client.DocschemasDocExportInputs(
            format=download_format,
            pose=pose,
            animation=animation,
            compatibilityMode=compatibility_mode,
            avatarSceneIndex=None,
        )
        export_method = self.asset_api_instance.export_avatar

        log.debug(f"Exporting avatar with parameters: {export_parameters}")

        self.export(export_parameters=export_parameters, export_method=export_method, timeout=timeout)
