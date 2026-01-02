"""
Test suite for Plugin System - testing the overall plugin architecture and access patterns.

Tests cover:
- PluginAccess class functionality
- Plugin factory functions consistency
- Multi-database integration patterns
- Plugin configuration patterns
- Plugin error recovery
- Integration workflow patterns
"""
import pytest
import asyncio
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from contextlib import asynccontextmanager

# Plugin imports
from daita.plugins import (
    PluginAccess,
    PostgreSQLPlugin, postgresql,
    MySQLPlugin, mysql,
    MongoDBPlugin, mongodb,
    RESTPlugin, rest
)


class TestPluginAccess:
    """Test the plugin access system for SDK integration."""
    
    def test_plugin_access_initialization(self):
        """Test PluginAccess class initialization."""
        plugins = PluginAccess()
        
        # Should have methods for all plugins
        assert hasattr(plugins, 'postgresql')
        assert hasattr(plugins, 'mysql')
        assert hasattr(plugins, 'mongodb')
        assert hasattr(plugins, 'rest')
        assert callable(plugins.postgresql)
        assert callable(plugins.mysql)
        assert callable(plugins.mongodb)
        assert callable(plugins.rest)
    
    def test_plugin_creation_through_access(self):
        """Test creating plugins through PluginAccess."""
        plugins = PluginAccess()
        
        # Test PostgreSQL
        pg = plugins.postgresql(host="localhost", database="test")
        assert isinstance(pg, PostgreSQLPlugin)
        assert "localhost" in pg.connection_string
        
        # Test MySQL
        my = plugins.mysql(host="localhost", database="test")
        assert isinstance(my, MySQLPlugin)
        assert "localhost" in my.connection_string
        
        # Test MongoDB
        mongo = plugins.mongodb(host="localhost", database="test")
        assert isinstance(mongo, MongoDBPlugin)
        assert mongo.database_name == "test"
        
        # Test REST
        api = plugins.rest(base_url="https://api.example.com")
        assert isinstance(api, RESTPlugin)
        assert api.base_url == "https://api.example.com"


class TestPluginFactoryConsistency:
    """Test that all plugin factories work consistently."""
    
    def test_plugin_factory_functions(self):
        """Test that all plugin factory functions work consistently."""
        # Test all factory functions
        pg = postgresql(host="localhost", database="test", username="user", password="pass")
        my = mysql(host="localhost", database="test", username="user", password="pass")
        mongo = mongodb(host="localhost", database="test")
        api = rest(base_url="https://api.example.com")
        
        # All should return correct types
        assert isinstance(pg, PostgreSQLPlugin)
        assert isinstance(my, MySQLPlugin)
        assert isinstance(mongo, MongoDBPlugin)
        assert isinstance(api, RESTPlugin)
    
    def test_plugin_interface_consistency(self):
        """Test that all plugins have consistent interfaces."""
        pg = postgresql(host="localhost", database="test", username="user", password="pass")
        my = mysql(host="localhost", database="test", username="user", password="pass")
        mongo = mongodb(host="localhost", database="test")
        api = rest(base_url="https://api.example.com")
        
        # All should have consistent interface
        plugins = [pg, my, mongo, api]
        for plugin in plugins:
            # Should have connect/disconnect for database plugins
            if hasattr(plugin, 'connect'):
                assert callable(plugin.connect)
                assert callable(plugin.disconnect)
            
            # Should work as context manager
            assert hasattr(plugin, '__aenter__')
            assert hasattr(plugin, '__aexit__')


