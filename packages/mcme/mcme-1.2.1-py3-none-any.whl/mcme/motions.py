import os
import tempfile

import click
import requests
import openapi_client as client
from .logger import log
from openapi_client import PostgresqlBuildState as BuildState
from smplcodec import SMPLCodec
import logging
from .assets import Asset

# Remove handlers added by smplcodec
logging.getLogger().handlers = []

motion_parameters = ["body_translation", "body_pose", "head_pose", "left_hand_pose", "right_hand_pose"]


class Motion(Asset):
    """Represents a motion asset.

    This class inherits from Asset to use functionality no unique to motions.
    A motion can be retrieved by text prompt using the /motions/search API endpoint.
    It can then be trimmed to the relevant frames, creating a temporary .smpl file that can be used for avatar creation.
    """

    asset_api = client.MotionsApi
    list_method_name = "describe_motions"
    list_all_method_name = "list_motions"

    def find_from_text(self, prompt: str) -> None:
        """Finding motion and downloading motion .smpl file as a temporary file"""
        find_from_text_method = client.SearchMotionsApi(self.api_client).submit_search_motions
        request_parameters = client.ServicesSearchMotionsOptions(num_motions=1, text=prompt)
        try:
            # Search for motion using prompt
            api_response = find_from_text_method(options=request_parameters)
        except Exception as e:
            raise click.ClickException(f"Exception when calling {find_from_text_method.__qualname__}: %s\n" % e) from e
        if api_response.data is None or api_response.data.attributes is None:
            raise click.ClickException("Searching for motion response came back empty")
        log.info(f"Creating motion from text finished with state {BuildState(api_response.data.attributes.state).name}")
        if (
            api_response.included is None
            or len(api_response.included) == 0
            or api_response.included[0] is None
            or api_response.included[0].attributes is None
            or api_response.data is None
            or api_response.data.attributes is None
            or api_response.data.attributes.result is None
            or api_response.data.attributes.result.motions is None
            or len(api_response.data.attributes.result.motions) == 0
            or api_response.data.attributes.result.motions[0] is None
            or api_response.data.attributes.result.motions[0].start_time is None
            or api_response.data.attributes.result.motions[0].end_time is None
        ):
            raise click.ClickException("No motion found.")

        self.smpl_download_url = api_response.included[0].attributes.url.path
        log.debug(f"Motion found: {api_response.data.attributes.result.motions[0].path_key}")

        # Save start and end times of motion for later trimming
        self.start = api_response.data.attributes.result.motions[0].start_time
        self.end = api_response.data.attributes.result.motions[0].end_time

    def download_temp_smpl(self) -> None:
        """Downloads the smpl file as temporary file"""
        if not hasattr(self, "smpl_download_url"):
            raise RuntimeError("smpl download URL is not set, please check if motion is ready for download.")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".smpl") as file:
            self.smpl_file = file.name
            try:
                stream = requests.get(self.smpl_download_url, stream=True, timeout=60)
                stream.raise_for_status()
            except requests.exceptions.HTTPError as err:
                raise click.ClickException(str(err)) from err
            for chunk in stream.iter_content(chunk_size=1024 * 1024):
                file.write(chunk)

    def trim(self, start=None, end=None) -> None:
        """Trimming motion to relevant part as indicated in search motions response"""
        if start is None:
            start = self.start
        if end is None:
            end = self.end
        smpl_motion = SMPLCodec.from_file(self.smpl_file)

        # set original file as trimmed file if trimming is unnecessary
        if end == smpl_motion.frame_count / smpl_motion.frame_rate:
            log.debug("Motion trimming not necessary.")
            self.trimmed_smpl_file = self.smpl_file

        # else, write trimmed temp file
        first_frame = int(start * smpl_motion.frame_rate)
        last_frame = int(end * smpl_motion.frame_rate)
        # update frame count to prevent smplcodec validation from failing
        setattr(smpl_motion, "frame_count", last_frame - first_frame)
        for attr in motion_parameters:
            if hasattr(smpl_motion, attr):
                frames = getattr(smpl_motion, attr)
                trimmed_frames = frames[first_frame:last_frame]
                setattr(smpl_motion, attr, trimmed_frames)

        temp = tempfile.NamedTemporaryFile(delete=False, suffix="_trimmed.smpl")
        try:
            self.trimmed_smpl_file = temp.name
            # remove codec_version if present since it is not compatible with the API (yet)
            if "codec_version" in smpl_motion.__dataclass_fields__:
                del smpl_motion.__dataclass_fields__["codec_version"]
            smpl_motion.write(temp.name)
        finally:
            temp.close()

    def cleanup_temp_smpl(self):
        """ "Deleting temporary .smpl file containing the downloaded motion"""
        os.remove(self.smpl_file)
        if os.path.isfile(self.trimmed_smpl_file):
            os.remove(self.trimmed_smpl_file)
