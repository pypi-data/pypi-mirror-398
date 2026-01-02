"""SQLAlchemy ORM models."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""

    pass


class CustomerModel(Base):
    """Customer ORM model."""

    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    external_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), index=True)
    name: Mapped[str | None] = mapped_column(String(255))
    provider_refs: Mapped[dict] = mapped_column(JSON, default=list)
    tax_info: Mapped[dict | None] = mapped_column(JSON)
    billing_address: Mapped[dict | None] = mapped_column(JSON)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    subscriptionkores: Mapped[list["SubscriptionModel"]] = relationship(back_populates="customer")

    __table_args__ = (Index("ix_customers_provider_ref", "provider_refs", postgresql_using="gin"),)


class ProductModel(Base):
    """Product ORM model."""

    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    provider_refs: Mapped[dict] = mapped_column(JSON, default=list)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    plans: Mapped[list["PlanModel"]] = relationship(back_populates="product")


class PlanModel(Base):
    """Plan ORM model."""

    __tablename__ = "plans"

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    product_id: Mapped[str] = mapped_column(String(26), ForeignKey("products. id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    provider_refs: Mapped[dict] = mapped_column(JSON, default=list)
    price_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    price_currency: Mapped[str] = mapped_column(String(3), default="USD")
    billing_interval: Mapped[str] = mapped_column(String(20))
    billing_interval_count: Mapped[int] = mapped_column(Integer, default=1)
    trial_period_days: Mapped[int | None] = mapped_column(Integer)
    entitlements: Mapped[dict] = mapped_column(JSON, default=list)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    tier: Mapped[int] = mapped_column(Integer, default=0)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    product: Mapped["ProductModel"] = relationship(back_populates="plans")


class SubscriptionModel(Base):
    """Subscription ORM model."""

    __tablename__ = "subscriptionkores"

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    customer_id: Mapped[str] = mapped_column(String(26), ForeignKey("customers.id"), index=True)
    plan_id: Mapped[str] = mapped_column(String(26), ForeignKey("plans.id"), index=True)
    provider: Mapped[str] = mapped_column(String(20))
    provider_external_id: Mapped[str] = mapped_column(String(255), index=True)
    provider_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(30), index=True)
    current_period_start: Mapped[datetime] = mapped_column(DateTime)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime)
    trial_end: Mapped[datetime | None] = mapped_column(DateTime)
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False)
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime)
    pause_resumes_at: Mapped[datetime | None] = mapped_column(DateTime)
    pause_behavior: Mapped[str | None] = mapped_column(String(30))
    discount_data: Mapped[dict | None] = mapped_column(JSON)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    customer: Mapped["CustomerModel"] = relationship(back_populates="subscriptionkores")

    __table_args__ = (
        Index("ix_subscriptionkores_provider", "provider", "provider_external_id"),
        Index("ix_subscriptionkores_status", "status"),
        Index("ix_subscriptionkores_trial_end", "trial_end"),
    )


class EntitlementModel(Base):
    """Entitlement definition ORM model."""

    __tablename__ = "entitlements"

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    value_type: Mapped[str] = mapped_column(String(20))
    default_value: Mapped[str | None] = mapped_column(String(255))
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class EntitlementOverrideModel(Base):
    """Entitlement override ORM model."""

    __tablename__ = "entitlement_overrides"

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    customer_id: Mapped[str] = mapped_column(String(26), index=True)
    entitlement_key: Mapped[str] = mapped_column(String(100), index=True)
    value: Mapped[str] = mapped_column(String(255))
    value_type: Mapped[str] = mapped_column(String(20))
    reason: Mapped[str | None] = mapped_column(Text)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_by: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_overrides_customer_key", "customer_id", "entitlement_key", unique=True),
    )


class InvoiceModel(Base):
    """Invoice ORM model."""

    __tablename__ = "invoices"

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    customer_id: Mapped[str] = mapped_column(String(26), index=True)
    subscriptionkore_id: Mapped[str | None] = mapped_column(String(26), index=True)
    provider: Mapped[str] = mapped_column(String(20))
    provider_external_id: Mapped[str] = mapped_column(String(255), index=True)
    provider_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(30))
    subtotal_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    amount_due: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    line_items: Mapped[dict] = mapped_column(JSON, default=list)
    period_start: Mapped[datetime | None] = mapped_column(DateTime)
    period_end: Mapped[datetime | None] = mapped_column(DateTime)
    due_date: Mapped[datetime | None] = mapped_column(DateTime)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime)
    invoice_pdf_url: Mapped[str | None] = mapped_column(Text)
    hosted_invoice_url: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("ix_invoices_provider", "provider", "provider_external_id"),)


class PaymentEventModel(Base):
    """Payment event ORM model."""

    __tablename__ = "payment_events"

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    provider: Mapped[str] = mapped_column(String(20))
    provider_external_id: Mapped[str] = mapped_column(String(255), index=True)
    provider_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    customer_id: Mapped[str] = mapped_column(String(26), index=True)
    subscriptionkore_id: Mapped[str | None] = mapped_column(String(26), index=True)
    invoice_id: Mapped[str | None] = mapped_column(String(26))
    event_type: Mapped[str] = mapped_column(String(50))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    status: Mapped[str] = mapped_column(String(30))
    failure_reason: Mapped[str | None] = mapped_column(Text)
    failure_code: Mapped[str | None] = mapped_column(String(100))
    payment_method_type: Mapped[str | None] = mapped_column(String(50))
    payment_method_last4: Mapped[str | None] = mapped_column(String(4))
    occurred_at: Mapped[datetime] = mapped_column(DateTime)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)

    __table_args__ = (Index("ix_payment_events_provider", "provider", "provider_external_id"),)


class ProcessedEventModel(Base):
    """Processed webhook event ORM model (for idempotency)."""

    __tablename__ = "processed_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider: Mapped[str] = mapped_column(String(20))
    event_id: Mapped[str] = mapped_column(String(255))
    processed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_processed_events_lookup", "provider", "event_id", unique=True),
        Index("ix_processed_events_cleanup", "processed_at"),
    )
