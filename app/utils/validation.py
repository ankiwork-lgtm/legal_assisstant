"""Shared input-validation helpers for LegalLens AI routers."""

from __future__ import annotations

from fastapi import status
from fastapi.responses import JSONResponse

from app.config import MAX_TEXT_CHARS
from app.models.schemas import ErrorDetail, ErrorResponse
from app.utils.logger import get_logger

_logger = get_logger(__name__)


def check_text_length(text: str, label: str) -> JSONResponse | None:
    """Return a 400 JSONResponse when *text* exceeds :data:`~app.config.MAX_TEXT_CHARS`.

    Parameters
    ----------
    text:
        The (already-stripped) text to measure.
    label:
        Human-readable field name used in log output (e.g. ``"text"``,
        ``"doc_a"``, ``"doc_b"``).

    Returns
    -------
    JSONResponse | None
        ``None`` when the text is within the allowed limit; a ``JSONResponse``
        with ``TEXT_TOO_LONG`` (HTTP 400) when it is not.
    """
    if len(text) <= MAX_TEXT_CHARS:
        return None

    _logger.warning(
        "Text too long — label=%s  length=%d  limit=%d", label, len(text), MAX_TEXT_CHARS
    )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(
            error=ErrorDetail(
                code="TEXT_TOO_LONG",
                message=f"The provided text exceeds the {MAX_TEXT_CHARS:,}-character limit.",
            )
        ).model_dump(),
    )
