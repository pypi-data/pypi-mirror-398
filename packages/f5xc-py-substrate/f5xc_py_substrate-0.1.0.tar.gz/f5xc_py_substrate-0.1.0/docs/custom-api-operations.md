# CustomAPI Operations

This SDK generates methods for **all** operations defined in F5's OpenAPI specifications, including both standard API operations (CRUD) and CustomAPI operations.

## How It Works

The generator iterates through every operation in every OAS file and generates a method for it:

1. **Method naming**: The last segment of the `operationId` is converted to snake_case
   - `ves.io.schema.resource.API.Create` → `create()`
   - `ves.io.schema.resource.CustomAPI.GetDnsInfo` → `get_dns_info()`

2. **Collision handling**: When both standard API and CustomAPI have the same method name:
   - Standard API claims the base name: `get()`, `list()`
   - CustomAPI gets prefixed: `custom_get()`, `custom_list()`

3. **Duplicate handling**: Multiple operations with the same name get numeric suffixes:
   - First occurrence: `get_status()`
   - Second occurrence: `get_status_2()`

## Coverage

- **269 resources** generated from OAS specs
- **1,777 total operations** (827 standard API + 644 CustomAPI + others)
- Only **2 collision cases** across the entire API (both in `user_group`)

## Examples

### Standard CRUD operations

```python
from f5xc_py_substrate import Client

client = Client()

# Create
lb = client.http_loadbalancer.create(
    namespace="default",
    name="my-lb",
    spec=HttpLoadbalancerSpec(...)
)

# Get, List, Replace, Delete
lb = client.http_loadbalancer.get(namespace="default", name="my-lb")
lbs = client.http_loadbalancer.list(namespace="default")
client.http_loadbalancer.replace(namespace="default", name="my-lb", spec=new_spec)
client.http_loadbalancer.delete(namespace="default", name="my-lb")
```

### CustomAPI operations

```python
# Get DNS info for a load balancer
dns_info = client.http_loadbalancer.get_dns_info(namespace="default", name="my-lb")

# Get swagger spec
swagger = client.http_loadbalancer.get_swagger_spec(namespace="default", name="my-lb")

# Subscribe/unsubscribe
client.cdn_loadbalancer.subscribe(namespace="default", name="my-cdn", body={...})
client.cdn_loadbalancer.unsubscribe(namespace="default", name="my-cdn", body={...})

# Cascade delete
client.namespace.cascade_delete(name="my-ns")
```

### Collision example (user_group)

```python
# Standard API operations
groups = client.user_group.list(namespace="system")
group = client.user_group.get(namespace="system", name="admins")

# CustomAPI operations (prefixed due to collision)
custom_groups = client.user_group.custom_list()
custom_group = client.user_group.custom_get(name="admins")
```

## Direct HTTP Access

If you need to call an endpoint that isn't generated correctly, use direct HTTP access:

```python
from f5xc_py_substrate import Client

client = Client()

# POST request
response = client._http.post(
    "/api/some/path/operation",
    json={"param": "value"}
)

# GET request with query params
response = client._http.get(
    "/api/some/path/resource",
    params={"filter": "value"}
)
```
