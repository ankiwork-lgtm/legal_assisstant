# LexAid — Task Breakdown

> **Spec source:** [`TECHNICAL_DESIGN.md`](./TECHNICAL_DESIGN.md)  
> **Plan source:** [`legal-assistant-plan.md`](./legal-assistant-plan.md)  
> **Approach:** Spec-Driven Development — every task maps to one or more AC codes. A task is done only when all its AC codes pass.

---

## How to Read This File

| Column | Meaning |
|---|---|
| **ID** | Unique task identifier (`T-XX`) |
| **Status** | `[ ]` pending · `[-]` in progress · `[x]` done · `[!]` blocked |
| **Layer** | `config` · `types` · `lib` · `api` · `component` · `page` · `test` · `deploy` |
| **File** | Primary file created or modified |
| **Depends on** | Task IDs that must be complete first |
| **AC Codes** | Acceptance criteria from `TECHNICAL_DESIGN.md` that this task satisfies |

Tasks within a phase can be worked in parallel unless a dependency is listed.

---

## Phase 1 — Project Scaffold & Configuration

> **Goal:** A compilable, deployable skeleton with all dependencies, config files, and shared types in place.  
> **Phase complete when:** `npm run build` exits 0 and `tsc --noEmit` reports zero errors.

---

### T-01 — Scaffold Next.js 14 App

| Field | Value |
|---|---|
| **Status** | `[x]` |
| **Layer** | config |
| **File** | `package.json`, `next.config.mjs`, `tsconfig.json`, `app/layout.tsx`, `app/globals.css` |
| **Depends on** | — |
| **AC Codes** | `TC-01`, `TC-02`, `TC-03`, `AC-CFG-02`, `AC-LAY-03` |

**Steps:**
- [x] Run: `npx create-next-app@14 . --ts --tailwind --app --no-src-dir --import-alias "@/*"` *(files created manually — scaffold refused non-empty dir)*
- [x] Confirm `next.config.mjs` exists *(used `.mjs` — Next.js 14 does not support `.ts` config)*
- [x] Confirm `tsconfig.json` has `"strict": true` and `"paths": { "@/*": ["./*"] }`
- [x] Confirm `app/globals.css` contains Tailwind directives (`@tailwind base`, `@tailwind components`, `@tailwind utilities`)

**Definition of Done:** `npm run dev` starts without errors; `app/layout.tsx` renders a blank page.

---

### T-02 — Install Runtime Dependencies

| Field | Value |
|---|---|
| **Status** | `[x]` |
| **Layer** | config |
| **File** | `package.json` |
| **Depends on** | T-01 |
| **AC Codes** | `TC-04`, `TC-06` |

**Steps:**
- [x] Run: `npm install @google/generative-ai pdf-parse`
- [x] Verify both appear in `dependencies` in `package.json`

---

### T-03 — Install Dev Dependencies

| Field | Value |
|---|---|
| **Status** | `[x]` |
| **Layer** | config |
| **File** | `package.json` |
| **Depends on** | T-01 |
| **AC Codes** | `TC-07` |

**Steps:**
- [x] Run: `npm install -D @types/pdf-parse`
- [x] Verify `@types/pdf-parse` appears in `devDependencies`

---

### T-04 — Configure `next.config.ts`

| Field | Value |
|---|---|
| **Status** | `[x]` |
| **Layer** | config |
| **File** | `next.config.mjs` |
| **Depends on** | T-02 |
| **AC Codes** | `AC-CFG-01`, `AC-CFG-02` |

**Steps:**
- [x] Add `experimental.serverComponentsExternalPackages: ['pdf-parse']` to `next.config.mjs` *(Next.js 14 uses `experimental.serverComponentsExternalPackages`; `serverExternalPackages` is Next.js 15+)*
- [x] Verify `npm run build` completes without `pdf-parse` bundling errors

---

### T-05 — Configure Tailwind Theme

| Field | Value |
|---|---|
| **Status** | `[x]` |
| **Layer** | config |
| **File** | `tailwind.config.ts` |
| **Depends on** | T-01 |
| **AC Codes** | `TC-03`, `AC-TW-01`, `AC-TW-02`, `AC-TW-03` |

**Steps:**
- [x] Add `primary` colour scale to `theme.extend.colors` (see `TECHNICAL_DESIGN.md` Section 10.2 for exact values)
- [x] Confirm `content` array includes `'./app/**/*.{ts,tsx}'` and `'./components/**/*.{ts,tsx}'`
- [x] Verify `bg-primary-500` class is resolvable (check with `npm run build` — no purge warnings)

---

### T-06 — Create `.env.example`

| Field | Value |
|---|---|
| **Status** | `[x]` |
| **Layer** | config |
| **File** | `.env.example` |
| **Depends on** | — |
| **AC Codes** | `AC-ENV-01`, `AC-ENV-03` |

**Steps:**
- [x] Create `.env.example` with exact content from `TECHNICAL_DESIGN.md` Section 10.4
- [x] Verify the file does NOT contain a real API key

---

### T-07 — Verify `.gitignore` for `.env.local`

| Field | Value |
|---|---|
| **Status** | `[x]` |
| **Layer** | config |
| **File** | `.gitignore` |
| **Depends on** | T-01 |
| **AC Codes** | `AC-ENV-02` |

**Steps:**
- [x] Confirm `.env.local` is listed in `.gitignore`
- [x] `.env.local` confirmed present in `.gitignore`

---

### T-08 — Create Shared Type Definitions

