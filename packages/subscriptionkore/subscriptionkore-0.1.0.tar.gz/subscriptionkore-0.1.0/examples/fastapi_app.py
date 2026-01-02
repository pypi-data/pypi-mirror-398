"""Example FastAPI application using SubscriptionKore."""

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

from subscriptionkore import (
    SubscriptionKoreConfig,
    SubscriptionActivated,
    SubscriptionCanceled,
    PaymentFailed,
)
from subscriptionkore.config import StripeConfig
from subscriptionkore.core.exceptions import EntityNotFoundError
from subscriptionkore.integrations. fastapi import (
    create_webhook_router,
    get_customer_manager,
    get_entitlement_service,
    get_subscription_manager,
    setup_subscriptionkore,
)
from subscriptionkore.services import CustomerManager, EntitlementService, SubscriptionManager
from subscriptionkore. services.webhook_processor import WebhookResult


# Configuration - load from environment in production
config = SubscriptionKoreConfig(
    database_url="postgresql+asyncpg://user:password@localhost: 5432/subscriptionkore",
    redis_url="redis://localhost:6379/0",
    stripe=StripeConfig(
        api_key="sk_test_your_stripe_key",
        webhook_secret="whsec_your_webhook_secret",
    ),
)

# Create FastAPI app
app = FastAPI(title="My SaaS App")

# Setup SubscriptionKore
subscriptionkore = setup_subscriptionkore(app, config)


# Event handlers - register before app starts
async def on_subscription_activated(event: SubscriptionActivated) -> None:
    """Handle subscription activation."""
    print(f"Subscription activated: {event.subscription.id}")
    # Send welcome email, provision resources, etc.


async def on_subscription_canceled(event: SubscriptionCanceled) -> None:
    """Handle subscription cancellation."""
    print(f"Subscription canceled: {event. subscription.id}")
    # Send cancellation email, cleanup resources, etc.


async def on_payment_failed(event: PaymentFailed) -> None:
    """Handle payment failure."""
    print(f"Payment failed for customer: {event.customer_id}")
    # Send payment failure notification


async def on_webhook_processed(result: WebhookResult) -> None:
    """Called after each webhook is processed."""
    print(f"Webhook processed: {result.event_id} - {result.status}")


# Include webhook router with event callback
webhook_router = create_webhook_router(
    prefix="/webhooks",
    on_event=on_webhook_processed,
)
app.include_router(webhook_router)


# Request/Response models
class CreateCustomerRequest(BaseModel):
    user_id: str
    email: str
    name: str | None = None


class CreateSubscriptionRequest(BaseModel):
    customer_id: str
    plan_id:  str
    trial_days: int | None = None
    coupon_code: str | None = None


class CancelSubscriptionRequest(BaseModel):
    immediate: bool = False
    reason: str | None = None


class ChangePlanRequest(BaseModel):
    new_plan_id:  str


class GrantEntitlementRequest(BaseModel):
    entitlement_key: str
    value: bool | int | str
    expires_in_days: int | None = None
    reason: str | None = None


class CustomerResponse(BaseModel):
    id: str
    external_id: str
    email: str
    name: str | None


class SubscriptionResponse(BaseModel):
    id: str
    customer_id:  str
    plan_id: str
    status: str
    cancel_at_period_end:  bool
    trial_end: str | None
    current_period_end: str | None


class EntitlementCheckResponse(BaseModel):
    entitlement_key:  str
    has_access: bool
    value: bool | int | str | None
    source: str
    expires_at: str | None


class EntitlementListResponse(BaseModel):
    entitlements: list[EntitlementCheckResponse]


# Startup event to register domain event handlers
@app. on_event("startup")
async def register_event_handlers() -> None:
    """Register domain event handlers on startup."""
    from subscriptio.integrations.fastapi. setup import get_state
    
    # Wait a moment for subscriptio to initialize
    import asyncio
    await asyncio.sleep(0.1)
    
    try:
        state = get_state()
        if state. event_bus:
            state.event_bus. subscribe(SubscriptionActivated, on_subscription_activated)
            state.event_bus.subscribe(SubscriptionCanceled, on_subscription_canceled)
            state.event_bus.subscribe(PaymentFailed, on_payment_failed)
    except RuntimeError: 
        # State not yet initialized, handlers will be registered later
        pass


