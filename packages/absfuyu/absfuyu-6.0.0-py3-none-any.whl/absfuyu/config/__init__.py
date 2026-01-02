"""
Absfuyu: Configuration
----------------------
Package configuration module - internal use

Version: 6.0.0
Date updated: 24/12/2025 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = [
    "ABSFUYU_CONFIG",
    "Config",
    "CONFIG_PATH",
    # "Setting"
]


# Library
# ---------------------------------------------------------------------------
from importlib.resources import files
from pathlib import Path
from typing import Any, TypedDict

from absfuyu.core import BaseClass
from absfuyu.util.json_method import JsonFile

# Setting
# ---------------------------------------------------------------------------
CONFIG_PATH = files("absfuyu.config").joinpath("config.json")
_SPACE_REPLACE = "-"  # Replace " " character in setting name


# Type hint
# ---------------------------------------------------------------------------
class SettingDictFormat(TypedDict):
    """
    Format for the ``setting`` section in ``config``

    :param default: Default value for the setting
    :param help: Description for the setting
    :param value: Current value of the setting
    """

    default: Any
    help: str
    value: Any


class ConfigFormat(TypedDict):
    """
    Config file format

    :param setting: setting section
    :type setting: dict[str, SettingDictFormat]
    :param version: version section
    :type version: VersionDictFormat
    """

    setting: dict[str, SettingDictFormat]


# Class
# ---------------------------------------------------------------------------
class Setting(BaseClass):
    """Setting"""

    def __init__(self, name: str, value: Any, default: Any, help_: str = "") -> None:
        """
        :param name: Name of the setting
        :param value: Value of the setting
        :param default: Default value of the setting
        :param help: Description of the setting
        """
        self.name = name
        self.value = value
        self.default = default
        self.help = help_

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.name}: {self.value})"

    @classmethod
    def from_dict(cls, dict_data: dict[str, SettingDictFormat]):
        """
        Convert ``dict`` into ``Setting`` (``len==1`` only)
        """
        name: str = list(dict_data.keys())[0]
        _val: SettingDictFormat = list(dict_data.values())[0]
        value: Any = _val["value"]
        default: Any = _val["default"]
        help_: str = _val["help"]
        return cls(name, value, default, help_)

    def reset(self) -> None:
        """
        Reset setting to default value
        (``Setting.value = Setting.default``)
        """
        self.value = self.default

    def update_value(self, value: Any) -> None:
        """Update current value"""
        self.value = value

    def to_dict(self) -> dict[str, SettingDictFormat]:
        """
        Convert ``Setting`` into ``dict``
        """
        output: dict[str, SettingDictFormat] = {
            self.name: {"default": self.default, "help": self.help, "value": self.value}
        }
        return output


class Config(BaseClass):
    """
    Config handling
    """

    def __init__(self, config_file: Path, name: str | None = None) -> None:
        """
        config_file: Path to `.json` config file
        """
        self.config_path: Path = config_file
        self.json_engine: JsonFile = JsonFile(self.config_path)

        if name is None:
            self.name = self.config_path.name
        else:
            self.name = name

        # Data
        self.settings: list[Setting] = None  # type: ignore
        self._fetch_data()  # Load data

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.config_path.name})"

    # Data prepare and export
    def _fetch_data(self) -> None:
        """Load data from ``self.config_file`` file"""
        data: dict = self.json_engine.load_json()
        settings: dict[str, SettingDictFormat] = data.get("setting")  # type: ignore
        self.settings = [Setting.from_dict({k: v}) for k, v in settings.items()]

    def _prepare_data(self) -> ConfigFormat:
        """Prepare data to save config"""
        settings = dict()
        for setting in self.settings:
            settings.update(setting.to_dict())

        out: ConfigFormat = {"setting": settings}
        return out

    def save(self) -> None:
        """Save config to ``.json`` file"""
        self.json_engine.update_data(self._prepare_data())  # type: ignore
        self.json_engine.save_json()

    # Setting method
    @property
    def setting_list(self) -> list[str]:
        """List of name of available settings"""
        return [setting.name for setting in self.settings]

    def _get_setting(self, name: str):
        """Get setting"""
        name = name.strip().lower().replace(" ", _SPACE_REPLACE)
        if name in self.setting_list:
            for setting in self.settings:
                if setting.name.startswith(name):
                    return setting
        else:
            raise ValueError(f"Setting list: {self.setting_list}")

    def reset_config(self) -> None:
        """Reset all settings to default value"""
        [setting.reset() for setting in self.settings]  # type: ignore
        self.save()

    def show_settings(self) -> list[Setting]:
        """
        Returns a list of available settings
        (wrapper for ``Config.settings``)
        """
        return self.settings

    def change_setting(self, name: str, value: Any) -> None:
        """
        Change ``Setting`` (if available)

        Parameters
        ----------
        name : str
            Name of the setting

        value : Any
            Value of the setting
        """
        name = name.strip().lower().replace(" ", _SPACE_REPLACE)
        if name in self.setting_list:
            for setting in self.settings:
                if setting.name.startswith(name):
                    setting.update_value(value)
                    break
        else:
            raise ValueError(f"Setting list: {self.setting_list}")
        self.save()

    def toggle_setting(self, name: str) -> None:
        """
        Special ``change_setting()`` method.
        Turn on/off if ``type(<setting>) is bool``

        Parameters
        ----------
        name : str
            Name of the setting
        """
        # Get setting
        setting = self._get_setting(name)
        setting_value: bool = setting.value

        # Change value
        try:
            self.change_setting(name, not setting_value)
        except Exception:
            raise SystemExit("This setting is not type: bool")  # noqa: B904

    def add_setting(self, name: str, value: Any, default: Any, help_: str = "") -> None:
        """
        Add ``Setting`` if not exist

        Parameters
        ----------
        name : str
            Name of the setting

        value : Any
            Value of the setting

        default : Any
            Default value of the setting

        help_ : str
            Description of the setting (Default: ``None``)
        """
        name = name.strip().lower().replace(" ", _SPACE_REPLACE)
        new_setting = Setting(name, value, default, help_)
        if new_setting not in self.settings:
            self.settings.append(new_setting)
        self.save()

    def del_setting(self, name: str) -> None:
        """
        Delete ``Setting``

        Parameters
        ----------
        name : str
            Name of the setting
        """
        name = name.strip().lower().replace(" ", _SPACE_REPLACE)
        self.settings = [x for x in self.settings if x.name != name]
        self.save()

    def welcome(self) -> None:
        """Run first-run script (if any)"""
        self.change_setting("first-run", False)


# Init
# ---------------------------------------------------------------------------
ABSFUYU_CONFIG = Config(CONFIG_PATH)  # type: ignore
