#!/usr/bin/env python3
"""
End-to-end test of the new runtime system.

This script tests:
1. BaseRuntime abstract class
2. RuntimeRegistry system
3. RuntimeFactory
4. Lifecycle hooks
5. Control Plane integration
6. Complete execution flow
"""

import asyncio
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent / "control_plane_api"))

from worker.runtimes.base import (
    BaseRuntime,
    RuntimeType,
    RuntimeCapabilities,
    RuntimeExecutionContext,
    RuntimeExecutionResult,
    RuntimeRegistry,
)
from worker.runtimes.factory import RuntimeFactory
from unittest.mock import MagicMock, AsyncMock
from typing import AsyncIterator, Optional, Callable, Dict


# ==================== Test Runtime Implementation ====================

@RuntimeRegistry.register(RuntimeType.DEFAULT)
class TestRuntime(BaseRuntime):
    """
    Test runtime to verify the system works end-to-end.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.before_execute_called = False
        self.after_execute_called = False
        self.on_error_called = False

    async def _execute_impl(
        self, context: RuntimeExecutionContext
    ) -> RuntimeExecutionResult:
        """Core execution logic."""
        self.logger.info("TestRuntime executing", execution_id=context.execution_id)

        # Simulate some work
        await asyncio.sleep(0.1)

        return RuntimeExecutionResult(
            response=f"Test response for: {context.prompt}",
            usage={"input_tokens": 10, "output_tokens": 20, "total_tokens": 30},
            success=True,
            model=context.model_id or "test-model",
            finish_reason="stop",
        )

    async def _stream_execute_impl(
        self,
        context: RuntimeExecutionContext,
        event_callback: Optional[Callable[[Dict], None]] = None,
    ) -> AsyncIterator[RuntimeExecutionResult]:
        """Streaming execution logic."""
        self.logger.info("TestRuntime streaming", execution_id=context.execution_id)

        # Simulate streaming chunks
        chunks = ["Hello", " ", "World", "!"]

        for chunk in chunks:
            await asyncio.sleep(0.05)

            # Publish event
            if event_callback:
                event_callback({
                    "type": "content_chunk",
                    "content": chunk,
                    "execution_id": context.execution_id,
                })

            yield RuntimeExecutionResult(
                response=chunk,
                usage={},
                success=True,
            )

        # Final result with usage
        yield RuntimeExecutionResult(
            response="",
            usage={"input_tokens": 10, "output_tokens": 20, "total_tokens": 30},
            success=True,
            finish_reason="stop",
        )

    def get_runtime_type(self) -> RuntimeType:
        """Return runtime type."""
        return RuntimeType.DEFAULT

    def get_capabilities(self) -> RuntimeCapabilities:
        """Return capabilities."""
        return RuntimeCapabilities(
            streaming=True,
            tools=True,
            mcp=False,
            hooks=True,
            cancellation=True,
            conversation_history=True,
            custom_tools=False,
        )

    # Override lifecycle hooks for testing
    async def before_execute(self, context: RuntimeExecutionContext):
        """Before execute hook."""
        self.before_execute_called = True
        self.logger.info("before_execute hook called")

    async def after_execute(
        self, context: RuntimeExecutionContext, result: RuntimeExecutionResult
    ):
        """After execute hook."""
        self.after_execute_called = True
        self.logger.info("after_execute hook called", success=result.success)

    async def on_error(
        self, context: RuntimeExecutionContext, error: Exception
    ) -> RuntimeExecutionResult:
        """Error hook."""
        self.on_error_called = True
        self.logger.error("on_error hook called", error=str(error))
        return await super().on_error(context, error)


# ==================== Test Functions ====================


async def test_1_basic_imports():
    """Test 1: Basic imports and structure."""
    print("\n" + "=" * 80)
    print("TEST 1: Basic Imports and Structure")
    print("=" * 80)

    try:
        print("✅ BaseRuntime imported")
        print("✅ RuntimeRegistry imported")
        print("✅ RuntimeType imported")
        print("✅ RuntimeCapabilities imported")
        print("✅ RuntimeFactory imported")
        print("\n✅ TEST 1 PASSED: All imports successful")
        return True
    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {e}")
        return False


async def test_2_runtime_registration():
    """Test 2: Runtime registration system."""
    print("\n" + "=" * 80)
    print("TEST 2: Runtime Registration")
    print("=" * 80)

    try:
        # Check if runtime is registered
        available = RuntimeRegistry.list_available()
        print(f"Available runtimes: {[rt.value for rt in available]}")

        if RuntimeType.DEFAULT not in available:
            raise AssertionError("TestRuntime not registered")

        print("✅ TestRuntime registered successfully")

        # Get runtime class
        runtime_class = RuntimeRegistry.get(RuntimeType.DEFAULT)
        print(f"✅ Retrieved runtime class: {runtime_class.__name__}")

        # Get runtime info
        info = RuntimeRegistry.get_runtime_info_all()
        print(f"✅ Runtime info retrieved: {list(info.keys())}")

        print("\n✅ TEST 2 PASSED: Registration system works")
        return True
    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_3_runtime_creation():
    """Test 3: Runtime creation via factory."""
    print("\n" + "=" * 80)
    print("TEST 3: Runtime Creation")
    print("=" * 80)

    try:
        # Create mock dependencies
        mock_control_plane = MagicMock()
        mock_control_plane.cache_metadata = MagicMock()
        mock_cancellation_manager = MagicMock()
        mock_cancellation_manager.register = MagicMock()
        mock_cancellation_manager.unregister = MagicMock()

        # Create runtime via factory
        runtime = RuntimeFactory.create_runtime(
            runtime_type=RuntimeType.DEFAULT,
            control_plane_client=mock_control_plane,
            cancellation_manager=mock_cancellation_manager,
        )

        print(f"✅ Runtime created: {runtime.__class__.__name__}")

        # Check capabilities
        caps = runtime.get_capabilities()
        print(f"✅ Capabilities:")
        print(f"   - Streaming: {caps.streaming}")
        print(f"   - Tools: {caps.tools}")
        print(f"   - MCP: {caps.mcp}")
        print(f"   - Hooks: {caps.hooks}")
        print(f"   - Cancellation: {caps.cancellation}")

        # Check runtime info
        info = runtime.get_runtime_info()
        print(f"✅ Runtime info: {info}")

        print("\n✅ TEST 3 PASSED: Runtime creation works")
        return True
    except Exception as e:
        print(f"\n❌ TEST 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_4_execution():
    """Test 4: Non-streaming execution."""
    print("\n" + "=" * 80)
    print("TEST 4: Non-Streaming Execution")
    print("=" * 80)

    try:
        # Create runtime
        mock_control_plane = MagicMock()
        mock_control_plane.cache_metadata = MagicMock()
        mock_cancellation_manager = MagicMock()
        mock_cancellation_manager.register = MagicMock()
        mock_cancellation_manager.unregister = MagicMock()

        runtime = RuntimeFactory.create_runtime(
            runtime_type=RuntimeType.DEFAULT,
            control_plane_client=mock_control_plane,
            cancellation_manager=mock_cancellation_manager,
        )

        # Create context
        context = RuntimeExecutionContext(
            execution_id="test-exec-123",
            agent_id="agent-456",
            organization_id="org-789",
            prompt="Hello, test!",
            system_prompt="You are a test assistant",
            model_id="test-model",
        )

        # Execute
        print("Executing...")
        result = await runtime.execute(context)

        # Verify result
        assert result.success, "Execution should succeed"
        assert len(result.response) > 0, "Response should not be empty"
        assert result.usage["total_tokens"] == 30, "Usage should be tracked"

        print(f"✅ Execution succeeded")
        print(f"   Response: {result.response[:50]}...")
        print(f"   Usage: {result.usage}")
        print(f"   Model: {result.model}")

        # Verify lifecycle hooks
        assert runtime.before_execute_called, "before_execute should be called"
        assert runtime.after_execute_called, "after_execute should be called"
        print(f"✅ Lifecycle hooks called")

        # Verify Control Plane integration
        mock_control_plane.cache_metadata.assert_called_once()
        print(f"✅ Control Plane metadata cached")

        # Verify cancellation manager
        mock_cancellation_manager.register.assert_called_once()
        mock_cancellation_manager.unregister.assert_called_once()
        print(f"✅ Cancellation manager integrated")

        print("\n✅ TEST 4 PASSED: Execution works end-to-end")
        return True
    except Exception as e:
        print(f"\n❌ TEST 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_5_streaming():
    """Test 5: Streaming execution."""
    print("\n" + "=" * 80)
    print("TEST 5: Streaming Execution")
    print("=" * 80)

    try:
        # Create runtime
        mock_control_plane = MagicMock()
        mock_control_plane.cache_metadata = MagicMock()
        mock_cancellation_manager = MagicMock()
        mock_cancellation_manager.register = MagicMock()
        mock_cancellation_manager.unregister = MagicMock()

        runtime = RuntimeFactory.create_runtime(
            runtime_type=RuntimeType.DEFAULT,
            control_plane_client=mock_control_plane,
            cancellation_manager=mock_cancellation_manager,
        )

        # Create context
        context = RuntimeExecutionContext(
            execution_id="test-exec-456",
            agent_id="agent-789",
            organization_id="org-123",
            prompt="Stream test",
        )

        # Event callback
        events_received = []

        def event_callback(event):
            events_received.append(event)

        # Stream execution
        print("Streaming...")
        chunks = []
        async for chunk in runtime.stream_execute(context, event_callback):
            chunks.append(chunk)
            if chunk.response:
                print(f"   Chunk: {repr(chunk.response)}")

        # Verify
        assert len(chunks) > 0, "Should receive chunks"
        assert len(events_received) > 0, "Should receive events"

        print(f"✅ Received {len(chunks)} chunks")
        print(f"✅ Received {len(events_received)} events")

        # Verify final result
        final_chunk = chunks[-1]
        assert final_chunk.finish_reason == "stop", "Should have finish reason"
        assert final_chunk.usage["total_tokens"] == 30, "Should have usage"
        print(f"✅ Final chunk has usage and finish reason")

        # Verify hooks
        assert runtime.before_execute_called, "before_execute should be called"
        assert runtime.after_execute_called, "after_execute should be called"
        print(f"✅ Lifecycle hooks called for streaming")

        print("\n✅ TEST 5 PASSED: Streaming works end-to-end")
        return True
    except Exception as e:
        print(f"\n❌ TEST 5 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_6_error_handling():
    """Test 6: Error handling."""
    print("\n" + "=" * 80)
    print("TEST 6: Error Handling")
    print("=" * 80)

    try:
        # Create failing runtime
        @RuntimeRegistry.register(RuntimeType.CLAUDE_CODE)
        class FailingRuntime(BaseRuntime):
            async def _execute_impl(self, context):
                raise ValueError("Intentional test error")

            async def _stream_execute_impl(self, context, event_callback=None):
                raise ValueError("Intentional test error")
                yield  # Never reached

            def get_runtime_type(self):
                return RuntimeType.CLAUDE_CODE

            def get_capabilities(self):
                return RuntimeCapabilities()

        # Create runtime
        mock_control_plane = MagicMock()
        mock_control_plane.cache_metadata = MagicMock()
        mock_cancellation_manager = MagicMock()

        runtime = RuntimeFactory.create_runtime(
            runtime_type=RuntimeType.CLAUDE_CODE,
            control_plane_client=mock_control_plane,
            cancellation_manager=mock_cancellation_manager,
        )

        # Create context
        context = RuntimeExecutionContext(
            execution_id="test-exec-error",
            agent_id="agent-error",
            organization_id="org-error",
            prompt="This will fail",
        )

        # Execute (should handle error gracefully)
        print("Executing (expecting error)...")
        result = await runtime.execute(context)

        # Verify error handling
        assert not result.success, "Execution should fail"
        assert result.error is not None, "Should have error message"
        assert "Intentional test error" in result.error, "Should contain error details"

        print(f"✅ Error handled gracefully")
        print(f"   Error: {result.error}")

        print("\n✅ TEST 6 PASSED: Error handling works")
        return True
    except Exception as e:
        print(f"\n❌ TEST 6 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_7_configuration_validation():
    """Test 7: Configuration validation."""
    print("\n" + "=" * 80)
    print("TEST 7: Configuration Validation")
    print("=" * 80)

    try:
        # Create runtime
        mock_control_plane = MagicMock()
        mock_control_plane.cache_metadata = MagicMock()
        mock_cancellation_manager = MagicMock()

        runtime = RuntimeFactory.create_runtime(
            runtime_type=RuntimeType.DEFAULT,
            control_plane_client=mock_control_plane,
            cancellation_manager=mock_cancellation_manager,
        )

        # Test 1: Missing prompt (should fail)
        context_invalid = RuntimeExecutionContext(
            execution_id="test",
            agent_id="test",
            organization_id="test",
            prompt="",  # Empty prompt
        )

        result = await runtime.execute(context_invalid)
        assert not result.success, "Should fail with empty prompt"
        print(f"✅ Empty prompt validation works")

        # Test 2: Valid context (should pass)
        context_valid = RuntimeExecutionContext(
            execution_id="test",
            agent_id="test",
            organization_id="test",
            prompt="Valid prompt",
        )

        result = await runtime.execute(context_valid)
        assert result.success, "Should succeed with valid prompt"
        print(f"✅ Valid prompt validation works")

        print("\n✅ TEST 7 PASSED: Configuration validation works")
        return True
    except Exception as e:
        print(f"\n❌ TEST 7 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("RUNTIME SYSTEM END-TO-END TESTS")
    print("=" * 80)

    tests = [
        ("Basic Imports", test_1_basic_imports),
        ("Runtime Registration", test_2_runtime_registration),
        ("Runtime Creation", test_3_runtime_creation),
        ("Non-Streaming Execution", test_4_execution),
        ("Streaming Execution", test_5_streaming),
        ("Error Handling", test_6_error_handling),
        ("Configuration Validation", test_7_configuration_validation),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            passed = await test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")

    print("\n" + "=" * 80)
    print(f"RESULTS: {passed_count}/{total_count} tests passed")
    print("=" * 80)

    if passed_count == total_count:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        print("\nThe runtime system is working end-to-end:")
        print("  ✅ Abstract base class")
        print("  ✅ Runtime registry")
        print("  ✅ Factory pattern")
        print("  ✅ Lifecycle hooks")
        print("  ✅ Control Plane integration")
        print("  ✅ Error handling")
        print("  ✅ Configuration validation")
        print("  ✅ Streaming execution")
        return True
    else:
        print(f"\n⚠️  {total_count - passed_count} test(s) failed")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
