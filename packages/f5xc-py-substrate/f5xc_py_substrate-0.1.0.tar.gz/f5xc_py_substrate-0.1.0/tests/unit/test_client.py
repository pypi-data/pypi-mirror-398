"""Unit tests for the F5 XC SDK client."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from f5xc_py_substrate import Client


class TestClientInit:
    """Test client initialization."""

    def test_init_with_explicit_params(self) -> None:
        """Test client initialization with explicit parameters."""
        client = Client(
            tenant_url="https://test.console.ves.volterra.io",
            token="test-token",
        )
        assert client.tenant_url == "https://test.console.ves.volterra.io"

    def test_init_strips_trailing_slash(self) -> None:
        """Test that trailing slash is removed from tenant URL."""
        client = Client(
            tenant_url="https://test.console.ves.volterra.io/",
            token="test-token",
        )
        assert client.tenant_url == "https://test.console.ves.volterra.io"

    def test_init_from_env_vars(self) -> None:
        """Test client initialization from environment variables."""
        with patch.dict(os.environ, {
            "F5XC_TENANT_URL": "https://env.console.ves.volterra.io",
            "F5XC_API_TOKEN": "env-token",
        }):
            client = Client()
            assert client.tenant_url == "https://env.console.ves.volterra.io"

    def test_init_missing_tenant_url_raises(self) -> None:
        """Test that missing tenant_url raises ValueError."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove any existing env vars
            os.environ.pop("F5XC_TENANT_URL", None)
            os.environ.pop("F5XC_API_TOKEN", None)

            with pytest.raises(ValueError, match="tenant_url is required"):
                Client(token="test-token")

    def test_init_missing_token_raises(self) -> None:
        """Test that missing token raises ValueError."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("F5XC_TENANT_URL", None)
            os.environ.pop("F5XC_API_TOKEN", None)

            with pytest.raises(ValueError, match="token is required"):
                Client(tenant_url="https://test.console.ves.volterra.io")


class TestClientLazyLoading:
    """Test lazy loading of resources."""

    def test_resource_lazy_loaded(self) -> None:
        """Test that resources are lazy loaded on first access."""
        client = Client(
            tenant_url="https://test.console.ves.volterra.io",
            token="test-token",
        )
        # Access a resource
        ns_resource = client.namespace
        assert ns_resource is not None

        # Same instance returned on second access
        assert client.namespace is ns_resource

    def test_unknown_resource_raises(self) -> None:
        """Test that accessing unknown resource raises AttributeError."""
        client = Client(
            tenant_url="https://test.console.ves.volterra.io",
            token="test-token",
        )
        with pytest.raises(AttributeError, match="Unknown resource"):
            _ = client.nonexistent_resource

    def test_private_attribute_raises(self) -> None:
        """Test that accessing private attributes raises AttributeError."""
        client = Client(
            tenant_url="https://test.console.ves.volterra.io",
            token="test-token",
        )
        with pytest.raises(AttributeError):
            _ = client._nonexistent
