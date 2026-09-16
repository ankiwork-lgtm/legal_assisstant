"""PDF text extraction using pypdf (pure-Python, no disk writes)."""

from __future__ import annotations

import io
from dataclasses import dataclass

import pypdf

from app.utils.logger import get_logger

_logger = get_logger(__name__)

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
    _logger.debug("PDF extraction started — size=%d bytes", len(pdf_bytes))

    # ── Magic-byte validation ────────────────────────────────────────────────
    # Valid PDF files always begin with the 4-byte sequence b"%PDF" (0x25504446).
    # Checking this before pypdf prevents confusing internal exceptions when a
    # caller uploads a non-PDF file (e.g. an image renamed as .pdf).
    if len(pdf_bytes) < 4 or pdf_bytes[:4] != b"%PDF":
        _logger.warning("PDF magic bytes missing — rejecting non-PDF upload")
        raise CorruptPDFError(
            "The uploaded file does not appear to be a valid PDF "
            "(missing %PDF header). Please upload a text-based PDF file."
        )

    try:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    except Exception as exc:
        _logger.warning("PDF parse failed — %s", exc)
        raise CorruptPDFError(
            "The uploaded file could not be parsed as a PDF. "
            "Please check that it is a valid, non-encrypted PDF."
        ) from exc

    page_count = len(reader.pages)
    _logger.debug("PDF opened — pages=%d", page_count)

    if page_count == 0:
        _logger.warning("PDF has no pages")
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
        _logger.warning(
            "PDF appears scanned — avg_chars_per_page=%.1f (threshold=%d)",
            avg_chars_per_page,
            _MIN_CHARS_PER_PAGE,
        )
        raise ScannedPDFError(
            "This document appears to be a scanned or image-only PDF and contains "
            "no extractable text. Scanned PDFs are not supported in this version. "
            "Please upload a text-based PDF or paste the document text directly."
        )

    word_count = len(full_text.split())
    _logger.info(
        "PDF extracted — pages=%d  words=%d  chars=%d",
        page_count,
        word_count,
        total_chars,
    )
    return ExtractionResult(text=full_text, page_count=page_count, word_count=word_count)
