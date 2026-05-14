/**
 * Raptor Browser Intelligence — Background Service Worker
 * =========================================================
 * Manifest V3 service worker. Responsibilities:
 *   1. Maintain a WebSocket connection to the local FastAPI bridge (ws://localhost:7890/ws)
 *   2. Relay commands FROM bridge → content script
 *   3. Forward page data FROM content script → bridge
 *   4. Auto-reconnect with exponential backoff
 */

(() => {
  "use strict";

  const BRIDGE_WS_URL = "ws://localhost:7890/ws";
  const RECONNECT_BASE_MS = 1000;
  const RECONNECT_MAX_MS = 30000;

  let ws = null;
  let reconnectAttempts = 0;
  let reconnectTimer = null;

  // ── WebSocket Connection ──────────────────────────────────────────

  function connectWebSocket() {
    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    console.log("[Raptor BG] Connecting to bridge:", BRIDGE_WS_URL);
    ws = new WebSocket(BRIDGE_WS_URL);

    ws.onopen = () => {
      console.log("[Raptor BG] Connected to bridge.");
      reconnectAttempts = 0;
    };

    ws.onmessage = (event) => {
      let msg;
      try {
        msg = JSON.parse(event.data);
      } catch (e) {
        console.error("[Raptor BG] Invalid JSON from bridge:", e);
        return;
      }

      handleBridgeCommand(msg);
    };

    ws.onerror = (err) => {
      console.error("[Raptor BG] WebSocket error:", err);
    };

    ws.onclose = () => {
      console.log("[Raptor BG] Disconnected from bridge. Will reconnect...");
      ws = null;
      scheduleReconnect();
    };
  }

  function scheduleReconnect() {
    if (reconnectTimer) clearTimeout(reconnectTimer);
    const delay = Math.min(
      RECONNECT_BASE_MS * Math.pow(2, reconnectAttempts),
      RECONNECT_MAX_MS
    );
    reconnectAttempts++;
    console.log(`[Raptor BG] Reconnecting in ${delay}ms (attempt ${reconnectAttempts})`);
    reconnectTimer = setTimeout(connectWebSocket, delay);
  }

  function sendToBridge(data) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(data));
    } else {
      console.warn("[Raptor BG] Bridge not connected. Dropping message.");
    }
  }

  // ── Command Handler (Bridge → Content Script) ─────────────────────

  async function handleBridgeCommand(msg) {
    const { id, action, payload } = msg;

    if (!action) {
      console.warn("[Raptor BG] Received message without action:", msg);
      return;
    }

    // Get the active tab
    let tabs;
    try {
      tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    } catch (e) {
      sendToBridge({
        id,
        status: "error",
        message: "Could not query active tabs.",
      });
      return;
    }

    if (!tabs || tabs.length === 0) {
      sendToBridge({
        id,
        status: "error",
        message: "No active tab found.",
      });
      return;
    }

    const activeTab = tabs[0];

    // Skip chrome:// and edge:// internal pages
    if (
      !activeTab.url ||
      activeTab.url.startsWith("chrome://") ||
      activeTab.url.startsWith("edge://") ||
      activeTab.url.startsWith("chrome-extension://")
    ) {
      sendToBridge({
        id,
        status: "error",
        message: "Cannot access internal browser pages.",
      });
      return;
    }

    // Forward to content script
    try {
      const response = await chrome.tabs.sendMessage(activeTab.id, {
        action,
        payload: payload || {},
      });

      sendToBridge({
        id,
        status: response?.status || "success",
        data: response,
      });
    } catch (e) {
      console.error("[Raptor BG] Content script error:", e);

      // Try injecting the content script if it hasn't loaded
      if (e.message?.includes("Could not establish connection")) {
        try {
          await chrome.scripting.executeScript({
            target: { tabId: activeTab.id },
            files: ["content.js"],
          });
          // Retry the message after injection
          const retryResponse = await chrome.tabs.sendMessage(activeTab.id, {
            action,
            payload: payload || {},
          });
          sendToBridge({
            id,
            status: retryResponse?.status || "success",
            data: retryResponse,
          });
        } catch (retryErr) {
          sendToBridge({
            id,
            status: "error",
            message: `Content script injection failed: ${retryErr.message}`,
          });
        }
      } else {
        sendToBridge({
          id,
          status: "error",
          message: e.message || "Unknown error communicating with content script.",
        });
      }
    }
  }

  // ── Content Script → Bridge (page data auto-reports) ──────────────

  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === "page_data_report" && message.data) {
      sendToBridge({
        type: "page_data",
        data: message.data,
      });
      sendResponse({ status: "ok" });
    }
    return false;
  });

  // ── Tab Change Listener — request fresh page data on tab switch ───

  chrome.tabs.onActivated.addListener(async (activeInfo) => {
    try {
      const tab = await chrome.tabs.get(activeInfo.tabId);
      if (
        tab.url &&
        !tab.url.startsWith("chrome://") &&
        !tab.url.startsWith("chrome-extension://")
      ) {
        // Small delay to let content script settle
        setTimeout(async () => {
          try {
            const response = await chrome.tabs.sendMessage(activeInfo.tabId, {
              action: "get_page_data",
              payload: {},
            });
            sendToBridge({ type: "page_data", data: response });
          } catch {
            // Content script not yet loaded — ignore
          }
        }, 500);
      }
    } catch {
      // Tab might have been closed — ignore
    }
  });

  // ── Page navigation listener — refresh data on URL change ─────────

  chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === "complete" && tab.active) {
      setTimeout(async () => {
        try {
          const response = await chrome.tabs.sendMessage(tabId, {
            action: "get_page_data",
            payload: {},
          });
          sendToBridge({ type: "page_data", data: response });
        } catch {
          // Content script not ready — ignore
        }
      }, 1000);
    }
  });

  // ── Initialize ────────────────────────────────────────────────────

  connectWebSocket();
  console.log("[Raptor BG] Service worker initialized.");
})();
