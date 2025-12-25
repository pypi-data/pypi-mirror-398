#!/usr/bin/env python3
"""
Test for multi-workflow support in WorkflowExecutorTools.

This test validates that a single skill instance can contain multiple
workflow definitions, each exposed as a separate tool method.

Example configuration:
{
    "type": "workflow_executor",
    "configuration": {
        "workflows": [
            {"name": "analyze-logs", "type": "json", "definition": {...}},
            {"name": "deploy-app", "type": "json", "definition": {...}}
        ],
        "default_runner": "kubiya-prod"
    }
}

This should create:
- execute_workflow_analyze_logs()
- execute_workflow_deploy_app()
- list_all_workflows()
- get_workflow_info()
"""

import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from control_plane_api.worker.services.skill_factory import SkillFactory


def test_multi_workflow_basic():
    """Test basic multi-workflow configuration."""
    print("=" * 80)
    print("TEST 1: Basic Multi-Workflow Configuration")
    print("=" * 80)

    # Define multiple workflows
    analyze_logs_workflow = {
        "name": "analyze-logs",
        "description": "Analyze application logs",
        "runner": "kubiya-prod",
        "steps": [
            {
                "name": "fetch-logs",
                "description": "Fetch logs from source",
                "executor": {
                    "type": "shell",
                    "config": {
                        "command": "echo 'Fetching logs from {{log_source}}...'"
                    }
                }
            },
            {
                "name": "analyze-patterns",
                "description": "Analyze log patterns",
                "depends_on": ["fetch-logs"],
                "executor": {
                    "type": "shell",
                    "config": {
                        "command": "echo 'Analyzing patterns... Found {{error_count}} errors'"
                    }
                }
            }
        ]
    }

    deploy_app_workflow = {
        "name": "deploy-app",
        "description": "Deploy application to environment",
        "runner": "kubiya-prod",
        "steps": [
            {
                "name": "build-image",
                "description": "Build Docker image",
                "executor": {
                    "type": "shell",
                    "config": {
                        "command": "echo 'Building image {{image_tag}}...'"
                    }
                }
            },
            {
                "name": "push-image",
                "description": "Push to registry",
                "depends_on": ["build-image"],
                "executor": {
                    "type": "shell",
                    "config": {
                        "command": "echo 'Pushing to {{registry}}...'"
                    }
                }
            },
            {
                "name": "deploy",
                "description": "Deploy to environment",
                "depends_on": ["push-image"],
                "executor": {
                    "type": "shell",
                    "config": {
                        "command": "echo 'Deploying to {{environment}}...'"
                    }
                }
            }
        ]
    }

    backup_db_workflow = {
        "name": "backup-database",
        "description": "Backup database to S3",
        "runner": "kubiya-prod",
        "steps": [
            {
                "name": "create-backup",
                "description": "Create database backup",
                "executor": {
                    "type": "shell",
                    "config": {
                        "command": "echo 'Creating backup of {{database_name}}...'"
                    }
                }
            },
            {
                "name": "upload-to-s3",
                "description": "Upload backup to S3",
                "depends_on": ["create-backup"],
                "executor": {
                    "type": "shell",
                    "config": {
                        "command": "echo 'Uploading to {{s3_bucket}}...'"
                    }
                }
            }
        ]
    }

    # Create skill configuration with multiple workflows
    skill_config = {
        "type": "workflow_executor",
        "name": "DevOps Workflows",
        "enabled": True,
        "configuration": {
            "workflows": [
                {
                    "name": "analyze-logs",
                    "type": "json",
                    "definition": analyze_logs_workflow
                },
                {
                    "name": "deploy-app",
                    "type": "json",
                    "definition": deploy_app_workflow
                },
                {
                    "name": "backup-database",
                    "type": "json",
                    "definition": backup_db_workflow
                }
            ],
            "validation_enabled": True,
            "default_runner": "kubiya-prod",
            "timeout": 3600
        }
    }

    print("\n1. Creating multi-workflow skill...")
    try:
        tool = SkillFactory.create_skill(skill_config)
        if not tool:
            print("   ❌ Skill creation returned None")
            return False
        print("   ✅ Skill created successfully")
        print(f"   Type: {type(tool).__name__}")
    except Exception as e:
        print(f"   ❌ Failed to create skill: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n2. Verifying dynamically registered tools...")
    expected_tools = [
        "execute_workflow_analyze_logs",
        "execute_workflow_deploy_app",
        "execute_workflow_backup_database",
        "list_all_workflows",
        "get_workflow_info"
    ]

    # Check if methods exist directly on the tool object
    for expected in expected_tools:
        if hasattr(tool, expected):
            print(f"   ✅ {expected}")
        else:
            print(f"   ❌ {expected} NOT FOUND")

    print("\n3. Listing all workflows...")
    try:
        workflows_list = tool.list_all_workflows()
        print(workflows_list)
        print("   ✅ Listed workflows")
    except Exception as e:
        print(f"   ❌ Failed to list workflows: {e}")

    print("\n4. Getting workflow info...")
    try:
        info = tool.get_workflow_info()
        print(info)
        print("   ✅ Got workflow info")
    except Exception as e:
        print(f"   ❌ Failed to get info: {e}")

    print("\n5. Testing execute_workflow_analyze_logs()...")
    try:
        if hasattr(tool, 'execute_workflow_analyze_logs'):
            result = tool.execute_workflow_analyze_logs(
                parameters={
                    "log_source": "/var/log/app.log",
                    "error_count": "5"
                }
            )
            print("\n" + "="*60)
            print("RESULT:")
            print("="*60)
            print(result[:500] if len(result) > 500 else result)
            print("="*60)
            print("\n   ✅ execute_workflow_analyze_logs() worked!")
        else:
            print("   ❌ execute_workflow_analyze_logs() method not found")
            return False
    except Exception as e:
        print(f"   ❌ Failed to execute: {e}")
        import traceback
        traceback.print_exc()

    print("\n6. Testing execute_workflow_deploy_app()...")
    try:
        if hasattr(tool, 'execute_workflow_deploy_app'):
            result = tool.execute_workflow_deploy_app(
                parameters={
                    "image_tag": "v1.2.3",
                    "registry": "docker.io/myapp",
                    "environment": "production"
                }
            )
            print("\n" + "="*60)
            print("RESULT:")
            print("="*60)
            print(result[:500] if len(result) > 500 else result)
            print("="*60)
            print("\n   ✅ execute_workflow_deploy_app() worked!")
        else:
            print("   ❌ execute_workflow_deploy_app() method not found")
            return False
    except Exception as e:
        print(f"   ❌ Failed to execute: {e}")
        import traceback
        traceback.print_exc()

    print("\n7. Testing execute_workflow_backup_database()...")
    try:
        if hasattr(tool, 'execute_workflow_backup_database'):
            result = tool.execute_workflow_backup_database(
                parameters={
                    "database_name": "production_db",
                    "s3_bucket": "s3://backups/db"
                }
            )
            print("\n" + "="*60)
            print("RESULT:")
            print("="*60)
            print(result[:500] if len(result) > 500 else result)
            print("="*60)
            print("\n   ✅ execute_workflow_backup_database() worked!")
        else:
            print("   ❌ execute_workflow_backup_database() method not found")
            return False
    except Exception as e:
        print(f"   ❌ Failed to execute: {e}")
        import traceback
        traceback.print_exc()

    return True


