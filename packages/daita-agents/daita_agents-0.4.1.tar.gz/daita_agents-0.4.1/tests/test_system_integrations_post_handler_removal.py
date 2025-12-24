"""
Test critical system integrations after handler removal.

Validates that all system entry points work correctly with the new
tool-based architecture:

1. Webhooks → on_webhook()
2. Scheduled tasks → on_schedule()
3. Lambda execution paths
4. Direct agent execution (run/run_detailed)

These tests ensure production systems still work after removing handlers.
"""
import pytest
import asyncio
import os
from typing import Dict, Any

from daita.agents.substrate import SubstrateAgent
from daita.llm.mock import MockLLMProvider
from daita.core.tools import tool


class TestWebhookIntegration:
    """Test webhook → agent integration via on_webhook()."""

    @pytest.mark.asyncio
    async def test_on_webhook_basic_execution(self):
        """Test that on_webhook() executes agent with webhook payload."""
        agent = SubstrateAgent(
            name="WebhookHandler",
            model="gpt-4o-mini",
            prompt="You process webhook payloads. Summarize what you received.",
            llm_provider=MockLLMProvider()
        )

        await agent.start()

        try:
            # Simulate webhook call
            webhook_payload = {
                "event": "user.signup",
                "user_id": "12345",
                "email": "test@example.com",
                "timestamp": "2024-01-15T10:30:00Z"
            }

            webhook_config = {
                "slug": "user-events",
                "field_mapping": {}
            }

            result = await agent.on_webhook(webhook_payload, webhook_config)

            # Verify result structure
            assert result is not None
            assert "result" in result
            assert "webhook_metadata" in result
            assert result["webhook_metadata"]["entry_point"] == "on_webhook"

            print(f"\nWebhook result: {result['result'][:200]}")

        finally:
            await agent.stop()

    @pytest.mark.asyncio
    async def test_on_webhook_with_tools(self):
        """Test webhook handler with registered tools."""
        agent = SubstrateAgent(
            name="WebhookWithTools",
            model="gpt-4o-mini",
            prompt="You process webhook events and store them.",
            llm_provider=MockLLMProvider()
        )

        # Track tool calls
        tool_calls = []

        @tool
        async def store_event(event_type: str, user_id: str) -> dict:
            """Store an event in the database."""
            tool_calls.append({"event_type": event_type, "user_id": user_id})
            return {"stored": True, "event_id": "evt_123"}

        agent.register_tool(store_event)
        await agent.start()

        try:
            webhook_payload = {
                "event": "purchase.completed",
                "user_id": "67890",
                "amount": 99.99
            }

            result = await agent.on_webhook(webhook_payload, {"slug": "payments"})

            assert result is not None
            assert "result" in result
            print(f"\nWebhook with tools result: {result['result'][:200]}")

        finally:
            await agent.stop()

    @pytest.mark.asyncio
    async def test_on_webhook_with_field_mapping(self):
        """Test webhook with field mapping (data transformation)."""
        agent = SubstrateAgent(
            name="MappedWebhook",
            model="gpt-4o-mini",
            prompt="Process the mapped webhook data.",
            llm_provider=MockLLMProvider()
        )

        await agent.start()

        try:
            # Original webhook payload
            webhook_payload = {
                "repository": {
                    "name": "my-repo",
                    "owner": "john"
                },
                "commits": [
                    {"message": "Fix bug", "author": "jane"}
                ]
            }

            # Field mapping extracts specific fields
            webhook_config = {
                "slug": "github-push",
                "field_mapping": {
                    "repository.name": "repo_name",
                    "commits[0].message": "commit_msg"
                }
            }

            result = await agent.on_webhook(webhook_payload, webhook_config)

            assert result is not None
            assert "result" in result
            print(f"\nMapped webhook result: {result}")

        finally:
            await agent.stop()


