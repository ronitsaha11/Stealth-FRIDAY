"""
browser_bridge.py — Local FastAPI Bridge for Raptor Browser Intelligence
=========================================================================
Runs a lightweight HTTP + WebSocket server on port 7890.
  - Receives page data from the Chrome extension (via WebSocket)
  - Stores latest page snapshot in memory
  - Exposes REST endpoints for Raptor tools to query / send actions
  - Sends action commands to the extension via WebSocket

Lifecycle: started as a daemon thread from agent.py (same pattern as ws_bridge.py).
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
import time
import uuid
import subprocess
from typing import Any

logger = logging.getLogger("RaptorBrowserBridge")

# ── Safety: Restricted Domains ──────────────────────────────────────────────
RESTRICTED_DOMAINS = [
    "accounts.google.com",
    "myaccount.google.com",
    "chase.com",
    "wellsfargo.com",
    "bankofamerica.com",
    "citibank.com",
    "paypal.com",
    "venmo.com",
    "1password.com",
    "lastpass.com",
    "bitwarden.com",
    "dashlane.com",
    "login.microsoftonline.com",
    "appleid.apple.com",
]


def _is_restricted(domain: str) -> bool:
    """Check if a domain falls under the restricted list."""
    if not domain:
        return False
    domain_lower = domain.lower()
    for restricted in RESTRICTED_DOMAINS:
        if domain_lower == restricted or domain_lower.endswith("." + restricted):
            return True
    return False


class BrowserBridge:
    """
    In-process bridge between Raptor and the Chrome extension.
    Uses aiohttp for zero extra dependencies (fastapi/uvicorn not required).
    """

    def __init__(self, host: str = "localhost", port: int = 7890):
        self.host = host
        self.port = port
        self.loop: asyncio.AbstractEventLoop | None = None
        self.thread: threading.Thread | None = None

        # Latest page data from the extension
        self._page_data: dict[str, Any] = {}
        self._page_data_time: float = 0

        # Connected WebSocket clients (extension background.js instances)
        self._ws_clients: set = set()

        # Pending action requests: {request_id: asyncio.Future}
        self._pending_actions: dict[str, asyncio.Future] = {}

    # ── Public API (called from Raptor tools, synchronous) ──────────

    def get_latest_page_data(self) -> dict | None:
        """Return the latest page data snapshot, or None if stale / empty."""
        if not self._page_data:
            return None
        # Consider data stale after 60 seconds
        if time.time() - self._page_data_time > 60:
            return None
        return dict(self._page_data)

    def request_fresh_page_data(self, timeout: float = 5.0) -> dict | None:
        """Send a get_page_data command to the extension and wait for response."""
        return self._send_action_sync("get_page_data", {}, timeout)

    def send_click(self, selector: str, timeout: float = 5.0) -> dict:
        """Send a click command to the extension."""
        page = self._page_data
        if page and _is_restricted(page.get("domain", "")):
            return {"status": "blocked", "message": "Action blocked: restricted domain."}
        return self._send_action_sync("click_element", {"selector": selector}, timeout)

    def send_click_by_text(self, text: str, timeout: float = 5.0) -> dict:
        """Send a fuzzy click-by-text command to the extension."""
        page = self._page_data
        if page and _is_restricted(page.get("domain", "")):
            return {"status": "blocked", "message": "Action blocked: restricted domain."}
        return self._send_action_sync("click_by_text", {"text": text}, timeout)

    def send_type(self, selector: str, text: str, timeout: float = 5.0) -> dict:
        """Send a type command to the extension."""
        page = self._page_data
        if page and _is_restricted(page.get("domain", "")):
            return {"status": "blocked", "message": "Action blocked: restricted domain."}
        return self._send_action_sync("type_input", {"selector": selector, "text": text}, timeout)

    def send_type_by_hint(self, field: str, text: str, timeout: float = 5.0) -> dict:
        """Send a fuzzy type-by-field-hint command to the extension."""
        page = self._page_data
        if page and _is_restricted(page.get("domain", "")):
            return {"status": "blocked", "message": "Action blocked: restricted domain."}
        return self._send_action_sync("type_by_hint", {"field": field, "text": text}, timeout)

    # ── Sync wrapper for async action dispatch ──────────────────────

    def _send_action_sync(self, action: str, payload: dict, timeout: float) -> dict:
        """Thread-safe sync wrapper to dispatch an action via the event loop."""
        if not self.loop or not self.loop.is_running():
            return {"status": "error", "message": "Browser bridge is not running."}

        if not self._ws_clients:
            return {"status": "error", "message": "No browser extension connected."}

        future = asyncio.run_coroutine_threadsafe(
            self._dispatch_action(action, payload, timeout), self.loop
        )
        try:
            return future.result(timeout=timeout + 1)
        except Exception as e:
            return {"status": "error", "message": f"Bridge timeout: {e}"}

    async def _dispatch_action(self, action: str, payload: dict, timeout: float) -> dict:
        """Send an action command to the extension and await the response."""
        request_id = str(uuid.uuid4())[:8]

        msg = json.dumps({"id": request_id, "action": action, "payload": payload})

        # Create a future for the response
        response_future: asyncio.Future = self.loop.create_future()
        self._pending_actions[request_id] = response_future

        # Broadcast to all connected extension instances
        disconnected = set()
        for ws_client in self._ws_clients:
            try:
                await ws_client.send_str(msg)
            except Exception:
                disconnected.add(ws_client)

        self._ws_clients -= disconnected

        # Wait for the content script response
        try:
            result = await asyncio.wait_for(response_future, timeout=timeout)
            return result
        except asyncio.TimeoutError:
            return {"status": "error", "message": "Extension did not respond in time."}
        finally:
            self._pending_actions.pop(request_id, None)

    # ── aiohttp Server ──────────────────────────────────────────────

    async def _start_server(self):
        """Start the aiohttp web server."""
        try:
            from aiohttp import web
        except ImportError:
            logger.error("[BROWSER BRIDGE] aiohttp not installed. Run: pip install aiohttp")
            return

        app = web.Application()
        app.router.add_get("/tab", self._handle_get_tab)
        app.router.add_post("/tab", self._handle_post_tab)
        app.router.add_post("/action", self._handle_post_action)
        app.router.add_get("/ws", self._handle_websocket)
        app.router.add_get("/health", self._handle_health)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        logger.info(f"[BROWSER BRIDGE] Server started on http://{self.host}:{self.port}")

        # Keep running forever
        await asyncio.Future()

    async def _handle_health(self, request):
        """Health check endpoint."""
        from aiohttp import web
        return web.json_response({
            "status": "ok",
            "clients": len(self._ws_clients),
            "has_page_data": bool(self._page_data),
        })

    async def _handle_get_tab(self, request):
        """GET /tab — return latest stored page data."""
        from aiohttp import web

        data = self.get_latest_page_data()
        if not data:
            return web.json_response(
                {"status": "no_data", "message": "No page data available."},
                status=204,
            )
        return web.json_response({"status": "ok", "data": data})

    async def _handle_post_tab(self, request):
        """POST /tab — receive page data from extension (HTTP fallback)."""
        from aiohttp import web

        try:
            body = await request.json()
        except Exception:
            return web.json_response(
                {"status": "error", "message": "Invalid JSON."}, status=400
            )

        domain = body.get("domain", "")
        if _is_restricted(domain):
            logger.info(f"[BROWSER BRIDGE] Dropping data from restricted domain: {domain}")
            return web.json_response({"status": "blocked"})

        self._page_data = body
        self._page_data_time = time.time()
        return web.json_response({"status": "ok"})

    async def _handle_post_action(self, request):
        """POST /action — send an action to the extension."""
        from aiohttp import web

        try:
            body = await request.json()
        except Exception:
            return web.json_response(
                {"status": "error", "message": "Invalid JSON."}, status=400
            )

        action_type = body.get("type")
        if not action_type:
            return web.json_response(
                {"status": "error", "message": "Missing 'type' field."}, status=400
            )

        # Map simplified action types to content script actions
        action_map = {
            "click": "click_element",
            "click_text": "click_by_text",
            "type": "type_input",
            "type_hint": "type_by_hint",
            "get_page": "get_page_data",
        }

        cs_action = action_map.get(action_type, action_type)
        payload = {k: v for k, v in body.items() if k != "type"}

        result = await self._dispatch_action(cs_action, payload, timeout=5.0)
        return web.json_response(result)

    async def _handle_websocket(self, request):
        """WebSocket endpoint /ws — bidirectional comms with extension."""
        from aiohttp import web, WSMsgType

        ws = web.WebSocketResponse()
        await ws.prepare(request)

        self._ws_clients.add(ws)
        logger.info(f"[BROWSER BRIDGE] Extension connected. Total: {len(self._ws_clients)}")

        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                    except json.JSONDecodeError:
                        continue

                    # Route based on message type
                    msg_type = data.get("type")
                    msg_id = data.get("id")

                    if msg_type == "page_data":
                        # Auto-report from content script
                        page = data.get("data", {})
                        domain = page.get("domain", "")
                        if not _is_restricted(domain):
                            self._page_data = page
                            self._page_data_time = time.time()

                    elif msg_id and msg_id in self._pending_actions:
                        # Response to a pending action request
                        future = self._pending_actions.get(msg_id)
                        if future and not future.done():
                            future.set_result(data.get("data", data))

                elif msg.type in (WSMsgType.ERROR, WSMsgType.CLOSE):
                    break
        finally:
            self._ws_clients.discard(ws)
            logger.info(f"[BROWSER BRIDGE] Extension disconnected. Total: {len(self._ws_clients)}")

        return ws

    # ── Thread Lifecycle ────────────────────────────────────────────

    def _run_thread(self):
        """Background thread entry point."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self._start_server())
        except Exception as e:
            logger.error(f"[BROWSER BRIDGE] Server error: {e}")
        finally:
            self.loop.close()

    def start(self):
        """Start the bridge server in a daemon thread."""
        if self.thread and self.thread.is_alive():
            logger.warning("[BROWSER BRIDGE] Already running.")
            return

        def free_port(port: int):
            """Kill any process listening on the given port."""
            try:
                result = subprocess.run(["lsof", "-t", "-i", f":{port}"], capture_output=True, text=True)
                pids = result.stdout.strip().split()
                for pid in pids:
                    if pid:
                        logger.info(f"[DEBUG] Port {port} is in use by PID {pid}. Killing it.")
                        subprocess.run(["kill", "-9", pid])
                        time.sleep(0.5)
            except Exception as e:
                logger.error(f"[DEBUG] Failed to free port {port}: {e}")

        free_port(self.port)

        self.thread = threading.Thread(
            target=self._run_thread, daemon=True, name="BrowserBridgeThread"
        )
        self.thread.start()
        logger.info("[BROWSER BRIDGE] Daemon thread started.")

    def stop(self):
        """Stop the bridge server."""
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)


# Global singleton instance
browser_bridge = BrowserBridge()
