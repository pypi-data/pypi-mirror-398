"""Chargebee payment provider adapter."""

from __future__ import annotations

import base64
import json
from datetime import datetime
from decimal import Decimal
from typing import Any
from urllib.parse import urlencode

import httpx
import structlog
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from subscriptionkore.config import ChargebeeConfig
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


class ChargebeeAdapter(PaymentProviderPort):
    """
    Chargebee payment provider implementation.

    Implements the Chargebee API for subscriptionkore management.
    Reference: https://apidocs.eu.chargebee. com/docs/api/
    """

    STATUS_MAP = {
        "in_trial": SubscriptionStatus.TRIALING,
        "active": SubscriptionStatus.ACTIVE,
        "non_renewing": SubscriptionStatus.ACTIVE,
        "paused": SubscriptionStatus.PAUSED,
        "cancelled": SubscriptionStatus.CANCELED,
        "future": SubscriptionStatus.INCOMPLETE,
    }

    INVOICE_STATUS_MAP = {
        "paid": InvoiceStatus.PAID,
        "posted": InvoiceStatus.OPEN,
        "payment_due": InvoiceStatus.OPEN,
        "not_paid": InvoiceStatus.OPEN,
        "voided": InvoiceStatus.VOID,
        "pending": InvoiceStatus.DRAFT,
    }

    def __init__(self, config: ChargebeeConfig) -> None:
        self._config = config
        self._client: httpx.AsyncClient | None = None
        self._base_url = f"https://{config.site}. chargebee.com/api/v2"

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            auth_string = base64.b64encode(f"{self._config.api_key}:".encode("utf-8")).decode(
                "utf-8"
            )

            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                headers={
                    "Authorization": f"Basic {auth_string}",
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
        return ProviderType.CHARGEBEE

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
        """Handle Chargebee API errors."""
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise ProviderRateLimitError(
                provider="chargebee",
                retry_after=int(retry_after) if retry_after else None,
            )

        if response.status_code == 401:
            raise ProviderAuthenticationError(provider="chargebee")

        if response.status_code >= 400:
            try:
                error_data = response.json()
                raise ProviderAPIError(
                    message=error_data.get("message", "Unknown Chargebee error"),
                    provider="chargebee",
                    status_code=response.status_code,
                    provider_message=error_data.get("message"),
                    provider_code=error_data.get("error_code"),
                )
            except json.JSONDecodeError:
                raise ProviderAPIError(
                    message=f"Chargebee API error: {response.status_code}",
                    provider="chargebee",
                    status_code=response.status_code,
                )

    def _flatten_params(self, data: dict[str, Any], prefix: str = "") -> dict[str, str]:
        """Flatten nested dict to Chargebee's format:  customer[email] = value."""
        result: dict[str, str] = {}
        for key, value in data.items():
            full_key = f"{prefix}[{key}]" if prefix else key
            if isinstance(value, dict):
                result.update(self._flatten_params(value, full_key))
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        result.update(self._flatten_params(item, f"{full_key}[{i}]"))
                    else:
                        result[f"{full_key}[{i}]"] = str(item)
            elif value is not None:
                result[full_key] = str(value)
        return result

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
        """Make authenticated request to Chargebee API."""
        client = await self._get_client()

        try:
            encoded_data = None
            if data:
                flat_data = self._flatten_params(data)
                encoded_data = urlencode(flat_data)

            response = await client.request(
                method=method,
                url=endpoint,
                content=encoded_data,
                params=params,
            )
        except httpx.NetworkError as e:
            raise ProviderNetworkError(provider="chargebee", original_error=e) from e

        self._handle_error(response)
        return response.json()

    # Customer Operations

    async def create_customer(self, customer: Customer) -> ProviderReference:
        data: dict[str, Any] = {
            "email": customer.email,
            "cf_subscriptionkore_id": customer.id,
            "cf_external_id": customer.external_id,
        }

        if customer.name:
            parts = customer.name.split(" ", 1)
            data["first_name"] = parts[0]
            if len(parts) > 1:
                data["last_name"] = parts[1]

        if customer.billing_address:
            addr = customer.billing_address
            data["billing_address"] = {
                "line1": addr.line1,
                "line2": addr.line2,
                "city": addr.city,
                "state": addr.state,
                "zip": addr.postal_code,
                "country": addr.country,
            }

        result = await self._request("POST", "/customers", data=data)
        customer_data = result.get("customer", {})

        return ProviderReference(
            provider=ProviderType.CHARGEBEE,
            external_id=customer_data["id"],
            metadata={"email": customer_data.get("email")},
        )

    async def update_customer(self, customer: Customer) -> None:
        provider_ref = customer.get_provider_ref("chargebee")
        if provider_ref is None:
            raise ProviderAPIError(
                message="Customer has no Chargebee reference",
                provider="chargebee",
                status_code=400,
            )

        data: dict[str, Any] = {"email": customer.email}

        if customer.name:
            parts = customer.name.split(" ", 1)
            data["first_name"] = parts[0]
            if len(parts) > 1:
                data["last_name"] = parts[1]

        await self._request("POST", f"/customers/{provider_ref.external_id}", data=data)

    async def delete_customer(self, provider_ref: ProviderReference) -> None:
        await self._request("POST", f"/customers/{provider_ref.external_id}/delete")

    async def get_customer(self, provider_ref: ProviderReference) -> Customer:
        result = await self._request("GET", f"/customers/{provider_ref.external_id}")
        data = result.get("customer", {})

        name = None
        if data.get("first_name") or data.get("last_name"):
            name = f"{data.get('first_name', '')} {data.get('last_name', '')}".strip()

        address = None
        billing = data.get("billing_address", {})
        if billing:
            address = Address(
                line1=billing.get("line1"),
                line2=billing.get("line2"),
                city=billing.get("city"),
                state=billing.get("state"),
                postal_code=billing.get("zip"),
                country=billing.get("country"),
            )

        return Customer(
            id=data.get("cf_subscriptionkore_id", ""),
            external_id=data.get("cf_external_id", ""),
            email=data.get("email", ""),
            name=name,
            billing_address=address,
            provider_refs=[provider_ref],
            created_at=datetime.fromtimestamp(data.get("created_at", 0)),
        )

    # Subscription Operations

    async def create_subscriptionkore(
        self,
        request: CreateSubscriptionRequest,
        customer_provider_ref: ProviderReference,
        plan_provider_ref: ProviderReference,
    ) -> Subscription:
        data: dict[str, Any] = {
            "plan_id": plan_provider_ref.external_id,
            "plan_quantity": request.quantity,
            "cf_subscriptionkore_customer_id": request.customer_id,
            "cf_subscriptionkore_plan_id": request.plan_id,
        }

        if request.trial_period_days:
            data["trial_end"] = int(
                (datetime.utcnow().timestamp()) + (request.trial_period_days * 86400)
            )

        if request.coupon_code:
            data["coupon_ids"] = [request.coupon_code]

        for key, value in request.metadata.items():
            data[f"cf_{key}"] = str(value)

        result = await self._request(
            "POST",
            f"/customers/{customer_provider_ref.external_id}/subscriptionkores",
            data=data,
        )

        return self._map_subscriptionkore(
            result.get("subscriptionkore", {}),
            result.get("customer", {}),
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
            data["plan_quantity"] = request.quantity

        if request.cancel_at_period_end is not None:
            if request.cancel_at_period_end:
                result = await self._request(
                    "POST",
                    f"/subscriptionkores/{subscriptionkore_provider_ref.external_id}/cancel_for_items",
                    data={"end_of_term": True},
                )
            else:
                result = await self._request(
                    "POST",
                    f"/subscriptionkores/{subscriptionkore_provider_ref.external_id}/remove_scheduled_cancellation",
                )
            return self._map_subscriptionkore(result.get("subscriptionkore", {}), {}, "", "")

        if request.metadata:
            for key, value in request.metadata.items():
                data[f"cf_{key}"] = str(value)

        result = await self._request(
            "POST",
            f"/subscriptionkores/{subscriptionkore_provider_ref.external_id}",
            data=data,
        )

        return self._map_subscriptionkore(result.get("subscriptionkore", {}), {}, "", "")

    async def cancel_subscriptionkore(
        self,
        subscriptionkore_provider_ref: ProviderReference,
        immediate: bool = False,
    ) -> Subscription:
        result = await self._request(
            "POST",
            f"/subscriptionkores/{subscriptionkore_provider_ref.external_id}/cancel_for_items",
            data={"end_of_term": not immediate},
        )

        return self._map_subscriptionkore(result.get("subscriptionkore", {}), {}, "", "")

    async def pause_subscriptionkore(
        self,
        subscriptionkore_provider_ref: ProviderReference,
        resumes_at: datetime | None = None,
    ) -> Subscription:
        data: dict[str, Any] = {}

        if resumes_at:
            data["resume_date"] = int(resumes_at.timestamp())

        result = await self._request(
            "POST",
            f"/subscriptionkores/{subscriptionkore_provider_ref.external_id}/pause",
            data=data,
        )

        return self._map_subscriptionkore(result.get("subscriptionkore", {}), {}, "", "")

    async def resume_subscriptionkore(
        self,
        subscriptionkore_provider_ref: ProviderReference,
    ) -> Subscription:
        result = await self._request(
            "POST",
            f"/subscriptionkores/{subscriptionkore_provider_ref.external_id}/resume",
        )

        return self._map_subscriptionkore(result.get("subscriptionkore", {}), {}, "", "")

    async def get_subscriptionkore(
        self,
        provider_ref: ProviderReference,
    ) -> Subscription:
        result = await self._request("GET", f"/subscriptionkores/{provider_ref.external_id}")
        return self._map_subscriptionkore(result.get("subscriptionkore", {}), {}, "", "")

    # Plan Change Operations

    async def change_plan(
        self,
        request: ChangePlanRequest,
        subscriptionkore_provider_ref: ProviderReference,
        new_plan_provider_ref: ProviderReference,
    ) -> Subscription:
        proration_map = {
            ProrationBehavior.CREATE_PRORATIONS: True,
            ProrationBehavior.NONE: False,
            ProrationBehavior.ALWAYS_INVOICE: True,
        }

        data = {
            "subscriptionkore_items": {
                "item_price_id": {0: new_plan_provider_ref.external_id},
                "quantity": {0: 1},
            },
            "prorate": proration_map.get(request.proration_behavior, True),
        }

        result = await self._request(
            "POST",
            f"/subscriptionkores/{subscriptionkore_provider_ref.external_id}/update_for_items",
            data=data,
        )

        return self._map_subscriptionkore(
            result.get("subscriptionkore", {}),
            {},
            "",
            request.new_plan_id,
        )

    async def preview_plan_change(
        self,
        request: ChangePlanRequest,
        subscriptionkore_provider_ref: ProviderReference,
        new_plan_provider_ref: ProviderReference,
    ) -> ChangePreview:
        data = {
            "subscriptionkore": {"id": subscriptionkore_provider_ref.external_id},
            "subscriptionkore_items": {
                "item_price_id": {0: new_plan_provider_ref.external_id},
                "quantity": {0: 1},
            },
            "replace_items_list": True,
        }

        result = await self._request(
            "POST", "/estimates/update_subscriptionkore_for_items", data=data
        )
        estimate = result.get("estimate", {})
        invoice_estimate = estimate.get("invoice_estimate", {})

        currency = Currency(invoice_estimate.get("currency_code", "USD"))

        return ChangePreview(
            immediate_charge=Money(
                amount=Decimal(str(invoice_estimate.get("amount_due", 0))) / 100,
                currency=currency,
            ),
            next_invoice_amount=Money(
                amount=Decimal(str(invoice_estimate.get("total", 0))) / 100,
                currency=currency,
            ),
            proration_amount=Money(
                amount=Decimal(str(invoice_estimate.get("credits_applied", 0))) / 100,
                currency=currency,
            ),
            credit_amount=Money.zero(currency),
            next_billing_date=datetime.fromtimestamp(
                estimate.get("next_invoice_estimate", {}).get("date", 0)
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
            data["coupon_ids"] = [discount.coupon_code]

        result = await self._request(
            "POST",
            f"/subscriptionkores/{subscriptionkore_provider_ref.external_id}",
            data=data,
        )

        return self._map_subscriptionkore(result.get("subscriptionkore", {}), {}, "", "")

    async def remove_discount(
        self,
        subscriptionkore_provider_ref: ProviderReference,
    ) -> Subscription:
        sub_result = await self._request(
            "GET",
            f"/subscriptionkores/{subscriptionkore_provider_ref.external_id}",
        )
        sub = sub_result.get("subscriptionkore", {})
        coupons = sub.get("coupons", [])

        for coupon in coupons:
            await self._request(
                "POST",
                f"/subscriptionkores/{subscriptionkore_provider_ref.external_id}/remove_coupons",
                data={"coupon_ids": [coupon.get("coupon_id")]},
            )

        result = await self._request(
            "GET",
            f"/subscriptionkores/{subscriptionkore_provider_ref.external_id}",
        )

        return self._map_subscriptionkore(result.get("subscriptionkore", {}), {}, "", "")

    # Billing Operations

    async def get_invoice(self, provider_ref: ProviderReference) -> Invoice:
        result = await self._request("GET", f"/invoices/{provider_ref.external_id}")
        return self._map_invoice(result.get("invoice", {}))

    async def list_invoices(
        self,
        customer_provider_ref: ProviderReference,
        limit: int = 10,
        starting_after: str | None = None,
    ) -> list[Invoice]:
        params: dict[str, Any] = {
            "customer_id[is]": customer_provider_ref.external_id,
            "limit": limit,
            "sort_by[desc]": "date",
        }

        if starting_after:
            params["offset"] = starting_after

        result = await self._request("GET", "/invoices", params=params)

        return [self._map_invoice(item.get("invoice", {})) for item in result.get("list", [])]

    async def get_upcoming_invoice(
        self,
        subscriptionkore_provider_ref: ProviderReference,
    ) -> Invoice | None:
        try:
            result = await self._request(
                "POST",
                "/estimates/upcoming_invoices_estimate",
                data={"subscriptionkore_id": subscriptionkore_provider_ref.external_id},
            )
            estimates = result.get("estimate", {}).get("invoice_estimates", [])
            if estimates:
                return self._map_estimate_to_invoice(estimates[0])
            return None
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
            "subscriptionkore_items": {
                "item_price_id": {0: plan_provider_ref.external_id},
                "quantity": {0: request.quantity},
            },
            "redirect_url": request.success_url,
            "cancel_url": request.cancel_url,
        }

        if customer_provider_ref:
            data["customer"] = {"id": customer_provider_ref.external_id}
        elif request.customer_email:
            data["customer"] = {"email": request.customer_email}

        if request.trial_period_days:
            data["subscriptionkore"] = {
                "trial_end": int(
                    datetime.utcnow().timestamp() + (request.trial_period_days * 86400)
                )
            }

        for key, value in request.metadata.items():
            data[f"cf_{key}"] = str(value)

        result = await self._request("POST", "/hosted_pages/checkout_new_for_items", data=data)
        hosted_page = result.get("hosted_page", {})

        return CheckoutSession(
            id=hosted_page["id"],
            url=hosted_page["url"],
            expires_at=datetime.fromtimestamp(hosted_page.get("expires_at", 0)),
        )

    async def create_portal_session(
        self,
        customer_provider_ref: ProviderReference,
        return_url: str,
    ) -> PortalSession:
        result = await self._request(
            "POST",
            "/portal_sessions",
            data={
                "customer": {"id": customer_provider_ref.external_id},
                "redirect_url": return_url,
            },
        )
        portal = result.get("portal_session", {})

        return PortalSession(
            id=portal["id"],
            url=portal["access_url"],
            expires_at=datetime.fromtimestamp(portal.get("expires_at", 0)),
        )

    # Webhook Handling

    async def verify_webhook(
        self,
        payload: bytes,
        headers: dict[str, str],
    ) -> bool:
        """Verify Chargebee webhook using basic auth."""
        if self._config.webhook_username and self._config.webhook_password:
            auth_header = headers.get("authorization", "")
            if auth_header.startswith("Basic "):
                try:
                    encoded = auth_header[6:]
                    decoded = base64.b64decode(encoded).decode("utf-8")
                    username, password = decoded.split(":", 1)
                    return (
                        username == self._config.webhook_username
                        and password == self._config.webhook_password
                    )
                except Exception:
                    return False
            return False

        logger.warning("Chargebee webhook received without authentication configured")
        return True

    async def parse_webhook(
        self,
        payload: bytes,
        headers: dict[str, str],
    ) -> ProviderWebhookEvent:
        """Parse Chargebee webhook payload."""
        data = json.loads(payload)

        return ProviderWebhookEvent(
            provider=ProviderType.CHARGEBEE,
            event_id=data.get("id", ""),
            event_type=data.get("event_type", ""),
            occurred_at=datetime.fromtimestamp(data.get("occurred_at", 0)),
            data=data.get("content", {}),
            raw_payload=payload,
        )

    # Sync Operations

    async def sync_products(self) -> list[Product]:
        result = await self._request("GET", "/item_families")

        products = []
        for item in result.get("list", []):
            family = item.get("item_family", {})
            products.append(
                Product(
                    id="",
                    name=family.get("name", ""),
                    description=family.get("description"),
                    provider_refs=[
                        ProviderReference(
                            provider=ProviderType.CHARGEBEE,
                            external_id=family["id"],
                        )
                    ],
                    active=family.get("status") == "active",
                    metadata={},
                    created_at=datetime.utcnow(),
                )
            )

        return products

    async def sync_plans(self, product_provider_ref: ProviderReference) -> list[Plan]:
        result = await self._request(
            "GET",
            "/item_prices",
            params={"item_family_id[is]": product_provider_ref.external_id},
        )

        plans = []
        for item in result.get("list", []):
            price = item.get("item_price", {})

            period_unit = price.get("period_unit", "month")
            period_map = {
                "day": Interval.DAY,
                "week": Interval.WEEK,
                "month": Interval.MONTH,
                "year": Interval.YEAR,
            }

            plans.append(
                Plan(
                    id="",
                    product_id="",
                    name=price.get("name", price.get("id", "")),
                    description=price.get("description"),
                    provider_refs=[
                        ProviderReference(
                            provider=ProviderType.CHARGEBEE,
                            external_id=price["id"],
                        )
                    ],
                    price=Money(
                        amount=Decimal(str(price.get("price", 0))) / 100,
                        currency=Currency(price.get("currency_code", "USD")),
                    ),
                    billing_period=BillingPeriod(
                        interval=period_map.get(period_unit, Interval.MONTH),
                        interval_count=price.get("period", 1),
                    ),
                    trial_period_days=price.get("trial_period"),
                    active=price.get("status") == "active",
                    metadata={},
                    created_at=datetime.utcnow(),
                )
            )

        return plans

    # Mapping Helpers

    def _map_subscriptionkore(
        self,
        data: dict[str, Any],
        customer_data: dict[str, Any],
        customer_id: str,
        plan_id: str,
    ) -> Subscription:
        """Map Chargebee subscriptionkore to domain model."""
        status = self.STATUS_MAP.get(data.get("status", "active"), SubscriptionStatus.ACTIVE)

        # Handle pause
        pause_config = None
        if data.get("pause_date"):
            pause_config = PauseConfig(
                resumes_at=datetime.fromtimestamp(data["resume_date"])
                if data.get("resume_date")
                else None,
                behavior=PauseBehavior.VOID,
            )

        # Handle discount
        discount = None
        coupons = data.get("coupons", [])
        if coupons:
            coupon = coupons[0]
            discount = AppliedDiscount(
                discount_id=coupon.get("coupon_id", ""),
                coupon_code=coupon.get("coupon_code"),
            )

        # Get trial end
        trial_end = None
        if data.get("trial_end"):
            trial_end = datetime.fromtimestamp(data["trial_end"])

        # Get current period
        current_term_start = data.get("current_term_start", 0)
        current_term_end = data.get("current_term_end")

        # Use custom fields for internal IDs
        resolved_customer_id = customer_id or data.get("cf_subscriptionkore_customer_id", "")
        resolved_plan_id = plan_id or data.get("cf_subscriptionkore_plan_id", "")

        return Subscription(
            id="",
            customer_id=resolved_customer_id,
            plan_id=resolved_plan_id,
            provider_ref=ProviderReference(
                provider=ProviderType.CHARGEBEE,
                external_id=data["id"],
                metadata={"customer_id": data.get("customer_id")},
            ),
            status=status,
            current_period=DateRange(
                start=datetime.fromtimestamp(current_term_start)
                if current_term_start
                else datetime.utcnow(),
                end=datetime.fromtimestamp(current_term_end) if current_term_end else None,
            ),
            trial_end=trial_end,
            cancel_at_period_end=data.get("cancel_schedule_created_at") is not None,
            canceled_at=datetime.fromtimestamp(data["cancelled_at"])
            if data.get("cancelled_at")
            else None,
            pause_collection=pause_config,
            discount=discount,
            quantity=data.get("plan_quantity", 1),
            metadata={},
            created_at=datetime.fromtimestamp(data.get("created_at", 0)),
        )

    def _map_invoice(self, data: dict[str, Any]) -> Invoice:
        """Map Chargebee invoice to domain model."""
        currency = Currency(data.get("currency_code", "USD"))
        status = self.INVOICE_STATUS_MAP.get(data.get("status", "posted"), InvoiceStatus.OPEN)

        # Map line items
        line_items = []
        for item in data.get("line_items", []):
            line_items.append(
                InvoiceLineItem(
                    id=item.get("id", ""),
                    description=item.get("description", ""),
                    quantity=item.get("quantity", 1),
                    unit_amount=Money(
                        amount=Decimal(str(item.get("unit_amount", 0))) / 100,
                        currency=currency,
                    ),
                    amount=Money(
                        amount=Decimal(str(item.get("amount", 0))) / 100,
                        currency=currency,
                    ),
                )
            )

        # Build period
        period = None
        if data.get("line_items"):
            first_item = data["line_items"][0]
            if first_item.get("date_from") and first_item.get("date_to"):
                period = DateRange(
                    start=datetime.fromtimestamp(first_item["date_from"]),
                    end=datetime.fromtimestamp(first_item["date_to"]),
                )

        return Invoice(
            id="",
            customer_id=data.get("customer_id", ""),
            subscriptionkore_id=data.get("subscriptionkore_id"),
            provider_ref=ProviderReference(
                provider=ProviderType.CHARGEBEE,
                external_id=data.get("id", ""),
            ),
            status=status,
            subtotal=Money(
                amount=Decimal(str(data.get("sub_total", 0))) / 100,
                currency=currency,
            ),
            tax=Money(
                amount=Decimal(str(data.get("tax", 0))) / 100,
                currency=currency,
            ),
            discount_amount=Money(
                amount=Decimal(str(data.get("discounts", [{}])[0].get("amount", 0))) / 100
                if data.get("discounts")
                else Decimal("0"),
                currency=currency,
            ),
            total=Money(
                amount=Decimal(str(data.get("total", 0))) / 100,
                currency=currency,
            ),
            amount_paid=Money(
                amount=Decimal(str(data.get("amount_paid", 0))) / 100,
                currency=currency,
            ),
            amount_due=Money(
                amount=Decimal(str(data.get("amount_due", 0))) / 100,
                currency=currency,
            ),
            currency=currency,
            line_items=line_items,
            period=period,
            due_date=datetime.fromtimestamp(data["due_date"]) if data.get("due_date") else None,
            paid_at=datetime.fromtimestamp(data["paid_at"]) if data.get("paid_at") else None,
            invoice_pdf_url=data.get("download_url"),
            metadata={},
            created_at=datetime.fromtimestamp(data.get("date", 0)),
        )

    def _map_estimate_to_invoice(self, data: dict[str, Any]) -> Invoice:
        """Map Chargebee invoice estimate to Invoice domain model."""
        currency = Currency(data.get("currency_code", "USD"))

        return Invoice(
            id="",
            customer_id="",
            subscriptionkore_id="",
            provider_ref=ProviderReference(
                provider=ProviderType.CHARGEBEE,
                external_id="estimate",
            ),
            status=InvoiceStatus.DRAFT,
            subtotal=Money(
                amount=Decimal(str(data.get("sub_total", 0))) / 100,
                currency=currency,
            ),
            tax=Money(
                amount=Decimal(str(data.get("tax", 0))) / 100,
                currency=currency,
            ),
            discount_amount=Money.zero(currency),
            total=Money(
                amount=Decimal(str(data.get("total", 0))) / 100,
                currency=currency,
            ),
            amount_paid=Money.zero(currency),
            amount_due=Money(
                amount=Decimal(str(data.get("total", 0))) / 100,
                currency=currency,
            ),
            currency=currency,
            line_items=[],
            due_date=datetime.fromtimestamp(data["date"]) if data.get("date") else None,
            metadata={},
            created_at=datetime.utcnow(),
        )