class TestScheduledTaskIntegration:
    """Test scheduled task → agent integration via on_schedule()."""

    @pytest.mark.asyncio
    async def test_on_schedule_basic_execution(self):
        """Test that on_schedule() executes agent on schedule."""
        agent = SubstrateAgent(
            name="ScheduledTask",
            model="gpt-4o-mini",
            prompt="You run daily reports. Generate a summary.",
            llm_provider=MockLLMProvider()
        )

        await agent.start()

        try:
            schedule_config = {
                "schedule": "0 9 * * *",  # Daily at 9am
                "name": "daily-report",
                "enabled": True
            }

            result = await agent.on_schedule(schedule_config)

            # Verify result structure
            assert result is not None
            assert "result" in result
            assert "schedule_metadata" in result
            assert result["schedule_metadata"]["entry_point"] == "on_schedule"

            print(f"\nScheduled task result: {result['result'][:200]}")

        finally:
            await agent.stop()

    @pytest.mark.asyncio
    async def test_on_schedule_with_tools(self):
        """Test scheduled task with tools for data fetching."""
        agent = SubstrateAgent(
            name="ScheduledWithTools",
            model="gpt-4o-mini",
            prompt="You generate daily reports from database data.",
            llm_provider=MockLLMProvider()
        )

        # Track tool usage
        tool_calls = []

        @tool
        async def fetch_daily_metrics() -> dict:
            """Fetch metrics for the daily report."""
            tool_calls.append("fetch_daily_metrics")
            return {
                "users": 1500,
                "revenue": 12500.50,
                "orders": 450
            }

        agent.register_tool(fetch_daily_metrics)
        await agent.start()

        try:
            schedule_config = {
                "schedule": "0 0 * * *",
                "name": "nightly-metrics"
            }

            result = await agent.on_schedule(schedule_config)

            assert result is not None
            assert "result" in result
            print(f"\nScheduled task with tools: {result['result'][:200]}")

        finally:
            await agent.stop()

    @pytest.mark.asyncio
    async def test_on_schedule_error_handling(self):
        """Test that schedule errors are handled gracefully."""
        agent = SubstrateAgent(
            name="ScheduledWithError",
            model="gpt-4o-mini",
            prompt="You process schedules.",
            llm_provider=MockLLMProvider()
        )

        @tool
        async def failing_task() -> dict:
            """A task that fails."""
            raise ValueError("Scheduled task failed!")

        agent.register_tool(failing_task)
        await agent.start()

        try:
            schedule_config = {
                "schedule": "* * * * *",
                "name": "failing-schedule"
            }

            # Should handle error gracefully
            result = await agent.on_schedule(schedule_config)

            # Result should still be returned even with internal errors
            assert result is not None

        finally:
            await agent.stop()


