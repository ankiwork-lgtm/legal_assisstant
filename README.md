# LegalLens AI

A GenAI-powered web application that helps non-lawyers understand, compare, and navigate legal documents using Anthropic Claude.

> ⚠️ **LegalLens AI provides legal information only — not legal advice.** Outputs do not constitute legal counsel and do not create an attorney–client relationship. Always consult a qualified attorney before making decisions with legal consequences.

---

## Features

| Feature | Endpoint | Description |
|---|---|---|
| Document Ingestion | `POST /api/documents/extract` | Upload a PDF or paste text; returns extracted text + metadata |
| Plain-Language Simplification | `POST /api/analyze/simplify` | Translates dense legal text into plain English by section |
| Risk & Clause Highlighting | `POST /api/analyze/risks` | Flags risky clauses with severity (high/medium/low/info) and grouped by category |
| Checklist Generator | `POST /api/analyze/checklist` | Produces actionable "ask a lawyer" and "verify yourself" checklists |
| Document Comparison | `POST /api/analyze/compare` | Side-by-side diff of two documents, highlighting material differences |
| Document Q&A | `POST /api/analyze/qa` | Grounded question-answering with citation; never fabricates answers |

---

## Tech Stack

- **Backend:** Python 3.12, FastAPI, Uvicorn
- **LLM:** Anthropic Claude (`claude-haiku-4-5`) via `anthropic` SDK
- **PDF extraction:** `pypdf` (pure-Python, no system deps)
- **Rate limiting:** `slowapi` (per-IP, 20 req/min on analyze endpoints; 60 req/min on health)
- **Frontend:** Static HTML5 + CSS3 + vanilla JS (no build step)
- **Client persistence:** `localStorage` only — no server-side storage
- **Deployment:** Vercel (Python ASGI function + static files)

---

## Local Development

### 1. Prerequisites

- Python 3.12+
- An Anthropic API key (set via `ANTHROPIC_API_KEY`)

### 2. Install dependencies

For production only:
```bash
python -m pip install -r requirements.txt
```

For development and testing (includes pytest and coverage tools):
```bash
python -m pip install -r requirements-dev.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env and set your ANTHROPIC_API_KEY
```

`.env.example`:
```
ANTHROPIC_API_KEY=                                        # Required — your Anthropic API key
ANTHROPIC_MODEL=claude-haiku-4-5                          # Model to use
CORS_ORIGIN=http://localhost:8000                          # Dev only — change for production
```

Optional environment variables:

| Variable | Default | Description |
|---|---|---|
| `LOG_LEVEL` | `INFO` | Log verbosity. Set to `DEBUG` to see prompt snippets and raw AI payloads. |

### 4. Run the server

```bash
uvicorn app.main:app --reload
```

The API is available at `http://localhost:8000/api/`.  
The frontend is served from `public/` — open `http://localhost:8000/` in your browser  
(or open `public/index.html` directly via a local static server).

### 5. Run backend tests

```bash
python -m pytest -v
```

All tests should pass. Tests mock the Anthropic API — no API key is needed. The root `conftest.py` injects a dummy `ANTHROPIC_API_KEY` so `app.config` loads cleanly during test collection. A `tests/conftest.py` resets the in-memory rate-limit counters before every test so 429s don't bleed between test cases.

### 6. Run frontend JS tests

No npm, no build step — plain Node.js (v18+) only.

```bash
node tests/js/test_storage.js
node tests/js/test_api.js
```

Both scripts exit **0** on success and print a per-assertion pass/fail summary.

| Test file | What it covers |
|---|---|
| `tests/js/test_storage.js` | `saveDocument`, `getDocument`, `saveResult` (all kinds including `qa` append), `getHistory` (newest-first sort), `clearHistory`, duplicate-ID deduplication, implicit-entry creation |
| `tests/js/test_api.js` | Every exported function (`extractDocument`, `simplifyDocument`, `analyzeRisks`, `generateChecklist`, `compareDocuments`, `askQuestion`) — asserts correct URL, HTTP method, headers, and request body; also checks that non-`ok` responses throw, and that `MAX_FILE_SIZE` is exported correctly |

