const API_BASE_URL = window.location.hostname === "localhost"
  ? "http://localhost:8000/api"
  : "/api";

/** Maximum upload size (10 MB) — must match MAX_FILE_BYTES in app/routers/documents.py */
export const MAX_FILE_SIZE = 10 * 1024 * 1024;

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, options);
  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error?.message || "The request could not be completed.");
  }

  return data;
}

function postJson(path, body) {
  return request(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export function extractDocument(formData) {
  return request("/documents/extract", {
    method: "POST",
    body: formData,
  });
}

export function simplifyDocument(text) {
  return postJson("/analyze/simplify", { text });
}

export function analyzeRisks(text) {
  return postJson("/analyze/risks", { text });
}

export function generateChecklist(text) {
  return postJson("/analyze/checklist", { text });
}

export function compareDocuments(docA, docB, labelA, labelB) {
  return postJson("/analyze/compare", {
    doc_a: docA,
    doc_b: docB,
    label_a: labelA,
    label_b: labelB,
  });
}

export function askQuestion(text, question, history) {
  return postJson("/analyze/qa", { text, question, history });
}
