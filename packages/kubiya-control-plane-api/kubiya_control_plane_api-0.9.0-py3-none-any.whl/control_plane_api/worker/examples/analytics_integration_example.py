"""
Example of integrating analytics collection into agent execution.

This shows how to instrument your agent execution to automatically
track metrics without blocking performance.
"""

import asyncio
import os
import time
from typing import Any, Dict
from datetime import datetime, timezone

# Import analytics components
from control_plane_api.worker.services.analytics_collector import (
    create_analytics_collector,
    ExecutionContext,
)


async def execute_agent_with_analytics_example():
    """
    Example showing end-to-end analytics integration.

    This demonstrates:
    1. Setting up the analytics collector
    2. Tracking LLM turns with token usage
    3. Tracking tool calls
    4. Tracking tasks
    5. Async submission (non-blocking)
    """

    # ========================================================================
    # 1. Setup Analytics Collector
    # ========================================================================

    collector = create_analytics_collector(
        control_plane_url=os.getenv("CONTROL_PLANE_URL", "http://localhost:8000"),
        api_key=os.getenv("KUBIYA_API_KEY"),
    )

    # Create execution context
    ctx = ExecutionContext(
        execution_id="550e8400-e29b-41d4-a716-446655440000",  # From Temporal workflow
        organization_id="org-123",  # From execution record
        turn_number=0,
    )

    print("🚀 Starting agent execution with analytics tracking\n")

    # ========================================================================
    # 2. Track LLM Turn (Using LiteLLM)
    # ========================================================================

    print("📊 Turn 1: LLM Call with LiteLLM")
    ctx = collector.start_turn(ctx)

    # Simulate LiteLLM call
    turn_start = time.time()

    # In real code, you'd do:
    # response = await litellm.acompletion(
    #     model="claude-sonnet-4",
    #     messages=[{"role": "user", "content": "Hello"}],
    # )

    # For this example, create a mock response
    class MockUsage:
        prompt_tokens = 1000
        completion_tokens = 500
        total_tokens = 1500

    class MockMessage:
        content = "This is the LLM response with detailed information about the task."

    class MockChoice:
        message = MockMessage()
        finish_reason = "stop"

    class MockLiteLLMResponse:
        usage = MockUsage()
        choices = [MockChoice()]

    await asyncio.sleep(0.1)  # Simulate API call
    response = MockLiteLLMResponse()

    # Record the turn (async, non-blocking)
    collector.record_turn_from_litellm(
        ctx=ctx,
        response=response,
        model="claude-sonnet-4",
        finish_reason="stop",
    )

    print(f"  ✓ Turn recorded: {response.usage.total_tokens} tokens")
    print(f"  ✓ Duration: {int((time.time() - turn_start) * 1000)}ms\n")

    # ========================================================================
    # 3. Track Tool Calls
    # ========================================================================

    print("🔧 Turn 1: Tool Calls")

    # Tool call 1: Read file
    tool_start = time.time()
    await asyncio.sleep(0.05)  # Simulate tool execution
    tool_end = time.time()

    collector.record_tool_call(
        ctx=ctx,
        tool_name="Read",
        tool_input={"file_path": "/app/main.py"},
        tool_output="def main():\n    print('Hello')\n    ...",
        start_time=tool_start,
        end_time=tool_end,
        success=True,
    )

    print(f"  ✓ Tool call recorded: Read (successful)")

    # Tool call 2: Bash command
    tool_start = time.time()
    await asyncio.sleep(0.1)  # Simulate tool execution
    tool_end = time.time()

    collector.record_tool_call(
        ctx=ctx,
        tool_name="Bash",
        tool_input={"command": "ls -la"},
        tool_output="total 48\ndrwxr-xr-x  10 user  staff   320 Jan  8 14:00 .\n...",
        start_time=tool_start,
        end_time=tool_end,
        success=True,
    )

    print(f"  ✓ Tool call recorded: Bash (successful)\n")

    # ========================================================================
    # 4. Track LLM Turn (Using Agno)
    # ========================================================================

    print("📊 Turn 2: LLM Call with Agno")
    ctx = collector.start_turn(ctx)

    turn_start = time.time()

    # In real code, you'd do:
    # result = agent.run(message)

    # For this example, create a mock Agno result
    class MockMetrics:
        input_tokens = 800
        output_tokens = 600
        total_tokens = 1400
        input_token_details = {
            "cache_read": 200,
            "cache_creation": 100,
        }

    class MockAgnoResult:
        metrics = MockMetrics()
        content = "Based on the analysis, I recommend the following changes..."
        run_id = "run-456"

    await asyncio.sleep(0.15)  # Simulate API call
    result = MockAgnoResult()

    # Record the turn (async, non-blocking)
    collector.record_turn_from_agno(
        ctx=ctx,
        result=result,
        model="claude-sonnet-4",
        finish_reason="stop",
    )

    print(f"  ✓ Turn recorded: {result.metrics.total_tokens} tokens (with cache)")
    print(f"  ✓ Cache read: {result.metrics.input_token_details['cache_read']} tokens")
    print(f"  ✓ Duration: {int((time.time() - turn_start) * 1000)}ms\n")

    # ========================================================================
    # 5. Track Tasks
    # ========================================================================

    print("📋 Task Tracking")

    task_id = collector.record_task(
        ctx=ctx,
        task_number=1,
        task_description="Analyze codebase and identify issues",
        task_type="analysis",
        status="completed",
        started_at=datetime.now(timezone.utc).isoformat(),
    )

    print(f"  ✓ Task recorded: {task_id}\n")

    # ========================================================================
    # 6. Wait for Analytics Submission
    # ========================================================================

    print("⏳ Waiting for analytics submission...")

    # Wait for all analytics to be submitted (with timeout)
    await collector.wait_for_submissions(timeout=5.0)

    print("✅ All analytics submitted!\n")

    # ========================================================================
    # 7. Query Analytics
    # ========================================================================

    print("📈 Analytics Summary:")
    print(f"  - Total turns: 2")
    print(f"  - Total tokens: 2900")
    print(f"  - Total tool calls: 2")
    print(f"  - Total tasks: 1")
    print(f"  - Estimated cost: $0.0435")


