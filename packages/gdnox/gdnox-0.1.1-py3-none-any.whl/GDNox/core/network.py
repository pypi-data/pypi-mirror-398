"""
Network - Request/Response interception and monitoring.

Provides decorators for:
- Monitoring requests and responses
- Intercepting and modifying requests
- Blocking requests
- Returning fake responses
"""

import asyncio
import base64
import fnmatch
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union

from GDNox.core.cdp_client import CDPClient

logger = logging.getLogger(__name__)


@dataclass
class Request:
    """Represents an intercepted request."""
    
    request_id: str
    url: str
    method: str
    headers: Dict[str, str]
    post_data: Optional[str] = None
    resource_type: str = "Other"
    
    # Internal reference for interception
    _cdp: Optional[CDPClient] = field(default=None, repr=False)
    _intercepted: bool = field(default=False, repr=False)
    
    async def continue_(
        self,
        url: Optional[str] = None,
        method: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        post_data: Optional[str] = None,
    ) -> None:
        """Continue the request, optionally modifying it."""
        if not self._cdp or not self._intercepted:
            return
        
        params = {"requestId": self.request_id}
        
        if url:
            params["url"] = url
        if method:
            params["method"] = method
        if headers:
            params["headers"] = [{"name": k, "value": v} for k, v in headers.items()]
        if post_data:
            params["postData"] = base64.b64encode(post_data.encode()).decode()
        
        await self._cdp.send("Fetch.continueRequest", params)
    
    async def abort(self, reason: str = "Failed") -> None:
        """Abort the request."""
        if not self._cdp or not self._intercepted:
            return
        
        await self._cdp.send("Fetch.failRequest", {
            "requestId": self.request_id,
            "errorReason": reason,
        })
    
    async def respond(
        self,
        status: int = 200,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[str] = None,
        json_data: Optional[Any] = None,
    ) -> None:
        """Fulfill request with a custom response."""
        if not self._cdp or not self._intercepted:
            return
        
        response_headers = headers or {}
        
        if json_data is not None:
            body = json.dumps(json_data)
            response_headers["Content-Type"] = "application/json"
        
        body_bytes = (body or "").encode()
        
        await self._cdp.send("Fetch.fulfillRequest", {
            "requestId": self.request_id,
            "responseCode": status,
            "responseHeaders": [{"name": k, "value": v} for k, v in response_headers.items()],
            "body": base64.b64encode(body_bytes).decode(),
        })


@dataclass
class Response:
    """Represents a network response."""
    
    request_id: str
    url: str
    status: int
    status_text: str
    headers: Dict[str, str]
    mime_type: str
    
    # Internal reference
    _cdp: Optional[CDPClient] = field(default=None, repr=False)
    _body: Optional[str] = field(default=None, repr=False)
    _body_fetched: bool = field(default=False, repr=False)
    
    async def body(self) -> str:
        """Get response body as string."""
        if self._body_fetched:
            return self._body or ""
        
        if not self._cdp:
            return ""
        
        try:
            result = await self._cdp.send("Network.getResponseBody", {
                "requestId": self.request_id,
            })
            
            body = result.get("body", "")
            if result.get("base64Encoded"):
                body = base64.b64decode(body).decode("utf-8", errors="replace")
            
            self._body = body
            self._body_fetched = True
            return body
        except Exception as e:
            logger.debug(f"Failed to get response body: {e}")
            return ""
    
    async def json(self) -> Any:
        """Get response body as JSON."""
        body = await self.body()
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return None


