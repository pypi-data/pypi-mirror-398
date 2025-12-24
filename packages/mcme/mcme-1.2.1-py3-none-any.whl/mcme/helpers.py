import requests
import tomli
import os
import click
import time
from datetime import datetime
from .logger import log
from .constants import (
    MIME_TYPES,
)


def load_config(config: str) -> dict[str, str]:
    """Load config"""
    with open(config, mode="rb") as conf:
        return tomli.load(conf)


def create_parent_dir_if_not_exists(keycloak_file: str) -> None:
    parent_dir = os.path.dirname(keycloak_file)
    if not os.path.exists(parent_dir):
        os.makedirs(parent_dir, exist_ok=True)


def parse_betas(ctx: click.Context, param: click.Parameter, value: str, is_smplx: bool) -> list[float]:
    """Parse betas from command line"""
    shape_params = [float(x) for x in value.strip("[").strip("]").split(",")] if value is not None else []
    if is_smplx and value is not None and len(shape_params) != 10:
        raise click.BadArgumentUsage("If supplied, shape parameters have to have exactly 10 values.")
    return shape_params


def validate_export_parameter(ctx: click.Context, param: click.Parameter, value: str) -> str:
    """Check export parameters for direct download after creation"""
    if ctx.params["download_format"] is None:
        if value is not None:
            raise click.BadOptionUsage(
                str(param.name),
                f"""Please use option --download_format if you want to download the avatar or scene. 
                Otherwise, please leave out option --{param.name}.""",
                ctx=None,
            )
    # Set pose default value if download is requested
    elif param.name == "pose" and value is None:
        return "A"
    return value


def validate_auth_method(username, password, token):
    if token is not None and (username is not None or password is not None):
        raise click.BadOptionUsage("Please don't provide usename or password when providing a token.")


def download_file(out_filename: str, download_url: str) -> None:
    """Download file using presigned aws s3 url."""
    with open(out_filename, "wb") as file:
        try:
            stream = requests.get(download_url, stream=True, timeout=60)
            stream.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise click.ClickException(str(err)) from err
        for chunk in stream.iter_content(chunk_size=1024 * 1024):
            file.write(chunk)
    log.info(f"Downloaded file to {out_filename}")


class TimeoutTracker(object):
    """Helper class for tracking timeout length"""

    def __init__(self, timeout_length):
        self.start_time = time.time()
        self.timeout = timeout_length

    def reset(self):
        self.start_time = time.time()

    def timed_out(self):
        return time.time() - self.start_time > self.timeout * 60

    def is_active(self):
        return not self.timed_out()


def get_timestamp():
    """Get timestamp"""
    return datetime.now().strftime("%Y%m%d%H%M%S")


class Uploader:
    """Class for uploading files that can be mocked"""

    def upload(self, file_to_upload: str, upload_url: str) -> None:
        """Upload an image to given url"""
        content_type = MIME_TYPES[file_to_upload.split(".")[-1].lower()]
        with open(file_to_upload, "rb") as input:
            upload_response = requests.put(upload_url, data=input, headers={"Content-Type": content_type})
        upload_response.raise_for_status()


class LocalUploader:
    """Class for uploading files that can be mocked"""

    def upload(self, file_to_upload: str, upload_url: str) -> None:
        # TODO(dheid)
        # Due to time constraints and to enable debugging this is here for now
        # Make this configurable and move it back into the Uploader above
        # Should not always be the case, and only be done if we target the local mcme stack
        # See mcme/batch_create.py line 71 and replace that with Uploader() when done
        upload_url = upload_url.replace("localstack", "localhost")
        """Upload an image to given url"""
        content_type = MIME_TYPES[file_to_upload.split(".")[-1].lower()]
        with open(file_to_upload, "rb") as input:
            upload_response = requests.put(upload_url, data=input, headers={"Content-Type": content_type})
        upload_response.raise_for_status()


def get_measurements_dict(
    height=None,
    weight=None,
    bust_girth=None,
    ankle_girth=None,
    thigh_girth=None,
    waist_girth=None,
    armscye_girth=None,
    top_hip_girth=None,
    neck_base_girth=None,
    shoulder_length=None,
    lower_arm_length=None,
    upper_arm_length=None,
    inside_leg_height=None,
) -> dict[str, float]:
    """Helper for assembling input measurements"""
    measurements = {
        "Height": height,
        "Weight": weight,
        "Bust_girth": bust_girth,
        "Ankle_girth": ankle_girth,
        "Thigh_girth": thigh_girth,
        "Waist_girth": waist_girth,
        "Armscye_girth": armscye_girth,
        "Top_hip_girth": top_hip_girth,
        "Neck_base_girth": neck_base_girth,
        "Shoulder_length": shoulder_length,
        "Lower_arm_length": lower_arm_length,
        "Upper_arm_length": upper_arm_length,
        "Inside_leg_height": inside_leg_height,
    }
    for key, value in measurements.copy().items():
        if value is None:
            del measurements[key]
    return measurements
