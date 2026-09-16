# LegalLens AI — Security & Efficiency Improvement Plan (Updated)

## Overview

This plan tracks all Security and Efficiency improvements targeting the
**Security: 90** and **Efficiency: 85** submission scores. It reflects the
current state of the codebase after a partial round of manual changes.

Completed items are marked `[x]`. Remaining items are `[ ]`.

---

## Completed Changes (already in codebase)

| Change | File | Notes |
|--------|------|-------|
| `Strict-Transport-Security` + `Permissions-Policy` headers | `app/main.py` | Also added `X-XSS-Protection: 0` |
| Strict MIME-type allowlist for PDF uploads | `app/routers/documents.py` | Allowlist replaces old prefix check |
| `asyncio.to_thread` for `extract_text` | `app/routers/documents.py` | Unblocks event loop during PDF parse |
| Exponential backoff + jitter on retry | `app/services/anthropic_client.py` | `2^(n-1) + uniform(0, 0.5)` s |
| Native `AsyncAnthropic` client | `app/services/anthropic_client.py` | Eliminates sync `to_thread` wrapper |
| TTL response cache (`cachetools.TTLCache`) | `app/services/anthropic_client.py` | 64 entries, 5-min TTL |
| Question length guard in QA router | `app/routers/qa.py` | `MAX_QUESTION_CHARS = 2000`, HTTP 400 |
| Label truncation in Compare router | `app/routers/compare.py` | Runtime `[:100]` slice on `label_a`/`label_b` |

---

## Remaining Sub-Tasks

### ST-1 — Harden CORS Configuration

**Intent**
`allow_methods=["*"]` and `allow_headers=["*"]` are both overly broad.
Wildcard methods enable `PUT`, `DELETE`, `PATCH` cross-origin — none of which
the frontend uses. Wildcard headers allow arbitrary request headers (including
`Authorization`) and prevent browser preflight caching.
Lock both to the exact set the frontend needs.

**Expected Outcomes**
- `allow_methods` is `["GET", "POST"]`.
- `allow_headers` is `["Content-Type", "Accept"]`.
- All existing API calls continue to work (every endpoint is GET or POST with
  JSON or multipart bodies).

**Todo List**
1. In `app/main.py`, change `allow_methods=["*"]` → `allow_methods=["GET", "POST"]`.
2. Change `allow_headers=["*"]` → `allow_headers=["Content-Type", "Accept"]`.

**Relevant Context**
- `app/main.py:32-38` — `CORSMiddleware` registration block.

**Status:** `[x] done`

---

### ST-2 — Add Pydantic `max_length` Constraints to Schema Fields

**Intent**
The question length cap and label truncation are currently implemented at the
**router level** (runtime checks / slicing), but the Pydantic request schemas
have no corresponding constraints. This means:
- Invalid requests still reach router logic before being rejected.
- OpenAPI docs (`/docs`) advertise no field length limits, misleading API consumers.
- Pydantic validation errors (HTTP 422) — the idiomatic FastAPI pattern — are
  not used for these cases.

Adding `max_length` to the schema models is the correct, idiomatic fix.
The router-level guards can then be simplified or removed.

**Expected Outcomes**
- `QARequest.question` has `max_length=2000` in the Pydantic field.
- `CompareRequest.label_a` and `CompareRequest.label_b` each have `max_length=200`.
- Requests exceeding these limits receive HTTP 422 automatically from Pydantic
  before any router code runs.
- The manual length guard block in `qa.py` (lines 97-114) can be removed since
  Pydantic now enforces it.
- The runtime `[:100]` truncation in `compare.py` (lines 53-55) can be removed
  since invalid inputs are now rejected at the schema boundary instead of silently
  truncated.

**Todo List**
1. In `app/models/schemas.py`, add `max_length=2000` to the `question` field
   of `QARequest`.
2. Add `max_length=200` to the `label_a` field of `CompareRequest`.
3. Add `max_length=200` to the `label_b` field of `CompareRequest`.
4. In `app/routers/qa.py`, remove the manual `if len(question) > MAX_QUESTION_CHARS`
   block (lines 97-114) and the `MAX_QUESTION_CHARS` constant — now redundant.
5. In `app/routers/compare.py`, remove the `_MAX_LABEL_CHARS` constant and the
   `[:_MAX_LABEL_CHARS]` slices (lines 53-55) and restore `label_a = body.label_a`
   and `label_b = body.label_b` — Pydantic now rejects out-of-range values.

**Relevant Context**
- `app/models/schemas.py:164-170` — `CompareRequest.label_a` / `label_b` fields.
- `app/models/schemas.py:237` — `QARequest.question` field.
- `app/routers/qa.py:19,97-114` — router-level guard to remove.
- `app/routers/compare.py:53-55` — runtime truncation to remove.

**Status:** `[x] done`

---

### ST-3 — Rate-Limit the `/api/health` Endpoint

