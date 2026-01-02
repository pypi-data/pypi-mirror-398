"""Payment domain events."""

from __future__ import annotations

from subscriptionkore.core.events.base import DomainEvent
from subscriptionkore.core.models.invoice import Invoice
from subscriptionkore.core.models.payment_event import PaymentEvent
from subscriptionkore.core.models.value_objects import Money


class PaymentSucceeded(DomainEvent):
    """Emitted when a payment succeeds."""

    payment_event: PaymentEvent
    customer_id: str
    subscription_id: str | None = None
    invoice_id: str | None = None
    amount: Money


class PaymentFailed(DomainEvent):
    """Emitted when a payment fails."""

    payment_event: PaymentEvent
    customer_id: str
    subscription_id: str | None = None
    invoice_id: str | None = None
    amount: Money
    failure_reason: str | None = None
    failure_code: str | None = None
    attempt_count: int = 1


class InvoiceCreated(DomainEvent):
    """Emitted when an invoice is created."""

    invoice: Invoice
    customer_id: str
    subscription_id: str | None = None


class InvoicePaid(DomainEvent):
    """Emitted when an invoice is paid."""

    invoice: Invoice
    customer_id: str
    subscription_id: str | None = None
    amount_paid: Money
