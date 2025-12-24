"""
Test Direct PostgreSQL Plugin Usage (Backwards Compatibility).

Ensures that the PostgreSQL plugin still works correctly when used
directly (non-tool mode) as it did before the tool integration.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from daita.plugins.postgresql import PostgreSQLPlugin, postgresql


class TestPostgreSQLDirectUsage:
    """Test direct PostgreSQL plugin usage (original functionality)"""

    def test_postgresql_factory_function(self):
        """Test postgresql() factory function"""
        plugin = postgresql(
            host="localhost",
            port=5432,
            database="test_db",
            user="test_user",
            password="test_pass"
        )

        assert isinstance(plugin, PostgreSQLPlugin)
        assert "localhost" in plugin.connection_string
        assert "test_db" in plugin.connection_string

    def test_postgresql_connection_string_override(self):
        """Test creating plugin with connection string"""
        plugin = postgresql(
            connection_string="postgresql://user:pass@host:5432/db"
        )

        assert plugin.connection_string == "postgresql://user:pass@host:5432/db"

    def test_postgresql_pool_config(self):
        """Test PostgreSQL pool configuration"""
        plugin = postgresql(
            host="localhost",
            database="test",
            user="test",
            password="test",
            min_size=2,
            max_size=20,
            command_timeout=120
        )

        assert plugin.pool_config["min_size"] == 2
        assert plugin.pool_config["max_size"] == 20
        assert plugin.pool_config["command_timeout"] == 120

    @pytest.mark.asyncio
    async def test_direct_query_execution(self):
        """Test direct query execution"""
        plugin = postgresql(
            host="localhost",
            database="test",
            user="test",
            password="test"
        )

        # Mock pool and connection
        mock_record = MagicMock()
        mock_record.items = lambda: [("id", 1), ("name", "Alice"), ("email", "alice@example.com")]

        mock_conn = MagicMock()
        mock_conn.fetch = AsyncMock(return_value=[mock_record])

        plugin._pool = MagicMock()
        plugin._pool.acquire = MagicMock()
        plugin._pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        plugin._pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

        # Direct query
        result = await plugin.query("SELECT * FROM users WHERE id = $1", [1])

        assert isinstance(result, list)
        assert len(result) == 1
        mock_conn.fetch.assert_called_once_with("SELECT * FROM users WHERE id = $1", 1)

    @pytest.mark.asyncio
    async def test_direct_query_without_params(self):
        """Test direct query without parameters"""
        plugin = postgresql(
            host="localhost",
            database="test",
            user="test",
            password="test"
        )

        mock_record1 = MagicMock()
        mock_record1.items = lambda: [("id", 1), ("name", "Alice")]
        mock_record2 = MagicMock()
        mock_record2.items = lambda: [("id", 2), ("name", "Bob")]

        mock_conn = MagicMock()
        mock_conn.fetch = AsyncMock(return_value=[mock_record1, mock_record2])

        plugin._pool = MagicMock()
        plugin._pool.acquire = MagicMock()
        plugin._pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        plugin._pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await plugin.query("SELECT * FROM users")

        assert len(result) == 2
        mock_conn.fetch.assert_called_once_with("SELECT * FROM users")

    @pytest.mark.asyncio
    async def test_direct_execute(self):
        """Test direct execute for INSERT/UPDATE/DELETE"""
        plugin = postgresql(
            host="localhost",
            database="test",
            user="test",
            password="test"
        )

        mock_conn = MagicMock()
        mock_conn.execute = AsyncMock(return_value="INSERT 0 3")

        plugin._pool = MagicMock()
        plugin._pool.acquire = MagicMock()
        plugin._pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        plugin._pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await plugin.execute("INSERT INTO users (name) VALUES ($1)", ["Charlie"])

        assert result == 3
        mock_conn.execute.assert_called_once_with("INSERT INTO users (name) VALUES ($1)", "Charlie")

    @pytest.mark.asyncio
    async def test_direct_execute_update(self):
        """Test direct execute for UPDATE"""
        plugin = postgresql(
            host="localhost",
            database="test",
            user="test",
            password="test"
        )

        mock_conn = MagicMock()
        mock_conn.execute = AsyncMock(return_value="UPDATE 5")

        plugin._pool = MagicMock()
        plugin._pool.acquire = MagicMock()
        plugin._pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        plugin._pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await plugin.execute("UPDATE users SET active = true WHERE id > $1", [10])

        assert result == 5

    @pytest.mark.asyncio
    async def test_insert_many(self):
        """Test bulk insert"""
        plugin = postgresql(
            host="localhost",
            database="test",
            user="test",
            password="test"
        )

        mock_conn = MagicMock()
        mock_conn.executemany = AsyncMock()

        plugin._pool = MagicMock()
        plugin._pool.acquire = MagicMock()
        plugin._pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        plugin._pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
            {"name": "Charlie", "age": 35}
        ]

        result = await plugin.insert_many("users", data)

        assert result == 3
        mock_conn.executemany.assert_called_once()

    @pytest.mark.asyncio
    async def test_tables_list(self):
        """Test listing tables"""
        plugin = postgresql(
            host="localhost",
            database="test",
            user="test",
            password="test"
        )

        # Mock the query method directly since tables() just calls query()
        plugin.query = AsyncMock(return_value=[
            {"table_name": "users"},
            {"table_name": "orders"},
            {"table_name": "products"}
        ])

        tables = await plugin.tables()

        assert tables == ["users", "orders", "products"]
        plugin.query.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager_usage(self):
        """Test using plugin as context manager"""
        plugin = postgresql(
            host="localhost",
            database="test",
            user="test",
            password="test"
        )

        # Mock connect and disconnect
        plugin.connect = AsyncMock()
        plugin.disconnect = AsyncMock()

        async with plugin as db:
            assert db == plugin

        plugin.connect.assert_called_once()
        plugin.disconnect.assert_called_once()

    def test_is_connected_property(self):
        """Test is_connected property"""
        plugin = postgresql(
            host="localhost",
            database="test",
            user="test",
            password="test"
        )

        # No connection initially
        assert plugin.is_connected == False

        # Simulate connection
        plugin._pool = MagicMock()
        assert plugin.is_connected == True

    def test_plugin_info_property(self):
        """Test plugin info property"""
        plugin = postgresql(
            host="localhost",
            database="test",
            user="test",
            password="test",
            timeout=60
        )

        info = plugin.info

        assert info["plugin_type"] == "PostgreSQLPlugin"
        assert info["connected"] == False
        assert info["timeout"] == 60
        assert "config_keys" in info


class TestPostgreSQLWithAgentOldStyle:
    """Test PostgreSQL plugin with agent (old style, non-tool)"""

    @pytest.mark.asyncio
    async def test_agent_with_plugin_old_style(self):
        """Test agent using plugin directly (old style)"""
        from daita.agents.substrate import SubstrateAgent

        plugin = postgresql(
            host="localhost",
            database="test",
            user="test",
            password="test"
        )

        # Old style: use plugins parameter
        agent = SubstrateAgent(
            name="test_agent",
            plugins=[plugin]
        )

        # Plugin should be in plugin_instances
        assert len(agent.plugin_instances) == 1
        assert agent.plugin_instances[0] == plugin

        # Can still access plugin directly
        assert agent.plugin_instances[0].config["database"] == "test"

    @pytest.mark.asyncio
    async def test_agent_direct_plugin_usage_in_handler(self):
        """Test using plugin directly in custom handler"""
        from daita.agents.substrate import SubstrateAgent

        plugin = postgresql(
            host="localhost",
            database="test",
            user="test",
            password="test"
        )

        # Mock query
        plugin.query = AsyncMock(return_value=[{"count": 42}])

        async def custom_handler(data, context, agent):
            # Access plugin directly (old way)
            db = agent.plugin_instances[0]
            result = await db.query("SELECT COUNT(*) as count FROM users")
            return {"user_count": result[0]["count"]}

        agent = SubstrateAgent(
            name="test_agent",
            plugins=[plugin],
            handlers={"count_users": custom_handler}
        )

        result = await agent.process("count_users", data={})

        # Result is wrapped by BaseAgent.process()
        assert "result" in result
        assert result["result"]["user_count"] == 42
        plugin.query.assert_called_once()


class TestPostgreSQLErrorHandling:
    """Test PostgreSQL plugin error handling"""

    @pytest.mark.asyncio
    async def test_query_error_handling(self):
        """Test that query errors are properly raised"""
        plugin = postgresql(
            host="localhost",
            database="test",
            user="test",
            password="test"
        )

        mock_conn = MagicMock()
        mock_conn.fetch = AsyncMock(side_effect=Exception("Database error"))

        plugin._pool = MagicMock()
        plugin._pool.acquire = MagicMock()
        plugin._pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        plugin._pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

        with pytest.raises(Exception, match="Database error"):
            await plugin.query("SELECT * FROM nonexistent")

    @pytest.mark.asyncio
    async def test_execute_error_handling(self):
        """Test that execute errors are properly raised"""
        plugin = postgresql(
            host="localhost",
            database="test",
            user="test",
            password="test"
        )

        mock_conn = MagicMock()
        mock_conn.execute = AsyncMock(side_effect=Exception("Constraint violation"))

        plugin._pool = MagicMock()
        plugin._pool.acquire = MagicMock()
        plugin._pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        plugin._pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

        with pytest.raises(Exception, match="Constraint violation"):
            await plugin.execute("INSERT INTO users (id) VALUES (1)")

    @pytest.mark.asyncio
    async def test_insert_many_empty_list(self):
        """Test insert_many with empty list"""
        plugin = postgresql(
            host="localhost",
            database="test",
            user="test",
            password="test"
        )

        result = await plugin.insert_many("users", [])

        assert result == 0


class TestPostgreSQLConfigurationOptions:
    """Test PostgreSQL configuration options"""

    def test_user_parameter_alias(self):
        """Test that 'user' parameter works as alias for 'username'"""
        plugin = postgresql(
            host="localhost",
            database="test",
            user="alice",
            password="secret"
        )

        assert "alice" in plugin.connection_string

    def test_username_parameter(self):
        """Test that 'username' parameter still works"""
        plugin = postgresql(
            host="localhost",
            database="test",
            username="bob",
            password="secret"
        )

        assert "bob" in plugin.connection_string

    def test_custom_pool_settings(self):
        """Test custom pool configuration"""
        plugin = postgresql(
            host="localhost",
            database="test",
            user="test",
            password="test",
            min_size=5,
            max_size=50,
            command_timeout=300
        )

        assert plugin.pool_config["min_size"] == 5
        assert plugin.pool_config["max_size"] == 50
        assert plugin.pool_config["command_timeout"] == 300

    def test_default_pool_settings(self):
        """Test default pool configuration"""
        plugin = postgresql(
            host="localhost",
            database="test",
            user="test",
            password="test"
        )

        assert plugin.pool_config["min_size"] == 1
        assert plugin.pool_config["max_size"] == 10
        assert plugin.pool_config["command_timeout"] == 60
