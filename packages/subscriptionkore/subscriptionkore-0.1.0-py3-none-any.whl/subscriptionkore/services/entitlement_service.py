"""Entitlement resolution service."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import structlog

from subscriptionkore.core.exceptions import EntitlementNotFoundError, UsageLimitExceededError
from subscriptionkore.core.models import (
    CustomerEntitlement,
    EntitlementOverride,
    EntitlementSource,
    EntitlementValueType,
    SubscriptionStatus,
)

if TYPE_CHECKING:
    from subscriptionkore.ports.cache import CachePort
    from subscriptionkore.ports.repository import (
        EntitlementOverrideRepository,
        EntitlementRepository,
        PlanRepository,
        SubscriptionRepository,
    )

logger = structlog.get_logger()


class EntitlementService:
    """
    Resolves and manages customer entitlements.

    Entitlements are derived from:
    1. Customer-level overrides (highest priority)
    2. Active subscriptionkore plan entitlements
    3. Trial entitlements
    4. Default entitlements (lowest priority)
    """

    def __init__(
        self,
        entitlement_repo: EntitlementRepository,
        override_repo: EntitlementOverrideRepository,
        subscriptionkore_repo: SubscriptionRepository,
        plan_repo: PlanRepository,
        cache: CachePort | None = None,
        cache_ttl: int = 300,
    ) -> None:
        self._entitlement_repo = entitlement_repo
        self._override_repo = override_repo
        self._subscriptionkore_repo = subscriptionkore_repo
        self._plan_repo = plan_repo
        self._cache = cache
        self._cache_ttl = cache_ttl

    def _cache_key(self, customer_id: str) -> str:
        return f"entitlements:{customer_id}"

    async def check(
        self,
        customer_id: str,
        entitlement_key: str,
    ) -> CustomerEntitlement:
        """
        Check a specific entitlement for a customer.

        Args:
            customer_id: Customer ID
            entitlement_key: Entitlement key to check

        Returns:
            Resolved CustomerEntitlement

        Raises:
            EntitlementNotFoundError: If entitlement key doesn't exist
        """
        all_entitlements = await self.check_all(customer_id)

        for ent in all_entitlements:
            if ent.entitlement_key == entitlement_key:
                return ent

        # Check if entitlement definition exists
        entitlement_def = await self._entitlement_repo.get_by_key(entitlement_key)
        if entitlement_def is None:
            raise EntitlementNotFoundError(entitlement_key)

        # Return default value
        return CustomerEntitlement(
            customer_id=customer_id,
            entitlement_key=entitlement_key,
            current_value=entitlement_def.default_value or False,
            value_type=entitlement_def.value_type,
            source=EntitlementSource.DEFAULT,
        )

    async def check_many(
        self,
        customer_id: str,
        entitlement_keys: list[str],
    ) -> dict[str, CustomerEntitlement]:
        """Check multiple entitlements at once."""
        result: dict[str, CustomerEntitlement] = {}

        for key in entitlement_keys:
            result[key] = await self.check(customer_id, key)

        return result

    async def check_all(self, customer_id: str) -> list[CustomerEntitlement]:
        """
        Get all resolved entitlements for a customer.

        Results are cached for performance.
        """
        log = logger.bind(customer_id=customer_id)

        # Check cache
        if self._cache:
            cached = await self._cache.get(self._cache_key(customer_id))
            if cached is not None:
                log.debug("Entitlements cache hit")
                return [CustomerEntitlement.model_validate(e) for e in cached]

        log.debug("Resolving entitlements")

        # Collect entitlements from all sources
        entitlements: dict[str, CustomerEntitlement] = {}

        # 1. Load defaults from entitlement definitions
        all_definitions = await self._entitlement_repo.list_all()
        for definition in all_definitions:
            if definition.default_value is not None:
                entitlements[definition.key] = CustomerEntitlement(
                    customer_id=customer_id,
                    entitlement_key=definition.key,
                    current_value=definition.default_value,
                    value_type=definition.value_type,
                    source=EntitlementSource.DEFAULT,
                )

        # 2. Load from active subscriptionkores (overrides defaults)
        subscriptionkores = await self._subscriptionkore_repo.list_active_by_customer(customer_id)

        for subscriptionkore in subscriptionkores:
            plan = await self._plan_repo.get(subscriptionkore.plan_id)
            if plan is None:
                continue

            source = (
                EntitlementSource.TRIAL
                if subscriptionkore.status == SubscriptionStatus.TRIALING
                else EntitlementSource.PLAN
            )

            expires_at = subscriptionkore.trial_end if subscriptionkore.is_trialing() else None

            for plan_ent in plan.entitlements:
                existing = entitlements.get(plan_ent.entitlement_key)

                # Resolve value based on type
                new_value = plan_ent.value
                if existing and plan_ent.value is not None:
                    new_value = self._resolve_value(
                        existing.current_value,
                        plan_ent.value,
                        plan_ent.value_type,
                    )

                if new_value is not None:
                    entitlements[plan_ent.entitlement_key] = CustomerEntitlement(
                        customer_id=customer_id,
                        entitlement_key=plan_ent.entitlement_key,
                        current_value=new_value,
                        value_type=plan_ent.value_type,
                        source=source,
                        expires_at=expires_at,
                        subscriptionkore_id=subscriptionkore.id,
                        plan_id=plan.id,
                    )

        # 3. Load overrides (highest priority)
        overrides = await self._override_repo.list_by_customer(
            customer_id=customer_id,
            include_expired=False,
        )

        for override in overrides:
            if override.is_expired():
                continue

            entitlements[override.entitlement_key] = CustomerEntitlement(
                customer_id=customer_id,
                entitlement_key=override.entitlement_key,
                current_value=override.value,
                value_type=override.value_type,
                source=EntitlementSource.OVERRIDE,
                expires_at=override.expires_at,
            )

        result = list(entitlements.values())

        # Cache result
        if self._cache:
            # Find shortest expiration for TTL
            min_ttl = self._cache_ttl
            for ent in result:
                if ent.expires_at:
                    remaining = (ent.expires_at - datetime.utcnow()).total_seconds()
                    if remaining > 0:
                        min_ttl = min(min_ttl, int(remaining))

            await self._cache.set(
                self._cache_key(customer_id),
                [e.model_dump() for e in result],
                ttl_seconds=min_ttl,
            )

        return result

    def _resolve_value(
        self,
        existing: bool | int | str,
        new: bool | int | str | None,
        value_type: EntitlementValueType,
    ) -> bool | int | str | None:
        """Resolve value when multiple sources provide the same entitlement."""
        if new is None:
            return existing

        if value_type == EntitlementValueType.BOOLEAN:
            # Any true source wins
            return bool(existing) or bool(new)

        if value_type == EntitlementValueType.NUMERIC:
            # Maximum value wins
            return max(int(existing), int(new))

        if value_type == EntitlementValueType.UNLIMITED:
            # Unlimited always wins
            return new

        # String:  new value wins (higher priority source)
        return new

    async def has_access(
        self,
        customer_id: str,
        entitlement_key: str,
    ) -> bool:
        """Check if customer has access to a feature."""
        try:
            ent = await self.check(customer_id, entitlement_key)
            return ent.as_bool()
        except EntitlementNotFoundError:
            return False

    async def get_limit(
        self,
        customer_id: str,
        entitlement_key: str,
    ) -> int | None:
        """
        Get numeric limit for an entitlement.

        Returns None for unlimited entitlements.
        """
        ent = await self.check(customer_id, entitlement_key)
        return ent.as_int()

    async def check_within_limit(
        self,
        customer_id: str,
        entitlement_key: str,
        current_usage: int,
        requested: int = 1,
    ) -> tuple[bool, int | None]:
        """
        Check if usage is within limit.

        Args:
            customer_id: Customer ID
            entitlement_key: Entitlement key
            current_usage: Current usage count
            requested: Additional usage being requested

        Returns:
            Tuple of (within_limit, remaining)
            remaining is None for unlimited
        """
        limit = await self.get_limit(customer_id, entitlement_key)

        if limit is None:
            # Unlimited
            return True, None

        new_usage = current_usage + requested
        within_limit = new_usage <= limit
        remaining = max(0, limit - current_usage)

        return within_limit, remaining

    async def enforce_limit(
        self,
        customer_id: str,
        entitlement_key: str,
        current_usage: int,
        requested: int = 1,
    ) -> int | None:
        """
        Enforce usage limit, raising exception if exceeded.

        Args:
            customer_id: Customer ID
            entitlement_key:  Entitlement key
            current_usage:  Current usage count
            requested: Additional usage being requested

        Returns:
            Remaining quota (None for unlimited)

        Raises:
            UsageLimitExceededError:  If limit would be exceeded
        """
        limit = await self.get_limit(customer_id, entitlement_key)

        if limit is None:
            return None

        new_usage = current_usage + requested
        if new_usage > limit:
            raise UsageLimitExceededError(
                entitlement_key=entitlement_key,
                limit=limit,
                current_usage=current_usage,
                requested=requested,
            )

        return limit - new_usage

    # Override Management

    async def grant_override(
        self,
        customer_id: str,
        entitlement_key: str,
        value: bool | int | str,
        expires_at: datetime | None = None,
        reason: str | None = None,
        created_by: str | None = None,
    ) -> EntitlementOverride:
        """
        Grant an entitlement override to a customer.

        Args:
            customer_id: Customer ID
            entitlement_key: Entitlement key
            value:  Override value
            expires_at: When override expires (None for permanent)
            reason: Reason for override
            created_by: Who created the override

        Returns:
            Created override
        """
        log = logger.bind(customer_id=customer_id, entitlement_key=entitlement_key)
        log.info("Granting entitlement override")

        # Get entitlement definition
        entitlement_def = await self._entitlement_repo.get_by_key(entitlement_key)
        if entitlement_def is None:
            raise EntitlementNotFoundError(entitlement_key)

        # Delete existing override if any
        await self._override_repo.delete_by_customer_and_key(customer_id, entitlement_key)

        # Create new override
        override = EntitlementOverride(
            customer_id=customer_id,
            entitlement_key=entitlement_key,
            value=value,
            value_type=entitlement_def.value_type,
            reason=reason,
            expires_at=expires_at,
            created_by=created_by,
        )

        override = await self._override_repo.save(override)

        # Invalidate cache
        await self.invalidate(customer_id)

        log.info("Entitlement override granted", override_id=override.id)
        return override

    async def revoke_override(
        self,
        customer_id: str,
        entitlement_key: str,
    ) -> bool:
        """
        Revoke an entitlement override.

        Returns:
            True if override was deleted
        """
        log = logger.bind(customer_id=customer_id, entitlement_key=entitlement_key)
        log.info("Revoking entitlement override")

        deleted = await self._override_repo.delete_by_customer_and_key(customer_id, entitlement_key)

        if deleted:
            await self.invalidate(customer_id)

        log.info("Entitlement override revoked", deleted=deleted)
        return deleted

    async def list_overrides(
        self,
        customer_id: str,
        include_expired: bool = False,
    ) -> list[EntitlementOverride]:
        """List all overrides for a customer."""
        return await self._override_repo.list_by_customer(
            customer_id=customer_id,
            include_expired=include_expired,
        )

    # Cache Management

    async def invalidate(self, customer_id: str) -> None:
        """Invalidate entitlement cache for a customer."""
        if self._cache:
            await self._cache.delete(self._cache_key(customer_id))
            logger.debug("Entitlement cache invalidated", customer_id=customer_id)

    async def invalidate_all(self) -> None:
        """Invalidate all entitlement caches."""
        if self._cache:
            count = await self._cache.delete_pattern("entitlements:*")
            logger.info("All entitlement caches invalidated", count=count)
