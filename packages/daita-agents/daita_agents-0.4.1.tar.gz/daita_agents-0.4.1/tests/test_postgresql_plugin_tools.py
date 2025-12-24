"""
Unit tests for PostgreSQL Plugin Tool Integration.

Tests that the PostgreSQL plugin correctly exposes tools and that
the tools function properly.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from daita.plugins.postgresql import PostgreSQLPlugin, postgresql
from daita.core.tools import AgentTool


class TestPostgreSQLPluginTools:
    """Test PostgreSQL plugin tool exposure"""

    def test_plugin_has_get_tools_method(self):
        """Test that PostgreSQL plugin has get_tools method"""
        plugin = postgresql(
            host="localhost",
            database="test",
            user="test_user",
            password="test_pass"
        )

        assert hasattr(plugin, 'get_tools')
        assert callable(plugin.get_tools)

    def test_plugin_exposes_tools(self):
        """Test that PostgreSQL plugin exposes expected tools"""
        plugin = postgresql(
            host="localhost",
            database="test",
            user="test_user",
            password="test_pass"
        )

        tools = plugin.get_tools()

        assert len(tools) == 4
        tool_names = [t.name for t in tools]

        assert "query_database" in tool_names
        assert "list_tables" in tool_names
        assert "get_table_schema" in tool_names
        assert "execute_sql" in tool_names

    def test_tools_are_agenttool_instances(self):
        """Test that all returned tools are AgentTool instances"""
        plugin = postgresql(
            host="localhost",
            database="test",
            user="test_user",
            password="test_pass"
        )

        tools = plugin.get_tools()

        for tool in tools:
            assert isinstance(tool, AgentTool)
            assert tool.source == "plugin"
            assert tool.plugin_name == "PostgreSQL"
            assert tool.category == "database"

    def test_query_database_tool_definition(self):
        """Test query_database tool has correct definition"""
        plugin = postgresql(
            host="localhost",
            database="test",
            user="test_user",
            password="test_pass"
        )

        tools = plugin.get_tools()
        query_tool = next(t for t in tools if t.name == "query_database")

        assert query_tool.name == "query_database"
        assert "SQL SELECT query" in query_tool.description
        assert "sql" in query_tool.parameters
        assert query_tool.parameters["sql"]["required"] == True
        assert "params" in query_tool.parameters
        assert query_tool.parameters["params"]["required"] == False
        assert query_tool.timeout_seconds == 60

    def test_list_tables_tool_definition(self):
        """Test list_tables tool has correct definition"""
        plugin = postgresql(
            host="localhost",
            database="test",
            user="test_user",
            password="test_pass"
        )

        tools = plugin.get_tools()
        list_tool = next(t for t in tools if t.name == "list_tables")

        assert list_tool.name == "list_tables"
        assert "List all tables" in list_tool.description
        assert len(list_tool.parameters) == 0  # No parameters
        assert list_tool.timeout_seconds == 30

    def test_get_table_schema_tool_definition(self):
        """Test get_table_schema tool has correct definition"""
        plugin = postgresql(
            host="localhost",
            database="test",
            user="test_user",
            password="test_pass"
        )

        tools = plugin.get_tools()
        schema_tool = next(t for t in tools if t.name == "get_table_schema")

        assert schema_tool.name == "get_table_schema"
        assert "column information" in schema_tool.description
        assert "table_name" in schema_tool.parameters
        assert schema_tool.parameters["table_name"]["required"] == True

    def test_execute_sql_tool_definition(self):
        """Test execute_sql tool has correct definition"""
        plugin = postgresql(
            host="localhost",
            database="test",
            user="test_user",
            password="test_pass"
        )

        tools = plugin.get_tools()
        execute_tool = next(t for t in tools if t.name == "execute_sql")

        assert execute_tool.name == "execute_sql"
        assert "INSERT, UPDATE, or DELETE" in execute_tool.description
        assert "sql" in execute_tool.parameters
        assert execute_tool.timeout_seconds == 60

    @pytest.mark.asyncio
    async def test_query_database_tool_execution(self):
        """Test query_database tool execution"""
        plugin = postgresql(
            host="localhost",
            database="test",
            user="test_user",
            password="test_pass"
        )

        # Mock the query method
        plugin.query = AsyncMock(return_value=[
            {"id": 1, "name": "John"},
            {"id": 2, "name": "Jane"}
        ])

        tools = plugin.get_tools()
        query_tool = next(t for t in tools if t.name == "query_database")

        # Execute tool
        result = await query_tool.execute({
            "sql": "SELECT * FROM users"
        })

        assert result["success"] == True
        assert len(result["rows"]) == 2
        assert result["row_count"] == 2
        plugin.query.assert_called_once_with("SELECT * FROM users", None)

    @pytest.mark.asyncio
    async def test_query_database_tool_with_params(self):
        """Test query_database tool with parameters"""
        plugin = postgresql(
            host="localhost",
            database="test",
            user="test_user",
            password="test_pass"
        )

        plugin.query = AsyncMock(return_value=[{"id": 1, "name": "John"}])

        tools = plugin.get_tools()
        query_tool = next(t for t in tools if t.name == "query_database")

        result = await query_tool.execute({
            "sql": "SELECT * FROM users WHERE id = $1",
            "params": ["1"]
        })

        assert result["success"] == True
        plugin.query.assert_called_once_with("SELECT * FROM users WHERE id = $1", ["1"])

    @pytest.mark.asyncio
    async def test_list_tables_tool_execution(self):
        """Test list_tables tool execution"""
        plugin = postgresql(
            host="localhost",
            database="test",
            user="test_user",
            password="test_pass"
        )

        plugin.tables = AsyncMock(return_value=["users", "orders", "products"])

        tools = plugin.get_tools()
        list_tool = next(t for t in tools if t.name == "list_tables")

        result = await list_tool.execute({})

        assert result["success"] == True
        assert result["tables"] == ["users", "orders", "products"]
        assert result["count"] == 3
        plugin.tables.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_table_schema_tool_execution(self):
        """Test get_table_schema tool execution"""
        plugin = postgresql(
            host="localhost",
            database="test",
            user="test_user",
            password="test_pass"
        )

        plugin.query = AsyncMock(return_value=[
            {"column_name": "id", "data_type": "integer", "is_nullable": "NO"},
            {"column_name": "name", "data_type": "varchar", "is_nullable": "YES"}
        ])

        tools = plugin.get_tools()
        schema_tool = next(t for t in tools if t.name == "get_table_schema")

        result = await schema_tool.execute({
            "table_name": "users"
        })

        assert result["success"] == True
        assert result["table"] == "users"
        assert len(result["columns"]) == 2
        assert result["column_count"] == 2
        plugin.query.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_sql_tool_execution(self):
        """Test execute_sql tool execution"""
        plugin = postgresql(
            host="localhost",
            database="test",
            user="test_user",
            password="test_pass"
        )

        plugin.execute = AsyncMock(return_value=5)

        tools = plugin.get_tools()
        execute_tool = next(t for t in tools if t.name == "execute_sql")

        result = await execute_tool.execute({
            "sql": "INSERT INTO users (name) VALUES ($1)",
            "params": ["Alice"]
        })

        assert result["success"] == True
        assert result["affected_rows"] == 5
        plugin.execute.assert_called_once_with("INSERT INTO users (name) VALUES ($1)", ["Alice"])

    def test_has_tools_property(self):
        """Test has_tools property returns True"""
        plugin = postgresql(
            host="localhost",
            database="test",
            user="test_user",
            password="test_pass"
        )

        assert plugin.has_tools == True

    def test_tools_have_callable_handlers(self):
        """Test that all tool handlers are callable"""
        plugin = postgresql(
            host="localhost",
            database="test",
            user="test_user",
            password="test_pass"
        )

        tools = plugin.get_tools()

        for tool in tools:
            assert callable(tool.handler)

    def test_tool_llm_format_conversion(self):
        """Test that tools can be converted to LLM format"""
        plugin = postgresql(
            host="localhost",
            database="test",
            user="test_user",
            password="test_pass"
        )

        tools = plugin.get_tools()

        for tool in tools:
            llm_format = tool.to_llm_function()
            assert "name" in llm_format
            assert "description" in llm_format
            assert "parameters" in llm_format

            openai_format = tool.to_openai_function()
            assert openai_format["type"] == "function"

            anthropic_format = tool.to_anthropic_tool()
            assert "input_schema" in anthropic_format


class TestPostgreSQLBackwardsCompatibility:
    """Test that PostgreSQL plugin still works with direct usage (non-tool)"""

    @pytest.mark.asyncio
    async def test_direct_query_still_works(self):
        """Test that direct query method still works"""
        plugin = postgresql(
            host="localhost",
            database="test",
            user="test_user",
            password="test_pass"
        )

        # Mock connection
        plugin._pool = MagicMock()
        mock_conn = MagicMock()
        mock_conn.fetch = AsyncMock(return_value=[
            MagicMock(items=lambda: [("id", 1), ("name", "John")])
        ])
        plugin._pool.acquire = MagicMock()
        plugin._pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        plugin._pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

        # Direct usage (old way) should still work
        result = await plugin.query("SELECT * FROM users")

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_direct_execute_still_works(self):
        """Test that direct execute method still works"""
        plugin = postgresql(
            host="localhost",
            database="test",
            user="test_user",
            password="test_pass"
        )

        # Mock connection
        plugin._pool = MagicMock()
        mock_conn = MagicMock()
        mock_conn.execute = AsyncMock(return_value="INSERT 0 5")
        plugin._pool.acquire = MagicMock()
        plugin._pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        plugin._pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

        # Direct usage should still work
        result = await plugin.execute("INSERT INTO users (name) VALUES ('Alice')")

        assert result == 5

    def test_plugin_factory_function(self):
        """Test that postgresql() factory function works"""
        plugin = postgresql(
            host="localhost",
            database="test",
            user="test_user",
            password="test_pass"
        )

        assert isinstance(plugin, PostgreSQLPlugin)
        assert plugin.config["host"] == "localhost"
        assert plugin.config["database"] == "test"
