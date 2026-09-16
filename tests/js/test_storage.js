/**
 * tests/js/test_storage.js
 *
 * Plain Node.js unit tests for public/js/storage.js.
 * No test framework, no npm. Run with:
 *   node tests/js/test_storage.js
 *
 * Exits 0 on success, 1 on the first assertion failure.
 */

import { createRequire } from "module";
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import path from "path";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// ---------------------------------------------------------------------------
// Minimal assertion helper
// ---------------------------------------------------------------------------
let passed = 0;
let failed = 0;

function assert(condition, message) {
  if (!condition) {
    console.error(`  FAIL: ${message}`);
    failed++;
  } else {
    console.log(`  pass: ${message}`);
    passed++;
  }
}

function assertEqual(actual, expected, message) {
  const ok = JSON.stringify(actual) === JSON.stringify(expected);
  assert(ok, `${message} — expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`);
}

// ---------------------------------------------------------------------------
// localStorage mock (in-memory Map)
// ---------------------------------------------------------------------------
function makeLocalStorage() {
  const store = new Map();
  return {
    getItem: (k) => (store.has(k) ? store.get(k) : null),
    setItem: (k, v) => store.set(k, String(v)),
    removeItem: (k) => store.delete(k),
    clear: () => store.clear(),
    get length() { return store.size; },
  };
}

// ---------------------------------------------------------------------------
// Load storage.js in this Node.js context.
// Because storage.js is an ES module that references the `localStorage`
// global, we must set globalThis.localStorage before the module is evaluated.
// We do this by reading the source and executing it via a data: URL import.
// ---------------------------------------------------------------------------
const storageSrc = readFileSync(
  path.resolve(__dirname, "../../public/js/storage.js"),
  "utf8"
);

