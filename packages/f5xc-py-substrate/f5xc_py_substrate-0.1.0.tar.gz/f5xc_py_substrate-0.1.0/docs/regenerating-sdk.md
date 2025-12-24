# Regenerating the SDK

The SDK is generated from F5 Distributed Cloud OpenAPI specifications. When F5 updates their API specs, you can regenerate the SDK to pick up new resources and changes.

## Prerequisites

Install the generator dependencies:

```bash
pip install -e ".[generator]"
```

## Usage

### Fetch Latest Specs and Regenerate

```bash
python generate.py
```

This will:
1. Download the latest OpenAPI specs from F5
2. Compare against the cached hash to detect changes
3. Regenerate the SDK if specs have changed

### Force Regeneration

```bash
python generate.py --force
```

Regenerate even if the specs haven't changed (useful after template modifications).

### Use Local OpenAPI Files

```bash
python generate.py --oas-dir ./local-oas
```

Use local OpenAPI specification files instead of fetching from F5 (useful for offline development or testing).

## How It Works

The generator fetches OpenAPI specifications from:
```
https://docs.cloud.f5.com/docs-v2/downloads/f5-distributed-cloud-open-api.zip
```

It computes a SHA256 hash of the downloaded zip and compares it against a cached hash. Regeneration is skipped if unchanged (unless `--force` is used).

## Generator Pipeline

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Fetch OAS zip  │────▶│  Check hash     │────▶│  Generate if    │
│  from F5 docs   │     │  against cached │     │  changed        │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

The generator produces:
- Resource classes with CRUD methods (`f5xc_py_substrate/resources/*/resource.py`)
- Pydantic models for request/response types (`f5xc_py_substrate/resources/*/models.py`)

## Project Structure

```
generator/
├── __init__.py
├── main.py          # Entry point
├── parser.py        # OAS parsing - extracts all operations from specs
├── transformer.py   # Transforms parsed OAS to code generation models
├── renderer.py      # Jinja2 template rendering
└── templates/       # Jinja2 templates for code generation
```

## How Operations Are Processed

The generator processes every operation defined in each OAS file:

1. **Parser** extracts all operations (standard API and CustomAPI) from the spec
2. **Transformer** handles naming:
   - Standard API operations claim base names (`get`, `list`, `create`, etc.)
   - CustomAPI operations get `custom_` prefix if they collide with standard API
   - Duplicates get numeric suffix (`_2`, `_3`, etc.)
3. **Renderer** generates Python code using Jinja2 templates