| Field | Value |
|---|---|
| **Status** | `[x]` |
| **Layer** | types |
| **File** | `types/index.ts` |
| **Depends on** | T-01 |
| **AC Codes** | `AC-TYPES-01`, `AC-TYPES-02`, `AC-TYPES-03` |

**Steps:**
- [x] Create `types/index.ts` with the complete type definitions from `TECHNICAL_DESIGN.md` Section 3 (copy verbatim)
- [x] Includes: `DocumentContent`, `SimplifyRequest`, `CompareRequest`, `ChatRequest`, `PrepRequest`, `SimplifyResponse`, `Clause`, `CompareResponse`, `ChatResponse`, `PrepResponse`, `ApiError`, `ChatMessage`, `FileOrTextInputProps`, `ResultCardProps`, `LoadingSpinnerProps`
- [x] Run `tsc --noEmit` — zero errors

---

### T-09 — Phase 1 Build Verification

| Field | Value |
|---|---|
| **Status** | `[x]` |
| **Layer** | test |
| **File** | — |
| **Depends on** | T-01, T-02, T-03, T-04, T-05, T-06, T-07, T-08 |
| **AC Codes** | `AC-BUILD-01`, `AC-BUILD-02`, `AC-BUILD-03`, `AC-DIR-01` (partial) |

**Steps:**
- [x] Run `npm run build` — exit code 0 ✓
- [x] Confirm zero TypeScript errors in build output ✓
- [x] Confirm no `pdf-parse` bundling warnings ✓
- [x] Confirm all root config files exist: `next.config.mjs`, `tailwind.config.ts`, `postcss.config.js`, `tsconfig.json`, `.env.example` ✓

---

## Phase 2 — Shared UI Components & Layout

> **Goal:** All reusable UI components and the root layout are built, typed, and pass their AC codes.  
> **Phase complete when:** All components render correctly in the browser and `tsc --noEmit` is clean.  
> **Prerequisite:** Phase 1 complete.

---

### T-10 — Build `Navbar` Component

| Field | Value |
|---|---|
| **Status** | `[x]` |
| **Layer** | component |
| **File** | `components/Navbar.tsx` |
| **Depends on** | T-08 |
| **AC Codes** | `AC-NAV-01`, `AC-NAV-02`, `AC-NAV-03`, `AC-NAV-04` |

**Steps:**
- [x] Create `components/Navbar.tsx` as a `"use client"` component
- [x] Import `usePathname` from `next/navigation`
- [x] Render `<nav>` with 5 `<Link>` elements per the Navigation Link Contract in `TECHNICAL_DESIGN.md` Section 5.1
- [x] Apply `font-semibold underline` (or equivalent) to the active link when `pathname === href`
- [x] Root element must include `bg-slate-900 text-white` classes
- [x] Verify: Tab-key reaches all 5 links (keyboard test)
- [x] Verify: `<nav>` element present in DOM

---

### T-11 — Build `DisclaimerBanner` Component

| Field | Value |
|---|---|
| **Status** | `[x]` |
| **Layer** | component |
| **File** | `components/DisclaimerBanner.tsx` |
| **Depends on** | T-08 |
| **AC Codes** | `AC-DISC-01`, `AC-DISC-02`, `AC-DISC-03` |

**Steps:**
- [x] Create `components/DisclaimerBanner.tsx` as a Server Component (no `"use client"`)
- [x] Render the **exact** disclaimer text from `TECHNICAL_DESIGN.md` Section 5.2 — including the sentence about sensitive personal information
- [x] Root element must include `bg-amber-50 border-b border-amber-200 text-amber-800` classes
- [x] Verify text is visible without scrolling at 320px viewport width

---

### T-12 — Build `FileOrTextInput` Component

| Field | Value |
|---|---|
| **Status** | `[x]` |
| **Layer** | component |
| **File** | `components/FileOrTextInput.tsx` |
| **Depends on** | T-08 |
| **AC Codes** | `AC-FTI-01`, `AC-FTI-02`, `AC-FTI-03`, `AC-FTI-04`, `AC-FTI-05`, `AC-FTI-06` |

**Steps:**
- [x] Create `components/FileOrTextInput.tsx` as a `"use client"` component
- [x] Import `FileOrTextInputProps` from `@/types/index.ts`
- [x] Implement state: `activeTab: 'upload' | 'text'`, `textValue: string`, `fileName: string`
- [x] Upload PDF tab: `<input type="file" accept=".pdf">` — on change, call `onContentReady(file)` with the `File` object; display `file.name`
- [x] Paste Text tab: `<textarea rows={10}>` — on change, call `onContentReady(textValue)`
- [x] Switching tabs clears the other tab's state (`fileName` cleared when switching to text; `textValue` cleared when switching to upload)
- [x] Verify file input `accept` attribute is `.pdf`
- [x] Run `tsc --noEmit` — verify no errors against `FileOrTextInputProps`

---

### T-13 — Build `ResultCard` Component

| Field | Value |
|---|---|
| **Status** | `[x]` |
| **Layer** | component |
| **File** | `components/ResultCard.tsx` |
| **Depends on** | T-08 |
| **AC Codes** | `AC-RC-01`, `AC-RC-02`, `AC-RC-03`, `AC-RC-04` |

**Steps:**
- [x] Create `components/ResultCard.tsx` as a Server Component (no `"use client"`)
- [x] Import `ResultCardProps` from `@/types/index.ts`
- [x] Render `title` in a visually distinct heading element (`<h2>` or `<h3>`)
- [x] Render `content` inside an element with `whitespace-pre-wrap` class
- [x] Implement three variants per `TECHNICAL_DESIGN.md` Section 5.4 Variant Contract:
  - `default`: white background, slate border
  - `warning`: `bg-amber-50 border-amber-300`
  - `info`: `bg-blue-50 border-blue-300`
