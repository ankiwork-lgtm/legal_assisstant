# LegalLens AI — Requirements Specification

## 1. Purpose & Problem Statement

Legal documents (contracts, leases, terms of service, employment offers, NDAs, policies)
are hard for non-lawyers to read, compare, and act on. **LegalLens AI** is a GenAI-powered
web application that helps a person understand, compare, and navigate legal documents by:

- Turning dense legal text into plain language.
- Comparing two or more documents to surface differences.
- Answering questions grounded in the document the user provided.
- Flagging risky, unusual, or important clauses and obligations.
- Producing an actionable checklist / question list before talking to a real lawyer.

**LegalLens AI provides information and assistance. It does not provide legal advice,
does not create an attorney–client relationship, and must never claim to.** This
constraint applies to every feature below and is treated as a hard requirement, not a
UI afterthought.

## 2. Target Users / Personas

| Persona | Scenario |
|---|---|
| Freelancer | Reviewing a client services contract before signing |
| Renter | Reviewing a residential lease |
| Consumer | Reviewing Terms of Service / Privacy Policy before agreeing |
| Small business owner | Comparing two vendor/SaaS agreements |
| Job candidate | Reviewing an offer letter / employment contract |

## 3. Scope (Hackathon MVP)

**In scope (prioritized use cases):**
1. Plain-language simplification of a single document
2. Side-by-side comparison of 2+ documents
3. Document-grounded Q&A (chat)
4. Risk & clause highlighting (obligations, red flags, unusual terms)
5. Checklist / next-steps generator for a lawyer meeting

**Input formats supported:** PDF upload, pasted raw text.
**Out of scope for MVP:** DOCX upload, OCR for scanned/image PDFs, user accounts,
server-side database, multi-user collaboration, e-signatures, payments.

**Storage model:** No backend persistence. The backend is stateless per request.
Session/document history is kept in the browser (`localStorage`) only, scoped to
that browser.

## 4. Functional Requirements (EARS Format)

### FR-1: Document Ingestion
- WHEN a user uploads a PDF file, THE SYSTEM SHALL extract its text content and return
  it to the client for further processing.
- WHEN a user pastes raw text instead of uploading a file, THE SYSTEM SHALL accept the
  pasted text directly without requiring a file.
- IF an uploaded file is not a valid PDF or exceeds the configured size limit,
  THEN THE SYSTEM SHALL reject it and return a clear, specific error message.
- IF a PDF contains no extractable text (e.g., it is a scanned image), THEN THE SYSTEM
  SHALL inform the user that the document appears to be a scanned/image PDF and is not
  supported in this version, rather than silently returning empty results.
- WHEN text is successfully extracted, THE SYSTEM SHALL return the extracted text along
  with basic metadata (character/word count, page count if available).

### FR-2: Plain-Language Simplification
- WHEN a user requests a simplified summary of a document, THE SYSTEM SHALL produce a
  plain-language explanation organized by section/clause, avoiding legal jargon or
  defining it inline where unavoidable.
- WHEN generating a simplified summary, THE SYSTEM SHALL preserve the meaning and not
  omit obligations, deadlines, monetary amounts, or termination conditions.
- WHEN the simplification is returned, THE SYSTEM SHALL include a short top-level
  "in plain English, this document means..." overview in addition to the section-level
  breakdown.

### FR-3: Document Comparison
- WHEN a user submits two or more documents for comparison, THE SYSTEM SHALL identify
  clauses/sections present in one document but not the other(s).
- WHEN comparing documents, THE SYSTEM SHALL identify clauses that address the same
  topic but differ materially in terms (e.g., different notice periods, different
  liability caps).
- WHEN a comparison is returned, THE SYSTEM SHALL present it as a structured list of
  differences, each labeled with the topic, what each document says, and why the
  difference may matter.
- IF the user submits documents that are of very different types (e.g., a lease vs. a
  loan agreement), THEN THE SYSTEM SHALL still attempt a best-effort comparison and
  note that the documents are not directly comparable in structure.

### FR-4: Document-Grounded Q&A
- WHEN a user asks a question about an uploaded/pasted document, THE SYSTEM SHALL
  answer using only the content of that document as grounding context.
