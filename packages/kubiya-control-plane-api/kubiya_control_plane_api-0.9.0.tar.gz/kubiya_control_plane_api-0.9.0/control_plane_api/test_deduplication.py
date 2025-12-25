#!/usr/bin/env python3
"""
Manual test script to verify message deduplication works correctly.
Tests the session_service.deduplicate_messages method.
"""

import sys
sys.path.insert(0, '/Users/shaked/projects/kubiya-stack/agent-control-plane/control_plane_api')

from worker.services.session_service import SessionService
from worker.control_plane_client import ControlPlaneClient


def test_deduplicate_messages():
    """Test that deduplicate_messages correctly removes duplicates."""

    # Create session service
    control_plane = ControlPlaneClient(base_url="http://localhost:8000", api_key="test")
    session_service = SessionService(control_plane)

    # Test data with duplicates
    messages_with_duplicates = [
        {
            "role": "user",
            "content": "Hello",
            "message_id": "exec_123_user_1",
            "timestamp": "2025-12-08T10:00:00Z"
        },
        {
            "role": "assistant",
            "content": "Hi there!",
            "message_id": "exec_123_assistant_1",
            "timestamp": "2025-12-08T10:00:01Z"
        },
        {
            "role": "user",
            "content": "Hello",  # DUPLICATE
            "message_id": "exec_123_user_1",  # SAME ID
            "timestamp": "2025-12-08T10:00:00Z"
        },
        {
            "role": "user",
            "content": "How are you?",
            "message_id": "exec_123_user_2",
            "timestamp": "2025-12-08T10:00:02Z"
        },
        {
            "role": "assistant",
            "content": "Hi there!",  # DUPLICATE
            "message_id": "exec_123_assistant_1",  # SAME ID
            "timestamp": "2025-12-08T10:00:01Z"
        },
    ]

    print(f"📝 Original messages: {len(messages_with_duplicates)}")
    print()
    for i, msg in enumerate(messages_with_duplicates):
        print(f"  {i+1}. [{msg['role']}] {msg['content'][:30]:<30} | ID: {msg['message_id']}")

    # Deduplicate
    deduplicated = session_service.deduplicate_messages(messages_with_duplicates)

    print(f"\n✅ Deduplicated messages: {len(deduplicated)}")
    print()
    for i, msg in enumerate(deduplicated):
        print(f"  {i+1}. [{msg['role']}] {msg['content'][:30]:<30} | ID: {msg['message_id']}")

    # Verify results
    print(f"\n📊 Results:")
    print(f"  Original count: {len(messages_with_duplicates)}")
    print(f"  Deduplicated count: {len(deduplicated)}")
    print(f"  Removed: {len(messages_with_duplicates) - len(deduplicated)}")

    # Check correctness
    expected_count = 3  # Only 3 unique message_ids
    if len(deduplicated) == expected_count:
        print(f"\n✅ TEST PASSED: Deduplication working correctly!")
        return True
    else:
        print(f"\n❌ TEST FAILED: Expected {expected_count} messages, got {len(deduplicated)}")
        return False


def test_content_based_deduplication():
    """Test that messages with same content but different IDs are deduplicated."""

    control_plane = ControlPlaneClient(base_url="http://localhost:8000", api_key="test")
    session_service = SessionService(control_plane)

    # Test data with duplicate content but different message_ids
    messages = [
        {
            "role": "assistant",
            "content": "Hello, how can I help you today?",
            "message_id": "exec_123_assistant_1",
            "timestamp": "2025-12-12T10:00:00Z"
        },
        {
            "role": "assistant",
            "content": "Hello, how can I help you today?",  # SAME CONTENT
            "message_id": "exec_123_1733990400123456",  # DIFFERENT ID (timestamp-based)
            "timestamp": "2025-12-12T10:00:01Z"  # Close timestamp (1 second apart)
        },
        {
            "role": "user",
            "content": "Can you help me with Python?",
            "message_id": "exec_123_user_1",
            "timestamp": "2025-12-12T10:00:02Z"
        },
        {
            "role": "assistant",
            "content": "Sure! I'd be happy to help.",
            "message_id": "exec_123_assistant_2",
            "timestamp": "2025-12-12T10:00:03Z"
        },
        {
            "role": "assistant",
            "content": "Sure! I'd be happy to help.",  # SAME CONTENT
            "message_id": "exec_123_1733990403789012",  # DIFFERENT ID
            "timestamp": "2025-12-12T10:00:04Z"  # Close timestamp (1 second apart)
        },
    ]

    print(f"\n📝 Testing content-based deduplication...")
    print(f"  Original: {len(messages)} messages")
    print()
    for i, msg in enumerate(messages):
        print(f"  {i+1}. [{msg['role']:<9}] {msg['content'][:40]:<40} | ID: {msg['message_id'][:25]}")

    # Deduplicate
    deduplicated = session_service.deduplicate_messages(messages)

    print(f"\n✅ Deduplicated messages: {len(deduplicated)}")
    print()
    for i, msg in enumerate(deduplicated):
        print(f"  {i+1}. [{msg['role']:<9}] {msg['content'][:40]:<40} | ID: {msg['message_id'][:25]}")

    # Verify results
    print(f"\n📊 Results:")
    print(f"  Original count: {len(messages)}")
    print(f"  Deduplicated count: {len(deduplicated)}")
    print(f"  Removed: {len(messages) - len(deduplicated)}")

    # Should have 3 messages (2 duplicates removed)
    expected_count = 3
    if len(deduplicated) == expected_count:
        print(f"\n✅ TEST PASSED: Content-based deduplication working!")
        return True
    else:
        print(f"\n❌ TEST FAILED: Expected {expected_count} messages, got {len(deduplicated)}")
        return False


