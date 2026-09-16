"""Router: POST /api/analyze/compare — FR-3 Document Comparison."""

from __future__ import annotations

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from app.config import MAX_TEXT_CHARS
from app.limiter import limiter
from app.models.schemas import CompareRequest, CompareResponse, ErrorDetail, ErrorResponse
from app.services.anthropic_client import generate_structured
from app.services.prompts import COMPARE_SCHEMA, build_compare_prompt
from app.utils.errors import http_error_response
from app.utils.logger import get_logger

_logger = get_logger(__name__)

router = APIRouter(prefix="/api/analyze", tags=["analyze"])


@router.post(
    "/compare",
    response_model=CompareResponse,
    responses={
        400: {"description": "Empty or invalid input"},
        429: {"description": "Rate limit exceeded"},
        502: {"description": "AI service unavailable"},
    },
    summary="Compare two legal documents and highlight similarities and differences",
)
@limiter.limit("20/minute")
async def analyze_compare(request: Request, body: CompareRequest) -> CompareResponse | JSONResponse:
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
    _logger.info(
        "Compare request — label_a=%r  label_b=%r  doc_a_len=%d  doc_b_len=%d chars",
        body.label_a,
        body.label_b,
        len(doc_a),
        len(doc_b),
    )

    if not doc_a:
        _logger.warning("Compare request — doc_a is empty")
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
        _logger.warning("Compare request — doc_b is empty")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="EMPTY_DOC_B",
                    message="The second document text (doc_b) is empty. Please provide document content.",
                )
            ).model_dump(),
        )

    if len(doc_a) > MAX_TEXT_CHARS or len(doc_b) > MAX_TEXT_CHARS:
        _logger.warning(
            "Compare request — document text too long  doc_a_len=%d  doc_b_len=%d  limit=%d",
            len(doc_a),
            len(doc_b),
            MAX_TEXT_CHARS,
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="TEXT_TOO_LONG",
                    message=f"Each document must not exceed the {MAX_TEXT_CHARS:,}-character limit.",
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
        result = await generate_structured(prompt, COMPARE_SCHEMA)
        shared_count = len(result.get("shared_topics", []))
        only_a_count = len(result.get("only_in_a", []))
        only_b_count = len(result.get("only_in_b", []))
        _logger.info(
            "Compare complete — shared=%d  only_in_a=%d  only_in_b=%d",
            shared_count,
            only_a_count,
            only_b_count,
        )
        return CompareResponse(**result)
    except Exception as exc:  # noqa: BLE001
        return http_error_response(exc)
