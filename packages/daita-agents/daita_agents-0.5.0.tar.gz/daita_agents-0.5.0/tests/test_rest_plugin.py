"""
Test suite for REST Plugin - testing REST API integration.

Simple tests to ensure the REST plugin works correctly.
"""
import pytest
import asyncio
import tempfile
import os
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from contextlib import asynccontextmanager

from daita.plugins.rest import RESTPlugin, rest


class TestRESTInitialization:
    """Test REST plugin initialization."""
    
    def test_basic_initialization(self):
        """Test basic REST plugin initialization."""
        plugin = RESTPlugin(base_url="https://api.example.com")
        
        assert plugin.base_url == "https://api.example.com"
        assert plugin.api_key is None
        assert plugin.auth_header == "Authorization"
        assert plugin.auth_prefix == "Bearer"
        assert plugin.timeout == 30
        assert plugin.default_headers['Content-Type'] == "application/json"
        assert plugin.default_headers['Accept'] == "application/json"
        assert plugin._session is None
    
    def test_initialization_with_auth(self):
        """Test initialization with API key."""
        plugin = RESTPlugin(
            base_url="https://api.example.com",
            api_key="test-api-key"
        )
        
        assert plugin.api_key == "test-api-key"
        assert plugin.default_headers["Authorization"] == "Bearer test-api-key"
    
    def test_custom_auth_configuration(self):
        """Test initialization with custom auth configuration."""
        plugin = RESTPlugin(
            base_url="https://api.example.com",
            api_key="test-key",
            auth_header="X-API-Key",
            auth_prefix=""
        )
        
        assert plugin.auth_header == "X-API-Key"
        assert plugin.auth_prefix == ""
        assert plugin.default_headers["X-API-Key"] == "test-key"  # No prefix
    
    def test_custom_configuration(self):
        """Test initialization with custom settings."""
        custom_headers = {"User-Agent": "MyApp/1.0"}
        
        plugin = RESTPlugin(
            base_url="https://api.example.com",
            timeout=60,
            headers=custom_headers
        )
        
        assert plugin.timeout == 60
        assert plugin.default_headers["User-Agent"] == "MyApp/1.0"
        assert plugin.default_headers["Content-Type"] == "application/json"  # Should still have defaults
    
    def test_empty_base_url_error(self):
        """Test initialization with empty base URL."""
        with pytest.raises(ValueError, match="base_url cannot be empty"):
            RESTPlugin(base_url="")
        
        with pytest.raises(ValueError, match="base_url cannot be empty"):
            RESTPlugin(base_url="   ")  # Whitespace only


class TestRESTConnection:
    """Test REST connection management."""
    
    @pytest.mark.asyncio
    async def test_connect_disconnect(self):
        """Test connection and disconnection."""
        plugin = RESTPlugin(base_url="https://api.example.com")
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session
            
            # Test connect
            await plugin.connect()
            assert plugin._session == mock_session
            mock_session_class.assert_called_once()
            
            # Test disconnect
            await plugin.disconnect()
            mock_session.close.assert_called_once()
            assert plugin._session is None
    
    @pytest.mark.asyncio
    async def test_connect_import_error(self):
        """Test connection with missing aiohttp."""
        plugin = RESTPlugin(base_url="https://api.example.com")
        
        with patch('builtins.__import__', side_effect=ImportError):
            with pytest.raises(RuntimeError, match="aiohttp not installed"):
                await plugin.connect()


def create_mock_response(status=200, headers=None, json_data=None, text_data=None, binary_data=None):
    """Helper function to create properly mocked aiohttp responses."""
    mock_response = Mock()
    mock_response.status = status
    mock_response.headers = headers or {}
    
    # Always create async methods, even if no data is provided
    if json_data is not None:
        mock_response.json = AsyncMock(return_value=json_data)
    else:
        # For empty JSON responses, return empty dict
        mock_response.json = AsyncMock(return_value={})
    
    if text_data is not None:
        mock_response.text = AsyncMock(return_value=text_data)
    else:
        # For empty text responses, return empty string
        mock_response.text = AsyncMock(return_value="")
    
    if binary_data is not None:
        mock_response.read = AsyncMock(return_value=binary_data)
    else:
        # For empty binary responses, return empty bytes
        mock_response.read = AsyncMock(return_value=b"")
    
    return mock_response