- [x] Run `tsc --noEmit` — no errors against `ResultCardProps`

---

### T-14 — Build `LoadingSpinner` Component

| Field | Value |
|---|---|
| **Status** | `[x]` |
| **Layer** | component |
| **File** | `components/LoadingSpinner.tsx` |
| **Depends on** | T-08 |
| **AC Codes** | `AC-LS-01`, `AC-LS-02`, `AC-LS-03`, `AC-LS-04` |

**Steps:**
- [x] Create `components/LoadingSpinner.tsx` as a Server Component (no `"use client"`)
- [x] Import `LoadingSpinnerProps` from `@/types/index.ts`
- [x] Render a spinner element with `animate-spin` Tailwind class
- [x] Add `role="status"` to the spinner wrapper element
- [x] Add `aria-label` equal to the `label` prop value (or `"Loading"` if prop not provided)
- [x] When `label` prop is provided, render it as visible text below the spinner
- [x] Run `tsc --noEmit` — no errors

---

### T-15 — Update Root Layout

| Field | Value |
|---|---|
| **Status** | `[x]` |
| **Layer** | page |
| **File** | `app/layout.tsx` |
| **Depends on** | T-10, T-11 |
| **AC Codes** | `AC-LAY-01`, `AC-LAY-02`, `AC-LAY-03`, `UC-01` |

**Steps:**
- [x] Update `app/layout.tsx` to import and render `<Navbar>` and `<DisclaimerBanner>`
- [x] Layout order must be: `<Navbar>` → `<DisclaimerBanner>` → `<main>{children}</main>`
- [x] Ensure `<html lang="en">` attribute is set
- [x] Ensure `import './globals.css'` is present
- [x] Set metadata: `title: "LexAid"`, `description: "AI-powered legal document assistant"`
- [x] Verify: Navigate to `/` — both Navbar and DisclaimerBanner are visible

---

### T-16 — Build Home/Landing Page

| Field | Value |
|---|---|
| **Status** | `[x]` |
| **Layer** | page |
| **File** | `app/page.tsx` |
| **Depends on** | T-15 |
| **AC Codes** | `AC-HOME-01`, `AC-HOME-02`, `AC-HOME-03` |

**Steps:**
- [x] Create `app/page.tsx` as a Server Component
- [x] Render a hero section with: app name "LexAid", tagline (≤ 15 words), brief description (≤ 50 words)
- [x] Render four feature cards, one per feature (`FEAT-01` through `FEAT-04`) — each card has: feature name, one-sentence description, an icon/emoji, a `<Link>` to the feature route
- [x] Feature card routes: `/simplify`, `/compare`, `/chat`, `/prep`
- [x] Verify all four links are keyboard-focusable (Tab test)
- [x] Run `tsc --noEmit` — no errors

---

### T-17 — Phase 2 Component Verification

| Field | Value |
|---|---|
| **Status** | `[x]` |
| **Layer** | test |
| **File** | — |
| **Depends on** | T-10, T-11, T-12, T-13, T-14, T-15, T-16 |
| **AC Codes** | `AC-DIR-02`, `AC-DIR-03`, `AC-A11Y-01`, `AC-A11Y-02` |

**Steps:**
- [x] Run `grep -r '"use client"' lib/` — confirm zero results (`AC-DIR-02`)
- [x] Run `grep -r 'from.*components' lib/` — confirm zero results (`AC-DIR-03`)
- [x] Verify `<LoadingSpinner>` has `role="status"` in rendered HTML (`AC-A11Y-02`)
- [x] Verify all `<FileOrTextInput>` form inputs have associated `<label>` elements (`AC-A11Y-01`)
- [x] Run `tsc --noEmit` — zero errors

---

## Phase 3 — Server-Side Utilities

> **Goal:** All three `lib/` utilities are implemented, typed correctly, and pass manual smoke tests.  
> **Phase complete when:** Each utility's AC codes pass and `tsc --noEmit` is clean.  
> **Prerequisite:** Phase 1 complete (types must exist in `types/index.ts`).

---

### T-18 — Implement `lib/gemini.ts`

| Field | Value |
|---|---|
| **Status** | `[x]` |
| **Layer** | lib |
| **File** | `lib/gemini.ts` |
| **Depends on** | T-08 |
| **AC Codes** | `AC-GEM-01`, `AC-GEM-02`, `AC-GEM-03`, `AC-GEM-04`, `UC-03` |

**Steps:**
- [x] Create `lib/gemini.ts` — no `"use client"` directive
- [x] Define `const MODEL_NAME = "gemini-2.0-flash"` as a named constant
- [x] Export `async function callGemini(prompt: string): Promise<string>`
- [x] Inside the function: read `process.env.GEMINI_API_KEY` — if falsy, throw `Error("GEMINI_API_KEY is not set")`
- [x] Call `new GoogleGenerativeAI(apiKey).getGenerativeModel({ model: MODEL_NAME })`
- [x] Call `model.generateContent(prompt)` and return `result.response.text()`
- [x] If response text is empty string, throw `Error("Empty response from Gemini")`
- [x] Smoke test: call `callGemini("Say hello")` with a valid key — confirm non-empty string returned

---

### T-19 — Implement `lib/parsePdf.ts`

