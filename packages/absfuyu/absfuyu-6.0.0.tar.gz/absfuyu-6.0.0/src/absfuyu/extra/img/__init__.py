"""
Absfuyu: Image
--------------
Image related

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = ["ImgConverter"]


# Library
# ---------------------------------------------------------------------------
try:
    from PIL import Image
except ImportError:
    from subprocess import run

    from absfuyu.config import ABSFUYU_CONFIG

    if ABSFUYU_CONFIG._get_setting("auto-install-extra").value:  # type: ignore
        cmd = "python -m pip install -U absfuyu[pic]".split()
        run(cmd)
    else:
        raise SystemExit("This feature is in absfuyu[pic] package")  # noqa: B904

from absfuyu.extra.img.converter import ImgConverter
