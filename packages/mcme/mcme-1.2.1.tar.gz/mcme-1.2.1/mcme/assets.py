import re
import time
import click
from .helpers import TimeoutTracker, Uploader, get_timestamp, download_file
import openapi_client as client
from typing import Callable, Optional, Type, TypeVar
from .logger import log
from openapi_client import PostgresqlAssetState as AssetState
from openapi_client import DocschemasDocAssetResponse as AssetResponse
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.text import Text
import rich.box
from .constants import (
    ASSET_COLUMN_STYLES,
)

T = TypeVar("T", bound="Asset")


class Asset:
    """
    Represents an asset like Avatar, Motion, or Scene.

    This class serves as a base for different asset types, each of which has its own API instance.
    It provides basic methods that are shared between all asset types.

    Attributes:
        asset_api (type[client.AvatarsApi | client.ScenesApi | client.MotionsApi]):
            API class used by openapi_client to make meshcapade.me API calls specific to the respective type.
        list_method_name (str):
            The name of the method used to list one asset.
        list_all_method_name (str):
            The name of the method used to list all assets.
        list_all_method (Optional[Callable]):
            The method used for listing all assets. Is an attribute of an Asset instance.
        api_client (client.ApiClient):
            The API client instance used to make meshcapade.me API calls.
        asset_api_instance (client.AvatarsApi | client.ScenesApi | client.MotionsApi):
            An instance of asset_api, used to make API calls.
        list_method (Callable):
            The method used for listing one asset.
        state (AssetState):
            The current state of the asset.
    """

    asset_api: type[client.AvatarsApi | client.ScenesApi | client.MotionsApi]
    list_method_name: str
    list_all_method_name: str
    list_all_method: Optional[Callable]
    # TODO: None is only allowed because scenes don't have a list all function right now,
    # requires action in meshcapade-me-api

    def __init__(self, api_client: client.ApiClient):
        self.api_client = api_client
        self.asset_api_instance = self.asset_api(api_client)
        self.list_method = getattr(self.asset_api_instance, self.list_method_name)
        self.state = AssetState("EMPTY")

    @classmethod
    def get_ready_assets(cls: Type[T], api_client: client.ApiClient, show_max_assets: int) -> list[T]:
        """Returns a list of assets that have state READY."""
        # Get list_all_method using an instance of asset_api
        cls.list_all_method = getattr(cls.asset_api(api_client=api_client), cls.list_all_method_name)
        if cls.list_all_method is None:
            # TODO: Remove once scenes has list_all method
            raise RuntimeError("list_all_method must exist for asset type (doesn't for scenes yet)")
        assets: list[T] = []
        page = 1
        # iterate through pages and collect avatars with state ready until there are enough
        while len(assets) < show_max_assets:
            api_response = cls.list_all_method(limit=show_max_assets * 2, page=page)
            if api_response.data is None:
                raise click.ClickException("Response came back empty")
            if len(api_response.data) == 0:
                break
            for asset_response in api_response.data:
                asset = cls(api_client=api_client)
                asset.from_api_response(asset_response)
                if asset.state == AssetState.READY:
                    assets.append(asset)
                if len(assets) == show_max_assets:
                    break
            page += 1
        return assets

    @classmethod
    def select_asset(
        cls: Type[T], api_client: client.ApiClient, ready_assets: list[T], columns: list[str], prompt_message: str
    ) -> T:
        """Select asset from a list of assets for further action like download or motion blending"""
        column_keys = [key.lower().replace(" ", "_") for key in columns]
        # Print table using rich
        console = Console()
        table = Table(box=rich.box.ROUNDED, show_lines=True)

        # Add index column and all columns that were selected in list columns
        table.add_column("Number", justify="right", max_width=8)
        for key in columns:
            table.add_column(key, **ASSET_COLUMN_STYLES.get(key, {}), overflow="fold")

        # No relevant assets available for this account
        if len(ready_assets) == 0:
            raise click.ClickException("You have no relevant assets to select.")

        # Add row for each ready asset
        for i, asset in enumerate(ready_assets):
            table.add_row(
                Text(str(i), style="default on default"),
                *[Text(getattr(asset, key), style="default on default") for key in column_keys],
            )
        console.print(table)
        # Prompt for input to select an asset
        asset_number = click.prompt(prompt_message, type=int)
        asset = cls(api_client=api_client)
        asset.asset_id = ready_assets[asset_number].asset_id
        asset.name = ready_assets[asset_number].name
        return asset

    @classmethod
    def create_from_asset_id(cls: Type[T], api_client: client.ApiClient, asset_id) -> T:
        """Create an asset instance from a known asset id."""
        asset = cls(api_client=api_client)
        asset.asset_id = asset_id
        return asset

    def from_api_response(self, asset: AssetResponse):
        """Parse asset from api response and return with selected attributes."""
        if (
            asset.attributes is not None
            and asset.attributes.created_at is not None
            and asset.attributes.origin is not None
            and asset.attributes.state is not None
            and asset.id is not None
        ):
            self.created_at = datetime.fromtimestamp(asset.attributes.created_at).strftime("%Y/%m/%d %H:%M:%S")
            created_from_match = re.search("(?<=\\.).*", str(asset.attributes.origin))
            self.created_from = created_from_match.group() if created_from_match is not None else ""
            self.name = asset.attributes.name
            self.asset_id = asset.id
            self.state = asset.attributes.state

    def validate_asset_exists(self):
        """Checks if asset id is set, meaning asset exists in database"""
        if not hasattr(self, "asset_id"):
            raise RuntimeError("Asset does not exist in database yet, please check if asset creation finished.")

    def set_name(self, name):
        """Sets the name of the asset locally."""
        self.name = name

    def download(self, download_format, out_file):
        """Downloads asset.
        Requires self.download url, make sure to export asset if necessary before calling this method."""
        log.debug(f"Downloading asset in format {download_format}...")
        if not hasattr(self, "download_url"):
            raise RuntimeError("Download URL is not set, please check if asset is ready for download.")
        out_filename = (
            str(out_file)
            if out_file is not None
            else f"{get_timestamp()}_{self.name}.{download_format.lower()}"
            if (hasattr(self, "name") and self.name is not None and self.name != "")
            else f"{get_timestamp()}_{self.asset_id}.{download_format.lower()}"
            if (hasattr(self, "asset_id") and self.asset_id is not None)
            else f"{get_timestamp()}.{download_format.lower()}"
        )
        download_file(out_filename, self.download_url)

    def upload_source(self, source_file: str, uploader: Uploader):
        """Uploads a file to self.upload_url."""
        if not hasattr(self, "upload_url"):
            raise RuntimeError("Asset has no upload url, please request upload first.")

        uploader.upload(file_to_upload=source_file, upload_url=self.upload_url)

    def wait_for_processing(self, timeout: int, desired_state: AssetState, polling_interval=5):
        """Polls API for asset state, stops once it has reached the desired state or it times out."""
        timeout_tracker = TimeoutTracker(timeout)
        while timeout_tracker.is_active() and self.state != desired_state:
            self.update_state()
            log.info(f"Processing state: {self.state.name}")
            time.sleep(polling_interval)
        if self.state != desired_state:
            # didn't finish before it timed out
            raise click.ClickException("Process timed out.")

    def update_state(self):
        """Query API to sync state of local asset instance."""
        self.validate_asset_exists()
        # List one asset
        api_response = self.list()
        if api_response.data is None or api_response.data.attributes is None:
            raise click.ClickException("Response came back empty")
        state = api_response.data.attributes.state
        if state == AssetState.ERROR:
            raise click.ClickException("Processing finished with state ERROR")
        self.state = AssetState(state)

    def update_download_url(self):
        """Query API to sync download url of local asset instance"""
        self.validate_asset_exists()
        # List one asset
        api_response = self.list()
        if (
            api_response.data is None
            or api_response.data.attributes is None
            or api_response.data.attributes.url is None
            or api_response.data.attributes.url.path is None
        ):
            raise click.ClickException("Response came back empty")
        self.download_url = api_response.data.attributes.url.path

    def refresh(self):
        """Query API to sync local asset instance."""
        self.validate_asset_exists()
        # List one asset
        api_response = self.list()
        if api_response.data is None or api_response.data.attributes is None:
            raise click.ClickException("Response came back empty")
        self.state = AssetState(api_response.data.attributes.state)
        self.name = str(api_response.data.attributes.name)

    def list(self):
        """ "Lists one asset and handles error if one occurs."""
        try:
            return self.list_method(self.asset_id)
        except Exception as e:
            raise click.ClickException(f"Exception when calling {self.list_method.__qualname__}: %s\n" % e) from e

    def set_asset_id(self, asset_id):
        """Sets asset id of local asset instance."""
        self.asset_id = asset_id