| Field | Value |
|---|---|
| **Status** | `[x]` |
| **Layer** | lib |
| **File** | `lib/parsePdf.ts` |
| **Depends on** | T-02, T-03 |
| **AC Codes** | `AC-PDF-01`, `AC-PDF-02`, `AC-PDF-03`, `AC-PDF-04` |

**Steps:**
- [x] Create `lib/parsePdf.ts` — no `"use client"` directive
- [x] Import `pdf` (default export) from `pdf-parse`
- [x] Export `async function parsePdf(buffer: Buffer): Promise<string>`
- [x] If `buffer.length === 0`, throw `Error("PDF buffer is empty")`
- [x] Call `await pdf(buffer)` and return `data.text`
- [x] Do NOT truncate — truncation is `extractText.ts`'s responsibility
- [x] Smoke test: call `parsePdf(Buffer.alloc(0))` — confirm throws `"PDF buffer is empty"`

---

### T-20 — Implement `lib/extractText.ts`

| Field | Value |
|---|---|
| **Status** | `[x]` |
| **Layer** | lib |
| **File** | `lib/extractText.ts` |
| **Depends on** | T-08, T-19 |
| **AC Codes** | `AC-ET-01`, `AC-ET-02`, `AC-ET-03`, `AC-ET-04`, `AC-ET-05`, `AC-ET-06`, `UC-05` |

**Steps:**
- [x] Create `lib/extractText.ts` — no `"use client"` directive
- [x] Export `export const MAX_CHARS = 40000`
- [x] Export `async function extractTextFromRequest(req: Request): Promise<string>`
- [x] Detect content type from `req.headers.get('content-type')`
- [x] **`multipart/form-data` path:** call `req.formData()`, get `file` field; if absent throw `Error("No file provided in form data")`; convert Blob to Buffer via `Buffer.from(await file.arrayBuffer())`; call `parsePdf(buffer)`; truncate to `MAX_CHARS`
- [x] **`application/json` path:** call `req.json()`; read `.text` field; if absent or empty throw `Error("No text provided in request body")`; return `text.slice(0, MAX_CHARS)`
- [x] **Other content types:** throw `Error("Unsupported content type")`
- [x] Smoke test: pass a 50,000-char string via JSON — confirm return length is exactly 40,000

---

### T-21 — Phase 3 Utility Verification

| Field | Value |
|---|---|
| **Status** | `[x]` |
| **Layer** | test |
| **File** | — |
| **Depends on** | T-18, T-19, T-20 |
| **AC Codes** | `AC-DIR-02`, `AC-DIR-03` |

**Steps:**
- [x] Run `grep -r '"use client"' lib/` — confirm zero results
- [x] Run `grep -r 'from.*components' lib/` — confirm zero results
- [x] Run `tsc --noEmit` — zero errors

---

## Phase 4 — Document Simplifier (`FEAT-01`)

> **Goal:** End-to-end simplifier works: upload/paste → API → structured result displayed.  
> **Prerequisite:** Phases 1, 2, 3 complete.

---

### T-22 — Implement `/api/simplify` Route

| Field | Value |
|---|---|
| **Status** | `[x]` |
| **Layer** | api |
| **File** | `app/api/simplify/route.ts` |
| **Depends on** | T-18, T-20 |
| **AC Codes** | `AC-API-S-01`, `AC-API-S-02`, `AC-API-S-03`, `AC-API-S-04`, `AC-API-S-06`, `UC-04`, `UC-05` |

**Steps:**
- [x] Create `app/api/simplify/route.ts`
- [x] Add `export const runtime = 'nodejs'` at top of file
- [x] Export `async function POST(req: Request)` only — no GET/PUT/DELETE
- [x] Call `extractTextFromRequest(req)`; on empty string return `NextResponse.json({ error: "No document text provided." }, { status: 400 })`
- [x] Build prompt using the **verbatim** template from `TECHNICAL_DESIGN.md` Section 8.1
- [x] Call `callGemini(prompt)`
- [x] Parse response using the parsing rules in `TECHNICAL_DESIGN.md` Section 8.1 — split on `"CLAUSE:"`, extract summary, set `risk: true` when `"⚠️ RISK"` present
- [x] Return `NextResponse.json(simplifyResponse)` — shape matches `SimplifyResponse` from `@/types/index.ts`
- [x] Wrap in try/catch — on error return `NextResponse.json({ error: "Failed to analyse document. Please try again." }, { status: 500 })`

---

### T-23 — Implement Risk Flag Detection in Simplifier Parser

| Field | Value |
|---|---|
| **Status** | `[x]` |
| **Layer** | api |
| **File** | `app/api/simplify/route.ts` |
| **Depends on** | T-22 |
| **AC Codes** | `AC-API-S-05`, `AC-PR-S-01`, `AC-PR-S-02`, `AC-PR-S-03`, `AC-PR-S-04` |

**Steps:**
- [x] Verify the parser sets `risk: true` when clause text includes the string `"⚠️ RISK"`
- [x] Manually test with a sample contract containing unusual clauses — confirm at least one `risk: true` clause returned
- [x] Confirm `summary` is non-empty for any non-trivial document
- [x] Confirm `clauses` array has ≥ 1 item

---

### T-24 — Build Simplify Page

| Field | Value |
|---|---|
| **Status** | `[x]` |
| **Layer** | page |
| **File** | `app/simplify/page.tsx` |
| **Depends on** | T-12, T-13, T-14, T-22 |
| **AC Codes** | `AC-SIMP-01`, `AC-SIMP-02`, `AC-SIMP-03`, `AC-SIMP-04`, `AC-SIMP-05`, `AC-INP-01`, `AC-INP-02` |

