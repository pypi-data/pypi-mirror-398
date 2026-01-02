"""Paddle payment provider adapter."""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime
from decimal import Decimal
from typing import Any

import httpx
import structlog
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from subscriptionkore.config import PaddleConfig
from subscriptionkore.core.exceptions import (
    ProviderAPIError,
    ProviderAuthenticationError,
    ProviderNetworkError,
    ProviderRateLimitError,
)
from subscriptionkore.core.models import (
    Customer,
    Invoice,
    InvoiceStatus,
    Plan,
    Product,
    ProviderReference,
    ProviderType,
    Subscription,
    SubscriptionStatus,
)
from subscriptionkore.core.models.customer import Address
from subscriptionkore.core.models.invoice import InvoiceLineItem
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
from subscriptionkore.ports.provider import (
    ChangePlanRequest,
    ChangePreview,
    CheckoutRequest,
    CheckoutSession,
    CreateSubscriptionRequest,
    DiscountRequest,
    PaymentProviderPort,
    PortalSession,
    ProrationBehavior,
    ProviderCapabilities,
    ProviderWebhookEvent,
    UpdateSubscriptionRequest,
)

logger = structlog.get_logger()


class PaddleAdapter(PaymentProviderPort):
    """
    Paddle Billing payment provider implementation.

    Implements the Paddle Billing API (v1) for subscriptionkore management.
    Reference: https://developer.paddle.com/api-reference/overview
    """

    def __init__(self, config: PaddleConfig) -> None:
        self._config = config
        self._client: httpx.AsyncClient | None = None

        # Set base URL based on environment
        if config.environment == "sandbox":
            self._base_url = "https://sandbox-api.paddle.com"
        else:
            self._base_url = "https://api.paddle.com"

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                headers={
                    "Authorization": f"Bearer {self._config.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.PADDLE

    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_pausing=True,
            supports_trials=True,
            supports_quantity=True,
            supports_immediate_cancel=True,
            supports_proration=True,
            supports_coupons=True,
            supports_metered_billing=True,
            supports_customer_portal=True,
            supports_checkout_sessions=True,
        )

    def _handle_error(self, response: httpx.Response) -> None:
        """Handle Paddle API errors."""
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise ProviderRateLimitError(
                provider="paddle",
                retry_after=int(retry_after) if retry_after else None,
            )

        if response.status_code == 401:
            raise ProviderAuthenticationError(provider="paddle")

        if response.status_code >= 400:
            try:
                error_data = response.json().get("error", {})
                raise ProviderAPIError(
                    message=error_data.get("detail", "Unknown Paddle error"),
                    provider="paddle",
                    status_code=response.status_code,
                    provider_message=error_data.get("detail"),
                    provider_code=error_data.get("code"),
                )
            except json.JSONDecodeError:
                raise ProviderAPIError(
                    message=f"Paddle API error: {response.status_code}",
                    provider="paddle",
                    status_code=response.status_code,
                )

    @retry(
        retry=retry_if_exception_type((ProviderRateLimitError, ProviderNetworkError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(initial=1, max=60),
    )
    async def _request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make authenticated request to Paddle API."""
        client = await self._get_client()

        try:
            response = await client.request(
                method=method,
                url=endpoint,
                json=data,
                params=params,
            )
        except httpx.NetworkError as e:
            raise ProviderNetworkError(provider="paddle", original_error=e) from e

        self._handle_error(response)
        return response.json()

    # Status mapping
    STATUS_MAP = {
        "active": SubscriptionStatus.ACTIVE,
        "trialing": SubscriptionStatus.TRIALING,
        "past_due": SubscriptionStatus.PAST_DUE,
        "paused": SubscriptionStatus.PAUSED,
        "canceled": SubscriptionStatus.CANCELED,
    }

    # Customer Operations

    async def create_customer(self, customer: Customer) -> ProviderReference:
        data: dict[str, Any] = {
            "email": customer.email,
            "custom_data": {
                "subscriptionkore_id": customer.id,
                "external_id": customer.external_id,
            },
        }

        if customer.name:
            data["name"] = customer.name

        result = await self._request("POST", "/customers", data=data)
        customer_data = result.get("data", {})

        return ProviderReference(
            provider=ProviderType.PADDLE,
            external_id=customer_data["id"],
            metadata={"email": customer_data.get("email")},
        )

    async def update_customer(self, customer: Customer) -> None:
        provider_ref = customer.get_provider_ref("paddle")
        if provider_ref is None:
            raise ProviderAPIError(
                message="Customer has no Paddle reference",
                provider="paddle",
                status_code=400,
            )

        data: dict[str, Any] = {"email": customer.email}

        if customer.name:
            data["name"] = customer.name

        await self._request("PATCH", f"/customers/{provider_ref.external_id}", data=data)

    async def delete_customer(self, provider_ref: ProviderReference) -> None:
        # Paddle doesn't support customer deletion, but we can update to anonymize
        await self._request(
            "PATCH",
            f"/customers/{provider_ref.external_id}",
            data={
                "name": "Deleted Customer",
                "email": f"deleted_{provider_ref.external_id}@example.com",
            },
        )

    async def get_customer(self, provider_ref: ProviderReference) -> Customer:
        result = await self._request("GET", f"/customers/{provider_ref.external_id}")
        data = result.get("data", {})

        custom_data = data.get("custom_data", {})

        return Customer(
            id=custom_data.get("subscriptionkore_id", ""),
            external_id=custom_data.get("external_id", ""),
            email=data.get("email", ""),
            name=data.get("name"),
            provider_refs=[provider_ref],
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
        )

    # Subscription Operations

    async def create_subscriptionkore(
        self,
        request: CreateSubscriptionRequest,
        customer_provider_ref: ProviderReference,
        plan_provider_ref: ProviderReference,
    ) -> Subscription:
        """
        Create a subscriptionkore in Paddle.

        Note: Paddle subscriptionkores are typically created through checkout.
        This method creates a subscriptionkore directly via API.
        """
        data: dict[str, Any] = {
            "customer_id": customer_provider_ref.external_id,
            "items": [
                {
                    "price_id": plan_provider_ref.external_id,
                    "quantity": request.quantity,
                }
            ],
            "custom_data": {
                "subscriptionkore_customer_id": request.customer_id,
                "subscriptionkore_plan_id": request.plan_id,
            },
        }

        if request.trial_period_days:
            # Calculate trial end date
            from datetime import timedelta

            trial_end = datetime.utcnow() + timedelta(days=request.trial_period_days)
            data["billing_cycle"] = {
                "interval": "month",
                "frequency": 1,
            }
            # Paddle handles trials through the price configuration

        if request.coupon_code:
            data["discount_id"] = request.coupon_code

        for key, value in request.metadata.items():
            data["custom_data"][key] = str(value)

        result = await self._request("POST", "/subscriptionkores", data=data)

        return self._map_subscriptionkore(
            result.get("data", {}),
            request.customer_id,
            request.plan_id,
        )

    async def update_subscriptionkore(
        self,
        request: UpdateSubscriptionRequest,
        subscriptionkore_provider_ref: ProviderReference,
    ) -> Subscription:
        data: dict[str, Any] = {}

        if request.quantity is not None:
            # Get current subscriptionkore to find item
            sub = await self._request(
                "GET",
                f"/subscriptionkores/{subscriptionkore_provider_ref.external_id}",
            )
            items = sub.get("data", {}).get("items", [])
            if items:
                data["items"] = [
                    {
                        "price_id": items[0]["price"]["id"],
                        "quantity": request.quantity,
                    }
                ]

        if request.cancel_at_period_end is not None:
            if request.cancel_at_period_end:
                data["scheduled_change"] = {"action": "cancel"}
            else:
                # Remove scheduled cancellation
                pass

        if request.metadata:
            data["custom_data"] = request.metadata

        result = await self._request(
            "PATCH",
            f"/subscriptionkores/{subscriptionkore_provider_ref.external_id}",
            data=data,
        )

        return self._map_subscriptionkore(result.get("data", {}), "", "")

    async def cancel_subscriptionkore(
        self,
        subscriptionkore_provider_ref: ProviderReference,
        immediate: bool = False,
    ) -> Subscription:
        if immediate:
            data = {"effective_from": "immediately"}
        else:
            data = {"effective_from": "next_billing_period"}

        result = await self._request(
            "POST",
            f"/subscriptionkores/{subscriptionkore_provider_ref.external_id}/cancel",
            data=data,
        )

        return self._map_subscriptionkore(result.get("data", {}), "", "")

    async def pause_subscriptionkore(
        self,
        subscriptionkore_provider_ref: ProviderReference,
        resumes_at: datetime | None = None,
    ) -> Subscription:
        data: dict[str, Any] = {"effective_from": "next_billing_period"}

        if resumes_at:
            data["resume_at"] = resumes_at.isoformat() + "Z"

        result = await self._request(
            "POST",
            f"/subscriptionkores/{subscriptionkore_provider_ref.external_id}/pause",
            data=data,
        )

        return self._map_subscriptionkore(result.get("data", {}), "", "")

    async def resume_subscriptionkore(
        self,
        subscriptionkore_provider_ref: ProviderReference,
    ) -> Subscription:
        result = await self._request(
            "POST",
            f"/subscriptionkores/{subscriptionkore_provider_ref.external_id}/resume",
            data={"effective_from": "immediately"},
        )

        return self._map_subscriptionkore(result.get("data", {}), "", "")

    async def get_subscriptionkore(
        self,
        provider_ref: ProviderReference,
    ) -> Subscription:
        result = await self._request("GET", f"/subscriptionkores/{provider_ref.external_id}")
        return self._map_subscriptionkore(result.get("data", {}), "", "")

    # Plan Change Operations

    async def change_plan(
        self,
        request: ChangePlanRequest,
        subscriptionkore_provider_ref: ProviderReference,
        new_plan_provider_ref: ProviderReference,
    ) -> Subscription:
        proration_map = {
            ProrationBehavior.CREATE_PRORATIONS: "prorated_immediately",
            ProrationBehavior.NONE: "full_immediately",
            ProrationBehavior.ALWAYS_INVOICE: "prorated_immediately",
        }

        data = {
            "items": [
                {
                    "price_id": new_plan_provider_ref.external_id,
                    "quantity": 1,
                }
            ],
            "proration_billing_mode": proration_map.get(
                request.proration_behavior, "prorated_immediately"
            ),
        }

        result = await self._request(
            "PATCH",
            f"/subscriptionkores/{subscriptionkore_provider_ref.external_id}",
            data=data,
        )

        return self._map_subscriptionkore(result.get("data", {}), "", request.new_plan_id)

    async def preview_plan_change(
        self,
        request: ChangePlanRequest,
        subscriptionkore_provider_ref: ProviderReference,
        new_plan_provider_ref: ProviderReference,
    ) -> ChangePreview:
        data = {
            "items": [
                {
                    "price_id": new_plan_provider_ref.external_id,
                    "quantity": 1,
                }
            ],
            "proration_billing_mode": "prorated_immediately",
        }

        result = await self._request(
            "POST",
            f"/subscriptionkores/{subscriptionkore_provider_ref.external_id}/preview",
            data=data,
        )

        preview_data = result.get("data", {})
        immediate_transaction = preview_data.get("immediate_transaction", {})

        currency = Currency(
            immediate_transaction.get("details", {}).get("totals", {}).get("currency_code", "USD")
        )

        totals = immediate_transaction.get("details", {}).get("totals", {})

        return ChangePreview(
            immediate_charge=Money(
                amount=Decimal(totals.get("grand_total", "0")) / 100,
                currency=currency,
            ),
            next_invoice_amount=Money(
                amount=Decimal(
                    preview_data.get("recurring_transaction_details", {})
                    .get("totals", {})
                    .get("grand_total", "0")
                )
                / 100,
                currency=currency,
            ),
            proration_amount=Money(
                amount=Decimal(totals.get("proration", "0")) / 100,
                currency=currency,
            ),
            credit_amount=Money(
                amount=Decimal(totals.get("credit", "0")) / 100,
                currency=currency,
            ),
            next_billing_date=datetime.fromisoformat(
                preview_data.get("next_billed_at", datetime.utcnow().isoformat()).replace(
                    "Z", "+00:00"
                )
            ),
        )

    # Discount Operations

    async def apply_discount(
        self,
        subscriptionkore_provider_ref: ProviderReference,
        discount: DiscountRequest,
    ) -> Subscription:
        data: dict[str, Any] = {}

        if discount.coupon_code:
            data["discount_id"] = discount.coupon_code
        elif discount.promotion_code:
            data["discount_id"] = discount.promotion_code

        result = await self._request(
            "PATCH",
            f"/subscriptionkores/{subscriptionkore_provider_ref.external_id}",
            data=data,
        )

        return self._map_subscriptionkore(result.get("data", {}), "", "")

    async def remove_discount(
        self,
        subscriptionkore_provider_ref: ProviderReference,
    ) -> Subscription:
        result = await self._request(
            "PATCH",
            f"/subscriptionkores/{subscriptionkore_provider_ref.external_id}",
            data={"discount_id": None},
        )

        return self._map_subscriptionkore(result.get("data", {}), "", "")

    # Billing Operations

    async def get_invoice(self, provider_ref: ProviderReference) -> Invoice:
        result = await self._request("GET", f"/transactions/{provider_ref.external_id}")
        return self._map_transaction_to_invoice(result.get("data", {}))

    async def list_invoices(
        self,
        customer_provider_ref: ProviderReference,
        limit: int = 10,
        starting_after: str | None = None,
    ) -> list[Invoice]:
        params: dict[str, Any] = {
            "customer_id": customer_provider_ref.external_id,
            "per_page": limit,
            "status": "completed,billed",
        }

        if starting_after:
            params["after"] = starting_after

        result = await self._request("GET", "/transactions", params=params)

        return [self._map_transaction_to_invoice(txn) for txn in result.get("data", [])]

    async def get_upcoming_invoice(
        self,
        subscriptionkore_provider_ref: ProviderReference,
    ) -> Invoice | None:
        try:
            result = await self._request(
                "GET",
                f"/subscriptionkores/{subscriptionkore_provider_ref.external_id}/upcoming-invoice",
            )
            return self._map_transaction_to_invoice(result.get("data", {}))
        except ProviderAPIError as e:
            if e.status_code == 404:
                return None
            raise

    # Checkout / Portal

    async def create_checkout_session(
        self,
        request: CheckoutRequest,
        plan_provider_ref: ProviderReference,
        customer_provider_ref: ProviderReference | None = None,
    ) -> CheckoutSession:
        data: dict[str, Any] = {
            "items": [
                {
                    "price_id": plan_provider_ref.external_id,
                    "quantity": request.quantity,
                }
            ],
            "settings": {
                "success_url": request.success_url,
            },
            "custom_data": request.metadata,
        }

        if customer_provider_ref:
            data["customer_id"] = customer_provider_ref.external_id
        elif request.customer_email:
            data["customer"] = {"email": request.customer_email}

        if request.trial_period_days:
            data["items"][0]["trial_period"] = {
                "interval": "day",
                "frequency": request.trial_period_days,
            }

        result = await self._request("POST", "/transactions", data=data)
        txn_data = result.get("data", {})

        checkout_url = txn_data.get("checkout", {}).get("url", "")

        return CheckoutSession(
            id=txn_data["id"],
            url=checkout_url,
            expires_at=datetime.utcnow(),  # Paddle doesn't provide expiration
        )

    async def create_portal_session(
        self,
        customer_provider_ref: ProviderReference,
        return_url: str,
    ) -> PortalSession:
        # Paddle uses a different approach - customer portal URL
        # The portal URL is static per environment
        if self._config.environment == "sandbox":
            portal_base = "https://sandbox-customer-portal.paddle.com"
        else:
            portal_base = "https://customer-portal.paddle. com"

        # Generate a portal session
        result = await self._request(
            "POST",
            f"/customers/{customer_provider_ref.external_id}/portal-sessions",
            data={},
        )

        session_data = result.get("data", {})

        return PortalSession(
            id=session_data.get("id", ""),
            url=session_data.get("urls", {}).get("general", {}).get("overview", portal_base),
        )

    # Webhook Handling

    async def verify_webhook(
        self,
        payload: bytes,
        headers: dict[str, str],
    ) -> bool:
        """Verify Paddle webhook signature."""
        signature = headers.get("paddle-signature", "")
        if not signature:
            return False

        # Parse signature header
        # Format: ts=timestamp;h1=hash
        parts = dict(part.split("=", 1) for part in signature.split(";") if "=" in part)
        timestamp = parts.get("ts", "")
        received_hash = parts.get("h1", "")

        if not timestamp or not received_hash:
            return False

        # Build signed payload
        signed_payload = f"{timestamp}:{payload.decode('utf-8')}"

        # Compute expected signature
        expected_hash = hmac.new(
            self._config.webhook_secret.encode("utf-8"),
            signed_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected_hash, received_hash)

    async def parse_webhook(
        self,
        payload: bytes,
        headers: dict[str, str],
    ) -> ProviderWebhookEvent:
        """Parse Paddle webhook payload."""
        data = json.loads(payload)

        return ProviderWebhookEvent(
            provider=ProviderType.PADDLE,
            event_id=data.get("event_id", data.get("notification_id", "")),
            event_type=data.get("event_type", ""),
            occurred_at=datetime.fromisoformat(
                data.get("occurred_at", datetime.utcnow().isoformat()).replace("Z", "+00:00")
            ),
            data=data.get("data", {}),
            raw_payload=payload,
        )

    # Sync Operations

    async def sync_products(self) -> list[Product]:
        result = await self._request("GET", "/products", params={"status": "active"})

        products = []
        for prod in result.get("data", []):
            products.append(
                Product(
                    id="",
                    name=prod["name"],
                    description=prod.get("description"),
                    provider_refs=[
                        ProviderReference(
                            provider=ProviderType.PADDLE,
                            external_id=prod["id"],
                        )
                    ],
                    active=prod["status"] == "active",
                    metadata=prod.get("custom_data", {}),
                    created_at=datetime.fromisoformat(prod["created_at"].replace("Z", "+00:00")),
                )
            )

        return products

    async def sync_plans(self, product_provider_ref: ProviderReference) -> list[Plan]:
        result = await self._request(
            "GET",
            "/prices",
            params={
                "product_id": product_provider_ref.external_id,
                "status": "active",
            },
        )

        plans = []
        for price in result.get("data", []):
            billing_cycle = price.get("billing_cycle", {})
            interval = billing_cycle.get("interval", "month")
            interval_count = billing_cycle.get("frequency", 1)

            # Map Paddle intervals to our intervals
            interval_map = {
                "day": Interval.DAY,
                "week": Interval.WEEK,
                "month": Interval.MONTH,
                "year": Interval.YEAR,
            }

            unit_price = price.get("unit_price", {})

            plans.append(
                Plan(
                    id="",
                    product_id="",
                    name=price.get("description") or price["id"],
                    provider_refs=[
                        ProviderReference(
                            provider=ProviderType.PADDLE,
                            external_id=price["id"],
                        )
                    ],
                    price=Money(
                        amount=Decimal(unit_price.get("amount", "0")) / 100,
                        currency=Currency(unit_price.get("currency_code", "USD")),
                    ),
                    billing_period=BillingPeriod(
                        interval=interval_map.get(interval, Interval.MONTH),
                        interval_count=interval_count,
                    ),
                    trial_period_days=price.get("trial_period", {}).get("frequency"),
                    active=price["status"] == "active",
                    metadata=price.get("custom_data", {}),
                    created_at=datetime.fromisoformat(price["created_at"].replace("Z", "+00:00")),
                )
            )

        return plans

    # Mapping Helpers

    def _map_subscriptionkore(
        self,
        data: dict[str, Any],
        customer_id: str,
        plan_id: str,
    ) -> Subscription:
        """Map Paddle subscriptionkore to domain model."""
        status = self.STATUS_MAP.get(data.get("status", "active"), SubscriptionStatus.ACTIVE)

        # Handle pause
        pause_config = None
        if data.get("paused_at"):
            pause_config = PauseConfig(
                resumes_at=datetime.fromisoformat(
                    data["scheduled_change"]["resume_at"].replace("Z", "+00:00")
                )
                if data.get("scheduled_change", {}).get("resume_at")
                else None,
                behavior=PauseBehavior.VOID,
            )

        # Handle discount
        discount = None
        if data.get("discount"):
            disc = data["discount"]
            discount = AppliedDiscount(
                discount_id=disc["id"],
                coupon_code=disc.get("code"),
                amount_off=Money(
                    amount=Decimal(disc["amount"]) / 100,
                    currency=Currency(data.get("currency_code", "USD")),
                )
                if disc.get("amount")
                else None,
                percent_off=Decimal(str(disc["percentage"])) if disc.get("percentage") else None,
                valid_until=datetime.fromisoformat(disc["ends_at"].replace("Z", "+00:00"))
                if disc.get("ends_at")
                else None,
            )

        # Get quantity from items
        quantity = 1
        items = data.get("items", [])
        if items:
            quantity = items[0].get("quantity", 1)

        # Get trial end
        trial_end = None
        if data.get("current_billing_period", {}).get("trial_ends_at"):
            trial_end = datetime.fromisoformat(
                data["current_billing_period"]["trial_ends_at"].replace("Z", "+00:00")
            )

        # Use custom_data for internal IDs
        custom_data = data.get("custom_data", {})
        resolved_customer_id = customer_id or custom_data.get("subscriptionkore_customer_id", "")
        resolved_plan_id = plan_id or custom_data.get("subscriptionkore_plan_id", "")

        # Parse billing period
        current_period_start = datetime.utcnow()
        current_period_end = None
        if data.get("current_billing_period"):
            period = data["current_billing_period"]
            current_period_start = datetime.fromisoformat(
                period["starts_at"].replace("Z", "+00:00")
            )
            current_period_end = datetime.fromisoformat(period["ends_at"].replace("Z", "+00:00"))

        return Subscription(
            id="",
            customer_id=resolved_customer_id,
            plan_id=resolved_plan_id,
            provider_ref=ProviderReference(
                provider=ProviderType.PADDLE,
                external_id=data["id"],
                metadata={"customer_id": data.get("customer_id")},
            ),
            status=status,
            current_period=DateRange(
                start=current_period_start,
                end=current_period_end,
            ),
            trial_end=trial_end,
            cancel_at_period_end=data.get("scheduled_change", {}).get("action") == "cancel",
            canceled_at=datetime.fromisoformat(data["canceled_at"].replace("Z", "+00:00"))
            if data.get("canceled_at")
            else None,
            pause_collection=pause_config,
            discount=discount,
            quantity=quantity,
            metadata=custom_data,
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
        )

    def _map_transaction_to_invoice(self, data: dict[str, Any]) -> Invoice:
        """Map Paddle transaction to Invoice domain model."""
        details = data.get("details", {})
        totals = details.get("totals", {})
        currency = Currency(totals.get("currency_code", "USD"))

        status_map = {
            "draft": InvoiceStatus.DRAFT,
            "ready": InvoiceStatus.OPEN,
            "billed": InvoiceStatus.OPEN,
            "paid": InvoiceStatus.PAID,
            "completed": InvoiceStatus.PAID,
            "canceled": InvoiceStatus.VOID,
        }

        # Map line items
        line_items = []
        for item in details.get("line_items", []):
            line_items.append(
                InvoiceLineItem(
                    id=item.get("id", ""),
                    description=item.get("product", {}).get("name", ""),
                    quantity=item.get("quantity", 1),
                    unit_amount=Money(
                        amount=Decimal(item.get("unit_totals", {}).get("subtotal", "0")) / 100,
                        currency=currency,
                    ),
                    amount=Money(
                        amount=Decimal(item.get("totals", {}).get("subtotal", "0")) / 100,
                        currency=currency,
                    ),
                    proration=item.get("proration", False),
                )
            )

        return Invoice(
            id="",
            customer_id=data.get("customer_id", ""),
            subscriptionkore_id=data.get("subscriptionkore_id"),
            provider_ref=ProviderReference(
                provider=ProviderType.PADDLE,
                external_id=data.get("id", ""),
            ),
            status=status_map.get(data.get("status", "draft"), InvoiceStatus.DRAFT),
            subtotal=Money(
                amount=Decimal(totals.get("subtotal", "0")) / 100,
                currency=currency,
            ),
            tax=Money(
                amount=Decimal(totals.get("tax", "0")) / 100,
                currency=currency,
            ),
            discount_amount=Money(
                amount=Decimal(totals.get("discount", "0")) / 100,
                currency=currency,
            ),
            total=Money(
                amount=Decimal(totals.get("grand_total", "0")) / 100,
                currency=currency,
            ),
            amount_paid=Money(
                amount=Decimal(totals.get("grand_total", "0")) / 100
                if data.get("status") in ("paid", "completed")
                else Decimal("0"),
                currency=currency,
            ),
            amount_due=Money(
                amount=Decimal(totals.get("grand_total", "0")) / 100
                if data.get("status") not in ("paid", "completed")
                else Decimal("0"),
                currency=currency,
            ),
            currency=currency,
            line_items=line_items,
            invoice_pdf_url=data.get("checkout", {}).get("url"),
            metadata=data.get("custom_data", {}),
            created_at=datetime.fromisoformat(
                data.get("created_at", datetime.utcnow().isoformat()).replace("Z", "+00:00")
            ),
        )
