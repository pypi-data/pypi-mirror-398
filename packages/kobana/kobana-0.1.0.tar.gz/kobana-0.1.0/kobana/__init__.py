"""
Kobana Python SDK.

A Python client library for the Kobana financial automation API.

Usage:
    # Global configuration (simple usage)
    import kobana

    kobana.configure(api_token="your-token", environment="sandbox")
    billets = kobana.charge.bank_billet.all()

    # Instance-based configuration (multi-tenant)
    from kobana import KobanaClient

    client = KobanaClient(api_token="your-token", environment="production")
    billets = client.charge.bank_billet.all()
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from kobana.client import ChargeProxy, FinancialProxy, KobanaClient
from kobana.configuration import Configuration
from kobana.connection import Connection
from kobana.errors import (
    APIError,
    ConfigurationError,
    ConnectionError,
    KobanaError,
    ResourceNotFoundError,
    UnauthorizedError,
    ValidationError,
)
from kobana.resources.base import BaseResource, PaginatedList
from kobana.resources.charge import BankBillet, Pix
from kobana.resources.financial import Account, BankBilletAccount

if TYPE_CHECKING:
    from kobana.configuration import Environment

__version__ = "0.1.0"
__all__ = [
    # Client
    "KobanaClient",
    "ChargeProxy",
    "FinancialProxy",
    # Configuration
    "Configuration",
    "Connection",
    # Errors
    "KobanaError",
    "ConfigurationError",
    "ConnectionError",
    "UnauthorizedError",
    "ResourceNotFoundError",
    "ValidationError",
    "APIError",
    # Resources
    "BaseResource",
    "PaginatedList",
    "BankBillet",
    "Pix",
    "BankBilletAccount",
    "Account",
    # Functions
    "configure",
    "charge",
    "financial",
]

# Global client instance for simple usage
_global_client: KobanaClient | None = None


def _get_global_client() -> KobanaClient:
    """Get the global client instance."""
    global _global_client
    if _global_client is None:
        _global_client = KobanaClient()
    return _global_client


def configure(
    api_token: str | None = None,
    environment: "Environment" = "sandbox",
    custom_headers: dict[str, str] | None = None,
    debug: bool = False,
    timeout: float = 30.0,
) -> None:
    """
    Configure the global Kobana client.

    Args:
        api_token: Kobana API token (can also be set via KOBANA_API_TOKEN env var)
        environment: API environment ("sandbox" or "production")
        custom_headers: Additional HTTP headers to send with each request
        debug: Enable debug logging
        timeout: Request timeout in seconds

    Example:
        import kobana

        kobana.configure(
            api_token="your-api-token",
            environment="sandbox",
        )
    """
    global _global_client
    _global_client = KobanaClient(
        api_token=api_token,
        environment=environment,
        custom_headers=custom_headers or {},
        debug=debug,
        timeout=timeout,
    )


@property  # type: ignore[misc]
def charge() -> ChargeProxy:
    """
    Access charge-related resources.

    Returns:
        ChargeProxy with access to bank_billet and pix resources

    Example:
        billets = kobana.charge.bank_billet.all()
        pix_charges = kobana.charge.pix.all()
    """
    return _get_global_client().charge


@property  # type: ignore[misc]
def financial() -> FinancialProxy:
    """
    Access financial resources.

    Returns:
        FinancialProxy with access to bank_billet_account and account resources

    Example:
        accounts = kobana.financial.bank_billet_account.all()
        current = kobana.financial.account.current()
    """
    return _get_global_client().financial


# Make the module properties work by using __getattr__
def __getattr__(name: str) -> ChargeProxy | FinancialProxy:
    """Module-level attribute access for charge and financial proxies."""
    if name == "charge":
        return _get_global_client().charge
    if name == "financial":
        return _get_global_client().financial
    raise AttributeError(f"module 'kobana' has no attribute '{name}'")
