from fastapi import FastAPI
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

app = FastAPI(title="LegalLens AI")

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

app.include_router(documents.router)
app.include_router(simplify.router)
app.include_router(risks.router)
app.include_router(checklist.router)
app.include_router(compare.router)
app.include_router(qa.router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def root() -> RedirectResponse:
    return RedirectResponse(url="/index.html")


# Serve the frontend static files (HTML/CSS/JS) from the public/ directory.
# This mount must come last so API routes take priority.
app.mount("/", StaticFiles(directory="public"), name="static")