**Steps:**
- [x] Create `app/simplify/page.tsx` as a `"use client"` component
- [x] Add `export const metadata` with unique `title` and `description`
- [x] Declare state: `content: DocumentContent | null`, `result: SimplifyResponse | null`, `loading: boolean`, `error: string | null`
- [x] Render `<FileOrTextInput onContentReady={(c) => setContent(c)} />`
- [x] Submit button: disabled when `content === null || loading === true`
- [x] On submit: set `loading = true`; build `FormData` or JSON body depending on `content` type; POST to `/api/simplify`; parse response into `SimplifyResponse`; set `result`; set `loading = false`
- [x] When `loading`: render `<LoadingSpinner label="Analysing document..." />`
- [x] When `result`: render `<ResultCard title="Plain-English Summary" content={result.summary} />` followed by one `<ResultCard>` per clause — use `variant="warning"` when `clause.risk === true`
- [x] When `error`: render error string in a visible styled banner (not a raw error object)
- [x] Network/API error: catch and set `error` state with human-readable message

---

## Phase 5 — Contract Comparator (`FEAT-02`)

> **Goal:** Two-document comparison works end-to-end with five result sections.  
> **Prerequisite:** Phases 1, 2, 3 complete.

---

### T-25 — Implement `/api/compare` Route

| Field | Value |
|---|---|
| **Status** | `[x]` |
| **Layer** | api |
| **File** | `app/api/compare/route.ts` |
| **Depends on** | T-18, T-19, T-20 |
| **AC Codes** | `AC-API-C-01`, `AC-API-C-02`, `AC-API-C-03`, `AC-API-C-05`, `UC-04`, `UC-05` |

**Steps:**
- [x] Create `app/api/compare/route.ts`
- [x] Add `export const runtime = 'nodejs'`
- [x] Export `async function POST(req: Request)`
- [x] Parse `multipart/form-data` — extract `doc1` and `doc2` fields independently using `formData.get()`
- [x] For each field: if it's a `File`, convert to Buffer and call `parsePdf`; if it's a string, use as-is
- [x] Truncate each extracted text to `MAX_CHARS` independently
- [x] If either text is empty/missing: return `NextResponse.json({ error: "Both documents are required." }, { status: 400 })`
- [x] Build prompt using the **verbatim** template from `TECHNICAL_DESIGN.md` Section 8.2
- [x] Call `callGemini(prompt)`
- [x] Parse response into `CompareResponse` — all five arrays always present, empty `[]` valid
- [x] Return `NextResponse.json(compareResponse)`
- [x] Wrap in try/catch — on error return HTTP 500 with `{ error: string }`

---

### T-26 — Implement Compare Response Parser

| Field | Value |
|---|---|
| **Status** | `[x]` |
| **Layer** | api |
| **File** | `app/api/compare/route.ts` |
| **Depends on** | T-25 |
| **AC Codes** | `AC-API-C-04`, `AC-PR-C-01`, `AC-PR-C-02`, `AC-PR-C-03` |

**Steps:**
- [x] Parse five sections by splitting on headers: `"MATCHING:"`, `"DIFFERENCES:"`, `"RISKS IN DOC A:"`, `"RISKS IN DOC B:"`, `"INCONSISTENCIES:"`
- [x] Within each section, split on `"\n- "` to produce `string[]`; filter empty strings
- [x] Return `CompareResponse` — all five keys always present (empty `[]` if section is missing)
- [x] Test: submit two identical documents — confirm `matching` array is non-empty

---

### T-27 — Build Compare Page

| Field | Value |
|---|---|
| **Status** | `[x]` |
| **Layer** | page |
| **File** | `app/compare/page.tsx` |
| **Depends on** | T-12, T-13, T-14, T-25 |
| **AC Codes** | `AC-COMP-01`, `AC-COMP-02`, `AC-COMP-03`, `AC-COMP-04` |

**Steps:**
- [x] Create `app/compare/page.tsx` as `"use client"`
- [x] Add `export const metadata` with unique title
- [x] Declare state: `contentA: DocumentContent | null`, `contentB: DocumentContent | null`, `result: CompareResponse | null`, `loading: boolean`, `error: string | null`, `validationError: string | null`
- [x] Render two `<FileOrTextInput>` components in a side-by-side layout, labelled "Document A" and "Document B"
- [x] On submit: if either `contentA` or `contentB` is `null`, set `validationError = "Please provide both documents."` — do NOT call the API
- [x] Show `validationError` as inline text below the submit button
- [x] On valid submit: build `FormData` with `doc1` and `doc2` fields; POST to `/api/compare`
- [x] Render five `<ResultCard>` sections in this order: "Matching Terms" (default), "Key Differences" (default), "Risks in Document A" (warning), "Risks in Document B" (warning), "Inconsistencies" (warning)
- [x] Content of each card: `array.join('\n')` or `"None identified."` if array is empty

---

## Phase 6 — Q&A Chat (`FEAT-03`)

> **Goal:** Two-phase chat interface works; document extraction, multi-turn history, and auto-scroll all function correctly.  
> **Prerequisite:** Phases 1, 2, 3 complete.

---

### T-28 — Implement `/api/extract` Route

| Field | Value |
|---|---|
| **Status** | `[x]` |
| **Layer** | api |
| **File** | `app/api/extract/route.ts` |
| **Depends on** | T-20 |
| **AC Codes** | `UC-04`, `UC-05` |

