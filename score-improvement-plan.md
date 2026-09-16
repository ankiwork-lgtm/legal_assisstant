# LegalLens AI — Score Improvement Plan

## Overview

The evaluation report scored LegalLens AI at **82/100** across five criteria:
Code Quality (88), Security (80), Efficiency (78), Testing (85), Accessibility (75).

This plan closes every identified gap in a single, ordered set of sub-tasks.
Sub-tasks are grouped by impact tier so the highest-value work ships first.

---

## Sub-Tasks

### ST-1 — Pin Dependency Versions in `requirements.txt`

**Impact:** Code Quality (High)

**Intent**
Unpinned dependencies mean any future `pip install` can silently pick up a
breaking version. Pinning guarantees reproducible builds across local dev, CI,
and Vercel cold-starts.

**Expected Outcomes**
- `requirements.txt` lists every package with an exact or minimum-pinned version.
- A fresh `pip install -r requirements.txt` installs the same set of packages
  as the current working environment.

**Todo List**
1. Run `pip freeze` (or inspect known-good versions) to capture the current
   working versions of all 7 runtime packages.
2. Update `requirements.txt` with pinned versions using `==` specifiers for
   exact reproducibility.

**Relevant Context**
- File: `requirements.txt` — currently 7 unpinned packages.

**Status:** `[x] complete`

---

### ST-2 — Add Rate Limiting to Analyze Endpoints

**Impact:** Security (High)

**Intent**
All five `/api/analyze/*` endpoints (simplify, risks, checklist, compare, qa)
accept arbitrary text and forward it to the paid Anthropic API. Without
per-IP throttling, a single caller can exhaust the API quota or inflate costs.
`slowapi` provides an in-process rate limiter that works on Vercel with no
external state store.

**Expected Outcomes**
- `slowapi` added to `requirements.txt`.
- A `Limiter` instance is created in `app/main.py` and attached to the FastAPI
  app.
- Each of the five analyze routers is decorated so that each IP is limited to
  a sensible number of requests per minute (e.g. 20 req/min).
- Requests exceeding the limit receive HTTP 429 with the standard error
  envelope `{"error": {"code": "RATE_LIMITED", "message": "..."}}`
- Tests added to verify that a 429 is returned when the limit is hit.

**Todo List**
1. Add `slowapi` to `requirements.txt`.
2. In `app/main.py`, create a `Limiter` keyed on client IP and register the
   `_rate_limit_exceeded_handler` on the app.
3. Decorate each of the five `async def` route handlers in their router files
   with `@limiter.limit("20/minute")`.
4. Add a `RateLimitExceeded` handler that returns the standard error envelope.
5. Write tests asserting that the 429 response body uses the standard error
   envelope shape.

**Relevant Context**
- `app/main.py:20` — FastAPI `app` creation and middleware registration point.
- `app/routers/simplify.py`, `risks.py`, `checklist.py`, `compare.py`, `qa.py`
  — the five route handlers that need the decorator.
- `app/models/schemas.py` — `ErrorDetail` / `ErrorResponse` for the 429 body.
- `app/utils/errors.py` — existing error-mapping pattern to follow.

**Status:** `[x] complete`

---

### ST-3 — Add Maximum Text-Length Guard to All Analyze Endpoints

**Impact:** Security (High) + Efficiency (Medium)

**Intent**
The pasted-text path in `documents.py` and every `/api/analyze/*` router
accept unbounded text. A single 10 MB text payload inflates the LLM prompt
to thousands of tokens, increases cost, and can cause timeout failures.
Capping at ~50,000 characters (≈ 12,000 tokens) covers full contracts while
rejecting unreasonable inputs.

**Expected Outcomes**
- A shared constant `MAX_TEXT_CHARS = 50_000` is defined (e.g. in
  `app/config.py` or a shared constants module).
- The pasted-text path in `app/routers/documents.py` rejects inputs exceeding
  this limit with HTTP 400 and error code `TEXT_TOO_LONG`.
- Each of the five analyze routers applies the same guard before calling the
  LLM service.
- The frontend (`public/js/upload.js`) shows a client-side warning when pasted
  text exceeds the limit before submitting.
- Tests verify the 400 response and correct error code.

**Todo List**
1. Add `MAX_TEXT_CHARS = 50_000` constant to `app/config.py` (or a new
   `app/constants.py`).
2. Add the length guard to the pasted-text path in `app/routers/documents.py`
   after the empty-text check, returning a `TEXT_TOO_LONG` error.
3. Add the same guard to each of the five analyze routers immediately after
   the empty-text check.
4. Update `public/js/upload.js` to show an inline error when `textarea` input
   exceeds the limit (mirror the existing file-size check pattern).
5. Write tests for the 400 response on the documents endpoint and at least one
   analyze endpoint.

**Relevant Context**
- `app/routers/documents.py:123–139` — pasted-text path; guards follow the
  pattern used for `EMPTY_TEXT`.
