"""In-memory event bus implementation."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any

import structlog

from subscriptionkore.core.events import DomainEvent
from subscriptionkore.ports.event_bus import EventBusPort, EventHandler

logger = structlog.get_logger()


class InMemoryEventBus(EventBusPort):
    """
    In-memory event bus implementation.

    Suitable for single-process applications.
    For distributed systems, use a message broker implementation.
    """

    def __init__(self) -> None:
        self._handlers: dict[type[DomainEvent], list[EventHandler[Any]]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def publish(self, event: DomainEvent) -> None:
        """Publish a single event."""
        log = logger.bind(event_type=type(event).__name__, event_id=event.event_id)
        log.debug("Publishing event")

        handlers = self._handlers.get(type(event), [])

        if not handlers:
            log.debug("No handlers registered for event")
            return

        # Execute handlers concurrently
        tasks = [self._execute_handler(handler, event) for handler in handlers]
        await asyncio.gather(*tasks, return_exceptions=True)

        log.debug("Event published", handler_count=len(handlers))

    async def publish_many(self, events: list[DomainEvent]) -> None:
        """Publish multiple events."""
        for event in events:
            await self.publish(event)

    def subscribe(
        self,
        event_type: type[DomainEvent],
        handler: EventHandler[Any],
    ) -> None:
        """Subscribe a handler to an event type."""
        self._handlers[event_type].append(handler)
        logger.debug(
            "Handler subscribed",
            event_type=event_type.__name__,
            handler=handler.__name__ if hasattr(handler, "__name__") else str(handler),
        )

    def unsubscribe(
        self,
        event_type: type[DomainEvent],
        handler: EventHandler[Any],
    ) -> None:
        """Unsubscribe a handler from an event type."""
        handlers = self._handlers.get(event_type, [])
        if handler in handlers:
            handlers.remove(handler)
            logger.debug(
                "Handler unsubscribed",
                event_type=event_type.__name__,
            )

    async def _execute_handler(
        self,
        handler: EventHandler[Any],
        event: DomainEvent,
    ) -> None:
        """Execute a handler with error handling."""
        try:
            await handler(event)
        except Exception as e:
            logger.error(
                "Event handler failed",
                event_type=type(event).__name__,
                event_id=event.event_id,
                error=str(e),
                exc_info=True,
            )
            # Re-raise to let gather capture it
            raise