@asynccontextmanager
async def mock_async_context_manager(mock_response):
    """Create a proper async context manager for mocking."""
    yield mock_response


def create_mock_session_with_response(mock_response):
    """Helper function to create a properly mocked session with async context manager."""
    mock_session = Mock()
    
    # Create async context manager that yields the response
    context_manager = mock_async_context_manager(mock_response)
    
    # Set up all HTTP methods to return the context manager
    mock_session.request = Mock(return_value=context_manager)
    mock_session.get = Mock(return_value=context_manager)
    mock_session.post = Mock(return_value=context_manager)
    mock_session.put = Mock(return_value=context_manager)
    mock_session.patch = Mock(return_value=context_manager)
    mock_session.delete = Mock(return_value=context_manager)
    
    return mock_session


class TestRESTOperations:
    """Test REST API operations."""
    
    @pytest.mark.asyncio
    async def test_get_request(self):
        """Test GET request."""
        plugin = RESTPlugin(base_url="https://api.example.com")
        
        # Create mock response
        mock_response = create_mock_response(
            status=200,
            headers={'content-type': 'application/json'},
            json_data={"id": 1, "name": "John"}
        )
        
        # Create mock session with proper context manager
        mock_session = create_mock_session_with_response(mock_response)
        plugin._session = mock_session
        
        result = await plugin.get("/users/1", params={"include": "profile"})
        
        expected = {"id": 1, "name": "John"}
        assert result == expected
        
        # Verify request was made correctly
        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"  # method
        assert call_args[0][1] == "https://api.example.com/users/1"  # URL
        assert call_args[1]['params'] == {"include": "profile"}
    
    @pytest.mark.asyncio
    async def test_post_request_json(self):
        """Test POST request with JSON data."""
        plugin = RESTPlugin(base_url="https://api.example.com")
        
        # Create mock response
        mock_response = create_mock_response(
            status=201,
            headers={'content-type': 'application/json'},
            json_data={"id": 2, "name": "Jane", "created": True}
        )
        
        # Create mock session
        mock_session = create_mock_session_with_response(mock_response)
        plugin._session = mock_session
        
        data = {"name": "Jane", "email": "jane@example.com"}
        result = await plugin.post("/users", json_data=data)
        
        expected = {"id": 2, "name": "Jane", "created": True}
        assert result == expected
        
        # Verify request
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert call_args[1]['json'] == data
    
    @pytest.mark.asyncio
    async def test_put_request(self):
        """Test PUT request."""
        plugin = RESTPlugin(base_url="https://api.example.com")
        
        # Create mock response
        mock_response = create_mock_response(
            status=200,
            headers={'content-type': 'application/json'},
            json_data={"id": 1, "name": "John Updated"}
        )
        
        # Create mock session
        mock_session = create_mock_session_with_response(mock_response)
        plugin._session = mock_session
        
        data = {"name": "John Updated"}
        result = await plugin.put("/users/1", json_data=data)
        
        assert result["name"] == "John Updated"
        
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "PUT"
    
    @pytest.mark.asyncio
    async def test_patch_request(self):
        """Test PATCH request."""
        plugin = RESTPlugin(base_url="https://api.example.com")
        
        # Create mock response
        mock_response = create_mock_response(
            status=200,
            headers={'content-type': 'application/json'},
            json_data={"id": 1, "status": "active"}
        )
        
        # Create mock session
        mock_session = create_mock_session_with_response(mock_response)
        plugin._session = mock_session
        
        data = {"status": "active"}
        result = await plugin.patch("/users/1", json_data=data)
        
        assert result["status"] == "active"
        
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "PATCH"
    
    @pytest.mark.asyncio
    async def test_delete_request(self):
        """Test DELETE request."""
        plugin = RESTPlugin(base_url="https://api.example.com")
        
        # Create mock response for empty content - use different content type for 204
        mock_response = create_mock_response(status=204, headers={})
        mock_response.content_length = 0
        
        # Create mock session
        mock_session = create_mock_session_with_response(mock_response)
        plugin._session = mock_session
        
        result = await plugin.delete("/users/1")
        
        # The plugin returns binary content structure for responses without content-type
        expected = {
            'content': b'',
            'content_type': '',
            'size': 0
        }
        assert result == expected
        
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "DELETE"


