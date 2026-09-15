# Public UI Redesign Plan

## Overview

Redesign all public LegalLens AI pages as a cohesive, professional legal-product experience. The work will retain the existing static HTML architecture, API contracts, local-storage behavior, accessibility semantics, and user journeys while introducing a refined navy and slate design system, hosted typography, and inline SVG icons. The redesign covers the upload home page, analysis workspace, and document-comparison page.

## Sub-Tasks

### 1. Establish the visual foundation

**Status:** [x] complete

**Intent:** Create a consistent high-trust visual language that replaces the current generic blue-and-gray presentation without changing application behavior.

**Expected Outcomes:**
- A navy, slate, and restrained accent color system with accessible contrast across interactive, informative, warning, and risk states.
- Hosted premium typography with robust system fallbacks.
- Updated global spacing, surface, border, shadow, focus, button, form-control, tab, and responsive-layout rules.
- Reusable inline SVG icon treatment that avoids a separate icon dependency or asset pipeline.

**Todo List:**
1. [x] Define semantic color, typography, elevation, radius, and spacing tokens in the shared stylesheet.
2. [x] Add the selected hosted font to each public document with appropriate fallback fonts.
3. [x] Restyle shared layout, header, disclaimer, actions, controls, cards, tabs, alerts, loading states, and focus states.
4. [x] Preserve reduced-motion behavior and existing semantic and ARIA patterns.
5. [x] Verify mobile and desktop visual behavior using the existing static-page structure.

**Relevant Context:**
- [`public/css/styles.css`](public/css/styles.css)
- [`public/index.html`](public/index.html)
- [`public/analyze.html`](public/analyze.html)
- [`public/compare.html`](public/compare.html)

### 2. Redesign the upload and recent-document experience

**Status:** [x] complete

**Intent:** Make the entry page feel like a confident, guided legal-document intake flow and improve the scanability of uploaded-document history.

**Expected Outcomes:**
- A more intentional product header and page introduction with clearer value proposition and legal trust framing.
- A prominent upload surface with inline SVG document and upload affordances, clearer drag-and-drop states, and an elevated primary action.
- Harmonized upload and paste-text tabs without changing their JavaScript selectors or behavior.
- Recent-document history that is visually structured and remains usable on narrow screens.

**Todo List:**
1. [x] Update the upload page markup only where needed for visual hierarchy and inline SVG icons.
2. [x] Move page-specific styling into the shared design system where it supports reusable patterns.
3. [x] Apply polished empty, selected-file, disabled, hover, keyboard-focus, and drag-over presentation while preserving current upload validation and submission logic.
4. [x] Improve history-section hierarchy and action placement without changing local-storage behavior.
5. [x] Confirm that all existing IDs, classes used by scripts, and accessible labels remain intact.

**Relevant Context:**
- [`public/index.html`](public/index.html)
- [`public/js/upload.js`](public/js/upload.js)
- [`public/js/storage.js`](public/js/storage.js)
- [`public/css/styles.css`](public/css/styles.css)

### 3. Redesign the analysis workspace and generated insights

**Status:** [ ] pending

**Intent:** Turn the post-upload analysis page into a focused legal-review workspace that clearly distinguishes document context, tools, findings, and conversational answers.

**Expected Outcomes:**
- A stronger workspace header with document metadata, back navigation, and trustworthy context cues.
- Clearer tool navigation and panel hierarchy for Simplify, Risks, Checklist, and Ask a Question.
- Refined result surfaces for overviews, clause explanations, risk findings, checklist tasks, and Q&A messages.
- Severity and disclaimer styling that communicates importance without relying on color alone.

**Todo List:**
1. Update analysis-page structural wrappers and add inline SVGs only where they reinforce navigation or content meaning.
2. Restyle tool tabs, panel states, prompts, action buttons, error views, loading indicators, and toast presentation.
3. Update result-rendering markup and CSS hooks as necessary while preserving returned API data, persisted results, and existing rendering behavior.
4. Improve Q&A message hierarchy and supporting-clause cues without altering question submission or chat-history storage.
5. Confirm keyboard navigation, tab semantics, readable contrast, screen-reader labels, and reduced-motion support remain functional.

**Relevant Context:**
- [`public/analyze.html`](public/analyze.html)
- [`public/js/render.js`](public/js/render.js)
- [`public/js/toast.js`](public/js/toast.js)
- [`public/js/api.js`](public/js/api.js)
- [`public/css/styles.css`](public/css/styles.css)

### 4. Redesign the two-document comparison workflow

**Status:** [ ] pending

**Intent:** Make document comparison feel structured and equitable, so users can confidently provide two sources and interpret similarities and material differences.

**Expected Outcomes:**
- A clear comparison header, guidance, and back-navigation treatment consistent with the upload page.
- Visually balanced Document A and Document B input panels with premium upload and paste-text states.
- More legible comparison results, including accessible treatment of material differences and mobile-friendly table behavior.
- Preserved file constraints, form validation, comparison requests, and response rendering.

**Todo List:**
1. Update comparison markup for hierarchy, panel labels, inline SVG affordances, and consistent calls to action.
2. Apply the shared upload, tab, form, and card treatments to both document inputs without breaking their selectors.
3. Restyle results sections, topic groups, difference indicators, and scrollable comparison tables.
4. Retain non-color indicators for changed rows and severity-like states.
5. Verify the existing one-column small-screen layout remains clear and usable.

**Relevant Context:**
- [`public/compare.html`](public/compare.html)
- Inline comparison logic in [`public/compare.html`](public/compare.html)
- [`public/js/render.js`](public/js/render.js)
- [`public/css/styles.css`](public/css/styles.css)

### 5. Validate the completed public experience

**Status:** [ ] pending

**Intent:** Ensure the redesign is visually consistent and does not regress the static frontend’s behavior or accessibility.

**Expected Outcomes:**
- All public pages load their hosted font and render correctly with fallbacks.
- Existing upload, paste, analysis, comparison, history, and navigation interactions continue to work.
- The experience is usable at desktop and mobile widths, with keyboard focus and reduced-motion support intact.

**Todo List:**
1. Exercise the upload and paste-text paths through the analysis page.
2. Exercise comparison inputs and results using the existing client-side flow.
3. Inspect responsive layouts at narrow and wide viewports.
4. Review keyboard navigation, focus visibility, tab controls, and contrast-sensitive status communication.
5. Run the project’s relevant automated checks and resolve regressions directly caused by the redesign.

**Relevant Context:**
- [`public/index.html`](public/index.html)
- [`public/analyze.html`](public/analyze.html)
- [`public/compare.html`](public/compare.html)
- [`tests`](tests)
- [`README.md`](README.md)
