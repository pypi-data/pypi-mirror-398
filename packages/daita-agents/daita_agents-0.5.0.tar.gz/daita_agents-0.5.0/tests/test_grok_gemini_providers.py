"""
Basic provider tests for Grok (xAI) and Google Gemini.

These tests verify that both providers work with the framework after
handler removal. Note: Tool calling not yet implemented for these providers,
so we only test basic execution.

Tests:
- Basic execution (run/run_detailed)
- Workflows
- System integrations (webhooks, schedules)
"""
import pytest
import asyncio
import os
from daita.agents.substrate import SubstrateAgent
from daita.core.workflow import Workflow


class TestGrokProvider:
    """Test Grok (xAI) provider basic functionality."""

    @pytest.mark.asyncio
    async def test_grok_simple_run(self):
        """Test simple execution with Grok."""
        api_key = os.getenv("XAI_API_KEY") or os.getenv("GROK_API_KEY")
        if not api_key:
            pytest.skip("XAI_API_KEY or GROK_API_KEY not set")

        agent = SubstrateAgent(
            name="GrokAgent",
            model="grok-3",
            prompt="You are a helpful assistant. Answer questions concisely.",
            api_key=api_key,
            llm_provider="grok"
        )

        await agent.start()

        try:
            result = await agent.run("What is 2+2?")

            assert isinstance(result, str)
            assert len(result) > 0
            print(f"\nGrok response: {result}")

        finally:
            await agent.stop()

    @pytest.mark.asyncio
    async def test_grok_detailed_run(self):
        """Test detailed execution with Grok."""
        api_key = os.getenv("XAI_API_KEY") or os.getenv("GROK_API_KEY")
        if not api_key:
            pytest.skip("XAI_API_KEY or GROK_API_KEY not set")

        agent = SubstrateAgent(
            name="GrokDetailed",
            model="grok-3",
            prompt="You provide detailed responses.",
            api_key=api_key,
            llm_provider="grok"
        )

        await agent.start()

        try:
            result = await agent.run_detailed("Explain what Python is in one sentence.")

            assert isinstance(result, dict)
            assert "result" in result
            assert "processing_time_ms" in result
            assert "agent_id" in result

            print(f"\nGrok detailed response:")
            print(f"  Result: {result['result'][:200]}")
            print(f"  Time: {result.get('processing_time_ms', 0)}ms")

        finally:
            await agent.stop()

    @pytest.mark.asyncio
    async def test_grok_in_workflow(self):
        """Test Grok in a workflow context."""
        api_key = os.getenv("XAI_API_KEY") or os.getenv("GROK_API_KEY")
        if not api_key:
            pytest.skip("XAI_API_KEY or GROK_API_KEY not set")

        workflow = Workflow("Grok Workflow")

        agent1 = SubstrateAgent(
            name="GrokAgent1",
            model="grok-3",
            prompt="You are agent 1.",
            api_key=api_key,
            llm_provider="grok"
        )

        agent2_state = {"received": False}

        agent2 = SubstrateAgent(
            name="GrokAgent2",
            model="grok-3",
            prompt="You are agent 2.",
            api_key=api_key,
            llm_provider="grok"
        )

        original_receive = agent2.receive_message

        async def tracked_receive(data, source_agent, channel, workflow_name=None):
            agent2_state["received"] = True
            return await original_receive(data, source_agent, channel, workflow_name)

        agent2.receive_message = tracked_receive

        workflow.add_agent("agent1", agent1)
        workflow.add_agent("agent2", agent2)
        workflow.connect("agent1", "test_channel", "agent2")

        await workflow.start()

        try:
            await workflow.relay_manager.publish(
                "test_channel",
                {"message": "Hello from agent1"},
                publisher="GrokAgent1"
            )

            await asyncio.sleep(2)

            assert agent2_state["received"], "Agent2 did not receive message"
            print("\nGrok workflow test: Communication successful")

        finally:
            await workflow.stop()

    @pytest.mark.asyncio
    async def test_grok_webhook_handler(self):
        """Test Grok handling webhooks."""
        api_key = os.getenv("XAI_API_KEY") or os.getenv("GROK_API_KEY")
        if not api_key:
            pytest.skip("XAI_API_KEY or GROK_API_KEY not set")

        agent = SubstrateAgent(
            name="GrokWebhook",
            model="grok-3",
            prompt="You process webhook events.",
            api_key=api_key,
            llm_provider="grok"
        )

        await agent.start()

        try:
            webhook_payload = {
                "event": "user.signup",
                "user_id": "12345"
            }

            result = await agent.on_webhook(webhook_payload, {"slug": "user-events"})

            assert result is not None
            assert "result" in result
            print(f"\nGrok webhook test: {result['result'][:200]}")

        finally:
            await agent.stop()


