"""
Unit tests for AgentTool and ToolRegistry.

Tests the core tool abstraction system including:
- AgentTool creation and execution
- ToolRegistry management
- Tool format conversion
- Custom tool creation from functions
"""

import pytest
import asyncio
from typing import Dict, Any, Optional, Literal, List, Union

from daita.core.tools import AgentTool, ToolRegistry
from daita import tool


class TestAgentTool:
    """Test AgentTool class functionality"""

    def test_agenttool_creation(self):
        """Test basic AgentTool creation"""
        async def test_handler(args: Dict[str, Any]) -> Dict[str, Any]:
            return {"result": "success"}

        tool = AgentTool(
            name="test_tool",
            description="A test tool",
            parameters={
                "type": "object",
                "properties": {
                    "param1": {
                        "type": "string",
                        "description": "Test parameter"
                    }
                },
                "required": ["param1"]
            },
            handler=test_handler,
            category="test",
            source="custom"
        )

        assert tool.name == "test_tool"
        assert tool.description == "A test tool"
        assert tool.category == "test"
        assert tool.source == "custom"
        assert "properties" in tool.parameters
        assert "param1" in tool.parameters["properties"]

    def test_to_llm_function(self):
        """Test LLM function format conversion"""
        async def test_handler(args: Dict[str, Any]) -> Dict[str, Any]:
            return {"result": "success"}

        tool = AgentTool(
            name="test_tool",
            description="A test tool",
            parameters={
                "type": "object",
                "properties": {
                    "param1": {
                        "type": "string",
                        "description": "Test parameter"
                    },
                    "param2": {
                        "type": "integer",
                        "description": "Optional parameter"
                    }
                },
                "required": ["param1"]
            },
            handler=test_handler
        )

        llm_format = tool.to_llm_function()

        assert llm_format["name"] == "test_tool"
        assert llm_format["description"] == "A test tool"
        assert "parameters" in llm_format
        assert llm_format["parameters"]["type"] == "object"
        assert "param1" in llm_format["parameters"]["properties"]
        assert "param1" in llm_format["parameters"]["required"]
        assert "param2" not in llm_format["parameters"]["required"]

    def test_to_openai_function(self):
        """Test OpenAI function format conversion"""
        async def test_handler(args: Dict[str, Any]) -> Dict[str, Any]:
            return {"result": "success"}

        tool = AgentTool(
            name="test_tool",
            description="A test tool",
            parameters={
                "type": "object",
                "properties": {
                    "param1": {
                        "type": "string",
                        "description": "Test parameter"
                    }
                },
                "required": ["param1"]
            },
            handler=test_handler
        )

        openai_format = tool.to_openai_function()

        assert openai_format["type"] == "function"
        assert "function" in openai_format
        assert openai_format["function"]["name"] == "test_tool"
        assert "parameters" in openai_format["function"]

    def test_to_anthropic_tool(self):
        """Test Anthropic tool format conversion"""
        async def test_handler(args: Dict[str, Any]) -> Dict[str, Any]:
            return {"result": "success"}

        tool = AgentTool(
            name="test_tool",
            description="A test tool",
            parameters={
                "type": "object",
                "properties": {
                    "param1": {
                        "type": "string",
                        "description": "Test parameter"
                    }
                },
                "required": ["param1"]
            },
            handler=test_handler
        )

        anthropic_format = tool.to_anthropic_tool()

        assert anthropic_format["name"] == "test_tool"
        assert anthropic_format["description"] == "A test tool"
        assert "input_schema" in anthropic_format
        assert anthropic_format["input_schema"]["type"] == "object"

    def test_to_prompt_description(self):
        """Test prompt description generation"""
        async def test_handler(args: Dict[str, Any]) -> Dict[str, Any]:
            return {"result": "success"}

        tool = AgentTool(
            name="test_tool",
            description="A test tool for testing",
            parameters={
                "type": "object",
                "properties": {
                    "param1": {
                        "type": "string",
                        "description": "First parameter"
                    },
                    "param2": {
                        "type": "integer",
                        "description": "Second parameter"
                    }
                },
                "required": ["param1"]
            },
            handler=test_handler
        )

        description = tool.to_prompt_description()

        assert "test_tool" in description
        assert "A test tool for testing" in description
        assert "param1" in description
        assert "param2" in description
        assert "(required)" in description
        assert "(optional)" in description

    @pytest.mark.asyncio
    async def test_tool_execution(self):
        """Test tool execution"""
        async def test_handler(args: Dict[str, Any]) -> Dict[str, Any]:
            return {"result": args.get("input") * 2}

        tool = AgentTool(
            name="double",
            description="Double the input",
            parameters={
                "type": "object",
                "properties": {
                    "input": {"type": "integer"}
                },
                "required": ["input"]
            },
            handler=test_handler
        )

        result = await tool.execute({"input": 5})
        assert result["result"] == 10

    @pytest.mark.asyncio
    async def test_tool_execution_with_timeout(self):
        """Test tool execution with timeout"""
        async def slow_handler(args: Dict[str, Any]) -> Dict[str, Any]:
            await asyncio.sleep(2)
            return {"result": "done"}

        tool = AgentTool(
            name="slow_tool",
            description="A slow tool",
            parameters={
                "type": "object",
                "properties": {},
                "required": []
            },
            handler=slow_handler,
            timeout_seconds=1
        )

        with pytest.raises(RuntimeError, match="timed out"):
            await tool.execute({})

    def test_tool_from_sync_function(self):
        """Test creating AgentTool from sync function"""
        def sync_function(param1: str, param2: int = 10):
            """Test sync function"""
            return f"{param1}_{param2}"

        agent_tool = tool(sync_function)

        assert agent_tool.name == "sync_function"
        assert "Test sync function" in agent_tool.description
        assert "param1" in agent_tool.parameters["properties"]
        assert "param2" in agent_tool.parameters["properties"]
        assert "param1" in agent_tool.parameters["required"]
        assert "param2" not in agent_tool.parameters["required"]

    def test_tool_from_async_function(self):
        """Test creating AgentTool from async function"""
        async def async_function(query: str):
            """Search for something"""
            return ["result1", "result2"]

        agent_tool = tool(async_function)

        assert agent_tool.name == "async_function"
        assert "Search for something" in agent_tool.description
        assert "query" in agent_tool.parameters["properties"]
        assert agent_tool.parameters["properties"]["query"]["type"] == "string"

    def test_tool_with_explicit_options(self):
        """Test creating AgentTool with explicit name/description/category"""
        async def my_function(x: int, y: int):
            """Helper function"""
            return x + y

        agent_tool = tool(
            my_function,
            name="add_numbers",
            description="Add two numbers",
            category="math"
        )

        assert agent_tool.name == "add_numbers"
        assert agent_tool.description == "Add two numbers"
        assert agent_tool.category == "math"
        # Parameters auto-detected from type hints
        assert agent_tool.parameters["properties"]["x"]["type"] == "integer"
        assert agent_tool.parameters["properties"]["y"]["type"] == "integer"

    def test_tool_as_decorator(self):
        """Test @tool decorator without arguments"""
        @tool
        async def simple_tool(arg: str):
            """A simple tool"""
            return arg

        assert isinstance(simple_tool, AgentTool)
        assert simple_tool.name == "simple_tool"
        assert "A simple tool" in simple_tool.description

    def test_tool_as_decorator_with_options(self):
        """Test @tool decorator with arguments"""
        @tool(name="custom_name", timeout_seconds=30, category="test")
        async def my_tool(arg: str):
            """My custom tool"""
            return arg

        assert isinstance(my_tool, AgentTool)
        assert my_tool.name == "custom_name"
        assert my_tool.timeout_seconds == 30
        assert my_tool.category == "test"

    def test_tool_as_function_call(self):
        """Test tool() as direct function call"""
        async def my_func(arg: str):
            """Test function"""
            return arg

        agent_tool = tool(my_func)
        assert isinstance(agent_tool, AgentTool)
        assert agent_tool.name == "my_func"
        assert "Test function" in agent_tool.description


