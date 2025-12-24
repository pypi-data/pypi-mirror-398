"""Integration tests for ip_prefix_set resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestIpPrefixSet:
    """Test ip_prefix_set CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-ip-prefix-set"

    @pytest.mark.order(1070)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a ip_prefix_set."""
        body = SPEC_REGISTRY.get_spec("ip_prefix_set", "create", test_namespace)
        result = client.ip_prefix_set.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(8401)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a ip_prefix_set by name."""
        result = client.ip_prefix_set.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(8402)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing ip_prefix_set resources in namespace."""
        items = client.ip_prefix_set.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(8403)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a ip_prefix_set."""
        body = SPEC_REGISTRY.get_spec("ip_prefix_set", "replace", test_namespace)
        client.ip_prefix_set.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.ip_prefix_set.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(98930)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the ip_prefix_set."""
        client.ip_prefix_set.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.ip_prefix_set.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
