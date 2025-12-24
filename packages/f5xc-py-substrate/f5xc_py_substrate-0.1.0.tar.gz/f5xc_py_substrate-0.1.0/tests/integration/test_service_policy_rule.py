"""Integration tests for service_policy_rule resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestServicePolicyRule:
    """Test service_policy_rule CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-service-policy-rule"

    @pytest.mark.order(1810)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a service_policy_rule."""
        body = SPEC_REGISTRY.get_spec("service_policy_rule", "create", test_namespace)
        result = client.service_policy_rule.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(13501)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a service_policy_rule by name."""
        result = client.service_policy_rule.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(13502)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing service_policy_rule resources in namespace."""
        items = client.service_policy_rule.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(13503)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a service_policy_rule."""
        body = SPEC_REGISTRY.get_spec("service_policy_rule", "replace", test_namespace)
        client.service_policy_rule.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.service_policy_rule.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(98190)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the service_policy_rule."""
        client.service_policy_rule.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.service_policy_rule.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
