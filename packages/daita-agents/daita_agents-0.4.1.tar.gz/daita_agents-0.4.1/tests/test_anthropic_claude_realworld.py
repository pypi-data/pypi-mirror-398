"""
Real-world tests using Anthropic's Claude (our own LLM!).

This is a CRITICAL test suite - validates that DAITA works with Anthropic's
own LLM provider. Tests:
- Basic agent execution with Claude
- Tool calling with Claude
- Workflow integration with Claude
- All system entry points (webhooks, schedules, workflows)

Uses Claude Sonnet (fast, cost-effective for testing).
"""
import pytest
import asyncio
import os
from typing import Dict, Any

from daita.agents.substrate import SubstrateAgent
from daita.core.tools import tool
from daita.core.workflow import Workflow


# Sample data
SAMPLE_CUSTOMER_DATA = [
    {"id": "C001", "name": "Acme Corp", "revenue": 125000, "status": "active"},
    {"id": "C002", "name": "TechStart Inc", "revenue": 85000, "status": "active"},
    {"id": "C003", "name": "Global Industries", "revenue": 250000, "status": "active"},
]


class TestAnthropicBasicExecution:
    """Test basic Claude execution."""

    @pytest.mark.asyncio
    async def test_claude_simple_run(self):
        """Test simple execution with Claude."""
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set")

        agent = SubstrateAgent(
            name="ClaudeAgent",
            model="claude-3-opus-20240229",
            prompt="You are a helpful assistant. Answer questions concisely.",
            api_key=api_key,
            llm_provider="anthropic"
        )

        await agent.start()

        try:
            # Simple run
            result = await agent.run("What is the capital of France?")

            assert isinstance(result, str)
            assert len(result) > 0
            assert "Paris" in result or "paris" in result.lower()

            print(f"\nClaude simple response: {result}")

        finally:
            await agent.stop()

    @pytest.mark.asyncio
    async def test_claude_detailed_run(self):
        """Test detailed execution with full metadata."""
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set")

        agent = SubstrateAgent(
            name="ClaudeDetailed",
            model="claude-3-opus-20240229",
            prompt="You provide detailed, thoughtful responses.",
            api_key=api_key,
            llm_provider="anthropic"
        )

        await agent.start()

        try:
            result = await agent.run_detailed("Explain what an API is in one sentence.")

            assert isinstance(result, dict)
            assert "result" in result
            assert "processing_time_ms" in result
            assert "agent_id" in result
            assert "tokens" in result or "cost" in result

            print(f"\nClaude detailed response:")
            print(f"  Result: {result['result'][:200]}")
            print(f"  Time: {result.get('processing_time_ms', 0)}ms")
            print(f"  Tokens: {result.get('tokens', {})}")

        finally:
            await agent.stop()


class TestAnthropicToolCalling:
    """Test Claude's tool calling capabilities."""

    @pytest.mark.asyncio
    async def test_claude_with_single_tool(self):
        """Test Claude calling a single tool."""
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set")

        agent = SubstrateAgent(
            name="ClaudeWithTool",
            model="claude-3-opus-20240229",
            prompt="You help users with calculations. Use the calculator tool when needed.",
            api_key=api_key,
            llm_provider="anthropic"
        )

        @tool
        async def calculate(expression: str) -> float:
            """Calculate a mathematical expression."""
            return eval(expression)

        agent.register_tool(calculate)
        await agent.start()

        try:
            result = await agent.run_detailed("What is 127 * 89?")

            assert isinstance(result, dict)
            assert "result" in result
            assert "tool_calls" in result

            print(f"\nClaude tool calling:")
            print(f"  Result: {result['result']}")
            print(f"  Tool calls: {result['tool_calls']}")
            print(f"  Iterations: {result.get('iterations', 1)}")

        finally:
            await agent.stop()

    @pytest.mark.asyncio
    async def test_claude_with_multiple_tools(self):
        """Test Claude using multiple tools."""
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set")

        agent = SubstrateAgent(
            name="ClaudeMultiTool",
            model="claude-3-opus-20240229",
            prompt="You are a customer service assistant. Use tools to help customers.",
            api_key=api_key,
            llm_provider="anthropic"
        )

        @tool
        async def get_customer_data(customer_id: str) -> dict:
            """Get customer information from database."""
            for customer in SAMPLE_CUSTOMER_DATA:
                if customer["id"] == customer_id:
                    return customer
            return {"error": "Customer not found"}

        @tool
        async def calculate_discount(revenue: float, discount_percent: float) -> float:
            """Calculate discount amount."""
            return revenue * (discount_percent / 100)

        agent.register_tool(get_customer_data)
        agent.register_tool(calculate_discount)
        await agent.start()

        try:
            result = await agent.run_detailed(
                "Get customer C001's data and calculate a 10% discount on their revenue"
            )

            assert isinstance(result, dict)
            assert "result" in result
            assert "tool_calls" in result

            print(f"\nClaude multi-tool response:")
            print(f"  Result: {result['result'][:300]}")
            print(f"  Tool calls: {result['tool_calls']}")

        finally:
            await agent.stop()