# Customer Routes
@app.post("/customers", response_model=CustomerResponse, tags=["customers"])
async def create_customer(
    request:  CreateCustomerRequest,
    customers: CustomerManager = Depends(get_customer_manager),
) -> CustomerResponse:
    """Create a new customer and sync to payment provider."""
    customer = await customers.create(
        external_id=request.user_id,
        email=request.email,
        name=request.name,
    )
    return CustomerResponse(
        id=customer.id,
        external_id=customer.external_id,
        email=customer.email,
        name=customer.name,
    )


@app.get("/customers/{customer_id}", response_model=CustomerResponse, tags=["customers"])
async def get_customer(
    customer_id: str,
    customers: CustomerManager = Depends(get_customer_manager),
) -> CustomerResponse:
    """Get customer by ID."""
    try:
        customer = await customers.get(customer_id)
    except EntityNotFoundError:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return CustomerResponse(
        id=customer.id,
        external_id=customer.external_id,
        email=customer.email,
        name=customer.name,
    )


@app.get("/customers/by-external-id/{external_id}", response_model=CustomerResponse, tags=["customers"])
async def get_customer_by_external_id(
    external_id:  str,
    customers: CustomerManager = Depends(get_customer_manager),
) -> CustomerResponse: 
    """Get customer by external (application) ID."""
    try:
        customer = await customers.get_by_external_id(external_id)
    except EntityNotFoundError: 
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return CustomerResponse(
        id=customer.id,
        external_id=customer.external_id,
        email=customer.email,
        name=customer.name,
    )


# Subscription Routes
@app.post("/subscriptions", response_model=SubscriptionResponse, tags=["subscriptions"])
async def create_subscription(
    request: CreateSubscriptionRequest,
    subscriptions: SubscriptionManager = Depends(get_subscription_manager),
) -> SubscriptionResponse: 
    """Create a new subscription."""
    try:
        subscription = await subscriptions.create(
            customer_id=request.customer_id,
            plan_id=request.plan_id,
            trial_period_days=request. trial_days,
            coupon_code=request.coupon_code,
        )
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    return SubscriptionResponse(
        id=subscription.id,
        customer_id=subscription.customer_id,
        plan_id=subscription.plan_id,
        status=subscription.status. value,
        cancel_at_period_end=subscription.cancel_at_period_end,
        trial_end=subscription. trial_end. isoformat() if subscription.trial_end else None,
        current_period_end=subscription.current_period. end.isoformat() 
            if subscription.current_period. end else None,
    )


@app.get("/subscriptions/{subscription_id}", response_model=SubscriptionResponse, tags=["subscriptions"])
async def get_subscription(
    subscription_id: str,
    subscriptions:  SubscriptionManager = Depends(get_subscription_manager),
) -> SubscriptionResponse:
    """Get subscription by ID."""
    try: 
        subscription = await subscriptions.get(subscription_id)
    except EntityNotFoundError:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    return SubscriptionResponse(
        id=subscription.id,
        customer_id=subscription.customer_id,
        plan_id=subscription.plan_id,
        status=subscription.status. value,
        cancel_at_period_end=subscription.cancel_at_period_end,
        trial_end=subscription. trial_end.isoformat() if subscription.trial_end else None,
        current_period_end=subscription.current_period.end.isoformat() 
            if subscription.current_period.end else None,
    )


@app.get("/customers/{customer_id}/subscriptions", response_model=list[SubscriptionResponse], tags=["subscriptions"])
async def get_customer_subscriptions(
    customer_id: str,
    include_canceled: bool = False,
    subscriptions: SubscriptionManager = Depends(get_subscription_manager),
) -> list[SubscriptionResponse]:
    """Get all subscriptions for a customer."""
    subs = await subscriptions.get_by_customer(
        customer_id=customer_id,
        include_canceled=include_canceled,
    )
    
    return [
        SubscriptionResponse(
            id=sub.id,
            customer_id=sub.customer_id,
            plan_id=sub.plan_id,
            status=sub.status. value,
            cancel_at_period_end=sub.cancel_at_period_end,
            trial_end=sub. trial_end.isoformat() if sub.trial_end else None,
            current_period_end=sub.current_period.end.isoformat() 
                if sub.current_period.end else None,
        )
        for sub in subs
    ]