**Steps:**
- [x] Create `app/api/extract/route.ts`
- [x] Add `export const runtime = 'nodejs'`
- [x] Export `async function POST(req: Request)`
- [x] Call `extractTextFromRequest(req)`
- [x] Return `NextResponse.json({ text: extractedText })`
- [x] On error: return `NextResponse.json({ error: "..." }, { status: 400 })`

---

### T-29 — Implement `/api/chat` Route

| Field | Value |
|---|---|
| **Status** | `[x]` |
| **Layer** | api |
| **File** | `app/api/chat/route.ts` |
| **Depends on** | T-18 |
| **AC Codes** | `AC-API-CH-01`, `AC-API-CH-02`, `AC-API-CH-03`, `AC-API-CH-04`, `AC-API-CH-05`, `UC-02`, `UC-04` |

**Steps:**
- [x] Create `app/api/chat/route.ts`
- [x] Add `export const runtime = 'nodejs'`
- [x] Export `async function POST(req: Request)`
- [x] Parse JSON body into `ChatRequest` shape (`documentText`, `history`, `question`)
- [x] Validate: if `documentText` is empty, return `400 { error: "No document text provided." }`
- [x] Validate: if `question` is empty/blank, return `400 { error: "Question is required." }`
- [x] `history` may be empty array — valid
- [x] Build prompt using the **verbatim** template from `TECHNICAL_DESIGN.md` Section 8.3:
  - Prepend document context
  - Format history as `User: {text}\nAssistant: {text}` turns
  - End prompt with `Assistant:`
- [x] Call `callGemini(prompt)`
- [x] Return `NextResponse.json({ answer: responseText })`
- [x] Server MUST NOT store any state — all context provided by client per `UC-02`

---

### T-30 — Build Chat Page — Phase 1 (Document Load)

| Field | Value |
|---|---|
| **Status** | `[x]` |
| **Layer** | page |
| **File** | `app/chat/page.tsx` |
| **Depends on** | T-12, T-14, T-28 |
| **AC Codes** | `AC-CHAT-01`, `AC-CHAT-02` |

**Steps:**
- [x] Create `app/chat/page.tsx` as `"use client"`
- [x] Add `export const metadata` with unique title
- [x] Declare state: `phase: 'load' | 'chat'`, `documentContent: DocumentContent | null`, `documentText: string | null`, `loadError: string | null`
- [x] Render Phase 1 when `phase === 'load'`:
  - `<FileOrTextInput onContentReady={(c) => setDocumentContent(c)} />`
  - "Load Document" button — disabled when `documentContent === null`
  - On click: if `documentContent` is a `File`, POST to `/api/extract` with FormData; if string, use directly as `documentText`
  - On success: set `documentText`; set `phase = 'chat'`
  - On error: set `loadError` with human-readable message

---

### T-31 — Build Chat Page — Phase 2 (Chat Window)

| Field | Value |
|---|---|
| **Status** | `[x]` |
| **Layer** | page |
| **File** | `app/chat/page.tsx` |
| **Depends on** | T-30, T-29 |
| **AC Codes** | `AC-CHAT-03`, `AC-CHAT-04`, `AC-CHAT-05`, `AC-CHAT-06`, `AC-PR-CH-01`, `AC-PR-CH-02`, `AC-PR-CH-03`, `AC-PR-CH-04` |

**Steps:**
- [x] Declare additional state for Phase 2: `messages: ChatMessage[]`, `question: string`, `loading: boolean`, `chatError: string | null`
- [x] Render Phase 2 when `phase === 'chat'`:
  - Scrollable message list container with `useRef` attached (`messagesEndRef`)
  - Each user message: right-aligned, indigo background (`bg-indigo-600 text-white`)
  - Each model message: left-aligned, slate background (`bg-slate-100`)
  - `<textarea>` or `<input>` for question entry, bound to `question` state
  - "Send" button — disabled when `loading || question.trim() === ''`
- [x] On send:
  - Append `{ role: 'user', text: question }` to `messages` immediately (optimistic update)
  - Clear `question` input
  - Set `loading = true`
  - POST to `/api/chat` with `{ documentText, history: messages, question }`
  - Append `{ role: 'model', text: answer }` to `messages`
  - Set `loading = false`
- [x] Auto-scroll: call `messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })` after `messages` state updates (via `useEffect`)
- [x] Test: conduct a 3-turn conversation — verify history accumulates

---

## Phase 7 — Lawyer Prep (`FEAT-04`)

> **Goal:** Checklist generator works end-to-end with print support.  
> **Prerequisite:** Phases 1, 2, 3 complete.

---

### T-32 — Implement `/api/prep` Route

| Field | Value |
|---|---|
| **Status** | `[x]` |
| **Layer** | api |
| **File** | `app/api/prep/route.ts` |
| **Depends on** | T-18, T-20 |
| **AC Codes** | `AC-API-P-01`, `AC-API-P-02`, `AC-API-P-04`, `UC-04`, `UC-05` |

**Steps:**
- [x] Create `app/api/prep/route.ts`
- [x] Add `export const runtime = 'nodejs'`
- [x] Export `async function POST(req: Request)`
- [x] Call `extractTextFromRequest(req)`; if empty return `400 { error: "No document text provided." }`
- [x] Build prompt using the **verbatim** template from `TECHNICAL_DESIGN.md` Section 8.4
- [x] Call `callGemini(prompt)`
- [x] Parse response into `PrepResponse` — three sections with headers `QUESTIONS TO ASK:`, `DOCUMENTS TO BRING:`, `WATCH OUT FOR:`
- [x] All three arrays always present (empty `[]` valid)
- [x] Return `NextResponse.json(prepResponse)`

