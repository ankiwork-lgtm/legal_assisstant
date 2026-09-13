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
