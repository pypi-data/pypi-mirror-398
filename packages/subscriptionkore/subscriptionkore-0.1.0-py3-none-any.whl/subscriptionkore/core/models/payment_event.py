"""Payment event domain model."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field
from ulid import ULID

from subscriptionkore.core.models.value_objects import Money, ProviderReference


class PaymentEventType(StrEnum):
    """Payment event types."""

    PAYMENT_SUCCEEDED = "payment_succeeded"
    PAYMENT_FAILED = "payment_failed"
    PAYMENT_REFUNDED = "payment_refunded"
    PAYMENT_DISPUTED = "payment_disputed"


class PaymentStatus(StrEnum):
    """Payment status values."""

    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"
    DISPUTED = "disputed"


class PaymentEvent(BaseModel):
    """Payment event domain entity."""

    id: str = Field(default_factory=lambda: str(ULID()))
    provider_ref: ProviderReference
    customer_id: str
    subscriptionkore_id: str | None = None
    invoice_id: str | None = None
    event_type: PaymentEventType
    amount: Money
    status: PaymentStatus
    failure_reason: str | None = None
    failure_code: str | None = None
    payment_method_type: str | None = None
    payment_method_last4: str | None = None
    occurred_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def is_successful(self) -> bool:
        """Check if payment succeeded."""
        return self.status == PaymentStatus.SUCCEEDED

    def is_failed(self) -> bool:
        """Check if payment failed."""
        return self.status == PaymentStatus.FAILED
