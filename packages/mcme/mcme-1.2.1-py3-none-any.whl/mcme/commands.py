import functools
import os
from typing import Any, Optional, OrderedDict

from .state import State
import openapi_client as client
import click
from os import path
from .logger import log
from .auth import Authenticator
from .helpers import (
    load_config,
    parse_betas,
    validate_auth_method,
    validate_export_parameter,
    get_measurements_dict,
    Uploader,
)
from .motions import Motion

from .scenes import Scene
from .user import request_user_info
from functools import partial
from .avatars import Avatar


CURRENT_DIR = path.dirname(path.abspath(__file__))
DEFAULT_CONFIG = path.join(CURRENT_DIR, "../configs/prod.toml")


class CustomOption(click.Option):
    """Custom option class that adds the attribute help_group to the option"""

    def __init__(self, *args, **kwargs):
        self.help_group = kwargs.pop("help_group", None)
        super().__init__(*args, **kwargs)


class CustomCommand(click.Command):
    """Custom command class that can be used to format the help text."""

    def format_options(self, ctx, formatter):
        """Writes options into the help text. Separates them by help_group"""
        opts = OrderedDict([("Options", [])])
        for param in self.get_params(ctx):
            rv = param.get_help_record(ctx)
            if rv is not None:
                if hasattr(param, "help_group"):
                    opts.setdefault(param.help_group, []).append(rv)
                else:
                    opts["Options"].append(rv)

        for help_group, param in opts.items():
            with formatter.section(help_group):
                formatter.write_dl(param)


