"""Configuration management."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from subscriptionkore.core.models.value_objects import ProviderType


class StripeConfig(BaseSettings):
    """Stripe provider configuration."""

    model_config = SettingsConfigDict(env_prefix="STRIPE_")

    api_key: str = Field(..., description="Stripe secret API key")
    webhook_secret: str = Field(..., description="Stripe webhook signing secret")
    api_version: str = Field(default="2024-06-20", description="Stripe API version")


class PaddleConfig(BaseSettings):
    """Paddle provider configuration."""

    model_config = SettingsConfigDict(env_prefix="PADDLE_")

    api_key: str = Field(..., description="Paddle API key")
    webhook_secret: str = Field(..., description="Paddle webhook secret key")
    environment: Literal["sandbox", "production"] = Field(default="sandbox")
    seller_id: str | None = Field(default=None, description="Paddle seller/vendor ID")


class LemonSqueezyConfig(BaseSettings):
    """LemonSqueezy provider configuration."""

    model_config = SettingsConfigDict(env_prefix="LEMONSQUEEZY_")

    api_key: str = Field(..., description="LemonSqueezy API key")
    webhook_secret: str = Field(..., description="LemonSqueezy webhook signing secret")
    store_id: str = Field(..., description="LemonSqueezy store ID")


class ChargebeeConfig(BaseSettings):
    """Chargebee provider configuration."""

    model_config = SettingsConfigDict(env_prefix="CHARGEBEE_")

    site: str = Field(..., description="Chargebee site name")
    api_key: str = Field(..., description="Chargebee API key")
    webhook_username: str | None = Field(default=None, description="Webhook basic auth username")
    webhook_password: str | None = Field(default=None, description="Webhook basic auth password")


ProviderConfig = StripeConfig | PaddleConfig | LemonSqueezyConfig | ChargebeeConfig


class SubscriptionKoreConfig(BaseSettings):
    """Main configuration for SubscriptionKore."""

    model_config = SettingsConfigDict(
        env_prefix="SUBSCRIPTIONKORE_",
        env_nested_delimiter="__",
    )

    # Database
    database_url: str = Field(..., description="PostgreSQL async connection URL")

    # Cache (optional)
    redis_url: str | None = Field(default=None, description="Redis connection URL")

    # Provider configurations
    stripe: StripeConfig | None = None
    paddle: PaddleConfig | None = None
    lemonsqueezy: LemonSqueezyConfig | None = None
    chargebee: ChargebeeConfig | None = None

    # Default provider
    default_provider: ProviderType = Field(
        default=ProviderType.STRIPE,
        description="Default payment provider to use",
    )

    # Webhook processing
    webhook_processing: Literal["sync", "async"] = Field(
        default="sync",
        description="Webhook processing mode",
    )

    # Entitlement caching
    entitlement_cache_ttl: int = Field(
        default=300,
        description="Entitlement cache TTL in seconds",
    )

    # Idempotency
    processed_event_ttl_days: int = Field(
        default=7,
        description="Days to keep processed event records",
    )

    @model_validator(mode="after")
    def validate_default_provider_configured(self) -> "SubscriptionKoreConfig":
        """Ensure default provider has configuration."""
        provider_configs: dict[ProviderType, Any] = {
            ProviderType.STRIPE: self.stripe,
            ProviderType.PADDLE: self.paddle,
            ProviderType.LEMONSQUEEZY: self.lemonsqueezy,
            ProviderType.CHARGEBEE: self.chargebee,
        }

        if provider_configs.get(self.default_provider) is None:
            raise ValueError(
                f"Default provider '{self.default_provider}' is not configured.  "
                f"Please provide {self.default_provider} configuration."
            )

        return self

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL is async-compatible."""
        if not v.startswith(("postgresql+asyncpg://", "sqlite+aiosqlite://")):
            raise ValueError(
                "Database URL must use async driver (postgresql+asyncpg: // or sqlite+aiosqlite://)"
            )
        return v

    def get_provider_config(self, provider: ProviderType) -> ProviderConfig | None:
        """Get configuration for a specific provider."""
        configs: dict[ProviderType, ProviderConfig | None] = {
            ProviderType.STRIPE: self.stripe,
            ProviderType.PADDLE: self.paddle,
            ProviderType.LEMONSQUEEZY: self.lemonsqueezy,
            ProviderType.CHARGEBEE: self.chargebee,
        }
        return configs.get(provider)

    def get_configured_providers(self) -> list[ProviderType]:
        """Get list of configured providers."""
        providers: list[ProviderType] = []
        if self.stripe:
            providers.append(ProviderType.STRIPE)
        if self.paddle:
            providers.append(ProviderType.PADDLE)
        if self.lemonsqueezy:
            providers.append(ProviderType.LEMONSQUEEZY)
        if self.chargebee:
            providers.append(ProviderType.CHARGEBEE)
        return providers
