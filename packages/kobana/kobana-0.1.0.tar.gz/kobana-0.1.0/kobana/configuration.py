"""Configuration management for Kobana SDK."""

from __future__ import annotations

import os
from typing import Literal

from dotenv import load_dotenv

from kobana.errors import ConfigurationError

# Load environment variables from .env file
load_dotenv()

Environment = Literal["sandbox", "production"]

BASE_URLS: dict[Environment, str] = {
    "sandbox": "https://api-sandbox.kobana.com.br",
    "production": "https://api.kobana.com.br",
}


class Configuration:
    """Configuration settings for Kobana API client."""

    def __init__(
        self,
        api_token: str | None = None,
        environment: Environment | None = None,
        custom_headers: dict[str, str] | None = None,
        debug: bool | None = None,
        timeout: float = 30.0,
    ) -> None:
        """
        Initialize configuration.

        Args:
            api_token: API token. Falls back to KOBANA_API_TOKEN env var.
            environment: sandbox or production. Falls back to KOBANA_ENVIRONMENT env var.
            custom_headers: Additional headers to send with requests.
            debug: Enable debug logging. Falls back to KOBANA_DEBUG env var.
            timeout: Request timeout in seconds.
        """
        # API Token: use explicit value, fall back to env var
        if api_token is not None:
            self.api_token = api_token
        else:
            self.api_token = os.getenv("KOBANA_API_TOKEN", "")

        # Environment: use explicit value, fall back to env var, default to sandbox
        if environment is not None:
            self.environment: Environment = environment
        else:
            env_environment = os.getenv("KOBANA_ENVIRONMENT", "").lower()
            if env_environment in ("sandbox", "production"):
                self.environment = env_environment  # type: ignore[assignment]
            else:
                self.environment = "sandbox"

        # Debug: use explicit value, fall back to env var, default to False
        if debug is not None:
            self.debug = debug
        else:
            env_debug = os.getenv("KOBANA_DEBUG", "").lower()
            self.debug = env_debug in ("true", "1", "yes")

        self.custom_headers = custom_headers or {}
        self.timeout = timeout

    @property
    def base_url(self) -> str:
        """Get the base URL for the configured environment."""
        return BASE_URLS[self.environment]

    def validate(self) -> None:
        """Validate that required configuration is present."""
        if not self.api_token:
            raise ConfigurationError(
                "API token is required. Set KOBANA_API_TOKEN environment variable "
                "or pass api_token to configure()."
            )

    def to_dict(self) -> dict[str, str | bool | float | dict[str, str]]:
        """Convert configuration to dictionary (excluding sensitive data)."""
        return {
            "environment": self.environment,
            "base_url": self.base_url,
            "debug": self.debug,
            "timeout": self.timeout,
        }
