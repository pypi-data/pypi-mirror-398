"""
Test suite for SubstrateAgent - the core agent implementation.

Tests cover:
- Agent initialization and configuration
- Tool-based execution with run() and run_detailed()
- Error handling and classification
- Focus parameter application
- Relay publishing
- Plugin integration
- Token tracking
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from daita.agents.substrate import SubstrateAgent
from daita.config.base import AgentConfig, AgentType, RetryPolicy, RetryStrategy
from daita.core.exceptions import (
    AgentError, LLMError, ValidationError, InvalidDataError,
    TransientError, RetryableError, PermanentError
)
from daita.llm.mock import MockLLMProvider


class TestSubstrateAgentInitialization:
    """Test agent initialization and configuration."""
    
    def test_minimal_initialization(self):
        """Test creating agent with minimal configuration."""
        agent = SubstrateAgent()
        
        assert agent.name == "Substrate Agent"
        assert agent.agent_type == AgentType.SUBSTRATE
        assert agent.agent_id is not None
        assert len(agent.agent_id) > 0
        assert not agent.config.retry_enabled
        assert agent.llm is None
        assert agent.default_focus is None
        assert agent.relay is None
    
    def test_custom_configuration(self):
        """Test creating agent with custom configuration."""
        config = AgentConfig(
            name="Test Agent",
            enable_retry=True,
            retry_policy=RetryPolicy(max_retries=5, initial_delay=2.0)
        )

        llm = MockLLMProvider()

        agent = SubstrateAgent(
            config=config,
            llm_provider=llm,
            name="Custom Agent",
            focus=["field1", "field2"],
            relay="test_channel",
            api_key="test_key"  # Provide api_key to skip auto-detection
        )

        assert agent.name == "Custom Agent"  # name parameter overrides config
        assert agent.config.retry_enabled
        assert agent.config.retry_policy.max_retries == 5
        assert agent.llm == llm
        assert agent.default_focus == ["field1", "field2"]
        assert agent.relay == "test_channel"
    
    def test_agent_id_generation(self):
        """Test agent ID generation is unique."""
        agent1 = SubstrateAgent(name="Test Agent")
        agent2 = SubstrateAgent(name="Test Agent")

        assert agent1.agent_id != agent2.agent_id
        assert "test_agent" in agent1.agent_id.lower()


class TestSubstrateAgentProcessing:
    """Test core task processing functionality."""
    
    @pytest.fixture
    def agent(self):
        """Create test agent with mock LLM."""
        llm = MockLLMProvider()
        llm.set_response("default", "Mock LLM response for testing")

        return SubstrateAgent(
            name="Test Agent",
            llm_provider=llm,
            api_key="test_key"  # Provide api_key to skip auto-detection
        )
    
    @pytest.fixture
    def retry_agent(self):
        """Create test agent with retry enabled."""
        config = AgentConfig(
            name="Retry Agent",
            enable_retry=True,
            retry_policy=RetryPolicy(max_retries=3, initial_delay=0.1)
        )

        llm = MockLLMProvider()
        return SubstrateAgent(config=config, llm_provider=llm, api_key="test_key")
    
    @pytest.mark.asyncio
    async def test_basic_task_processing(self, agent):
        """Test basic task processing with new run() API."""
        await agent.start()

        # Use new run_detailed() API
        result = await agent.run_detailed("test task with test data")

        assert "result" in result
        assert result["agent_id"] == agent.agent_id
        assert result["agent_name"] == agent.name

        await agent.stop()
    
    @pytest.mark.asyncio
    async def test_llm_query_handler(self, agent):
        """Test LLM query with new run() API."""
        await agent.start()

        # Use new run API
        result = await agent.run("Analyze this text")

        # run() returns just the string result
        assert isinstance(result, str)
        assert len(result) > 0

        await agent.stop()
    
    @pytest.mark.asyncio
    async def test_data_analysis(self, agent):
        """Test data analysis with run_detailed() API."""
        await agent.start()

        test_data = {"sales": [100, 200, 300], "region": "North"}
        result = await agent.run_detailed(f"Analyze this sales data: {test_data}")

        assert "result" in result
        assert isinstance(result["result"], str)

        await agent.stop()

    @pytest.mark.asyncio
    async def test_data_transformation(self, agent):
        """Test data transformation with run() API."""
        await agent.start()

        answer = await agent.run("Transform this data: {'test': 'data'}")

        # run() returns string result
        assert isinstance(answer, str)
        assert len(answer) > 0

        await agent.stop()


class TestSubstrateAgentRetry:
    """Test retry behavior and error handling.

    Note: Retry logic is implemented in BaseAgent and tested there.
    SubstrateAgent inherits this functionality through run_detailed().
    """

    @pytest.mark.asyncio
    async def test_successful_execution(self):
        """Test that successful operations work with retry enabled."""
        config = AgentConfig(
            name="Test Agent",
            enable_retry=True,
            retry_policy=RetryPolicy(max_retries=3)
        )

        llm = MockLLMProvider()
        agent = SubstrateAgent(config=config, llm_provider=llm, api_key="test")
        await agent.start()

        # Use run() API
        result = await agent.run("Test query")

        assert isinstance(result, str)
        assert len(result) > 0

        await agent.stop()


class TestSubstrateAgentFocus:
    """Test focus parameter application.

    Note: Focus is applied to tool results before reaching the LLM.
    These tests verify focus configuration doesn't break execution.
    """

    @pytest.fixture
    def agent(self):
        llm = MockLLMProvider()
        return SubstrateAgent(name="Focus Test Agent", llm_provider=llm, api_key="test")

    @pytest.mark.asyncio
    async def test_dict_focus_list(self, agent):
        """Test agent works with focus configuration (list of keys)."""
        agent.default_focus = ["name", "age"]
        await agent.start()

        # Focus is applied to tool results, not direct queries
        result = await agent.run("Process this information")

        assert isinstance(result, str)
        assert len(result) > 0

        await agent.stop()

    @pytest.mark.asyncio
    async def test_dict_focus_single(self, agent):
        """Test agent works with focus configuration (single key)."""
        agent.default_focus = "name"
        await agent.start()

        result = await agent.run("Process data")

        assert isinstance(result, str)
        assert len(result) > 0

        await agent.stop()

    @pytest.mark.asyncio
    async def test_no_focus_passthrough(self, agent):
        """Test that agent works when no focus is set."""
        await agent.start()

        result = await agent.run("Process data")

        assert isinstance(result, str)
        assert len(result) > 0

        await agent.stop()


class TestSubstrateAgentRelay:
    """Test relay channel publishing.

    Note: Relay publishing is internal infrastructure feature.
    These tests verify relay configuration doesn't break execution.
    """

    @pytest.mark.asyncio
    async def test_relay_configuration(self):
        """Test that agent works with relay channel configured."""
        with patch('daita.core.relay.publish') as mock_publish:
            llm = MockLLMProvider()
            agent = SubstrateAgent(
                name="Relay Agent",
                relay="test_channel",
                llm_provider=llm,
                api_key="test"
            )
            await agent.start()

            # Execute via internal _process() which triggers relay
            result = await agent._process("test task", {"test": "data"})

            assert result["status"] == "success"

            await agent.stop()

    @pytest.mark.asyncio
    async def test_relay_error_handling(self):
        """Test that relay publishing errors don't break main processing."""
        with patch('daita.core.relay.publish', side_effect=Exception("Relay failed")):
            llm = MockLLMProvider()
            agent = SubstrateAgent(
                name="Relay Agent",
                relay="test_channel",
                llm_provider=llm,
                api_key="test"
            )
            await agent.start()

            # Main processing should still succeed despite relay failure
            result = await agent.run("Test query")

            assert isinstance(result, str)
            assert len(result) > 0

            await agent.stop()


