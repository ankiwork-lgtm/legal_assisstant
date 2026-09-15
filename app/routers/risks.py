"""Router: POST /api/analyze/risks — FR-5 Risk & clause highlighting."""

from __future__ import annotations

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.models.schemas import ErrorDetail, ErrorResponse, RisksRequest, RisksResponse
from app.services.anthropic_client import generate_structured
from app.services.prompts import RISKS_SCHEMA, build_risks_prompt
from app.utils.errors import http_error_response

router = APIRouter(prefix="/api/analyze", tags=["analyze"])


@router.post(
    "/risks",
    response_model=RisksResponse,
    responses={
        400: {"description": "Empty or invalid input"},
        502: {"description": "AI service unavailable"},
    },
    summary="Identify and categorise risk clauses in a legal document",
)
async def analyze_risks(body: RisksRequest) -> RisksResponse | JSONResponse:
    """Accept raw document text and return risk clauses grouped by category.

    - **body.text** — The full document text to analyse.

    Returns a JSON object with:
    - **categories** — A list of topic groups, each with a ``category`` name and
      an ``items`` list.  Every item has ``clause_ref``, ``severity``
      (``high`` | ``medium`` | ``low`` | ``info``), and an ``explanation``
      phrased as informational hedged language ("may be worth reviewing because…").
    """
    text = body.text.strip()
    if not text:
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
        prompt = build_risks_prompt(text)
        result = generate_structured(prompt, RISKS_SCHEMA)
        return RisksResponse(**result)
    except Exception as exc:  # noqa: BLE001
        return http_error_response(exc)