class TestRESTResponseHandling:
    """Test REST response handling."""
    
    @pytest.mark.asyncio
    async def test_json_response(self):
        """Test JSON response handling."""
        plugin = RESTPlugin(base_url="https://api.example.com")
        
        mock_response = create_mock_response(
            status=200,
            headers={'content-type': 'application/json'},
            json_data={"message": "success"}
        )
        
        mock_session = create_mock_session_with_response(mock_response)
        plugin._session = mock_session
        
        result = await plugin.get("/status")
        assert result == {"message": "success"}
    
    @pytest.mark.asyncio
    async def test_text_response(self):
        """Test text response handling."""
        plugin = RESTPlugin(base_url="https://api.example.com")
        
        mock_response = create_mock_response(
            status=200,
            headers={'content-type': 'text/plain'},
            text_data="Plain text response"
        )
        mock_response.content_length = 10
        
        mock_session = create_mock_session_with_response(mock_response)
        plugin._session = mock_session
        
        result = await plugin.get("/status")
        
        expected = {
            'content': 'Plain text response',
            'content_type': 'text/plain'
        }
        assert result == expected
    
    @pytest.mark.asyncio
    async def test_binary_response(self):
        """Test binary response handling."""
        plugin = RESTPlugin(base_url="https://api.example.com")
        
        mock_response = create_mock_response(
            status=200,
            headers={'content-type': 'application/pdf'},
            binary_data=b"binary content"
        )
        mock_response.content_length = 1024
        
        mock_session = create_mock_session_with_response(mock_response)
        plugin._session = mock_session
        
        result = await plugin.get("/document.pdf")
        
        expected = {
            'content': b"binary content",
            'content_type': 'application/pdf',
            'size': 14  # len(b"binary content")
        }
        assert result == expected


class TestRESTErrorHandling:
    """Test REST error handling."""
    
    @pytest.mark.asyncio
    async def test_http_error(self):
        """Test HTTP error handling."""
        plugin = RESTPlugin(base_url="https://api.example.com")
        
        # Create mock error response
        mock_response = create_mock_response(
            status=404,
            text_data="Not Found"
        )
        
        # Create mock session
        mock_session = create_mock_session_with_response(mock_response)
        plugin._session = mock_session
        
        with pytest.raises(RuntimeError, match="HTTP 404"):
            await plugin.get("/users/999")
    
    @pytest.mark.asyncio
    async def test_request_error(self):
        """Test request error handling."""
        plugin = RESTPlugin(base_url="https://api.example.com")
        
        mock_session = Mock()
        # Make the request method raise an exception directly
        mock_session.request.side_effect = Exception("Connection error")
        
        plugin._session = mock_session
        
        with pytest.raises(RuntimeError, match="REST request failed"):
            await plugin.get("/users")


class TestRESTFileOperations:
    """Test REST file operations."""
    
    @pytest.mark.asyncio
    async def test_upload_file(self):
        """Test file upload."""
        plugin = RESTPlugin(base_url="https://api.example.com")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
            temp_file.write("Test file content")
            temp_file_path = temp_file.name
        
        try:
            # Create mock response
            mock_response = create_mock_response(
                status=200,
                headers={'content-type': 'application/json'},
                json_data={"file_id": "123", "status": "uploaded"}
            )
            
            # Create mock session
            mock_session = create_mock_session_with_response(mock_response)
            plugin._session = mock_session
            
            result = await plugin.upload_file(
                "/upload",
                temp_file_path,
                field_name="document",
                additional_data={"category": "test"}
            )
            
            expected = {"file_id": "123", "status": "uploaded"}
            assert result == expected
            
            # Verify post was called
            mock_session.post.assert_called_once()
        
        finally:
            # Clean up temp file
            os.unlink(temp_file_path)
    
    @pytest.mark.asyncio
    async def test_upload_file_not_found(self):
        """Test file upload with missing file."""
        plugin = RESTPlugin(base_url="https://api.example.com")
        
        with pytest.raises(FileNotFoundError):
            await plugin.upload_file("/upload", "/nonexistent/file.txt")
    
    @pytest.mark.asyncio
    async def test_download_file(self):
        """Test file download."""
        plugin = RESTPlugin(base_url="https://api.example.com")
        
        # Create mock response
        mock_response = create_mock_response(status=200)
        
        # Mock content iterator
        async def mock_iter_chunked(size):
            yield b"chunk1"
            yield b"chunk2"
        
        mock_response.content = Mock()
        mock_response.content.iter_chunked = mock_iter_chunked
        
        # Create mock session
        mock_session = create_mock_session_with_response(mock_response)
        plugin._session = mock_session
        
        # Create temporary directory for download
        with tempfile.TemporaryDirectory() as temp_dir:
            save_path = os.path.join(temp_dir, "downloaded_file.txt")
            
            result = await plugin.download_file("/download/file", save_path)
            
            assert result == save_path
            assert os.path.exists(save_path)
            
            # Check file content
            with open(save_path, 'rb') as f:
                content = f.read()
            assert content == b"chunk1chunk2"


