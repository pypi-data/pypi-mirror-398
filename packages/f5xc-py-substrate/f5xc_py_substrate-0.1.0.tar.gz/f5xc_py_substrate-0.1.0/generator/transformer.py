"""Transform parsed OAS into code generation models.

Converts raw OAS structures into clean, code-generation-ready models.
"""

from __future__ import annotations

import keyword
import re
from dataclasses import dataclass, field

from generator.parser import Operation, ParsedOAS, Schema, SchemaProperty

# Python keywords and builtins that cannot be used as identifiers
PYTHON_RESERVED = set(keyword.kwlist) | {
    # Common builtins that would shadow important names
    "type", "id", "list", "dict", "set", "str", "int", "float", "bool",
    "object", "property", "class", "import", "from", "as", "with",
    # Pydantic BaseModel attributes that cannot be used as field names
    "schema", "schema_json", "validate", "copy", "json",
    "construct", "parse_obj", "parse_raw", "parse_file", "from_orm",
    "update_forward_refs", "model_config", "model_fields", "model_extra",
    "model_fields_set", "model_computed_fields", "model_construct",
    "model_copy", "model_dump", "model_dump_json", "model_json_schema",
    "model_parametrized_name", "model_post_init", "model_rebuild",
    "model_validate", "model_validate_json", "model_validate_strings",
}

# Typing names that would shadow important typing imports in generated code
# These cannot be used as generated class names
PYTHON_TYPING_RESERVED = {
    "Any", "Dict", "List", "Set", "Tuple", "Optional", "Union", "Literal",
    "Type", "Callable", "Sequence", "Mapping", "Iterable", "Iterator",
}


@dataclass
class PydanticField:
    """A field for Pydantic model generation."""

    name: str
    python_name: str  # Snake case name for Python
    type_hint: str
    default: str | None = None  # Default value as string, None means required
    description: str = ""
    alias: str | None = None  # Field alias for JSON serialization


@dataclass
class PydanticModel:
    """A Pydantic model to be generated."""

    name: str
    class_name: str  # PascalCase class name
    fields: list[PydanticField] = field(default_factory=list)
    description: str = ""


@dataclass
class QueryParam:
    """A query parameter for a method."""

    name: str  # Original name for API calls
    python_name: str  # Python-safe name for function signature
    type_hint: str  # Python type
    required: bool


@dataclass
class ResourceMethod:
    """A method on a resource class."""

    name: str  # Method name (e.g., "get", "list", "create", "get_dns_info")
    http_method: str  # "GET", "POST", etc.
    path_template: str  # Path with {param} placeholders
    path_params: list[str]  # Parameters in path
    query_params: list[QueryParam]  # Query parameters
    operation_id: str = ""  # Full operationId for collision detection
    request_model: str | None = None  # Request body model name
    response_model: str | None = None  # Response model name
    list_item_model: str | None = None  # For list methods: resource-specific item class name
    returns_list: bool = False  # Whether this returns a list of items
    description: str = ""


@dataclass
class ResourceDefinition:
    """Complete definition for a generated resource."""

    name: str  # e.g., "http_loadbalancer"
    class_name: str  # e.g., "HttpLoadbalancer"
    module_path: str  # e.g., "ves.io.schema.views.http_loadbalancer"
    methods: list[ResourceMethod] = field(default_factory=list)
    models: list[PydanticModel] = field(default_factory=list)
    description: str = ""


# Type mappings from OAS types to Python types
OAS_TO_PYTHON_TYPE: dict[str, str] = {
    "string": "str",
    "integer": "int",
    "number": "float",
    "boolean": "bool",
    "object": "dict[str, Any]",
    "array": "list",
}


def to_snake_case(name: str) -> str:
    """Convert string to snake_case."""
    # Handle already snake_case
    if "_" in name and name.islower():
        return name
    # Convert camelCase/PascalCase to snake_case
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def escape_python_keyword(name: str) -> str:
    """Escape Python reserved keywords by appending underscore."""
    if name in PYTHON_RESERVED:
        return f"{name}_"
    return name


def to_pascal_case(name: str) -> str:
    """Convert string to PascalCase."""
    # Handle snake_case
    if "_" in name:
        return "".join(word.capitalize() for word in name.split("_"))
    # Handle already PascalCase or camelCase
    return name[0].upper() + name[1:] if name else name


