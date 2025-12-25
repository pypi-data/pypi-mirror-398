#!/usr/bin/env python3
"""
Test Claude Code runtime directly without Temporal.
This bypasses Temporal auth issues and tests the runtime system directly.
"""
import asyncio
import sys
import os

# Add control_plane_api to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from control_plane_api.worker.runtimes.base import RuntimeRegistry, RuntimeType, RuntimeExecutionContext
from control_plane_api.worker.runtimes.factory import RuntimeFactory

# Mock clients
class MockControlPlaneClient:
    def cache_metadata(self, execution_id, entity_type):
        print(f"   [Control Plane] Cached metadata for {execution_id}")

    def publish_event(self, execution_id, event_type, data):
        print(f"   [Control Plane] Event: {event_type} - {data.get('type', 'N/A')}")

class MockCancellationManager:
    def register(self, execution_id, instance, instance_type):
        print(f"   [Cancellation] Registered {execution_id}")

    def unregister(self, execution_id):
        print(f"   [Cancellation] Unregistered {execution_id}")

    def cancel(self, execution_id):
        return {"success": True}

    def set_run_id(self, execution_id, run_id):
        pass

async def test_default_runtime():
    """Test DefaultRuntime (Agno-based)"""
    print("\n" + "=" * 80)
    print("TEST 1: DEFAULT RUNTIME (AGNO)")
    print("=" * 80)

    # Create runtime
    factory = RuntimeFactory()
    runtime = factory.create_runtime(
        runtime_type=RuntimeType.DEFAULT,
        control_plane_client=MockControlPlaneClient(),
        cancellation_manager=MockCancellationManager()
    )

    print(f"✅ Created runtime: {runtime.__class__.__name__}")
    print(f"   Type: {runtime.get_runtime_type()}")
    print(f"   Info: {runtime.get_runtime_info()}")
    print()

    # Create execution context
    context = RuntimeExecutionContext(
        execution_id="test-default-001",
        agent_id="test-agent",
        organization_id="test-org",
        prompt="Hello! What is 2+2? Please explain briefly.",
        system_prompt="You are a helpful AI assistant.",
        model_id="claude-sonnet-4",
        skills=[],
        conversation_history=[],
        runtime_type=RuntimeType.DEFAULT
    )

    print("📝 Execution Context:")
    print(f"   Execution ID: {context.execution_id}")
    print(f"   Prompt: {context.prompt}")
    print()

    # Execute (non-streaming)
    print("⚡ Executing (non-streaming)...")
    try:
        result = await runtime.execute(context)

        print()
        print("✅ Execution Result:")
        print(f"   Success: {result.success}")
        print(f"   Response: {result.response[:200]}...")
        print(f"   Usage: {result.usage}")
        print(f"   Model: {result.model}")
        print()

    except Exception as e:
        print(f"❌ Execution failed: {e}")
        import traceback
        traceback.print_exc()

async def test_claude_code_runtime():
    """Test ClaudeCodeRuntime"""
    print("\n" + "=" * 80)
    print("TEST 2: CLAUDE CODE RUNTIME")
    print("=" * 80)

    # Check if runtime is registered
    print(f"Claude Code runtime registered: {RuntimeType.CLAUDE_CODE in RuntimeRegistry._registry}")

    if RuntimeType.CLAUDE_CODE not in RuntimeRegistry._registry:
        print("❌ Claude Code runtime not registered!")
        return

    # Create runtime
    factory = RuntimeFactory()
    runtime = factory.create_runtime(
        runtime_type=RuntimeType.CLAUDE_CODE,
        control_plane_client=MockControlPlaneClient(),
        cancellation_manager=MockCancellationManager()
    )

    print(f"✅ Created runtime: {runtime.__class__.__name__}")
    print(f"   Type: {runtime.get_runtime_type()}")
    print(f"   Info: {runtime.get_runtime_info()}")
    print()

    # Create execution context
    context = RuntimeExecutionContext(
        execution_id="test-claude-001",
        agent_id="test-agent-claude",
        organization_id="test-org",
        prompt="Count from 1 to 3. Be very brief.",
        system_prompt="You are a helpful AI assistant powered by Claude Code SDK.",
        model_id="claude-sonnet-4",
        skills=[],
        conversation_history=[],
        runtime_type=RuntimeType.CLAUDE_CODE
    )

    print("📝 Execution Context:")
    print(f"   Execution ID: {context.execution_id}")
    print(f"   Prompt: {context.prompt}")
    print()

    # Test streaming execution
    print("⚡ Executing (streaming)...")
    try:
        chunk_count = 0
        async for result in runtime.stream_execute(context):
            chunk_count += 1
            if result.response:
                print(f"   Chunk {chunk_count}: {result.response[:100]}")

            if result.finish_reason:
                print()
                print("✅ Streaming Complete:")
                print(f"   Total chunks: {chunk_count}")
                print(f"   Usage: {result.usage}")
                print(f"   Model: {result.model}")
                print()

    except Exception as e:
        print(f"❌ Execution failed: {e}")
        import traceback
        traceback.print_exc()

async def main():
    print("\n" + "=" * 80)
    print("DIRECT RUNTIME TESTING (NO TEMPORAL)")
    print("=" * 80)
    print()
    print("This test directly invokes the runtime system without Temporal workflows.")
    print("It demonstrates that the runtime registration and execution works correctly.")
    print()

    # Test 1: Default Runtime
    await test_default_runtime()

    # Test 2: Claude Code Runtime
    await test_claude_code_runtime()

    print("=" * 80)
    print("ALL TESTS COMPLETE")
    print("=" * 80)
    print()

if __name__ == "__main__":
    asyncio.run(main())
