"""Router: POST /api/analyze/risks — FR-5 Risk & clause highlighting."""

from __future__ import annotations

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from app.limiter import limiter
from app.models.schemas import ErrorDetail, ErrorResponse, RisksRequest, RisksResponse
from app.services.anthropic_client import generate_structured
from app.services.prompts import RISKS_SCHEMA, build_risks_prompt
from app.utils.errors import http_error_response
from app.utils.logger import get_logger
from app.utils.validation import check_text_length

_logger = get_logger(__name__)

router = APIRouter(prefix="/api/analyze", tags=["analyze"])


@router.post(
    "/risks",
    response_model=RisksResponse,
    responses={
        400: {"description": "Empty or invalid input"},
        429: {"description": "Rate limit exceeded"},
        502: {"description": "AI service unavailable"},
    },
    summary="Identify and categorise risk clauses in a legal document",
)
@limiter.limit("20/minute")
async def analyze_risks(request: Request, body: RisksRequest) -> RisksResponse | JSONResponse:
    """Accept raw document text and return risk clauses grouped by category.

    - **body.text** — The full document text to analyse.

    Returns a JSON object with:
    - **categories** — A list of topic groups, each with a ``category`` name and
      an ``items`` list.  Every item has ``clause_ref``, ``severity``
      (``high`` | ``medium`` | ``low`` | ``info``), and an ``explanation``
      phrased as informational hedged language ("may be worth reviewing because…").
    """
    text = body.text.strip()
    _logger.info("Risks request — text_len=%d chars", len(text))

    if not text:
        _logger.warning("Risks request — empty text")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="EMPTY_TEXT",
                    message="The provided text is empty. Please paste your document text.",
                )
            ).model_dump(),
        )

    if err := check_text_length(text, "text"):
        return err

    try:
        prompt = build_risks_prompt(text)
        result = await generate_structured(prompt, RISKS_SCHEMA)
        categories_count = len(result.get("categories", []))
        _logger.info("Risks complete — categories=%d", categories_count)
        return RisksResponse(**result)
    except Exception as exc:  # noqa: BLE001
        return http_error_response(exc)
