/**
 * Raptor Browser Intelligence — Content Script
 * ==============================================
 * Injected into every page. Provides:
 *   - get_page_data()   → scrape title, URL, visible text, buttons, inputs
 *   - click_element()   → click a DOM element by CSS selector
 *   - type_input()      → focus an input and type text
 *
 * Communicates with background.js via chrome.runtime messaging.
 */

(() => {
  "use strict";

  // ── Helpers ──────────────────────────────────────────────────────────

  /**
   * Build a unique CSS selector for a given element.
   * Prefers id > [data-*] > nth-child path.
   */
  function getSelector(el) {
    if (el.id) return `#${CSS.escape(el.id)}`;

    // data-testid or name attribute
    if (el.dataset && el.dataset.testid) {
      return `[data-testid="${CSS.escape(el.dataset.testid)}"]`;
    }
    if (el.name) {
      const tag = el.tagName.toLowerCase();
      return `${tag}[name="${CSS.escape(el.name)}"]`;
    }

    // Build nth-child path (up to 5 levels)
    const parts = [];
    let current = el;
    for (let i = 0; i < 5 && current && current !== document.body; i++) {
      const parent = current.parentElement;
      if (!parent) break;
      const siblings = Array.from(parent.children).filter(
        (c) => c.tagName === current.tagName
      );
      const index = siblings.indexOf(current) + 1;
      const tag = current.tagName.toLowerCase();
      parts.unshift(
        siblings.length > 1 ? `${tag}:nth-of-type(${index})` : tag
      );
      current = parent;
    }
    return parts.length ? parts.join(" > ") : el.tagName.toLowerCase();
  }

  /**
   * Get visible text from the page body, truncated.
   */
  function getVisibleText(maxLen = 5000) {
    const walker = document.createTreeWalker(
      document.body,
      NodeFilter.SHOW_TEXT,
      {
        acceptNode(node) {
          const parent = node.parentElement;
          if (!parent) return NodeFilter.FILTER_REJECT;
          const tag = parent.tagName;
          if (["SCRIPT", "STYLE", "NOSCRIPT", "SVG"].includes(tag))
            return NodeFilter.FILTER_REJECT;
          if (parent.offsetParent === null && parent !== document.body)
            return NodeFilter.FILTER_REJECT;
          const text = node.textContent.trim();
          return text.length > 0
            ? NodeFilter.FILTER_ACCEPT
            : NodeFilter.FILTER_REJECT;
        },
      }
    );

    const chunks = [];
    let totalLen = 0;
    while (walker.nextNode()) {
      const text = walker.currentNode.textContent.trim();
      if (totalLen + text.length > maxLen) {
        chunks.push(text.substring(0, maxLen - totalLen));
        break;
      }
      chunks.push(text);
      totalLen += text.length;
    }
    return chunks.join(" ");
  }

  // ── Core Functions ──────────────────────────────────────────────────

  /**
   * Scrape structured page data.
   */
  function getPageData() {
    // Buttons: <button>, <a>, [role="button"], input[type="submit"]
    const buttonEls = document.querySelectorAll(
      'button, a, [role="button"], input[type="submit"], input[type="button"]'
    );
    const buttons = [];
    const seenSelectors = new Set();
    buttonEls.forEach((el) => {
      const text = (
        el.textContent ||
        el.value ||
        el.getAttribute("aria-label") ||
        ""
      ).trim();
      if (!text || text.length > 100) return;
      const selector = getSelector(el);
      if (seenSelectors.has(selector)) return;
      seenSelectors.add(selector);
      buttons.push({ text, selector });
    });

    // Inputs: <input>, <textarea>, <select>
    const inputEls = document.querySelectorAll("input, textarea, select");
    const inputs = [];
    inputEls.forEach((el) => {
      const type = el.type || "text";
      if (["hidden", "submit", "button", "image"].includes(type)) return;
      const name =
        el.name ||
        el.placeholder ||
        el.getAttribute("aria-label") ||
        el.id ||
        "";
      const selector = getSelector(el);
      inputs.push({ name, type, selector, value: el.value || "" });
    });

    return {
      title: document.title,
      url: window.location.href,
      domain: window.location.hostname,
      visible_text: getVisibleText(),
      buttons: buttons.slice(0, 50), // cap to prevent huge payloads
      inputs: inputs.slice(0, 30),
      timestamp: Date.now(),
    };
  }

  /**
   * Click a DOM element by CSS selector.
   */
  function clickElement(selector) {
    const el = document.querySelector(selector);
    if (!el) {
      return { status: "error", message: `Element not found: ${selector}` };
    }
    el.scrollIntoView({ behavior: "smooth", block: "center" });
    // Brief delay to allow scroll, then click
    setTimeout(() => {
      el.click();
    }, 200);
    return { status: "success", message: `Clicked: ${selector}` };
  }

  /**
   * Focus an input element and type text into it.
   */
  function typeInput(selector, text) {
    const el = document.querySelector(selector);
    if (!el) {
      return { status: "error", message: `Input not found: ${selector}` };
    }
    el.scrollIntoView({ behavior: "smooth", block: "center" });
    el.focus();

    // Clear existing value
    el.value = "";
    // Dispatch input events so frameworks (React, Vue) pick up the change
    el.dispatchEvent(new Event("focus", { bubbles: true }));

    // Type character by character for realism
    for (const char of text) {
      el.value += char;
      el.dispatchEvent(new Event("input", { bubbles: true }));
    }
    el.dispatchEvent(new Event("change", { bubbles: true }));

    return {
      status: "success",
      message: `Typed "${text}" into ${selector}`,
    };
  }

  /**
   * Find a clickable element by visible text (fuzzy match).
   */
  function findAndClick(buttonText) {
    const lower = buttonText.toLowerCase().trim();

    // Search buttons, links, and role=button elements
    const candidates = document.querySelectorAll(
      'button, a, [role="button"], input[type="submit"], input[type="button"]'
    );

    let bestMatch = null;
    let bestScore = 0;

    candidates.forEach((el) => {
      const elText = (
        el.textContent ||
        el.value ||
        el.getAttribute("aria-label") ||
        ""
      )
        .trim()
        .toLowerCase();
      if (!elText) return;

      // Exact match
      if (elText === lower) {
        bestMatch = el;
        bestScore = 100;
        return;
      }
      // Contains match
      if (elText.includes(lower) && lower.length >= 3) {
        const score = (lower.length / elText.length) * 80;
        if (score > bestScore) {
          bestMatch = el;
          bestScore = score;
        }
      }
    });

    if (bestMatch && bestScore >= 30) {
      bestMatch.scrollIntoView({ behavior: "smooth", block: "center" });
      setTimeout(() => bestMatch.click(), 200);
      return {
        status: "success",
        message: `Clicked button matching "${buttonText}"`,
      };
    }

    return {
      status: "error",
      message: `No button found matching "${buttonText}"`,
    };
  }

  /**
   * Find an input by name/placeholder and type into it (fuzzy match).
   */
  function findAndType(fieldHint, text) {
    const lower = fieldHint.toLowerCase().trim();
    const candidates = document.querySelectorAll("input, textarea, select");

    let bestMatch = null;
    let bestScore = 0;

    candidates.forEach((el) => {
      const type = el.type || "text";
      if (["hidden", "submit", "button", "image"].includes(type)) return;

      const label = (
        el.name +
        " " +
        (el.placeholder || "") +
        " " +
        (el.getAttribute("aria-label") || "") +
        " " +
        (el.id || "")
      ).toLowerCase();

      if (label.includes(lower)) {
        const score = lower.length / Math.max(label.length, 1);
        if (score > bestScore) {
          bestMatch = el;
          bestScore = score;
        }
      }
    });

    if (bestMatch) {
      return typeInput(getSelector(bestMatch), text);
    }

    return {
      status: "error",
      message: `No input field found matching "${fieldHint}"`,
    };
  }

  // ── Message Handler ─────────────────────────────────────────────────

  chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    const { action, payload } = message;

    switch (action) {
      case "get_page_data":
        sendResponse(getPageData());
        break;

      case "click_element":
        sendResponse(clickElement(payload.selector));
        break;

      case "click_by_text":
        sendResponse(findAndClick(payload.text));
        break;

      case "type_input":
        sendResponse(typeInput(payload.selector, payload.text));
        break;

      case "type_by_hint":
        sendResponse(findAndType(payload.field, payload.text));
        break;

      default:
        sendResponse({ status: "error", message: `Unknown action: ${action}` });
    }

    // Return true to keep the message channel open for async responses
    return true;
  });

  // ── Auto-report page data on load ───────────────────────────────────
  // Send initial page snapshot to background after a brief settle delay
  setTimeout(() => {
    try {
      chrome.runtime.sendMessage({
        type: "page_data_report",
        data: getPageData(),
      });
    } catch {
      // Extension context may be invalidated — ignore
    }
  }, 1500);

  console.log("[Raptor] Content script loaded.");
})();
