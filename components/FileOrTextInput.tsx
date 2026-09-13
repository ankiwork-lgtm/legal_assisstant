"use client";

import { useState } from "react";
import type { FileOrTextInputProps } from "@/types/index";

type ActiveTab = "upload" | "text";

export default function FileOrTextInput({
  label,
  onContentReady,
}: FileOrTextInputProps) {
  const [activeTab, setActiveTab] = useState<ActiveTab>("upload");
  const [textValue, setTextValue] = useState<string>("");
  const [fileName, setFileName] = useState<string>("");

  function switchToUpload() {
    setTextValue("");
    setActiveTab("upload");
  }

  function switchToText() {
    setFileName("");
    setActiveTab("text");
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) {
      setFileName(file.name);
      onContentReady(file);
    }
  }

  function handleTextChange(e: React.ChangeEvent<HTMLTextAreaElement>) {
    const value = e.target.value;
    setTextValue(value);
    onContentReady(value);
  }

  return (
    <div className="border border-slate-200 rounded-lg overflow-hidden">
      {label && (
        <p className="px-4 pt-3 text-sm font-medium text-slate-700">{label}</p>
      )}

      {/* Tab bar */}
      <div className="flex border-b border-slate-200">
        <button
          type="button"
          onClick={switchToUpload}
          className={`px-4 py-2 text-sm font-medium ${
            activeTab === "upload"
              ? "border-b-2 border-blue-600 text-blue-600"
              : "text-slate-500 hover:text-slate-700"
          }`}
        >
          Upload PDF
        </button>
        <button
          type="button"
          onClick={switchToText}
          className={`px-4 py-2 text-sm font-medium ${
            activeTab === "text"
              ? "border-b-2 border-blue-600 text-blue-600"
              : "text-slate-500 hover:text-slate-700"
          }`}
        >
          Paste Text
        </button>
      </div>

      <div className="p-4">
        {activeTab === "upload" ? (
          <div>
            <label
              htmlFor="pdf-upload"
              className="block text-sm font-medium text-slate-700 mb-1"
            >
              Select a PDF file
            </label>
            <input
              id="pdf-upload"
              type="file"
              accept=".pdf"
              onChange={handleFileChange}
              className="block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
            {fileName && (
              <p className="mt-2 text-sm text-slate-600">
                Selected: <span className="font-medium">{fileName}</span>
              </p>
            )}
          </div>
        ) : (
          <div>
            <label
              htmlFor="text-input"
              className="block text-sm font-medium text-slate-700 mb-1"
            >
              Paste document text
            </label>
            <textarea
              id="text-input"
              rows={10}
              value={textValue}
              onChange={handleTextChange}
              placeholder="Paste your legal document text here…"
              className="w-full rounded border border-slate-300 px-3 py-2 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        )}
      </div>
    </div>
  );
}
