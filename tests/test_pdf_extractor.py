"""Unit tests for app/services/pdf_extractor.py — Phase 1, task 1.5."""

from __future__ import annotations

import io

import pytest
import pypdf

from app.services.pdf_extractor import (
    CorruptPDFError,
    ExtractionResult,
    ScannedPDFError,
    extract_text,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_minimal_pdf(pages: list[str]) -> bytes:
    """Build hand-crafted minimal PDFs whose text pypdf can extract.

    Writes raw PDF syntax so that pypdf's WinAnsiEncoding / Type1 text
    extraction path can recover the page strings without needing reportlab
    or any extra dependency.
    """
    objects: list[bytes] = []

    def add_obj(content: bytes) -> int:
        objects.append(content)
        return len(objects)

    # Build per-page content stream + font + page dict
    page_obj_ids: list[int] = []
    for page_text in pages:
        safe = page_text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream_data = f"BT /F1 12 Tf 50 700 Td ({safe}) Tj ET".encode()
        stream_obj = (
            f"<< /Length {len(stream_data)} >>\nstream\n".encode()
            + stream_data
            + b"\nendstream"
        )
        content_id = add_obj(stream_obj)
        font_id = add_obj(
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica"
            b" /Encoding /WinAnsiEncoding >>"
        )
        # Use placeholder 9999 for /Parent — fixed up after pages dict is built
        page_obj = (
            f"<< /Type /Page /MediaBox [0 0 612 792] "
            f"/Contents {content_id} 0 R "
            f"/Resources << /Font << /F1 {font_id} 0 R >> >> "
            f"/Parent 9999 0 R >>"
        ).encode()
        page_id = add_obj(page_obj)
        page_obj_ids.append(page_id)

    # Pages dictionary
    kids = " ".join(f"{i} 0 R" for i in page_obj_ids)
    pages_id = add_obj(
        f"<< /Type /Pages /Kids [{kids}] /Count {len(page_obj_ids)} >>".encode()
    )

    # Patch /Parent in each page object
    for idx, page_text in enumerate(pages):
        safe = page_text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        c_id = page_obj_ids[idx] - 2
        f_id = page_obj_ids[idx] - 1
        objects[page_obj_ids[idx] - 1] = (
            f"<< /Type /Page /MediaBox [0 0 612 792] "
            f"/Contents {c_id} 0 R "
            f"/Resources << /Font << /F1 {f_id} 0 R >> >> "
            f"/Parent {pages_id} 0 R >>"
        ).encode()

    catalog_id = add_obj(
        f"<< /Type /Catalog /Pages {pages_id} 0 R >>".encode()
    )

    # Assemble body + xref + trailer
    body = b"%PDF-1.4\n"
    offsets: list[int] = []
    for i, obj_content in enumerate(objects, start=1):
        offsets.append(len(body))
        body += f"{i} 0 obj\n".encode() + obj_content + b"\nendobj\n"

    xref_offset = len(body)
    xref = f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n"
    for off in offsets:
        xref += f"{off:010d} 00000 n \n"
    trailer = (
        f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    )
    return body + xref.encode() + trailer.encode()


def _make_image_only_pdf(num_pages: int = 2) -> bytes:
    """Build a valid PDF with blank pages (no text streams) to simulate a scanned PDF."""
    writer = pypdf.PdfWriter()
    for _ in range(num_pages):
        writer.add_blank_page(width=612, height=792)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Tests — valid PDF path
# ---------------------------------------------------------------------------

class TestValidPDF:
    def test_returns_extraction_result_type(self):
        pdf = _make_minimal_pdf(["Hello world this is a legal contract document text here."])
        result = extract_text(pdf)
        assert isinstance(result, ExtractionResult)

    def test_page_count_matches(self):
        pdf = _make_minimal_pdf(
            ["Page one has enough text to pass the heuristic threshold check.",
             "Page two also has enough text to pass the minimum character threshold."]
        )
        result = extract_text(pdf)
        assert result.page_count == 2

    def test_word_count_positive(self):
        pdf = _make_minimal_pdf(["Hello world this is a legal contract document text."])
        result = extract_text(pdf)
        assert result.word_count > 0

    def test_text_contains_page_marker(self):
        pdf = _make_minimal_pdf(
            ["Some contract text on page one with plenty of words here."]
        )
        result = extract_text(pdf)
        assert "[Page 1]" in result.text

    def test_multi_page_markers_present(self):
        pdf = _make_minimal_pdf(
            ["First page content with enough characters here.",
             "Second page content with enough characters here."]
        )
        result = extract_text(pdf)
        assert "[Page 1]" in result.text
        assert "[Page 2]" in result.text


# ---------------------------------------------------------------------------
# Tests — corrupt / invalid PDF path
# ---------------------------------------------------------------------------

class TestCorruptPDF:
    def test_random_bytes_raises_corrupt_error(self):
        garbage = b"this is definitely not a pdf" + b"\x00\x01\x02" * 100
        with pytest.raises(CorruptPDFError):
            extract_text(garbage)

    def test_empty_bytes_raises_corrupt_error(self):
        with pytest.raises(CorruptPDFError):
            extract_text(b"")

    def test_truncated_pdf_raises_corrupt_error(self):
        truncated = b"%PDF-1.4\n" + b"garbage content that is not valid pdf structure"
        with pytest.raises((CorruptPDFError, ScannedPDFError)):
            extract_text(truncated)


# ---------------------------------------------------------------------------
# Tests — scanned / image-only PDF path
# ---------------------------------------------------------------------------

class TestScannedPDF:
    def test_blank_pages_raises_scanned_error(self):
        pdf = _make_image_only_pdf(num_pages=3)
        with pytest.raises(ScannedPDFError):
            extract_text(pdf)

    def test_scanned_error_message_mentions_scanned(self):
        pdf = _make_image_only_pdf(num_pages=1)
        with pytest.raises(ScannedPDFError, match="scanned"):
            extract_text(pdf)


# ---------------------------------------------------------------------------
# Tests — endpoint integration via TestClient
# ---------------------------------------------------------------------------

from fastapi.testclient import TestClient

from app.config import MAX_TEXT_CHARS
from app.main import app
from app.routers.documents import MAX_FILE_BYTES

client = TestClient(app, raise_server_exceptions=False)


class TestExtractEndpoint:
    def test_pasted_text_returns_200(self):
        resp = client.post("/api/documents/extract", data={"text": "This is a simple contract."})
        assert resp.status_code == 200
        body = resp.json()
        assert body["text"] == "This is a simple contract."
        assert body["word_count"] == 5
        assert body["page_count"] == 0

    def test_pasted_text_trims_whitespace(self):
        resp = client.post("/api/documents/extract", data={"text": "  hello world  "})
        assert resp.status_code == 200
        assert resp.json()["text"] == "hello world"

    def test_empty_text_returns_400(self):
        resp = client.post("/api/documents/extract", data={"text": "   "})
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "EMPTY_TEXT"

    def test_pasted_text_exceeding_limit_returns_text_too_long(self):
        resp = client.post("/api/documents/extract", data={"text": "x" * (MAX_TEXT_CHARS + 1)})
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "TEXT_TOO_LONG"

    def test_no_input_returns_400(self):
        resp = client.post("/api/documents/extract")
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "NO_INPUT"

    def test_valid_pdf_upload_returns_200(self):
        pdf = _make_minimal_pdf(
            ["This is a rental agreement between two parties with sufficient text content."]
        )
        resp = client.post(
            "/api/documents/extract",
            files={"file": ("contract.pdf", pdf, "application/pdf")},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["page_count"] == 1
        assert body["word_count"] > 0

    def test_corrupt_pdf_upload_returns_400(self):
        garbage = b"not a pdf at all " * 50
        resp = client.post(
            "/api/documents/extract",
            files={"file": ("bad.pdf", garbage, "application/pdf")},
        )
        assert resp.status_code in (400, 422)
        assert resp.json()["error"]["code"] in ("CORRUPT_PDF", "SCANNED_PDF")

    def test_scanned_pdf_returns_422(self):
        pdf = _make_image_only_pdf(num_pages=2)
        resp = client.post(
            "/api/documents/extract",
            files={"file": ("scanned.pdf", pdf, "application/pdf")},
        )
        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == "SCANNED_PDF"

    def test_oversized_file_returns_413(self):
        oversized = b"%PDF-1.4\n" + b" " * (MAX_FILE_BYTES + 1024)
        resp = client.post(
            "/api/documents/extract",
            files={"file": ("huge.pdf", oversized, "application/pdf")},
        )
        assert resp.status_code == 413
        assert resp.json()["error"]["code"] == "FILE_TOO_LARGE"

    def test_empty_file_returns_400(self):
        resp = client.post(
            "/api/documents/extract",
            files={"file": ("empty.pdf", b"", "application/pdf")},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "EMPTY_FILE"

    def test_non_pdf_bytes_return_400_corrupt_pdf(self):
        """A file with a .pdf name but non-PDF content should get CORRUPT_PDF (400)."""
        fake_pdf = b"JPEG\xff\xd8\xff\xe0 not a pdf"
        resp = client.post(
            "/api/documents/extract",
            files={"file": ("image.pdf", fake_pdf, "application/pdf")},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "CORRUPT_PDF"


# ---------------------------------------------------------------------------
# Unit-level magic-byte tests (call extract_text directly)
# ---------------------------------------------------------------------------

class TestMagicByteValidation:
    """Verify that extract_text() rejects non-PDF bytes before calling pypdf."""

    def test_rejects_completely_random_bytes(self):
        with pytest.raises(CorruptPDFError, match="does not appear to be a valid PDF"):
            extract_text(b"not a pdf at all")

    def test_rejects_jpeg_header(self):
        jpeg_header = b"\xff\xd8\xff\xe0\x00\x10JFIF"
        with pytest.raises(CorruptPDFError, match="does not appear to be a valid PDF"):
            extract_text(jpeg_header)

    def test_rejects_empty_bytes(self):
        with pytest.raises(CorruptPDFError):
            extract_text(b"")

    def test_rejects_three_byte_truncated_header(self):
        """Even %PD (3 bytes) should fail the 4-byte magic check."""
        with pytest.raises(CorruptPDFError):
            extract_text(b"%PD")

    def test_accepts_valid_pdf_header(self):
        """A real minimal PDF starting with %PDF should not raise CorruptPDFError
        at the magic-byte stage (it may fail later on parse, but not here)."""
        # Use a hand-crafted multi-page PDF from the helper if available,
        # or just confirm that b"%PDF" passes the magic check and gets to pypdf.
        valid_pdf = _make_minimal_pdf(
            ["Hello world this is a valid legal document with enough text content here."]
        )
        # Should not raise CorruptPDFError due to magic bytes
        result = extract_text(valid_pdf)
        assert result.page_count >= 1