@app.post("/subscriptions/{subscription_id}/cancel", response_model=SubscriptionResponse, tags=["subscriptions"])
async def cancel_subscription(
    subscription_id: str,
    request: CancelSubscriptionRequest,
    subscriptions: SubscriptionManager = Depends(get_subscription_manager),
) -> SubscriptionResponse: 
    """Cancel a subscription."""
    try:
        subscription = await subscriptions.cancel(
            subscription_id=subscription_id,
            immediate=request. immediate,
            reason=request.reason,
        )
    except EntityNotFoundError:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    return SubscriptionResponse(
        id=subscription.id,
        customer_id=subscription.customer_id,
        plan_id=subscription.plan_id,
        status=subscription.status. value,
        cancel_at_period_end=subscription.cancel_at_period_end,
        trial_end=subscription. trial_end.isoformat() if subscription.trial_end else None,
        current_period_end=subscription.current_period.end.isoformat() 
            if subscription.current_period.end else None,
    )


@app.post("/subscriptions/{subscription_id}/reactivate", response_model=SubscriptionResponse, tags=["subscriptions"])
async def reactivate_subscription(
    subscription_id: str,
    subscriptions: SubscriptionManager = Depends(get_subscription_manager),
) -> SubscriptionResponse: 
    """Reactivate a subscription that was scheduled to cancel."""
    try:
        subscription = await subscriptions.reactivate(subscription_id)
    except EntityNotFoundError:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    return SubscriptionResponse(
        id=subscription.id,
        customer_id=subscription.customer_id,
        plan_id=subscription.plan_id,
        status=subscription.status. value,
        cancel_at_period_end=subscription.cancel_at_period_end,
        trial_end=subscription. trial_end.isoformat() if subscription.trial_end else None,
        current_period_end=subscription.current_period.end.isoformat() 
            if subscription.current_period.end else None,
    )


@app.post("/subscriptions/{subscription_id}/pause", response_model=SubscriptionResponse, tags=["subscriptions"])
async def pause_subscription(
    subscription_id: str,
    subscriptions: SubscriptionManager = Depends(get_subscription_manager),
) -> SubscriptionResponse:
    """Pause a subscription."""
    try:
        subscription = await subscriptions.pause(subscription_id)
    except EntityNotFoundError:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    return SubscriptionResponse(
        id=subscription.id,
        customer_id=subscription.customer_id,
        plan_id=subscription.plan_id,
        status=subscription.status.value,
        cancel_at_period_end=subscription. cancel_at_period_end,
        trial_end=subscription.trial_end. isoformat() if subscription.trial_end else None,
        current_period_end=subscription.current_period.end.isoformat() 
            if subscription.current_period.end else None,
    )


@app.post("/subscriptions/{subscription_id}/resume", response_model=SubscriptionResponse, tags=["subscriptions"])
async def resume_subscription(
    subscription_id: str,
    subscriptions:  SubscriptionManager = Depends(get_subscription_manager),
) -> SubscriptionResponse:
    """Resume a paused subscription."""
    try:
        subscription = await subscriptions. resume(subscription_id)
    except EntityNotFoundError: 
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    return SubscriptionResponse(
        id=subscription.id,
        customer_id=subscription.customer_id,
        plan_id=subscription.plan_id,
        status=subscription.status.value,
        cancel_at_period_end=subscription.cancel_at_period_end,
        trial_end=subscription.trial_end.isoformat() if subscription.trial_end else None,
        current_period_end=subscription. current_period.end.isoformat() 
            if subscription.current_period. end else None,
    )


@app.post("/subscriptions/{subscription_id}/change-plan", response_model=SubscriptionResponse, tags=["subscriptions"])
async def change_subscription_plan(
    subscription_id: str,
    request: ChangePlanRequest,
    subscriptions: SubscriptionManager = Depends(get_subscription_manager),
) -> SubscriptionResponse: 
    """Change subscription plan (upgrade/downgrade)."""
    try: 
        subscription = await subscriptions.change_plan(
            subscription_id=subscription_id,
            new_plan_id=request.new_plan_id,
        )
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    return SubscriptionResponse(
        id=subscription.id,
        customer_id=subscription.customer_id,
        plan_id=subscription.plan_id,
        status=subscription.status. value,
        cancel_at_period_end=subscription.cancel_at_period_end,
        trial_end=subscription. trial_end.isoformat() if subscription.trial_end else None,
        current_period_end=subscription.current_period.end.isoformat() 
            if subscription.current_period.end else None,
    )


