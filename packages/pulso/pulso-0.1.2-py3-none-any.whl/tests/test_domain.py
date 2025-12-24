"""Tests for domain registration."""

import pytest
from pulso.domain import DomainPolicy, DomainRegistry


def test_ttl_parsing():
    """Test TTL string parsing."""
    policy = DomainPolicy("example.com", ttl="1d")
    assert policy.ttl_seconds == 86400

    policy = DomainPolicy("example.com", ttl="12h")
    assert policy.ttl_seconds == 43200

    policy = DomainPolicy("example.com", ttl="30m")
    assert policy.ttl_seconds == 1800

    policy = DomainPolicy("example.com", ttl="60s")
    assert policy.ttl_seconds == 60


def test_invalid_ttl():
    """Test invalid TTL format raises error."""
    with pytest.raises(ValueError):
        DomainPolicy("example.com", ttl="invalid")


def test_domain_registry():
    """Test domain registry."""
    registry = DomainRegistry()
    registry.register("example.com", ttl="12h", driver="playwright")

    policy = registry.get_policy("https://example.com/page")
    assert policy.domain == "example.com"
    assert policy.ttl_seconds == 43200
    assert policy.driver == "playwright"


def test_default_policy():
    """Test default policy for unregistered domains."""
    registry = DomainRegistry()
    policy = registry.get_policy("https://unknown.com/page")

    assert policy.domain == "*"
    assert policy.driver == "requests"
