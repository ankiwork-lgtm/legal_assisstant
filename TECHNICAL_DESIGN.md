# LexAid — Technical Design Document (Spec-Driven)

> **Project:** GenAI-Powered Legal Assistant  
> **Deployment Target:** Vercel  
> **Approach:** Spec-Driven Development — every section defines *what* must be true, not *how* to build it. Implementation is complete when all acceptance criteria pass.  
> **Status:** Approved — ready for implementation  

---

## How to Use This Document

This document follows **Spec-Driven Development (SDD)**. Each section defines:

1. **Specification** — the precise contract a unit must satisfy (types, inputs, outputs, constraints)
2. **Acceptance Criteria** — observable, testable conditions that confirm the spec is met
3. **Error Contracts** — exact error shapes and HTTP codes for every failure mode

Implementors write code to satisfy the spec. Reviewers verify against acceptance criteria. Nothing is "done" until every criterion for a section is checkable.

---

## Table of Contents

1. [Product Specification](#1-product-specification)
2. [Technology Contracts](#2-technology-contracts)
3. [Shared Type Definitions](#3-shared-type-definitions)
4. [Directory & File Contract](#4-directory--file-contract)
5. [Component Specifications](#5-component-specifications)
6. [API Route Specifications](#6-api-route-specifications)
7. [Server-Side Utility Specifications](#7-server-side-utility-specifications)
8. [AI Prompt Specifications](#8-ai-prompt-specifications)
9. [Page Specifications](#9-page-specifications)
10. [Configuration Specifications](#10-configuration-specifications)
11. [Non-Functional Specifications](#11-non-functional-specifications)
12. [Security Specifications](#12-security-specifications)
13. [Deployment Specification](#13-deployment-specification)

---

## 1. Product Specification

### 1.1 Purpose

LexAid SHALL provide non-lawyers with a free, accessible tool to understand, compare, and prepare around legal documents — without replacing professional legal advice.

### 1.2 Feature Registry

Each feature has a unique ID used throughout this document for traceability.

| Feature ID | Name | One-line Spec |
|---|---|---|
| `FEAT-01` | Document Simplifier | Given a legal document, produce a plain-English summary and a labelled list of key clauses with risk flags |
| `FEAT-02` | Contract Comparator | Given two legal documents, produce a structured diff of obligations, risks, and inconsistencies |
| `FEAT-03` | Q&A Chat | Given a legal document and a multi-turn conversation history, answer questions grounded only in that document |
| `FEAT-04` | Lawyer Prep | Given a legal document, produce a printable three-section checklist for a lawyer consultation |

### 1.3 Universal Constraints

All four features MUST satisfy the following constraints. These are tested as cross-cutting acceptance criteria.

| ID | Constraint |
|---|---|
| `UC-01` | Every rendered page MUST display the disclaimer text defined in Section 5.2 |
| `UC-02` | No document content MUST be written to any persistent storage |
| `UC-03` | `GEMINI_API_KEY` MUST NOT appear in any client-side bundle or network response |
| `UC-04` | All API routes MUST return `{ error: string }` with an appropriate HTTP status code on failure |
| `UC-05` | Document text sent to Gemini MUST be truncated to `MAX_CHARS` (40,000) before the API call |
| `UC-06` | All pages MUST be reachable by keyboard navigation alone |

---

## 2. Technology Contracts

The following dependencies are fixed. Substitutions require a plan revision.

| Contract ID | Dependency | Version Constraint | Reason for Lock |
|---|---|---|---|
| `TC-01` | Next.js | `^14.0.0` (App Router) | Vercel-native; App Router required for `route.ts` API conventions |
| `TC-02` | TypeScript | `^5.0.0` | Strict mode enabled; all shared data shapes defined as interfaces |
| `TC-03` | Tailwind CSS | `^3.0.0` | Only styling mechanism; no CSS-in-JS, no component library |
| `TC-04` | `@google/generative-ai` | `latest` | Official Google SDK; `generateContent` API |
| `TC-05` | Gemini model | `gemini-2.0-flash` | Fixed model name string used in `lib/gemini.ts`; change requires plan revision |
| `TC-06` | `pdf-parse` | `latest` | Server-side only; MUST be in `serverExternalPackages` |
| `TC-07` | `@types/pdf-parse` | `latest` | Dev dependency for TypeScript types |

### 2.1 Prohibited Dependencies

The following are explicitly prohibited to keep the bundle lean and the implementation focused:

- Any CSS-in-JS library (styled-components, Emotion, etc.)
- Any UI component library (shadcn, MUI, Chakra, etc.)
- Any markdown rendering library (react-markdown, etc.)
- Any client-side state management library (Redux, Zustand, etc.)
- Any ORM or database client

---

## 3. Shared Type Definitions

All types below MUST be defined in `types/index.ts` and imported wherever used. Using inline or duplicate type definitions is not permitted.

```typescript
// types/index.ts

// ── Document Input ──────────────────────────────────────────────────────────

/** Represents the content ready to submit to an API route */
export type DocumentContent = File | string;

// ── API Request Bodies ───────────────────────────────────────────────────────

export interface SimplifyRequest {
  text: string; // used when content-type is application/json
}

export interface CompareRequest {
  text1: string;
  text2: string;
}

export interface ChatRequest {
  documentText: string;
  history: ChatMessage[];
  question: string;
}

export interface PrepRequest {
  text: string;
}

// ── API Response Bodies ──────────────────────────────────────────────────────

export interface SimplifyResponse {
  summary: string;
  clauses: Clause[];
}

export interface Clause {
  label: string;   // e.g. "Termination Clause"
  text: string;    // plain-English explanation
  risk: boolean;   // true when Gemini flags with ⚠️ RISK
}

export interface CompareResponse {
  matching: string[];
  differences: string[];
  risksA: string[];
  risksB: string[];
  inconsistencies: string[];
}

export interface ChatResponse {
  answer: string;
}

export interface PrepResponse {
  questions: string[];
  documents: string[];
  watchouts: string[];
}

export interface ApiError {
  error: string;
}

// ── Chat ─────────────────────────────────────────────────────────────────────

export interface ChatMessage {
  role: 'user' | 'model';
  text: string;
}

// ── Component Props ──────────────────────────────────────────────────────────

export interface FileOrTextInputProps {
  label?: string;
  onContentReady: (content: DocumentContent) => void;
}

export interface ResultCardProps {
  title: string;
  content: string;
  variant?: 'default' | 'warning' | 'info';
}

export interface LoadingSpinnerProps {
  label?: string;
}
```

### 3.1 Type Acceptance Criteria

- [ ] `AC-TYPES-01`: `types/index.ts` exports all types above with no compilation errors under `strict: true`
- [ ] `AC-TYPES-02`: No API route or component file defines a type that duplicates one in `types/index.ts`
- [ ] `AC-TYPES-03`: `tsc --noEmit` passes with zero errors across the entire project

---

## 4. Directory & File Contract

The following files MUST exist at the specified paths. Deviating from these paths breaks imports defined in this spec.

```
legal_assisstant/
├── types/
│   └── index.ts                    # Section 3 — all shared types
├── app/
│   ├── layout.tsx                  # Section 9.1
│   ├── page.tsx                    # Section 9.2
│   ├── globals.css                 # Tailwind directives only
│   ├── simplify/page.tsx           # Section 9.3
│   ├── compare/page.tsx            # Section 9.4
│   ├── chat/page.tsx               # Section 9.5
│   ├── prep/page.tsx               # Section 9.6
│   └── api/
│       ├── simplify/route.ts       # Section 6.1
│       ├── compare/route.ts        # Section 6.2
│       ├── chat/route.ts           # Section 6.3
│       └── prep/route.ts           # Section 6.4
├── components/
│   ├── Navbar.tsx                  # Section 5.1
│   ├── DisclaimerBanner.tsx        # Section 5.2
│   ├── FileOrTextInput.tsx         # Section 5.3
│   ├── ResultCard.tsx              # Section 5.4
│   └── LoadingSpinner.tsx          # Section 5.5
├── lib/
│   ├── gemini.ts                   # Section 7.1
│   ├── parsePdf.ts                 # Section 7.2
│   └── extractText.ts             # Section 7.3
├── public/                         # Static assets
├── .env.example
├── next.config.ts                  # Section 10.1
├── tailwind.config.ts              # Section 10.2
├── postcss.config.js
├── tsconfig.json
├── vercel.json                     # Section 10.3
└── README.md
```

### 4.1 File Contract Acceptance Criteria

- [ ] `AC-DIR-01`: All files listed above exist at the exact paths shown
- [ ] `AC-DIR-02`: No `"use client"` directive appears in any file under `lib/`
- [ ] `AC-DIR-03`: No file under `lib/` or `app/api/` imports from `components/`

---

## 5. Component Specifications

### 5.1 `Navbar` — `components/Navbar.tsx`

**Spec:** Renders a persistent top navigation bar visible on every page.

| Property | Value |
|---|---|
| React type | Client Component (`"use client"` — required for `usePathname`) |
| Props | None |
| DOM output | `<nav>` element containing 5 `<a>` or `<Link>` elements |

**Navigation Link Contract:**

| Link text | `href` | Active when pathname is |
|---|---|---|
| LexAid (logo/brand) | `/` | `/` |
| Simplify | `/simplify` | `/simplify` |
| Compare | `/compare` | `/compare` |
| Chat | `/chat` | `/chat` |
| Lawyer Prep | `/prep` | `/prep` |

**Active state spec:** The link matching the current pathname MUST receive a visually distinct style (e.g. `font-semibold underline`) compared to inactive links.

**Tailwind class contract:** Root element MUST include `bg-slate-900 text-white`.

**Acceptance Criteria:**
- [ ] `AC-NAV-01`: All 5 links render and are focusable via keyboard Tab
- [ ] `AC-NAV-02`: Active link is visually distinct from inactive links when pathname matches
- [ ] `AC-NAV-03`: `<nav>` element is present (semantic HTML requirement)
- [ ] `AC-NAV-04`: Component has no TypeScript errors

---

### 5.2 `DisclaimerBanner` — `components/DisclaimerBanner.tsx`

**Spec:** Renders a full-width, always-visible legal disclaimer strip.

| Property | Value |
|---|---|
| React type | Server Component |
| Props | None |
| Placement | Immediately below `<Navbar>` in `app/layout.tsx`, above `{children}` |

**Required disclaimer text (verbatim):**

> ⚖️ This tool provides general legal information only and does not constitute legal advice. The information generated is based on AI analysis and may not be accurate, complete, or applicable to your specific situation. Consult a qualified lawyer for advice specific to your circumstances. Do not upload documents containing sensitive personal information.

**Tailwind class contract:** Root element MUST include `bg-amber-50 border-b border-amber-200 text-amber-800`.

**Acceptance Criteria:**
- [ ] `AC-DISC-01`: Banner renders on every page (verified via `app/layout.tsx` inclusion)
- [ ] `AC-DISC-02`: The exact disclaimer text above is present in the rendered HTML
- [ ] `AC-DISC-03`: Banner is visible without scrolling on all screen widths ≥ 320px

---

### 5.3 `FileOrTextInput` — `components/FileOrTextInput.tsx`

**Spec:** A dual-mode document input component that accepts either a PDF file upload or pasted plain text, and notifies the parent when content is ready.

| Property | Value |
|---|---|
| React type | Client Component (`"use client"`) |
| Props | `FileOrTextInputProps` (from `types/index.ts`) |
| Emits | `onContentReady(content: File \| string)` |

**Internal State Contract:**

```typescript
type ActiveTab = 'upload' | 'text';

const [activeTab, setActiveTab] = useState<ActiveTab>('upload');
const [textValue, setTextValue] = useState<string>('');
const [fileName, setFileName] = useState<string>('');
```

**Behaviour Contract by Tab:**

| Tab | Trigger | `onContentReady` called with |
|---|---|---|
| Upload PDF | User selects a `.pdf` file | `File` object |
| Paste Text | User types/pastes in `<textarea>` | Current `string` value on every change |

**Constraints:**
- File input MUST have `accept=".pdf"` attribute
- When the user switches tabs, the other tab's value MUST be cleared (both `fileName` and `textValue` reset)
- The selected file name MUST be displayed below the file input when a file is chosen
- The `<textarea>` MUST have `rows={10}` minimum

**Acceptance Criteria:**
- [ ] `AC-FTI-01`: Uploading a `.pdf` file triggers `onContentReady` with a `File` instance
- [ ] `AC-FTI-02`: Typing in the textarea triggers `onContentReady` with the current string
- [ ] `AC-FTI-03`: Switching from Upload to Text tab clears the file name display
- [ ] `AC-FTI-04`: Switching from Text to Upload tab clears the textarea
- [ ] `AC-FTI-05`: File input `accept` attribute is `.pdf`
- [ ] `AC-FTI-06`: Component has no TypeScript errors against `FileOrTextInputProps`

---

### 5.4 `ResultCard` — `components/ResultCard.tsx`

**Spec:** A presentational card that displays a titled section of AI output with preserved formatting.

| Property | Value |
|---|---|
| React type | Server Component |
| Props | `ResultCardProps` (from `types/index.ts`) |

**Variant Contract:**

| `variant` value | Visual treatment |
|---|---|
| `'default'` (or omitted) | White background, slate border |
| `'warning'` | Amber background (`bg-amber-50`), amber border (`border-amber-300`) |
| `'info'` | Blue background (`bg-blue-50`), blue border (`border-blue-300`) |

**Content rendering spec:** The `content` prop MUST be rendered inside an element with `whitespace-pre-wrap` applied. No markdown parsing library is used.

**Acceptance Criteria:**
- [ ] `AC-RC-01`: `title` prop renders in a visually distinct heading element
- [ ] `AC-RC-02`: `content` prop renders with newlines preserved (`whitespace-pre-wrap`)
- [ ] `AC-RC-03`: `variant='warning'` applies amber background and border
- [ ] `AC-RC-04`: Component renders with no TypeScript errors against `ResultCardProps`

---

### 5.5 `LoadingSpinner` — `components/LoadingSpinner.tsx`

**Spec:** An animated loading indicator with an optional descriptive label.

| Property | Value |
|---|---|
| React type | Server Component |
| Props | `LoadingSpinnerProps` (from `types/index.ts`) |

**Behaviour Contract:**
- MUST render a CSS `animate-spin` ring using Tailwind classes
- When `label` prop is provided, MUST render the label text visibly below the spinner
- MUST have `role="status"` on the spinner element for accessibility
- MUST have an `aria-label` of `"Loading"` (or the `label` prop value if provided)

**Acceptance Criteria:**
- [ ] `AC-LS-01`: Spinner element has `animate-spin` class applied
- [ ] `AC-LS-02`: `role="status"` is present on the spinner wrapper
- [ ] `AC-LS-03`: Label text renders when `label` prop is supplied
- [ ] `AC-LS-04`: Component has no TypeScript errors

---

## 6. API Route Specifications

### Global API Route Contract

Every file under `app/api/` MUST satisfy:

| Requirement | Value |
|---|---|
| Runtime export | `export const runtime = 'nodejs'` at file top level |
| Accepted HTTP method | `POST` only; respond `405 Method Not Allowed` for all others |
| Success response | `Content-Type: application/json`, HTTP 200 |
| Client error response | `{ error: string }`, HTTP 400 |
| Server error response | `{ error: string }`, HTTP 500 |
| Gemini key absent | `{ error: "AI service is not configured." }`, HTTP 500 |
| Empty document | `{ error: "No document text provided." }`, HTTP 400 |

---

### 6.1 `POST /api/simplify` — `app/api/simplify/route.ts`

**Feature:** `FEAT-01`

#### Request Contract

| Format | Fields |
|---|---|
| `multipart/form-data` | `file`: PDF `File` |
| `application/json` | `{ text: string }` |

#### Response Contract

Success — HTTP 200:
```typescript
// Matches SimplifyResponse from types/index.ts
{
  summary: string;
  clauses: Array<{
    label: string;
    text: string;
    risk: boolean;
  }>;
}
```

#### Processing Contract

| Step | Spec |
|---|---|
| 1 | Call `extractTextFromRequest(req)` — delegates content-type handling |
| 2 | If returned string length is 0, return `400 { error: "No document text provided." }` |
| 3 | Build prompt using the template in Section 8.1 |
| 4 | Call `callGemini(prompt)` |
| 5 | Parse Gemini response using the parsing rules in Section 8.1 |
| 6 | Return `SimplifyResponse` as JSON |

#### Acceptance Criteria

- [ ] `AC-API-S-01`: POST with a valid PDF returns HTTP 200 with `summary` (non-empty string) and `clauses` (array with ≥ 1 item)
- [ ] `AC-API-S-02`: POST with valid JSON `{ text }` returns same shape as above
- [ ] `AC-API-S-03`: POST with no body returns HTTP 400 `{ error: "No document text provided." }`
- [ ] `AC-API-S-04`: Each item in `clauses` has `label`, `text`, and `risk` fields
- [ ] `AC-API-S-05`: `risk: true` on at least one clause when the document contains unusual terms (tested with a known risky contract sample)
- [ ] `AC-API-S-06`: `export const runtime = 'nodejs'` is present at the top of the file

---

### 6.2 `POST /api/compare` — `app/api/compare/route.ts`

**Feature:** `FEAT-02`

#### Request Contract

| Format | Fields |
|---|---|
| `multipart/form-data` | `doc1`: PDF `File` or text string; `doc2`: PDF `File` or text string |
| `application/json` | `{ text1: string, text2: string }` |

#### Response Contract

Success — HTTP 200:
```typescript
// Matches CompareResponse from types/index.ts
{
  matching: string[];
  differences: string[];
  risksA: string[];
  risksB: string[];
  inconsistencies: string[];
}
```

#### Processing Contract

| Step | Spec |
|---|---|
| 1 | Extract `doc1`/`doc2` (or `text1`/`text2`) independently |
| 2 | Parse each as PDF if a `File`, else use raw string |
| 3 | Truncate each text to `MAX_CHARS` separately |
| 4 | If either text is empty, return `400 { error: "Both documents are required." }` |
| 5 | Build prompt using template in Section 8.2 |
| 6 | Call `callGemini(prompt)` |
| 7 | Parse into `CompareResponse`; empty array `[]` is valid for any section |
| 8 | Return as JSON |

#### Acceptance Criteria

- [ ] `AC-API-C-01`: POST with two valid docs returns HTTP 200 with all five arrays present
- [ ] `AC-API-C-02`: Each of the five arrays contains only `string` elements
- [ ] `AC-API-C-03`: Submitting only one document returns HTTP 400 `{ error: "Both documents are required." }`
- [ ] `AC-API-C-04`: Submitting identical documents results in a non-empty `matching` array
- [ ] `AC-API-C-05`: `export const runtime = 'nodejs'` is present

---

### 6.3 `POST /api/chat` — `app/api/chat/route.ts`

**Feature:** `FEAT-03`

#### Request Contract

```typescript
// application/json only — no file upload on this route
{
  documentText: string;   // full extracted text (truncated client-side to MAX_CHARS)
  history: ChatMessage[]; // from types/index.ts
  question: string;       // the new user question
}
```

#### Response Contract

Success — HTTP 200:
```typescript
// Matches ChatResponse from types/index.ts
{ answer: string }
```

#### Processing Contract

| Step | Spec |
|---|---|
| 1 | Parse JSON body |
| 2 | Validate `documentText` is non-empty and `question` is non-empty |
| 3 | `history` MAY be an empty array on the first turn |
| 4 | Build prompt using template in Section 8.3 |
| 5 | Call `callGemini(prompt)` |
| 6 | Return `{ answer: responseText }` |

**Statefulness contract:** The server MUST NOT store any session state. All context is provided by the client on every request.

#### Acceptance Criteria

- [ ] `AC-API-CH-01`: First-turn POST (`history: []`) returns HTTP 200 `{ answer: string }`
- [ ] `AC-API-CH-02`: Multi-turn POST with `history` containing prior turns returns an answer that references prior context (manually verified)
- [ ] `AC-API-CH-03`: POST with empty `question` returns HTTP 400 `{ error: "Question is required." }`
- [ ] `AC-API-CH-04`: POST with empty `documentText` returns HTTP 400 `{ error: "No document text provided." }`
- [ ] `AC-API-CH-05`: `export const runtime = 'nodejs'` is present

---

### 6.4 `POST /api/prep` — `app/api/prep/route.ts`

**Feature:** `FEAT-04`

#### Request Contract

| Format | Fields |
|---|---|
| `multipart/form-data` | `file`: PDF `File` |
| `application/json` | `{ text: string }` |

#### Response Contract

Success — HTTP 200:
```typescript
// Matches PrepResponse from types/index.ts
{
  questions: string[];
  documents: string[];
  watchouts: string[];
}
```

#### Processing Contract

| Step | Spec |
|---|---|
| 1 | Call `extractTextFromRequest(req)` |
| 2 | If text is empty, return HTTP 400 |
| 3 | Build prompt using template in Section 8.4 |
| 4 | Call `callGemini(prompt)` |
| 5 | Parse three-section response into three `string[]` arrays |
| 6 | Return `PrepResponse` as JSON |

#### Acceptance Criteria

- [x] `AC-API-P-01`: POST with valid doc returns HTTP 200 with all three arrays present
- [x] `AC-API-P-02`: Each array has ≥ 1 item for any non-trivial legal document
- [x] `AC-API-P-03`: Items are document-specific (contain references to actual document content), not generic advice — manually verified with a sample document
- [x] `AC-API-P-04`: `export const runtime = 'nodejs'` is present

---

## 7. Server-Side Utility Specifications

### 7.1 `lib/gemini.ts`

**Spec:** Provides a single callable interface to the Gemini API. All API routes MUST call this function — direct SDK calls in route files are prohibited.

#### Export Contract

```typescript
export async function callGemini(prompt: string): Promise<string>
```

#### Behaviour Contract

| Condition | Behaviour |
|---|---|
| `GEMINI_API_KEY` is set | Calls `gemini-2.0-flash` with the prompt, returns response text |
| `GEMINI_API_KEY` is missing | Throws `Error("GEMINI_API_KEY is not set")` |
| Gemini returns an empty response | Throws `Error("Empty response from Gemini")` |
| Gemini API call fails | Re-throws the SDK error (route catches and returns HTTP 500) |

**Implementation constraint:** `GEMINI_API_KEY` MUST be read inside the function body (`process.env.GEMINI_API_KEY`), NOT at module initialisation time.

#### Acceptance Criteria

- [ ] `AC-GEM-01`: Called with a non-empty prompt and valid env key, returns a non-empty string
- [ ] `AC-GEM-02`: When `GEMINI_API_KEY` is undefined, throws with message `"GEMINI_API_KEY is not set"`
- [ ] `AC-GEM-03`: Model string `"gemini-2.0-flash"` is a named constant in this file
- [ ] `AC-GEM-04`: No `"use client"` directive is present

---

### 7.2 `lib/parsePdf.ts`

**Spec:** Wraps `pdf-parse` to produce plain text from a Node.js `Buffer`. No business logic — pure I/O wrapper.

#### Export Contract

```typescript
export async function parsePdf(buffer: Buffer): Promise<string>
```

#### Behaviour Contract

| Input | Output |
|---|---|
| Valid PDF buffer | Extracted plain text string (may include whitespace/newlines from layout) |
| Empty buffer | Throws `Error("PDF buffer is empty")` |
| Non-PDF buffer | `pdf-parse` will throw; error is allowed to propagate |

#### Acceptance Criteria

- [ ] `AC-PDF-01`: Calling with a valid PDF buffer returns a non-empty string containing readable text
- [ ] `AC-PDF-02`: Calling with an empty `Buffer.alloc(0)` throws `Error("PDF buffer is empty")`
- [ ] `AC-PDF-03`: No `"use client"` directive is present
- [ ] `AC-PDF-04`: Function does not truncate — truncation is the responsibility of `extractText.ts`

---

### 7.3 `lib/extractText.ts`

**Spec:** Normalises an incoming HTTP `Request` into a plain text string, handling both `multipart/form-data` (PDF upload) and `application/json` (text paste) content types.

#### Export Contract

```typescript
export const MAX_CHARS = 40000;

export async function extractTextFromRequest(req: Request): Promise<string>
```

#### Behaviour Contract

| `Content-Type` | Field/Body | Behaviour |
|---|---|---|
| `multipart/form-data` | `file` field present, is PDF | Parse PDF → truncate to `MAX_CHARS` → return |
| `multipart/form-data` | `file` field absent | Throw `Error("No file provided in form data")` |
| `application/json` | `{ text: string }` | Return `text.slice(0, MAX_CHARS)` |
| `application/json` | `text` field absent or empty | Throw `Error("No text provided in request body")` |
| Anything else | — | Throw `Error("Unsupported content type")` |

**Truncation contract:** Any string longer than `MAX_CHARS` (40,000 characters) MUST be silently truncated to exactly `MAX_CHARS`. No error is thrown for over-limit inputs.

#### Acceptance Criteria

- [ ] `AC-ET-01`: A `multipart/form-data` request with a PDF file returns extracted text ≤ 40,000 chars
- [ ] `AC-ET-02`: A `application/json` request with `{ text: "hello" }` returns `"hello"`
- [ ] `AC-ET-03`: A text of 50,000 characters is returned as exactly 40,000 characters
- [ ] `AC-ET-04`: A request with no `file` field throws with message `"No file provided in form data"`
- [ ] `AC-ET-05`: `MAX_CHARS` is exported as a named constant with value `40000`
- [ ] `AC-ET-06`: No `"use client"` directive is present

---

## 8. AI Prompt Specifications

### Prompt Structure Contract

All prompts MUST follow this four-part structure:

```
[ROLE CONTEXT]       ← one sentence establishing Gemini's persona
[DOCUMENT INPUT]     ← the document text, clearly labelled
[TASK INSTRUCTIONS]  ← numbered list of what to do
[OUTPUT FORMAT]      ← exact section headers and format Gemini must follow
```

The output format MUST use uppercase section headers (e.g. `SUMMARY:`, `CLAUSE:`) rather than raw JSON. This is specified because large language models more reliably follow header-based formatting than JSON schema constraints.

### Response Parsing Contract

All response parsers MUST:
1. Split the raw string on exact section headers (case-sensitive)
2. Strip leading/trailing whitespace from each extracted segment
3. For bulleted lists: split on `\n- ` to extract items, filter empty strings
4. Return typed objects matching the shapes in Section 3

---

### 8.1 Document Simplifier Prompt — `FEAT-01`

#### Prompt Template

```
You are a legal document analyst. Your task is to help a non-lawyer understand the following legal document.

DOCUMENT:
{documentText}

INSTRUCTIONS:
1. Write a plain-English summary of what this document is about and what it means for the parties involved. Use simple language a non-lawyer can understand.
2. Identify and explain the key clauses. For each clause provide:
   - A short descriptive label (e.g. "Termination Clause", "Payment Terms")
   - A plain-English explanation of what it means
   - Whether it contains unusual, unfair, or high-risk terms (mark these with ⚠️ RISK)
3. Focus on: parties and roles, obligations, payment terms, deadlines, penalties, termination rights, liability limitations.

OUTPUT FORMAT (use exactly these headers):
SUMMARY:
[your plain-English summary here]

CLAUSE: [Label]
[Plain-English explanation. End with ⚠️ RISK if this clause is unusual or high-risk.]

CLAUSE: [Label]
[Plain-English explanation. End with ⚠️ RISK if this clause is unusual or high-risk.]
```

#### Response Parsing Rules

| Parse step | Rule |
|---|---|
| Extract summary | Substring from `"SUMMARY:\n"` to the first `"CLAUSE:"` |
| Extract clauses | Split on `"\nCLAUSE: "` to get an array of clause blocks |
| Parse clause label | First line of each clause block |
| Parse clause text | Remaining lines joined |
| Set `risk: true` | When clause text contains `"⚠️ RISK"` |

#### Acceptance Criteria

- [ ] `AC-PR-S-01`: Prompt template is used verbatim (no inline modifications in route code)
- [ ] `AC-PR-S-02`: Parser returns `SimplifyResponse` that matches `types/index.ts`
- [ ] `AC-PR-S-03`: `summary` is a non-empty string when a valid document is provided
- [ ] `AC-PR-S-04`: `clauses` contains ≥ 1 item for any non-trivial document

---

### 8.2 Contract Comparator Prompt — `FEAT-02`

#### Prompt Template

```
You are a legal contract analyst. Compare the following two legal documents and identify similarities, differences, and risks.

DOCUMENT A:
{text1}

DOCUMENT B:
{text2}

INSTRUCTIONS:
1. Identify terms or clauses that are substantially the same in both documents.
2. Identify key differences in obligations, rights, or terms between the documents.
3. Identify risks or unfavourable terms in Document A that are not in Document B.
4. Identify risks or unfavourable terms in Document B that are not in Document A.
5. Identify any direct contradictions or inconsistencies between the two documents.

OUTPUT FORMAT (use exactly these headers):
MATCHING:
- [item]

DIFFERENCES:
- [item describing the difference, citing which document]

RISKS IN DOC A:
- [risk item]

RISKS IN DOC B:
- [risk item]

INCONSISTENCIES:
- [inconsistency item]
```

#### Response Parsing Rules

| Section header | Maps to `CompareResponse` field |
|---|---|
| `MATCHING:` | `matching` |
| `DIFFERENCES:` | `differences` |
| `RISKS IN DOC A:` | `risksA` |
| `RISKS IN DOC B:` | `risksB` |
| `INCONSISTENCIES:` | `inconsistencies` |

Each section: split on `\n- ` to produce `string[]`. Empty array `[]` is valid.

#### Acceptance Criteria

- [ ] `AC-PR-C-01`: Parser produces `CompareResponse` matching `types/index.ts`
- [ ] `AC-PR-C-02`: All five keys are always present (even if empty arrays)
- [ ] `AC-PR-C-03`: Identical documents produce a non-empty `matching` array

---

### 8.3 Q&A Chat Prompt — `FEAT-03`

#### Prompt Template

```
You are a legal document assistant. You have been given a legal document to analyse. Answer questions about this document accurately and in plain English. If the answer cannot be determined from the document, say so clearly. Always remind the user that your answers are informational only and not legal advice.

DOCUMENT:
{documentText}

CONVERSATION HISTORY:
{formattedHistory}

User: {question}
Assistant:
```

Where `formattedHistory` is constructed as:
```typescript
history.map(h => `${h.role === 'user' ? 'User' : 'Assistant'}: ${h.text}`).join('\n')
```

#### Acceptance Criteria

- [ ] `AC-PR-CH-01`: Prompt contains the full document text at `{documentText}`
- [ ] `AC-PR-CH-02`: All prior history turns are included in `{formattedHistory}`
- [ ] `AC-PR-CH-03`: Prompt ends with `Assistant:` to prime the model
- [ ] `AC-PR-CH-04`: When `history` is empty, `CONVERSATION HISTORY:` section is present but blank

---

### 8.4 Lawyer Prep Prompt — `FEAT-04`

#### Prompt Template

```
You are a legal consultant helping a person prepare for a meeting with their lawyer. Based on the following legal document, generate a practical preparation checklist.

DOCUMENT:
{documentText}

INSTRUCTIONS:
Generate three specific, actionable lists based on the actual content of this document. Be specific — refer to actual clauses and terms in the document, not generic advice.
1. Questions the person should ask their lawyer about this specific document.
2. Documents, records, or information they should bring to the meeting.
3. Specific terms, clauses, or obligations they should ask their lawyer to clarify or watch out for.

OUTPUT FORMAT (use exactly these headers):
QUESTIONS TO ASK:
- [specific question referencing this document]

DOCUMENTS TO BRING:
- [specific document or information item]

WATCH OUT FOR:
- [specific clause or term to clarify]
```

#### Response Parsing Rules

| Section header | Maps to `PrepResponse` field |
|---|---|
| `QUESTIONS TO ASK:` | `questions` |
| `DOCUMENTS TO BRING:` | `documents` |
| `WATCH OUT FOR:` | `watchouts` |

#### Acceptance Criteria

- [x] `AC-PR-P-01`: Parser produces `PrepResponse` matching `types/index.ts`
- [x] `AC-PR-P-02`: All three arrays are present; each has ≥ 1 item for any non-trivial document
- [x] `AC-PR-P-03`: Items reference actual document content (verified manually with a sample document)

---

## 9. Page Specifications

### 9.1 Root Layout — `app/layout.tsx`

**Spec:** Wraps every page with shared chrome.

| Requirement | Spec |
|---|---|
| Component type | Server Component |
| Children | `<Navbar>` → `<DisclaimerBanner>` → `<main>{children}</main>` |
| `<html>` attributes | `lang="en"` |
| Global CSS | `import './globals.css'` present |
| Metadata export | `title: "LexAid"`, `description: "AI-powered legal document assistant"` |

**Acceptance Criteria:**
- [ ] `AC-LAY-01`: `<html lang="en">` present in rendered output
- [ ] `AC-LAY-02`: `<Navbar>` renders before `<DisclaimerBanner>` renders before `{children}`
- [ ] `AC-LAY-03`: Page `<title>` is `"LexAid"` on all pages

---

### 9.2 Home Page — `app/page.tsx`

**Spec:** Landing page with hero section and four feature cards.

| Section | Required content |
|---|---|
| Hero | App name "LexAid", tagline (≤ 15 words), brief description (≤ 50 words) |
| Feature cards | One card per feature (`FEAT-01` through `FEAT-04`) |

**Feature card spec — each card MUST contain:**
- Feature name
- One-sentence description
- A `<Link>` to the feature route
- Visual icon or emoji representing the feature

**Acceptance Criteria:**
- [ ] `AC-HOME-01`: All four feature cards render with correct route links
- [ ] `AC-HOME-02`: All four feature links are keyboard-focusable
- [ ] `AC-HOME-03`: Page passes `next build` with zero TypeScript errors

---

### 9.3 Simplify Page — `app/simplify/page.tsx`

**Spec:** `FEAT-01` user interface.

| State variable | Type | Initial value |
|---|---|---|
| `content` | `DocumentContent \| null` | `null` |
| `result` | `SimplifyResponse \| null` | `null` |
| `loading` | `boolean` | `false` |
| `error` | `string \| null` | `null` |

**User flow:**
1. `<FileOrTextInput>` → sets `content`
2. Submit button (disabled when `content` is `null` or `loading` is `true`)
3. On submit: set `loading = true`, POST to `/api/simplify`, set `result` or `error`, set `loading = false`
4. When `loading` is `true`: show `<LoadingSpinner label="Analysing document..." />`
5. When `result` is set: show `<ResultCard title="Plain-English Summary" content={result.summary} />` followed by one `<ResultCard>` per clause (variant `'warning'` if `clause.risk === true`)
6. When `error` is set: show error string in a visible red/amber banner

**Acceptance Criteria:**
- [ ] `AC-SIMP-01`: Submit button is disabled when no content is provided
- [ ] `AC-SIMP-02`: Loading spinner shows during the API call
- [ ] `AC-SIMP-03`: Summary `ResultCard` renders when response is received
- [ ] `AC-SIMP-04`: Clauses with `risk: true` render with `variant='warning'`
- [ ] `AC-SIMP-05`: Network error displays a human-readable error message (not a stack trace)

---

### 9.4 Compare Page — `app/compare/page.tsx`

**Spec:** `FEAT-02` user interface.

| State variable | Type | Initial value |
|---|---|---|
| `contentA` | `DocumentContent \| null` | `null` |
| `contentB` | `DocumentContent \| null` | `null` |
| `result` | `CompareResponse \| null` | `null` |
| `loading` | `boolean` | `false` |
| `error` | `string \| null` | `null` |

**Layout spec:** Two `<FileOrTextInput>` components rendered side by side (CSS grid or flex), labelled "Document A" and "Document B".

**Submit validation:** If either `contentA` or `contentB` is `null`, show inline validation error "Please provide both documents." — do not make the API call.

**Result rendering:** Five `<ResultCard>` components in this order:
1. Title: "Matching Terms" — content: `result.matching.join('\n')`
2. Title: "Key Differences" — content: `result.differences.join('\n')`
3. Title: "Risks in Document A" — variant: `'warning'` — content: `result.risksA.join('\n')`
4. Title: "Risks in Document B" — variant: `'warning'` — content: `result.risksB.join('\n')`
5. Title: "Inconsistencies" — variant: `'warning'` — content: `result.inconsistencies.join('\n')`

**Acceptance Criteria:**
- [ ] `AC-COMP-01`: Two `FileOrTextInput` components render labelled "Document A" and "Document B"
- [ ] `AC-COMP-02`: Submitting with only one document shows validation error without calling the API
- [ ] `AC-COMP-03`: All five result sections render when response is received
- [ ] `AC-COMP-04`: Risks and Inconsistencies sections use `variant='warning'`

---

### 9.5 Chat Page — `app/chat/page.tsx`

**Spec:** `FEAT-03` user interface. Two-phase UI.

**Phase 1 — Document Load:**

| State variable | Type | Initial value |
|---|---|---|
| `documentContent` | `DocumentContent \| null` | `null` |
| `documentText` | `string \| null` | `null` |
| `phase` | `'load' \| 'chat'` | `'load'` |

- Shows `<FileOrTextInput>` and a "Load Document" button
- On "Load Document": if `documentContent` is a `File`, extract text by POSTing to `/api/simplify` is **NOT** done — instead, the `File` is stored and sent with the first chat message; if it is a `string`, store it directly in `documentText` and transition to `phase = 'chat'`

> **Note on PDF extraction in Chat:** For the chat feature, PDF text extraction happens on the server. The `File` object is sent as `multipart/form-data` to `/api/chat` with each question. The route uses `extractTextFromRequest` for the first message, then the client sends the extracted text as `documentText` for subsequent messages.

**Simpler alternative (preferred):** On "Load Document" click, POST the file to a lightweight `/api/extract` route that returns `{ text: string }`. Store the extracted text and transition to the chat phase. This avoids re-sending the PDF with every message.

> **Decision required before implementation:** Choose between (a) sending the File on every chat call, or (b) a `/api/extract` pre-processing step. This spec defaults to option (b) — add `/api/extract` as a POST endpoint that calls `extractTextFromRequest` and returns `{ text: string }`.

**Phase 2 — Chat:**

| State variable | Type | Initial value |
|---|---|---|
| `messages` | `ChatMessage[]` | `[]` |
| `question` | `string` | `''` |
| `loading` | `boolean` | `false` |

- Scrollable message list rendering each `ChatMessage`
- User messages: right-aligned, indigo background
- Model messages: left-aligned, slate background
- Text input + "Send" button (disabled when `loading` or `question` is empty)
- On send: append user message to `messages`, POST to `/api/chat`, append model response, auto-scroll to bottom

**Acceptance Criteria:**
- [ ] `AC-CHAT-01`: Phase 1 renders document input; clicking "Load Document" with no content does nothing
- [ ] `AC-CHAT-02`: After loading, phase 2 chat interface appears
- [ ] `AC-CHAT-03`: User messages render right-aligned; model messages left-aligned
- [ ] `AC-CHAT-04`: Message list auto-scrolls to the latest message after each response
- [ ] `AC-CHAT-05`: Send button is disabled while `loading` is `true`
- [ ] `AC-CHAT-06`: Conversation history accumulates across turns (manually verify 3-turn conversation)

---

### 9.6 Lawyer Prep Page — `app/prep/page.tsx`

**Spec:** `FEAT-04` user interface.

| State variable | Type | Initial value |
|---|---|---|
| `content` | `DocumentContent \| null` | `null` |
| `result` | `PrepResponse \| null` | `null` |
| `loading` | `boolean` | `false` |
| `error` | `string \| null` | `null` |

**Result rendering spec:**

Three labelled checklist sections:
1. **"Questions to Ask Your Lawyer"** — render each `questions` item as a checkbox list item (`<li>` with `<input type="checkbox" disabled>` for visual styling)
2. **"Documents & Information to Bring"** — same pattern for `documents` items
3. **"Watch Out For"** — same pattern for `watchouts` items

**Print spec:**
- "Print Checklist" button calls `window.print()`
- Tailwind `print:hidden` applied to Navbar, DisclaimerBanner, FileOrTextInput, submit button, and Print button itself
- Tailwind `print:block` ensures checklist sections are visible in print

**Acceptance Criteria:**
- [x] `AC-PREP-01`: All three checklist sections render with ≥ 1 item each for a non-trivial document
- [x] `AC-PREP-02`: Each item renders as a visually styled checkbox list item
- [x] `AC-PREP-03`: "Print Checklist" button is visible only after results are loaded
- [x] `AC-PREP-04`: Navbar is hidden in print preview (`print:hidden` class applied)
- [x] `AC-PREP-05`: Checklist sections are visible in print preview

---

## 10. Configuration Specifications

### 10.1 `next.config.ts`

**Required config — MUST be present verbatim:**

```typescript
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  serverExternalPackages: ['pdf-parse'],
};

export default nextConfig;
```

**Why this is a spec requirement:** Omitting `serverExternalPackages` causes a webpack bundling error for `pdf-parse` at build time due to its use of Node.js `fs`.

**Acceptance Criteria:**
- [ ] `AC-CFG-01`: `serverExternalPackages` array contains `'pdf-parse'`
- [ ] `AC-CFG-02`: `npm run build` completes with zero errors

---

### 10.2 `tailwind.config.ts`

**Required extensions:**

```typescript
theme: {
  extend: {
    colors: {
      primary: {
        50:  '#eef2ff',
        100: '#e0e7ff',
        500: '#6366f1',
        600: '#4f46e5',
        700: '#4338ca',
        900: '#1e1b4b',
      },
    },
  },
},
```

**Content paths MUST include:**
```typescript
content: [
  './app/**/*.{ts,tsx}',
  './components/**/*.{ts,tsx}',
],
```

**Acceptance Criteria:**
- [ ] `AC-TW-01`: `primary` colour scale is defined and accessible via `bg-primary-500` etc.
- [ ] `AC-TW-02`: All component and page files are included in the `content` scan paths
- [ ] `AC-TW-03`: `npm run build` produces no Tailwind class purge warnings

---

### 10.3 `vercel.json`

**Required config:**

```json
{
  "functions": {
    "app/api/**/*.ts": {
      "maxDuration": 30
    }
  }
}
```

**Acceptance Criteria:**
- [ ] `AC-VCL-01`: File exists at project root
- [ ] `AC-VCL-02`: All API route functions have `maxDuration: 30` applied

---

### 10.4 `.env.example`

**Required content (exact):**

```
# Google AI Studio API key — required for all AI features
# Get yours at: https://aistudio.google.com/
GEMINI_API_KEY=your_key_here
```

**Acceptance Criteria:**
- [ ] `AC-ENV-01`: `.env.example` exists and contains `GEMINI_API_KEY=`
- [ ] `AC-ENV-02`: `.env.local` is listed in `.gitignore`
- [ ] `AC-ENV-03`: No real API key appears in any committed file

---

## 11. Non-Functional Specifications

### 11.1 Performance Targets

| Metric | Required | Notes |
|---|---|---|
| Time to First Byte | < 200ms | Static pages from Vercel CDN edge |
| API response — short doc (< 5 pages) | < 15s | Acceptable for hackathon |
| API response — large doc (15–20 pages) | < 30s | Within Vercel `maxDuration` |
| Client-side JS bundle | < 150KB gzipped | No heavy client libraries |

**Acceptance Criteria:**
- [ ] `AC-PERF-01`: `npm run build` reports first-load JS for any page < 150KB

---

### 11.2 Accessibility Specification

| Requirement | Standard | Test method |
|---|---|---|
| Colour contrast (text on background) | WCAG AA (4.5:1 minimum) | Browser DevTools / axe |
| All interactive elements keyboard-reachable | WCAG 2.1 SC 2.1.1 | Manual Tab-key test |
| Loading states announced to screen readers | WCAG 2.1 SC 4.1.3 | `aria-live="polite"` on loading regions |
| All images have alt text | WCAG 2.1 SC 1.1.1 | Code review |
| Form inputs have visible labels | WCAG 2.1 SC 1.3.1 | Code review |
| Page title unique per route | WCAG 2.4.2 | Next.js `metadata` export per page |

**Acceptance Criteria:**
- [ ] `AC-A11Y-01`: All form inputs in `FileOrTextInput` have associated `<label>` elements
- [ ] `AC-A11Y-02`: `<LoadingSpinner>` has `role="status"` and appropriate `aria-label`
- [ ] `AC-A11Y-03`: Each page exports a unique `metadata.title`
- [ ] `AC-A11Y-04`: Tab-key navigation reaches every interactive element on every page

---

### 11.3 Reliability Specification

| Failure scenario | Required behaviour |
|---|---|
| Gemini API returns an error | Route returns HTTP 500 `{ error: "Failed to analyse document. Please try again." }` |
| PDF contains no extractable text (scanned image PDF) | Route returns HTTP 400 `{ error: "Could not extract text from this PDF. Please use a text-based PDF or paste the text directly." }` |
| Network timeout | Client shows error banner: "Request timed out. Please try with a shorter document." |
| Missing `GEMINI_API_KEY` | Route returns HTTP 500 `{ error: "AI service is not configured." }` |

**Acceptance Criteria:**
- [ ] `AC-REL-01`: All four error scenarios above produce the exact specified messages
- [ ] `AC-REL-02`: No page shows a raw JavaScript error object or stack trace to the user

---

## 12. Security Specifications

### 12.1 API Key Security

| Requirement | Verification |
|---|---|
| `GEMINI_API_KEY` MUST NOT appear in any client bundle | `grep -r "GEMINI_API_KEY" .next/static/` returns no results |
| All Gemini calls MUST originate from `lib/gemini.ts` server-side only | Code review: no `@google/generative-ai` import in `components/` or `app/**/page.tsx` |
| Key MUST be read from `process.env` at runtime | Code review: no hard-coded key strings |

**Acceptance Criteria:**
- [ ] `AC-SEC-01`: `grep -r "GEMINI_API_KEY" .next/static/` returns zero results after build
- [ ] `AC-SEC-02`: `grep -r "@google/generative-ai" components/` returns zero results
- [ ] `AC-SEC-03`: `grep -r "@google/generative-ai" app/` returns zero results (only `lib/gemini.ts` imports it)

---

### 12.2 Input Validation

| Input | Client-side check | Server-side check |
|---|---|---|
| File upload | `accept=".pdf"` attribute | `parsePdf` throws on non-PDF buffer |
| File size | Reject files > 10MB before upload | `MAX_CHARS` truncation prevents oversized processing |
| Text input | None required | `MAX_CHARS` truncation |
| Chat question | Non-empty check before send | Route rejects empty `question` with HTTP 400 |

**Acceptance Criteria:**
- [ ] `AC-INP-01`: File input has `accept=".pdf"` attribute
- [ ] `AC-INP-02`: Submitting a text file (`.txt`) via the file input is blocked by browser
- [ ] `AC-INP-03`: A document of 50,000 characters is processed without error (truncated to 40,000)

---

## 13. Deployment Specification

### 13.1 Build Verification

The following commands MUST all pass with zero errors before deployment:

```bash
npm run build    # next build — zero TypeScript errors, zero build warnings
```

**Acceptance Criteria:**
- [ ] `AC-BUILD-01`: `npm run build` exits with code 0
- [ ] `AC-BUILD-02`: Build output shows zero TypeScript errors
- [ ] `AC-BUILD-03`: No `serverExternalPackages` warning appears in build output

---

### 13.2 Vercel Deployment Checklist

Before marking deployment complete:

- [ ] `AC-DEPLOY-01`: `GEMINI_API_KEY` is set in Vercel project Settings → Environment Variables for Production environment
- [ ] `AC-DEPLOY-02`: Vercel deployment completes with no build errors
- [ ] `AC-DEPLOY-03`: All four feature pages load on the production URL
- [ ] `AC-DEPLOY-04`: Each feature produces a valid AI response with a sample document on the production URL
- [ ] `AC-DEPLOY-05`: `vercel.json` `maxDuration: 30` is reflected in the Vercel Functions dashboard

---

### 13.3 README Specification

`README.md` MUST contain all of the following sections:

| Section | Required content |
|---|---|
| Project title & description | "LexAid" + 2–3 sentence summary |
| Features | Bullet list of all four features with one-line descriptions |
| Tech stack | List matching Section 2 |
| Prerequisites | Node.js ≥ 18, npm, Gemini API key |
| Local setup | `git clone`, `npm install`, `.env.local` setup, `npm run dev` |
| Environment variables | Table: variable name, required, description |
| Deployment | Vercel connect, env var setup, deploy steps |
| Disclaimer | Legal information / not legal advice notice |

**Acceptance Criteria:**
- [ ] `AC-README-01`: All eight sections above are present in `README.md`
- [ ] `AC-README-02`: Local setup steps can be followed by a new developer to run the app in < 5 minutes

---

*Document version: 2.0 — Spec-Driven revision*  
*Supersedes: version 1.0*  
*All acceptance criteria must be verified before each sub-task is marked complete in `legal-assistant-plan.md`*
