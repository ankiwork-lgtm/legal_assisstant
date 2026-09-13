# Legal Assistant — Hackathon Build Plan (Spec-Driven)

## Top-Level Overview

Build a GenAI-powered legal assistant web app (**LexAid**) that makes legal information more accessible to everyday users — without replacing professional advice. The app is a **Next.js 14 (App Router)** project styled with **Tailwind CSS**, deployed on **Vercel**, and powered by **Google Gemini** (`gemini-2.0-flash`) via the `@google/generative-ai` SDK.

> **Note on model name:** `gemini-3.5-flash` is not a released model name. The closest high-quality, fast Gemini model available via the SDK is `gemini-2.0-flash`, which is used throughout.

> **Approach:** This plan follows **Spec-Driven Development**. Every sub-task references acceptance criteria (AC codes) defined in [`TECHNICAL_DESIGN.md`](./TECHNICAL_DESIGN.md). A sub-task is complete only when all referenced AC codes pass. Implementation decisions are driven by the spec, not by ad-hoc choices.

Four core features are exposed as distinct pages:
1. **Document Simplifier** (`FEAT-01`) — plain-English summary + key-clause extraction
2. **Contract Comparator** (`FEAT-02`) — side-by-side diff of two documents
3. **Q&A Chat** (`FEAT-03`) — multi-turn grounded chat about an uploaded document
4. **Lawyer Prep** (`FEAT-04`) — question checklist to bring to a legal professional

PDF uploads are parsed server-side using `pdf-parse` inside Next.js API Routes. No database or auth — all state is in-memory per session.

---

## How Sub-Tasks Are Verified

Each sub-task has a **Spec References** field listing the AC codes from `TECHNICAL_DESIGN.md` that must pass before the sub-task is marked done. After implementation, the implementor runs through each AC code and checks it off. Unverified AC codes = incomplete sub-task.

---

## Sub-Tasks

---

### Sub-Task 1 — Project Scaffold & Configuration

**Status:** `[x] done`

**Intent**
Bootstrap the Next.js 14 project with Tailwind CSS, install all required dependencies, and configure environment variables so every subsequent sub-task has a working foundation to build on.

**Spec References**
- `TC-01` through `TC-07` — all locked dependencies must be installed at correct versions
- `AC-CFG-01` — `serverExternalPackages: ['pdf-parse']` present in `next.config.ts`
- `AC-CFG-02` — `npm run build` completes with zero errors
- `AC-TW-02` — Tailwind `content` paths include `app/` and `components/`
- `AC-ENV-01` — `.env.example` exists and contains `GEMINI_API_KEY=`
- `AC-ENV-02` — `.env.local` listed in `.gitignore`
- `AC-BUILD-01` — `npm run build` exits with code 0
- `AC-DIR-01` (partial) — root-level config files exist

**Expected Outcomes**
- `package.json` with all dependencies present at specified version constraints
- `tailwind.config.ts` and `postcss.config.js` configured with correct content paths
- `next.config.ts` with `serverExternalPackages: ['pdf-parse']`
- `.env.example` with `GEMINI_API_KEY=your_key_here`
- `app/layout.tsx` with global Tailwind import and `<html lang="en"><body>` wrapper
- App runs locally with `npm run dev` without errors
- `npm run build` exits 0

**Todo List**
- [ ] Run `npx create-next-app@14 . --ts --tailwind --app --no-src-dir --import-alias "@/*"` in the workspace root
- [ ] Install runtime dependencies: `@google/generative-ai`, `pdf-parse`
- [ ] Install dev dependency: `@types/pdf-parse`
- [ ] Add `serverExternalPackages: ['pdf-parse']` to `next.config.ts` (see `TECHNICAL_DESIGN.md` Section 10.1)
- [ ] Add `primary` colour scale to `tailwind.config.ts` (see `TECHNICAL_DESIGN.md` Section 10.2)
- [ ] Create `.env.example` with exact content specified in `TECHNICAL_DESIGN.md` Section 10.4
- [ ] Confirm `.env.local` is in `.gitignore`
- [ ] Create `types/index.ts` with all shared type definitions from `TECHNICAL_DESIGN.md` Section 3
- [ ] Run `npm run build` — verify exit 0, zero TypeScript errors
- [ ] Run `tsc --noEmit` — verify zero errors

