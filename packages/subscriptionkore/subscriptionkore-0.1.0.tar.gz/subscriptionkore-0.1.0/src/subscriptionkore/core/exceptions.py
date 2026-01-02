"""Domain exceptions."""

from __future__ import annotations

from typing import Any

from subscriptionkore.core.models.subscription import SubscriptionStatus


class SubscriptionKoreError(Exception):
    """Base exception for all subscriptionkore errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


# Configuration Errors


class ConfigurationError(SubscriptionKoreError):
    """Base class for configuration errors."""

    pass


class MissingProviderCredentialsError(ConfigurationError):
    """Raised when provider credentials are missing."""

    def __init__(self, provider: str, missing_fields: list[str]) -> None:
        super().__init__(
            f"Missing credentials for provider '{provider}':  {', '.join(missing_fields)}",
            {"provider": provider, "missing_fields": missing_fields},
        )
        self.provider = provider
        self.missing_fields = missing_fields


class InvalidConfigurationError(ConfigurationError):
    """Raised when configuration is invalid."""

    pass


# Provider Errors


class ProviderError(SubscriptionKoreError):
    """Base class for provider errors."""

    def __init__(
        self,
        message: str,
        provider: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details)
        self.provider = provider


class ProviderAPIError(ProviderError):
    """Raised for non-recoverable API errors from providers."""

    def __init__(
        self,
        message: str,
        provider: str,
        status_code: int,
        provider_message: str | None = None,
        provider_code: str | None = None,
    ) -> None:
        super().__init__(
            message,
            provider,
            {
                "status_code": status_code,
                "provider_message": provider_message,
                "provider_code": provider_code,
            },
        )
        self.status_code = status_code
        self.provider_message = provider_message
        self.provider_code = provider_code


class ProviderRateLimitError(ProviderError):
    """Raised when provider rate limit is exceeded.  Recoverable with retry."""

    def __init__(
        self,
        provider: str,
        retry_after: int | None = None,
    ) -> None:
        super().__init__(
            f"Rate limit exceeded for provider '{provider}'",
            provider,
            {"retry_after": retry_after},
        )
        self.retry_after = retry_after


class ProviderNetworkError(ProviderError):
    """Raised for network errors.  Recoverable with retry."""

    def __init__(self, provider: str, original_error: Exception) -> None:
        super().__init__(
            f"Network error connecting to provider '{provider}': {original_error}",
            provider,
            {"original_error": str(original_error)},
        )
        self.original_error = original_error


class ProviderAuthenticationError(ProviderError):
    """Raised when authentication fails.  Non-recoverable."""

    def __init__(self, provider: str, message: str | None = None) -> None:
        super().__init__(
            message or f"Authentication failed for provider '{provider}'",
            provider,
        )


# Webhook Errors


class WebhookError(SubscriptionKoreError):
    """Base class for webhook errors."""

    pass


class WebhookSignatureInvalidError(WebhookError):
    """Raised when webhook signature verification fails."""

    def __init__(self, provider: str) -> None:
        super().__init__(
            f"Invalid webhook signature for provider '{provider}'",
            {"provider": provider},
        )
        self.provider = provider


class WebhookPayloadInvalidError(WebhookError):
    """Raised when webhook payload cannot be parsed."""

    def __init__(self, provider: str, reason: str) -> None:
        super().__init__(
            f"Invalid webhook payload from '{provider}': {reason}",
            {"provider": provider, "reason": reason},
        )
        self.provider = provider
        self.reason = reason


class WebhookProcessingError(WebhookError):
    """Raised when webhook processing fails."""

    def __init__(self, event_id: str, reason: str) -> None:
        super().__init__(
            f"Failed to process webhook event '{event_id}': {reason}",
            {"event_id": event_id, "reason": reason},
        )
        self.event_id = event_id
        self.reason = reason


# Domain Errors


class DomainError(SubscriptionKoreError):
    """Base class for domain errors."""

    pass


class EntityNotFoundError(DomainError):
    """Raised when an entity is not found."""

    def __init__(self, entity_type: str, entity_id: str) -> None:
        super().__init__(
            f"{entity_type} with id '{entity_id}' not found",
            {"entity_type": entity_type, "entity_id": entity_id},
        )
        self.entity_type = entity_type
        self.entity_id = entity_id


class InvalidStateTransitionError(DomainError):
    """Raised when an invalid state transition is attempted."""

    def __init__(
        self,
        from_state: SubscriptionStatus,
        to_state: SubscriptionStatus,
        reason: str | None = None,
    ) -> None:
        msg = f"Invalid state transition from '{from_state}' to '{to_state}'"
        if reason:
            msg += f": {reason}"
        super().__init__(
            msg,
            {"from_state": from_state, "to_state": to_state, "reason": reason},
        )
        self.from_state = from_state
        self.to_state = to_state
        self.reason = reason


class DuplicateEntityError(DomainError):
    """Raised when attempting to create a duplicate entity."""

    def __init__(self, entity_type: str, identifier: str) -> None:
        super().__init__(
            f"{entity_type} with identifier '{identifier}' already exists",
            {"entity_type": entity_type, "identifier": identifier},
        )
        self.entity_type = entity_type
        self.identifier = identifier


class ValidationError(DomainError):
    """Raised when validation fails."""

    def __init__(self, field: str, message: str) -> None:
        super().__init__(
            f"Validation error for '{field}': {message}",
            {"field": field},
        )
        self.field = field


# Entitlement Errors


class EntitlementError(SubscriptionKoreError):
    """Base class for entitlement errors."""

    pass


class EntitlementNotFoundError(EntitlementError):
    """Raised when an entitlement is not found."""

    def __init__(self, key: str) -> None:
        super().__init__(
            f"Entitlement with key '{key}' not found",
            {"key": key},
        )
        self.key = key


class UsageLimitExceededError(EntitlementError):
    """Raised when a usage limit is exceeded."""

    def __init__(
        self,
        entitlement_key: str,
        limit: int,
        current_usage: int,
        requested: int,
    ) -> None:
        super().__init__(
            f"Usage limit exceeded for '{entitlement_key}': "
            f"limit={limit}, current={current_usage}, requested={requested}",
            {
                "entitlement_key": entitlement_key,
                "limit": limit,
                "current_usage": current_usage,
                "requested": requested,
            },
        )
        self.entitlement_key = entitlement_key
        self.limit = limit
        self.current_usage = current_usage
        self.requested = requested


# Repository Errors


class RepositoryError(SubscriptionKoreError):
    """Raised when a repository operation fails."""

    def __init__(self, operation: str, entity_type: str, original_error: Exception) -> None:
        super().__init__(
            f"Repository error during '{operation}' on '{entity_type}': {original_error}",
            {
                "operation": operation,
                "entity_type": entity_type,
                "original_error": str(original_error),
            },
        )
        self.operation = operation
        self.entity_type = entity_type
        self.original_error = original_error
