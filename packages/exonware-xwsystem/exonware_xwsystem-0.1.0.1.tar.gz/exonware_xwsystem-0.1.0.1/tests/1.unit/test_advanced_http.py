"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1
Generation Date: January 31, 2025

Unit tests for advanced HTTP client.
"""

import asyncio
import json
import pytest
from unittest.mock import Mock, AsyncMock

from src.exonware.xwsystem.http_client.advanced_client import (
    AdvancedHttpClient,
    AdvancedHttpConfig,
    Http2Config,
    StreamingConfig,
    MockTransport,
    MockResponse,
)
from src.exonware.xwsystem.http_client.client import HttpError


class TestMockTransport:
    """Test MockTransport functionality."""

    def test_mock_response_creation(self):
        """Test MockResponse creation and methods."""
        response = MockResponse(
            status_code=200,
            content=b'{"message": "success"}',
            headers={"Content-Type": "application/json"},
            url="https://api.example.com/test"
        )
        
        assert response.status_code == 200
        assert response.content == b'{"message": "success"}'
        assert response.headers["Content-Type"] == "application/json"
        assert response.url == "https://api.example.com/test"
        assert response.text == '{"message": "success"}'
        
        # Test JSON parsing
        data = response.json()
        assert data["message"] == "success"

    def test_mock_response_error_status(self):
        """Test MockResponse error handling."""
        response = MockResponse(status_code=404, content=b"Not Found")
        
        with pytest.raises(HttpError):
            response.raise_for_status()

    @pytest.mark.asyncio
    async def test_mock_transport_basic(self):
        """Test basic MockTransport functionality."""
        responses = {
            "https://api.example.com/users": {
                "status_code": 200,
                "content": b'{"users": ["alice", "bob"]}',
                "headers": {"Content-Type": "application/json"}
            }
        }
        
        transport = MockTransport(responses)
        
        # Mock request object
        request = Mock()
        request.url = "https://api.example.com/users"
        
        response = await transport.handle_async_request(request)
        
        assert response.status_code == 200
        assert "alice" in response.text
        assert len(transport.requests) == 1

    @pytest.mark.asyncio
    async def test_mock_transport_not_found(self):
        """Test MockTransport 404 response for unknown URLs."""
        transport = MockTransport({})
        
        request = Mock()
        request.url = "https://api.example.com/unknown"
        
        response = await transport.handle_async_request(request)
        
        assert response.status_code == 404
        assert response.content == b"Not Found"


class TestAdvancedHttpConfig:
    """Test AdvancedHttpConfig and related config classes."""

    def test_http2_config_defaults(self):
        """Test Http2Config default values."""
        config = Http2Config()
        
        assert config.enabled is True
        assert config.max_concurrent_streams == 100
        assert config.initial_window_size == 65536
        assert config.max_frame_size == 16384
        assert config.enable_push is False

    def test_streaming_config_defaults(self):
        """Test StreamingConfig default values."""
        config = StreamingConfig()
        
        assert config.chunk_size == 8192
        assert config.buffer_size == 65536
        assert config.timeout_per_chunk == 30.0
        assert config.max_content_length is None

    def test_advanced_http_config_defaults(self):
        """Test AdvancedHttpConfig default values."""
        config = AdvancedHttpConfig()
        
        assert isinstance(config.http2, Http2Config)
        assert isinstance(config.streaming, StreamingConfig)
        assert config.verify_ssl is True
        assert config.trust_env is True
        assert config.follow_redirects is True
        assert config.max_redirects == 20


class TestAdvancedHttpClient:
    """Test AdvancedHttpClient functionality."""

    @pytest.mark.asyncio
    async def test_client_with_mock_transport(self):
        """Test client with mock transport."""
        responses = {
            "https://api.example.com/users": {
                "status_code": 200,
                "content": b'{"users": ["alice", "bob"]}',
                "headers": {"Content-Type": "application/json"}
            }
        }
        
        transport = MockTransport(responses)
        client = AdvancedHttpClient(transport=transport)
        
        response = await client.get("https://api.example.com/users")
        
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert len(data["users"]) == 2

    @pytest.mark.asyncio
    async def test_client_post_request(self):
        """Test POST request with mock transport."""
        responses = {
            "https://api.example.com/users": {
                "status_code": 201,
                "content": b'{"id": 123, "name": "John"}',
                "headers": {"Content-Type": "application/json"}
            }
        }
        
        transport = MockTransport(responses)
        client = AdvancedHttpClient(transport=transport)
        
        user_data = {"name": "John", "email": "john@example.com"}
        response = await client.post("https://api.example.com/users", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "John"
        assert data["id"] == 123

    @pytest.mark.asyncio
    async def test_client_all_http_methods(self):
        """Test all HTTP methods."""
        responses = {
            "https://api.example.com/resource": {
                "status_code": 200,
                "content": b'{"method": "success"}',
            }
        }
        
        transport = MockTransport(responses)
        client = AdvancedHttpClient(transport=transport)
        
        # Test all methods
        methods = [
            client.get,
            client.post,
            client.put,
            client.patch,
            client.delete,
            client.head,
            client.options,
        ]
        
        for method in methods:
            response = await method("https://api.example.com/resource")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_client_with_headers(self):
        """Test client with custom headers."""
        responses = {
            "https://api.example.com/protected": {
                "status_code": 200,
                "content": b'{"authenticated": true}',
            }
        }
        
        transport = MockTransport(responses)
        client = AdvancedHttpClient(
            transport=transport,
            default_headers={"Authorization": "Bearer token123"}
        )
        
        response = await client.get("https://api.example.com/protected")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_client_error_handling(self):
        """Test client error handling."""
        responses = {
            "https://api.example.com/error": {
                "status_code": 500,
                "content": b'{"error": "Internal Server Error"}',
            }
        }
        
        transport = MockTransport(responses)
        
        # Create config with no retries to avoid retry logic
        config = AdvancedHttpConfig()
        config.retry.max_retries = 0
        
        client = AdvancedHttpClient(transport=transport, config=config)
        
        # Should raise HttpError for 500 status
        with pytest.raises(HttpError):
            await client.get("https://api.example.com/error")

    @pytest.mark.asyncio
    async def test_sync_methods(self):
        """Test synchronous method wrappers."""
        responses = {
            "https://api.example.com/sync": {
                "status_code": 200,
                "content": b'{"sync": true}',
            }
        }
        
        transport = MockTransport(responses)
        client = AdvancedHttpClient(transport=transport)
        
        # Test sync_get (this will use asyncio.run internally)
        response = client.sync_get("https://api.example.com/sync")
        assert response.status_code == 200
        
        # Test other sync methods
        response = client.sync_post("https://api.example.com/sync", json={"test": True})
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_context_managers(self):
        """Test async and sync context managers."""
        transport = MockTransport({})
        
        # Test async context manager
        async with AdvancedHttpClient(transport=transport) as client:
            assert isinstance(client, AdvancedHttpClient)
        
        # Test sync context manager
        with AdvancedHttpClient(transport=transport) as client:
            assert isinstance(client, AdvancedHttpClient)

    @pytest.mark.asyncio
    async def test_streaming_simulation(self):
        """Test streaming functionality with mock transport."""
        # Note: Real streaming would require actual httpx integration
        # This tests the interface and basic functionality
        
        responses = {
            "https://api.example.com/stream": {
                "status_code": 200,
                "content": b'{"chunk": 1}\n{"chunk": 2}\n{"chunk": 3}',
                "headers": {"Content-Type": "application/x-ndjson"}
            }
        }
        
        transport = MockTransport(responses)
        client = AdvancedHttpClient(transport=transport)
        
        # Test basic streaming interface (mock doesn't actually stream)
        async with client.stream("GET", "https://api.example.com/stream") as response:
            assert response.status_code == 200
            # In a real implementation, this would be streamable
            content = response.content
            assert b'{"chunk": 1}' in content

    @pytest.mark.asyncio
    async def test_download_file_simulation(self):
        """Test download file functionality."""
        import tempfile
        
        responses = {
            "https://example.com/file.txt": {
                "status_code": 200,
                "content": b"File content for download test",
                "headers": {"Content-Type": "text/plain", "Content-Length": "29"}
            }
        }
        
        transport = MockTransport(responses)
        client = AdvancedHttpClient(transport=transport)
        
        # Test download to temporary file
        with tempfile.NamedTemporaryFile(mode='w+b', delete=False) as temp_file:
            await client.download_file(
                "https://example.com/file.txt",
                temp_file.name
            )
            
            # Verify file was written
            temp_file.seek(0)
            content = temp_file.read()
            assert content == b"File content for download test"

    @pytest.mark.asyncio
    async def test_client_configuration(self):
        """Test client with custom configuration."""
        config = AdvancedHttpConfig()
        config.http2.enabled = False
        config.streaming.chunk_size = 4096
        config.verify_ssl = False
        
        transport = MockTransport({})
        client = AdvancedHttpClient(config=config, transport=transport)
        
        assert client.config.http2.enabled is False
        assert client.config.streaming.chunk_size == 4096
        assert client.config.verify_ssl is False

    def test_config_validation(self):
        """Test configuration validation."""
        # Test that config objects can be created with various parameters
        http2_config = Http2Config(
            enabled=False,
            max_concurrent_streams=50,
            initial_window_size=32768
        )
        assert http2_config.enabled is False
        assert http2_config.max_concurrent_streams == 50
        
        streaming_config = StreamingConfig(
            chunk_size=4096,
            max_content_length=1024*1024  # 1MB
        )
        assert streaming_config.chunk_size == 4096
        assert streaming_config.max_content_length == 1024*1024
        
        advanced_config = AdvancedHttpConfig(
            http2=http2_config,
            streaming=streaming_config,
            verify_ssl=False
        )
        assert advanced_config.http2 == http2_config
        assert advanced_config.streaming == streaming_config
        assert advanced_config.verify_ssl is False


class TestRealWorldScenarios:
    """Test real-world usage scenarios."""

    @pytest.mark.asyncio
    async def test_api_client_pattern(self):
        """Test typical API client usage pattern."""
        # Simulate a REST API
        responses = {
            "https://api.service.com/users": {
                "status_code": 200,
                "content": b'[{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]',
                "headers": {"Content-Type": "application/json"}
            },
            "https://api.service.com/users/1": {
                "status_code": 200,
                "content": b'{"id": 1, "name": "Alice", "email": "alice@example.com"}',
                "headers": {"Content-Type": "application/json"}
            }
        }
        
        transport = MockTransport(responses)
        
        # Create API client with base configuration
        client = AdvancedHttpClient(
            base_url="https://api.service.com",
            transport=transport,
            default_headers={
                "User-Agent": "MyApp/1.0",
                "Accept": "application/json"
            }
        )
        
        # List users
        response = await client.get("/users")
        users = response.json()
        assert len(users) == 2
        assert users[0]["name"] == "Alice"
        
        # Get specific user
        response = await client.get("/users/1")
        user = response.json()
        assert user["email"] == "alice@example.com"

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test concurrent request handling."""
        responses = {
            f"https://api.example.com/item/{i}": {
                "status_code": 200,
                "content": f'{{"id": {i}, "value": "item_{i}"}}'.encode(),
                "headers": {"Content-Type": "application/json"}
            }
            for i in range(5)
        }
        
        transport = MockTransport(responses)
        client = AdvancedHttpClient(transport=transport)
        
        # Make concurrent requests
        tasks = [
            client.get(f"https://api.example.com/item/{i}")
            for i in range(5)
        ]
        
        responses = await asyncio.gather(*tasks)
        
        # Verify all requests completed successfully
        assert len(responses) == 5
        for i, response in enumerate(responses):
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == i
            assert data["value"] == f"item_{i}"

    @pytest.mark.asyncio
    async def test_error_recovery_pattern(self):
        """Test error recovery and retry patterns."""
        # Simulate server that fails first, then succeeds
        call_count = 0
        
        def create_response():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return {
                    "status_code": 503,
                    "content": b'{"error": "Service Temporarily Unavailable"}',
                }
            else:
                return {
                    "status_code": 200,
                    "content": b'{"success": true, "attempt": 2}',
                }
        
        # Mock transport that changes response based on call count
        transport = MockTransport({})
        original_handle = transport.handle_async_request
        
        async def dynamic_handle(request):
            # Override responses dynamically
            transport.responses[str(request.url)] = create_response()
            return await original_handle(request)
        
        transport.handle_async_request = dynamic_handle
        
        # Configure client with retry
        config = AdvancedHttpConfig()
        config.retry.max_retries = 2
        config.retry.base_delay = 0.1  # Fast retry for testing
        
        client = AdvancedHttpClient(transport=transport, config=config)
        
        # This should succeed after retry
        response = await client.get("https://api.example.com/flaky")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


if __name__ == "__main__":
    pytest.main([__file__])
