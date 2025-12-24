"""Integration tests for malicious_user_mitigation resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestMaliciousUserMitigation:
    """Test malicious_user_mitigation CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-malicious-user-mitigation"

    @pytest.mark.order(1210)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a malicious_user_mitigation."""
        body = SPEC_REGISTRY.get_spec("malicious_user_mitigation", "create", test_namespace)
        result = client.malicious_user_mitigation.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(9401)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a malicious_user_mitigation by name."""
        result = client.malicious_user_mitigation.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(9402)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing malicious_user_mitigation resources in namespace."""
        items = client.malicious_user_mitigation.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(9403)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a malicious_user_mitigation."""
        body = SPEC_REGISTRY.get_spec("malicious_user_mitigation", "replace", test_namespace)
        client.malicious_user_mitigation.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.malicious_user_mitigation.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(98790)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the malicious_user_mitigation."""
        client.malicious_user_mitigation.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.malicious_user_mitigation.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
