"""Router: POST /api/analyze/qa — FR-4 Document-Grounded Q&A."""

from __future__ import annotations

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.models.schemas import ErrorDetail, ErrorResponse, QARequest, QAResponse
from app.services.anthropic_client import generate_structured
from app.services.prompts import QA_SCHEMA, build_qa_prompt
from app.utils.errors import http_error_response

router = APIRouter(prefix="/api/analyze", tags=["analyze"])


@router.post(
    "/qa",
    response_model=QAResponse,
    responses={
        400: {"description": "Empty or invalid input"},
        502: {"description": "AI service unavailable"},
    },
    summary="Answer a question grounded in the provided document text",
)
async def analyze_qa(body: QARequest) -> QAResponse | JSONResponse:
    """Answer *body.question* using only the content of *body.text*.

    - **body.text** — Full document text to query against.
    - **body.question** — The question to answer.
    - **body.history** — Optional list of prior turns (role + content) for
      conversational follow-ups.

    Returns a JSON object with:
    - **answer** — Plain-English answer grounded solely in the document.
      When the document does not address the question, states that clearly.
    - **found_in_document** — ``false`` when the document doesn't contain the
      answer; no fabrication occurs.
    - **supporting_clause_ref** — Reference to the relevant clause/page, or
      ``null`` when ``found_in_document`` is ``false``.
    """
    text = body.text.strip()
    question = body.question.strip()

    if not text:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="EMPTY_TEXT",
                    message="The document text is empty. Please provide document content.",
                )
            ).model_dump(),
        )

    if not question:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="EMPTY_QUESTION",
                    message="The question is empty. Please provide a question.",
                )
            ).model_dump(),
        )

    try:
        history = [item.model_dump() for item in body.history] if body.history else None
        prompt = build_qa_prompt(
            document_text=text,
            question=question,
            history=history,
        )
        result = generate_structured(prompt, QA_SCHEMA)
        return QAResponse(**result)
    except Exception as exc:  # noqa: BLE001
        return http_error_response(exc)
