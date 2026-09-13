export const runtime = 'nodejs';

import { NextResponse } from 'next/server';
import { extractTextFromRequest } from '@/lib/extractText';

export async function POST(req: Request) {
  try {
    const text = await extractTextFromRequest(req);
    return NextResponse.json({ text });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Failed to extract text.';
    return NextResponse.json({ error: message }, { status: 400 });
  }
}
