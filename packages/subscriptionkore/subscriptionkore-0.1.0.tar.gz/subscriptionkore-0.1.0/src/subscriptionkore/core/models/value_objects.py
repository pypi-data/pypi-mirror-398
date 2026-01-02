"""Value objects for the domain layer."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any, Self

from pydantic import BaseModel, Field, field_validator, model_validator


class ProviderType(StrEnum):
    """Supported payment providers."""

    STRIPE = "stripe"
    PADDLE = "paddle"
    LEMONSQUEEZY = "lemonsqueezy"
    CHARGEBEE = "chargebee"


class Currency(StrEnum):
    """ISO 4217 currency codes."""

    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    CAD = "CAD"
    AUD = "AUD"
    JPY = "JPY"
    CHF = "CHF"
    INR = "INR"
    BRL = "BRL"
    MXN = "MXN"


class Interval(StrEnum):
    """Billing interval types."""

    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class Money(BaseModel):
    """Immutable monetary value with currency."""

    amount: Decimal = Field(..., description="Amount in major currency units")
    currency: Currency = Field(default=Currency.USD)

    model_config = {"frozen": True}

    @field_validator("amount", mode="before")
    @classmethod
    def normalize_amount(cls, v: Any) -> Decimal:
        if isinstance(v, float):
            return Decimal(str(v))
        if isinstance(v, int):
            return Decimal(v)
        return Decimal(v)

    def __add__(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} and {other.currency}")
        return Money(amount=self.amount + other.amount, currency=self.currency)

    def __sub__(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract {self.currency} and {other.currency}")
        return Money(amount=self.amount - other.amount, currency=self.currency)

    def __mul__(self, multiplier: int | Decimal) -> Money:
        return Money(amount=self.amount * Decimal(multiplier), currency=self.currency)

    def __neg__(self) -> Money:
        return Money(amount=-self.amount, currency=self.currency)

    def __lt__(self, other: Money) -> bool:
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare {self.currency} and {other.currency}")
        return self.amount < other.amount

    def __le__(self, other: Money) -> bool:
        return self == other or self < other

    def __gt__(self, other: Money) -> bool:
        return not self <= other

    def __ge__(self, other: Money) -> bool:
        return not self < other

    @classmethod
    def zero(cls, currency: Currency = Currency.USD) -> Money:
        return cls(amount=Decimal("0"), currency=currency)

    @classmethod
    def from_cents(cls, cents: int, currency: Currency = Currency.USD) -> Money:
        """Create Money from minor units (cents)."""
        return cls(amount=Decimal(cents) / Decimal("100"), currency=currency)

    def to_cents(self) -> int:
        """Convert to minor units (cents)."""
        return int(self.amount * Decimal("100"))

    def is_zero(self) -> bool:
        return self.amount == Decimal("0")

    def is_positive(self) -> bool:
        return self.amount > Decimal("0")

    def is_negative(self) -> bool:
        return self.amount < Decimal("0")


class BillingPeriod(BaseModel):
    """Billing period configuration."""

    interval: Interval
    interval_count: int = Field(default=1, ge=1)
    anchor_date: datetime | None = None

    model_config = {"frozen": True}

    @property
    def display_name(self) -> str:
        if self.interval_count == 1:
            return f"per {self.interval.value}"
        return f"every {self.interval_count} {self.interval.value}s"

    @classmethod
    def monthly(cls) -> BillingPeriod:
        return cls(interval=Interval.MONTH, interval_count=1)

    @classmethod
    def yearly(cls) -> BillingPeriod:
        return cls(interval=Interval.YEAR, interval_count=1)

    @classmethod
    def weekly(cls) -> BillingPeriod:
        return cls(interval=Interval.WEEK, interval_count=1)


class DateRange(BaseModel):
    """Date range with start and optional end."""

    start: datetime
    end: datetime | None = None

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def validate_range(self) -> Self:
        if self.end is not None and self.end < self.start:
            raise ValueError("End date must be after start date")
        return self

    def contains(self, dt: datetime) -> bool:
        if self.end is None:
            return dt >= self.start
        return self.start <= dt <= self.end

    def is_open_ended(self) -> bool:
        return self.end is None


class ProviderReference(BaseModel):
    """Reference to an entity in a payment provider."""

    provider: ProviderType
    external_id: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": True}

    def __str__(self) -> str:
        return f"{self.provider.value}:{self.external_id}"
