from dataclasses import dataclass
import click


@dataclass
class ExportParameters:
    """Class for defining export parameters."""

    download_format: str
    pose: str
    animation: str
    compatibility_mode: str
    out_file: click.Path
