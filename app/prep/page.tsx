"use client";

import { useState } from "react";
import FileOrTextInput from "@/components/FileOrTextInput";
import LoadingSpinner from "@/components/LoadingSpinner";
import type { DocumentContent, PrepResponse } from "@/types/index";

export default function PrepPage() {
  const [content, setContent] = useState<DocumentContent | null>(null);
  const [result, setResult] = useState<PrepResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!content) return;

    setLoading(true);
    setResult(null);
    setError(null);

    try {
      let response: Response;

      if (content instanceof File) {
        const formData = new FormData();
        formData.append("file", content);
        response = await fetch("/api/prep", {
          method: "POST",
          body: formData,
        });
      } else {
        response = await fetch("/api/prep", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: content }),
        });
      }

      const data = await response.json();

      if (!response.ok) {
        setError(data.error ?? "An unexpected error occurred. Please try again.");
      } else {
        setResult(data as PrepResponse);
      }
    } catch {
      setError("Network error — please check your connection and try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="max-w-3xl mx-auto px-4 py-10">
      <h1 className="text-2xl font-bold text-slate-800 mb-1">Lawyer Prep Checklist</h1>
      <p className="text-sm text-slate-500 mb-6">
        Upload a PDF or paste your legal document to generate a preparation checklist for your lawyer meeting.
      </p>

      <div className="print:hidden">
        <form onSubmit={handleSubmit} className="space-y-4">
          <FileOrTextInput onContentReady={(c) => setContent(c)} />

          <button
            type="submit"
            disabled={content === null || loading}
            className="w-full rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Generate Checklist
          </button>
        </form>
      </div>

      {loading && (
        <div className="mt-8 flex justify-center print:hidden">
          <LoadingSpinner label="Generating checklist..." />
        </div>
      )}

      {error && (
        <div className="mt-6 rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700 print:hidden">
          {error}
        </div>
      )}

      {result && !loading && (
        <div className="mt-8 space-y-6 print:block">
          <ChecklistSection title="Questions to Ask Your Lawyer" items={result.questions} />
          <ChecklistSection title="Documents &amp; Information to Bring" items={result.documents} />
          <ChecklistSection title="Watch Out For" items={result.watchouts} />

          <div className="print:hidden">
            <button
              onClick={() => window.print()}
              className="mt-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors"
            >
              Print Checklist
            </button>
          </div>
        </div>
      )}
    </main>
  );
}

function ChecklistSection({ title, items }: { title: string; items: string[] }) {
  return (
    <section className="print:block">
      <h2 className="text-lg font-semibold text-slate-800 mb-3">{title}</h2>
      <ul className="space-y-2">
        {items.map((item, i) => (
          <li key={i} className="flex items-center gap-2 text-sm text-slate-700">
            <input type="checkbox" disabled className="h-4 w-4 rounded border-slate-300 text-blue-600" />
            {item}
          </li>
        ))}
      </ul>
    </section>
  );
}
