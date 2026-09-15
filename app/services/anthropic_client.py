"""Thin wrapper around the Anthropic SDK for structured JSON generation.

- Model: configured via ANTHROPIC_MODEL env var (default: claude-haiku-4-5)
- Base URL: configured via ANTHROPIC_BASE_URL env var
- Forces JSON output via a system prompt instructing JSON-only responses.
- Wraps calls with a 60-second timeout and one retry on transient failure.
- Raises AnthropicServiceError (HTTP 502) on permanent failure.
"""

from __future__ import annotations

import json
import time
from typing import Any

import anthropic

from app.config import settings

# ---------------------------------------------------------------------------
# Typed exception
# ---------------------------------------------------------------------------


class AnthropicServiceError(RuntimeError):
    """Raised when the Anthropic API call fails after retries.

    Routers should convert this to an HTTP 502 with a user-friendly message.
    """

    def __init__(self, message: str, cause: BaseException | None = None) -> None:
        super().__init__(message)
        self.cause = cause


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_TIMEOUT_SECONDS = 60.0
_MAX_ATTEMPTS = 2  # 1 initial attempt + 1 retry
_MAX_TOKENS = 4096


# ---------------------------------------------------------------------------
# Client singleton (initialised lazily so tests can import without a real key)
# ---------------------------------------------------------------------------

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(
            api_key=settings.anthropic_api_key,
            base_url=settings.anthropic_base_url,
            timeout=_TIMEOUT_SECONDS,
        )
    return _client


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_structured(prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
    """Call Anthropic Claude and return a structured JSON object matching *schema*.

    Parameters
    ----------
    prompt:
        The full prompt to send to the model (system instruction + user content
        combined by the caller via :mod:`app.services.prompts`).
    schema:
        A JSON Schema dict describing the expected response shape. Included in
        the system prompt so the model produces valid structured output.

    Returns
    -------
    dict
        The parsed JSON response from Claude.

    Raises
    ------
    AnthropicServiceError
        If all attempts fail (timeout, API error, or unparseable response).
    """
    client = _get_client()
    last_exc: BaseException | None = None

    system_prompt = (
        "You are a structured JSON API. "
        "You MUST respond with a single valid JSON object and nothing else — "
        "no markdown fences, no prose, no explanation outside the JSON. "
        f"The response MUST conform to this JSON Schema:\n{json.dumps(schema, indent=2)}"
    )

    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            response = client.messages.create(
                model=settings.anthropic_model,
                max_tokens=_MAX_TOKENS,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}],
            )

            raw = response.content[0].text if response.content else ""
            if not raw:
                raise ValueError("Anthropic returned an empty response body.")

            # Strip markdown code fences if the model wraps its output
            stripped = raw.strip()
            if stripped.startswith("```"):
                stripped = stripped.split("\n", 1)[-1]
                stripped = stripped.rsplit("```", 1)[0]

            return json.loads(stripped)

        except AnthropicServiceError:
            raise  # don't swallow our own typed error
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if attempt < _MAX_ATTEMPTS:
                time.sleep(1.0)
            continue

    raise AnthropicServiceError(
        "The AI service is temporarily unavailable. Please try again in a moment.",
        cause=last_exc,
    )
