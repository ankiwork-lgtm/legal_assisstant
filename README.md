# LexAid — AI-Powered Legal Assistant

LexAid is a free, accessible tool that helps non-lawyers understand, compare, and prepare around legal documents. It uses Google's Gemini AI to translate complex legal language into plain English — without replacing professional legal advice.

---

## Features

- **Document Simplifier** — Upload or paste a legal document and receive a plain-English summary with labelled key clauses and risk flags.
- **Contract Comparator** — Compare two contracts side-by-side to surface matching terms, key differences, and potential risks in each document.
- **Q&A Chat** — Ask plain-English questions about any legal document and get answers grounded in its text, in a multi-turn conversation.
- **Lawyer Prep Checklist** — Generate a tailored, printable three-section checklist (questions to ask, documents to bring, watch-out points) before your lawyer meeting.

---

## Tech Stack

| Technology | Version | Purpose |
|---|---|---|
| Next.js (App Router) | ^14.0.0 | Full-stack React framework, API routes |
| TypeScript | ^5.0.0 | Strict typing across all layers |
| Tailwind CSS | ^3.0.0 | Utility-first styling |
| `@google/generative-ai` | latest | Google Gemini SDK for AI features |
| `pdf-parse` | latest | Server-side PDF text extraction |
| Vercel | — | Deployment platform |

---

## Prerequisites

- **Node.js** ≥ 18 (LTS recommended)
- **npm** ≥ 9
- **Gemini API key** — Get yours free at [https://aistudio.google.com/](https://aistudio.google.com/)

---

## Local Setup

```bash
# 1. Clone the repository
git clone https://github.com/your-username/legal_assisstant.git
cd legal_assisstant

# 2. Install dependencies
npm install

# 3. Create your local environment file
cp .env.example .env.local
# Open .env.local and replace "your_key_here" with your Gemini API key

# 4. Start the development server
npm run dev
```

The app will be available at [http://localhost:3000](http://localhost:3000).

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | ✅ Yes | Your Google AI Studio API key. Used server-side only — never exposed to the browser. |

Create a `.env.local` file at the project root (see `.env.example` for the template). This file is listed in `.gitignore` and is **never committed**.

---

## Deployment

LexAid is designed to deploy to [Vercel](https://vercel.com/) in one click.

1. **Connect your repository** — Import the GitHub repository into a new Vercel project at [https://vercel.com/new](https://vercel.com/new).
2. **Set the environment variable** — In your Vercel project, go to **Settings → Environment Variables** and add:
   - `GEMINI_API_KEY` = your Google AI Studio API key (Production environment)
3. **Deploy** — Vercel will automatically detect the Next.js framework and run `npm run build`. All four API routes are configured with `maxDuration: 30` seconds via `vercel.json` to handle large document processing.
4. **Verify** — Once deployed, open the production URL and smoke-test each of the four feature pages with a sample legal document.

---

## Disclaimer

> **LexAid is for informational purposes only and does not constitute legal advice.**
>
> The AI-generated summaries, comparisons, checklists, and answers produced by LexAid are not a substitute for advice from a qualified legal professional. Do not rely on LexAid output for legal decisions. Always consult a licensed lawyer for advice specific to your situation.
>
> No document content is stored or retained by this application beyond the duration of a single request.
