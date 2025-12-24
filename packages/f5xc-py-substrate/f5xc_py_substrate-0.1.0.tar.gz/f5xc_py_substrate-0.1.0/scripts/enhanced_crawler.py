#!/usr/bin/env python3
"""Enhanced parallel crawler for F5 XC tenant resource discovery.

This script crawls an F5 XC tenant to:
1. Discover all namespaces automatically
2. Crawl all SDK resources systematically
3. Save raw JSON data for dependency analysis
4. Support resume from checkpoints

Usage:
    # Full crawl with 4 parallel workers
    python scripts/enhanced_crawler.py --full --env-file .env.crawl

    # Resume interrupted crawl
    python scripts/enhanced_crawler.py --resume --env-file .env.crawl

    # Crawl specific resources
    python scripts/enhanced_crawler.py --resources origin_pool,http_loadbalancer

    # Custom workers and delay
    python scripts/enhanced_crawler.py --full --workers 4 --delay 0.5
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Paths
DATA_DIR = PROJECT_ROOT / "data"
CRAWLED_DIR = DATA_DIR / "crawled"
MANIFEST_FILE = DATA_DIR / "crawl_manifest.json"
RESOURCES_DIR = PROJECT_ROOT / "f5xc_py_substrate" / "resources"

# Default settings
DEFAULT_WORKERS = 4
DEFAULT_DELAY = 0.5  # seconds between API calls per worker

# Namespaces to skip (system namespaces)
SKIP_NAMESPACES = {
    "system",
    "shared",
    "ves-io-system",
}


def get_all_sdk_resources() -> list[str]:
    """Get all resource names from the SDK resources directory."""
    resources = []
    for item in RESOURCES_DIR.iterdir():
        if item.is_dir() and not item.name.startswith("_"):
            # Verify it has resource.py
            if (item / "resource.py").exists():
                resources.append(item.name)
    return sorted(resources)


def load_manifest() -> dict[str, Any]:
    """Load the crawl manifest for resume capability."""
    if MANIFEST_FILE.exists():
        with open(MANIFEST_FILE) as f:
            return json.load(f)
    return {
        "started_at": None,
        "completed_at": None,
        "namespaces": [],
        "resources": {},
        "status": "not_started",
    }


def save_manifest(manifest: dict[str, Any]) -> None:
    """Save the crawl manifest."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_FILE, "w") as f:
        json.dump(manifest, f, indent=2, default=str)