**Relevant Context**
- Workspace root: `c:\Users\AnkitGarg\OneDrive - IBM\Desktop\H2S\legal_assisstant`
- Vercel reads env vars from the dashboard — `.env.local` is never committed
- `pdf-parse` must be in `serverExternalPackages` to avoid webpack `fs` resolution errors
- All types in `types/index.ts` must be present before any other sub-task begins — they are shared across all components, routes, and utilities
- See `TECHNICAL_DESIGN.md` Section 3 for the complete `types/index.ts` content to copy verbatim

---

### Sub-Task 2 — Shared UI Components & Layout

**Status:** `[ ] pending`

**Intent**
Build the reusable UI building blocks and global layout that all four feature pages depend on. This sub-task must be complete before any feature page sub-task begins.

**Spec References**
- `AC-NAV-01` through `AC-NAV-04` — Navbar spec
- `AC-DISC-01` through `AC-DISC-03` — DisclaimerBanner spec
- `AC-FTI-01` through `AC-FTI-06` — FileOrTextInput spec
- `AC-RC-01` through `AC-RC-04` — ResultCard spec
- `AC-LS-01` through `AC-LS-04` — LoadingSpinner spec
- `AC-LAY-01` through `AC-LAY-03` — Root layout spec
- `AC-HOME-01` through `AC-HOME-03` — Home page spec
- `AC-DIR-02` — no `"use client"` in `lib/` (enforced from this sub-task onward)
- `UC-01` — disclaimer visible on every page

**Expected Outcomes**
- `app/layout.tsx` renders `<Navbar>` → `<DisclaimerBanner>` → `<main>{children}</main>` in that order
- `components/Navbar.tsx` — 5 nav links, active state, `bg-slate-900 text-white`
- `components/DisclaimerBanner.tsx` — exact disclaimer text, `bg-amber-50` styling
- `components/FileOrTextInput.tsx` — Upload PDF / Paste Text tabs, emits `File | string`
- `components/ResultCard.tsx` — three variants, `whitespace-pre-wrap` content
- `components/LoadingSpinner.tsx` — `animate-spin`, `role="status"`, optional label
- `app/page.tsx` — hero + four feature cards with correct route links

**Todo List**
- [ ] Create `components/Navbar.tsx` per spec in `TECHNICAL_DESIGN.md` Section 5.1
- [ ] Create `components/DisclaimerBanner.tsx` with the verbatim disclaimer text from `TECHNICAL_DESIGN.md` Section 5.2
- [ ] Create `components/FileOrTextInput.tsx` per spec in `TECHNICAL_DESIGN.md` Section 5.3 — import `FileOrTextInputProps` from `types/index.ts`
- [ ] Create `components/ResultCard.tsx` per spec in `TECHNICAL_DESIGN.md` Section 5.4 — import `ResultCardProps` from `types/index.ts`
- [ ] Create `components/LoadingSpinner.tsx` per spec in `TECHNICAL_DESIGN.md` Section 5.5 — import `LoadingSpinnerProps` from `types/index.ts`
- [ ] Update `app/layout.tsx` to render `<Navbar>` and `<DisclaimerBanner>` above `{children}`, with `<html lang="en">`
- [ ] Create `app/page.tsx` as the landing page with feature cards per `TECHNICAL_DESIGN.md` Section 9.2
- [ ] Run `tsc --noEmit` — zero errors
- [ ] Manually verify: Tab-key reaches all 5 nav links, disclaimer text matches spec verbatim

**Relevant Context**
- `FileOrTextInput` imports `FileOrTextInputProps` from `../../types/index.ts` (relative import) or `@/types/index.ts` with the configured alias
- `ResultCard` and `LoadingSpinner` are Server Components — no `"use client"` needed
- `Navbar` requires `"use client"` for `usePathname()`
- The disclaimer text in `DisclaimerBanner` must match `TECHNICAL_DESIGN.md` Section 5.2 exactly, including the sentence about sensitive personal information

---

### Sub-Task 3 — Gemini API Utility & PDF Parser

**Status:** `[ ] pending`

**Intent**
Implement the three server-side utility files that form the foundation of every API route. These must be complete and individually verifiable before any API route is built.