class TestGeminiProvider:
    """Test Google Gemini provider basic functionality."""

    @pytest.mark.asyncio
    async def test_gemini_simple_run(self):
        """Test simple execution with Gemini."""
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            pytest.skip("GOOGLE_API_KEY or GEMINI_API_KEY not set")

        agent = SubstrateAgent(
            name="GeminiAgent",
            model="gemini-2.5-flash",
            prompt="You are a helpful assistant. Answer questions concisely.",
            api_key=api_key,
            llm_provider="gemini"
        )

        await agent.start()

        try:
            result = await agent.run("What is the capital of Japan?")

            assert isinstance(result, str)
            assert len(result) > 0
            print(f"\nGemini response: {result}")

        finally:
            await agent.stop()

    @pytest.mark.asyncio
    async def test_gemini_detailed_run(self):
        """Test detailed execution with Gemini."""
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            pytest.skip("GOOGLE_API_KEY or GEMINI_API_KEY not set")

        agent = SubstrateAgent(
            name="GeminiDetailed",
            model="gemini-2.5-flash",
            prompt="You provide detailed responses.",
            api_key=api_key,
            llm_provider="gemini"
        )

        await agent.start()

        try:
            result = await agent.run_detailed("What is machine learning?")

            assert isinstance(result, dict)
            assert "result" in result
            assert "processing_time_ms" in result
            assert "agent_id" in result

            print(f"\nGemini detailed response:")
            print(f"  Result: {result['result'][:200]}")
            print(f"  Time: {result.get('processing_time_ms', 0)}ms")

        finally:
            await agent.stop()

    @pytest.mark.asyncio
    async def test_gemini_in_workflow(self):
        """Test Gemini in a workflow context."""
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            pytest.skip("GOOGLE_API_KEY or GEMINI_API_KEY not set")

        workflow = Workflow("Gemini Workflow")

        agent1 = SubstrateAgent(
            name="GeminiAgent1",
            model="gemini-2.5-flash",
            prompt="You are agent 1.",
            api_key=api_key,
            llm_provider="gemini"
        )

        agent2_state = {"received": False}

        agent2 = SubstrateAgent(
            name="GeminiAgent2",
            model="gemini-2.5-flash",
            prompt="You are agent 2.",
            api_key=api_key,
            llm_provider="gemini"
        )

        original_receive = agent2.receive_message

        async def tracked_receive(data, source_agent, channel, workflow_name=None):
            agent2_state["received"] = True
            return await original_receive(data, source_agent, channel, workflow_name)

        agent2.receive_message = tracked_receive

        workflow.add_agent("agent1", agent1)
        workflow.add_agent("agent2", agent2)
        workflow.connect("agent1", "test_channel", "agent2")

        await workflow.start()

        try:
            await workflow.relay_manager.publish(
                "test_channel",
                {"message": "Hello from agent1"},
                publisher="GeminiAgent1"
            )

            await asyncio.sleep(2)

            assert agent2_state["received"], "Agent2 did not receive message"
            print("\nGemini workflow test: Communication successful")

        finally:
            await workflow.stop()

    @pytest.mark.asyncio
    async def test_gemini_scheduled_task(self):
        """Test Gemini running scheduled tasks."""
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            pytest.skip("GOOGLE_API_KEY or GEMINI_API_KEY not set")

        agent = SubstrateAgent(
            name="GeminiScheduler",
            model="gemini-2.5-flash",
            prompt="You run scheduled tasks.",
            api_key=api_key,
            llm_provider="gemini"
        )

        await agent.start()

        try:
            schedule_config = {
                "schedule": "0 9 * * *",
                "name": "daily-task",
                "task": "Generate daily summary"
            }

            result = await agent.on_schedule(schedule_config)

            assert result is not None
            assert "result" in result
            assert "schedule_metadata" in result

            print(f"\nGemini scheduled task: {result['result'][:200]}")

        finally:
            await agent.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
