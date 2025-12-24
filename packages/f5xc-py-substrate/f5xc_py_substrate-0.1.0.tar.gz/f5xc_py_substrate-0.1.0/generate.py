#!/usr/bin/env python3
"""Generate F5 XC Python SDK from OpenAPI specifications.

Usage:
    python generate.py              # Fetch OAS from F5 and generate
    python generate.py --force      # Force regeneration
    python generate.py --oas-dir ./f5xc-OAS  # Use local OAS files
"""

from generator.main import main

if __name__ == "__main__":
    raise SystemExit(main())
