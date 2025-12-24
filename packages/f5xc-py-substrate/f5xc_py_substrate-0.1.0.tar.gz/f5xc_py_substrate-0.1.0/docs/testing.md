# Testing

## Unit Tests

Unit tests run fast and don't require network access. They test SDK mechanics with mocked HTTP responses.

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run unit tests
pytest tests/unit/ -v
```

## Integration Tests

Integration tests validate the SDK against a real F5 XC tenant.

### Prerequisites

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your F5 XC credentials:
   ```bash
   F5XC_TENANT_URL=https://your-tenant.console.ves.volterra.io
   F5XC_API_TOKEN=your-api-token
   ```

### Running Integration Tests

```bash
./scripts/run-integration-tests.sh
```

This script will:
1. Load credentials from `.env`
2. Create a temporary test namespace
3. Run all integration tests
4. Clean up the test namespace
5. Generate coverage reports

### Test Namespace Lifecycle

Integration tests use namespace isolation:
1. A test namespace is created (e.g., `sdk-test-1702825852`)
2. All namespaced resource tests use that namespace
3. On teardown, the namespace is cascade-deleted, cleaning up all resources

## Coverage Reports

After running integration tests, coverage reports are generated in `docs/test-results/`:

- `coverage.json` - Raw test results in JSON format
- `coverage.md` - Human-readable Markdown report

## Current Test Coverage

Integration tests use a spec-based system:
- **229 test files** in `tests/integration/`
- **166 spec YAML files** in `tests/integration/specs/`

Spec statuses:
- **complete** (3): Manually validated specs that pass all tests
- **generated** (136): Auto-generated from F5 API docs, tests run but may need adjustment
- **missing** (26): No spec available, tests are skipped
- **blocked** (1): Cannot test due to permissions or dependencies

See `docs/test-results/coverage.md` for detailed results after running tests.

## Adding New Integration Tests

Tests are located in `tests/integration/`. Each resource has its own test file:

```
tests/integration/
├── conftest.py              # Fixtures: client, test namespace
├── fixtures/
│   └── spec_registry.py     # Spec loading utility
├── specs/                   # YAML spec templates
│   ├── healthcheck.yaml
│   ├── origin_pool.yaml
│   └── {resource}.yaml
├── test_namespace.py
├── test_http_loadbalancer.py
└── test_{resource}.py       # Generated test files
```

## Test Execution Order

Tests use `@pytest.mark.order()` to control execution order across all test files. This ensures:
1. Dependencies are created before resources that reference them
2. Delete tests run after all CRUD tests complete
3. Dependent resources are deleted before their dependencies

### Order Numbering Scheme

Each test method has its own order number:
- **CRUD tests**: Lower order numbers (100-9999 range)
- **Delete tests**: Higher order numbers (98000-99999 range)

Resources are ordered alphabetically by default, with dependencies always running before dependents.

Example for `origin_pool` (no dependencies) and `tcp_loadbalancer` (depends on origin_pool):
```
origin_pool:     test_create=1440, test_get=1441, test_list=1442, test_replace=1443
tcp_loadbalancer: test_create=1920, test_get=1921, test_list=1922, test_replace=1923
tcp_loadbalancer: test_delete=98080  (runs first - deletes dependent)
origin_pool:     test_delete=98560  (runs second - deletes dependency)
```

### Dependency System

Resources can declare dependencies in their spec files:

```yaml
resource: tcp_loadbalancer
dependencies:
  - origin_pool  # Must exist before tcp_loadbalancer can be created
```

The dependency graph module (`tests/integration/fixtures/dependency_graph.py`) provides utilities for:
- Building the dependency graph from spec files
- Topological sorting of resources
- Generating correct order numbers

### Updating Test Order

When adding new resources or dependencies:

```bash
# See what changes would be made
python scripts/generate_test_order.py --dry-run

# Update all test files with new order values
python scripts/generate_test_order.py

