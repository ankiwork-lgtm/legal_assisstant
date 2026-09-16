import { compareDocuments, extractDocument, MAX_FILE_SIZE } from "/js/api.js";
import { saveResult } from "/js/storage.js";
import { renderCompare } from "/js/render.js";
import { showError as showToastError } from "/js/toast.js";

const form = document.getElementById("compare-form");
const compareButton = document.getElementById("compare-btn");
const error = document.getElementById("error-msg");
const loading = document.getElementById("loading-indicator");
const resultsSection = document.getElementById("results-section");
const results = document.getElementById("results");
const documents = {
  a: createDocumentInput("a", "Document A"),
  b: createDocumentInput("b", "Document B"),
};

function createDocumentInput(key, defaultLabel) {
  const input = {
    mode: "file",
    file: null,
    defaultLabel,
    label: document.getElementById(`label-${key}`),
    text: document.getElementById(`text-${key}`),
    fileInput: document.getElementById(`file-${key}`),
    fileChosen: document.getElementById(`file-chosen-${key}`),
    dropZone: document.getElementById(`drop-zone-${key}`),
    fileTab: document.getElementById(`tab-${key}-file`),
    textTab: document.getElementById(`tab-${key}-text`),
    filePanel: document.getElementById(`panel-${key}-file`),
    textPanel: document.getElementById(`panel-${key}-text`),
  };

  input.fileTab.addEventListener("click", () => activateMode(input, "file"));
  input.textTab.addEventListener("click", () => activateMode(input, "text"));
  [input.fileTab, input.textTab].forEach((tab) => {
    tab.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        tab.click();
      }
    });
  });
  input.text.addEventListener("input", updateSubmitState);
  input.fileInput.addEventListener("change", () => selectFile(input, input.fileInput.files?.[0]));
  input.dropZone.addEventListener("dragover", (event) => {
    event.preventDefault();
    input.dropZone.classList.add("drop-zone--over");
  });
  input.dropZone.addEventListener("dragleave", () => input.dropZone.classList.remove("drop-zone--over"));
  input.dropZone.addEventListener("drop", (event) => {
    event.preventDefault();
    input.dropZone.classList.remove("drop-zone--over");
    selectFile(input, event.dataTransfer?.files?.[0]);
  });
  input.dropZone.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      input.fileInput.click();
    }
  });
  return input;
}

function activateMode(input, mode) {
  input.mode = mode;
  const isFile = mode === "file";
  input.fileTab.setAttribute("aria-selected", String(isFile));
  input.fileTab.classList.toggle("tab--active", isFile);
  input.textTab.setAttribute("aria-selected", String(!isFile));
  input.textTab.classList.toggle("tab--active", !isFile);
  input.filePanel.hidden = !isFile;
  input.textPanel.hidden = isFile;
  hideError();
  updateSubmitState();
}

function selectFile(input, file) {
  hideError();
  if (!file) return;
  if (!file.name.toLowerCase().endsWith(".pdf")) {
    input.file = null;
    input.fileInput.value = "";
    input.fileChosen.textContent = "";
    showError("Only PDF files are supported. Please select a .pdf file.");
  } else if (file.size > MAX_FILE_SIZE) {
    input.file = null;
    input.fileInput.value = "";
    input.fileChosen.textContent = "";
    showError("Each file must be 10 MB or smaller.");
  } else {
    input.file = file;
    input.fileChosen.textContent = `Selected: ${file.name} (${(file.size / 1024).toFixed(0)} KB)`;
  }
  updateSubmitState();
}

function hasContent(input) {
  return input.mode === "file" ? input.file !== null : input.text.value.trim().length > 0;
}

function updateSubmitState() {
  compareButton.disabled = !hasContent(documents.a) || !hasContent(documents.b);
}

function showError(message) {
  error.textContent = message;
  error.style.display = "block";
}

function hideError() {
  error.textContent = "";
  error.style.display = "none";
}

async function getDocumentText(input) {
  if (input.mode === "text") return input.text.value.trim();
  const formData = new FormData();
  formData.append("file", input.file);
  const extracted = await extractDocument(formData);
  return extracted.text ?? "";
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideError();
  if (!hasContent(documents.a) || !hasContent(documents.b)) {
    showError("Please provide both documents before comparing.");
    return;
  }

  const labelA = documents.a.label.value.trim() || documents.a.defaultLabel;
  const labelB = documents.b.label.value.trim() || documents.b.defaultLabel;
  compareButton.disabled = true;
  loading.style.display = "flex";
  resultsSection.style.display = "none";

  try {
    const [docA, docB] = await Promise.all([
      getDocumentText(documents.a),
      getDocumentText(documents.b),
    ]);
    const data = await compareDocuments(docA, docB, labelA, labelB);
    saveResult(`compare-${Date.now()}`, "compare", data);
    renderCompare(data, results, labelA, labelB);
    resultsSection.style.display = "block";
  } catch (err) {
    const msg = err.message || "Something went wrong. Please try again.";
    showError(msg);
    showToastError(msg);
  } finally {
    loading.style.display = "none";
    updateSubmitState();
  }
});