class TestPluginConfigurationPatterns:
    """Test common plugin configuration patterns."""
    
    def test_environment_based_configuration(self):
        """Test plugin configuration with environment variables."""
        # Configuration with environment variables (simulated)
        with patch.dict(os.environ, {
            'DB_HOST': 'prod-db.example.com',
            'DB_USER': 'app_user',
            'DB_PASS': 'secret_pass',
            'API_KEY': 'prod-api-key'
        }):
            # Database from environment
            pg = postgresql(
                host=os.environ.get('DB_HOST', 'localhost'),
                username=os.environ.get('DB_USER'),
                password=os.environ.get('DB_PASS'),
                database='production'
            )
            
            assert 'prod-db.example.com' in pg.connection_string
            assert 'app_user' in pg.connection_string
            
            # API from environment
            api = rest(
                base_url="https://api.production.com",
                api_key=os.environ.get('API_KEY')
            )
            
            assert api.api_key == 'prod-api-key'
    
    def test_connection_string_configuration(self):
        """Test plugin configuration with connection strings."""
        # PostgreSQL with connection string
        pg_conn_str = "postgresql://user:pass@localhost:5432/mydb"
        pg = postgresql(connection_string=pg_conn_str)
        assert pg.connection_string == pg_conn_str
        
        # MySQL with connection string
        my_conn_str = "mysql://user:pass@localhost:3306/mydb"
        my = mysql(connection_string=my_conn_str)
        assert my.connection_string == my_conn_str
        
        # MongoDB with connection string
        mongo_conn_str = "mongodb://user:pass@localhost:27017/mydb"
        mongo = mongodb(connection_string=mongo_conn_str, database="mydb")
        assert mongo.connection_string == mongo_conn_str
    
    def test_custom_configuration_options(self):
        """Test plugins with custom configuration options."""
        # PostgreSQL with custom pool settings
        pg = postgresql(
            host="localhost",
            database="test",
            username="user",
            password="pass",
            min_size=2,
            max_size=20,
            command_timeout=120
        )
        assert pg.pool_config['min_size'] == 2
        assert pg.pool_config['max_size'] == 20
        assert pg.pool_config['command_timeout'] == 120
        
        # MySQL with custom settings
        my = mysql(
            host="localhost",
            database="test",
            username="user",
            password="pass",
            min_size=3,
            max_size=15,
            charset="latin1",
            autocommit=False
        )
        assert my.pool_config['minsize'] == 3
        assert my.pool_config['maxsize'] == 15
        assert my.pool_config['charset'] == "latin1"
        assert my.pool_config['autocommit'] is False
        
        # MongoDB with custom settings
        mongo = mongodb(
            host="localhost",
            database="test",
            max_pool_size=20,
            min_pool_size=5,
            server_timeout=60000
        )
        assert mongo.client_config['maxPoolSize'] == 20
        assert mongo.client_config['minPoolSize'] == 5
        assert mongo.client_config['serverSelectionTimeoutMS'] == 60000
        
        # REST API with custom settings
        api = rest(
            base_url="https://api.example.com",
            timeout=60,
            headers={"User-Agent": "MyApp/1.0"}
        )
        assert api.timeout == 60
        assert api.default_headers["User-Agent"] == "MyApp/1.0"


class TestMultiDatabaseIntegration:
    """Test using multiple database plugins together."""
    
    @pytest.mark.asyncio
    async def test_multi_database_workflow(self):
        """Test using multiple database plugins in a workflow."""
        # Initialize multiple database plugins
        pg = postgresql(host="localhost", database="analytics", username="user", password="pass")
        mongo = mongodb(host="localhost", database="logs")
        
        # Mock PostgreSQL with proper async context manager
        mock_conn = AsyncMock()
        
        # Mock row objects for PostgreSQL
        class MockRow:
            def __init__(self, data):
                self._data = data
            
            def __getitem__(self, key):
                return self._data[key]
            
            def keys(self):
                return self._data.keys()
            
            def values(self):
                return self._data.values()
            
            def items(self):
                return self._data.items()
        
        mock_conn.fetch.return_value = [
            MockRow({'id': 1, 'event': 'login', 'user_id': 123}),
            MockRow({'id': 2, 'event': 'logout', 'user_id': 123})
        ]
        
        # Create proper async context manager for pool.acquire()
        @asynccontextmanager
        async def mock_acquire():
            yield mock_conn
        
        mock_pool = AsyncMock()
        mock_pool.acquire = mock_acquire
        
        # Set PostgreSQL mock directly
        pg._pool = mock_pool
        
        # Mock MongoDB
        mock_collection = AsyncMock()
        mock_collection.insert_many.return_value = AsyncMock(inserted_ids=["obj1", "obj2"])
        mock_db = AsyncMock()
        mock_db.__getitem__.return_value = mock_collection
        
        # Set MongoDB mocks directly
        mongo._client = AsyncMock()  # Set to non-None to avoid connect()
        mongo._db = mock_db
        
        # Simulate data transfer between databases
        # Read from PostgreSQL
        analytics_data = await pg.query("SELECT * FROM events WHERE user_id = $1", [123])
        
        # Transform and insert to MongoDB
        log_documents = [
            {"postgres_id": row['id'], "event_type": row['event'], "user": row['user_id']}
            for row in analytics_data
        ]
        
        result = await mongo.insert_many("event_logs", log_documents)
        assert len(result) == 2
    
    @pytest.mark.asyncio
    async def test_database_api_integration(self):
        """Test database and API plugin integration."""
        pg = postgresql(host="localhost", database="test", username="user", password="pass")
        api = rest(base_url="https://api.example.com", api_key="test-key")
        
        # Mock PostgreSQL
        mock_conn = AsyncMock()
        
        class MockRow:
            def __init__(self, data):
                self._data = data
            def __getitem__(self, key):
                return self._data[key]
            def keys(self):
                return self._data.keys()
            def values(self):
                return self._data.values()
            def items(self):
                return self._data.items()
        
        mock_conn.fetch.return_value = [MockRow({'id': 1, 'name': 'John', 'email': 'john@example.com'})]
        
        # Create proper async context manager for pool.acquire()
        @asynccontextmanager
        async def mock_acquire():
            yield mock_conn
        
        mock_pool = AsyncMock()
        mock_pool.acquire = mock_acquire
        pg._pool = mock_pool
        
        # Mock API with proper async context manager
        mock_response = AsyncMock()
        mock_response.status = 201
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {"id": "api_123", "status": "created"}
        
        @asynccontextmanager
        async def mock_request(*args, **kwargs):
            yield mock_response
        
        mock_session = AsyncMock()
        mock_session.request = mock_request
        api._session = mock_session
        
        # Simulate workflow: read from DB, send to API
        users = await pg.query("SELECT * FROM users WHERE id = $1", [1])
        user = users[0]
        
        api_result = await api.post("/users", json_data={
            "name": user['name'],
            "email": user['email']
        })
        
        assert api_result["status"] == "created"


