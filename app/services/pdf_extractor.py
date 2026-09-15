"""PDF text extraction using pypdf (pure-Python, no disk writes)."""

from __future__ import annotations

import io
from dataclasses import dataclass

import pypdf

# Minimum average characters per page to consider a PDF text-bearing.
# Below this threshold we treat the file as a scanned/image PDF.
_MIN_CHARS_PER_PAGE = 50


@dataclass
class ExtractionResult:
    text: str
    page_count: int
    word_count: int


class ScannedPDFError(ValueError):
    """Raised when a PDF appears to contain no extractable text (scanned/image PDF)."""


class CorruptPDFError(ValueError):
    """Raised when the uploaded bytes cannot be parsed as a valid PDF."""


def extract_text(pdf_bytes: bytes) -> ExtractionResult:
    """Extract text from *pdf_bytes* held entirely in memory.

    Returns an :class:`ExtractionResult` on success.

    Raises:
        CorruptPDFError: if *pdf_bytes* is not a parseable PDF.
        ScannedPDFError: if the PDF has pages but no meaningful text content
            (heuristic: average < ``_MIN_CHARS_PER_PAGE`` chars/page).
    """
    try:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    except Exception as exc:
        raise CorruptPDFError(
            "The uploaded file could not be parsed as a PDF. "
            "Please check that it is a valid, non-encrypted PDF."
        ) from exc

    page_count = len(reader.pages)

    if page_count == 0:
        raise CorruptPDFError(
            "The uploaded PDF has no pages. "
            "Please upload a non-empty PDF file."
        )

    page_texts: list[str] = []
    for page_num, page in enumerate(reader.pages, start=1):
        raw = page.extract_text() or ""
        # Annotate with page marker so clause references can mention page numbers.
        page_texts.append(f"[Page {page_num}]\n{raw}")

    full_text = "\n\n".join(page_texts)
    total_chars = sum(len(p) for p in page_texts)
    avg_chars_per_page = total_chars / page_count

    if avg_chars_per_page < _MIN_CHARS_PER_PAGE:
        raise ScannedPDFError(
            "This document appears to be a scanned or image-only PDF and contains "
            "no extractable text. Scanned PDFs are not supported in this version. "
            "Please upload a text-based PDF or paste the document text directly."
        )

    word_count = len(full_text.split())
    return ExtractionResult(text=full_text, page_count=page_count, word_count=word_count)
