"""Thin wrapper around the google-genai SDK for structured JSON generation.

Design ref: design.md §4.2
- Model: gemini-2.5-flash
- Forces JSON output via response_mime_type + response_schema.
- Wraps calls with a 25-second timeout and one retry on transient failure.
- Raises GeminiServiceError (HTTP 502) on permanent failure.
"""

from __future__ import annotations

import time
from typing import Any

import google.genai as genai
import google.genai.types as genai_types

from app.config import settings

# ---------------------------------------------------------------------------
# Typed exception
# ---------------------------------------------------------------------------

class GeminiServiceError(RuntimeError):
    """Raised when the Gemini API call fails after retries.

    Routers should convert this to an HTTP 502 with a user-friendly message.
    """

    def __init__(self, message: str, cause: BaseException | None = None) -> None:
        super().__init__(message)
        self.cause = cause


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_MODEL = "gemini-2.5-flash"
_TIMEOUT_SECONDS = 25.0
_MAX_ATTEMPTS = 2  # 1 initial attempt + 1 retry


# ---------------------------------------------------------------------------
# Client singleton (initialised lazily so tests can import without a real key)
# ---------------------------------------------------------------------------

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_structured(prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
    """Call Gemini and return a structured JSON object matching *schema*.

    Parameters
    ----------
    prompt:
        The full prompt to send to the model (system instruction + user content
        combined by the caller via :mod:`app.services.prompts`).
    schema:
        A JSON Schema dict describing the expected response shape.  Passed to
        Gemini as ``response_schema`` so the model is constrained to produce
        valid structured output — no brittle regex parsing needed.

    Returns
    -------
    dict
        The parsed JSON response from Gemini.

    Raises
    ------
    GeminiServiceError
        If all attempts fail (timeout, API error, or unparseable response).
    """
    client = _get_client()
    last_exc: BaseException | None = None

    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            response = client.models.generate_content(
                model=_MODEL,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                    http_options=genai_types.HttpOptions(
                        timeout=int(_TIMEOUT_SECONDS * 1000),  # milliseconds
                    ),
                ),
            )

            # response.text is the raw JSON string when response_mime_type is set
            raw = response.text
            if not raw:
                raise ValueError("Gemini returned an empty response body.")

            import json
            return json.loads(raw)

        except GeminiServiceError:
            raise  # don't swallow our own typed error
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if attempt < _MAX_ATTEMPTS:
                # Brief pause before retry (avoids hammering on transient blips)
                time.sleep(1.0)
            continue

    raise GeminiServiceError(
        "The AI service is temporarily unavailable. Please try again in a moment.",
        cause=last_exc,
    )
