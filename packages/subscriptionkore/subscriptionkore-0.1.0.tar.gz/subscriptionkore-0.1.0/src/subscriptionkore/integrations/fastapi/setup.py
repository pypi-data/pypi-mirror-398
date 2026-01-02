"""FastAPI setup and initialization."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from subscriptionkore.adapters.chargebee import ChargebeeAdapter
from subscriptionkore.adapters.lemonsqueezy import LemonSqueezyAdapter
from subscriptionkore.adapters.paddle import PaddleAdapter
from subscriptionkore.adapters.stripe import StripeAdapter
from subscriptionkore.config import SubscriptionKoreConfig
from subscriptionkore.core.models import ProviderType
from subscriptionkore.infrastructure.cache.memory import InMemoryCache
from subscriptionkore.infrastructure.cache.redis import RedisCache
from subscriptionkore.infrastructure.event_bus.memory import InMemoryEventBus
from subscriptionkore.infrastructure.repositories.sqlalchemy.models import Base
from subscriptionkore.ports.provider import PaymentProviderPort

if TYPE_CHECKING:
    from fastapi import FastAPI


class SubscriptionKoreState:
    """Holds SubscriptionKore runtime state."""

    def __init__(self) -> None:
        self.config: SubscriptionKoreConfig | None = None
        self.engine: any = None
        self.session_factory: async_sessionmaker[AsyncSession] | None = None
        self.providers: dict[ProviderType, PaymentProviderPort] = {}
        self.event_bus: InMemoryEventBus | None = None
        self.cache: InMemoryCache | RedisCache | None = None

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session."""
        if self.session_factory is None:
            raise RuntimeError("Subscriptio not initialized")
        async with self.session_factory() as session:
            yield session


# Global state - will be attached to FastAPI app
_state: SubscriptionKoreState | None = None


def get_state() -> SubscriptionKoreState:
    """Get global state."""
    if _state is None:
        raise RuntimeError("SubscriptionKore not initialized.  Call setup_subscriptionkore first.")
    return _state


async def _initialize(config: SubscriptionKoreConfig) -> SubscriptionKoreState:
    """Initialize SubscriptionKore components."""
    state = SubscriptionKoreState()
    state.config = config

    # Create database engine
    state.engine = create_async_engine(
        config.database_url,
        echo=False,
        pool_pre_ping=True,
    )

    # Create tables
    async with state.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    state.session_factory = async_sessionmaker(
        state.engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Initialize cache
    if config.redis_url:
        state.cache = RedisCache(config.redis_url)
    else:
        state.cache = InMemoryCache()

    # Initialize event bus
    state.event_bus = InMemoryEventBus()

    # Initialize all configured providers
    if config.stripe:
        state.providers[ProviderType.STRIPE] = StripeAdapter(config.stripe)

    if config.paddle:
        state.providers[ProviderType.PADDLE] = PaddleAdapter(config.paddle)

    if config.lemonsqueezy:
        state.providers[ProviderType.LEMONSQUEEZY] = LemonSqueezyAdapter(config.lemonsqueezy)

    if config.chargebee:
        state.providers[ProviderType.CHARGEBEE] = ChargebeeAdapter(config.chargebee)

    return state


async def _shutdown(state: SubscriptionKoreState) -> None:
    """Shutdown SubscriptionKore components."""
    # Close provider connections
    for provider in state.providers.values():
        if hasattr(provider, "close"):
            await provider.close()

    # Close cache
    if state.cache and hasattr(state.cache, "close"):
        await state.cache.close()

    # Close database engine
    if state.engine:
        await state.engine.dispose()


def setup_subscriptionkore(app: "FastAPI", config: SubscriptionKoreConfig) -> SubscriptionKoreState:
    """
    Setup SubscriptionKore with a FastAPI application.

    Args:
        app: FastAPI application instance
        config:  SubscriptionKore configuration

    Returns:
        SubscriptionKoreState instance

    Example:
        ```python
        from fastapi import FastAPI
        from subscriptionkore import SubscriptionKoreConfig
        from subscriptionkore.config import StripeConfig, PaddleConfig
        from subscriptionkore.integrations.fastapi import setup_subscriptionkore

        app = FastAPI()
        config = SubscriptionKoreConfig(
            database_url="postgresql+asyncpg://...",
            stripe=StripeConfig(api_key=".. .", webhook_secret="..."),
            paddle=PaddleConfig(api_key="...", webhook_secret="... "),
            default_provider="stripe",
        )
        subscriptionkore = setup_subscriptionkore(app, config)
        ```
    """
    global _state

    @asynccontextmanager
    async def lifespan(app: "FastAPI") -> AsyncGenerator[None, None]:
        global _state
        _state = await _initialize(config)
        app.state.subscriptionkore = _state
        yield
        await _shutdown(_state)
        _state = None

    # If app already has a lifespan, we need to compose them
    original_lifespan = getattr(app, "router", None) and getattr(
        app.router, "lifespan_context", None
    )

    if original_lifespan:
        # Compose lifespans
        @asynccontextmanager
        async def combined_lifespan(app: "FastAPI") -> AsyncGenerator[None, None]:
            async with lifespan(app):
                async with original_lifespan(app):
                    yield

        app.router.lifespan_context = combined_lifespan
    else:
        app.router.lifespan_context = lifespan

    # Return a placeholder state that will be populated on startup
    state = SubscriptionKoreState()
    state.config = config
    return state
