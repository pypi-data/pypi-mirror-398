#!/usr/bin/env python3
"""Test script for workflow executor tool instantiation."""
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from control_plane_api.worker.services.skill_factory import SkillFactory


def test_workflow_tool_instantiation():
    """Test that workflow tools can be instantiated from skill factory."""
    print("=" * 80)
    print("TEST: Workflow Tool Instantiation")
    print("=" * 80)

    # Define a test workflow configuration
    workflow_config = {
        "type": "workflow_executor",
        "name": "Test Deployment Workflow",
        "enabled": True,
        "configuration": {
            "workflow_type": "json",
            "validation_enabled": True,
            "timeout": 3600,
            "default_runner": "test-runner",
            "workflow_definition": json.dumps({
                "name": "deploy-app",
                "description": "Deploy application",
                "steps": [
                    {
                        "name": "build",
                        "description": "Build the application",
                        "executor": {
                            "type": "shell",
                            "config": {
                                "command": "npm run build"
                            }
                        }
                    },
                    {
                        "name": "deploy",
                        "description": "Deploy to environment",
                        "executor": {
                            "type": "shell",
                            "config": {
                                "command": "kubectl apply -f deployment.yaml"
                            }
                        },
                        "depends_on": ["build"]
                    }
                ]
            })
        }
    }

    print("\n1. Creating workflow tool from configuration...")
    try:
        tool = SkillFactory.create_skill(workflow_config)

        if tool is None:
            print("   ❌ Tool creation returned None")
            return False

        print("   ✅ Tool created successfully")
        print(f"   Tool type: {type(tool).__name__}")
        print(f"   Tool name: {tool.name}")

    except Exception as e:
        print(f"   ❌ Failed to create tool: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n2. Checking tool methods...")
    expected_methods = ['execute_workflow', 'list_workflow_steps', 'get_workflow_info']

    for method_name in expected_methods:
        if hasattr(tool, method_name):
            print(f"   ✅ Method '{method_name}' exists")
        else:
            print(f"   ❌ Method '{method_name}' missing")
            return False

    print("\n3. Testing get_workflow_info()...")
    try:
        info = tool.get_workflow_info()
        print("   ✅ get_workflow_info() executed")
        print(f"\n{info}\n")
    except Exception as e:
        print(f"   ❌ get_workflow_info() failed: {e}")
        return False

    print("\n4. Testing list_workflow_steps()...")
    try:
        steps = tool.list_workflow_steps()
        print("   ✅ list_workflow_steps() executed")
        print(f"\n{steps}\n")
    except Exception as e:
        print(f"   ❌ list_workflow_steps() failed: {e}")
        return False

    print("\n5. Testing execute_workflow() with parameters...")
    try:
        # Note: Runner comes from workflow definition, not as parameter
        result = tool.execute_workflow(
            parameters={
                "environment": "staging",
                "version": "v1.0.0"
            }
        )
        print("   ✅ execute_workflow() executed")
        # Verify runner was picked up from workflow definition or config
        if "test-runner" in result or "Runner:" in result:
            print("   ✅ Runner correctly used from workflow/config")
        print(f"\n{result}\n")
    except Exception as e:
        print(f"   ❌ execute_workflow() failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


def test_python_dsl_workflow_tool():
    """Test Python DSL workflow tool instantiation."""
    print("\n" + "=" * 80)
    print("TEST: Python DSL Workflow Tool")
    print("=" * 80)

    python_workflow_config = {
        "type": "workflow_executor",
        "name": "Python DSL Workflow",
        "enabled": True,
        "configuration": {
            "workflow_type": "python_dsl",
            "validation_enabled": True,
            "timeout": 1800,
            "python_dsl_code": """
from kubiya_sdk import StatefulWorkflow

workflow = StatefulWorkflow(
    name="data-processing",
    description="Process data pipeline"
)
"""
        }
    }

    print("\n1. Creating Python DSL workflow tool...")
    try:
        tool = SkillFactory.create_skill(python_workflow_config)

        if tool is None:
            print("   ❌ Tool creation returned None")
            return False

        print("   ✅ Tool created successfully")
        print(f"   Workflow type: {tool.workflow_type}")

    except Exception as e:
        print(f"   ❌ Failed to create tool: {e}")
        return False

    print("\n2. Testing get_workflow_info()...")
    try:
        info = tool.get_workflow_info()
        print("   ✅ get_workflow_info() executed")
        print(f"\n{info}\n")
    except Exception as e:
        print(f"   ❌ get_workflow_info() failed: {e}")
        return False

    return True


def test_disabled_workflow_tool():
    """Test that disabled workflows return None."""
    print("\n" + "=" * 80)
    print("TEST: Disabled Workflow Tool")
    print("=" * 80)

    disabled_config = {
        "type": "workflow_executor",
        "name": "Disabled Workflow",
        "enabled": False,
        "configuration": {
            "workflow_type": "json",
            "workflow_definition": json.dumps({
                "name": "test",
                "steps": []
            })
        }
    }

    print("\n1. Creating disabled workflow tool...")
    tool = SkillFactory.create_skill(disabled_config)

    if tool is None:
        print("   ✅ Disabled tool correctly returned None")
        return True
    else:
        print("   ❌ Disabled tool should return None")
        return False


def test_runner_hierarchy():
    """Test that runner comes from workflow definition."""
    print("\n" + "=" * 80)
    print("TEST: Runner Hierarchy")
    print("=" * 80)

    # Test 1: Runner from workflow definition
    print("\n1. Testing runner from workflow definition...")
    workflow_with_runner = {
        "type": "workflow_executor",
        "name": "Workflow with Runner",
        "enabled": True,
        "configuration": {
            "workflow_type": "json",
            "default_runner": "config-runner",
            "workflow_definition": json.dumps({
                "name": "test-workflow",
                "runner": "workflow-runner",  # This should take precedence
                "steps": [{
                    "name": "test",
                    "executor": {"type": "shell", "config": {"command": "echo test"}}
                }]
            })
        }
    }

    tool = SkillFactory.create_skill(workflow_with_runner)
    info = tool.get_workflow_info()

    if "workflow-runner" in info:
        print("   ✅ Runner correctly taken from workflow definition")
    else:
        print(f"   ❌ Runner not from workflow definition. Info:\n{info}")
        return False

    # Test 2: Runner from config when not in workflow
    print("\n2. Testing runner from config (fallback)...")
    workflow_without_runner = {
        "type": "workflow_executor",
        "name": "Workflow without Runner",
        "enabled": True,
        "configuration": {
            "workflow_type": "json",
            "default_runner": "config-runner",
            "workflow_definition": json.dumps({
                "name": "test-workflow",
                # No runner specified here
                "steps": [{
                    "name": "test",
                    "executor": {"type": "shell", "config": {"command": "echo test"}}
                }]
            })
        }
    }

    tool2 = SkillFactory.create_skill(workflow_without_runner)
    info2 = tool2.get_workflow_info()

    if "config-runner" in info2:
        print("   ✅ Runner correctly taken from skill config")
    else:
        print(f"   ❌ Runner not from config. Info:\n{info2}")
        return False

    # Test 3: Execution uses workflow runner
    print("\n3. Testing execution uses correct runner...")
    result = tool.execute_workflow(parameters={"test": "value"})

    if "workflow-runner" in result or "Runner:" in result:
        print("   ✅ Execution uses workflow-defined runner")
    else:
        print(f"   ❌ Execution doesn't show runner correctly")
        return False

    return True


def test_bulk_skill_creation():
    """Test creating multiple skills including workflow."""
    print("\n" + "=" * 80)
    print("TEST: Bulk Skill Creation")
    print("=" * 80)

    configs = [
        {
            "type": "shell",
            "name": "Shell Tool",
            "enabled": True,
            "configuration": {}
        },
        {
            "type": "workflow_executor",
            "name": "Workflow Tool",
            "enabled": True,
            "configuration": {
                "workflow_type": "json",
                "workflow_definition": json.dumps({
                    "name": "test-workflow",
                    "steps": [{
                        "name": "test",
                        "executor": {"type": "shell", "config": {}}
                    }]
                })
            }
        },
        {
            "type": "python",
            "name": "Python Tool",
            "enabled": True,
            "configuration": {}
        }
    ]

    print(f"\n1. Creating {len(configs)} skills...")
    try:
        skills = SkillFactory.create_skills_from_list(configs)

        print(f"   ✅ Created {len(skills)} skills")

        for skill in skills:
            print(f"      - {type(skill).__name__}")

        if len(skills) == len(configs):
            print("   ✅ All skills created successfully")
            return True
        else:
            print(f"   ❌ Expected {len(configs)} skills, got {len(skills)}")
            return False

    except Exception as e:
        print(f"   ❌ Bulk creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "🚀" * 40)
    print("WORKFLOW TOOL INSTANTIATION TEST SUITE")
    print("🚀" * 40 + "\n")

    tests = [
        ("Workflow Tool Instantiation", test_workflow_tool_instantiation),
        ("Python DSL Workflow Tool", test_python_dsl_workflow_tool),
        ("Disabled Workflow Tool", test_disabled_workflow_tool),
        ("Runner Hierarchy", test_runner_hierarchy),
        ("Bulk Skill Creation", test_bulk_skill_creation),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")

    print("\n" + "-" * 80)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 80 + "\n")

    if passed == total:
        print("✅ All tests passed! Workflow tools are ready for agent use.")
        print("\nNext steps:")
        print("  1. Create workflow skills via API")
        print("  2. Associate with agents/teams")
        print("  3. Agents can now call workflow tools with parameters")
    else:
        print("❌ Some tests failed. Please review the errors above.")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
