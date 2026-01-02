"""Subscription state machine implementation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from subscriptionkore.core.events import (
    DomainEvent,
    SubscriptionActivated,
    SubscriptionCanceled,
    SubscriptionPastDue,
    SubscriptionPaused,
    SubscriptionResumed,
    SubscriptionTrialEnded,
    SubscriptionTrialStarted,
)
from subscriptionkore.core.exceptions import InvalidStateTransitionError
from subscriptionkore.core.models.subscription import Subscription, SubscriptionStatus

if TYPE_CHECKING:
    pass


@dataclass
class TransitionResult:
    """Result of a state transition."""

    success: bool
    new_status: SubscriptionStatus
    events: list[DomainEvent]
    error: InvalidStateTransitionError | None = None


class SubscriptionStateMachine:
    """
    State machine for subscriptionkore status transitions.

    Enforces valid transitions and emits appropriate domain events.
    """

    # Valid transitions:  from_status -> set of valid to_statuses
    VALID_TRANSITIONS: dict[SubscriptionStatus, set[SubscriptionStatus]] = {
        SubscriptionStatus.INCOMPLETE: {
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.TRIALING,
            SubscriptionStatus.INCOMPLETE_EXPIRED,
            SubscriptionStatus.CANCELED,
        },
        SubscriptionStatus.TRIALING: {
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.PAST_DUE,
            SubscriptionStatus.CANCELED,
        },
        SubscriptionStatus.ACTIVE: {
            SubscriptionStatus.PAST_DUE,
            SubscriptionStatus.PAUSED,
            SubscriptionStatus.CANCELED,
        },
        SubscriptionStatus.PAST_DUE: {
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.UNPAID,
            SubscriptionStatus.CANCELED,
        },
        SubscriptionStatus.UNPAID: {
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.CANCELED,
        },
        SubscriptionStatus.PAUSED: {
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.CANCELED,
        },
        # Terminal states - no outgoing transitions
        SubscriptionStatus.CANCELED: set(),
        SubscriptionStatus.INCOMPLETE_EXPIRED: set(),
        SubscriptionStatus.EXPIRED: set(),
    }

    def can_transition(
        self,
        from_status: SubscriptionStatus,
        to_status: SubscriptionStatus,
    ) -> bool:
        """Check if a transition is valid."""
        if from_status == to_status:
            return True  # No-op is always valid
        valid_targets = self.VALID_TRANSITIONS.get(from_status, set())
        return to_status in valid_targets

    def transition(
        self,
        subscriptionkore: Subscription,
        new_status: SubscriptionStatus,
        reason: str | None = None,
        immediate: bool = False,
    ) -> TransitionResult:
        """
        Attempt to transition a subscriptionkore to a new status.

        Returns a TransitionResult with emitted events on success,
        or an error on failure.
        """
        current_status = subscriptionkore.status

        # No-op transition
        if current_status == new_status:
            return TransitionResult(
                success=True,
                new_status=new_status,
                events=[],
            )

        # Validate transition
        if not self.can_transition(current_status, new_status):
            error = InvalidStateTransitionError(
                from_state=current_status,
                to_state=new_status,
                reason=reason,
            )
            return TransitionResult(
                success=False,
                new_status=current_status,
                events=[],
                error=error,
            )

        # Apply transition
        subscriptionkore.status = new_status
        subscriptionkore.updated_at = datetime.utcnow()

        # Emit appropriate events
        events = self._create_transition_events(
            subscriptionkore=subscriptionkore,
            from_status=current_status,
            to_status=new_status,
            reason=reason,
            immediate=immediate,
        )

        return TransitionResult(
            success=True,
            new_status=new_status,
            events=events,
        )

    def _create_transition_events(
        self,
        subscriptionkore: Subscription,
        from_status: SubscriptionStatus,
        to_status: SubscriptionStatus,
        reason: str | None,
        immediate: bool,
    ) -> list[DomainEvent]:
        """Create domain events for a transition."""
        events: list[DomainEvent] = []

        # Trial started
        if to_status == SubscriptionStatus.TRIALING:
            if subscriptionkore.trial_end:
                events.append(
                    SubscriptionTrialStarted(
                        subscriptionkore=subscriptionkore,
                        customer_id=subscriptionkore.customer_id,
                        trial_end=subscriptionkore.trial_end,
                    )
                )

        # Activated (from trial or initial)
        if to_status == SubscriptionStatus.ACTIVE:
            # If coming from trial, emit trial ended
            if from_status == SubscriptionStatus.TRIALING:
                events.append(
                    SubscriptionTrialEnded(
                        subscriptionkore=subscriptionkore,
                        customer_id=subscriptionkore.customer_id,
                        converted=True,
                    )
                )
            events.append(
                SubscriptionActivated(
                    subscriptionkore=subscriptionkore,
                    customer_id=subscriptionkore.customer_id,
                    plan_id=subscriptionkore.plan_id,
                )
            )

        # Past due
        if to_status == SubscriptionStatus.PAST_DUE:
            events.append(
                SubscriptionPastDue(
                    subscriptionkore=subscriptionkore,
                    customer_id=subscriptionkore.customer_id,
                )
            )

        # Paused
        if to_status == SubscriptionStatus.PAUSED:
            resumes_at = None
            if subscriptionkore.pause_collection:
                resumes_at = subscriptionkore.pause_collection.resumes_at
            events.append(
                SubscriptionPaused(
                    subscriptionkore=subscriptionkore,
                    customer_id=subscriptionkore.customer_id,
                    resumes_at=resumes_at,
                )
            )

        # Resumed (from paused to active)
        if from_status == SubscriptionStatus.PAUSED and to_status == SubscriptionStatus.ACTIVE:
            events.append(
                SubscriptionResumed(
                    subscriptionkore=subscriptionkore,
                    customer_id=subscriptionkore.customer_id,
                )
            )

        # Canceled
        if to_status == SubscriptionStatus.CANCELED:
            subscriptionkore.ended_at = datetime.utcnow()
            # If coming from trial without converting
            if from_status == SubscriptionStatus.TRIALING:
                events.append(
                    SubscriptionTrialEnded(
                        subscriptionkore=subscriptionkore,
                        customer_id=subscriptionkore.customer_id,
                        converted=False,
                    )
                )
            events.append(
                SubscriptionCanceled(
                    subscriptionkore=subscriptionkore,
                    customer_id=subscriptionkore.customer_id,
                    plan_id=subscriptionkore.plan_id,
                    immediate=immediate,
                    reason=reason,
                )
            )

        return events
