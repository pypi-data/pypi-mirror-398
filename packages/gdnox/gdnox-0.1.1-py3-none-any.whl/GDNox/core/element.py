"""
Element - DOM element wrapper.

Handles:
- Element interactions (click, type, etc.)
- Human-like behavior simulation
- Getting element properties
"""

import asyncio
import logging
import random
from typing import Any, Dict, Optional, TYPE_CHECKING

from GDNox.core.cdp_client import CDPClient

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class Element:
    """
    DOM element wrapper with interaction methods.
    """
    
    def __init__(
        self,
        cdp: CDPClient,
        node_id: int,
        selector: str = "",
        session_id: Optional[str] = None,
        iframe_offset: Optional[tuple] = None,  # (x, y) offset of iframe in viewport
    ):
        """
        Initialize element.
        
        Args:
            cdp: CDP client
            node_id: DOM node ID
            selector: Original selector used to find this element
            session_id: Optional session ID for OOP iframe elements
            iframe_offset: Optional (x, y) offset of containing iframe in viewport
        """
        self._cdp = cdp
        self._node_id = node_id
        self._selector = selector
        self._session_id = session_id
        self._iframe_offset = iframe_offset or (0, 0)
        self._object_id: Optional[str] = None
        self._backend_node_id: Optional[int] = None
    
    async def _resolve_object(self) -> str:
        """Get object ID for this element."""
        if self._object_id:
            return self._object_id
        
        result = await self._cdp.send("DOM.resolveNode", {
            "nodeId": self._node_id,
        }, session_id=self._session_id)
        self._object_id = result.get("object", {}).get("objectId")
        return self._object_id
    
    async def _get_box_model(self) -> Optional[Dict]:
        """Get element's box model for positioning."""
        try:
            result = await self._cdp.send("DOM.getBoxModel", {
                "nodeId": self._node_id,
            }, session_id=self._session_id)  # Use session_id for OOP iframe elements
            return result.get("model")
        except Exception:
            return None
    
    async def click(self, human_like: bool = True) -> None:
        """
        Click the element.
        
        Args:
            human_like: If True, use realistic mouse movement and timing
        """
        # For OOP iframe elements, we need to use DOM.getContentQuads
        # which gives us coordinates in the viewport
        if self._session_id:
            await self._click_in_iframe(human_like)
        else:
            await self._click_normal(human_like)
    
    async def _click_in_iframe(self, human_like: bool = True) -> None:
        """Click element inside OOP iframe using viewport coordinates."""
        # Use getContentQuads to get coordinates relative to iframe
        try:
            quads_result = await self._cdp.send("DOM.getContentQuads", {
                "nodeId": self._node_id,
            }, session_id=self._session_id)
            
            quads = quads_result.get("quads", [])
            if not quads or len(quads[0]) < 8:
                raise Exception("Could not get content quads")
            
            # quads[0] is [x1,y1, x2,y2, x3,y3, x4,y4] - corners of the element
            quad = quads[0]
            x = (quad[0] + quad[2] + quad[4] + quad[6]) / 4
            y = (quad[1] + quad[3] + quad[5] + quad[7]) / 4
            
        except Exception as e:
            # Fallback to box model
            box = await self._get_box_model()
            if not box:
                raise Exception(f"Could not get element position: {e}")
            
            content = box.get("content", [])
            if len(content) >= 6:
                x = (content[0] + content[2]) / 2
                y = (content[1] + content[5]) / 2
            else:
                raise Exception("Invalid box model")
        
        # Add iframe offset to get absolute viewport coordinates
        # The element coords are relative to iframe, we need to add iframe's position
        iframe_x, iframe_y = self._iframe_offset
        x += iframe_x
        y += iframe_y
        
        # Add small random offset for human-like behavior
        if human_like:
            x += random.uniform(-2, 2)
            y += random.uniform(-2, 2)
            await asyncio.sleep(random.uniform(0.05, 0.15))
        
        # Dispatch mouse events to MAIN session (None), not iframe session
        await self._cdp.send("Input.dispatchMouseEvent", {
            "type": "mouseMoved",
            "x": x,
            "y": y,
        })  # No session_id - goes to main page
        
        if human_like:
            await asyncio.sleep(random.uniform(0.02, 0.08))
        
        await self._cdp.send("Input.dispatchMouseEvent", {
            "type": "mousePressed",
            "x": x,
            "y": y,
            "button": "left",
            "clickCount": 1,
        })
        
        if human_like:
            await asyncio.sleep(random.uniform(0.03, 0.1))
        
        await self._cdp.send("Input.dispatchMouseEvent", {
            "type": "mouseReleased",
            "x": x,
            "y": y,
            "button": "left",
            "clickCount": 1,
        })
    
    async def _click_normal(self, human_like: bool = True) -> None:
        """Click regular element (not in OOP iframe)."""
        # Get element center
        box = await self._get_box_model()
        if not box:
            # Try scrolling into view first
            await self.scroll_into_view()
            box = await self._get_box_model()
            if not box:
                raise Exception("Could not get element position")
        
        # Calculate center point
        content = box.get("content", [])
        if len(content) >= 6:
            x = (content[0] + content[2]) / 2
            y = (content[1] + content[5]) / 2
        else:
            raise Exception("Invalid box model")
        
        # Add small random offset for human-like behavior
        if human_like:
            x += random.uniform(-3, 3)
            y += random.uniform(-3, 3)
            await asyncio.sleep(random.uniform(0.05, 0.15))
        
        # Dispatch mouse events
        await self._cdp.send("Input.dispatchMouseEvent", {
            "type": "mouseMoved",
            "x": x,
            "y": y,
        })
        
        if human_like:
            await asyncio.sleep(random.uniform(0.02, 0.08))
        
        await self._cdp.send("Input.dispatchMouseEvent", {
            "type": "mousePressed",
            "x": x,
            "y": y,
            "button": "left",
            "clickCount": 1,
        })
        
        if human_like:
            await asyncio.sleep(random.uniform(0.03, 0.1))
        
        await self._cdp.send("Input.dispatchMouseEvent", {
            "type": "mouseReleased",
            "x": x,
            "y": y,
            "button": "left",
            "clickCount": 1,
        })
    
    async def type(self, text: str, human_like: bool = True) -> None:
        """
        Type text into the element.
        
        Args:
            text: Text to type
            human_like: If True, use realistic typing speed
        """
        # Focus the element first
        await self.focus()
        
        for char in text:
            # Dispatch key events
            await self._cdp.send("Input.dispatchKeyEvent", {
                "type": "keyDown",
                "text": char,
            })
            await self._cdp.send("Input.dispatchKeyEvent", {
                "type": "keyUp",
                "text": char,
            })
            
            if human_like:
                # Variable typing speed
                delay = random.uniform(0.05, 0.15)
                # Occasional longer pause
                if random.random() < 0.1:
                    delay += random.uniform(0.1, 0.3)
                await asyncio.sleep(delay)
    
    async def focus(self) -> None:
        """Focus the element."""
        await self._cdp.send("DOM.focus", {
            "nodeId": self._node_id,
        }, session_id=self._session_id)
    
    async def scroll_into_view(self) -> None:
        """Scroll element into view."""
        object_id = await self._resolve_object()
        
        await self._cdp.send("Runtime.callFunctionOn", {
            "objectId": object_id,
            "functionDeclaration": """
                function() {
                    this.scrollIntoView({
                        behavior: 'smooth',
                        block: 'center',
                        inline: 'center'
                    });
                }
            """,
        }, session_id=self._session_id)
        
        # Wait for scroll animation
        await asyncio.sleep(0.3)
    
    async def text(self) -> str:
        """Get element's text content."""
        object_id = await self._resolve_object()
        
        result = await self._cdp.send("Runtime.callFunctionOn", {
            "objectId": object_id,
            "functionDeclaration": "function() { return this.textContent; }",
            "returnByValue": True,
        }, session_id=self._session_id)
        
        return result.get("result", {}).get("value", "")
    
    async def inner_html(self) -> str:
        """Get element's inner HTML."""
        result = await self._cdp.send("DOM.getOuterHTML", {
            "nodeId": self._node_id,
        }, session_id=self._session_id)
        return result.get("outerHTML", "")
    
    async def get_attribute(self, name: str) -> Optional[str]:
        """Get element attribute value."""
        result = await self._cdp.send("DOM.getAttributes", {
            "nodeId": self._node_id,
        }, session_id=self._session_id)
        
        attrs = result.get("attributes", [])
        # Attributes come as [name, value, name, value, ...]
        for i in range(0, len(attrs), 2):
            if attrs[i] == name:
                return attrs[i + 1]
        
        return None
    
    async def set_attribute(self, name: str, value: str) -> None:
        """Set element attribute."""
        await self._cdp.send("DOM.setAttributeValue", {
            "nodeId": self._node_id,
            "name": name,
            "value": value,
        }, session_id=self._session_id)
    
    async def is_visible(self) -> bool:
        """Check if element is visible."""
        box = await self._get_box_model()
        if not box:
            return False
        
        content = box.get("content", [])
        if len(content) < 4:
            return False
        
        width = abs(content[2] - content[0])
        height = abs(content[5] - content[1])
        
        return width > 0 and height > 0
    
    @property
    def node_id(self) -> int:
        return self._node_id
    
    @property
    def selector(self) -> str:
        return self._selector