**Spec References**
- `AC-GEM-01` through `AC-GEM-04` — `lib/gemini.ts` spec
- `AC-PDF-01` through `AC-PDF-04` — `lib/parsePdf.ts` spec
- `AC-ET-01` through `AC-ET-06` — `lib/extractText.ts` spec
- `AC-DIR-02` — no `"use client"` in any `lib/` file
- `AC-DIR-03` — no imports from `components/` in `lib/`
- `UC-03` — `GEMINI_API_KEY` never in client code
- `UC-05` — truncation to `MAX_CHARS` enforced here

**Expected Outcomes**
- `lib/gemini.ts` — exports `callGemini(prompt): Promise<string>`; model constant is `"gemini-2.0-flash"`; key read at call time; throws descriptively on missing key or empty response
- `lib/parsePdf.ts` — exports `parsePdf(buffer: Buffer): Promise<string>`; throws on empty buffer; does not truncate
- `lib/extractText.ts` — exports `MAX_CHARS = 40000` and `extractTextFromRequest(req): Promise<string>`; handles both content types; truncates to `MAX_CHARS`; throws with exact error messages from spec

**Todo List**
- [ ] Create `lib/gemini.ts` — follow exact behaviour contract in `TECHNICAL_DESIGN.md` Section 7.1; model string `"gemini-2.0-flash"` as a named `const`
- [ ] Create `lib/parsePdf.ts` — follow exact behaviour contract in `TECHNICAL_DESIGN.md` Section 7.2; throw `Error("PDF buffer is empty")` for empty buffer
- [ ] Create `lib/extractText.ts` — follow exact behaviour contract in `TECHNICAL_DESIGN.md` Section 7.3; export `MAX_CHARS = 40000`; throw exact error strings from the Behaviour Contract table
- [ ] Verify none of the three files contain `"use client"`
- [ ] Verify none of the three files import from `components/`
- [ ] Manual test: create a small test script to call `callGemini("Say hello")` with a valid key and confirm a non-empty string is returned
- [ ] Manual test: call `parsePdf(Buffer.alloc(0))` and confirm it throws `"PDF buffer is empty"`

**Relevant Context**
- `lib/gemini.ts` must read `process.env.GEMINI_API_KEY` *inside* the function, not at module scope — Vercel injects env vars at runtime
- `pdf-parse` returns a Promise; `async/await` usage is correct
- See `TECHNICAL_DESIGN.md` Section 7.3 Behaviour Contract table for the exact throw messages — these are tested by `AC-ET-04`

---

### Sub-Task 4 — Document Simplifier Feature (`FEAT-01`)

**Status:** `[ ] pending`

**Intent**
Implement the Document Simplifier end-to-end: API route + page + Gemini prompt + response parser.

**Spec References**
- `AC-API-S-01` through `AC-API-S-06` — `/api/simplify` route spec
- `AC-PR-S-01` through `AC-PR-S-04` — Simplifier prompt and parser spec
- `AC-SIMP-01` through `AC-SIMP-05` — Simplify page spec
- `UC-04` — structured error responses
- `UC-05` — truncation applied before Gemini call

**Expected Outcomes**
- `app/api/simplify/route.ts` — POST endpoint returning `SimplifyResponse`
- `app/simplify/page.tsx` — `"use client"` page; `FileOrTextInput` → submit → loading spinner → results
- Gemini prompt uses the exact template from `TECHNICAL_DESIGN.md` Section 8.1
- Response parser produces `SimplifyResponse` from `types/index.ts`
- Clauses with `⚠️ RISK` in their text have `risk: true`
- High-risk clauses render with `variant='warning'` on `ResultCard`

**Todo List**
- [ ] Create `app/api/simplify/route.ts` — `export const runtime = 'nodejs'`; follow Processing Contract from `TECHNICAL_DESIGN.md` Section 6.1 step-by-step
- [ ] Implement prompt using template from `TECHNICAL_DESIGN.md` Section 8.1 verbatim
- [ ] Implement response parser following parsing rules in `TECHNICAL_DESIGN.md` Section 8.1; return `SimplifyResponse`
- [ ] Create `app/simplify/page.tsx` — `"use client"`; state per `TECHNICAL_DESIGN.md` Section 9.3; wire all state transitions
- [ ] Use `<FileOrTextInput onContentReady={...} />`, `<LoadingSpinner label="Analysing document..." />`, `<ResultCard>` from Sub-Task 2
- [ ] Test: POST to `/api/simplify` with a sample contract text — verify HTTP 200, `summary` non-empty, `clauses` has ≥ 1 item
- [ ] Test: POST with no body — verify HTTP 400 `{ error: "No document text provided." }`
- [ ] Test: submit button is disabled when no content is provided