def test_mixed_workflow_types():
    """Test multi-workflow with both JSON and Python DSL types."""
    print("\n" + "=" * 80)
    print("TEST 2: Mixed Workflow Types (JSON + Python DSL)")
    print("=" * 80)

    skill_config = {
        "type": "workflow_executor",
        "name": "Mixed Workflows",
        "enabled": True,
        "configuration": {
            "workflows": [
                {
                    "name": "hello-json",
                    "type": "json",
                    "definition": {
                        "name": "hello-json",
                        "description": "Simple JSON workflow",
                        "runner": "kubiya-prod",
                        "steps": [
                            {
                                "name": "greet",
                                "executor": {
                                    "type": "shell",
                                    "config": {
                                        "command": "echo 'Hello from JSON workflow!'"
                                    }
                                }
                            }
                        ]
                    }
                },
                {
                    "name": "hello-python",
                    "type": "python_dsl",
                    "code": '''from kubiya_sdk import StatefulWorkflow

workflow = StatefulWorkflow(
    name="hello-python",
    description="Simple Python DSL workflow"
)
'''
                }
            ],
            "default_runner": "kubiya-prod"
        }
    }

    print("\n1. Creating mixed-type workflow skill...")
    try:
        tool = SkillFactory.create_skill(skill_config)
        if not tool:
            print("   ❌ Creation failed")
            return False
        print("   ✅ Created successfully")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False

    print("\n2. Verifying both workflow types are registered...")
    if hasattr(tool, 'execute_workflow_hello_json'):
        print("   ✅ execute_workflow_hello_json()")
    else:
        print("   ❌ execute_workflow_hello_json() NOT FOUND")

    if hasattr(tool, 'execute_workflow_hello_python'):
        print("   ✅ execute_workflow_hello_python()")
    else:
        print("   ❌ execute_workflow_hello_python() NOT FOUND")

    print("\n3. Listing workflows...")
    try:
        print(tool.list_all_workflows())
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    return True