class CreateFromParametersMixin:
    """Mixin class to add creation from parameters functionality."""

    def create_from_parameters(
        self,
        method: Callable,
        request_parameters: client.SchemasBetasAvatarRequest
        | client.SchemasMeasurementAvatarRequest
        | client.SchemasMotionBlendRequest,
        timeout: int,
    ):
        """Creates asset from parameters like measurements. Makes API call to create an asset from parameters,
        sets local asset id and waits for asset creation to finish."""
        if not isinstance(self, Asset):
            raise TypeError("create_from_parameters should only be used with a subclass of Asset.")
        try:
            # Calls API to create an asset from parameters
            api_response = method(request_parameters)
        except Exception as e:
            raise click.ClickException(f"Exception when calling {method.__qualname__}: %s\n" % e) from e
        if api_response.data is None or api_response.data.attributes is None or api_response.data.id is None:
            raise click.ClickException("Creation response came back empty")
        self.asset_id: str = str(api_response.data.id)
        self.update_state()
        # Wait for processing to finish
        try:
            self.wait_for_processing(
                timeout=timeout,
                desired_state=AssetState(AssetState.READY),
            )
        except click.ClickException as e:
            raise click.ClickException("Exception while processing: %s\n" % e) from e
        log.info(f"Creation finished with state {self.state.name}")