- `app/routers/risks.py:42–52` — example of existing empty-text guard to
  extend.
- `public/js/upload.js:140–146` — existing `MAX_FILE_SIZE` client-side check
  to mirror.

**Status:** `[x] complete`

---

### ST-4 — Unblock Async Event Loop in Anthropic Client

**Impact:** Efficiency (Medium)

**Intent**
`generate_structured` uses the synchronous Anthropic SDK and calls
`time.sleep(1.0)` for its retry delay. Because all FastAPI route handlers are
`async def`, this blocks the entire event loop on every retry, degrading
concurrency. Wrapping the sync call in `asyncio.to_thread` offloads the
blocking work to a thread pool without changing the SDK or adding a new
dependency.

**Expected Outcomes**
- `generate_structured` becomes `async def generate_structured(...)`.
- The `client.messages.create(...)` call is wrapped in `asyncio.to_thread(...)`.
- `time.sleep(1.0)` is replaced with `await asyncio.sleep(1.0)`.
- All five calling routers `await` the function.
- All existing tests continue to pass (the mock patches `generate_structured`
  directly, so no test changes are needed for the mock).

**Todo List**
1. In `app/services/anthropic_client.py`, make `generate_structured` an
   `async def` function.
2. Replace the `client.messages.create(...)` call with
   `await asyncio.to_thread(client.messages.create, ...)`.
3. Replace `time.sleep(1.0)` with `await asyncio.sleep(1.0)`.
4. In each of the five analyze routers, change `result = generate_structured(...)`
   to `result = await generate_structured(...)`.
5. Run the full test suite to confirm all 269 tests pass.

**Relevant Context**
- `app/services/anthropic_client.py:71` — `generate_structured` function.
- `app/services/anthropic_client.py:112` — sync `client.messages.create` call.
- `app/services/anthropic_client.py:153` — `time.sleep(1.0)` retry delay.
- `app/routers/simplify.py:55`, `risks.py:56`, `checklist.py:54`,
  `compare.py:69`, `qa.py:85` — the five call sites that need `await`.

**Status:** `[x] complete`

---

### ST-5 — Write Frontend JS Unit Tests (Plain Node.js)

**Impact:** Testing (Medium)

**Intent**
`storage.js` contains all client-side persistence logic and `api.js` contains
all fetch wrappers. Neither has automated tests. Plain Node.js test scripts
(no framework, no npm) can import these modules and assert their behaviour
without a browser or build step, closing the coverage gap.

**Expected Outcomes**
- A `tests/js/` directory is created.
- `tests/js/test_storage.js` tests: `saveDocument`, `getDocument`,
  `saveResult`, `getHistory` (sorting), `clearHistory`, and duplicate-ID
  deduplication.
- `tests/js/test_api.js` tests: that each exported function builds the correct
  `fetch` call (method, path, headers, body) using a minimal `fetch` mock.
- Scripts are runnable with `node tests/js/test_storage.js` and
  `node tests/js/test_api.js` and exit with code 0 on success, non-zero on
  failure.
- `README.md` updated with a "Frontend JS Tests" section describing how to
  run them.

**Todo List**
1. Create `tests/js/` directory.
2. Write `tests/js/test_storage.js` — mock `localStorage` using a plain
   in-memory object, import `storage.js` functions (adapt for Node `require`
   or use `--input-type=module`), and assert each function's behaviour.
3. Write `tests/js/test_api.js` — mock the global `fetch` and `window.location`
   objects, import `api.js`, call each exported function, and assert the
   correct URL, method, headers, and body were passed to `fetch`.
4. Add a "Run frontend tests" command to `README.md`.

**Relevant Context**
- `public/js/storage.js` — all exports: `saveDocument`, `getDocument`,
  `saveResult`, `getHistory`, `clearHistory`.
- `public/js/api.js` — all exports: `extractDocument`, `simplifyDocument`,
  `analyzeRisks`, `generateChecklist`, `compareDocuments`, `askQuestion`.
- `tests/` — existing Python test directory for structural reference.

**Status:** `[x] complete`

---

### ST-6 — Implement Arrow-Key Tab Navigation (WAI-ARIA Pattern)

**Impact:** Accessibility (Low)

**Intent**
The WAI-ARIA Tabs pattern requires that Left/Right arrow keys move focus
between tabs (with wrapping). This is a WCAG 2.1 success criterion 2.1.1
(keyboard) that keyboard-only users rely on. Both `index.html` (2 tabs) and
`analyze.html` (4 tabs) need the upgrade.

**Expected Outcomes**
- Pressing `ArrowRight` on any tab moves focus to the next tab (wrapping from
  last to first).
- Pressing `ArrowLeft` on any tab moves focus to the previous tab (wrapping
  from first to last).
