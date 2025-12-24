"""
Integration tests for SubstrateAgent with Plugin Tools.

Tests that SubstrateAgent correctly integrates with the tool system
and can discover, register, and execute plugin tools.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from daita.agents.substrate import SubstrateAgent
from daita.plugins.postgresql import postgresql
from daita.plugins.s3 import s3
from daita.core.tools import AgentTool


class TestSubstrateAgentToolIntegration:
    """Test SubstrateAgent tool integration"""

    def test_agent_has_tool_registry(self):
        """Test that SubstrateAgent has a tool registry"""
        agent = SubstrateAgent(
            name="test_agent",
            tools=[]
        )

        assert hasattr(agent, 'tool_registry')
        assert hasattr(agent, 'tool_sources')
        assert agent.tool_registry.tool_count == 0

    def test_agent_accepts_tools_parameter(self):
        """Test that agent accepts tools parameter"""
        db = postgresql(
            host="localhost",
            database="test",
            user="test",
            password="test"
        )

        agent = SubstrateAgent(
            name="test_agent",
            tools=[db]
        )

        assert len(agent.tool_sources) == 1
        assert agent.tool_sources[0] == db

    @pytest.mark.asyncio
    async def test_agent_discovers_plugin_tools(self):
        """Test that agent discovers tools from plugins"""
        db = postgresql(
            host="localhost",
            database="test",
            user="test",
            password="test"
        )

        agent = SubstrateAgent(
            name="test_agent",
            tools=[db]
        )

        # Trigger tool setup
        await agent._setup_tools()

        assert agent.tool_registry.tool_count == 4
        tool_names = agent.tool_registry.tool_names

        assert "query_database" in tool_names
        assert "list_tables" in tool_names
        assert "get_table_schema" in tool_names
        assert "execute_sql" in tool_names

    @pytest.mark.asyncio
    async def test_agent_discovers_multiple_plugin_tools(self):
        """Test that agent discovers tools from multiple plugins"""
        db = postgresql(
            host="localhost",
            database="test",
            user="test",
            password="test"
        )

        storage = s3(bucket="test-bucket")

        agent = SubstrateAgent(
            name="test_agent",
            tools=[db, storage]
        )

        await agent._setup_tools()

        # Should have 4 postgres tools + 4 s3 tools = 8 total
        assert agent.tool_registry.tool_count == 8

        tool_names = agent.tool_registry.tool_names
        assert "query_database" in tool_names
        assert "read_s3_file" in tool_names
        assert "write_s3_file" in tool_names

    @pytest.mark.asyncio
    async def test_agent_can_execute_tool_manually(self):
        """Test that agent can manually execute a tool"""
        db = postgresql(
            host="localhost",
            database="test",
            user="test",
            password="test"
        )

        # Mock the query method
        db.query = AsyncMock(return_value=[
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"}
        ])

        agent = SubstrateAgent(
            name="test_agent",
            tools=[db]
        )

        # Execute tool manually
        result = await agent.call_tool("query_database", {
            "sql": "SELECT * FROM users"
        })

        assert result["success"] == True
        assert len(result["rows"]) == 2
        assert result["row_count"] == 2

    @pytest.mark.asyncio
    async def test_agent_call_tool_triggers_setup(self):
        """Test that calling a tool triggers setup if not already done"""
        db = postgresql(
            host="localhost",
            database="test",
            user="test",
            password="test"
        )

        db.tables = AsyncMock(return_value=["users", "orders"])

        agent = SubstrateAgent(
            name="test_agent",
            tools=[db]
        )

        # Tools not setup yet
        assert agent._tools_setup == False

        # Call tool - should trigger setup
        result = await agent.call_tool("list_tables", {})

        # Now setup
        assert agent._tools_setup == True
        assert result["success"] == True

    @pytest.mark.asyncio
    async def test_agent_process_triggers_tool_setup(self):
        """Test that agent.process() triggers tool setup"""
        db = postgresql(
            host="localhost",
            database="test",
            user="test",
            password="test"
        )

        from daita.llm.mock import MockLLMProvider
        mock_llm = MockLLMProvider()

        agent = SubstrateAgent(
            name="test_agent",
            tools=[db],
            llm_provider=mock_llm,
            api_key="test"
        )

        # Tools not setup
        assert agent._tools_setup == False

        # Internal _process() should trigger tool setup
        await agent._process("test_task", data={})

        # Should be setup now
        assert agent._tools_setup == True

    def test_agent_register_tool_method(self):
        """Test agent.register_tool() method"""
        agent = SubstrateAgent(name="test_agent", tools=[])

        async def custom_handler(args): return {"result": "custom"}

        custom_tool = AgentTool(
            name="custom_tool",
            description="Custom tool",
            parameters={},
            handler=custom_handler
        )

        agent.register_tool(custom_tool)

        assert agent.tool_registry.tool_count == 1
        assert "custom_tool" in agent.tool_registry.tool_names

    def test_agent_register_tools_method(self):
        """Test agent.register_tools() method for multiple tools"""
        agent = SubstrateAgent(name="test_agent", tools=[])

        async def handler1(args): return {}
        async def handler2(args): return {}

        tools = [
            AgentTool(name="tool1", description="Tool 1", parameters={}, handler=handler1),
            AgentTool(name="tool2", description="Tool 2", parameters={}, handler=handler2)
        ]

        agent.register_tools(tools)

        assert agent.tool_registry.tool_count == 2

    def test_agent_available_tools_property(self):
        """Test agent.available_tools property"""
        db = postgresql(
            host="localhost",
            database="test",
            user="test",
            password="test"
        )

        agent = SubstrateAgent(
            name="test_agent",
            tools=[db]
        )

        # Returns copy of tools list
        tools = agent.available_tools
        assert isinstance(tools, list)
        # Before setup, should be empty
        assert len(tools) == 0

    def test_agent_tool_names_property(self):
        """Test agent.tool_names property"""
        agent = SubstrateAgent(name="test_agent", tools=[])

        names = agent.tool_names
        assert isinstance(names, list)
        assert len(names) == 0

    def test_agent_health_includes_tool_info(self):
        """Test that agent health includes tool information"""
        db = postgresql(
            host="localhost",
            database="test",
            user="test",
            password="test"
        )

        agent = SubstrateAgent(
            name="test_agent",
            tools=[db]
        )

        health = agent.health

        assert "tools" in health
        assert "count" in health["tools"]
        assert "setup" in health["tools"]
        assert "names" in health["tools"]
        assert health["tools"]["setup"] == False  # Not setup yet

    @pytest.mark.asyncio
    async def test_agent_with_direct_agenttool_instances(self):
        """Test agent with direct AgentTool instances in tools list"""
        async def custom_handler(args): return {"result": "custom"}

        custom_tool = AgentTool(
            name="my_tool",
            description="My custom tool",
            parameters={"input": {"type": "string", "required": True}},
            handler=custom_handler
        )

        agent = SubstrateAgent(
            name="test_agent",
            tools=[custom_tool]
        )

        await agent._setup_tools()

        assert agent.tool_registry.tool_count == 1
        assert "my_tool" in agent.tool_registry.tool_names

    @pytest.mark.asyncio
    async def test_agent_with_mixed_tool_sources(self):
        """Test agent with mix of plugins and direct AgentTool instances"""
        db = postgresql(
            host="localhost",
            database="test",
            user="test",
            password="test"
        )

        async def custom_handler(args): return {"custom": True}

        custom_tool = AgentTool(
            name="custom",
            description="Custom",
            parameters={},
            handler=custom_handler
        )

        agent = SubstrateAgent(
            name="test_agent",
            tools=[db, custom_tool]
        )

        await agent._setup_tools()

        # 4 postgres tools + 1 custom = 5
        assert agent.tool_registry.tool_count == 5
        assert "query_database" in agent.tool_registry.tool_names
        assert "custom" in agent.tool_registry.tool_names

    @pytest.mark.asyncio
    async def test_tool_execution_error_handling(self):
        """Test that tool execution errors are handled properly"""
        db = postgresql(
            host="localhost",
            database="test",
            user="test",
            password="test"
        )

        # Make query raise an error
        db.query = AsyncMock(side_effect=Exception("Database error"))

        agent = SubstrateAgent(
            name="test_agent",
            tools=[db]
        )

        # Should raise the exception
        with pytest.raises(Exception, match="Database error"):
            await agent.call_tool("query_database", {"sql": "SELECT 1"})

    @pytest.mark.asyncio
    async def test_calling_nonexistent_tool(self):
        """Test calling a tool that doesn't exist"""
        agent = SubstrateAgent(name="test_agent", tools=[])

        with pytest.raises(RuntimeError, match="not found"):
            await agent.call_tool("nonexistent_tool", {})
