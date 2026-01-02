"""Tests for Configuration class."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from kobana.configuration import Configuration
from kobana.errors import ConfigurationError


class TestConfiguration:
    """Tests for Configuration class."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        with patch.dict(os.environ, {}, clear=True):
            config = Configuration(api_token="test-token")

        assert config.api_token == "test-token"
        assert config.environment == "sandbox"
        assert config.debug is False
        assert config.timeout == 30.0
        assert config.custom_headers == {}

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = Configuration(
            api_token="my-token",
            environment="production",
            debug=True,
            timeout=60.0,
            custom_headers={"X-Custom": "value"},
        )

        assert config.api_token == "my-token"
        assert config.environment == "production"
        assert config.debug is True
        assert config.timeout == 60.0
        assert config.custom_headers == {"X-Custom": "value"}

    def test_environment_variables(self) -> None:
        """Test loading configuration from environment variables."""
        env_vars = {
            "KOBANA_API_TOKEN": "env-token",
            "KOBANA_ENVIRONMENT": "production",
            "KOBANA_DEBUG": "true",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = Configuration()

        assert config.api_token == "env-token"
        assert config.environment == "production"
        assert config.debug is True

    def test_explicit_values_override_env(self) -> None:
        """Test that explicit values override environment variables."""
        env_vars = {
            "KOBANA_API_TOKEN": "env-token",
            "KOBANA_ENVIRONMENT": "production",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = Configuration(
                api_token="explicit-token",
                environment="sandbox",
            )

        assert config.api_token == "explicit-token"
        assert config.environment == "sandbox"

    def test_base_url_sandbox(self) -> None:
        """Test base URL for sandbox environment."""
        config = Configuration(api_token="test", environment="sandbox")
        assert config.base_url == "https://api-sandbox.kobana.com.br"

    def test_base_url_production(self) -> None:
        """Test base URL for production environment."""
        config = Configuration(api_token="test", environment="production")
        assert config.base_url == "https://api.kobana.com.br"

    def test_validate_success(self) -> None:
        """Test successful validation."""
        config = Configuration(api_token="valid-token")
        config.validate()  # Should not raise

    def test_validate_missing_token(self) -> None:
        """Test validation fails without API token."""
        with patch.dict(os.environ, {}, clear=True):
            config = Configuration()

        with pytest.raises(ConfigurationError) as exc_info:
            config.validate()

        assert "API token is required" in str(exc_info.value)

    def test_to_dict(self) -> None:
        """Test configuration to dictionary conversion."""
        config = Configuration(
            api_token="secret-token",
            environment="sandbox",
            debug=True,
            timeout=45.0,
        )
        result = config.to_dict()

        # Should not include api_token (sensitive)
        assert "api_token" not in result
        assert result["environment"] == "sandbox"
        assert result["debug"] is True
        assert result["timeout"] == 45.0
        assert "base_url" in result

    def test_debug_env_variations(self) -> None:
        """Test different debug environment variable values."""
        for value in ("true", "1", "yes"):
            with patch.dict(os.environ, {"KOBANA_DEBUG": value}, clear=True):
                config = Configuration(api_token="test")
                assert config.debug is True, f"Failed for debug value: {value}"

        for value in ("false", "0", "no", ""):
            with patch.dict(os.environ, {"KOBANA_DEBUG": value}, clear=True):
                config = Configuration(api_token="test")
                assert config.debug is False, f"Failed for debug value: {value}"