class TestPluginErrorRecovery:
    """Test plugin error handling and recovery patterns."""
    
    @pytest.mark.asyncio
    async def test_connection_error_recovery(self):
        """Test plugin behavior on connection errors."""
        pg = postgresql(host="localhost", database="test", username="user", password="pass")
        
        # Test connection failure
        with patch('asyncpg.create_pool', side_effect=Exception("Connection refused")):
            with pytest.raises(RuntimeError) as exc_info:
                await pg.connect()
            
            assert "Failed to connect to PostgreSQL" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_api_request_retry_pattern(self):
        """Test API plugin error recovery patterns."""
        api = rest(base_url="https://api.example.com")
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session
            
            # Simulate connection error then success
            call_count = 0
            
            # Create a mock that properly handles the async context manager protocol
            class MockRequest:
                def __init__(self, should_fail=False):
                    self.should_fail = should_fail
                
                def __call__(self, *args, **kwargs):
                    return self
                
                async def __aenter__(self):
                    nonlocal call_count
                    call_count += 1
                    
                    if call_count == 1:
                        # First call fails
                        raise Exception("Connection failed")
                    else:
                        # Second call succeeds
                        success_response = AsyncMock()
                        success_response.status = 200
                        success_response.headers = {'content-type': 'application/json'}
                        success_response.json.return_value = {"status": "ok"}
                        return success_response
                
                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    return None
            
            mock_session.request = MockRequest()
            
            # First call should fail
            with pytest.raises(RuntimeError):
                await api.get("/status")
            
            # Reset for second call
            mock_session.request = MockRequest()
            
            # Second call should succeed
            result = await api.get("/status")
            assert result["status"] == "ok"
    
    @pytest.mark.asyncio
    async def test_import_error_handling(self):
        """Test plugin behavior when required packages are missing."""
        pg = postgresql(host="localhost", database="test", username="user", password="pass")
        my = mysql(host="localhost", database="test", username="user", password="pass")
        mongo = mongodb(host="localhost", database="test")
        api = rest(base_url="https://api.example.com")
        
        # Test PostgreSQL import error
        with patch('builtins.__import__', side_effect=ImportError):
            with pytest.raises(RuntimeError) as exc_info:
                await pg.connect()
            assert "asyncpg not installed" in str(exc_info.value)
        
        # Test MySQL import error
        with patch('builtins.__import__', side_effect=ImportError):
            with pytest.raises(RuntimeError) as exc_info:
                await my.connect()
            assert "aiomysql not installed" in str(exc_info.value)
        
        # Test MongoDB import error
        with patch('builtins.__import__', side_effect=ImportError):
            with pytest.raises(RuntimeError) as exc_info:
                await mongo.connect()
            assert "motor not installed" in str(exc_info.value)
        
        # Test REST API import error
        with patch('builtins.__import__', side_effect=ImportError):
            with pytest.raises(RuntimeError) as exc_info:
                await api.connect()
            assert "aiohttp not installed" in str(exc_info.value)


