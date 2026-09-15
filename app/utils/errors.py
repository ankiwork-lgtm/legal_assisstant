"""Central exception → HTTP status mapping for LegalLens AI.

Design ref: design.md §4.5

Routers import :func:`http_error_response` to convert known domain exceptions
into the uniform ``{"error": {"code": ..., "message": ...}}`` envelope defined
in :mod:`app.models.schemas`.  Unknown exceptions map to 500 with a generic
message so no stack traces are ever leaked to the client.

Usage example::

    from app.utils.errors import http_error_response
    from app.services.pdf_extractor import CorruptPDFError

    try:
        result = extract_text(data)
    except Exception as exc:
        return http_error_response(exc)
"""

from __future__ import annotations

from fastapi import status
from fastapi.responses import JSONResponse

from app.models.schemas import ErrorDetail, ErrorResponse
from app.services.pdf_extractor import CorruptPDFError, ScannedPDFError
from app.services.anthropic_client import AnthropicServiceError


# ---------------------------------------------------------------------------
# Mapping: exception type → (error_code, http_status)
# ---------------------------------------------------------------------------

_EXCEPTION_MAP: list[tuple[type[Exception], str, int]] = [
    # Document ingestion errors
    (ScannedPDFError,        "SCANNED_PDF",      422),
    (CorruptPDFError,        "CORRUPT_PDF",       status.HTTP_400_BAD_REQUEST),
    # Anthropic / upstream service errors
    (AnthropicServiceError,  "AI_SERVICE_ERROR",  status.HTTP_502_BAD_GATEWAY),
    # Generic value / validation errors (e.g. empty text)
    (ValueError,         "INVALID_INPUT",     status.HTTP_400_BAD_REQUEST),
]

# Fallback for any exception not in the map above
_FALLBACK_CODE = "INTERNAL_ERROR"
_FALLBACK_STATUS = status.HTTP_500_INTERNAL_SERVER_ERROR
_FALLBACK_MESSAGE = (
    "An unexpected error occurred. Please try again. "
    "If the problem persists, contact support."
)


# ---------------------------------------------------------------------------
# Public helper
# ---------------------------------------------------------------------------

def http_error_response(exc: Exception) -> JSONResponse:
    """Convert *exc* to a :class:`~fastapi.responses.JSONResponse` error envelope.

    The response body always follows the shape::

        {"error": {"code": "<CODE>", "message": "<human-readable text>"}}

    Parameters
    ----------
    exc:
        Any exception raised during request handling.

    Returns
    -------
    JSONResponse
        A response with the appropriate HTTP status code and error body.
    """
    for exc_type, code, http_status in _EXCEPTION_MAP:
        if isinstance(exc, exc_type):
            body = ErrorResponse(
                error=ErrorDetail(code=code, message=str(exc))
            )
            return JSONResponse(status_code=http_status, content=body.model_dump())

    # Unknown exception — return a safe generic message, no internal details
    body = ErrorResponse(
        error=ErrorDetail(code=_FALLBACK_CODE, message=_FALLBACK_MESSAGE)
    )
    return JSONResponse(status_code=_FALLBACK_STATUS, content=body.model_dump())
