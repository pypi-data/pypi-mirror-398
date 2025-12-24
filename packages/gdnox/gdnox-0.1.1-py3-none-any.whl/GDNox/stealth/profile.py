"""
Profile - Browser profile management for stealth operation.

Provides:
- History pre-seeding (SQLite)
- Cookie injection
- Local storage injection
- Session simulation
"""

import json
import logging
import os
import random
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# Common sites to seed in history for realistic profile (BR + US)
DEFAULT_HISTORY_SITES = [
    # Global / US sites
    ("https://www.google.com/", "Google", 50),
    ("https://www.youtube.com/", "YouTube", 45),
    ("https://www.gmail.com/", "Gmail", 30),
    ("https://www.facebook.com/", "Facebook", 20),
    ("https://twitter.com/", "X", 15),
    ("https://www.reddit.com/", "Reddit", 18),
    ("https://www.amazon.com/", "Amazon", 15),
    ("https://www.wikipedia.org/", "Wikipedia", 20),
    ("https://www.linkedin.com/", "LinkedIn", 10),
    ("https://www.instagram.com/", "Instagram", 25),
    ("https://github.com/", "GitHub", 20),
    ("https://stackoverflow.com/", "Stack Overflow", 15),
    ("https://www.netflix.com/", "Netflix", 12),
    ("https://www.twitch.tv/", "Twitch", 10),
    ("https://discord.com/", "Discord", 15),
    ("https://www.tiktok.com/", "TikTok", 18),
    ("https://www.spotify.com/", "Spotify", 10),
    ("https://www.microsoft.com/", "Microsoft", 8),
    ("https://www.apple.com/", "Apple", 6),
    ("https://www.ebay.com/", "eBay", 5),
    ("https://www.yahoo.com/", "Yahoo", 8),
    ("https://www.bing.com/", "Bing", 5),
    ("https://www.cnn.com/", "CNN", 6),
    ("https://www.nytimes.com/", "The New York Times", 5),
    # Brazil sites
    ("https://www.google.com.br/", "Google Brasil", 40),
    ("https://www.uol.com.br/", "UOL", 15),
    ("https://www.globo.com/", "Globo", 18),
    ("https://www.mercadolivre.com.br/", "Mercado Livre", 12),
    ("https://www.magazineluiza.com.br/", "Magazine Luiza", 8),
    ("https://www.americanas.com.br/", "Americanas", 6),
    ("https://www.olx.com.br/", "OLX Brasil", 5),
    ("https://www.ifood.com.br/", "iFood", 10),
    ("https://www.nubank.com.br/", "Nubank", 8),
    ("https://www.itau.com.br/", "Itaú", 5),
    ("https://www.bradesco.com.br/", "Bradesco", 4),
    ("https://www.terra.com.br/", "Terra", 6),
    ("https://www.r7.com/", "R7", 5),
    ("https://www.cartola.globo.com/", "Cartola FC", 4),
    ("https://ge.globo.com/", "ge - Globo Esporte", 10),
    ("https://www.letras.mus.br/", "Letras", 5),
]


