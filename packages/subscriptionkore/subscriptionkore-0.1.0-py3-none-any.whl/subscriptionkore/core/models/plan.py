"""Plan domain model."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field
from ulid import ULID

from subscriptionkore.core.models.entitlement import EntitlementValueType
from subscriptionkore.core.models.value_objects import BillingPeriod, Money, ProviderReference


class PlanEntitlement(BaseModel):
    """Entitlement configuration for a plan."""

    entitlement_id: str
    entitlement_key: str
    value: bool | int | str | None
    value_type: EntitlementValueType


class Plan(BaseModel):
    """Plan domain entity (a pricing tier for a product)."""

    id: str = Field(default_factory=lambda: str(ULID()))
    product_id: str
    name: str
    description: str | None = None
    provider_refs: list[ProviderReference] = Field(default_factory=list)
    price: Money
    billing_period: BillingPeriod
    trial_period_days: int | None = None
    entitlements: list[PlanEntitlement] = Field(default_factory=list)
    active: bool = True
    tier: int = Field(default=0, description="For upgrade/downgrade ordering")
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def get_provider_ref(self, provider_type: str) -> ProviderReference | None:
        """Get provider reference for a specific provider."""
        for ref in self.provider_refs:
            if ref.provider.value == provider_type:
                return ref
        return None

    def add_provider_ref(self, ref: ProviderReference) -> None:
        """Add or update a provider reference."""
        self.provider_refs = [r for r in self.provider_refs if r.provider != ref.provider]
        self.provider_refs.append(ref)
        self.updated_at = datetime.utcnow()

    def is_upgrade_from(self, other: Plan) -> bool:
        """Check if this plan is an upgrade from another."""
        return self.tier > other.tier

    def is_downgrade_from(self, other: Plan) -> bool:
        """Check if this plan is a downgrade from another."""
        return self.tier < other.tier

    def get_entitlement_value(self, key: str) -> bool | int | str | None:
        """Get entitlement value by key."""
        for ent in self.entitlements:
            if ent.entitlement_key == key:
                return ent.value
        return None

    def deactivate(self) -> None:
        """Deactivate the plan."""
        self.active = False
        self.updated_at = datetime.utcnow()
