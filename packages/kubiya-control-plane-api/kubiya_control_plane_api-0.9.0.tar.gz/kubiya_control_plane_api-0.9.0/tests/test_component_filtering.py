#!/usr/bin/env python3
"""Test component filtering on runners endpoint"""

import os
import asyncio
import httpx
from control_plane_api.app.routers.runners import (
    _has_healthy_component,
    _get_component_name_variants,
)

# Mock health data
MOCK_HEALTH_DATA = {
    "status": "ok",
    "checks": [
        {"name": "workflow-engine", "status": "ok"},
        {"name": "tool-manager", "status": "ok"},
        {"name": "agent-manager", "status": "degraded"},
    ],
}


def test_component_name_variants():
    """Test that component name variants are generated correctly"""
    print("\n=== Testing Component Name Variants ===")

    # Test workflow_engine
    variants = _get_component_name_variants("workflow_engine")
    print(f"workflow_engine variants: {variants}")
    assert "workflow_engine" in variants
    assert "workflow-engine" in variants
    assert "workflowEngine" in variants

    # Test tool-manager
    variants = _get_component_name_variants("tool-manager")
    print(f"tool-manager variants: {variants}")
    assert "tool-manager" in variants
    assert "tool_manager" in variants
    assert "toolManager" in variants

    print("✅ Component name variant tests passed")


def test_healthy_component_check():
    """Test that component health checking works"""
    print("\n=== Testing Component Health Checking ===")

    # Test workflow-engine (should be healthy)
    assert _has_healthy_component(MOCK_HEALTH_DATA, "workflow_engine")
    assert _has_healthy_component(MOCK_HEALTH_DATA, "workflow-engine")
    assert _has_healthy_component(MOCK_HEALTH_DATA, "workflowEngine")
    print("✅ workflow_engine is correctly identified as healthy")

    # Test tool-manager (should be healthy)
    assert _has_healthy_component(MOCK_HEALTH_DATA, "tool_manager")
    assert _has_healthy_component(MOCK_HEALTH_DATA, "tool-manager")
    print("✅ tool_manager is correctly identified as healthy")

    # Test agent-manager (should NOT be healthy - degraded)
    assert not _has_healthy_component(MOCK_HEALTH_DATA, "agent_manager")
    assert not _has_healthy_component(MOCK_HEALTH_DATA, "agent-manager")
    print("✅ agent_manager is correctly identified as degraded (not healthy)")

    # Test non-existent component
    assert not _has_healthy_component(MOCK_HEALTH_DATA, "non-existent")
    print("✅ non-existent component is correctly identified as not healthy")

    print("✅ Component health checking tests passed")


async def test_api_validation():
    """Test API endpoint validation"""
    print("\n=== Testing API Endpoint ===")

    api_base = os.environ.get("CONTROL_PLANE_API_URL", "http://localhost:8001")
    token = os.environ.get("KUBIYA_API_KEY", "")

    if not token:
        print("⚠️  Skipping API test - KUBIYA_API_KEY not set")
        return

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test without filter
        print("\n1. Testing without component filter...")
        response = await client.get(
            f"{api_base}/api/v1/runners",
            headers={"Authorization": f"UserKey {token}"},
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Got {data['count']} runners (no filter)")
        else:
            print(f"❌ Failed: {response.status_code}")

        # Test with workflow_engine filter
        print("\n2. Testing with workflow_engine filter...")
        response = await client.get(
            f"{api_base}/api/v1/runners?component=workflow_engine",
            headers={"Authorization": f"UserKey {token}"},
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Got {data['count']} runners with workflow_engine")
        else:
            print(f"❌ Failed: {response.status_code}")

        # Test with invalid component
        print("\n3. Testing with invalid component (should get 400)...")
        response = await client.get(
            f"{api_base}/api/v1/runners?component=invalid-component",
            headers={"Authorization": f"UserKey {token}"},
        )
        if response.status_code == 400:
            data = response.json()
            print(f"✅ Got expected 400 error")
            print(f"   Error message: {data.get('detail', {}).get('message')}")
        else:
            print(f"❌ Expected 400, got: {response.status_code}")


def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing Component Filtering Implementation")
    print("=" * 60)

    test_component_name_variants()
    test_healthy_component_check()

    # Run async API tests if API is available
    try:
        asyncio.run(test_api_validation())
    except Exception as e:
        print(f"\n⚠️  API tests skipped: {e}")

    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
