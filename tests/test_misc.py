"""Miscellaneous tests covering gaps identified in ST-T2.

Covers:
- GET /api/health  — health endpoint contract
- POST /api/documents/extract  — MIME-type rejection (non-PDF upload)
- POST /api/analyze/compare  — doc_b over MAX_TEXT_CHARS limit

All three test classes use a module-level TestClient(app) following the
pattern established in tests/test_phase3_simplify.py.
"""

from __future__ import annotations

import io

from fastapi.testclient import TestClient

from app.config import MAX_TEXT_CHARS
from app.main import app

client = TestClient(app)


# ===========================================================================
# Health endpoint
# ===========================================================================


class TestHealthEndpoint:
    def test_health_returns_200(self):
        resp = client.get("/api/health")
        assert resp.status_code == 200

    def test_health_returns_status_ok(self):
        resp = client.get("/api/health")
        assert resp.json() == {"status": "ok"}


# ===========================================================================
# MIME-type rejection on /api/documents/extract
# ===========================================================================


class TestMimeRejection:
    def test_non_pdf_upload_returns_400(self):
        resp = client.post(
            "/api/documents/extract",
            files={"file": ("image.png", io.BytesIO(b"fakecontent"), "image/png")},
        )
        assert resp.status_code == 400

    def test_non_pdf_upload_error_code_is_invalid_file_type(self):
        resp = client.post(
            "/api/documents/extract",
            files={"file": ("image.png", io.BytesIO(b"fakecontent"), "image/png")},
        )
        assert resp.json()["error"]["code"] == "INVALID_FILE_TYPE"


# ===========================================================================
# Compare doc_b over MAX_TEXT_CHARS limit
# ===========================================================================


class TestCompareLimits:
    def test_doc_b_over_limit_returns_400(self):
        resp = client.post(
            "/api/analyze/compare",
            json={
                "doc_a": "Valid short document text.",
                "doc_b": "x" * (MAX_TEXT_CHARS + 1),
            },
        )
        assert resp.status_code == 400

    def test_doc_b_over_limit_error_code_is_text_too_long(self):
        resp = client.post(
            "/api/analyze/compare",
            json={
                "doc_a": "Valid short document text.",
                "doc_b": "x" * (MAX_TEXT_CHARS + 1),
            },
        )
        assert resp.json()["error"]["code"] == "TEXT_TOO_LONG"
