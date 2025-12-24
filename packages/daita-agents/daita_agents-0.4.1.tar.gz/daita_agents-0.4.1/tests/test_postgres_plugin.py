"""
Test suite for PostgreSQL Plugin - testing PostgreSQL database integration.

Simple tests to ensure the PostgreSQL plugin works correctly.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from daita.plugins.postgresql import PostgreSQLPlugin, postgresql


class TestPostgreSQLInitialization:
    """Test PostgreSQL plugin initialization."""
    
    def test_basic_initialization(self):
        """Test basic PostgreSQL plugin initialization."""
        plugin = PostgreSQLPlugin(
            host="localhost",
            port=5432,
            database="testdb",
            username="user",
            password="pass"
        )
        
        assert plugin.connection_string == "postgresql://user:pass@localhost:5432/testdb"
        assert plugin._pool is None
    
    def test_connection_string_override(self):
        """Test initialization with connection string."""
        conn_str = "postgresql://user:pass@localhost:5432/mydb"
        plugin = PostgreSQLPlugin(connection_string=conn_str)
        
        assert plugin.connection_string == conn_str
    
    def test_custom_configuration(self):
        """Test initialization with custom settings."""
        plugin = PostgreSQLPlugin(
            host="localhost",
            database="test",
            username="user",
            password="pass",
            min_size=2,
            max_size=20,
            command_timeout=120
        )
        
        assert plugin.pool_config['min_size'] == 2
        assert plugin.pool_config['max_size'] == 20
        assert plugin.pool_config['command_timeout'] == 120


class TestPostgreSQLConnection:
    """Test PostgreSQL connection management."""
    
    @pytest.mark.asyncio
    async def test_connect_disconnect(self):
        """Test connection and disconnection."""
        plugin = PostgreSQLPlugin(host="localhost", database="test", username="user", password="pass")
        
        # Fix: Patch the import at the point where it's used
        with patch('asyncpg.create_pool') as mock_create_pool:
            mock_pool = AsyncMock()
            
            # Make create_pool return a coroutine that resolves to mock_pool
            async def mock_create_pool_func(*args, **kwargs):
                return mock_pool
            
            mock_create_pool.side_effect = mock_create_pool_func
            
            # Test connect
            await plugin.connect()
            assert plugin._pool == mock_pool
            mock_create_pool.assert_called_once()
            
            # Test disconnect
            await plugin.disconnect()
            mock_pool.close.assert_called_once()
            assert plugin._pool is None
    
    @pytest.mark.asyncio
    async def test_connect_import_error(self):
        """Test connection with missing asyncpg."""
        plugin = PostgreSQLPlugin(host="localhost", database="test", username="user", password="pass")
        
        with patch('builtins.__import__', side_effect=ImportError):
            with pytest.raises(RuntimeError, match="asyncpg not installed"):
                await plugin.connect()
    
    @pytest.mark.asyncio
    async def test_connect_failure(self):
        """Test connection failure."""
        plugin = PostgreSQLPlugin(host="localhost", database="test", username="user", password="pass")
        
        # Fix: Patch the import at the point where it's used
        with patch('asyncpg.create_pool') as mock_create_pool:
            async def mock_create_pool_func(*args, **kwargs):
                raise Exception("Connection failed")
            
            mock_create_pool.side_effect = mock_create_pool_func
            
            with pytest.raises(RuntimeError, match="Failed to connect to PostgreSQL"):
                await plugin.connect()


class MockAsyncContextManager:
    """Helper class to properly mock async context managers."""
    
    def __init__(self, return_value):
        self.return_value = return_value
    
    async def __aenter__(self):
        return self.return_value
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return None


def create_mock_pool_with_acquire(mock_conn):
    """Create a properly mocked pool with working acquire method."""
    mock_pool = MagicMock()  # Use regular MagicMock, not AsyncMock
    
    # Make acquire return our async context manager
    mock_pool.acquire.return_value = MockAsyncContextManager(mock_conn)
    
    # Add other methods that might be called
    mock_pool.close = MagicMock()
    
    return mock_pool


class MockRow:
    """Mock row that behaves like asyncpg.Record and supports dict() conversion."""
    
    def __init__(self, data):
        self._data = data
    
    def __getitem__(self, key):
        return self._data[key]
    
    def __iter__(self):
        """Support iteration for dict() conversion."""
        return iter(self._data.items())
    
    def keys(self):
        return self._data.keys()
    
    def values(self):
        return self._data.values()
    
    def items(self):
        return self._data.items()


class TestPostgreSQLOperations:
    """Test PostgreSQL database operations."""
    
    @pytest.mark.asyncio
    async def test_query(self):
        """Test query execution."""
        plugin = PostgreSQLPlugin(host="localhost", database="test", username="user", password="pass")
        
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = [
            MockRow({'id': 1, 'name': 'John', 'age': 30}),
            MockRow({'id': 2, 'name': 'Jane', 'age': 25})
        ]
        
        # Fix: Use the helper function to create a proper mock pool
        mock_pool = create_mock_pool_with_acquire(mock_conn)
        plugin._pool = mock_pool
        
        # Test query
        result = await plugin.query("SELECT * FROM users")
        
        expected = [
            {'id': 1, 'name': 'John', 'age': 30},
            {'id': 2, 'name': 'Jane', 'age': 25}
        ]
        assert result == expected
        mock_conn.fetch.assert_called_with("SELECT * FROM users")
    
    @pytest.mark.asyncio
    async def test_query_with_params(self):
        """Test query with parameters."""
        plugin = PostgreSQLPlugin(host="localhost", database="test", username="user", password="pass")
        
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = [MockRow({'id': 1, 'name': 'John', 'age': 30})]
        
        # Fix: Use the helper function to create a proper mock pool
        mock_pool = create_mock_pool_with_acquire(mock_conn)
        plugin._pool = mock_pool
        
        result = await plugin.query("SELECT * FROM users WHERE age > $1", [25])
        
        assert len(result) == 1
        assert result[0]['name'] == 'John'
        mock_conn.fetch.assert_called_with("SELECT * FROM users WHERE age > $1", 25)
    
    @pytest.mark.asyncio
    async def test_execute(self):
        """Test execute operation."""
        plugin = PostgreSQLPlugin(host="localhost", database="test", username="user", password="pass")
        
        mock_conn = AsyncMock()
        mock_conn.execute.return_value = "DELETE 3"  # PostgreSQL result format
        
        # Fix: Use the helper function to create a proper mock pool
        mock_pool = create_mock_pool_with_acquire(mock_conn)
        plugin._pool = mock_pool
        
        result = await plugin.execute("DELETE FROM users WHERE age < $1", [20])
        
        assert result == 3  # Extracted from "DELETE 3"
        mock_conn.execute.assert_called_with("DELETE FROM users WHERE age < $1", 20)
    
    @pytest.mark.asyncio
    async def test_insert_many(self):
        """Test bulk insert."""
        plugin = PostgreSQLPlugin(host="localhost", database="test", username="user", password="pass")
        
        mock_conn = AsyncMock()
        
        # Fix: Use the helper function to create a proper mock pool
        mock_pool = create_mock_pool_with_acquire(mock_conn)
        plugin._pool = mock_pool
        
        data = [
            {"name": "John", "age": 30},
            {"name": "Jane", "age": 25}
        ]
        
        result = await plugin.insert_many("users", data)
        
        assert result == 2
        mock_conn.executemany.assert_called_once()
        
        # Check that SQL was generated correctly
        call_args = mock_conn.executemany.call_args
        sql = call_args[0][0]
        assert "INSERT INTO users" in sql
        assert "name, age" in sql
        assert "$1, $2" in sql
    
    @pytest.mark.asyncio
    async def test_insert_many_empty(self):
        """Test bulk insert with empty data."""
        plugin = PostgreSQLPlugin(host="localhost", database="test", username="user", password="pass")
        
        result = await plugin.insert_many("users", [])
        assert result == 0
    
    @pytest.mark.asyncio
    async def test_tables(self):
        """Test tables listing."""
        plugin = PostgreSQLPlugin(host="localhost", database="test", username="user", password="pass")
        
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = [
            MockRow({'table_name': 'users'}),
            MockRow({'table_name': 'products'}),
            MockRow({'table_name': 'orders'})
        ]
        
        # Fix: Use the helper function to create a proper mock pool
        mock_pool = create_mock_pool_with_acquire(mock_conn)
        plugin._pool = mock_pool
        
        tables = await plugin.tables()
        
        assert tables == ['users', 'products', 'orders']
        
        # Verify SQL query
        call_args = mock_conn.fetch.call_args
        sql = call_args[0][0]
        assert "information_schema.tables" in sql
        assert "table_schema = 'public'" in sql


class TestPostgreSQLContextManager:
    """Test PostgreSQL context manager."""
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test PostgreSQL as context manager."""
        plugin = PostgreSQLPlugin(host="localhost", database="test", username="user", password="pass")
        
        # Fix: Patch the import at the point where it's used
        with patch('asyncpg.create_pool') as mock_create_pool:
            mock_pool = AsyncMock()
            
            # Make create_pool return a coroutine that resolves to mock_pool
            async def mock_create_pool_func(*args, **kwargs):
                return mock_pool
            
            mock_create_pool.side_effect = mock_create_pool_func
            
            async with plugin as pg:
                assert pg == plugin
                assert plugin._pool == mock_pool
            
            mock_pool.close.assert_called_once()


