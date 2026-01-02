"""Payment provider port (interface)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

from subscriptionkore.core.models import (
    Customer,
    Invoice,
    Plan,
    Product,
    ProviderReference,
    ProviderType,
    Subscription,
)
from subscriptionkore.core.models.value_objects import Money


class ProrationBehavior(StrEnum):
    """How to handle proration during plan changes."""

    CREATE_PRORATIONS = "create_prorations"
    NONE = "none"
    ALWAYS_INVOICE = "always_invoice"


@dataclass
class ProviderCapabilities:
    """Capabilities supported by a provider."""

    supports_pausing: bool = True
    supports_trials: bool = True
    supports_quantity: bool = True
    supports_immediate_cancel: bool = True
    supports_proration: bool = True
    supports_coupons: bool = True
    supports_metered_billing: bool = False
    supports_customer_portal: bool = True
    supports_checkout_sessions: bool = True


@dataclass
class CreateSubscriptionRequest:
    """Request to create a subscriptionkore."""

    customer_id: str
    plan_id: str
    quantity: int = 1
    trial_period_days: int | None = None
    coupon_code: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    payment_method_id: str | None = None
    collection_method: str = "charge_automatically"


@dataclass
class UpdateSubscriptionRequest:
    """Request to update a subscriptionkore."""

    subscriptionkore_id: str
    quantity: int | None = None
    metadata: dict[str, Any] | None = None
    cancel_at_period_end: bool | None = None


@dataclass
class ChangePlanRequest:
    """Request to change subscriptionkore plan."""

    subscriptionkore_id: str
    new_plan_id: str
    proration_behavior: ProrationBehavior = ProrationBehavior.CREATE_PRORATIONS
    billing_cycle_anchor: str | None = None  # "unchanged" or "now"


@dataclass
class ChangePreview:
    """Preview of plan change costs."""

    immediate_charge: Money
    next_invoice_amount: Money
    proration_amount: Money
    credit_amount: Money
    next_billing_date: datetime


@dataclass
class DiscountRequest:
    """Request to apply a discount."""

    coupon_code: str | None = None
    promotion_code: str | None = None


@dataclass
class CheckoutRequest:
    """Request to create a checkout session."""

    plan_id: str
    success_url: str
    cancel_url: str
    customer_id: str | None = None
    customer_email: str | None = None
    quantity: int = 1
    trial_period_days: int | None = None
    allow_promotion_codes: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CheckoutSession:
    """Checkout session response."""

    id: str
    url: str
    expires_at: datetime


@dataclass
class PortalSession:
    """Customer portal session response."""

    id: str
    url: str
    expires_at: datetime | None = None


@dataclass
class ProviderWebhookEvent:
    """Raw webhook event from a provider."""

    provider: ProviderType
    event_id: str
    event_type: str
    occurred_at: datetime
    data: dict[str, Any]
    raw_payload: bytes


class PaymentProviderPort(ABC):
    """
    Abstract interface for payment providers.

    Each provider adapter must implement this interface to ensure
    consistent behavior across Stripe, Paddle, LemonSqueezy, and Chargebee.
    """

    @property
    @abstractmethod
    def provider_type(self) -> ProviderType:
        """Return the provider type."""
        ...

    @property
    @abstractmethod
    def capabilities(self) -> ProviderCapabilities:
        """Return provider capabilities."""
        ...

    # Customer Operations

    @abstractmethod
    async def create_customer(self, customer: Customer) -> ProviderReference:
        """Create a customer in the provider."""
        ...

    @abstractmethod
    async def update_customer(self, customer: Customer) -> None:
        """Update a customer in the provider."""
        ...

    @abstractmethod
    async def delete_customer(self, provider_ref: ProviderReference) -> None:
        """Delete a customer from the provider."""
        ...

    @abstractmethod
    async def get_customer(self, provider_ref: ProviderReference) -> Customer:
        """Get a customer from the provider."""
        ...

    # Subscription Operations

    @abstractmethod
    async def create_subscriptionkore(
        self,
        request: CreateSubscriptionRequest,
        customer_provider_ref: ProviderReference,
        plan_provider_ref: ProviderReference,
    ) -> Subscription:
        """Create a subscriptionkore."""
        ...

    @abstractmethod
    async def update_subscriptionkore(
        self,
        request: UpdateSubscriptionRequest,
        subscriptionkore_provider_ref: ProviderReference,
    ) -> Subscription:
        """Update a subscriptionkore."""
        ...

    @abstractmethod
    async def cancel_subscriptionkore(
        self,
        subscriptionkore_provider_ref: ProviderReference,
        immediate: bool = False,
    ) -> Subscription:
        """Cancel a subscriptionkore."""
        ...

    @abstractmethod
    async def pause_subscriptionkore(
        self,
        subscriptionkore_provider_ref: ProviderReference,
        resumes_at: datetime | None = None,
    ) -> Subscription:
        """Pause a subscriptionkore."""
        ...

    @abstractmethod
    async def resume_subscriptionkore(
        self,
        subscriptionkore_provider_ref: ProviderReference,
    ) -> Subscription:
        """Resume a paused subscriptionkore."""
        ...

    @abstractmethod
    async def get_subscriptionkore(
        self,
        provider_ref: ProviderReference,
    ) -> Subscription:
        """Get a subscriptionkore from the provider."""
        ...

    # Plan Change Operations

    @abstractmethod
    async def change_plan(
        self,
        request: ChangePlanRequest,
        subscriptionkore_provider_ref: ProviderReference,
        new_plan_provider_ref: ProviderReference,
    ) -> Subscription:
        """Change subscriptionkore plan (upgrade/downgrade)."""
        ...

    @abstractmethod
    async def preview_plan_change(
        self,
        request: ChangePlanRequest,
        subscriptionkore_provider_ref: ProviderReference,
        new_plan_provider_ref: ProviderReference,
    ) -> ChangePreview:
        """Preview plan change costs."""
        ...

    # Discount Operations

    @abstractmethod
    async def apply_discount(
        self,
        subscriptionkore_provider_ref: ProviderReference,
        discount: DiscountRequest,
    ) -> Subscription:
        """Apply a discount to a subscriptionkore."""
        ...

    @abstractmethod
    async def remove_discount(
        self,
        subscriptionkore_provider_ref: ProviderReference,
    ) -> Subscription:
        """Remove discount from a subscriptionkore."""
        ...

    # Billing Operations

    @abstractmethod
    async def get_invoice(self, provider_ref: ProviderReference) -> Invoice:
        """Get an invoice from the provider."""
        ...

    @abstractmethod
    async def list_invoices(
        self,
        customer_provider_ref: ProviderReference,
        limit: int = 10,
        starting_after: str | None = None,
    ) -> list[Invoice]:
        """List invoices for a customer."""
        ...

    @abstractmethod
    async def get_upcoming_invoice(
        self,
        subscriptionkore_provider_ref: ProviderReference,
    ) -> Invoice | None:
        """Get upcoming invoice for a subscriptionkore."""
        ...

    # Checkout / Portal

    @abstractmethod
    async def create_checkout_session(
        self,
        request: CheckoutRequest,
        plan_provider_ref: ProviderReference,
        customer_provider_ref: ProviderReference | None = None,
    ) -> CheckoutSession:
        """Create a checkout session."""
        ...

    @abstractmethod
    async def create_portal_session(
        self,
        customer_provider_ref: ProviderReference,
        return_url: str,
    ) -> PortalSession:
        """Create a customer portal session."""
        ...

    # Webhook Handling

    @abstractmethod
    async def verify_webhook(
        self,
        payload: bytes,
        headers: dict[str, str],
    ) -> bool:
        """Verify webhook signature."""
        ...

    @abstractmethod
    async def parse_webhook(
        self,
        payload: bytes,
        headers: dict[str, str],
    ) -> ProviderWebhookEvent:
        """Parse webhook payload into provider event."""
        ...

    # Sync Operations

    @abstractmethod
    async def sync_products(self) -> list[Product]:
        """Sync all products from provider."""
        ...

    @abstractmethod
    async def sync_plans(self, product_provider_ref: ProviderReference) -> list[Plan]:
        """Sync all plans for a product from provider."""
        ...
