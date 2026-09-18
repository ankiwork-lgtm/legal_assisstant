"""Thin wrapper around the Anthropic SDK for structured JSON generation.

- Model: configured via ANTHROPIC_MODEL env var (default: claude-haiku-4-5)
- Base URL: configured via ANTHROPIC_BASE_URL env var
- Forces JSON output via a system prompt instructing JSON-only responses.
- Wraps calls with a 60-second timeout and one retry on transient failure
  using exponential backoff with jitter.
- Caches identical prompt+schema pairs for 5 minutes (max 64 entries) to
  avoid redundant API calls for the same document analysis.
- Raises AnthropicServiceError (HTTP 502) on permanent failure.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import random
import time
from typing import Any

import anthropic
from cachetools import TTLCache

from app.config import settings
from app.utils.logger import get_logger

_logger = get_logger(__name__)

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
# Max characters to send in a single prompt.  Very long prompts consume most
# of the model's context window, leaving little room for the structured
# response and degrading output quality.  We truncate and append a notice
# rather than rejecting outright so the user still gets a result.
_PROMPT_CHAR_LIMIT = 40_000

# ---------------------------------------------------------------------------
# Response cache: avoids redundant AI calls for identical prompt+schema pairs.
# TTL = 300 s (5 min), max 64 entries — lightweight, zero external deps.
# ---------------------------------------------------------------------------

_response_cache: TTLCache[str, dict[str, Any]] = TTLCache(maxsize=64, ttl=300)

# In-flight futures: deduplicates concurrent identical cache misses so that
# only one API call is made per unique cache key at any given time.
_in_flight: dict[str, asyncio.Future[dict[str, Any]]] = {}


def _cache_key(prompt: str, schema: dict[str, Any]) -> str:
    """Return a stable hex digest for a (prompt, schema) pair."""
    h = hashlib.sha256()
    h.update(prompt.encode("utf-8"))
    h.update(json.dumps(schema, sort_keys=True).encode("utf-8"))
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Async client singleton (eagerly initialised at module load — race-free)
# ---------------------------------------------------------------------------

_client = anthropic.AsyncAnthropic(
    api_key=settings.anthropic_api_key,
    base_url=settings.anthropic_base_url,
    timeout=_TIMEOUT_SECONDS,
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def generate_structured(prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
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
    # ── Cache lookup ─────────────────────────────────────────────────────────
    cache_key = _cache_key(prompt, schema)
    if cache_key in _response_cache:
        _logger.debug("Cache hit — returning cached response (key=%s…)", cache_key[:12])
        return _response_cache[cache_key]

    # ── In-flight deduplication ───────────────────────────────────────────────
    # If another coroutine is already fetching this exact key, await its result.
    if cache_key in _in_flight:
        _logger.debug("In-flight hit — awaiting existing request (key=%s…)", cache_key[:12])
        return await _in_flight[cache_key]

    future: asyncio.Future[dict[str, Any]] = asyncio.get_event_loop().create_future()
    _in_flight[cache_key] = future

    last_exc: BaseException | None = None

    # ── Prompt length guard ──────────────────────────────────────────────────
    # Truncate excessively long prompts before they consume the entire context
    # window, which would leave too few tokens for the structured JSON response.
    if len(prompt) > _PROMPT_CHAR_LIMIT:
        _logger.warning(
            "Prompt truncated — original=%d chars  limit=%d chars",
            len(prompt),
            _PROMPT_CHAR_LIMIT,
        )
        prompt = (
            prompt[:_PROMPT_CHAR_LIMIT]
            + "\n\n[Note: document was truncated to fit within the processing limit. "
            "The analysis covers the first portion of the document.]"
        )

    system_prompt = (
        "You are a structured JSON API. "
        "You MUST respond with a single valid JSON object and nothing else — "
        "no markdown fences, no prose, no explanation outside the JSON. "
        f"The response MUST conform to this JSON Schema:\n{json.dumps(schema, indent=2)}"
    )

    _logger.debug(
        "Anthropic request — model=%s  prompt_len=%d chars",
        settings.anthropic_model,
        len(prompt),
    )

    try:
        for attempt in range(1, _MAX_ATTEMPTS + 1):
            t0 = time.perf_counter()
            try:
                # Native async call — no thread-pool blocking
                response = await _client.messages.create(
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

                elapsed_ms = (time.perf_counter() - t0) * 1000
                _logger.info(
                    "Anthropic response received — attempt=%d  %.1fms  response_len=%d chars",
                    attempt,
                    elapsed_ms,
                    len(raw),
                )
                result = json.loads(stripped)

                # Store in cache and resolve in-flight future before returning
                _response_cache[cache_key] = result
                future.set_result(result)
                return result

            except AnthropicServiceError:
                raise  # don't swallow our own typed error
            except Exception as exc:  # noqa: BLE001
                elapsed_ms = (time.perf_counter() - t0) * 1000
                _logger.warning(
                    "Anthropic attempt %d/%d failed after %.1fms — %s: %s",
                    attempt,
                    _MAX_ATTEMPTS,
                    elapsed_ms,
                    type(exc).__name__,
                    exc,
                )
                last_exc = exc
                if attempt < _MAX_ATTEMPTS:
                    # Exponential backoff with jitter: 1s ± 0–0.5s, 2s ± 0–0.5s, …
                    wait = 2 ** (attempt - 1) + random.uniform(0, 0.5)  # noqa: S311
                    _logger.info("Retrying in %.2f s…", wait)
                    await asyncio.sleep(wait)
                continue

        _logger.error(
            "All %d Anthropic attempts exhausted — last error: %s: %s",
            _MAX_ATTEMPTS,
            type(last_exc).__name__ if last_exc else "unknown",
            last_exc,
        )
        service_exc = AnthropicServiceError(
            "The AI service is temporarily unavailable. Please try again in a moment.",
            cause=last_exc,
        )
        future.set_exception(service_exc)
        raise service_exc

    finally:
        _in_flight.pop(cache_key, None)
