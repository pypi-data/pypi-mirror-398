"""
Unit tests for LLM tool calling implementation.

Tests the core functionality of the tool calling system including:
- JSON schema format validation
- Function calling loop logic
- Tool execution with mocks
- OpenAI and Anthropic provider implementations
- Handler helper methods
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from daita.agents.substrate import SubstrateAgent
from daita.core.tools import AgentTool
from daita.llm.base import BaseLLMProvider
from daita.llm.openai import OpenAIProvider
from daita.llm.anthropic import AnthropicProvider
from daita.core.exceptions import AgentError


# Mock tool for testing
async def mock_calculator(args: Dict[str, Any]) -> Dict[str, Any]:
    """Mock calculator tool for testing."""
    operation = args.get("operation")
    a = args.get("a", 0)
    b = args.get("b", 0)

    if operation == "add":
        result = a + b
    elif operation == "multiply":
        result = a * b
    elif operation == "subtract":
        result = a - b
    elif operation == "divide":
        result = a / b if b != 0 else "Error: Division by zero"
    else:
        result = "Unknown operation"

    return {
        "operation": operation,
        "a": a,
        "b": b,
        "result": result
    }


async def mock_database_query(args: Dict[str, Any]) -> Dict[str, Any]:
    """Mock database query tool for testing."""
    return {
        "success": True,
        "rows": [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"}
        ],
        "row_count": 2
    }


class TestJSONSchemaFormat:
    """Test that all plugin tools use correct JSON schema format."""

    def test_postgresql_tool_schema(self):
        """Test PostgreSQL plugin tools have correct JSON schema format."""
        from daita.plugins.postgresql import PostgreSQLPlugin

        # Create plugin instance (won't actually connect)
        plugin = PostgreSQLPlugin(host="localhost", database="test", user="test", password="test")
        tools = plugin.get_tools()

        # Check each tool has correct schema
        for tool in tools:
            assert "type" in tool.parameters, f"Tool {tool.name} missing 'type' field"
            assert tool.parameters["type"] == "object", f"Tool {tool.name} has incorrect type"
            assert "properties" in tool.parameters, f"Tool {tool.name} missing 'properties' field"
            assert "required" in tool.parameters, f"Tool {tool.name} missing 'required' field"
            assert isinstance(tool.parameters["required"], list), f"Tool {tool.name} 'required' must be array"

            # Check no nested 'required' inside properties
            for prop_name, prop_spec in tool.parameters["properties"].items():
                assert "required" not in prop_spec, f"Tool {tool.name} has nested 'required' in property {prop_name}"

    def test_mongodb_tool_schema(self):
        """Test MongoDB plugin tools have correct JSON schema format."""
        from daita.plugins.mongodb import MongoDBPlugin

        plugin = MongoDBPlugin(uri="mongodb://localhost:27017", database="test")
        tools = plugin.get_tools()

        for tool in tools:
            assert tool.parameters["type"] == "object"
            assert "properties" in tool.parameters
            assert isinstance(tool.parameters["required"], list)

    def test_s3_tool_schema(self):
        """Test S3 plugin tools have correct JSON schema format."""
        from daita.plugins.s3 import S3Plugin

        plugin = S3Plugin(bucket="test-bucket")
        tools = plugin.get_tools()

        for tool in tools:
            assert tool.parameters["type"] == "object"
            assert "properties" in tool.parameters
            assert isinstance(tool.parameters["required"], list)

    def test_rest_tool_schema(self):
        """Test REST plugin tools have correct JSON schema format."""
        from daita.plugins.rest import RESTPlugin

        plugin = RESTPlugin(base_url="https://api.example.com")
        tools = plugin.get_tools()

        for tool in tools:
            assert tool.parameters["type"] == "object"
            assert "properties" in tool.parameters
            assert isinstance(tool.parameters["required"], list)

    def test_elasticsearch_tool_schema(self):
        """Test Elasticsearch plugin tools have correct JSON schema format."""
        from daita.plugins.elasticsearch import ElasticsearchPlugin

        plugin = ElasticsearchPlugin(hosts=["http://localhost:9200"])
        tools = plugin.get_tools()

        for tool in tools:
            assert tool.parameters["type"] == "object"
            assert "properties" in tool.parameters
            assert isinstance(tool.parameters["required"], list)


class TestAgentToolConversion:
    """Test AgentTool conversion to different provider formats."""

    def test_to_openai_function(self):
        """Test conversion to OpenAI function format."""
        tool = AgentTool(
            name="test_tool",
            description="A test tool",
            parameters={
                "type": "object",
                "properties": {
                    "input": {
                        "type": "string",
                        "description": "Input parameter"
                    }
                },
                "required": ["input"]
            },
            handler=mock_calculator
        )

        openai_format = tool.to_openai_function()

        assert openai_format["type"] == "function"
        assert openai_format["function"]["name"] == "test_tool"
        assert openai_format["function"]["description"] == "A test tool"
        assert openai_format["function"]["parameters"]["type"] == "object"
        assert "properties" in openai_format["function"]["parameters"]
        assert "required" in openai_format["function"]["parameters"]

    def test_to_anthropic_tool(self):
        """Test conversion to Anthropic tool format."""
        tool = AgentTool(
            name="test_tool",
            description="A test tool",
            parameters={
                "type": "object",
                "properties": {
                    "input": {
                        "type": "string",
                        "description": "Input parameter"
                    }
                },
                "required": ["input"]
            },
            handler=mock_calculator
        )

        anthropic_format = tool.to_anthropic_tool()

        assert anthropic_format["name"] == "test_tool"
        assert anthropic_format["description"] == "A test tool"
        assert anthropic_format["input_schema"]["type"] == "object"


class MockToolCallingProvider(BaseLLMProvider):
    """Mock provider that supports tool calling for testing."""

    def __init__(self, **kwargs):
        super().__init__(model="mock-model", **kwargs)
        self.call_count = 0
        self.tool_calls_to_make = []  # Queue of tool calls to simulate
        self.final_response = "Task completed successfully"

    def set_tool_calls(self, tool_calls_sequence):
        """Set the sequence of tool calls the LLM will make."""
        self.tool_calls_to_make = tool_calls_sequence

    async def _generate_impl(self, prompt: str, **kwargs) -> str:
        """Mock generate implementation."""
        return "Mock response"

    async def _generate_with_tools_single(
        self,
        messages: list[Dict[str, Any]],
        tools: list[Dict[str, Any]],
        **kwargs
    ) -> Dict[str, Any]:
        """Mock single tool calling iteration."""
        self.call_count += 1

        # If there are tool calls to make, return them
        if self.tool_calls_to_make:
            tool_call = self.tool_calls_to_make.pop(0)
            return {
                "tool_calls": [tool_call]
            }
        else:
            # No more tool calls, return final response
            return {
                "content": self.final_response
            }


@pytest.mark.asyncio
class TestFunctionCallingLoop:
    """Test the core function calling loop logic."""

    async def test_single_tool_call(self):
        """Test LLM making a single tool call."""
        # Create mock provider
        provider = MockToolCallingProvider()
        provider.set_tool_calls([
            {
                "id": "call_1",
                "name": "calculator",
                "arguments": {"operation": "add", "a": 5, "b": 3}
            }
        ])

        # Create tool
        calc_tool = AgentTool(
            name="calculator",
            description="Perform calculations",
            parameters={
                "type": "object",
                "properties": {
                    "operation": {"type": "string"},
                    "a": {"type": "number"},
                    "b": {"type": "number"}
                },
                "required": ["operation", "a", "b"]
            },
            handler=mock_calculator
        )

        # Execute tool calling loop
        result = await provider.generate_with_tools(
            prompt="Calculate 5 + 3",
            tools=[calc_tool]
        )

        # Verify results
        assert result["iterations"] == 2  # One tool call + final response
        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["tool"] == "calculator"
        assert result["tool_calls"][0]["result"]["result"] == 8
        assert "result" in result

    async def test_multiple_tool_calls(self):
        """Test LLM making multiple tool calls in sequence."""
        provider = MockToolCallingProvider()
        provider.set_tool_calls([
            {
                "id": "call_1",
                "name": "calculator",
                "arguments": {"operation": "add", "a": 5, "b": 3}
            },
            {
                "id": "call_2",
                "name": "calculator",
                "arguments": {"operation": "multiply", "a": 8, "b": 2}
            }
        ])

        calc_tool = AgentTool(
            name="calculator",
            description="Perform calculations",
            parameters={
                "type": "object",
                "properties": {
                    "operation": {"type": "string"},
                    "a": {"type": "number"},
                    "b": {"type": "number"}
                },
                "required": ["operation", "a", "b"]
            },
            handler=mock_calculator
        )

        result = await provider.generate_with_tools(
            prompt="Calculate 5 + 3, then multiply the result by 2",
            tools=[calc_tool]
        )

        assert len(result["tool_calls"]) == 2
        assert result["tool_calls"][0]["result"]["result"] == 8
        assert result["tool_calls"][1]["result"]["result"] == 16

    async def test_max_iterations_exceeded(self):
        """Test that max iterations limit is enforced."""
        provider = MockToolCallingProvider()

        # Set up infinite tool calls
        for i in range(10):
            provider.tool_calls_to_make.append({
                "id": f"call_{i}",
                "name": "calculator",
                "arguments": {"operation": "add", "a": i, "b": 1}
            })

        calc_tool = AgentTool(
            name="calculator",
            description="Perform calculations",
            parameters={
                "type": "object",
                "properties": {
                    "operation": {"type": "string"},
                    "a": {"type": "number"},
                    "b": {"type": "number"}
                },
                "required": ["operation", "a", "b"]
            },
            handler=mock_calculator
        )

        result = await provider.generate_with_tools(
            prompt="Keep calculating",
            tools=[calc_tool],
            max_iterations=3
        )

        assert result["iterations"] == 3
        assert "error" in result
        assert result["error"] == "max_iterations_exceeded"

    async def test_tool_timeout_handling(self):
        """Test that tool timeouts are handled gracefully."""
        async def slow_tool(args):
            await asyncio.sleep(5)
            return {"result": "done"}

        provider = MockToolCallingProvider()
        provider.set_tool_calls([
            {
                "id": "call_1",
                "name": "slow_tool",
                "arguments": {}
            }
        ])

        slow_tool_obj = AgentTool(
            name="slow_tool",
            description="A slow tool",
            parameters={
                "type": "object",
                "properties": {},
                "required": []
            },
            handler=slow_tool,
            timeout_seconds=1  # 1 second timeout
        )

        result = await provider.generate_with_tools(
            prompt="Run slow tool",
            tools=[slow_tool_obj]
        )

        # Should complete with error in tool result
        assert len(result["tool_calls"]) == 1
        assert "error" in result["tool_calls"][0]["result"]
        assert "timed out" in result["tool_calls"][0]["result"]["error"]


@pytest.mark.asyncio
class TestHandlerHelpers:
    """Test handler helper methods in SubstrateAgent."""

    async def test_autonomous_handler(self):
        """Test built-in autonomous handler."""
        # Create agent with mock LLM
        agent = SubstrateAgent(
            name="test_agent",
            llm_provider="mock",
            model="mock-model"
        )

        # Replace LLM with our mock
        mock_provider = MockToolCallingProvider(agent_id=agent.agent_id)
        mock_provider.set_tool_calls([
            {
                "id": "call_1",
                "name": "database_query",
                "arguments": {"sql": "SELECT * FROM users"}
            }
        ])
        agent.llm = mock_provider

        # Register a tool
        db_tool = AgentTool(
            name="database_query",
            description="Query database",
            parameters={
                "type": "object",
                "properties": {
                    "sql": {"type": "string"}
                },
                "required": ["sql"]
            },
            handler=mock_database_query
        )
        agent.register_tool(db_tool)

        # Call autonomous handler
        result = await agent.process(
            'autonomous',
            context={
                'instructions': 'Get all users from the database',
                'tools': ['database_query']
            }
        )

        # Verify result structure
        assert "result" in result
        assert "tool_calls" in result
        assert "iterations" in result
        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["tool"] == "database_query"

    async def test_call_llm_with_tools_helper(self):
        """Test _call_llm_with_tools helper method."""
        agent = SubstrateAgent(
            name="test_agent",
            llm_provider="mock",
            model="mock-model"
        )

        mock_provider = MockToolCallingProvider(agent_id=agent.agent_id)
        mock_provider.set_tool_calls([
            {
                "id": "call_1",
                "name": "calculator",
                "arguments": {"operation": "add", "a": 10, "b": 20}
            }
        ])
        agent.llm = mock_provider

        calc_tool = AgentTool(
            name="calculator",
            description="Perform calculations",
            parameters={
                "type": "object",
                "properties": {
                    "operation": {"type": "string"},
                    "a": {"type": "number"},
                    "b": {"type": "number"}
                },
                "required": ["operation", "a", "b"]
            },
            handler=mock_calculator
        )
        agent.register_tool(calc_tool)

        # Call helper directly
        result = await agent._call_llm_with_tools(
            prompt="Add 10 and 20",
            tools=["calculator"]
        )

        assert result["result"]
        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["result"]["result"] == 30

    async def test_custom_handler_with_tools(self):
        """Test custom handler using _call_llm_with_tools internally."""
        agent = SubstrateAgent(
            name="test_agent",
            llm_provider="mock",
            model="mock-model"
        )

        mock_provider = MockToolCallingProvider(agent_id=agent.agent_id)
        mock_provider.set_tool_calls([
            {
                "id": "call_1",
                "name": "database_query",
                "arguments": {"sql": "SELECT * FROM users WHERE active = true"}
            }
        ])
        agent.llm = mock_provider

        db_tool = AgentTool(
            name="database_query",
            description="Query database",
            parameters={
                "type": "object",
                "properties": {
                    "sql": {"type": "string"}
                },
                "required": ["sql"]
            },
            handler=mock_database_query
        )
        agent.register_tool(db_tool)

        # Define custom handler that uses tool calling
        async def custom_handler(data, context, agent):
            result = await agent._call_llm_with_tools(
                prompt="Find all active users",
                tools=["database_query"]
            )
            return {
                "custom_handler_result": result,
                "processed": True
            }

        agent.add_handler("custom_task", custom_handler)

        # Execute custom handler
        result = await agent.process('custom_task', data=None)

        assert result["processed"] is True
        assert "custom_handler_result" in result
        assert len(result["custom_handler_result"]["tool_calls"]) == 1

    async def test_autonomous_handler_missing_instructions(self):
        """Test that autonomous handler requires instructions."""
        agent = SubstrateAgent(
            name="test_agent",
            llm_provider="mock",
            model="mock-model"
        )

        # Try to call autonomous handler without instructions
        # Should return error result, not raise exception (production behavior)
        result = await agent.process('autonomous', context={})

        # Check that it returned an error status
        assert result['status'] == 'error'
        assert 'instructions' in result['error'].lower()


@pytest.mark.asyncio
class TestToolExecution:
    """Test tool execution with various scenarios."""

    async def test_tool_not_found(self):
        """Test handling of missing tool."""
        provider = MockToolCallingProvider()
        provider.set_tool_calls([
            {
                "id": "call_1",
                "name": "nonexistent_tool",
                "arguments": {}
            }
        ])

        result = await provider.generate_with_tools(
            prompt="Use nonexistent tool",
            tools=[]
        )

        # Should complete with error in tool result
        assert len(result["tool_calls"]) == 1
        assert "error" in result["tool_calls"][0]["result"]
        assert "not found" in result["tool_calls"][0]["result"]["error"]

    async def test_tool_execution_error(self):
        """Test handling of tool execution errors."""
        async def error_tool(args):
            raise ValueError("Tool execution failed")

        provider = MockToolCallingProvider()
        provider.set_tool_calls([
            {
                "id": "call_1",
                "name": "error_tool",
                "arguments": {}
            }
        ])

        error_tool_obj = AgentTool(
            name="error_tool",
            description="A tool that errors",
            parameters={
                "type": "object",
                "properties": {},
                "required": []
            },
            handler=error_tool
        )

        result = await provider.generate_with_tools(
            prompt="Run error tool",
            tools=[error_tool_obj]
        )

        # Should complete with error in tool result
        assert len(result["tool_calls"]) == 1
        assert "error" in result["tool_calls"][0]["result"]
        assert "failed" in result["tool_calls"][0]["result"]["error"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