- Arrow-key navigation only moves focus; it does not activate the tab (follows
  the "manual activation" model to avoid triggering LLM calls on every
  keypress).
- `Enter` or `Space` on a focused tab activates it (existing behaviour
  retained).
- Both `public/js/upload.js` (2-tab set) and the inline script in
  `public/analyze.html` (4-tab set) are updated.

**Todo List**
1. In `public/js/upload.js`, extend the existing `keydown` handler on
   `[tabFile, tabText]` to handle `ArrowRight` (focus next) and `ArrowLeft`
   (focus previous) with wrapping. Set `tabindex="-1"` on inactive tabs and
   `tabindex="0"` on the active tab so focus follows the ARIA roving-tabindex
   pattern.
2. In `public/analyze.html`, extend the existing inline `keydown` handler on
   the 4-tab set with the same `ArrowRight`/`ArrowLeft` logic.
3. Update the `activateTab` helper in both files to toggle `tabindex`
   attributes alongside `aria-selected`.

**Relevant Context**
- `public/js/upload.js:66–74` — existing Enter/Space handler for 2-tab set.
- `public/analyze.html:308–313` — existing Enter/Space handler for 4-tab set.
- WAI-ARIA Authoring Practices Guide — Tabs Pattern (manual activation model).

**Status:** `[x] complete`

---

### ST-7 — Expand `prefers-reduced-motion` Coverage in CSS

**Impact:** Accessibility (Low)

**Intent**
The existing `@media (prefers-reduced-motion: reduce)` block (lines 562–572)
correctly disables the spinner animation and the toast transition. However,
ten other `transition` properties on buttons, inputs, links, tabs, drop zones,
and focus rings are not suppressed for users who prefer reduced motion.

**Expected Outcomes**
- The `@media (prefers-reduced-motion: reduce)` block in `styles.css` is
  expanded to set `transition: none` on all elements that carry a CSS
  `transition` property.
- The existing spinner and toast rules within that block are retained.
- The existing spinner animation and toast fade behaviour continue to work for
  users who have not set the preference.

**Todo List**
1. Identify all selectors in `styles.css` that use the `transition` property
   (lines 207, 294, 390, 481, 627, 662, 689, 752, 896 and any others found
   by grep).
2. Add `transition: none` overrides for every identified selector inside the
   existing `@media (prefers-reduced-motion: reduce)` block at line 562.

**Relevant Context**
- `public/css/styles.css:562–572` — existing reduced-motion block to extend.
- Transition lines found by grep: 207, 294, 390, 481, 570, 627, 662, 689,
  752, 896.

**Status:** `[x] complete`

---

### ST-8 — Extract Inline Styles from `analyze.html` into `styles.css`

**Impact:** Code Quality (Low)

**Intent**
`analyze.html` contains an inline `<style>` block with rules for
`.disclaimer-inline`, `.qa-input-row`, `.doc-meta`, `.tab-panel`,
`.panel-inner`, `.generate-row`, `.loading-row`, `.error-msg`, `.result-area`,
and an `@media` breakpoint. These duplicate the stylesheet's design system
(using `var(--color-*)` tokens) but live outside it, making the codebase
harder to maintain and increasing the risk of divergence.

**Expected Outcomes**
- All rules from the inline `<style>` block in `analyze.html` are moved to
  `public/css/styles.css` under a clearly commented section.
- The `<style>` block is removed from `analyze.html`.
- Visual appearance is unchanged.

**Todo List**
1. Read the full inline `<style>` block in `analyze.html` (lines 11–129).
2. Append the extracted rules to `public/css/styles.css` under a new
   `/* ── analyze.html page-specific styles ── */` comment section.
3. Remove the `<style>...</style>` block from `analyze.html`.
4. Visually verify the page renders identically.

**Relevant Context**
- `public/analyze.html:11–129` — the inline `<style>` block to remove.
- `public/css/styles.css` — target file; append after the last existing rule.

**Status:** `[x] complete`

---

## Implementation Order

```
ST-1  Pin dependencies            (Code Quality, quick win)
ST-2  Rate limiting               (Security, High Impact)
ST-3  Text-length cap             (Security + Efficiency, High Impact)
ST-4  Async Anthropic client      (Efficiency, Medium Impact)
ST-5  Frontend JS tests           (Testing, Medium Impact)
ST-6  Arrow-key tab nav           (Accessibility, Low Impact)
ST-7  Reduced-motion CSS          (Accessibility, Low Impact)
ST-8  Extract inline styles       (Code Quality, Low Impact)
```

## Score Projection After All Sub-Tasks

| Criterion       | Current | Projected |
|-----------------|---------|-----------|
| Code Quality    | 88      | 95        |
| Security        | 80      | 93        |
| Efficiency      | 78      | 88        |
| Testing         | 85      | 92        |
| Accessibility   | 75      | 88        |
| **Overall**     | **82**  | **~91**   |
