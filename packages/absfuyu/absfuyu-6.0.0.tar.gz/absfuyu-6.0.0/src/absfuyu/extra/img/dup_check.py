"""
Absfuyu: Image duplicate checker
--------------------------------
Image duplicate checker


Version: 6.0.0
Date updated: 25/11/2025 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = ["DirectoryRemoveDuplicateImageMixin"]


# Library
# ---------------------------------------------------------------------------
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from functools import partial, total_ordering
from pathlib import Path
from typing import Literal, NamedTuple

from absfuyu.core.dummy_func import tqdm as tqdm_base
from absfuyu.tools.checksum import DirectoryRemoveDuplicateMixin, DuplicateSummary

try:
    import imagehash
    from PIL import Image
except ImportError:
    from subprocess import run

    from absfuyu.config import ABSFUYU_CONFIG

    if ABSFUYU_CONFIG._get_setting("auto-install-extra").value:  # type: ignore
        cmd = "python -m pip install -U absfuyu[pic]".split()
        run(cmd)
    else:
        raise SystemExit("This feature is in absfuyu[pic] package")  # noqa: B904

# Setup
# ---------------------------------------------------------------------------
tqdm = partial(tqdm_base, unit_scale=True, dynamic_ncols=True)
SupportedImageFormat = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


# Class
# ---------------------------------------------------------------------------
class HashMode(StrEnum):
    PERCEPTUAL_HASH = "phash"
    AVERAGE_HASH = "ahash"
    DIFFERENCE_HASH = "dhash"
    WAVELET_HASH = "whash"


class DuplicateImgPair(NamedTuple):
    """
    Duplicate image pair

    Parameters
    ----------
    original : Path
        Original image path

    duplicate : Path
        Duplicate image path

    distant : int
        Similarity between image (0 is exact)
    """

    original: Path
    duplicate: Path
    distant: int


@total_ordering
@dataclass
class ImageInfo:
    """
    Quick image info

    Parameters
    ----------
    path : Path
        Image path

    file_size : int
        File size

    dimension : tuple[int, int]
        Dimension (width, height)
    """

    path: Path
    file_size: int
    dimension: tuple[int, int]

    def __eq__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            raise NotImplementedError("Not implemented")
        return self.dimension == other.dimension and self.file_size == other.file_size

    def __lt__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            raise NotImplementedError("Not implemented")

        # prioritize dimension first, then size
        if self.dimension != other.dimension:
            return self.dimension < other.dimension
        return self.file_size < other.file_size


class DirectoryRemoveDuplicateImageMixin(DirectoryRemoveDuplicateMixin):
    """
    Directory - Remove duplicate image

    - remove_duplicate_images


    Example:
    --------
    >>> DirectoryRemoveDuplicateImageMixin(".").remove_duplicate_images()
    """

    def __init__(self, source_path, create_if_not_exist=False) -> None:
        super().__init__(source_path, create_if_not_exist)

        # Unused yet
        self._duplicate_image_cache = None

    # Hash
    def _get_img_hash_mode(
        self, hash_mode: HashMode = HashMode.PERCEPTUAL_HASH
    ) -> Callable[[Image, int], imagehash.ImageHash]:
        """
        Get image hash mode

        Parameters
        ----------
        hash_mode : HashMode, optional
            Hash mode, by default ``HashMode.PERCEPTUAL_HASH``

        Returns
        -------
        Callable[[Image, int], imagehash.ImageHash]
            Hash function
        """
        if hash_mode == HashMode.AVERAGE_HASH:
            return imagehash.average_hash
        elif hash_mode == HashMode.DIFFERENCE_HASH:
            return imagehash.dhash
        elif hash_mode == HashMode.WAVELET_HASH:
            return imagehash.whash
        else:
            return imagehash.phash

    def _gather_duplicate_image_cache(
        self, recursive: bool = True, threshold: int = 5, hash_mode: HashMode = HashMode.PERCEPTUAL_HASH
    ) -> None:
        """
        Gather duplicate image cache

        Parameters
        ----------
        recursive : bool, optional
            Scan every file in the folder (including child folder), by default ``True``

        threshold : int, optional
            Maximum hamming distance between image hashes to consider them "similar", by default ``5``
            - 0: Exact image
            - [5,10]: Tolerant of light edits

        hash_mode : HashMode, optional
            Hash mode, by default ``HashMode.PERCEPTUAL_HASH``
        """
        valid = [
            x
            for x in self.source_path.glob("**/*" if recursive else "*")
            if x.is_file() and x.suffix.lower() in SupportedImageFormat
        ]
        hash_cache: dict[imagehash.ImageHash, list[Path]] = {}
        duplicates: list[DuplicateImgPair] = []

        # Checksum
        for x in tqdm(valid, desc="Hashing image..."):
            try:
                with Image.open(x) as img:
                    hash_func = self._get_img_hash_mode(hash_mode=hash_mode)
                    hash = hash_func(img)  # perceptual hash

            except Exception as err:
                print(f"ERROR: {x} - {err}")
                continue

            # Compare against all cached hashes
            found = False
            for existing_hash, paths in hash_cache.items():
                distance = hash - existing_hash
                if distance <= threshold:
                    duplicates.append(DuplicateImgPair(paths[0], x, distance))
                    if x not in paths:
                        paths.append(x)
                    found = True
                    break

            if not found:
                hash_cache[hash] = [x]

        # Save to cache
        self._duplicate_cache = DuplicateSummary({k: v for k, v in hash_cache.items() if len(v) > 1})
        self._duplicate_image_cache = duplicates

    # Remove
    def _gather_img_info(self, image_path: Path) -> ImageInfo:
        with Image.open(image_path) as img:
            dim = img.size
        return ImageInfo(image_path, image_path.stat().st_size, dim)

    def _remove_duplicate_image_best(self, dry_run: bool = True, debug: bool = True) -> None:
        """This will take image with large size in dimension and storage"""
        if self._duplicate_cache is None or self._duplicate_image_cache is None:
            raise ValueError("No duplicates found")

        del_list: list[ImageInfo] = []
        for paths in self._duplicate_cache.values():
            # Sort image by dimension then size ascending order then cut the last value
            data = sorted([self._gather_img_info(img) for img in paths])[:-1]
            # Extend to delete list
            del_list.extend(data)

        for i, x in enumerate(del_list, start=1):
            if debug:
                print(f"{i:02}. Deleting {x.path}")
            if not dry_run:
                x.path.unlink(missing_ok=True)

    # Main
    def remove_duplicate_images(
        self,
        dry_run: bool = True,
        recursive: bool = True,
        threshold: int = 5,
        hash_mode: HashMode = HashMode.PERCEPTUAL_HASH,
        keep_mode: Literal["first", "last", "best"] = "best",
        debug: bool = True,
    ) -> None:
        """
        Remove duplicate images in a directory

        Parameters
        ----------
        dry_run : bool, optional
            Simulate only (no files deleted), by default ``True``

        recursive : bool, optional
            Scan every file in the folder (including child folder), by default ``True``

        threshold : int, optional
            Maximum hamming distance between image hashes to consider them "similar", by default ``5``
            - 0: Exact image
            - [5,10]: Tolerant of light edits

        hash_mode : HashMode, optional
            Hash mode, by default ``HashMode.PERCEPTUAL_HASH``

        keep_mode : Literal["first", "last", "best"], optional
            What to keep in duplicate images, by default ``"best"``
            - "first": First item in delete list
            - "last": Last item in delete list
            - "best": Best item (largest dimension and size) in delete list

        debug : bool, optional
            Debug message, by default ``True``
        """
        # Cache
        self._gather_duplicate_image_cache(recursive=recursive, threshold=threshold, hash_mode=hash_mode)

        # Remove
        try:
            if keep_mode in ["first", "last"]:
                summary = self._duplicate_cache
                print(f"Duplicate files: {summary.summary()}")
                summary.remove_duplicates(dry_run=dry_run, keep_first=keep_mode == "first", debug=debug)

            else:  # best mode
                self._remove_duplicate_image_best(dry_run=dry_run, debug=debug)

        except Exception as err:
            pass
