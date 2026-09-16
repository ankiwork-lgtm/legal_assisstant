import os
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.limiter import limiter
from app.models.schemas import ErrorDetail, ErrorResponse
from app.routers import checklist
from app.routers import compare
from app.routers import documents
from app.routers import qa
from app.routers import risks
from app.routers import simplify
from app.utils.logger import get_logger

_logger = get_logger(__name__)

app = FastAPI(title="LegalLens AI")
app.state.limiter = limiter

_logger.info("LegalLens AI application starting up")

# CORS is locked to settings.cors_origin (loaded from the CORS_ORIGIN env var).
# The default value "http://localhost:8000" is for local development only.
# Before final deployment set CORS_ORIGIN to the Vercel frontend URL, e.g.:
#   CORS_ORIGIN=https://legallens-ai.vercel.app
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):  # type: ignore[type-arg]
    """Inject security headers on every outbound response.

    Content-Security-Policy restricts resource loading to same-origin plus
    Google Fonts (used by the Inter typeface in the frontend).
    """
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data:; "
        "connect-src 'self'; "
        "frame-ancestors 'none';"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Return the standard error envelope on HTTP 429."""
    body = ErrorResponse(
        error=ErrorDetail(
            code="RATE_LIMITED",
            message="Too many requests. Please wait a moment before trying again.",
        )
    )
    return JSONResponse(status_code=429, content=body.model_dump())


@app.middleware("http")
async def log_requests(request: Request, call_next):  # type: ignore[type-arg]
    """Log every inbound request and its response status + duration."""
    start = time.perf_counter()
    _logger.info("→ %s %s", request.method, request.url.path)
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    _logger.info(
        "← %s %s  status=%d  %.1fms",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response


app.include_router(documents.router)
app.include_router(simplify.router)
app.include_router(risks.router)
app.include_router(checklist.router)
app.include_router(compare.router)
app.include_router(qa.router)


@app.get("/api/health")
def health() -> dict[str, str]:
    _logger.debug("Health check requested")
    return {"status": "ok"}


# Serve the frontend static files (HTML/CSS/JS) from the public/ directory.
# This mount must come last so API routes take priority.
# Guard: on Vercel, public/ is served by @vercel/static and is not bundled
# with the Python function, so only mount when the directory is present.
if os.path.isdir("public"):

    @app.get("/")
    def root() -> RedirectResponse:
        return RedirectResponse(url="/index.html")

    app.mount("/", StaticFiles(directory="public"), name="static")
