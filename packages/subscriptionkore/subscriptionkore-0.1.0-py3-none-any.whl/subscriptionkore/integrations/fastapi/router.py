"""FastAPI webhook router."""

from __future__ import annotations

from typing import Annotated, Callable, Awaitable

from fastapi import APIRouter, Depends, HTTPException, Request, Response
import structlog

from subscriptionkore.core.exceptions import (
    WebhookPayloadInvalidError,
    WebhookProcessingError,
    WebhookSignatureInvalidError,
)
from subscriptionkore.integrations.fastapi.dependencies import get_webhook_processor
from subscriptionkore.services.webhook_processor import WebhookProcessor, WebhookResult

logger = structlog.get_logger()


def create_webhook_router(
    prefix: str = "/webhooks",
    on_event: Callable[[WebhookResult], Awaitable[None]] | None = None,
    tags: list[str] | None = None,
) -> APIRouter:
    """
    Create a FastAPI router for handling payment provider webhooks.

    Args:
        prefix: URL prefix for webhook endpoints
        on_event: Optional callback for processed events
        tags: OpenAPI tags for the router

    Returns:
        Configured APIRouter

    Example:
        ```python
        from fastapi import FastAPI
        from subscriptionkore. integrations.fastapi import create_webhook_router

        app = FastAPI()

        async def handle_event(result):
            print(f"Processed event: {result.event_id}")

        webhook_router = create_webhook_router(
            prefix="/webhooks",
            on_event=handle_event,
        )

        app.include_router(webhook_router)
        ```
    """
    router = APIRouter(prefix=prefix, tags=tags or ["webhooks"])

    async def handle_webhook(
        provider: str,
        request: Request,
        processor: Annotated[WebhookProcessor, Depends(get_webhook_processor)],
    ) -> Response:
        """Generic webhook handler for all providers."""
        log = logger.bind(provider=provider)

        # Read raw body for signature verification
        body = await request.body()
        headers = dict(request.headers)

        try:
            result = await processor.process(
                provider=provider,
                payload=body,
                headers=headers,
            )

            # Call optional event handler
            if on_event:
                try:
                    await on_event(result)
                except Exception as e:
                    log.error("Event handler failed", error=str(e))

            log.info(
                "Webhook processed",
                event_id=result.event_id,
                status=result.status,
            )

            return Response(
                content='{"status": "ok"}',
                status_code=200,
                media_type="application/json",
            )

        except WebhookSignatureInvalidError:
            log.warning("Invalid webhook signature")
            raise HTTPException(status_code=401, detail="Invalid signature")

        except WebhookPayloadInvalidError as e:
            log.warning("Invalid webhook payload", reason=e.reason)
            raise HTTPException(status_code=400, detail=str(e))

        except WebhookProcessingError as e:
            log.error("Webhook processing failed", error=str(e))
            # Return 500 so provider retries
            raise HTTPException(status_code=500, detail="Processing failed")

    # Register endpoints for each provider
    @router.post("/stripe")
    async def stripe_webhook(
        request: Request,
        processor: Annotated[WebhookProcessor, Depends(get_webhook_processor)],
    ) -> Response:
        """Handle Stripe webhooks."""
        return await handle_webhook("stripe", request, processor)

    @router.post("/paddle")
    async def paddle_webhook(
        request: Request,
        processor: Annotated[WebhookProcessor, Depends(get_webhook_processor)],
    ) -> Response:
        """Handle Paddle webhooks."""
        return await handle_webhook("paddle", request, processor)

    @router.post("/lemonsqueezy")
    async def lemonsqueezy_webhook(
        request: Request,
        processor: Annotated[WebhookProcessor, Depends(get_webhook_processor)],
    ) -> Response:
        """Handle LemonSqueezy webhooks."""
        return await handle_webhook("lemonsqueezy", request, processor)

    @router.post("/chargebee")
    async def chargebee_webhook(
        request: Request,
        processor: Annotated[WebhookProcessor, Depends(get_webhook_processor)],
    ) -> Response:
        """Handle Chargebee webhooks."""
        return await handle_webhook("chargebee", request, processor)

    return router
