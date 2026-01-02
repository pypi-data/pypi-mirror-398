"""
Absfuyu: Audio
--------------
Audio convert

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = ["DirectoryAudioConvertMixin"]


# Library
# ---------------------------------------------------------------------------
import json
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Literal

from absfuyu.core.dummy_func import tqdm
from absfuyu.extra.audio._util import ResultStatus as ConvertStatus
from absfuyu.extra.audio._util import StatusCode
from absfuyu.util import is_command_available
from absfuyu.util.path import DirectoryBase


# Class
# ---------------------------------------------------------------------------
class DirectoryAudioConvertMixin(DirectoryBase):
    """
    Directory - Audio convert to mp3

    - convert_to_mp3
    """

    def __init__(self, source_path, create_if_not_exist=False):
        super().__init__(source_path, create_if_not_exist)
        is_command_available(["ffmpeg"], "ERROR: ffmpeg not installed to PATH")

    def _read_metadata(self, audio_path: Path, /) -> dict:
        """
        Read audio metadata

        Parameters
        ----------
        audio_path : Path
            Path to audio

        Returns
        -------
        dict
            Audio's metadata
        """
        cmd = [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            str(audio_path.resolve()),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)

        if "format" in data and "tags" in data["format"]:
            return data["format"]["tags"]
        return {}

    def convert_one(self, audio_path: Path | str, bitrate: Literal["128k", "320k"] = "320k") -> ConvertStatus:
        """
        Convert audio to mp3

        Parameters
        ----------
        audio_path : Path | str
            Path to audio

        bitrate : Literal["128k", "320k"], optional
            Bitrate, by default "320k"

        Returns
        -------
        ConvertStatus
            Result
        """
        audio_path = Path(audio_path)
        mp3_path = audio_path.with_suffix(".mp3")

        if mp3_path.exists():
            return ConvertStatus(StatusCode.SKIP, mp3_path)

        metadata = self._read_metadata(audio_path)

        ffmpeg_cmd = ["ffmpeg", "-y", "-i", str(audio_path.resolve())]

        # Add metadata tags
        for key, value in metadata.items():
            ffmpeg_cmd.extend(["-metadata", f"{key}={value}"])

        ffmpeg_cmd.extend(["-vn", "-codec:a", "libmp3lame", "-b:a", bitrate, str(mp3_path.resolve())])

        subprocess.run(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return ConvertStatus(StatusCode.OK, mp3_path)

    def convert_to_mp3_single_thread(
        self,
        from_format: str = ".flac",
        recursive: bool = True,
        bitrate: Literal["128k", "320k"] = "320k",
    ) -> None:
        """
        Convert audios to .mp3 - Single thread

        Parameters
        ----------
        from_format : str, optional
            Audio format, by default ".flac"

        recursive : bool, optional
            Include audio in child folder, by default True

        bitrate : Literal["128k", "320k"], optional
            Bitrate, by default "320k"
        """
        audios = list(self.source_path.rglob(f"{'**/*'if recursive else '*'}{from_format}"))

        if not audios:
            print(f"No {from_format.upper()} files found.")
            return None

        print(f"Found {len(audios)} {from_format.upper()} files.")

        results: list[ConvertStatus] = []
        for x in tqdm(audios, desc="Converting", unit="file", unit_scale=True):
            results.append(self.convert_one(x, bitrate=bitrate))

        print("\n--- Summary ---")
        for line in results:
            line.print()

    def convert_to_mp3(
        self,
        from_format: str = ".flac",
        workers: int | None = None,
        recursive: bool = True,
        bitrate: Literal["128k", "320k"] = "320k",
    ) -> None:
        """
        Convert audios to .mp3

        Parameters
        ----------
        from_format : str, optional
            Audio format, by default ".flac"

        workers : int | None, optional
            Number of parallel processing threads, by default None

        recursive : bool, optional
            Include audio in child folder, by default True

        bitrate : Literal["128k", "320k"], optional
            Bitrate, by default "320k"
        """
        audios = list(self.source_path.rglob(f"{'**/*'if recursive else '*'}{from_format}"))

        if not audios:
            print(f"No {from_format.upper()} files found.")
            return None

        print(f"Found {len(audios)} {from_format.upper()} files.")

        results: list[ConvertStatus] = []
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(self.convert_one, x, bitrate): x for x in audios}

            for fut in tqdm(
                as_completed(futures),
                total=len(futures),
                desc="Converting",
                unit="file",
                unit_scale=True,
            ):
                results.append(fut.result())

        print("\n--- Summary ---")
        for line in results:
            line.print()
