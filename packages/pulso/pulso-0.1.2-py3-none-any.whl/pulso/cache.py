"""Cache management with hash-based storage."""

import hashlib
import json
import os
import platform
import time
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import urlparse

try:
    from .config import config
except ImportError:
    config = None


class CacheEntry:
    """A single cache entry with metadata."""

    def __init__(
        self,
        url: str,
        html: str,
        content_hash: str,
        fetch_time: float,
        change_time: float,
        change_count: int = 0
    ):
        self.url = url
        self.html = html
        self.content_hash = content_hash
        self.fetch_time = fetch_time
        self.change_time = change_time
        self.change_count = change_count

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "url": self.url,
            "content_hash": self.content_hash,
            "fetch_time": self.fetch_time,
            "change_time": self.change_time,
            "change_count": self.change_count
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], html: str) -> "CacheEntry":
        """Create from dictionary."""
        return cls(
            url=data["url"],
            html=html,
            content_hash=data["content_hash"],
            fetch_time=data["fetch_time"],
            change_time=data["change_time"],
            change_count=data.get("change_count", 0)
        )


class CacheManager:
    """Manages cache storage and retrieval."""

    def __init__(self, session_id: Optional[str] = None):
        self._session_id = session_id
        self.cache_dir = self._get_cache_dir()
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_dir(self) -> Path:
        """Get platform-specific cache directory with session support."""
        # Check for custom cache directory from config
        if config and config.cache_dir:
            base_dir = config.cache_dir
        else:
            # Use platform defaults
            system = platform.system()
            if system == "Windows":
                base = Path(os.environ.get("LOCALAPPDATA", "~"))
                base_dir = (base / "pulso").expanduser()
            else:
                base = Path.home() / ".cache"
                base_dir = base / "pulso"

        # Apply session if configured
        if config and config.session_id != "default":
            return base_dir / "sessions" / config.session_id
        elif self._session_id:
            return base_dir / "sessions" / self._session_id

        return base_dir

    def _normalize_html(self, html: str) -> str:
        """Normalize HTML for hashing."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, 'lxml')

        # Remove script and style tags
        for tag in soup(['script', 'style']):
            tag.decompose()

        # Get text and normalize whitespace
        text = soup.get_text()
        normalized = ' '.join(text.split())

        return normalized

    def _compute_hash(self, html: str) -> str:
        """Compute hash of normalized HTML content."""
        normalized = self._normalize_html(html)
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

    def _url_to_path(self, url: str) -> Path:
        """Convert URL to cache file path."""
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path.split('/')[0]

        # Create URL hash for filename
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()

        domain_dir = self.cache_dir / domain
        domain_dir.mkdir(parents=True, exist_ok=True)

        return domain_dir / f"{url_hash}.json"

    def _html_path(self, url: str) -> Path:
        """Get path for HTML content storage."""
        cache_path = self._url_to_path(url)
        return cache_path.with_suffix('.html')

    def get(self, url: str) -> Optional[CacheEntry]:
        """Get cache entry for URL."""
        cache_path = self._url_to_path(url)
        html_path = self._html_path(url)

        if not cache_path.exists() or not html_path.exists():
            return None

        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            with open(html_path, 'r', encoding='utf-8') as f:
                html = f.read()

            return CacheEntry.from_dict(data, html)
        except (json.JSONDecodeError, IOError):
            return None

    def set(self, url: str, html: str, previous_entry: Optional[CacheEntry] = None) -> CacheEntry:
        """Store cache entry for URL."""
        content_hash = self._compute_hash(html)
        current_time = time.time()

        # Determine if content changed
        if previous_entry and previous_entry.content_hash == content_hash:
            # No change, update fetch time only
            entry = CacheEntry(
                url=url,
                html=html,
                content_hash=content_hash,
                fetch_time=current_time,
                change_time=previous_entry.change_time,
                change_count=previous_entry.change_count
            )
        else:
            # Content changed or new entry
            change_count = previous_entry.change_count + 1 if previous_entry else 1
            entry = CacheEntry(
                url=url,
                html=html,
                content_hash=content_hash,
                fetch_time=current_time,
                change_time=current_time,
                change_count=change_count
            )

        # Write metadata
        cache_path = self._url_to_path(url)
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(entry.to_dict(), f, indent=2)

        # Write HTML content
        html_path = self._html_path(url)
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)

        return entry

    def is_fresh(self, url: str, ttl_seconds: int) -> bool:
        """Check if cached entry is still fresh."""
        entry = self.get(url)
        if not entry:
            return False

        age = time.time() - entry.fetch_time
        return age < ttl_seconds

    def has_changed(self, url: str, current_hash: str) -> bool:
        """Check if content hash has changed."""
        entry = self.get(url)
        if not entry:
            return True

        return entry.content_hash != current_hash

    def clear(self, domain: Optional[str] = None, url: Optional[str] = None) -> None:
        """Clear cache entries.

        Args:
            domain: Clear all entries for a domain
            url: Clear specific URL entry
        """
        if url:
            # Clear specific URL
            cache_path = self._url_to_path(url)
            html_path = self._html_path(url)
            cache_path.unlink(missing_ok=True)
            html_path.unlink(missing_ok=True)
        elif domain:
            # Clear domain directory
            domain_dir = self.cache_dir / domain
            if domain_dir.exists():
                import shutil
                shutil.rmtree(domain_dir)
        else:
            # Clear entire cache
            if self.cache_dir.exists():
                import shutil
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(parents=True, exist_ok=True)

    def snapshot(self, url: str, snapshot_dir: Optional[Path] = None) -> Optional[Path]:
        """Create a snapshot of the current HTML.

        Args:
            url: URL to snapshot
            snapshot_dir: Optional directory for snapshots (defaults to cache_dir/snapshots)

        Returns:
            Path to snapshot file if successful
        """
        entry = self.get(url)
        if not entry:
            return None

        if snapshot_dir is None:
            snapshot_dir = self.cache_dir / "snapshots"

        snapshot_dir.mkdir(parents=True, exist_ok=True)

        timestamp = int(time.time())
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()[:8]
        snapshot_path = snapshot_dir / f"{url_hash}_{timestamp}.html"

        with open(snapshot_path, 'w', encoding='utf-8') as f:
            f.write(entry.html)

        return snapshot_path


# Global cache instance
cache = CacheManager()
