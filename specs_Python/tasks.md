# LegalLens AI — Implementation Tasks

Each task references the requirement(s) it satisfies (`FR-#`) from `requirements.md`.
Suggested execution order for a hackathon timeline is top to bottom.

## Phase 0 — Project Setup
- [x] 0.1 Scaffold repo structure as described in `design.md` §3
- [x] 0.2 `requirements.txt`: `fastapi`, `uvicorn`, `google-genai`, `pypdf`,
      `python-multipart`, `pydantic`
- [x] 0.3 `.env.example` with `GEMINI_API_KEY=`
- [x] 0.4 `app/config.py` — load env vars, raise clear startup error if
      `GEMINI_API_KEY` missing
- [x] 0.5 `app/main.py` — FastAPI app, CORS middleware, mount routers, `/api/health`
- [x] 0.6 `api/index.py` — re-export `app` for Vercel
- [x] 0.7 `vercel.json` per `design.md` §7
- [x] 0.8 Verify local dev: `uvicorn app.main:app --reload`

## Phase 1 — Document Ingestion (FR-1)
- [x] 1.1 `app/services/pdf_extractor.py`: extract text per page from in-memory bytes
- [x] 1.2 Heuristic to detect near-empty extraction → scanned-PDF error path
- [x] 1.3 `POST /api/documents/extract` router: accept `multipart/form-data` file OR
      JSON `{text}`; validate size limit; return `{text, word_count, page_count}`
- [x] 1.4 Pydantic response/error models for this endpoint
- [x] 1.5 Unit tests: valid PDF, corrupt PDF, oversized file, pasted text path

## Phase 2 — Gemini Integration Core
- [x] 2.1 `app/services/gemini_client.py`: `generate_structured(prompt, schema)`
      wrapper using `google-genai`, model `gemini-3.6-flash`
- [x] 2.2 Timeout + single retry + typed `GeminiServiceError`
- [x] 2.3 `app/utils/errors.py`: central exception → HTTP status mapping
- [x] 2.4 Shared "informational, not legal advice" instruction block reused by all
      prompt templates (FR-8)
- [x] 2.5 `app/services/prompts.py`: base prompt-builder utility

## Phase 3 — Feature: Simplification (FR-2)
- [x] 3.1 Prompt template + JSON schema: `{overview, sections[]}`
- [x] 3.2 `POST /api/analyze/simplify` router
- [x] 3.3 Manual test: verify obligations/dates/amounts aren't dropped from output

## Phase 4 — Feature: Risk & Clause Highlighting (FR-5)
- [x] 4.1 Prompt template + JSON schema: `{categories:[{category, items:[{clause_ref,
      severity, explanation}]}]}`, severity enum `high|medium|low|info`
- [x] 4.2 `POST /api/analyze/risks` router
- [x] 4.3 Verify phrasing avoids definitive verdicts ("worth reviewing because…")

## Phase 5 — Feature: Checklist Generator (FR-6)
- [x] 5.1 Prompt template + JSON schema: `{ask_lawyer[], verify_yourself[]}`
- [x] 5.2 `POST /api/analyze/checklist` router

## Phase 6 — Feature: Document Comparison (FR-3)
- [x] 6.1 Prompt template + JSON schema: `{shared_topics[], only_in_a[], only_in_b[]}`
- [x] 6.2 `POST /api/analyze/compare` router (accepts `doc_a`, `doc_b`, optional labels)
- [x] 6.3 Handle "different document types" case gracefully (still returns best-effort
      comparison + a note)

## Phase 7 — Feature: Document Q&A (FR-4)
- [x] 7.1 Prompt template + JSON schema: `{answer, found_in_document, supporting_clause_ref}`
- [x] 7.2 `POST /api/analyze/qa` router — accepts optional `history[]` for follow-ups
- [x] 7.3 Verify "not found in document" path doesn't fabricate an answer

## Phase 8 — Frontend: Shared Shell
- [x] 8.1 `public/css/styles.css` — base layout, disclaimer banner styling
- [x] 8.2 `public/js/api.js` — fetch wrappers for every backend endpoint
- [x] 8.3 `public/js/storage.js` — `saveResult`, `getHistory`, `clearHistory` (FR-7)
- [x] 8.4 Persistent disclaimer banner component included on every page (FR-8)

## Phase 9 — Frontend: Upload & Home (FR-1, FR-7)
- [x] 9.1 `public/index.html` — upload/paste UI, drag-and-drop
- [x] 9.2 `public/js/upload.js` — handles file vs. pasted text, calls `/documents/extract`
- [x] 9.3 Session history list rendered from `localStorage` on load

## Phase 10 — Frontend: Analyze Workspace (FR-2, FR-4, FR-5, FR-6)
- [x] 10.1 `public/analyze.html` — tabs: Simplify / Risks / Checklist / Ask
- [x] 10.2 `public/js/render.js` — render each JSON shape into readable DOM (severity
      color-coding for risks, checkbox list for checklist, chat thread for Q&A)
- [x] 10.3 Lazy-load each tab's result on first click; cache to `localStorage`
- [x] 10.4 Inline "not legal advice" reminder near every AI output block (FR-8)

## Phase 11 — Frontend: Compare Workspace (FR-3)
- [x] 11.1 `public/compare.html` — two-document upload + labels
- [x] 11.2 Render `shared_topics` as a diff-style table; `only_in_a`/`only_in_b` as lists

## Phase 12 — Hardening & Polish
- [x] 12.1 Central error toast/banner on frontend for all API error shapes
- [x] 12.2 Loading states for all async calls (Gemini latency ~5–20s)
- [x] 12.3 Accessibility pass: semantic HTML, labels, contrast, keyboard nav
- [x] 12.4 Upload size limit enforced client- and server-side
- [x] 12.5 CORS locked to deployed origin before final deploy

## Phase 13 — Deployment
- [ ] 13.1 Set `GEMINI_API_KEY` in Vercel project env vars  *(manual — set in Vercel dashboard → Project Settings → Environment Variables)*
- [ ] 13.2 Deploy, verify `/api/health`  *(manual — run `vercel --prod` or push to connected GitHub repo; then GET /api/health)*
- [ ] 13.3 End-to-end manual click-through: upload PDF → simplify → risks → checklist
      → ask a question → paste second doc → compare → refresh browser → confirm
      history persists → clear history → confirm it's gone  *(manual — see smoke-test checklist in README.md)*

## Phase 14 — Demo Prep (hackathon-specific)
- [ ] 14.1 Prepare 2–3 sample documents (e.g., sample lease, sample freelance
      contract, sample ToS) for a smooth live demo
- [ ] 14.2 Script a 3–4 minute walkthrough hitting all 5 core use cases
- [ ] 14.3 One slide/README paragraph stating the "not legal advice" positioning clearly
