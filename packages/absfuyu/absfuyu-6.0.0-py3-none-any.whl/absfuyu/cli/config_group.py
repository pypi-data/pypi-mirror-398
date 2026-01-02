"""
ABSFUYU CLI
-----------
Config

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

# Module Package
# ---------------------------------------------------------------------------
__all__ = ["config_group"]


# Library
# ---------------------------------------------------------------------------
import click

from absfuyu.cli.color import COLOR
from absfuyu.config import ABSFUYU_CONFIG


# CLI
# ---------------------------------------------------------------------------
@click.command()
@click.option(
    "--setting",
    "-s",
    type=click.Choice(["luckgod", "install-extra"]),
    help="Toggle on/off selected setting",
)
def toggle(setting: str) -> None:
    """Toggle on/off setting"""

    # Dictionary
    trans = {
        "luckgod": "luckgod-mode",
        "install-extra": "auto-install-extra",
    }  # trans[setting]

    if setting is None:
        click.echo(f"{COLOR['red']}Invalid setting")  # type: ignore
    else:
        ABSFUYU_CONFIG.toggle_setting(trans[setting])
        out = ABSFUYU_CONFIG._get_setting(trans[setting])
        click.echo(f"{COLOR['red']}{out}")


@click.command()
def reset():
    """Reset config to default value"""
    ABSFUYU_CONFIG.reset_config()
    click.echo(f"{COLOR['green']}All settings have been reseted")


@click.group(name="config")
def config_group() -> None:
    """absfuyu configuration"""
    pass


config_group.add_command(toggle)
config_group.add_command(reset)
