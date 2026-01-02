"""LemonSqueezy payment provider adapter."""

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

from subscriptionkore.config import LemonSqueezyConfig
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
    ProviderCapabilities,
    ProviderWebhookEvent,
    UpdateSubscriptionRequest,
)

logger = structlog.get_logger()


class LemonSqueezyAdapter(PaymentProviderPort):
    """
    LemonSqueezy payment provider implementation.

    Implements the LemonSqueezy API for subscriptionkore management.
    Reference: https://docs.lemonsqueezy.com/api
    """

    BASE_URL = "https://api.lemonsqueezy.com/v1"

    STATUS_MAP = {
        "on_trial": SubscriptionStatus.TRIALING,
        "active": SubscriptionStatus.ACTIVE,
        "paused": SubscriptionStatus.PAUSED,
        "past_due": SubscriptionStatus.PAST_DUE,
        "unpaid": SubscriptionStatus.UNPAID,
        "cancelled": SubscriptionStatus.CANCELED,
        "expired": SubscriptionStatus.EXPIRED,
    }

    def __init__(self, config: LemonSqueezyConfig) -> None:
        self._config = config
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers={
                    "Authorization": f"Bearer {self._config.api_key}",
                    "Accept": "application/vnd.api+json",
                    "Content-Type": "application/vnd.api+json",
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
        return ProviderType.LEMONSQUEEZY

    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_pausing=True,
            supports_trials=True,
            supports_quantity=True,
            supports_immediate_cancel=True,
            supports_proration=True,
            supports_coupons=True,
            supports_metered_billing=False,
            supports_customer_portal=True,
            supports_checkout_sessions=True,
        )

    def _handle_error(self, response: httpx.Response) -> None:
        """Handle LemonSqueezy API errors."""
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise ProviderRateLimitError(
                provider="lemonsqueezy",
                retry_after=int(retry_after) if retry_after else None,
            )

        if response.status_code == 401:
            raise ProviderAuthenticationError(provider="lemonsqueezy")

        if response.status_code >= 400:
            try:
                error_data = response.json()
                errors = error_data.get("errors", [{}])
                first_error = errors[0] if errors else {}
                raise ProviderAPIError(
                    message=first_error.get("detail", "Unknown LemonSqueezy error"),
                    provider="lemonsqueezy",
                    status_code=response.status_code,
                    provider_message=first_error.get("detail"),
                    provider_code=first_error.get("code"),
                )
            except json.JSONDecodeError:
                raise ProviderAPIError(
                    message=f"LemonSqueezy API error: {response.status_code}",
                    provider="lemonsqueezy",
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
        """Make authenticated request to LemonSqueezy API."""
        client = await self._get_client()

        try:
            response = await client.request(
                method=method,
                url=endpoint,
                json=data,
                params=params,
            )
        except httpx.NetworkError as e:
            raise ProviderNetworkError(provider="lemonsqueezy", original_error=e) from e

        self._handle_error(response)
        return response.json()

    # Customer Operations

    async def create_customer(self, customer: Customer) -> ProviderReference:
        data = {
            "data": {
                "type": "customers",
                "attributes": {
                    "name": customer.name or customer.email.split("@")[0],
                    "email": customer.email,
                },
                "relationships": {
                    "store": {
                        "data": {
                            "type": "stores",
                            "id": self._config.store_id,
                        }
                    }
                },
            }
        }

        result = await self._request("POST", "/customers", data=data)
        customer_data = result.get("data", {})

        return ProviderReference(
            provider=ProviderType.LEMONSQUEEZY,
            external_id=str(customer_data["id"]),
            metadata={
                "email": customer_data.get("attributes", {}).get("email"),
                "subscriptionkore_id": customer.id,
                "external_id": customer.external_id,
            },
        )

    async def update_customer(self, customer: Customer) -> None:
        provider_ref = customer.get_provider_ref("lemonsqueezy")
        if provider_ref is None:
            raise ProviderAPIError(
                message="Customer has no LemonSqueezy reference",
                provider="lemonsqueezy",
                status_code=400,
            )

        data = {
            "data": {
                "type": "customers",
                "id": provider_ref.external_id,
                "attributes": {
                    "name": customer.name,
                    "email": customer.email,
                },
            }
        }

        await self._request("PATCH", f"/customers/{provider_ref.external_id}", data=data)

    async def delete_customer(self, provider_ref: ProviderReference) -> None:
        logger.warning(
            "LemonSqueezy does not support customer deletion",
            customer_id=provider_ref.external_id,
        )

    async def get_customer(self, provider_ref: ProviderReference) -> Customer:
        result = await self._request("GET", f"/customers/{provider_ref.external_id}")
        data = result.get("data", {})
        attrs = data.get("attributes", {})

        return Customer(
            id=provider_ref.metadata.get("subscriptionkore_id", ""),
            external_id=provider_ref.metadata.get("external_id", ""),
            email=attrs.get("email", ""),
            name=attrs.get("name"),
            provider_refs=[provider_ref],
            created_at=datetime.fromisoformat(
                attrs.get("created_at", datetime.utcnow().isoformat()).replace("Z", "+00:00")
            ),
        )

    # Subscription Operations

    async def create_subscriptionkore(
        self,
        request: CreateSubscriptionRequest,
        customer_provider_ref: ProviderReference,
        plan_provider_ref: ProviderReference,
    ) -> Subscription:
        raise ProviderAPIError(
            message="LemonSqueezy requires checkout for subscriptionkore creation.  Use create_checkout_session instead.",
            provider="lemonsqueezy",
            status_code=400,
        )

    async def update_subscriptionkore(
        self,
        request: UpdateSubscriptionRequest,
        subscriptionkore_provider_ref: ProviderReference,
    ) -> Subscription:
        data: dict[str, Any] = {
            "data": {
                "type": "subscriptionkores",
                "id": subscriptionkore_provider_ref.external_id,
                "attributes": {},
            }
        }

        if request.cancel_at_period_end is not None:
            data["data"]["attributes"]["cancelled"] = request.cancel_at_period_end

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
            await self._request(
                "DELETE",
                f"/subscriptionkores/{subscriptionkore_provider_ref.external_id}",
            )
            result = await self._request(
                "GET",
                f"/subscriptionkores/{subscriptionkore_provider_ref.external_id}",
            )
        else:
            data = {
                "data": {
                    "type": "subscriptionkores",
                    "id": subscriptionkore_provider_ref.external_id,
                    "attributes": {
                        "cancelled": True,
                    },
                }
            }
            result = await self._request(
                "PATCH",
                f"/subscriptionkores/{subscriptionkore_provider_ref.external_id}",
                data=data,
            )

        return self._map_subscriptionkore(result.get("data", {}), "", "")

    async def pause_subscriptionkore(
        self,
        subscriptionkore_provider_ref: ProviderReference,
        resumes_at: datetime | None = None,
    ) -> Subscription:
        pause_data: dict[str, Any] = {"mode": "void"}

        if resumes_at:
            pause_data["resumes_at"] = resumes_at.isoformat() + "Z"

        data = {
            "data": {
                "type": "subscriptionkores",
                "id": subscriptionkore_provider_ref.external_id,
                "attributes": {
                    "pause": pause_data,
                },
            }
        }

        result = await self._request(
            "PATCH",
            f"/subscriptionkores/{subscriptionkore_provider_ref.external_id}",
            data=data,
        )

        return self._map_subscriptionkore(result.get("data", {}), "", "")

    async def resume_subscriptionkore(
        self,
        subscriptionkore_provider_ref: ProviderReference,
    ) -> Subscription:
        data = {
            "data": {
                "type": "subscriptionkores",
                "id": subscriptionkore_provider_ref.external_id,
                "attributes": {
                    "pause": None,
                },
            }
        }

        result = await self._request(
            "PATCH",
            f"/subscriptionkores/{subscriptionkore_provider_ref.external_id}",
            data=data,
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
        data = {
            "data": {
                "type": "subscriptionkores",
                "id": subscriptionkore_provider_ref.external_id,
                "attributes": {
                    "variant_id": int(new_plan_provider_ref.external_id),
                    "invoice_immediately": request.proration_behavior != "none",
                },
            }
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
        variant_result = await self._request(
            "GET",
            f"/variants/{new_plan_provider_ref.external_id}",
        )
        variant = variant_result.get("data", {}).get("attributes", {})

        price = Decimal(str(variant.get("price", 0))) / 100
        currency = Currency("USD")

        return ChangePreview(
            immediate_charge=Money(amount=price, currency=currency),
            next_invoice_amount=Money(amount=price, currency=currency),
            proration_amount=Money.zero(currency),
            credit_amount=Money.zero(currency),
            next_billing_date=datetime.utcnow(),
        )

    # Discount Operations

    async def apply_discount(
        self,
        subscriptionkore_provider_ref: ProviderReference,
        discount: DiscountRequest,
    ) -> Subscription:
        if discount.coupon_code:
            discounts_result = await self._request(
                "GET",
                "/discounts",
                params={"filter[code]": discount.coupon_code},
            )
            discounts = discounts_result.get("data", [])
            if not discounts:
                raise ProviderAPIError(
                    message=f"Discount code '{discount.coupon_code}' not found",
                    provider="lemonsqueezy",
                    status_code=404,
                )
            discount_id = discounts[0]["id"]

            data = {
                "data": {
                    "type": "subscriptionkores",
                    "id": subscriptionkore_provider_ref.external_id,
                    "relationships": {
                        "discount": {
                            "data": {
                                "type": "discounts",
                                "id": discount_id,
                            }
                        }
                    },
                }
            }

            result = await self._request(
                "PATCH",
                f"/subscriptionkores/{subscriptionkore_provider_ref.external_id}",
                data=data,
            )

            return self._map_subscriptionkore(result.get("data", {}), "", "")

        return await self.get_subscriptionkore(subscriptionkore_provider_ref)

    async def remove_discount(
        self,
        subscriptionkore_provider_ref: ProviderReference,
    ) -> Subscription:
        logger.warning(
            "LemonSqueezy does not support removing discounts from active subscriptionkores",
            subscriptionkore_id=subscriptionkore_provider_ref.external_id,
        )
        return await self.get_subscriptionkore(subscriptionkore_provider_ref)

    # Billing Operations

    async def get_invoice(self, provider_ref: ProviderReference) -> Invoice:
        result = await self._request(
            "GET",
            f"/subscriptionkore-invoices/{provider_ref.external_id}",
        )
        return self._map_invoice(result.get("data", {}))

    async def list_invoices(
        self,
        customer_provider_ref: ProviderReference,
        limit: int = 10,
        starting_after: str | None = None,
    ) -> list[Invoice]:
        subs_result = await self._request(
            "GET",
            "/subscriptionkores",
            params={"filter[customer_id]": customer_provider_ref.external_id},
        )

        all_invoices: list[Invoice] = []
        for sub in subs_result.get("data", []):
            invoices_result = await self._request(
                "GET",
                "/subscriptionkore-invoices",
                params={"filter[subscriptionkore_id]": sub["id"], "page[size]": limit},
            )
            all_invoices.extend([self._map_invoice(inv) for inv in invoices_result.get("data", [])])

        return all_invoices[:limit]

    async def get_upcoming_invoice(
        self,
        subscriptionkore_provider_ref: ProviderReference,
    ) -> Invoice | None:
        return None

    # Checkout / Portal

    async def create_checkout_session(
        self,
        request: CheckoutRequest,
        plan_provider_ref: ProviderReference,
        customer_provider_ref: ProviderReference | None = None,
    ) -> CheckoutSession:
        data: dict[str, Any] = {
            "data": {
                "type": "checkouts",
                "attributes": {
                    "checkout_data": {
                        "custom": request.metadata,
                    },
                    "product_options": {
                        "redirect_url": request.success_url,
                    },
                },
                "relationships": {
                    "store": {
                        "data": {
                            "type": "stores",
                            "id": self._config.store_id,
                        }
                    },
                    "variant": {
                        "data": {
                            "type": "variants",
                            "id": plan_provider_ref.external_id,
                        }
                    },
                },
            }
        }

        if customer_provider_ref:
            data["data"]["attributes"]["checkout_data"]["email"] = (
                customer_provider_ref.metadata.get("email")
            )
        elif request.customer_email:
            data["data"]["attributes"]["checkout_data"]["email"] = request.customer_email

        result = await self._request("POST", "/checkouts", data=data)
        checkout_data = result.get("data", {})
        attrs = checkout_data.get("attributes", {})

        return CheckoutSession(
            id=str(checkout_data["id"]),
            url=attrs.get("url", ""),
            expires_at=datetime.fromisoformat(
                attrs.get("expires_at", datetime.utcnow().isoformat()).replace("Z", "+00:00")
            ),
        )

    async def create_portal_session(
        self,
        customer_provider_ref: ProviderReference,
        return_url: str,
    ) -> PortalSession:
        result = await self._request(
            "GET",
            "/subscriptionkores",
            params={"filter[customer_id]": customer_provider_ref.external_id},
        )

        subscriptionkores = result.get("data", [])
        if not subscriptionkores:
            raise ProviderAPIError(
                message="Customer has no subscriptionkores",
                provider="lemonsqueezy",
                status_code=404,
            )

        sub = subscriptionkores[0]
        urls = sub.get("attributes", {}).get("urls", {})
        portal_url = urls.get("customer_portal", "")

        return PortalSession(
            id=str(sub["id"]),
            url=portal_url,
        )

    # Webhook Handling

    async def verify_webhook(
        self,
        payload: bytes,
        headers: dict[str, str],
    ) -> bool:
        """Verify LemonSqueezy webhook signature."""
        signature = headers.get("x-signature", "")
        if not signature:
            return False

        expected_sig = hmac.new(
            self._config.webhook_secret.encode("utf-8"),
            payload,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected_sig, signature)

    async def parse_webhook(
        self,
        payload: bytes,
        headers: dict[str, str],
    ) -> ProviderWebhookEvent:
        """Parse LemonSqueezy webhook payload."""
        data = json.loads(payload)
        meta = data.get("meta", {})

        return ProviderWebhookEvent(
            provider=ProviderType.LEMONSQUEEZY,
            event_id=meta.get("event_id", ""),
            event_type=meta.get("event_name", ""),
            occurred_at=datetime.fromisoformat(
                meta.get("created_at", datetime.utcnow().isoformat()).replace("Z", "+00:00")
            ),
            data=data.get("data", {}),
            raw_payload=payload,
        )

    # Sync Operations

    async def sync_products(self) -> list[Product]:
        result = await self._request(
            "GET",
            "/products",
            params={"filter[store_id]": self._config.store_id},
        )

        products = []
        for prod in result.get("data", []):
            attrs = prod.get("attributes", {})
            products.append(
                Product(
                    id="",
                    name=attrs.get("name", ""),
                    description=attrs.get("description"),
                    provider_refs=[
                        ProviderReference(
                            provider=ProviderType.LEMONSQUEEZY,
                            external_id=str(prod["id"]),
                        )
                    ],
                    active=attrs.get("status") == "published",
                    metadata={},
                    created_at=datetime.fromisoformat(
                        attrs.get("created_at", datetime.utcnow().isoformat()).replace(
                            "Z", "+00:00"
                        )
                    ),
                )
            )

        return products

    async def sync_plans(self, product_provider_ref: ProviderReference) -> list[Plan]:
        result = await self._request(
            "GET",
            "/variants",
            params={"filter[product_id]": product_provider_ref.external_id},
        )

        plans = []
        for variant in result.get("data", []):
            attrs = variant.get("attributes", {})

            interval_str = attrs.get("interval", "month")
            interval_map = {
                "day": Interval.DAY,
                "week": Interval.WEEK,
                "month": Interval.MONTH,
                "year": Interval.YEAR,
            }

            plans.append(
                Plan(
                    id="",
                    product_id="",
                    name=attrs.get("name", ""),
                    description=attrs.get("description"),
                    provider_refs=[
                        ProviderReference(
                            provider=ProviderType.LEMONSQUEEZY,
                            external_id=str(variant["id"]),
                        )
                    ],
                    price=Money(
                        amount=Decimal(str(attrs.get("price", 0))) / 100,
                        currency=Currency("USD"),
                    ),
                    billing_period=BillingPeriod(
                        interval=interval_map.get(interval_str, Interval.MONTH),
                        interval_count=attrs.get("interval_count", 1),
                    ),
                    trial_period_days=attrs.get("trial_interval_count"),
                    active=attrs.get("status") == "published",
                    metadata={},
                    created_at=datetime.fromisoformat(
                        attrs.get("created_at", datetime.utcnow().isoformat()).replace(
                            "Z", "+00:00"
                        )
                    ),
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
        """Map LemonSqueezy subscriptionkore to domain model."""
        attrs = data.get("attributes", {})
        status = self.STATUS_MAP.get(attrs.get("status", "active"), SubscriptionStatus.ACTIVE)

        # Handle pause
        pause_config = None
        pause_data = attrs.get("pause")
        if pause_data:
            pause_config = PauseConfig(
                resumes_at=datetime.fromisoformat(pause_data["resumes_at"].replace("Z", "+00:00"))
                if pause_data.get("resumes_at")
                else None,
                behavior=PauseBehavior.VOID,
            )

        # Handle trial
        trial_end = None
        if attrs.get("trial_ends_at"):
            trial_end = datetime.fromisoformat(attrs["trial_ends_at"].replace("Z", "+00:00"))

        # Parse dates
        renews_at = attrs.get("renews_at")
        current_period_end = None
        if renews_at:
            current_period_end = datetime.fromisoformat(renews_at.replace("Z", "+00:00"))

        created_at = datetime.fromisoformat(
            attrs.get("created_at", datetime.utcnow().isoformat()).replace("Z", "+00:00")
        )

        return Subscription(
            id="",
            customer_id=customer_id,
            plan_id=plan_id,
            provider_ref=ProviderReference(
                provider=ProviderType.LEMONSQUEEZY,
                external_id=str(data["id"]),
                metadata={
                    "customer_id": str(attrs.get("customer_id", "")),
                    "variant_id": str(attrs.get("variant_id", "")),
                },
            ),
            status=status,
            current_period=DateRange(
                start=created_at,
                end=current_period_end,
            ),
            trial_end=trial_end,
            cancel_at_period_end=attrs.get("cancelled", False),
            canceled_at=datetime.fromisoformat(attrs["cancelled_at"].replace("Z", "+00:00"))
            if attrs.get("cancelled_at")
            else None,
            ended_at=datetime.fromisoformat(attrs["ends_at"].replace("Z", "+00:00"))
            if attrs.get("ends_at")
            else None,
            pause_collection=pause_config,
            discount=None,
            quantity=1,
            metadata={},
            created_at=created_at,
        )

    def _map_invoice(self, data: dict[str, Any]) -> Invoice:
        """Map LemonSqueezy subscriptionkore invoice to domain model."""
        attrs = data.get("attributes", {})
        currency = Currency("USD")

        status_map = {
            "pending": InvoiceStatus.OPEN,
            "paid": InvoiceStatus.PAID,
            "void": InvoiceStatus.VOID,
            "refunded": InvoiceStatus.VOID,
        }

        total_amount = Decimal(str(attrs.get("total", 0))) / 100
        subtotal_amount = Decimal(str(attrs.get("subtotal", 0))) / 100
        tax_amount = Decimal(str(attrs.get("tax", 0))) / 100
        discount_amount = Decimal(str(attrs.get("discount_total", 0))) / 100

        return Invoice(
            id="",
            customer_id="",
            subscriptionkore_id=str(attrs.get("subscriptionkore_id", "")),
            provider_ref=ProviderReference(
                provider=ProviderType.LEMONSQUEEZY,
                external_id=str(data.get("id", "")),
            ),
            status=status_map.get(attrs.get("status", "pending"), InvoiceStatus.OPEN),
            subtotal=Money(amount=subtotal_amount, currency=currency),
            tax=Money(amount=tax_amount, currency=currency),
            discount_amount=Money(amount=discount_amount, currency=currency),
            total=Money(amount=total_amount, currency=currency),
            amount_paid=Money(amount=total_amount, currency=currency)
            if attrs.get("status") == "paid"
            else Money.zero(currency),
            amount_due=Money(amount=total_amount, currency=currency)
            if attrs.get("status") != "paid"
            else Money.zero(currency),
            currency=currency,
            line_items=[],
            invoice_pdf_url=attrs.get("urls", {}).get("invoice_url"),
            metadata={},
            created_at=datetime.fromisoformat(
                attrs.get("created_at", datetime.utcnow().isoformat()).replace("Z", "+00:00")
            ),
        )
