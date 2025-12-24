"""
Shadow Root Access - Access elements inside closed Shadow DOMs.

Uses CDP techniques:
- DOM.describeNode with pierce=true to see closed shadow roots
- DOM.resolveNode to get element handles
"""

import logging
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from GDNox.core.cdp_client import CDPClient, CDPError

if TYPE_CHECKING:
    from GDNox.core.element import Element

logger = logging.getLogger(__name__)


class ShadowRootAccessor:
    """
    Provides access to closed Shadow DOM elements.
    
    This uses Chrome DevTools Protocol to pierce closed shadow roots,
    which is normally not possible via standard DOM APIs.
    """
    
    def __init__(self, cdp: CDPClient):
        """
        Initialize shadow root accessor.
        
        Args:
            cdp: CDP client for communication
        """
        self._cdp = cdp
    
    async def describe_node_with_shadow(
        self,
        node_id: Optional[int] = None,
        object_id: Optional[str] = None,
        depth: int = -1,
    ) -> Dict[str, Any]:
        """
        Describe a DOM node including its closed shadow roots.
        
        Using pierce=true allows us to see inside closed shadow roots.
        
        Args:
            node_id: DOM node ID
            object_id: Runtime object ID
            depth: Tree depth (-1 for entire subtree)
            
        Returns:
            Node description including shadow root info
        """
        params = {
            "depth": depth,
            "pierce": True,  # CRITICAL: This allows seeing closed shadow roots
        }
        
        if node_id:
            params["nodeId"] = node_id
        elif object_id:
            params["objectId"] = object_id
        else:
            raise ValueError("Either node_id or object_id must be provided")
        
        result = await self._cdp.send("DOM.describeNode", params)
        return result.get("node", {})
    
    async def find_closed_shadow_roots(
        self,
        root_node: Dict[str, Any],
    ) -> List[int]:
        """
        Find all closed shadow roots in a DOM subtree.
        
        Args:
            root_node: Root node from DOM.describeNode
            
        Returns:
            List of backend node IDs for closed shadow roots
        """
        shadow_roots = []
        self._collect_shadow_roots(root_node, shadow_roots)
        return shadow_roots
    
    def _collect_shadow_roots(
        self,
        node: Dict[str, Any],
        results: List[int],
    ) -> None:
        """Recursively collect closed shadow root backend IDs."""
        # Check for shadow roots on this node
        for sr in node.get("shadowRoots", []):
            if sr.get("shadowRootType") == "closed":
                backend_id = sr.get("backendNodeId")
                if backend_id:
                    results.append(backend_id)
                    logger.debug(f"Found closed shadow root: {backend_id}")
            
            # Also search inside the shadow root
            self._collect_shadow_roots(sr, results)
        
        # Search children
        for child in node.get("children", []):
            self._collect_shadow_roots(child, results)
    
    async def resolve_shadow_root(
        self,
        backend_node_id: int,
        context_id: Optional[int] = None,
    ) -> Optional[str]:
        """
        Resolve a shadow root backend ID to an object ID.
        
        Args:
            backend_node_id: Backend node ID of the shadow root
            context_id: Execution context ID (optional)
            
        Returns:
            Object ID for the shadow root, or None if failed
        """
        try:
            params = {"backendNodeId": backend_node_id}
            if context_id:
                params["executionContextId"] = context_id
            
            result = await self._cdp.send("DOM.resolveNode", params)
            return result.get("object", {}).get("objectId")
        except CDPError as e:
            logger.debug(f"Failed to resolve shadow root {backend_node_id}: {e}")
            return None
    
    async def query_selector_in_shadow(
        self,
        shadow_object_id: str,
        selector: str,
    ) -> Optional[str]:
        """
        Execute querySelector inside a shadow root.
        
        Args:
            shadow_object_id: Object ID of the shadow root
            selector: CSS selector
            
        Returns:
            Object ID of found element, or None
        """
        try:
            result = await self._cdp.send("Runtime.callFunctionOn", {
                "objectId": shadow_object_id,
                "functionDeclaration": f"""
                    function() {{
                        return this.querySelector('{selector}');
                    }}
                """,
                "returnByValue": False,
            })
            
            return result.get("result", {}).get("objectId")
        except CDPError as e:
            logger.debug(f"querySelector in shadow failed: {e}")
            return None
    
    async def query_selector_all_in_shadow(
        self,
        shadow_object_id: str,
        selector: str,
    ) -> List[str]:
        """
        Execute querySelectorAll inside a shadow root.
        
        Args:
            shadow_object_id: Object ID of the shadow root
            selector: CSS selector
            
        Returns:
            List of object IDs for found elements
        """
        try:
            # Get the NodeList
            result = await self._cdp.send("Runtime.callFunctionOn", {
                "objectId": shadow_object_id,
                "functionDeclaration": f"""
                    function() {{
                        return Array.from(this.querySelectorAll('{selector}'));
                    }}
                """,
                "returnByValue": False,
            })
            
            array_object_id = result.get("result", {}).get("objectId")
            if not array_object_id:
                return []
            
            # Get array properties to extract individual elements
            props = await self._cdp.send("Runtime.getProperties", {
                "objectId": array_object_id,
                "ownProperties": True,
            })
            
            object_ids = []
            for prop in props.get("result", []):
                if prop.get("name", "").isdigit():
                    obj_id = prop.get("value", {}).get("objectId")
                    if obj_id:
                        object_ids.append(obj_id)
            
            return object_ids
        except CDPError as e:
            logger.debug(f"querySelectorAll in shadow failed: {e}")
            return []
    
    async def find_in_all_shadow_roots(
        self,
        selector: str,
        root_node_id: Optional[int] = None,
    ) -> Optional[str]:
        """
        Find element by selector, searching in all closed shadow roots.
        
        This is the main method for finding elements that might be
        inside closed shadow DOMs.
        
        Args:
            selector: CSS selector
            root_node_id: Starting node (document root if not specified)
            
        Returns:
            Object ID of first matching element, or None
        """
        # Get document with shadow roots pierced
        if root_node_id:
            root = await self.describe_node_with_shadow(node_id=root_node_id)
        else:
            doc_result = await self._cdp.send("DOM.getDocument", {
                "depth": -1,
                "pierce": True,
            })
            root = doc_result.get("root", {})
        
        # Find all closed shadow roots
        shadow_root_ids = await self.find_closed_shadow_roots(root)
        
        # Search in each shadow root
        for backend_id in shadow_root_ids:
            object_id = await self.resolve_shadow_root(backend_id)
            if not object_id:
                continue
            
            elem_object_id = await self.query_selector_in_shadow(object_id, selector)
            if elem_object_id:
                return elem_object_id
        
        return None
