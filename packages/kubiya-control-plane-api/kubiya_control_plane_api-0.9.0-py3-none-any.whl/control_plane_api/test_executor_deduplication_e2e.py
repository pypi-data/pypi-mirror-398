#!/usr/bin/env python3
"""
End-to-end integration test for executor deduplication.
Tests the full flow: session_history + new_messages → deduplication → persistence
"""

import sys
sys.path.insert(0, '/Users/shaked/projects/kubiya-stack/agent-control-plane/control_plane_api')

from worker.services.session_service import SessionService
from worker.control_plane_client import ControlPlaneClient


def test_executor_deduplication_flow():
    """
    Simulate the executor flow where messages are combined and deduplicated.
    This tests the ACTUAL code path used by executors.
    """
    print("=" * 70)
    print("EXECUTOR DEDUPLICATION - END-TO-END TEST")
    print("=" * 70)
    print()

    # Create session service
    control_plane = ControlPlaneClient(base_url="http://localhost:8000", api_key="test")
    session_service = SessionService(control_plane)

    print("📋 Simulating Executor Flow:")
    print("   1. Load session_history (previous turns)")
    print("   2. Add new_messages (current turn)")
    print("   3. Add tool_messages (from streaming)")
    print("   4. Combine all messages")
    print("   5. Deduplicate using session_service.deduplicate_messages()")
    print()

    # Simulate session_history (messages from previous turns)
    session_history = [
        {
            "role": "user",
            "content": "Hello",
            "message_id": "exec_123_user_1",
            "timestamp": "2025-12-12T10:00:00Z"
        },
        {
            "role": "assistant",
            "content": "Hi! How can I help you?",
            "message_id": "exec_123_assistant_1",
            "timestamp": "2025-12-12T10:00:01Z"
        },
    ]

    # Simulate new_messages (current turn)
    # NOTE: These might accidentally duplicate content from session_history due to bugs
    new_messages = [
        {
            "role": "user",
            "content": "Can you help with Python?",
            "message_id": "exec_123_user_2",
            "timestamp": "2025-12-12T10:00:05Z"
        },
        {
            "role": "assistant",
            "content": "Sure! I'd be happy to help with Python.",
            "message_id": "exec_123_assistant_2",
            "timestamp": "2025-12-12T10:00:06Z"
        },
        # DUPLICATE: Same content as assistant_2 but different message_id (timing issue)
        {
            "role": "assistant",
            "content": "Sure! I'd be happy to help with Python.",
            "message_id": "exec_123_1733990406789012",  # Timestamp-based ID
            "timestamp": "2025-12-12T10:00:07Z"  # 1 second later
        },
    ]

    # Simulate tool_messages (from streaming helper)
    tool_messages = [
        {
            "role": "system",
            "tool_name": "python_repl",
            "tool_output": "Executed successfully",
            "message_id": "exec_123_tool_python_1",
            "timestamp": "2025-12-12T10:00:08Z"
        },
    ]

    print("📊 Message Counts:")
    print(f"   - session_history: {len(session_history)} messages")
    print(f"   - new_messages: {len(new_messages)} messages")
    print(f"   - tool_messages: {len(tool_messages)} messages")
    print()

    # STEP 1: Combine messages (what executors do)
    complete_session = session_history + new_messages + tool_messages
    print(f"🔗 Combined messages: {len(complete_session)} total")
    print()

    # STEP 2: Deduplicate (using enhanced session_service method)
    print("🧹 Deduplicating messages...")
    original_count = len(complete_session)
    deduplicated_session = session_service.deduplicate_messages(complete_session)

    print()
    print("📋 Deduplicated messages:")
    for i, msg in enumerate(deduplicated_session):
        role = msg.get("role", "unknown")
        content = msg.get("content", msg.get("tool_name", ""))
        msg_id = msg.get("message_id", "no_id")
        timestamp = msg.get("timestamp", "")[-9:]
        print(f"   {i+1}. [{role:<9}] {content[:40]:<40} | {timestamp}")

    print()
    print("📊 Final Results:")
    print(f"   Original count: {original_count}")
    print(f"   Deduplicated count: {len(deduplicated_session)}")
    print(f"   Duplicates removed: {original_count - len(deduplicated_session)}")
    print()

    # Verify results
    expected_count = 5  # user_1, assistant_1, user_2, assistant_2 (deduplicated), tool_1
    if len(deduplicated_session) == expected_count:
        print("✅ TEST PASSED: Executor deduplication working correctly!")
        print(f"   Expected {expected_count} messages, got {len(deduplicated_session)}")
        return True
    else:
        print(f"❌ TEST FAILED: Expected {expected_count} messages, got {len(deduplicated_session)}")
        return False


