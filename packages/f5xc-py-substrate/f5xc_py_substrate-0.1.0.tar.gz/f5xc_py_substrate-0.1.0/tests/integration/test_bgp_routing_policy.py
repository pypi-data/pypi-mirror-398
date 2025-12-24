"""Integration tests for bgp_routing_policy resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestBgpRoutingPolicy:
    """Test bgp_routing_policy CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-bgp-routing-policy"

    @pytest.mark.order(320)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a bgp_routing_policy."""
        body = SPEC_REGISTRY.get_spec("bgp_routing_policy", "create", test_namespace)
        result = client.bgp_routing_policy.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(2401)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a bgp_routing_policy by name."""
        result = client.bgp_routing_policy.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(2402)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing bgp_routing_policy resources in namespace."""
        items = client.bgp_routing_policy.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(2403)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a bgp_routing_policy."""
        body = SPEC_REGISTRY.get_spec("bgp_routing_policy", "replace", test_namespace)
        client.bgp_routing_policy.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.bgp_routing_policy.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99680)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the bgp_routing_policy."""
        client.bgp_routing_policy.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.bgp_routing_policy.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