**Relevant Context**
- All response types (`SimplifyResponse`, `Clause`) must be imported from `@/types/index.ts`
- The prompt template in `TECHNICAL_DESIGN.md` Section 8.1 must be used verbatim — do not paraphrase
- The parser splits on `"\nCLAUSE: "` and checks for `"⚠️ RISK"` to set `risk: true`
- `extractTextFromRequest` from `lib/extractText.ts` handles both form-data and JSON input

---

### Sub-Task 5 — Contract Comparator Feature (`FEAT-02`)

**Status:** `[ ] pending`

**Intent**
Implement the Contract Comparator: two-document input, Gemini comparison, five-section structured result.

**Spec References**
- `AC-API-C-01` through `AC-API-C-05` — `/api/compare` route spec
- `AC-PR-C-01` through `AC-PR-C-03` — Comparator prompt and parser spec
- `AC-COMP-01` through `AC-COMP-04` — Compare page spec
- `UC-04` — error contract
- `UC-05` — truncation per document

**Expected Outcomes**
- `app/api/compare/route.ts` — POST endpoint returning `CompareResponse`
- `app/compare/page.tsx` — two side-by-side `FileOrTextInput` panels; five result sections
- Prompt uses template from `TECHNICAL_DESIGN.md` Section 8.2
- All five `CompareResponse` arrays always present (empty `[]` is valid)

**Todo List**
- [ ] Create `app/api/compare/route.ts` — `export const runtime = 'nodejs'`; follow Processing Contract in `TECHNICAL_DESIGN.md` Section 6.2
- [ ] Extract doc1 and doc2 independently (each may be PDF or text); truncate each to `MAX_CHARS`
- [ ] If either text is empty, return `400 { error: "Both documents are required." }`
- [ ] Implement prompt from `TECHNICAL_DESIGN.md` Section 8.2 verbatim
- [ ] Implement parser per parsing rules in `TECHNICAL_DESIGN.md` Section 8.2; ensure all five keys in `CompareResponse` are always present
- [ ] Create `app/compare/page.tsx` per `TECHNICAL_DESIGN.md` Section 9.4; two `<FileOrTextInput>` components labelled "Document A" and "Document B"
- [ ] Render five `<ResultCard>` sections; risks and inconsistencies use `variant='warning'`
- [ ] Test: submit one doc only — verify inline validation error, no API call made
- [ ] Test: submit two identical docs — verify `matching` array is non-empty

**Relevant Context**
- The compare route cannot use `extractTextFromRequest` directly (it handles only one doc field); extract doc1 and doc2 using `formData.get('doc1')` / `formData.get('doc2')` and call `parsePdf` or cast to string independently
- `CompareResponse` must be imported from `@/types/index.ts`

---

### Sub-Task 6 — Q&A Chat Feature (`FEAT-03`)

**Status:** `[ ] pending`

**Intent**
Implement the multi-turn Q&A chat interface with a two-phase UX (document load → chat). This is the most stateful feature.

**Spec References**
- `AC-API-CH-01` through `AC-API-CH-05` — `/api/chat` route spec
- `AC-PR-CH-01` through `AC-PR-CH-04` — Chat prompt spec
- `AC-CHAT-01` through `AC-CHAT-06` — Chat page spec
- `UC-02` — no persistent storage (server is stateless)
- `UC-04` — error contract

**Expected Outcomes**
- `app/api/extract/route.ts` — lightweight POST endpoint that extracts text from a PDF or text request and returns `{ text: string }` (used in Phase 1 of the chat page)
- `app/api/chat/route.ts` — POST endpoint accepting `ChatRequest`, building the conversation prompt, returning `ChatResponse`
- `app/chat/page.tsx` — two-phase client component; phase 1 loads doc, phase 2 is scrollable chat window
- Conversation history accumulates and is sent with each question
- Auto-scroll to newest message