class ProfileManager:
    """
    Manages browser profiles for stealth operation.
    
    Usage:
        # Create profile with pre-seeded data
        profile = ProfileManager("/path/to/profile")
        profile.seed_history()
        profile.seed_cookies()
        
        # Use with browser
        async with Browser(user_data_dir="/path/to/profile") as browser:
            ...
    """
    
    def __init__(self, profile_dir: str):
        """
        Initialize profile manager.
        
        Args:
            profile_dir: Path to Chrome profile directory
        """
        self.profile_dir = Path(profile_dir)
        self.default_dir = self.profile_dir / "Default"
        
        # Ensure directories exist
        self.default_dir.mkdir(parents=True, exist_ok=True)
    
    def seed_history(
        self,
        sites: Optional[List[tuple]] = None,
        days_back: int = 30,
    ) -> None:
        """
        Pre-seed browser history with realistic browsing data.
        
        Args:
            sites: List of (url, title, visit_count) tuples
            days_back: How many days back to distribute visits
        """
        sites = sites or DEFAULT_HISTORY_SITES
        history_db = self.default_dir / "History"
        
        # Create history database
        conn = sqlite3.connect(str(history_db))
        cursor = conn.cursor()
        
        # Create tables (Chrome schema)
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                title TEXT,
                visit_count INTEGER DEFAULT 0,
                typed_count INTEGER DEFAULT 0,
                last_visit_time INTEGER DEFAULT 0,
                hidden INTEGER DEFAULT 0
            );
            
            CREATE TABLE IF NOT EXISTS visits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url INTEGER NOT NULL,
                visit_time INTEGER NOT NULL,
                from_visit INTEGER DEFAULT 0,
                transition INTEGER DEFAULT 0,
                segment_id INTEGER DEFAULT 0,
                visit_duration INTEGER DEFAULT 0,
                incremented_omnibox_typed_score INTEGER DEFAULT 0
            );
            
            CREATE INDEX IF NOT EXISTS urls_url_index ON urls (url);
            CREATE INDEX IF NOT EXISTS visits_url_index ON visits (url);
            CREATE INDEX IF NOT EXISTS visits_time_index ON visits (visit_time);
        """)
        
        # Chrome time format: microseconds since Windows epoch (1601-01-01)
        WINDOWS_EPOCH_OFFSET = 11644473600  # Seconds from Windows to Unix epoch
        
        def to_chrome_time(unix_timestamp: float) -> int:
            return int((unix_timestamp + WINDOWS_EPOCH_OFFSET) * 1000000)
        
        now = time.time()
        
        for url, title, visit_count in sites:
            # Add some randomness to visit count
            visits = max(1, visit_count + random.randint(-5, 5))
            
            # Calculate last visit time (within last few days)
            last_visit_offset = random.uniform(0, days_back * 24 * 3600)
            last_visit = to_chrome_time(now - last_visit_offset)
            
            # Insert URL entry
            cursor.execute("""
                INSERT OR REPLACE INTO urls (url, title, visit_count, typed_count, last_visit_time)
                VALUES (?, ?, ?, ?, ?)
            """, (url, title, visits, visits // 3, last_visit))
            
            url_id = cursor.lastrowid
            
            # Insert individual visits
            for i in range(visits):
                visit_offset = random.uniform(0, days_back * 24 * 3600)
                visit_time = to_chrome_time(now - visit_offset)
                visit_duration = random.randint(10000000, 300000000)  # 10s to 5min
                
                cursor.execute("""
                    INSERT INTO visits (url, visit_time, transition, visit_duration)
                    VALUES (?, ?, ?, ?)
                """, (url_id, visit_time, 805306368, visit_duration))  # 805306368 = LINK transition
        
        conn.commit()
        conn.close()
        
        logger.info(f"Seeded history with {len(sites)} sites in {history_db}")
    
    def seed_cookies(
        self,
        cookies: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """
        Pre-seed cookies for common sites.
        
        Args:
            cookies: List of cookie dicts with name, value, domain, etc.
        """
        if cookies is None:
            cookies = self._generate_default_cookies()
        
        cookies_db = self.default_dir / "Cookies"
        
        conn = sqlite3.connect(str(cookies_db))
        cursor = conn.cursor()
        
        # Create cookies table (Chrome schema)
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS cookies (
                creation_utc INTEGER NOT NULL,
                host_key TEXT NOT NULL,
                top_frame_site_key TEXT NOT NULL,
                name TEXT NOT NULL,
                value TEXT NOT NULL,
                encrypted_value BLOB DEFAULT '',
                path TEXT NOT NULL,
                expires_utc INTEGER NOT NULL,
                is_secure INTEGER NOT NULL,
                is_httponly INTEGER NOT NULL,
                last_access_utc INTEGER NOT NULL,
                has_expires INTEGER NOT NULL DEFAULT 1,
                is_persistent INTEGER NOT NULL DEFAULT 1,
                priority INTEGER NOT NULL DEFAULT 1,
                samesite INTEGER NOT NULL DEFAULT -1,
                source_scheme INTEGER NOT NULL DEFAULT 0,
                source_port INTEGER NOT NULL DEFAULT -1,
                last_update_utc INTEGER NOT NULL DEFAULT 0,
                source_type INTEGER NOT NULL DEFAULT 0,
                has_cross_site_ancestor INTEGER NOT NULL DEFAULT 0,
                UNIQUE (host_key, top_frame_site_key, name, path, source_scheme, source_port)
            );
        """)
        
        now = int(time.time() * 1000000) + 11644473600000000
        one_year = 365 * 24 * 3600 * 1000000
        
        for cookie in cookies:
            cursor.execute("""
                INSERT OR REPLACE INTO cookies (
                    creation_utc, host_key, top_frame_site_key, name, value,
                    path, expires_utc, is_secure, is_httponly, last_access_utc,
                    has_expires, is_persistent, priority, samesite, source_scheme
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                now - random.randint(0, 30 * 24 * 3600 * 1000000),  # creation_utc
                cookie.get("domain", ""),
                "",
                cookie.get("name", ""),
                cookie.get("value", ""),
                cookie.get("path", "/"),
                now + one_year,
                1 if cookie.get("secure", True) else 0,
                1 if cookie.get("httpOnly", True) else 0,
                now,
                1, 1, 1, -1, 2
            ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Seeded {len(cookies)} cookies in {cookies_db}")
    
    def _generate_default_cookies(self) -> List[Dict[str, Any]]:
        """Generate realistic default cookies for US and Brazil sites."""
        cookies = []
        
        # Google cookies (not logged in, but with tracking)
        cookies.extend([
            {"domain": ".google.com", "name": "NID", "value": self._random_hex(67), "path": "/", "secure": True, "httpOnly": True},
            {"domain": ".google.com", "name": "1P_JAR", "value": f"2024-12-{random.randint(1, 20):02d}-{random.randint(0, 23):02d}", "path": "/", "secure": True, "httpOnly": False},
            {"domain": ".google.com", "name": "AEC", "value": self._random_base64(76), "path": "/", "secure": True, "httpOnly": True},
            {"domain": ".google.com", "name": "_GRECAPTCHA", "value": f"09{self._random_hex(126)}", "path": "/recaptcha", "secure": True, "httpOnly": True},
            {"domain": ".google.com.br", "name": "NID", "value": self._random_hex(67), "path": "/", "secure": True, "httpOnly": True},
        ])
        
        # YouTube cookies
        cookies.extend([
            {"domain": ".youtube.com", "name": "PREF", "value": f"f6=40000000&tz=America.Sao_Paulo&f5=30000", "path": "/", "secure": True, "httpOnly": False},
            {"domain": ".youtube.com", "name": "VISITOR_INFO1_LIVE", "value": self._random_base64(11), "path": "/", "secure": True, "httpOnly": True},
            {"domain": ".youtube.com", "name": "YSC", "value": self._random_base64(11), "path": "/", "secure": True, "httpOnly": True},
        ])
        
        # Facebook cookies
        cookies.extend([
            {"domain": ".facebook.com", "name": "datr", "value": self._random_base64(24), "path": "/", "secure": True, "httpOnly": True},
            {"domain": ".facebook.com", "name": "sb", "value": self._random_base64(24), "path": "/", "secure": True, "httpOnly": True},
            {"domain": ".facebook.com", "name": "fr", "value": self._random_hex(42), "path": "/", "secure": True, "httpOnly": True},
        ])
        
        # Twitter/X cookies
        cookies.extend([
            {"domain": ".twitter.com", "name": "guest_id", "value": f"v1%3A{self._random_hex(19)}", "path": "/", "secure": True, "httpOnly": False},
            {"domain": ".twitter.com", "name": "ct0", "value": self._random_hex(32), "path": "/", "secure": True, "httpOnly": False},
            {"domain": ".x.com", "name": "guest_id", "value": f"v1%3A{self._random_hex(19)}", "path": "/", "secure": True, "httpOnly": False},
        ])
        
        # Reddit cookies
        cookies.extend([
            {"domain": ".reddit.com", "name": "session_tracker", "value": self._random_base64(32), "path": "/", "secure": True, "httpOnly": False},
            {"domain": ".reddit.com", "name": "csv", "value": "2", "path": "/", "secure": True, "httpOnly": False},
        ])
        
        # Amazon cookies (US and BR)
        cookies.extend([
            {"domain": ".amazon.com", "name": "session-id", "value": f"{random.randint(100, 999)}-{random.randint(1000000, 9999999)}-{random.randint(1000000, 9999999)}", "path": "/", "secure": True, "httpOnly": False},
            {"domain": ".amazon.com", "name": "ubid-main", "value": f"{random.randint(100, 999)}-{random.randint(1000000, 9999999)}-{random.randint(1000000, 9999999)}", "path": "/", "secure": True, "httpOnly": False},
            {"domain": ".amazon.com.br", "name": "session-id", "value": f"{random.randint(100, 999)}-{random.randint(1000000, 9999999)}-{random.randint(1000000, 9999999)}", "path": "/", "secure": True, "httpOnly": False},
        ])
        
        # Netflix cookies
        cookies.extend([
            {"domain": ".netflix.com", "name": "memclid", "value": self._random_hex(32), "path": "/", "secure": True, "httpOnly": False},
            {"domain": ".netflix.com", "name": "flwssn", "value": self._random_hex(32), "path": "/", "secure": True, "httpOnly": False},
        ])
        
        # Instagram cookies
        cookies.extend([
            {"domain": ".instagram.com", "name": "csrftoken", "value": self._random_hex(32), "path": "/", "secure": True, "httpOnly": False},
            {"domain": ".instagram.com", "name": "mid", "value": self._random_base64(27), "path": "/", "secure": True, "httpOnly": False},
            {"domain": ".instagram.com", "name": "ig_did", "value": self._random_hex(36), "path": "/", "secure": True, "httpOnly": True},
        ])
        
        # TikTok cookies
        cookies.extend([
            {"domain": ".tiktok.com", "name": "ttwid", "value": self._random_base64(60), "path": "/", "secure": True, "httpOnly": True},
            {"domain": ".tiktok.com", "name": "tt_csrf_token", "value": self._random_hex(16), "path": "/", "secure": True, "httpOnly": False},
        ])
        
        # LinkedIn cookies
        cookies.extend([
            {"domain": ".linkedin.com", "name": "bcookie", "value": f'"v=2&{self._random_hex(32)}"', "path": "/", "secure": True, "httpOnly": False},
            {"domain": ".linkedin.com", "name": "bscookie", "value": f'"v=1&{self._random_hex(64)}"', "path": "/", "secure": True, "httpOnly": True},
        ])
        
        # Brazil sites - Mercado Livre
        cookies.extend([
            {"domain": ".mercadolivre.com.br", "name": "_d2id", "value": self._random_hex(36), "path": "/", "secure": True, "httpOnly": False},
        ])
        
        # Brazil sites - Globo
        cookies.extend([
            {"domain": ".globo.com", "name": "GLBID", "value": self._random_hex(32), "path": "/", "secure": True, "httpOnly": True},
        ])
        
        # Brazil sites - UOL
        cookies.extend([
            {"domain": ".uol.com.br", "name": "uolId", "value": self._random_hex(24), "path": "/", "secure": True, "httpOnly": False},
        ])
        
        return cookies
    
    def _random_hex(self, length: int) -> str:
        """Generate random hex string."""
        import secrets
        return secrets.token_hex(length // 2 + 1)[:length]
    
    def _random_base64(self, length: int) -> str:
        """Generate random base64-like string."""
        import secrets
        import base64
        return base64.urlsafe_b64encode(secrets.token_bytes(length)).decode()[:length]
    
    def seed_local_storage(
        self,
        data: Optional[Dict[str, Dict[str, str]]] = None,
    ) -> None:
        """
        Pre-seed local storage for common sites.
        
        Args:
            data: Dict of {origin: {key: value, ...}}
        """
        if data is None:
            data = self._generate_default_local_storage()
        
        local_storage_dir = self.default_dir / "Local Storage" / "leveldb"
        local_storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Note: Chrome uses LevelDB for local storage which is complex to write directly.
        # For now, we'll create a placeholder - the actual injection happens via CDP.
        logger.info(f"Local storage directory prepared: {local_storage_dir}")
    
    def _generate_default_local_storage(self) -> Dict[str, Dict[str, str]]:
        """Generate realistic default local storage."""
        return {
            "https://www.youtube.com": {
                "yt-player-volume": '{"data":"{\\"volume\\":100,\\"muted\\":false}","expiration":1735689600000,"creation":1703980800000}',
            },
            "https://www.google.com": {
                "_gads_sync": "accepted",
            },
        }
