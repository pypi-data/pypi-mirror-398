"""Integration tests for k8s_pod_security_policy resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestK8sPodSecurityPolicy:
    """Test k8s_pod_security_policy CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-k8s-pod-security-policy"

    @pytest.mark.order(1130)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a k8s_pod_security_policy."""
        body = SPEC_REGISTRY.get_spec("k8s_pod_security_policy", "create", test_namespace)
        result = client.k8s_pod_security_policy.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(9001)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a k8s_pod_security_policy by name."""
        result = client.k8s_pod_security_policy.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(9002)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing k8s_pod_security_policy resources in namespace."""
        items = client.k8s_pod_security_policy.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(9003)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a k8s_pod_security_policy."""
        body = SPEC_REGISTRY.get_spec("k8s_pod_security_policy", "replace", test_namespace)
        client.k8s_pod_security_policy.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.k8s_pod_security_policy.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(98870)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the k8s_pod_security_policy."""
        client.k8s_pod_security_policy.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.k8s_pod_security_policy.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
