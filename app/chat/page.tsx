"use client";

import { useState, useRef, useEffect } from "react";
import FileOrTextInput from "@/components/FileOrTextInput";
import LoadingSpinner from "@/components/LoadingSpinner";
import type { DocumentContent, ChatMessage } from "@/types/index";

export default function ChatPage() {
  // ── Phase control ────────────────────────────────────────────────────────
  const [phase, setPhase] = useState<"load" | "chat">("load");

  // ── Phase 1 state ────────────────────────────────────────────────────────
  const [documentContent, setDocumentContent] = useState<DocumentContent | null>(null);
  const [documentText, setDocumentText] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loadingDoc, setLoadingDoc] = useState<boolean>(false);

  // ── Phase 2 state ────────────────────────────────────────────────────────
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [chatError, setChatError] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to the latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // ── Phase 1: load document ───────────────────────────────────────────────
  async function handleLoadDocument() {
    if (!documentContent) return;

    setLoadError(null);
    setLoadingDoc(true);

    try {
      if (typeof documentContent === "string") {
        // Plain text — use directly
        setDocumentText(documentContent);
        setPhase("chat");
      } else {
        // PDF File — extract via /api/extract
        const formData = new FormData();
        formData.append("file", documentContent);

        const res = await fetch("/api/extract", {
          method: "POST",
          body: formData,
        });

        const data = await res.json();

        if (!res.ok) {
          setLoadError(data.error ?? "Failed to extract text from document.");
        } else {
          setDocumentText(data.text);
          setPhase("chat");
        }
      }
    } catch {
      setLoadError("Network error — please check your connection and try again.");
    } finally {
      setLoadingDoc(false);
    }
  }

  // ── Phase 2: send message ────────────────────────────────────────────────
  async function handleSend() {
    if (!question.trim() || loading || !documentText) return;

    const userMessage: ChatMessage = { role: "user", text: question };

    // Optimistic update — append user message immediately
    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    setQuestion("");
    setChatError(null);
    setLoading(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          documentText,
          history: messages, // history before this turn
          question: userMessage.text,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        setChatError(data.error ?? "An unexpected error occurred.");
      } else {
        setMessages([...updatedMessages, { role: "model", text: data.answer }]);
      }
    } catch {
      setChatError("Network error — please check your connection and try again.");
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  // ── Render ───────────────────────────────────────────────────────────────
  return (
    <main className="max-w-3xl mx-auto px-4 py-10">
      {/* ── Phase 1 — Document Load ── */}
      {phase === "load" && (
        <>
          <h1 className="text-2xl font-bold text-slate-800 mb-1">Q&amp;A Chat</h1>
          <p className="text-sm text-slate-500 mb-6">
            Upload a PDF or paste your legal document to start a conversation about it.
          </p>

          <div className="space-y-4">
            <FileOrTextInput onContentReady={(c) => setDocumentContent(c)} />

            <button
              type="button"
              onClick={handleLoadDocument}
              disabled={documentContent === null || loadingDoc}
              className="w-full rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loadingDoc ? "Loading…" : "Load Document"}
            </button>
          </div>

          {loadingDoc && (
            <div className="mt-8 flex justify-center">
              <LoadingSpinner label="Extracting document text…" />
            </div>
          )}

          {loadError && (
            <div className="mt-6 rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">
              {loadError}
            </div>
          )}
        </>
      )}

      {/* ── Phase 2 — Chat Window ── */}
      {phase === "chat" && (
        <>
          <h1 className="text-2xl font-bold text-slate-800 mb-1">Q&amp;A Chat</h1>
          <p className="text-sm text-slate-500 mb-4">
            Ask questions about your document. Answers are informational only and not legal advice.
          </p>

          {/* Message list */}
          <div className="flex flex-col gap-3 rounded-xl border border-slate-200 bg-slate-50 p-4 h-[420px] overflow-y-auto mb-4">
            {messages.length === 0 && (
              <p className="text-sm text-slate-400 m-auto">
                No messages yet. Ask your first question below.
              </p>
            )}

            {messages.map((msg, i) => (
              <div
                key={i}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap ${
                    msg.role === "user"
                      ? "bg-indigo-600 text-white"
                      : "bg-slate-100 text-slate-800"
                  }`}
                >
                  {msg.text}
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex justify-start">
                <div className="bg-slate-100 rounded-2xl px-4 py-2.5">
                  <LoadingSpinner label="Thinking…" />
                </div>
              </div>
            )}

            {/* Scroll anchor */}
            <div ref={messagesEndRef} />
          </div>

          {chatError && (
            <div className="mb-3 rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">
              {chatError}
            </div>
          )}

          {/* Input row */}
          <div className="flex gap-2 items-end">
            <label htmlFor="chat-question" className="sr-only">
              Ask a question about the document
            </label>
            <textarea
              id="chat-question"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about the document… (Enter to send, Shift+Enter for new line)"
              rows={3}
              className="flex-1 resize-none rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <button
              type="button"
              onClick={handleSend}
              disabled={loading || question.trim() === ""}
              className="rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors self-end"
            >
              Send
            </button>
          </div>
        </>
      )}
    </main>
  );
}
