"""Tests for KobanaClient class."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from kobana import KobanaClient
from kobana.client import ChargeProxy, FinancialProxy
from kobana.connection import Connection


class TestKobanaClient:
    """Tests for KobanaClient class."""

    def test_initialization_defaults(self) -> None:
        """Test client initialization with defaults."""
        client = KobanaClient(api_token="test-token")

        assert client.configuration.api_token == "test-token"
        assert client.configuration.environment == "sandbox"
        assert client.configuration.debug is False

    def test_initialization_custom(self) -> None:
        """Test client initialization with custom values."""
        client = KobanaClient(
            api_token="my-token",
            environment="production",
            debug=True,
            timeout=60.0,
            custom_headers={"X-Custom": "header"},
        )

        assert client.configuration.api_token == "my-token"
        assert client.configuration.environment == "production"
        assert client.configuration.debug is True
        assert client.configuration.timeout == 60.0
        assert client.configuration.custom_headers == {"X-Custom": "header"}

    def test_configure_updates_settings(self) -> None:
        """Test that configure() updates settings."""
        client = KobanaClient(api_token="initial-token")
        client.configure(
            api_token="new-token",
            environment="production",
        )

        assert client.configuration.api_token == "new-token"
        assert client.configuration.environment == "production"

    def test_configure_resets_connection(self) -> None:
        """Test that configure() resets the connection."""
        client = KobanaClient(api_token="test-token")

        # Create connection
        with patch.object(Connection, "_create_client"):
            _ = client.connection

        # Reconfigure
        client.configure(api_token="new-token")

        # Connection should be None
        assert client._connection is None

    def test_charge_proxy(self) -> None:
        """Test charge proxy access."""
        client = KobanaClient(api_token="test-token")

        with patch.object(Connection, "_create_client"):
            charge = client.charge

        assert isinstance(charge, ChargeProxy)

    def test_financial_proxy(self) -> None:
        """Test financial proxy access."""
        client = KobanaClient(api_token="test-token")

        with patch.object(Connection, "_create_client"):
            financial = client.financial

        assert isinstance(financial, FinancialProxy)

    def test_context_manager(self) -> None:
        """Test client as context manager."""
        with patch.object(Connection, "_create_client"):
            with KobanaClient(api_token="test-token") as client:
                # Force connection creation
                _ = client.connection

            # Connection should be closed
            assert client._connection is None

    def test_close(self) -> None:
        """Test client close method."""
        client = KobanaClient(api_token="test-token")

        with patch.object(Connection, "_create_client"):
            _ = client.connection

        client.close()
        assert client._connection is None


class TestChargeProxy:
    """Tests for ChargeProxy class."""

    def test_bank_billet_property(self) -> None:
        """Test bank_billet property returns correct resource."""
        mock_connection = MagicMock(spec=Connection)
        proxy = ChargeProxy(mock_connection)

        bank_billet = proxy.bank_billet
        assert bank_billet is not None
        assert hasattr(bank_billet, "create")
        assert hasattr(bank_billet, "find")
        assert hasattr(bank_billet, "all")

    def test_pix_property(self) -> None:
        """Test pix property returns correct resource."""
        mock_connection = MagicMock(spec=Connection)
        proxy = ChargeProxy(mock_connection)

        pix = proxy.pix
        assert pix is not None
        assert hasattr(pix, "create")
        assert hasattr(pix, "find")
        assert hasattr(pix, "all")

    def test_resources_cached(self) -> None:
        """Test that resources are cached."""
        mock_connection = MagicMock(spec=Connection)
        proxy = ChargeProxy(mock_connection)

        bank_billet1 = proxy.bank_billet
        bank_billet2 = proxy.bank_billet

        assert bank_billet1 is bank_billet2


class TestFinancialProxy:
    """Tests for FinancialProxy class."""

    def test_bank_billet_account_property(self) -> None:
        """Test bank_billet_account property returns correct resource."""
        mock_connection = MagicMock(spec=Connection)
        proxy = FinancialProxy(mock_connection)

        account = proxy.bank_billet_account
        assert account is not None
        assert hasattr(account, "create")
        assert hasattr(account, "find")
        assert hasattr(account, "all")

    def test_account_property(self) -> None:
        """Test account property returns correct resource."""
        mock_connection = MagicMock(spec=Connection)
        proxy = FinancialProxy(mock_connection)

        account = proxy.account
        assert account is not None
        assert hasattr(account, "current")
        assert hasattr(account, "balance")

    def test_resources_cached(self) -> None:
        """Test that resources are cached."""
        mock_connection = MagicMock(spec=Connection)
        proxy = FinancialProxy(mock_connection)

        account1 = proxy.bank_billet_account
        account2 = proxy.bank_billet_account

        assert account1 is account2
