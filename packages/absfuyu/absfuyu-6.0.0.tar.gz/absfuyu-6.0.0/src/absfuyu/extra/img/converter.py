"""
Absfuyu: Picture converter
--------------------------
Image converter


Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = ["ImgConverter"]


# Library
# ---------------------------------------------------------------------------
import logging
import shutil
from functools import partial
from importlib.util import find_spec as check_for_package_installed
from pathlib import Path
from typing import Any, Literal, Protocol

from absfuyu.core.dummy_func import tqdm as tqdm_base
from absfuyu.util.path import DirectorySelectMixin

try:
    from PIL import Image
    from PIL import features as pil_features
    from PIL.ImageFile import ImageFile
except ImportError:
    from subprocess import run

    from absfuyu.config import ABSFUYU_CONFIG

    if ABSFUYU_CONFIG._get_setting("auto-install-extra").value:  # type: ignore
        cmd = "python -m pip install -U absfuyu[pic]".split()
        run(cmd)
    else:
        raise SystemExit("This feature is in absfuyu[pic] package")  # noqa: B904
else:
    from PIL import Image
    from PIL import features as pil_features
    from PIL.ImageFile import ImageFile

try:
    from pillow_heif import register_heif_opener  # type: ignore
except ImportError:
    from absfuyu.core.dummy_func import dummy_function as register_heif_opener
register_heif_opener()


# Setup
# ---------------------------------------------------------------------------
tqdm = partial(tqdm_base, unit_scale=True, dynamic_ncols=True)
SupportedImageFormat = Literal[".jpg", ".jpeg", ".png", ".webp"]


# Exporter/Converter
# ---------------------------------------------------------------------------
class SupportImageConverter(Protocol):
    # Callable[[ImageFile, Path], None]
    def __call__(self, image: ImageFile, path: Path, **params: Any) -> None: ...


def _image_convert_default(image: ImageFile, path: Path, **params: Any) -> None:
    """
    Default convert image function

    Parameters
    ----------
    image : ImageFile
        Image file

    path : Path
        Path to export
    """
    image.save(path, **params)


def _image_convert_webp(image: ImageFile, path: Path, **params: Any) -> None:
    """
    Convert image to .webp format (with custom settings)

    Parameters
    ----------
    image : ImageFile
        Image file

    path : Path
        Path to export
    """
    image.save(
        path,
        format="WEBP",
        lossless=True,
        quality=100,
        alpha_quality=100,
        method=4,
        exact=False,  # If true, preserve the transparent RGB values. Otherwise, discard invisible RGB values for better compression. Defaults to false.
        **params,
    )


def _image_convert_png(image: ImageFile, path: Path, **params: Any) -> None:
    """
    Convert image to .png format (with custom settings)

    Parameters
    ----------
    image : ImageFile
        Image file

    path : Path
        Path to export
    """
    image.save(
        path,
        format="PNG",
        # optimize=True,
        compress_level=6,
        **params,
    )


def _image_convert_jpg(image: ImageFile, path: Path, **params: Any) -> None:
    """
    Convert image to .jpg format (with custom settings)

    Parameters
    ----------
    image : ImageFile
        Image file

    path : Path
        Path to export
    """

    if image.mode == "RGBA":
        white_background = Image.new("RGB", image.size, (255, 255, 255))
        white_background.paste(image, mask=image.getchannel("A"))
        image = white_background
    else:
        image = image.convert("RGB")

    image.save(
        path,
        format="JPEG",
        optimize=True,
        keep_rgb=True,
        **params,
    )


# Class
# ---------------------------------------------------------------------------
class ImgConverter(DirectorySelectMixin):
    _IMAGE_CONVERTER: dict[str, SupportImageConverter] = {
        "default": _image_convert_default,
        ".webp": _image_convert_webp,
        ".png": _image_convert_png,
        ".jpg": _image_convert_jpg,
        ".jpeg": _image_convert_jpg,
    }

    def __init__(
        self,
        source_path: str | Path,
        create_if_not_exist: bool = False,
        backup_dir_name: str | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        super().__init__(source_path, create_if_not_exist)

        # Supported image extension
        self._supported_image_format = [".png"]
        self._register_img_format()

        # Backup
        if backup_dir_name is None:
            backup_dir_name = "ZZZ_Backup"
        self.backup_path = self.source_path.joinpath(backup_dir_name)

        # Not available yet
        self.logger = logger

    # Extra format
    @classmethod
    def install_all_extension(cls) -> None:
        """
        Install all extra package to unlock all features
        """
        extra = [
            "pillow_heif",  # heic support
            "defusedxml",  # xmp
            "olefile",  # FPX and MIC images
        ]
        base = ["pip", "install", "-U"]
        base.extend(extra)

        import subprocess

        subprocess.run(base)

    def _register_img_format(self) -> None:
        """
        Try to register these format:
        - ``.webp``
        - ``.heif``, ``.heic`` (``pillow_heif`` package required)
        """
        if pil_features.check("jpg"):
            self._supported_image_format.extend([".jpg", ".jpeg"])
        if pil_features.check("webp"):
            self._supported_image_format.append(".webp")

        if check_for_package_installed("pillow_heif", "pillow_heif") is not None:
            self._supported_image_format.extend([".heic", ".heif"])

    @property
    def supported_image_format(self) -> list[str]:
        """
        Supported image format

        Returns
        -------
        list[str]
            Supported image format
        """
        return self._supported_image_format

    @classmethod
    def add_converter(cls, format_name: str, converter_func: SupportImageConverter) -> None:
        """
        Add image converter function to a format

        Parameters
        ----------
        format_name : str
            Image format name

        converter_func : SupportImageConverter
            Converter function


        Example:
        --------
        >>> ImgConverter.add_converter(".png", convert_to_png)
        """
        cls._IMAGE_CONVERTER[format_name] = converter_func

    # Support
    def _make_suffix_selection(self, exclude_suffix: str) -> tuple[str, ...]:
        """
        Make suffix selection (exclude the image with converted to suffix)

        Parameters
        ----------
        exclude_suffix : str
            Converted to suffix

        Returns
        -------
        tuple[str, ...]
            Suffix selection
        """
        # out = []
        # for x in self._supported_image_format:
        #     if x.lower() == exclude_suffix.lower():
        #         continue
        #     out.append(x.lower())
        #     out.append(x.upper())
        out = (x for x in self._supported_image_format if x.lower() != exclude_suffix.lower())
        return tuple(out)

    def _make_backup(self, src_file: Path) -> None:
        dest = self.backup_path.joinpath(src_file.name)
        shutil.move(src_file, dest)

    # Convert
    def _image_convert_legacy(
        self,
        path: Path,
        to_format: SupportedImageFormat | None = None,
        lossless: bool = True,
        compression_level: int | None = None,
    ) -> None:
        """
        Convert image to other format (settings are mostly for .webp format)

        Parameters
        ----------
        path : Path
            Path to image

        to_format : SupportedImageFormat | None, optional
            New image format, by default None

        lossless : bool, optional
            Lossless compression, by default True

        compression_level : int | None, optional
            Compression level, by default None
        """
        # Load image
        new_suffix = path.suffix if to_format is None else to_format
        image = Image.open(path)

        # Extract metadata
        # exif = image.info.get("exif")
        # xmp = image.getxmp()
        # icc_profile = image.info.get("icc_profile")
        xmp = image.info.get("xmp")
        exif = image.getexif()
        icc_profile = image.info.get("icc_profile")
        # print(image.info.keys())

        # Save
        image.save(
            path.with_suffix(new_suffix),
            format=new_suffix[1:].upper(),
            lossless=lossless,
            quality=100,
            alpha_quality=100,
            method=(4 if compression_level is None else compression_level),
            exact=False,  # If true, preserve the transparent RGB values. Otherwise, discard invisible RGB values for better compression. Defaults to false.
            exif=exif,
            icc_profile=icc_profile,
            xmp=xmp,
        )

    def _image_convert(
        self,
        path: Path,
        to_format: str | None = None,
    ) -> None:
        """
        Convert image to other format

        Parameters
        ----------
        path : Path
            Path to image

        to_format : SupportedImageFormat | None, optional
            New image format, by default None
        """
        # Load image
        new_suffix = path.suffix if to_format is None else to_format
        image = Image.open(path)

        # Extract metadata
        save_kwargs = {}
        if exif := image.getexif():
            save_kwargs["exif"] = exif
        if icc := image.info.get("icc_profile"):
            save_kwargs["icc_profile"] = icc
        if xmp := image.info.get("xmp"):
            save_kwargs["xmp"] = xmp

        # # Convert image mode
        # if image.mode not in ("RGB", "RGBA", "L"):
        #     image = image.convert("RGBA")

        # Save
        convert_func = self._IMAGE_CONVERTER.get(new_suffix, _image_convert_default)
        # self.logger.debug(f"Using {convert_func}")
        convert_func(image, path.with_suffix(new_suffix), **save_kwargs)

    def img_convert(self, to_format: SupportedImageFormat | str, backup: bool = True) -> None:
        """
        Convert images in directory to desire format

        Parameters
        ----------
        to_format : SupportedImageFormat
            Format to convert

        backup : bool
            Move pictures to a backup folder

        Raises
        ------
        NotImplementedError
            Not supported image format
        """
        if to_format not in self._supported_image_format:
            raise NotImplementedError("Format not supported")

        imgs = self.select_all(*self._make_suffix_selection(to_format))

        for x in tqdm(imgs, desc=f"Converting to {to_format}"):
            try:
                self._image_convert(x, to_format=to_format)

                if backup:
                    self.backup_path.mkdir(parents=True, exist_ok=True)
                    self._make_backup(x)
            except TypeError as err:
                print(f" TYPE ERROR: {x} - {err}")
            except Exception as err:
                print(f" ERROR: {x} - {err}")