The tests mock `localStorage` and `fetch` as in-memory stubs — no browser and no network connection required.

---

## Security

The application enforces several security controls:

- **Security headers** — every response includes `Content-Security-Policy`, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Strict-Transport-Security`, `Referrer-Policy`, `Permissions-Policy`, and `X-XSS-Protection: 0`.
- **Rate limiting** — powered by `slowapi`; analyze endpoints are capped at **20 requests/minute per IP**; the health endpoint allows 60/minute. Exceeding the limit returns HTTP 429 with `{"error": {"code": "RATE_LIMITED", "message": "..."}}`.
- **Input size cap** — all text inputs are limited to **50,000 characters**. Requests exceeding this return HTTP 400 with `{"error": {"code": "TEXT_TOO_LONG", "message": "..."}}`.
- **CORS** — locked to the single origin set in `CORS_ORIGIN`; defaults to `http://localhost:8000` for local dev.

---

## Deployment to Vercel

### Step 1 — Install Vercel CLI (optional but convenient)

```bash
npm i -g vercel
```

### Step 2 — Set environment variables in Vercel

In the Vercel dashboard → **Project Settings → Environment Variables**, add:

| Variable | Value |
|---|---|
| `ANTHROPIC_API_KEY` | Your Anthropic API key |
| `ANTHROPIC_MODEL` | `claude-haiku-4-5` |
| `CORS_ORIGIN` | Your deployed frontend URL, e.g. `https://legallens-ai.vercel.app` |
| `LOG_LEVEL` | `INFO` (or `DEBUG` for verbose logs) |

> ⚠️ `ANTHROPIC_API_KEY` is a **secret** — never expose it to the frontend or commit it to source control.

### Step 3 — Deploy

```bash
vercel --prod
```

Or push to your connected GitHub repo and Vercel auto-deploys.

### Step 4 — Verify health endpoint

```
GET https://<your-project>.vercel.app/api/health
→ {"status": "ok"}
```

### Step 5 — End-to-end smoke test

Work through this checklist manually after each deploy:

- [ ] Open `https://<your-project>.vercel.app/` — disclaimer banner visible
- [ ] Upload a PDF → extraction succeeds → redirected to `analyze.html`
- [ ] **Simplify tab** — click Generate, result appears within 20s, inline disclaimer visible
- [ ] **Risks tab** — click Generate, severity badges shown, no definitive legal verdicts
- [ ] **Checklist tab** — click Generate, two sections appear, checkboxes work
- [ ] **Ask tab** — type a question, answer cites clause, found_in_document shown correctly
- [ ] Navigate back to home — document appears in "Recent Documents" history
- [ ] Refresh browser — history still present
- [ ] Paste text for a second document on `compare.html` — comparison table renders
- [ ] Click "Clear History" — history gone, empty-state message shown

---

## Project Structure