**Todo List**
- [ ] Create `app/api/extract/route.ts` — `export const runtime = 'nodejs'`; call `extractTextFromRequest(req)`; return `{ text: string }`; handle errors with HTTP 400
- [ ] Create `app/api/chat/route.ts` per Processing Contract in `TECHNICAL_DESIGN.md` Section 6.3; build prompt from template in Section 8.3; history formatted as `User:` / `Assistant:` turns; prompt ends with `Assistant:`
- [ ] Create `app/chat/page.tsx` — two phases (`'load'` | `'chat'`); state per `TECHNICAL_DESIGN.md` Section 9.5
- [ ] Phase 1: `<FileOrTextInput>` + "Load Document" button; on click POST to `/api/extract`; on success store `documentText` in state; transition to `'chat'` phase
- [ ] Phase 2: scrollable message list; user messages right-aligned indigo, model messages left-aligned slate; text input + "Send" button disabled while loading
- [ ] Auto-scroll: use `useRef` on message container + `scrollIntoView` after state update
- [ ] History: `messages` state is `ChatMessage[]`; on send, append user message immediately, await API, append model response
- [ ] Test: load a document; send three questions; verify answers reference document content
- [ ] Test: POST to `/api/chat` with empty `question` — verify HTTP 400

**Relevant Context**
- The chat page sends `documentText` as a plain string in the JSON body — PDFs are extracted in Phase 1 via `/api/extract`; no PDF is sent during the chat phase
- `ChatMessage` and `ChatRequest`/`ChatResponse` imported from `@/types/index.ts`
- When `history` is empty (first turn), the `CONVERSATION HISTORY:` section is present but blank — see `AC-PR-CH-04`
- Server is stateless per `UC-02`; the full history is sent client-side with every request

---

### Sub-Task 7 — Lawyer Prep Feature (`FEAT-04`)

**Status:** `[ ] pending`

**Intent**
Implement the Lawyer Prep checklist generator with a print-friendly output.

**Spec References**
- `AC-API-P-01` through `AC-API-P-04` — `/api/prep` route spec
- `AC-PR-P-01` through `AC-PR-P-03` — Prep prompt and parser spec
- `AC-PREP-01` through `AC-PREP-05` — Prep page spec
- `UC-01` — disclaimer prominent on this page
- `UC-04` — error contract

**Expected Outcomes**
- `app/api/prep/route.ts` — POST endpoint returning `PrepResponse`
- `app/prep/page.tsx` — `FileOrTextInput` + submit; three labelled checklist sections; "Print Checklist" button
- Each checklist item rendered as `<li>` with `<input type="checkbox" disabled>` for visual styling
- `window.print()` triggered by "Print Checklist" button
- Navbar, buttons, and input hidden in print via `print:hidden`

**Todo List**
- [ ] Create `app/api/prep/route.ts` per Processing Contract in `TECHNICAL_DESIGN.md` Section 6.4
- [ ] Implement prompt from `TECHNICAL_DESIGN.md` Section 8.4 verbatim
- [ ] Implement parser per parsing rules in `TECHNICAL_DESIGN.md` Section 8.4; all three arrays always present
- [ ] Create `app/prep/page.tsx` per `TECHNICAL_DESIGN.md` Section 9.6
- [ ] Render three sections: "Questions to Ask Your Lawyer", "Documents & Information to Bring", "Watch Out For"
- [ ] Each item: `<li className="flex items-center gap-2"><input type="checkbox" disabled /> {item}</li>`
- [ ] "Print Checklist" button — calls `window.print()`; visible only after results loaded
- [ ] Apply `print:hidden` to `<Navbar>`, `<DisclaimerBanner>`, submit area, and Print button
- [ ] Apply `print:block` to checklist sections if they are conditionally hidden in non-print CSS
- [ ] Test: submit a non-trivial legal doc — all three arrays have ≥ 1 item
- [ ] Test: open print preview — Navbar absent, checklist visible

**Relevant Context**
- `PrepResponse` imported from `@/types/index.ts`
- The print disclaimer should still appear in print (not hidden) — only chrome elements are hidden
- The items must be document-specific per `AC-PR-P-03` — verify manually with a sample NDA

---

### Sub-Task 8 — Home Page, Polish & Deployment Verification

**Status:** `[ ] pending`

**Intent**
Finalise the landing page, verify global polish across all pages, create `vercel.json`, update `README.md`, and confirm the full build is production-ready.

