"""Tests for Connection class."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from kobana.configuration import Configuration
from kobana.connection import Connection
from kobana.errors import (
    APIError,
    ConnectionError,
    ResourceNotFoundError,
    UnauthorizedError,
    ValidationError,
)


class TestConnection:
    """Tests for Connection class."""

    @pytest.fixture
    def config(self) -> Configuration:
        """Create test configuration."""
        return Configuration(
            api_token="test-token",
            environment="sandbox",
        )

    @pytest.fixture
    def connection(self, config: Configuration) -> Connection:
        """Create test connection."""
        return Connection(config)

    def test_initialization(self, config: Configuration) -> None:
        """Test connection initialization."""
        conn = Connection(config)
        assert conn.configuration is config
        assert conn._client is None

    def test_client_creation(self, config: Configuration) -> None:
        """Test HTTP client creation."""
        conn = Connection(config)

        with patch("httpx.Client") as mock_client:
            _ = conn.client

        mock_client.assert_called_once()
        call_kwargs = mock_client.call_args[1]
        assert call_kwargs["base_url"] == config.base_url
        assert "Authorization" in call_kwargs["headers"]
        assert call_kwargs["headers"]["Authorization"] == "Bearer test-token"

    def test_client_caching(self, connection: Connection) -> None:
        """Test that client is cached."""
        with patch("httpx.Client") as mock_client:
            mock_client.return_value = MagicMock()
            client1 = connection.client
            client2 = connection.client

        assert client1 is client2
        mock_client.assert_called_once()

    def test_close(self, connection: Connection) -> None:
        """Test connection close."""
        mock_client = MagicMock()
        connection._client = mock_client

        connection.close()

        mock_client.close.assert_called_once()
        assert connection._client is None

    def test_get_success(self, connection: Connection) -> None:
        """Test successful GET request."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"id": 1}'
        mock_response.json.return_value = {"id": 1}

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        connection._client = mock_client

        result = connection.get("/test")

        assert result == {"id": 1}
        mock_client.get.assert_called_once_with("/test", params=None)

    def test_get_with_params(self, connection: Connection) -> None:
        """Test GET request with parameters."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "[]"
        mock_response.json.return_value = []

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        connection._client = mock_client

        connection.get("/test", params={"page": 1})

        mock_client.get.assert_called_once_with("/test", params={"page": 1})

    def test_post_success(self, connection: Connection) -> None:
        """Test successful POST request."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.text = '{"id": 1}'
        mock_response.json.return_value = {"id": 1}

        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        connection._client = mock_client

        result = connection.post("/test", data={"name": "test"})

        assert result == {"id": 1}
        mock_client.post.assert_called_once()

    def test_post_with_idempotency_key(self, connection: Connection) -> None:
        """Test POST request with idempotency key."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.text = '{"id": 1}'
        mock_response.json.return_value = {"id": 1}

        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        connection._client = mock_client

        connection.post("/test", data={}, idempotency_key="unique-key")

        call_kwargs = mock_client.post.call_args[1]
        assert call_kwargs["headers"]["X-Idempotency-Key"] == "unique-key"

    def test_put_success(self, connection: Connection) -> None:
        """Test successful PUT request."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"id": 1}'
        mock_response.json.return_value = {"id": 1}

        mock_client = MagicMock()
        mock_client.put.return_value = mock_response
        connection._client = mock_client

        result = connection.put("/test/1", data={"name": "updated"})

        assert result == {"id": 1}

    def test_delete_success(self, connection: Connection) -> None:
        """Test successful DELETE request."""
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_response.text = ""

        mock_client = MagicMock()
        mock_client.delete.return_value = mock_response
        connection._client = mock_client

        result = connection.delete("/test/1")

        assert result == {}

    def test_unauthorized_error(self, connection: Connection) -> None:
        """Test 401 response raises UnauthorizedError."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = '{"error": "unauthorized"}'
        mock_response.json.return_value = {"error": "unauthorized"}

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        connection._client = mock_client

        with pytest.raises(UnauthorizedError):
            connection.get("/test")

    def test_not_found_error(self, connection: Connection) -> None:
        """Test 404 response raises ResourceNotFoundError."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = '{"error": "not found"}'
        mock_response.json.return_value = {"error": "not found"}

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        connection._client = mock_client

        with pytest.raises(ResourceNotFoundError):
            connection.get("/test/999")

    def test_validation_error(self, connection: Connection) -> None:
        """Test 422 response raises ValidationError."""
        mock_response = MagicMock()
        mock_response.status_code = 422
        mock_response.text = '{"errors": {"amount": ["is required"]}}'
        mock_response.json.return_value = {"errors": {"amount": ["is required"]}}

        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        connection._client = mock_client

        with pytest.raises(ValidationError) as exc_info:
            connection.post("/test", data={})

        assert exc_info.value.errors == {"amount": ["is required"]}

    def test_api_error(self, connection: Connection) -> None:
        """Test 500 response raises APIError."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = '{"errors": [{"detail": "Server error"}]}'
        mock_response.json.return_value = {"errors": [{"detail": "Server error"}]}

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        connection._client = mock_client

        with pytest.raises(APIError) as exc_info:
            connection.get("/test")

        assert exc_info.value.status == 500

    def test_connection_error(self, connection: Connection) -> None:
        """Test network error raises ConnectionError."""
        mock_client = MagicMock()
        mock_client.get.side_effect = httpx.RequestError("Network error")
        connection._client = mock_client

        with pytest.raises(ConnectionError):
            connection.get("/test")

    def test_get_list(self, connection: Connection) -> None:
        """Test get_list returns data with pagination."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '[{"id": 1}, {"id": 2}]'
        mock_response.json.return_value = [{"id": 1}, {"id": 2}]
        mock_response.headers = {
            "X-Total-Count": "10",
            "X-Total-Pages": "5",
        }

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        connection._client = mock_client

        data, pagination = connection.get_list("/test", params={"page": 1})

        assert len(data) == 2
        assert pagination["total_count"] == 10
        assert pagination["total_pages"] == 5
