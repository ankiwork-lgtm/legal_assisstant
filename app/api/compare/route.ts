export const runtime = 'nodejs';

import { NextResponse } from 'next/server';
import { callGemini } from '@/lib/gemini';
import { parsePdf } from '@/lib/parsePdf';
import type { CompareResponse } from '@/types/index';

const MAX_CHARS = 40000;

const PROMPT_TEMPLATE = `You are a legal contract analyst. Compare the following two legal documents and identify similarities, differences, and risks.

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
- [inconsistency item]`;

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

function parseCompareResponse(raw: string): CompareResponse {
  const allHeaders = [
    'MATCHING:',
    'DIFFERENCES:',
    'RISKS IN DOC A:',
    'RISKS IN DOC B:',
    'INCONSISTENCIES:',
  ];

  const matching = parseSection(raw, 'MATCHING:', allHeaders.slice(1));
  const differences = parseSection(raw, 'DIFFERENCES:', [
    'RISKS IN DOC A:',
    'RISKS IN DOC B:',
    'INCONSISTENCIES:',
  ]);
  const risksA = parseSection(raw, 'RISKS IN DOC A:', [
    'RISKS IN DOC B:',
    'INCONSISTENCIES:',
  ]);
  const risksB = parseSection(raw, 'RISKS IN DOC B:', ['INCONSISTENCIES:']);
  const inconsistencies = parseSection(raw, 'INCONSISTENCIES:', []);

  return { matching, differences, risksA, risksB, inconsistencies };
}

async function extractField(formData: FormData, key: string): Promise<string> {
  const field = formData.get(key);
  if (!field) return '';

  if (field instanceof File) {
    const buffer = Buffer.from(await field.arrayBuffer());
    const text = await parsePdf(buffer);
    return text.slice(0, MAX_CHARS);
  }

  return (field as string).slice(0, MAX_CHARS);
}

const SCANNED_PDF_ERROR =
  'Could not extract text from this PDF. Please use a text-based PDF or paste the text directly.';

export async function POST(req: Request) {
  try {
    let text1: string;
    let text2: string;

    const contentType = req.headers.get('content-type') ?? '';

    if (contentType.includes('multipart/form-data')) {
      const formData = await req.formData();
      [text1, text2] = await Promise.all([
        extractField(formData, 'doc1'),
        extractField(formData, 'doc2'),
      ]);
    } else {
      const body = await req.json();
      text1 = ((body?.text1 as string) ?? '').slice(0, MAX_CHARS);
      text2 = ((body?.text2 as string) ?? '').slice(0, MAX_CHARS);
    }

    if (!text1 || !text2) {
      return NextResponse.json(
        { error: 'Both documents are required.' },
        { status: 400 }
      );
    }

    const prompt = PROMPT_TEMPLATE.replace('{text1}', text1).replace('{text2}', text2);
    const raw = await callGemini(prompt);
    const compareResponse = parseCompareResponse(raw);

    return NextResponse.json(compareResponse);
  } catch (err) {
    if (err instanceof Error && err.message === SCANNED_PDF_ERROR) {
      return NextResponse.json({ error: SCANNED_PDF_ERROR }, { status: 400 });
    }
    const message =
      err instanceof Error && err.message === 'AI service is not configured.'
        ? 'AI service is not configured.'
        : 'Failed to compare documents. Please try again.';
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
