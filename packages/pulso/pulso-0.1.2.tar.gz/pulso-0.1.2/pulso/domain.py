"""Domain registration and policy management."""

from typing import Dict, Optional, Literal, Callable
from urllib.parse import urlparse
import re
import logging


DriverType = Literal["requests", "playwright"]
FallbackBehavior = Literal["return_cached", "raise_error", "return_none"]

logger = logging.getLogger(__name__)


class DomainPolicy:
    """Domain-specific policy for fetching and caching."""

    def __init__(
        self,
        domain: str,
        ttl: str = "1d",
        driver: DriverType = "requests",
        max_retries: int = 3,
        retry_delay: float = 1.0,
        fallback_on_error: FallbackBehavior = "return_cached",
        on_error: Optional[Callable[[str, Exception], None]] = None
    ):
        self.domain = domain
        self.ttl_seconds = self._parse_ttl(ttl)
        self.driver = driver
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.fallback_on_error = fallback_on_error
        self.on_error = on_error

    def _parse_ttl(self, ttl: str) -> int:
        """Parse TTL string like '1d', '12h', '30m' to seconds."""
        match = re.match(r'^(\d+)([smhd])$', ttl.lower())
        if not match:
            raise ValueError(f"Invalid TTL format: {ttl}. Use format like '1d', '12h', '30m'")

        value, unit = match.groups()
        value = int(value)

        multipliers = {
            's': 1,
            'm': 60,
            'h': 3600,
            'd': 86400
        }

        return value * multipliers[unit]


class DomainRegistry:
    """Registry for domain-specific policies."""

    def __init__(self):
        self._domains: Dict[str, DomainPolicy] = {}
        self._default_policy = DomainPolicy(
            "*",
            ttl="1d",
            driver="requests",
            fallback_on_error="return_cached"
        )

    def register(
        self,
        domain: str,
        ttl: str = "1d",
        driver: DriverType = "requests",
        max_retries: int = 3,
        retry_delay: float = 1.0,
        fallback_on_error: FallbackBehavior = "return_cached",
        on_error: Optional[Callable[[str, Exception], None]] = None
    ) -> None:
        """Register a domain with its policy."""
        policy = DomainPolicy(
            domain,
            ttl,
            driver,
            max_retries,
            retry_delay,
            fallback_on_error,
            on_error
        )
        self._domains[domain] = policy

    def get_policy(self, url: str) -> DomainPolicy:
        """Get policy for a URL."""
        domain = self._extract_domain(url)
        return self._domains.get(domain, self._default_policy)

    def get_all_domains(self) -> Dict[str, DomainPolicy]:
        """Get all registered domains.

        Returns:
            Dictionary mapping domain names to their policies
        """
        return self._domains.copy()

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        parsed = urlparse(url)
        return parsed.netloc or parsed.path


# Global registry
_registry = DomainRegistry()


def register_domain(
    domain: str,
    ttl: str = "1d",
    driver: DriverType = "requests",
    max_retries: int = 3,
    retry_delay: float = 1.0,
    fallback_on_error: FallbackBehavior = "return_cached",
    on_error: Optional[Callable[[str, Exception], None]] = None
) -> None:
    """Register a domain with fetching and caching policy.

    Args:
        domain: Domain name (e.g., 'example.com')
        ttl: Time-to-live for cache (e.g., '1d', '12h', '30m')
        driver: Fetch driver to use ('requests' or 'playwright')
        max_retries: Maximum number of retry attempts on failure (default: 3)
        retry_delay: Delay in seconds between retries (default: 1.0)
        fallback_on_error: Behavior when fetch fails after retries:
            - 'return_cached': Return last cached data if available (default)
            - 'raise_error': Raise the exception
            - 'return_none': Return None on error
        on_error: Optional callback function(url, exception) called on errors
    """
    _registry.register(
        domain,
        ttl,
        driver,
        max_retries,
        retry_delay,
        fallback_on_error,
        on_error
    )


def get_policy(url: str) -> DomainPolicy:
    """Get policy for a URL."""
    return _registry.get_policy(url)


def get_registered_domains() -> Dict[str, DomainPolicy]:
    """Get all currently registered domains.

    Returns:
        Dictionary mapping domain names to their DomainPolicy objects
    """
    return _registry.get_all_domains()