- IF the answer to a question is not found in the document, THEN THE SYSTEM SHALL state
  that the document does not address that point, rather than fabricating an answer.
- WHEN answering, THE SYSTEM SHALL cite or reference the relevant clause/section so the
  user can locate it in the source document.
- WHEN a user asks a follow-up question, THE SYSTEM SHALL take prior Q&A turns (sent by
  the client) into account to maintain conversational context.

### FR-5: Risk & Clause Highlighting
- WHEN a user requests risk analysis of a document, THE SYSTEM SHALL identify clauses
  that represent obligations, restrictions, deadlines, penalties, auto-renewals,
  liability, indemnification, or termination conditions.
- WHEN a risk item is identified, THE SYSTEM SHALL assign it a severity level (e.g.,
  High / Medium / Low / Informational) and a one-line plain-language explanation of why
  it matters.
- WHEN risk analysis is returned, THE SYSTEM SHALL group results by category (e.g.,
  Financial, Termination, Liability, Privacy, Obligations) so a user can scan by topic.
- THE SYSTEM SHALL NOT present risk ratings as a legal conclusion; each item SHALL be
  phrased as "this may be worth reviewing because..." rather than a definitive verdict.

### FR-6: Checklist / Next-Steps Generator
- WHEN a user requests a checklist, THE SYSTEM SHALL generate an actionable list of
  items the user should verify, negotiate, or ask a lawyer about, derived from the
  document's content.
- WHEN generating the checklist, THE SYSTEM SHALL separate items into "Questions to ask
  a lawyer or the other party" and "Things to verify yourself" where applicable.
- WHEN a checklist is generated, THE SYSTEM SHALL allow the user to mark items as
  done/not done in the UI (client-side only).

### FR-7: Session History
- WHEN a user completes an analysis (simplify, compare, Q&A, risk, checklist), THE
  SYSTEM SHALL allow the client to save that result to browser-local storage under the
  current session.
- WHEN a user reopens the app in the same browser, THE SYSTEM SHALL display their prior
  session history (document names + analysis types) from `localStorage`.
- WHEN a user clears their history, THE SYSTEM SHALL remove all locally stored data and
  SHALL NOT need to contact the backend to do so (no server-side copy exists).

### FR-8: Legal Disclaimers & Safety
- THE SYSTEM SHALL display a persistent, non-dismissible-per-session disclaimer stating
  that outputs are informational only, are not legal advice, and do not create an
  attorney-client relationship.
- WHEN any AI-generated output is displayed (simplification, comparison, Q&A, risk
  analysis, checklist), THE SYSTEM SHALL include an inline reminder to consult a
  qualified attorney for decisions with legal consequences.
- IF a user asks a question seeking a direct legal recommendation (e.g., "should I sign
  this," "will I win in court"), THEN THE SYSTEM SHALL answer informationally (explain
  relevant factors from the document) while explicitly declining to give a definitive
  legal recommendation, and SHALL suggest consulting an attorney.

## 5. Non-Functional Requirements

- **Statelessness/Privacy:** The backend SHALL NOT persist uploaded document content or
  extracted text beyond the lifecycle of a single request. No document text is written
  to disk or a database on the server.
- **Secrets:** The Gemini API key SHALL be stored only as a server-side environment
  variable and SHALL NEVER be exposed to the frontend/browser.
- **Latency:** Simple operations (simplify, risk, checklist) on a document under ~15
  pages SHOULD return within 15–20 seconds given LLM latency.
- **Resilience:** IF the Gemini API call fails or times out, THEN THE SYSTEM SHALL
  return a user-readable error rather than a raw stack trace, and the frontend SHALL
  allow retry.
- **Accessibility:** Pages SHALL use semantic HTML, sufficient color contrast, and
  keyboard-navigable controls.
- **Portability:** The system SHALL be deployable to Vercel using a Python (FastAPI)
  serverless backend and static HTML/CSS/JS frontend, with no other required hosting
  infrastructure for the hackathon demo.

## 6. Explicit Out-of-Scope Items

- User authentication / accounts
- Server-side database or document storage
- OCR of scanned/image-only PDFs
- DOCX/other file formats
- Multi-user real-time collaboration
- Jurisdiction-specific legal correctness guarantees
- Any feature that outputs a definitive legal verdict or recommendation
