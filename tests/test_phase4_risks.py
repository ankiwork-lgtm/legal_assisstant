"""Tests for Phase 4 — Feature: Risk & Clause Highlighting (FR-5).

Covers:
- POST /api/analyze/risks  (app/routers/risks.py)
- Pydantic models: RisksRequest, RiskItem, RiskCategory, RisksResponse, Severity
- Hedging language: explanations must contain qualifying phrases, never definitive verdicts
- Severity enum: all items must have a value within {high, medium, low, info}
- Error paths: empty text → 400, Gemini failure → 502, unexpected error → 500
- Categories list is non-empty when the document contains risks

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
    "EMPLOYMENT AGREEMENT\n\n"
    "1. Compensation. Employee shall receive $120,000 per annum payable bi-weekly. "
    "A performance bonus of up to 20% of base salary is at the sole discretion of Employer.\n\n"
    "2. Non-Compete. For 24 months after termination, Employee shall not engage in any "
    "business that competes with Employer within a 100-mile radius.\n\n"
    "3. Intellectual Property. All work product, inventions, and developments created "
    "during employment are the exclusive property of Employer, including work done outside "
    "normal business hours.\n\n"
    "4. Termination. Employer may terminate this Agreement at will with or without cause "
    "and without notice. Employee must provide 90 days written notice of resignation.\n\n"
    "5. Auto-Renewal. This Agreement renews automatically for successive one-year terms "
    "unless either party provides 60 days written notice before each anniversary date.\n\n"
    "6. Indemnification. Employee shall indemnify and hold harmless Employer from any "
    "claims, damages, or expenses arising from Employee's gross negligence or wilful misconduct."
)

# Canonical mock Gemini response — valid shape with hedging explanations
MOCK_RISKS_RESPONSE = {
    "categories": [
        {
            "category": "Termination",
            "items": [
                {
                    "clause_ref": "Section 4",
                    "severity": "high",
                    "explanation": (
                        "This clause may be worth reviewing because the employer can "
                        "terminate at will without notice, while you must give 90 days."
                    ),
                },
            ],
        },
        {
            "category": "Obligations",
            "items": [
                {
                    "clause_ref": "Section 2",
                    "severity": "high",
                    "explanation": (
                        "You may want to consider whether the 24-month non-compete and "
                        "100-mile radius restriction are acceptable for your situation."
                    ),
                },
                {
                    "clause_ref": "Section 3",
                    "severity": "medium",
                    "explanation": (
                        "This clause may be worth reviewing because it assigns IP rights "
                        "even for work done outside normal business hours."
                    ),
                },
            ],
        },
        {
            "category": "Auto-Renewal",
            "items": [
                {
                    "clause_ref": "Section 5",
                    "severity": "low",
                    "explanation": (
                        "Consider setting a reminder before the anniversary date — "
                        "the agreement may renew automatically if notice is not given."
                    ),
                },
            ],
        },
        {
            "category": "Indemnification",
            "items": [
                {
                    "clause_ref": "Section 6",
                    "severity": "info",
                    "explanation": (
                        "This indemnification clause is standard; it may be worth confirming "
                        "what 'gross negligence' means in your jurisdiction."
                    ),
                },
            ],
        },
    ]
}

VALID_SEVERITIES = {"high", "medium", "low", "info"}

# Hedging phrases the prompt instructs the model to use (FR-5 / task 4.3)
HEDGING_PHRASES = [
    "worth reviewing",
    "may be worth",
    "consider",
    "may ",
    "might ",
    "could ",
    "it is advisable",
    "you may want",
    "we recommend consulting",
]

# Definitive-verdict phrases that must NOT appear (FR-8 / task 4.3)
FORBIDDEN_VERDICTS = [
    "you will lose",
    "you will win",
    "this is illegal",
    "this is enforceable",
    "this is unenforceable",
    "you must sign",
    "do not sign",
    "you should sign",
    "i advise you",
    "my legal advice",
]


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _mock_generate(payload: dict):
    """Patch generate_structured to return *payload* without calling Gemini."""
    return patch(
        "app.routers.risks.generate_structured",
        return_value=payload,
    )


# ===========================================================================
# Happy-path: structure and fields
# ===========================================================================

class TestRisksEndpointHappyPath:
    def test_returns_200(self):
        with _mock_generate(MOCK_RISKS_RESPONSE):
            resp = client.post("/api/analyze/risks", json={"text": LEGAL_TEXT})
        assert resp.status_code == 200

    def test_response_has_categories_list(self):
        with _mock_generate(MOCK_RISKS_RESPONSE):
            resp = client.post("/api/analyze/risks", json={"text": LEGAL_TEXT})
        body = resp.json()
        assert "categories" in body
        assert isinstance(body["categories"], list)

    def test_categories_non_empty(self):
        with _mock_generate(MOCK_RISKS_RESPONSE):
            resp = client.post("/api/analyze/risks", json={"text": LEGAL_TEXT})
        body = resp.json()
        assert len(body["categories"]) >= 1, "categories list must be non-empty for a risk-laden document"

    def test_each_category_has_required_fields(self):
        with _mock_generate(MOCK_RISKS_RESPONSE):
            resp = client.post("/api/analyze/risks", json={"text": LEGAL_TEXT})
        for cat in resp.json()["categories"]:
            assert "category" in cat, "category object missing 'category' field"
            assert "items" in cat, "category object missing 'items' field"

    def test_each_category_name_is_non_empty_string(self):
        with _mock_generate(MOCK_RISKS_RESPONSE):
            resp = client.post("/api/analyze/risks", json={"text": LEGAL_TEXT})
        for cat in resp.json()["categories"]:
            assert isinstance(cat["category"], str) and cat["category"].strip()

    def test_each_item_has_required_fields(self):
        with _mock_generate(MOCK_RISKS_RESPONSE):
            resp = client.post("/api/analyze/risks", json={"text": LEGAL_TEXT})
        for cat in resp.json()["categories"]:
            for item in cat["items"]:
                assert "clause_ref" in item, f"item missing 'clause_ref': {item}"
                assert "severity" in item, f"item missing 'severity': {item}"
                assert "explanation" in item, f"item missing 'explanation': {item}"

    def test_clause_ref_is_non_empty_string(self):
        with _mock_generate(MOCK_RISKS_RESPONSE):
            resp = client.post("/api/analyze/risks", json={"text": LEGAL_TEXT})
        for cat in resp.json()["categories"]:
            for item in cat["items"]:
                assert isinstance(item["clause_ref"], str) and item["clause_ref"].strip()

    def test_explanation_is_non_empty_string(self):
        with _mock_generate(MOCK_RISKS_RESPONSE):
            resp = client.post("/api/analyze/risks", json={"text": LEGAL_TEXT})
        for cat in resp.json()["categories"]:
            for item in cat["items"]:
                assert isinstance(item["explanation"], str) and item["explanation"].strip()


# ===========================================================================
# Task 4.3 — Severity enum validation
# ===========================================================================

class TestSeverityEnum:
    def test_all_severity_values_within_enum(self):
        """Every item's severity must be one of: high, medium, low, info."""
        with _mock_generate(MOCK_RISKS_RESPONSE):
            resp = client.post("/api/analyze/risks", json={"text": LEGAL_TEXT})
        for cat in resp.json()["categories"]:
            for item in cat["items"]:
                assert item["severity"] in VALID_SEVERITIES, (
                    f"Unexpected severity value '{item['severity']}' in item {item}"
                )

    def test_high_severity_items_present(self):
        """Mock response contains at least one 'high' severity item."""
        with _mock_generate(MOCK_RISKS_RESPONSE):
            resp = client.post("/api/analyze/risks", json={"text": LEGAL_TEXT})
        severities = [
            item["severity"]
            for cat in resp.json()["categories"]
            for item in cat["items"]
        ]
        assert "high" in severities

    def test_all_four_severity_levels_represented(self):
        """Mock covers all four enum values — confirms the enum is complete."""
        with _mock_generate(MOCK_RISKS_RESPONSE):
            resp = client.post("/api/analyze/risks", json={"text": LEGAL_TEXT})
        severities = {
            item["severity"]
            for cat in resp.json()["categories"]
            for item in cat["items"]
        }
        assert severities == VALID_SEVERITIES, (
            f"Expected all four severity levels; got {severities}"
        )

    def test_pydantic_rejects_invalid_severity(self):
        """Pydantic must reject an out-of-enum severity value at the model level."""
        from pydantic import ValidationError
        from app.models.schemas import RiskItem

        with pytest.raises(ValidationError):
            RiskItem(clause_ref="§1", severity="critical", explanation="Some explanation")


