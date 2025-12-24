from typing import Optional
import openapi_client as client
from .helpers import Uploader
from .logger import log
from .assets import Asset, CreateFromSourceMixin, ExportMixin


class Scene(CreateFromSourceMixin, ExportMixin, Asset):
    """Represents a scene asset.

    This class inherits from Asset as well as from mixin classes to add functionality not unique to scenes.
    """

    asset_api = client.ScenesApi
    list_method_name = "describe_scene"
    list_all_method_name = "list_scenes"
    asset_api_instance: client.ScenesApi

    def from_video(
        self,
        name: str,
        input: str,
        max_person_count: bool,
        model_version: Optional[client.EnumsModelVersion],
        lock_feet: bool,
        uploader: Uploader,
        timeout: int,
    ):
        """Creates a scene from a video."""
        from_video_api = client.CreateSceneFromVideoApi(self.api_client)
        initialize_asset_method = from_video_api.create_scene_from_video
        request_upload_method = from_video_api.upload_video_to_scene
        fit_to_source_method = from_video_api.scene_fit_to_video
        request_parameters = client.DocschemasDocSceneFromVideoInputs(
            sceneName=name, maxPersonCount=max_person_count, modelVersion=model_version, lockFeet=lock_feet
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

    def export_scene(self, download_format: str, compatibility_mode: str, avatarSceneIndex: int, timeout: int):
        """Exports avatar. Sets download_url for later downloading."""
        export_parameters = client.DocschemasDocExportInputs(
            format=download_format,
            animation="scan",
            compatibilityMode=compatibility_mode,
            avatarSceneIndex=avatarSceneIndex,
        )
        export_method = self.asset_api_instance.export_scene

        log.debug(f"Exporting scene with parameters: {export_parameters}")

        self.export(export_parameters=export_parameters, export_method=export_method, timeout=timeout)