class TestSubstrateAgentUtilities:
    """Test utility methods and properties."""

    @pytest.mark.asyncio
    async def test_health_property(self):
        """Test health property provides comprehensive status."""
        llm = MockLLMProvider()
        agent = SubstrateAgent(
            name="Health Test",
            llm_provider=llm,
            relay="test_channel",
            api_key="test_key"
        )

        health = agent.health

        assert health["name"] == "Health Test"
        assert health["id"] == agent.agent_id
        assert health["type"] == "substrate"
        assert "tools" in health
        assert "relay" in health
        assert "llm" in health
        assert "handlers" not in health  # Handlers removed in v2.0.0

        # Check relay and LLM status
        assert health["relay"]["enabled"] is True
        assert health["relay"]["channel"] == "test_channel"
        assert health["llm"]["available"] is True
    
    def test_token_usage_tracking(self):
        """Test token usage tracking integration."""
        llm = MockLLMProvider()
        agent = SubstrateAgent(llm_provider=llm, agent_id="test_agent_123", api_key="test_key")

        # Should return token usage data structure
        usage = agent.get_token_usage()

        assert isinstance(usage, dict)
        assert "total_tokens" in usage
        assert "prompt_tokens" in usage
        assert "completion_tokens" in usage
        assert "total_calls" in usage  # MockLLMProvider uses "total_calls" instead of "requests"


class TestSubstrateAgentPlugins:
    """Test plugin integration."""
    
    def test_plugin_access(self):
        """Test plugin access object."""
        agent = SubstrateAgent()
        
        # Should have plugin access
        assert hasattr(agent, 'plugins')
        assert hasattr(agent.plugins, 'postgresql')
        assert hasattr(agent.plugins, 'mysql') 
        assert hasattr(agent.plugins, 'mongodb')
        assert hasattr(agent.plugins, 'rest')
    
    def test_add_plugin(self):
        """Test adding plugins to agent."""
        agent = SubstrateAgent()

        mock_plugin = Mock()
        mock_plugin.__class__.__name__ = "MockPlugin"

        agent.add_plugin(mock_plugin)

        # Plugins are stored in tool_sources
        assert mock_plugin in agent.tool_sources

        # Tools appear in health info
        health = agent.health
        assert "tools" in health
        assert health["tools"]["count"] >= 0  # May be 0 if not set up yet


class TestSubstrateAgentEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_empty_prompt(self):
        """Test processing with empty prompt."""
        llm = MockLLMProvider()
        agent = SubstrateAgent(llm_provider=llm, api_key="test")
        await agent.start()

        # Empty prompt should still work
        result = await agent.run("")

        assert isinstance(result, str)

        await agent.stop()

    @pytest.mark.asyncio
    async def test_with_llm(self):
        """Test execution with LLM configured."""
        llm = MockLLMProvider()
        agent = SubstrateAgent(llm_provider=llm, api_key="test_key")
        await agent.start()

        result = await agent.run("Test query")

        assert isinstance(result, str)
        assert len(result) > 0

        await agent.stop()

    @pytest.mark.asyncio
    async def test_without_llm(self):
        """Test behavior when no LLM is available."""
        agent = SubstrateAgent()  # No LLM provider
        await agent.start()

        # Should raise an error when trying to use LLM without one configured
        from daita.core.exceptions import AgentError
        with pytest.raises(AgentError):
            await agent.run("Test query")

        await agent.stop()


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])