class TestDirectAgentExecution:
    """Test direct agent execution paths (run/run_detailed)."""

    @pytest.mark.asyncio
    async def test_run_simple_execution(self):
        """Test simple run() execution."""
        agent = SubstrateAgent(
            name="SimpleAgent",
            model="gpt-4o-mini",
            prompt="You answer questions briefly.",
            llm_provider=MockLLMProvider()
        )

        await agent.start()

        try:
            # Simple run - returns just the string result
            result = await agent.run("What is 2+2?")

            assert isinstance(result, str)
            assert len(result) > 0
            print(f"\nSimple run() result: {result[:200]}")

        finally:
            await agent.stop()

    @pytest.mark.asyncio
    async def test_run_detailed_execution(self):
        """Test run_detailed() execution with full metadata."""
        agent = SubstrateAgent(
            name="DetailedAgent",
            model="gpt-4o-mini",
            prompt="You provide detailed answers.",
            llm_provider=MockLLMProvider()
        )

        await agent.start()

        try:
            # Detailed run - returns full result dict
            result = await agent.run_detailed("Explain photosynthesis briefly.")

            assert isinstance(result, dict)
            assert "result" in result
            assert "processing_time_ms" in result
            assert "agent_id" in result
            assert "agent_name" in result
            assert result["agent_name"] == "DetailedAgent"

            print(f"\nDetailed run() result keys: {list(result.keys())}")
            print(f"Result: {result['result'][:200]}")
            print(f"Time: {result['processing_time_ms']}ms")

        finally:
            await agent.stop()

    @pytest.mark.asyncio
    async def test_run_detailed_with_tools(self):
        """Test run_detailed with tool usage tracking."""
        agent = SubstrateAgent(
            name="ToolAgent",
            model="gpt-4o-mini",
            prompt="You use tools to answer questions.",
            llm_provider=MockLLMProvider()
        )

        @tool
        async def get_weather(city: str) -> dict:
            """Get weather for a city."""
            return {"city": city, "temp": 72, "condition": "sunny"}

        agent.register_tool(get_weather)
        await agent.start()

        try:
            result = await agent.run_detailed("What's the weather in Seattle?")

            assert isinstance(result, dict)
            assert "result" in result
            assert "tool_calls" in result
            assert "iterations" in result

            print(f"\nTool-based execution:")
            print(f"Result: {result['result'][:200]}")
            print(f"Tool calls: {result['tool_calls']}")
            print(f"Iterations: {result['iterations']}")

        finally:
            await agent.stop()

    @pytest.mark.asyncio
    async def test_run_with_multiple_iterations(self):
        """Test agent with multiple tool calling iterations."""
        agent = SubstrateAgent(
            name="MultiStepAgent",
            model="gpt-4o-mini",
            prompt="You solve problems step by step using tools.",
            llm_provider=MockLLMProvider()
        )

        @tool
        async def calculate(expression: str) -> float:
            """Calculate a mathematical expression."""
            return eval(expression)  # Safe in test environment

        @tool
        async def format_result(value: float) -> str:
            """Format a number as currency."""
            return f"${value:,.2f}"

        agent.register_tool(calculate)
        agent.register_tool(format_result)
        await agent.start()

        try:
            result = await agent.run_detailed(
                "Calculate 1000 * 1.05 and format as currency"
            )

            assert isinstance(result, dict)
            assert "iterations" in result
            print(f"\nMulti-step execution: {result['iterations']} iterations")

        finally:
            await agent.stop()


class TestLegacyFallback:
    """Test _process() fallback for legacy compatibility."""

    @pytest.mark.asyncio
    async def test_process_fallback_still_works(self):
        """Test that _process() still works as internal API."""
        agent = SubstrateAgent(
            name="LegacyAgent",
            model="gpt-4o-mini",
            prompt="You process tasks.",
            llm_provider=MockLLMProvider()
        )

        await agent.start()

        try:
            # _process() is internal but should still work
            result = await agent._process(
                task="analyze",
                data={"values": [1, 2, 3, 4, 5]},
                context={"source": "test"}
            )

            assert isinstance(result, dict)
            assert "result" in result
            assert "task" in result
            assert result["task"] == "analyze"
            assert result["status"] == "success"

            print(f"\nLegacy _process() result: {result['result'][:200]}")

        finally:
            await agent.stop()


class TestEndToEndIntegration:
    """Test complete end-to-end scenarios."""

    @pytest.mark.asyncio
    async def test_webhook_to_scheduled_task_flow(self):
        """Test a realistic flow: webhook triggers data collection, schedule generates report."""
        # Webhook handler agent
        webhook_agent = SubstrateAgent(
            name="WebhookCollector",
            model="gpt-4o-mini",
            prompt="You collect and validate webhook data.",
            llm_provider=MockLLMProvider()
        )

        # Scheduled report agent
        report_agent = SubstrateAgent(
            name="ReportGenerator",
            model="gpt-4o-mini",
            prompt="You generate reports from collected data.",
            llm_provider=MockLLMProvider()
        )

        await webhook_agent.start()
        await report_agent.start()

        try:
            # Step 1: Process webhook
            webhook_result = await webhook_agent.on_webhook(
                {"event": "sale", "amount": 150.00},
                {"slug": "sales-tracker"}
            )

            assert webhook_result is not None
            print(f"\nWebhook processed: {webhook_result['result'][:100]}")

            # Step 2: Generate scheduled report
            report_result = await report_agent.on_schedule(
                {"schedule": "0 0 * * *", "name": "daily-sales"}
            )

            assert report_result is not None
            print(f"Report generated: {report_result['result'][:100]}")

        finally:
            await webhook_agent.stop()
            await report_agent.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
