"""FastAPI dependency injection."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, AsyncGenerator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from subscriptionkore.core.models import ProviderType
from subscriptionkore.infrastructure.repositories.sqlalchemy import (
    SQLAlchemyCustomerRepository,
    SQLAlchemyEntitlementOverrideRepository,
    SQLAlchemyEntitlementRepository,
    SQLAlchemyInvoiceRepository,
    SQLAlchemyPaymentEventRepository,
    SQLAlchemyPlanRepository,
    SQLAlchemyProcessedEventRepository,
    SQLAlchemyProductRepository,
    SQLAlchemySubscriptionRepository,
)
from subscriptionkore.integrations.fastapi.setup import SubscriptioState, get_state
from subscriptionkore.ports.provider import PaymentProviderPort
from subscriptionkore.services import (
    CustomerManager,
    EntitlementService,
    SubscriptionManager,
    WebhookProcessor,
)

if TYPE_CHECKING:
    from subscriptionkore.ports.cache import CachePort
    from subscriptionkore.ports.event_bus import EventBusPort


async def get_db_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """Get database session from app state."""
    state: SubscriptioState = request.app.state.subscriptionkore
    async for session in state.get_session():
        yield session


async def get_event_bus(request: Request) -> "EventBusPort":
    """Get event bus from app state."""
    state: SubscriptioState = request.app.state.subscriptionkore
    if state.event_bus is None:
        raise RuntimeError("Event bus not initialized")
    return state.event_bus


async def get_cache(request: Request) -> "CachePort":
    """Get cache from app state."""
    state: SubscriptioState = request.app.state.subscriptionkore
    if state.cache is None:
        raise RuntimeError("Cache not initialized")
    return state.cache


async def get_provider(
    request: Request,
    provider_type: ProviderType | None = None,
) -> PaymentProviderPort:
    """Get payment provider adapter."""
    state: SubscriptioState = request.app.state.subscriptionkore

    if state.config is None:
        raise RuntimeError("Subscriptio not configured")

    target_type = provider_type or state.config.default_provider
    provider = state.providers.get(target_type)

    if provider is None:
        raise RuntimeError(f"Provider {target_type} not configured")

    return provider


async def get_subscriptionkore_manager(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    request: Request,
) -> SubscriptionManager:
    """Get subscriptionkore manager instance."""
    state: SubscriptioState = request.app.state.subscriptionkore

    if state.config is None or state.event_bus is None:
        raise RuntimeError("Subscriptio not initialized")

    provider = state.providers.get(state.config.default_provider)
    if provider is None:
        raise RuntimeError("Default provider not configured")

    return SubscriptionManager(
        subscriptionkore_repo=SQLAlchemySubscriptionRepository(session),
        customer_repo=SQLAlchemyCustomerRepository(session),
        plan_repo=SQLAlchemyPlanRepository(session),
        provider=provider,
        event_bus=state.event_bus,
    )


async def get_customer_manager(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    request: Request,
) -> CustomerManager:
    """Get customer manager instance."""
    state: SubscriptioState = request.app.state.subscriptionkore

    if state.config is None or state.event_bus is None:
        raise RuntimeError("Subscriptio not initialized")

    provider = state.providers.get(state.config.default_provider)
    if provider is None:
        raise RuntimeError("Default provider not configured")

    return CustomerManager(
        customer_repo=SQLAlchemyCustomerRepository(session),
        provider=provider,
        event_bus=state.event_bus,
    )


async def get_entitlement_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    request: Request,
) -> EntitlementService:
    """Get entitlement service instance."""
    state: SubscriptioState = request.app.state.subscriptionkore

    if state.config is None:
        raise RuntimeError("Subscriptio not initialized")

    return EntitlementService(
        entitlement_repo=SQLAlchemyEntitlementRepository(session),
        override_repo=SQLAlchemyEntitlementOverrideRepository(session),
        subscriptionkore_repo=SQLAlchemySubscriptionRepository(session),
        plan_repo=SQLAlchemyPlanRepository(session),
        cache=state.cache,
        cache_ttl=state.config.entitlement_cache_ttl,
    )


async def get_webhook_processor(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    request: Request,
) -> WebhookProcessor:
    """Get webhook processor instance."""
    state: SubscriptioState = request.app.state.subscriptionkore

    if state.config is None or state.event_bus is None:
        raise RuntimeError("Subscriptio not initialized")

    entitlement_service = EntitlementService(
        entitlement_repo=SQLAlchemyEntitlementRepository(session),
        override_repo=SQLAlchemyEntitlementOverrideRepository(session),
        subscriptionkore_repo=SQLAlchemySubscriptionRepository(session),
        plan_repo=SQLAlchemyPlanRepository(session),
        cache=state.cache,
        cache_ttl=state.config.entitlement_cache_ttl,
    )

    return WebhookProcessor(
        providers=state.providers,
        subscriptionkore_repo=SQLAlchemySubscriptionRepository(session),
        customer_repo=SQLAlchemyCustomerRepository(session),
        plan_repo=SQLAlchemyPlanRepository(session),
        invoice_repo=SQLAlchemyInvoiceRepository(session),
        payment_event_repo=SQLAlchemyPaymentEventRepository(session),
        processed_event_repo=SQLAlchemyProcessedEventRepository(session),
        event_bus=state.event_bus,
        entitlement_service=entitlement_service,
    )
