export const runtime = 'nodejs';

import { NextResponse } from 'next/server';
import { callGemini } from '@/lib/gemini';
import type { ChatRequest } from '@/types/index';

export async function POST(req: Request) {
  try {
    const body: ChatRequest = await req.json();
    const { documentText, history, question } = body;

    if (!documentText || documentText.trim() === '') {
      return NextResponse.json({ error: 'No document text provided.' }, { status: 400 });
    }

    if (!question || question.trim() === '') {
      return NextResponse.json({ error: 'Question is required.' }, { status: 400 });
    }

    const formattedHistory = (history ?? [])
      .map((h) => `${h.role === 'user' ? 'User' : 'Assistant'}: ${h.text}`)
      .join('\n');

    const prompt = `You are a legal document assistant. You have been given a legal document to analyse. Answer questions about this document accurately and in plain English. If the answer cannot be determined from the document, say so clearly. Always remind the user that your answers are informational only and not legal advice.

DOCUMENT:
${documentText}

CONVERSATION HISTORY:
${formattedHistory}

User: ${question}
Assistant:`;

    const responseText = await callGemini(prompt);

    return NextResponse.json({ answer: responseText });
  } catch (err) {
    const message =
      err instanceof Error && err.message === 'AI service is not configured.'
        ? 'AI service is not configured.'
        : 'Failed to process chat request. Please try again.';
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
