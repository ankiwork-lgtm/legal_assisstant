"""Router: POST /api/analyze/simplify — FR-2 Plain-language simplification."""

from __future__ import annotations

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.models.schemas import ErrorDetail, ErrorResponse, SimplifyRequest, SimplifyResponse
from app.services.anthropic_client import generate_structured
from app.services.prompts import SIMPLIFY_SCHEMA, build_simplify_prompt
from app.utils.errors import http_error_response
from app.utils.logger import get_logger

_logger = get_logger(__name__)

router = APIRouter(prefix="/api/analyze", tags=["analyze"])


@router.post(
    "/simplify",
    response_model=SimplifyResponse,
    responses={
        400: {"description": "Empty or invalid input"},
        502: {"description": "AI service unavailable"},
    },
    summary="Return a plain-language explanation of a legal document",
)
async def simplify_document(body: SimplifyRequest) -> SimplifyResponse | JSONResponse:
    """Accept raw document text and return a structured plain-language explanation.

    - **body.text** — The full document text to simplify.

    Returns a JSON object with:
    - **overview** — A short top-level plain-English summary.
    - **sections** — One entry per clause/section, each with
      ``heading``, ``original_excerpt_ref``, and ``plain_language``.
    """
    text = body.text.strip()
    _logger.info("Simplify request — text_len=%d chars", len(text))

    if not text:
        _logger.warning("Simplify request — empty text")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="EMPTY_TEXT",
                    message="The provided text is empty. Please paste your document text.",
                )
            ).model_dump(),
        )

    try:
        prompt = build_simplify_prompt(text)
        result = generate_structured(prompt, SIMPLIFY_SCHEMA)
        sections_count = len(result.get("sections", []))
        _logger.info("Simplify complete — sections=%d", sections_count)
        return SimplifyResponse(**result)
    except Exception as exc:  # noqa: BLE001
        return http_error_response(exc)
