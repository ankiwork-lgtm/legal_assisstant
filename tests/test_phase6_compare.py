"""Tests for Phase 6 — Feature: Document Comparison (FR-3).

Covers:
- POST /api/analyze/compare  (app/routers/compare.py)
- Pydantic models: CompareRequest, SharedTopic, CompareResponse
- Happy path: 200, all three top-level fields present, shared_topics items have
  all required sub-fields
- Optional labels: works with and without label_a / label_b
- Different document types: response still returns (doesn't error), graceful handling
  via why_it_matters note in shared_topics
- Error paths: empty doc_a → 400, empty doc_b → 400, Gemini failure → 502,
  unexpected → 500
- Pydantic model validation (direct unit tests)
- Prompt template tests

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
# Test fixtures
# ---------------------------------------------------------------------------

LEASE_TEXT = (
    "RESIDENTIAL LEASE AGREEMENT\n\n"
    "1. Parties. Landlord: John Smith. Tenant: Jane Doe.\n\n"
    "2. Premises. The leased property is located at 123 Main St, Springfield.\n\n"
    "3. Term. The lease commences on January 1, 2025 and ends on December 31, 2025.\n\n"
    "4. Rent. Tenant shall pay $1,500 per month, due on the 1st of each month.\n\n"
    "5. Security Deposit. Tenant shall deposit $3,000 as security, refundable within "
    "30 days of lease termination, less any deductions for damages.\n\n"
    "6. Pets. No pets are permitted without prior written consent from Landlord.\n\n"
    "7. Termination. Either party may terminate with 60 days written notice."
)

LEASE_V2_TEXT = (
    "RESIDENTIAL LEASE AGREEMENT (REVISED)\n\n"
    "1. Parties. Landlord: John Smith. Tenant: Jane Doe.\n\n"
    "2. Premises. The leased property is located at 123 Main St, Springfield.\n\n"
    "3. Term. The lease commences on February 1, 2025 and ends on January 31, 2026.\n\n"
    "4. Rent. Tenant shall pay $1,650 per month, due on the 1st of each month. "
    "Late payments incur a $50 fee after a 5-day grace period.\n\n"
    "5. Security Deposit. Tenant shall deposit $3,300 as security, refundable within "
    "21 days of lease termination.\n\n"
    "6. Pets. One cat or dog (under 25 lbs) is permitted with a $500 pet deposit.\n\n"
    "7. Termination. Either party may terminate with 30 days written notice."
)

LOAN_TEXT = (
    "LOAN AGREEMENT\n\n"
    "1. Parties. Lender: First National Bank. Borrower: Jane Doe.\n\n"
    "2. Principal. Lender agrees to loan $50,000 to Borrower.\n\n"
    "3. Interest Rate. The loan bears interest at 6.5% per annum.\n\n"
    "4. Repayment. Borrower shall repay the loan in 60 monthly installments of $977.\n\n"
    "5. Default. Failure to make two consecutive payments constitutes default, "
    "whereupon the full outstanding balance becomes immediately due.\n\n"
    "6. Collateral. The loan is secured by the Borrower's vehicle, VIN 123456789."
)

# Canonical mock Gemini response — two similar leases, valid shape
MOCK_COMPARE_RESPONSE = {
    "shared_topics": [
        {
            "topic": "Monthly Payment",
            "doc_a_position": "Tenant pays $1,500 per month.",
            "doc_b_position": "Tenant pays $1,650 per month, with a $50 late fee after 5 days.",
            "materially_different": True,
            "why_it_matters": (
                "The rent increased by $150/month (10%). The new late fee clause adds "
                "financial exposure if payments are delayed."
            ),
        },
        {
            "topic": "Security Deposit",
            "doc_a_position": "Deposit of $3,000, refunded within 30 days.",
            "doc_b_position": "Deposit of $3,300, refunded within 21 days.",
            "materially_different": True,
            "why_it_matters": (
                "The deposit amount increased by $300. The refund window shortened from "
                "30 to 21 days, which is actually more favourable for the tenant."
            ),
        },
        {
            "topic": "Pet Policy",
            "doc_a_position": "No pets without prior written consent.",
            "doc_b_position": "One pet under 25 lbs allowed with a $500 pet deposit.",
            "materially_different": True,
            "why_it_matters": (
                "V2 explicitly permits small pets, removing ambiguity. "
                "However, it adds a $500 non-refundable pet deposit."
            ),
        },
        {
            "topic": "Termination Notice",
            "doc_a_position": "60 days written notice required.",
            "doc_b_position": "30 days written notice required.",
            "materially_different": True,
            "why_it_matters": (
                "The notice period was halved. This reduces flexibility for long-term planning."
            ),
        },
    ],
    "only_in_a": [],
    "only_in_b": ["Late payment fee clause ($50 after 5-day grace period)"],
}

# Mock response for different document types (lease vs loan)
MOCK_COMPARE_DIFFERENT_TYPES = {
    "shared_topics": [
        {
            "topic": "Parties",
            "doc_a_position": "Landlord: John Smith, Tenant: Jane Doe.",
            "doc_b_position": "Lender: First National Bank, Borrower: Jane Doe.",
            "materially_different": True,
            "why_it_matters": (
                "NOTE: These documents are of structurally different types (residential lease "
                "vs. loan agreement). A direct comparison is limited. Both documents identify "
                "Jane Doe as a party in different roles (tenant vs. borrower)."
            ),
        },
        {
            "topic": "Financial Obligation",
            "doc_a_position": "$1,500 per month in rent.",
            "doc_b_position": "$977 per month in loan repayment over 60 months.",
            "materially_different": True,
            "why_it_matters": (
                "Both documents impose monthly financial obligations on Jane Doe, but the "
                "nature differs significantly: rent is for occupancy while the loan repayment "
                "builds equity in a financed asset."
            ),
        },
    ],
    "only_in_a": [
        "Security deposit requirement",
        "Pet policy",
        "Premises address and occupancy rights",
        "60-day termination notice",
    ],
    "only_in_b": [
        "Principal loan amount ($50,000)",
        "Interest rate (6.5% per annum)",
        "Default clause",
        "Collateral (vehicle)",
    ],
}


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _mock_generate(payload: dict):
    """Patch generate_structured in the compare router to return *payload*."""
    return patch(
        "app.routers.compare.generate_structured",
        return_value=payload,
    )


# ===========================================================================
# Happy-path: structure and fields
# ===========================================================================

class TestCompareEndpointHappyPath:
    def test_returns_200(self):
        with _mock_generate(MOCK_COMPARE_RESPONSE):
            resp = client.post(
                "/api/analyze/compare",
                json={"doc_a": LEASE_TEXT, "doc_b": LEASE_V2_TEXT},
            )
        assert resp.status_code == 200

    def test_response_has_shared_topics(self):
        with _mock_generate(MOCK_COMPARE_RESPONSE):
            resp = client.post(
                "/api/analyze/compare",
                json={"doc_a": LEASE_TEXT, "doc_b": LEASE_V2_TEXT},
            )
        assert "shared_topics" in resp.json()

    def test_response_has_only_in_a(self):
        with _mock_generate(MOCK_COMPARE_RESPONSE):
            resp = client.post(
                "/api/analyze/compare",
                json={"doc_a": LEASE_TEXT, "doc_b": LEASE_V2_TEXT},
            )
        assert "only_in_a" in resp.json()

    def test_response_has_only_in_b(self):
        with _mock_generate(MOCK_COMPARE_RESPONSE):
            resp = client.post(
                "/api/analyze/compare",
                json={"doc_a": LEASE_TEXT, "doc_b": LEASE_V2_TEXT},
            )
        assert "only_in_b" in resp.json()

    def test_shared_topics_is_list(self):
        with _mock_generate(MOCK_COMPARE_RESPONSE):
            resp = client.post(
                "/api/analyze/compare",
                json={"doc_a": LEASE_TEXT, "doc_b": LEASE_V2_TEXT},
            )
        assert isinstance(resp.json()["shared_topics"], list)

    def test_only_in_a_is_list(self):
        with _mock_generate(MOCK_COMPARE_RESPONSE):
            resp = client.post(
                "/api/analyze/compare",
                json={"doc_a": LEASE_TEXT, "doc_b": LEASE_V2_TEXT},
            )
        assert isinstance(resp.json()["only_in_a"], list)

    def test_only_in_b_is_list(self):
        with _mock_generate(MOCK_COMPARE_RESPONSE):
            resp = client.post(
                "/api/analyze/compare",
                json={"doc_a": LEASE_TEXT, "doc_b": LEASE_V2_TEXT},
            )
        assert isinstance(resp.json()["only_in_b"], list)

    def test_shared_topics_items_have_required_subfields(self):
        """Every item in shared_topics must have all five required sub-fields."""
        with _mock_generate(MOCK_COMPARE_RESPONSE):
            resp = client.post(
                "/api/analyze/compare",
                json={"doc_a": LEASE_TEXT, "doc_b": LEASE_V2_TEXT},
            )
        required = {"topic", "doc_a_position", "doc_b_position", "materially_different", "why_it_matters"}
        for i, item in enumerate(resp.json()["shared_topics"]):
            assert required <= set(item.keys()), (
                f"shared_topics[{i}] is missing fields: {required - set(item.keys())}"
            )

    def test_shared_topics_materially_different_is_bool(self):
        with _mock_generate(MOCK_COMPARE_RESPONSE):
            resp = client.post(
                "/api/analyze/compare",
                json={"doc_a": LEASE_TEXT, "doc_b": LEASE_V2_TEXT},
            )
        for item in resp.json()["shared_topics"]:
            assert isinstance(item["materially_different"], bool), (
                f"materially_different must be a bool, got {type(item['materially_different'])}"
            )

    def test_response_only_has_expected_top_level_keys(self):
        with _mock_generate(MOCK_COMPARE_RESPONSE):
            resp = client.post(
                "/api/analyze/compare",
                json={"doc_a": LEASE_TEXT, "doc_b": LEASE_V2_TEXT},
            )
        assert set(resp.json().keys()) == {"shared_topics", "only_in_a", "only_in_b"}

    def test_only_in_b_items_are_strings(self):
        with _mock_generate(MOCK_COMPARE_RESPONSE):
            resp = client.post(
                "/api/analyze/compare",
                json={"doc_a": LEASE_TEXT, "doc_b": LEASE_V2_TEXT},
            )
        for item in resp.json()["only_in_b"]:
            assert isinstance(item, str) and item.strip()


# ===========================================================================
# Optional labels
# ===========================================================================

class TestCompareOptionalLabels:
    def test_request_without_labels_uses_defaults(self):
        """Omitting label_a and label_b should succeed and use default labels."""
        with _mock_generate(MOCK_COMPARE_RESPONSE):
            resp = client.post(
                "/api/analyze/compare",
                json={"doc_a": LEASE_TEXT, "doc_b": LEASE_V2_TEXT},
            )
        assert resp.status_code == 200

    def test_request_with_both_labels(self):
        """Providing both custom labels should succeed."""
        with _mock_generate(MOCK_COMPARE_RESPONSE):
            resp = client.post(
                "/api/analyze/compare",
                json={
                    "doc_a": LEASE_TEXT,
                    "doc_b": LEASE_V2_TEXT,
                    "label_a": "Original Lease",
                    "label_b": "Revised Lease",
                },
            )
        assert resp.status_code == 200

    def test_request_with_label_a_only(self):
        """Providing only label_a should succeed (label_b falls back to default)."""
        with _mock_generate(MOCK_COMPARE_RESPONSE):
            resp = client.post(
                "/api/analyze/compare",
                json={
                    "doc_a": LEASE_TEXT,
                    "doc_b": LEASE_V2_TEXT,
                    "label_a": "My Lease",
                },
            )
        assert resp.status_code == 200

    def test_request_with_label_b_only(self):
        """Providing only label_b should succeed (label_a falls back to default)."""
        with _mock_generate(MOCK_COMPARE_RESPONSE):
            resp = client.post(
                "/api/analyze/compare",
                json={
                    "doc_a": LEASE_TEXT,
                    "doc_b": LEASE_V2_TEXT,
                    "label_b": "Amended Version",
                },
            )
        assert resp.status_code == 200

    def test_labels_passed_to_prompt(self):
        """Custom labels must appear in the generated prompt."""
        from app.services.prompts import build_compare_prompt

        prompt = build_compare_prompt(
            doc_a="text a",
            doc_b="text b",
            label_a="Employment Contract",
            label_b="Amendment",
        )
        assert "Employment Contract" in prompt
        assert "Amendment" in prompt

    def test_default_labels_in_prompt(self):
        """Default labels 'Document A' and 'Document B' appear when no labels given."""
        from app.services.prompts import build_compare_prompt

        prompt = build_compare_prompt(doc_a="text a", doc_b="text b")
        assert "Document A" in prompt
        assert "Document B" in prompt


# ===========================================================================
# Different document types — graceful handling (task 6.3)
# ===========================================================================

class TestCompareDifferentDocumentTypes:
    def test_different_types_returns_200(self):
        """Even when comparing fundamentally different document types, a 200 is returned."""
        with _mock_generate(MOCK_COMPARE_DIFFERENT_TYPES):
            resp = client.post(
                "/api/analyze/compare",
                json={"doc_a": LEASE_TEXT, "doc_b": LOAN_TEXT},
            )
        assert resp.status_code == 200

    def test_different_types_shared_topics_present(self):
        """Best-effort comparison still populates shared_topics."""
        with _mock_generate(MOCK_COMPARE_DIFFERENT_TYPES):
            resp = client.post(
                "/api/analyze/compare",
                json={"doc_a": LEASE_TEXT, "doc_b": LOAN_TEXT},
            )
        assert len(resp.json()["shared_topics"]) >= 1

    def test_different_types_only_in_a_present(self):
        """Different-type comparison populates only_in_a."""
        with _mock_generate(MOCK_COMPARE_DIFFERENT_TYPES):
            resp = client.post(
                "/api/analyze/compare",
                json={"doc_a": LEASE_TEXT, "doc_b": LOAN_TEXT},
            )
        assert len(resp.json()["only_in_a"]) >= 1

    def test_different_types_only_in_b_present(self):
        """Different-type comparison populates only_in_b."""
        with _mock_generate(MOCK_COMPARE_DIFFERENT_TYPES):
            resp = client.post(
                "/api/analyze/compare",
                json={"doc_a": LEASE_TEXT, "doc_b": LOAN_TEXT},
            )
        assert len(resp.json()["only_in_b"]) >= 1

    def test_prompt_instructs_best_effort_for_different_types(self):
        """build_compare_prompt must explicitly instruct the model to attempt
        best-effort comparison when document types differ."""
        from app.services.prompts import build_compare_prompt

        prompt = build_compare_prompt(doc_a="text a", doc_b="text b")
        assert "best-effort" in prompt or "best effort" in prompt.lower(), (
            "Prompt must instruct the model to perform best-effort comparison "
            "for structurally different document types."
        )

    def test_prompt_instructs_note_on_why_it_matters(self):
        """build_compare_prompt must mention noting structural difference."""
        from app.services.prompts import build_compare_prompt

        prompt = build_compare_prompt(doc_a="text a", doc_b="text b")
        assert "why_it_matters" in prompt or "note" in prompt.lower(), (
            "Prompt must instruct the model to note structural differences."
        )


# ===========================================================================
# Error paths
# ===========================================================================

class TestCompareEndpointErrors:
    def test_empty_doc_a_returns_400(self):
        resp = client.post(
            "/api/analyze/compare",
            json={"doc_a": "   ", "doc_b": LEASE_V2_TEXT},
        )
        assert resp.status_code == 400

    def test_empty_doc_a_error_code(self):
        resp = client.post(
            "/api/analyze/compare",
            json={"doc_a": "   ", "doc_b": LEASE_V2_TEXT},
        )
        assert resp.json()["error"]["code"] == "EMPTY_DOC_A"

    def test_empty_doc_b_returns_400(self):
        resp = client.post(
            "/api/analyze/compare",
            json={"doc_a": LEASE_TEXT, "doc_b": "   "},
        )
        assert resp.status_code == 400

    def test_empty_doc_b_error_code(self):
        resp = client.post(
            "/api/analyze/compare",
            json={"doc_a": LEASE_TEXT, "doc_b": "   "},
        )
        assert resp.json()["error"]["code"] == "EMPTY_DOC_B"

    def test_missing_doc_a_returns_422(self):
        """Pydantic validation rejects a missing required field."""
        resp = client.post(
            "/api/analyze/compare",
            json={"doc_b": LEASE_V2_TEXT},
        )
        assert resp.status_code == 422

    def test_missing_doc_b_returns_422(self):
        resp = client.post(
            "/api/analyze/compare",
            json={"doc_a": LEASE_TEXT},
        )
        assert resp.status_code == 422

    def test_gemini_failure_returns_502(self):
        from app.services.anthropic_client import AnthropicServiceError as GeminiServiceError

        with patch(
            "app.routers.compare.generate_structured",
            side_effect=GeminiServiceError("AI down"),
        ):
            resp = client.post(
                "/api/analyze/compare",
                json={"doc_a": LEASE_TEXT, "doc_b": LEASE_V2_TEXT},
            )
        assert resp.status_code == 502

    def test_gemini_failure_error_code(self):
        from app.services.anthropic_client import AnthropicServiceError as GeminiServiceError

        with patch(
            "app.routers.compare.generate_structured",
            side_effect=GeminiServiceError("AI down"),
        ):
            resp = client.post(
                "/api/analyze/compare",
                json={"doc_a": LEASE_TEXT, "doc_b": LEASE_V2_TEXT},
            )
        assert resp.json()["error"]["code"] == "AI_SERVICE_ERROR"

    def test_unexpected_exception_returns_500(self):
        with patch(
            "app.routers.compare.generate_structured",
            side_effect=RuntimeError("unexpected"),
        ):
            resp = client.post(
                "/api/analyze/compare",
                json={"doc_a": LEASE_TEXT, "doc_b": LEASE_V2_TEXT},
            )
        assert resp.status_code == 500

    def test_unexpected_exception_error_code(self):
        with patch(
            "app.routers.compare.generate_structured",
            side_effect=RuntimeError("unexpected"),
        ):
            resp = client.post(
                "/api/analyze/compare",
                json={"doc_a": LEASE_TEXT, "doc_b": LEASE_V2_TEXT},
            )
        assert resp.json()["error"]["code"] == "INTERNAL_ERROR"

    def test_unexpected_exception_does_not_leak_details(self):
        with patch(
            "app.routers.compare.generate_structured",
            side_effect=RuntimeError("secret internal detail"),
        ):
            resp = client.post(
                "/api/analyze/compare",
                json={"doc_a": LEASE_TEXT, "doc_b": LEASE_V2_TEXT},
            )
        assert "secret internal detail" not in resp.text

    def test_error_body_has_error_key(self):
        resp = client.post(
            "/api/analyze/compare",
            json={"doc_a": "   ", "doc_b": LEASE_V2_TEXT},
        )
        assert "error" in resp.json()

    def test_error_body_has_message(self):
        resp = client.post(
            "/api/analyze/compare",
            json={"doc_a": "   ", "doc_b": LEASE_V2_TEXT},
        )
        assert resp.json()["error"]["message"]


# ===========================================================================
# Pydantic model validation
# ===========================================================================

class TestPydanticModels:
    def test_compare_request_rejects_empty_doc_a(self):
        from pydantic import ValidationError
        from app.models.schemas import CompareRequest

        with pytest.raises(ValidationError):
            CompareRequest(doc_a="", doc_b="some text")

    def test_compare_request_rejects_empty_doc_b(self):
        from pydantic import ValidationError
        from app.models.schemas import CompareRequest

        with pytest.raises(ValidationError):
            CompareRequest(doc_a="some text", doc_b="")

    def test_compare_request_valid_without_labels(self):
        from app.models.schemas import CompareRequest

        req = CompareRequest(doc_a="text a", doc_b="text b")
        assert req.doc_a == "text a"
        assert req.doc_b == "text b"
        assert req.label_a == "Document A"
        assert req.label_b == "Document B"

    def test_compare_request_valid_with_labels(self):
        from app.models.schemas import CompareRequest

        req = CompareRequest(
            doc_a="text a", doc_b="text b",
            label_a="Lease", label_b="Amended Lease",
        )
        assert req.label_a == "Lease"
        assert req.label_b == "Amended Lease"

    def test_shared_topic_requires_all_fields(self):
        from pydantic import ValidationError
        from app.models.schemas import SharedTopic

        with pytest.raises(ValidationError):
            SharedTopic(
                topic="Payment",
                doc_a_position="$1,000/month",
                # missing doc_b_position, materially_different, why_it_matters
            )

    def test_shared_topic_valid(self):
        from app.models.schemas import SharedTopic

        st = SharedTopic(
            topic="Payment",
            doc_a_position="$1,000/month",
            doc_b_position="$1,200/month",
            materially_different=True,
            why_it_matters="The rent increased by 20%.",
        )
        assert st.materially_different is True

    def test_shared_topic_materially_different_must_be_bool(self):
        from pydantic import ValidationError
        from app.models.schemas import SharedTopic

        # Pydantic v2 coerces "true" strings to bool, but passing a non-coercible
        # value like a list should fail.
        with pytest.raises((ValidationError, Exception)):
            SharedTopic(
                topic="X",
                doc_a_position="a",
                doc_b_position="b",
                materially_different=[],  # type: ignore[arg-type]
                why_it_matters="n/a",
            )

    def test_compare_response_valid(self):
        from app.models.schemas import CompareResponse, SharedTopic

        resp = CompareResponse(
            shared_topics=[
                SharedTopic(
                    topic="Rent",
                    doc_a_position="$1,000",
                    doc_b_position="$1,200",
                    materially_different=True,
                    why_it_matters="20% increase.",
                )
            ],
            only_in_a=["Pet clause"],
            only_in_b=["Late fee clause"],
        )
        assert len(resp.shared_topics) == 1
        assert resp.only_in_a == ["Pet clause"]
        assert resp.only_in_b == ["Late fee clause"]

    def test_compare_response_allows_empty_lists(self):
        from app.models.schemas import CompareResponse

        resp = CompareResponse(shared_topics=[], only_in_a=[], only_in_b=[])
        assert resp.shared_topics == []
        assert resp.only_in_a == []
        assert resp.only_in_b == []

    def test_compare_response_requires_all_three_fields(self):
        from pydantic import ValidationError
        from app.models.schemas import CompareResponse

        with pytest.raises(ValidationError):
            CompareResponse(shared_topics=[], only_in_a=[])  # missing only_in_b


# ===========================================================================
# Prompt template tests
# ===========================================================================

class TestComparePrompt:
    def test_prompt_includes_doc_a_text(self):
        from app.services.prompts import build_compare_prompt

        prompt = build_compare_prompt(doc_a="UNIQUE_MARKER_DOC_A", doc_b="other text")
        assert "UNIQUE_MARKER_DOC_A" in prompt

    def test_prompt_includes_doc_b_text(self):
        from app.services.prompts import build_compare_prompt

        prompt = build_compare_prompt(doc_a="first doc", doc_b="UNIQUE_MARKER_DOC_B")
        assert "UNIQUE_MARKER_DOC_B" in prompt

    def test_prompt_includes_legal_disclaimer(self):
        from app.services.prompts import build_compare_prompt

        prompt = build_compare_prompt(doc_a="a", doc_b="b")
        assert "legal advice" in prompt.lower() or "legal information" in prompt.lower()

    def test_compare_schema_has_all_required_top_level_keys(self):
        from app.services.prompts import COMPARE_SCHEMA

        assert "shared_topics" in COMPARE_SCHEMA["properties"]
        assert "only_in_a" in COMPARE_SCHEMA["properties"]
        assert "only_in_b" in COMPARE_SCHEMA["properties"]
        assert set(COMPARE_SCHEMA["required"]) == {"shared_topics", "only_in_a", "only_in_b"}

    def test_compare_schema_shared_topic_subfields(self):
        from app.services.prompts import COMPARE_SCHEMA

        shared_item_props = COMPARE_SCHEMA["properties"]["shared_topics"]["items"]["properties"]
        expected = {"topic", "doc_a_position", "doc_b_position", "materially_different", "why_it_matters"}
        assert expected <= set(shared_item_props.keys())

    def test_compare_schema_shared_topic_required_subfields(self):
        from app.services.prompts import COMPARE_SCHEMA

        required_sub = set(
            COMPARE_SCHEMA["properties"]["shared_topics"]["items"]["required"]
        )
        expected = {"topic", "doc_a_position", "doc_b_position", "materially_different", "why_it_matters"}
        assert expected == required_sub

    def test_compare_schema_only_in_a_is_string_array(self):
        from app.services.prompts import COMPARE_SCHEMA

        props = COMPARE_SCHEMA["properties"]
        assert props["only_in_a"]["type"] == "array"
        assert props["only_in_a"]["items"]["type"] == "string"

    def test_compare_schema_only_in_b_is_string_array(self):
        from app.services.prompts import COMPARE_SCHEMA

        props = COMPARE_SCHEMA["properties"]
        assert props["only_in_b"]["type"] == "array"
        assert props["only_in_b"]["items"]["type"] == "string"