class TestToolRegistry:
    """Test ToolRegistry class functionality"""

    def test_registry_creation(self):
        """Test ToolRegistry creation"""
        registry = ToolRegistry()
        assert registry.tool_count == 0
        assert len(registry.tools) == 0

    def test_register_tool(self):
        """Test registering a single tool"""
        async def test_handler(args: Dict[str, Any]) -> Dict[str, Any]:
            return {"result": "success"}

        registry = ToolRegistry()
        tool = AgentTool(
            name="test_tool",
            description="Test",
            parameters={"type": "object", "properties": {}, "required": []},
            handler=test_handler
        )

        registry.register(tool)

        assert registry.tool_count == 1
        assert "test_tool" in registry.tool_names
        assert registry.get("test_tool") == tool

    def test_register_many_tools(self):
        """Test registering multiple tools"""
        async def handler1(args): return {"result": 1}
        async def handler2(args): return {"result": 2}

        registry = ToolRegistry()
        tools = [
            AgentTool(name="tool1", description="Tool 1", parameters={"type": "object", "properties": {}, "required": []}, handler=handler1),
            AgentTool(name="tool2", description="Tool 2", parameters={"type": "object", "properties": {}, "required": []}, handler=handler2)
        ]

        registry.register_many(tools)

        assert registry.tool_count == 2
        assert "tool1" in registry.tool_names
        assert "tool2" in registry.tool_names

    def test_register_duplicate_tool_warning(self, caplog):
        """Test that registering duplicate tool name shows warning"""
        async def handler1(args): return {"result": 1}
        async def handler2(args): return {"result": 2}

        registry = ToolRegistry()
        tool1 = AgentTool(name="duplicate", description="First", parameters={"type": "object", "properties": {}, "required": []}, handler=handler1)
        tool2 = AgentTool(name="duplicate", description="Second", parameters={"type": "object", "properties": {}, "required": []}, handler=handler2)

        registry.register(tool1)
        registry.register(tool2)

        assert registry.tool_count == 2  # Both added to list
        assert registry.get("duplicate") == tool2  # Map has second one

    def test_get_nonexistent_tool(self):
        """Test getting a tool that doesn't exist"""
        registry = ToolRegistry()
        assert registry.get("nonexistent") is None

    @pytest.mark.asyncio
    async def test_execute_tool(self):
        """Test executing a tool via registry"""
        async def test_handler(args: Dict[str, Any]) -> Dict[str, Any]:
            return {"result": args.get("value") * 3}

        registry = ToolRegistry()
        tool = AgentTool(
            name="triple",
            description="Triple the value",
            parameters={
                "type": "object",
                "properties": {"value": {"type": "integer"}},
                "required": ["value"]
            },
            handler=test_handler
        )

        registry.register(tool)
        result = await registry.execute("triple", {"value": 7})

        assert result["result"] == 21

    @pytest.mark.asyncio
    async def test_execute_nonexistent_tool(self):
        """Test executing a tool that doesn't exist"""
        registry = ToolRegistry()

        with pytest.raises(RuntimeError, match="not found"):
            await registry.execute("nonexistent", {})

    def test_tool_names_property(self):
        """Test tool_names property"""
        async def handler(args): return {}

        registry = ToolRegistry()
        registry.register(AgentTool(name="tool1", description="", parameters={"type": "object", "properties": {}, "required": []}, handler=handler))
        registry.register(AgentTool(name="tool2", description="", parameters={"type": "object", "properties": {}, "required": []}, handler=handler))

        names = registry.tool_names
        assert len(names) == 2
        assert "tool1" in names
        assert "tool2" in names


