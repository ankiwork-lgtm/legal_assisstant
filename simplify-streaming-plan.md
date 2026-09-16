# Simplify Streaming Plan

## Top-Level Overview

Change the existing Simplify request from a complete structured JSON response to a plain-text streaming response. The browser will read the response body incrementally and append escaped text into the existing Simplify result card, so users see the explanation as it is generated instead of waiting behind a spinner. The streamed result will not be written to localStorage, and Risks, Checklist, Q&A, Compare, and their existing caching behavior will remain unchanged.

## Sub-Tasks

### 1. Add plain-text streaming to the Simplify backend

- **Intent** — Make `POST /api/analyze/simplify` deliver model output progressively while preserving current input validation, rate limiting, and sanitized error behavior.
- **Expected Outcomes**
  - Valid Simplify requests receive a `text/plain` streaming response.
  - AI output is emitted as text chunks without requiring JSON/schema parsing.
  - Empty and oversized inputs still return the existing structured 400 error responses.
  - AI and unexpected failures retain the existing user-safe error mapping as far as the streaming response lifecycle permits.
- **Todo List**
  1. Add a streaming Anthropic client path that uses the configured model, prompt limits, timeout/retry conventions where compatible, and yields text chunks.
  2. Update the Simplify router to use a streaming response and a plain-language prompt suitable for free-form text rather than structured JSON.
  3. Remove the endpoint’s successful-response dependency on `SimplifyResponse` and `SIMPLIFY_SCHEMA`, while leaving shared schemas used elsewhere intact unless they are no longer referenced.
  4. Set the response media type and headers needed to avoid buffering and make incremental delivery observable by the browser.
  5. Add or update backend tests for response media type, chunked/plain-text content, validation errors, and AI failure behavior.
- **Relevant Context**
  - [`simplify_document()`](app/routers/simplify.py:32) currently awaits [`generate_structured()`](app/services/anthropic_client.py:77) and returns [`SimplifyResponse`](app/models/schemas.py:75).
  - [`build_simplify_prompt()`](app/services/prompts.py:81) currently targets structured output and includes the legal disclaimer.
  - [`http_error_response()`](app/utils/errors.py:61) is the existing shared error mapping.
  - [`tests/test_phase3_simplify.py`](tests/test_phase3_simplify.py:1) is coupled to the old JSON contract and needs to reflect the new endpoint contract.
- **Status** — [ ] pending

### 2. Stream and render Simplify text in the browser

- **Intent** — Replace the Simplify spinner-only wait with progressive escaped plain text in the current result card, without affecting the generic loading flow for other tabs.
- **Expected Outcomes**
  - Clicking Generate hides the generate row and starts displaying text in the existing `simplify-result` container as chunks arrive.
  - Streamed content is inserted as text, never interpreted as HTML.
  - The result remains visible after completion, and no streamed value is saved to localStorage.
  - Network/API errors display through the existing Simplify error area and restore retry behavior.
  - The spinner is not shown for Simplify while streaming; other tab spinners continue to work.
- **Todo List**
  1. Add a frontend API function that posts the existing `{ text }` payload and exposes the response body reader while retaining JSON error parsing for non-success responses.
  2. Add a Simplify-specific streaming handler rather than changing [`setupLazyTab()`](public/js/analyze.js:98), so Risks, Checklist, and other consumers remain unchanged.
  3. Create or clear a text result element in `simplify-result` and append decoded chunks using text-safe DOM APIs.
  4. Remove the Simplify call to [`saveResult()`](public/js/storage.js:64) and the structured [`renderSimplify()`](public/js/render.js:27) path for newly streamed responses; keep existing cached structured results behavior only if the implementation must support already-stored historical data, otherwise ensure no new streamed data is cached.
  5. Update frontend tests to cover request construction, incremental chunk consumption, escaped rendering expectations, completion state, and error/retry behavior.
- **Relevant Context**
  - [`public/js/api.js`](public/js/api.js:8) currently always calls `response.json()` through [`request()`](public/js/api.js:8).
  - [`init()`](public/js/analyze.js:126) currently routes Simplify through [`setupLazyTab()`](public/js/analyze.js:98), caches the result, and calls [`renderSimplify()`](public/js/render.js:27).
  - [`public/analyze.html`](public/analyze.html:62) contains the existing Simplify loading row, error region, and result container.
  - No current `ReadableStream`, `getReader`, SSE, or `EventSource` implementation exists in the project.

### 3. Validate the changed contract and user flow

- **Intent** — Confirm the endpoint and UI work together and that unrelated analysis flows do not regress.
- **Expected Outcomes**
  - Backend tests pass with the new plain-text streaming contract.
  - Frontend API tests pass with a stream-capable response mock.
  - Existing Risks, Checklist, Q&A, Compare, storage, and non-Simplify rendering tests remain green.
  - The final diff contains no new Simplify localStorage writes and no accidental changes to unrelated tabs.
- **Todo List**
  1. Run the focused backend Simplify tests.
  2. Run the focused frontend JavaScript tests.
  3. Run the repository’s broader available test, lint, typecheck, or formatting commands discovered from project configuration.
  4. Review the final diff for response-contract, escaping, spinner, caching, and retry requirements.
- **Relevant Context**
  - [`tests/js/test_api.js`](tests/js/test_api.js:102) currently assumes a JSON Simplify response.
  - [`tests/js/test_storage.js`](tests/js/test_storage.js:112) verifies generic Simplify storage behavior and should remain valid unless the requested contract explicitly requires removing the storage utility itself.
  - Existing modified files in the workspace include [`public/analyze.html`](public/analyze.html), [`public/compare.html`](public/compare.html), [`public/js/storage.js`](public/js/storage.js), and [`tests/js/test_storage.js`](tests/js/test_storage.js); implementation should avoid overwriting unrelated work.
- **Status** — [ ] pending