**Spec References**
- `AC-HOME-01` through `AC-HOME-03` — Home page
- `AC-TW-01` through `AC-TW-03` — Tailwind config
- `AC-VCL-01` through `AC-VCL-02` — `vercel.json`
- `AC-README-01` through `AC-README-02` — README
- `AC-A11Y-01` through `AC-A11Y-04` — accessibility
- `AC-BUILD-01` through `AC-BUILD-03` — build verification
- `AC-DEPLOY-01` through `AC-DEPLOY-05` — deployment checklist
- `AC-SEC-01` through `AC-SEC-03` — security verification
- `AC-PERF-01` — bundle size
- All `UC-` constraints — final cross-cutting verification

**Expected Outcomes**
- `app/page.tsx` — hero section + four feature cards with correct routes, icons, and descriptions
- `vercel.json` — `maxDuration: 30` for all API functions
- `README.md` — all 8 required sections per `TECHNICAL_DESIGN.md` Section 13.3
- All pages have unique `metadata.title` via Next.js metadata export
- `npm run build` exits 0 with zero TypeScript errors
- `GEMINI_API_KEY` not present in `.next/static/` after build
- All AC codes in Sub-Tasks 1–7 are verified and passing

**Todo List**
- [ ] Polish `app/page.tsx` hero + four feature cards — confirm links match routes in `TECHNICAL_DESIGN.md` Section 9.2
- [ ] Add unique `metadata` export to every page (`/simplify`, `/compare`, `/chat`, `/prep`)
- [ ] Create `vercel.json` per `TECHNICAL_DESIGN.md` Section 10.3
- [ ] Update `README.md` with all 8 sections per `TECHNICAL_DESIGN.md` Section 13.3
- [ ] Run `npm run build` — confirm exit 0, zero TypeScript errors (`AC-BUILD-01`, `AC-BUILD-02`)
- [ ] Run `grep -r "GEMINI_API_KEY" .next/static/` — confirm zero results (`AC-SEC-01`)
- [ ] Run `grep -r "@google/generative-ai" components/` — confirm zero results (`AC-SEC-02`)
- [ ] Run `grep -r "@google/generative-ai" app/` — confirm zero results (`AC-SEC-03`)
- [ ] Manual accessibility check: Tab through every page, confirm all interactive elements reachable (`AC-A11Y-04`)
- [ ] Deploy to Vercel: set `GEMINI_API_KEY` in Vercel dashboard; confirm build passes (`AC-DEPLOY-01`, `AC-DEPLOY-02`)
- [ ] Smoke test on production URL: test all four features with a sample legal document (`AC-DEPLOY-03`, `AC-DEPLOY-04`)

**Relevant Context**
- `vercel.json` must be at the project root (alongside `package.json`)
- Vercel free tier default timeout is 10s; `maxDuration: 30` is required for large PDF + Gemini calls
- The README local setup steps must be followable in < 5 minutes by a new developer (`AC-README-02`)

---

## Architecture Summary

```
app/
├── layout.tsx           # Root layout — Navbar + DisclaimerBanner (AC-LAY-01~03)
├── page.tsx             # Landing page (AC-HOME-01~03)
├── simplify/page.tsx    # FEAT-01: Document Simplifier (AC-SIMP-01~05)
├── compare/page.tsx     # FEAT-02: Contract Comparator (AC-COMP-01~04)
├── chat/page.tsx        # FEAT-03: Q&A Chat (AC-CHAT-01~06)
├── prep/page.tsx        # FEAT-04: Lawyer Prep (AC-PREP-01~05)
└── api/
    ├── simplify/route.ts  (AC-API-S-01~06)
    ├── compare/route.ts   (AC-API-C-01~05)
    ├── chat/route.ts      (AC-API-CH-01~05)
    ├── extract/route.ts   (used by chat page Phase 1)
    └── prep/route.ts      (AC-API-P-01~04)
types/
└── index.ts             # All shared types (AC-TYPES-01~03)
components/
├── Navbar.tsx           (AC-NAV-01~04)
├── DisclaimerBanner.tsx (AC-DISC-01~03)
├── FileOrTextInput.tsx  (AC-FTI-01~06)
├── ResultCard.tsx       (AC-RC-01~04)
└── LoadingSpinner.tsx   (AC-LS-01~04)
lib/
├── gemini.ts            (AC-GEM-01~04)
├── parsePdf.ts          (AC-PDF-01~04)
└── extractText.ts       (AC-ET-01~06)
```

## Acceptance Criteria Index

All AC codes are defined in [`TECHNICAL_DESIGN.md`](./TECHNICAL_DESIGN.md). Quick reference:

