/**
 * toast.js — Shared toast notification utility for LegalLens AI.
 *
 * Usage:
 *   import { showToast, showError } from "/js/toast.js";
 *   showError("Something went wrong.");
 *   showToast("Saved!", "success", 3000);
 *
 * Requires a <div id="toast-container"></div> in the page body and
 * the toast CSS from styles.css.
 */

/**
 * Display a toast notification.
 *
 * @param {string} message   - Text to display.
 * @param {"error"|"success"|"info"} [type="error"] - Visual style.
 * @param {number} [duration=5000] - Auto-dismiss delay in ms (0 = persistent).
 */
export function showToast(message, type = "error", duration = 5000) {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast toast--${type}`;
  toast.setAttribute("role", "status");
  toast.setAttribute("aria-live", type === "error" ? "assertive" : "polite");
  toast.setAttribute("aria-atomic", "true");

  const text = document.createElement("span");
  text.className = "toast__message";
  text.textContent = message;

  const closeBtn = document.createElement("button");
  closeBtn.className = "toast__close";
  closeBtn.setAttribute("aria-label", "Dismiss notification");
  closeBtn.textContent = "×";
  closeBtn.addEventListener("click", () => dismiss(toast));

  toast.appendChild(text);
  toast.appendChild(closeBtn);
  container.appendChild(toast);

  // Trigger fade-in on next frame
  requestAnimationFrame(() => toast.classList.add("toast--visible"));

  if (duration > 0) {
    setTimeout(() => dismiss(toast), duration);
  }
}

/**
 * Convenience wrapper: display an error toast (red, 5 s auto-dismiss).
 *
 * @param {string} message
 * @param {number} [duration=5000]
 */
export function showError(message, duration = 5000) {
  showToast(message, "error", duration);
}

function dismiss(toast) {
  toast.classList.remove("toast--visible");
  toast.addEventListener("transitionend", () => toast.remove(), { once: true });
  // Fallback: remove after 400 ms in case transitionend doesn't fire
  setTimeout(() => toast.remove(), 400);
}
