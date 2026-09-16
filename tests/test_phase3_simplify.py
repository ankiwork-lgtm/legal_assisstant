"""Tests for Phase 3 — Feature: Simplification (FR-2).

Covers:
- POST /api/analyze/simplify  (app/routers/simplify.py)
- Pydantic models: SimplifyRequest, SimplifySection, SimplifyResponse
- Structure preservation: obligations, dates, and amounts must survive in output
- Error paths: empty text → 400, Gemini failure → 502

The Gemini client is always mocked so these are pure unit/integration tests
that run offline with no API key.
"""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.config import MAX_TEXT_CHARS
from app.main import app

client = TestClient(app)

# ---------------------------------------------------------------------------
# Shared fixture: a realistic legal text containing obligations, dates, amounts
# ---------------------------------------------------------------------------

LEGAL_TEXT = (
    "SERVICE AGREEMENT\n\n"
    "1. Payment. The Client shall pay $5,000 per month due on the 1st of each month. "
    "Late payments accrue interest at 1.5% per month.\n\n"
    "2. Term. This Agreement commences on January 1, 2025 and terminates on "
    "December 31, 2025 unless renewed in writing by both parties.\n\n"
    "3. Obligations. The Service Provider shall deliver weekly status reports every "
    "Friday. The Client shall provide access credentials within 5 business days of "
    "signing.\n\n"
    "4. Termination. Either party may terminate this Agreement with 30 days written "
    "notice. Immediate termination is permitted upon material breach.\n\n"
    "5. Liability. In no event shall either party's liability exceed the total fees "
    "paid in the 3 months preceding the claim."
)

# Canonical mock Gemini response — valid shape, mentions obligations/dates/amounts
MOCK_SIMPLIFY_RESPONSE = {
    "overview": (
        "This is a one-year service contract from January 2025 to December 2025. "
        "The client pays $5,000/month and both parties have specific obligations."
    ),
    "sections": [
        {
            "heading": "Payment",
            "original_excerpt_ref": "Section 1 — '$5,000 per month due on the 1st'",
            "plain_language": (
                "You must pay $5,000 every month on the 1st. "
                "If you pay late, you will owe an extra 1.5% interest per month."
            ),
        },
        {
            "heading": "Term",
            "original_excerpt_ref": "Section 2 — 'January 1, 2025 … December 31, 2025'",
            "plain_language": (
                "The agreement runs from January 1, 2025 to December 31, 2025. "
                "To renew, both sides must agree in writing."
            ),
        },
        {
            "heading": "Obligations",
            "original_excerpt_ref": "Section 3 — 'weekly status reports … within 5 business days'",
            "plain_language": (
                "The service provider must send a status report every Friday. "
                "You must share login credentials within 5 business days of signing."
            ),
        },
        {
            "heading": "Termination",
            "original_excerpt_ref": "Section 4 — '30 days written notice'",
            "plain_language": (
                "Either side can end this contract by giving 30 days written notice. "
                "If one party seriously breaks the contract, the other can end it immediately."
            ),
        },
        {
            "heading": "Liability Cap",
            "original_excerpt_ref": "Section 5 — 'not exceed the total fees paid in the 3 months'",
            "plain_language": (
                "Neither party can be sued for more than the total amount paid in "
                "the 3 months before the dispute."
            ),
        },
    ],
}


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _mock_generate(payload: dict):
    """Patch generate_structured to return *payload* without calling Gemini."""
    return patch(
        "app.routers.simplify.generate_structured",
        return_value=payload,
    )


# ===========================================================================
# Happy-path: structure and fields
# ===========================================================================