def avatar_download_format(func):
    """Decorator to add avatar download format to a command."""

    @click.option(
        "--download-format",
        cls=CustomOption,
        help_group="Avatar download options",
        type=click.Choice(["OBJ", "FBX", "GLB"], case_sensitive=False),
        is_eager=True,
        help="Format for downloading avatar.",
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def avatar_download_params(func):
    """Decorator to add avatar download options to a command."""

    @click.option(
        "--pose",
        cls=CustomOption,
        help_group="Avatar download options",
        type=click.Choice(["T", "A", "I", "SCAN"], case_sensitive=False),
        callback=validate_export_parameter,
        help="""Pose the downloaded avatar should be in. SCAN is not applicable for avatars created from betas or 
        measurements since it corresponds to a captured pose or motion.""",
    )
    @click.option(
        "--animation",
        cls=CustomOption,
        help_group="Avatar download options",
        type=click.Choice(["a-salsa"], case_sensitive=False),
        callback=validate_export_parameter,
        help="Animation for the downloaded avatar",
    )
    @click.option(
        "--compatibility-mode",
        cls=CustomOption,
        help_group="Avatar download options",
        type=click.Choice(["DEFAULT", "OPTITEX", "UNREAL"], case_sensitive=False),
        callback=validate_export_parameter,
        help="Adjust output for compatibility with selected software.",
    )
    @click.option(
        "--out-file",
        cls=CustomOption,
        help_group="Avatar download options",
        type=click.Path(dir_okay=False),
        callback=validate_export_parameter,
        help="File to save created avatar mesh to",
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


@click.group()
@click.pass_context
@click.option(
    "--config",
    type=click.Path(exists=True),
    default=os.environ.get("MCME_CONFIG_PATH", DEFAULT_CONFIG),
    help="Path to config file. Alternatively, set env variable MCME_CONFIG_PATH.",
)
@click.option(
    "--username",
    default=lambda: os.environ.get("MCME_USERNAME"),
    help="Username for authentication with Meshcapade.me. Alternatively, set env variable MCME_USERNAME.",
)
@click.option(
    "--password",
    default=lambda: os.environ.get("MCME_PASSWORD"),
    help="Password for authentication with Meshcapade.me. Alternatively, set env variable MCME_PASSWORD.",
)
@click.option(
    "--token",
    type=str,
    default=lambda: os.environ.get("MCME_TOKEN"),
    help="Authentication token retrieved from Meshcapade.me. Alternatively, set env variable MCME_TOKEN. "
    "Please don't set username and password when setting a token.",
)
def cli(ctx: click.Context, username: str, password: str, config: str, token: str) -> None:
    """
    Command-line interface for the Meshcapade.me API.
    """
    log.debug(f"Using config file: {config}")
    ctx.ensure_object(dict)
    ctx.obj["config"] = load_config(config)
    ctx.obj["keycloak_token_file"] = os.path.expanduser(ctx.obj["config"]["cli_state"]["keycloak_token_file"])
    validate_auth_method(username, password, token)
    ctx.obj["username"] = username
    ctx.obj["password"] = password
    ctx.obj["token"] = token
    # construct api client
    configuration = client.Configuration(host=ctx.obj["config"]["api"]["host"])
    ctx.obj["api_client"] = client.ApiClient(configuration)
    # set log level if specified in config
    if "logging" in ctx.obj["config"] and "level" in ctx.obj["config"]["logging"]:
        log.setLevel(ctx.obj["config"]["logging"]["level"].upper())


def require_auth(func):
    """Decorator to authenticate with the meshcapade.me API. Only required for commands making API calls."""

    @functools.wraps(func)
    @click.pass_context
    def wrapper(ctx: click.Context, *args, **kwargs):
        authenticator = Authenticator(auth_config=ctx.obj["config"]["auth"])
        state = State(ctx.obj["keycloak_token_file"])
        username = ctx.obj["username"]
        password = ctx.obj["password"]
        token = ctx.obj["token"]
        api_client = ctx.obj["api_client"]
        if username:
            state.active_user = username
        if token is not None:
            log.debug("Used token provided by user")
            username = authenticator.get_user_from_token(token=token)  # raises an error if token is invalid
            state.active_user = username
            state.set_active_keycloak_token(token)
            api_client.configuration.access_token = token
        elif (token := state.active_access_token) is not None and authenticator.is_access_token_valid(token):
            log.debug("Used saved auth token.")
            api_client.configuration.access_token = token
        else:
            log.debug("Authenticated with username and password.")
            keycloak_token = authenticator.authenticate(username, password)
            state.set_active_keycloak_token(keycloak_token)
            api_client.configuration.access_token = state.active_access_token
        return func(*args, **kwargs)

    return wrapper


@cli.result_callback()
@click.pass_context
def close_api_client(ctx: click.Context, result: Any, **kwargs):
    """Cleanup function that closes the api client."""
    ctx.obj["api_client"].close()


@cli.group()
@click.pass_context
@require_auth
def create(ctx: click.Context) -> None:
    """
    Create avatars or scenes. Please be aware that these commands cost credits.
    """
    # all create avatar operations need keycloak authentication


@cli.group()
@click.pass_context
@require_auth
def download(ctx: click.Context) -> None:
    """
    Download avatars or scenes.
    """
    # all download operations need keycloak authentication


@create.command(cls=CustomCommand, name="from-betas")
@click.pass_context
@click.option(
    "--gender",
    type=click.Choice(client.EnumsGender.enum_values(), case_sensitive=False),
    help="Gender of created avatar",
)
@click.option(
    "--betas",
    type=click.UNPROCESSED,
    callback=partial(parse_betas, is_smplx=False),
    help='Beta values. Supply like 0.1,0.2 or "[0.1,0.2]"',
)
@click.option("--name", type=str, default="avatar_from_betas", help="Name of created avatar")
@click.option(
    "--model-version",
    type=click.Choice(client.EnumsModelVersion.enum_values(), case_sensitive=False),
    help="Model version",
)
@avatar_download_format
@avatar_download_params
def create_from_betas(
    ctx: click.Context,
    gender: Optional[client.EnumsGender],
    betas: list[float],
    name: str,
    model_version: Optional[client.EnumsModelVersion],
    download_format: str,
    pose: str,
    animation: str,
    compatibility_mode: str,
    out_file: click.Path,
) -> None:
    """Create avatar from betas."""
    timeout = ctx.obj["config"]["cli"]["timeout"]
    avatar = Avatar(api_client=ctx.obj["api_client"])
    avatar.from_betas(
        betas=betas,
        gender=gender,
        name=name,
        model_version=model_version,
        poseName="",
    )
    log.info(f"AssetID: {avatar.asset_id}")

    # Exit here if avatar should not be downloaded
    if download_format:
        avatar.export_avatar(download_format, pose, animation, compatibility_mode, timeout)
        avatar.download(download_format=download_format, out_file=out_file)


@create.command(cls=CustomCommand, name="from-measurements")
@click.pass_context
@click.option(
    "--gender",
    type=click.Choice(client.EnumsGender.enum_values(), case_sensitive=False),
    required=True,
    help="Gender of created avatar",
)
@click.option("--name", type=str, default="avatar_from_measurements", help="Name of created avatar")
@click.option("--height", type=float, help="Height")
@click.option("--weight", type=float, help="Weight")
@click.option("--bust-girth", type=float, help="Bust girth")
@click.option("--ankle-girth", type=float, help="Ankle girth")
@click.option("--thigh-girth", type=float, help="Thigh girth")
@click.option("--waist-girth", type=float, help="Waist girth")
@click.option("--armscye-girth", type=float, help="Armscye girth")
@click.option("--top-hip-girth", type=float, help="Top hip girth")
@click.option("--neck-base-girth", type=float, help="Neck base girth")
@click.option("--shoulder-length", type=float, help="Shoulder length")
@click.option("--lower-arm-length", type=float, help="Lower arm length")
@click.option("--upper-arm-length", type=float, help="Upper arm length")
@click.option("--inside-leg-height", type=float, help="Inside leg height")
@click.option(
    "--model-version",
    type=click.Choice(client.EnumsModelVersion.enum_values(), case_sensitive=False),
    help="Model version",
)
@avatar_download_format
@avatar_download_params
def create_from_measurements(
    ctx: click.Context,
    gender: Optional[client.EnumsGender],
    name: str,
    height,
    weight,
    bust_girth,
    ankle_girth,
    thigh_girth,
    waist_girth,
    armscye_girth,
    top_hip_girth,
    neck_base_girth,
    shoulder_length,
    lower_arm_length,
    upper_arm_length,
    inside_leg_height,
    model_version: Optional[client.EnumsModelVersion],
    download_format: str,
    pose: str,
    animation: str,
    compatibility_mode: str,
    out_file: click.Path,
) -> None:
    """Create avatar from measurements."""
    # Create avatar from measurements
    measurements = get_measurements_dict(
        height,
        weight,
        bust_girth,
        ankle_girth,
        thigh_girth,
        waist_girth,
        armscye_girth,
        top_hip_girth,
        neck_base_girth,
        shoulder_length,
        lower_arm_length,
        upper_arm_length,
        inside_leg_height,
    )
    timeout = ctx.obj["config"]["cli"]["timeout"]
    avatar = Avatar(api_client=ctx.obj["api_client"])
    avatar.from_measurements(
        measurements=measurements, gender=gender, name=name, model_version=model_version, timeout=timeout
    )

    log.info(f"AssetID: {avatar.asset_id}")

    # Exit here if avatar should not be downloaded
    if download_format:
        avatar.export_avatar(download_format, pose, animation, compatibility_mode, timeout)
        avatar.download(download_format=download_format, out_file=out_file)


@create.command(cls=CustomCommand, name="from-images")
@click.pass_context
@click.option(
    "--gender",
    type=click.Choice(client.EnumsGender.enum_values(), case_sensitive=False),
    help="Gender of created avatar",
)
@click.option("--name", type=str, default="avatar_from_images", help="Name of created avatar")
@click.option("--input", required=True, type=click.Path(dir_okay=False, exists=True), help="Path to input image")
@click.option("--height", type=int, help="Height of the person in the image")
@click.option("--weight", type=int, help="Weight of the person in the image")
@click.option(
    "--image-mode",
    type=click.Choice(["AFI", "BEDLAM_CLIFF"], case_sensitive=False),
    default="AFI",
    help="Mode for avatar creation",
)
@avatar_download_format
@avatar_download_params
def create_from_images(
    ctx: click.Context,
    gender: Optional[client.EnumsGender],
    name: str,
    input: str,
    height: int,
    weight: int,
    image_mode: str,
    download_format: str,
    pose: str,
    animation: str,
    compatibility_mode: str,
    out_file: click.Path,
) -> None:
    """Create avatar from images."""
    uploader = Uploader()
    timeout = ctx.obj["config"]["cli"]["timeout"]
    avatar = Avatar(api_client=ctx.obj["api_client"])
    avatar.from_images(
        gender=gender,
        name=name,
        input=input,
        height=height,
        weight=weight,
        image_mode=image_mode,
        uploader=uploader,
        timeout=timeout,
    )

    log.info(f"AssetID: {avatar.asset_id}")

    # Exit here if avatar should not be downloaded
    if download_format:
        avatar.export_avatar(download_format, pose, animation, compatibility_mode, timeout)
        avatar.download(download_format=download_format, out_file=out_file)


@create.command(cls=CustomCommand, name="from-scans")
@click.pass_context
@click.option(
    "--gender",
    type=click.Choice(client.EnumsGender.enum_values(), case_sensitive=False),
    help="Gender of created avatar",
)
@click.option("--name", type=str, default="avatar_from_scans", help="Name of created avatar")
@click.option("--input", type=click.Path(dir_okay=False, exists=True), help="Path to input image")
@click.option("--init-pose", type=str, help="Pose for initialization")
@click.option("--up-axis", type=str, help="Up axis")
@click.option("--look-axis", type=str, help="Look axis")
@click.option("--input-units", type=str, help="Input units of scan")
@avatar_download_format
@avatar_download_params
def create_from_scans(
    ctx: click.Context,
    gender: Optional[client.EnumsGender],
    name: str,
    input: str,
    init_pose: str,
    up_axis: str,
    look_axis: str,
    input_units: str,
    download_format: str,
    pose: str,
    animation: str,
    compatibility_mode: str,
    out_file: click.Path,
) -> None:
    """Create avatar from scans."""
    uploader = Uploader()
    timeout = ctx.obj["config"]["cli"]["timeout"]
    avatar = Avatar(api_client=ctx.obj["api_client"])
    avatar.from_scans(
        gender=gender,
        name=name,
        input=input,
        init_pose=init_pose,
        up_axis=up_axis,
        look_axis=look_axis,
        input_units=input_units,
        uploader=uploader,
        timeout=timeout,
    )

    log.info(f"AssetID: {avatar.asset_id}")

    # Exit here if avatar should not be downloaded
    if download_format:
        avatar.export_avatar(download_format, pose, animation, compatibility_mode, timeout)
        avatar.download(download_format=download_format, out_file=out_file)


@create.command(cls=CustomCommand, name="from-video")
@click.pass_context
@click.option("--name", type=str, default="scene_from_video", help="Name of created scene")
@click.option("--input", type=click.Path(dir_okay=False, exists=True), required=True, help="Path to input video")
@click.option(
    "--max-person-count",
    type=int,
    default=1,
    help="Specify the maximum number of people you want to track in this video",
)
@click.option(
    "--model-version",
    type=click.Choice(client.EnumsModelVersion.enum_values(), case_sensitive=False),
    help="Model version",
)
@click.option("--lock-feet", type=bool, is_flag=True, help="Enable foot locking")
@click.option(
    "--download-format",
    cls=CustomOption,
    help_group="Download options",
    type=click.Choice(["FBX", "GLB", "USD"], case_sensitive=False),
    help="Format for downloading scene",
)
@click.option(
    "--compatibility-mode",
    cls=CustomOption,
    help_group="Download options",
    type=click.Choice(["DEFAULT", "OPTITEX", "UNREAL"], case_sensitive=False),
    callback=validate_export_parameter,
    help="Adjust output for compatibility with selected software.",
)
@click.option(
    "--out-file",
    cls=CustomOption,
    help_group="Download options",
    type=click.Path(dir_okay=False),
    callback=validate_export_parameter,
    help="File to save created scene to",
)
def create_from_video(
    ctx: click.Context,
    name: str,
    input: str,
    max_person_count: bool,
    model_version: Optional[client.EnumsModelVersion],
    lock_feet: bool,
    download_format: str,
    compatibility_mode: str,
    out_file: click.Path,
) -> None:
    """Create scene from video. If you want to create a scene with multiple avatars,
    please set --max-person-count > 1."""
    uploader = Uploader()
    timeout = ctx.obj["config"]["cli"]["timeout"]
    # Create scene
    log.debug("Creating scene from video...")
    scene = Scene(api_client=ctx.obj["api_client"])
    scene.from_video(
        name=name,
        input=input,
        max_person_count=max_person_count,
        model_version=model_version,
        lock_feet=lock_feet,
        uploader=uploader,
        timeout=timeout,
    )
    log.info(f"AssetID: {scene.asset_id}")
    if download_format:
        scene.export_scene(
            download_format=download_format,
            compatibility_mode=compatibility_mode,
            avatarSceneIndex=-1,
            timeout=timeout,
        )
        scene.download(download_format=download_format, out_file=out_file)


@create.command(cls=CustomCommand, name="from-text")
@click.pass_context
@click.option("--prompt", type=str, required=True, help="Text prompt describing desired motion")
@click.option("--name", type=str, help="Name of created avatar")
@avatar_download_format
@avatar_download_params
def create_from_text(
    ctx: click.Context,
    prompt: str,
    name: str,
    download_format: str,
    pose: str,
    animation: str,
    compatibility_mode: str,
    out_file: click.Path,
) -> None:
    """Create avatar with motion from text prompt."""
    timeout = ctx.obj["config"]["cli"]["timeout"]

    if name is None:
        name = prompt.replace(" ", "_")

    motion = Motion(api_client=ctx.obj["api_client"])

    # Search for motion by prompt and save temporary smpl file
    motion.find_from_text(prompt=prompt)
    motion.download_temp_smpl()
    # Trim motion to relevant frames
    motion.trim()

    # Use found and trimmed motion .smpl file to create avatar
    uploader = Uploader()
    avatar = Avatar(api_client=ctx.obj["api_client"])
    avatar.from_smpl(motion.trimmed_smpl_file, name=name, uploader=uploader, timeout=timeout)

    log.info(f"AssetID: {avatar.asset_id}")

    # Delete temporary motion .smpl file
    motion.cleanup_temp_smpl()

    # Exit here if avatar should not be downloaded
    if download_format:
        avatar.export_avatar(download_format, pose, animation, compatibility_mode, timeout)
        avatar.download(download_format=download_format, out_file=out_file)


# TODO: reimplement batch processing


@download.command(name="avatar")
@click.pass_context
@click.option("--asset-id", type=str, help="Asset id of avatar to be downloaded")
@click.option(
    "--show-max-avatars",
    type=int,
    default=10,
    help="Maximum number of created avatars to show (most recent ones are shown first)",
)
@avatar_download_format
@avatar_download_params
def export_and_download_avatar(
    ctx: click.Context,
    download_format: str,
    pose: str,
    animation: str,
    compatibility_mode: str,
    out_file: click.Path,
    asset_id: str,
    show_max_avatars: int,
) -> None:
    """
    Export avatar. You can supply an asset id or select from a list of created avatars.
    """
    # show avatar selection dialogue if asset id is not supplied
    if asset_id is None:
        ready_assets = Avatar.get_ready_assets(api_client=ctx.obj["api_client"], show_max_assets=show_max_avatars)
        avatar = Avatar.select_asset(
            api_client=ctx.obj["api_client"],
            ready_assets=ready_assets,
            columns=["Name", "Asset ID", "Created from", "Created at"],
            prompt_message="Number of avatar to download",
        )
    else:
        avatar = Avatar(ctx.obj["api_client"])
        avatar.set_asset_id(asset_id=asset_id)
        avatar.refresh()

    # Export avatar
    timeout = ctx.obj["config"]["cli"]["timeout"]
    avatar.export_avatar(
        download_format=download_format,
        pose=pose,
        animation=animation,
        compatibility_mode=compatibility_mode,
        timeout=timeout,
    )

    avatar.download(download_format=download_format, out_file=out_file)


@download.command(name="scene")
@click.pass_context
@click.option("--asset-id", type=str, help="Asset id of avatar to be downloaded")
@click.option(
    "--show-max-scenes",
    type=int,
    default=10,
    help="Maximum number of created scenes to show (most recent ones are shown first)",
)
@click.option(
    "--download-format",
    type=click.Choice(["GLB", "USD", "FBX"], case_sensitive=False),
    default="GLB",
    is_eager=True,
    help="Format for downloading avatar.",
)
@click.option(
    "--avatar-scene-index",
    type=int,
    default=-1,
    help="0-based index of the avatar to download. If omitted, a scene with all avatars is downloaded.",
)
@click.option(
    "--out-file",
    type=click.Path(dir_okay=False),
    help="File to save created scene to",
)
@click.option(
    "--compatibility-mode",
    cls=CustomOption,
    help_group="Download options",
    type=click.Choice(["DEFAULT", "OPTITEX", "UNREAL"], case_sensitive=False),
    callback=validate_export_parameter,
    help="Adjust output for compatibility with selected software. \
        Note that OPTITEX mode is only available for FBX format.",
)
def export_and_download_scene(
    ctx: click.Context,
    asset_id: str,
    show_max_scenes: int,
    download_format: str,
    avatar_scene_index: int,
    out_file: click.Path,
    compatibility_mode: str,
) -> None:
    """
    Export scene. You can supply an asset id or select from a list of created scenes.
    """
    # show avatar selection dialogue if asset id is not supplied
    if asset_id is None:
        ready_assets = Scene.get_ready_assets(api_client=ctx.obj["api_client"], show_max_assets=show_max_scenes)
        scene = Scene.select_asset(
            api_client=ctx.obj["api_client"],
            ready_assets=ready_assets,
            columns=["Name", "Asset ID", "Created from", "Created at"],
            prompt_message="Number of scene to download",
        )
    else:
        scene = Scene(ctx.obj["api_client"])
        scene.set_asset_id(asset_id=asset_id)
        scene.refresh()

    log.debug(f"asset_id to download: {scene.asset_id}")

    # Export scene
    timeout = ctx.obj["config"]["cli"]["timeout"]

    scene.export_scene(
        download_format=download_format,
        compatibility_mode=compatibility_mode,
        avatarSceneIndex=avatar_scene_index,
        timeout=timeout,
    )

    scene.download(download_format=download_format, out_file=out_file)


@cli.command()
@click.pass_context
def info(ctx: click.Context) -> None:
    """Show API info."""
    # Create an instance of the API class
    api_instance = client.InfoApi(ctx.obj["api_client"])

    try:
        # Show API info
        api_response: str = api_instance.info()
        log.info(api_response)
    except Exception as e:
        log.info("Exception when calling InfoApi->info: %s\n" % e)


@cli.command(name="user-info")
@require_auth
@click.pass_context
def user_info(ctx: click.Context) -> None:
    """Show username and available credits."""
    api_instance_user = client.UserApi(ctx.obj["api_client"])

    user = request_user_info(api_instance_user)

    log.info(f"Username: {user.email}")
    log.info(f"Credits: {user.credits}")