# Entitlement Routes
@app.get("/customers/{customer_id}/entitlements", response_model=EntitlementListResponse, tags=["entitlements"])
async def get_customer_entitlements(
    customer_id: str,
    entitlements: EntitlementService = Depends(get_entitlement_service),
) -> EntitlementListResponse:
    """Get all entitlements for a customer."""
    ents = await entitlements.check_all(customer_id)
    
    return EntitlementListResponse(
        entitlements=[
            EntitlementCheckResponse(
                entitlement_key=ent.entitlement_key,
                has_access=ent.as_bool(),
                value=ent. current_value,
                source=ent. source. value,
                expires_at=ent.expires_at. isoformat() if ent.expires_at else None,
            )
            for ent in ents
        ]
    )


@app.get("/customers/{customer_id}/entitlements/{entitlement_key}", response_model=EntitlementCheckResponse, tags=["entitlements"])
async def check_entitlement(
    customer_id: str,
    entitlement_key: str,
    entitlements: EntitlementService = Depends(get_entitlement_service),
) -> EntitlementCheckResponse:
    """Check a specific entitlement for a customer."""
    from subscriptio.core.exceptions import EntitlementNotFoundError
    
    try:
        ent = await entitlements.check(customer_id, entitlement_key)
    except EntitlementNotFoundError:
        raise HTTPException(status_code=404, detail=f"Entitlement '{entitlement_key}' not found")
    
    return EntitlementCheckResponse(
        entitlement_key=ent.entitlement_key,
        has_access=ent.as_bool(),
        value=ent.current_value,
        source=ent.source.value,
        expires_at=ent.expires_at.isoformat() if ent.expires_at else None,
    )


@app.get("/customers/{customer_id}/can-access/{feature}", tags=["entitlements"])
async def can_access_feature(
    customer_id: str,
    feature: str,
    entitlements:  EntitlementService = Depends(get_entitlement_service),
) -> dict[str, bool]: 
    """Quick check if customer can access a feature."""
    has_access = await entitlements.has_access(customer_id, feature)
    return {"has_access": has_access}


@app.post("/customers/{customer_id}/entitlements/grant", response_model=EntitlementCheckResponse, tags=["entitlements"])
async def grant_entitlement_override(
    customer_id: str,
    request: GrantEntitlementRequest,
    entitlements: EntitlementService = Depends(get_entitlement_service),
) -> EntitlementCheckResponse: 
    """Grant an entitlement override to a customer."""
    from datetime import datetime, timedelta
    from subscriptio.core.exceptions import EntitlementNotFoundError
    
    expires_at = None
    if request. expires_in_days:
        expires_at = datetime. utcnow() + timedelta(days=request.expires_in_days)
    
    try: 
        override = await entitlements.grant_override(
            customer_id=customer_id,
            entitlement_key=request.entitlement_key,
            value=request.value,
            expires_at=expires_at,
            reason=request.reason,
        )
    except EntitlementNotFoundError: 
        raise HTTPException(status_code=404, detail=f"Entitlement '{request.entitlement_key}' not found")
    
    # Return the new resolved entitlement
    ent = await entitlements.check(customer_id, request. entitlement_key)
    
    return EntitlementCheckResponse(
        entitlement_key=ent.entitlement_key,
        has_access=ent.as_bool(),
        value=ent. current_value,
        source=ent.source.value,
        expires_at=ent.expires_at.isoformat() if ent.expires_at else None,
    )


@app.delete("/customers/{customer_id}/entitlements/{entitlement_key}/override", tags=["entitlements"])
async def revoke_entitlement_override(
    customer_id:  str,
    entitlement_key:  str,
    entitlements: EntitlementService = Depends(get_entitlement_service),
) -> dict[str, bool]: 
    """Revoke an entitlement override from a customer."""
    deleted = await entitlements.revoke_override(customer_id, entitlement_key)
    return {"deleted": deleted}


# Health check
@app.get("/health", tags=["system"])
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn. run(app, host="0.0.0.0", port=8000)