# ===========================================================================
# Task 4.3 — Hedging language (FR-8: no definitive legal verdicts)
# ===========================================================================

class TestHedgingLanguage:
    """Every explanation must contain qualifying, hedging language and must NOT
    contain definitive legal verdicts.  This operationalises FR-8 and the
    prompt instruction that forces 'may be worth reviewing because...' phrasing.
    """

    def _all_explanations(self) -> list[str]:
        with _mock_generate(MOCK_RISKS_RESPONSE):
            resp = client.post("/api/analyze/risks", json={"text": LEGAL_TEXT})
        return [
            item["explanation"]
            for cat in resp.json()["categories"]
            for item in cat["items"]
        ]

    def test_each_explanation_contains_hedging_phrase(self):
        """Every explanation must contain at least one recognised hedging phrase."""
        for explanation in self._all_explanations():
            lower = explanation.lower()
            found = any(phrase in lower for phrase in HEDGING_PHRASES)
            assert found, (
                f"Explanation lacks hedging language: '{explanation}'\n"
                f"Expected at least one of: {HEDGING_PHRASES}"
            )

    def test_no_explanation_contains_definitive_verdict(self):
        """No explanation may contain a definitive legal verdict phrase."""
        for explanation in self._all_explanations():
            lower = explanation.lower()
            for verdict in FORBIDDEN_VERDICTS:
                assert verdict not in lower, (
                    f"Explanation contains forbidden definitive verdict '{verdict}': "
                    f"'{explanation}'"
                )

    def test_explanation_does_not_use_first_person_advice(self):
        """'I advise' or 'my advice' should never appear in explanations."""
        for explanation in self._all_explanations():
            lower = explanation.lower()
            assert "i advise" not in lower, (
                f"Explanation uses first-person legal advice: '{explanation}'"
            )
            assert "my advice" not in lower, (
                f"Explanation uses first-person legal advice: '{explanation}'"
            )

    def test_prompt_instructs_hedging_phrasing(self):
        """build_risks_prompt must embed the hedging instruction in the output prompt."""
        from app.services.prompts import build_risks_prompt

        prompt = build_risks_prompt("sample document text")
        assert "worth reviewing" in prompt.lower(), (
            "build_risks_prompt must instruct the model to use 'worth reviewing' phrasing"
        )

    def test_prompt_includes_legal_disclaimer(self):
        """build_risks_prompt must include the shared legal-information disclaimer."""
        from app.services.prompts import build_risks_prompt

        prompt = build_risks_prompt("sample document text")
        assert "legal advice" in prompt.lower() or "legal information" in prompt.lower(), (
            "build_risks_prompt must embed the legal disclaimer block"
        )

    def test_prompt_forbids_definitive_verdict_instruction(self):
        """Prompt must tell model NOT to issue definitive legal conclusions."""
        from app.services.prompts import build_risks_prompt

        prompt = build_risks_prompt("sample document text")
        assert "not" in prompt.lower() and (
            "definitive" in prompt.lower() or "verdict" in prompt.lower()
            or "definitive legal conclusion" in prompt.lower()
        ), (
            "build_risks_prompt must instruct model to avoid definitive legal conclusions"
        )


