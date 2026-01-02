"""
Absfuyu: Audio
--------------
Audio lossless checker

Version: 6.0.0
Date updated: 23/11/2025 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = ["AudioInfo", "DirectoryAudioLosslessCheckMixin"]


# Library
# ---------------------------------------------------------------------------
import json
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, NamedTuple

from absfuyu.core.dummy_func import tqdm
from absfuyu.extra.audio._util import ResultStatus, StatusCode
from absfuyu.util import is_command_available
from absfuyu.util.path import DirectoryBase
from absfuyu.util.shorten_number import Duration

try:
    import numpy as np
except ImportError:
    from subprocess import run

    from absfuyu.config import ABSFUYU_CONFIG

    if ABSFUYU_CONFIG._get_setting("auto-install-extra").value:  # type: ignore
        cmd = "python -m pip install -U absfuyu[extra]".split()
        run(cmd)
    else:
        raise SystemExit("This feature is in absfuyu[extra] package")  # noqa: B904


# Class
# ---------------------------------------------------------------------------
class FrequencyRange(NamedTuple):
    """Audio frequency range"""

    min: int | float
    max: int | float


@dataclass
class AudioInfo:
    """
    Audio infomation

    Parameters
    ----------
    sample_rate : int | None, optional
        Sample rate (Hz)

    bit_depth : int, optional
        Bit depth

    channels : int | None, optional
        Number of channels

    codec : str | None, optional
        Audio codec

    duration_raw : float, optional
        Duration of audio (second)

    bitrate : Any | None, optional
        Bitrate

    audio_path : Path | None, optional
        Path to audio

    Returns
    -------
    AudioInfo
        Audio infomation
    """

    sample_rate: int | None = field(default=None, metadata={"unit": "Hz"})
    bit_depth: int = field(default=0, metadata={"unit": "bit"})
    channels: int | None = field(default=None)
    codec: str | None = field(default=None)
    duration_raw: float = field(default=0.0, repr=False, metadata={"unit": "second"})
    bitrate: int | None = field(default=None)
    audio_path: Path | None = field(default=None, repr=False)  # hide path in repr

    # computed fields
    duration: float = field(init=False)
    freq_range: FrequencyRange = field(init=False, metadata={"unit": "Hz"})

    def __post_init__(self):
        self.duration = Duration(self.duration_raw)

        # Resource intensive method
        # _, sampling_rate = librosa.load(audio_path, sr=None)
        # freqs = librosa.fft_frequencies(sr=sampling_rate)
        freqs = np.fft.rfftfreq(n=2048, d=1.0 / self.sample_rate)
        self.freq_range = FrequencyRange(freqs[0], freqs[-1])

    @property
    def is_lossless(self) -> bool:
        """
        Audio is lossless when frequencies above 20,000 are not cut off

        Returns
        -------
        bool
            If audio is lossless
        """
        return self.freq_range[1] >= 20000

    @property
    def is_hi_res(self) -> bool:
        """
        Audio is HiRes when lossless and have sample rate >= 48,000Hz or bit rate >= 16 bit

        Returns
        -------
        bool
            If audio is lossless
        """
        bd = 0 if self.bit_depth is None else self.bit_depth
        return all([self.sample_rate >= 48000, bd >= 24, self.is_lossless])


class DirectoryAudioLosslessCheckMixin(DirectoryBase):
    """
    Directory - Audio lossless checker

    - lossless_check
    """

    def get_audio_info(self, audio_path: Path, /) -> AudioInfo:
        """
        Return audio info using ffprobe.

        Parameters
        ----------
        audio_path : Path
            Path to audio

        Returns
        -------
        AudioInfo
            Audio infomation
        """

        is_command_available(["ffmpeg"], "ERROR: ffmpeg not installed to PATH")

        # Probe
        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_streams",
            "-select_streams",
            "a:0",
            str(audio_path.resolve()),
        ]

        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        data: dict[str, Any] = json.loads(result.stdout)["streams"][0]

        bit_depth = data.get("bits_per_sample") or data.get("bits_per_raw_sample")
        if bit_depth is not None:
            bit_depth = int(bit_depth)

        ai = AudioInfo(
            sample_rate=int(data.get("sample_rate", 0)),
            bit_depth=bit_depth,
            channels=data.get("channels"),
            codec=data.get("codec_name"),
            duration_raw=float(data["duration"]) if "duration" in data else None,
            bitrate=int(data["bit_rate"]) if "bit_rate" in data else None,
            audio_path=audio_path,
        )
        return ai

    def lossless_check_one(self, audio_path: Path) -> ResultStatus:
        """
        Check if audio is lossless

        Parameters
        ----------
        audio_path : Path
            Path to audio

        Returns
        -------
        ResultStatus
            If audio is lossless
        """
        res = self.get_audio_info(audio_path)
        if res.is_hi_res:
            return ResultStatus(StatusCode.HIRES, audio_path)
        elif res.is_lossless:
            return ResultStatus(StatusCode.LOSSLESS, audio_path)
        return ResultStatus(StatusCode.NOT_LOSSLESS, audio_path)

    def lossless_check_single_thread(self, from_format: str = ".flac", recursive: bool = True) -> None:
        """
        Check if audios in directory are lossless - single thread version

        Parameters
        ----------
        from_format : str, optional
            Audio format, by default ".flac"

        recursive : bool, optional
            Include audio in child folder, by default True
        """
        audios = list(self.source_path.rglob(f"{'**/*'if recursive else '*'}{from_format}"))

        if not audios:
            print(f"No {from_format.upper()} files found.")
            return None

        print(f"Found {len(audios)} {from_format.upper()} files.")

        results: list[ResultStatus] = []
        for x in tqdm(audios, desc="Checking", unit="file", unit_scale=True):
            results.append(self.lossless_check_one(x))

        print("\n--- Summary ---")
        for line in results:
            line.print()

    def lossless_check(
        self,
        from_format: str = ".flac",
        recursive: bool = True,
        workers: int | None = None,
    ) -> None:
        """
        Check if audios in directory are lossless

        Parameters
        ----------
        from_format : str, optional
            Audio format, by default ".flac"

        recursive : bool, optional
            Include audio in child folder, by default True

        workers : int | None, optional
            Number of parallel processing threads, by default None
        """
        audios = list(self.source_path.rglob(f"{'**/*'if recursive else '*'}{from_format}"))

        if not audios:
            print(f"No {from_format.upper()} files found.")
            return None

        print(f"Found {len(audios)} {from_format.upper()} files.")

        results: list[ResultStatus] = []
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(self.lossless_check_one, x): x for x in audios}

            for fut in tqdm(
                as_completed(futures),
                total=len(futures),
                desc="Checking",
                unit="file",
                unit_scale=True,
            ):
                results.append(fut.result())

        print("\n--- Summary ---")
        for line in results:
            line.print()
