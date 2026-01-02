"""FastAPI integration."""

from subscriptionkore.integrations.fastapi.dependencies import (
    get_customer_manager,
    get_entitlement_service,
    get_provider,
    get_subscriptionkore_manager,
    get_webhook_processor,
)
from subscriptionkore.integrations.fastapi.router import create_webhook_router
from subscriptionkore.integrations.fastapi.setup import setup_subscriptionkore

__all__ = [
    "setup_subscriptionkore",
    "create_webhook_router",
    "get_subscriptionkore_manager",
    "get_customer_manager",
    "get_entitlement_service",
    "get_provider",
    "get_webhook_processor",
]
