"""
Test suite for SubstrateAgent WITHOUT MCP integration.

This test suite ensures that SubstrateAgent works correctly when MCP
functionality is NOT used, verifying that the agent works fine without
MCP tools.

Tests cover:
- Agent initialization without MCP
- run() and run_detailed() APIs work without MCP
- LLM queries work without MCP tools
- No MCP dependencies are loaded when not used
- System integration APIs work without MCP
"""
import pytest
import asyncio
from typing import Dict, Any
from unittest.mock import patch

from daita.agents.substrate import SubstrateAgent
from daita.config.base import AgentConfig, RetryPolicy
from daita.llm.mock import MockLLMProvider


class TestSubstrateAgentWithoutMCP:
    """Test that SubstrateAgent works perfectly without MCP."""

    def test_initialization_no_mcp(self):
        """Test agent initializes correctly without MCP parameter."""
        agent = SubstrateAgent(name="No MCP Agent")

        assert agent.name == "No MCP Agent"
        assert agent.mcp_registry is None
        assert agent.mcp_tools == []
        assert agent._mcp_server_configs == []
        # Agent should work fine without MCP
        assert agent.tool_registry is not None

    def test_initialization_with_llm_no_mcp(self):
        """Test agent with LLM but no MCP."""
        llm = MockLLMProvider()
        agent = SubstrateAgent(
            name="LLM Agent",
            llm_provider=llm,
            api_key="test_key"
        )

        assert agent.llm is not None
        assert agent.mcp_registry is None
        assert agent.mcp_tools == []

    def test_no_mcp_attributes_set(self):
        """Test MCP attributes are properly initialized even without MCP."""
        agent = SubstrateAgent()

        # These should exist but be empty/None
        assert hasattr(agent, 'mcp_registry')
        assert hasattr(agent, 'mcp_tools')
        assert hasattr(agent, '_mcp_server_configs')
        assert agent.mcp_registry is None
        assert isinstance(agent.mcp_tools, list)
        assert len(agent.mcp_tools) == 0


class TestExecutionWithoutMCP:
    """Test execution APIs work without MCP."""

    @pytest.fixture
    def agent_with_llm(self):
        """Create agent with LLM but no MCP."""
        llm = MockLLMProvider()
        llm.set_response("default", "Test response from LLM")
        return SubstrateAgent(
            name="Test Agent",
            llm_provider=llm,
            api_key="test_key"
        )

    @pytest.mark.asyncio
    async def test_run_with_llm_no_mcp(self, agent_with_llm):
        """Test run() works with LLM but without MCP."""
        await agent_with_llm.start()

        result = await agent_with_llm.run("Analyze this data")

        assert isinstance(result, str)
        assert len(result) > 0

        await agent_with_llm.stop()

    @pytest.mark.asyncio
    async def test_run_detailed_no_mcp(self, agent_with_llm):
        """Test run_detailed() works without MCP."""
        await agent_with_llm.start()

        result = await agent_with_llm.run_detailed("Process this request")

        assert "result" in result
        assert isinstance(result["result"], str)
        assert "agent_name" in result
        assert result["agent_name"] == "Test Agent"

        await agent_with_llm.stop()

    @pytest.mark.asyncio
    async def test_internal_process_no_mcp(self, agent_with_llm):
        """Test internal _process() API works without MCP."""
        await agent_with_llm.start()

        # Internal API used by workflows
        result = await agent_with_llm._process("test_task", {"data": "value"})

        assert result["status"] == "success"
        assert "result" in result

        await agent_with_llm.stop()


class TestMCPSetupSkipped:
    """Test that MCP is not configured when not provided."""

    @pytest.mark.asyncio
    async def test_mcp_not_configured_without_param(self):
        """Test that MCP registry is None when not configured."""
        agent = SubstrateAgent(name="Test Agent")

        await agent.start()

        # MCP should not be configured
        assert agent.mcp_registry is None
        assert agent.mcp_tools == []

        await agent.stop()

    @pytest.mark.asyncio
    async def test_mcp_setup_skipped_with_llm(self):
        """Test MCP setup skipped even with LLM configured."""
        llm = MockLLMProvider()
        agent = SubstrateAgent(
            name="LLM Agent",
            llm_provider=llm,
            api_key="test"
        )

        await agent.start()

        result = await agent.run("Test query")

        assert isinstance(result, str)
        # MCP was never setup
        assert agent.mcp_registry is None

        await agent.stop()


