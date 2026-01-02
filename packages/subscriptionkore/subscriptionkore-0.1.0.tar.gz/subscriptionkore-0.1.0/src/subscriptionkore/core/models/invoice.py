"""Invoice domain model."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field
from ulid import ULID

from subscriptionkore.core.models.value_objects import Currency, DateRange, Money, ProviderReference


class InvoiceStatus(StrEnum):
    """Invoice status values."""

    DRAFT = "draft"
    OPEN = "open"
    PAID = "paid"
    VOID = "void"
    UNCOLLECTIBLE = "uncollectible"


class InvoiceLineItem(BaseModel):
    """Line item on an invoice."""

    id: str = Field(default_factory=lambda: str(ULID()))
    description: str
    quantity: int = 1
    unit_amount: Money
    amount: Money
    period: DateRange | None = None
    proration: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class Invoice(BaseModel):
    """Invoice domain entity."""

    id: str = Field(default_factory=lambda: str(ULID()))
    customer_id: str
    subscriptionkore_id: str | None = None
    provider_ref: ProviderReference
    status: InvoiceStatus = InvoiceStatus.DRAFT
    subtotal: Money
    tax: Money = Field(default_factory=lambda: Money.zero())
    discount_amount: Money = Field(default_factory=lambda: Money.zero())
    total: Money
    amount_paid: Money = Field(default_factory=lambda: Money.zero())
    amount_due: Money
    currency: Currency = Currency.USD
    line_items: list[InvoiceLineItem] = Field(default_factory=list)
    period: DateRange | None = None
    due_date: datetime | None = None
    paid_at: datetime | None = None
    invoice_pdf_url: str | None = None
    hosted_invoice_url: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def is_paid(self) -> bool:
        """Check if invoice is fully paid."""
        return self.status == InvoiceStatus.PAID

    def is_open(self) -> bool:
        """Check if invoice is open for payment."""
        return self.status == InvoiceStatus.OPEN

    def is_overdue(self) -> bool:
        """Check if invoice is past due date."""
        if self.due_date is None or self.is_paid():
            return False
        return datetime.utcnow() > self.due_date

    def remaining_balance(self) -> Money:
        """Get remaining balance to be paid."""
        return self.amount_due - self.amount_paid
