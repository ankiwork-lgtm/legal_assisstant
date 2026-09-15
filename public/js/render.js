/**
 * render.js — DOM rendering helpers for LegalLens AI analyze.html
 *
 * All functions clear `container`, build DOM nodes, and append them.
 * Each function ends with an inline FR-8 disclaimer paragraph.
 */

const DISCLAIMER_TEXT =
  "⚠️ This output is for informational purposes only and is not legal advice. " +
  "Consult a qualified attorney before making decisions with legal consequences.";

function escapeHtml(str) {
  return String(str ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function appendDisclaimer(container) {
  const p = document.createElement("p");
  p.className = "disclaimer-inline";
  p.textContent = DISCLAIMER_TEXT;
  container.appendChild(p);
}

// ── renderSimplify ─────────────────────────────────────────────────────────────
// data shape: { overview: str, sections: [{ heading, plain_language }] }
export function renderSimplify(data, container) {
  container.innerHTML = "";

  // Overview box
  const overviewBox = document.createElement("div");
  overviewBox.className = "panel";
  overviewBox.style.cssText =
    "background:#eff6ff;border-color:#bfdbfe;margin-bottom:1.25rem;";
  const overviewHeading = document.createElement("h3");
  overviewHeading.className = "panel__title";
  overviewHeading.textContent = "Overview";
  const overviewText = document.createElement("p");
  overviewText.style.margin = "0";
  overviewText.textContent = data.overview ?? "";
  overviewBox.appendChild(overviewHeading);
  overviewBox.appendChild(overviewText);
  container.appendChild(overviewBox);

  // Sections
  const sections = Array.isArray(data.sections) ? data.sections : [];
  sections.forEach((section) => {
    const card = document.createElement("div");
    card.className = "card";
    const h3 = document.createElement("h3");
    h3.style.cssText = "margin:0 0 0.5rem;font-size:1rem;";
    h3.textContent = section.heading ?? "Section";
    const p = document.createElement("p");
    p.style.margin = "0";
    p.textContent = section.plain_language ?? "";
    card.appendChild(h3);
    card.appendChild(p);
    container.appendChild(card);
  });

  appendDisclaimer(container);
}

// ── renderRisks ───────────────────────────────────────────────────────────────
// data shape: { categories: [{ category, items: [{ clause_ref, severity, explanation }] }] }
export function renderRisks(data, container) {
  container.innerHTML = "";

  const severityClass = (s) => {
    const level = String(s ?? "info").toLowerCase();
    if (level === "high") return "severity--high";
    if (level === "medium") return "severity--medium";
    if (level === "low") return "severity--low";
    return "severity--info";
  };

  const categories = Array.isArray(data.categories) ? data.categories : [];
  categories.forEach((cat) => {
    const section = document.createElement("div");
    section.className = "card";
    section.style.marginBottom = "1rem";

    const h3 = document.createElement("h3");
    h3.style.cssText = "margin:0 0 0.75rem;font-size:1rem;";
    h3.textContent = cat.category ?? "General";
    section.appendChild(h3);

    const items = Array.isArray(cat.items) ? cat.items : [];
    items.forEach((item) => {
      const row = document.createElement("div");
      row.style.cssText =
        "display:flex;flex-wrap:wrap;gap:0.5rem;align-items:flex-start;" +
        "padding:0.625rem 0;border-top:1px solid var(--color-border);";

      const badge = document.createElement("span");
      badge.className = `severity ${severityClass(item.severity)}`;
      badge.textContent = String(item.severity ?? "info").toUpperCase();

      const body = document.createElement("div");
      body.style.flex = "1";

      const clauseRef = document.createElement("div");
      clauseRef.style.cssText =
        "font-size:0.8125rem;color:var(--color-muted);margin-bottom:0.25rem;";
      clauseRef.textContent = item.clause_ref ?? "";

      const explanation = document.createElement("div");
      explanation.style.cssText = "font-size:0.9375rem;";
      explanation.textContent = item.explanation ?? "";

      body.appendChild(clauseRef);
      body.appendChild(explanation);
      row.appendChild(badge);
      row.appendChild(body);
      section.appendChild(row);
    });

    container.appendChild(section);
  });

  appendDisclaimer(container);
}

// ── renderChecklist ───────────────────────────────────────────────────────────
// data shape: { ask_lawyer: [str], verify_yourself: [str] }
export function renderChecklist(data, container) {
  container.innerHTML = "";

  function buildList(title, items, storagePrefix) {
    const section = document.createElement("div");
    section.className = "card";
    section.style.marginBottom = "1rem";

    const h3 = document.createElement("h3");
    h3.style.cssText = "margin:0 0 0.75rem;font-size:1rem;";
    h3.textContent = title;
    section.appendChild(h3);

    const ul = document.createElement("ul");
    ul.style.cssText = "margin:0;padding:0;list-style:none;";

    const arr = Array.isArray(items) ? items : [];
    arr.forEach((text, idx) => {
      const key = `${storagePrefix}-${idx}`;
      const li = document.createElement("li");
      li.style.cssText =
        "display:flex;gap:0.625rem;align-items:flex-start;" +
        "padding:0.5rem 0;border-top:1px solid var(--color-border);";
      li.style.borderTop = idx === 0 ? "none" : "1px solid var(--color-border)";

      const cb = document.createElement("input");
      cb.type = "checkbox";
      cb.id = `cb-${key}`;
      cb.style.marginTop = "0.2rem";
      cb.checked = localStorage.getItem(`legallens-cb-${key}`) === "1";
      cb.addEventListener("change", () => {
        localStorage.setItem(`legallens-cb-${key}`, cb.checked ? "1" : "0");
      });

      const label = document.createElement("label");
      label.htmlFor = `cb-${key}`;
      label.style.cssText = "flex:1;cursor:pointer;";
      label.textContent = text;

      li.appendChild(cb);
      li.appendChild(label);
      ul.appendChild(li);
    });

    section.appendChild(ul);
    return section;
  }

  container.appendChild(
    buildList("Questions to Ask a Lawyer or the Other Party", data.ask_lawyer, "ask")
  );
  container.appendChild(
    buildList("Things to Verify Yourself", data.verify_yourself, "verify")
  );

  appendDisclaimer(container);
}

// ── renderQA ──────────────────────────────────────────────────────────────────
// history shape: [{ question, answer, found_in_document, supporting_clause_ref }]
// Renders the full chat thread; the caller appends new exchanges on each answer.
export function renderQA(history, container) {
  container.innerHTML = "";

  const thread = document.createElement("div");
  thread.id = "qa-thread";
  thread.style.cssText = "display:flex;flex-direction:column;gap:0.75rem;margin-bottom:1rem;";

  const arr = Array.isArray(history) ? history : [];
  arr.forEach((exchange) => {
    // User bubble
    const userBubble = document.createElement("div");
    userBubble.style.cssText =
      "align-self:flex-end;max-width:80%;padding:0.625rem 0.875rem;" +
      "background:#dbeafe;border:1px solid #bfdbfe;border-radius:1rem 1rem 0.25rem 1rem;" +
      "font-size:0.9375rem;";
    userBubble.textContent = exchange.question ?? "";
    thread.appendChild(userBubble);

    // AI bubble
    const aiBubble = document.createElement("div");
    aiBubble.style.cssText =
      "align-self:flex-start;max-width:85%;padding:0.625rem 0.875rem;" +
      "background:var(--color-surface);border:1px solid var(--color-border);" +
      "border-radius:1rem 1rem 1rem 0.25rem;font-size:0.9375rem;";

    const answerText = document.createElement("p");
    answerText.style.margin = "0";
    answerText.textContent = exchange.answer ?? "";
    aiBubble.appendChild(answerText);

    if (exchange.found_in_document === false) {
      const note = document.createElement("p");
      note.style.cssText =
        "margin:0.5rem 0 0;font-size:0.8125rem;color:var(--color-muted);font-style:italic;";
      note.textContent = "ℹ️ This point was not found in the document.";
      aiBubble.appendChild(note);
    }

    if (exchange.supporting_clause_ref) {
      const tag = document.createElement("span");
      tag.style.cssText =
        "display:inline-block;margin-top:0.5rem;padding:0.125rem 0.5rem;" +
        "font-size:0.75rem;background:#f0fdf4;border:1px solid #86efac;" +
        "border-radius:0.25rem;color:#166534;";
      tag.textContent = `§ ${exchange.supporting_clause_ref}`;
      aiBubble.appendChild(tag);
    }

    thread.appendChild(aiBubble);
  });

  container.appendChild(thread);
  appendDisclaimer(container);
}

// ── renderCompare ─────────────────────────────────────────────────────────────
// data shape: { shared_topics: [{ topic, doc_a_position, doc_b_position,
//   materially_different, why_it_matters }], only_in_a: [str], only_in_b: [str] }
export function renderCompare(data, container, labelA = "Document A", labelB = "Document B") {
  container.innerHTML = "";

  const sharedTopics = Array.isArray(data.shared_topics) ? data.shared_topics : [];
  const onlyInA = Array.isArray(data.only_in_a) ? data.only_in_a : [];
  const onlyInB = Array.isArray(data.only_in_b) ? data.only_in_b : [];

  if (sharedTopics.length === 0 && onlyInA.length === 0 && onlyInB.length === 0) {
    const empty = document.createElement("p");
    empty.className = "comparison-empty";
    empty.textContent = "No significant differences found.";
    container.appendChild(empty);
    appendDisclaimer(container);
    return;
  }

  if (sharedTopics.length > 0) {
    const heading = document.createElement("h3");
    heading.className = "comparison-heading";
    heading.textContent = "Shared Topics";
    container.appendChild(heading);

    const tableWrapper = document.createElement("div");
    tableWrapper.className = "comparison-table-wrapper";
    const table = document.createElement("table");
    table.className = "comparison-table";
    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");

    ["Topic", `${labelA} Position`, `${labelB} Position`, "Materially Different", "Why It Matters"].forEach((text) => {
      const th = document.createElement("th");
      th.scope = "col";
      th.textContent = text;
      headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);

    const tbody = document.createElement("tbody");
    sharedTopics.forEach((item) => {
      const row = document.createElement("tr");
      if (item.materially_different) row.className = "comparison-table__row--different";
      [
        item.topic,
        item.doc_a_position,
        item.doc_b_position,
        item.materially_different ? "Yes" : "No",
        item.why_it_matters,
      ].forEach((text) => {
        const td = document.createElement("td");
        td.textContent = text ?? "";
        row.appendChild(td);
      });
      tbody.appendChild(row);
    });
    table.appendChild(tbody);
    tableWrapper.appendChild(table);
    container.appendChild(tableWrapper);
  }

  function appendOnlyList(title, items) {
    if (items.length === 0) return;
    const section = document.createElement("section");
    section.className = "comparison-only";
    const heading = document.createElement("h3");
    heading.className = "comparison-heading";
    heading.textContent = title;
    const list = document.createElement("ul");
    list.className = "comparison-list";
    items.forEach((item) => {
      const listItem = document.createElement("li");
      listItem.textContent = item ?? "";
      list.appendChild(listItem);
    });
    section.appendChild(heading);
    section.appendChild(list);
    container.appendChild(section);
  }

  appendOnlyList(`${labelA} Only`, onlyInA);
  appendOnlyList(`${labelB} Only`, onlyInB);
  appendDisclaimer(container);
}
