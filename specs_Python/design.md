# LegalLens AI — Technical Design

Companion to `requirements.md`. This document describes *how* the requirements are
implemented.

## 1. Architecture Overview

```
┌────────────────────────┐        HTTPS/JSON        ┌───────────────────────────┐
│   Static Frontend       │  ───────────────────────▶ │   FastAPI Backend          │
│   (HTML/CSS/vanilla JS) │  ◀─────────────────────── │   (Vercel Python Function) │
│   served from /public   │                            │   /api/*                  │
└──────────┬──────────────┘                            └────────────┬──────────────┘
           │                                                          │
           │ localStorage                                            │ google-genai SDK
           ▼                                                          ▼
   Browser session history                              Gemini 3.6 Flash (gemini-3.6-flash)
   (documents, results — client only)                    Google AI API
```

Key principle: **the backend is a stateless "smart proxy" to Gemini.** It never writes
document content to disk/DB. All persistence that exists (session history) lives in the
browser via `localStorage`, exactly per FR-7.

## 2. Tech Stack

| Layer | Choice |
|---|---|
| Backend framework | Python 3.12, FastAPI |
| ASGI server (local dev) | uvicorn |
| Deployment | Vercel (Python runtime, ASGI serverless function) |
| LLM | Gemini 3.6 Flash (`gemini-3.6-flash`) via `google-genai` SDK |
| PDF text extraction | `pypdf` (pure-Python, no system deps — required for serverless) |
| Frontend | Static HTML5 + CSS3 + vanilla JS (fetch API), no build step |
| Client-side persistence | `localStorage` |
| Validation | Pydantic v2 models |

## 3. Repository Structure

```
legallens-ai/
├── api/
│   └── index.py              # FastAPI app entry point (Vercel picks this up)
├── app/
│   ├── __init__.py
│   ├── main.py                # FastAPI app factory, CORS, routers mounted here
│   ├── config.py              # env var loading (GEMINI_API_KEY, limits)
│   ├── models/
│   │   └── schemas.py         # Pydantic request/response models
│   ├── routers/
│   │   ├── documents.py       # /api/documents/extract
│   │   ├── simplify.py        # /api/analyze/simplify
│   │   ├── risks.py           # /api/analyze/risks
│   │   ├── checklist.py       # /api/analyze/checklist
│   │   ├── compare.py         # /api/analyze/compare
│   │   └── qa.py              # /api/analyze/qa
│   ├── services/
│   │   ├── gemini_client.py   # thin wrapper around google-genai
│   │   ├── pdf_extractor.py   # pypdf-based extraction
│   │   └── prompts.py         # prompt templates + JSON schemas per feature
│   └── utils/
│       └── errors.py          # shared exception → HTTP error mapping
├── public/
│   ├── index.html             # landing / upload page
│   ├── analyze.html           # results workspace (tabs: simplify/risk/qa/checklist)
│   ├── compare.html           # comparison workspace
│   ├── css/
│   │   └── styles.css
│   └── js/
│       ├── api.js             # fetch() wrappers for backend endpoints
│       ├── storage.js         # localStorage read/write helpers (session history)
│       ├── upload.js          # drag/drop + paste handling
│       └── render.js          # renders LLM JSON results into DOM
├── requirements.txt
├── vercel.json
└── .env.example
```

## 4. Backend Design

### 4.1 App entry (`api/index.py`)
Vercel's Python runtime supports ASGI apps directly. `api/index.py` imports and
re-exports the FastAPI `app` object from `app/main.py`. `vercel.json` routes all
`/api/*` traffic to this function; everything else is served as static files from
`/public`.

### 4.2 Gemini client wrapper (`app/services/gemini_client.py`)
A single wrapper function `generate_structured(prompt: str, schema: dict) -> dict`:
- Uses `google-genai` Python SDK, `client.models.generate_content(...)`.
- Model: `gemini-3.6-flash`.
- Sets `response_mime_type="application/json"` and `response_schema=<pydantic-derived
  schema>` so Gemini returns **structured JSON**, not free text — this removes the need
  for brittle regex parsing on the backend and matches the "grouped/categorized" shape
  required by FR-3, FR-5, FR-6.
- Wraps calls with a timeout (25s) and one retry on transient failure, then raises a
  typed `GeminiServiceError` that routers convert to a clean HTTP 502 with a friendly
  message (NFR: Resilience).
- Because Gemini 3.6 Flash supports a 1M-token context window, the **whole extracted
  document text is passed directly in the prompt** — no chunking/embedding/vector DB is
  needed for the document sizes expected in this hackathon (contracts, leases, ToS
  typically well under 100k tokens). This is a deliberate simplicity trade-off.

### 4.3 Prompt templates (`app/services/prompts.py`)
Each feature gets its own system-style instruction + JSON schema:

- **Simplify:** instructs the model to produce `{overview: str, sections: [{heading,
  original_excerpt_ref, plain_language}]}`.
- **Risk analysis:** `{categories: [{category, items: [{clause_ref, severity,
  explanation}]}]}` with severity constrained to an enum (`high|medium|low|info`).
- **Checklist:** `{ask_lawyer: [str], verify_yourself: [str]}`.
- **Compare:** `{shared_topics: [{topic, doc_a_position, doc_b_position, materially_different, why_it_matters}], only_in_a: [str], only_in_b: [str]}`.
- **Q&A:** `{answer: str, found_in_document: bool, supporting_clause_ref: str|null}` —
  `found_in_document=false` is how FR-4's "don't fabricate" requirement is enforced
  programmatically, not just by prompt wording.