class TestSimplifyEndpointHappyPath:
    def test_returns_200(self):
        with _mock_generate(MOCK_SIMPLIFY_RESPONSE):
            resp = client.post("/api/analyze/simplify", json={"text": LEGAL_TEXT})
        assert resp.status_code == 200

    def test_response_has_overview_field(self):
        with _mock_generate(MOCK_SIMPLIFY_RESPONSE):
            resp = client.post("/api/analyze/simplify", json={"text": LEGAL_TEXT})
        body = resp.json()
        assert "overview" in body
        assert isinstance(body["overview"], str)
        assert len(body["overview"]) > 0

    def test_response_has_sections_list(self):
        with _mock_generate(MOCK_SIMPLIFY_RESPONSE):
            resp = client.post("/api/analyze/simplify", json={"text": LEGAL_TEXT})
        body = resp.json()
        assert "sections" in body
        assert isinstance(body["sections"], list)

    def test_at_least_one_section_returned(self):
        with _mock_generate(MOCK_SIMPLIFY_RESPONSE):
            resp = client.post("/api/analyze/simplify", json={"text": LEGAL_TEXT})
        body = resp.json()
        assert len(body["sections"]) >= 1

    def test_each_section_has_required_fields(self):
        with _mock_generate(MOCK_SIMPLIFY_RESPONSE):
            resp = client.post("/api/analyze/simplify", json={"text": LEGAL_TEXT})
        for section in resp.json()["sections"]:
            assert "heading" in section, "section missing 'heading'"
            assert "original_excerpt_ref" in section, "section missing 'original_excerpt_ref'"
            assert "plain_language" in section, "section missing 'plain_language'"

    def test_section_fields_are_non_empty_strings(self):
        with _mock_generate(MOCK_SIMPLIFY_RESPONSE):
            resp = client.post("/api/analyze/simplify", json={"text": LEGAL_TEXT})
        for section in resp.json()["sections"]:
            assert isinstance(section["heading"], str) and section["heading"].strip()
            assert isinstance(section["original_excerpt_ref"], str) and section["original_excerpt_ref"].strip()
            assert isinstance(section["plain_language"], str) and section["plain_language"].strip()


# ===========================================================================
# Structure preservation: obligations, dates, monetary amounts
# ===========================================================================

class TestStructurePreservation:
    """Verify that the output sections collectively preserve the key content types
    present in the input document (obligations, dates, amounts).

    The mock response mirrors the real document faithfully, so these assertions
    confirm that the router/schema pipeline does not silently drop content.
    """

    def _get_all_text(self, body: dict) -> str:
        """Concatenate overview + all section plain_language fields."""
        parts = [body["overview"]]
        for section in body["sections"]:
            parts.append(section["plain_language"])
            parts.append(section["original_excerpt_ref"])
        return " ".join(parts).lower()

    def test_monetary_amount_preserved(self):
        """$5,000 monthly fee must appear in the output."""
        with _mock_generate(MOCK_SIMPLIFY_RESPONSE):
            resp = client.post("/api/analyze/simplify", json={"text": LEGAL_TEXT})
        all_text = self._get_all_text(resp.json())
        assert "5,000" in all_text, "Monetary amount $5,000 was dropped from output"

    def test_start_date_preserved(self):
        """Contract start date (January 2025) must appear in the output."""
        with _mock_generate(MOCK_SIMPLIFY_RESPONSE):
            resp = client.post("/api/analyze/simplify", json={"text": LEGAL_TEXT})
        all_text = self._get_all_text(resp.json())
        assert "january" in all_text or "2025" in all_text, (
            "Contract start date was dropped from output"
        )

    def test_end_date_preserved(self):
        """Contract end date (December 2025) must appear in the output."""
        with _mock_generate(MOCK_SIMPLIFY_RESPONSE):
            resp = client.post("/api/analyze/simplify", json={"text": LEGAL_TEXT})
        all_text = self._get_all_text(resp.json())
        assert "december" in all_text or "2025" in all_text, (
            "Contract end date was dropped from output"
        )

    def test_obligation_notice_period_preserved(self):
        """30-day termination notice obligation must appear in the output."""
        with _mock_generate(MOCK_SIMPLIFY_RESPONSE):
            resp = client.post("/api/analyze/simplify", json={"text": LEGAL_TEXT})
        all_text = self._get_all_text(resp.json())
        assert "30 day" in all_text or "30-day" in all_text, (
            "30-day termination notice obligation was dropped from output"
        )

    def test_obligation_weekly_reports_preserved(self):
        """Weekly status report obligation must appear in the output."""
        with _mock_generate(MOCK_SIMPLIFY_RESPONSE):
            resp = client.post("/api/analyze/simplify", json={"text": LEGAL_TEXT})
        all_text = self._get_all_text(resp.json())
        assert "friday" in all_text or "weekly" in all_text or "status report" in all_text, (
            "Weekly status report obligation was dropped from output"
        )

    def test_section_count_matches_document_clauses(self):
        """There should be one section per major clause (5 in the mock document)."""
        with _mock_generate(MOCK_SIMPLIFY_RESPONSE):
            resp = client.post("/api/analyze/simplify", json={"text": LEGAL_TEXT})
        assert len(resp.json()["sections"]) == 5

    def test_original_excerpt_ref_traces_back_to_source(self):
        """Each original_excerpt_ref must contain a section number or quoted text."""
        with _mock_generate(MOCK_SIMPLIFY_RESPONSE):
            resp = client.post("/api/analyze/simplify", json={"text": LEGAL_TEXT})
        for section in resp.json()["sections"]:
            ref = section["original_excerpt_ref"]
            # Should reference a section number OR contain a quoted fragment
            has_section_ref = any(
                f"section {i}" in ref.lower() or f"§ {i}" in ref.lower()
                for i in range(1, 10)
            )
            has_quote = "'" in ref or '"' in ref or "…" in ref
            assert has_section_ref or has_quote, (
                f"original_excerpt_ref '{ref}' doesn't reference source text"
            )


