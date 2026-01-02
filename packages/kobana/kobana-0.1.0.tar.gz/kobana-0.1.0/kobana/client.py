"""Kobana API client implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from kobana.configuration import Configuration
from kobana.connection import Connection
from kobana.resources.charge import BankBillet, Pix
from kobana.resources.financial import Account, BankBilletAccount

if TYPE_CHECKING:
    from kobana.configuration import Environment


class ChargeProxy:
    """Proxy for charge-related resources."""

    def __init__(self, connection: Connection) -> None:
        self._connection = connection
        self._bank_billet: type[BankBillet] | None = None
        self._pix: type[Pix] | None = None

    @property
    def bank_billet(self) -> type[BankBillet]:
        """Get BankBillet resource class with connection."""
        if self._bank_billet is None:
            # Create a subclass with the connection set
            class BoundBankBillet(BankBillet):
                pass

            BoundBankBillet.set_connection(self._connection)
            self._bank_billet = BoundBankBillet
        return self._bank_billet

    @property
    def pix(self) -> type[Pix]:
        """Get Pix resource class with connection."""
        if self._pix is None:

            class BoundPix(Pix):
                pass

            BoundPix.set_connection(self._connection)
            self._pix = BoundPix
        return self._pix


class FinancialProxy:
    """Proxy for financial-related resources."""

    def __init__(self, connection: Connection) -> None:
        self._connection = connection
        self._bank_billet_account: type[BankBilletAccount] | None = None
        self._account: type[Account] | None = None

    @property
    def bank_billet_account(self) -> type[BankBilletAccount]:
        """Get BankBilletAccount resource class with connection."""
        if self._bank_billet_account is None:

            class BoundBankBilletAccount(BankBilletAccount):
                pass

            BoundBankBilletAccount.set_connection(self._connection)
            self._bank_billet_account = BoundBankBilletAccount
        return self._bank_billet_account

    @property
    def account(self) -> type[Account]:
        """Get Account resource class with connection."""
        if self._account is None:

            class BoundAccount(Account):
                pass

            BoundAccount.set_connection(self._connection)
            self._account = BoundAccount
        return self._account


class KobanaClient:
    """
    Kobana API client for multi-tenant or instance-based usage.

    Example:
        client = KobanaClient(api_token="your-token", environment="sandbox")
        billets = client.charge.bank_billet.all()
        pix_charges = client.charge.pix.all()
        accounts = client.financial.bank_billet_account.all()
    """

    def __init__(
        self,
        api_token: str | None = None,
        environment: "Environment" = "sandbox",
        custom_headers: dict[str, str] | None = None,
        debug: bool = False,
        timeout: float = 30.0,
    ) -> None:
        """
        Initialize the Kobana client.

        Args:
            api_token: Kobana API token (can also be set via KOBANA_API_TOKEN env var)
            environment: API environment ("sandbox" or "production")
            custom_headers: Additional HTTP headers to send with each request
            debug: Enable debug logging
            timeout: Request timeout in seconds
        """
        self._configuration = Configuration(
            api_token=api_token or "",
            environment=environment,
            custom_headers=custom_headers or {},
            debug=debug,
            timeout=timeout,
        )
        self._connection: Connection | None = None
        self._charge_proxy: ChargeProxy | None = None
        self._financial_proxy: FinancialProxy | None = None

    def configure(
        self,
        api_token: str | None = None,
        environment: "Environment | None" = None,
        custom_headers: dict[str, str] | None = None,
        debug: bool | None = None,
        timeout: float | None = None,
    ) -> None:
        """
        Update client configuration.

        Resets the connection and resource proxies when configuration changes.
        """
        if api_token is not None:
            self._configuration.api_token = api_token
        if environment is not None:
            self._configuration.environment = environment
        if custom_headers is not None:
            self._configuration.custom_headers = custom_headers
        if debug is not None:
            self._configuration.debug = debug
        if timeout is not None:
            self._configuration.timeout = timeout

        # Reset connection and proxies
        if self._connection is not None:
            self._connection.close()
            self._connection = None
        self._charge_proxy = None
        self._financial_proxy = None

    @property
    def configuration(self) -> Configuration:
        """Get the current configuration."""
        return self._configuration

    @property
    def connection(self) -> Connection:
        """Get the HTTP connection (creates one if needed)."""
        if self._connection is None:
            self._configuration.validate()
            self._connection = Connection(self._configuration)
        return self._connection

    @property
    def charge(self) -> ChargeProxy:
        """Access charge-related resources (bank_billet, pix)."""
        if self._charge_proxy is None:
            self._charge_proxy = ChargeProxy(self.connection)
        return self._charge_proxy

    @property
    def financial(self) -> FinancialProxy:
        """Access financial resources (bank_billet_account, account)."""
        if self._financial_proxy is None:
            self._financial_proxy = FinancialProxy(self.connection)
        return self._financial_proxy

    def close(self) -> None:
        """Close the HTTP connection."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def __enter__(self) -> "KobanaClient":
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()