Every prompt template includes a shared boilerplate clause (injected once, not
repeated per feature) instructing the model: *"You provide legal information, not legal
advice. Do not tell the user what to decide. If asked for a definitive legal
recommendation, explain the relevant facts from the document and recommend consulting a
licensed attorney."* This operationalizes FR-8.

### 4.4 PDF extraction (`app/services/pdf_extractor.py`)
- `pypdf.PdfReader` reads the uploaded bytes in-memory (no temp files, no disk writes —
  keeps the "no persistence" guarantee simple).
- Extracts text per page, joins with page-break markers so clause references (FR-4,
  FR-5) can mention approximate page numbers.
- If total extracted text length is near-zero relative to page count, the file is
  flagged as a likely scanned/image PDF and FR-1's specific error is returned instead
  of an empty result.

### 4.5 Error handling (`app/utils/errors.py`)
Central exception handler maps: invalid file → 400, file too large → 413, Gemini
timeout/error → 502, unexpected → 500 with generic message (no stack traces leaked).

## 5. API Contract

Base path: `/api`

| Method | Path | Request body | Response body (200) |
|---|---|---|---|
| POST | `/documents/extract` | `multipart/form-data`: `file` (PDF) **or** JSON `{text}` | `{document_id, text, word_count, page_count}` |
| POST | `/analyze/simplify` | `{text: str}` | `{overview, sections[]}` |
| POST | `/analyze/risks` | `{text: str}` | `{categories[]}` |
| POST | `/analyze/checklist` | `{text: str}` | `{ask_lawyer[], verify_yourself[]}` |
| POST | `/analyze/compare` | `{doc_a: str, doc_b: str, label_a?: str, label_b?: str}` | `{shared_topics[], only_in_a[], only_in_b[]}` |
| POST | `/analyze/qa` | `{text: str, question: str, history?: [{role, content}]}` | `{answer, found_in_document, supporting_clause_ref}` |
| GET | `/health` | — | `{status: "ok"}` |

`document_id` from `/documents/extract` is a client-side-generated UUID (or returned by
the backend as an opaque echo) used only as a `localStorage` key — the backend does not
retain it.

All error responses follow: `{"error": {"code": str, "message": str}}`.

## 6. Frontend Design

### 6.1 Pages
- **`index.html`** — Upload/paste a document (or two, for compare mode); shows the
  persistent disclaimer banner (FR-8); lists session history read from `localStorage`.
- **`analyze.html`** — Tabbed workspace for a single document: Simplify / Risks /
  Checklist / Ask a Question. Each tab lazily calls its endpoint and caches the result
  into `localStorage` on success (FR-7).
- **`compare.html`** — Two-document upload + side-by-side comparison results view.

### 6.2 State management
No frameworks. `js/storage.js` exposes small helpers:
```
saveResult(documentId, kind, data)
getHistory()
clearHistory()
```
`kind` ∈ `{simplify, risks, checklist, compare, qa}`. Data model per history entry:
```json
{
  "id": "uuid",
  "label": "Freelance_Contract.pdf",
  "created_at": "iso8601",
  "results": { "simplify": {...}, "risks": {...}, "qa": [{"q":..,"a":..}] }
}
```
Document *text itself* is also cached in `localStorage` per entry so re-visiting a tab
doesn't require re-uploading — this is what makes the "no backend persistence" model
usable across tabs within one session.

### 6.3 UX flow for Q&A
The chat history sent to `/analyze/qa` is the client-held array from `localStorage`,
satisfying FR-4's follow-up-question requirement without any server-side session state.

## 7. Deployment on Vercel

`vercel.json`:
```json
{
  "builds": [
    { "src": "api/index.py", "use": "@vercel/python" },
    { "src": "public/**", "use": "@vercel/static" }
  ],
  "routes": [
    { "src": "/api/(.*)", "dest": "api/index.py" },
    { "src": "/(.*)", "dest": "public/$1" }
  ]
}
```
- `GEMINI_API_KEY` set as a Vercel **encrypted environment variable**, read via
  `app/config.py` (`os.environ["GEMINI_API_KEY"]`) — never sent to the client.
- `requirements.txt` pins `fastapi`, `google-genai`, `pypdf`, `python-multipart`.
- Function size/time limits: keep dependencies minimal (no heavy OCR/ML libs) to stay
  within Vercel's serverless function size and duration limits on the free tier.

## 8. Security & Privacy Considerations

- CORS restricted to the deployed origin.
- Upload size capped (e.g., 8–10 MB) to protect against abuse and Vercel payload limits.
- No document content is logged; only request metadata (endpoint, status, latency) may
  be logged for debugging.
- Because there is no auth, the app is explicitly a single-session demo tool, not a
  system for storing sensitive documents long-term — this is called out in the UI
  disclaimer text.

## 9. Testing Strategy (hackathon-scoped)

- Unit tests for `pdf_extractor.py` (valid PDF, empty/scanned PDF, corrupt file).
- Unit tests for prompt/schema builders (correct JSON schema shape per feature).
- Manual test matrix: upload PDF vs. paste text, single doc vs. two-doc compare,
  Gemini timeout simulated via mock, disclaimer visibility check.
- No E2E framework required for hackathon scope; manual click-through checklist instead
  (see `tasks.md`).
