"""Integration tests for certificate_chain resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestCertificateChain:
    """Test certificate_chain CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-certificate-chain"

    @pytest.mark.order(450)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a certificate_chain."""
        body = SPEC_REGISTRY.get_spec("certificate_chain", "create", test_namespace)
        result = client.certificate_chain.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(3501)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a certificate_chain by name."""
        result = client.certificate_chain.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(3502)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing certificate_chain resources in namespace."""
        items = client.certificate_chain.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(3503)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a certificate_chain."""
        body = SPEC_REGISTRY.get_spec("certificate_chain", "replace", test_namespace)
        client.certificate_chain.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.certificate_chain.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99550)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the certificate_chain."""
        client.certificate_chain.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.certificate_chain.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
