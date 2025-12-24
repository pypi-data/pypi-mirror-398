"""Integration tests for certificate resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestCertificate:
    """Test certificate CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-certificate"

    @pytest.mark.order(440)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a certificate."""
        body = SPEC_REGISTRY.get_spec("certificate", "create", test_namespace)
        result = client.certificate.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(3401)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a certificate by name."""
        result = client.certificate.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(3402)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing certificate resources in namespace."""
        items = client.certificate.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(3403)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a certificate."""
        body = SPEC_REGISTRY.get_spec("certificate", "replace", test_namespace)
        client.certificate.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.certificate.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99560)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the certificate."""
        client.certificate.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.certificate.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
