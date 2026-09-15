import os

from dotenv import load_dotenv

load_dotenv()

from app.utils.logger import get_logger  # noqa: E402 — must come after load_dotenv

_logger = get_logger(__name__)


class Settings:
    def __init__(self) -> None:
        self.anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
        if not self.anthropic_api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is required. Set it in the environment before starting the application."
            )

        self.anthropic_base_url = os.environ.get(
            "ANTHROPIC_BASE_URL",
            "https://api.nextgen-beta.ica.ibm.com/ica",
        ).strip()

        self.anthropic_model = os.environ.get(
            "ANTHROPIC_MODEL",
            "claude-haiku-4-5",
        ).strip()

        # CORS_ORIGIN controls which frontend origin is allowed to call the API.
        #
        # DEV ONLY default — "http://localhost:8000" is intentionally permissive for
        # local development.  Before deploying to production you MUST set this env var
        # to the actual deployed frontend URL, e.g.:
        #
        #   CORS_ORIGIN=https://legallens-ai.vercel.app
        #
        # Set this in Vercel → Project Settings → Environment Variables.
        self.cors_origin = os.environ.get("CORS_ORIGIN", "http://localhost:8000").strip()

        _logger.info(
            "Settings loaded — model=%s base_url=%s cors_origin=%s",
            self.anthropic_model,
            self.anthropic_base_url,
            self.cors_origin,
        )


settings = Settings()
