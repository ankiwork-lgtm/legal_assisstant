import os
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import checklist
from app.routers import compare
from app.routers import documents
from app.routers import qa
from app.routers import risks
from app.routers import simplify
from app.utils.logger import get_logger

_logger = get_logger(__name__)

app = FastAPI(title="LegalLens AI")

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
