import os

from dotenv import load_dotenv

load_dotenv()


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


settings = Settings()