class TestRESTContextManager:
    """Test REST context manager."""
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test REST as context manager."""
        plugin = RESTPlugin(base_url="https://api.example.com")
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session
            
            async with plugin as api:
                assert api == plugin
                assert plugin._session == mock_session
            
            mock_session.close.assert_called_once()


class TestRESTFactory:
    """Test REST factory function."""
    
    def test_factory_function(self):
        """Test rest factory function."""
        plugin = rest(
            base_url="https://api.example.com",
            api_key="test-key"
        )
        
        assert isinstance(plugin, RESTPlugin)
        assert plugin.base_url == "https://api.example.com"
        assert plugin.api_key == "test-key"
    
    def test_factory_with_custom_auth(self):
        """Test rest factory function with custom auth."""
        plugin = rest(
            base_url="https://api.example.com",
            api_key="test-key",
            auth_header="X-Custom-Auth",
            auth_prefix="Token"
        )
        
        assert isinstance(plugin, RESTPlugin)
        assert plugin.auth_header == "X-Custom-Auth"
        assert plugin.auth_prefix == "Token"
        assert plugin.default_headers["X-Custom-Auth"] == "Token test-key"


class TestRESTEdgeCases:
    """Test some basic edge cases."""
    
    @pytest.mark.asyncio
    async def test_auto_connect_on_request(self):
        """Test that requests auto-connect if not connected."""
        plugin = RESTPlugin(base_url="https://api.example.com")
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_response = create_mock_response(
                status=200,
                headers={'content-type': 'application/json'},
                json_data={"status": "ok"}
            )
            
            mock_session = create_mock_session_with_response(mock_response)
            mock_session_class.return_value = mock_session
            
            # Request should auto-connect
            result = await plugin.get("/status")
            
            mock_session_class.assert_called_once()
            assert plugin._session == mock_session
            assert result == {"status": "ok"}
    
    @pytest.mark.asyncio
    async def test_empty_response_handling(self):
        """Test handling of empty responses."""
        plugin = RESTPlugin(base_url="https://api.example.com")
        
        # For empty responses, don't set JSON content-type to avoid trying to parse JSON
        mock_response = create_mock_response(
            status=200,
            headers={}  # No content-type header for truly empty response
        )
        mock_response.content_length = 0
        
        mock_session = create_mock_session_with_response(mock_response)
        plugin._session = mock_session
        
        result = await plugin.get("/empty")
        
        # Should return binary content section since no content-type
        expected = {
            'content': b"",
            'content_type': '',
            'size': 0
        }
        assert result == expected
    
    def test_auth_header_variations(self):
        """Test different authentication header configurations."""
        # Test with Bearer prefix
        api1 = rest(base_url="https://api.example.com", api_key="key123", auth_prefix="Bearer")
        assert api1.default_headers["Authorization"] == "Bearer key123"
        
        # Test with empty prefix
        api2 = rest(base_url="https://api.example.com", api_key="key123", auth_prefix="")
        assert api2.default_headers["Authorization"] == "key123"
        
        # Test with custom header and prefix
        api3 = rest(
            base_url="https://api.example.com", 
            api_key="key123", 
            auth_header="X-API-Key",
            auth_prefix="Token"
        )
        assert api3.default_headers["X-API-Key"] == "Token key123"
        
        # Test with no API key
        api4 = rest(base_url="https://api.example.com")
        assert "Authorization" not in api4.default_headers


if __name__ == "__main__":
    pytest.main([__file__, "-v"])