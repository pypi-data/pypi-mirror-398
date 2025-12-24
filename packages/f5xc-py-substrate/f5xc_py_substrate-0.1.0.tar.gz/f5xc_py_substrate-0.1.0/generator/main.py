"""Main entry point for the SDK generator."""

from __future__ import annotations

import argparse
import hashlib
import io
import sys
import zipfile
from pathlib import Path

import httpx

from generator.parser import parse_oas_directory
from generator.renderer import Renderer
from generator.transformer import transform_all

# F5 XC OAS download URL
OAS_URL = "https://docs.cloud.f5.com/docs-v2/downloads/f5-distributed-cloud-open-api.zip"

# Paths
GENERATOR_DIR = Path(__file__).parent
OAS_CACHE_DIR = GENERATOR_DIR / ".oas_cache"
OAS_HASH_FILE = GENERATOR_DIR / ".oas_hash"
OUTPUT_DIR = GENERATOR_DIR.parent / "f5xc_py_substrate"


def fetch_oas_zip() -> bytes:
    """Fetch OAS zip from F5 documentation."""
    print(f"Fetching OAS from {OAS_URL}...")
    response = httpx.get(OAS_URL, follow_redirects=True, timeout=60.0)
    response.raise_for_status()
    print(f"Downloaded {len(response.content)} bytes")
    return response.content


def compute_hash(data: bytes) -> str:
    """Compute SHA256 hash of data."""
    return hashlib.sha256(data).hexdigest()


def get_cached_hash() -> str | None:
    """Get the cached OAS hash, if any."""
    if OAS_HASH_FILE.exists():
        return OAS_HASH_FILE.read_text().strip()
    return None


def save_hash(hash_value: str) -> None:
    """Save the OAS hash."""
    OAS_HASH_FILE.write_text(hash_value)


def extract_zip(zip_data: bytes, output_dir: Path) -> None:
    """Extract OAS zip to output directory."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Clear existing files
    for f in output_dir.glob("*.json"):
        f.unlink()

    with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
        for name in zf.namelist():
            if name.endswith(".json"):
                # Extract to flat directory structure
                content = zf.read(name)
                filename = Path(name).name
                (output_dir / filename).write_bytes(content)

    print(f"Extracted OAS files to {output_dir}")


def generate(oas_dir: Path, output_dir: Path) -> None:
    """Generate SDK from OAS files."""
    print(f"Parsing OAS files from {oas_dir}...")
    parsed = parse_oas_directory(oas_dir)
    print(f"Parsed {len(parsed)} resources")

    print("Transforming to resource definitions...")
    resources = transform_all(parsed)
    print(f"Transformed {len(resources)} resources")

    print(f"Rendering to {output_dir}...")
    renderer = Renderer(output_dir)
    renderer.render_all(resources)

    print(f"Generated {len(resources)} resources")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate F5 XC Python SDK from OpenAPI specifications"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force regeneration even if OAS unchanged",
    )
    parser.add_argument(
        "--oas-dir",
        type=Path,
        help="Use local OAS directory instead of fetching",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help="Output directory for generated SDK",
    )
    args = parser.parse_args()

    try:
        if args.oas_dir:
            # Use local OAS files
            if not args.oas_dir.exists():
                print(f"Error: OAS directory not found: {args.oas_dir}")
                return 1
            generate(args.oas_dir, args.output_dir)
        else:
            # Fetch from F5
            zip_data = fetch_oas_zip()
            current_hash = compute_hash(zip_data)

            if not args.force and get_cached_hash() == current_hash:
                print("OAS unchanged, skipping generation (use --force to override)")
                return 0

            extract_zip(zip_data, OAS_CACHE_DIR)
            generate(OAS_CACHE_DIR, args.output_dir)
            save_hash(current_hash)

        print("Done!")
        return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
