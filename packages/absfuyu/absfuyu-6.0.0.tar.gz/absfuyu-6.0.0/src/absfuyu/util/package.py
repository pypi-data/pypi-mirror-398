"""
Absfuyu: Package
----------------
Package related

Version: 6.0.0
Date updated: 27/12/2025 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = ["PackageManager"]


# Library
# ---------------------------------------------------------------------------
import ensurepip
import importlib
import importlib.metadata
import importlib.util
import subprocess
import sys

from absfuyu.core.baseclass import BaseClass


# Class
# ---------------------------------------------------------------------------
class PackageManager(BaseClass):
    """
    Utility class for checking, installing, and importing Python packages safely.
    """

    def __init__(
        self,
        package: str,
        import_name: str | None = None,
        auto_upgrade: bool = False,
        auto_bootstrap: bool = True,
    ) -> None:
        """
        A configurable package manager utility that can check, install, and import Python packages safely.

        Parameters
        ----------
        package : str
            The pip package name (e.g. "absfuyu", "random").

        import_name : str | None
            The importable module name if different from the package name (e.g. "PIL" for "pillow").

        auto_upgrade : bool, by default ``False``
            Whether to automatically upgrade packages during installation.

        auto_bootstrap : bool, by default ``True``
            Whether to automatically bootstrap pip using ensurepip if it's missing.
        """
        self.package = package
        self.import_name = import_name
        self.auto_upgrade = auto_upgrade
        self.auto_bootstrap = auto_bootstrap

    @property
    def version(self) -> str | None:
        """
        Version of package if available

        Returns
        -------
        str
            Version of package

        None
            When package is not available
        """
        try:
            return importlib.metadata.version(self.package or self.import_name)
        except importlib.metadata.PackageNotFoundError:
            return None

    def _run_pip_install(self, package: str) -> None:
        """
        Internal helper to safely run pip install, bootstrapping pip if needed.
        """
        try:
            import pip  # noqa: F401
        except ImportError:
            if self.auto_bootstrap:
                ensurepip.bootstrap()
            else:
                raise RuntimeError("pip not found and auto_bootstrap is disabled.")

        cmd = [sys.executable, "-m", "pip", "install", package]
        if self.auto_upgrade:
            cmd.append("--upgrade")

        try:
            subprocess.check_call(cmd)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to install {package}: {e}")

    def ensure_installed(self) -> None:
        """
        Ensure a Python package is installed. Installs (and optionally upgrades) it if missing.
        """
        module_name = self.import_name or self.package

        if importlib.util.find_spec(module_name) is None:
            self._run_pip_install(self.package)

    def ensure_import(self):
        """
        Ensure a Python package is importable, installing it if necessary.
        Returns the imported module.
        """
        module_name = self.import_name or self.package

        if importlib.util.find_spec(module_name) is not None:
            return importlib.import_module(module_name)

        self.logger.info(f"Installing missing package: {self.package} ...")

        self._run_pip_install(self.package)
        return importlib.import_module(module_name)
