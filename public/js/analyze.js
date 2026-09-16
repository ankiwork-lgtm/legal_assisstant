import { simplifyDocument, analyzeRisks, generateChecklist, askQuestion } from "/js/api.js";
import { getDocument, getHistory, saveResult } from "/js/storage.js";
import { renderSimplify, renderRisks, renderChecklist, renderQA } from "/js/render.js";
import { showError } from "/js/toast.js";

// ── Read ?id= query param ──────────────────────────────────────────────────
const params = new URLSearchParams(window.location.search);
const documentId = params.get("id");

const docMetaEl    = document.getElementById("doc-meta");
const docLabelEl   = document.getElementById("doc-label");
const errorPageEl  = document.getElementById("error-page");
const errorPageMsg = document.getElementById("error-page-msg");
const workspaceEl  = document.getElementById("workspace");

// ── Load document from localStorage ───────────────────────────────────────
if (!documentId) {
  showErrorPage("No document ID was provided in the URL.");
} else {
  const text = getDocument(documentId);
  if (text === null) {
    showErrorPage(
      "This document could not be found. It may have been cleared from your " +
      "browser history, or the link may belong to a different browser session " +
      "(e.g. private/incognito mode clears storage on close). " +
      "Please upload the document again."
    );
  } else if (text === "") {
    showErrorPage(
      "The document was saved but contains no text. " +
      "Please go back and upload the document again."
    );
  } else {
    // Find the label from history
    const entry = getHistory().find((e) => e.id === documentId);
    const label = entry?.label ?? "Document";
    docLabelEl.textContent = label;
    docLabelEl.title = label;
    document.title = `LegalLens AI — ${label}`;
    docMetaEl.hidden = false;
    workspaceEl.hidden = false;
    try {
      init(text, entry);
    } catch (err) {
      // init() failing after workspace is revealed would leave a blank UI —
      // show the error page so the user has a clear recovery path.
      workspaceEl.hidden = true;
      docMetaEl.hidden = true;
      showErrorPage(
        "An unexpected error occurred while loading the workspace. " +
        "Please go back and upload the document again."
      );
      console.error("[LegalLens] init() threw:", err);
    }
  }
}

function showErrorPage(msg) {
  errorPageMsg.textContent = msg;
  errorPageEl.hidden = false;
}

// ── Tab switching ──────────────────────────────────────────────────────────
const tabs = [
  { tab: document.getElementById("tab-simplify"),  panel: document.getElementById("panel-simplify") },
  { tab: document.getElementById("tab-risks"),     panel: document.getElementById("panel-risks") },
  { tab: document.getElementById("tab-checklist"), panel: document.getElementById("panel-checklist") },
  { tab: document.getElementById("tab-qa"),        panel: document.getElementById("panel-qa") },
];

function activateTab(index) {
  tabs.forEach(({ tab, panel }, i) => {
    const active = i === index;
    tab.setAttribute("aria-selected", String(active));
    tab.classList.toggle("tab--active", active);
    tab.setAttribute("tabindex", active ? "0" : "-1");
    panel.hidden = !active;
  });
}

tabs.forEach(({ tab }, i) => {
  tab.addEventListener("click", () => activateTab(i));
  tab.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      tab.click();
    } else if (e.key === "ArrowRight") {
      e.preventDefault();
      tabs[(i + 1) % tabs.length].tab.focus();
    } else if (e.key === "ArrowLeft") {
      e.preventDefault();
      tabs[(i - 1 + tabs.length) % tabs.length].tab.focus();
    }
  });
});

// ── Generic lazy-load helper ───────────────────────────────────────────────
function setupLazyTab({ generateBtn, generateRow, loading, error, result, apiFn, kind, renderFn, loadingLabel }) {
  generateBtn.addEventListener("click", async () => {
    generateRow.style.display = "none";
    error.style.display = "none";
    // Update the accessible label so screen readers announce the right action
    if (loadingLabel) loading.setAttribute("aria-label", loadingLabel);
    loading.style.display = "flex";
    result.style.display = "none";

    try {
      const text = getDocument(documentId);
      const data = await apiFn(text);
      saveResult(documentId, kind, data);
      renderFn(data, result);
      result.style.display = "block";
    } catch (err) {
      const msg = err.message || "Something went wrong. Please try again.";
      error.textContent = msg;
      error.style.display = "block";
      showError(msg);
      generateRow.style.display = "flex"; // allow retry
    } finally {
      loading.style.display = "none";
    }
  });
}

// ── Initialise all tabs ────────────────────────────────────────────────────
function init(text, entry) {
  const cached = entry?.results ?? {};

  // ── Simplify ────────────────────────────────────────────────────────────
  const simplifyResult  = document.getElementById("simplify-result");
  const simplifyGenRow  = document.getElementById("simplify-generate-row");
  if (cached.simplify) {
    renderSimplify(cached.simplify, simplifyResult);
    simplifyResult.style.display = "block";
    simplifyGenRow.style.display = "none";
  } else {
    setupLazyTab({
      generateBtn: document.getElementById("simplify-generate-btn"),
      generateRow: simplifyGenRow,
      loading:     document.getElementById("simplify-loading"),
      error:       document.getElementById("simplify-error"),
      result:      simplifyResult,
      apiFn:       simplifyDocument,
      kind:        "simplify",
      renderFn:    renderSimplify,
      loadingLabel: "Simplifying document…",
    });
  }

  // ── Risks ────────────────────────────────────────────────────────────────
  const risksResult  = document.getElementById("risks-result");
  const risksGenRow  = document.getElementById("risks-generate-row");
  if (cached.risks) {
    renderRisks(cached.risks, risksResult);
    risksResult.style.display = "block";
    risksGenRow.style.display = "none";
  } else {
    setupLazyTab({
      generateBtn: document.getElementById("risks-generate-btn"),
      generateRow: risksGenRow,
      loading:     document.getElementById("risks-loading"),
      error:       document.getElementById("risks-error"),
      result:      risksResult,
      apiFn:       analyzeRisks,
      kind:        "risks",
      renderFn:    renderRisks,
      loadingLabel: "Analysing risks…",
    });
  }

  // ── Checklist ────────────────────────────────────────────────────────────
  const checklistResult = document.getElementById("checklist-result");
  const checklistGenRow = document.getElementById("checklist-generate-row");
  if (cached.checklist) {
    renderChecklist(cached.checklist, checklistResult);
    checklistResult.style.display = "block";
    checklistGenRow.style.display = "none";
  } else {
    setupLazyTab({
      generateBtn: document.getElementById("checklist-generate-btn"),
      generateRow: checklistGenRow,
      loading:     document.getElementById("checklist-loading"),
      error:       document.getElementById("checklist-error"),
      result:      checklistResult,
      apiFn:       generateChecklist,
      kind:        "checklist",
      renderFn:    renderChecklist,
      loadingLabel: "Generating checklist…",
    });
  }

  // ── Q&A ──────────────────────────────────────────────────────────────────
  const qaResult  = document.getElementById("qa-result");
  const qaLoading = document.getElementById("qa-loading");
  const qaError   = document.getElementById("qa-error");
  const qaInput   = document.getElementById("qa-question");
  const qaAskBtn  = document.getElementById("qa-ask-btn");

  // Build history array: [{question, answer, found_in_document, supporting_clause_ref}]
  // storage.js saves qa as an array of raw API responses; we need the associated questions too.
  // We store enriched objects: { question, answer, found_in_document, supporting_clause_ref }
  let qaHistory = Array.isArray(cached.qa) ? cached.qa : [];

  // Render any cached exchanges
  if (qaHistory.length > 0) {
    renderQA(qaHistory, qaResult);
  } else {
    // Show empty state placeholder
    qaResult.innerHTML =
      '<p style="color:var(--color-muted);font-size:0.9375rem;margin:0 0 0.5rem;">' +
      'Ask any question about this document and get an answer grounded in the text.</p>';
  }

  // Enable/disable Ask button on textarea input
  qaInput.addEventListener("input", () => {
    qaAskBtn.disabled = qaInput.value.trim().length === 0;
  });

  qaAskBtn.addEventListener("click", async () => {
    const question = qaInput.value.trim();
    if (!question) return;

    qaInput.disabled = true;
    qaAskBtn.disabled = true;
    qaError.style.display = "none";
    qaLoading.setAttribute("aria-label", "Answering your question…");
    qaLoading.style.display = "flex";

    try {
      // Build history format for the API: [{role, content}]
      const apiHistory = qaHistory.flatMap((exchange) => [
        { role: "user",  content: exchange.question },
        { role: "assistant", content: exchange.answer },
      ]);

      const data = await askQuestion(text, question, apiHistory);
      const exchange = {
        question,
        answer:               data.answer,
        found_in_document:    data.found_in_document,
        supporting_clause_ref: data.supporting_clause_ref ?? null,
      };
      qaHistory = [...qaHistory, exchange];
      saveResult(documentId, "qa", exchange);
      renderQA(qaHistory, qaResult);
      qaInput.value = "";
      qaAskBtn.disabled = true;
    } catch (err) {
      const msg = err.message || "Something went wrong. Please try again.";
      qaError.textContent = msg;
      qaError.style.display = "block";
      showError(msg);
    } finally {
      qaLoading.style.display = "none";
      qaInput.disabled = false;
      qaInput.focus();
    }
  });

  // Allow Ctrl+Enter / Cmd+Enter to submit the question
  qaInput.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault();
      if (!qaAskBtn.disabled) qaAskBtn.click();
    }
  });
}
