"use client";

import { useState } from "react";
import FileOrTextInput from "@/components/FileOrTextInput";
import LoadingSpinner from "@/components/LoadingSpinner";
import ResultCard from "@/components/ResultCard";
import type { DocumentContent, CompareResponse } from "@/types/index";

export default function ComparePage() {
  const [contentA, setContentA] = useState<DocumentContent | null>(null);
  const [contentB, setContentB] = useState<DocumentContent | null>(null);
  const [result, setResult] = useState<CompareResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    if (!contentA || !contentB) {
      setValidationError("Please provide both documents.");
      return;
    }

    setValidationError(null);
    setLoading(true);
    setResult(null);
    setError(null);

    try {
      const formData = new FormData();

      if (contentA instanceof File) {
        formData.append("doc1", contentA);
      } else {
        formData.append("doc1", contentA);
      }

      if (contentB instanceof File) {
        formData.append("doc2", contentB);
      } else {
        formData.append("doc2", contentB);
      }

      const response = await fetch("/api/compare", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        setError(data.error ?? "An unexpected error occurred. Please try again.");
      } else {
        setResult(data as CompareResponse);
      }
    } catch {
      setError("Network error — please check your connection and try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="max-w-5xl mx-auto px-4 py-10">
      <h1 className="text-2xl font-bold text-slate-800 mb-1">Contract Comparator</h1>
      <p className="text-sm text-slate-500 mb-6">
        Upload or paste two legal documents to compare their terms, differences, and risks side by side.
      </p>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          <div>
            <p className="text-sm font-semibold text-slate-700 mb-2">Document A</p>
            <FileOrTextInput onContentReady={(c) => setContentA(c)} />
          </div>
          <div>
            <p className="text-sm font-semibold text-slate-700 mb-2">Document B</p>
            <FileOrTextInput onContentReady={(c) => setContentB(c)} />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Compare Documents
        </button>

        {validationError && (
          <p className="text-sm text-red-600 text-center">{validationError}</p>
        )}
      </form>

      {loading && (
        <div className="mt-8 flex justify-center">
          <LoadingSpinner label="Comparing documents..." />
        </div>
      )}

      {error && (
        <div className="mt-6 rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {result && !loading && (
        <div className="mt-8 space-y-4">
          <ResultCard
            title="Matching Terms"
            content={result.matching.length > 0 ? result.matching.join('\n') : "None identified."}
          />
          <ResultCard
            title="Key Differences"
            content={result.differences.length > 0 ? result.differences.join('\n') : "None identified."}
          />
          <ResultCard
            title="Risks in Document A"
            variant="warning"
            content={result.risksA.length > 0 ? result.risksA.join('\n') : "None identified."}
          />
          <ResultCard
            title="Risks in Document B"
            variant="warning"
            content={result.risksB.length > 0 ? result.risksB.join('\n') : "None identified."}
          />
          <ResultCard
            title="Inconsistencies"
            variant="warning"
            content={result.inconsistencies.length > 0 ? result.inconsistencies.join('\n') : "None identified."}
          />
        </div>
      )}
    </main>
  );
}
