"""Router: POST /api/documents/extract — FR-1 Document Ingestion."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import JSONResponse

from app.config import MAX_TEXT_CHARS
from app.limiter import limiter
from app.models.schemas import ErrorDetail, ErrorResponse, ExtractResponse, ExtractTextRequest
from app.services.pdf_extractor import CorruptPDFError, ScannedPDFError, extract_text
from app.utils.logger import get_logger

_logger = get_logger(__name__)

# Default upload size limit: 10 MB (keeps us within Vercel's payload limits)
MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB

router = APIRouter(prefix="/api/documents", tags=["documents"])


def _error(code: str, message: str, status_code: int) -> JSONResponse:
    body = ErrorResponse(error=ErrorDetail(code=code, message=message))
    return JSONResponse(status_code=status_code, content=body.model_dump())


@router.post(
    "/extract",
    response_model=ExtractResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid or corrupt PDF"},
        413: {"model": ErrorResponse, "description": "File exceeds size limit"},
        422: {"model": ErrorResponse, "description": "Scanned/image PDF"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    },
    summary="Extract text from a PDF upload or accept pasted text",
)
@limiter.limit("10/minute")
async def extract_document(
    request: Request,
    file: UploadFile | None = File(default=None),
    text: str | None = Form(default=None),
) -> ExtractResponse | JSONResponse:
    """Accept either a PDF file *or* pasted text and return the extracted document text.

    Priority: if *file* is provided it takes precedence over *text*.

    - **file** — PDF upload via ``multipart/form-data``.
    - **text** — Raw text field via ``multipart/form-data`` (pasted-text path).

    Both fields live in the same ``multipart/form-data`` body so clients can use
    a single ``<form>`` or ``FormData`` object regardless of input type.

    If neither field is provided the endpoint returns a 400 error.
    """

    # ------------------------------------------------------------------ #
    # Path A — file upload
    # ------------------------------------------------------------------ #
    if file is not None:
        _logger.info("Extract request — path=file  filename=%s  content_type=%s", file.filename, file.content_type)
        # Strict allowlist: only accept known PDF MIME types.
        # Using a blocklist/partial check allowed application/zip and similar
        # types to bypass validation — an explicit allowlist is safer.
        _ALLOWED_CONTENT_TYPES = {"application/pdf", "application/octet-stream"}
        if file.content_type not in _ALLOWED_CONTENT_TYPES:
            _logger.warning("Rejected invalid file type — %s", file.content_type)
            return _error(
                code="INVALID_FILE_TYPE",
                message=(
                    f"Unsupported file type '{file.content_type}'. "
                    "Please upload a PDF file."
                ),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        pdf_bytes = await file.read()
        _logger.debug("File read — size=%d bytes", len(pdf_bytes))

        if len(pdf_bytes) > MAX_FILE_BYTES:
            _logger.warning("File too large — size=%d bytes  limit=%d bytes", len(pdf_bytes), MAX_FILE_BYTES)
            return _error(
                code="FILE_TOO_LARGE",
                message=(
                    f"Uploaded file is {len(pdf_bytes) // (1024 * 1024)} MB, "
                    f"which exceeds the {MAX_FILE_BYTES // (1024 * 1024)} MB limit. "
                    "Please upload a smaller file."
                ),
                status_code=413,
            )

        if len(pdf_bytes) == 0:
            _logger.warning("Empty file uploaded")
            return _error(
                code="EMPTY_FILE",
                message="The uploaded file is empty. Please upload a valid PDF.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # extract_text is CPU-bound (synchronous pypdf parse).
            # Run in a thread-pool so the async event loop stays free.
            result = await asyncio.to_thread(extract_text, pdf_bytes)
        except ScannedPDFError as exc:
            return _error(
                code="SCANNED_PDF",
                message=str(exc),
                status_code=422,
            )
        except CorruptPDFError as exc:
            return _error(
                code="CORRUPT_PDF",
                message=str(exc),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        _logger.info(
            "Extract complete — path=file  pages=%d  words=%d",
            result.page_count,
            result.word_count,
        )
        return ExtractResponse(
            text=result.text,
            word_count=result.word_count,
            page_count=result.page_count,
        )

    # ------------------------------------------------------------------ #
    # Path B — pasted text
    # ------------------------------------------------------------------ #
    if text is not None:
        stripped = text.strip()
        if not stripped:
            _logger.warning("Extract request — empty pasted text")
            return _error(
                code="EMPTY_TEXT",
                message="The provided text is empty. Please paste your document text.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if len(stripped) > MAX_TEXT_CHARS:
            _logger.warning("Extract request — pasted text too long  length=%d  limit=%d", len(stripped), MAX_TEXT_CHARS)
            return _error(
                code="TEXT_TOO_LONG",
                message=f"The provided text exceeds the {MAX_TEXT_CHARS:,}-character limit.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        word_count = len(stripped.split())
        _logger.info("Extract complete — path=text  words=%d", word_count)
        return ExtractResponse(
            text=stripped,
            word_count=word_count,
            page_count=0,
        )

    # ------------------------------------------------------------------ #
    # Neither provided
    # ------------------------------------------------------------------ #
    _logger.warning("Extract request — no input provided")
    return _error(
        code="NO_INPUT",
        message=(
            "No document provided. "
            "Upload a PDF file via the 'file' field or paste text via the 'text' field."
        ),
        status_code=status.HTTP_400_BAD_REQUEST,
    )
