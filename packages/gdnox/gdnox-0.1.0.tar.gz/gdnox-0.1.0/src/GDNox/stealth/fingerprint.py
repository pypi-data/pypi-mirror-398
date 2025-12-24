"""
Fingerprint Spoofing - Hide automation fingerprints.

Spoofs browser fingerprints to avoid detection:
- Canvas fingerprint
- WebGL fingerprint
- AudioContext fingerprint
- Navigator properties
"""

import logging
import random
from typing import Optional

from GDNox.core.cdp_client import CDPClient

logger = logging.getLogger(__name__)


# JavaScript to inject for fingerprint spoofing
FINGERPRINT_SPOOF_SCRIPT = """
(() => {
    // Store original values
    const originalGetContext = HTMLCanvasElement.prototype.getContext;
    const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
    const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
    
    // Canvas fingerprint noise
    const addNoise = (data) => {
        const noise = %NOISE_LEVEL%;
        for (let i = 0; i < data.length; i += 4) {
            // Add small random variations to RGB values
            data[i] = Math.max(0, Math.min(255, data[i] + (Math.random() * noise * 2 - noise)));
            data[i+1] = Math.max(0, Math.min(255, data[i+1] + (Math.random() * noise * 2 - noise)));
            data[i+2] = Math.max(0, Math.min(255, data[i+2] + (Math.random() * noise * 2 - noise)));
        }
        return data;
    };
    
    // Override getImageData
    CanvasRenderingContext2D.prototype.getImageData = function(x, y, w, h) {
        const imageData = originalGetImageData.call(this, x, y, w, h);
        addNoise(imageData.data);
        return imageData;
    };
    
    // Override toDataURL
    HTMLCanvasElement.prototype.toDataURL = function(type, quality) {
        const ctx = this.getContext('2d');
        if (ctx) {
            const imageData = originalGetImageData.call(ctx, 0, 0, this.width, this.height);
            addNoise(imageData.data);
            ctx.putImageData(imageData, 0, 0);
        }
        return originalToDataURL.call(this, type, quality);
    };
    
    // WebGL fingerprint spoofing
    const originalGetParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(param) {
        // UNMASKED_VENDOR_WEBGL
        if (param === 37445) {
            return '%WEBGL_VENDOR%';
        }
        // UNMASKED_RENDERER_WEBGL
        if (param === 37446) {
            return '%WEBGL_RENDERER%';
        }
        return originalGetParameter.call(this, param);
    };
    
    // WebGL2 spoofing
    if (typeof WebGL2RenderingContext !== 'undefined') {
        const originalGetParameter2 = WebGL2RenderingContext.prototype.getParameter;
        WebGL2RenderingContext.prototype.getParameter = function(param) {
            if (param === 37445) return '%WEBGL_VENDOR%';
            if (param === 37446) return '%WEBGL_RENDERER%';
            return originalGetParameter2.call(this, param);
        };
    }
    
    // Override navigator.webdriver
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined,
        configurable: true
    });
    
    // Delete webdriver property
    delete navigator.__proto__.webdriver;
    
    // Spoof plugins if empty
    if (navigator.plugins.length === 0) {
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
                { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
                { name: 'Native Client', filename: 'internal-nacl-plugin' },
            ],
            configurable: true
        });
    }
    
    // Spoof languages
    Object.defineProperty(navigator, 'languages', {
        get: () => ['%LANGUAGE%', '%LANGUAGE_SHORT%'],
        configurable: true
    });
    
    // Hide automation flags
    window.chrome = window.chrome || {};
    window.chrome.runtime = window.chrome.runtime || {};
    
    console.log('[gdnium] Fingerprint spoofing applied');
})();
"""


# Common WebGL vendor/renderer combinations
WEBGL_CONFIGS = [
    ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce GTX 1080 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (AMD)", "ANGLE (AMD, AMD Radeon RX 580 Series Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Google Inc. (Intel)", "ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0, D3D11)"),
    ("Intel Inc.", "Intel Iris OpenGL Engine"),
    ("ATI Technologies Inc.", "AMD Radeon Pro 5500M OpenGL Engine"),
]


class FingerprintSpoofer:
    """
    Applies fingerprint spoofing to avoid detection.
    
    Injects JavaScript to modify Canvas, WebGL, and other
    fingerprinting vectors.
    """
    
    def __init__(
        self,
        cdp: CDPClient,
        noise_level: int = 5,
        language: str = "en-US",
        webgl_config: Optional[tuple] = None,
    ):
        """
        Initialize fingerprint spoofer.
        
        Args:
            cdp: CDP client
            noise_level: Amount of canvas noise (1-10)
            language: Browser language
            webgl_config: (vendor, renderer) tuple, or random if None
        """
        self._cdp = cdp
        self.noise_level = max(1, min(10, noise_level))
        self.language = language
        
        if webgl_config:
            self.webgl_vendor, self.webgl_renderer = webgl_config
        else:
            self.webgl_vendor, self.webgl_renderer = random.choice(WEBGL_CONFIGS)
    
    async def apply(self, frame_id: str) -> None:
        """
        Apply fingerprint spoofing to a frame.
        
        Args:
            frame_id: Target frame ID
        """
        # Prepare the script with our values
        script = FINGERPRINT_SPOOF_SCRIPT
        script = script.replace("%NOISE_LEVEL%", str(self.noise_level))
        script = script.replace("%WEBGL_VENDOR%", self.webgl_vendor)
        script = script.replace("%WEBGL_RENDERER%", self.webgl_renderer)
        script = script.replace("%LANGUAGE%", self.language)
        script = script.replace("%LANGUAGE_SHORT%", self.language.split("-")[0])
        
        # Add script to run on page load
        await self._cdp.send("Page.addScriptToEvaluateOnNewDocument", {
            "source": script,
        })
        
        logger.info(f"Fingerprint spoofing applied (noise={self.noise_level})")
    
    async def apply_navigator_patches(self) -> None:
        """Apply navigator property patches."""
        # These patches hide automation indicators
        patches = """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        
        // Chrome runtime simulation
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {}
        };
        
        // Permissions API
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        """
        
        await self._cdp.send("Page.addScriptToEvaluateOnNewDocument", {
            "source": patches,
        })
