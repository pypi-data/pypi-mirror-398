"""
Browser - Main browser controller for Gdnium.

Handles:
- Launching Chrome with proper flags
- Managing browser process
- Creating new tabs
- Cleanup on exit
"""

import asyncio
import json
import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
import aiohttp

from GDNox.core.cdp_client import CDPClient
from GDNox.core.tab import Tab
from GDNox.utils.chrome_finder import find_chrome, get_chrome_version

logger = logging.getLogger(__name__)


# Chrome flags for stealth operation
STEALTH_FLAGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-infobars",
    "--disable-extensions",
    "--disable-popup-blocking",
    "--disable-background-networking",
    "--disable-sync",
    "--disable-translate",
    "--metrics-recording-only",
    "--safebrowsing-disable-auto-update",
    "--disable-component-update",
    "--disable-default-apps",
    "--disable-domain-reliability",
    "--disable-features=AutofillServerCommunication",
    # WebRTC leak prevention - important for proxy usage
    "--disable-webrtc",
    "--webrtc-ip-handling-policy=disable_non_proxied_udp",
    "--force-webrtc-ip-handling-policy",
]


class BrowserError(Exception):
    """Browser launch/operation error."""
    pass


class Browser:
    """
    Main browser controller.
    
    Usage:
        async with Browser() as browser:
            tab = await browser.new_tab()
            await tab.goto("https://example.com")
    """
    
    def __init__(
        self,
        chrome_path: Optional[str] = None,
        headless: bool = False,
        user_data_dir: Optional[str] = None,
        proxy: Optional[str] = None,
        extra_args: Optional[List[str]] = None,
        auto_seed: bool = True,
    ):
        """
        Initialize browser.
        
        Args:
            chrome_path: Path to Chrome. Auto-detected if not provided.
            headless: Run in headless mode. NOT recommended for stealth.
            user_data_dir: Chrome profile directory. Temp dir used if not provided.
            proxy: Proxy server (e.g., "http://user:pass@127.0.0.1:8080")
            extra_args: Additional Chrome command line arguments
            auto_seed: Automatically seed history and cookies for stealth (default: True)
        """
        self.chrome_path = chrome_path or find_chrome()
        if not self.chrome_path:
            raise BrowserError("Could not find Chrome. Please install Chrome or provide path.")
        
        self.headless = headless
        self.user_data_dir = user_data_dir
        self.extra_args = extra_args or []
        self.auto_seed = auto_seed
        
        # Parse proxy credentials
        self.proxy = proxy
        self.proxy_auth: Optional[tuple] = None  # (username, password)
        if proxy:
            self._parse_proxy(proxy)
        
        self._process: Optional[subprocess.Popen] = None
        self._temp_dir: Optional[str] = None
        self._debug_port: int = 0
        self._ws_endpoint: Optional[str] = None
        self._cdp_client: Optional[CDPClient] = None
        self._tabs: List[Tab] = []
    
    def _parse_proxy(self, proxy: str) -> None:
        """Parse proxy URL and extract credentials if present."""
        from urllib.parse import urlparse
        
        parsed = urlparse(proxy)
        
        if parsed.username and parsed.password:
            self.proxy_auth = (parsed.username, parsed.password)
            # Rebuild proxy URL without credentials for Chrome flag
            if parsed.port:
                self.proxy = f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"
            else:
                self.proxy = f"{parsed.scheme}://{parsed.hostname}"
            logger.debug(f"Proxy with auth: {self.proxy} (user: {parsed.username})")
        else:
            self.proxy = proxy
    
    async def launch(self) -> None:
        """Launch Chrome browser."""
        if self._process is not None:
            return
        
        # Create temp profile if needed
        if not self.user_data_dir:
            self._temp_dir = tempfile.mkdtemp(prefix="gdnium_")
            self.user_data_dir = self._temp_dir
        
        # Auto-seed profile for stealth (only for new profiles)
        if self.auto_seed and self._temp_dir:
            self._seed_profile()
        
        # Find available port
        self._debug_port = await self._find_free_port()
        
        # Build command
        cmd = [self.chrome_path]
        cmd.extend(STEALTH_FLAGS)
        cmd.append(f"--remote-debugging-port={self._debug_port}")
        cmd.append(f"--user-data-dir={self.user_data_dir}")
        
        if self.headless:
            cmd.append("--headless=new")
        
        if self.proxy:
            cmd.append(f"--proxy-server={self.proxy}")
        
        cmd.extend(self.extra_args)
        cmd.append("about:blank")
        
        logger.debug(f"Launching Chrome: {' '.join(cmd)}")
        
        # Launch process
        self._process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        
        # Wait for debug endpoint
        self._ws_endpoint = await self._get_ws_endpoint()
        
        logger.info(f"Chrome launched (PID: {self._process.pid}, port: {self._debug_port})")
    
    async def close(self) -> None:
        """Close browser and cleanup."""
        # Close all tabs
        for tab in self._tabs:
            await tab.close()
        self._tabs.clear()
        
        # Close CDP client
        if self._cdp_client:
            await self._cdp_client.disconnect()
            self._cdp_client = None
        
        # Terminate process
        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=5)
            except Exception:
                self._process.kill()
            self._process = None
        
        # Cleanup temp directory
        if self._temp_dir and os.path.exists(self._temp_dir):
            try:
                shutil.rmtree(self._temp_dir)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp dir: {e}")
            self._temp_dir = None
        
        logger.info("Browser closed")
    
    async def new_tab(self, url: str = "about:blank") -> Tab:
        """
        Create a new tab.
        
        Args:
            url: Initial URL to navigate to
            
        Returns:
            Tab instance
        """
        if not self._process:
            await self.launch()
        
        # Create new target via CDP
        async with aiohttp.ClientSession() as session:
            async with session.put(
                f"http://127.0.0.1:{self._debug_port}/json/new?{url}"
            ) as resp:
                target_info = await resp.json()
        
        ws_url = target_info.get("webSocketDebuggerUrl")
        if not ws_url:
            raise BrowserError("Failed to get WebSocket URL for new tab")
        
        tab = Tab(ws_url, target_info, proxy_auth=self.proxy_auth)
        await tab.connect()
        self._tabs.append(tab)
        
        return tab
    
    async def get_tabs(self) -> List[Dict[str, Any]]:
        """Get list of all open tabs/targets."""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"http://127.0.0.1:{self._debug_port}/json"
            ) as resp:
                return await resp.json()
    
    async def _find_free_port(self) -> int:
        """Find an available port."""
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]
    
    async def _get_ws_endpoint(self, timeout: float = 30.0) -> str:
        """Wait for and get the WebSocket debug endpoint."""
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"http://127.0.0.1:{self._debug_port}/json/version"
                    ) as resp:
                        data = await resp.json()
                        return data.get("webSocketDebuggerUrl", "")
            except Exception:
                await asyncio.sleep(0.2)
        
        raise BrowserError("Timeout waiting for Chrome to start")
    
    def _seed_profile(self) -> None:
        """Seed browser profile with realistic history and cookies for stealth."""
        try:
            from GDNox.stealth.profile import ProfileManager
            
            profile = ProfileManager(self.user_data_dir)
            profile.seed_history()
            profile.seed_cookies()
            
            logger.debug(f"Profile seeded: {self.user_data_dir}")
        except Exception as e:
            logger.warning(f"Failed to seed profile: {e}")
    
    async def __aenter__(self) -> "Browser":
        await self.launch()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()
