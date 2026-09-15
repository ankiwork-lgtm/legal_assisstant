"""Router: POST /api/analyze/checklist — FR-6 Checklist / next-steps generator."""

from __future__ import annotations

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.models.schemas import ChecklistRequest, ChecklistResponse, ErrorDetail, ErrorResponse
from app.services.anthropic_client import generate_structured
from app.services.prompts import CHECKLIST_SCHEMA, build_checklist_prompt
from app.utils.errors import http_error_response

router = APIRouter(prefix="/api/analyze", tags=["analyze"])


@router.post(
    "/checklist",
    response_model=ChecklistResponse,
    responses={
        400: {"description": "Empty or invalid input"},
        502: {"description": "AI service unavailable"},
    },
    summary="Generate an actionable pre-signing checklist from a legal document",
)
async def analyze_checklist(body: ChecklistRequest) -> ChecklistResponse | JSONResponse:
    """Accept raw document text and return an actionable checklist.

    - **body.text** — The full document text to analyse.

    Returns a JSON object with:
    - **ask_lawyer** — Questions and items to raise with a licensed attorney or the other party.
    - **verify_yourself** — Things the user can check or confirm on their own.
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
        prompt = build_checklist_prompt(text)
        result = generate_structured(prompt, CHECKLIST_SCHEMA)
        return ChecklistResponse(**result)
    except Exception as exc:  # noqa: BLE001
        return http_error_response(exc)