---

### T-33 — Implement Prep Response Parser & Quality Test

| Field | Value |
|---|---|
| **Status** | `[x]` |
| **Layer** | api |
| **File** | `app/api/prep/route.ts` |
| **Depends on** | T-32 |
| **AC Codes** | `AC-API-P-03`, `AC-PR-P-01`, `AC-PR-P-02`, `AC-PR-P-03` |

**Steps:**
- [x] Parser splits on `"\nQUESTIONS TO ASK:"`, `"\nDOCUMENTS TO BRING:"`, `"\nWATCH OUT FOR:"`
- [x] Within each section: split on `"\n- "`; filter empty strings
- [x] Manual test with a sample NDA: verify all three arrays have ≥ 1 item
- [x] Manual test: verify items reference actual document content, not generic advice

---

### T-34 — Build Lawyer Prep Page

| Field | Value |
|---|---|
| **Status** | `[x]` |
| **Layer** | page |
| **File** | `app/prep/page.tsx` |
| **Depends on** | T-12, T-14, T-32 |
| **AC Codes** | `AC-PREP-01`, `AC-PREP-02`, `AC-PREP-03`, `AC-PREP-04`, `AC-PREP-05`, `UC-01` |

**Steps:**
- [x] Create `app/prep/page.tsx` as `"use client"`
- [x] Add `export const metadata` with unique title
- [x] Declare state: `content: DocumentContent | null`, `result: PrepResponse | null`, `loading: boolean`, `error: string | null`
- [x] Render `<FileOrTextInput>`, submit button, `<LoadingSpinner>` when loading
- [x] When `result` is set, render three sections:
  - "Questions to Ask Your Lawyer" — items from `result.questions`
  - "Documents & Information to Bring" — items from `result.documents`
  - "Watch Out For" — items from `result.watchouts`
- [x] Each item rendered as: `<li className="flex items-center gap-2"><input type="checkbox" disabled /> {item}</li>`
- [x] "Print Checklist" button — rendered only when `result` is set; calls `window.print()`
- [x] Apply `print:hidden` to: Navbar wrapper, DisclaimerBanner wrapper, submit area, Print button
- [x] Apply `print:block` to checklist result sections if they might be `hidden` in screen CSS
- [x] Test: open browser print preview — confirm Navbar absent, checklist visible

---

## Phase 8 — Polish, Security & Deployment

> **Goal:** Full production-ready state: passing build, security clean, accessibility verified, README complete, deployed.  
> **Prerequisite:** Phases 1–7 complete.

---

### T-35 — Add Per-Page Metadata

| Field | Value |
|---|---|
| **Status** | `[x]` |
| **Layer** | page |
| **File** | `app/simplify/page.tsx`, `app/compare/page.tsx`, `app/chat/page.tsx`, `app/prep/page.tsx` |
| **Depends on** | T-24, T-27, T-31, T-34 |
| **AC Codes** | `AC-A11Y-03` |

**Steps:**
- [x] Each feature page exports a `metadata` object with a unique `title` and `description`
- [x] Titles: "Simplify Document — LexAid", "Compare Contracts — LexAid", "Chat with Document — LexAid", "Lawyer Prep Checklist — LexAid"

---

### T-36 — Create `vercel.json`

| Field | Value |
|---|---|
| **Status** | `[x]` |
| **Layer** | config |
| **File** | `vercel.json` |
| **Depends on** | T-01 |
| **AC Codes** | `AC-VCL-01`, `AC-VCL-02` |

**Steps:**
- [x] Create `vercel.json` at project root with exact content from `TECHNICAL_DESIGN.md` Section 10.3
- [x] Verify `maxDuration: 30` applies to all `app/api/**/*.ts` routes

---

### T-37 — Update `README.md`

| Field | Value |
|---|---|
| **Status** | `[x]` |
| **Layer** | deploy |
| **File** | `README.md` |
| **Depends on** | T-01 |
| **AC Codes** | `AC-README-01`, `AC-README-02` |

**Steps:**
- [x] Add all 8 required sections per `TECHNICAL_DESIGN.md` Section 13.3:
  1. Project title & description
  2. Features (bullet list of all four with one-line descriptions)
  3. Tech stack
  4. Prerequisites (Node.js ≥ 18, npm, Gemini API key)
  5. Local setup (`git clone`, `npm install`, `.env.local`, `npm run dev`)
  6. Environment variables table
  7. Deployment (Vercel connect, env var setup, deploy)
  8. Disclaimer notice
- [x] Verify setup steps can be followed in < 5 minutes by a new developer

---

### T-38 — Final Build Verification

| Field | Value |
|---|---|
| **Status** | `[x]` |
| **Layer** | test |
| **File** | — |
| **Depends on** | T-35, T-36, T-37 |
| **AC Codes** | `AC-BUILD-01`, `AC-BUILD-02`, `AC-BUILD-03`, `AC-TYPES-03` |

**Steps:**
- [x] Run `npm run build` — confirm exit code 0
- [x] Confirm zero TypeScript errors in output
- [x] Confirm no `serverExternalPackages` warning
- [x] Run `tsc --noEmit` — zero errors

---

### T-39 — Security Verification

| Field | Value |
|---|---|
| **Status** | `[x]` |
| **Layer** | test |
| **File** | — |
| **Depends on** | T-38 |
| **AC Codes** | `AC-SEC-01`, `AC-SEC-02`, `AC-SEC-03`, `UC-03` |

