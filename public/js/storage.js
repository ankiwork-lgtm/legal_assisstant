const STORAGE_KEY = "legallens-history";
const RESULT_KINDS = new Set(["simplify", "risks", "checklist", "compare", "qa"]);

function readHistory() {
  try {
    const history = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    return Array.isArray(history) ? history : [];
  } catch {
    return [];
  }
}

function writeHistory(history) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
  } catch (err) {
    // QuotaExceededError — storage is full (common in Incognito / private browsing).
    // Propagate a user-friendly message so callers can surface it.
    throw new Error(
      "Your browser storage is full. This can happen in private/incognito mode. " +
        "Please try again in a regular browser window, or clear your browser data and retry.",
    );
  }
}

function createEntry(documentId, label, text = "") {
  return {
    id: documentId,
    label,
    created_at: new Date().toISOString(),
    text,
    results: {
      simplify: null,
      risks: null,
      checklist: null,
      compare: null,
      qa: [],
    },
  };
}

export function saveDocument(documentId, label, text) {
  const history = readHistory();
  const entry = history.find((item) => item.id === documentId);

  if (entry) {
    entry.label = label;
    entry.text = text;
  } else {
    history.push(createEntry(documentId, label, text));
  }

  writeHistory(history);
}

export function getDocument(documentId) {
  const entry = readHistory().find((item) => item.id === documentId);
  if (!entry) return null;
  // Return the text even if it is an empty string — callers must check for null
  // (entry not found) vs "" (entry exists but text is empty).
  return entry.text ?? null;
}

export function saveResult(documentId, kind, data) {
  if (!RESULT_KINDS.has(kind)) {
    throw new Error(`Unsupported result kind: ${kind}`);
  }

  const history = readHistory();
  let entry = history.find((item) => item.id === documentId);

  if (!entry) {
    entry = createEntry(documentId, "Untitled document");
    history.push(entry);
  }

  entry.results ??= createEntry(documentId, entry.label).results;
  entry.results[kind] = kind === "qa"
    ? [...(entry.results.qa || []), data]
    : data;
  writeHistory(history);
}

export function getHistory() {
  return readHistory().sort(
    (first, second) => new Date(second.created_at) - new Date(first.created_at),
  );
}

export function clearHistory() {
  localStorage.clear();
}
