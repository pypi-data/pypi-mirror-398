"""Integration tests for tcpdump resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestTcpdump:
    """Test tcpdump CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-tcpdump"

    @pytest.mark.skip(reason="No spec template available for tcpdump")
    @pytest.mark.order(1930)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a tcpdump."""
        body = SPEC_REGISTRY.get_spec("tcpdump", "create", test_namespace)
        result = client.tcpdump.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for tcpdump")
    @pytest.mark.order(1931)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a tcpdump by name."""
        result = client.tcpdump.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for tcpdump")
    @pytest.mark.order(1932)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing tcpdump resources in namespace."""
        items = client.tcpdump.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for tcpdump")
    @pytest.mark.order(1933)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a tcpdump."""
        body = SPEC_REGISTRY.get_spec("tcpdump", "replace", test_namespace)
        client.tcpdump.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.tcpdump.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME