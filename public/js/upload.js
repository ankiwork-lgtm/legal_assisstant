import { extractDocument, MAX_FILE_SIZE } from "/js/api.js";
import { saveDocument, getHistory, clearHistory } from "/js/storage.js";
import { showError as showToast } from "/js/toast.js";

const MAX_TEXT_CHARS = 50_000;

// ── UUID helper ───────────────────────────────────────────────────────────────
function generateId() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  // Simple fallback for environments without crypto.randomUUID
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    return (c === "x" ? r : (r & 0x3) | 0x8).toString(16);
  });
}

// ── DOM references ────────────────────────────────────────────────────────────
const form = document.getElementById("upload-form");
const submitBtn = document.getElementById("submit-btn");
const errorMsg = document.getElementById("error-msg");
const loadingIndicator = document.getElementById("loading-indicator");

// Tabs
const tabFile = document.getElementById("tab-file");
const tabText = document.getElementById("tab-text");
const panelFile = document.getElementById("panel-file");
const panelText = document.getElementById("panel-text");

// File upload
const dropZone = document.getElementById("drop-zone");
const fileInput = document.getElementById("file-input");
const fileChosen = document.getElementById("file-chosen");

// Paste text
const docNameInput = document.getElementById("doc-name");
const docTextArea = document.getElementById("doc-text");

// History
const historyList = document.getElementById("history-list");
const clearHistoryBtn = document.getElementById("clear-history-btn");

// ── State ─────────────────────────────────────────────────────────────────────
let activeMode = "file"; // "file" | "text"
let selectedFile = null;

// ── Tab switching ─────────────────────────────────────────────────────────────
const tabOrder = [tabFile, tabText];

function activateTab(mode) {
  activeMode = mode;
  const isFile = mode === "file";

  tabFile.setAttribute("aria-selected", String(isFile));
  tabFile.classList.toggle("tab--active", isFile);
  tabFile.setAttribute("tabindex", isFile ? "0" : "-1");

  tabText.setAttribute("aria-selected", String(!isFile));
  tabText.classList.toggle("tab--active", !isFile);
  tabText.setAttribute("tabindex", isFile ? "-1" : "0");

  panelFile.hidden = !isFile;
  panelText.hidden = isFile;

  hideError();
  updateSubmitState();
}

tabFile.addEventListener("click", () => activateTab("file"));
tabText.addEventListener("click", () => activateTab("text"));

// Allow keyboard activation (Enter / Space) and arrow-key focus navigation
tabOrder.forEach((tab, i) => {
  tab.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      tab.click();
    } else if (e.key === "ArrowRight") {
      e.preventDefault();
      tabOrder[(i + 1) % tabOrder.length].focus();
    } else if (e.key === "ArrowLeft") {
      e.preventDefault();
      tabOrder[(i - 1 + tabOrder.length) % tabOrder.length].focus();
    }
  });
});

// ── Submit state ──────────────────────────────────────────────────────────────
function updateSubmitState() {
  const ready =
    activeMode === "file"
      ? selectedFile !== null
      : docTextArea.value.trim().length > 0 && docTextArea.value.trim().length <= MAX_TEXT_CHARS;
  submitBtn.disabled = !ready;
}

docTextArea.addEventListener("input", () => {
  const textLength = docTextArea.value.trim().length;
  if (textLength > MAX_TEXT_CHARS) {
    showError(`Pasted text is too long (${textLength.toLocaleString()} characters). Maximum allowed length is ${MAX_TEXT_CHARS.toLocaleString()} characters.`);
  } else {
    hideError();
  }
  updateSubmitState();
});

// ── Error helpers ─────────────────────────────────────────────────────────────
function showError(message) {
  errorMsg.textContent = message;
  errorMsg.style.display = "block";
}

function hideError() {
  errorMsg.textContent = "";
  errorMsg.style.display = "none";
}

// ── Drag-and-drop ─────────────────────────────────────────────────────────────
dropZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropZone.classList.add("drop-zone--over");
});

dropZone.addEventListener("dragleave", () => {
  dropZone.classList.remove("drop-zone--over");
});

dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropZone.classList.remove("drop-zone--over");
  const file = e.dataTransfer?.files?.[0];
  if (file) handleFileSelection(file);
});

// Keyboard activation for the drop zone (acts as a button)
dropZone.addEventListener("keydown", (e) => {
  if (e.key === "Enter" || e.key === " ") {
    e.preventDefault();
    fileInput.click();
  }
});

