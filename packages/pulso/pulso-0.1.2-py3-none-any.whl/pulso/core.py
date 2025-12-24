"""Core functions for stateful fetching."""

from typing import Optional
from pathlib import Path
import logging

from .cache import cache
from .domain import get_policy
from .fetcher import fetch_raw, FetchError


logger = logging.getLogger(__name__)


def fetch(url: str, force: bool = False) -> Optional[str]:
    """Fetch web content with caching and TTL.

    Args:
        url: URL to fetch
        force: Force refetch even if cached and fresh

    Returns:
        HTML content, or None if fetch fails and fallback_on_error='return_none'
    """
    policy = get_policy(url)

    # Check if we have fresh cache
    if not force and cache.is_fresh(url, policy.ttl_seconds):
        entry = cache.get(url)
        if entry:
            return entry.html

    # Need to fetch
    try:
        html = fetch_raw(url, driver=policy.driver, policy=policy)

        # Get previous entry for change tracking
        previous_entry = cache.get(url)

        # Update cache
        cache.set(url, html, previous_entry)

        return html

    except FetchError as e:
        # Handle fetch failure based on domain policy
        logger.error(f"Fetch failed for {url}: {e}")

        if policy.fallback_on_error == "return_cached":
            # Return cached data if available
            entry = cache.get(url)
            if entry:
                logger.info(f"Returning cached data for {url} (last fetch: {entry.fetch_time})")
                return entry.html
            else:
                logger.warning(f"No cached data available for {url}, raising error")
                raise

        elif policy.fallback_on_error == "return_none":
            logger.info(f"Returning None for {url} due to fetch error")
            return None

        else:  # raise_error
            raise


def has_changed(url: str) -> bool:
    """Check if content has changed since last fetch.

    This compares the content hash of the current cached version
    with a fresh fetch.

    Args:
        url: URL to check

    Returns:
        True if content has changed or URL not cached
    """
    policy = get_policy(url)

    # Get current cached entry
    cached_entry = cache.get(url)
    if not cached_entry:
        # No cache, so technically it has "changed" (or is new)
        return True

    # Fetch fresh content with error handling
    try:
        fresh_html = fetch_raw(url, policy=policy)
        fresh_hash = cache._compute_hash(fresh_html)

        # Compare hashes
        changed = cached_entry.content_hash != fresh_hash

        # Update cache with fresh content if changed
        if changed:
            cache.set(url, fresh_html, cached_entry)

        return changed

    except FetchError as e:
        logger.error(f"Failed to check if {url} changed: {e}")

        # If we can't fetch, assume no change (return cached data is still valid)
        if policy.fallback_on_error == "return_cached":
            logger.info(f"Assuming no change for {url} due to fetch error")
            return False
        elif policy.fallback_on_error == "return_none":
            return False
        else:  # raise_error
            raise


def snapshot(url: str, snapshot_dir: Optional[Path] = None) -> Optional[Path]:
    """Create a snapshot of the current cached HTML.

    Args:
        url: URL to snapshot
        snapshot_dir: Optional directory for snapshots

    Returns:
        Path to snapshot file if successful, None if URL not cached
    """
    return cache.snapshot(url, snapshot_dir)


def get_metadata(url: str) -> Optional[dict]:
    """Get metadata about a cached URL.

    Args:
        url: URL to get metadata for

    Returns:
        Dictionary with metadata or None if not cached
    """
    entry = cache.get(url)
    if not entry:
        return None

    return {
        "url": entry.url,
        "content_hash": entry.content_hash,
        "fetch_time": entry.fetch_time,
        "change_time": entry.change_time,
        "change_count": entry.change_count
    }
