"""
Absfuyu: Shutdownizer
---------------------
This shutdowns

Version: 6.0.0
Date updated: 24/12/2025 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = ["ShutDownizer", "ShutdownEngine"]


# Library
# ---------------------------------------------------------------------------
import os
import subprocess
import sys
from abc import ABC, abstractmethod
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Annotated, override

from absfuyu.core import BaseClass, versionadded, versionchanged
from absfuyu.logger import logger

# TODO: Schedule shutdown, random time shutdown, test


# Class
# ---------------------------------------------------------------------------
@versionadded("4.2.0")
class ShutDownizer(BaseClass):
    """
    ShutDownizer

    Shutdown tool because why not
    """

    __slots__ = ("os", "engine")

    def __init__(self) -> None:
        self.os: str = sys.platform
        logger.debug(f"Current OS: {self.os}")

        if self.os in ["win32", "cygwin"]:  # Windows
            self.engine = ShutdownEngineWin()  # type: ignore
        elif self.os == "darwin":  # MacOS
            self.engine = ShutdownEngineMac()  # type: ignore
        elif self.os == "linux":  # Linux
            self.engine = ShutdownEngineLinux()  # type: ignore
        else:
            raise SystemError("OS not supported")

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.os})"

    def shutdown(self, *args, **kwargs) -> None:
        """Shutdown"""
        self.engine.shutdown(*args, **kwargs)

    def restart(self, *args, **kwargs) -> None:
        """Restart"""
        self.engine.restart(*args, **kwargs)

    def cancel(self) -> None:
        """Cancel"""
        self.engine.cancel()


class ShutdownEngine(ABC, BaseClass):
    """
    Abstract shutdown class for different type of OS
    """

    def __str__(self) -> str:
        return f"{self.__class__.__name__}()"

    def _execute_cmd(self, cmd: str | list) -> None:
        """Execute the cmd"""
        try:
            if isinstance(cmd, str):
                subprocess.run(cmd.split())
            elif isinstance(cmd, list):
                subprocess.run(cmd)
        except (FileNotFoundError, Exception) as e:
            logger.error(f'"{cmd}" failed to run: {e}')
            raise ValueError(f'"{cmd}" failed to run')  # noqa

    def _execute_multiple_cmds(self, cmds: list) -> None:
        if not isinstance(cmds, list):
            raise ValueError("cmds must be a <list>")
        for cmd in cmds:
            try:
                logger.debug(f"Executing: {cmd}")
                self._execute_cmd(cmd)
                break
            except Exception as e:
                logger.error(f'"{cmd}" failed to run: {e}')

    @abstractmethod
    def shutdown(self, *args, **kwargs) -> None:
        """Shutdown"""
        pass

    @abstractmethod
    def restart(self, *args, **kwargs) -> None:
        """Restart"""
        pass

    @abstractmethod
    def sleep(self, *args, **kwargs) -> None:
        """Sleep"""
        pass

    @abstractmethod
    def abort(self) -> None:
        """Abort/Cancel"""
        pass

    def cancel(self) -> None:
        """Abort/Cancel"""
        self.abort()

    def _calculate_time(
        self,
        h: Annotated[int, "positive"] = 0,
        m: Annotated[int, "positive"] = 0,
        aggregate: bool = True,
    ) -> int:
        """
        Calculate time for scheduled shutdown.

        Parameters
        ----------
        h : int, optional
            Hours to add (24h format), by default ``0``

        m : int, optional
            Minutes to add (24h format), by default ``0``

        aggregate : bool, optional
            This add hours and and minutes to `time.now()`, by default ``True``
            - ``True`` : Add hours and minutes to current time
            - ``False``: Use ``h`` and ``m`` as fixed time point to shutdown

        Returns
        -------
        int
            Seconds left until shutdown.
        """
        h = max(0, h)  # Force >= 0
        m = max(0, m)
        now = datetime.now()
        if aggregate:
            delta = timedelta(hours=h, minutes=m)
            out = delta.seconds
        else:
            new_time = datetime.combine(now.date(), time(hour=h, minute=m))
            diff = new_time - now
            out = diff.seconds
        return out


class ShutdownEngineWin(ShutdownEngine):
    """ShutDownizer - Windows"""

    @override
    @versionchanged("5.0.0", "Scheduled shutdown")
    def shutdown(
        self,
        h: Annotated[int, "positive"] = 0,
        m: Annotated[int, "positive"] = 0,
        aggregate: bool = True,
    ) -> None:
        time_until_sd = self._calculate_time(h=h, m=m, aggregate=aggregate)
        cmds = [f"shutdown -f -s -t {time_until_sd}"]
        self._execute_multiple_cmds(cmds)

    @override
    def restart(self, *args, **kwargs) -> None:
        cmds = ["shutdown -r"]
        self._execute_multiple_cmds(cmds)

    @override
    def sleep(self, *args, **kwargs) -> None:
        cmds = ["rundll32.exe powrprof.dll,SetSuspendState 0,1,0"]
        self._execute_multiple_cmds(cmds)

    @override
    def abort(self) -> None:
        cmds = ["shutdown -a"]
        self._execute_multiple_cmds(cmds)

    def _punish(self, *, are_you_sure_about_this: bool = False) -> None:
        """Create a `batch` script that shut down computer when boot up"""
        if not are_you_sure_about_this:
            return None
        try:
            startup_folder_win = Path(os.getenv("appdata")).joinpath(  # type: ignore
                "Microsoft", "Windows", "Start Menu", "Programs", "Startup"
            )
            with open(startup_folder_win.joinpath("system.bat"), "w") as f:
                f.write("shutdown -f -s -t 0")
        except Exception:
            logger.error("Cannot write file to startup folder")


class ShutdownEngineMac(ShutdownEngine):
    """ShutDownizer - MacOS"""

    @override
    def shutdown(self, *args, **kwargs) -> None:
        cmds = [
            ["osascript", "-e", 'tell application "System Events" to shut down'],
            "pmset sleepnow",
            "shutdown -h now",
            "sudo shutdown -h now",
        ]
        self._execute_multiple_cmds(cmds)

    @override
    def restart(self, *args, **kwargs) -> None:
        cmds = [
            ["osascript", "-e", 'tell application "System Events" to restart'],
            "shutdown -r now",
            "sudo shutdown -r now",
        ]
        self._execute_multiple_cmds(cmds)

    @override
    def sleep(self, *args, **kwargs) -> None:
        cmds = [
            ["osascript", "-e", 'tell application "System Events" to sleep'],
            "pmset sleepnow",
            "shutdown -s now",
            "sudo shutdown -s now",
        ]
        self._execute_multiple_cmds(cmds)

    @override
    def abort(self) -> None:
        cmds = [
            ["osascript", "-e", 'tell application "System Events" to cancel shutdown'],
            "killall shutdown",
            "shutdown -c",
            "sudo shutdown -c",
        ]
        self._execute_multiple_cmds(cmds)


class ShutdownEngineLinux(ShutdownEngine):
    """ShutDownizer - Linux"""

    @override
    def shutdown(self, *args, **kwargs) -> None:
        cmds = [
            "gnome-session-quit --power-off",
            "systemctl --user poweroff",
            "sudo shutdown -h now",
        ]
        self._execute_multiple_cmds(cmds)

    @override
    def restart(self, *args, **kwargs) -> None:
        cmds = [
            "gnome-session-quit --reboot",
            "systemctl reboot",
            "sudo shutdown -r now",
        ]
        self._execute_multiple_cmds(cmds)

    @override
    def sleep(self, *args, **kwargs) -> None:
        cmds = ["systemctl suspend", "sudo shutdown -s now"]
        self._execute_multiple_cmds(cmds)

    @override
    def abort(self) -> None:
        cmds = ["sudo shutdown -c"]
        self._execute_multiple_cmds(cmds)
