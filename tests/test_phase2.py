"""Unit tests for Phase 2 — Anthropic Integration Core.

Covers:
- app/services/anthropic_client.py  (AnthropicServiceError, retry, structured call)
- app/utils/errors.py               (exception → HTTP status mapping)
- app/services/prompts.py           (schema shapes, disclaimer presence)
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.responses import JSONResponse

from app.services.anthropic_client import AnthropicServiceError, generate_structured
from app.services.pdf_extractor import CorruptPDFError, ScannedPDFError
from app.utils.errors import http_error_response
from app.services.prompts import (
    LEGAL_DISCLAIMER_BLOCK,
    SIMPLIFY_SCHEMA,
    RISKS_SCHEMA,
    CHECKLIST_SCHEMA,
    COMPARE_SCHEMA,
    QA_SCHEMA,
    build_simplify_prompt,
    build_risks_prompt,
    build_checklist_prompt,
    build_compare_prompt,
    build_qa_prompt,
)


# ===========================================================================
# anthropic_client.py
# ===========================================================================

class TestAnthropicServiceError:
    def test_is_runtime_error(self):
        err = AnthropicServiceError("test")
        assert isinstance(err, RuntimeError)

    def test_stores_cause(self):
        cause = ValueError("root cause")
        err = AnthropicServiceError("wrapper", cause=cause)
        assert err.cause is cause

    def test_message_accessible(self):
        err = AnthropicServiceError("oops")
        assert str(err) == "oops"


def _mock_anthropic_response(payload: dict) -> MagicMock:
    """Build a MagicMock that mimics an anthropic.types.Message with one TextBlock."""
    content_block = MagicMock()
    content_block.text = json.dumps(payload)
    resp = MagicMock()
    resp.content = [content_block]
    return resp


@pytest.fixture(autouse=True)
def clear_response_cache():
    """Ensure the TTL cache is empty before each test to prevent bleed-through."""
    from app.services.anthropic_client import _response_cache
    _response_cache.clear()
    yield
    _response_cache.clear()


class TestGenerateStructured:
    """Tests for generate_structured() — Anthropic API is always mocked."""

    @pytest.mark.asyncio
    @patch("app.services.anthropic_client._client")
    async def test_returns_parsed_dict_on_success(self, mock_client):
        expected = {"overview": "test", "sections": []}
        mock_client.messages.create = AsyncMock(
            return_value=_mock_anthropic_response(expected)
        )
        result = await generate_structured("some prompt", SIMPLIFY_SCHEMA)
        assert result == expected

    @pytest.mark.asyncio
    @patch("app.services.anthropic_client._client")
    async def test_calls_create_once_on_success(self, mock_client):
        mock_client.messages.create = AsyncMock(
            return_value=_mock_anthropic_response(
                {"answer": "yes", "found_in_document": True, "supporting_clause_ref": None}
            )
        )
        await generate_structured("prompt", QA_SCHEMA)
        assert mock_client.messages.create.call_count == 1

    @pytest.mark.asyncio
    @patch("app.services.anthropic_client.asyncio.sleep")
    @patch("app.services.anthropic_client._client")
    async def test_retries_once_on_transient_failure(self, mock_client, mock_sleep):
        """First call raises, second succeeds — only one retry allowed."""
        ok_response = _mock_anthropic_response({"overview": "ok", "sections": []})
        mock_client.messages.create = AsyncMock(
            side_effect=[
                Exception("transient network error"),
                ok_response,
            ]
        )
        result = await generate_structured("prompt", SIMPLIFY_SCHEMA)
        assert result["overview"] == "ok"
        mock_sleep.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.anthropic_client.asyncio.sleep")
    @patch("app.services.anthropic_client._client")
    async def test_raises_anthropic_service_error_after_all_attempts_fail(
        self, mock_client, mock_sleep
    ):
        """Both attempts fail → AnthropicServiceError raised."""
        mock_client.messages.create = AsyncMock(
            side_effect=Exception("always fails")
        )
        with pytest.raises(AnthropicServiceError):
            await generate_structured("prompt", SIMPLIFY_SCHEMA)

    @pytest.mark.asyncio
    @patch("app.services.anthropic_client._client")
    async def test_raises_anthropic_service_error_on_empty_response(self, mock_client):
        """Empty content list should cause AnthropicServiceError after retries."""
        empty_resp = MagicMock()
        empty_resp.content = []
        mock_client.messages.create = AsyncMock(return_value=empty_resp)
        with pytest.raises(AnthropicServiceError):
            await generate_structured("prompt", SIMPLIFY_SCHEMA)

    @pytest.mark.asyncio
    @patch("app.services.anthropic_client._client")
    async def test_strips_markdown_fences(self, mock_client):
        """Model wrapping JSON in ```json fences should still parse correctly."""
        payload = {"overview": "ok", "sections": []}
        content_block = MagicMock()
        content_block.text = f"```json\n{json.dumps(payload)}\n```"
        resp = MagicMock()
        resp.content = [content_block]
        mock_client.messages.create = AsyncMock(return_value=resp)
        result = await generate_structured("prompt", SIMPLIFY_SCHEMA)
        assert result == payload


# ===========================================================================
# app/utils/errors.py
# ===========================================================================

class TestHttpErrorResponse:
    def test_scanned_pdf_maps_to_422(self):
        resp = http_error_response(ScannedPDFError("scanned"))
        assert resp.status_code == 422
        body = json.loads(resp.body)
        assert body["error"]["code"] == "SCANNED_PDF"

    def test_corrupt_pdf_maps_to_400(self):
        resp = http_error_response(CorruptPDFError("corrupt"))
        assert resp.status_code == 400
        body = json.loads(resp.body)
        assert body["error"]["code"] == "CORRUPT_PDF"

    def test_anthropic_service_error_maps_to_502(self):
        resp = http_error_response(AnthropicServiceError("ai down"))
        assert resp.status_code == 502
        body = json.loads(resp.body)
        assert body["error"]["code"] == "AI_SERVICE_ERROR"

    def test_value_error_maps_to_400(self):
        resp = http_error_response(ValueError("bad value"))
        assert resp.status_code == 400
        body = json.loads(resp.body)
        assert body["error"]["code"] == "INVALID_INPUT"

    def test_unknown_exception_maps_to_500(self):
        resp = http_error_response(RuntimeError("unexpected"))
        assert resp.status_code == 500
        body = json.loads(resp.body)
        assert body["error"]["code"] == "INTERNAL_ERROR"

    def test_unknown_exception_message_is_generic(self):
        """Stack traces / internal details must not leak."""
        resp = http_error_response(RuntimeError("secret internal detail"))
        body = json.loads(resp.body)
        assert "secret internal detail" not in body["error"]["message"]

    def test_returns_json_response_type(self):
        resp = http_error_response(ValueError("x"))
        assert isinstance(resp, JSONResponse)

    def test_error_envelope_shape(self):
        """Response body always has {'error': {'code': ..., 'message': ...}}."""
        resp = http_error_response(AnthropicServiceError("x"))
        body = json.loads(resp.body)
        assert "error" in body
        assert "code" in body["error"]
        assert "message" in body["error"]


# ===========================================================================
# app/services/prompts.py
# ===========================================================================

class TestLegalDisclaimerBlock:
    def test_disclaimer_mentions_not_legal_advice(self):
        assert "not legal advice" in LEGAL_DISCLAIMER_BLOCK.lower()

    def test_disclaimer_mentions_attorney(self):
        assert "attorney" in LEGAL_DISCLAIMER_BLOCK.lower()

    def test_disclaimer_mentions_attorney_client(self):
        assert "attorney-client" in LEGAL_DISCLAIMER_BLOCK.lower()


class TestDisclaimerInjectedInAllPrompts:
    """Every build_* function must include the disclaimer."""

    def _check(self, prompt: str) -> None:
        assert "not legal advice" in prompt.lower(), (
            "Disclaimer block missing from prompt"
        )

    def test_simplify_prompt_has_disclaimer(self):
        self._check(build_simplify_prompt("some contract text"))

    def test_risks_prompt_has_disclaimer(self):
        self._check(build_risks_prompt("some contract text"))

    def test_checklist_prompt_has_disclaimer(self):
        self._check(build_checklist_prompt("some contract text"))

    def test_compare_prompt_has_disclaimer(self):
        self._check(build_compare_prompt("doc a text", "doc b text"))

    def test_qa_prompt_has_disclaimer(self):
        self._check(build_qa_prompt("doc text", "What is the notice period?"))


class TestPromptContainsDocumentText:
    """Document text must appear in the generated prompt."""

    SAMPLE = "THIS IS THE CONTRACT TEXT"

    def test_simplify_includes_document(self):
        assert self.SAMPLE in build_simplify_prompt(self.SAMPLE)

    def test_risks_includes_document(self):
        assert self.SAMPLE in build_risks_prompt(self.SAMPLE)

    def test_checklist_includes_document(self):
        assert self.SAMPLE in build_checklist_prompt(self.SAMPLE)

    def test_compare_includes_both_docs(self):
        prompt = build_compare_prompt("DOC_A_TEXT", "DOC_B_TEXT")
        assert "DOC_A_TEXT" in prompt
        assert "DOC_B_TEXT" in prompt

    def test_qa_includes_document_and_question(self):
        prompt = build_qa_prompt("CONTRACT_TEXT", "WHAT_IS_THE_TERM?")
        assert "CONTRACT_TEXT" in prompt
        assert "WHAT_IS_THE_TERM?" in prompt


class TestQAPromptHistory:
    def test_history_included_when_provided(self):
        history = [
            {"role": "user", "content": "First question"},
            {"role": "assistant", "content": "First answer"},
        ]
        prompt = build_qa_prompt("doc", "follow-up", history=history)
        assert "First question" in prompt
        assert "First answer" in prompt

    def test_no_history_block_when_none(self):
        prompt = build_qa_prompt("doc", "question", history=None)
        assert "CONVERSATION HISTORY" not in prompt


class TestComparePromptLabels:
    def test_custom_labels_appear_in_prompt(self):
        prompt = build_compare_prompt("a", "b", label_a="Lease 2023", label_b="Lease 2024")
        assert "Lease 2023" in prompt
        assert "Lease 2024" in prompt

    def test_default_labels_are_document_a_b(self):
        prompt = build_compare_prompt("a", "b")
        assert "Document A" in prompt
        assert "Document B" in prompt


class TestSchemaShapes:
    """Minimal structural checks on the exported schema dicts."""

    def test_simplify_schema_has_required_keys(self):
        assert "overview" in SIMPLIFY_SCHEMA["properties"]
        assert "sections" in SIMPLIFY_SCHEMA["properties"]

    def test_risks_schema_has_categories(self):
        assert "categories" in RISKS_SCHEMA["properties"]

    def test_risks_severity_enum(self):
        items_schema = (
            RISKS_SCHEMA["properties"]["categories"]["items"]
            ["properties"]["items"]["items"]
        )
        assert set(items_schema["properties"]["severity"]["enum"]) == {
            "high", "medium", "low", "info"
        }

    def test_checklist_schema_has_ask_lawyer_and_verify(self):
        props = CHECKLIST_SCHEMA["properties"]
        assert "ask_lawyer" in props
        assert "verify_yourself" in props

    def test_compare_schema_has_shared_topics_and_only_lists(self):
        props = COMPARE_SCHEMA["properties"]
        assert "shared_topics" in props
        assert "only_in_a" in props
        assert "only_in_b" in props

    def test_qa_schema_has_found_in_document_bool(self):
        assert QA_SCHEMA["properties"]["found_in_document"]["type"] == "boolean"

    def test_qa_schema_clause_ref_nullable(self):
        ref_type = QA_SCHEMA["properties"]["supporting_clause_ref"]["type"]
        assert "null" in ref_type
