"""
Human-like Mouse Movements - Bezier curves and realistic motion.

Simulates natural mouse behavior:
- Curved trajectories using Bezier curves
- Acceleration and deceleration
- Micro-movements and overshoot
- Random variations
"""

import asyncio
import logging
import math
import random
from typing import List, Optional, Tuple

from GDNox.core.cdp_client import CDPClient

logger = logging.getLogger(__name__)


def bezier_point(t: float, points: List[Tuple[float, float]]) -> Tuple[float, float]:
    """
    Calculate point on a Bezier curve.
    
    Args:
        t: Parameter 0-1
        points: Control points [(x, y), ...]
        
    Returns:
        (x, y) point on curve
    """
    n = len(points) - 1
    x = 0.0
    y = 0.0
    
    for i, (px, py) in enumerate(points):
        # Bernstein polynomial
        binom = math.factorial(n) / (math.factorial(i) * math.factorial(n - i))
        term = binom * (t ** i) * ((1 - t) ** (n - i))
        x += px * term
        y += py * term
    
    return x, y


def generate_control_points(
    start: Tuple[float, float],
    end: Tuple[float, float],
    deviation: float = 0.3,
) -> List[Tuple[float, float]]:
    """
    Generate random control points for a Bezier curve.
    
    Args:
        start: Starting point
        end: Ending point
        deviation: How much the curve can deviate (0-1)
        
    Returns:
        List of control points including start and end
    """
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    distance = math.sqrt(dx * dx + dy * dy)
    
    # Perpendicular direction for deviation
    if distance > 0:
        perp_x = -dy / distance
        perp_y = dx / distance
    else:
        perp_x, perp_y = 0, 1
    
    # Generate 1-2 control points
    num_controls = random.randint(1, 2)
    points = [start]
    
    for i in range(num_controls):
        t = (i + 1) / (num_controls + 1)
        
        # Point along the line
        base_x = start[0] + dx * t
        base_y = start[1] + dy * t
        
        # Add random perpendicular deviation
        dev = (random.random() * 2 - 1) * deviation * distance
        
        points.append((base_x + perp_x * dev, base_y + perp_y * dev))
    
    points.append(end)
    return points


class HumanMouse:
    """
    Human-like mouse movement simulation.
    
    Features:
    - Bezier curve trajectories
    - Natural acceleration/deceleration
    - Micro-movements and jitter
    - Realistic timing
    """
    
    def __init__(self, cdp: CDPClient):
        """
        Initialize human mouse.
        
        Args:
            cdp: CDP client
        """
        self._cdp = cdp
        self._current_x = 0.0
        self._current_y = 0.0
    
    async def move_to(
        self,
        x: float,
        y: float,
        duration: float = 0.5,
        steps: int = 50,
        deviation: float = 0.2,
    ) -> None:
        """
        Move mouse to position with human-like motion.
        
        Args:
            x: Target X coordinate
            y: Target Y coordinate
            duration: Total movement time in seconds
            steps: Number of intermediate positions
            deviation: Curve deviation amount (0-1)
        """
        start = (self._current_x, self._current_y)
        end = (x, y)
        
        # Generate curved path
        control_points = generate_control_points(start, end, deviation)
        
        # Calculate timing with acceleration/deceleration
        step_delay = duration / steps
        
        for i in range(steps + 1):
            # Ease-out cubic for natural deceleration
            t = i / steps
            eased_t = 1 - (1 - t) ** 3
            
            # Get point on curve
            px, py = bezier_point(eased_t, control_points)
            
            # Add micro-jitter
            jitter = 0.5
            px += random.uniform(-jitter, jitter)
            py += random.uniform(-jitter, jitter)
            
            # Dispatch mouse move
            await self._cdp.send("Input.dispatchMouseEvent", {
                "type": "mouseMoved",
                "x": int(px),
                "y": int(py),
            })
            
            self._current_x = px
            self._current_y = py
            
            # Variable delay for realism
            delay = step_delay * random.uniform(0.8, 1.2)
            await asyncio.sleep(delay)
    
    async def click(
        self,
        x: Optional[float] = None,
        y: Optional[float] = None,
        button: str = "left",
        click_count: int = 1,
    ) -> None:
        """
        Click at position.
        
        Args:
            x: X coordinate (current position if None)
            y: Y coordinate (current position if None)
            button: 'left', 'right', or 'middle'
            click_count: Number of clicks
        """
        if x is not None and y is not None:
            await self.move_to(x, y)
        
        cx = x if x is not None else self._current_x
        cy = y if y is not None else self._current_y
        
        # Small delay before click
        await asyncio.sleep(random.uniform(0.03, 0.08))
        
        # Mouse down
        await self._cdp.send("Input.dispatchMouseEvent", {
            "type": "mousePressed",
            "x": int(cx),
            "y": int(cy),
            "button": button,
            "clickCount": click_count,
        })
        
        # Hold for realistic duration
        await asyncio.sleep(random.uniform(0.05, 0.12))
        
        # Mouse up
        await self._cdp.send("Input.dispatchMouseEvent", {
            "type": "mouseReleased",
            "x": int(cx),
            "y": int(cy),
            "button": button,
            "clickCount": click_count,
        })
    
    async def scroll(
        self,
        delta_x: int = 0,
        delta_y: int = 0,
        x: Optional[float] = None,
        y: Optional[float] = None,
    ) -> None:
        """
        Scroll with realistic behavior.
        
        Args:
            delta_x: Horizontal scroll amount
            delta_y: Vertical scroll amount (positive = down)
            x: X position for scroll
            y: Y position for scroll
        """
        cx = x if x is not None else self._current_x
        cy = y if y is not None else self._current_y
        
        # Scroll in smaller increments for realism
        remaining_y = delta_y
        remaining_x = delta_x
        
        while abs(remaining_y) > 20 or abs(remaining_x) > 20:
            # Scroll a random portion
            chunk_y = int(remaining_y * random.uniform(0.2, 0.4))
            chunk_x = int(remaining_x * random.uniform(0.2, 0.4))
            
            if chunk_y == 0 and remaining_y != 0:
                chunk_y = remaining_y
            if chunk_x == 0 and remaining_x != 0:
                chunk_x = remaining_x
            
            await self._cdp.send("Input.dispatchMouseEvent", {
                "type": "mouseWheel",
                "x": int(cx),
                "y": int(cy),
                "deltaX": chunk_x,
                "deltaY": chunk_y,
            })
            
            remaining_y -= chunk_y
            remaining_x -= chunk_x
            
            await asyncio.sleep(random.uniform(0.02, 0.05))
        
        # Final scroll
        if remaining_y != 0 or remaining_x != 0:
            await self._cdp.send("Input.dispatchMouseEvent", {
                "type": "mouseWheel",
                "x": int(cx),
                "y": int(cy),
                "deltaX": remaining_x,
                "deltaY": remaining_y,
            })
    
    @property
    def position(self) -> Tuple[float, float]:
        """Get current mouse position."""
        return (self._current_x, self._current_y)