# View the dependency graph
python scripts/generate_test_order.py --show-graph
```

### Enabling Tests for a Resource

To enable tests for a resource that's currently skipped:

1. Create or edit the spec file in `tests/integration/specs/{resource}.yaml`
2. Set the status to `generated` or `complete`
3. Add valid `create` and `replace` specs
4. Run the tests: `pytest tests/integration/test_{resource}.py -v`

### Regenerating Test Files

Test files are generated from `generator/templates/test_resource.py.j2`. To regenerate:

```bash
python generator/test_generator.py --resource {resource}  # Single resource
python generator/test_generator.py --all                   # All resources
```

## Spec YAML Reference

Each resource has a spec file in `tests/integration/specs/`. The spec defines the request body for create and replace operations.

### Format

```yaml
resource: healthcheck
is_namespaced: true
dependencies: []           # Resources that must be created first
status: complete           # complete | partial | generated | missing | blocked
notes: "Optional notes about the spec"
spec:
  create:
    # Minimal valid spec for create operation
    http_health_check:
      use_origin_server_name: {}
      path: "/health"
    timeout: 3
    interval: 15
  replace:
    # Spec for replace operation (should differ from create to verify update)
    http_health_check:
      use_origin_server_name: {}
      path: "/healthz"     # Changed value to verify replace works
    timeout: 5
    interval: 15
```

### Status Values

| Status | Meaning | Test Behavior |
|--------|---------|---------------|
| `complete` | Manually validated, all CRUD works | Tests run normally |
| `partial` | Some operations work | Tests run, some may fail |
| `generated` | Auto-generated from API docs | Tests run, may need adjustment |
| `missing` | No spec available | All tests skipped |
| `blocked` | Cannot test (permissions, etc.) | All tests skipped with reason |

### Template Variables

Specs support the `{test_namespace}` placeholder which is replaced with the actual test namespace at runtime:

```yaml
spec:
  create:
    origin_servers:
      - public_name:
          dns_name: "example.com"
        labels:
          namespace: "{test_namespace}"  # Will be replaced
```

### Updating a Generated Spec

Many specs were auto-generated from F5 API documentation. To fix a failing test:

1. Run the test to see the error: `pytest tests/integration/test_{resource}.py -v`
2. Check the F5 API documentation for required fields
3. Edit `tests/integration/specs/{resource}.yaml` with valid values
4. Update status to `complete` when all operations pass

### Marking a Resource as Blocked

If a resource cannot be tested (requires specific permissions, cloud resources, etc.):

```yaml
resource: aws_vpc_site
status: blocked
notes: "Requires AWS credentials and creates real cloud resources"
spec:
  create: null
  replace: null
```

## Delete Tests

Each test class includes a `test_delete` method that:
1. Deletes the resource created during `test_create`
2. Verifies the resource is deleted by expecting a 404 response
3. Runs after ALL CRUD tests complete (for all resources)
4. Runs in reverse dependency order (dependents deleted before dependencies)

### Non-Namespaced Resources

Delete tests for non-namespaced resources (like `namespace` itself) are marked with `@pytest.mark.skip` for safety. These resources operate at the tenant level and should not be deleted during tests.

### Delete Test Safety

The delete tests are designed to only affect resources created within the test namespace (`sdk-test-{timestamp}`). The test namespace itself is cleaned up via `cascade_delete` at session end, providing a safety net.

## Migrating to Method-Level Ordering

The test framework uses method-level `@pytest.mark.order()` decorators. If you need to migrate test files or update ordering:

```bash
# Migrate class-level order to method-level (one-time migration)
python scripts/migrate_order_to_methods.py --dry-run
python scripts/migrate_order_to_methods.py

# Add delete tests to test files
python scripts/add_delete_tests.py --dry-run
python scripts/add_delete_tests.py

# Update order values based on dependency graph
python scripts/generate_test_order.py --dry-run
python scripts/generate_test_order.py
```
