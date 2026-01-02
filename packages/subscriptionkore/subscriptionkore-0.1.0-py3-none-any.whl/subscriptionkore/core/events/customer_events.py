"""Customer domain events."""

from __future__ import annotations

from subscriptionkore.core.events.base import DomainEvent
from subscriptionkore.core.models.customer import Customer


class CustomerCreated(DomainEvent):
    """Emitted when a customer is created."""

    customer: Customer


class CustomerUpdated(DomainEvent):
    """Emitted when a customer is updated."""

    customer: Customer
    changed_fields: list[str]
