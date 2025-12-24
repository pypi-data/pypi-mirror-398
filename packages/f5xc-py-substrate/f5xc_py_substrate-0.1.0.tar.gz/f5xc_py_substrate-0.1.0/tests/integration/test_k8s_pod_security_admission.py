"""Integration tests for k8s_pod_security_admission resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestK8sPodSecurityAdmission:
    """Test k8s_pod_security_admission CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-k8s-pod-security-admission"

    @pytest.mark.order(1120)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a k8s_pod_security_admission."""
        body = SPEC_REGISTRY.get_spec("k8s_pod_security_admission", "create", test_namespace)
        result = client.k8s_pod_security_admission.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(8901)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a k8s_pod_security_admission by name."""
        result = client.k8s_pod_security_admission.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(8902)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing k8s_pod_security_admission resources in namespace."""
        items = client.k8s_pod_security_admission.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(8903)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a k8s_pod_security_admission."""
        body = SPEC_REGISTRY.get_spec("k8s_pod_security_admission", "replace", test_namespace)
        client.k8s_pod_security_admission.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.k8s_pod_security_admission.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(98880)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the k8s_pod_security_admission."""
        client.k8s_pod_security_admission.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.k8s_pod_security_admission.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
