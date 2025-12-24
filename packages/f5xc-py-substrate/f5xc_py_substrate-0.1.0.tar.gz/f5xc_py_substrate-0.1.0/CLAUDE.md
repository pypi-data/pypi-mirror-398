# CLAUDE.md

## Project Overview

Python SDK for F5 Distributed Cloud (XC) APIs. The SDK is auto-generated from F5's OpenAPI specifications using a custom generator pipeline.

- **250+ resources** generated from OpenAPI specs
- **All operations** - both standard CRUD and CustomAPI operations
- **Pydantic v2 models** for typed request/response handling
- **Lazy loading** for fast startup
- **Python 3.9+** compatible

## Key Commands

```bash
# Activate virtual environment
source .venv/bin/activate

# Run unit tests
pytest tests/unit/ -v

# Run integration tests (requires F5 XC credentials in .env)
./scripts/run-integration-tests.sh

# Regenerate SDK from latest F5 OpenAPI specs
pip install -e ".[generator]"
python generate.py

# Force regeneration
python generate.py --force
```

## Project Structure

```
f5xc-py-substrate/
├── f5xc_py_substrate/           # Generated SDK package
│   ├── client.py             # Main client with lazy resource loading
│   ├── exceptions.py         # Typed exceptions (F5XCNotFoundError, etc.)
│   ├── _http.py              # httpx wrapper
│   └── resources/            # 250+ generated resource modules
│       └── {resource}/
│           ├── resource.py   # CRUD methods
│           └── models.py     # Pydantic models
├── generator/                # Code generator
│   ├── main.py               # Entry point
│   ├── parser.py             # OAS parsing
│   ├── renderer.py           # Jinja2 rendering
│   └── templates/            # Code templates
├── tests/
│   ├── unit/                 # Fast, mocked tests
│   └── integration/          # Real tenant tests
│       ├── conftest.py       # Pytest fixtures and test client
│       ├── specs/            # YAML test specifications per resource
│       └── fixtures/         # Test fixtures (dependency_graph.py)
├── scripts/
│   ├── run-integration-tests.sh    # Integration test runner
│   ├── generate_coverage_report.py # Coverage report generator
│   ├── crawl_tenant_specs.py       # Crawl tenant for test specs
│   ├── enhanced_crawler.py         # Enhanced spec crawler
│   ├── dependency_analyzer.py      # Analyze resource dependencies
│   ├── add_delete_tests.py         # Add delete test methods
│   ├── add_dependency_markers.py   # Add pytest dependency markers
│   └── generate_test_order.py      # Generate test execution order
├── docs/
│   ├── advanced-usage.md     # Error handling, custom HTTP
│   ├── regenerating-sdk.md   # SDK regeneration
│   ├── testing.md            # Test instructions
│   └── test-results/         # Test output (coverage reports)
└── data/                     # Data files (gitkeep only)
```

## Development Workflow

This project follows an issue-based development workflow.

### IMPORTANT: Always Use Feature Branches

**NEVER commit directly to `staging` or `main`.** Always create a feature branch first.

```bash
# Correct workflow
git checkout staging
git pull origin staging
git checkout -b feature/my-feature-name
# ... make changes ...
git add -A && git commit -m "Add feature"
git push origin feature/my-feature-name
gh pr create --base staging --title "Add feature"
gh pr merge --merge
```

### Branching Strategy
1. **Create Issue First**: All work starts with a GitHub issue (when applicable)
2. **Branch from Staging**: Create feature branches from `staging`
3. **PR to Staging**: All feature branches must PR into `staging`, never directly to `main`
4. **Staging to Main**: Only `staging` branch PRs to `main` for releases
5. **Branch Naming**: Use descriptive prefixes followed by concise description
   - `feature/add-metrics-endpoint`
   - `bug/fix-authentication-timeout`
   - `docs/update-readme`
   - `refactor/simplify-config-parsing`
   - `chore/update-dependencies`

### Development Process
1. Create or assign yourself to an issue
2. **Create branch from staging**: `git checkout staging && git pull && git checkout -b feature/your-feature-name`
3. Implement changes with clear, atomic commits
4. Push branch and create Pull Request targeting `staging` branch
5. PR review and merge to `staging`
6. Delete feature branch after merge
7. Periodically, `staging` is PR'd and merged to `main` for releases

### Branch Naming Guidelines
- Use lowercase with hyphens
- Start with type prefix (`feature/`, `bug/`, `docs/`, `refactor/`, `chore/`)
- Keep descriptions concise but clear about purpose
- Examples: `feature/prometheus-metrics`, `bug/connection-leak`, `docs/api-examples`

## Code Patterns

### SDK Usage
```python
from f5xc_py_substrate import Client

client = Client()  # Uses F5XC_TENANT_URL and F5XC_API_TOKEN env vars
lbs = client.http_loadbalancer.list(namespace="default")
```

### Error Handling
```python
from f5xc_py_substrate.exceptions import F5XCNotFoundError, F5XCError

try:
    lb = client.http_loadbalancer.get(namespace="ns", name="missing")
except F5XCNotFoundError:
    # Handle 404
except F5XCError as e:
    # Handle any API error
    print(f"{e.status_code}: {e.message}")
```

## Environment Variables

- `F5XC_TENANT_URL` - F5 XC tenant URL (e.g., `https://tenant.console.ves.volterra.io`)
- `F5XC_API_TOKEN` - API token for authentication

For integration tests, copy `.env.example` to `.env` and fill in credentials.

## Code Patterns to Avoid

### Don't Add Properties to Base Model with Common Field Names

Never add `@property` methods to `F5XCBaseModel` using names that are common fields in API responses (e.g., `name`, `namespace`, `labels`, `description`). This causes Pydantic to emit thousands of "shadows an attribute" warnings because many generated models have fields with these names.

If convenience accessors are needed, use a different naming convention:
- Use method syntax: `get_name()`, `get_namespace()`
- Use prefixed properties: `meta_name`, `meta_namespace`
- Or simply document that users should access via `model.metadata.name`
