"""Integration tests for bgp_asn_set resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestBgpAsnSet:
    """Test bgp_asn_set CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-bgp-asn-set"

    @pytest.mark.order(310)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a bgp_asn_set."""
        body = SPEC_REGISTRY.get_spec("bgp_asn_set", "create", test_namespace)
        result = client.bgp_asn_set.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(2301)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a bgp_asn_set by name."""
        result = client.bgp_asn_set.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(2302)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing bgp_asn_set resources in namespace."""
        items = client.bgp_asn_set.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(2303)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a bgp_asn_set."""
        body = SPEC_REGISTRY.get_spec("bgp_asn_set", "replace", test_namespace)
        client.bgp_asn_set.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.bgp_asn_set.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99690)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the bgp_asn_set."""
        client.bgp_asn_set.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.bgp_asn_set.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
