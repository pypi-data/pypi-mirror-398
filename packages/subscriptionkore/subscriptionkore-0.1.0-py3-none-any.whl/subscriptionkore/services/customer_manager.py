"""Customer management service."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from subscriptionkore.core.events import CustomerCreated, CustomerUpdated
from subscriptionkore.core.exceptions import DuplicateEntityError, EntityNotFoundError
from subscriptionkore.core.models import Customer, ProviderType
from subscriptionkore.core.models.customer import Address, TaxInfo

if TYPE_CHECKING:
    from subscriptionkore.ports.event_bus import EventBusPort
    from subscriptionkore.ports.provider import PaymentProviderPort
    from subscriptionkore.ports.repository import CustomerRepository

logger = structlog.get_logger()


class CustomerManager:
    """
    Manages customer lifecycle operations.

    Provides a unified interface for customer operations across providers.
    """

    def __init__(
        self,
        customer_repo: CustomerRepository,
        provider: PaymentProviderPort,
        event_bus: EventBusPort,
    ) -> None:
        self._customer_repo = customer_repo
        self._provider = provider
        self._event_bus = event_bus

    async def create(
        self,
        external_id: str,
        email: str,
        name: str | None = None,
        tax_info: TaxInfo | None = None,
        billing_address: Address | None = None,
        metadata: dict | None = None,
        sync_to_provider: bool = True,
    ) -> Customer:
        """
        Create a new customer.

        Args:
            external_id: Your application's user ID
            email:  Customer email
            name: Customer name
            tax_info: Tax information
            billing_address:  Billing address
            metadata: Additional metadata
            sync_to_provider: Whether to create in payment provider

        Returns:
            Created customer

        Raises:
            DuplicateEntityError: If customer with external_id exists
        """
        log = logger.bind(external_id=external_id, email=email)
        log.info("Creating customer")

        # Check for existing customer
        existing = await self._customer_repo.get_by_external_id(external_id)
        if existing is not None:
            raise DuplicateEntityError("Customer", external_id)

        # Create customer model
        customer = Customer(
            external_id=external_id,
            email=email,
            name=name,
            tax_info=tax_info,
            billing_address=billing_address,
            metadata=metadata or {},
        )

        # Sync to provider if requested
        if sync_to_provider:
            provider_ref = await self._provider.create_customer(customer)
            customer.add_provider_ref(provider_ref)

        # Save to repository
        customer = await self._customer_repo.save(customer)

        # Emit event
        await self._event_bus.publish(CustomerCreated(customer=customer))

        log.info("Customer created", customer_id=customer.id)
        return customer

    async def get(self, customer_id: str) -> Customer:
        """Get customer by internal ID."""
        customer = await self._customer_repo.get(customer_id)
        if customer is None:
            raise EntityNotFoundError("Customer", customer_id)
        return customer

    async def get_by_external_id(self, external_id: str) -> Customer:
        """Get customer by external (application) ID."""
        customer = await self._customer_repo.get_by_external_id(external_id)
        if customer is None:
            raise EntityNotFoundError("Customer", external_id)
        return customer

    async def get_or_create(
        self,
        external_id: str,
        email: str,
        name: str | None = None,
        sync_to_provider: bool = True,
    ) -> tuple[Customer, bool]:
        """
        Get existing customer or create new one.

        Returns:
            Tuple of (customer, created) where created is True if new
        """
        existing = await self._customer_repo.get_by_external_id(external_id)
        if existing is not None:
            return existing, False

        customer = await self.create(
            external_id=external_id,
            email=email,
            name=name,
            sync_to_provider=sync_to_provider,
        )
        return customer, True

    async def update(
        self,
        customer_id: str,
        email: str | None = None,
        name: str | None = None,
        tax_info: TaxInfo | None = None,
        billing_address: Address | None = None,
        metadata: dict | None = None,
        sync_to_provider: bool = True,
    ) -> Customer:
        """Update customer information."""
        log = logger.bind(customer_id=customer_id)
        log.info("Updating customer")

        customer = await self.get(customer_id)

        # Track changed fields
        changed_fields: list[str] = []
        if email is not None and customer.email != email:
            changed_fields.append("email")
        if name is not None and customer.name != name:
            changed_fields.append("name")
        if tax_info is not None:
            changed_fields.append("tax_info")
        if billing_address is not None:
            changed_fields.append("billing_address")
        if metadata is not None:
            changed_fields.append("metadata")

        # Update local model
        customer.update(
            email=email,
            name=name,
            tax_info=tax_info,
            billing_address=billing_address,
            metadata=metadata,
        )

        # Sync to provider
        if sync_to_provider and customer.provider_refs:
            await self._provider.update_customer(customer)

        # Save to repository
        customer = await self._customer_repo.save(customer)

        # Emit event if changed
        if changed_fields:
            await self._event_bus.publish(
                CustomerUpdated(
                    customer=customer,
                    changed_fields=changed_fields,
                )
            )

        log.info("Customer updated", changed_fields=changed_fields)
        return customer

    async def delete(
        self,
        customer_id: str,
        delete_from_provider: bool = True,
    ) -> bool:
        """
        Delete a customer.

        Args:
            customer_id:  Customer ID
            delete_from_provider: Whether to delete from payment provider

        Returns:
            True if deleted
        """
        log = logger.bind(customer_id=customer_id)
        log.info("Deleting customer")

        customer = await self.get(customer_id)

        # Delete from provider
        if delete_from_provider:
            for ref in customer.provider_refs:
                await self._provider.delete_customer(ref)

        # Delete from repository
        deleted = await self._customer_repo.delete(customer_id)

        log.info("Customer deleted", deleted=deleted)
        return deleted

    async def sync_to_provider(
        self,
        customer_id: str,
        provider: ProviderType | None = None,
    ) -> Customer:
        """
        Sync customer to payment provider.

        Creates customer in provider if not exists, or updates if exists.
        """
        customer = await self.get(customer_id)
        target_provider = provider or self._provider.provider_type

        existing_ref = customer.get_provider_ref(target_provider.value)

        if existing_ref is None:
            # Create in provider
            provider_ref = await self._provider.create_customer(customer)
            customer.add_provider_ref(provider_ref)
        else:
            # Update in provider
            await self._provider.update_customer(customer)

        return await self._customer_repo.save(customer)

    async def list(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Customer]:
        """List customers with pagination."""
        return await self._customer_repo.list(limit=limit, offset=offset)
