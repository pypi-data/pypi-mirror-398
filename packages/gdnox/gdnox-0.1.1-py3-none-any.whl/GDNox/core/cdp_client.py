"""
CDP Client - Chrome DevTools Protocol WebSocket Client

Self-contained implementation for communicating with Chrome via CDP.
No external dependencies except websockets.
"""

import asyncio
import json
import logging
from typing import Any, Callable, Dict, Optional
import websockets
from websockets.client import WebSocketClientProtocol

logger = logging.getLogger(__name__)


class CDPError(Exception):
    """CDP command error."""
    def __init__(self, code: int, message: str, data: Any = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(f"CDP Error {code}: {message}")


class CDPClient:
    """
    Chrome DevTools Protocol WebSocket client.
    
    Handles:
    - WebSocket connection to Chrome
    - Sending CDP commands
    - Receiving responses and events
    - Event subscriptions
    """
    
    def __init__(self, ws_url: str):
        """
        Initialize CDP client.
        
        Args:
            ws_url: WebSocket URL for CDP connection
                    (e.g., ws://127.0.0.1:9222/devtools/page/...)
        """
        self.ws_url = ws_url
        self._ws: Optional[WebSocketClientProtocol] = None
        self._message_id = 0
        self._pending_commands: Dict[int, asyncio.Future] = {}
        self._event_handlers: Dict[str, list[Callable]] = {}
        self._receive_task: Optional[asyncio.Task] = None
        self._connected = False
    
    async def connect(self) -> None:
        """Connect to Chrome CDP WebSocket."""
        if self._connected:
            return
        
        logger.debug(f"Connecting to CDP: {self.ws_url}")
        self._ws = await websockets.connect(
            self.ws_url,
            max_size=None,  # No limit on message size
            close_timeout=5,
        )
        self._connected = True
        
        # Start receiving messages in background
        self._receive_task = asyncio.create_task(self._receive_loop())
        logger.debug("CDP connection established")
    
    async def disconnect(self) -> None:
        """Disconnect from CDP WebSocket."""
        if not self._connected:
            return
        
        self._connected = False
        
        # Cancel receive task
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
        
        # Close WebSocket
        if self._ws:
            await self._ws.close()
            self._ws = None
        
        logger.debug("CDP connection closed")
    
    async def send(
        self,
        method: str,
        params: Optional[Dict] = None,
        session_id: Optional[str] = None,
    ) -> Any:
        """
        Send a CDP command and wait for response.
        
        Args:
            method: CDP method name (e.g., 'Page.navigate')
            params: Optional parameters dict
            session_id: Optional session ID for flattened sessions (OOP iframes)
            
        Returns:
            Response result
            
        Raises:
            CDPError: If CDP returns an error
        """
        if not self._connected:
            await self.connect()
        
        self._message_id += 1
        msg_id = self._message_id
        
        message = {
            "id": msg_id,
            "method": method,
        }
        if params:
            message["params"] = params
        if session_id:
            message["sessionId"] = session_id
        
        # Create future for response
        future: asyncio.Future = asyncio.get_event_loop().create_future()
        self._pending_commands[msg_id] = future
        
        # Send message
        logger.debug(f"CDP send: {method} (id={msg_id}, session={session_id})")
        await self._ws.send(json.dumps(message))
        
        # Wait for response
        try:
            result = await asyncio.wait_for(future, timeout=30.0)
            return result
        except asyncio.TimeoutError:
            del self._pending_commands[msg_id]
            raise CDPError(-1, f"Timeout waiting for response to {method}")
    
    def on(self, event: str, handler: Callable) -> None:
        """
        Subscribe to a CDP event.
        
        Args:
            event: Event name (e.g., 'Page.loadEventFired')
            handler: Async or sync callback function
        """
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)
    
    def off(self, event: str, handler: Callable) -> None:
        """Unsubscribe from a CDP event."""
        if event in self._event_handlers:
            try:
                self._event_handlers[event].remove(handler)
            except ValueError:
                pass
    
    async def _receive_loop(self) -> None:
        """Background task to receive and dispatch CDP messages."""
        try:
            async for message in self._ws:
                await self._handle_message(message)
        except websockets.ConnectionClosed:
            logger.debug("CDP WebSocket connection closed")
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Error in CDP receive loop: {e}")
    
    async def _handle_message(self, raw_message: str) -> None:
        """Handle incoming CDP message."""
        try:
            message = json.loads(raw_message)
        except json.JSONDecodeError:
            logger.error(f"Failed to decode CDP message: {raw_message[:100]}")
            return
        
        # Response to a command
        if "id" in message:
            msg_id = message["id"]
            if msg_id in self._pending_commands:
                future = self._pending_commands.pop(msg_id)
                
                if "error" in message:
                    error = message["error"]
                    future.set_exception(CDPError(
                        error.get("code", -1),
                        error.get("message", "Unknown error"),
                        error.get("data")
                    ))
                else:
                    future.set_result(message.get("result", {}))
        
        # CDP event
        elif "method" in message:
            event_name = message["method"]
            params = message.get("params", {})
            await self._dispatch_event(event_name, params)
    
    async def _dispatch_event(self, event: str, params: Dict) -> None:
        """Dispatch CDP event to registered handlers."""
        handlers = self._event_handlers.get(event, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(params)
                else:
                    handler(params)
            except Exception as e:
                logger.error(f"Error in event handler for {event}: {e}")
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
