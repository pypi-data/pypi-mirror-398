from typing_extensions import NotRequired

from typing import Literal, TypedDict


MIME_JPG = "image/jpg"
MIME_PLAIN = "text/plain"
MIME_PNG = "image/png"
MIME_VIDEO = "video/mp4"
MIME_BINARY = "application/octet-stream"
MIME_TYPES = {
    "jpg": MIME_JPG,
    "jpeg": MIME_JPG,
    "png": MIME_PNG,
    "obj": MIME_PLAIN,
    "mp4": MIME_VIDEO,
    "smpl": MIME_BINARY,
}


class ColumnStyleDict(TypedDict):
    style: NotRequired[str]
    no_wrap: NotRequired[bool]
    justify: NotRequired[Literal["default", "left", "center", "right", "full"]]
    max_width: NotRequired[int]


ASSET_COLUMN_STYLES: dict[str, ColumnStyleDict] = {
    "Name": {"max_width": 30},
    "Asset ID": {"max_width": 40},
    "Created from": {"max_width": 20},
    "Created at": {"max_width": 20},
}