**Steps:**
- [x] Run `grep -r "GEMINI_API_KEY" .next/static/` — confirm zero results
- [x] Run `grep -r "@google/generative-ai" components/` — confirm zero results
- [x] Run `grep -r "@google/generative-ai" app/` — confirm zero results (only `lib/gemini.ts` should import it)

---

### T-40 — Accessibility Verification

| Field | Value |
|---|---|
| **Status** | `[x]` |
| **Layer** | test |
| **File** | — |
| **Depends on** | T-38 |
| **AC Codes** | `AC-A11Y-01`, `AC-A11Y-02`, `AC-A11Y-03`, `AC-A11Y-04`, `UC-06` |

**Steps:**
- [x] All `<FileOrTextInput>` inputs have visible `<label>` elements
- [x] `<LoadingSpinner>` has `role="status"` in DOM
- [x] Each page has a unique `<title>` tag (check browser tab)
- [x] Tab-key test: navigate every page — all interactive elements reachable without mouse

---

### T-41 — Input Validation Verification

| Field | Value |
|---|---|
| **Status** | `[x]` |
| **Layer** | test |
| **File** | — |
| **Depends on** | T-24, T-27, T-31, T-34 |
| **AC Codes** | `AC-INP-01`, `AC-INP-02`, `AC-INP-03` |

**Steps:**
- [x] Verify all file inputs have `accept=".pdf"` attribute
- [x] Attempt to upload a `.txt` file — confirm browser blocks it
- [x] Submit a 50,000-character text document — confirm processed without error, results returned

---

### T-42 — Reliability Verification

| Field | Value |
|---|---|
| **Status** | `[x]` |
| **Layer** | test |
| **File** | — |
| **Depends on** | T-22, T-25, T-29, T-32 |
| **AC Codes** | `AC-REL-01`, `AC-REL-02`, `UC-04` |

**Steps:**
- [x] Temporarily remove `GEMINI_API_KEY` from `.env.local`; submit a document — verify page shows human-readable error, not a stack trace
- [x] Verify API routes return `{ error: string }` for all four error scenarios in `TECHNICAL_DESIGN.md` Section 11.3
- [x] Re-add `GEMINI_API_KEY`

---

### T-43 — Vercel Deployment

| Field | Value |
|---|---|
| **Status** | `[x]` |
| **Layer** | deploy |
| **File** | — |
| **Depends on** | T-38, T-39, T-40 |
| **AC Codes** | `AC-DEPLOY-01`, `AC-DEPLOY-02`, `AC-DEPLOY-03`, `AC-DEPLOY-04`, `AC-DEPLOY-05` |

**Steps:**
- [x] Connect GitHub repository to Vercel project
- [x] Set `GEMINI_API_KEY` in Vercel project Settings → Environment Variables (Production)
- [x] Trigger deployment — confirm build passes (`AC-DEPLOY-01`, `AC-DEPLOY-02`)
- [x] Verify all four feature pages load on the production URL (`AC-DEPLOY-03`)
- [x] Smoke test each feature with a sample legal document on production (`AC-DEPLOY-04`)
- [x] Confirm Vercel Functions dashboard shows `maxDuration: 30` for API routes (`AC-DEPLOY-05`)

---

## Task Summary

| Phase | Tasks | Files Created |
|---|---|---|
| 1 — Scaffold & Config | T-01 to T-09 | `package.json`, `next.config.ts`, `tailwind.config.ts`, `.env.example`, `types/index.ts` |
| 2 — Shared UI | T-10 to T-17 | `components/Navbar.tsx`, `DisclaimerBanner.tsx`, `FileOrTextInput.tsx`, `ResultCard.tsx`, `LoadingSpinner.tsx`, `app/layout.tsx`, `app/page.tsx` |
| 3 — Server Utilities | T-18 to T-21 | `lib/gemini.ts`, `lib/parsePdf.ts`, `lib/extractText.ts` |
| 4 — Simplifier | T-22 to T-24 | `app/api/simplify/route.ts`, `app/simplify/page.tsx` |
| 5 — Comparator | T-25 to T-27 | `app/api/compare/route.ts`, `app/compare/page.tsx` |
| 6 — Q&A Chat | T-28 to T-31 | `app/api/extract/route.ts`, `app/api/chat/route.ts`, `app/chat/page.tsx` |
| 7 — Lawyer Prep | T-32 to T-34 | `app/api/prep/route.ts`, `app/prep/page.tsx` |
| 8 — Polish & Deploy | T-35 to T-43 | `vercel.json`, `README.md` (updated) |

**Total tasks: 43**  
**Total files created/modified: 24**

---

## Dependency Graph

```
Phase 1 (T-01 → T-09)
    │
    ├── Phase 2 (T-10 → T-17)   [needs T-08 for types]
    │
    ├── Phase 3 (T-18 → T-21)   [needs T-08 for types, T-02/T-03 for deps]
    │         │
    │         ├── Phase 4 (T-22 → T-24)   [needs T-18, T-20, T-12, T-13, T-14]
    │         │
    │         ├── Phase 5 (T-25 → T-27)   [needs T-18, T-19, T-20, T-12, T-13, T-14]
    │         │
    │         ├── Phase 6 (T-28 → T-31)   [needs T-18, T-20, T-12, T-14]
    │         │
    │         └── Phase 7 (T-32 → T-34)   [needs T-18, T-20, T-12, T-14]
    │
    └── Phase 8 (T-35 → T-43)   [needs Phases 4–7 complete]
```

Phases 4, 5, 6, and 7 can be worked in parallel once Phases 1, 2, and 3 are complete.
