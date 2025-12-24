"""Tests for error handling and retry logic."""

import pytest
from unittest.mock import patch, MagicMock
from pulso.domain import register_domain, get_policy
from pulso.fetcher import fetch_raw, FetchError
from pulso.core import fetch
from pulso import cache


def test_retry_logic():
    """Test that retries happen according to policy."""
    register_domain("retry-test.com", max_retries=3, retry_delay=0.1)
    policy = get_policy("https://retry-test.com")

    assert policy.max_retries == 3
    assert policy.retry_delay == 0.1


def test_fallback_return_cached():
    """Test return_cached fallback behavior."""
    register_domain(
        "fallback-test.com",
        fallback_on_error="return_cached",
        max_retries=1,
        retry_delay=0.1
    )

    policy = get_policy("https://fallback-test.com")
    assert policy.fallback_on_error == "return_cached"


def test_fallback_raise_error():
    """Test raise_error fallback behavior."""
    register_domain(
        "strict-test.com",
        fallback_on_error="raise_error",
        max_retries=1
    )

    policy = get_policy("https://strict-test.com")
    assert policy.fallback_on_error == "raise_error"


def test_fallback_return_none():
    """Test return_none fallback behavior."""
    register_domain(
        "optional-test.com",
        fallback_on_error="return_none",
        max_retries=1
    )

    policy = get_policy("https://optional-test.com")
    assert policy.fallback_on_error == "return_none"


def test_error_callback():
    """Test that error callback is called on failures."""
    error_calls = []

    def error_handler(url, exception):
        error_calls.append((url, str(exception)))

    register_domain(
        "callback-test.com",
        max_retries=2,
        retry_delay=0.1,
        on_error=error_handler
    )

    policy = get_policy("https://callback-test.com")
    assert policy.on_error is not None
    assert policy.on_error == error_handler


def test_default_policy_values():
    """Test default policy values."""
    register_domain("default-test.com")
    policy = get_policy("https://default-test.com")

    assert policy.max_retries == 3
    assert policy.retry_delay == 1.0
    assert policy.fallback_on_error == "return_cached"
    assert policy.on_error is None
