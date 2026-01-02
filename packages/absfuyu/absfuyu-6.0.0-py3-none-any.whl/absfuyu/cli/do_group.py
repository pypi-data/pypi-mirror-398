"""
ABSFUYU CLI
-----------
Do

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

# Module Package
# ---------------------------------------------------------------------------
__all__ = ["do_group"]


# Library
# ---------------------------------------------------------------------------
import subprocess

import click

from absfuyu import __title__
from absfuyu.cli.color import COLOR
from absfuyu.core import __package_feature__
from absfuyu.tools.shutdownizer import ShutDownizer
from absfuyu.util.path import Directory
from absfuyu.version import PkgVersion


# CLI
# ---------------------------------------------------------------------------
@click.command()
@click.option(
    "--force_update/--no-force-update",
    "-F/-f",
    "force_update",
    type=bool,
    default=True,
    show_default=True,
    help="Update the package",
)
def update(force_update: bool) -> None:
    """Update the package to latest version"""
    click.echo(f"{COLOR['green']}")
    AbsfuyuPackage = PkgVersion(
        package_name=__title__,
    )
    AbsfuyuPackage.check_for_update(force_update=force_update)


@click.command()
@click.argument("pkg", type=click.Choice(__package_feature__))
def install(pkg: str) -> None:
    """Install absfuyu's extension"""
    cmd = f"pip install -U absfuyu[{pkg}]".split()
    try:
        subprocess.run(cmd)
    except Exception:
        try:
            cmd2 = f"python -m pip install -U absfuyu[{pkg}]".split()
            subprocess.run(cmd2)
        except Exception:
            click.echo(f"{COLOR['red']}Unable to install absfuyu[{pkg}]")
        else:
            click.echo(f"{COLOR['green']}absfuyu[{pkg}] installed")
    else:
        click.echo(f"{COLOR['green']}absfuyu[{pkg}] installed")


@click.command(name="unzip")
@click.argument("dir", type=str)
def unzip_files_in_dir(dir: str) -> None:
    """Unzip every files in directory"""

    engine = Directory(dir)
    engine.decompress()
    click.echo(f"{COLOR['green']}Done!")


@click.command(name="shutdown")
def os_shutdown() -> None:
    """Shutdown"""
    engine = ShutDownizer()
    engine.shutdown()


@click.command(name="organize")
@click.argument("dir", type=str)
def organize_directory(dir: str) -> None:
    """Organize a directory"""
    engine = Directory(dir)
    engine.organize()
    click.echo(f"{COLOR['green']}Done!")


@click.group(name="do")
def do_group() -> None:
    """Perform functionalities"""
    pass


do_group.add_command(update)
do_group.add_command(install)
do_group.add_command(unzip_files_in_dir)
do_group.add_command(os_shutdown)
do_group.add_command(organize_directory)
