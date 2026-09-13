export const runtime = 'nodejs';

import { NextResponse } from 'next/server';
import { callGemini } from '@/lib/gemini';
import { extractTextFromRequest } from '@/lib/extractText';
import type { PrepResponse } from '@/types/index';

const PROMPT_TEMPLATE = `You are a legal consultant helping a person prepare for a meeting with their lawyer. Based on the following legal document, generate a practical preparation checklist.

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
- [specific clause or term to clarify]`;

function parseSection(raw: string, header: string, nextHeaders: string[]): string[] {
  const start = raw.indexOf(header);
  if (start === -1) return [];

  const contentStart = start + header.length;
  let contentEnd = raw.length;
  for (const next of nextHeaders) {
    const idx = raw.indexOf(next, contentStart);
    if (idx !== -1 && idx < contentEnd) {
      contentEnd = idx;
    }
  }

  const section = raw.slice(contentStart, contentEnd);
  return section
    .split('\n- ')
    .map((s) => s.replace(/^- /, '').trim())
    .filter((s) => s.length > 0);
}

function parsePrepResponse(raw: string): PrepResponse {
  const allHeaders = ['QUESTIONS TO ASK:', 'DOCUMENTS TO BRING:', 'WATCH OUT FOR:'];

  const questions = parseSection(raw, 'QUESTIONS TO ASK:', [
    'DOCUMENTS TO BRING:',
    'WATCH OUT FOR:',
  ]);
  const documents = parseSection(raw, 'DOCUMENTS TO BRING:', ['WATCH OUT FOR:']);
  const watchouts = parseSection(raw, 'WATCH OUT FOR:', []);

  // Ensure all three arrays are always present
  return {
    questions: questions.length > 0 ? questions : [],
    documents: documents.length > 0 ? documents : [],
    watchouts: watchouts.length > 0 ? watchouts : [],
  };
}

const SCANNED_PDF_ERROR =
  'Could not extract text from this PDF. Please use a text-based PDF or paste the text directly.';

export async function POST(req: Request) {
  try {
    const text = await extractTextFromRequest(req);

    if (!text.trim()) {
      return NextResponse.json(
        { error: 'No document text provided.' },
        { status: 400 }
      );
    }

    const prompt = PROMPT_TEMPLATE.replace('{documentText}', text);
    const raw = await callGemini(prompt);
    const prepResponse = parsePrepResponse(raw);

    return NextResponse.json(prepResponse);
  } catch (err) {
    if (err instanceof Error && err.message === SCANNED_PDF_ERROR) {
      return NextResponse.json({ error: SCANNED_PDF_ERROR }, { status: 400 });
    }
    const message =
      err instanceof Error && err.message === 'AI service is not configured.'
        ? 'AI service is not configured.'
        : 'Failed to generate prep checklist. Please try again.';
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
