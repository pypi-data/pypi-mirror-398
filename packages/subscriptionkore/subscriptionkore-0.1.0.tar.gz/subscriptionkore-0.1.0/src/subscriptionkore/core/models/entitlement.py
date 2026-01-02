"""Entitlement domain models."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field
from ulid import ULID


class EntitlementValueType(StrEnum):
    """Types of entitlement values."""

    BOOLEAN = "boolean"
    NUMERIC = "numeric"
    STRING = "string"
    UNLIMITED = "unlimited"


class EntitlementSource(StrEnum):
    """Source of an entitlement."""

    PLAN = "plan"
    OVERRIDE = "override"
    TRIAL = "trial"
    DEFAULT = "default"


class Entitlement(BaseModel):
    """Entitlement definition entity."""

    id: str = Field(default_factory=lambda: str(ULID()))
    key: str  # Unique identifier, e.g., "api_calls", "seats"
    name: str
    description: str | None = None
    value_type: EntitlementValueType
    default_value: bool | int | str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CustomerEntitlement(BaseModel):
    """Resolved entitlement for a customer."""

    customer_id: str
    entitlement_key: str
    current_value: bool | int | str
    value_type: EntitlementValueType
    source: EntitlementSource
    expires_at: datetime | None = None
    subscription_id: str | None = None
    plan_id: str | None = None

    def is_expired(self) -> bool:
        """Check if entitlement has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def is_boolean(self) -> bool:
        return self.value_type == EntitlementValueType.BOOLEAN

    def is_numeric(self) -> bool:
        return self.value_type in {
            EntitlementValueType.NUMERIC,
            EntitlementValueType.UNLIMITED,
        }

    def as_bool(self) -> bool:
        """Get value as boolean."""
        if self.value_type == EntitlementValueType.BOOLEAN:
            return bool(self.current_value)
        if self.value_type == EntitlementValueType.UNLIMITED:
            return True
        if self.value_type == EntitlementValueType.NUMERIC:
            return int(self.current_value) > 0  # type: ignore[arg-type]
        return bool(self.current_value)

    def as_int(self) -> int | None:
        """Get value as integer (None for unlimited)."""
        if self.value_type == EntitlementValueType.UNLIMITED:
            return None
        if self.value_type == EntitlementValueType.NUMERIC:
            return int(self.current_value)  # type: ignore[arg-type]
        return None


class EntitlementOverride(BaseModel):
    """Manual entitlement override for a customer."""

    id: str = Field(default_factory=lambda: str(ULID()))
    customer_id: str
    entitlement_key: str
    value: bool | int | str
    value_type: EntitlementValueType
    reason: str | None = None
    expires_at: datetime | None = None
    created_by: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def is_expired(self) -> bool:
        """Check if override has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
