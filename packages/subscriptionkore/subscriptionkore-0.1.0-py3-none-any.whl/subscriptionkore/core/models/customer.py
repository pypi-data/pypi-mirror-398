"""Customer domain model."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field
from ulid import ULID

from subscriptionkore.core.models.value_objects import ProviderReference


class Address(BaseModel):
    """Billing address."""

    line1: str | None = None
    line2: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str | None = None  # ISO 3166-1 alpha-2


class TaxInfo(BaseModel):
    """Customer tax information."""

    tax_id: str | None = None
    tax_id_type: str | None = None  # e.g., "eu_vat", "us_ein"
    tax_exempt: bool = False


class Customer(BaseModel):
    """Customer domain entity."""

    id: str = Field(default_factory=lambda: str(ULID()))
    external_id: str  # Your application's user ID
    email: EmailStr
    name: str | None = None
    provider_refs: list[ProviderReference] = Field(default_factory=list)
    tax_info: TaxInfo | None = None
    billing_address: Address | None = None
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

    def update(
        self,
        email: str | None = None,
        name: str | None = None,
        tax_info: TaxInfo | None = None,
        billing_address: Address | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Update customer fields."""
        if email is not None:
            self.email = email  # type: ignore[assignment]
        if name is not None:
            self.name = name
        if tax_info is not None:
            self.tax_info = tax_info
        if billing_address is not None:
            self.billing_address = billing_address
        if metadata is not None:
            self.metadata.update(metadata)
        self.updated_at = datetime.utcnow()