# ===========================================================================
# Error paths
# ===========================================================================

class TestRisksEndpointErrors:
    def test_empty_text_returns_400(self):
        resp = client.post("/api/analyze/risks", json={"text": "   "})
        assert resp.status_code == 400

    def test_empty_text_error_code(self):
        resp = client.post("/api/analyze/risks", json={"text": "   "})
        body = resp.json()
        assert body["error"]["code"] == "EMPTY_TEXT"

    def test_missing_text_field_returns_422(self):
        """Pydantic validation rejects a missing required field."""
        resp = client.post("/api/analyze/risks", json={})
        assert resp.status_code == 422

    def test_gemini_failure_returns_502(self):
        from app.services.anthropic_client import AnthropicServiceError as GeminiServiceError

        with patch(
            "app.routers.risks.generate_structured",
            side_effect=GeminiServiceError("AI down"),
        ):
            resp = client.post("/api/analyze/risks", json={"text": LEGAL_TEXT})
        assert resp.status_code == 502

    def test_gemini_failure_error_code(self):
        from app.services.anthropic_client import AnthropicServiceError as GeminiServiceError

        with patch(
            "app.routers.risks.generate_structured",
            side_effect=GeminiServiceError("AI down"),
        ):
            resp = client.post("/api/analyze/risks", json={"text": LEGAL_TEXT})
        body = resp.json()
        assert body["error"]["code"] == "AI_SERVICE_ERROR"

    def test_unexpected_exception_returns_500(self):
        with patch(
            "app.routers.risks.generate_structured",
            side_effect=RuntimeError("unexpected"),
        ):
            resp = client.post("/api/analyze/risks", json={"text": LEGAL_TEXT})
        assert resp.status_code == 500

    def test_unexpected_exception_does_not_leak_details(self):
        with patch(
            "app.routers.risks.generate_structured",
            side_effect=RuntimeError("secret internal detail"),
        ):
            resp = client.post("/api/analyze/risks", json={"text": LEGAL_TEXT})
        assert "secret internal detail" not in resp.text