fileInput.addEventListener("change", () => {
  if (fileInput.files?.[0]) {
    handleFileSelection(fileInput.files[0]);
  }
});

function handleFileSelection(file) {
  hideError();

  if (!file.name.toLowerCase().endsWith(".pdf")) {
    showError("Only PDF files are supported. Please select a .pdf file.");
    selectedFile = null;
    fileChosen.innerHTML = "";
    updateSubmitState();
    return;
  }

  if (file.size > MAX_FILE_SIZE) {
    showError(`File is too large (${(file.size / 1024 / 1024).toFixed(1)} MB). Maximum allowed size is 10 MB.`);
    selectedFile = null;
    fileChosen.innerHTML = "";
    updateSubmitState();
    return;
  }

  selectedFile = file;
  fileChosen.innerHTML = `
    <svg class="icon icon--sm file-chosen__icon" aria-hidden="true" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
      <polyline points="22 4 12 14.01 9 11.01"/>
    </svg>
    <strong>${escapeHtml(file.name)}</strong>
    <span class="file-chosen__size">(${(file.size / 1024).toFixed(0)} KB)</span>`;
  updateSubmitState();
}

// ── Form submission ───────────────────────────────────────────────────────────
form.addEventListener("submit", async (e) => {
  e.preventDefault();
  hideError();

  const documentId = generateId();
  const formData = new FormData();

  if (activeMode === "file") {
    if (!selectedFile) {
      showError("Please select a PDF file before submitting.");
      return;
    }
    formData.append("file", selectedFile);
  } else {
    const text = docTextArea.value.trim();
    if (!text) {
      showError("Please paste some document text before submitting.");
      return;
    }
    if (text.length > MAX_TEXT_CHARS) {
      showError(`Pasted text is too long (${text.length.toLocaleString()} characters). Maximum allowed length is ${MAX_TEXT_CHARS.toLocaleString()} characters.`);
      return;
    }
    formData.append("text", text);
    const name = docNameInput.value.trim();
    if (name) formData.append("doc_name", name);
  }

  submitBtn.disabled = true;
  loadingIndicator.style.display = "flex";

  try {
    const result = await extractDocument(formData);

    const label =
      activeMode === "file"
        ? selectedFile.name
        : (docNameInput.value.trim() || "Pasted document");

    saveDocument(documentId, label, result.text ?? "");
    window.location.href = `/analyze.html?id=${encodeURIComponent(documentId)}`;
  } catch (err) {
    const msg = err.message || "Something went wrong. Please try again.";
    showError(msg);
    showToast(msg);
    submitBtn.disabled = false;
    loadingIndicator.style.display = "none";
  }
});

// ── FR-7: Session history ─────────────────────────────────────────────────────
function formatDate(isoString) {
  try {
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(isoString));
  } catch {
    return isoString;
  }
}

function renderHistory() {
  const entries = getHistory();
  historyList.innerHTML = "";

  if (entries.length === 0) {
    historyList.innerHTML =
      '<li class="history-empty">No recent documents. Upload one above to get started.</li>';
    return;
  }

  entries.forEach((entry) => {
    const li = document.createElement("li");
    li.className = "history-item";
    li.innerHTML = `
      <span class="history-item__icon" aria-hidden="true">
        <svg class="icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
          <line x1="16" y1="13" x2="8" y2="13"/>
          <line x1="16" y1="17" x2="8" y2="17"/>
          <polyline points="10 9 9 9 8 9"/>
        </svg>
      </span>
      <div class="history-item__meta">
        <div class="history-item__label" title="${escapeHtml(entry.label)}">${escapeHtml(entry.label)}</div>
        <div class="history-item__date">${formatDate(entry.created_at)}</div>
      </div>
      <a class="button button--secondary button--sm history-item__open" href="/analyze.html?id=${encodeURIComponent(entry.id)}">
        <svg class="icon icon--sm" aria-hidden="true" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
          <circle cx="12" cy="12" r="3"/>
        </svg>
        Open
      </a>
    `;
    historyList.appendChild(li);
  });
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

clearHistoryBtn.addEventListener("click", () => {
  clearHistory();
  renderHistory();
});

// ── Initialise ────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", renderHistory);

// In case the script runs after DOMContentLoaded (defer/module)
if (document.readyState !== "loading") {
  renderHistory();
}
