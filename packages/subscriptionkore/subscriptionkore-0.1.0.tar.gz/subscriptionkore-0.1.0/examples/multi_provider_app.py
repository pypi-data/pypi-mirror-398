"""Example showing multi-provider usage."""

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

from subscriptionkore import SubscriptionKoreConfig, ProviderType
from subscriptionkore. config import (
    StripeConfig,
    PaddleConfig,
    LemonSqueezyConfig,
    ChargebeeConfig,
)
from subscriptionkore.integrations.fastapi import (
    create_webhook_router,
    get_customer_manager,
    get_subscription_manager,
    setup_subscriptionkore,
)
from subscriptionkore. services import CustomerManager, SubscriptionManager


# Multi-provider configuration
config = SubscriptionKoreConfig(
    database_url="postgresql+asyncpg://user:password@localhost: 5432/subscriptionkore",
    redis_url="redis://localhost:6379/0",
    
    # Configure multiple providers
    stripe=StripeConfig(
        api_key="sk_test_stripe_key",
        webhook_secret="whsec_stripe_secret",
    ),
    paddle=PaddleConfig(
        api_key="paddle_api_key",
        webhook_secret="paddle_webhook_secret",
        environment="sandbox",
    ),
    lemonsqueezy=LemonSqueezyConfig(
        api_key="lemonsqueezy_api_key",
        webhook_secret="lemonsqueezy_webhook_secret",
        store_id="12345",
    ),
    chargebee=ChargebeeConfig(
        site="your-site",
        api_key="chargebee_api_key",
        webhook_username="webhook_user",
        webhook_password="webhook_pass",
    ),
    
    # Set default provider
    default_provider=ProviderType. STRIPE,
)

app = FastAPI(title="Multi-Provider SaaS App")

# Setup SubscriptionKore with all providers
subscriptionkore = setup_subscriptionkore(app, config)

# Include webhook router (handles all providers)
webhook_router = create_webhook_router(prefix="/webhooks")
app.include_router(webhook_router)


class CreateCustomerRequest(BaseModel):
    user_id: str
    email: str
    name: str | None = None
    provider:  str = "stripe"  # Allow specifying provider


class CreateSubscriptionRequest(BaseModel):
    customer_id:  str
    plan_id: str
    provider: str = "stripe"


@app.post("/customers")
async def create_customer(
    request: CreateCustomerRequest,
    customers: CustomerManager = Depends(get_customer_manager),
):
    """Create customer in specified provider."""
    # Get provider-specific manager
    from subscriptionkore.integrations.fastapi. setup import get_state
    
    state = get_state()
    provider_type = ProviderType(request.provider)
    provider = state.providers.get(provider_type)
    
    if provider is None:
        raise HTTPException(
            status_code=400,
            detail=f"Provider '{request.provider}' not configured"
        )
    
    # Create customer manager for specific provider
    from subscriptionkore.infrastructure.repositories.sqlalchemy import SQLAlchemyCustomerRepository
    from subscriptionkore.services import CustomerManager
    from sqlalchemy.ext.asyncio import AsyncSession
    
    async for session in state.get_session():
        manager = CustomerManager(
            customer_repo=SQLAlchemyCustomerRepository(session),
            provider=provider,
            event_bus=state.event_bus,
        )
        
        customer = await manager.create(
            external_id=request.user_id,
            email=request.email,
            name=request.name,
        )
        
        return {
            "id": customer.id,
            "email":  customer.email,
            "provider": request.provider,
            "provider_id": customer.provider_refs[0].external_id if customer. provider_refs else None,
        }


@app.get("/providers")
async def list_configured_providers():
    """List all configured providers."""
    from subscriptionkore.integrations.fastapi. setup import get_state
    
    state = get_state()
    return {
        "providers":  [p.value for p in state.providers.keys()],
        "default":  state.config.default_provider. value if state.config else None,
    }


@app.get("/providers/{provider}/capabilities")
async def get_provider_capabilities(provider: str):
    """Get capabilities for a specific provider."""
    from subscriptionkore.integrations.fastapi.setup import get_state
    
    state = get_state()
    
    try:
        provider_type = ProviderType(provider)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Unknown provider: {provider}")
    
    adapter = state.providers. get(provider_type)
    if adapter is None:
        raise HTTPException(status_code=404, detail=f"Provider '{provider}' not configured")
    
    caps = adapter.capabilities
    return {
        "provider": provider,
        "capabilities": {
            "pausing": caps.supports_pausing,
            "trials": caps.supports_trials,
            "quantity": caps.supports_quantity,
            "immediate_cancel": caps.supports_immediate_cancel,
            "proration": caps.supports_proration,
            "coupons": caps. supports_coupons,
            "metered_billing": caps.supports_metered_billing,
            "customer_portal": caps. supports_customer_portal,
            "checkout_sessions": caps.supports_checkout_sessions,
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn. run(app, host="0.0.0.0", port=8000)