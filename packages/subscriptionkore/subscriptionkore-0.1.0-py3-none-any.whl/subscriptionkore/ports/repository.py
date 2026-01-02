"""Repository port interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Generic, TypeVar

from subscriptionkore.core.models import (
    Customer,
    CustomerEntitlement,
    Entitlement,
    EntitlementOverride,
    Invoice,
    PaymentEvent,
    Plan,
    Product,
    Subscription,
    SubscriptionStatus,
)

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """Base repository interface."""

    @abstractmethod
    async def get(self, id: str) -> T | None:
        """Get entity by ID."""
        ...

    @abstractmethod
    async def save(self, entity: T) -> T:
        """Save entity (create or update)."""
        ...

    @abstractmethod
    async def delete(self, id: str) -> bool:
        """Delete entity by ID.  Returns True if deleted."""
        ...


class CustomerRepository(BaseRepository[Customer]):
    """Repository for Customer entities."""

    @abstractmethod
    async def get_by_external_id(self, external_id: str) -> Customer | None:
        """Get customer by external (application) ID."""
        ...

    @abstractmethod
    async def get_by_email(self, email: str) -> Customer | None:
        """Get customer by email."""
        ...

    @abstractmethod
    async def get_by_provider_ref(
        self,
        provider: str,
        external_id: str,
    ) -> Customer | None:
        """Get customer by provider reference."""
        ...

    @abstractmethod
    async def list(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Customer]:
        """List customers with pagination."""
        ...


class ProductRepository(BaseRepository[Product]):
    """Repository for Product entities."""

    @abstractmethod
    async def get_by_provider_ref(
        self,
        provider: str,
        external_id: str,
    ) -> Product | None:
        """Get product by provider reference."""
        ...

    @abstractmethod
    async def list_active(self) -> list[Product]:
        """List all active products."""
        ...


class PlanRepository(BaseRepository[Plan]):
    """Repository for Plan entities."""

    @abstractmethod
    async def get_by_provider_ref(
        self,
        provider: str,
        external_id: str,
    ) -> Plan | None:
        """Get plan by provider reference."""
        ...

    @abstractmethod
    async def list_by_product(self, product_id: str) -> list[Plan]:
        """List all plans for a product."""
        ...

    @abstractmethod
    async def list_active(self) -> list[Plan]:
        """List all active plans."""
        ...


class SubscriptionRepository(BaseRepository[Subscription]):
    """Repository for Subscription entities."""

    @abstractmethod
    async def get_by_provider_ref(
        self,
        provider: str,
        external_id: str,
    ) -> Subscription | None:
        """Get subscriptionkore by provider reference."""
        ...

    @abstractmethod
    async def list_by_customer(
        self,
        customer_id: str,
        include_canceled: bool = False,
    ) -> list[Subscription]:
        """List subscriptionkores for a customer."""
        ...

    @abstractmethod
    async def list_active_by_customer(self, customer_id: str) -> list[Subscription]:
        """List active subscriptionkores for a customer."""
        ...

    @abstractmethod
    async def list_by_status(
        self,
        status: SubscriptionStatus,
        limit: int = 100,
    ) -> list[Subscription]:
        """List subscriptionkores by status."""
        ...

    @abstractmethod
    async def list_expiring_trials(
        self,
        before: datetime,
    ) -> list[Subscription]:
        """List subscriptionkores with trials expiring before date."""
        ...


class EntitlementRepository(BaseRepository[Entitlement]):
    """Repository for Entitlement definitions."""

    @abstractmethod
    async def get_by_key(self, key: str) -> Entitlement | None:
        """Get entitlement by key."""
        ...

    @abstractmethod
    async def list_all(self) -> list[Entitlement]:
        """List all entitlements."""
        ...


class EntitlementOverrideRepository(BaseRepository[EntitlementOverride]):
    """Repository for EntitlementOverride entities."""

    @abstractmethod
    async def get_by_customer_and_key(
        self,
        customer_id: str,
        entitlement_key: str,
    ) -> EntitlementOverride | None:
        """Get override by customer and entitlement key."""
        ...

    @abstractmethod
    async def list_by_customer(
        self,
        customer_id: str,
        include_expired: bool = False,
    ) -> list[EntitlementOverride]:
        """List all overrides for a customer."""
        ...

    @abstractmethod
    async def delete_by_customer_and_key(
        self,
        customer_id: str,
        entitlement_key: str,
    ) -> bool:
        """Delete override by customer and key."""
        ...


class InvoiceRepository(BaseRepository[Invoice]):
    """Repository for Invoice entities."""

    @abstractmethod
    async def get_by_provider_ref(
        self,
        provider: str,
        external_id: str,
    ) -> Invoice | None:
        """Get invoice by provider reference."""
        ...

    @abstractmethod
    async def list_by_customer(
        self,
        customer_id: str,
        limit: int = 100,
    ) -> list[Invoice]:
        """List invoices for a customer."""
        ...

    @abstractmethod
    async def list_by_subscriptionkore(
        self,
        subscriptionkore_id: str,
    ) -> list[Invoice]:
        """List invoices for a subscriptionkore."""
        ...


class PaymentEventRepository(BaseRepository[PaymentEvent]):
    """Repository for PaymentEvent entities."""

    @abstractmethod
    async def get_by_provider_ref(
        self,
        provider: str,
        external_id: str,
    ) -> PaymentEvent | None:
        """Get payment event by provider reference."""
        ...

    @abstractmethod
    async def list_by_customer(
        self,
        customer_id: str,
        limit: int = 100,
    ) -> list[PaymentEvent]:
        """List payment events for a customer."""
        ...

    @abstractmethod
    async def list_by_subscriptionkore(
        self,
        subscriptionkore_id: str,
    ) -> list[PaymentEvent]:
        """List payment events for a subscriptionkore."""
        ...


class ProcessedEventRepository(ABC):
    """Repository for tracking processed webhook events (idempotency)."""

    @abstractmethod
    async def exists(self, provider: str, event_id: str) -> bool:
        """Check if event has been processed."""
        ...

    @abstractmethod
    async def mark_processed(
        self,
        provider: str,
        event_id: str,
        processed_at: datetime | None = None,
    ) -> None:
        """Mark event as processed."""
        ...

    @abstractmethod
    async def cleanup_old_events(self, older_than_days: int = 7) -> int:
        """Remove old processed event records.  Returns count deleted."""
        ...
