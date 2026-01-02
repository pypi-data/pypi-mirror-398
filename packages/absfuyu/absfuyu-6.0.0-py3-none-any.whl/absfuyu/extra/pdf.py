"""
Absfuyu: PDF
------------
PDF Tool [W.I.P]

Version: 6.0.0
Date updated: 27/12/2025 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = ["PDFTool"]


# Library
# ---------------------------------------------------------------------------
from collections.abc import Sequence
from pathlib import Path
from typing import overload

from absfuyu.core import BaseClass
from absfuyu.core.dummy_func import tqdm

PDF_MODE = False

try:
    from spire.pdf import PdfDocument, PdfTextExtractOptions, PdfTextExtractor
except ImportError:
    from subprocess import run

    from absfuyu.config import ABSFUYU_CONFIG

    if ABSFUYU_CONFIG._get_setting("auto-install-extra").value:  # type: ignore
        cmd = "python -m pip install -U absfuyu[pdf]".split()
        run(cmd)
    else:
        raise SystemExit("This feature is in absfuyu[pdf] package")  # noqa: B904
else:
    PDF_MODE = True


# Class
# ---------------------------------------------------------------------------
class PDFTool(BaseClass):
    def __init__(self) -> None:
        super().__init__()
        self.engine = PdfDocument()  # type: ignore

        self.files: list[Path] = []

    @overload
    def add_file(self, file: Path | str) -> None: ...

    @overload
    def add_file(self, file: Sequence[Path | str]) -> None: ...

    def add_file(self, file: Path | Sequence[Path | str] | str) -> None:
        if isinstance(file, Sequence) and not isinstance(file, str):
            self.files.extend([Path(x) for x in file])
        else:
            self.files.append(Path(file))

    def load_file(self) -> list[str]:
        """
        Extract text from all file

        Returns
        -------
        list[str]
            Extracted text
        """
        engine = PdfDocument()  # type: ignore

        extracted: list[str] = []
        for x in tqdm(self.files, desc="Extracting", unit_scale=True):
            engine.LoadFromFile(x.absolute().__str__())

            # Get pages
            for page in engine.Pages:
                # Create a PdfTextExtractor for the page
                extractor = PdfTextExtractor(page)  # type: ignore

                # Extract all text from the page
                text = extractor.ExtractText(PdfTextExtractOptions())  # type: ignore
                extracted.append(text)

        return extracted