class TestRetryWithoutMCP:
    """Test retry logic works without MCP."""

    @pytest.mark.asyncio
    async def test_retry_success_no_mcp(self):
        """Test that retry works without MCP configured."""
        config = AgentConfig(
            name="Retry Agent",
            enable_retry=True,
            retry_policy=RetryPolicy(max_retries=2, initial_delay=0.01)
        )

        llm = MockLLMProvider()
        agent = SubstrateAgent(config=config, llm_provider=llm, api_key="test")

        await agent.start()

        result = await agent.run("Test with retry enabled")

        assert isinstance(result, str)

        await agent.stop()


class TestFocusWithoutMCP:
    """Test focus system works without MCP."""

    @pytest.mark.asyncio
    async def test_focus_application_no_mcp(self):
        """Test focus configuration works without MCP."""
        llm = MockLLMProvider()
        agent = SubstrateAgent(
            name="Focus Agent",
            llm_provider=llm,
            focus=["field1", "field2"],
            api_key="test"
        )

        await agent.start()

        result = await agent.run("Process data")

        assert isinstance(result, str)
        assert agent.default_focus == ["field1", "field2"]

        await agent.stop()


class TestRelayWithoutMCP:
    """Test relay publishing works without MCP."""

    @pytest.mark.asyncio
    async def test_relay_publishing_no_mcp(self):
        """Test relay works without MCP configured."""
        with patch('daita.core.relay.publish') as mock_publish:
            llm = MockLLMProvider()
            agent = SubstrateAgent(
                name="Relay Agent",
                relay="test_channel",
                llm_provider=llm,
                api_key="test"
            )

            await agent.start()

            # Use internal _process() which triggers relay
            await agent._process("task", {"data": "value"})

            await agent.stop()


class TestHealthWithoutMCP:
    """Test health reporting without MCP."""

    def test_health_no_mcp(self):
        """Test health property works without MCP."""
        agent = SubstrateAgent(name="Health Test")

        health = agent.health

        assert health["name"] == "Health Test"
        assert "tools" in health
        assert "relay" in health
        assert "llm" in health
        assert health["llm"]["available"] is False


class TestSystemIntegrationWithoutMCP:
    """Test system integration APIs work without MCP."""

    @pytest.mark.asyncio
    async def test_receive_message_no_mcp(self):
        """Test receive_message() works without MCP."""
        llm = MockLLMProvider()
        agent = SubstrateAgent(
            name="Workflow Agent",
            llm_provider=llm,
            api_key="test"
        )

        await agent.start()

        result = await agent.receive_message(
            data={"test": "data"},
            source_agent="source",
            channel="test_channel"
        )

        assert "result" in result
        assert isinstance(result["result"], str)

        await agent.stop()

    @pytest.mark.asyncio
    async def test_on_webhook_no_mcp(self):
        """Test on_webhook() works without MCP."""
        llm = MockLLMProvider()
        agent = SubstrateAgent(
            name="Webhook Agent",
            llm_provider=llm,
            api_key="test"
        )

        await agent.start()

        result = await agent.on_webhook(
            payload={"event": "test"},
            webhook_config={"instructions": "Process webhook"}
        )

        assert "result" in result
        assert "webhook_metadata" in result

        await agent.stop()

    @pytest.mark.asyncio
    async def test_on_schedule_no_mcp(self):
        """Test on_schedule() works without MCP."""
        llm = MockLLMProvider()
        agent = SubstrateAgent(
            name="Schedule Agent",
            llm_provider=llm,
            api_key="test"
        )

        await agent.start()

        result = await agent.on_schedule(
            schedule_config={"task": "Daily task"}
        )

        assert "result" in result
        assert "schedule_metadata" in result

        await agent.stop()


class TestErrorHandlingWithoutMCP:
    """Test error handling works without MCP."""

    @pytest.mark.asyncio
    async def test_no_llm_error(self):
        """Test proper error when no LLM configured."""
        agent = SubstrateAgent(name="No LLM")

        await agent.start()

        from daita.core.exceptions import AgentError
        with pytest.raises(AgentError):
            await agent.run("This should fail - no LLM")

        await agent.stop()


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
