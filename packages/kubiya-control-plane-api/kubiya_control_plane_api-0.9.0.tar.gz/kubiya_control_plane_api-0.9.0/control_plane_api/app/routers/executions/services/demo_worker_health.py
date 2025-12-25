#!/usr/bin/env python
"""Demo script for WorkerHealthChecker service

This script demonstrates the WorkerHealthChecker service in action.
It shows health checks, degradation modes, and capabilities.

Usage:
    cd /Users/shaked/projects/agent-control-plane/control_plane_api/app/routers/executions/services
    python demo_worker_health.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from worker_health import (
    WorkerHealthChecker,
    DegradationMode,
    CAPABILITIES,
)


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


async def demo_no_services():
    """Demo: No services available."""
    print_section("Demo 1: No Services Available")

    checker = WorkerHealthChecker(
        temporal_client=None,
        redis_client=None,
        db_session=None,
    )

    print("Checking service health...")
    results = await checker.check_all()
    print(f"  Temporal: {'✓' if results['temporal'] else '✗'}")
    print(f"  Redis: {'✓' if results['redis'] else '✗'}")
    print(f"  Database: {'✓' if results['database'] else '✗'}")

    print("\nDetermining degradation mode...")
    mode = await checker.get_degradation_mode()
    print(f"  Mode: {mode.value}")

    print("\nAvailable capabilities:")
    capabilities = checker.get_capabilities(mode)
    if capabilities:
        for cap in capabilities:
            print(f"  - {cap}")
    else:
        print("  (none)")


async def demo_cache_behavior():
    """Demo: Cache behavior."""
    print_section("Demo 2: Health Check Caching")

    checker = WorkerHealthChecker(
        temporal_client=None,
        redis_client=None,
        db_session=None,
        cache_ttl=5  # 5 second cache
    )

    print("First health check (will hit services)...")
    start = asyncio.get_event_loop().time()
    await checker.check_all()
    duration1 = asyncio.get_event_loop().time() - start
    print(f"  Duration: {duration1:.3f}s")

    print("\nSecond health check (should use cache)...")
    start = asyncio.get_event_loop().time()
    await checker.check_all()
    duration2 = asyncio.get_event_loop().time() - start
    print(f"  Duration: {duration2:.3f}s")

    if duration2 < duration1:
        print(f"  ✓ Cache is working! Second check was faster.")
    else:
        print(f"  ℹ Both checks were similar (expected if services are None)")

    print("\nClearing cache...")
    checker.clear_cache()
    print("  ✓ Cache cleared")

    print("\nThird health check (should hit services again)...")
    start = asyncio.get_event_loop().time()
    await checker.check_all()
    duration3 = asyncio.get_event_loop().time() - start
    print(f"  Duration: {duration3:.3f}s")


async def demo_all_degradation_modes():
    """Demo: All degradation modes."""
    print_section("Demo 3: All Degradation Modes")

    print("Degradation mode capabilities:\n")

    for mode in DegradationMode:
        capabilities = CAPABILITIES.get(mode, [])
        print(f"{mode.value.upper()}")
        print(f"  Capabilities: {', '.join(capabilities) if capabilities else 'none'}")
        print()


async def demo_timeout_behavior():
    """Demo: Timeout behavior simulation."""
    print_section("Demo 4: Timeout Behavior")

    print("Health check timeouts:")
    print(f"  Temporal: {WorkerHealthChecker.TEMPORAL_TIMEOUT}s")
    print(f"  Redis: {WorkerHealthChecker.REDIS_TIMEOUT}s")
    print(f"  Database: {WorkerHealthChecker.DATABASE_TIMEOUT}s")

    print("\nThese timeouts ensure the API remains responsive even when")
    print("services are down or slow. Without timeouts, a client request")
    print("could hang for 30+ seconds waiting for services to fail.")


async def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("  WorkerHealthChecker Service Demo")
    print("=" * 60)
    print("\nThis demo shows how the WorkerHealthChecker service works.")
    print("It demonstrates health checks, degradation modes, and caching.")

    try:
        await demo_no_services()
        await demo_cache_behavior()
        await demo_all_degradation_modes()
        await demo_timeout_behavior()

        print_section("Demo Complete")
        print("✓ All demos completed successfully")
        print("\nFor integration examples, see:")
        print("  - USAGE_EXAMPLE.md")
        print("  - test_worker_health.py")
        print()

    except Exception as e:
        print(f"\n✗ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
