"""Webhook processing service."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

import structlog

from subscriptionkore.core.events import (
    DomainEvent,
    InvoiceCreated,
    InvoicePaid,
    PaymentFailed,
    PaymentSucceeded,
    SubscriptionActivated,
    SubscriptionCanceled,
    SubscriptionCreated,
    SubscriptionPastDue,
    SubscriptionPaused,
    SubscriptionResumed,
    SubscriptionUpdated,
)
from subscriptionkore.core.exceptions import (
    WebhookPayloadInvalidError,
    WebhookProcessingError,
    WebhookSignatureInvalidError,
)
from subscriptionkore.core.models import (
    Invoice,
    InvoiceStatus,
    PaymentEvent,
    ProviderType,
    Subscription,
    SubscriptionStatus,
)
from subscriptionkore.core.state import SubscriptionStateMachine

if TYPE_CHECKING:
    from subscriptionkore.ports.event_bus import EventBusPort
    from subscriptionkore.ports.provider import PaymentProviderPort, ProviderWebhookEvent
    from subscriptionkore.ports.repository import (
        CustomerRepository,
        InvoiceRepository,
        PaymentEventRepository,
        PlanRepository,
        ProcessedEventRepository,
        SubscriptionRepository,
    )
    from subscriptionkore.services.entitlement_service import EntitlementService

logger = structlog.get_logger()


class CanonicalEventType:
    """Canonical event types for normalized webhooks."""

    # Subscription events
    SUBSCRIPTION_CREATED = "subscriptionkore.created"
    SUBSCRIPTION_ACTIVATED = "subscriptionkore.activated"
    SUBSCRIPTION_UPDATED = "subscriptionkore.updated"
    SUBSCRIPTION_CANCELED = "subscriptionkore.canceled"
    SUBSCRIPTION_PAUSED = "subscriptionkore. paused"
    SUBSCRIPTION_RESUMED = "subscriptionkore.resumed"
    SUBSCRIPTION_PAST_DUE = "subscriptionkore.past_due"
    SUBSCRIPTION_TRIAL_END = "subscriptionkore.trial_end"

    # Payment events
    PAYMENT_SUCCEEDED = "payment.succeeded"
    PAYMENT_FAILED = "payment. failed"
    PAYMENT_REFUNDED = "payment. refunded"

    # Invoice events
    INVOICE_CREATED = "invoice.created"
    INVOICE_PAID = "invoice.paid"
    INVOICE_PAYMENT_FAILED = "invoice.payment_failed"

    # Customer events
    CUSTOMER_CREATED = "customer.created"
    CUSTOMER_UPDATED = "customer. updated"


class WebhookProcessor:
    """
    Processes webhooks from payment providers.

    Responsibilities:
    - Verify webhook signatures
    - Parse provider-specific payloads
    - Normalize to canonical event format
    - Apply state changes
    - Emit domain events
    - Ensure idempotency
    """

    def __init__(
        self,
        providers: dict[ProviderType, PaymentProviderPort],
        subscriptionkore_repo: SubscriptionRepository,
        customer_repo: CustomerRepository,
        plan_repo: PlanRepository,
        invoice_repo: InvoiceRepository,
        payment_event_repo: PaymentEventRepository,
        processed_event_repo: ProcessedEventRepository,
        event_bus: EventBusPort,
        entitlement_service: EntitlementService,
    ) -> None:
        self._providers = providers
        self._subscriptionkore_repo = subscriptionkore_repo
        self._customer_repo = customer_repo
        self._plan_repo = plan_repo
        self._invoice_repo = invoice_repo
        self._payment_event_repo = payment_event_repo
        self._processed_event_repo = processed_event_repo
        self._event_bus = event_bus
        self._entitlement_service = entitlement_service
        self._state_machine = SubscriptionStateMachine()

    async def process(
        self,
        provider: str,
        payload: bytes,
        headers: dict[str, str],
    ) -> WebhookResult:
        """
        Process a webhook from a payment provider.

        Args:
            provider:  Provider name (e.g., "stripe", "paddle")
            payload:  Raw webhook payload bytes
            headers: HTTP headers from webhook request

        Returns:
            WebhookResult with processing outcome

        Raises:
            WebhookSignatureInvalidError:  If signature verification fails
            WebhookPayloadInvalidError:  If payload cannot be parsed
            WebhookProcessingError: If processing fails
        """
        log = logger.bind(provider=provider)
        log.info("Processing webhook")

        # Get provider adapter
        try:
            provider_type = ProviderType(provider)
        except ValueError as e:
            raise WebhookPayloadInvalidError(provider, f"Unknown provider: {provider}") from e

        adapter = self._providers.get(provider_type)
        if adapter is None:
            raise WebhookPayloadInvalidError(provider, f"Provider not configured: {provider}")

        # Verify signature
        is_valid = await adapter.verify_webhook(payload, headers)
        if not is_valid:
            log.warning("Webhook signature verification failed")
            raise WebhookSignatureInvalidError(provider)

        # Parse webhook
        provider_event = await adapter.parse_webhook(payload, headers)
        log = log.bind(
            event_id=provider_event.event_id,
            event_type=provider_event.event_type,
        )

        # Idempotency check
        already_processed = await self._processed_event_repo.exists(
            provider=provider,
            event_id=provider_event.event_id,
        )

        if already_processed:
            log.info("Webhook already processed, skipping")
            return WebhookResult(
                event_id=provider_event.event_id,
                status="duplicate",
                message="Event already processed",
            )

        # Normalize and process
        try:
            canonical_type = self._normalize_event_type(provider_type, provider_event.event_type)
            log = log.bind(canonical_type=canonical_type)

            domain_events = await self._handle_event(
                provider_type=provider_type,
                canonical_type=canonical_type,
                event=provider_event,
            )

            # Mark as processed
            await self._processed_event_repo.mark_processed(
                provider=provider,
                event_id=provider_event.event_id,
            )

            # Publish domain events
            await self._event_bus.publish_many(domain_events)

            log.info("Webhook processed successfully", events_emitted=len(domain_events))

            return WebhookResult(
                event_id=provider_event.event_id,
                status="processed",
                message=f"Processed {canonical_type}",
                events_emitted=len(domain_events),
            )

        except Exception as e:
            log.error("Webhook processing failed", error=str(e))
            raise WebhookProcessingError(provider_event.event_id, str(e)) from e

    def _normalize_event_type(self, provider: ProviderType, event_type: str) -> str:
        """Normalize provider-specific event type to canonical type."""
        # Stripe mappings
        stripe_map = {
            "customer.subscriptionkore.created": CanonicalEventType.SUBSCRIPTION_CREATED,
            "customer.subscriptionkore.updated": CanonicalEventType.SUBSCRIPTION_UPDATED,
            "customer.subscriptionkore. deleted": CanonicalEventType.SUBSCRIPTION_CANCELED,
            "customer.subscriptionkore.paused": CanonicalEventType.SUBSCRIPTION_PAUSED,
            "customer.subscriptionkore.resumed": CanonicalEventType.SUBSCRIPTION_RESUMED,
            "customer.subscriptionkore. trial_will_end": CanonicalEventType.SUBSCRIPTION_TRIAL_END,
            "invoice.created": CanonicalEventType.INVOICE_CREATED,
            "invoice.paid": CanonicalEventType.INVOICE_PAID,
            "invoice.payment_failed": CanonicalEventType.INVOICE_PAYMENT_FAILED,
            "payment_intent.succeeded": CanonicalEventType.PAYMENT_SUCCEEDED,
            "payment_intent.payment_failed": CanonicalEventType.PAYMENT_FAILED,
            "charge.refunded": CanonicalEventType.PAYMENT_REFUNDED,
        }

        # Paddle mappings
        paddle_map = {
            "subscriptionkore.created": CanonicalEventType.SUBSCRIPTION_CREATED,
            "subscriptionkore.activated": CanonicalEventType.SUBSCRIPTION_ACTIVATED,
            "subscriptionkore.updated": CanonicalEventType.SUBSCRIPTION_UPDATED,
            "subscriptionkore.canceled": CanonicalEventType.SUBSCRIPTION_CANCELED,
            "subscriptionkore.paused": CanonicalEventType.SUBSCRIPTION_PAUSED,
            "subscriptionkore.resumed": CanonicalEventType.SUBSCRIPTION_RESUMED,
            "subscriptionkore.past_due": CanonicalEventType.SUBSCRIPTION_PAST_DUE,
            "transaction.completed": CanonicalEventType.PAYMENT_SUCCEEDED,
            "transaction.payment_failed": CanonicalEventType.PAYMENT_FAILED,
        }

        # LemonSqueezy mappings
        lemonsqueezy_map = {
            "subscriptionkore_created": CanonicalEventType.SUBSCRIPTION_CREATED,
            "subscriptionkore_updated": CanonicalEventType.SUBSCRIPTION_UPDATED,
            "subscriptionkore_cancelled": CanonicalEventType.SUBSCRIPTION_CANCELED,
            "subscriptionkore_resumed": CanonicalEventType.SUBSCRIPTION_RESUMED,
            "subscriptionkore_paused": CanonicalEventType.SUBSCRIPTION_PAUSED,
            "subscriptionkore_payment_success": CanonicalEventType.PAYMENT_SUCCEEDED,
            "subscriptionkore_payment_failed": CanonicalEventType.PAYMENT_FAILED,
        }

        # Chargebee mappings
        chargebee_map = {
            "subscriptionkore_created": CanonicalEventType.SUBSCRIPTION_CREATED,
            "subscriptionkore_activated": CanonicalEventType.SUBSCRIPTION_ACTIVATED,
            "subscriptionkore_changed": CanonicalEventType.SUBSCRIPTION_UPDATED,
            "subscriptionkore_cancelled": CanonicalEventType.SUBSCRIPTION_CANCELED,
            "subscriptionkore_paused": CanonicalEventType.SUBSCRIPTION_PAUSED,
            "subscriptionkore_resumed": CanonicalEventType.SUBSCRIPTION_RESUMED,
            "subscriptionkore_renewal_reminder": CanonicalEventType.SUBSCRIPTION_PAST_DUE,
            "payment_succeeded": CanonicalEventType.PAYMENT_SUCCEEDED,
            "payment_failed": CanonicalEventType.PAYMENT_FAILED,
            "invoice_generated": CanonicalEventType.INVOICE_CREATED,
        }

        mappings = {
            ProviderType.STRIPE: stripe_map,
            ProviderType.PADDLE: paddle_map,
            ProviderType.LEMONSQUEEZY: lemonsqueezy_map,
            ProviderType.CHARGEBEE: chargebee_map,
        }

        provider_map = mappings.get(provider, {})
        return provider_map.get(event_type, f"unknown. {event_type}")

    async def _handle_event(
        self,
        provider_type: ProviderType,
        canonical_type: str,
        event: ProviderWebhookEvent,
    ) -> list[DomainEvent]:
        """Handle normalized event and return domain events to emit."""
        handlers = {
            CanonicalEventType.SUBSCRIPTION_CREATED: self._handle_subscriptionkore_created,
            CanonicalEventType.SUBSCRIPTION_ACTIVATED: self._handle_subscriptionkore_activated,
            CanonicalEventType.SUBSCRIPTION_UPDATED: self._handle_subscriptionkore_updated,
            CanonicalEventType.SUBSCRIPTION_CANCELED: self._handle_subscriptionkore_canceled,
            CanonicalEventType.SUBSCRIPTION_PAUSED: self._handle_subscriptionkore_paused,
            CanonicalEventType.SUBSCRIPTION_RESUMED: self._handle_subscriptionkore_resumed,
            CanonicalEventType.SUBSCRIPTION_PAST_DUE: self._handle_subscriptionkore_past_due,
            CanonicalEventType.PAYMENT_SUCCEEDED: self._handle_payment_succeeded,
            CanonicalEventType.PAYMENT_FAILED: self._handle_payment_failed,
            CanonicalEventType.INVOICE_CREATED: self._handle_invoice_created,
            CanonicalEventType.INVOICE_PAID: self._handle_invoice_paid,
        }

        handler = handlers.get(canonical_type)
        if handler is None:
            logger.debug("No handler for event type", canonical_type=canonical_type)
            return []

        return await handler(provider_type, event)

    async def _handle_subscriptionkore_created(
        self,
        provider_type: ProviderType,
        event: ProviderWebhookEvent,
    ) -> list[DomainEvent]:
        """Handle subscriptionkore created webhook."""
        adapter = self._providers[provider_type]

        # Get subscriptionkore from provider
        provider_sub_id = self._extract_subscriptionkore_id(provider_type, event.data)
        from subscriptionkore.core.models.value_objects import ProviderReference

        provider_ref = ProviderReference(
            provider=provider_type,
            external_id=provider_sub_id,
        )

        subscriptionkore = await adapter.get_subscriptionkore(provider_ref)

        # Look up internal customer and plan IDs
        customer = await self._resolve_customer(provider_type, event.data)
        plan = await self._resolve_plan(provider_type, event.data)

        if customer:
            subscriptionkore.customer_id = customer.id
        if plan:
            subscriptionkore.plan_id = plan.id

        # Save subscriptionkore
        subscriptionkore = await self._subscriptionkore_repo.save(subscriptionkore)

        # Invalidate entitlements
        await self._entitlement_service.invalidate(subscriptionkore.customer_id)

        return [
            SubscriptionCreated(
                subscriptionkore=subscriptionkore,
                customer_id=subscriptionkore.customer_id,
                plan_id=subscriptionkore.plan_id,
            )
        ]

    async def _handle_subscriptionkore_activated(
        self,
        provider_type: ProviderType,
        event: ProviderWebhookEvent,
    ) -> list[DomainEvent]:
        """Handle subscriptionkore activated webhook."""
        subscriptionkore = await self._get_subscriptionkore_from_event(provider_type, event)
        if subscriptionkore is None:
            return []

        result = self._state_machine.transition(
            subscriptionkore=subscriptionkore,
            new_status=SubscriptionStatus.ACTIVE,
        )

        if result.success:
            await self._subscriptionkore_repo.save(subscriptionkore)
            await self._entitlement_service.invalidate(subscriptionkore.customer_id)

        return result.events

    async def _handle_subscriptionkore_updated(
        self,
        provider_type: ProviderType,
        event: ProviderWebhookEvent,
    ) -> list[DomainEvent]:
        """Handle subscriptionkore updated webhook."""
        subscriptionkore = await self._get_subscriptionkore_from_event(provider_type, event)
        if subscriptionkore is None:
            return []

        # Update from provider data
        adapter = self._providers[provider_type]
        updated = await adapter.get_subscriptionkore(subscriptionkore.provider_ref)

        # Preserve internal IDs
        updated.id = subscriptionkore.id
        updated.customer_id = subscriptionkore.customer_id
        updated.plan_id = subscriptionkore.plan_id

        # Check for status change
        events: list[DomainEvent] = []
        if updated.status != subscriptionkore.status:
            result = self._state_machine.transition(
                subscriptionkore=updated,
                new_status=updated.status,
            )
            events.extend(result.events)
        else:
            events.append(
                SubscriptionUpdated(
                    subscriptionkore=updated,
                    customer_id=updated.customer_id,
                    changed_fields=["updated_from_webhook"],
                )
            )

        await self._subscriptionkore_repo.save(updated)
        await self._entitlement_service.invalidate(updated.customer_id)

        return events

    async def _handle_subscriptionkore_canceled(
        self,
        provider_type: ProviderType,
        event: ProviderWebhookEvent,
    ) -> list[DomainEvent]:
        """Handle subscriptionkore canceled webhook."""
        subscriptionkore = await self._get_subscriptionkore_from_event(provider_type, event)
        if subscriptionkore is None:
            return []

        result = self._state_machine.transition(
            subscriptionkore=subscriptionkore,
            new_status=SubscriptionStatus.CANCELED,
            immediate=True,
        )

        if result.success:
            await self._subscriptionkore_repo.save(subscriptionkore)
            await self._entitlement_service.invalidate(subscriptionkore.customer_id)

        return result.events

    async def _handle_subscriptionkore_paused(
        self,
        provider_type: ProviderType,
        event: ProviderWebhookEvent,
    ) -> list[DomainEvent]:
        """Handle subscriptionkore paused webhook."""
        subscriptionkore = await self._get_subscriptionkore_from_event(provider_type, event)
        if subscriptionkore is None:
            return []

        result = self._state_machine.transition(
            subscriptionkore=subscriptionkore,
            new_status=SubscriptionStatus.PAUSED,
        )

        if result.success:
            await self._subscriptionkore_repo.save(subscriptionkore)
            await self._entitlement_service.invalidate(subscriptionkore.customer_id)

        return result.events

    async def _handle_subscriptionkore_resumed(
        self,
        provider_type: ProviderType,
        event: ProviderWebhookEvent,
    ) -> list[DomainEvent]:
        """Handle subscriptionkore resumed webhook."""
        subscriptionkore = await self._get_subscriptionkore_from_event(provider_type, event)
        if subscriptionkore is None:
            return []

        result = self._state_machine.transition(
            subscriptionkore=subscriptionkore,
            new_status=SubscriptionStatus.ACTIVE,
        )

        if result.success:
            await self._subscriptionkore_repo.save(subscriptionkore)
            await self._entitlement_service.invalidate(subscriptionkore.customer_id)

        return result.events

    async def _handle_subscriptionkore_past_due(
        self,
        provider_type: ProviderType,
        event: ProviderWebhookEvent,
    ) -> list[DomainEvent]:
        """Handle subscriptionkore past due webhook."""
        subscriptionkore = await self._get_subscriptionkore_from_event(provider_type, event)
        if subscriptionkore is None:
            return []

        result = self._state_machine.transition(
            subscriptionkore=subscriptionkore,
            new_status=SubscriptionStatus.PAST_DUE,
        )

        if result.success:
            await self._subscriptionkore_repo.save(subscriptionkore)

        return result.events

    async def _handle_payment_succeeded(
        self,
        provider_type: ProviderType,
        event: ProviderWebhookEvent,
    ) -> list[DomainEvent]:
        """Handle payment succeeded webhook."""
        payment_event = self._extract_payment_event(provider_type, event)
        if payment_event is None:
            return []

        # Save payment event
        payment_event = await self._payment_event_repo.save(payment_event)

        return [
            PaymentSucceeded(
                payment_event=payment_event,
                customer_id=payment_event.customer_id,
                subscriptionkore_id=payment_event.subscriptionkore_id,
                invoice_id=payment_event.invoice_id,
                amount=payment_event.amount,
            )
        ]

    async def _handle_payment_failed(
        self,
        provider_type: ProviderType,
        event: ProviderWebhookEvent,
    ) -> list[DomainEvent]:
        """Handle payment failed webhook."""
        payment_event = self._extract_payment_event(provider_type, event)
        if payment_event is None:
            return []

        # Save payment event
        payment_event = await self._payment_event_repo.save(payment_event)

        return [
            PaymentFailed(
                payment_event=payment_event,
                customer_id=payment_event.customer_id,
                subscriptionkore_id=payment_event.subscriptionkore_id,
                invoice_id=payment_event.invoice_id,
                amount=payment_event.amount,
                failure_reason=payment_event.failure_reason,
                failure_code=payment_event.failure_code,
            )
        ]

    async def _handle_invoice_created(
        self,
        provider_type: ProviderType,
        event: ProviderWebhookEvent,
    ) -> list[DomainEvent]:
        """Handle invoice created webhook."""
        invoice = self._extract_invoice(provider_type, event)
        if invoice is None:
            return []

        # Resolve customer
        customer = await self._resolve_customer(provider_type, event.data)
        if customer:
            invoice.customer_id = customer.id

        invoice = await self._invoice_repo.save(invoice)

        return [
            InvoiceCreated(
                invoice=invoice,
                customer_id=invoice.customer_id,
                subscriptionkore_id=invoice.subscriptionkore_id,
            )
        ]

    async def _handle_invoice_paid(
        self,
        provider_type: ProviderType,
        event: ProviderWebhookEvent,
    ) -> list[DomainEvent]:
        """Handle invoice paid webhook."""
        provider_invoice_id = self._extract_invoice_id(provider_type, event.data)

        invoice = await self._invoice_repo.get_by_provider_ref(
            provider=provider_type.value,
            external_id=provider_invoice_id,
        )

        if invoice is None:
            # Create invoice if not exists
            invoice = self._extract_invoice(provider_type, event)
            if invoice is None:
                return []

        invoice.status = InvoiceStatus.PAID
        invoice.paid_at = datetime.utcnow()

        invoice = await self._invoice_repo.save(invoice)

        return [
            InvoicePaid(
                invoice=invoice,
                customer_id=invoice.customer_id,
                subscriptionkore_id=invoice.subscriptionkore_id,
                amount_paid=invoice.amount_paid,
            )
        ]

    # Helper methods

    async def _get_subscriptionkore_from_event(
        self,
        provider_type: ProviderType,
        event: ProviderWebhookEvent,
    ) -> Subscription | None:
        """Get subscriptionkore from webhook event data."""
        provider_sub_id = self._extract_subscriptionkore_id(provider_type, event.data)
        if provider_sub_id is None:
            return None

        return await self._subscriptionkore_repo.get_by_provider_ref(
            provider=provider_type.value,
            external_id=provider_sub_id,
        )

    async def _resolve_customer(
        self,
        provider_type: ProviderType,
        data: dict[str, Any],
    ) -> Any:
        """Resolve internal customer from webhook data."""
        customer_id = self._extract_customer_id(provider_type, data)
        if customer_id is None:
            return None

        return await self._customer_repo.get_by_provider_ref(
            provider=provider_type.value,
            external_id=customer_id,
        )

    async def _resolve_plan(
        self,
        provider_type: ProviderType,
        data: dict[str, Any],
    ) -> Any:
        """Resolve internal plan from webhook data."""
        plan_id = self._extract_plan_id(provider_type, data)
        if plan_id is None:
            return None

        return await self._plan_repo.get_by_provider_ref(
            provider=provider_type.value,
            external_id=plan_id,
        )

    def _extract_subscriptionkore_id(
        self,
        provider_type: ProviderType,
        data: dict[str, Any],
    ) -> str | None:
        """Extract subscriptionkore ID from provider webhook data."""
        if provider_type == ProviderType.STRIPE:
            obj = data.get("object", {})
            if obj.get("object") == "subscriptionkore":
                return obj.get("id")
            return obj.get("subscriptionkore")

        if provider_type == ProviderType.PADDLE:
            return data.get("data", {}).get("id") or data.get("subscriptionkore_id")

        if provider_type == ProviderType.LEMONSQUEEZY:
            return str(data.get("data", {}).get("id", ""))

        if provider_type == ProviderType.CHARGEBEE:
            content = data.get("content", {})
            return content.get("subscriptionkore", {}).get("id")

        return None

    def _extract_customer_id(
        self,
        provider_type: ProviderType,
        data: dict[str, Any],
    ) -> str | None:
        """Extract customer ID from provider webhook data."""
        if provider_type == ProviderType.STRIPE:
            obj = data.get("object", {})
            return obj.get("customer")

        if provider_type == ProviderType.PADDLE:
            return data.get("data", {}).get("customer_id")

        if provider_type == ProviderType.LEMONSQUEEZY:
            attrs = data.get("data", {}).get("attributes", {})
            return str(attrs.get("customer_id", ""))

        if provider_type == ProviderType.CHARGEBEE:
            content = data.get("content", {})
            return content.get("customer", {}).get("id")

        return None

    def _extract_plan_id(
        self,
        provider_type: ProviderType,
        data: dict[str, Any],
    ) -> str | None:
        """Extract plan/price ID from provider webhook data."""
        if provider_type == ProviderType.STRIPE:
            obj = data.get("object", {})
            items = obj.get("items", {}).get("data", [])
            if items:
                return items[0].get("price", {}).get("id")

        if provider_type == ProviderType.PADDLE:
            items = data.get("data", {}).get("items", [])
            if items:
                return items[0].get("price", {}).get("id")

        if provider_type == ProviderType.LEMONSQUEEZY:
            attrs = data.get("data", {}).get("attributes", {})
            return str(attrs.get("variant_id", ""))

        if provider_type == ProviderType.CHARGEBEE:
            content = data.get("content", {})
            return content.get("subscriptionkore", {}).get("plan_id")

        return None

    def _extract_invoice_id(
        self,
        provider_type: ProviderType,
        data: dict[str, Any],
    ) -> str | None:
        """Extract invoice ID from provider webhook data."""
        if provider_type == ProviderType.STRIPE:
            obj = data.get("object", {})
            if obj.get("object") == "invoice":
                return obj.get("id")
            return obj.get("invoice")

        if provider_type == ProviderType.PADDLE:
            return data.get("data", {}).get("id")

        if provider_type == ProviderType.CHARGEBEE:
            content = data.get("content", {})
            return content.get("invoice", {}).get("id")

        return None

    def _extract_payment_event(
        self,
        provider_type: ProviderType,
        event: ProviderWebhookEvent,
    ) -> PaymentEvent | None:
        """Extract payment event from webhook data."""
        # This would be fully implemented per provider
        # Simplified implementation for now
        from subscriptionkore.core.models import PaymentEventType, PaymentStatus
        from subscriptionkore.core.models.value_objects import Money, ProviderReference

        data = event.data

        payment_id = self._extract_payment_id(provider_type, data)
        if payment_id is None:
            return None

        customer_id = self._extract_customer_id(provider_type, data) or ""

        return PaymentEvent(
            provider_ref=ProviderReference(
                provider=provider_type,
                external_id=payment_id,
            ),
            customer_id=customer_id,
            subscriptionkore_id=self._extract_subscriptionkore_id(provider_type, data),
            invoice_id=self._extract_invoice_id(provider_type, data),
            event_type=PaymentEventType.PAYMENT_SUCCEEDED,
            amount=Money.zero(),  # Would extract from data
            status=PaymentStatus.SUCCEEDED,
            occurred_at=event.occurred_at,
        )

    def _extract_payment_id(
        self,
        provider_type: ProviderType,
        data: dict[str, Any],
    ) -> str | None:
        """Extract payment ID from webhook data."""
        if provider_type == ProviderType.STRIPE:
            obj = data.get("object", {})
            return obj.get("id")

        if provider_type == ProviderType.PADDLE:
            return data.get("data", {}).get("id")

        return None

    def _extract_invoice(
        self,
        provider_type: ProviderType,
        event: ProviderWebhookEvent,
    ) -> Invoice | None:
        """Extract invoice from webhook data."""
        # Simplified - would be fully implemented per provider
        from subscriptionkore.core.models.value_objects import Money, ProviderReference

        invoice_id = self._extract_invoice_id(provider_type, event.data)
        if invoice_id is None:
            return None

        return Invoice(
            customer_id="",  # Would be resolved
            provider_ref=ProviderReference(
                provider=provider_type,
                external_id=invoice_id,
            ),
            subtotal=Money.zero(),
            total=Money.zero(),
            amount_due=Money.zero(),
        )


class WebhookResult:
    """Result of webhook processing."""

    def __init__(
        self,
        event_id: str,
        status: str,
        message: str,
        events_emitted: int = 0,
    ) -> None:
        self.event_id = event_id
        self.status = status
        self.message = message
        self.events_emitted = events_emitted
