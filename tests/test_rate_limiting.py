"""Tests for ST-2 — Rate Limiting on /api/analyze/* endpoints.

Verifies that when the per-IP limit (20 req/min) is exceeded the server
returns HTTP 429 with the standard error envelope:
    {"error": {"code": "RATE_LIMITED", "message": "..."}}

Strategy
--------
slowapi stores the rate-limit state on the ``Limiter`` instance attached to
``app.state.limiter``.  To trigger a 429 without making 20 real requests we
patch the limiter's internal ``_check_request_limit`` method to raise
``RateLimitExceeded`` unconditionally, then assert on the response.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from slowapi.errors import RateLimitExceeded

from app.main import app

client = TestClient(app, raise_server_exceptions=False)

# ---------------------------------------------------------------------------
# Minimal request bodies for each endpoint
# ---------------------------------------------------------------------------

SIMPLIFY_BODY  = {"text": "Some legal text."}
RISKS_BODY     = {"text": "Some legal text."}
CHECKLIST_BODY = {"text": "Some legal text."}
COMPARE_BODY   = {"doc_a": "Text A.", "doc_b": "Text B."}
QA_BODY        = {"text": "Some legal text.", "question": "What does it say?"}


# ---------------------------------------------------------------------------
# Helper: build a valid RateLimitExceeded exception
# ---------------------------------------------------------------------------

def _make_rate_limit_exceeded() -> RateLimitExceeded:
    """Construct a RateLimitExceeded using a proper Limit-like mock."""
    fake_limit = MagicMock()
    fake_limit.error_message = None
    fake_limit.limit = "20 per 1 minute"
    return RateLimitExceeded(fake_limit)


# ---------------------------------------------------------------------------
# Helper: context manager that forces any limiter check to raise 429
# ---------------------------------------------------------------------------

def _force_rate_limit():
    """Patch slowapi so the very first request triggers a 429."""
    return patch(
        "app.limiter.limiter._check_request_limit",
        side_effect=_make_rate_limit_exceeded(),
    )


# ---------------------------------------------------------------------------
# Shared assertion helper
# ---------------------------------------------------------------------------

def _assert_429_envelope(resp) -> None:
    assert resp.status_code == 429, f"Expected 429, got {resp.status_code}"
    body = resp.json()
    assert "error" in body, "Response body must have an 'error' key"
    assert body["error"]["code"] == "RATE_LIMITED", (
        f"Expected code='RATE_LIMITED', got {body['error']['code']!r}"
    )
    assert isinstance(body["error"]["message"], str) and body["error"]["message"], (
        "error.message must be a non-empty string"
    )


# ===========================================================================
# Tests — one per endpoint
# ===========================================================================

class TestRateLimitSimplify:
    def test_429_status(self):
        with _force_rate_limit():
            resp = client.post("/api/analyze/simplify", json=SIMPLIFY_BODY)
        assert resp.status_code == 429

    def test_429_error_envelope(self):
        with _force_rate_limit():
            resp = client.post("/api/analyze/simplify", json=SIMPLIFY_BODY)
        _assert_429_envelope(resp)


class TestRateLimitRisks:
    def test_429_status(self):
        with _force_rate_limit():
            resp = client.post("/api/analyze/risks", json=RISKS_BODY)
        assert resp.status_code == 429

    def test_429_error_envelope(self):
        with _force_rate_limit():
            resp = client.post("/api/analyze/risks", json=RISKS_BODY)
        _assert_429_envelope(resp)


class TestRateLimitChecklist:
    def test_429_status(self):
        with _force_rate_limit():
            resp = client.post("/api/analyze/checklist", json=CHECKLIST_BODY)
        assert resp.status_code == 429

    def test_429_error_envelope(self):
        with _force_rate_limit():
            resp = client.post("/api/analyze/checklist", json=CHECKLIST_BODY)
        _assert_429_envelope(resp)


class TestRateLimitCompare:
    def test_429_status(self):
        with _force_rate_limit():
            resp = client.post("/api/analyze/compare", json=COMPARE_BODY)
        assert resp.status_code == 429

    def test_429_error_envelope(self):
        with _force_rate_limit():
            resp = client.post("/api/analyze/compare", json=COMPARE_BODY)
        _assert_429_envelope(resp)


class TestRateLimitQA:
    def test_429_status(self):
        with _force_rate_limit():
            resp = client.post("/api/analyze/qa", json=QA_BODY)
        assert resp.status_code == 429

    def test_429_error_envelope(self):
        with _force_rate_limit():
            resp = client.post("/api/analyze/qa", json=QA_BODY)
        _assert_429_envelope(resp)