```
legallens-ai/
├── api/
│   └── index.py                  # Vercel ASGI entry point
├── app/
│   ├── main.py                   # FastAPI app, CORS, security headers, router mounts
│   ├── config.py                 # Env var loading (ANTHROPIC_API_KEY, ANTHROPIC_BASE_URL,
│   │                             #   ANTHROPIC_MODEL, CORS_ORIGIN); MAX_TEXT_CHARS = 50,000
│   ├── limiter.py                # Shared slowapi Limiter instance (avoids circular imports)
│   ├── models/
│   │   └── schemas.py            # Pydantic request/response models
│   ├── routers/
│   │   ├── documents.py          # POST /api/documents/extract
│   │   ├── simplify.py           # POST /api/analyze/simplify
│   │   ├── risks.py              # POST /api/analyze/risks
│   │   ├── checklist.py          # POST /api/analyze/checklist
│   │   ├── compare.py            # POST /api/analyze/compare
│   │   └── qa.py                 # POST /api/analyze/qa
│   ├── services/
│   │   ├── anthropic_client.py   # anthropic SDK wrapper (structured JSON, timeout, retry)
│   │   ├── pdf_extractor.py      # pypdf-based in-memory extraction
│   │   └── prompts.py            # Prompt templates + JSON schemas for all features
│   └── utils/
│       ├── errors.py             # Exception → HTTP status mapping
│       ├── logger.py             # Centralised logging (legallens.* namespace, LOG_LEVEL)
│       └── validation.py        # Shared input-length guard (check_text_length)
├── public/
│   ├── index.html                # Upload / home page
│   ├── analyze.html              # Tabbed analysis workspace
│   ├── compare.html              # Two-document comparison workspace
│   ├── feature-gap-analysis.html # Internal feature-gap tracking page
│   ├── css/styles.css            # All styles (layout, severity colors, toast, spinner)
│   └── js/
│       ├── api.js                # Fetch wrappers for all backend endpoints
│       ├── storage.js            # localStorage helpers (FR-7)
│       ├── toast.js              # Error toast utility
│       ├── upload.js             # Upload/paste handling + session history
│       ├── analyze.js            # Analysis workspace controller
│       ├── compare.js            # Comparison workspace controller
│       └── render.js             # JSON → DOM renderers for all 5 features
├── scripts/
│   └── generate_sample_pdfs.py  # Developer utility — generates sample PDFs for manual testing
├── tests/
│   ├── conftest.py               # Resets rate-limit counters before every test
│   ├── fixtures/                 # Shared test fixture files
│   ├── test_misc.py              # Health endpoint, MIME rejection, compare text-length limits
│   ├── test_pdf_extractor.py
│   ├── test_phase2.py
│   ├── test_phase3_simplify.py
│   ├── test_phase4_risks.py
│   ├── test_phase5_checklist.py
│   ├── test_phase6_compare.py
│   ├── test_phase7_qa.py
│   └── test_rate_limiting.py     # 429 behaviour on all analyze endpoints
│   └── js/
│       ├── test_storage.js
│       └── test_api.js
├── conftest.py                   # Sets dummy ANTHROPIC_API_KEY for test collection
├── requirements.txt              # Runtime dependencies
├── requirements-dev.txt          # Dev/test dependencies (extends requirements.txt)
├── vercel.json
└── .env.example
```

---

## API Reference

Base path: `/api`

| Method | Path | Request | Response (200) |
|---|---|---|---|
| GET | `/health` | — | `{status: "ok"}` |
| POST | `/documents/extract` | `multipart/form-data`: `file` (PDF) **or** `text` field | `{text, word_count, page_count}` |
| POST | `/analyze/simplify` | `{text: str}` | `{overview, sections[{heading, original_excerpt_ref, plain_language}]}` |
| POST | `/analyze/risks` | `{text: str}` | `{categories[{category, items[{clause_ref, severity, explanation}]}]}` |
| POST | `/analyze/checklist` | `{text: str}` | `{ask_lawyer[], verify_yourself[]}` |
| POST | `/analyze/compare` | `{doc_a, doc_b, label_a?, label_b?}` | `{shared_topics[], only_in_a[], only_in_b[]}` |
| POST | `/analyze/qa` | `{text, question, history?}` | `{answer, found_in_document, supporting_clause_ref}` |

All errors return: `{"error": {"code": str, "message": str}}`

### Error codes

| Code | HTTP | Description |
|---|---|---|
| `RATE_LIMITED` | 429 | Per-IP request limit exceeded |
| `TEXT_TOO_LONG` | 400 | Input text exceeds 50,000 characters |
| `INVALID_FILE_TYPE` | 400 | Uploaded file is not a PDF |

---

## Legal Disclaimer

**LegalLens AI is an informational tool only.** It does not provide legal advice, does not create an attorney–client relationship, and should never be relied upon as a substitute for advice from a licensed attorney. All AI-generated outputs are provided "as-is" for informational and educational purposes. Users are solely responsible for decisions made based on information provided by this tool.
