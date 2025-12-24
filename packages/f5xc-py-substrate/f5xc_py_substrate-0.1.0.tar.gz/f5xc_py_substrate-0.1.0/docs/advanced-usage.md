# Advanced Usage

## Resource-Attached Models

Commonly-used models are available directly on the resource, so you don't need to import from deep module paths:

```python
# Access models directly from the resource
spec = client.http_loadbalancer.CreateSpecType(
    domains=["example.com"],
)

# Available models on each resource:
# - CreateSpecType  (for create operations)
# - ReplaceSpecType (for replace operations)
# - GetResponse     (response from get)
# - GetSpecType     (spec portion of get response)
```

You can still import from models if preferred:

```python
from f5xc_py_substrate.resources.http_loadbalancer.models import CreateSpecType
```

## Serialization Helpers

All SDK models include convenience methods for serialization with sensible defaults.

### to_dict()

Convert a model to a Python dictionary:

```python
lb = client.http_loadbalancer.get(namespace="default", name="my-lb")

# Default: exclude None values
data = lb.to_dict()

# Include None values
data = lb.to_dict(exclude_none=False)

# Exclude specific fields
data = lb.to_dict(exclude={"system_metadata", "status"})
```

### to_json()

Convert a model to a JSON string:

```python
lb = client.http_loadbalancer.get(namespace="default", name="my-lb")

# Default: compact JSON, use API field names (aliases)
json_str = lb.to_json()

# Pretty print with indentation
json_str = lb.to_json(indent=2)

# Customize output
json_str = lb.to_json(indent=4, by_alias=False)

# Exclude fields
json_str = lb.to_json(exclude={"status"})
```

### to_yaml()

Convert a model to YAML (requires pyyaml):

```bash
pip install f5xc-py-substrate[yaml]
```

```python
lb = client.http_loadbalancer.get(namespace="default", name="my-lb")

# Default: use API field names
yaml_str = lb.to_yaml()

# Python field names
yaml_str = lb.to_yaml(by_alias=False)
```

## get() Response Filtering

By default, `get()` excludes verbose fields that are rarely needed:
- Form templates (`create_form`, `replace_form`)
- Reference data (`referring_objects`, `deleted_referred_objects`, `disabled_referred_objects`)
- System metadata (`system_metadata`)

This keeps responses clean and focused on the data you typically need.

```python
# Default: clean response without verbose fields
lb = client.http_loadbalancer.get(namespace="default", name="my-lb")
print(lb.metadata)  # Available
print(lb.spec)      # Available
# lb.create_form    # Not present (excluded by default)

# Get the complete response with all fields
lb = client.http_loadbalancer.get(
    namespace="default",
    name="my-lb",
    include_all=True
)
print(lb.create_form)  # Now available

# Exclude additional fields beyond the defaults
lb = client.http_loadbalancer.get(
    namespace="default",
    name="my-lb",
    exclude=["status"]  # Also exclude status field
)
```

### Predefined Exclusion Groups

| Group | Excluded Fields |
|-------|-----------------|
| `forms` | `create_form`, `replace_form` |
| `references` | `referring_objects`, `deleted_referred_objects`, `disabled_referred_objects` |
| `system_metadata` | `system_metadata` |

These groups are excluded by default. Use `include_all=True` to get all fields.

## list() vs get() Responses

The `list()` and `get()` methods return different response structures:

### list() Response

Returns a list of lightweight items with basic metadata:

```python
lbs = client.http_loadbalancer.list(namespace="default")
for lb in lbs:
    print(f"{lb.name}: {lb.description}")
    # Available: name, namespace, description, labels, annotations, uid, tenant, disabled
```

To get full spec details, you need to call `get()` for each item:

```python
lbs = client.http_loadbalancer.list(namespace="default")
for item in lbs:
    lb = client.http_loadbalancer.get(namespace=item.namespace, name=item.name)
    print(lb.spec)
```

### get() Response

Returns a detailed object with full spec and metadata. By default, verbose fields are excluded for cleaner output:

```python
lb = client.http_loadbalancer.get(namespace="default", name="my-lb")
print(lb.metadata)  # Full metadata
print(lb.spec)      # Full specification
print(lb.status)    # Status information
```

To get the complete response including form templates and reference data:

```python
lb = client.http_loadbalancer.get(
    namespace="default",
    name="my-lb",
    include_all=True
)
print(lb.create_form)        # Template for creating similar resources
print(lb.replace_form)       # Template for replacing
print(lb.referring_objects)  # Objects that reference this one
print(lb.system_metadata)    # System-managed metadata
```

## Error Handling

The SDK provides typed exceptions for each HTTP error status:

```python
from f5xc_py_substrate.exceptions import (
    F5XCError,
    F5XCNotFoundError,
    F5XCAuthError,
    F5XCForbiddenError,
    F5XCConflictError,
    F5XCRateLimitError,
    F5XCServerError,
    F5XCServiceUnavailableError,
    F5XCTimeoutError,
    F5XCPartialResultsError,
)
```

### Exception Hierarchy

| Exception | HTTP Status | Description |
|-----------|-------------|-------------|
| `F5XCError` | - | Base class for all SDK errors |
| `F5XCAuthError` | 401 | Authentication failed |
| `F5XCForbiddenError` | 403 | No permission to access resource |
| `F5XCNotFoundError` | 404 | Resource does not exist |
| `F5XCConflictError` | 409 | Operation conflicts with current state |
| `F5XCRateLimitError` | 429 | Rate limit exceeded |
| `F5XCServerError` | 500 | Internal server error |
| `F5XCServiceUnavailableError` | 503 | Service temporarily unavailable |
| `F5XCTimeoutError` | 504 | Gateway timeout |
| `F5XCPartialResultsError` | 200 | List returned items with some errors |

### Exception Attributes

All exceptions have these attributes:

- `status_code`: HTTP status code
- `message`: Human-readable error message
- `body`: Parsed JSON response body (if available)

### Usage Examples

```python
# Catch specific errors
try:
    lb = client.http_loadbalancer.get(namespace="default", name="missing")
except F5XCNotFoundError as e:
    print(f"Not found: {e.message}")

# Catch any API error
try:
    client.http_loadbalancer.delete(namespace="default", name="my-lb")
except F5XCError as e:
    print(f"API error {e.status_code}: {e.message}")

# Handle partial results from list operations
try:
    lbs = client.http_loadbalancer.list(namespace="default")
except F5XCPartialResultsError as e:
    print(f"Got {len(e.items)} items, but {len(e.errors)} errors")
    for lb in e.items:
        print(lb.metadata.name)
```

## Custom HTTP Client

Pass a custom httpx client for proxies, timeouts, or other HTTP configuration:

```python
import httpx
from f5xc_py_substrate import Client

http_client = httpx.Client(
    timeout=60.0,
    proxies="http://proxy.example.com:8080",
)

client = Client(
    tenant_url="https://your-tenant.console.ves.volterra.io",
    token="your-api-token",
    http_client=http_client,
)
```

### Timeout Configuration

```python
import httpx

# Configure different timeouts
http_client = httpx.Client(
    timeout=httpx.Timeout(
        connect=5.0,    # Connection timeout
        read=30.0,      # Read timeout
        write=30.0,     # Write timeout
        pool=10.0,      # Pool timeout
    )
)
```

### Retry Logic

httpx doesn't include built-in retry logic, but you can use `httpx` with a transport that supports retries:

```python
import httpx
from httpx import HTTPTransport

transport = HTTPTransport(retries=3)
http_client = httpx.Client(transport=transport)
```
