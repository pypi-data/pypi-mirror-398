"""
Test suite for MySQL Plugin - testing MySQL database integration.

Simple tests to ensure the MySQL plugin works correctly.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from daita.plugins.mysql import MySQLPlugin, mysql


class TestMySQLInitialization:
    """Test MySQL plugin initialization."""
    
    def test_basic_initialization(self):
        """Test basic MySQL plugin initialization."""
        plugin = MySQLPlugin(
            host="localhost",
            port=3306,
            database="testdb",
            username="user",
            password="pass"
        )
        
        assert plugin.connection_string == "mysql://user:pass@localhost:3306/testdb"
        assert plugin.host == "localhost"
        assert plugin.port == 3306
        assert plugin.user == "user"
        assert plugin.password == "pass"
        assert plugin.db == "testdb"
        assert plugin._pool is None
    
    def test_connection_string_override(self):
        """Test initialization with connection string."""
        conn_str = "mysql://user:pass@localhost:3306/mydb"
        plugin = MySQLPlugin(connection_string=conn_str)
        
        assert plugin.connection_string == conn_str
    
    def test_custom_configuration(self):
        """Test initialization with custom settings."""
        plugin = MySQLPlugin(
            host="localhost",
            database="test",
            username="user",
            password="pass",
            min_size=2,
            max_size=20,
            charset="latin1"
        )
        
        assert plugin.pool_config['minsize'] == 2
        assert plugin.pool_config['maxsize'] == 20
        assert plugin.pool_config['charset'] == "latin1"


class TestMySQLConnection:
    """Test MySQL connection management."""
    
    @pytest.mark.asyncio
    async def test_connect_disconnect(self):
        """Test connection and disconnection."""
        plugin = MySQLPlugin(host="localhost", database="test", username="user", password="pass")
        
        with patch('aiomysql.create_pool') as mock_create_pool:
            mock_pool = MagicMock()  # Use MagicMock for the pool itself
            mock_pool.close = MagicMock()
            mock_pool.wait_closed = AsyncMock()  # wait_closed is async
            
            # Fix: create_pool is async, so it should return a coroutine that resolves to the pool
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
            mock_pool.wait_closed.assert_called_once()
            assert plugin._pool is None
    
    @pytest.mark.asyncio
    async def test_connect_import_error(self):
        """Test connection with missing aiomysql."""
        plugin = MySQLPlugin(host="localhost", database="test", username="user", password="pass")
        
        with patch('builtins.__import__', side_effect=ImportError):
            with pytest.raises(RuntimeError, match="aiomysql not installed"):
                await plugin.connect()
    
    @pytest.mark.asyncio
    async def test_connect_failure(self):
        """Test connection failure."""
        plugin = MySQLPlugin(host="localhost", database="test", username="user", password="pass")
        
        with patch('aiomysql.create_pool', side_effect=Exception("Connection failed")):
            with pytest.raises(RuntimeError, match="Failed to connect to MySQL"):
                await plugin.connect()


class TestMySQLOperations:
    """Test MySQL database operations."""
    
    @pytest.mark.asyncio
    async def test_query(self):
        """Test query execution."""
        plugin = MySQLPlugin(host="localhost", database="test", username="user", password="pass")
        
        # Mock cursor and connection
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = [
            (1, 'John', 30),
            (2, 'Jane', 25)
        ]
        mock_cursor.description = [('id', None), ('name', None), ('age', None)]
        
        mock_conn = MagicMock()  # Use MagicMock for connection
        # cursor() returns an async context manager
        mock_cursor_cm = AsyncMock()
        mock_cursor_cm.__aenter__ = AsyncMock(return_value=mock_cursor)
        mock_cursor_cm.__aexit__ = AsyncMock(return_value=None)
        mock_conn.cursor.return_value = mock_cursor_cm
        
        # Use MagicMock for pool since acquire() is not async - it returns an async context manager
        mock_pool = MagicMock()
        mock_acquire_cm = AsyncMock()
        mock_acquire_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_acquire_cm.__aexit__ = AsyncMock(return_value=None)
        mock_pool.acquire.return_value = mock_acquire_cm
        
        plugin._pool = mock_pool
        
        # Test query
        result = await plugin.query("SELECT * FROM users")
        
        expected = [
            {'id': 1, 'name': 'John', 'age': 30},
            {'id': 2, 'name': 'Jane', 'age': 25}
        ]
        assert result == expected
        mock_cursor.execute.assert_called_with("SELECT * FROM users")
    
    @pytest.mark.asyncio
    async def test_query_with_params(self):
        """Test query with parameters."""
        plugin = MySQLPlugin(host="localhost", database="test", username="user", password="pass")
        
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = [(1, 'John', 30)]
        mock_cursor.description = [('id', None), ('name', None), ('age', None)]
        
        mock_conn = MagicMock()
        mock_cursor_cm = AsyncMock()
        mock_cursor_cm.__aenter__ = AsyncMock(return_value=mock_cursor)
        mock_cursor_cm.__aexit__ = AsyncMock(return_value=None)
        mock_conn.cursor.return_value = mock_cursor_cm
        
        mock_pool = MagicMock()
        mock_acquire_cm = AsyncMock()
        mock_acquire_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_acquire_cm.__aexit__ = AsyncMock(return_value=None)
        mock_pool.acquire.return_value = mock_acquire_cm
        
        plugin._pool = mock_pool
        
        result = await plugin.query("SELECT * FROM users WHERE age > %s", [25])
        
        assert len(result) == 1
        assert result[0]['name'] == 'John'
        mock_cursor.execute.assert_called_with("SELECT * FROM users WHERE age > %s", [25])
    
    @pytest.mark.asyncio
    async def test_execute(self):
        """Test execute operation."""
        plugin = MySQLPlugin(host="localhost", database="test", username="user", password="pass")
        
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 3
        
        mock_conn = MagicMock()
        mock_cursor_cm = AsyncMock()
        mock_cursor_cm.__aenter__ = AsyncMock(return_value=mock_cursor)
        mock_cursor_cm.__aexit__ = AsyncMock(return_value=None)
        mock_conn.cursor.return_value = mock_cursor_cm
        
        mock_pool = MagicMock()
        mock_acquire_cm = AsyncMock()
        mock_acquire_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_acquire_cm.__aexit__ = AsyncMock(return_value=None)
        mock_pool.acquire.return_value = mock_acquire_cm
        
        plugin._pool = mock_pool
        
        result = await plugin.execute("DELETE FROM users WHERE age < %s", [20])
        
        assert result == 3
        mock_cursor.execute.assert_called_with("DELETE FROM users WHERE age < %s", [20])
    
    @pytest.mark.asyncio
    async def test_insert_many(self):
        """Test bulk insert."""
        plugin = MySQLPlugin(host="localhost", database="test", username="user", password="pass")
        
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 2
        
        mock_conn = MagicMock()
        mock_cursor_cm = AsyncMock()
        mock_cursor_cm.__aenter__ = AsyncMock(return_value=mock_cursor)
        mock_cursor_cm.__aexit__ = AsyncMock(return_value=None)
        mock_conn.cursor.return_value = mock_cursor_cm
        
        mock_pool = MagicMock()
        mock_acquire_cm = AsyncMock()
        mock_acquire_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_acquire_cm.__aexit__ = AsyncMock(return_value=None)
        mock_pool.acquire.return_value = mock_acquire_cm
        
        plugin._pool = mock_pool
        
        data = [
            {"name": "John", "age": 30},
            {"name": "Jane", "age": 25}
        ]
        
        result = await plugin.insert_many("users", data)
        
        assert result == 2
        mock_cursor.executemany.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_insert_many_empty(self):
        """Test bulk insert with empty data."""
        plugin = MySQLPlugin(host="localhost", database="test", username="user", password="pass")
        
        result = await plugin.insert_many("users", [])
        assert result == 0
    
    @pytest.mark.asyncio
    async def test_tables(self):
        """Test tables listing."""
        plugin = MySQLPlugin(host="localhost", database="test", username="user", password="pass")
        
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = [('users',), ('products',), ('orders',)]
        mock_cursor.description = [('table_name', None)]
        
        mock_conn = MagicMock()
        mock_cursor_cm = AsyncMock()
        mock_cursor_cm.__aenter__ = AsyncMock(return_value=mock_cursor)
        mock_cursor_cm.__aexit__ = AsyncMock(return_value=None)
        mock_conn.cursor.return_value = mock_cursor_cm
        
        mock_pool = MagicMock()
        mock_acquire_cm = AsyncMock()
        mock_acquire_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_acquire_cm.__aexit__ = AsyncMock(return_value=None)
        mock_pool.acquire.return_value = mock_acquire_cm
        
        plugin._pool = mock_pool
        
        tables = await plugin.tables()
        
        assert tables == ['users', 'products', 'orders']
    
    @pytest.mark.asyncio
    async def test_describe(self):
        """Test table description."""
        plugin = MySQLPlugin(host="localhost", database="test", username="user", password="pass")
        
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = [
            ('id', 'int', 'NO', None, 'int(11)'),
            ('name', 'varchar', 'YES', None, 'varchar(255)')
        ]
        mock_cursor.description = [
            ('column_name', None), ('data_type', None), ('is_nullable', None),
            ('column_default', None), ('column_type', None)
        ]
        
        mock_conn = MagicMock()
        mock_cursor_cm = AsyncMock()
        mock_cursor_cm.__aenter__ = AsyncMock(return_value=mock_cursor)
        mock_cursor_cm.__aexit__ = AsyncMock(return_value=None)
        mock_conn.cursor.return_value = mock_cursor_cm
        
        mock_pool = MagicMock()
        mock_acquire_cm = AsyncMock()
        mock_acquire_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_acquire_cm.__aexit__ = AsyncMock(return_value=None)
        mock_pool.acquire.return_value = mock_acquire_cm
        
        plugin._pool = mock_pool
        
        description = await plugin.describe("users")
        
        expected = [
            {'column_name': 'id', 'data_type': 'int', 'is_nullable': 'NO', 'column_default': None, 'column_type': 'int(11)'},
            {'column_name': 'name', 'data_type': 'varchar', 'is_nullable': 'YES', 'column_default': None, 'column_type': 'varchar(255)'}
        ]
        assert description == expected


class TestMySQLContextManager:
    """Test MySQL context manager."""
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test MySQL as context manager."""
        plugin = MySQLPlugin(host="localhost", database="test", username="user", password="pass")
        
        with patch('aiomysql.create_pool') as mock_create_pool:
            mock_pool = MagicMock()
            mock_pool.close = MagicMock()
            mock_pool.wait_closed = AsyncMock()
            
            # Fix: create_pool should return a coroutine
            async def mock_create_pool_func(*args, **kwargs):
                return mock_pool
            
            mock_create_pool.side_effect = mock_create_pool_func
            
            async with plugin as my:
                assert my == plugin
                assert plugin._pool == mock_pool
            
            mock_pool.close.assert_called_once()
            mock_pool.wait_closed.assert_called_once()


class TestMySQLFactory:
    """Test MySQL factory function."""
    
    def test_factory_function(self):
        """Test mysql factory function."""
        plugin = mysql(
            host="localhost",
            database="testdb",
            username="user",
            password="pass"
        )
        
        assert isinstance(plugin, MySQLPlugin)
        assert "localhost" in plugin.connection_string
        assert plugin.db == "testdb"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])