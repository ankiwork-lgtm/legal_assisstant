/**
 * tests/js/test_api.js
 *
 * Plain Node.js unit tests for public/js/api.js.
 * No test framework, no npm. Run with:
 *   node tests/js/test_api.js
 *
 * Exits 0 on success, 1 on the first assertion failure.
 */

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
// Globals required by api.js
//   • window.location.hostname  — api.js uses this to decide the base URL
//   • fetch                     — replaced with a capture mock per test
// ---------------------------------------------------------------------------
globalThis.window = { location: { hostname: "localhost" } };
// With hostname === "localhost", API_BASE_URL resolves to "http://localhost:8000/api"
const EXPECTED_BASE = "http://localhost:8000/api";

// ---------------------------------------------------------------------------
// fetch mock factory
// Returns { mock, calls } where:
//   mock  — the function to assign to globalThis.fetch
//   calls — array of { url, options } recorded by the mock
// The mock always resolves with a minimal successful response.
// ---------------------------------------------------------------------------
function makeFetchMock(responseData = { ok: true }) {
  const calls = [];
  const mock = (url, options = {}) => {
    calls.push({ url, options });
    const response = {
      ok: true,
      json: () => Promise.resolve(responseData),
    };
    return Promise.resolve(response);
  };
  return { mock, calls };
}

// ---------------------------------------------------------------------------
// Load api.js via a data: URL so globals are captured at eval time.
// ---------------------------------------------------------------------------
const apiSrc = readFileSync(
  path.resolve(__dirname, "../../public/js/api.js"),
  "utf8"
);

async function loadApi() {
  const uid = Math.random().toString(36).slice(2);
  const src = apiSrc + `\n//# uid=${uid}`;
  const dataUrl = `data:text/javascript;charset=utf-8,${encodeURIComponent(src)}`;
  return import(dataUrl);
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

async function testExtractDocument() {
  console.log("\n[extractDocument]");
  const { mock, calls } = makeFetchMock({ text: "extracted", word_count: 2, page_count: 1 });
  globalThis.fetch = mock;
  const api = await loadApi();

  const formData = new FormData(); // Node 24 has FormData built-in
  await api.extractDocument(formData);

  assertEqual(calls.length, 1, "fetch called once");
  assertEqual(calls[0].url, `${EXPECTED_BASE}/documents/extract`, "correct URL");
  assertEqual(calls[0].options.method, "POST", "method is POST");
  assert(calls[0].options.body === formData, "body is the FormData instance");
  assert(!calls[0].options.headers, "no Content-Type header set (multipart boundary auto-set)");
}

async function testSimplifyDocument() {
  console.log("\n[simplifyDocument]");
  const { mock, calls } = makeFetchMock({ overview: "ok", sections: [] });
  globalThis.fetch = mock;
  const api = await loadApi();

  await api.simplifyDocument("contract text");

  assertEqual(calls.length, 1, "fetch called once");
  assertEqual(calls[0].url, `${EXPECTED_BASE}/analyze/simplify`, "correct URL");
  assertEqual(calls[0].options.method, "POST", "method is POST");
  assertEqual(calls[0].options.headers["Content-Type"], "application/json", "Content-Type header");
  assertEqual(JSON.parse(calls[0].options.body), { text: "contract text" }, "body contains text");
}

async function testAnalyzeRisks() {
  console.log("\n[analyzeRisks]");
  const { mock, calls } = makeFetchMock({ categories: [] });
  globalThis.fetch = mock;
  const api = await loadApi();

  await api.analyzeRisks("risky clause text");

  assertEqual(calls[0].url, `${EXPECTED_BASE}/analyze/risks`, "correct URL");
  assertEqual(calls[0].options.method, "POST", "method is POST");
  assertEqual(JSON.parse(calls[0].options.body), { text: "risky clause text" }, "body contains text");
}

async function testGenerateChecklist() {
  console.log("\n[generateChecklist]");
  const { mock, calls } = makeFetchMock({ ask_lawyer: [], verify_yourself: [] });
  globalThis.fetch = mock;
  const api = await loadApi();

  await api.generateChecklist("checklist text");

  assertEqual(calls[0].url, `${EXPECTED_BASE}/analyze/checklist`, "correct URL");
  assertEqual(calls[0].options.method, "POST", "method is POST");
  assertEqual(JSON.parse(calls[0].options.body), { text: "checklist text" }, "body contains text");
}

async function testCompareDocuments() {
  console.log("\n[compareDocuments]");
  const { mock, calls } = makeFetchMock({ shared_topics: [], only_in_a: [], only_in_b: [] });
  globalThis.fetch = mock;
  const api = await loadApi();

  await api.compareDocuments("textA", "textB", "LabelA", "LabelB");

  assertEqual(calls[0].url, `${EXPECTED_BASE}/analyze/compare`, "correct URL");
  assertEqual(calls[0].options.method, "POST", "method is POST");
  assertEqual(
    JSON.parse(calls[0].options.body),
    { doc_a: "textA", doc_b: "textB", label_a: "LabelA", label_b: "LabelB" },
    "body contains all four fields"
  );
}

async function testAskQuestion() {
  console.log("\n[askQuestion]");
  const { mock, calls } = makeFetchMock({
    answer: "Yes",
    found_in_document: true,
    supporting_clause_ref: "§1",
  });
  globalThis.fetch = mock;
  const api = await loadApi();

  const history = [{ role: "user", content: "prior Q" }];
  await api.askQuestion("doc text", "Is this valid?", history);

  assertEqual(calls[0].url, `${EXPECTED_BASE}/analyze/qa`, "correct URL");
  assertEqual(calls[0].options.method, "POST", "method is POST");
  assertEqual(
    JSON.parse(calls[0].options.body),
    { text: "doc text", question: "Is this valid?", history },
    "body contains text, question, and history"
  );
}

async function testRequestThrowsOnErrorResponse() {
  console.log("\n[request — throws on non-ok response]");
  const { mock } = makeFetchMock({ error: { message: "Not found" } });
  // Override to return ok: false
  const errorMock = (url, options) => Promise.resolve({
    ok: false,
    json: () => Promise.resolve({ error: { message: "Not found" } }),
  });
  globalThis.fetch = errorMock;
  const api = await loadApi();

  let threw = false;
  try {
    await api.simplifyDocument("some text");
  } catch (err) {
    threw = true;
    assert(err.message === "Not found", "error message propagated from response");
  }
  assert(threw, "promise rejects when response.ok is false");
}

async function testMaxFileSizeExported() {
  console.log("\n[MAX_FILE_SIZE constant]");
  const { mock } = makeFetchMock();
  globalThis.fetch = mock;
  const api = await loadApi();

  assertEqual(api.MAX_FILE_SIZE, 10 * 1024 * 1024, "MAX_FILE_SIZE is 10 MB");
}

// ---------------------------------------------------------------------------
// Runner
// ---------------------------------------------------------------------------
async function run() {
  console.log("=== test_api.js ===");
  await testExtractDocument();
  await testSimplifyDocument();
  await testAnalyzeRisks();
  await testGenerateChecklist();
  await testCompareDocuments();
  await testAskQuestion();
  await testRequestThrowsOnErrorResponse();
  await testMaxFileSizeExported();

  console.log(`\n${passed} passed, ${failed} failed`);
  if (failed > 0) process.exit(1);
}

run().catch((err) => {
  console.error("Unexpected error:", err);
  process.exit(1);
});
