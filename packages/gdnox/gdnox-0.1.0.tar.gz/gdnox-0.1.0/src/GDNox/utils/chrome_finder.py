"""
Chrome Finder - Locate Chrome/Chromium executable across platforms.
"""

import os
import platform
import subprocess
from pathlib import Path
from typing import Optional


def find_chrome() -> Optional[str]:
    """
    Find Chrome/Chromium executable on the system.
    
    Returns:
        Path to Chrome executable, or None if not found.
    """
    system = platform.system()
    
    if system == "Windows":
        return _find_chrome_windows()
    elif system == "Darwin":
        return _find_chrome_macos()
    else:
        return _find_chrome_linux()


def _find_chrome_windows() -> Optional[str]:
    """Find Chrome on Windows."""
    # Common Chrome installation paths
    paths = [
        os.path.join(os.environ.get("PROGRAMFILES", ""), "Google", "Chrome", "Application", "chrome.exe"),
        os.path.join(os.environ.get("PROGRAMFILES(X86)", ""), "Google", "Chrome", "Application", "chrome.exe"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "Application", "chrome.exe"),
        # Chromium
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Chromium", "Application", "chrome.exe"),
        # Edge (Chromium-based)
        os.path.join(os.environ.get("PROGRAMFILES(X86)", ""), "Microsoft", "Edge", "Application", "msedge.exe"),
        os.path.join(os.environ.get("PROGRAMFILES", ""), "Microsoft", "Edge", "Application", "msedge.exe"),
    ]
    
    for path in paths:
        if os.path.exists(path):
            return path
    
    return None


def _find_chrome_macos() -> Optional[str]:
    """Find Chrome on macOS."""
    paths = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
    ]
    
    for path in paths:
        if os.path.exists(path):
            return path
    
    return None


def _find_chrome_linux() -> Optional[str]:
    """Find Chrome on Linux."""
    # Try common executable names
    names = [
        "google-chrome",
        "google-chrome-stable",
        "chromium",
        "chromium-browser",
        "chrome",
    ]
    
    for name in names:
        try:
            result = subprocess.run(
                ["which", name],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
    
    # Check common paths
    paths = [
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        "/snap/bin/chromium",
    ]
    
    for path in paths:
        if os.path.exists(path):
            return path
    
    return None


def get_chrome_version(chrome_path: str) -> Optional[str]:
    """
    Get Chrome version string.
    
    Args:
        chrome_path: Path to Chrome executable
        
    Returns:
        Version string (e.g., "120.0.6099.109") or None
    """
    try:
        result = subprocess.run(
            [chrome_path, "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            # Output is like "Google Chrome 120.0.6099.109" or "Chromium 120.0..."
            version = result.stdout.strip().split()[-1]
            return version
    except Exception:
        pass
    
    return None
