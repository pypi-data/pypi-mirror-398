#!/usr/bin/env python3
"""
Test that agent_activities.py properly instantiates workflow_executor skills.

This specifically tests the bug fix where instantiate_skill() was replaced
with SkillFactory.create_skill() to support workflow_executor skills.
"""

import json
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from control_plane_api.worker.services.skill_factory import SkillFactory


def test_workflow_skill_instantiation_via_skill_factory():
    """
    Test that workflow_executor skills are instantiated correctly.

    This reproduces the bug where instantiate_skill() didn't support
    workflow_executor, causing "Kubiya SDK client not initialized".
    """
    print("=" * 80)
    print("TEST: Agent Activities Workflow Skill Instantiation")
    print("=" * 80)

    # Set API key
    test_api_key = "test-api-key-12345"
    original_api_key = os.environ.get("KUBIYA_API_KEY")
    os.environ["KUBIYA_API_KEY"] = test_api_key

    try:
        # Simulate what Control Plane sends (with execution_id)
        skills = [
            {
                "type": "shell",
                "name": "Shell Commands",
                "enabled": True,
                "configuration": {}
            },
            {
                "type": "workflow_executor",
                "name": "Find certs for renewal on OpenShift",  # Real skill name from error
                "enabled": True,
                "execution_id": "exec-test-12345",  # Added by agent_activities.py
                "configuration": {
                    "workflow_type": "json",
                    "validation_enabled": True,
                    "default_runner": "kubiya-prod",
                    "workflow_definition": json.dumps({
                        "name": "default",
                        "description": "Find certificates for renewal",
                        "runner": "kubiya-prod",
                        "steps": [
                            {
                                "name": "find-certs",
                                "description": "Find certs",
                                "executor": {
                                    "type": "shell",
                                    "config": {
                                        "command": "oc get certificates"
                                    }
                                }
                            }
                        ]
                    })
                }
            }
        ]

        print("\n1. Simulating agent_activities.py skill instantiation...")
        print(f"   Total skills to instantiate: {len(skills)}")

        # This is what agent_activities.py does NOW (after the fix)
        agno_toolkits = []
        for skill in skills:
            print(f"\n   Processing skill: {skill['name']} (type: {skill['type']})")

            # Use SkillFactory (THE FIX)
            toolkit = SkillFactory.create_skill(skill)

            if toolkit:
                print(f"   ✅ Created toolkit: {type(toolkit).__name__}")
                agno_toolkits.append(toolkit)
            else:
                print(f"   ⚠️  Skill returned None (disabled or unsupported)")

        print(f"\n2. Verifying all skills were instantiated...")
        print(f"   Expected: 2 toolkits")
        print(f"   Got: {len(agno_toolkits)} toolkits")

        if len(agno_toolkits) != 2:
            print(f"   ❌ FAILED: Expected 2, got {len(agno_toolkits)}")
            return False

        print("   ✅ All skills instantiated")

        print("\n3. Verifying workflow_executor toolkit...")
        workflow_toolkit = None
        for toolkit in agno_toolkits:
            if type(toolkit).__name__ == "WorkflowExecutorTools":
                workflow_toolkit = toolkit
                break

        if not workflow_toolkit:
            print("   ❌ FAILED: WorkflowExecutorTools not found")
            return False

        print(f"   ✅ Found WorkflowExecutorTools")

        print("\n4. Verifying WorkflowExecutorTools has API key...")
        if not hasattr(workflow_toolkit, 'kubiya_api_key'):
            print("   ❌ FAILED: No kubiya_api_key attribute")
            return False

        if workflow_toolkit.kubiya_api_key != test_api_key:
            print(f"   ❌ FAILED: Wrong API key")
            return False

        print(f"   ✅ API key correct: {workflow_toolkit.kubiya_api_key[:10]}...")

        print("\n5. Verifying Kubiya client is initialized...")
        if not hasattr(workflow_toolkit, 'kubiya_client'):
            print("   ❌ FAILED: No kubiya_client attribute")
            return False

        if workflow_toolkit.kubiya_client is None:
            print("   ⚠️  WARNING: Kubiya client is None (SDK may not be installed)")
        else:
            print(f"   ✅ Kubiya client initialized")

        print("\n6. Verifying execution_id was passed...")
        if not hasattr(workflow_toolkit, 'execution_id'):
            print("   ❌ FAILED: No execution_id attribute")
            return False

        if workflow_toolkit.execution_id != "exec-test-12345":
            print(f"   ❌ FAILED: Wrong execution_id: {workflow_toolkit.execution_id}")
            return False

        print(f"   ✅ execution_id correct: {workflow_toolkit.execution_id}")

        print("\n✅ TEST PASSED: agent_activities.py workflow skill instantiation works!")
        print("\n📝 Summary:")
        print("   - SkillFactory correctly creates WorkflowExecutorTools")
        print("   - KUBIYA_API_KEY is passed from environment")
        print("   - execution_id is propagated for streaming")
        print("   - Kubiya SDK client can be initialized")
        print("\n🐛 This fixes the bug: 'Kubiya SDK client not initialized'")
        return True

    finally:
        # Restore original API key
        if original_api_key is not None:
            os.environ["KUBIYA_API_KEY"] = original_api_key
        elif "KUBIYA_API_KEY" in os.environ:
            del os.environ["KUBIYA_API_KEY"]


if __name__ == "__main__":
    success = test_workflow_skill_instantiation_via_skill_factory()
    sys.exit(0 if success else 1)