class Transformer:
    """Transform parsed OAS into code generation models."""

    def __init__(self, parsed: ParsedOAS) -> None:
        self.parsed = parsed
        self._models: dict[str, PydanticModel] = {}

    def transform(self) -> ResourceDefinition:
        """Transform parsed OAS into a resource definition."""
        # Build models from schemas
        self._build_models()

        # Build methods from operations
        methods = self._build_methods()

        # Get models relevant to this resource
        models = self._get_relevant_models()

        return ResourceDefinition(
            name=self.parsed.resource_name,
            class_name=to_pascal_case(self.parsed.resource_name),
            module_path=self.parsed.module_path,
            methods=methods,
            models=models,
            description=self.parsed.description,
        )

    def _build_models(self) -> None:
        """Build Pydantic models from schemas."""
        for name, schema in self.parsed.schemas.items():
            if schema.ref:
                # Skip pure reference schemas
                continue
            if schema.is_string_enum:
                # Skip string enums - they become Literal types, not model classes
                continue

            model = self._schema_to_model(name, schema)
            self._models[name] = model

    def _schema_to_model(self, name: str, schema: Schema) -> PydanticModel:
        """Convert a schema to a Pydantic model."""
        fields = []
        for prop in schema.properties:
            field = self._property_to_field(prop)
            fields.append(field)

        return PydanticModel(
            name=name,
            class_name=self._schema_name_to_class(name),
            fields=fields,
            description=schema.description,
        )

    def _property_to_field(self, prop: SchemaProperty) -> PydanticField:
        """Convert a schema property to a Pydantic field."""
        type_hint = self._get_type_hint(prop)

        # Determine default
        default = None
        if not prop.required:
            if prop.default is not None:
                default = repr(prop.default)
            else:
                default = "None"
                # Keep Optional[X] for Pydantic model fields (runtime evaluation in Python 3.9)
                if not type_hint.startswith("Optional["):
                    type_hint = f"Optional[{type_hint}]"

        # Handle Python keywords and reserved names
        snake_name = to_snake_case(prop.name)
        python_name = escape_python_keyword(snake_name)
        alias = None
        # Set alias if name differs (for JSON serialization)
        if python_name != prop.name:
            alias = prop.name

        return PydanticField(
            name=prop.name,
            python_name=python_name,
            type_hint=type_hint,
            default=default,
            description=prop.description,
            alias=alias,
        )

    def _get_type_hint(self, prop: SchemaProperty) -> str:
        """Get Python type hint for a property."""
        if prop.ref:
            ref_schema = self.parsed.schemas.get(prop.ref)
            if ref_schema:
                # String enum schema - use Literal type instead of model class
                if ref_schema.is_string_enum:
                    enum_values = ", ".join(repr(v) for v in ref_schema.enum_values)
                    return f"Literal[{enum_values}]"
                # Empty object schema - use Any to accept various types
                if not ref_schema.properties and not ref_schema.ref:
                    return "Any"
            return self._schema_name_to_class(prop.ref)

        if prop.enum:
            # Use Literal for enums
            enum_values = ", ".join(repr(v) for v in prop.enum)
            return f"Literal[{enum_values}]"

        if prop.type == "array":
            if prop.items_ref:
                # Check if the referenced schema is a string enum
                items_schema = self.parsed.schemas.get(prop.items_ref)
                if items_schema and items_schema.is_string_enum:
                    enum_values = ", ".join(repr(v) for v in items_schema.enum_values)
                    item_type = f"Literal[{enum_values}]"
                else:
                    item_type = self._schema_name_to_class(prop.items_ref)
            elif prop.items_type:
                item_type = OAS_TO_PYTHON_TYPE.get(prop.items_type, "Any")
            else:
                item_type = "Any"
            return f"list[{item_type}]"

        return OAS_TO_PYTHON_TYPE.get(prop.type, "Any")

    def _schema_name_to_class(self, name: str) -> str:
        """Convert schema name to Python class name.

        OAS schema names come in formats like:
        - app_firewallAppFirewallViolationType -> AppFirewallViolationType
        - common_cache_ruleCustomCacheRule -> CustomCacheRule
        - clusterCircuitBreaker -> CircuitBreaker
        - ioschemaEmpty -> Empty
        - http_loadbalancerCreateRequest -> CreateRequest
        - protobufAny -> ProtobufAny (typing collision avoidance)
        """
        # First, check if there's a snake_case prefix followed by PascalCase
        # Pattern: lowercase/underscore prefix, then uppercase letter starts the real name
        match = re.match(r'^[a-z_]+([A-Z].*)$', name)
        if match:
            result = match.group(1)
            prefix = name[:-len(result)]  # Keep track of stripped prefix
        else:
            # No clear prefix, use the whole name
            result = name
            prefix = ""

        # If the result starts with the resource name (PascalCase), strip it
        # e.g., HttpLoadbalancerCreateRequest -> CreateRequest
        resource_pascal = to_pascal_case(self.parsed.resource_name)
        if result.startswith(resource_pascal) and len(result) > len(resource_pascal):
            result = result[len(resource_pascal):]

        # Handle edge cases
        if not result or result[0].islower():
            # Fallback: convert entire name to PascalCase
            result = to_pascal_case(name)
            prefix = ""

        # Check for collision with typing names (e.g., Any, List, Dict)
        # These would shadow typing imports in generated code
        if result in PYTHON_TYPING_RESERVED:
            if prefix:
                # Use the stripped prefix to disambiguate
                # e.g., protobufAny -> ProtobufAny
                result = to_pascal_case(prefix) + result
            else:
                # No prefix available, add Model prefix
                result = f"Model{result}"

        return result

    def _build_methods(self) -> list[ResourceMethod]:
        """Build resource methods from operations.

        Two-pass processing for smart deduplication:
        1. First pass: process standard API operations (claim base names)
        2. Second pass: process CustomAPI operations (prefix with 'custom_' if collision)
        - Remaining duplicates get numeric suffix (_2, _3, etc.)
        """
        methods = []
        # Track: name -> count for deduplication
        name_counts: dict[str, int] = {}

        # First pass: standard API operations claim base names
        for op in self.parsed.operations:
            if "CustomAPI" in op.operation_id:
                continue  # Skip CustomAPI in first pass

            method = self._operation_to_method(op)
            base_name = method.name

            if base_name not in name_counts:
                name_counts[base_name] = 1
                methods.append(method)
            else:
                # Duplicate standard API method - add suffix
                name_counts[base_name] += 1
                method.name = f"{base_name}_{name_counts[base_name]}"
                methods.append(method)

        # Second pass: CustomAPI operations
        for op in self.parsed.operations:
            if "CustomAPI" not in op.operation_id:
                continue  # Skip standard API in second pass

            method = self._operation_to_method(op)
            base_name = method.name

            # If standard API claimed this name, prefix with custom_
            if base_name in name_counts:
                base_name = f"custom_{base_name}"

            if base_name not in name_counts:
                name_counts[base_name] = 1
                method.name = base_name
                methods.append(method)
            else:
                # Duplicate - add suffix
                name_counts[base_name] += 1
                method.name = f"{base_name}_{name_counts[base_name]}"
                methods.append(method)

        return methods

    def _operation_to_method(self, op: Operation) -> ResourceMethod:
        """Convert an operation to a resource method."""
        # Extract path parameters
        path_params = re.findall(r"\{([^}]+)\}", op.path)
        # Clean up parameter names (e.g., "metadata.namespace" -> "namespace")
        clean_path_params = [p.split(".")[-1] for p in path_params]

        # Extract query parameters with keyword escaping
        query_params = []
        for p in op.parameters:
            if p.location == "query":
                snake_name = to_snake_case(p.name)
                python_name = escape_python_keyword(snake_name)
                query_params.append(QueryParam(
                    name=p.name,
                    python_name=python_name,
                    type_hint=OAS_TO_PYTHON_TYPE.get(p.schema_type, "str"),
                    required=p.required,
                ))

        # Get model names
        request_model = None
        if op.request_body_ref:
            request_model = self._schema_name_to_class(op.request_body_ref)

        response_model = None
        list_item_model = None
        returns_list = False
        if op.response_ref:
            response_model = self._schema_name_to_class(op.response_ref)
            returns_list = op.name == "list"
            if returns_list:
                # Generate resource-specific list item class name
                resource_class = to_pascal_case(self.parsed.resource_name)
                list_item_model = f"{resource_class}ListItem"

        return ResourceMethod(
            name=op.name,
            http_method=op.method,
            path_template=op.path,
            path_params=clean_path_params,
            query_params=query_params,
            operation_id=op.operation_id,
            request_model=request_model,
            response_model=response_model,
            list_item_model=list_item_model,
            returns_list=returns_list,
            description=op.description,
        )

    def _get_relevant_models(self) -> list[PydanticModel]:
        """Get models that are relevant to this resource."""
        # Start with models referenced by operations
        relevant_names: set[str] = set()

        for op in self.parsed.operations:
            if op.request_body_ref:
                relevant_names.add(op.request_body_ref)
            if op.response_ref:
                relevant_names.add(op.response_ref)

        # Expand to include referenced models (transitive)
        expanded: set[str] = set()
        to_expand = list(relevant_names)

        while to_expand:
            name = to_expand.pop()
            if name in expanded:
                continue
            expanded.add(name)

            schema = self.parsed.schemas.get(name)
            if not schema:
                continue

            for prop in schema.properties:
                if prop.ref and prop.ref not in expanded:
                    to_expand.append(prop.ref)
                if prop.items_ref and prop.items_ref not in expanded:
                    to_expand.append(prop.items_ref)

        # Return models in dependency order (referenced before referencing)
        result = []
        added: set[str] = set()

        def add_model(name: str) -> None:
            if name in added or name not in self._models:
                return
            model = self._models[name]
            # Add dependencies first
            schema = self.parsed.schemas.get(name)
            if schema:
                for prop in schema.properties:
                    if prop.ref:
                        add_model(prop.ref)
                    if prop.items_ref:
                        add_model(prop.items_ref)
            added.add(name)
            result.append(model)

        for name in sorted(expanded):
            add_model(name)

        return result


def transform_all(parsed_list: list[ParsedOAS]) -> list[ResourceDefinition]:
    """Transform all parsed OAS into resource definitions."""
    results = []
    for parsed in parsed_list:
        transformer = Transformer(parsed)
        definition = transformer.transform()
        if definition.methods:  # Only include resources with methods
            results.append(definition)
    return results
