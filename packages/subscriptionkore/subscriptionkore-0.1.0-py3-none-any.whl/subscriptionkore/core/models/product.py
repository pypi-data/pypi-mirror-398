"""Product domain model."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field
from ulid import ULID

from subscriptionkore.core.models.value_objects import ProviderReference


class Product(BaseModel):
    """Product domain entity."""

    id: str = Field(default_factory=lambda: str(ULID()))
    name: str
    description: str | None = None
    provider_refs: list[ProviderReference] = Field(default_factory=list)
    active: bool = True
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

    def deactivate(self) -> None:
        """Deactivate the product."""
        self.active = False
        self.updated_at = datetime.utcnow()

    def activate(self) -> None:
        """Activate the product."""
        self.active = True
        self.updated_at = datetime.utcnow()