// Each test suite gets a fresh localStorage instance.
function makeMod() {
  const ls = makeLocalStorage();
  globalThis.localStorage = ls;

  // Build a data: URL so Node re-evaluates the module each time (no cache
  // sharing between distinct data: URLs with different content).
  const uid = Math.random().toString(36).slice(2);
  const src = storageSrc + `\n//# uid=${uid}`;
  const dataUrl = `data:text/javascript;charset=utf-8,${encodeURIComponent(src)}`;
  return { ls, dataUrl };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

async function testSaveAndGetDocument() {
  console.log("\n[saveDocument / getDocument]");
  const { dataUrl } = makeMod();
  const { saveDocument, getDocument } = await import(dataUrl);

  saveDocument("doc-1", "My Contract", "hello world");
  assertEqual(getDocument("doc-1"), "hello world", "getDocument returns saved text");
  assertEqual(getDocument("missing"), null, "getDocument returns null for unknown id");
}

async function testSaveDocumentDeduplication() {
  console.log("\n[saveDocument — duplicate-ID deduplication]");
  const { dataUrl } = makeMod();
  const { saveDocument, getHistory } = await import(dataUrl);

  saveDocument("doc-dup", "First", "text-v1");
  saveDocument("doc-dup", "Updated", "text-v2");

  const history = getHistory();
  const entries = history.filter((e) => e.id === "doc-dup");
  assertEqual(entries.length, 1, "Only one entry exists for the same id");
  assertEqual(entries[0].label, "Updated", "Label was updated");
  assertEqual(entries[0].text, "text-v2", "Text was updated");
}

async function testSaveResult() {
  console.log("\n[saveResult]");
  const { dataUrl } = makeMod();
  const { saveDocument, saveResult, getHistory } = await import(dataUrl);

  saveDocument("doc-r", "Label", "content");
  saveResult("doc-r", "simplify", { overview: "ok" });

  const entry = getHistory().find((e) => e.id === "doc-r");
  assert(entry !== undefined, "entry exists after saveResult");
  assertEqual(entry.results.simplify, { overview: "ok" }, "simplify result stored");
}

async function testSaveResultQaAppends() {
  console.log("\n[saveResult — qa kind appends]");
  const { dataUrl } = makeMod();
  const { saveDocument, saveResult, getHistory } = await import(dataUrl);

  saveDocument("doc-qa", "Label", "content");
  saveResult("doc-qa", "qa", { question: "Q1", answer: "A1" });
  saveResult("doc-qa", "qa", { question: "Q2", answer: "A2" });

  const entry = getHistory().find((e) => e.id === "doc-qa");
  assertEqual(entry.results.qa.length, 2, "qa array has 2 entries after two saves");
  assertEqual(entry.results.qa[0].question, "Q1", "first qa entry is correct");
  assertEqual(entry.results.qa[1].question, "Q2", "second qa entry is correct");
}

async function testSaveResultUnknownKindThrows() {
  console.log("\n[saveResult — unknown kind throws]");
  const { dataUrl } = makeMod();
  const { saveDocument, saveResult } = await import(dataUrl);

  saveDocument("doc-x", "Label", "content");
  let threw = false;
  try {
    saveResult("doc-x", "unknown-kind", {});
  } catch {
    threw = true;
  }
  assert(threw, "saveResult throws for unsupported kind");
}

async function testGetHistorySorting() {
  console.log("\n[getHistory — sorted newest-first]");
  const { dataUrl } = makeMod();
  const { saveDocument, getHistory } = await import(dataUrl);

  // Insert in old→new order; history should return new→old
  saveDocument("doc-a", "Old", "");
  // Small delay so created_at timestamps differ (they use new Date())
  await new Promise((r) => setTimeout(r, 5));
  saveDocument("doc-b", "New", "");

  const history = getHistory();
  assert(history.length >= 2, "at least two entries");
  const idxA = history.findIndex((e) => e.id === "doc-a");
  const idxB = history.findIndex((e) => e.id === "doc-b");
  assert(idxB < idxA, "newer document (doc-b) appears before older document (doc-a)");
}

async function testClearHistory() {
  console.log("\n[clearHistory]");
  const { dataUrl } = makeMod();
  const { saveDocument, clearHistory, getHistory } = await import(dataUrl);

  saveDocument("doc-c", "Label", "text");
  clearHistory();

  const history = getHistory();
  assertEqual(history.length, 0, "history is empty after clearHistory");
}

async function testSaveResultCreatesEntryIfMissing() {
  console.log("\n[saveResult — creates entry when document was never saved]");
  const { dataUrl } = makeMod();
  const { saveResult, getHistory } = await import(dataUrl);

  saveResult("ghost-doc", "risks", { categories: [] });

  const entry = getHistory().find((e) => e.id === "ghost-doc");
  assert(entry !== undefined, "entry was created implicitly");
  assertEqual(entry.results.risks, { categories: [] }, "risk result stored on implicit entry");
}

async function testGetDocumentEmptyStringDistinct() {
  console.log("\n[getDocument — empty string vs null]");
  const { dataUrl } = makeMod();
  const { saveDocument, getDocument } = await import(dataUrl);

  saveDocument("doc-empty", "Empty", "");
  // An entry that exists but has empty text should return "" not null
  assertEqual(getDocument("doc-empty"), "", "getDocument returns empty string for entry with empty text");
  // A completely missing entry should still return null
  assertEqual(getDocument("no-such-id"), null, "getDocument returns null for unknown id");
}

async function testWriteHistoryQuotaError() {
  console.log("\n[writeHistory — QuotaExceededError propagates as user-friendly message]");
  const { dataUrl, ls } = makeMod();
  // Override setItem to simulate a QuotaExceededError
  ls.setItem = () => { throw new DOMException("QuotaExceededError", "QuotaExceededError"); };
  const { saveDocument } = await import(dataUrl);

  let thrownMsg = null;
  try {
    saveDocument("doc-q", "Label", "text");
  } catch (err) {
    thrownMsg = err.message;
  }
  assert(thrownMsg !== null, "saveDocument throws when storage quota is exceeded");
  assert(
    thrownMsg.toLowerCase().includes("storage") || thrownMsg.toLowerCase().includes("incognito"),
    "error message mentions storage or incognito"
  );
}

// ---------------------------------------------------------------------------
// Runner
// ---------------------------------------------------------------------------
async function run() {
  console.log("=== test_storage.js ===");
  await testSaveAndGetDocument();
  await testSaveDocumentDeduplication();
  await testSaveResult();
  await testSaveResultQaAppends();
  await testSaveResultUnknownKindThrows();
  await testGetHistorySorting();
  await testClearHistory();
  await testSaveResultCreatesEntryIfMissing();
  await testGetDocumentEmptyStringDistinct();
  await testWriteHistoryQuotaError();

  console.log(`\n${passed} passed, ${failed} failed`);
  if (failed > 0) process.exit(1);
}

run().catch((err) => {
  console.error("Unexpected error:", err);
  process.exit(1);
});
