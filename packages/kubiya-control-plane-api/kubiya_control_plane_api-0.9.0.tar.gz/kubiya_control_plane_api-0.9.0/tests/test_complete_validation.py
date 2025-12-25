#!/usr/bin/env python3
"""
Complete validation test for the runtime system integration.

This test validates:
1. Runtime validation system works correctly
2. Both runtimes are registered properly
3. Model compatibility validation is enforced
4. Requirements can be retrieved
5. Error messages are helpful

This does NOT require Control Plane API or Worker to be running.
"""
import sys
import os

# Add control_plane_api to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'control_plane_api'))

from worker.runtimes.validation import (
    validate_agent_for_runtime,
    get_runtime_requirements_info,
    list_all_runtime_requirements,
)
from worker.runtimes.base import RuntimeType, RuntimeRegistry


def test_runtime_registration():
    """Test that both runtimes are registered."""
    print("\n" + "="*80)
    print("TEST 1: Runtime Registration")
    print("="*80 + "\n")

    # Get registered runtimes
    registered = RuntimeRegistry.list_runtimes()

    print(f"Registered runtimes: {list(registered.keys())}")

    # Check both runtimes are registered
    if RuntimeType.DEFAULT in registered:
        print(f"✅ Default runtime registered: {registered[RuntimeType.DEFAULT]}")
    else:
        print(f"❌ Default runtime NOT registered")
        return False

    if RuntimeType.CLAUDE_CODE in registered:
        print(f"✅ Claude Code runtime registered: {registered[RuntimeType.CLAUDE_CODE]}")
    else:
        print(f"❌ Claude Code runtime NOT registered")
        return False

    return True


def test_model_validation():
    """Test model validation for different runtimes."""
    print("\n" + "="*80)
    print("TEST 2: Model Validation")
    print("="*80 + "\n")

    test_cases = [
        # Default runtime - should accept any model
        ("default", "gpt-4", True, "GPT-4 should work with default runtime"),
        ("default", "claude-3-opus", True, "Claude should work with default runtime"),
        ("default", "gemini-pro", True, "Gemini should work with default runtime"),

        # Claude Code runtime - should only accept Claude models
        ("claude_code", "kubiya/claude-sonnet-4", True, "Claude Sonnet should work with claude_code runtime"),
        ("claude_code", "claude-3-opus-20240229", True, "Claude Opus should work with claude_code runtime"),
        ("claude_code", "gpt-4", False, "GPT-4 should NOT work with claude_code runtime"),
        ("claude_code", "gemini-pro", False, "Gemini should NOT work with claude_code runtime"),
        ("claude_code", None, False, "None model should fail validation"),
    ]

    passed = 0
    failed = 0

    for runtime_type, model_id, should_pass, description in test_cases:
        is_valid, errors = validate_agent_for_runtime(
            runtime_type=runtime_type,
            model_id=model_id,
        )

        if (is_valid == should_pass):
            print(f"✅ {description}")
            passed += 1
        else:
            print(f"❌ {description}")
            print(f"   Expected: {should_pass}, Got: {is_valid}")
            if errors:
                print(f"   Errors: {errors}")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed\n")
    return failed == 0


def test_requirements_info():
    """Test getting requirements information."""
    print("\n" + "="*80)
    print("TEST 3: Requirements Information")
    print("="*80 + "\n")

    all_requirements = list_all_runtime_requirements()

    for runtime_type, requirements in all_requirements.items():
        print(f"Runtime: {runtime_type}")
        print(f"  Description: {requirements['model_requirement']['description'][:80]}...")
        print(f"  Supported Providers: {', '.join(requirements['model_requirement']['supported_providers'])}")
        print(f"  Supported Families: {', '.join(requirements['model_requirement']['supported_families'])}")
        print(f"  Example Models: {', '.join(requirements['model_requirement']['examples'][:3])}")
        print(f"  Max History Length: {requirements.get('max_history_length', 'N/A')}")
        print()

    # Check that we have requirements for both runtimes
    if 'default' in all_requirements and 'claude_code' in all_requirements:
        return True
    else:
        print("❌ Missing requirements for one or more runtimes")
        return False


def test_validation_errors():
    """Test that validation provides helpful error messages."""
    print("\n" + "="*80)
    print("TEST 4: Validation Error Messages")
    print("="*80 + "\n")

    # Test claude_code with wrong model
    is_valid, errors = validate_agent_for_runtime(
        runtime_type="claude_code",
        model_id="gpt-4",
    )

    print(f"Testing claude_code runtime with gpt-4 model:")
    print(f"  Valid: {is_valid}")
    print(f"  Error Message:")
    for error in errors:
        print(f"    {error}")
    print()

    # Check that error message is helpful
    if errors and "claude" in errors[0].lower():
        print("✅ Error message mentions Claude requirement")
        return True
    else:
        print("❌ Error message should mention Claude requirement")
        return False


def test_claude_model_patterns():
    """Test various Claude model ID patterns."""
    print("\n" + "="*80)
    print("TEST 5: Claude Model Pattern Matching")
    print("="*80 + "\n")

    claude_models = [
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-5-sonnet-20241022",
        "claude-3-haiku-20240307",
        "kubiya/claude-sonnet-4",
        "kubiya/claude-opus-4",
        "anthropic.claude-3-sonnet",
    ]

    non_claude_models = [
        "gpt-4",
        "gpt-4-turbo",
        "gpt-3.5-turbo",
        "gemini-pro",
        "mistral-large",
    ]

    passed = 0
    failed = 0

    print("Testing Claude models (should all PASS):")
    for model in claude_models:
        is_valid, errors = validate_agent_for_runtime(
            runtime_type="claude_code",
            model_id=model,
        )
        if is_valid:
            print(f"  ✅ {model}")
            passed += 1
        else:
            print(f"  ❌ {model} - {errors}")
            failed += 1

    print("\nTesting non-Claude models (should all FAIL):")
    for model in non_claude_models:
        is_valid, errors = validate_agent_for_runtime(
            runtime_type="claude_code",
            model_id=model,
        )
        if not is_valid:
            print(f"  ✅ {model} correctly rejected")
            passed += 1
        else:
            print(f"  ❌ {model} should have been rejected")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed\n")
    return failed == 0


if __name__ == "__main__":
    print("\n" + "="*80)
    print("COMPLETE RUNTIME VALIDATION SYSTEM TEST")
    print("="*80)

    results = []

    results.append(("Runtime Registration", test_runtime_registration()))
    results.append(("Model Validation", test_model_validation()))
    results.append(("Requirements Info", test_requirements_info()))
    results.append(("Error Messages", test_validation_errors()))
    results.append(("Claude Model Patterns", test_claude_model_patterns()))

    print("\n" + "="*80)
    print("FINAL RESULTS")
    print("="*80)

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {test_name}: {status}")
        if not passed:
            all_passed = False

    print()

    if all_passed:
        print("🎉 All validation tests passed!")
        print("\n✅ The runtime validation system is working correctly.")
        print("✅ Both runtimes (default and claude_code) are registered.")
        print("✅ Model compatibility validation is enforced.")
        print("✅ Claude Code runtime only accepts Claude models.")
        print("✅ Default runtime accepts all models.")
        print("\n📝 Next Steps:")
        print("   1. Start Control Plane API to test API endpoints")
        print("   2. Test /api/v1/runtimes endpoint")
        print("   3. Test /api/v1/runtimes/validate endpoint")
        print("   4. Update database schema with runtime_type columns")
        print("   5. Integrate validation into agent/team CRUD endpoints")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        sys.exit(1)
