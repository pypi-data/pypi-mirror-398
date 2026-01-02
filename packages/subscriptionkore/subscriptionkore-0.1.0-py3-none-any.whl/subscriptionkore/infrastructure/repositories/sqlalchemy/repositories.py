"""SQLAlchemy repository implementations."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from subscriptionkore.core.models import (
    Customer,
    Entitlement,
    EntitlementOverride,
    EntitlementValueType,
    Invoice,
    InvoiceStatus,
    PaymentEvent,
    PaymentEventType,
    PaymentStatus,
    Plan,
    PlanEntitlement,
    Product,
    ProviderReference,
    ProviderType,
    Subscription,
    SubscriptionStatus,
)
from subscriptionkore.core.models.customer import Address, TaxInfo
from subscriptionkore.core.models.subscription import (
    AppliedDiscount,
    PauseBehavior,
    PauseConfig,
)
from subscriptionkore.core.models.value_objects import (
    BillingPeriod,
    Currency,
    DateRange,
    Interval,
    Money,
)
from subscriptionkore.infrastructure.repositories.sqlalchemy.models import (
    CustomerModel,
    EntitlementModel,
    EntitlementOverrideModel,
    InvoiceModel,
    PaymentEventModel,
    PlanModel,
    ProcessedEventModel,
    ProductModel,
    SubscriptionModel,
)
from subscriptionkore.ports.repository import (
    CustomerRepository,
    EntitlementOverrideRepository,
    EntitlementRepository,
    InvoiceRepository,
    PaymentEventRepository,
    PlanRepository,
    ProcessedEventRepository,
    ProductRepository,
    SubscriptionRepository,
)


class SQLAlchemyCustomerRepository(CustomerRepository):
    """SQLAlchemy implementation of CustomerRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: str) -> Customer | None:
        result = await self._session.execute(select(CustomerModel).where(CustomerModel.id == id))
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def save(self, entity: Customer) -> Customer:
        model = self._to_model(entity)
        merged = await self._session.merge(model)
        await self._session.commit()
        return self._to_domain(merged)

    async def delete(self, id: str) -> bool:
        result = await self._session.execute(delete(CustomerModel).where(CustomerModel.id == id))
        await self._session.commit()
        return result.rowcount > 0

    async def get_by_external_id(self, external_id: str) -> Customer | None:
        result = await self._session.execute(
            select(CustomerModel).where(CustomerModel.external_id == external_id)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_email(self, email: str) -> Customer | None:
        result = await self._session.execute(
            select(CustomerModel).where(CustomerModel.email == email)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_provider_ref(
        self,
        provider: str,
        external_id: str,
    ) -> Customer | None:
        result = await self._session.execute(select(CustomerModel))
        models = result.scalars().all()

        for model in models:
            for ref in model.provider_refs:
                if ref.get("provider") == provider and ref.get("external_id") == external_id:
                    return self._to_domain(model)
        return None

    async def list(self, limit: int = 100, offset: int = 0) -> list[Customer]:
        result = await self._session.execute(select(CustomerModel).offset(offset).limit(limit))
        return [self._to_domain(m) for m in result.scalars().all()]

    def _to_model(self, entity: Customer) -> CustomerModel:
        return CustomerModel(
            id=entity.id,
            external_id=entity.external_id,
            email=entity.email,
            name=entity.name,
            provider_refs=[r.model_dump() for r in entity.provider_refs],
            tax_info=entity.tax_info.model_dump() if entity.tax_info else None,
            billing_address=entity.billing_address.model_dump() if entity.billing_address else None,
            metadata_=entity.metadata,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def _to_domain(self, model: CustomerModel) -> Customer:
        return Customer(
            id=model.id,
            external_id=model.external_id,
            email=model.email,
            name=model.name,
            provider_refs=[ProviderReference(**r) for r in model.provider_refs],
            tax_info=TaxInfo(**model.tax_info) if model.tax_info else None,
            billing_address=Address(**model.billing_address) if model.billing_address else None,
            metadata=model.metadata_,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class SQLAlchemyProductRepository(ProductRepository):
    """SQLAlchemy implementation of ProductRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: str) -> Product | None:
        result = await self._session.execute(select(ProductModel).where(ProductModel.id == id))
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def save(self, entity: Product) -> Product:
        model = self._to_model(entity)
        merged = await self._session.merge(model)
        await self._session.commit()
        return self._to_domain(merged)

    async def delete(self, id: str) -> bool:
        result = await self._session.execute(delete(ProductModel).where(ProductModel.id == id))
        await self._session.commit()
        return result.rowcount > 0

    async def get_by_provider_ref(
        self,
        provider: str,
        external_id: str,
    ) -> Product | None:
        result = await self._session.execute(select(ProductModel))
        models = result.scalars().all()

        for model in models:
            for ref in model.provider_refs:
                if ref.get("provider") == provider and ref.get("external_id") == external_id:
                    return self._to_domain(model)
        return None

    async def list_active(self) -> list[Product]:
        result = await self._session.execute(
            select(ProductModel).where(ProductModel.active == True)
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    def _to_model(self, entity: Product) -> ProductModel:
        return ProductModel(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            provider_refs=[r.model_dump() for r in entity.provider_refs],
            active=entity.active,
            metadata_=entity.metadata,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def _to_domain(self, model: ProductModel) -> Product:
        return Product(
            id=model.id,
            name=model.name,
            description=model.description,
            provider_refs=[ProviderReference(**r) for r in model.provider_refs],
            active=model.active,
            metadata=model.metadata_,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class SQLAlchemyPlanRepository(PlanRepository):
    """SQLAlchemy implementation of PlanRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: str) -> Plan | None:
        result = await self._session.execute(select(PlanModel).where(PlanModel.id == id))
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def save(self, entity: Plan) -> Plan:
        model = self._to_model(entity)
        merged = await self._session.merge(model)
        await self._session.commit()
        return self._to_domain(merged)

    async def delete(self, id: str) -> bool:
        result = await self._session.execute(delete(PlanModel).where(PlanModel.id == id))
        await self._session.commit()
        return result.rowcount > 0

    async def get_by_provider_ref(
        self,
        provider: str,
        external_id: str,
    ) -> Plan | None:
        result = await self._session.execute(select(PlanModel))
        models = result.scalars().all()

        for model in models:
            for ref in model.provider_refs:
                if ref.get("provider") == provider and ref.get("external_id") == external_id:
                    return self._to_domain(model)
        return None

    async def list_by_product(self, product_id: str) -> list[Plan]:
        result = await self._session.execute(
            select(PlanModel).where(PlanModel.product_id == product_id)
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def list_active(self) -> list[Plan]:
        result = await self._session.execute(select(PlanModel).where(PlanModel.active == True))
        return [self._to_domain(m) for m in result.scalars().all()]

    def _to_model(self, entity: Plan) -> PlanModel:
        return PlanModel(
            id=entity.id,
            product_id=entity.product_id,
            name=entity.name,
            description=entity.description,
            provider_refs=[r.model_dump() for r in entity.provider_refs],
            price_amount=entity.price.amount,
            price_currency=entity.price.currency.value,
            billing_interval=entity.billing_period.interval.value,
            billing_interval_count=entity.billing_period.interval_count,
            trial_period_days=entity.trial_period_days,
            entitlements=[e.model_dump() for e in entity.entitlements],
            active=entity.active,
            tier=entity.tier,
            metadata_=entity.metadata,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def _to_domain(self, model: PlanModel) -> Plan:
        return Plan(
            id=model.id,
            product_id=model.product_id,
            name=model.name,
            description=model.description,
            provider_refs=[ProviderReference(**r) for r in model.provider_refs],
            price=Money(amount=model.price_amount, currency=Currency(model.price_currency)),
            billing_period=BillingPeriod(
                interval=Interval(model.billing_interval),
                interval_count=model.billing_interval_count,
            ),
            trial_period_days=model.trial_period_days,
            entitlements=[PlanEntitlement(**e) for e in model.entitlements],
            active=model.active,
            tier=model.tier,
            metadata=model.metadata_,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class SQLAlchemySubscriptionRepository(SubscriptionRepository):
    """SQLAlchemy implementation of SubscriptionRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: str) -> Subscription | None:
        result = await self._session.execute(
            select(SubscriptionModel).where(SubscriptionModel.id == id)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def save(self, entity: Subscription) -> Subscription:
        model = self._to_model(entity)
        merged = await self._session.merge(model)
        await self._session.commit()
        return self._to_domain(merged)

    async def delete(self, id: str) -> bool:
        result = await self._session.execute(
            delete(SubscriptionModel).where(SubscriptionModel.id == id)
        )
        await self._session.commit()
        return result.rowcount > 0

    async def get_by_provider_ref(
        self,
        provider: str,
        external_id: str,
    ) -> Subscription | None:
        result = await self._session.execute(
            select(SubscriptionModel).where(
                SubscriptionModel.provider == provider,
                SubscriptionModel.provider_external_id == external_id,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_by_customer(
        self,
        customer_id: str,
        include_canceled: bool = False,
    ) -> list[Subscription]:
        query = select(SubscriptionModel).where(SubscriptionModel.customer_id == customer_id)

        if not include_canceled:
            query = query.where(SubscriptionModel.status != SubscriptionStatus.CANCELED.value)

        result = await self._session.execute(query)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def list_active_by_customer(self, customer_id: str) -> list[Subscription]:
        active_statuses = [
            SubscriptionStatus.ACTIVE.value,
            SubscriptionStatus.TRIALING.value,
        ]
        result = await self._session.execute(
            select(SubscriptionModel).where(
                SubscriptionModel.customer_id == customer_id,
                SubscriptionModel.status.in_(active_statuses),
            )
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def list_by_status(
        self,
        status: SubscriptionStatus,
        limit: int = 100,
    ) -> list[Subscription]:
        result = await self._session.execute(
            select(SubscriptionModel).where(SubscriptionModel.status == status.value).limit(limit)
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def list_expiring_trials(self, before: datetime) -> list[Subscription]:
        result = await self._session.execute(
            select(SubscriptionModel).where(
                SubscriptionModel.status == SubscriptionStatus.TRIALING.value,
                SubscriptionModel.trial_end <= before,
            )
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    def _to_model(self, entity: Subscription) -> SubscriptionModel:
        return SubscriptionModel(
            id=entity.id,
            customer_id=entity.customer_id,
            plan_id=entity.plan_id,
            provider=entity.provider_ref.provider.value,
            provider_external_id=entity.provider_ref.external_id,
            provider_metadata=entity.provider_ref.metadata,
            status=entity.status.value,
            current_period_start=entity.current_period.start,
            current_period_end=entity.current_period.end,
            trial_end=entity.trial_end,
            cancel_at_period_end=entity.cancel_at_period_end,
            canceled_at=entity.canceled_at,
            ended_at=entity.ended_at,
            pause_resumes_at=entity.pause_collection.resumes_at
            if entity.pause_collection
            else None,
            pause_behavior=entity.pause_collection.behavior.value
            if entity.pause_collection
            else None,
            discount_data=entity.discount.model_dump() if entity.discount else None,
            quantity=entity.quantity,
            metadata_=entity.metadata,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def _to_domain(self, model: SubscriptionModel) -> Subscription:
        pause_collection = None
        if model.pause_behavior:
            pause_collection = PauseConfig(
                resumes_at=model.pause_resumes_at,
                behavior=PauseBehavior(model.pause_behavior),
            )

        return Subscription(
            id=model.id,
            customer_id=model.customer_id,
            plan_id=model.plan_id,
            provider_ref=ProviderReference(
                provider=ProviderType(model.provider),
                external_id=model.provider_external_id,
                metadata=model.provider_metadata,
            ),
            status=SubscriptionStatus(model.status),
            current_period=DateRange(
                start=model.current_period_start,
                end=model.current_period_end,
            ),
            trial_end=model.trial_end,
            cancel_at_period_end=model.cancel_at_period_end,
            canceled_at=model.canceled_at,
            ended_at=model.ended_at,
            pause_collection=pause_collection,
            discount=AppliedDiscount(**model.discount_data) if model.discount_data else None,
            quantity=model.quantity,
            metadata=model.metadata_,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class SQLAlchemyEntitlementRepository(EntitlementRepository):
    """SQLAlchemy implementation of EntitlementRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: str) -> Entitlement | None:
        result = await self._session.execute(
            select(EntitlementModel).where(EntitlementModel.id == id)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def save(self, entity: Entitlement) -> Entitlement:
        model = self._to_model(entity)
        merged = await self._session.merge(model)
        await self._session.commit()
        return self._to_domain(merged)

    async def delete(self, id: str) -> bool:
        result = await self._session.execute(
            delete(EntitlementModel).where(EntitlementModel.id == id)
        )
        await self._session.commit()
        return result.rowcount > 0

    async def get_by_key(self, key: str) -> Entitlement | None:
        result = await self._session.execute(
            select(EntitlementModel).where(EntitlementModel.key == key)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_all(self) -> list[Entitlement]:
        result = await self._session.execute(select(EntitlementModel))
        return [self._to_domain(m) for m in result.scalars().all()]

    def _to_model(self, entity: Entitlement) -> EntitlementModel:
        default_str = None
        if entity.default_value is not None:
            default_str = str(entity.default_value)

        return EntitlementModel(
            id=entity.id,
            key=entity.key,
            name=entity.name,
            description=entity.description,
            value_type=entity.value_type.value,
            default_value=default_str,
            metadata_=entity.metadata,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def _to_domain(self, model: EntitlementModel) -> Entitlement:
        value_type = EntitlementValueType(model.value_type)
        default_value: bool | int | str | None = None

        if model.default_value is not None:
            if value_type == EntitlementValueType.BOOLEAN:
                default_value = model.default_value.lower() == "true"
            elif value_type == EntitlementValueType.NUMERIC:
                default_value = int(model.default_value)
            else:
                default_value = model.default_value

        return Entitlement(
            id=model.id,
            key=model.key,
            name=model.name,
            description=model.description,
            value_type=value_type,
            default_value=default_value,
            metadata=model.metadata_,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class SQLAlchemyEntitlementOverrideRepository(EntitlementOverrideRepository):
    """SQLAlchemy implementation of EntitlementOverrideRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: str) -> EntitlementOverride | None:
        result = await self._session.execute(
            select(EntitlementOverrideModel).where(EntitlementOverrideModel.id == id)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def save(self, entity: EntitlementOverride) -> EntitlementOverride:
        model = self._to_model(entity)
        merged = await self._session.merge(model)
        await self._session.commit()
        return self._to_domain(merged)

    async def delete(self, id: str) -> bool:
        result = await self._session.execute(
            delete(EntitlementOverrideModel).where(EntitlementOverrideModel.id == id)
        )
        await self._session.commit()
        return result.rowcount > 0

    async def get_by_customer_and_key(
        self,
        customer_id: str,
        entitlement_key: str,
    ) -> EntitlementOverride | None:
        result = await self._session.execute(
            select(EntitlementOverrideModel).where(
                EntitlementOverrideModel.customer_id == customer_id,
                EntitlementOverrideModel.entitlement_key == entitlement_key,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_by_customer(
        self,
        customer_id: str,
        include_expired: bool = False,
    ) -> list[EntitlementOverride]:
        query = select(EntitlementOverrideModel).where(
            EntitlementOverrideModel.customer_id == customer_id
        )

        if not include_expired:
            query = query.where(
                (EntitlementOverrideModel.expires_at == None)  # noqa: E711
                | (EntitlementOverrideModel.expires_at > datetime.utcnow())
            )

        result = await self._session.execute(query)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def delete_by_customer_and_key(
        self,
        customer_id: str,
        entitlement_key: str,
    ) -> bool:
        result = await self._session.execute(
            delete(EntitlementOverrideModel).where(
                EntitlementOverrideModel.customer_id == customer_id,
                EntitlementOverrideModel.entitlement_key == entitlement_key,
            )
        )
        await self._session.commit()
        return result.rowcount > 0

    def _to_model(self, entity: EntitlementOverride) -> EntitlementOverrideModel:
        return EntitlementOverrideModel(
            id=entity.id,
            customer_id=entity.customer_id,
            entitlement_key=entity.entitlement_key,
            value=str(entity.value),
            value_type=entity.value_type.value,
            reason=entity.reason,
            expires_at=entity.expires_at,
            created_by=entity.created_by,
            created_at=entity.created_at,
        )

    def _to_domain(self, model: EntitlementOverrideModel) -> EntitlementOverride:
        value_type = EntitlementValueType(model.value_type)
        value: bool | int | str

        if value_type == EntitlementValueType.BOOLEAN:
            value = model.value.lower() == "true"
        elif value_type == EntitlementValueType.NUMERIC:
            value = int(model.value)
        else:
            value = model.value

        return EntitlementOverride(
            id=model.id,
            customer_id=model.customer_id,
            entitlement_key=model.entitlement_key,
            value=value,
            value_type=value_type,
            reason=model.reason,
            expires_at=model.expires_at,
            created_by=model.created_by,
            created_at=model.created_at,
        )


class SQLAlchemyInvoiceRepository(InvoiceRepository):
    """SQLAlchemy implementation of InvoiceRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: str) -> Invoice | None:
        result = await self._session.execute(select(InvoiceModel).where(InvoiceModel.id == id))
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def save(self, entity: Invoice) -> Invoice:
        model = self._to_model(entity)
        merged = await self._session.merge(model)
        await self._session.commit()
        return self._to_domain(merged)

    async def delete(self, id: str) -> bool:
        result = await self._session.execute(delete(InvoiceModel).where(InvoiceModel.id == id))
        await self._session.commit()
        return result.rowcount > 0

    async def get_by_provider_ref(
        self,
        provider: str,
        external_id: str,
    ) -> Invoice | None:
        result = await self._session.execute(
            select(InvoiceModel).where(
                InvoiceModel.provider == provider,
                InvoiceModel.provider_external_id == external_id,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_by_customer(
        self,
        customer_id: str,
        limit: int = 100,
    ) -> list[Invoice]:
        result = await self._session.execute(
            select(InvoiceModel)
            .where(InvoiceModel.customer_id == customer_id)
            .order_by(InvoiceModel.created_at.desc())
            .limit(limit)
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def list_by_subscriptionkore(
        self,
        subscriptionkore_id: str,
    ) -> list[Invoice]:
        result = await self._session.execute(
            select(InvoiceModel)
            .where(InvoiceModel.subscriptionkore_id == subscriptionkore_id)
            .order_by(InvoiceModel.created_at.desc())
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    def _to_model(self, entity: Invoice) -> InvoiceModel:
        return InvoiceModel(
            id=entity.id,
            customer_id=entity.customer_id,
            subscriptionkore_id=entity.subscriptionkore_id,
            provider=entity.provider_ref.provider.value,
            provider_external_id=entity.provider_ref.external_id,
            provider_metadata=entity.provider_ref.metadata,
            status=entity.status.value,
            subtotal_amount=entity.subtotal.amount,
            tax_amount=entity.tax.amount,
            discount_amount=entity.discount_amount.amount,
            total_amount=entity.total.amount,
            amount_paid=entity.amount_paid.amount,
            amount_due=entity.amount_due.amount,
            currency=entity.currency.value,
            line_items=[item.model_dump() for item in entity.line_items],
            period_start=entity.period.start if entity.period else None,
            period_end=entity.period.end if entity.period else None,
            due_date=entity.due_date,
            paid_at=entity.paid_at,
            invoice_pdf_url=entity.invoice_pdf_url,
            hosted_invoice_url=entity.hosted_invoice_url,
            metadata_=entity.metadata,
            created_at=entity.created_at,
        )

    def _to_domain(self, model: InvoiceModel) -> Invoice:
        from subscriptionkore.core.models.invoice import InvoiceLineItem

        period = None
        if model.period_start:
            period = DateRange(start=model.period_start, end=model.period_end)

        currency = Currency(model.currency)

        return Invoice(
            id=model.id,
            customer_id=model.customer_id,
            subscriptionkore_id=model.subscriptionkore_id,
            provider_ref=ProviderReference(
                provider=ProviderType(model.provider),
                external_id=model.provider_external_id,
                metadata=model.provider_metadata,
            ),
            status=InvoiceStatus(model.status),
            subtotal=Money(amount=model.subtotal_amount, currency=currency),
            tax=Money(amount=model.tax_amount, currency=currency),
            discount_amount=Money(amount=model.discount_amount, currency=currency),
            total=Money(amount=model.total_amount, currency=currency),
            amount_paid=Money(amount=model.amount_paid, currency=currency),
            amount_due=Money(amount=model.amount_due, currency=currency),
            currency=currency,
            line_items=[InvoiceLineItem(**item) for item in model.line_items],
            period=period,
            due_date=model.due_date,
            paid_at=model.paid_at,
            invoice_pdf_url=model.invoice_pdf_url,
            hosted_invoice_url=model.hosted_invoice_url,
            metadata=model.metadata_,
            created_at=model.created_at,
        )


class SQLAlchemyPaymentEventRepository(PaymentEventRepository):
    """SQLAlchemy implementation of PaymentEventRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: str) -> PaymentEvent | None:
        result = await self._session.execute(
            select(PaymentEventModel).where(PaymentEventModel.id == id)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def save(self, entity: PaymentEvent) -> PaymentEvent:
        model = self._to_model(entity)
        merged = await self._session.merge(model)
        await self._session.commit()
        return self._to_domain(merged)

    async def delete(self, id: str) -> bool:
        result = await self._session.execute(
            delete(PaymentEventModel).where(PaymentEventModel.id == id)
        )
        await self._session.commit()
        return result.rowcount > 0

    async def get_by_provider_ref(
        self,
        provider: str,
        external_id: str,
    ) -> PaymentEvent | None:
        result = await self._session.execute(
            select(PaymentEventModel).where(
                PaymentEventModel.provider == provider,
                PaymentEventModel.provider_external_id == external_id,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_by_customer(
        self,
        customer_id: str,
        limit: int = 100,
    ) -> list[PaymentEvent]:
        result = await self._session.execute(
            select(PaymentEventModel)
            .where(PaymentEventModel.customer_id == customer_id)
            .order_by(PaymentEventModel.occurred_at.desc())
            .limit(limit)
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def list_by_subscriptionkore(
        self,
        subscriptionkore_id: str,
    ) -> list[PaymentEvent]:
        result = await self._session.execute(
            select(PaymentEventModel)
            .where(PaymentEventModel.subscriptionkore_id == subscriptionkore_id)
            .order_by(PaymentEventModel.occurred_at.desc())
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    def _to_model(self, entity: PaymentEvent) -> PaymentEventModel:
        return PaymentEventModel(
            id=entity.id,
            provider=entity.provider_ref.provider.value,
            provider_external_id=entity.provider_ref.external_id,
            provider_metadata=entity.provider_ref.metadata,
            customer_id=entity.customer_id,
            subscriptionkore_id=entity.subscriptionkore_id,
            invoice_id=entity.invoice_id,
            event_type=entity.event_type.value,
            amount=entity.amount.amount,
            currency=entity.amount.currency.value,
            status=entity.status.value,
            failure_reason=entity.failure_reason,
            failure_code=entity.failure_code,
            payment_method_type=entity.payment_method_type,
            payment_method_last4=entity.payment_method_last4,
            occurred_at=entity.occurred_at,
            metadata_=entity.metadata,
        )

    def _to_domain(self, model: PaymentEventModel) -> PaymentEvent:
        return PaymentEvent(
            id=model.id,
            provider_ref=ProviderReference(
                provider=ProviderType(model.provider),
                external_id=model.provider_external_id,
                metadata=model.provider_metadata,
            ),
            customer_id=model.customer_id,
            subscriptionkore_id=model.subscriptionkore_id,
            invoice_id=model.invoice_id,
            event_type=PaymentEventType(model.event_type),
            amount=Money(amount=model.amount, currency=Currency(model.currency)),
            status=PaymentStatus(model.status),
            failure_reason=model.failure_reason,
            failure_code=model.failure_code,
            payment_method_type=model.payment_method_type,
            payment_method_last4=model.payment_method_last4,
            occurred_at=model.occurred_at,
            metadata=model.metadata_,
        )


class SQLAlchemyProcessedEventRepository(ProcessedEventRepository):
    """SQLAlchemy implementation of ProcessedEventRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def exists(self, provider: str, event_id: str) -> bool:
        result = await self._session.execute(
            select(ProcessedEventModel).where(
                ProcessedEventModel.provider == provider,
                ProcessedEventModel.event_id == event_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def mark_processed(
        self,
        provider: str,
        event_id: str,
        processed_at: datetime | None = None,
    ) -> None:
        model = ProcessedEventModel(
            provider=provider,
            event_id=event_id,
            processed_at=processed_at or datetime.utcnow(),
        )
        self._session.add(model)
        await self._session.commit()

    async def cleanup_old_events(self, older_than_days: int = 7) -> int:
        cutoff = datetime.utcnow() - timedelta(days=older_than_days)
        result = await self._session.execute(
            delete(ProcessedEventModel).where(ProcessedEventModel.processed_at < cutoff)
        )
        await self._session.commit()
        return result.rowcount
