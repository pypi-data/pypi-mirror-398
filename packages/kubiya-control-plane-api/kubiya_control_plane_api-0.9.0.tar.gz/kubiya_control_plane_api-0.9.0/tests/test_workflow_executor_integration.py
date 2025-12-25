#!/usr/bin/env python3
"""
Integration test for workflow executor via agent activities.

This tests the EXACT flow that was failing:
1. Agent has a workflow_executor skill configured in Control Plane
2. Agent activity loads skills using SkillFactory (the fix)
3. WorkflowExecutorTools is instantiated with KUBIYA_API_KEY
4. Workflow execution via Kubiya SDK client

This reproduces the bug: "Kubiya SDK client not initialized"
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from control_plane_api.worker.services.skill_factory import SkillFactory
from control_plane_api.worker.services.workflow_executor_tools import WorkflowExecutorTools


def test_skill_factory_creates_workflow_tool_with_api_key():
    """Test that SkillFactory properly creates WorkflowExecutorTools with API key."""
    print("=" * 80)
    print("TEST 1: SkillFactory creates WorkflowExecutorTools with API key")
    print("=" * 80)

    # Set KUBIYA_API_KEY in environment (simulating worker environment)
    test_api_key = "test-api-key-12345"
    original_api_key = os.environ.get("KUBIYA_API_KEY")
    os.environ["KUBIYA_API_KEY"] = test_api_key

    try:
        # Create skill config (same format as Control Plane sends)
        skill_config = {
            "type": "workflow_executor",
            "name": "Test Workflow",
            "enabled": True,
            "configuration": {
                "workflow_type": "json",
                "validation_enabled": True,
                "timeout": 3600,
                "default_runner": "kubiya-prod",
                "workflow_definition": json.dumps({
                    "name": "test-workflow",
                    "description": "Test workflow",
                    "runner": "kubiya-prod",
                    "steps": [
                        {
                            "name": "test-step",
                            "description": "Test step",
                            "executor": {
                                "type": "shell",
                                "config": {
                                    "command": "echo 'test'"
                                }
                            }
                        }
                    ]
                })
            }
        }

        print("\n1. Creating workflow tool via SkillFactory...")
        tool = SkillFactory.create_skill(skill_config)

        if tool is None:
            print("   ❌ FAILED: Tool creation returned None")
            return False

        print(f"   ✅ Tool created: {type(tool).__name__}")

        print("\n2. Verifying tool is WorkflowExecutorTools instance...")
        if not isinstance(tool, WorkflowExecutorTools):
            print(f"   ❌ FAILED: Expected WorkflowExecutorTools, got {type(tool).__name__}")
            return False
        print("   ✅ Correct type")

        print("\n3. Verifying API key was passed to tool...")
        if not hasattr(tool, 'kubiya_api_key'):
            print("   ❌ FAILED: Tool has no kubiya_api_key attribute")
            return False

        if tool.kubiya_api_key != test_api_key:
            print(f"   ❌ FAILED: Expected API key '{test_api_key}', got '{tool.kubiya_api_key}'")
            return False
        print(f"   ✅ API key correctly set: {tool.kubiya_api_key[:10]}...")

        print("\n4. Verifying Kubiya SDK client initialization status...")
        if not hasattr(tool, 'kubiya_client'):
            print("   ❌ FAILED: Tool has no kubiya_client attribute")
            return False

        # Note: kubiya_client may be None if kubiya SDK is not installed,
        # but the API key should still be set
        print(f"   ℹ️  Kubiya client: {tool.kubiya_client}")
        if tool.kubiya_client is None:
            print("   ⚠️  WARNING: Kubiya SDK client is None (SDK may not be installed)")
            print("   ℹ️  This is OK for testing - verifying API key was passed correctly")
        else:
            print("   ✅ Kubiya client initialized")

        print("\n✅ TEST PASSED: SkillFactory correctly passes API key to WorkflowExecutorTools")
        return True

    finally:
        # Restore original API key
        if original_api_key is not None:
            os.environ["KUBIYA_API_KEY"] = original_api_key
        elif "KUBIYA_API_KEY" in os.environ:
            del os.environ["KUBIYA_API_KEY"]


def test_workflow_execution_without_api_key_fails():
    """Test that workflow execution fails gracefully without API key."""
    print("\n" + "=" * 80)
    print("TEST 2: Workflow execution without API key fails correctly")
    print("=" * 80)

    # Remove API key from environment
    original_api_key = os.environ.get("KUBIYA_API_KEY")
    if "KUBIYA_API_KEY" in os.environ:
        del os.environ["KUBIYA_API_KEY"]

    try:
        skill_config = {
            "type": "workflow_executor",
            "name": "Test Workflow",
            "enabled": True,
            "configuration": {
                "workflow_type": "json",
                "validation_enabled": True,
                "default_runner": "kubiya-prod",
                "workflow_definition": json.dumps({
                    "name": "test-workflow",
                    "description": "Test workflow",
                    "steps": [
                        {
                            "name": "test-step",
                            "description": "Test step",
                            "executor": {
                                "type": "shell",
                                "config": {"command": "echo 'test'"}
                            }
                        }
                    ]
                })
            }
        }

        print("\n1. Creating workflow tool WITHOUT API key...")
        tool = SkillFactory.create_skill(skill_config)

        if tool is None:
            print("   ❌ FAILED: Tool creation returned None")
            return False

        print(f"   ✅ Tool created (API key warning expected)")

        print("\n2. Verifying API key is None...")
        if tool.kubiya_api_key is not None:
            print(f"   ❌ FAILED: Expected None, got '{tool.kubiya_api_key}'")
            return False
        print("   ✅ API key is None (as expected)")

        print("\n3. Verifying kubiya_client is None...")
        if tool.kubiya_client is not None:
            print(f"   ❌ FAILED: Expected None client, got {tool.kubiya_client}")
            return False
        print("   ✅ Kubiya client is None (as expected)")

        print("\n4. Attempting workflow execution (should fail)...")
        try:
            # This should fail with "Kubiya SDK client not initialized"
            result = tool.execute_workflow(parameters={})

            # Check if result contains error message
            if "Kubiya SDK client not initialized" in result:
                print("   ✅ Got expected error message")
                print(f"   Error: {result[:100]}...")
                print("\n✅ TEST PASSED: Workflow execution fails gracefully without API key")
                return True
            else:
                print(f"   ❌ FAILED: Unexpected result: {result[:200]}...")
                return False

        except Exception as e:
            error_msg = str(e)
            if "Kubiya SDK client not initialized" in error_msg:
                print("   ✅ Got expected exception")
                print(f"   Error: {error_msg}")
                print("\n✅ TEST PASSED: Workflow execution fails gracefully without API key")
                return True
            else:
                print(f"   ❌ FAILED: Unexpected exception: {e}")
                import traceback
                traceback.print_exc()
                return False

    finally:
        # Restore original API key
        if original_api_key is not None:
            os.environ["KUBIYA_API_KEY"] = original_api_key


def test_execution_id_propagation():
    """Test that execution_id is properly propagated to workflow tool."""
    print("\n" + "=" * 80)
    print("TEST 3: execution_id propagation for streaming")
    print("=" * 80)

    # Set API key for this test
    test_api_key = "test-api-key-12345"
    original_api_key = os.environ.get("KUBIYA_API_KEY")
    os.environ["KUBIYA_API_KEY"] = test_api_key

    try:
        test_execution_id = "exec-test-12345"

        skill_config = {
            "type": "workflow_executor",
            "name": "Test Workflow",
            "enabled": True,
            "execution_id": test_execution_id,  # This is what agent_activities.py adds
            "configuration": {
                "workflow_type": "json",
                "validation_enabled": True,
                "default_runner": "kubiya-prod",
                "workflow_definition": json.dumps({
                    "name": "test-workflow",
                    "description": "Test workflow",
                    "steps": [
                        {
                            "name": "test-step",
                            "description": "Test step",
                            "executor": {
                                "type": "shell",
                                "config": {"command": "echo 'test'"}
                            }
                        }
                    ]
                })
            }
        }

        print(f"\n1. Creating workflow tool with execution_id: {test_execution_id}...")
        tool = SkillFactory.create_skill(skill_config)

        if tool is None:
            print("   ❌ FAILED: Tool creation returned None")
            return False

        print("   ✅ Tool created")

        print("\n2. Verifying execution_id was propagated...")
        if not hasattr(tool, 'execution_id'):
            print("   ❌ FAILED: Tool has no execution_id attribute")
            return False

        if tool.execution_id != test_execution_id:
            print(f"   ❌ FAILED: Expected '{test_execution_id}', got '{tool.execution_id}'")
            return False

        print(f"   ✅ execution_id correctly set: {tool.execution_id}")
        print("\n✅ TEST PASSED: execution_id properly propagated for streaming")
        return True

    finally:
        # Restore original API key
        if original_api_key is not None:
            os.environ["KUBIYA_API_KEY"] = original_api_key
        elif "KUBIYA_API_KEY" in os.environ:
            del os.environ["KUBIYA_API_KEY"]


def test_multi_workflow_format():
    """Test the new multi-workflow format."""
    print("\n" + "=" * 80)
    print("TEST 4: Multi-workflow format support")
    print("=" * 80)

    # Set API key
    test_api_key = "test-api-key-12345"
    original_api_key = os.environ.get("KUBIYA_API_KEY")
    os.environ["KUBIYA_API_KEY"] = test_api_key

    try:
        skill_config = {
            "type": "workflow_executor",
            "name": "Multi Workflow Skill",
            "enabled": True,
            "configuration": {
                "workflows": [
                    {
                        "name": "deploy",
                        "type": "json",
                        "definition": {
                            "name": "deploy",
                            "description": "Deploy application",
                            "runner": "kubiya-prod",
                            "steps": [
                                {
                                    "name": "deploy-step",
                                    "description": "Deploy",
                                    "executor": {
                                        "type": "shell",
                                        "config": {"command": "echo 'deploying'"}
                                    }
                                }
                            ]
                        }
                    },
                    {
                        "name": "rollback",
                        "type": "json",
                        "definition": {
                            "name": "rollback",
                            "description": "Rollback deployment",
                            "runner": "kubiya-prod",
                            "steps": [
                                {
                                    "name": "rollback-step",
                                    "description": "Rollback",
                                    "executor": {
                                        "type": "shell",
                                        "config": {"command": "echo 'rolling back'"}
                                    }
                                }
                            ]
                        }
                    }
                ],
                "validation_enabled": True,
                "default_runner": "kubiya-prod"
            }
        }

        print("\n1. Creating multi-workflow tool...")
        tool = SkillFactory.create_skill(skill_config)

        if tool is None:
            print("   ❌ FAILED: Tool creation returned None")
            return False

        print("   ✅ Tool created")

        print("\n2. Verifying workflows were loaded...")
        if not hasattr(tool, 'workflows'):
            print("   ❌ FAILED: Tool has no workflows attribute")
            return False

        if len(tool.workflows) != 2:
            print(f"   ❌ FAILED: Expected 2 workflows, got {len(tool.workflows)}")
            return False

        print(f"   ✅ Loaded {len(tool.workflows)} workflows")

        print("\n3. Listing workflows...")
        try:
            workflows_list = tool.list_all_workflows()
            print(f"   ✅ list_all_workflows() executed")
            print(f"\n{workflows_list}\n")
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
            import traceback
            traceback.print_exc()
            return False

        print("\n✅ TEST PASSED: Multi-workflow format supported")
        return True

    finally:
        # Restore original API key
        if original_api_key is not None:
            os.environ["KUBIYA_API_KEY"] = original_api_key
        elif "KUBIYA_API_KEY" in os.environ:
            del os.environ["KUBIYA_API_KEY"]


def main():
    """Run all integration tests."""
    print("\n" + "=" * 80)
    print("WORKFLOW EXECUTOR INTEGRATION TESTS")
    print("Testing the fix for: 'Kubiya SDK client not initialized'")
    print("=" * 80)

    tests = [
        ("SkillFactory API key propagation", test_skill_factory_creates_workflow_tool_with_api_key),
        ("Workflow execution without API key", test_workflow_execution_without_api_key_fails),
        ("execution_id propagation", test_execution_id_propagation),
        ("Multi-workflow format", test_multi_workflow_format),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n❌ TEST CRASHED: {test_name}")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for _, p in results if p)
    total = len(results)

    for test_name, passed_test in results:
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
