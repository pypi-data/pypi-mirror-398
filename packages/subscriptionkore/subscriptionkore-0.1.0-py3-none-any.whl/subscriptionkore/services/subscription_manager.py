"""Subscription management service."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import structlog

from subscriptionkore.core.events import (
    SubscriptionCreated,
    SubscriptionPlanChanged,
    SubscriptionUpdated,
)
from subscriptionkore.core.exceptions import EntityNotFoundError, InvalidStateTransitionError
from subscriptionkore.core.models import (
    Plan,
    ProviderReference,
    Subscription,
    SubscriptionStatus,
)
from subscriptionkore.core.state import SubscriptionStateMachine
from subscriptionkore.ports.provider import (
    ChangePlanRequest,
    ChangePreview,
    CreateSubscriptionRequest,
    DiscountRequest,
    PaymentProviderPort,
    ProrationBehavior,
    UpdateSubscriptionRequest,
)

if TYPE_CHECKING:
    from subscriptionkore.ports.event_bus import EventBusPort
    from subscriptionkore.ports.repository import (
        CustomerRepository,
        PlanRepository,
        SubscriptionRepository,
    )

logger = structlog.get_logger()


class SubscriptionManager:
    """
    Manages subscriptionkore lifecycle operations.

    Provides a unified interface for subscriptionkore operations across providers.
    """

    def __init__(
        self,
        subscriptionkore_repo: SubscriptionRepository,
        customer_repo: CustomerRepository,
        plan_repo: PlanRepository,
        provider: PaymentProviderPort,
        event_bus: EventBusPort,
    ) -> None:
        self._subscriptionkore_repo = subscriptionkore_repo
        self._customer_repo = customer_repo
        self._plan_repo = plan_repo
        self._provider = provider
        self._event_bus = event_bus
        self._state_machine = SubscriptionStateMachine()

    async def create(
        self,
        customer_id: str,
        plan_id: str,
        quantity: int = 1,
        trial_period_days: int | None = None,
        coupon_code: str | None = None,
        metadata: dict | None = None,
    ) -> Subscription:
        """
        Create a new subscriptionkore.

        Args:
            customer_id: Internal customer ID
            plan_id: Internal plan ID
            quantity:  Subscription quantity
            trial_period_days: Override trial period (None uses plan default)
            coupon_code: Optional coupon code to apply
            metadata: Additional metadata

        Returns:
            Created subscriptionkore

        Raises:
            EntityNotFoundError: If customer or plan not found
        """
        log = logger.bind(customer_id=customer_id, plan_id=plan_id)
        log.info("Creating subscriptionkore")

        # Get customer and plan
        customer = await self._customer_repo.get(customer_id)
        if customer is None:
            raise EntityNotFoundError("Customer", customer_id)

        plan = await self._plan_repo.get(plan_id)
        if plan is None:
            raise EntityNotFoundError("Plan", plan_id)

        # Get provider references
        customer_ref = customer.get_provider_ref(self._provider.provider_type.value)
        if customer_ref is None:
            raise EntityNotFoundError(
                "CustomerProviderRef",
                f"{customer_id}:{self._provider.provider_type.value}",
            )

        plan_ref = plan.get_provider_ref(self._provider.provider_type.value)
        if plan_ref is None:
            raise EntityNotFoundError(
                "PlanProviderRef",
                f"{plan_id}:{self._provider.provider_type.value}",
            )

        # Determine trial period
        effective_trial = trial_period_days
        if effective_trial is None and plan.trial_period_days:
            effective_trial = plan.trial_period_days

        # Create subscriptionkore in provider
        request = CreateSubscriptionRequest(
            customer_id=customer_id,
            plan_id=plan_id,
            quantity=quantity,
            trial_period_days=effective_trial,
            coupon_code=coupon_code,
            metadata=metadata or {},
        )

        subscriptionkore = await self._provider.create_subscriptionkore(
            request=request,
            customer_provider_ref=customer_ref,
            plan_provider_ref=plan_ref,
        )

        # Set internal IDs
        subscriptionkore.customer_id = customer_id
        subscriptionkore.plan_id = plan_id

        # Save to repository
        subscriptionkore = await self._subscriptionkore_repo.save(subscriptionkore)

        # Emit event
        await self._event_bus.publish(
            SubscriptionCreated(
                subscriptionkore=subscriptionkore,
                customer_id=customer_id,
                plan_id=plan_id,
            )
        )

        log.info(
            "Subscription created",
            subscriptionkore_id=subscriptionkore.id,
            status=subscriptionkore.status,
        )

        return subscriptionkore

    async def get(self, subscriptionkore_id: str) -> Subscription:
        """Get subscriptionkore by ID."""
        subscriptionkore = await self._subscriptionkore_repo.get(subscriptionkore_id)
        if subscriptionkore is None:
            raise EntityNotFoundError("Subscription", subscriptionkore_id)
        return subscriptionkore

    async def get_by_customer(
        self,
        customer_id: str,
        include_canceled: bool = False,
    ) -> list[Subscription]:
        """Get all subscriptionkores for a customer."""
        return await self._subscriptionkore_repo.list_by_customer(
            customer_id=customer_id,
            include_canceled=include_canceled,
        )

    async def get_active_by_customer(self, customer_id: str) -> list[Subscription]:
        """Get active subscriptionkores for a customer."""
        return await self._subscriptionkore_repo.list_active_by_customer(customer_id)

    async def update(
        self,
        subscriptionkore_id: str,
        quantity: int | None = None,
        metadata: dict | None = None,
    ) -> Subscription:
        """Update subscriptionkore quantity or metadata."""
        log = logger.bind(subscriptionkore_id=subscriptionkore_id)
        log.info("Updating subscriptionkore")

        subscriptionkore = await self.get(subscriptionkore_id)

        request = UpdateSubscriptionRequest(
            subscriptionkore_id=subscriptionkore_id,
            quantity=quantity,
            metadata=metadata,
        )

        updated = await self._provider.update_subscriptionkore(
            request=request,
            subscriptionkore_provider_ref=subscriptionkore.provider_ref,
        )

        # Preserve internal IDs
        updated.id = subscriptionkore.id
        updated.customer_id = subscriptionkore.customer_id
        updated.plan_id = subscriptionkore.plan_id

        # Determine changed fields
        changed_fields: list[str] = []
        if quantity is not None and subscriptionkore.quantity != quantity:
            changed_fields.append("quantity")
        if metadata is not None:
            changed_fields.append("metadata")

        updated = await self._subscriptionkore_repo.save(updated)

        if changed_fields:
            await self._event_bus.publish(
                SubscriptionUpdated(
                    subscriptionkore=updated,
                    customer_id=updated.customer_id,
                    changed_fields=changed_fields,
                )
            )

        log.info("Subscription updated", changed_fields=changed_fields)
        return updated

    async def cancel(
        self,
        subscriptionkore_id: str,
        immediate: bool = False,
        reason: str | None = None,
    ) -> Subscription:
        """
        Cancel a subscriptionkore.

        Args:
            subscriptionkore_id:  Subscription ID
            immediate: If True, cancel immediately.  If False, cancel at period end.
            reason: Optional cancellation reason

        Returns:
            Updated subscriptionkore
        """
        log = logger.bind(subscriptionkore_id=subscriptionkore_id, immediate=immediate)
        log.info("Canceling subscriptionkore")

        subscriptionkore = await self.get(subscriptionkore_id)

        # Cancel in provider
        updated = await self._provider.cancel_subscriptionkore(
            subscriptionkore_provider_ref=subscriptionkore.provider_ref,
            immediate=immediate,
        )

        # Apply state transition
        if immediate:
            target_status = SubscriptionStatus.CANCELED
        else:
            target_status = subscriptionkore.status  # Stay in current status
            updated.cancel_at_period_end = True
            updated.canceled_at = datetime.utcnow()

        result = self._state_machine.transition(
            subscriptionkore=updated,
            new_status=target_status,
            reason=reason,
            immediate=immediate,
        )

        if not result.success and result.error:
            raise result.error

        # Preserve internal IDs
        updated.id = subscriptionkore.id
        updated.customer_id = subscriptionkore.customer_id
        updated.plan_id = subscriptionkore.plan_id

        updated = await self._subscriptionkore_repo.save(updated)

        # Publish events
        await self._event_bus.publish_many(result.events)

        log.info(
            "Subscription canceled",
            status=updated.status,
            cancel_at_period_end=updated.cancel_at_period_end,
        )

        return updated

    async def pause(
        self,
        subscriptionkore_id: str,
        resumes_at: datetime | None = None,
    ) -> Subscription:
        """Pause a subscriptionkore."""
        log = logger.bind(subscriptionkore_id=subscriptionkore_id)
        log.info("Pausing subscriptionkore")

        subscriptionkore = await self.get(subscriptionkore_id)

        if not self._provider.capabilities.supports_pausing:
            raise InvalidStateTransitionError(
                from_state=subscriptionkore.status,
                to_state=SubscriptionStatus.PAUSED,
                reason=f"Provider {self._provider.provider_type} does not support pausing",
            )

        # Pause in provider
        updated = await self._provider.pause_subscriptionkore(
            subscriptionkore_provider_ref=subscriptionkore.provider_ref,
            resumes_at=resumes_at,
        )

        # Apply state transition
        result = self._state_machine.transition(
            subscriptionkore=updated,
            new_status=SubscriptionStatus.PAUSED,
        )

        if not result.success and result.error:
            raise result.error

        # Preserve internal IDs
        updated.id = subscriptionkore.id
        updated.customer_id = subscriptionkore.customer_id
        updated.plan_id = subscriptionkore.plan_id

        updated = await self._subscriptionkore_repo.save(updated)
        await self._event_bus.publish_many(result.events)

        log.info("Subscription paused", resumes_at=resumes_at)
        return updated

    async def resume(self, subscriptionkore_id: str) -> Subscription:
        """Resume a paused subscriptionkore."""
        log = logger.bind(subscriptionkore_id=subscriptionkore_id)
        log.info("Resuming subscriptionkore")

        subscriptionkore = await self.get(subscriptionkore_id)

        if subscriptionkore.status != SubscriptionStatus.PAUSED:
            raise InvalidStateTransitionError(
                from_state=subscriptionkore.status,
                to_state=SubscriptionStatus.ACTIVE,
                reason="Can only resume paused subscriptionkores",
            )

        # Resume in provider
        updated = await self._provider.resume_subscriptionkore(
            subscriptionkore_provider_ref=subscriptionkore.provider_ref,
        )

        # Apply state transition
        result = self._state_machine.transition(
            subscriptionkore=updated,
            new_status=SubscriptionStatus.ACTIVE,
        )

        if not result.success and result.error:
            raise result.error

        # Preserve internal IDs
        updated.id = subscriptionkore.id
        updated.customer_id = subscriptionkore.customer_id
        updated.plan_id = subscriptionkore.plan_id

        updated = await self._subscriptionkore_repo.save(updated)
        await self._event_bus.publish_many(result.events)

        log.info("Subscription resumed")
        return updated

    async def change_plan(
        self,
        subscriptionkore_id: str,
        new_plan_id: str,
        proration_behavior: ProrationBehavior = ProrationBehavior.CREATE_PRORATIONS,
    ) -> Subscription:
        """
        Change subscriptionkore plan (upgrade/downgrade).

        Args:
            subscriptionkore_id:  Subscription ID
            new_plan_id:  New plan ID
            proration_behavior:  How to handle proration

        Returns:
            Updated subscriptionkore
        """
        log = logger.bind(subscriptionkore_id=subscriptionkore_id, new_plan_id=new_plan_id)
        log.info("Changing subscriptionkore plan")

        subscriptionkore = await self.get(subscriptionkore_id)
        old_plan_id = subscriptionkore.plan_id

        # Get new plan
        new_plan = await self._plan_repo.get(new_plan_id)
        if new_plan is None:
            raise EntityNotFoundError("Plan", new_plan_id)

        new_plan_ref = new_plan.get_provider_ref(self._provider.provider_type.value)
        if new_plan_ref is None:
            raise EntityNotFoundError(
                "PlanProviderRef",
                f"{new_plan_id}:{self._provider.provider_type.value}",
            )

        # Get old plan for comparison
        old_plan = await self._plan_repo.get(old_plan_id)
        is_upgrade = new_plan.is_upgrade_from(old_plan) if old_plan else False

        # Change plan in provider
        request = ChangePlanRequest(
            subscriptionkore_id=subscriptionkore_id,
            new_plan_id=new_plan_id,
            proration_behavior=proration_behavior,
        )

        updated = await self._provider.change_plan(
            request=request,
            subscriptionkore_provider_ref=subscriptionkore.provider_ref,
            new_plan_provider_ref=new_plan_ref,
        )

        # Preserve internal IDs and update plan
        updated.id = subscriptionkore.id
        updated.customer_id = subscriptionkore.customer_id
        updated.plan_id = new_plan_id

        updated = await self._subscriptionkore_repo.save(updated)

        # Emit event
        await self._event_bus.publish(
            SubscriptionPlanChanged(
                subscriptionkore=updated,
                customer_id=updated.customer_id,
                previous_plan_id=old_plan_id,
                new_plan_id=new_plan_id,
                is_upgrade=is_upgrade,
            )
        )

        log.info(
            "Subscription plan changed",
            old_plan_id=old_plan_id,
            is_upgrade=is_upgrade,
        )

        return updated

    async def preview_plan_change(
        self,
        subscriptionkore_id: str,
        new_plan_id: str,
        proration_behavior: ProrationBehavior = ProrationBehavior.CREATE_PRORATIONS,
    ) -> ChangePreview:
        """Preview costs for a plan change."""
        subscriptionkore = await self.get(subscriptionkore_id)

        new_plan = await self._plan_repo.get(new_plan_id)
        if new_plan is None:
            raise EntityNotFoundError("Plan", new_plan_id)

        new_plan_ref = new_plan.get_provider_ref(self._provider.provider_type.value)
        if new_plan_ref is None:
            raise EntityNotFoundError(
                "PlanProviderRef",
                f"{new_plan_id}:{self._provider.provider_type.value}",
            )

        request = ChangePlanRequest(
            subscriptionkore_id=subscriptionkore_id,
            new_plan_id=new_plan_id,
            proration_behavior=proration_behavior,
        )

        return await self._provider.preview_plan_change(
            request=request,
            subscriptionkore_provider_ref=subscriptionkore.provider_ref,
            new_plan_provider_ref=new_plan_ref,
        )

    async def apply_discount(
        self,
        subscriptionkore_id: str,
        coupon_code: str,
    ) -> Subscription:
        """Apply a discount to a subscriptionkore."""
        log = logger.bind(subscriptionkore_id=subscriptionkore_id, coupon_code=coupon_code)
        log.info("Applying discount")

        subscriptionkore = await self.get(subscriptionkore_id)

        updated = await self._provider.apply_discount(
            subscriptionkore_provider_ref=subscriptionkore.provider_ref,
            discount=DiscountRequest(coupon_code=coupon_code),
        )

        # Preserve internal IDs
        updated.id = subscriptionkore.id
        updated.customer_id = subscriptionkore.customer_id
        updated.plan_id = subscriptionkore.plan_id

        updated = await self._subscriptionkore_repo.save(updated)

        log.info("Discount applied")
        return updated

    async def remove_discount(self, subscriptionkore_id: str) -> Subscription:
        """Remove discount from a subscriptionkore."""
        log = logger.bind(subscriptionkore_id=subscriptionkore_id)
        log.info("Removing discount")

        subscriptionkore = await self.get(subscriptionkore_id)

        updated = await self._provider.remove_discount(
            subscriptionkore_provider_ref=subscriptionkore.provider_ref,
        )

        # Preserve internal IDs
        updated.id = subscriptionkore.id
        updated.customer_id = subscriptionkore.customer_id
        updated.plan_id = subscriptionkore.plan_id

        updated = await self._subscriptionkore_repo.save(updated)

        log.info("Discount removed")
        return updated

    async def reactivate(self, subscriptionkore_id: str) -> Subscription:
        """
        Reactivate a subscriptionkore that was scheduled to cancel.

        Removes the cancel_at_period_end flag.
        """
        log = logger.bind(subscriptionkore_id=subscriptionkore_id)
        log.info("Reactivating subscriptionkore")

        subscriptionkore = await self.get(subscriptionkore_id)

        if not subscriptionkore.cancel_at_period_end:
            log.info("Subscription not scheduled to cancel, no action needed")
            return subscriptionkore

        # Update in provider
        request = UpdateSubscriptionRequest(
            subscriptionkore_id=subscriptionkore_id,
            cancel_at_period_end=False,
        )

        updated = await self._provider.update_subscriptionkore(
            request=request,
            subscriptionkore_provider_ref=subscriptionkore.provider_ref,
        )

        # Update local state
        updated.id = subscriptionkore.id
        updated.customer_id = subscriptionkore.customer_id
        updated.plan_id = subscriptionkore.plan_id
        updated.cancel_at_period_end = False
        updated.canceled_at = None

        updated = await self._subscriptionkore_repo.save(updated)

        await self._event_bus.publish(
            SubscriptionUpdated(
                subscriptionkore=updated,
                customer_id=updated.customer_id,
                changed_fields=["cancel_at_period_end"],
            )
        )

        log.info("Subscription reactivated")
        return updated