class TestPluginIntegrationWorkflows:
    """Test plugin integration patterns and real-world usage."""
    
    @pytest.mark.asyncio
    async def test_database_workflow_integration(self):
        """Test database plugins in a typical workflow."""
        # Test PostgreSQL workflow
        pg = postgresql(host="localhost", database="test", username="user", password="pass")
        
        # Create async mock that can be properly awaited
        async def mock_create_pool(*args, **kwargs):
            mock_pool = AsyncMock()
            
            # Create proper async context manager for pool.acquire()
            @asynccontextmanager
            async def mock_acquire():
                mock_conn = AsyncMock()
                
                # Mock row objects
                class MockRow:
                    def __init__(self, data):
                        self._data = data
                    
                    def __getitem__(self, key):
                        return self._data[key]
                    
                    def keys(self):
                        return self._data.keys()
                    
                    def values(self):
                        return self._data.values()
                    
                    def items(self):
                        return self._data.items()
                
                mock_conn.fetch.return_value = [MockRow({'count': 5})]
                mock_conn.execute.return_value = "INSERT 0 1"
                yield mock_conn
            
            mock_pool.acquire = mock_acquire
            return mock_pool
        
        with patch('asyncpg.create_pool', side_effect=mock_create_pool):
            async with pg:
                # Simulate typical workflow: count, query, insert
                count_result = await pg.query("SELECT COUNT(*) as count FROM users")
                assert count_result[0]['count'] == 5
                
                # Insert new data
                insert_result = await pg.execute("INSERT INTO users (name) VALUES ($1)", ["Bob"])
                assert insert_result == 1
    
    @pytest.mark.asyncio
    async def test_api_workflow_integration(self):
        """Test REST API plugin in a typical workflow."""
        api = rest(base_url="https://api.example.com", api_key="test-key")
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session
            
            # Mock API responses
            def create_mock_response(status, data):
                response = AsyncMock()
                response.status = status
                response.headers = {'content-type': 'application/json'}
                response.json.return_value = data
                return response
            
            # Set up multiple responses for different calls
            responses = [
                create_mock_response(200, {"users": [{"id": 1, "name": "John"}]}),
                create_mock_response(201, {"id": 2, "name": "Jane", "created": True}),
                create_mock_response(200, {"id": 1, "name": "John Updated"})
            ]
            
            # Create a mock request handler that properly implements async context manager
            response_iter = iter(responses)
            
            class MockRequestHandler:
                def __call__(self, *args, **kwargs):
                    return self
                
                async def __aenter__(self):
                    return next(response_iter)
                
                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    return None
            
            mock_session.request = MockRequestHandler()
            
            async with api:
                # Simulate typical API workflow: GET, POST, PUT
                users = await api.get("/users")
                assert len(users["users"]) == 1
                
                # Reset iterator for next calls
                response_iter = iter([
                    create_mock_response(201, {"id": 2, "name": "Jane", "created": True}),
                    create_mock_response(200, {"id": 1, "name": "John Updated"})
                ])
                
                new_user = await api.post("/users", json_data={"name": "Jane"})
                assert new_user["created"] is True
                
                updated_user = await api.put("/users/1", json_data={"name": "John Updated"})
                assert updated_user["name"] == "John Updated"


class TestPluginEdgeCases:
    """Test plugin edge cases and error conditions."""
    
    def test_plugin_initialization_edge_cases(self):
        """Test plugin initialization with edge case parameters."""
        # Empty base URL for REST - should now raise ValueError
        with pytest.raises(ValueError):
            rest(base_url="")
        
        with pytest.raises(ValueError):
            rest(base_url="   ")  # Whitespace only
        
        # Invalid port numbers
        pg = postgresql(host="localhost", port=99999, database="test", username="user", password="pass")
        # Should not error during initialization, only during connection
        assert pg.connection_string is not None
        
        # Very long connection strings
        long_host = "very-long-hostname-" + "x" * 100 + ".example.com"
        pg_long = postgresql(host=long_host, database="test", username="user", password="pass")
        assert long_host in pg_long.connection_string
    
    def test_plugin_configuration_validation(self):
        """Test plugin configuration validation."""
        # Test that plugins accept various configuration combinations
        
        # PostgreSQL with minimal config
        pg_minimal = postgresql(host="localhost", database="test", username="user", password="pass")
        assert pg_minimal.connection_string is not None
        
        # MySQL with all options
        my_full = mysql(
            host="remote.db.com",
            port=3307,
            database="production",
            username="app_user",
            password="complex_pass123!",
            min_size=5,
            max_size=50,
            charset="utf8mb4",
            autocommit=True
        )
        assert "remote.db.com" in my_full.connection_string
        assert my_full.port == 3307
        
        # MongoDB with authentication
        mongo_auth = mongodb(
            host="cluster.mongodb.com",
            port=27017,
            database="app_data",
            username="mongo_user",
            password="mongo_pass"
        )
        assert "mongo_user" in mongo_auth.connection_string
        
        # REST API with custom auth
        api_custom = rest(
            base_url="https://custom-api.company.com/v2",
            api_key="sk-custom-key-12345",
            auth_header="X-Custom-Auth",
            auth_prefix="CustomToken",
            timeout=120
        )
        assert api_custom.timeout == 120
        assert "X-Custom-Auth" in api_custom.default_headers


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])