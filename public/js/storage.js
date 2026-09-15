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
  localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
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
  return readHistory().find((item) => item.id === documentId)?.text || null;
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
