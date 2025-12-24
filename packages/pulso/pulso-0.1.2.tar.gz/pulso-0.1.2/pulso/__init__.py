"""Pulso - Stateful web fetching with cache, hashes, and domain-aware rules."""

__version__ = "0.1.0"

from .core import fetch, has_changed, snapshot, get_metadata
from .domain import register_domain, get_registered_domains
from .cache import cache
from .fetcher import FetchError
from .config import set_session, get_session, load_config

__all__ = [
    "fetch",
    "has_changed",
    "snapshot",
    "get_metadata",
    "register_domain",
    "get_registered_domains",
    "cache",
    "FetchError",
    "set_session",
    "get_session",
    "load_config",
]