async def execute_agent_with_error_handling_example():
    """
    Example showing error handling in analytics.

    Demonstrates that analytics failures don't break execution.
    """

    collector = create_analytics_collector(
        control_plane_url="http://localhost:8000",
        api_key="test-key",
    )

    ctx = ExecutionContext(
        execution_id="exec-123",
        organization_id="org-456",
    )

    print("\n🔥 Error Handling Example\n")

    # Start turn
    ctx = collector.start_turn(ctx)

    # Even if analytics submission fails, execution continues
    try:
        # Simulate a failed LLM call
        raise Exception("LLM API timeout")
    except Exception as e:
        print(f"❌ LLM call failed: {e}")

        # Record turn with error (still tracked for analytics)
        class MockErrorResponse:
            usage = None

        collector.record_turn_from_litellm(
            ctx=ctx,
            response=MockErrorResponse(),
            model="claude-sonnet-4",
            finish_reason="error",
            error_message=str(e),
        )

        print("  ✓ Error tracked in analytics (execution can continue)")

    # Tool call that fails
    tool_start = time.time()
    try:
        raise PermissionError("Access denied to file")
    except Exception as e:
        tool_end = time.time()

        collector.record_tool_call(
            ctx=ctx,
            tool_name="Read",
            tool_input={"file_path": "/restricted/file.txt"},
            tool_output=None,
            start_time=tool_start,
            end_time=tool_end,
            success=False,
            error_message=str(e),
            error_type=type(e).__name__,
        )

        print(f"  ✓ Tool failure tracked: {type(e).__name__}")

    print("\n✅ Execution continued despite errors (resilient)")


async def performance_test_example():
    """
    Example showing performance characteristics.

    Analytics should add minimal overhead (<5ms per submission).
    """

    collector = create_analytics_collector(
        control_plane_url="http://localhost:8000",
        api_key="test-key",
    )

    ctx = ExecutionContext(
        execution_id="perf-test",
        organization_id="org-perf",
    )

    print("\n⚡ Performance Test\n")

    # Test turn recording performance
    turn_count = 10
    start_time = time.time()

    for i in range(turn_count):
        ctx = collector.start_turn(ctx)

        class MockResponse:
            class Usage:
                prompt_tokens = 1000
                completion_tokens = 500
                total_tokens = 1500

            usage = Usage()

            class Choice:
                class Message:
                    content = "Response content"

                message = Message()
                finish_reason = "stop"

            choices = [Choice()]

        collector.record_turn_from_litellm(
            ctx=ctx,
            response=MockResponse(),
            model="claude-sonnet-4",
        )

    end_time = time.time()
    overhead_per_turn = ((end_time - start_time) / turn_count) * 1000

    print(f"  • Recorded {turn_count} turns")
    print(f"  • Overhead per turn: {overhead_per_turn:.2f}ms")
    print(f"  • Status: {'✓ Fast' if overhead_per_turn < 5 else '⚠️ Slow'}")

    # Wait for submissions
    await collector.wait_for_submissions()

    print("\n✅ Performance test complete")


if __name__ == "__main__":
    """Run all examples"""
    print("=" * 70)
    print("Analytics Integration Examples")
    print("=" * 70)

    # Run examples
    asyncio.run(execute_agent_with_analytics_example())
    asyncio.run(execute_agent_with_error_handling_example())
    asyncio.run(performance_test_example())

    print("\n" + "=" * 70)
    print("Examples complete! Check Control Plane for analytics data.")
    print("=" * 70)