class TestAgentToolIntegration:
    """Integration tests for AgentTool features"""

    @pytest.mark.asyncio
    async def test_tool_with_category(self):
        """Test tool with category metadata"""
        async def db_query(args): return {"rows": []}

        tool = AgentTool(
            name="query_db",
            description="Query database",
            parameters={"type": "object", "properties": {}, "required": []},
            handler=db_query,
            category="database",
            source="plugin"
        )

        assert tool.category == "database"
        assert tool.source == "plugin"

    @pytest.mark.asyncio
    async def test_complete_tool_workflow(self):
        """Test complete workflow: create, register, execute"""
        # Create a simple tool
        async def calculator(args: Dict[str, Any]) -> Dict[str, Any]:
            operation = args.get("operation")
            a = args.get("a")
            b = args.get("b")

            if operation == "add":
                return {"result": a + b}
            elif operation == "multiply":
                return {"result": a * b}
            else:
                return {"error": "Unknown operation"}

        tool = AgentTool(
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
            handler=calculator,
            category="math"
        )

        # Register in registry
        registry = ToolRegistry()
        registry.register(tool)

        # Execute via registry
        result = await registry.execute("calculator", {
            "operation": "add",
            "a": 10,
            "b": 5
        })

        assert result["result"] == 15

        # Test another operation
        result = await registry.execute("calculator", {
            "operation": "multiply",
            "a": 10,
            "b": 5
        })

        assert result["result"] == 50


