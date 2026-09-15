"""Tests for Phase 5 — Feature: Checklist Generator (FR-6).

Covers:
- POST /api/analyze/checklist  (app/routers/checklist.py)
- Pydantic models: ChecklistRequest, ChecklistResponse
- Happy path: 200 response, both lists present and non-empty
- Both ask_lawyer and verify_yourself are lists of strings
- Error paths: empty text → 400, Gemini failure → 502, unexpected error → 500
- Pydantic model validation (direct unit tests)

The Gemini client is always mocked so these are pure unit/integration tests
that run offline with no API key.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

LEGAL_TEXT = (
    "SERVICE AGREEMENT\n\n"
    "1. Payment Terms. Client shall pay $5,000 per month, due on the 1st of each month. "
    "Late payments incur a 2% monthly interest charge.\n\n"
    "2. Termination. Either party may terminate this Agreement with 30 days written notice. "
    "Upon termination, all outstanding fees become immediately due and payable.\n\n"
    "3. Confidentiality. Both parties agree to keep all business information confidential "
    "for a period of 3 years after termination of this Agreement.\n\n"
    "4. Intellectual Property. Any work product created under this Agreement remains the "
    "exclusive property of the Client upon full payment.\n\n"
    "5. Limitation of Liability. Provider's total liability shall not exceed the fees paid "
    "in the three months immediately preceding the claim."
)

# Canonical mock Gemini response — valid shape with non-empty lists
MOCK_CHECKLIST_RESPONSE = {
    "ask_lawyer": [
        "Ask a lawyer whether the 2% monthly late-payment interest rate is enforceable in your jurisdiction.",
        "Clarify with counsel whether the IP assignment clause (Section 4) covers pre-existing materials.",
        "Verify with an attorney whether the confidentiality obligation survives early termination.",
    ],
    "verify_yourself": [
        "Confirm the monthly fee amount ($5,000) matches what was verbally agreed.",
        "Check that the payment due date (1st of each month) fits your cash-flow cycle.",
        "Ensure the 30-day termination notice window gives you adequate transition time.",
        "Verify that the 3-year confidentiality period aligns with your internal data policies.",
        "Confirm the party names and addresses in the agreement are spelled correctly.",
    ],
}


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _mock_generate(payload: dict):
    """Patch generate_structured to return *payload* without calling Gemini."""
    return patch(
        "app.routers.checklist.generate_structured",
        return_value=payload,
    )


# ===========================================================================
# Happy-path: structure and fields
# ===========================================================================

class TestChecklistEndpointHappyPath:
    def test_returns_200(self):
        with _mock_generate(MOCK_CHECKLIST_RESPONSE):
            resp = client.post("/api/analyze/checklist", json={"text": LEGAL_TEXT})
        assert resp.status_code == 200

    def test_response_has_ask_lawyer_field(self):
        with _mock_generate(MOCK_CHECKLIST_RESPONSE):
            resp = client.post("/api/analyze/checklist", json={"text": LEGAL_TEXT})
        body = resp.json()
        assert "ask_lawyer" in body

    def test_response_has_verify_yourself_field(self):
        with _mock_generate(MOCK_CHECKLIST_RESPONSE):
            resp = client.post("/api/analyze/checklist", json={"text": LEGAL_TEXT})
        body = resp.json()
        assert "verify_yourself" in body

    def test_ask_lawyer_is_list(self):
        with _mock_generate(MOCK_CHECKLIST_RESPONSE):
            resp = client.post("/api/analyze/checklist", json={"text": LEGAL_TEXT})
        body = resp.json()
        assert isinstance(body["ask_lawyer"], list)

    def test_verify_yourself_is_list(self):
        with _mock_generate(MOCK_CHECKLIST_RESPONSE):
            resp = client.post("/api/analyze/checklist", json={"text": LEGAL_TEXT})
        body = resp.json()
        assert isinstance(body["verify_yourself"], list)

    def test_ask_lawyer_non_empty(self):
        with _mock_generate(MOCK_CHECKLIST_RESPONSE):
            resp = client.post("/api/analyze/checklist", json={"text": LEGAL_TEXT})
        body = resp.json()
        assert len(body["ask_lawyer"]) >= 1, "ask_lawyer list must be non-empty for a complex document"

    def test_verify_yourself_non_empty(self):
        with _mock_generate(MOCK_CHECKLIST_RESPONSE):
            resp = client.post("/api/analyze/checklist", json={"text": LEGAL_TEXT})
        body = resp.json()
        assert len(body["verify_yourself"]) >= 1, "verify_yourself list must be non-empty for a complex document"

    def test_no_extra_top_level_keys(self):
        """Response must only contain ask_lawyer and verify_yourself at the top level."""
        with _mock_generate(MOCK_CHECKLIST_RESPONSE):
            resp = client.post("/api/analyze/checklist", json={"text": LEGAL_TEXT})
        body = resp.json()
        assert set(body.keys()) == {"ask_lawyer", "verify_yourself"}


# ===========================================================================
# List item type validation
# ===========================================================================

class TestChecklistListTypes:
    def test_ask_lawyer_items_are_strings(self):
        """Every item in ask_lawyer must be a non-empty string."""
        with _mock_generate(MOCK_CHECKLIST_RESPONSE):
            resp = client.post("/api/analyze/checklist", json={"text": LEGAL_TEXT})
        for item in resp.json()["ask_lawyer"]:
            assert isinstance(item, str) and item.strip(), (
                f"ask_lawyer item is not a non-empty string: {item!r}"
            )

    def test_verify_yourself_items_are_strings(self):
        """Every item in verify_yourself must be a non-empty string."""
        with _mock_generate(MOCK_CHECKLIST_RESPONSE):
            resp = client.post("/api/analyze/checklist", json={"text": LEGAL_TEXT})
        for item in resp.json()["verify_yourself"]:
            assert isinstance(item, str) and item.strip(), (
                f"verify_yourself item is not a non-empty string: {item!r}"
            )

    def test_ask_lawyer_count_matches_mock(self):
        with _mock_generate(MOCK_CHECKLIST_RESPONSE):
            resp = client.post("/api/analyze/checklist", json={"text": LEGAL_TEXT})
        assert len(resp.json()["ask_lawyer"]) == len(MOCK_CHECKLIST_RESPONSE["ask_lawyer"])

    def test_verify_yourself_count_matches_mock(self):
        with _mock_generate(MOCK_CHECKLIST_RESPONSE):
            resp = client.post("/api/analyze/checklist", json={"text": LEGAL_TEXT})
        assert len(resp.json()["verify_yourself"]) == len(MOCK_CHECKLIST_RESPONSE["verify_yourself"])

    def test_empty_lists_are_accepted(self):
        """A document with no actionable items may return empty lists — still a valid 200."""
        minimal_response = {"ask_lawyer": [], "verify_yourself": []}
        with _mock_generate(minimal_response):
            resp = client.post("/api/analyze/checklist", json={"text": LEGAL_TEXT})
        assert resp.status_code == 200
        body = resp.json()
        assert body["ask_lawyer"] == []
        assert body["verify_yourself"] == []


# ===========================================================================
# Error paths
# ===========================================================================

class TestChecklistEndpointErrors:
    def test_empty_text_returns_400(self):
        resp = client.post("/api/analyze/checklist", json={"text": "   "})
        assert resp.status_code == 400

    def test_empty_text_error_code(self):
        resp = client.post("/api/analyze/checklist", json={"text": "   "})
        body = resp.json()
        assert body["error"]["code"] == "EMPTY_TEXT"

    def test_empty_text_error_message_is_human_readable(self):
        resp = client.post("/api/analyze/checklist", json={"text": "   "})
        body = resp.json()
        assert body["error"]["message"], "error message must not be empty"

    def test_missing_text_field_returns_422(self):
        """Pydantic validation rejects a missing required field."""
        resp = client.post("/api/analyze/checklist", json={})
        assert resp.status_code == 422

    def test_gemini_failure_returns_502(self):
        from app.services.anthropic_client import AnthropicServiceError as GeminiServiceError

        with patch(
            "app.routers.checklist.generate_structured",
            side_effect=GeminiServiceError("AI down"),
        ):
            resp = client.post("/api/analyze/checklist", json={"text": LEGAL_TEXT})
        assert resp.status_code == 502

    def test_gemini_failure_error_code(self):
        from app.services.anthropic_client import AnthropicServiceError as GeminiServiceError

        with patch(
            "app.routers.checklist.generate_structured",
            side_effect=GeminiServiceError("AI down"),
        ):
            resp = client.post("/api/analyze/checklist", json={"text": LEGAL_TEXT})
        body = resp.json()
        assert body["error"]["code"] == "AI_SERVICE_ERROR"

    def test_unexpected_exception_returns_500(self):
        with patch(
            "app.routers.checklist.generate_structured",
            side_effect=RuntimeError("unexpected"),
        ):
            resp = client.post("/api/analyze/checklist", json={"text": LEGAL_TEXT})
        assert resp.status_code == 500

    def test_unexpected_exception_error_code(self):
        with patch(
            "app.routers.checklist.generate_structured",
            side_effect=RuntimeError("unexpected"),
        ):
            resp = client.post("/api/analyze/checklist", json={"text": LEGAL_TEXT})
        body = resp.json()
        assert body["error"]["code"] == "INTERNAL_ERROR"

    def test_unexpected_exception_does_not_leak_details(self):
        with patch(
            "app.routers.checklist.generate_structured",
            side_effect=RuntimeError("secret internal detail"),
        ):
            resp = client.post("/api/analyze/checklist", json={"text": LEGAL_TEXT})
        assert "secret internal detail" not in resp.text


# ===========================================================================
# Pydantic model validation
# ===========================================================================

class TestPydanticModels:
    def test_checklist_request_rejects_empty_string(self):
        from pydantic import ValidationError
        from app.models.schemas import ChecklistRequest

        with pytest.raises(ValidationError):
            ChecklistRequest(text="")

    def test_checklist_request_rejects_missing_text(self):
        from pydantic import ValidationError
        from app.models.schemas import ChecklistRequest

        with pytest.raises(ValidationError):
            ChecklistRequest()  # type: ignore[call-arg]

    def test_checklist_request_valid(self):
        from app.models.schemas import ChecklistRequest

        req = ChecklistRequest(text="Some document text")
        assert req.text == "Some document text"

    def test_checklist_response_valid_with_items(self):
        from app.models.schemas import ChecklistResponse

        resp = ChecklistResponse(
            ask_lawyer=["Ask a lawyer about clause 3.", "Clarify indemnification scope."],
            verify_yourself=["Confirm the payment amount.", "Check the start date."],
        )
        assert len(resp.ask_lawyer) == 2
        assert len(resp.verify_yourself) == 2

    def test_checklist_response_valid_with_empty_lists(self):
        from app.models.schemas import ChecklistResponse

        resp = ChecklistResponse(ask_lawyer=[], verify_yourself=[])
        assert resp.ask_lawyer == []
        assert resp.verify_yourself == []

    def test_checklist_response_requires_both_fields(self):
        from pydantic import ValidationError
        from app.models.schemas import ChecklistResponse

        with pytest.raises(ValidationError):
            ChecklistResponse(ask_lawyer=["Some question"])  # missing verify_yourself

    def test_checklist_response_requires_ask_lawyer(self):
        from pydantic import ValidationError
        from app.models.schemas import ChecklistResponse

        with pytest.raises(ValidationError):
            ChecklistResponse(verify_yourself=["Check the date"])  # missing ask_lawyer

    def test_checklist_response_ask_lawyer_is_list_of_strings(self):
        from app.models.schemas import ChecklistResponse

        resp = ChecklistResponse(
            ask_lawyer=["Question one", "Question two"],
            verify_yourself=[],
        )
        assert all(isinstance(item, str) for item in resp.ask_lawyer)

    def test_checklist_response_verify_yourself_is_list_of_strings(self):
        from app.models.schemas import ChecklistResponse

        resp = ChecklistResponse(
            ask_lawyer=[],
            verify_yourself=["Check name", "Verify date"],
        )
        assert all(isinstance(item, str) for item in resp.verify_yourself)


# ===========================================================================
# Prompt template tests
# ===========================================================================

class TestChecklistPrompt:
    def test_prompt_includes_ask_lawyer_instruction(self):
        from app.services.prompts import build_checklist_prompt

        prompt = build_checklist_prompt("sample document text")
        assert "ask_lawyer" in prompt.lower() or "lawyer" in prompt.lower(), (
            "build_checklist_prompt must instruct the model to produce ask_lawyer items"
        )

    def test_prompt_includes_verify_yourself_instruction(self):
        from app.services.prompts import build_checklist_prompt

        prompt = build_checklist_prompt("sample document text")
        assert "verify" in prompt.lower(), (
            "build_checklist_prompt must instruct the model to produce verify_yourself items"
        )

    def test_prompt_includes_legal_disclaimer(self):
        from app.services.prompts import build_checklist_prompt

        prompt = build_checklist_prompt("sample document text")
        assert "legal advice" in prompt.lower() or "legal information" in prompt.lower(), (
            "build_checklist_prompt must embed the shared legal disclaimer block"
        )

    def test_prompt_contains_document_text(self):
        from app.services.prompts import build_checklist_prompt

        doc = "UNIQUE_DOC_MARKER_12345"
        prompt = build_checklist_prompt(doc)
        assert doc in prompt, "build_checklist_prompt must embed the document text in the prompt"

    def test_checklist_schema_has_required_keys(self):
        from app.services.prompts import CHECKLIST_SCHEMA

        assert "ask_lawyer" in CHECKLIST_SCHEMA["properties"]
        assert "verify_yourself" in CHECKLIST_SCHEMA["properties"]
        assert "ask_lawyer" in CHECKLIST_SCHEMA["required"]
        assert "verify_yourself" in CHECKLIST_SCHEMA["required"]

    def test_checklist_schema_items_are_strings(self):
        from app.services.prompts import CHECKLIST_SCHEMA

        props = CHECKLIST_SCHEMA["properties"]
        assert props["ask_lawyer"]["type"] == "array"
        assert props["ask_lawyer"]["items"]["type"] == "string"
        assert props["verify_yourself"]["type"] == "array"
        assert props["verify_yourself"]["items"]["type"] == "string"