# ===========================================================================
# Pydantic model validation
# ===========================================================================

class TestPydanticModels:
    def test_risks_request_rejects_empty_string(self):
        from pydantic import ValidationError
        from app.models.schemas import RisksRequest

        with pytest.raises(ValidationError):
            RisksRequest(text="")

    def test_risk_item_valid(self):
        from app.models.schemas import RiskItem, Severity

        item = RiskItem(
            clause_ref="Section 3",
            severity=Severity.high,
            explanation="This clause may be worth reviewing because it assigns IP broadly.",
        )
        assert item.severity == Severity.high
        assert item.severity.value == "high"

    def test_risk_category_valid(self):
        from app.models.schemas import RiskCategory, RiskItem, Severity

        cat = RiskCategory(
            category="Intellectual Property",
            items=[
                RiskItem(
                    clause_ref="§3",
                    severity=Severity.medium,
                    explanation="May be worth considering for after-hours work.",
                )
            ],
        )
        assert cat.category == "Intellectual Property"
        assert len(cat.items) == 1

    def test_risks_response_valid(self):
        from app.models.schemas import RisksResponse, RiskCategory, RiskItem, Severity

        resp = RisksResponse(
            categories=[
                RiskCategory(
                    category="Termination",
                    items=[
                        RiskItem(
                            clause_ref="§4",
                            severity=Severity.high,
                            explanation=(
                                "This clause may be worth reviewing because "
                                "termination is at-will with no notice to employee."
                            ),
                        )
                    ],
                )
            ]
        )
        assert len(resp.categories) == 1
        assert resp.categories[0].items[0].severity == Severity.high

    def test_severity_enum_values(self):
        from app.models.schemas import Severity

        assert set(s.value for s in Severity) == {"high", "medium", "low", "info"}

    def test_risk_item_requires_all_three_fields(self):
        from pydantic import ValidationError
        from app.models.schemas import RiskItem

        with pytest.raises(ValidationError):
            RiskItem(clause_ref="§1", severity="high")  # missing explanation

    def test_risk_category_requires_both_fields(self):
        from pydantic import ValidationError
        from app.models.schemas import RiskCategory

        with pytest.raises(ValidationError):
            RiskCategory(category="Financial")  # missing items
