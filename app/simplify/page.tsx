"use client";

import { useState } from "react";
import FileOrTextInput from "@/components/FileOrTextInput";
import LoadingSpinner from "@/components/LoadingSpinner";
import ResultCard from "@/components/ResultCard";
import type { DocumentContent, SimplifyResponse } from "@/types/index";

export default function SimplifyPage() {
  const [content, setContent] = useState<DocumentContent | null>(null);
  const [result, setResult] = useState<SimplifyResponse | null>(null);
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
        response = await fetch("/api/simplify", {
          method: "POST",
          body: formData,
        });
      } else {
        response = await fetch("/api/simplify", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: content }),
        });
      }

      const data = await response.json();

      if (!response.ok) {
        setError(data.error ?? "An unexpected error occurred. Please try again.");
      } else {
        setResult(data as SimplifyResponse);
      }
    } catch {
      setError("Network error — please check your connection and try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="max-w-3xl mx-auto px-4 py-10">
      <h1 className="text-2xl font-bold text-slate-800 mb-1">Document Simplifier</h1>
      <p className="text-sm text-slate-500 mb-6">
        Upload a PDF or paste your legal document to get a plain-English summary and clause breakdown.
      </p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <FileOrTextInput onContentReady={(c) => setContent(c)} />

        <button
          type="submit"
          disabled={content === null || loading}
          className="w-full rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Analyse Document
        </button>
      </form>

      {loading && (
        <div className="mt-8 flex justify-center">
          <LoadingSpinner label="Analysing document..." />
        </div>
      )}

      {error && (
        <div className="mt-6 rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {result && !loading && (
        <div className="mt-8 space-y-4">
          <ResultCard title="Plain-English Summary" content={result.summary} />

          {result.clauses.map((clause, i) => (
            <ResultCard
              key={i}
              title={clause.label}
              content={clause.text}
              variant={clause.risk ? "warning" : "default"}
            />
          ))}
        </div>
      )}
    </main>
  );
}
