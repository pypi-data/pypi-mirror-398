"""Integration tests for waf resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestWaf:
    """Test waf CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-waf"

    @pytest.mark.skip(reason="No spec template available for waf")
    @pytest.mark.order(2240)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a waf."""
        body = SPEC_REGISTRY.get_spec("waf", "create", test_namespace)
        result = client.waf.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for waf")
    @pytest.mark.order(2241)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a waf by name."""
        result = client.waf.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for waf")
    @pytest.mark.order(2242)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing waf resources in namespace."""
        items = client.waf.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for waf")
    @pytest.mark.order(2243)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a waf."""
        body = SPEC_REGISTRY.get_spec("waf", "replace", test_namespace)
        client.waf.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.waf.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME