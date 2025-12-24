"""F5 XC API Client with lazy-loaded resources."""

from __future__ import annotations

import os
from importlib import import_module
from typing import Any

import httpx

from f5xc_py_substrate._http import HTTPClient


def _to_class_name(name: str) -> str:
    """Convert snake_case to PascalCase."""
    return "".join(word.capitalize() for word in name.split("_"))


class Client:
    """F5 Distributed Cloud API client.

    Resources are lazy-loaded on first access.

    Example:
        api = Client(
            tenant_url="https://example.console.ves.volterra.io",
            token="your-api-token"
        )
        lbs = api.http_loadbalancer.list(namespace="demo")
    """

    def __init__(
        self,
        tenant_url: str | None = None,
        token: str | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        resolved_tenant_url = tenant_url or os.environ.get("F5XC_TENANT_URL")
        resolved_token = token or os.environ.get("F5XC_API_TOKEN")

        if not resolved_tenant_url:
            raise ValueError(
                "tenant_url is required. Provide it directly or set F5XC_TENANT_URL env var."
            )
        if not resolved_token:
            raise ValueError(
                "token is required. Provide it directly or set F5XC_API_TOKEN env var."
            )

        # Remove trailing slash from tenant URL
        self._tenant_url: str = resolved_tenant_url.rstrip("/")
        self._token: str = resolved_token

        self._http = HTTPClient(
            base_url=self._tenant_url,
            token=self._token,
            client=http_client,
        )
        self._resources: dict[str, Any] = {}

    def __getattr__(self, name: str) -> Any:
        """Lazy load resource on first access."""
        if name.startswith("_"):
            raise AttributeError(name)

        if name not in self._resources:
            self._resources[name] = self._load_resource(name)

        return self._resources[name]

    def _load_resource(self, name: str) -> Any:
        """Load a resource module and instantiate its resource class."""
        try:
            module = import_module(f"f5xc_py_substrate.resources.{name}.resource")
            resource_class = getattr(module, f"{_to_class_name(name)}Resource")
            return resource_class(self._http)
        except ModuleNotFoundError:
            raise AttributeError(
                f"Unknown resource: {name}. "
                f"Available resources can be found in f5xc_py_substrate.resources"
            ) from None

    @property
    def tenant_url(self) -> str:
        """The tenant URL this client is connected to."""
        return self._tenant_url
