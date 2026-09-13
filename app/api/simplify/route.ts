export const runtime = 'nodejs';

import { NextResponse } from 'next/server';
import { callGemini } from '@/lib/gemini';
import { extractTextFromRequest } from '@/lib/extractText';
import type { SimplifyResponse, Clause } from '@/types/index';

const PROMPT_TEMPLATE = `You are a legal document analyst. Your task is to help a non-lawyer understand the following legal document.

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
[Plain-English explanation. End with ⚠️ RISK if this clause is unusual or high-risk.]`;

function parseSimplifyResponse(raw: string): SimplifyResponse {
  // Extract summary: substring from "SUMMARY:\n" to the first "CLAUSE:"
  const summaryStart = raw.indexOf('SUMMARY:\n');
  const firstClause = raw.indexOf('\nCLAUSE: ');

  const summaryRaw =
    summaryStart !== -1
      ? raw.slice(summaryStart + 'SUMMARY:\n'.length, firstClause !== -1 ? firstClause : undefined)
      : '';
  const summary = summaryRaw.trim();

  // Extract clauses: split on "\nCLAUSE: "
  const clauseParts = raw.split('\nCLAUSE: ');
  // First element is everything before the first clause (includes SUMMARY block), skip it
  const clauseBlocks = clauseParts.slice(1);

  const clauses: Clause[] = clauseBlocks.map((block) => {
    const newlineIdx = block.indexOf('\n');
    const label = newlineIdx !== -1 ? block.slice(0, newlineIdx).trim() : block.trim();
    const text = newlineIdx !== -1 ? block.slice(newlineIdx + 1).trim() : '';
    const risk = text.includes('⚠️ RISK');
    return { label, text, risk };
  });

  return { summary, clauses };
}

const SCANNED_PDF_ERROR =
  'Could not extract text from this PDF. Please use a text-based PDF or paste the text directly.';

export async function POST(req: Request) {
  try {
    const documentText = await extractTextFromRequest(req);

    if (!documentText) {
      return NextResponse.json({ error: 'No document text provided.' }, { status: 400 });
    }

    const prompt = PROMPT_TEMPLATE.replace('{documentText}', documentText);
    const raw = await callGemini(prompt);
    const simplifyResponse = parseSimplifyResponse(raw);

    return NextResponse.json(simplifyResponse);
  } catch (err) {
    if (err instanceof Error && err.message === SCANNED_PDF_ERROR) {
      return NextResponse.json({ error: SCANNED_PDF_ERROR }, { status: 400 });
    }
    const message =
      err instanceof Error && err.message === 'AI service is not configured.'
        ? 'AI service is not configured.'
        : 'Failed to analyse document. Please try again.';
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
