"""Router: POST /api/analyze/compare — FR-3 Document Comparison."""

from __future__ import annotations

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.models.schemas import CompareRequest, CompareResponse, ErrorDetail, ErrorResponse
from app.services.anthropic_client import generate_structured
from app.services.prompts import COMPARE_SCHEMA, build_compare_prompt
from app.utils.errors import http_error_response

router = APIRouter(prefix="/api/analyze", tags=["analyze"])


@router.post(
    "/compare",
    response_model=CompareResponse,
    responses={
        400: {"description": "Empty or invalid input"},
        502: {"description": "AI service unavailable"},
    },
    summary="Compare two legal documents and highlight similarities and differences",
)
async def analyze_compare(body: CompareRequest) -> CompareResponse | JSONResponse:
    """Accept two document texts and return a structured comparison.

    - **body.doc_a** — Full text of the first document.
    - **body.doc_b** — Full text of the second document.
    - **body.label_a** — Optional human-readable label for the first document (default: "Document A").
    - **body.label_b** — Optional human-readable label for the second document (default: "Document B").

    Returns a JSON object with:
    - **shared_topics** — Topics found in both documents, with each document's position,
      whether they are materially different, and why it matters.
    - **only_in_a** — Clauses/topics present only in the first document.
    - **only_in_b** — Clauses/topics present only in the second document.

    When the two documents are of very different types (e.g. a lease vs. a loan agreement),
    the endpoint still returns a best-effort comparison; the structural difference is noted
    in the `why_it_matters` field of the relevant shared_topics entries.
    """
    doc_a = body.doc_a.strip()
    doc_b = body.doc_b.strip()

    if not doc_a:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="EMPTY_DOC_A",
                    message="The first document text (doc_a) is empty. Please provide document content.",
                )
            ).model_dump(),
        )

    if not doc_b:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="EMPTY_DOC_B",
                    message="The second document text (doc_b) is empty. Please provide document content.",
                )
            ).model_dump(),
        )

    try:
        prompt = build_compare_prompt(
            doc_a=doc_a,
            doc_b=doc_b,
            label_a=body.label_a,
            label_b=body.label_b,
        )
        result = generate_structured(prompt, COMPARE_SCHEMA)
        return CompareResponse(**result)
    except Exception as exc:  # noqa: BLE001
        return http_error_response(exc)
