"""Main factory for creating SubscriptionKore instances."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from subscriptionkore.adapters.stripe import StripeAdapter
from subscriptionkore.config import SubscriptionKoreConfig
from subscriptionkore.core.models import ProviderType
from subscriptionkore.infrastructure.cache.memory import InMemoryCache
from subscriptionkore.infrastructure.cache.redis import RedisCache
from subscriptionkore.infrastructure.event_bus.memory import InMemoryEventBus
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
from subscriptionkore.infrastructure.repositories.sqlalchemy.models import Base
from subscriptionkore.ports.cache import CachePort
from subscriptionkore.ports.event_bus import EventBusPort
from subscriptionkore.ports.provider import PaymentProviderPort
from subscriptionkore.services import (
    CustomerManager,
    EntitlementService,
    SubscriptionManager,
    WebhookProcessor,
)

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from subscriptionkore.core.events import DomainEvent


class SubscriptionKore:
    """
    Main entry point for the SubscriptionKore library.

    Provides access to all subscriptionkore management functionality.

    Example:
        ```python
        from subscriptionkore import SubscriptionKore, SubscriptionKoreConfig
        from subscriptionkore.config import StripeConfig

        config = SubscriptionKoreConfig(
            database_url="postgresql+asyncpg://user:pass@localhost/db",
            stripe=StripeConfig(
                api_key="sk_test_.. .",
                webhook_secret="whsec_...",
            ),
        )

        async with SubscriptionKore(config) as subscriptionkore:
            # Create a customer
            customer = await subscriptionkore. customers.create(
                external_id="user_123",
                email="user@example. com",
            )

            # Create a subscriptionkore
            subscriptionkore = await subscriptionkore. subscriptionkores.create(
                customer_id=customer.id,
                plan_id="plan_abc",
            )

            # Check entitlements
            has_access = await subscriptionkore.entitlements. has_access(
                customer_id=customer.id,
                entitlement_key="premium_features",
            )
        ```
    """

    def __init__(self, config: SubscriptionKoreConfig) -> None:
        self._config = config
        self._engine: any = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None
        self._providers: dict[ProviderType, PaymentProviderPort] = {}
        self._event_bus: InMemoryEventBus = InMemoryEventBus()
        self._cache: CachePort | None = None
        self._initialized = False

    async def __aenter__(self) -> "SubscriptionKore":
        await self.initialize()
        return self

    async def __aexit__(self, exc_type: any, exc_val: any, exc_tb: any) -> None:
        await self.close()

    async def initialize(self) -> None:
        """Initialize all components."""
        if self._initialized:
            return

        # Create database engine
        self._engine = create_async_engine(
            self._config.database_url,
            echo=False,
            pool_pre_ping=True,
        )

        # Create tables
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Create session factory
        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Initialize cache
        if self._config.redis_url:
            self._cache = RedisCache(self._config.redis_url)
        else:
            self._cache = InMemoryCache()

        # Initialize providers
        if self._config.stripe:
            self._providers[ProviderType.STRIPE] = StripeAdapter(self._config.stripe)

        self._initialized = True

    async def close(self) -> None:
        """Close all connections and clean up resources."""
        # Close provider connections
        for provider in self._providers.values():
            if hasattr(provider, "close"):
                await provider.close()

        # Close cache
        if self._cache and hasattr(self._cache, "close"):
            await self._cache.close()

        # Close database engine
        if self._engine:
            await self._engine.dispose()

        self._initialized = False

    def _ensure_initialized(self) -> None:
        if not self._initialized:
            raise RuntimeError(
                "SubscriptionKore not initialized. Call initialize() first or use async context manager."
            )

    def _get_session(self) -> AsyncSession:
        self._ensure_initialized()
        if self._session_factory is None:
            raise RuntimeError("Session factory not initialized")
        return self._session_factory()

    def _get_provider(self, provider_type: ProviderType | None = None) -> PaymentProviderPort:
        self._ensure_initialized()
        target = provider_type or self._config.default_provider
        provider = self._providers.get(target)
        if provider is None:
            raise RuntimeError(f"Provider {target} not configured")
        return provider

    @property
    def event_bus(self) -> EventBusPort:
        """Access the event bus for subscribing to domain events."""
        return self._event_bus

    def on_event(
        self,
        event_type: type["DomainEvent"],
    ) -> Callable[
        [Callable[["DomainEvent"], Awaitable[None]]], Callable[["DomainEvent"], Awaitable[None]]
    ]:
        """
        Decorator to subscribe to domain events.

        Example:
            ```python
            @subscriptionkore.on_event(SubscriptionActivated)
            async def handle_activation(event: SubscriptionActivated):
                await send_welcome_email(event. customer_id)
            ```
        """

        def decorator(
            handler: Callable[["DomainEvent"], Awaitable[None]],
        ) -> Callable[["DomainEvent"], Awaitable[None]]:
            self._event_bus.subscribe(event_type, handler)
            return handler

        return decorator

    async def get_subscriptionkore_manager(self) -> SubscriptionManager:
        """Get a subscriptionkore manager instance."""
        session = self._get_session()
        return SubscriptionManager(
            subscriptionkore_repo=SQLAlchemySubscriptionRepository(session),
            customer_repo=SQLAlchemyCustomerRepository(session),
            plan_repo=SQLAlchemyPlanRepository(session),
            provider=self._get_provider(),
            event_bus=self._event_bus,
        )

    async def get_customer_manager(self) -> CustomerManager:
        """Get a customer manager instance."""
        session = self._get_session()
        return CustomerManager(
            customer_repo=SQLAlchemyCustomerRepository(session),
            provider=self._get_provider(),
            event_bus=self._event_bus,
        )

    async def get_entitlement_service(self) -> EntitlementService:
        """Get an entitlement service instance."""
        session = self._get_session()
        return EntitlementService(
            entitlement_repo=SQLAlchemyEntitlementRepository(session),
            override_repo=SQLAlchemyEntitlementOverrideRepository(session),
            subscriptionkore_repo=SQLAlchemySubscriptionRepository(session),
            plan_repo=SQLAlchemyPlanRepository(session),
            cache=self._cache,
            cache_ttl=self._config.entitlement_cache_ttl,
        )

    async def get_webhook_processor(self) -> WebhookProcessor:
        """Get a webhook processor instance."""
        session = self._get_session()
        entitlement_service = await self.get_entitlement_service()

        return WebhookProcessor(
            providers=self._providers,
            subscriptionkore_repo=SQLAlchemySubscriptionRepository(session),
            customer_repo=SQLAlchemyCustomerRepository(session),
            plan_repo=SQLAlchemyPlanRepository(session),
            invoice_repo=SQLAlchemyInvoiceRepository(session),
            payment_event_repo=SQLAlchemyPaymentEventRepository(session),
            processed_event_repo=SQLAlchemyProcessedEventRepository(session),
            event_bus=self._event_bus,
            entitlement_service=entitlement_service,
        )

    # Convenience properties for common operations

    @property
    async def subscriptionkores(self) -> SubscriptionManager:
        """Shortcut to get subscriptionkore manager."""
        return await self.get_subscriptionkore_manager()

    @property
    async def customers(self) -> CustomerManager:
        """Shortcut to get customer manager."""
        return await self.get_customer_manager()

    @property
    async def entitlements(self) -> EntitlementService:
        """Shortcut to get entitlement service."""
        return await self.get_entitlement_service()