# ===========================================================================
# Error paths
# ===========================================================================

class TestSimplifyEndpointErrors:
    def test_empty_text_returns_400(self):
        resp = client.post("/api/analyze/simplify", json={"text": "   "})
        assert resp.status_code == 400

    def test_empty_text_error_code(self):
        resp = client.post("/api/analyze/simplify", json={"text": "   "})
        body = resp.json()
        assert body["error"]["code"] == "EMPTY_TEXT"

    def test_text_exceeding_limit_returns_text_too_long(self):
        resp = client.post("/api/analyze/simplify", json={"text": "x" * (MAX_TEXT_CHARS + 1)})
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "TEXT_TOO_LONG"

    def test_missing_text_field_returns_422(self):
        """Pydantic validation rejects a missing required field."""
        resp = client.post("/api/analyze/simplify", json={})
        assert resp.status_code == 422

    def test_gemini_failure_returns_502(self):
        from app.services.anthropic_client import AnthropicServiceError as GeminiServiceError

        with patch(
            "app.routers.simplify.generate_structured",
            side_effect=GeminiServiceError("AI down"),
        ):
            resp = client.post("/api/analyze/simplify", json={"text": LEGAL_TEXT})
        assert resp.status_code == 502

    def test_gemini_failure_error_code(self):
        from app.services.anthropic_client import AnthropicServiceError as GeminiServiceError

        with patch(
            "app.routers.simplify.generate_structured",
            side_effect=GeminiServiceError("AI down"),
        ):
            resp = client.post("/api/analyze/simplify", json={"text": LEGAL_TEXT})
        body = resp.json()
        assert body["error"]["code"] == "AI_SERVICE_ERROR"

    def test_unexpected_exception_returns_500(self):
        with patch(
            "app.routers.simplify.generate_structured",
            side_effect=RuntimeError("unexpected"),
        ):
            resp = client.post("/api/analyze/simplify", json={"text": LEGAL_TEXT})
        assert resp.status_code == 500

    def test_unexpected_exception_does_not_leak_details(self):
        with patch(
            "app.routers.simplify.generate_structured",
            side_effect=RuntimeError("secret internal detail"),
        ):
            resp = client.post("/api/analyze/simplify", json={"text": LEGAL_TEXT})
        assert "secret internal detail" not in resp.text


# ===========================================================================
# Pydantic model validation
# ===========================================================================

class TestPydanticModels:
    def test_simplify_request_rejects_empty_string(self):
        from pydantic import ValidationError
        from app.models.schemas import SimplifyRequest

        with pytest.raises(ValidationError):
            SimplifyRequest(text="")

    def test_simplify_section_requires_all_three_fields(self):
        from pydantic import ValidationError
        from app.models.schemas import SimplifySection

        with pytest.raises(ValidationError):
            SimplifySection(heading="h", original_excerpt_ref="ref")  # missing plain_language

    def test_simplify_response_valid(self):
        from app.models.schemas import SimplifyResponse, SimplifySection

        resp = SimplifyResponse(
            overview="This is a test.",
            sections=[
                SimplifySection(
                    heading="Payment",
                    original_excerpt_ref="Clause 1",
                    plain_language="You pay $100 monthly.",
                )
            ],
        )
        assert resp.overview == "This is a test."
        assert len(resp.sections) == 1

    def test_simplify_response_empty_sections_allowed(self):
        """Edge case: model may return zero sections for a trivial document."""
        from app.models.schemas import SimplifyResponse

        resp = SimplifyResponse(overview="Simple doc.", sections=[])
        assert resp.sections == []
