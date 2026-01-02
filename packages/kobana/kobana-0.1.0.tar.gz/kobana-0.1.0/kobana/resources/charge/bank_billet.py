"""Bank Billet (Boleto) resource for Kobana SDK."""

from __future__ import annotations

from typing import Any, Self

from kobana.resources.base import BaseResource


class BankBillet(BaseResource):
    """
    Bank Billet (Boleto) resource.

    Represents a Brazilian bank billet (boleto bancário) for billing customers.

    Attributes:
        id: Unique identifier
        bank_billet_account_id: Associated billing account ID
        amount: Billet amount in BRL
        expire_at: Expiration date
        status: Current status (generating, opened, paid, canceled, etc.)
        customer_person_name: Customer's full name
        customer_cnpj_cpf: Customer's CPF or CNPJ
        customer_email: Customer's email
        customer_phone_number: Customer's phone
        customer_address: Customer's address
        customer_city_name: Customer's city
        customer_state: Customer's state (UF)
        customer_zipcode: Customer's ZIP code
        description: Billet description
        instructions: Payment instructions
        our_number: Bank-assigned number
        document_number: Custom document number
        discount_type: Type of discount (percentage, fixed)
        discount_value: Discount value
        discount_limit_date: Last date for discount
        interest_type: Type of interest (percentage, daily_fixed)
        interest_value: Interest value
        fine_type: Type of fine (percentage, fixed)
        fine_value: Fine value
        paid_at: Payment date
        paid_amount: Amount paid
        shorten_url: Shortened URL for billet
        url: Full URL for billet
        pdf_url: PDF download URL
    """

    _endpoint = "/v1/bank_billets"

    # Status constants
    STATUS_GENERATING = "generating"
    STATUS_GENERATION_FAILED = "generation_failed"
    STATUS_VALIDATION_FAILED = "validation_failed"
    STATUS_OPENED = "opened"
    STATUS_CANCELED = "canceled"
    STATUS_PAID = "paid"
    STATUS_OVERDUE = "overdue"
    STATUS_BLOCKED = "blocked"
    STATUS_CHARGEBACK = "chargeback"

    @classmethod
    def all(
        cls,
        bank_billet_account_id: int | None = None,
        status: str | None = None,
        our_number: str | None = None,
        cnpj_cpf: str | None = None,
        created_from: str | None = None,
        created_to: str | None = None,
        expire_from: str | None = None,
        expire_to: str | None = None,
        paid_from: str | None = None,
        paid_to: str | None = None,
        page: int = 1,
        per_page: int = 25,
        **kwargs: Any,
    ) -> Any:
        """
        List bank billets with optional filters.

        Args:
            bank_billet_account_id: Filter by billing account
            status: Filter by status
            our_number: Filter by our number
            cnpj_cpf: Filter by customer document
            created_from: Filter by creation date (from)
            created_to: Filter by creation date (to)
            expire_from: Filter by expiration date (from)
            expire_to: Filter by expiration date (to)
            paid_from: Filter by payment date (from)
            paid_to: Filter by payment date (to)
            page: Page number
            per_page: Items per page (max 50)

        Returns:
            PaginatedList of BankBillet instances
        """
        params: dict[str, Any] = {"page": page, "per_page": min(per_page, 50)}

        if bank_billet_account_id:
            params["bank_billet_account_id"] = bank_billet_account_id
        if status:
            params["status"] = status
        if our_number:
            params["our_number"] = our_number
        if cnpj_cpf:
            params["cnpj_cpf"] = cnpj_cpf
        if created_from:
            params["created_from"] = created_from
        if created_to:
            params["created_to"] = created_to
        if expire_from:
            params["expire_from"] = expire_from
        if expire_to:
            params["expire_to"] = expire_to
        if paid_from:
            params["paid_from"] = paid_from
        if paid_to:
            params["paid_to"] = paid_to

        params.update(kwargs)
        return super().all(**params)

    def cancel(self) -> bool:
        """Cancel this bank billet."""
        if not self._persisted or not self.id:
            raise ValueError("Cannot cancel a billet that hasn't been persisted.")
        connection = self.get_connection()
        data = connection.put(f"{self._endpoint}/{self.id}/cancel")
        self._attributes.update(data)
        return True

    def duplicate(
        self,
        expire_at: str | None = None,
        amount: float | None = None,
    ) -> Self:
        """
        Create a duplicate of this bank billet.

        Args:
            expire_at: New expiration date (optional)
            amount: New amount (optional)

        Returns:
            New BankBillet instance
        """
        if not self._persisted or not self.id:
            raise ValueError("Cannot duplicate a billet that hasn't been persisted.")
        connection = self.get_connection()
        data: dict[str, Any] = {}
        if expire_at:
            data["expire_at"] = expire_at
        if amount:
            data["amount"] = amount
        result = connection.post(f"{self._endpoint}/{self.id}/duplicate", data=data or None)
        instance = type(self)(**result)
        instance._persisted = True
        return instance

    @property
    def is_paid(self) -> bool:
        """Check if the billet is paid."""
        return self.status == self.STATUS_PAID

    @property
    def is_opened(self) -> bool:
        """Check if the billet is open/pending."""
        return self.status == self.STATUS_OPENED

    @property
    def is_canceled(self) -> bool:
        """Check if the billet is canceled."""
        return self.status == self.STATUS_CANCELED

    @property
    def is_overdue(self) -> bool:
        """Check if the billet is overdue."""
        return self.status == self.STATUS_OVERDUE