class TestAnthropicWorkflows:
    """Test Claude in workflow scenarios."""

    @pytest.mark.asyncio
    async def test_claude_two_agent_workflow(self):
        """Test workflow with two Claude agents communicating."""
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set")

        workflow = Workflow("Claude Workflow")

        # Agent 1: Data analyzer
        analyzer = SubstrateAgent(
            name="ClaudeAnalyzer",
            model="claude-3-opus-20240229",
            prompt="You analyze customer data and find insights.",
            api_key=api_key,
            llm_provider="anthropic"
        )

        # Agent 2: Report generator
        reporter_state = {"received": False, "data": None}

        reporter = SubstrateAgent(
            name="ClaudeReporter",
            model="claude-3-opus-20240229",
            prompt="You generate executive summaries from analysis.",
            api_key=api_key,
            llm_provider="anthropic"
        )

        # Track what reporter receives
        original_receive = reporter.receive_message

        async def custom_receive(data, source_agent, channel, workflow_name=None):
            reporter_state["received"] = True
            reporter_state["data"] = data
            return await original_receive(data, source_agent, channel, workflow_name)

        reporter.receive_message = custom_receive

        # Build workflow
        workflow.add_agent("analyzer", analyzer)
        workflow.add_agent("reporter", reporter)
        workflow.connect("analyzer", "analysis_results", "reporter")

        await workflow.start()

        try:
            # Publish data through workflow
            await workflow.relay_manager.publish(
                "analysis_results",
                SAMPLE_CUSTOMER_DATA,
                publisher="ClaudeAnalyzer"
            )

            await asyncio.sleep(2)

            # Verify communication
            assert reporter_state["received"], "Reporter did not receive data"
            assert reporter_state["data"] is not None

            print(f"\nClaude workflow: Reporter received data successfully")

        finally:
            await workflow.stop()


class TestAnthropicSystemIntegrations:
    """Test Claude with all system entry points."""

    @pytest.mark.asyncio
    async def test_claude_webhook_handler(self):
        """Test Claude handling webhooks."""
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set")

        agent = SubstrateAgent(
            name="ClaudeWebhookHandler",
            model="claude-3-opus-20240229",
            prompt="You process webhook events and summarize them.",
            api_key=api_key,
            llm_provider="anthropic"
        )

        await agent.start()

        try:
            webhook_payload = {
                "event": "order.created",
                "order_id": "ORD-12345",
                "customer": "Acme Corp",
                "amount": 5000
            }

            webhook_config = {
                "slug": "order-events",
                "field_mapping": {}
            }

            result = await agent.on_webhook(webhook_payload, webhook_config)

            assert result is not None
            assert "result" in result
            assert "webhook_metadata" in result

            print(f"\nClaude webhook handling: {result['result'][:200]}")

        finally:
            await agent.stop()

    @pytest.mark.asyncio
    async def test_claude_scheduled_task(self):
        """Test Claude running scheduled tasks."""
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set")

        agent = SubstrateAgent(
            name="ClaudeScheduler",
            model="claude-3-opus-20240229",
            prompt="You run daily summary tasks.",
            api_key=api_key,
            llm_provider="anthropic"
        )

        @tool
        async def get_daily_stats() -> dict:
            """Get daily statistics."""
            return {
                "orders": 125,
                "revenue": 15000,
                "new_customers": 8
            }

        agent.register_tool(get_daily_stats)
        await agent.start()

        try:
            schedule_config = {
                "schedule": "0 9 * * *",
                "name": "daily-summary",
                "task": "Generate daily summary report"
            }

            result = await agent.on_schedule(schedule_config)

            assert result is not None
            assert "result" in result
            assert "schedule_metadata" in result

            print(f"\nClaude scheduled task: {result['result'][:200]}")

        finally:
            await agent.stop()


class TestAnthropicTokenTracking:
    """Test token usage tracking with Claude."""

    @pytest.mark.asyncio
    async def test_claude_token_tracking(self):
        """Test that Claude usage is properly tracked."""
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set")

        agent = SubstrateAgent(
            name="ClaudeTokenTest",
            model="claude-3-opus-20240229",
            prompt="You respond to queries.",
            api_key=api_key,
            llm_provider="anthropic"
        )

        await agent.start()

        try:
            # Run multiple queries
            await agent.run("Hello")
            await agent.run("How are you?")
            result = await agent.run_detailed("Tell me about Python")

            # Check token tracking
            assert "tokens" in result or "cost" in result

            # Get agent's token usage
            usage = agent.get_token_usage()

            if usage:
                print(f"\nClaude token usage:")
                print(f"  Total tokens: {usage.get('total_tokens', 'N/A')}")
                print(f"  Total calls: {usage.get('total_calls', 'N/A')}")

                assert usage.get("total_tokens", 0) > 0, "No tokens tracked"
                assert usage.get("total_calls", 0) >= 3, "Not all calls tracked"

        finally:
            await agent.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