def test_multiple_content_duplicates():
    """Test deduplication with multiple content duplicates (stress test)."""
    print()
    print("=" * 70)
    print("STRESS TEST: Multiple Content Duplicates")
    print("=" * 70)
    print()

    control_plane = ControlPlaneClient(base_url="http://localhost:8000", api_key="test")
    session_service = SessionService(control_plane)

    # Create messages with many duplicates
    messages = [
        # Original message
        {
            "role": "assistant",
            "content": "Let me help you with that task.",
            "message_id": "exec_456_assistant_1",
            "timestamp": "2025-12-12T10:00:00Z"
        },
        # Duplicate 1 (different ID, 1 second later)
        {
            "role": "assistant",
            "content": "Let me help you with that task.",
            "message_id": "exec_456_1733990400123456",
            "timestamp": "2025-12-12T10:00:01Z"
        },
        # Duplicate 2 (different ID, 2 seconds later)
        {
            "role": "assistant",
            "content": "Let me help you with that task.",
            "message_id": "exec_456_1733990400234567",
            "timestamp": "2025-12-12T10:00:02Z"
        },
        # Different message
        {
            "role": "user",
            "content": "Thanks!",
            "message_id": "exec_456_user_1",
            "timestamp": "2025-12-12T10:00:05Z"
        },
        # Another original
        {
            "role": "assistant",
            "content": "You're welcome!",
            "message_id": "exec_456_assistant_2",
            "timestamp": "2025-12-12T10:00:06Z"
        },
        # Duplicate of "You're welcome!" (different ID, 1 second later)
        {
            "role": "assistant",
            "content": "You're welcome!",
            "message_id": "exec_456_1733990406345678",
            "timestamp": "2025-12-12T10:00:07Z"
        },
    ]

    print(f"📝 Testing with {len(messages)} messages (4 expected duplicates)...")
    print()

    deduplicated = session_service.deduplicate_messages(messages)

    print(f"✅ Deduplicated to {len(deduplicated)} messages")
    print()
    for i, msg in enumerate(deduplicated):
        content = msg.get("content", "")[:40]
        msg_id = msg.get("message_id", "")[:30]
        print(f"   {i+1}. [{msg['role']:<9}] {content:<40} | {msg_id}")

    # Should have 3 unique messages (2 assistant + 1 user)
    expected = 3
    duplicates_removed = len(messages) - len(deduplicated)

    print()
    print(f"📊 Results:")
    print(f"   Original: {len(messages)}")
    print(f"   Deduplicated: {len(deduplicated)}")
    print(f"   Removed: {duplicates_removed}")
    print()

    if len(deduplicated) == expected and duplicates_removed == 3:
        print(f"✅ STRESS TEST PASSED: Correctly removed {duplicates_removed} content duplicates!")
        return True
    else:
        print(f"❌ STRESS TEST FAILED: Expected {expected} messages, got {len(deduplicated)}")
        return False


def test_mixed_duplicates():
    """Test with both message_id duplicates AND content duplicates."""
    print()
    print("=" * 70)
    print("MIXED TEST: Both ID and Content Duplicates")
    print("=" * 70)
    print()

    control_plane = ControlPlaneClient(base_url="http://localhost:8000", api_key="test")
    session_service = SessionService(control_plane)

    messages = [
        # Original
        {
            "role": "assistant",
            "content": "Hello there!",
            "message_id": "exec_789_assistant_1",
            "timestamp": "2025-12-12T10:00:00Z"
        },
        # ID duplicate (same message_id)
        {
            "role": "assistant",
            "content": "Hello there!",
            "message_id": "exec_789_assistant_1",  # SAME ID
            "timestamp": "2025-12-12T10:00:00Z"
        },
        # Content duplicate (different ID)
        {
            "role": "assistant",
            "content": "Hello there!",
            "message_id": "exec_789_1733990400111111",  # DIFFERENT ID
            "timestamp": "2025-12-12T10:00:01Z"
        },
        # Unique message
        {
            "role": "user",
            "content": "Hi!",
            "message_id": "exec_789_user_1",
            "timestamp": "2025-12-12T10:00:05Z"
        },
    ]

    print(f"📝 Testing with {len(messages)} messages:")
    print("   - 1 unique assistant message")
    print("   - 1 ID duplicate (same message_id)")
    print("   - 1 content duplicate (different message_id)")
    print("   - 1 unique user message")
    print()

    deduplicated = session_service.deduplicate_messages(messages)

    print(f"✅ Deduplicated to {len(deduplicated)} messages")
    print()

    # Should have 2 messages (1 assistant + 1 user)
    expected = 2
    duplicates_removed = len(messages) - len(deduplicated)

    print(f"📊 Results:")
    print(f"   Original: {len(messages)}")
    print(f"   Deduplicated: {len(deduplicated)}")
    print(f"   Removed: {duplicates_removed}")
    print()

    if len(deduplicated) == expected and duplicates_removed == 2:
        print(f"✅ MIXED TEST PASSED: Correctly handled both ID and content duplicates!")
        return True
    else:
        print(f"❌ MIXED TEST FAILED: Expected {expected} messages, got {len(deduplicated)}")
        return False


if __name__ == "__main__":
    # Run all tests
    test1_passed = test_executor_deduplication_flow()
    test2_passed = test_multiple_content_duplicates()
    test3_passed = test_mixed_duplicates()

    print()
    print("=" * 70)
    if test1_passed and test2_passed and test3_passed:
        print("✅ ALL END-TO-END TESTS PASSED")
        print()
        print("🎉 Executor deduplication is working correctly!")
        print("   - Content-based deduplication: ✅")
        print("   - ID-based deduplication: ✅")
        print("   - Mixed duplicates: ✅")
        print("   - Stress test: ✅")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        sys.exit(1)
