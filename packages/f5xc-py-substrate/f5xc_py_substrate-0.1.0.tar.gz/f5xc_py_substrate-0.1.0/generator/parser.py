"""OAS parser for F5 XC OpenAPI specifications.

Parses OpenAPI 3.0 JSON files and extracts API operations and schemas.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Parameter:
    """API operation parameter."""

    name: str
    location: str  # "path", "query"
    required: bool
    schema_type: str
    description: str = ""


@dataclass
class SchemaProperty:
    """Property within a schema."""

    name: str
    type: str
    description: str = ""
    required: bool = False
    ref: str | None = None
    items_ref: str | None = None  # For array types
    items_type: str | None = None  # For array of primitives
    enum: list[str] | None = None
    default: Any = None


@dataclass
class Schema:
    """Parsed OpenAPI schema."""

    name: str
    properties: list[SchemaProperty] = field(default_factory=list)
    description: str = ""
    ref: str | None = None  # If this schema is just a reference
    is_string_enum: bool = False  # True if type=string with enum values
    enum_values: list[str] = field(default_factory=list)  # The enum values


@dataclass
class Operation:
    """Parsed API operation."""

    name: str  # Method name derived from operationId (e.g., "create", "get_dns_info")
    operation_id: str  # Full operationId (e.g., "ves.io.schema.resource.API.Create")
    method: str  # HTTP method: "GET", "POST", "PUT", "DELETE", "PATCH"
    path: str
    summary: str
    description: str
    parameters: list[Parameter] = field(default_factory=list)
    request_body_ref: str | None = None
    response_ref: str | None = None


@dataclass
class ParsedOAS:
    """Parsed OpenAPI specification for a single resource."""

    title: str
    description: str
    resource_name: str  # e.g., "http_loadbalancer"
    module_path: str  # e.g., "ves.io.schema.views.http_loadbalancer"
    operations: list[Operation] = field(default_factory=list)
    schemas: dict[str, Schema] = field(default_factory=dict)


class OASParser:
    """Parser for F5 XC OpenAPI specifications."""

    def __init__(self, oas_path: Path) -> None:
        self.oas_path = oas_path
        self._raw: dict[str, Any] = {}

    def parse(self) -> ParsedOAS | None:
        """Parse the OAS file and return structured data."""
        with open(self.oas_path) as f:
            self._raw = json.load(f)

        # Extract basic info
        info = self._raw.get("info", {})
        title = info.get("title", "")

        # Extract module path from title
        # e.g., "F5 Distributed Cloud Services API for ves.io.schema.views.http_loadbalancer"
        module_path = self._extract_module_path(title)
        if not module_path:
            return None

        # Extract resource name from module path
        resource_name = module_path.split(".")[-1]

        # Parse operations (all operations, not filtered)
        operations = self._parse_operations()
        if not operations:
            # Skip files without any operations
            return None

        # Parse schemas
        schemas = self._parse_schemas()

        return ParsedOAS(
            title=title,
            description=info.get("description", ""),
            resource_name=resource_name,
            module_path=module_path,
            operations=operations,
            schemas=schemas,
        )

    def _extract_module_path(self, title: str) -> str | None:
        """Extract module path from API title.

        Title format: "F5 Distributed Cloud Services API for ves.io.schema..."
        """
        prefix = "F5 Distributed Cloud Services API for "
        if title.startswith(prefix):
            return title[len(prefix):]
        return None

    def _parse_operations(self) -> list[Operation]:
        """Parse all API operations from paths."""
        operations = []
        paths = self._raw.get("paths", {})

        for path, path_item in paths.items():
            for method in ["get", "post", "put", "delete", "patch"]:
                if method not in path_item:
                    continue

                op_data = path_item[method]
                operation_id = op_data.get("operationId", "")
                if not operation_id:
                    continue

                # Extract method name from operation ID (last segment, snake_cased)
                op_name = self._operation_id_to_method_name(operation_id)

                # Parse parameters
                params = self._parse_parameters(op_data.get("parameters", []))

                # Parse request body reference
                request_body_ref = None
                if "requestBody" in op_data:
                    request_body_ref = self._get_schema_ref(
                        op_data["requestBody"].get("content", {})
                        .get("application/json", {})
                        .get("schema", {})
                    )

                # Parse response reference
                response_ref = None
                success_response = op_data.get("responses", {}).get("200", {})
                if "content" in success_response:
                    response_ref = self._get_schema_ref(
                        success_response["content"]
                        .get("application/json", {})
                        .get("schema", {})
                    )

                operations.append(
                    Operation(
                        name=op_name,
                        operation_id=operation_id,
                        method=method.upper(),
                        path=path,
                        summary=op_data.get("summary", ""),
                        description=op_data.get("description", ""),
                        parameters=params,
                        request_body_ref=request_body_ref,
                        response_ref=response_ref,
                    )
                )

        return operations

    def _operation_id_to_method_name(self, operation_id: str) -> str:
        """Convert operation ID to a Python method name.

        Examples:
            ves.io.schema.resource.API.Create -> create
            ves.io.schema.resource.CustomAPI.GetDnsInfo -> get_dns_info
            ves.io.schema.resource.API.List -> list
        """
        # Get the last segment (e.g., "Create", "GetDnsInfo", "List")
        last_segment = operation_id.split(".")[-1]

        # Convert to snake_case
        # Handle already snake_case
        if "_" in last_segment and last_segment.islower():
            return last_segment

        # Convert PascalCase/camelCase to snake_case
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", last_segment)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    def _parse_parameters(self, params: list[dict[str, Any]]) -> list[Parameter]:
        """Parse operation parameters."""
        result = []
        for param in params:
            schema = param.get("schema", {})
            result.append(
                Parameter(
                    name=param.get("name", ""),
                    location=param.get("in", ""),
                    required=param.get("required", False),
                    schema_type=schema.get("type", "string"),
                    description=param.get("description", ""),
                )
            )
        return result

    def _get_schema_ref(self, schema: dict[str, Any]) -> str | None:
        """Extract schema reference name."""
        ref = schema.get("$ref", "")
        if ref.startswith("#/components/schemas/"):
            return ref.split("/")[-1]
        return None

    def _parse_schemas(self) -> dict[str, Schema]:
        """Parse component schemas."""
        schemas = {}
        components = self._raw.get("components", {}).get("schemas", {})

        for name, schema_data in components.items():
            schema = self._parse_schema(name, schema_data)
            schemas[name] = schema

        return schemas

    def _parse_schema(self, name: str, data: dict[str, Any]) -> Schema:
        """Parse a single schema."""
        # Check if it's just a reference
        if "$ref" in data:
            return Schema(name=name, ref=self._get_schema_ref(data))

        # Check if this is a string enum schema (type=string with enum values, no properties)
        if data.get("type") == "string" and "enum" in data:
            return Schema(
                name=name,
                description=data.get("description", ""),
                is_string_enum=True,
                enum_values=data["enum"],
            )

        properties = []
        required_fields = set(data.get("required", []))

        for prop_name, prop_data in data.get("properties", {}).items():
            prop = self._parse_property(prop_name, prop_data, prop_name in required_fields)
            properties.append(prop)

        return Schema(
            name=name,
            properties=properties,
            description=data.get("description", ""),
        )

    def _parse_property(
        self, name: str, data: dict[str, Any], required: bool
    ) -> SchemaProperty:
        """Parse a schema property."""
        prop_type = data.get("type", "object")
        ref = None
        items_ref = None
        items_type = None
        enum = None

        if "$ref" in data:
            ref = self._get_schema_ref(data)
            prop_type = "object"
        elif prop_type == "array":
            items = data.get("items", {})
            if "$ref" in items:
                items_ref = self._get_schema_ref(items)
            else:
                items_type = items.get("type", "string")
        elif "enum" in data:
            enum = data["enum"]

        return SchemaProperty(
            name=name,
            type=prop_type,
            description=data.get("description", ""),
            required=required,
            ref=ref,
            items_ref=items_ref,
            items_type=items_type,
            enum=enum,
            default=data.get("default"),
        )


def parse_oas_directory(directory: Path) -> list[ParsedOAS]:
    """Parse all OAS files in a directory."""
    results = []
    for oas_file in sorted(directory.glob("*.json")):
        parser = OASParser(oas_file)
        parsed = parser.parse()
        if parsed:
            results.append(parsed)
    return results
