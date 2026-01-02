"""Bank Billet Account resource for Kobana SDK."""

from __future__ import annotations

from typing import Any

from kobana.resources.base import BaseResource


class BankBilletAccount(BaseResource):
    """
    Bank Billet Account (Carteira de Cobrança) resource.

    Represents a billing wallet/account used to issue bank billets.

    Attributes:
        id: Unique identifier
        bank_contract_slug: Bank contract identifier
        beneficiary_name: Beneficiary's name
        beneficiary_cnpj_cpf: Beneficiary's CPF or CNPJ
        beneficiary_address: Beneficiary's address
        beneficiary_address_number: Address number
        beneficiary_address_neighborhood: Address neighborhood
        beneficiary_address_city_name: Address city
        beneficiary_address_state: Address state (UF)
        beneficiary_address_zipcode: Address ZIP code
        kind: Account type
        agency: Bank agency number
        account: Bank account number
        account_digit: Account check digit
        status: Account status
        homologated_at: Homologation date
        is_default: Whether this is the default account
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    _endpoint = "/v1/bank_billet_accounts"

    # Status constants
    STATUS_PENDING = "pending"
    STATUS_HOMOLOGATING = "homologating"
    STATUS_ACTIVE = "active"
    STATUS_INACTIVE = "inactive"

    @classmethod
    def all(
        cls,
        status: str | None = None,
        page: int = 1,
        per_page: int = 25,
        **kwargs: Any,
    ) -> Any:
        """
        List bank billet accounts with optional filters.

        Args:
            status: Filter by status
            page: Page number
            per_page: Items per page (max 50)

        Returns:
            PaginatedList of BankBilletAccount instances
        """
        params: dict[str, Any] = {"page": page, "per_page": min(per_page, 50)}

        if status:
            params["status"] = status

        params.update(kwargs)
        return super().all(**params)

    def ask_homologation(self) -> bool:
        """
        Request account homologation from the bank.

        Returns:
            True if the request was successful
        """
        if not self._persisted or not self.id:
            raise ValueError("Cannot request homologation for an account that hasn't been persisted.")
        connection = self.get_connection()
        data = connection.get(f"{self._endpoint}/{self.id}/ask")
        self._attributes.update(data)
        return True

    def validate(self) -> bool:
        """
        Validate/homologate the account.

        Returns:
            True if validation was successful
        """
        if not self._persisted or not self.id:
            raise ValueError("Cannot validate an account that hasn't been persisted.")
        connection = self.get_connection()
        data = connection.put(f"{self._endpoint}/{self.id}/validate")
        self._attributes.update(data)
        return True

    def set_default(self) -> bool:
        """
        Set this account as the default billing account.

        Returns:
            True if the operation was successful
        """
        if not self._persisted or not self.id:
            raise ValueError("Cannot set default for an account that hasn't been persisted.")
        connection = self.get_connection()
        data = connection.put(f"{self._endpoint}/{self.id}/set_default")
        self._attributes.update(data)
        return True

    @property
    def is_active(self) -> bool:
        """Check if the account is active."""
        return self.status == self.STATUS_ACTIVE

    @property
    def is_pending(self) -> bool:
        """Check if the account is pending."""
        return self.status == self.STATUS_PENDING

    @property
    def is_homologating(self) -> bool:
        """Check if the account is being homologated."""
        return self.status == self.STATUS_HOMOLOGATING
