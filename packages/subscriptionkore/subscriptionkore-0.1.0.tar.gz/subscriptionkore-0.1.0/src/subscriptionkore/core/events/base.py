"""Base domain event."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field
from ulid import ULID


class DomainEvent(BaseModel):
    """Base class for all domain events."""

    event_id: str = Field(default_factory=lambda: str(ULID()))
    event_type: str = ""
    occurred_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        # Auto-set event_type from class name
        if not cls.__dict__.get("event_type"):
            cls.model_fields["event_type"].default = cls.__name__

    model_config = {"frozen": True}
