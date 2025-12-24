"""Integration tests for sensitive_data_policy resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestSensitiveDataPolicy:
    """Test sensitive_data_policy CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-sensitive-data-policy"

    @pytest.mark.order(1780)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a sensitive_data_policy."""
        body = SPEC_REGISTRY.get_spec("sensitive_data_policy", "create", test_namespace)
        result = client.sensitive_data_policy.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(13301)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a sensitive_data_policy by name."""
        result = client.sensitive_data_policy.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(13302)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing sensitive_data_policy resources in namespace."""
        items = client.sensitive_data_policy.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(13303)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a sensitive_data_policy."""
        body = SPEC_REGISTRY.get_spec("sensitive_data_policy", "replace", test_namespace)
        client.sensitive_data_policy.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.sensitive_data_policy.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(98220)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the sensitive_data_policy."""
        client.sensitive_data_policy.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.sensitive_data_policy.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