class Network:
    """
    Network monitoring and interception.
    
    Usage:
        network = tab.network
        
        @network.on('request')
        async def on_request(request):
            print(f"Request: {request.url}")
        
        @network.on('response')
        async def on_response(response):
            body = await response.body()
            print(f"Response: {response.url} - {len(body)} bytes")
        
        @network.intercept('*api.example.com*')
        async def intercept_api(request):
            if '/blocked' in request.url:
                await request.abort()
            else:
                await request.continue_()
    """
    
    def __init__(self, cdp: CDPClient):
        self._cdp = cdp
        self._enabled = False
        self._fetch_enabled = False
        
        # Event handlers
        self._request_handlers: List[Callable] = []
        self._response_handlers: List[Callable] = []
        self._loading_finished_handlers: List[Callable] = []
        self._loading_failed_handlers: List[Callable] = []
        
        # Interception handlers (pattern -> handler)
        self._intercept_handlers: List[tuple] = []  # [(pattern, handler), ...]
        
        # Track requests for response body retrieval
        self._requests: Dict[str, Request] = {}
    
    async def enable(self) -> None:
        """Enable network monitoring."""
        if self._enabled:
            return
        
        await self._cdp.send("Network.enable")
        
        # Register CDP event handlers
        self._cdp.on("Network.requestWillBeSent", self._on_request)
        self._cdp.on("Network.responseReceived", self._on_response)
        self._cdp.on("Network.loadingFinished", self._on_loading_finished)
        self._cdp.on("Network.loadingFailed", self._on_loading_failed)
        
        self._enabled = True
        logger.debug("Network monitoring enabled")
    
    async def _enable_fetch(self, patterns: List[str]) -> None:
        """Enable fetch interception for patterns."""
        if not patterns:
            return
        
        # Convert glob patterns to CDP patterns
        cdp_patterns = []
        for pattern in patterns:
            cdp_patterns.append({
                "urlPattern": pattern,
                "requestStage": "Request",
            })
        
        await self._cdp.send("Fetch.enable", {"patterns": cdp_patterns})
        self._cdp.on("Fetch.requestPaused", self._on_fetch_paused)
        self._fetch_enabled = True
        logger.debug(f"Fetch interception enabled for {len(patterns)} patterns")
    
    def on(self, event: str) -> Callable:
        """
        Decorator to register event handler.
        
        Events:
        - 'request': Called when a request is sent
        - 'response': Called when a response is received
        - 'finished': Called when loading finishes
        - 'failed': Called when loading fails
        """
        def decorator(handler: Callable) -> Callable:
            if event == "request":
                self._request_handlers.append(handler)
            elif event == "response":
                self._response_handlers.append(handler)
            elif event == "finished":
                self._loading_finished_handlers.append(handler)
            elif event == "failed":
                self._loading_failed_handlers.append(handler)
            else:
                raise ValueError(f"Unknown event: {event}")
            
            # Auto-enable network on first handler
            asyncio.create_task(self.enable())
            
            return handler
        return decorator
    
    def intercept(self, pattern: str = "*") -> Callable:
        """
        Decorator to intercept requests matching a pattern.
        
        Pattern uses glob syntax: * matches anything, ? matches single char.
        
        The handler receives a Request object and MUST call one of:
        - request.continue_() - continue normally
        - request.abort() - abort the request
        - request.respond(...) - return a custom response
        """
        def decorator(handler: Callable) -> Callable:
            self._intercept_handlers.append((pattern, handler))
            
            # Collect all patterns and enable fetch
            all_patterns = list(set(p for p, _ in self._intercept_handlers))
            asyncio.create_task(self._enable_fetch(all_patterns))
            
            return handler
        return decorator
    
    async def _on_request(self, params: Dict) -> None:
        """Handle Network.requestWillBeSent event."""
        request_data = params.get("request", {})
        
        request = Request(
            request_id=params.get("requestId", ""),
            url=request_data.get("url", ""),
            method=request_data.get("method", "GET"),
            headers=request_data.get("headers", {}),
            post_data=request_data.get("postData"),
            resource_type=params.get("type", "Other"),
            _cdp=self._cdp,
            _intercepted=False,
        )
        
        self._requests[request.request_id] = request
        
        for handler in self._request_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(request)
                else:
                    handler(request)
            except Exception as e:
                logger.error(f"Request handler error: {e}")
    
    async def _on_response(self, params: Dict) -> None:
        """Handle Network.responseReceived event."""
        response_data = params.get("response", {})
        
        response = Response(
            request_id=params.get("requestId", ""),
            url=response_data.get("url", ""),
            status=response_data.get("status", 0),
            status_text=response_data.get("statusText", ""),
            headers=response_data.get("headers", {}),
            mime_type=response_data.get("mimeType", ""),
            _cdp=self._cdp,
        )
        
        for handler in self._response_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(response)
                else:
                    handler(response)
            except Exception as e:
                logger.error(f"Response handler error: {e}")
    
    async def _on_loading_finished(self, params: Dict) -> None:
        """Handle Network.loadingFinished event."""
        request_id = params.get("requestId", "")
        
        for handler in self._loading_finished_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(request_id)
                else:
                    handler(request_id)
            except Exception as e:
                logger.error(f"Loading finished handler error: {e}")
    
    async def _on_loading_failed(self, params: Dict) -> None:
        """Handle Network.loadingFailed event."""
        request_id = params.get("requestId", "")
        error = params.get("errorText", "")
        
        for handler in self._loading_failed_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(request_id, error)
                else:
                    handler(request_id, error)
            except Exception as e:
                logger.error(f"Loading failed handler error: {e}")
    
    async def _on_fetch_paused(self, params: Dict) -> None:
        """Handle Fetch.requestPaused event."""
        request_data = params.get("request", {})
        
        request = Request(
            request_id=params.get("requestId", ""),
            url=request_data.get("url", ""),
            method=request_data.get("method", "GET"),
            headers=request_data.get("headers", {}),
            post_data=request_data.get("postData"),
            resource_type=params.get("resourceType", "Other"),
            _cdp=self._cdp,
            _intercepted=True,
        )
        
        # Find matching handler
        handled = False
        for pattern, handler in self._intercept_handlers:
            if fnmatch.fnmatch(request.url, pattern):
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(request)
                    else:
                        handler(request)
                    handled = True
                    break
                except Exception as e:
                    logger.error(f"Intercept handler error: {e}")
                    # Continue request on error
                    await request.continue_()
                    handled = True
                    break
        
        # If no handler matched, continue normally
        if not handled:
            await request.continue_()
    
    async def block(self, patterns: List[str]) -> None:
        """
        Block requests matching any of the patterns.
        
        Args:
            patterns: List of URL patterns to block (glob syntax)
        """
        for pattern in patterns:
            @self.intercept(pattern)
            async def block_handler(request):
                await request.abort("BlockedByClient")
