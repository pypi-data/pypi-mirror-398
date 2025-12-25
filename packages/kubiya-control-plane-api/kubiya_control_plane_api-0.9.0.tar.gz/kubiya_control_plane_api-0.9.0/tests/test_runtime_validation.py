#!/usr/bin/env python3
"""Test runtime validation system."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'control_plane_api'))

from worker.runtimes.validation import (
    validate_agent_for_runtime,
    get_runtime_requirements_info,
    list_all_runtime_requirements,
)


def test_model_validation():
    """Test model validation for different runtimes."""
    print("\n" + "="*80)
    print("TEST 1: Model Validation")
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

        expected = "✅ PASS" if should_pass else "❌ FAIL"
        actual = "✅ PASS" if is_valid else "❌ FAIL"

        if (is_valid == should_pass):
            print(f"✅ {description}")
            print(f"   Runtime: {runtime_type}, Model: {model_id}, Result: {actual}")
            passed += 1
        else:
            print(f"❌ {description}")
            print(f"   Runtime: {runtime_type}, Model: {model_id}")
            print(f"   Expected: {expected}, Got: {actual}")
            if errors:
                print(f"   Errors: {errors}")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed\n")
    return failed == 0


def test_requirements_info():
    """Test getting requirements information."""
    print("\n" + "="*80)
    print("TEST 2: Requirements Information")
    print("="*80 + "\n")

    all_requirements = list_all_runtime_requirements()

    for runtime_type, requirements in all_requirements.items():
        print(f"Runtime: {runtime_type}")
        print(f"  Description: {requirements['model_requirement']['description']}")
        print(f"  Supported Providers: {', '.join(requirements['model_requirement']['supported_providers'])}")
        print(f"  Supported Families: {', '.join(requirements['model_requirement']['supported_families'])}")
        print(f"  Example Models: {', '.join(requirements['model_requirement']['examples'][:3])}")
        print(f"  Max History Length: {requirements.get('max_history_length', 'N/A')}")
        print()

    return True


def test_validation_errors():
    """Test that validation provides helpful error messages."""
    print("\n" + "="*80)
    print("TEST 3: Validation Error Messages")
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


if __name__ == "__main__":
    print("\n" + "="*80)
    print("RUNTIME VALIDATION SYSTEM TEST")
    print("="*80)

    results = []

    results.append(("Model Validation", test_model_validation()))
    results.append(("Requirements Info", test_requirements_info()))
    results.append(("Error Messages", test_validation_errors()))

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
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        sys.exit(1)
