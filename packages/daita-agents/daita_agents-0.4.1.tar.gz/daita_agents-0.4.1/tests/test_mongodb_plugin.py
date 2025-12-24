"""
Test suite for MongoDB Plugin - testing MongoDB database integration.

Simple tests to ensure the MongoDB plugin works correctly.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from daita.plugins.mongodb import MongoDBPlugin, mongodb


class TestMongoDBInitialization:
    """Test MongoDB plugin initialization."""
    
    def test_basic_initialization(self):
        """Test basic MongoDB plugin initialization."""
        plugin = MongoDBPlugin(
            host="localhost",
            port=27017,
            database="testdb"
        )
        
        assert plugin.connection_string == "mongodb://localhost:27017/testdb"
        assert plugin.database_name == "testdb"
        assert plugin._client is None
        assert plugin._db is None
    
    def test_initialization_with_auth(self):
        """Test MongoDB initialization with authentication."""
        plugin = MongoDBPlugin(
            host="localhost",
            port=27017,
            database="testdb",
            username="user",
            password="pass"
        )
        
        assert plugin.connection_string == "mongodb://user:pass@localhost:27017/testdb"
        assert plugin.database_name == "testdb"
    
    def test_connection_string_override(self):
        """Test initialization with connection string."""
        conn_str = "mongodb://user:pass@localhost:27017/mydb"
        plugin = MongoDBPlugin(connection_string=conn_str, database="mydb")
        
        assert plugin.connection_string == conn_str
        assert plugin.database_name == "mydb"
    
    def test_custom_configuration(self):
        """Test initialization with custom settings."""
        plugin = MongoDBPlugin(
            host="localhost",
            database="test",
            max_pool_size=20,
            min_pool_size=5,
            server_timeout=60000
        )
        
        assert plugin.client_config['maxPoolSize'] == 20
        assert plugin.client_config['minPoolSize'] == 5
        assert plugin.client_config['serverSelectionTimeoutMS'] == 60000


class TestMongoDBConnection:
    """Test MongoDB connection management."""
    
    @pytest.mark.asyncio
    async def test_connect_disconnect(self):
        """Test connection and disconnection."""
        plugin = MongoDBPlugin(host="localhost", database="test")
        
        with patch('motor.motor_asyncio.AsyncIOMotorClient') as mock_client_class:
            mock_client = MagicMock()  # Use MagicMock for client
            mock_client.admin.command = AsyncMock(return_value={"ok": 1})  # ping response
            mock_client_class.return_value = mock_client
            
            mock_db = MagicMock()  # Use MagicMock for database
            mock_client.__getitem__.return_value = mock_db
            
            # Test connect
            await plugin.connect()
            assert plugin._client == mock_client
            assert plugin._db == mock_db
            mock_client.admin.command.assert_called_with('ping')
            
            # Test disconnect
            await plugin.disconnect()
            assert plugin._client is None
            assert plugin._db is None
    
    @pytest.mark.asyncio
    async def test_connect_import_error(self):
        """Test connection with missing motor."""
        plugin = MongoDBPlugin(host="localhost", database="test")
        
        with patch('builtins.__import__', side_effect=ImportError):
            with pytest.raises(RuntimeError, match="motor not installed"):
                await plugin.connect()
    
    @pytest.mark.asyncio
    async def test_connect_failure(self):
        """Test connection failure."""
        plugin = MongoDBPlugin(host="localhost", database="test")
        
        with patch('motor.motor_asyncio.AsyncIOMotorClient', side_effect=Exception("Connection failed")):
            with pytest.raises(RuntimeError, match="Failed to connect to MongoDB"):
                await plugin.connect()


class TestMongoDBOperations:
    """Test MongoDB database operations."""
    
    def _create_mock_cursor(self, data):
        """Create a properly configured mock cursor."""
        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(return_value=data)
        
        # Configure cursor methods to return the cursor itself for chaining
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        
        return mock_cursor
    
    @pytest.mark.asyncio
    async def test_find(self):
        """Test find operation."""
        plugin = MongoDBPlugin(host="localhost", database="test")
        
        # Mock cursor with proper chaining behavior
        mock_cursor = self._create_mock_cursor([
            {"_id": "507f1f77bcf86cd799439011", "name": "John", "age": 30},
            {"_id": "507f1f77bcf86cd799439012", "name": "Jane", "age": 25}
        ])
        
        # Mock collection
        mock_collection = MagicMock()
        mock_collection.find.return_value = mock_cursor
        
        # Mock database - use MagicMock to avoid coroutine issues
        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        
        # Set mocks directly to avoid connection
        plugin._client = MagicMock()
        plugin._db = mock_db
        
        result = await plugin.find("users")
        
        expected = [
            {"_id": "507f1f77bcf86cd799439011", "name": "John", "age": 30},
            {"_id": "507f1f77bcf86cd799439012", "name": "Jane", "age": 25}
        ]
        assert result == expected
        mock_collection.find.assert_called_with({})
    
    @pytest.mark.asyncio
    async def test_find_with_filter(self):
        """Test find with filter."""
        plugin = MongoDBPlugin(host="localhost", database="test")
        
        mock_cursor = self._create_mock_cursor([
            {"_id": "507f1f77bcf86cd799439011", "name": "John", "age": 30}
        ])
        
        mock_collection = MagicMock()
        mock_collection.find.return_value = mock_cursor
        
        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        
        plugin._client = MagicMock()
        plugin._db = mock_db
        
        result = await plugin.find("users", {"age": {"$gte": 25}})
        
        assert len(result) == 1
        assert result[0]['name'] == 'John'
        mock_collection.find.assert_called_with({"age": {"$gte": 25}})
    
    @pytest.mark.asyncio
    async def test_find_with_options(self):
        """Test find with limit, skip, and sort."""
        plugin = MongoDBPlugin(host="localhost", database="test")
        
        mock_cursor = self._create_mock_cursor([])
        
        mock_collection = MagicMock()
        mock_collection.find.return_value = mock_cursor
        
        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        
        plugin._client = MagicMock()
        plugin._db = mock_db
        
        await plugin.find("users", {}, limit=10, skip=5, sort=[("name", 1)])
        
        # Verify cursor operations
        mock_cursor.sort.assert_called_with([("name", 1)])
        mock_cursor.skip.assert_called_with(5)
        mock_cursor.limit.assert_called_with(10)
    
    @pytest.mark.asyncio
    async def test_insert(self):
        """Test single insert."""
        plugin = MongoDBPlugin(host="localhost", database="test")
        
        mock_result = MagicMock()
        mock_result.inserted_id = "507f1f77bcf86cd799439011"
        
        mock_collection = MagicMock()
        mock_collection.insert_one = AsyncMock(return_value=mock_result)
        
        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        
        plugin._client = MagicMock()
        plugin._db = mock_db
        
        document = {"name": "John", "age": 30}
        result = await plugin.insert("users", document)
        
        assert result == "507f1f77bcf86cd799439011"
        mock_collection.insert_one.assert_called_with(document)
    
    @pytest.mark.asyncio
    async def test_insert_many(self):
        """Test bulk insert."""
        plugin = MongoDBPlugin(host="localhost", database="test")
        
        mock_result = MagicMock()
        mock_result.inserted_ids = ["507f1f77bcf86cd799439011", "507f1f77bcf86cd799439012"]
        
        mock_collection = MagicMock()
        mock_collection.insert_many = AsyncMock(return_value=mock_result)
        
        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        
        plugin._client = MagicMock()
        plugin._db = mock_db
        
        documents = [
            {"name": "John", "age": 30},
            {"name": "Jane", "age": 25}
        ]
        result = await plugin.insert_many("users", documents)
        
        assert result == ["507f1f77bcf86cd799439011", "507f1f77bcf86cd799439012"]
        mock_collection.insert_many.assert_called_with(documents)
    
    @pytest.mark.asyncio
    async def test_insert_many_empty(self):
        """Test bulk insert with empty data."""
        plugin = MongoDBPlugin(host="localhost", database="test")
        
        result = await plugin.insert_many("users", [])
        assert result == []
    
    @pytest.mark.asyncio
    async def test_update(self):
        """Test update operation."""
        plugin = MongoDBPlugin(host="localhost", database="test")
        
        mock_result = MagicMock()
        mock_result.matched_count = 2
        mock_result.modified_count = 1
        mock_result.upserted_id = None
        
        mock_collection = MagicMock()
        mock_collection.update_many = AsyncMock(return_value=mock_result)
        
        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        
        plugin._client = MagicMock()
        plugin._db = mock_db
        
        filter_doc = {"age": {"$lt": 30}}
        update_doc = {"$set": {"status": "young"}}
        
        result = await plugin.update("users", filter_doc, update_doc)
        
        expected = {
            'matched_count': 2,
            'modified_count': 1,
            'upserted_id': None
        }
        assert result == expected
        mock_collection.update_many.assert_called_with(filter_doc, update_doc, upsert=False)
    
    @pytest.mark.asyncio
    async def test_delete(self):
        """Test delete operation."""
        plugin = MongoDBPlugin(host="localhost", database="test")
        
        mock_result = MagicMock()
        mock_result.deleted_count = 3
        
        mock_collection = MagicMock()
        mock_collection.delete_many = AsyncMock(return_value=mock_result)
        
        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        
        plugin._client = MagicMock()
        plugin._db = mock_db
        
        filter_doc = {"age": {"$lt": 18}}
        result = await plugin.delete("users", filter_doc)
        
        assert result == 3
        mock_collection.delete_many.assert_called_with(filter_doc)
    
    @pytest.mark.asyncio
    async def test_count(self):
        """Test count operation."""
        plugin = MongoDBPlugin(host="localhost", database="test")
        
        mock_collection = MagicMock()
        mock_collection.count_documents = AsyncMock(return_value=42)
        
        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        
        plugin._client = MagicMock()
        plugin._db = mock_db
        
        # Count without filter
        result = await plugin.count("users")
        assert result == 42
        mock_collection.count_documents.assert_called_with({})
        
        # Count with filter
        filter_doc = {"age": {"$gte": 18}}
        result = await plugin.count("users", filter_doc)
        assert result == 42
        mock_collection.count_documents.assert_called_with(filter_doc)
    
    @pytest.mark.asyncio
    async def test_collections(self):
        """Test collections listing."""
        plugin = MongoDBPlugin(host="localhost", database="test")
        
        mock_db = MagicMock()
        mock_db.list_collection_names = AsyncMock(return_value=["users", "products", "orders"])
        
        plugin._client = MagicMock()
        plugin._db = mock_db
        
        collections = await plugin.collections()
        
        assert collections == ["orders", "products", "users"]  # Sorted
        mock_db.list_collection_names.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_aggregate(self):
        """Test aggregation pipeline."""
        plugin = MongoDBPlugin(host="localhost", database="test")
        
        mock_cursor = self._create_mock_cursor([
            {"_id": "Engineering", "count": 5},
            {"_id": "Marketing", "count": 3}
        ])
        
        mock_collection = MagicMock()
        mock_collection.aggregate.return_value = mock_cursor
        
        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        
        plugin._client = MagicMock()
        plugin._db = mock_db
        
        pipeline = [
            {"$match": {"status": "active"}},
            {"$group": {"_id": "$department", "count": {"$sum": 1}}}
        ]
        
        result = await plugin.aggregate("employees", pipeline)
        
        expected = [
            {"_id": "Engineering", "count": 5},
            {"_id": "Marketing", "count": 3}
        ]
        assert result == expected
        mock_collection.aggregate.assert_called_with(pipeline)


class TestMongoDBContextManager:
    """Test MongoDB context manager."""
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test MongoDB as context manager."""
        plugin = MongoDBPlugin(host="localhost", database="test")
        
        with patch('motor.motor_asyncio.AsyncIOMotorClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client.admin.command = AsyncMock(return_value={"ok": 1})
            mock_client_class.return_value = mock_client
            
            mock_db = MagicMock()
            mock_client.__getitem__.return_value = mock_db
            
            async with plugin as mongo:
                assert mongo == plugin
                assert plugin._client == mock_client
                assert plugin._db == mock_db


class TestMongoDBFactory:
    """Test MongoDB factory function."""
    
    def test_factory_function(self):
        """Test mongodb factory function."""
        plugin = mongodb(
            host="localhost",
            database="testdb"
        )
        
        assert isinstance(plugin, MongoDBPlugin)
        assert "localhost" in plugin.connection_string
        assert plugin.database_name == "testdb"
    
    def test_factory_with_auth(self):
        """Test mongodb factory function with authentication."""
        plugin = mongodb(
            host="localhost",
            database="testdb",
            username="user",
            password="pass"
        )
        
        assert isinstance(plugin, MongoDBPlugin)
        assert "user:pass" in plugin.connection_string


class TestMongoDBEdgeCases:
    """Test some basic edge cases."""
    
    def _create_mock_cursor(self, data):
        """Create a properly configured mock cursor."""
        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(return_value=data)
        
        # Configure cursor methods to return the cursor itself for chaining
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        
        return mock_cursor
    
    @pytest.mark.asyncio
    async def test_find_empty_result(self):
        """Test find with empty result."""
        plugin = MongoDBPlugin(host="localhost", database="test")
        
        mock_cursor = self._create_mock_cursor([])
        
        mock_collection = MagicMock()
        mock_collection.find.return_value = mock_cursor
        
        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        
        plugin._client = MagicMock()
        plugin._db = mock_db
        
        result = await plugin.find("empty_collection")
        assert result == []
    
    @pytest.mark.asyncio
    async def test_collections_empty(self):
        """Test collections listing with no collections."""
        plugin = MongoDBPlugin(host="localhost", database="test")
        
        mock_db = MagicMock()
        mock_db.list_collection_names = AsyncMock(return_value=[])
        
        plugin._client = MagicMock()
        plugin._db = mock_db
        
        collections = await plugin.collections()
        assert collections == []
    
    @pytest.mark.asyncio
    async def test_auto_connect_on_find(self):
        """Test that find auto-connects if not connected."""
        plugin = MongoDBPlugin(host="localhost", database="test")
        
        with patch('motor.motor_asyncio.AsyncIOMotorClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client.admin.command = AsyncMock(return_value={"ok": 1})
            mock_client_class.return_value = mock_client
            
            mock_cursor = self._create_mock_cursor([])
            
            mock_collection = MagicMock()
            mock_collection.find.return_value = mock_cursor
            
            mock_db = MagicMock()
            mock_db.__getitem__.return_value = mock_collection
            mock_client.__getitem__.return_value = mock_db
            
            # Find should auto-connect
            await plugin.find("test_collection")
            
            mock_client_class.assert_called_once()
            assert plugin._client == mock_client
    
    @pytest.mark.asyncio
    async def test_objectid_conversion(self):
        """Test ObjectId to string conversion."""
        plugin = MongoDBPlugin(host="localhost", database="test")
        
        # Simulate ObjectId objects
        class MockObjectId:
            def __init__(self, id_str):
                self.id_str = id_str
            def __str__(self):
                return self.id_str
        
        mock_cursor = self._create_mock_cursor([
            {"_id": MockObjectId("507f1f77bcf86cd799439011"), "name": "John"},
            {"_id": MockObjectId("507f1f77bcf86cd799439012"), "name": "Jane"}
        ])
        
        mock_collection = MagicMock()
        mock_collection.find.return_value = mock_cursor
        
        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        
        plugin._client = MagicMock()
        plugin._db = mock_db
        
        result = await plugin.find("users")
        
        # ObjectIds should be converted to strings
        assert result[0]["_id"] == "507f1f77bcf86cd799439011"
        assert result[1]["_id"] == "507f1f77bcf86cd799439012"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])