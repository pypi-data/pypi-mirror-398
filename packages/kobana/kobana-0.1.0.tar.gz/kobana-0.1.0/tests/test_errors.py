"""Tests for error classes."""

from __future__ import annotations

import pytest

from kobana.errors import (
    APIError,
    ConfigurationError,
    ConnectionError,
    KobanaError,
    ResourceNotFoundError,
    UnauthorizedError,
    ValidationError,
)


class TestKobanaError:
    """Tests for base KobanaError class."""

    def test_default_message(self) -> None:
        """Test default error message."""
        error = KobanaError()
        assert str(error) == "An error occurred"

    def test_custom_message(self) -> None:
        """Test custom error message."""
        error = KobanaError("Custom error message")
        assert str(error) == "Custom error message"

    def test_is_exception(self) -> None:
        """Test that KobanaError is an Exception."""
        error = KobanaError()
        assert isinstance(error, Exception)


class TestConfigurationError:
    """Tests for ConfigurationError class."""

    def test_default_message(self) -> None:
        """Test default error message."""
        error = ConfigurationError()
        assert str(error) == "Invalid configuration"

    def test_custom_message(self) -> None:
        """Test custom error message."""
        error = ConfigurationError("Missing API token")
        assert str(error) == "Missing API token"

    def test_inheritance(self) -> None:
        """Test that ConfigurationError inherits from KobanaError."""
        error = ConfigurationError()
        assert isinstance(error, KobanaError)


class TestConnectionError:
    """Tests for ConnectionError class."""

    def test_default_message(self) -> None:
        """Test default error message."""
        error = ConnectionError()
        assert str(error) == "Connection failed"

    def test_inheritance(self) -> None:
        """Test that ConnectionError inherits from KobanaError."""
        error = ConnectionError()
        assert isinstance(error, KobanaError)


class TestUnauthorizedError:
    """Tests for UnauthorizedError class."""

    def test_default_message(self) -> None:
        """Test default error message."""
        error = UnauthorizedError()
        assert "Unauthorized" in str(error)

    def test_inheritance(self) -> None:
        """Test that UnauthorizedError inherits from KobanaError."""
        error = UnauthorizedError()
        assert isinstance(error, KobanaError)


class TestResourceNotFoundError:
    """Tests for ResourceNotFoundError class."""

    def test_default_message(self) -> None:
        """Test default error message."""
        error = ResourceNotFoundError()
        assert str(error) == "Resource not found"

    def test_inheritance(self) -> None:
        """Test that ResourceNotFoundError inherits from KobanaError."""
        error = ResourceNotFoundError()
        assert isinstance(error, KobanaError)


class TestValidationError:
    """Tests for ValidationError class."""

    def test_default_message(self) -> None:
        """Test default error message."""
        error = ValidationError()
        assert str(error) == "Validation failed"

    def test_with_errors(self) -> None:
        """Test error message with field errors."""
        errors = {
            "amount": ["is required", "must be positive"],
            "email": ["is invalid"],
        }
        error = ValidationError(errors=errors)
        error_str = str(error)

        assert "Validation failed" in error_str
        assert "amount" in error_str
        assert "email" in error_str

    def test_errors_attribute(self) -> None:
        """Test that errors dict is accessible."""
        errors = {"field": ["error1", "error2"]}
        error = ValidationError(errors=errors)
        assert error.errors == errors

    def test_empty_errors(self) -> None:
        """Test with empty errors dict."""
        error = ValidationError(errors={})
        assert str(error) == "Validation failed"

    def test_inheritance(self) -> None:
        """Test that ValidationError inherits from KobanaError."""
        error = ValidationError()
        assert isinstance(error, KobanaError)


class TestAPIError:
    """Tests for APIError class."""

    def test_default_message(self) -> None:
        """Test default error message."""
        error = APIError()
        assert "API error" in str(error)

    def test_with_status(self) -> None:
        """Test error message with status code."""
        error = APIError(message="Server error", status=500)
        error_str = str(error)
        assert "Server error" in error_str
        assert "500" in error_str

    def test_with_errors_list(self) -> None:
        """Test error message with errors list."""
        errors = [
            {"title": "Error", "code": "invalid", "detail": "Invalid input"},
        ]
        error = APIError(errors=errors)
        assert "Invalid input" in str(error)

    def test_attributes(self) -> None:
        """Test error attributes."""
        error = APIError(
            message="Test error",
            status=422,
            response_body={"key": "value"},
            errors=[{"detail": "test"}],
        )
        assert error.status == 422
        assert error.response_body == {"key": "value"}
        assert error.errors == [{"detail": "test"}]

    def test_inheritance(self) -> None:
        """Test that APIError inherits from KobanaError."""
        error = APIError()
        assert isinstance(error, KobanaError)