class TestAdvancedTypeHints:
    """Test advanced type hint and docstring parsing features"""

    def test_optional_type_hint(self):
        """Test Optional[T] type hints"""
        @tool
        async def optional_param(name: str, age: Optional[int] = None):
            """Test function with optional parameter"""
            return f"{name} is {age or 'unknown age'}"

        assert "name" in optional_param.parameters["required"]
        assert "age" not in optional_param.parameters["required"]
        assert optional_param.parameters["properties"]["age"]["type"] == "integer"

    def test_literal_type_hint(self):
        """Test Literal type hints create enums"""
        @tool
        async def calculator(operation: Literal["add", "subtract", "multiply", "divide"], a: float, b: float):
            """Perform calculations"""
            return a + b

        operation_schema = calculator.parameters["properties"]["operation"]
        assert operation_schema["type"] == "string"
        assert "enum" in operation_schema
        assert set(operation_schema["enum"]) == {"add", "subtract", "multiply", "divide"}

    def test_list_type_hint(self):
        """Test List[T] type hints"""
        @tool
        async def process_numbers(numbers: List[int]):
            """Process a list of numbers"""
            return sum(numbers)

        numbers_schema = process_numbers.parameters["properties"]["numbers"]
        assert numbers_schema["type"] == "array"
        assert numbers_schema["items"]["type"] == "integer"

    def test_union_type_hint(self):
        """Test Union type hints"""
        @tool
        async def flexible_input(value: Union[str, int]):
            """Accept string or int"""
            return str(value)

        value_schema = flexible_input.parameters["properties"]["value"]
        assert "anyOf" in value_schema
        types = [schema["type"] for schema in value_schema["anyOf"]]
        assert "string" in types
        assert "integer" in types

    def test_docstring_parameter_descriptions(self):
        """Test docstring parsing extracts parameter descriptions"""
        @tool
        async def search_documents(
            query: str,
            limit: int = 10,
            filters: Optional[Dict] = None
        ):
            """
            Search through documents.

            Args:
                query: The search query string
                limit: Maximum number of results to return
                filters: Optional filters to apply to the search
            """
            return []

        params = search_documents.parameters["properties"]
        assert params["query"]["description"] == "The search query string"
        assert params["limit"]["description"] == "Maximum number of results to return"
        assert params["filters"]["description"] == "Optional filters to apply to the search"

    def test_docstring_with_type_annotations(self):
        """Test docstring parsing handles (type) annotations"""
        @tool
        async def process_data(data: str, mode: str):
            """
            Process data.

            Args:
                data (str): The input data to process
                mode (str): Processing mode
            """
            return data

        params = process_data.parameters["properties"]
        assert params["data"]["description"] == "The input data to process"
        assert params["mode"]["description"] == "Processing mode"

    def test_default_values_make_optional(self):
        """Test parameters with defaults are not required"""
        @tool
        async def create_user(username: str, email: str, role: str = "user"):
            """Create a user"""
            return username

        required = create_user.parameters["required"]
        assert "username" in required
        assert "email" in required
        assert "role" not in required

    def test_complex_realistic_example(self):
        """Test a realistic complex example with all features"""
        @tool
        async def execute_query(
            operation: Literal["create", "read", "update", "delete"],
            table: str,
            conditions: Optional[Dict[str, Any]] = None,
            fields: Optional[List[str]] = None,
            limit: int = 100
        ):
            """
            Execute a database query.

            Args:
                operation: The CRUD operation to perform
                table: Name of the database table
                conditions: Optional WHERE conditions as key-value pairs
                fields: Optional list of fields to return
                limit: Maximum number of records to return
            """
            return {"operation": operation, "table": table}

        schema = execute_query.parameters
        props = schema["properties"]
        required = schema["required"]

        # Check required fields
        assert "operation" in required
        assert "table" in required
        assert "conditions" not in required
        assert "fields" not in required
        assert "limit" not in required

        # Check types
        assert props["operation"]["type"] == "string"
        assert "enum" in props["operation"]
        assert props["table"]["type"] == "string"
        assert props["conditions"]["type"] == "object"
        assert props["fields"]["type"] == "array"
        assert props["fields"]["items"]["type"] == "string"
        assert props["limit"]["type"] == "integer"

        # Check descriptions
        assert props["operation"]["description"] == "The CRUD operation to perform"
        assert props["table"]["description"] == "Name of the database table"
        assert props["limit"]["description"] == "Maximum number of records to return"

    def test_fallback_for_no_docstring(self):
        """Test that functions without docstrings still work"""
        @tool
        async def no_docs(x: int, y: Optional[str] = None):
            return x

        params = no_docs.parameters["properties"]
        # Should have generic descriptions
        assert "Parameter:" in params["x"]["description"]
        assert "Parameter:" in params["y"]["description"]

    def test_fallback_for_invalid_type_hints(self):
        """Test graceful fallback for unsupported type hints"""
        @tool
        async def weird_types(x):  # No type hint
            """Function with no type hints"""
            return x

        params = weird_types.parameters["properties"]
        # Should default to string type
        assert params["x"]["type"] == "string"
