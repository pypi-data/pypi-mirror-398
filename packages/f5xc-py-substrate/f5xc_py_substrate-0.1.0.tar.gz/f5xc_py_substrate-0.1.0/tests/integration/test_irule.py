"""Integration tests for irule resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestIrule:
    """Test irule CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-irule"

    @pytest.mark.order(1080)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a irule."""
        body = SPEC_REGISTRY.get_spec("irule", "create", test_namespace)
        result = client.irule.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(8501)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a irule by name."""
        result = client.irule.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(8502)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing irule resources in namespace."""
        items = client.irule.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(8503)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a irule."""
        body = SPEC_REGISTRY.get_spec("irule", "replace", test_namespace)
        client.irule.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.irule.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(98920)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the irule."""
        client.irule.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.irule.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
