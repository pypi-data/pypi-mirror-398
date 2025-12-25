#!/usr/bin/env python3
"""Test script for workflow executor skill."""
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from control_plane_api.app.skills.workflow_executor import (
    WorkflowExecutorSkill,
    WorkflowExecutorConfiguration
)


def test_json_workflow_validation():
    """Test JSON workflow validation."""
    print("=" * 80)
    print("TEST 1: JSON Workflow Validation")
    print("=" * 80)

    skill = WorkflowExecutorSkill()

    # Test valid JSON workflow
    valid_workflow = {
        "workflow_type": "json",
        "validation_enabled": True,
        "timeout": 3600,
        "workflow_definition": json.dumps({
            "name": "test-workflow",
            "description": "Test workflow",
            "steps": [
                {
                    "name": "step1",
                    "description": "First step",
                    "executor": {
                        "type": "shell",
                        "config": {
                            "command": "echo 'Hello World'"
                        }
                    }
                },
                {
                    "name": "step2",
                    "description": "Second step",
                    "executor": {
                        "type": "shell",
                        "config": {
                            "command": "echo 'Step 2'"
                        }
                    },
                    "depends_on": ["step1"]
                }
            ],
            "triggers": [
                {
                    "type": "manual",
                    "config": {
                        "name": "Manual Trigger"
                    }
                }
            ],
            "runner": "default"
        })
    }

    try:
        validated = skill.validate_configuration(valid_workflow)
        print("✅ Valid JSON workflow validated successfully")
        print(f"   Workflow name: {json.loads(validated['workflow_definition'])['name']}")
        print(f"   Steps: {len(json.loads(validated['workflow_definition'])['steps'])}")
        print(f"   Timeout: {validated['timeout']}s")
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False

    # Test invalid JSON workflow (missing executor)
    print("\n" + "-" * 80)
    print("Testing invalid workflow (missing executor)...")

    invalid_workflow = {
        "workflow_type": "json",
        "validation_enabled": True,
        "workflow_definition": json.dumps({
            "name": "invalid-workflow",
            "steps": [
                {
                    "name": "bad-step"
                    # Missing executor
                }
            ]
        })
    }

    try:
        skill.validate_configuration(invalid_workflow)
        print("❌ Should have failed validation")
        return False
    except ValueError as e:
        print(f"✅ Correctly rejected invalid workflow: {str(e)[:100]}")

    # Test invalid dependency
    print("\n" + "-" * 80)
    print("Testing invalid workflow (bad dependency)...")

    invalid_dep_workflow = {
        "workflow_type": "json",
        "validation_enabled": True,
        "workflow_definition": json.dumps({
            "name": "invalid-dep-workflow",
            "steps": [
                {
                    "name": "step1",
                    "executor": {"type": "shell", "config": {}}
                },
                {
                    "name": "step2",
                    "executor": {"type": "shell", "config": {}},
                    "depends_on": ["nonexistent-step"]
                }
            ]
        })
    }

    try:
        skill.validate_configuration(invalid_dep_workflow)
        print("❌ Should have failed validation")
        return False
    except ValueError as e:
        print(f"✅ Correctly rejected invalid dependency: {str(e)[:100]}")

    return True


def test_python_dsl_validation():
    """Test Python DSL validation."""
    print("\n" + "=" * 80)
    print("TEST 2: Python DSL Validation")
    print("=" * 80)

    skill = WorkflowExecutorSkill()

    # Test valid Python DSL
    valid_dsl = {
        "workflow_type": "python_dsl",
        "validation_enabled": True,
        "timeout": 3600,
        "python_dsl_code": """
from kubiya_sdk import StatefulWorkflow

# Create a workflow
workflow = StatefulWorkflow(
    name="test-python-workflow",
    description="Test workflow using Python DSL"
)

# Workflow steps would be added here
"""
    }

    try:
        validated = skill.validate_configuration(valid_dsl)
        print("✅ Valid Python DSL validated successfully")
        print(f"   Timeout: {validated['timeout']}s")
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False

    # Test invalid Python DSL (syntax error)
    print("\n" + "-" * 80)
    print("Testing invalid Python DSL (syntax error)...")

    invalid_dsl = {
        "workflow_type": "python_dsl",
        "validation_enabled": True,
        "python_dsl_code": """
from kubiya_sdk import StatefulWorkflow

# Syntax error: missing closing parenthesis
workflow = StatefulWorkflow(
    name="test-workflow"
"""
    }

    try:
        skill.validate_configuration(invalid_dsl)
        print("❌ Should have failed validation")
        return False
    except ValueError as e:
        print(f"✅ Correctly rejected invalid DSL: {str(e)[:100]}")

    # Test Python DSL without workflow creation
    print("\n" + "-" * 80)
    print("Testing Python DSL without workflow creation...")

    no_workflow_dsl = {
        "workflow_type": "python_dsl",
        "validation_enabled": True,
        "python_dsl_code": """
# This code doesn't create a workflow
x = 1 + 1
print("No workflow here!")
"""
    }

    try:
        skill.validate_configuration(no_workflow_dsl)
        print("❌ Should have failed validation")
        return False
    except ValueError as e:
        print(f"✅ Correctly rejected DSL without workflow: {str(e)[:100]}")

    return True


