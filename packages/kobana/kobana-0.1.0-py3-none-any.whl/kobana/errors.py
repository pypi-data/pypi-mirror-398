"""Custom exception classes for Kobana SDK."""

from __future__ import annotations

from typing import Any


class KobanaError(Exception):
    """Base exception for all Kobana SDK errors."""

    def __init__(self, message: str = "An error occurred") -> None:
        self.message = message
        super().__init__(self.message)


class ConfigurationError(KobanaError):
    """Raised when there's a configuration issue."""

    def __init__(self, message: str = "Invalid configuration") -> None:
        super().__init__(message)


class ConnectionError(KobanaError):
    """Raised when there's a network or connection issue."""

    def __init__(self, message: str = "Connection failed") -> None:
        super().__init__(message)


class UnauthorizedError(KobanaError):
    """Raised when authentication fails (401 response)."""

    def __init__(self, message: str = "Unauthorized: Invalid or missing API token") -> None:
        super().__init__(message)


class ResourceNotFoundError(KobanaError):
    """Raised when a resource is not found (404 response)."""

    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message)


class ValidationError(KobanaError):
    """Raised when validation fails (422 response)."""

    def __init__(
        self,
        message: str = "Validation failed",
        errors: dict[str, list[str]] | None = None,
    ) -> None:
        self.errors = errors or {}
        super().__init__(message)

    def __str__(self) -> str:
        if self.errors:
            error_details = "; ".join(
                f"{field}: {', '.join(messages)}" for field, messages in self.errors.items()
            )
            return f"{self.message}: {error_details}"
        return self.message


class APIError(KobanaError):
    """Raised for general API errors."""

    def __init__(
        self,
        message: str = "API error",
        status: int | None = None,
        response_body: dict[str, Any] | None = None,
        errors: list[dict[str, str]] | None = None,
    ) -> None:
        self.status = status
        self.response_body = response_body or {}
        self.errors = errors or []
        super().__init__(message)

    def __str__(self) -> str:
        parts = [self.message]
        if self.status:
            parts.append(f"(status: {self.status})")
        if self.errors:
            error_details = "; ".join(
                e.get("detail", e.get("title", str(e))) for e in self.errors
            )
            parts.append(f"- {error_details}")
        return " ".join(parts)