def test_content_deduplication_with_distant_timestamps():
    """Test that messages with same content but distant timestamps are NOT deduplicated."""

    control_plane = ControlPlaneClient(base_url="http://localhost:8000", api_key="test")
    session_service = SessionService(control_plane)

    # Test data with duplicate content but timestamps > 5 seconds apart
    messages = [
        {
            "role": "assistant",
            "content": "Let me help you with that.",
            "message_id": "exec_123_assistant_1",
            "timestamp": "2025-12-12T10:00:00Z"
        },
        {
            "role": "user",
            "content": "Thanks!",
            "message_id": "exec_123_user_1",
            "timestamp": "2025-12-12T10:00:03Z"
        },
        {
            "role": "assistant",
            "content": "Let me help you with that.",  # SAME CONTENT
            "message_id": "exec_123_assistant_2",
            "timestamp": "2025-12-12T10:00:10Z"  # 10 seconds later (> 5 second threshold)
        },
    ]

    print(f"\n📝 Testing content deduplication with distant timestamps...")
    print(f"  Original: {len(messages)} messages")
    print()
    for i, msg in enumerate(messages):
        print(f"  {i+1}. [{msg['role']:<9}] {msg['content'][:40]:<40} | Time: {msg['timestamp'][-9:]}")

    # Deduplicate
    deduplicated = session_service.deduplicate_messages(messages)

    print(f"\n✅ Deduplicated messages: {len(deduplicated)}")
    print()
    for i, msg in enumerate(deduplicated):
        print(f"  {i+1}. [{msg['role']:<9}] {msg['content'][:40]:<40} | Time: {msg['timestamp'][-9:]}")

    # Verify results - should keep all 3 messages (timestamps too far apart)
    print(f"\n📊 Results:")
    print(f"  Original count: {len(messages)}")
    print(f"  Deduplicated count: {len(deduplicated)}")
    print(f"  Removed: {len(messages) - len(deduplicated)}")

    # Should have 3 messages (no duplicates removed due to timestamp distance)
    expected_count = 3
    if len(deduplicated) == expected_count:
        print(f"\n✅ TEST PASSED: Distant timestamps not incorrectly deduplicated!")
        return True
    else:
        print(f"\n❌ TEST FAILED: Expected {expected_count} messages, got {len(deduplicated)}")
        return False


def test_messages_without_ids():
    """Test that messages without IDs are handled correctly."""

    control_plane = ControlPlaneClient(base_url="http://localhost:8000", api_key="test")
    session_service = SessionService(control_plane)

    messages = [
        {
            "role": "user",
            "content": "Message 1",
            # NO message_id
            "timestamp": "2025-12-08T10:00:00Z"
        },
        {
            "role": "assistant",
            "content": "Response 1",
            "message_id": "exec_123_assistant_1",
            "timestamp": "2025-12-08T10:00:01Z"
        },
        {
            "role": "user",
            "content": "Message 2",
            # NO message_id
            "timestamp": "2025-12-08T10:00:02Z"
        },
    ]

    print(f"\n📝 Testing messages without IDs...")
    print(f"  Original: {len(messages)} messages")

    deduplicated = session_service.deduplicate_messages(messages)

    print(f"  Deduplicated: {len(deduplicated)} messages")

    # Messages without IDs should be kept (they get warning but are included)
    if len(deduplicated) == len(messages):
        print(f"✅ Messages without IDs handled correctly (kept with warning)")
        return True
    else:
        print(f"❌ Messages without IDs were incorrectly filtered")
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("MESSAGE DEDUPLICATION TEST")
    print("=" * 70)
    print()

    # Run tests
    test1_passed = test_deduplicate_messages()
    test2_passed = test_content_based_deduplication()
    test3_passed = test_content_deduplication_with_distant_timestamps()
    test4_passed = test_messages_without_ids()

    print()
    print("=" * 70)
    if test1_passed and test2_passed and test3_passed and test4_passed:
        print("✅ ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        sys.exit(1)
