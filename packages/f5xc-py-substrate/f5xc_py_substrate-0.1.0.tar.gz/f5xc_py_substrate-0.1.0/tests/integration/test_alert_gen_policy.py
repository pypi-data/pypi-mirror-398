"""Integration tests for alert_gen_policy resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestAlertGenPolicy:
    """Test alert_gen_policy CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-alert-gen-policy"

    @pytest.mark.order(70)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a alert_gen_policy."""
        body = SPEC_REGISTRY.get_spec("alert_gen_policy", "create", test_namespace)
        result = client.alert_gen_policy.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(301)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a alert_gen_policy by name."""
        result = client.alert_gen_policy.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(302)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing alert_gen_policy resources in namespace."""
        items = client.alert_gen_policy.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(303)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a alert_gen_policy."""
        body = SPEC_REGISTRY.get_spec("alert_gen_policy", "replace", test_namespace)
        client.alert_gen_policy.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.alert_gen_policy.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99930)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the alert_gen_policy."""
        client.alert_gen_policy.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.alert_gen_policy.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
