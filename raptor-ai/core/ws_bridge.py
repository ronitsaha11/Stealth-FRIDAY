"""
WebSocket bridge for Raptor local AI agent.
Broadcasts agent state updates to the React frontend dashboard.
"""

import asyncio
import json
import logging
import threading
import websockets

logger = logging.getLogger("RaptorWS")

class RaptorWSBridge:
    def __init__(self, host="localhost", port=8765):
        self.host = host
        self.port = port
        self.clients = set()
        self.loop = None
        self.thread = None
        
        # Current state tracker
        self.current_state = {
            "type": "state_update",
            "state": "IDLE",
            "last_command": "",
            "last_response": "",
            "active_module": "none",
            "timestamp": 0
        }

    async def _handler(self, websocket):
        """Handle incoming WebSocket connections"""
        self.clients.add(websocket)
        logger.info(f"[WS] Client connected. Total: {len(self.clients)}")
        
        try:
            # Send initial state immediately upon connection
            await websocket.send(json.dumps(self.current_state))
            
            # Keep connection open and wait for client to disconnect
            async for message in websocket:
                # We don't really expect messages from the frontend yet, 
                # but if we get them we log them.
                logger.debug(f"[WS] Received from client: {message}")
                
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients.remove(websocket)
            logger.info(f"[WS] Client disconnected. Total: {len(self.clients)}")

    async def _server_main(self):
        """Main async entry point for the WebSocket server"""
        async with websockets.serve(self._handler, self.host, self.port):
            logger.info(f"[WS] Server started on ws://{self.host}:{self.port}")
            # Keep running forever
            await asyncio.Future()

    def _run_thread(self):
        """Function run by the background thread"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self._server_main())
        except Exception as e:
            logger.error(f"[WS] Server error: {e}")
        finally:
            self.loop.close()

    def start(self):
        """Start the WebSocket server in a daemon thread"""
        if self.thread and self.thread.is_alive():
            logger.warning("[WS] Server already running")
            return
            
        self.thread = threading.Thread(target=self._run_thread, daemon=True, name="WSBridgeThread")
        self.thread.start()
        
    def stop(self):
        """Stop the WebSocket server"""
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
            
    def update_state(self, new_state_dict: dict):
        """
        Update current state and broadcast to all connected clients.
        Expected keys: state, last_command, last_response, active_module
        """
        import time
        
        # Update our internal state tracker
        for k, v in new_state_dict.items():
            self.current_state[k] = v
        self.current_state["timestamp"] = time.time()
        
        message = json.dumps(self.current_state)
        
        # Broadcast to all clients on the async event loop
        if self.loop and self.loop.is_running() and self.clients:
            async def broadcast():
                websockets.broadcast(self.clients, message)
            
            asyncio.run_coroutine_threadsafe(broadcast(), self.loop)

# Global singleton instance
bridge = RaptorWSBridge()
