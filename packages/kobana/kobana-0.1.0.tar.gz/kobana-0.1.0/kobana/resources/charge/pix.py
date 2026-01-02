"""Pix charge resource for Kobana SDK."""

from __future__ import annotations

from typing import Any

from kobana.resources.base import BaseResource


class Pix(BaseResource):
    """
    Pix charge resource.

    Represents a Brazilian Pix instant payment charge.

    Attributes:
        id: Unique identifier
        amount: Charge amount in BRL
        status: Current status
        expire_in_seconds: Time until expiration in seconds
        customer_person_name: Customer's full name
        customer_cnpj_cpf: Customer's CPF or CNPJ
        customer_email: Customer's email
        description: Charge description
        pix_key: Pix key for payment
        qr_code: QR code data
        qr_code_url: QR code image URL
        paid_at: Payment date
        paid_amount: Amount paid
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    _endpoint = "/v1/pix_charges"

    # Status constants
    STATUS_PENDING = "pending"
    STATUS_PAID = "paid"
    STATUS_EXPIRED = "expired"
    STATUS_CANCELED = "canceled"

    @classmethod
    def all(
        cls,
        status: str | None = None,
        cnpj_cpf: str | None = None,
        created_from: str | None = None,
        created_to: str | None = None,
        paid_from: str | None = None,
        paid_to: str | None = None,
        page: int = 1,
        per_page: int = 25,
        **kwargs: Any,
    ) -> Any:
        """
        List Pix charges with optional filters.

        Args:
            status: Filter by status
            cnpj_cpf: Filter by customer document
            created_from: Filter by creation date (from)
            created_to: Filter by creation date (to)
            paid_from: Filter by payment date (from)
            paid_to: Filter by payment date (to)
            page: Page number
            per_page: Items per page (max 50)

        Returns:
            PaginatedList of Pix instances
        """
        params: dict[str, Any] = {"page": page, "per_page": min(per_page, 50)}

        if status:
            params["status"] = status
        if cnpj_cpf:
            params["cnpj_cpf"] = cnpj_cpf
        if created_from:
            params["created_from"] = created_from
        if created_to:
            params["created_to"] = created_to
        if paid_from:
            params["paid_from"] = paid_from
        if paid_to:
            params["paid_to"] = paid_to

        params.update(kwargs)
        return super().all(**params)

    @property
    def is_paid(self) -> bool:
        """Check if the charge is paid."""
        return self.status == self.STATUS_PAID

    @property
    def is_pending(self) -> bool:
        """Check if the charge is pending."""
        return self.status == self.STATUS_PENDING

    @property
    def is_expired(self) -> bool:
        """Check if the charge is expired."""
        return self.status == self.STATUS_EXPIRED

    @property
    def is_canceled(self) -> bool:
        """Check if the charge is canceled."""
        return self.status == self.STATUS_CANCELED
