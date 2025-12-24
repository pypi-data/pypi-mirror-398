"""Fetch web content using appropriate drivers."""

from typing import Optional
import time
import logging
import requests
from .domain import get_policy, DriverType, DomainPolicy


logger = logging.getLogger(__name__)


class FetchError(Exception):
    """Error during fetch operation."""
    pass


def _fetch_with_requests(url: str) -> str:
    """Fetch using requests library."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        raise FetchError(f"Failed to fetch {url}: {e}")


def _fetch_with_playwright(url: str) -> str:
    """Fetch using playwright for dynamic content."""
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=30000)

            # Wait for network to be idle
            page.wait_for_load_state("networkidle")

            html = page.content()
            browser.close()
            return html
    except ImportError:
        raise FetchError(
            "Playwright not installed. Install with: pip install playwright && playwright install"
        )
    except Exception as e:
        raise FetchError(f"Failed to fetch {url} with playwright: {e}")


def fetch_raw(url: str, driver: Optional[DriverType] = None, policy: Optional[DomainPolicy] = None) -> str:
    """Fetch raw HTML without caching, with retry logic.

    Args:
        url: URL to fetch
        driver: Override driver selection (None to use domain policy)
        policy: Optional DomainPolicy to use for retry configuration

    Returns:
        HTML content
    """
    if policy is None:
        policy = get_policy(url)

    if driver is None:
        driver = policy.driver

    # Retry logic
    last_error = None
    for attempt in range(policy.max_retries):
        try:
            if driver == "requests":
                return _fetch_with_requests(url)
            elif driver == "playwright":
                return _fetch_with_playwright(url)
            else:
                raise ValueError(f"Unknown driver: {driver}")
        except FetchError as e:
            last_error = e
            logger.warning(
                f"Fetch failed for {url} (attempt {attempt + 1}/{policy.max_retries}): {e}"
            )

            # Call error callback if provided
            if policy.on_error:
                try:
                    policy.on_error(url, e)
                except Exception as callback_error:
                    logger.error(f"Error callback failed: {callback_error}")

            # Retry with delay if not last attempt
            if attempt < policy.max_retries - 1:
                time.sleep(policy.retry_delay)

    # All retries failed
    logger.error(f"All {policy.max_retries} fetch attempts failed for {url}")
    raise last_error