def test_skill_variants():
    """Test skill variants."""
    print("\n" + "=" * 80)
    print("TEST 3: Skill Variants")
    print("=" * 80)

    skill = WorkflowExecutorSkill()
    variants = skill.get_variants()

    print(f"Found {len(variants)} variants:")
    for variant in variants:
        print(f"\n  📦 {variant.name}")
        print(f"     ID: {variant.id}")
        print(f"     Category: {variant.category}")
        print(f"     Description: {variant.description}")
        print(f"     Icon: {variant.icon}")
        print(f"     Default: {variant.is_default}")

        # Validate each variant's configuration
        try:
            validated = skill.validate_configuration(variant.configuration)
            print(f"     ✅ Configuration is valid")
        except Exception as e:
            print(f"     ❌ Configuration validation failed: {e}")
            return False

    return True


def test_skill_metadata():
    """Test skill metadata."""
    print("\n" + "=" * 80)
    print("TEST 4: Skill Metadata")
    print("=" * 80)

    skill = WorkflowExecutorSkill()

    print(f"Type: {skill.type}")
    print(f"Name: {skill.name}")
    print(f"Description: {skill.description}")
    print(f"Icon: {skill.icon}")
    print(f"Icon Type: {skill.icon_type}")
    print(f"Framework Class: {skill.get_framework_class_name()}")

    requirements = skill.get_requirements()
    print(f"\nRequirements:")
    print(f"  Supported OS: {requirements.supported_os}")
    print(f"  Min Python Version: {requirements.min_python_version}")
    print(f"  Python Packages: {requirements.python_packages}")
    print(f"  System Packages: {requirements.system_packages}")
    print(f"  Required Env Vars: {requirements.required_env_vars}")
    print(f"  Notes: {requirements.notes}")

    return True


def test_example_workflow():
    """Test with the example workflow from the requirements."""
    print("\n" + "=" * 80)
    print("TEST 5: Example Workflow from Requirements")
    print("=" * 80)

    skill = WorkflowExecutorSkill()

    example_workflow = {
        "workflow_type": "json",
        "validation_enabled": True,
        "timeout": 3600,
        "default_runner": "test1",
        "workflow_definition": json.dumps({
            "name": "deploy-busybox-logger",
            "description": "Deploy a busybox container that logs 'hello world' every 5 seconds in OpenShift",
            "steps": [
                {
                    "name": "create-deployment",
                    "executor": {
                        "type": "agent",
                        "config": {
                            "message": "deploy a busybox based deployment in the kubiya namespace that logs \"hello world\" every 5 seconds",
                            "manifest": {
                                "kind": "Deployment",
                                "spec": {
                                    "replicas": 1,
                                    "selector": {
                                        "matchLabels": {
                                            "app": "busybox-logger"
                                        }
                                    },
                                    "template": {
                                        "spec": {
                                            "containers": [
                                                {
                                                    "name": "busybox",
                                                    "image": "busybox",
                                                    "command": [
                                                        "/bin/sh",
                                                        "-c",
                                                        "while true; do echo 'hello world'; sleep 5; done"
                                                    ]
                                                }
                                            ]
                                        },
                                        "metadata": {
                                            "labels": {
                                                "app": "busybox-logger"
                                            }
                                        }
                                    }
                                },
                                "metadata": {
                                    "name": "busybox-logger",
                                    "namespace": "kubiya"
                                },
                                "apiVersion": "apps/v1"
                            },
                            "namespace": "kubiya",
                            "operation": "apply",
                            "agent_name": "test1-agent"
                        }
                    },
                    "description": "Create OpenShift deployment for busybox logger"
                }
            ],
            "triggers": [
                {
                    "type": "manual",
                    "config": {
                        "name": "Manual Trigger",
                        "description": "Manually triggered workflow"
                    },
                    "runner": "test1"
                }
            ],
            "runner": "test1"
        })
    }

    try:
        validated = skill.validate_configuration(example_workflow)
        workflow_data = json.loads(validated['workflow_definition'])

        print("✅ Example workflow validated successfully")
        print(f"   Workflow name: {workflow_data['name']}")
        print(f"   Description: {workflow_data['description']}")
        print(f"   Steps: {len(workflow_data['steps'])}")
        print(f"   Triggers: {len(workflow_data['triggers'])}")
        print(f"   Runner: {workflow_data['runner']}")
        print(f"   Default runner: {validated.get('default_runner')}")

        # Show step details
        for step in workflow_data['steps']:
            print(f"\n   Step: {step['name']}")
            print(f"     Executor type: {step['executor']['type']}")
            if 'description' in step:
                print(f"     Description: {step['description']}")

        return True

    except Exception as e:
        print(f"❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "🚀" * 40)
    print("WORKFLOW EXECUTOR SKILL TEST SUITE")
    print("🚀" * 40 + "\n")

    tests = [
        ("JSON Workflow Validation", test_json_workflow_validation),
        ("Python DSL Validation", test_python_dsl_validation),
        ("Skill Variants", test_skill_variants),
        ("Skill Metadata", test_skill_metadata),
        ("Example Workflow", test_example_workflow),
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

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