class EnhancedCrawler:
    """Parallel crawler for F5 XC tenant resources."""

    def __init__(
        self,
        env_file: str = ".env.crawl",
        workers: int = DEFAULT_WORKERS,
        delay: float = DEFAULT_DELAY,
    ):
        self.env_file = env_file
        self.workers = workers
        self.delay = delay
        self.client = None
        self.manifest = load_manifest()
        self.namespaces: list[str] = []
        self._lock = asyncio.Lock()

    def connect(self) -> None:
        """Connect to the F5 XC tenant."""
        load_dotenv(self.env_file)
        from f5xc_py_substrate import Client

        self.client = Client()
        print(f"Connected to tenant: {os.environ.get('F5XC_TENANT_URL', 'unknown')}")

    def discover_namespaces(self) -> list[str]:
        """Discover all non-system namespaces."""
        print("Discovering namespaces...")
        namespaces = self.client.namespace.list()

        discovered = []
        for ns in namespaces:
            name = ns.name
            if name and name not in SKIP_NAMESPACES:
                discovered.append(name)

        print(f"Found {len(discovered)} namespaces")
        self.namespaces = discovered
        self.manifest["namespaces"] = discovered
        save_manifest(self.manifest)
        return discovered

    def get_resources_to_crawl(self, resources: list[str] | None = None) -> list[str]:
        """Get list of resources to crawl."""
        if resources:
            return resources

        # Get all SDK resources
        all_resources = get_all_sdk_resources()
        print(f"Found {len(all_resources)} SDK resources")

        # Check manifest for already completed resources
        completed = set()
        for res, data in self.manifest.get("resources", {}).items():
            if data.get("status") == "completed":
                completed.add(res)

        remaining = [r for r in all_resources if r not in completed]
        print(f"{len(remaining)} resources remaining to crawl")

        return remaining

    def split_resources(self, resources: list[str]) -> list[list[str]]:
        """Split resources into batches for parallel workers."""
        if not resources:
            return []

        batch_size = max(1, len(resources) // self.workers + 1)
        batches = []
        for i in range(0, len(resources), batch_size):
            batches.append(resources[i : i + batch_size])
        return batches

    async def crawl_resource_in_namespace(
        self, resource_type: str, namespace: str
    ) -> dict[str, Any] | None:
        """Try to crawl a resource from a specific namespace."""
        resource_client = getattr(self.client, resource_type, None)
        if not resource_client:
            return None

        try:
            # Check if resource has list method with namespace param
            if not hasattr(resource_client, "list"):
                return None

            # Try to list resources in namespace
            items = resource_client.list(namespace=namespace)
            if not items:
                return None

            # Get the first item's details
            first_name = items[0].name
            if not first_name:
                return None

            result = resource_client.get(namespace=namespace, name=first_name)

            # Convert to dict
            if hasattr(result, "model_dump"):
                return result.model_dump()
            elif hasattr(result, "__dict__"):
                return result.__dict__
            return None

        except Exception:
            return None

    async def crawl_resource_non_namespaced(
        self, resource_type: str
    ) -> dict[str, Any] | None:
        """Try to crawl a non-namespaced resource."""
        resource_client = getattr(self.client, resource_type, None)
        if not resource_client:
            return None

        try:
            # Try list without namespace
            if hasattr(resource_client, "list"):
                try:
                    items = resource_client.list()
                    if items and len(items) > 0:
                        first_name = getattr(items[0], "name", None)
                        if first_name and hasattr(resource_client, "get"):
                            result = resource_client.get(name=first_name)
                            if hasattr(result, "model_dump"):
                                return result.model_dump()
                            return result.__dict__ if hasattr(result, "__dict__") else None
                except TypeError:
                    # list() requires namespace - this is namespaced
                    pass
        except Exception:
            pass

        return None

    async def crawl_single_resource(
        self, resource_type: str, worker_id: int
    ) -> dict[str, Any]:
        """Crawl a single resource across all namespaces."""
        result = {
            "resource": resource_type,
            "status": "not_found",
            "namespace": None,
            "name": None,
            "data": None,
            "crawled_at": datetime.now().isoformat(),
        }

        # Try namespaced first
        for namespace in self.namespaces:
            data = await self.crawl_resource_in_namespace(resource_type, namespace)
            if data:
                result["status"] = "found"
                result["namespace"] = namespace
                result["name"] = data.get("metadata", {}).get("name")
                result["data"] = data
                break
            await asyncio.sleep(self.delay)

        # If not found in namespaces, try non-namespaced
        if result["status"] == "not_found":
            data = await self.crawl_resource_non_namespaced(resource_type)
            if data:
                result["status"] = "found"
                result["namespace"] = None
                result["name"] = data.get("metadata", {}).get("name")
                result["data"] = data

        return result

    def save_crawled_data(self, resource_type: str, result: dict[str, Any]) -> None:
        """Save crawled data to disk."""
        if result["status"] != "found" or not result["data"]:
            return

        # Create directory structure
        resource_dir = CRAWLED_DIR / resource_type
        resource_dir.mkdir(parents=True, exist_ok=True)

        # Save the data
        namespace = result["namespace"] or "_global"
        name = result["name"] or "unknown"
        filename = f"{namespace}__{name}.json"

        with open(resource_dir / filename, "w") as f:
            json.dump(result["data"], f, indent=2, default=str)

    async def update_manifest(
        self, resource_type: str, result: dict[str, Any]
    ) -> None:
        """Update the manifest with crawl result."""
        async with self._lock:
            self.manifest["resources"][resource_type] = {
                "status": "completed" if result["status"] == "found" else "not_found",
                "namespace": result["namespace"],
                "name": result["name"],
                "crawled_at": result["crawled_at"],
            }
            save_manifest(self.manifest)

    async def crawl_batch(self, batch: list[str], worker_id: int) -> list[dict]:
        """Crawl a batch of resources with rate limiting."""
        results = []
        total = len(batch)

        for i, resource_type in enumerate(batch):
            print(f"[Worker {worker_id}] Crawling {resource_type} ({i + 1}/{total})")

            result = await self.crawl_single_resource(resource_type, worker_id)
            results.append(result)

            # Save data if found
            if result["status"] == "found":
                self.save_crawled_data(resource_type, result)
                print(
                    f"[Worker {worker_id}] Found {resource_type} in {result['namespace'] or 'global'}"
                )
            else:
                print(f"[Worker {worker_id}] Not found: {resource_type}")

            # Update manifest
            await self.update_manifest(resource_type, result)

            # Rate limiting (already done in crawl_single_resource, but add buffer)
            await asyncio.sleep(0.1)

        return results

    async def run_parallel_crawl(self, resources: list[str]) -> dict[str, Any]:
        """Run parallel crawl across all resources."""
        batches = self.split_resources(resources)
        print(f"Splitting {len(resources)} resources across {len(batches)} workers")

        # Update manifest
        self.manifest["started_at"] = datetime.now().isoformat()
        self.manifest["status"] = "in_progress"
        save_manifest(self.manifest)

        # Create tasks for each batch
        tasks = [
            self.crawl_batch(batch, worker_id)
            for worker_id, batch in enumerate(batches)
        ]

        # Run all workers in parallel
        all_results = await asyncio.gather(*tasks)

        # Flatten results
        results = []
        for batch_results in all_results:
            results.extend(batch_results)

        # Update manifest
        self.manifest["completed_at"] = datetime.now().isoformat()
        self.manifest["status"] = "completed"
        save_manifest(self.manifest)

        return {
            "total": len(results),
            "found": sum(1 for r in results if r["status"] == "found"),
            "not_found": sum(1 for r in results if r["status"] == "not_found"),
        }


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Enhanced parallel crawler for F5 XC tenant"
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Crawl all SDK resources",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume interrupted crawl",
    )
    parser.add_argument(
        "--resources",
        type=str,
        help="Specific resources to crawl, comma-separated",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_WORKERS,
        help=f"Number of parallel workers (default: {DEFAULT_WORKERS})",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=DEFAULT_DELAY,
        help=f"Delay between API calls per worker (default: {DEFAULT_DELAY}s)",
    )
    parser.add_argument(
        "--env-file",
        type=str,
        default=".env.crawl",
        help="Path to env file for credentials (default: .env.crawl)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be crawled without making API calls",
    )

    args = parser.parse_args()

    if not (args.full or args.resume or args.resources):
        parser.print_help()
        return 1

    # Create crawler
    crawler = EnhancedCrawler(
        env_file=args.env_file,
        workers=args.workers,
        delay=args.delay,
    )

    # Determine resources to crawl
    if args.resources:
        resources = [r.strip() for r in args.resources.split(",")]
    else:
        resources = None  # Will get all SDK resources

    if args.dry_run:
        resources_to_crawl = crawler.get_resources_to_crawl(resources)
        print(f"\nWould crawl {len(resources_to_crawl)} resources with {args.workers} workers:")
        for r in resources_to_crawl[:20]:
            print(f"  - {r}")
        if len(resources_to_crawl) > 20:
            print(f"  ... and {len(resources_to_crawl) - 20} more")
        return 0

    # Connect to tenant
    print(f"Connecting using {args.env_file}...")
    try:
        crawler.connect()
    except Exception as e:
        print(f"Failed to connect: {e}")
        return 1

    # Discover namespaces
    crawler.discover_namespaces()

    # Get resources to crawl
    resources_to_crawl = crawler.get_resources_to_crawl(resources)

    if not resources_to_crawl:
        print("No resources to crawl")
        return 0

    print(f"\nStarting parallel crawl of {len(resources_to_crawl)} resources...")
    print(f"Workers: {args.workers}, Delay: {args.delay}s")
    print(f"Estimated time: ~{len(resources_to_crawl) * args.delay / args.workers:.0f} seconds\n")

    # Run the crawl
    start_time = time.time()
    results = asyncio.run(crawler.run_parallel_crawl(resources_to_crawl))
    elapsed = time.time() - start_time

    # Summary
    print(f"\n{'=' * 50}")
    print(f"Crawl Complete!")
    print(f"{'=' * 50}")
    print(f"Total resources: {results['total']}")
    print(f"Found: {results['found']}")
    print(f"Not found: {results['not_found']}")
    print(f"Elapsed time: {elapsed:.1f} seconds")
    print(f"\nData saved to: {CRAWLED_DIR}")
    print(f"Manifest saved to: {MANIFEST_FILE}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
