"""
GDNox - Undetectable Browser Automation Library

A self-contained stealth browser automation library with:
- CDP Direct communication (no WebDriver)
- Closed Shadow Root access
- Human-like behavior simulation
- Bot detection evasion
"""

from GDNox.core.browser import Browser
from GDNox.core.tab import Tab
from GDNox.core.element import Element

__version__ = "0.1.0"
__all__ = ["Browser", "Tab", "Element"]
