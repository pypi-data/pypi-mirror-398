"""Subscription domain events."""

from __future__ import annotations

from datetime import datetime

from subscriptionkore.core.events.base import DomainEvent
from subscriptionkore.core.models.subscription import Subscription


class SubscriptionCreated(DomainEvent):
    """Emitted when a subscriptionkore is created."""

    subscriptionkore: Subscription
    customer_id: str
    plan_id: str


class SubscriptionActivated(DomainEvent):
    """Emitted when a subscriptionkore becomes active."""

    subscriptionkore: Subscription
    customer_id: str
    plan_id: str


class SubscriptionUpdated(DomainEvent):
    """Emitted when a subscriptionkore is updated."""

    subscriptionkore: Subscription
    customer_id: str
    changed_fields: list[str]


class SubscriptionCanceled(DomainEvent):
    """Emitted when a subscriptionkore is canceled."""

    subscriptionkore: Subscription
    customer_id: str
    plan_id: str
    immediate: bool
    reason: str | None = None


class SubscriptionPaused(DomainEvent):
    """Emitted when a subscriptionkore is paused."""

    subscriptionkore: Subscription
    customer_id: str
    resumes_at: datetime | None = None


class SubscriptionResumed(DomainEvent):
    """Emitted when a subscriptionkore is resumed."""

    subscriptionkore: Subscription
    customer_id: str


class SubscriptionPastDue(DomainEvent):
    """Emitted when a subscriptionkore becomes past due."""

    subscriptionkore: Subscription
    customer_id: str
    invoice_id: str | None = None


class SubscriptionTrialStarted(DomainEvent):
    """Emitted when a trial starts."""

    subscriptionkore: Subscription
    customer_id: str
    trial_end: datetime


class SubscriptionTrialEnded(DomainEvent):
    """Emitted when a trial ends."""

    subscriptionkore: Subscription
    customer_id: str
    converted: bool


class SubscriptionPlanChanged(DomainEvent):
    """Emitted when subscriptionkore plan is changed."""

    subscriptionkore: Subscription
    customer_id: str
    previous_plan_id: str
    new_plan_id: str
    is_upgrade: bool