**Intent**
The `/api/health` endpoint performs no LLM call but has no rate limit. It is a
free probe target for fingerprinting the stack and high-frequency availability
polling. All other endpoints already have `@limiter.limit` decorators. Adding
a generous limit (60/minute) closes this gap without affecting legitimate
monitoring tools.

**Expected Outcomes**
- `GET /api/health` is decorated with `@limiter.limit("60/minute")`.
- The function signature accepts `request: Request` as required by `slowapi`.
- Requests exceeding 60/minute receive HTTP 429 with the standard error
  envelope, handled by the existing `RateLimitExceeded` handler.

**Todo List**
1. In `app/main.py`, add `request: Request` as the first parameter of `health()`.
2. Add the `@limiter.limit("60/minute")` decorator directly above `health()`.

**Relevant Context**
- `app/main.py:107-110` — current `health()` definition (no decorator, no
  `Request` param).
- `app/main.py:70-79` — existing `RateLimitExceeded` handler (already handles
  the 429 response).
- `app/limiter.py` — shared `limiter` instance (already imported in `main.py`).

**Status:** `[x] done`

---

### ST-4 — Eliminate Lazy-Init Race in Anthropic Client

**Intent**
Although the client was upgraded from `anthropic.Anthropic` to
`anthropic.AsyncAnthropic`, the lazy singleton pattern is unchanged:

```python
_client: anthropic.AsyncAnthropic | None = None

def _get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:          # ← race window still exists
        _client = anthropic.AsyncAnthropic(...)
    return _client
```

Two coroutines running concurrently on a cold start can both observe
`_client is None` and each create an `AsyncAnthropic` instance. The extra
instance wastes an HTTP connection pool. Since `app/config.py` already
validates `ANTHROPIC_API_KEY` at import time (raises `RuntimeError` if absent),
there is no reason to defer client creation.

Eager module-level initialisation is simpler, race-free, and fails fast
if the SDK rejects the configuration.

**Expected Outcomes**
- `_client` is initialised once at module load, not on first call.
- The `_get_client()` function and the `None` sentinel are removed.
- `generate_structured` uses `_client` directly instead of calling `_get_client()`.
- All existing tests continue to pass (they mock `generate_structured` directly).

**Todo List**
1. In `app/services/anthropic_client.py`, remove the `_client: ... | None = None`
   declaration and the entire `_get_client()` function.
2. Add a module-level eager assignment immediately after the constants block:
   ```python
   _client = anthropic.AsyncAnthropic(
       api_key=settings.anthropic_api_key,
       base_url=settings.anthropic_base_url,
       timeout=_TIMEOUT_SECONDS,
   )
   ```
3. In `generate_structured`, remove the `client = _get_client()` line and replace
   all uses of `client` with `_client`.

**Relevant Context**
- `app/services/anthropic_client.py:79-90` — lazy singleton block to replace.
- `app/services/anthropic_client.py:126` — `client = _get_client()` call site.
- `app/services/anthropic_client.py:161` — `client.messages.create` → `_client.messages.create`.
- `app/config.py:21-25` — `Settings.__init__` raises `RuntimeError` on missing
  key — safe to initialise eagerly at import.

**Status:** `[x] done`

---

### ST-5 — Remove Redundant Character Count in PDF Extractor

**Intent**
After building `full_text = "\n\n".join(page_texts)`, the extractor immediately
computes `total_chars = sum(len(p) for p in page_texts)` — a second full
traversal of already-joined data. `len(full_text)` produces an equivalent
value for the `avg_chars_per_page` heuristic (the `"\n\n"` separators add
`2 * (page_count - 1)` chars, which is negligible relative to the 50-char
threshold). This one-line change eliminates redundant work on every PDF upload.

**Expected Outcomes**
- `total_chars = sum(len(p) for p in page_texts)` is replaced with
  `total_chars = len(full_text)`.
- The scanned-PDF detection heuristic continues to work identically.
- No other logic changes.

**Todo List**
1. In `app/services/pdf_extractor.py`, replace line 83:
   `total_chars = sum(len(p) for p in page_texts)`
   with:
   `total_chars = len(full_text)`

**Relevant Context**
- `app/services/pdf_extractor.py:82-84` — the three lines: join, count, average.

**Status:** `[x] done`

---

## Implementation Order

```
ST-1  Harden CORS                        (Security — 2 lines in main.py)
ST-2  Pydantic max_length on schema fields (Security — schema + router cleanup)
ST-3  Rate-limit /api/health              (Security — decorator + param)
ST-4  Eager AsyncAnthropic client init    (Efficiency — eliminate race)
ST-5  Remove redundant char count         (Efficiency — 1 line in pdf_extractor)
```

## Projected Score After All Sub-Tasks

| Criterion   | Before manual changes | After manual changes | After this plan |
|-------------|----------------------|---------------------|-----------------|
| Security    | 90                   | ~93                 | 97–100          |
| Efficiency  | 85                   | ~92                 | 96–99           |
| **Overall** | **94.25**            | **~95.5**           | **~98–99**      |
