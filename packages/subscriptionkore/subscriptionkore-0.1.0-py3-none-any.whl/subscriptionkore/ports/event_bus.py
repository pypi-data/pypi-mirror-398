"""Event bus port interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import TypeVar

from subscriptionkore.core.events import DomainEvent

E = TypeVar("E", bound=DomainEvent)
EventHandler = Callable[[E], Awaitable[None]]


class EventBusPort(ABC):
    """Abstract interface for domain event bus."""

    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """Publish a domain event."""
        ...

    @abstractmethod
    async def publish_many(self, events: list[DomainEvent]) -> None:
        """Publish multiple domain events."""
        ...

    @abstractmethod
    def subscribe(
        self,
        event_type: type[E],
        handler: EventHandler[E],
    ) -> None:
        """Subscribe a handler to an event type."""
        ...

    @abstractmethod
    def unsubscribe(
        self,
        event_type: type[E],
        handler: EventHandler[E],
    ) -> None:
        """Unsubscribe a handler from an event type."""
        ...
