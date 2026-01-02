"""Stripe payment provider adapter."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

import httpx
import structlog
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from subscriptionkore.config import StripeConfig
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

if TYPE_CHECKING:
    pass

logger = structlog.get_logger()


class StripeAdapter(PaymentProviderPort):
    """Stripe payment provider implementation."""

    BASE_URL = "https://api.stripe.com/v1"

    STATUS_MAP = {
        "incomplete": SubscriptionStatus.INCOMPLETE,
        "incomplete_expired": SubscriptionStatus.INCOMPLETE_EXPIRED,
        "trialing": SubscriptionStatus.TRIALING,
        "active": SubscriptionStatus.ACTIVE,
        "past_due": SubscriptionStatus.PAST_DUE,
        "canceled": SubscriptionStatus.CANCELED,
        "unpaid": SubscriptionStatus.UNPAID,
        "paused": SubscriptionStatus.PAUSED,
    }

    INVOICE_STATUS_MAP = {
        "draft": InvoiceStatus.DRAFT,
        "open": InvoiceStatus.OPEN,
        "paid": InvoiceStatus.PAID,
        "void": InvoiceStatus.VOID,
        "uncollectible": InvoiceStatus.UNCOLLECTIBLE,
    }

    def __init__(self, config: StripeConfig) -> None:
        self._config = config
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers={
                    "Authorization": f"Bearer {self._config.api_key}",
                    "Stripe-Version": self._config.api_version,
                    "Content-Type": "application/x-www-form-urlencoded",
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
        return ProviderType.STRIPE

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
        """Handle Stripe API errors."""
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise ProviderRateLimitError(
                provider="stripe",
                retry_after=int(retry_after) if retry_after else None,
            )

        if response.status_code == 401:
            raise ProviderAuthenticationError(provider="stripe")

        if response.status_code >= 400:
            try:
                error_data = response.json().get("error", {})
                raise ProviderAPIError(
                    message=error_data.get("message", "Unknown Stripe error"),
                    provider="stripe",
                    status_code=response.status_code,
                    provider_message=error_data.get("message"),
                    provider_code=error_data.get("code"),
                )
            except Exception as e:
                if isinstance(e, ProviderAPIError):
                    raise
                raise ProviderAPIError(
                    message=f"Stripe API error: {response.status_code}",
                    provider="stripe",
                    status_code=response.status_code,
                ) from e

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
        """Make authenticated request to Stripe API."""
        client = await self._get_client()

        try:
            response = await client.request(
                method=method,
                url=endpoint,
                data=data,
                params=params,
            )
        except httpx.NetworkError as e:
            raise ProviderNetworkError(provider="stripe", original_error=e) from e

        self._handle_error(response)
        return response.json()

    # Customer Operations

    async def create_customer(self, customer: Customer) -> ProviderReference:
        data: dict[str, Any] = {
            "email": customer.email,
            "metadata[subscriptionkore_id]": customer.id,
            "metadata[external_id]": customer.external_id,
        }

        if customer.name:
            data["name"] = customer.name

        if customer.billing_address:
            addr = customer.billing_address
            if addr.line1:
                data["address[line1]"] = addr.line1
            if addr.line2:
                data["address[line2]"] = addr.line2
            if addr.city:
                data["address[city]"] = addr.city
            if addr.state:
                data["address[state]"] = addr.state
            if addr.postal_code:
                data["address[postal_code]"] = addr.postal_code
            if addr.country:
                data["address[country]"] = addr.country

        result = await self._request("POST", "/customers", data=data)

        return ProviderReference(
            provider=ProviderType.STRIPE,
            external_id=result["id"],
            metadata={"email": result.get("email")},
        )

    async def update_customer(self, customer: Customer) -> None:
        provider_ref = customer.get_provider_ref("stripe")
        if provider_ref is None:
            raise ProviderAPIError(
                message="Customer has no Stripe reference",
                provider="stripe",
                status_code=400,
            )

        data: dict[str, Any] = {"email": customer.email}

        if customer.name:
            data["name"] = customer.name

        await self._request("POST", f"/customers/{provider_ref.external_id}", data=data)

    async def delete_customer(self, provider_ref: ProviderReference) -> None:
        await self._request("DELETE", f"/customers/{provider_ref.external_id}")

    async def get_customer(self, provider_ref: ProviderReference) -> Customer:
        result = await self._request("GET", f"/customers/{provider_ref.external_id}")

        from subscriptionkore.core.models.customer import Address

        address = None
        if result.get("address"):
            addr = result["address"]
            address = Address(
                line1=addr.get("line1"),
                line2=addr.get("line2"),
                city=addr.get("city"),
                state=addr.get("state"),
                postal_code=addr.get("postal_code"),
                country=addr.get("country"),
            )

        return Customer(
            id=result.get("metadata", {}).get("subscriptionkore_id", ""),
            external_id=result.get("metadata", {}).get("external_id", ""),
            email=result.get("email", ""),
            name=result.get("name"),
            billing_address=address,
            provider_refs=[provider_ref],
            created_at=datetime.fromtimestamp(result["created"]),
        )

    # Subscription Operations

    async def create_subscriptionkore(
        self,
        request: CreateSubscriptionRequest,
        customer_provider_ref: ProviderReference,
        plan_provider_ref: ProviderReference,
    ) -> Subscription:
        data: dict[str, Any] = {
            "customer": customer_provider_ref.external_id,
            "items[0][price]": plan_provider_ref.external_id,
            "items[0][quantity]": str(request.quantity),
            "metadata[subscriptionkore_customer_id]": request.customer_id,
            "metadata[subscriptionkore_plan_id]": request.plan_id,
        }

        if request.trial_period_days:
            data["trial_period_days"] = str(request.trial_period_days)

        if request.coupon_code:
            data["coupon"] = request.coupon_code

        if request.payment_method_id:
            data["default_payment_method"] = request.payment_method_id

        for key, value in request.metadata.items():
            data[f"metadata[{key}]"] = str(value)

        result = await self._request("POST", "/subscriptionkores", data=data)

        return self._map_subscriptionkore(result, request.customer_id, request.plan_id)

    async def update_subscriptionkore(
        self,
        request: UpdateSubscriptionRequest,
        subscriptionkore_provider_ref: ProviderReference,
    ) -> Subscription:
        data: dict[str, Any] = {}

        if request.quantity is not None:
            # Need to get the subscriptionkore first to find the item ID
            sub = await self._request(
                "GET",
                f"/subscriptionkores/{subscriptionkore_provider_ref.external_id}",
            )
            if sub.get("items", {}).get("data"):
                item_id = sub["items"]["data"][0]["id"]
                data[f"items[0][id]"] = item_id
                data[f"items[0][quantity]"] = str(request.quantity)

        if request.cancel_at_period_end is not None:
            data["cancel_at_period_end"] = str(request.cancel_at_period_end).lower()

        if request.metadata:
            for key, value in request.metadata.items():
                data[f"metadata[{key}]"] = str(value)

        result = await self._request(
            "POST",
            f"/subscriptionkores/{subscriptionkore_provider_ref.external_id}",
            data=data,
        )

        return self._map_subscriptionkore(result, "", "")

    async def cancel_subscriptionkore(
        self,
        subscriptionkore_provider_ref: ProviderReference,
        immediate: bool = False,
    ) -> Subscription:
        if immediate:
            result = await self._request(
                "DELETE",
                f"/subscriptionkores/{subscriptionkore_provider_ref.external_id}",
            )
        else:
            result = await self._request(
                "POST",
                f"/subscriptionkores/{subscriptionkore_provider_ref.external_id}",
                data={"cancel_at_period_end": "true"},
            )

        return self._map_subscriptionkore(result, "", "")

    async def pause_subscriptionkore(
        self,
        subscriptionkore_provider_ref: ProviderReference,
        resumes_at: datetime | None = None,
    ) -> Subscription:
        data: dict[str, Any] = {"pause_collection[behavior]": "void"}

        if resumes_at:
            data["pause_collection[resumes_at]"] = str(int(resumes_at.timestamp()))

        result = await self._request(
            "POST",
            f"/subscriptionkores/{subscriptionkore_provider_ref.external_id}",
            data=data,
        )

        return self._map_subscriptionkore(result, "", "")

    async def resume_subscriptionkore(
        self,
        subscriptionkore_provider_ref: ProviderReference,
    ) -> Subscription:
        result = await self._request(
            "POST",
            f"/subscriptionkores/{subscriptionkore_provider_ref.external_id}",
            data={"pause_collection": ""},
        )

        return self._map_subscriptionkore(result, "", "")

    async def get_subscriptionkore(
        self,
        provider_ref: ProviderReference,
    ) -> Subscription:
        result = await self._request("GET", f"/subscriptionkores/{provider_ref.external_id}")
        return self._map_subscriptionkore(result, "", "")

    # Plan Change Operations

    async def change_plan(
        self,
        request: ChangePlanRequest,
        subscriptionkore_provider_ref: ProviderReference,
        new_plan_provider_ref: ProviderReference,
    ) -> Subscription:
        # Get current subscriptionkore to find item ID
        sub = await self._request(
            "GET",
            f"/subscriptionkores/{subscriptionkore_provider_ref.external_id}",
        )

        item_id = sub["items"]["data"][0]["id"]

        proration_map = {
            ProrationBehavior.CREATE_PRORATIONS: "create_prorations",
            ProrationBehavior.NONE: "none",
            ProrationBehavior.ALWAYS_INVOICE: "always_invoice",
        }

        data: dict[str, Any] = {
            "items[0][id]": item_id,
            "items[0][price]": new_plan_provider_ref.external_id,
            "proration_behavior": proration_map.get(
                request.proration_behavior, "create_prorations"
            ),
        }

        result = await self._request(
            "POST",
            f"/subscriptionkores/{subscriptionkore_provider_ref.external_id}",
            data=data,
        )

        return self._map_subscriptionkore(result, "", request.new_plan_id)

    async def preview_plan_change(
        self,
        request: ChangePlanRequest,
        subscriptionkore_provider_ref: ProviderReference,
        new_plan_provider_ref: ProviderReference,
    ) -> ChangePreview:
        # Get current subscriptionkore
        sub = await self._request(
            "GET",
            f"/subscriptionkores/{subscriptionkore_provider_ref.external_id}",
        )

        item_id = sub["items"]["data"][0]["id"]

        # Create upcoming invoice preview
        result = await self._request(
            "GET",
            "/invoices/upcoming",
            params={
                "subscriptionkore": subscriptionkore_provider_ref.external_id,
                "subscriptionkore_items[0][id]": item_id,
                "subscriptionkore_items[0][price]": new_plan_provider_ref.external_id,
                "subscriptionkore_proration_behavior": "create_prorations",
            },
        )

        currency = Currency(result.get("currency", "usd").upper())

        # Calculate proration from line items
        proration_amount = Decimal("0")
        credit_amount = Decimal("0")

        for line in result.get("lines", {}).get("data", []):
            if line.get("proration"):
                amount = Decimal(line["amount"]) / 100
                if amount < 0:
                    credit_amount += abs(amount)
                else:
                    proration_amount += amount

        return ChangePreview(
            immediate_charge=Money.from_cents(result.get("amount_due", 0), currency),
            next_invoice_amount=Money.from_cents(result.get("total", 0), currency),
            proration_amount=Money(amount=proration_amount, currency=currency),
            credit_amount=Money(amount=credit_amount, currency=currency),
            next_billing_date=datetime.fromtimestamp(result.get("next_payment_attempt", 0)),
        )

    # Discount Operations

    async def apply_discount(
        self,
        subscriptionkore_provider_ref: ProviderReference,
        discount: DiscountRequest,
    ) -> Subscription:
        data: dict[str, Any] = {}

        if discount.coupon_code:
            data["coupon"] = discount.coupon_code
        elif discount.promotion_code:
            data["promotion_code"] = discount.promotion_code

        result = await self._request(
            "POST",
            f"/subscriptionkores/{subscriptionkore_provider_ref.external_id}",
            data=data,
        )

        return self._map_subscriptionkore(result, "", "")

    async def remove_discount(
        self,
        subscriptionkore_provider_ref: ProviderReference,
    ) -> Subscription:
        await self._request(
            "DELETE",
            f"/subscriptionkores/{subscriptionkore_provider_ref.external_id}/discount",
        )

        result = await self._request(
            "GET",
            f"/subscriptionkores/{subscriptionkore_provider_ref.external_id}",
        )

        return self._map_subscriptionkore(result, "", "")

    # Billing Operations

    async def get_invoice(self, provider_ref: ProviderReference) -> Invoice:
        result = await self._request("GET", f"/invoices/{provider_ref.external_id}")
        return self._map_invoice(result)

    async def list_invoices(
        self,
        customer_provider_ref: ProviderReference,
        limit: int = 10,
        starting_after: str | None = None,
    ) -> list[Invoice]:
        params: dict[str, Any] = {
            "customer": customer_provider_ref.external_id,
            "limit": limit,
        }

        if starting_after:
            params["starting_after"] = starting_after

        result = await self._request("GET", "/invoices", params=params)

        return [self._map_invoice(inv) for inv in result.get("data", [])]

    async def get_upcoming_invoice(
        self,
        subscriptionkore_provider_ref: ProviderReference,
    ) -> Invoice | None:
        try:
            result = await self._request(
                "GET",
                "/invoices/upcoming",
                params={"subscriptionkore": subscriptionkore_provider_ref.external_id},
            )
            return self._map_invoice(result)
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
            "mode": "subscriptionkore",
            "success_url": request.success_url,
            "cancel_url": request.cancel_url,
            "line_items[0][price]": plan_provider_ref.external_id,
            "line_items[0][quantity]": str(request.quantity),
        }

        if customer_provider_ref:
            data["customer"] = customer_provider_ref.external_id
        elif request.customer_email:
            data["customer_email"] = request.customer_email

        if request.trial_period_days:
            data["subscriptionkore_data[trial_period_days]"] = str(request.trial_period_days)

        if request.allow_promotion_codes:
            data["allow_promotion_codes"] = "true"

        for key, value in request.metadata.items():
            data[f"metadata[{key}]"] = str(value)

        result = await self._request("POST", "/checkout/sessions", data=data)

        return CheckoutSession(
            id=result["id"],
            url=result["url"],
            expires_at=datetime.fromtimestamp(result["expires_at"]),
        )

    async def create_portal_session(
        self,
        customer_provider_ref: ProviderReference,
        return_url: str,
    ) -> PortalSession:
        result = await self._request(
            "POST",
            "/billing_portal/sessions",
            data={
                "customer": customer_provider_ref.external_id,
                "return_url": return_url,
            },
        )

        return PortalSession(
            id=result["id"],
            url=result["url"],
        )

    # Webhook Handling

    async def verify_webhook(
        self,
        payload: bytes,
        headers: dict[str, str],
    ) -> bool:
        """Verify Stripe webhook signature."""
        import hashlib
        import hmac
        import time

        signature_header = headers.get("stripe-signature", "")
        if not signature_header:
            return False

        # Parse the signature header
        elements = dict(item.split("=", 1) for item in signature_header.split(",") if "=" in item)
        timestamp = elements.get("t", "")
        signatures = [v for k, v in elements.items() if k.startswith("v1")]

        if not timestamp or not signatures:
            return False

        # Check timestamp (within 5 minutes)
        try:
            ts = int(timestamp)
            if abs(time.time() - ts) > 300:
                return False
        except ValueError:
            return False

        # Compute expected signature
        signed_payload = f"{timestamp}. {payload.decode('utf-8')}"
        expected_sig = hmac.new(
            self._config.webhook_secret.encode("utf-8"),
            signed_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        # Compare signatures
        return any(hmac.compare_digest(expected_sig, sig) for sig in signatures)

    async def parse_webhook(
        self,
        payload: bytes,
        headers: dict[str, str],
    ) -> ProviderWebhookEvent:
        """Parse Stripe webhook payload."""
        import json

        data = json.loads(payload)

        return ProviderWebhookEvent(
            provider=ProviderType.STRIPE,
            event_id=data["id"],
            event_type=data["type"],
            occurred_at=datetime.fromtimestamp(data["created"]),
            data=data.get("data", {}),
            raw_payload=payload,
        )

    # Sync Operations

    async def sync_products(self) -> list[Product]:
        result = await self._request("GET", "/products", params={"limit": 100, "active": "true"})

        products = []
        for prod in result.get("data", []):
            products.append(
                Product(
                    id="",  # Will be assigned by repository
                    name=prod["name"],
                    description=prod.get("description"),
                    provider_refs=[
                        ProviderReference(
                            provider=ProviderType.STRIPE,
                            external_id=prod["id"],
                        )
                    ],
                    active=prod["active"],
                    metadata=prod.get("metadata", {}),
                    created_at=datetime.fromtimestamp(prod["created"]),
                )
            )

        return products

    async def sync_plans(self, product_provider_ref: ProviderReference) -> list[Plan]:
        result = await self._request(
            "GET",
            "/prices",
            params={
                "product": product_provider_ref.external_id,
                "limit": 100,
                "active": "true",
            },
        )

        plans = []
        for price in result.get("data", []):
            if price.get("type") != "recurring":
                continue

            recurring = price.get("recurring", {})
            interval = recurring.get("interval", "month")
            interval_count = recurring.get("interval_count", 1)

            plans.append(
                Plan(
                    id="",  # Will be assigned by repository
                    product_id="",  # Will be resolved
                    name=price.get("nickname") or price["id"],
                    provider_refs=[
                        ProviderReference(
                            provider=ProviderType.STRIPE,
                            external_id=price["id"],
                        )
                    ],
                    price=Money.from_cents(
                        price.get("unit_amount", 0),
                        Currency(price.get("currency", "usd").upper()),
                    ),
                    billing_period=BillingPeriod(
                        interval=Interval(interval),
                        interval_count=interval_count,
                    ),
                    trial_period_days=recurring.get("trial_period_days"),
                    active=price["active"],
                    metadata=price.get("metadata", {}),
                    created_at=datetime.fromtimestamp(price["created"]),
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
        """Map Stripe subscriptionkore to domain model."""
        status = self.STATUS_MAP.get(data["status"], SubscriptionStatus.ACTIVE)

        # Handle pause collection
        pause_config = None
        pause_data = data.get("pause_collection")
        if pause_data:
            resumes_at = None
            if pause_data.get("resumes_at"):
                resumes_at = datetime.fromtimestamp(pause_data["resumes_at"])
            pause_config = PauseConfig(
                resumes_at=resumes_at,
                behavior=PauseBehavior.VOID,
            )
            status = SubscriptionStatus.PAUSED

        # Handle discount
        discount = None
        discount_data = data.get("discount")
        if discount_data:
            coupon = discount_data.get("coupon", {})
            discount = AppliedDiscount(
                discount_id=discount_data["id"],
                coupon_code=coupon.get("id"),
                amount_off=Money.from_cents(coupon["amount_off"], Currency.USD)
                if coupon.get("amount_off")
                else None,
                percent_off=Decimal(str(coupon["percent_off"]))
                if coupon.get("percent_off")
                else None,
                valid_until=datetime.fromtimestamp(discount_data["end"])
                if discount_data.get("end")
                else None,
            )

        # Get quantity from items
        quantity = 1
        items = data.get("items", {}).get("data", [])
        if items:
            quantity = items[0].get("quantity", 1)

        # Get trial end
        trial_end = None
        if data.get("trial_end"):
            trial_end = datetime.fromtimestamp(data["trial_end"])

        # Use metadata for internal IDs if not provided
        metadata = data.get("metadata", {})
        resolved_customer_id = customer_id or metadata.get("subscriptionkore_customer_id", "")
        resolved_plan_id = plan_id or metadata.get("subscriptionkore_plan_id", "")

        return Subscription(
            id="",  # Will be assigned
            customer_id=resolved_customer_id,
            plan_id=resolved_plan_id,
            provider_ref=ProviderReference(
                provider=ProviderType.STRIPE,
                external_id=data["id"],
                metadata={"customer": data.get("customer")},
            ),
            status=status,
            current_period=DateRange(
                start=datetime.fromtimestamp(data["current_period_start"]),
                end=datetime.fromtimestamp(data["current_period_end"]),
            ),
            trial_end=trial_end,
            cancel_at_period_end=data.get("cancel_at_period_end", False),
            canceled_at=datetime.fromtimestamp(data["canceled_at"])
            if data.get("canceled_at")
            else None,
            ended_at=datetime.fromtimestamp(data["ended_at"]) if data.get("ended_at") else None,
            pause_collection=pause_config,
            discount=discount,
            quantity=quantity,
            metadata=metadata,
            created_at=datetime.fromtimestamp(data["created"]),
        )

    def _map_invoice(self, data: dict[str, Any]) -> Invoice:
        """Map Stripe invoice to domain model."""
        currency = Currency(data.get("currency", "usd").upper())
        status = self.INVOICE_STATUS_MAP.get(data.get("status", "draft"), InvoiceStatus.DRAFT)

        # Map line items
        line_items = []
        for line in data.get("lines", {}).get("data", []):
            period = None
            if line.get("period"):
                period = DateRange(
                    start=datetime.fromtimestamp(line["period"]["start"]),
                    end=datetime.fromtimestamp(line["period"]["end"]),
                )

            line_items.append(
                InvoiceLineItem(
                    id=line["id"],
                    description=line.get("description", ""),
                    quantity=line.get("quantity", 1),
                    unit_amount=Money.from_cents(line.get("unit_amount", 0), currency),
                    amount=Money.from_cents(line.get("amount", 0), currency),
                    period=period,
                    proration=line.get("proration", False),
                )
            )

        # Build period from line items or invoice dates
        period = None
        if data.get("period_start") and data.get("period_end"):
            period = DateRange(
                start=datetime.fromtimestamp(data["period_start"]),
                end=datetime.fromtimestamp(data["period_end"]),
            )

        return Invoice(
            id="",  # Will be assigned
            customer_id="",  # Will be resolved
            subscriptionkore_id=data.get("subscriptionkore"),
            provider_ref=ProviderReference(
                provider=ProviderType.STRIPE,
                external_id=data.get("id", ""),
            ),
            status=status,
            subtotal=Money.from_cents(data.get("subtotal", 0), currency),
            tax=Money.from_cents(data.get("tax", 0) or 0, currency),
            discount_amount=Money.from_cents(
                data.get("total_discount_amounts", [{}])[0].get("amount", 0)
                if data.get("total_discount_amounts")
                else 0,
                currency,
            ),
            total=Money.from_cents(data.get("total", 0), currency),
            amount_paid=Money.from_cents(data.get("amount_paid", 0), currency),
            amount_due=Money.from_cents(data.get("amount_due", 0), currency),
            currency=currency,
            line_items=line_items,
            period=period,
            due_date=datetime.fromtimestamp(data["due_date"]) if data.get("due_date") else None,
            paid_at=datetime.fromtimestamp(data["status_transitions"]["paid_at"])
            if data.get("status_transitions", {}).get("paid_at")
            else None,
            invoice_pdf_url=data.get("invoice_pdf"),
            hosted_invoice_url=data.get("hosted_invoice_url"),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromtimestamp(data["created"]),
        )
