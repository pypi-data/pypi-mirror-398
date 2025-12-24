"""
Runtime Patches - Avoid CDP detection.

Prevents detection by:
- Avoiding Runtime.enable (detectable)
- Using isolated execution contexts
- Patching console leaks
"""

import logging
from typing import Optional

from GDNox.core.cdp_client import CDPClient

logger = logging.getLogger(__name__)


class RuntimePatches:
    """
    Applies patches to avoid CDP detection.
    
    Key techniques:
    - Avoid calling Runtime.enable (creates detectable side effects)
    - Use Page.createIsolatedWorld for JS execution
    - Avoid Console.enable
    """
    
    def __init__(self, cdp: CDPClient):
        """
        Initialize runtime patches.
        
        Args:
            cdp: CDP client
        """
        self._cdp = cdp
        self._isolated_context_id: Optional[int] = None
    
    async def create_isolated_context(self, frame_id: str, name: str = "gdnium") -> int:
        """
        Create an isolated JavaScript execution context.
        
        Using isolated worlds avoids detection because:
        1. Scripts run in a separate context from the page
        2. No need to call Runtime.enable
        
        Args:
            frame_id: Frame ID to create context in
            name: Name for the world
            
        Returns:
            Execution context ID
        """
        result = await self._cdp.send("Page.createIsolatedWorld", {
            "frameId": frame_id,
            "worldName": name,
            "grantUniveralAccess": True,
        })
        
        context_id = result.get("executionContextId")
        self._isolated_context_id = context_id
        
        logger.debug(f"Created isolated context: {context_id}")
        return context_id
    
    async def evaluate_isolated(
        self,
        expression: str,
        context_id: Optional[int] = None,
        return_by_value: bool = True,
        await_promise: bool = True,
    ):
        """
        Evaluate JavaScript in isolated context.
        
        This is safer than Runtime.evaluate in main world because:
        1. It doesn't require Runtime.enable
        2. Scripts are isolated from page detection attempts
        
        Args:
            expression: JavaScript to evaluate
            context_id: Context ID (uses cached if not provided)
            return_by_value: Return primitive value instead of object
            await_promise: Wait for promise resolution
            
        Returns:
            Evaluation result
        """
        ctx = context_id or self._isolated_context_id
        if not ctx:
            raise RuntimeError("No isolated context available. Call create_isolated_context first.")
        
        result = await self._cdp.send("Runtime.evaluate", {
            "expression": expression,
            "contextId": ctx,
            "returnByValue": return_by_value,
            "awaitPromise": await_promise,
            "userGesture": True,  # Simulate user gesture
        })
        
        if "exceptionDetails" in result:
            exc = result["exceptionDetails"]
            raise Exception(f"JS Error: {exc.get('text', 'Unknown')}")
        
        return result.get("result", {}).get("value")
    
    async def apply_stealth_patches(self, frame_id: str) -> None:
        """
        Apply all stealth patches for a frame.
        
        Args:
            frame_id: Target frame ID
        """
        # Create isolated context first
        await self.create_isolated_context(frame_id)
        
        # Apply patches via addScriptToEvaluateOnNewDocument
        # This runs before any page scripts
        stealth_script = """
        // Remove webdriver property
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
            configurable: true
        });
        
        // Hide Headless indicators
        Object.defineProperty(navigator, 'plugins', {
            get: function() {
                return [
                    {
                        0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                        description: "Portable Document Format",
                        filename: "internal-pdf-viewer",
                        length: 1,
                        name: "Chrome PDF Plugin"
                    },
                    {
                        0: {type: "application/pdf", suffixes: "pdf", description: ""},
                        description: "",
                        filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                        length: 1,
                        name: "Chrome PDF Viewer"
                    }
                ];
            }
        });
        
        // Mock chrome object
        window.chrome = {
            app: {},
            runtime: {
                connect: function() {},
                sendMessage: function() {},
            },
            csi: function() { return {}; },
            loadTimes: function() { return {}; }
        };
        
        // Notification permission
        if (typeof Notification !== 'undefined') {
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = function(parameters) {
                return parameters.name === 'notifications' 
                    ? Promise.resolve({state: Notification.permission})
                    : originalQuery(parameters);
            };
        }
        """
        
        await self._cdp.send("Page.addScriptToEvaluateOnNewDocument", {
            "source": stealth_script,
        })
        
        logger.info("Stealth patches applied")
    
    @property
    def context_id(self) -> Optional[int]:
        """Get current isolated context ID."""
        return self._isolated_context_id
