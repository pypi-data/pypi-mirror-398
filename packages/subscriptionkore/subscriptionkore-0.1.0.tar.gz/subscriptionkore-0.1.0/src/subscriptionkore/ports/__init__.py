"""Port interfaces (abstractions)."""

from subscriptionkore.ports.cache import CachePort
from subscriptionkore.ports.event_bus import EventBusPort, EventHandler
from subscriptionkore.ports.provider import (
    ChangePlanRequest,
    ChangePreview,
    CheckoutRequest,
    CheckoutSession,
    CreateSubscriptionRequest,
    DiscountRequest,
    PaymentProviderPort,
    PortalSession,
    ProviderCapabilities,
    ProviderWebhookEvent,
    UpdateSubscriptionRequest,
)
from subscriptionkore.ports.repository import (
    CustomerRepository,
    EntitlementOverrideRepository,
    EntitlementRepository,
    InvoiceRepository,
    PaymentEventRepository,
    PlanRepository,
    ProcessedEventRepository,
    ProductRepository,
    SubscriptionRepository,
)

__all__ = [
    # Provider port
    "PaymentProviderPort",
    "ProviderCapabilities",
    "ProviderWebhookEvent",
    "CreateSubscriptionRequest",
    "UpdateSubscriptionRequest",
    "ChangePlanRequest",
    "ChangePreview",
    "DiscountRequest",
    "CheckoutRequest",
    "CheckoutSession",
    "PortalSession",
    # Repository ports
    "CustomerRepository",
    "ProductRepository",
    "PlanRepository",
    "SubscriptionRepository",
    "EntitlementRepository",
    "EntitlementOverrideRepository",
    "InvoiceRepository",
    "PaymentEventRepository",
    "ProcessedEventRepository",
    # Event bus
    "EventBusPort",
    "EventHandler",
    # Cache
    "CachePort",
]
