"""
ABSFUYU CLI
-----------
Tool

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

# Module Package
# ---------------------------------------------------------------------------
__all__ = ["tool_group"]


# Library
# ---------------------------------------------------------------------------
from pathlib import Path
from typing import Literal

import click

from absfuyu.tools.checksum import Checksum
from absfuyu.tools.converter import Base64EncodeDecode, Text2Chemistry


# CLI
# ---------------------------------------------------------------------------
@click.command(name="cs")
@click.argument("file_path", type=str)
@click.option(
    "--hashmode",
    "-m",
    "hash_mode",
    type=click.Choice(["md5", "sha1", "sha256", "sha512"]),
    default="sha256",
    show_default=True,
    help="Hash mode",
)
@click.option(
    "--save-result",
    "-s",
    "save_result",
    type=bool,
    default=False,
    is_flag=True,
    show_default=True,
    help="Save checksum result to file",
)
@click.option(
    "--recursive",
    "-r",
    "recursive_mode",
    type=bool,
    default=False,
    is_flag=True,
    show_default=True,
    help="Do checksum for every file in the folder (including child folder)",
)
@click.option(
    "--compare",
    "-c",
    "hash_to_compare",
    type=str,
    default=None,
    show_default=True,
    help="Hash to compare",
)
def file_checksum(
    file_path: str,
    hash_mode: Literal["md5", "sha1", "sha256", "sha512"],
    save_result: bool,
    recursive_mode: bool,
    hash_to_compare: str | None,
) -> None:
    """Checksum for file/directory"""
    instance = Checksum(file_path, hash_mode=hash_mode, save_result_to_file=save_result)
    res = instance.checksum(recursive=recursive_mode)
    if hash_to_compare is None:
        click.echo(res)
    else:
        click.echo(res == hash_to_compare)


@click.command(name="cimg")
@click.argument("dir_path", type=str)
@click.argument("to_format", type=str)
def convert_img(dir_path: str, to_format: str) -> None:
    """Convert image in directory"""
    from absfuyu.extra.img.converter import ImgConverter

    engine = ImgConverter(Path(dir_path).resolve())
    engine.img_convert(to_format)
    click.echo("Done")


@click.command(name="rdimg")
@click.argument("dir_path", type=str)
@click.option(
    "--dryrun",
    "-d",
    "dry_run",
    type=bool,
    default=False,
    is_flag=True,
    show_default=True,
    help="Simulate deleting only",
)
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
    "--threshold",
    "-t",
    "threshold",
    type=int,
    default=5,
    show_default=True,
    help="Threshold: 0 for exact image, 5 to 10 for light edit",
)
@click.option(
    "--keepmode",
    "-k",
    "keep_mode",
    type=click.Choice(["first", "last", "best"]),
    default="best",
    show_default=True,
    help="Keep mode",
)
def remove_dup_img(dir_path: str, threshold: bool, recursive_mode: bool, keep_mode: str, dry_run: bool) -> None:
    """Remove duplicate images in directory"""
    from absfuyu.extra.img.dup_check import DirectoryRemoveDuplicateImageMixin as DRDI

    engine = DRDI(Path(dir_path).resolve())
    engine.remove_duplicate_images(threshold=threshold, recursive=recursive_mode, keep_mode=keep_mode, dry_run=dry_run)
    click.echo("Done")


@click.command(name="t2c")
@click.argument("text", type=str)
def text2chem(text: str) -> None:
    """Convert text into chemistry symbol"""
    engine = Text2Chemistry()
    out = engine.convert(text)
    click.echo(Text2Chemistry.beautify_result(out))


@click.command(name="e")
@click.argument("text", type=str)
def base64encode(text: str) -> None:
    """Convert text to base64"""
    click.echo(Base64EncodeDecode.encode(text))


@click.command(name="d")
@click.argument("text", type=str)
def base64decode(text: str) -> None:
    """Convert base64 to text"""
    click.echo(Base64EncodeDecode.decode(text))


@click.command(name="img")
@click.option(
    "--data-tag",
    "-d",
    "data_tag",
    type=bool,
    default=False,
    is_flag=True,
    show_default=True,
    help="Add data tag before base64 string",
)
@click.argument("img_path", type=str)
def base64convert_img(img_path: str, data_tag: bool) -> None:
    """Convert img to base64"""
    click.echo(Base64EncodeDecode.encode_image(img_path, data_tag=data_tag))


@click.group(name="b64")
def base64_group() -> None:
    """Base64 encode decode"""
    pass


base64_group.add_command(base64encode)
base64_group.add_command(base64decode)
base64_group.add_command(base64convert_img)


@click.group(name="tool")
def tool_group() -> None:
    """Tools"""
    pass


tool_group.add_command(file_checksum)
tool_group.add_command(convert_img)
tool_group.add_command(remove_dup_img)
tool_group.add_command(base64_group)
tool_group.add_command(text2chem)
