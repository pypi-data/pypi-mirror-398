"""Integration tests for bigip_irule resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestBigipIrule:
    """Test bigip_irule CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-bigip-irule"

    @pytest.mark.order(330)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a bigip_irule."""
        body = SPEC_REGISTRY.get_spec("bigip_irule", "create", test_namespace)
        result = client.bigip_irule.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(2501)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a bigip_irule by name."""
        result = client.bigip_irule.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(2502)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing bigip_irule resources in namespace."""
        items = client.bigip_irule.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(2503)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a bigip_irule."""
        body = SPEC_REGISTRY.get_spec("bigip_irule", "replace", test_namespace)
        client.bigip_irule.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.bigip_irule.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99670)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the bigip_irule."""
        client.bigip_irule.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.bigip_irule.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
