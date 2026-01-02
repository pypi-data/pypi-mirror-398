"""Account resource for Kobana SDK."""

from __future__ import annotations

from typing import Any

from kobana.resources.base import BaseResource


class Account(BaseResource):
    """
    Account resource.

    Represents a Kobana account with balance information.

    Attributes:
        id: Unique identifier
        name: Account name
        email: Account email
        balance: Current balance in BRL
        available_balance: Available balance for withdrawal
        blocked_balance: Blocked balance
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    _endpoint = "/v1/accounts"

    @classmethod
    def current(cls) -> "Account":
        """
        Get the current account (the one associated with the API token).

        Returns:
            Account instance
        """
        connection = cls.get_connection()
        data = connection.get(f"{cls._endpoint}/current")
        instance = cls(**data)
        instance._persisted = True
        return instance

    @classmethod
    def balance(cls) -> dict[str, Any]:
        """
        Get the current account balance.

        Returns:
            Dictionary with balance information
        """
        connection = cls.get_connection()
        return connection.get(f"{cls._endpoint}/balance")