class TestPostgreSQLFactory:
    """Test PostgreSQL factory function."""
    
    def test_factory_function(self):
        """Test postgresql factory function."""
        plugin = postgresql(
            host="localhost",
            database="testdb",
            username="user",
            password="pass"
        )
        
        assert isinstance(plugin, PostgreSQLPlugin)
        assert "localhost" in plugin.connection_string
        assert "testdb" in plugin.connection_string


class TestPostgreSQLEdgeCases:
    """Test some basic edge cases."""
    
    @pytest.mark.asyncio
    async def test_query_empty_result(self):
        """Test query with empty result."""
        plugin = PostgreSQLPlugin(host="localhost", database="test", username="user", password="pass")
        
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = []
        
        # Fix: Use the helper function to create a proper mock pool
        mock_pool = create_mock_pool_with_acquire(mock_conn)
        plugin._pool = mock_pool
        
        result = await plugin.query("SELECT * FROM empty_table")
        assert result == []
    
    @pytest.mark.asyncio
    async def test_execute_no_result(self):
        """Test execute with no result string."""
        plugin = PostgreSQLPlugin(host="localhost", database="test", username="user", password="pass")
        
        mock_conn = AsyncMock()
        mock_conn.execute.return_value = ""  # Empty result
        
        # Fix: Use the helper function to create a proper mock pool
        mock_pool = create_mock_pool_with_acquire(mock_conn)
        plugin._pool = mock_pool
        
        result = await plugin.execute("CREATE TABLE test (id INT)")
        assert result == 0
    
    @pytest.mark.asyncio
    async def test_auto_connect_on_query(self):
        """Test that query auto-connects if not connected."""
        plugin = PostgreSQLPlugin(host="localhost", database="test", username="user", password="pass")
        
        # Fix: Patch the import at the point where it's used
        with patch('asyncpg.create_pool') as mock_create_pool:
            mock_conn = AsyncMock()
            mock_conn.fetch.return_value = []
            
            # Create proper mock pool
            mock_pool = create_mock_pool_with_acquire(mock_conn)
            
            # Make create_pool return a coroutine that resolves to mock_pool
            async def mock_create_pool_func(*args, **kwargs):
                return mock_pool
            
            mock_create_pool.side_effect = mock_create_pool_func
            
            # Query should auto-connect
            await plugin.query("SELECT 1")
            
            # Verify create_pool was called (auto-connect happened)
            mock_create_pool.assert_called_once()
            assert plugin._pool == mock_pool


if __name__ == "__main__":
    pytest.main([__file__, "-v"])