class CreateFromSourceMixin:
    """Mixin class to add creation from source (e.g. images) functionality."""

    def request_asset_from_source(
        self,
        initialize_asset_method: Callable,
        request_parameters: Optional[client.DocschemasDocCreateFromSMPLRequest] = None,
    ) -> None:
        """Initiate avatar from source creation. Makes API call to initialize asset creation, sets local asset id."""
        try:
            api_response = (
                initialize_asset_method() if request_parameters is None else initialize_asset_method(request_parameters)
            )
        except Exception as e:
            raise click.ClickException(
                f"Exception when calling {initialize_asset_method.__qualname__}: %s\n" % e
            ) from e
        if api_response.data is None:
            raise click.ClickException("Initializing asset response came back empty")
        self.asset_id = str(api_response.data.id)
        log.debug(f"AssetID: {self.asset_id}")
        if api_response.data.attributes is not None and api_response.data.attributes.url is not None:
            self.upload_url = str(api_response.data.attributes.url.path)

    def request_source_upload(self, request_upload_method: Callable) -> None:
        """Request source upload URL for asset creation, sets it as attribute to be used later."""
        try:
            api_response = request_upload_method(self.asset_id)
        except Exception as e:
            raise click.ClickException(f"Exception when calling {request_upload_method.__qualname__}: %s\n" % e) from e

        if (
            api_response.data is None
            or api_response.data.attributes is None
            or api_response.data.attributes.url is None
        ):
            raise click.ClickException("Requesting upload response came back empty")
        self.upload_url = str(api_response.data.attributes.url.path)

    def create_from_source(
        self,
        initialize_asset_method: Callable,
        request_upload_method: Callable,
        fit_to_source_method: Callable,
        input: str,
        request_parameters: client.SchemasBetasAvatarRequest
        | client.SchemasMeasurementAvatarRequest
        | client.DocschemasDocAFIInputs
        | client.DocschemasDocAFVInputs
        | client.DocschemasDocAFSInputs
        | client.DocschemasDocSceneFromVideoInputs,
        uploader: Uploader,
        timeout: int,
    ):
        """Creates asset from source like images. Initializes asset, requests upload url, uploads the source file,
        triggers fitting to source and waits for the creation to finish."""
        if not isinstance(self, Asset):
            raise TypeError("create_from_parameters should only be used with a subclass of Asset.")

        log.debug("Initializing asset from source...")
        self.request_asset_from_source(initialize_asset_method=initialize_asset_method)

        log.debug("Requesting upload url...")
        self.request_source_upload(request_upload_method=request_upload_method)

        log.debug(f"Uploading source file {input}...")
        self.upload_source(source_file=input, uploader=uploader)

        # Fit to source
        try:
            log.debug("Fitting to source...")
            fit_to_source_method(self.asset_id, request_parameters)
        except Exception as e:
            raise click.ClickException(f"Exception when calling {request_upload_method.__qualname__}: %s\n" % e) from e

        # Wait for processing to finish
        try:
            self.wait_for_processing(
                timeout=timeout,
                desired_state=AssetState(AssetState.READY),
            )
        except click.ClickException as e:
            raise click.ClickException("Exception while processing: %s\n" % e) from e
        log.info(f"Creation finished with state {self.state.name}")


class ExportMixin:
    """Mixin class to add exporting functionality. Assets need to have an asset_api_instance."""

    def export(
        self,
        export_method: Callable,
        export_parameters: client.DocschemasDocExportInputs,
        timeout: int,
        polling_interval=5,
    ):
        """Export asset. Calls export API endpoint and waits for processing to finish."""
        timeout_tracker = TimeoutTracker(timeout)
        download_url = None
        while not download_url and not timeout_tracker.timed_out():
            download_url = self.try_get_download_url(export_method, export_parameters)
            # if state is still processing or awaiting processing, call export enpoint again after waiting a bit
            time.sleep(polling_interval)
        if download_url is None:
            # export didn't return anything before it timed out
            raise click.ClickException("Export timed out.")
        self.download_url = download_url

    def try_get_download_url(
        self, export_method: Callable, export_parameters: client.DocschemasDocExportInputs
    ) -> Optional[str]:
        """Call export endpoint to trigger asset export and check on state."""
        try:
            # Call export endpoint
            if not hasattr(self, "asset_id"):
                raise AttributeError(
                    f"{self.__class__.__qualname__} must have an asset_id to export the asset. "
                    "Please check if asset creation has finished.",
                )
            api_response = export_method(self.asset_id, export_parameters)
        except Exception as e:
            raise click.ClickException(f"Exception when calling {export_method.__qualname__}: %s\n" % e) from e
        if (
            api_response.data is None
            or api_response.data.attributes is None
            or api_response.data.attributes.url is None
        ):
            raise click.ClickException("Export response came back empty")
        # get current processing state and download url from api response
        state = api_response.data.attributes.state
        download_url = str(api_response.data.attributes.url.path)
        if state == AssetState.READY:
            # export finished with state ready, return results
            log.info(f"Exporting finished with state {AssetState(state).name}")
            return download_url
        elif state == AssetState.ERROR:
            raise click.ClickException("Exporting finished with state ERROR")
        else:
            log.info(f"Exporting state: {AssetState(state).name}")
            return None
