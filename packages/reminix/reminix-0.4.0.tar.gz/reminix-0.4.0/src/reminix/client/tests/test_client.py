"""Unit tests for Reminix SDK Client"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from reminix.client import Client, AuthenticationError, APIError


class TestClient:
    """Test the Client class"""

    def test_client_initialization(self):
        """Test that client can be initialized"""
        client = Client(api_key="test-key")
        assert client._config.api_key == "test-key"
        assert client._config.base_url == "https://api.reminix.com/v1"
        assert client._config.timeout == 30

    def test_client_custom_config(self):
        """Test client with custom configuration"""
        client = Client(
            api_key="test-key",
            base_url="https://custom.com",
            timeout=60,
        )
        assert client._config.base_url == "https://custom.com"
        assert client._config.timeout == 60

    @pytest.mark.asyncio
    async def test_request_success(self):
        """Test successful API request"""
        client = Client(api_key="test-key")

        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {"id": "123", "name": "Test"}

        mock_client = AsyncMock()
        mock_client.request.return_value = mock_response

        with patch.object(client, "_client", mock_client):
            client._client = mock_client
            result = await client.request("GET", "/test")

        assert result == {"id": "123", "name": "Test"}
        mock_client.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_request_with_bearer_auth(self):
        """Test that bearer token is added to requests"""
        client = Client(api_key="test-key")

        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {}

        mock_client = AsyncMock()
        mock_client.request.return_value = mock_response

        with patch.object(client, "_client", mock_client):
            client._client = mock_client
            await client.request("GET", "/test")

        # Check that client was created with correct headers
        await client._ensure_client()
        assert "Authorization" in client._client.headers
        assert client._client.headers["Authorization"] == "Bearer test-key"

    @pytest.mark.asyncio
    async def test_request_authentication_error(self):
        """Test that 401 raises AuthenticationError"""
        client = Client(api_key="invalid-key")

        mock_response = MagicMock()
        mock_response.is_success = False
        mock_response.status_code = 401
        mock_response.reason_phrase = "Unauthorized"
        mock_response.json.return_value = {"error": "Invalid API key"}
        mock_response.text = '{"error": "Invalid API key"}'

        mock_client = AsyncMock()
        mock_client.request.return_value = mock_response

        with patch.object(client, "_client", mock_client):
            client._client = mock_client
            with pytest.raises(AuthenticationError) as exc_info:
                await client.request("GET", "/test")

        assert exc_info.value.status == 401

    @pytest.mark.asyncio
    async def test_request_api_error(self):
        """Test that non-2xx responses raise APIError"""
        client = Client(api_key="test-key")

        mock_response = MagicMock()
        mock_response.is_success = False
        mock_response.status_code = 500
        mock_response.reason_phrase = "Internal Server Error"
        mock_response.json.return_value = {"error": "Server error"}
        mock_response.text = '{"error": "Server error"}'

        mock_client = AsyncMock()
        mock_client.request.return_value = mock_response

        with patch.object(client, "_client", mock_client):
            client._client = mock_client
            with pytest.raises(APIError) as exc_info:
                await client.request("GET", "/test")

        assert exc_info.value.status == 500

    @pytest.mark.asyncio
    async def test_request_empty_response(self):
        """Test handling of empty or non-JSON responses"""
        client = Client(api_key="test-key")

        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.headers = {"content-type": "text/plain"}
        mock_response.text = ""

        mock_client = AsyncMock()
        mock_client.request.return_value = mock_response

        with patch.object(client, "_client", mock_client):
            client._client = mock_client
            result = await client.request("GET", "/test")

        assert result == {}

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test client as async context manager"""
        async with Client(api_key="test-key") as client:
            assert client._client is not None

        # Client should be closed after context
        assert client._client is None

    @pytest.mark.asyncio
    async def test_close(self):
        """Test closing the client"""
        client = Client(api_key="test-key")
        await client._ensure_client()
        assert client._client is not None

        await client.close()
        assert client._client is None
