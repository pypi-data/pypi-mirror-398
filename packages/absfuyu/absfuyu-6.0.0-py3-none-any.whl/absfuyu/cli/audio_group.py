"""
ABSFUYU CLI
-----------
Audio

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

# Module Package
# ---------------------------------------------------------------------------
__all__ = ["audio_group"]


# Library
# ---------------------------------------------------------------------------
from pathlib import Path

import click

from absfuyu.extra.audio.convert import DirectoryAudioConvertMixin
from absfuyu.extra.audio.lossless import DirectoryAudioLosslessCheckMixin


# CLI
# ---------------------------------------------------------------------------
@click.command(name="c3")
@click.argument("dir_path", type=str)
@click.option(
    "--recursive",
    "-r",
    "recursive_mode",
    type=bool,
    default=False,
    is_flag=True,
    show_default=True,
    help="Scan for every file in the folder (including child folder)",
)
@click.option(
    "--format",
    "-f",
    "from_format",
    type=str,
    default=".flac",
    show_default=True,
    help="From which audio format",
)
def convert_to_mp3(dir_path: str, from_format: str, recursive_mode: bool) -> None:
    """Convert to .mp3 file"""

    engine = DirectoryAudioConvertMixin(Path(dir_path).resolve())

    try:
        engine.convert_to_mp3(from_format=from_format, recursive=recursive_mode)
    except Exception:
        engine.convert_to_mp3_single_thread(from_format=from_format, recursive=recursive_mode)
    click.echo("Done")


@click.command(name="lc")
@click.argument("dir_path", type=str)
@click.option(
    "--recursive",
    "-r",
    "recursive_mode",
    type=bool,
    default=False,
    is_flag=True,
    show_default=True,
    help="Scan for every file in the folder (including child folder)",
)
@click.option(
    "--format",
    "-f",
    "format",
    type=str,
    default=".flac",
    show_default=True,
    help="Audio format",
)
def lossless_check(dir_path: str, format: str, recursive_mode: bool) -> None:
    """Check for lossless audio file"""

    engine = DirectoryAudioLosslessCheckMixin(Path(dir_path).resolve())
    try:
        engine.lossless_check(from_format=format, recursive=recursive_mode)
    except Exception:
        engine.lossless_check_single_thread(from_format=format, recursive=recursive_mode)
    click.echo("Done")


@click.group(name="audio")
def audio_group() -> None:
    """Audio related"""
    pass

audio_group.add_command(lossless_check)
audio_group.add_command(convert_to_mp3)