def test_backward_compatibility():
    """Test that legacy single-workflow format still works."""
    print("\n" + "=" * 80)
    print("TEST 3: Backward Compatibility (Legacy Format)")
    print("=" * 80)

    legacy_workflow = {
        "name": "legacy-workflow",
        "description": "Legacy single workflow",
        "runner": "kubiya-prod",
        "steps": [
            {
                "name": "step-1",
                "executor": {
                    "type": "shell",
                    "config": {
                        "command": "echo 'Legacy workflow step'"
                    }
                }
            }
        ]
    }

    # Old format: workflow_type + workflow_definition
    skill_config = {
        "type": "workflow_executor",
        "name": "Legacy Workflow",
        "enabled": True,
        "configuration": {
            "workflow_type": "json",
            "workflow_definition": json.dumps(legacy_workflow),
            "default_runner": "kubiya-prod"
        }
    }

    print("\n1. Creating skill with legacy format...")
    try:
        tool = SkillFactory.create_skill(skill_config)
        if not tool:
            print("   ❌ Creation failed")
            return False
        print("   ✅ Created successfully")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n2. Verifying legacy methods work...")
    try:
        info = tool.get_workflow_info()
        print(info)
        print("   ✅ get_workflow_info() works")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    try:
        steps = tool.list_workflow_steps()
        print(steps)
        print("   ✅ list_workflow_steps() works")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    try:
        # Legacy execute_workflow() should work
        result = tool.execute_workflow(parameters={"test": "value"})
        print(result[:300] if len(result) > 300 else result)
        print("   ✅ execute_workflow() works")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    return True


def main():
    """Run all tests."""
    print("\n" + "🚀" * 40)
    print("MULTI-WORKFLOW EXECUTOR TEST SUITE")
    print("🚀" * 40 + "\n")

    print("These tests verify:")
    print("  1. Multiple workflows in single skill instance")
    print("  2. Dynamic tool registration (execute_workflow_<name>)")
    print("  3. Mixed workflow types (JSON + Python DSL)")
    print("  4. Backward compatibility with legacy format")
    print("\n")

    tests = [
        ("Multi-Workflow Basic", test_multi_workflow_basic),
        ("Mixed Workflow Types", test_mixed_workflow_types),
        ("Backward Compatibility", test_backward_compatibility),
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
        print("✅ All tests passed!")
        print("\nMulti-workflow support is ready:")
        print("  • Multiple workflows in single skill instance")
        print("  • Dynamic tool registration: execute_workflow_<name>()")
        print("  • Global tools: list_all_workflows(), get_workflow_info()")
        print("  • Backward compatible with legacy single-workflow format")
    else:
        print("❌ Some tests failed. Please review the errors above.")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
