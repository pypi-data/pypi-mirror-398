"""
Tab - Browser tab/page controller.

Handles:
- Page navigation
- Element finding (including closed shadow roots)
- JavaScript execution
- Screenshots
"""

import asyncio
import base64
import json
import logging
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from GDNox.core.cdp_client import CDPClient, CDPError

if TYPE_CHECKING:
    from GDNox.core.element import Element

logger = logging.getLogger(__name__)


class Tab:
    """
    Browser tab controller.
    
    Provides navigation, element finding, and JavaScript execution.
    """
    
    def __init__(
        self, 
        ws_url: str, 
        target_info: Dict[str, Any],
        proxy_auth: Optional[tuple] = None,
    ):
        """
        Initialize tab.
        
        Args:
            ws_url: WebSocket URL for CDP connection to this tab
            target_info: Target info from Chrome /json endpoint
            proxy_auth: Optional tuple of (username, password) for proxy auth
        """
        self.ws_url = ws_url
        self.target_info = target_info
        self.target_id = target_info.get("id", "")
        
        self._cdp = CDPClient(ws_url)
        self._frame_id: Optional[str] = None
        self._execution_context_id: Optional[int] = None
        
        # Track OOP iframe sessions (cross-origin iframes)
        self._oop_frame_sessions: Dict[str, str] = {}  # targetId -> sessionId
        
        # Network interception (lazy init)
        self._network: Optional["Network"] = None
        
        # Proxy authentication
        self._proxy_auth = proxy_auth
    
    async def connect(self) -> None:
        """Connect to the tab via CDP."""
        await self._cdp.connect()
        
        # Enable required CDP domains
        await self._cdp.send("Page.enable")
        await self._cdp.send("DOM.enable")
        await self._cdp.send("Network.enable")
        
        # Enable Fetch for proxy authentication if credentials provided
        if self._proxy_auth:
            await self._cdp.send("Fetch.enable", {
                "handleAuthRequests": True
            })
            
            proxy_auth = self._proxy_auth  # Capture for closure
            cdp = self._cdp  # Capture for closure
            
            # Handle proxy auth requests (sync wrapper to avoid blocking)
            def handle_auth_required(params):
                async def _do_auth():
                    auth_challenge = params.get("authChallenge", {})
                    try:
                        if auth_challenge.get("source") == "Proxy":
                            username, password = proxy_auth
                            await cdp.send("Fetch.continueWithAuth", {
                                "requestId": params["requestId"],
                                "authChallengeResponse": {
                                    "response": "ProvideCredentials",
                                    "username": username,
                                    "password": password,
                                }
                            })
                            logger.debug(f"Proxy auth provided for: {params['requestId']}")
                        else:
                            await cdp.send("Fetch.continueWithAuth", {
                                "requestId": params["requestId"],
                                "authChallengeResponse": {
                                    "response": "CancelAuth"
                                }
                            })
                    except Exception as e:
                        logger.debug(f"Auth handler error: {e}")
                asyncio.create_task(_do_auth())
            
            # Handle paused requests - continue them (sync wrapper)
            def handle_request_paused(params):
                async def _do_continue():
                    try:
                        await cdp.send("Fetch.continueRequest", {
                            "requestId": params["requestId"]
                        })
                    except Exception as e:
                        logger.debug(f"Continue request error: {e}")
                asyncio.create_task(_do_continue())
            
            self._cdp.on("Fetch.authRequired", handle_auth_required)
            self._cdp.on("Fetch.requestPaused", handle_request_paused)
            logger.debug("Proxy authentication handler registered")
        
        # CRITICAL: Auto-attach to OOP iframes (cross-origin)
        # Note: We use setAutoAttach without Target.enable since it works in page session
        try:
            await self._cdp.send("Target.setAutoAttach", {
                "autoAttach": True,
                "waitForDebuggerOnStart": True,
                "flatten": True,  # Allows using sessionId in commands
            })
            
            # Listen for new frame attachments
            self._cdp.on("Target.attachedToTarget", self._on_frame_attached)
        except CDPError as e:
            # Target.setAutoAttach might not be available, continue without it
            logger.debug(f"Target.setAutoAttach not available: {e}")
        
        # Note: We deliberately avoid Runtime.enable as it's detectable
        # Instead, we use Page.createIsolatedWorld for JS execution
        
        # Get frame tree
        frame_tree = await self._cdp.send("Page.getFrameTree")
        self._frame_id = frame_tree["frameTree"]["frame"]["id"]
        
        logger.debug(f"Tab connected: {self.target_id}")
    
    async def close(self) -> None:
        """Close the tab."""
        await self._cdp.disconnect()
    
    def _on_frame_attached(self, params: Dict[str, Any]) -> None:
        """
        Handle Target.attachedToTarget event.
        
        This is called when Chrome auto-attaches to an OOP iframe.
        We store the session ID so we can use it to search in the iframe.
        """
        target_info = params.get("targetInfo", {})
        session_id = params.get("sessionId")
        target_id = target_info.get("targetId")
        target_type = target_info.get("type")
        
        if target_type == "iframe" and session_id and target_id:
            self._oop_frame_sessions[target_id] = session_id
            logger.debug(f"OOP iframe attached: {target_id} -> session {session_id}")
            
            # Enable DOM in the iframe (async task, fire and forget)
            asyncio.create_task(self._init_oop_frame(session_id))
    
    async def _init_oop_frame(self, session_id: str) -> None:
        """Initialize an OOP iframe by enabling DOM and resuming execution."""
        try:
            # Enable DOM in the iframe session
            await self._cdp.send("DOM.enable", {}, session_id=session_id)
            
            # Resume the iframe (it was paused by waitForDebuggerOnStart)
            await self._cdp.send("Runtime.runIfWaitingForDebugger", {}, session_id=session_id)
        except CDPError as e:
            logger.debug(f"Failed to init OOP frame: {e}")
    
    async def goto(self, url: str, wait_until: str = "load", timeout: float = 30.0) -> None:
        """
        Navigate to a URL.
        
        Args:
            url: URL to navigate to
            wait_until: Wait condition:
                - 'load': Wait for load event (default)
                - 'domcontentloaded': Wait for DOMContentLoaded event
                - 'networkidle': Wait until no network connections for 500ms (max 2 connections)
                - 'networkidle0': Wait until no network connections for 500ms (0 connections)
            timeout: Maximum time to wait in seconds
        """
        # Set up load event listener
        load_event = asyncio.Event()
        
        if wait_until == "load":
            def on_load(params):
                load_event.set()
            self._cdp.on("Page.loadEventFired", on_load)
        elif wait_until == "domcontentloaded":
            def on_dom(params):
                load_event.set()
            self._cdp.on("Page.domContentEventFired", on_dom)
        elif wait_until in ("networkidle", "networkidle2"):
            # networkidle: wait until <= 2 connections for 500ms
            load_event.set()  # Don't wait for page event
        elif wait_until == "networkidle0":
            # networkidle0: wait until 0 connections for 500ms
            load_event.set()
        else:
            load_event.set()
        
        # Navigate
        result = await self._cdp.send("Page.navigate", {"url": url})
        
        if "errorText" in result:
            raise Exception(f"Navigation failed: {result['errorText']}")
        
        # Wait for initial load event
        try:
            await asyncio.wait_for(load_event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(f"Timeout waiting for page load: {url}")
        
        # For networkidle, wait for network to be quiet
        if wait_until in ("networkidle", "networkidle2", "networkidle0"):
            max_connections = 0 if wait_until == "networkidle0" else 2
            await self._wait_for_network_idle(max_connections, timeout)
        
        # Update frame ID
        self._frame_id = result.get("frameId", self._frame_id)
    
    async def _wait_for_network_idle(
        self, 
        max_connections: int = 2, 
        timeout: float = 30.0,
        idle_time: float = 0.5,
    ) -> None:
        """
        Wait until network is idle.
        
        Args:
            max_connections: Max concurrent connections to consider "idle"
            timeout: Maximum time to wait
            idle_time: Time with no activity to consider idle (500ms default)
        """
        active_requests = set()
        last_activity = asyncio.get_event_loop().time()
        idle_event = asyncio.Event()
        
        def on_request(params):
            nonlocal last_activity
            request_id = params.get("requestId", "")
            active_requests.add(request_id)
            last_activity = asyncio.get_event_loop().time()
        
        def on_response(params):
            nonlocal last_activity
            request_id = params.get("requestId", "")
            active_requests.discard(request_id)
            last_activity = asyncio.get_event_loop().time()
            
            if len(active_requests) <= max_connections:
                # Schedule idle check
                asyncio.create_task(check_idle())
        
        def on_failed(params):
            nonlocal last_activity
            request_id = params.get("requestId", "")
            active_requests.discard(request_id)
            last_activity = asyncio.get_event_loop().time()
            
            if len(active_requests) <= max_connections:
                asyncio.create_task(check_idle())
        
        async def check_idle():
            await asyncio.sleep(idle_time)
            current_time = asyncio.get_event_loop().time()
            if current_time - last_activity >= idle_time and len(active_requests) <= max_connections:
                idle_event.set()
        
        # Register handlers
        self._cdp.on("Network.requestWillBeSent", on_request)
        self._cdp.on("Network.loadingFinished", on_response)
        self._cdp.on("Network.loadingFailed", on_failed)
        
        # Start initial idle check
        asyncio.create_task(check_idle())
        
        try:
            await asyncio.wait_for(idle_event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.debug(f"Network idle timeout ({len(active_requests)} active requests)")
    
    async def wait_for_selector(
        self,
        selector: str,
        visible: bool = False,
        hidden: bool = False,
        timeout: float = 30.0,
    ) -> Optional["Element"]:
        """
        Wait for selector to appear in DOM.
        
        Args:
            selector: CSS selector
            visible: Wait for element to be visible (not just in DOM)
            hidden: Wait for element to be hidden or removed
            timeout: Maximum time to wait in seconds
            
        Returns:
            Element if found (None if waiting for hidden)
        """
        import time
        start_time = time.time()
        poll_interval = 0.1
        
        while time.time() - start_time < timeout:
            element = await self.find(selector)
            
            if hidden:
                # Wait for element to disappear or be hidden
                if element is None:
                    return None
                if visible:
                    is_visible = await element.is_visible()
                    if not is_visible:
                        return None
            else:
                # Wait for element to appear
                if element is not None:
                    if visible:
                        is_visible = await element.is_visible()
                        if is_visible:
                            return element
                    else:
                        return element
            
            await asyncio.sleep(poll_interval)
        
        if not hidden:
            raise TimeoutError(f"Timeout waiting for selector: {selector}")
        return None
    
    async def wait_for_function(
        self,
        expression: str,
        timeout: float = 30.0,
        poll_interval: float = 0.1,
    ) -> Any:
        """
        Wait for a JavaScript expression to return truthy value.
        
        Args:
            expression: JavaScript expression
            timeout: Maximum time to wait
            poll_interval: Time between checks
            
        Returns:
            The truthy result
        """
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            result = await self.evaluate(expression)
            if result:
                return result
            await asyncio.sleep(poll_interval)
        
        raise TimeoutError(f"Timeout waiting for function: {expression[:50]}...")
    
    async def race(
        self,
        selectors: Optional[List[str]] = None,
        js_functions: Optional[List[str]] = None,
        visible: bool = False,
        timeout: float = 30.0,
    ) -> tuple[str, Any]:
        """
        Race multiple conditions - return the first one that resolves.
        
        Similar to Promise.race() in JavaScript.
        
        Args:
            selectors: List of CSS selectors to race
            js_functions: List of JavaScript expressions to race
            visible: For CSS selectors, wait for element to be visible
            timeout: Maximum time to wait
            
        Returns:
            Tuple of (winning_condition, result)
            - For CSS selectors: result is Element
            - For JS expressions: result is the truthy value
            
        Example:
            # Race CSS selectors only
            condition, element = await tab.race(
                selectors=[".success-message", ".error-message"],
            )
            
            # Race JS functions only
            condition, result = await tab.race(
                js_functions=["window.done === true", "document.title === 'Error'"],
            )
            
            # Race mixed conditions
            condition, result = await tab.race(
                selectors=[".success", ".error"],
                js_functions=["window.loginComplete === true"],
            )
        """
        import time
        
        selectors = selectors or []
        js_functions = js_functions or []
        
        if not selectors and not js_functions:
            raise ValueError("At least one selector or js_function required")
        
        start_time = time.time()
        poll_interval = 0.1
        
        while time.time() - start_time < timeout:
            # Check all CSS selectors (serialized to avoid CDP concurrency issues)
            for selector in selectors:
                element = await self.find(selector)
                if element is not None:
                    if visible:
                        is_visible = await element.is_visible()
                        if is_visible:
                            return (selector, element)
                    else:
                        return (selector, element)
            
            # Check all JS expressions
            for js_func in js_functions:
                result = await self.evaluate(js_func)
                if result:
                    return (js_func, result)
            
            await asyncio.sleep(poll_interval)
        
        raise TimeoutError(f"Timeout waiting for conditions")
    
    async def content(self) -> str:
        """Get page HTML content."""
        result = await self._cdp.send("DOM.getDocument", {"depth": -1})
        root_id = result["root"]["nodeId"]
        
        result = await self._cdp.send("DOM.getOuterHTML", {"nodeId": root_id})
        return result.get("outerHTML", "")
    
    async def evaluate(self, expression: str) -> Any:
        """
        Execute JavaScript and return result.
        
        Uses isolated world to avoid detection.
        
        Args:
            expression: JavaScript expression to evaluate
            
        Returns:
            JavaScript return value
        """
        # Create isolated world if we don't have one
        if not self._execution_context_id:
            result = await self._cdp.send("Page.createIsolatedWorld", {
                "frameId": self._frame_id,
                "worldName": "gdnium_isolated",
            })
            self._execution_context_id = result["executionContextId"]
        
        # Evaluate in isolated world
        result = await self._cdp.send("Runtime.evaluate", {
            "expression": expression,
            "contextId": self._execution_context_id,
            "returnByValue": True,
            "awaitPromise": True,
        })
        
        if "exceptionDetails" in result:
            exc = result["exceptionDetails"]
            raise Exception(f"JavaScript error: {exc.get('text', 'Unknown error')}")
        
        return result.get("result", {}).get("value")
    
    async def find(
        self,
        selector: str,
        timeout: float = 5.0,
    ) -> Optional["Element"]:
        """
        Find element by CSS selector.
        
        This method searches:
        1. Normal DOM
        2. Inside closed shadow roots
        3. Inside iframe contents (including their shadow roots)
        
        You don't need to do anything special - just use find().
        
        Args:
            selector: CSS selector
            timeout: How long to wait for element
            
        Returns:
            Element or None if not found
        """
        from GDNox.core.element import Element
        
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            try:
                # Get full document with shadow roots pierced
                doc = await self._cdp.send("DOM.getDocument", {"depth": -1, "pierce": True})
                
                # Step 1: Search in main frame DOM + shadow roots
                element = await self._unified_query_selector(doc["root"], selector)
                if element:
                    return element
                
                # Step 2: Search inside iframe contents
                element = await self._search_in_iframes(selector)
                if element:
                    return element
                
            except CDPError as e:
                if "No node with given id" not in str(e):
                    raise
            
            await asyncio.sleep(0.1)
        
        return None
    
    async def _search_in_iframes(self, selector: str) -> Optional["Element"]:
        """
        Search for element inside all iframe contents, including cross-origin.
        
        For cross-origin iframes (out-of-process), we use Target.getTargets
        to find the iframe's target and attach to it.
        """
        from GDNox.core.element import Element
        
        try:
            # Method 1: Get all available targets (includes OOP iframes)
            targets_result = await self._cdp.send("Target.getTargets")
            targets = targets_result.get("targetInfos", [])
            
            # Find iframe targets
            iframe_targets = [t for t in targets if t.get("type") == "iframe"]
            
            for target in iframe_targets:
                target_id = target.get("targetId")
                if not target_id:
                    continue
                
                element = await self._search_in_oop_iframe(target_id, selector)
                if element:
                    return element
            
            # Method 2: Also check frames in the frame tree
            doc = await self._cdp.send("DOM.getDocument", {"depth": -1, "pierce": True})
            
            # Find all iframes (including those in shadow roots)
            iframes = self._find_all_iframes(doc.get("root", {}))
            
            for iframe_info in iframes:
                backend_id = iframe_info.get("backendNodeId")
                if not backend_id:
                    continue
                
                element = await self._search_iframe_content(backend_id, selector)
                if element:
                    return element
                    
        except CDPError:
            pass
        
        return None
    
    async def _search_in_oop_iframe(self, target_id: str, selector: str) -> Optional["Element"]:
        """
        Search inside an out-of-process iframe using stored session or attachToTarget.
        
        This is needed for cross-origin iframes like Cloudflare Turnstile.
        """
        from GDNox.core.element import Element
        
        try:
            # First check if we already have a session from auto-attach
            session_id = self._oop_frame_sessions.get(target_id)
            
            if not session_id:
                # Fallback: manually attach to the iframe target
                attach_result = await self._cdp.send("Target.attachToTarget", {
                    "targetId": target_id,
                    "flatten": True,
                })
                session_id = attach_result.get("sessionId")
                
                if session_id:
                    # Store for future use
                    self._oop_frame_sessions[target_id] = session_id
                    
                    # Initialize the frame
                    await self._init_oop_frame(session_id)
            
            if not session_id:
                return None
            
            # Get iframe offset in viewport (for click coordinates)
            iframe_offset = await self._get_iframe_offset_for_target(target_id)
            
            # Enable DOM in the iframe session
            await self._cdp.send("DOM.enable", {}, session_id=session_id)
            
            # Get document with pierce
            doc_result = await self._cdp.send("DOM.getDocument", {
                "depth": -1,
                "pierce": True,
            }, session_id=session_id)
            
            root_id = doc_result.get("root", {}).get("nodeId")
            if not root_id:
                return None
            
            # Step 1: Try querySelector in iframe
            try:
                query_result = await self._cdp.send("DOM.querySelector", {
                    "nodeId": root_id,
                    "selector": selector,
                }, session_id=session_id)
                
                node_id = query_result.get("nodeId", 0)
                if node_id:
                    # For OOP iframe elements, include session_id and iframe offset
                    return Element(self._cdp, node_id, selector, session_id=session_id, iframe_offset=iframe_offset)
            except CDPError:
                pass
            
            # Step 2: Search in closed shadow roots inside iframe
            closed_srs = self._collect_all_shadow_roots(doc_result.get("root", {}))
            
            for sr_info in closed_srs:
                if sr_info.get("type") != "closed":
                    continue
                
                backend_id = sr_info.get("backendNodeId")
                try:
                    resolved = await self._cdp.send("DOM.resolveNode", {
                        "backendNodeId": backend_id,
                    }, session_id=session_id)
                    
                    sr_object_id = resolved.get("object", {}).get("objectId")
                    if not sr_object_id:
                        continue
                    
                    # Escape selector for JavaScript (use json.dumps to properly escape quotes)
                    import json
                    escaped_selector = json.dumps(selector)  # Produces "selector" with proper escaping
                    
                    query_result = await self._cdp.send("Runtime.callFunctionOn", {
                        "objectId": sr_object_id,
                        "functionDeclaration": f"""
                            function() {{
                                return this.querySelector({escaped_selector});
                            }}
                        """,
                        "returnByValue": False,
                    }, session_id=session_id)
                    
                    elem_obj_id = query_result.get("result", {}).get("objectId")
                    if elem_obj_id:
                        node_result = await self._cdp.send("DOM.requestNode", {
                            "objectId": elem_obj_id,
                        }, session_id=session_id)
                        
                        node_id = node_result.get("nodeId")
                        if node_id:
                            return Element(self._cdp, node_id, selector, session_id=session_id, iframe_offset=iframe_offset)
                except CDPError:
                    continue
                        
        except CDPError as e:
            logger.debug(f"OOP iframe search failed: {e}")
        
        return None
    
    async def _get_iframe_offset_for_target(self, target_id: str) -> tuple:
        """
        Get the viewport offset of an OOP iframe by finding it in the main DOM.
        
        Returns (x, y) offset of the iframe's top-left corner in viewport coordinates.
        """
        try:
            # Get main document with pierce to find all iframes
            doc = await self._cdp.send("DOM.getDocument", {"depth": -1, "pierce": True})
            
            # Find all iframe elements
            def find_iframes(node):
                results = []
                if node.get("nodeName", "").upper() == "IFRAME":
                    results.append(node.get("backendNodeId"))
                for child in node.get("children", []):
                    results.extend(find_iframes(child))
                for sr in node.get("shadowRoots", []):
                    results.extend(find_iframes(sr))
                return results
            
            iframe_backends = find_iframes(doc.get("root", {}))
            
            # For each iframe, try to get its content quads
            for backend_id in iframe_backends:
                try:
                    quads = await self._cdp.send("DOM.getContentQuads", {
                        "backendNodeId": backend_id,
                    })
                    
                    quads_list = quads.get("quads", [])
                    if quads_list and len(quads_list[0]) >= 2:
                        # Return top-left corner (x1, y1)
                        return (quads_list[0][0], quads_list[0][1])
                except CDPError:
                    continue
        except CDPError:
            pass
        
        return (0, 0)  # Default: no offset
    
    def _find_all_iframes(self, node: Dict, results: Optional[List[Dict]] = None) -> List[Dict]:
        """Recursively find all iframes in the DOM tree, including in shadow roots."""
        if results is None:
            results = []
        
        if node.get("nodeName", "").upper() == "IFRAME":
            results.append({
                "backendNodeId": node.get("backendNodeId"),
                "frameId": node.get("frameId"),
            })
        
        for child in node.get("children", []):
            self._find_all_iframes(child, results)
        
        for sr in node.get("shadowRoots", []):
            self._find_all_iframes(sr, results)
        
        return results
    
    def _collect_child_frames(self, frame_tree: Dict, results: Optional[List[Dict]] = None) -> List[Dict]:
        """Recursively collect all child frames from frame tree."""
        if results is None:
            results = []
        
        # Add child frames
        for child in frame_tree.get("childFrames", []):
            frame = child.get("frame", {})
            if frame:
                results.append(frame)
            # Recurse into nested frames
            self._collect_child_frames(child, results)
        
        return results
    
    async def _find_iframe_by_url(self, node: Dict, url: str) -> List[int]:
        """Find iframe elements by matching URL."""
        results = []
        
        node_name = node.get("nodeName", "").upper()
        if node_name == "IFRAME":
            # Check if this iframe's src matches
            attrs = node.get("attributes", [])
            for i in range(0, len(attrs), 2):
                if i + 1 < len(attrs) and attrs[i] == "src":
                    src = attrs[i + 1]
                    # Partial match - URL might have query params
                    if url in src or src in url or self._urls_match(src, url):
                        backend_id = node.get("backendNodeId")
                        if backend_id:
                            results.append(backend_id)
        
        # Check children
        for child in node.get("children", []):
            results.extend(await self._find_iframe_by_url(child, url))
        
        # Check shadow roots
        for sr in node.get("shadowRoots", []):
            results.extend(await self._find_iframe_by_url(sr, url))
        
        return results
    
    def _urls_match(self, url1: str, url2: str) -> bool:
        """Check if two URLs refer to the same resource (ignoring protocol and params)."""
        from urllib.parse import urlparse
        try:
            p1 = urlparse(url1)
            p2 = urlparse(url2)
            return p1.netloc == p2.netloc and p1.path == p2.path
        except:
            return False
    
    async def _search_iframe_content(self, iframe_backend_id: int, selector: str) -> Optional["Element"]:
        """Search for element inside an iframe's content document."""
        from GDNox.core.element import Element
        
        try:
            # Resolve iframe to object
            result = await self._cdp.send("DOM.resolveNode", {
                "backendNodeId": iframe_backend_id,
            })
            iframe_object_id = result.get("object", {}).get("objectId")
            if not iframe_object_id:
                return None
            
            # Get contentDocument from iframe
            content_doc_result = await self._cdp.send("Runtime.callFunctionOn", {
                "objectId": iframe_object_id,
                "functionDeclaration": """
                    function() {
                        try {
                            return this.contentDocument;
                        } catch (e) {
                            // Cross-origin iframe - can't access
                            return null;
                        }
                    }
                """,
                "returnByValue": False,
            })
            
            content_doc_id = content_doc_result.get("result", {}).get("objectId")
            if not content_doc_id:
                # Cross-origin iframe - try alternative approach
                return await self._search_cross_origin_iframe(iframe_backend_id, selector)
            
            # querySelector on content document
            query_result = await self._cdp.send("Runtime.callFunctionOn", {
                "objectId": content_doc_id,
                "functionDeclaration": f"""
                    function() {{
                        return this.querySelector('{selector}');
                    }}
                """,
                "returnByValue": False,
            })
            
            elem_object_id = query_result.get("result", {}).get("objectId")
            if elem_object_id:
                node_result = await self._cdp.send("DOM.requestNode", {
                    "objectId": elem_object_id,
                })
                node_id = node_result.get("nodeId")
                if node_id:
                    return Element(self._cdp, node_id, selector)
                    
        except CDPError:
            pass
        
        return None
    
    async def _search_cross_origin_iframe(self, iframe_backend_id: int, selector: str) -> Optional["Element"]:
        """
        Search inside a cross-origin iframe, including its closed shadow roots.
        
        For cross-origin iframes, we can't access contentDocument directly.
        We use CDP to get the frame's context and search there, including
        inside any closed shadow roots (like Cloudflare Turnstile uses).
        """
        from GDNox.core.element import Element
        
        try:
            # Get the iframe's frame ID
            described = await self._cdp.send("DOM.describeNode", {
                "backendNodeId": iframe_backend_id,
                "depth": -1,
                "pierce": True,  # Critical: pierce shadow roots
            })
            
            frame_id = described.get("node", {}).get("frameId")
            if not frame_id:
                return None
            
            # Create isolated world in the iframe's context
            world_result = await self._cdp.send("Page.createIsolatedWorld", {
                "frameId": frame_id,
                "worldName": "gdnium_iframe_search",
            })
            context_id = world_result.get("executionContextId")
            if not context_id:
                return None
            
            # Step 1: Try normal querySelector in iframe
            eval_result = await self._cdp.send("Runtime.evaluate", {
                "expression": f"document.querySelector('{selector}')",
                "contextId": context_id,
                "returnByValue": False,
            })
            
            elem_object_id = eval_result.get("result", {}).get("objectId")
            if elem_object_id:
                try:
                    node_result = await self._cdp.send("DOM.requestNode", {
                        "objectId": elem_object_id,
                    })
                    node_id = node_result.get("nodeId")
                    if node_id:
                        return Element(self._cdp, node_id, selector)
                except CDPError:
                    pass
            
            # Step 2: Search inside closed shadow roots within the iframe
            # Use JavaScript to find and query shadow roots
            shadow_search_js = f"""
                (function() {{
                    function findInShadowRoots(root, selector) {{
                        // Try in root first
                        let result = root.querySelector(selector);
                        if (result) return result;
                        
                        // Search all elements that might have shadow roots
                        const allElements = root.querySelectorAll('*');
                        for (const el of allElements) {{
                            if (el.shadowRoot) {{
                                result = findInShadowRoots(el.shadowRoot, selector);
                                if (result) return result;
                            }}
                        }}
                        return null;
                    }}
                    return findInShadowRoots(document, '{selector}');
                }})()
            """
            
            shadow_result = await self._cdp.send("Runtime.evaluate", {
                "expression": shadow_search_js,
                "contextId": context_id,
                "returnByValue": False,
            })
            
            elem_object_id = shadow_result.get("result", {}).get("objectId")
            if elem_object_id:
                try:
                    node_result = await self._cdp.send("DOM.requestNode", {
                        "objectId": elem_object_id,
                    })
                    node_id = node_result.get("nodeId")
                    if node_id:
                        return Element(self._cdp, node_id, selector)
                except CDPError:
                    pass
            
            # Step 3: For CLOSED shadow roots, we need CDP describeNode
            # Get iframe's document node in the frame context
            doc_result = await self._cdp.send("Runtime.evaluate", {
                "expression": "document",
                "contextId": context_id,
                "returnByValue": False,
            })
            doc_object_id = doc_result.get("result", {}).get("objectId")
            
            if doc_object_id:
                # Describe with pierce to see closed shadow roots
                described_doc = await self._cdp.send("DOM.describeNode", {
                    "objectId": doc_object_id,
                    "depth": -1,
                    "pierce": True,
                })
                
                # Collect closed shadow roots from the described tree
                closed_shadow_roots = self._collect_all_shadow_roots(described_doc.get("node", {}))
                
                for shadow_info in closed_shadow_roots:
                    if shadow_info.get("type") != "closed":
                        continue
                    
                    backend_id = shadow_info["backendNodeId"]
                    try:
                        # Resolve shadow root
                        resolved = await self._cdp.send("DOM.resolveNode", {
                            "backendNodeId": backend_id,
                            "executionContextId": context_id,
                        })
                        sr_object_id = resolved.get("object", {}).get("objectId")
                        if not sr_object_id:
                            continue
                        
                        # querySelector on closed shadow root
                        query_result = await self._cdp.send("Runtime.callFunctionOn", {
                            "objectId": sr_object_id,
                            "functionDeclaration": f"""
                                function() {{
                                    return this.querySelector('{selector}');
                                }}
                            """,
                            "returnByValue": False,
                        })
                        
                        elem_object_id = query_result.get("result", {}).get("objectId")
                        if elem_object_id:
                            node_result = await self._cdp.send("DOM.requestNode", {
                                "objectId": elem_object_id,
                            })
                            node_id = node_result.get("nodeId")
                            if node_id:
                                return Element(self._cdp, node_id, selector)
                    except CDPError:
                        continue
                    
        except CDPError as e:
            logger.debug(f"Cross-origin iframe search failed: {e}")
        
        return None
        return None
    
    async def _unified_query_selector(
        self,
        root_node: Dict,
        selector: str,
    ) -> Optional["Element"]:
        """
        Unified querySelector that searches normal DOM and closed shadow roots.
        
        A simple querySelector call automatically pierces closed shadow roots.
        """
        from GDNox.core.element import Element
        
        # Step 1: Try normal querySelector on document root
        root_id = root_node.get("nodeId")
        if root_id:
            try:
                result = await self._cdp.send("DOM.querySelector", {
                    "nodeId": root_id,
                    "selector": selector,
                })
                node_id = result.get("nodeId", 0)
                if node_id:
                    return Element(self._cdp, node_id, selector)
            except CDPError:
                pass
        
        # Step 2: Search in ALL shadow roots (open and closed)
        all_shadow_roots = self._collect_all_shadow_roots(root_node)
        
        for shadow_info in all_shadow_roots:
            backend_id = shadow_info["backendNodeId"]
            
            try:
                # Resolve shadow root to object
                result = await self._cdp.send("DOM.resolveNode", {
                    "backendNodeId": backend_id,
                })
                object_id = result.get("object", {}).get("objectId")
                if not object_id:
                    continue
                
                # Run querySelector inside shadow root
                query_result = await self._cdp.send("Runtime.callFunctionOn", {
                    "objectId": object_id,
                    "functionDeclaration": f"""
                        function() {{
                            return this.querySelector('{selector}');
                        }}
                    """,
                    "returnByValue": False,
                })
                
                elem_object_id = query_result.get("result", {}).get("objectId")
                if elem_object_id:
                    # Convert object to node
                    node_result = await self._cdp.send("DOM.requestNode", {
                        "objectId": elem_object_id,
                    })
                    node_id = node_result.get("nodeId")
                    if node_id:
                        return Element(self._cdp, node_id, selector)
            except CDPError:
                continue
        
        return None
    
    async def find_all(
        self,
        selector: str,
    ) -> List["Element"]:
        """
        Find all elements matching selector.
        
        Searches BOTH normal DOM AND inside closed shadow roots transparently.
        
        Args:
            selector: CSS selector
            
        Returns:
            List of Elements
        """
        from GDNox.core.element import Element
        
        elements = []
        
        doc = await self._cdp.send("DOM.getDocument", {"depth": -1, "pierce": True})
        root_id = doc["root"]["nodeId"]
        
        # Step 1: Get elements from normal DOM
        try:
            result = await self._cdp.send("DOM.querySelectorAll", {
                "nodeId": root_id,
                "selector": selector,
            })
            for node_id in result.get("nodeIds", []):
                if node_id:
                    elements.append(Element(self._cdp, node_id, selector))
        except CDPError:
            pass
        
        # Step 2: Get elements from ALL shadow roots
        all_shadow_roots = self._collect_all_shadow_roots(doc["root"])
        
        for shadow_info in all_shadow_roots:
            backend_id = shadow_info["backendNodeId"]
            
            try:
                result = await self._cdp.send("DOM.resolveNode", {
                    "backendNodeId": backend_id,
                })
                object_id = result.get("object", {}).get("objectId")
                if not object_id:
                    continue
                
                # querySelectorAll inside shadow root
                query_result = await self._cdp.send("Runtime.callFunctionOn", {
                    "objectId": object_id,
                    "functionDeclaration": f"""
                        function() {{
                            return Array.from(this.querySelectorAll('{selector}'));
                        }}
                    """,
                    "returnByValue": False,
                })
                
                array_object_id = query_result.get("result", {}).get("objectId")
                if not array_object_id:
                    continue
                
                # Extract elements from array
                props = await self._cdp.send("Runtime.getProperties", {
                    "objectId": array_object_id,
                    "ownProperties": True,
                })
                
                for prop in props.get("result", []):
                    if prop.get("name", "").isdigit():
                        elem_obj_id = prop.get("value", {}).get("objectId")
                        if elem_obj_id:
                            node_result = await self._cdp.send("DOM.requestNode", {
                                "objectId": elem_obj_id,
                            })
                            node_id = node_result.get("nodeId")
                            if node_id:
                                elements.append(Element(self._cdp, node_id, selector))
            except CDPError:
                continue
        
        return elements
    
    def _collect_all_shadow_roots(
        self,
        node: Dict,
        results: Optional[List[Dict]] = None,
    ) -> List[Dict]:
        """
        Recursively collect ALL shadow roots (open AND closed) from DOM tree.
        
        Returns list of dicts with backendNodeId and shadowRootType.
        """
        if results is None:
            results = []
        
        # Check for shadow roots on this node
        for sr in node.get("shadowRoots", []):
            backend_id = sr.get("backendNodeId")
            sr_type = sr.get("shadowRootType", "open")
            if backend_id:
                results.append({
                    "backendNodeId": backend_id,
                    "type": sr_type,
                })
            # Also collect from inside the shadow root
            self._collect_all_shadow_roots(sr, results)
        
        # Check children
        for child in node.get("children", []):
            self._collect_all_shadow_roots(child, results)
        
        return results
    
    async def screenshot(self, path: Optional[str] = None, full_page: bool = False) -> bytes:
        """
        Take a screenshot.
        
        Args:
            path: Optional path to save screenshot
            full_page: Capture full scrollable page
            
        Returns:
            Screenshot as PNG bytes
        """
        params = {"format": "png"}
        
        if full_page:
            # Get full page dimensions
            metrics = await self._cdp.send("Page.getLayoutMetrics")
            content_size = metrics.get("contentSize", {})
            params["clip"] = {
                "x": 0,
                "y": 0,
                "width": content_size.get("width", 1920),
                "height": content_size.get("height", 1080),
                "scale": 1,
            }
        
        result = await self._cdp.send("Page.captureScreenshot", params)
        data = base64.b64decode(result["data"])
        
        if path:
            with open(path, "wb") as f:
                f.write(data)
        
        return data
    
    async def set_cookies(self, cookies: List[Dict[str, Any]]) -> None:
        """
        Set cookies for the current page.
        
        Args:
            cookies: List of cookie dicts with name, value, domain, etc.
        """
        for cookie in cookies:
            params = {
                "name": cookie.get("name", ""),
                "value": cookie.get("value", ""),
                "domain": cookie.get("domain", ""),
                "path": cookie.get("path", "/"),
                "secure": cookie.get("secure", False),
                "httpOnly": cookie.get("httpOnly", False),
            }
            
            if "expires" in cookie:
                params["expires"] = cookie["expires"]
            if "sameSite" in cookie:
                params["sameSite"] = cookie["sameSite"]
            
            await self._cdp.send("Network.setCookie", params)
    
    async def get_cookies(self, urls: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Get cookies for the current page or specified URLs.
        
        Args:
            urls: Optional list of URLs to get cookies for
            
        Returns:
            List of cookie dicts
        """
        params = {}
        if urls:
            params["urls"] = urls
        
        result = await self._cdp.send("Network.getCookies", params)
        return result.get("cookies", [])
    
    async def clear_cookies(self) -> None:
        """Clear all cookies."""
        await self._cdp.send("Network.clearBrowserCookies")
    
    async def set_local_storage(self, origin: str, items: Dict[str, str]) -> None:
        """
        Set local storage items for an origin.
        
        Args:
            origin: Origin URL (e.g., "https://example.com")
            items: Dict of key-value pairs to set
        """
        for key, value in items.items():
            await self.evaluate(f"""
                (() => {{
                    localStorage.setItem({json.dumps(key)}, {json.dumps(value)});
                }})()
            """)
    
    async def get_local_storage(self) -> Dict[str, str]:
        """
        Get all local storage items for the current page.
        
        Returns:
            Dict of key-value pairs
        """
        result = await self.evaluate("""
            (() => {
                const items = {};
                for (let i = 0; i < localStorage.length; i++) {
                    const key = localStorage.key(i);
                    items[key] = localStorage.getItem(key);
                }
                return items;
            })()
        """)
        return result or {}
    
    async def sleep(self, seconds: float) -> None:
        """
        Wait for a randomized amount of time.
        
        The actual wait time is randomized between 50% less and 50% more
        of the specified value for natural human-like behavior.
        
        Args:
            seconds: Base wait time (will be randomized ±50%)
        """
        import random
        actual_time = seconds * random.uniform(0.5, 1.5)
        await asyncio.sleep(actual_time)
    
    @property
    def network(self) -> "Network":
        """
        Get network interception interface.
        
        Usage:
            @tab.network.on('request')
            async def on_request(request):
                print(f"Request: {request.url}")
            
            @tab.network.on('response')
            async def on_response(response):
                body = await response.body()
            
            @tab.network.intercept('*api.example.com*')
            async def intercept(request):
                await request.respond(json={"fake": "data"})
        """
        if self._network is None:
            from GDNox.core.network import Network
            self._network = Network(self._cdp)
        return self._network
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
