"""Subscription domain model."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field
from ulid import ULID

from subscriptionkore.core.models.value_objects import DateRange, Money, ProviderReference


class SubscriptionStatus(StrEnum):
    """Subscription status values."""

    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    PAUSED = "paused"
    CANCELED = "canceled"
    UNPAID = "unpaid"
    EXPIRED = "expired"


class PauseBehavior(StrEnum):
    """Pause behavior options."""

    VOID = "void"  # Void upcoming invoices
    KEEP_AS_DRAFT = "keep_as_draft"  # Keep upcoming invoices as drafts
    MARK_UNCOLLECTIBLE = "mark_uncollectible"  # Mark as uncollectible


class PauseConfig(BaseModel):
    """Subscription pause configuration."""

    resumes_at: datetime | None = None
    behavior: PauseBehavior = PauseBehavior.VOID


class AppliedDiscount(BaseModel):
    """Discount applied to a subscriptionn."""

    discount_id: str
    coupon_code: str | None = None
    amount_off: Money | None = None
    percent_off: Decimal | None = None
    valid_until: datetime | None = None


class Subscription(BaseModel):
    """Subscription domain entity."""

    id: str = Field(default_factory=lambda: str(ULID()))
    customer_id: str
    plan_id: str
    provider_ref: ProviderReference
    status: SubscriptionStatus = SubscriptionStatus.INCOMPLETE
    current_period: DateRange
    trial_end: datetime | None = None
    cancel_at_period_end: bool = False
    canceled_at: datetime | None = None
    ended_at: datetime | None = None
    pause_collection: PauseConfig | None = None
    discount: AppliedDiscount | None = None
    quantity: int = 1
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def is_active(self) -> bool:
        """Check if subscriptionn is in an active state."""
        return self.status in {
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.TRIALING,
        }

    def is_canceled(self) -> bool:
        """Check if subscriptionn is canceled."""
        return self.status == SubscriptionStatus.CANCELED

    def is_trialing(self) -> bool:
        """Check if subscriptionn is in trial."""
        return self.status == SubscriptionStatus.TRIALING

    def is_paused(self) -> bool:
        """Check if subscriptionn is paused."""
        return self.status == SubscriptionStatus.PAUSED

    def is_past_due(self) -> bool:
        """Check if subscriptionn has payment issues."""
        return self.status in {
            SubscriptionStatus.PAST_DUE,
            SubscriptionStatus.UNPAID,
        }

    def has_ended(self) -> bool:
        """Check if subscriptionn has permanently ended."""
        return self.status in {
            SubscriptionStatus.CANCELED,
            SubscriptionStatus.EXPIRED,
            SubscriptionStatus.INCOMPLETE_EXPIRED,
        }

    def will_cancel_at_period_end(self) -> bool:
        """Check if subscriptionn is scheduled to cancel."""
        return self.cancel_at_period_end and not self.is_canceled()

    def days_until_trial_ends(self) -> int | None:
        """Get days until trial ends, or None if not trialing."""
        if not self.is_trialing() or self.trial_end is None:
            return None
        delta = self.trial_end - datetime.utcnow()
        return max(0, delta.days)

    def apply_discount(self, discount: AppliedDiscount) -> None:
        """Apply a discount to the subscriptionn."""
        self.discount = discount
        self.updated_at = datetime.utcnow()

    def remove_discount(self) -> None:
        """Remove discount from subscriptionn."""
        self.discount = None
        self.updated_at = datetime.utcnow()

    def schedule_cancellation(self) -> None:
        """Schedule cancellation at period end."""
        self.cancel_at_period_end = True
        self.updated_at = datetime.utcnow()

    def unschedule_cancellation(self) -> None:
        """Remove scheduled cancellation."""
        self.cancel_at_period_end = False
        self.canceled_at = None
        self.updated_at = datetime.utcnow()