| AC Code Range | Section | Sub-Task |
|---|---|---|
| `UC-01` – `UC-06` | Universal Constraints | Verified in Sub-Task 8 |
| `TC-01` – `TC-07` | Technology Contracts | Sub-Task 1 |
| `AC-TYPES-01` – `AC-TYPES-03` | Shared Types | Sub-Task 1 |
| `AC-DIR-01` – `AC-DIR-03` | Directory Contract | Sub-Tasks 1–8 |
| `AC-NAV-01` – `AC-NAV-04` | Navbar | Sub-Task 2 |
| `AC-DISC-01` – `AC-DISC-03` | DisclaimerBanner | Sub-Task 2 |
| `AC-FTI-01` – `AC-FTI-06` | FileOrTextInput | Sub-Task 2 |
| `AC-RC-01` – `AC-RC-04` | ResultCard | Sub-Task 2 |
| `AC-LS-01` – `AC-LS-04` | LoadingSpinner | Sub-Task 2 |
| `AC-LAY-01` – `AC-LAY-03` | Root Layout | Sub-Task 2 |
| `AC-HOME-01` – `AC-HOME-03` | Home Page | Sub-Tasks 2, 8 |
| `AC-API-S-01` – `AC-API-S-06` | Simplify Route | Sub-Task 4 |
| `AC-API-C-01` – `AC-API-C-05` | Compare Route | Sub-Task 5 |
| `AC-API-CH-01` – `AC-API-CH-05` | Chat Route | Sub-Task 6 |
| `AC-API-P-01` – `AC-API-P-04` | Prep Route | Sub-Task 7 |
| `AC-GEM-01` – `AC-GEM-04` | Gemini Utility | Sub-Task 3 |
| `AC-PDF-01` – `AC-PDF-04` | PDF Parser | Sub-Task 3 |
| `AC-ET-01` – `AC-ET-06` | Extract Text | Sub-Task 3 |
| `AC-PR-S-01` – `AC-PR-S-04` | Simplifier Prompt | Sub-Task 4 |
| `AC-PR-C-01` – `AC-PR-C-03` | Comparator Prompt | Sub-Task 5 |
| `AC-PR-CH-01` – `AC-PR-CH-04` | Chat Prompt | Sub-Task 6 |
| `AC-PR-P-01` – `AC-PR-P-03` | Prep Prompt | Sub-Task 7 |
| `AC-SIMP-01` – `AC-SIMP-05` | Simplify Page | Sub-Task 4 |
| `AC-COMP-01` – `AC-COMP-04` | Compare Page | Sub-Task 5 |
| `AC-CHAT-01` – `AC-CHAT-06` | Chat Page | Sub-Task 6 |
| `AC-PREP-01` – `AC-PREP-05` | Prep Page | Sub-Task 7 |
| `AC-CFG-01` – `AC-CFG-02` | next.config.ts | Sub-Task 1 |
| `AC-TW-01` – `AC-TW-03` | tailwind.config.ts | Sub-Task 1 |
| `AC-VCL-01` – `AC-VCL-02` | vercel.json | Sub-Task 8 |
| `AC-ENV-01` – `AC-ENV-03` | .env.example | Sub-Task 1 |
| `AC-PERF-01` | Performance | Sub-Task 8 |
| `AC-A11Y-01` – `AC-A11Y-04` | Accessibility | Sub-Tasks 2, 8 |
| `AC-REL-01` – `AC-REL-02` | Reliability | Sub-Tasks 4–7 |
| `AC-SEC-01` – `AC-SEC-03` | Security | Sub-Task 8 |
| `AC-INP-01` – `AC-INP-03` | Input Validation | Sub-Tasks 2–7 |
| `AC-BUILD-01` – `AC-BUILD-03` | Build | Sub-Tasks 1, 8 |
| `AC-DEPLOY-01` – `AC-DEPLOY-05` | Deployment | Sub-Task 8 |
| `AC-README-01` – `AC-README-02` | README | Sub-Task 8 |

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | Yes | Google AI Studio API key for Gemini |

## Deployment Notes

- Set `GEMINI_API_KEY` in Vercel project settings → Environment Variables
- `vercel.json` sets `maxDuration: 30` for all API routes (see `TECHNICAL_DESIGN.md` Section 10.3)
- `pdf-parse` must be in `serverExternalPackages` in `next.config.ts` (see `TECHNICAL_DESIGN.md` Section 10.1)
