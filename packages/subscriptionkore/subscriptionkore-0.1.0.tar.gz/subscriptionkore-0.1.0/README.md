# SubscriptionKore

**Provider-agnostic async subscription management library for SaaS applications**

[![Documentation Status](https://readthedocs.org/projects/subscriptionkore/badge/?version=latest)](https://subscriptionkore.readthedocs.io/en/latest/?badge=latest)

## Features

- **Multi-provider support**: Stripe, Paddle, Chargebee, Lemon Squeezy
- **Async-first**: Built with asyncio for high performance
- **Type-safe**: Full type hints and Pydantic models
- **Database agnostic**: Works with SQLAlchemy, Redis, and more
- **Event-driven**: Domain events for extensibility
- **FastAPI integration**: Ready-to-use FastAPI routers

## Installation

```bash
pip install subscriptionkore
```

For optional dependencies:

```bash
pip install subscriptionkore[all]  # All providers and integrations
```

## Quick Start

```python
from subscriptionkore import SubscriptionKore, SubscriptionKoreConfig

# Configure
config = SubscriptionKoreConfig(
    default_provider="stripe",
    stripe_api_key="sk_test_...",
)

# Initialize
async with SubscriptionKore(config) as sk:
    # Create customer
    customer = await sk.create_customer(
        email="user@example.com",
        name="John Doe"
    )

    # Create subscription
    subscription = await sk.create_subscription(
        customer_id=customer.id,
        price_id="price_123"
    )

    print(f"Created subscription: {subscription.id}")
```

## Documentation

Full documentation is available at [Read the Docs](https://subscriptionkore.readthedocs.io/).

## Examples

See the `examples/` directory for complete applications:

- `fastapi_app.py`: FastAPI integration example
- `multi_provider_app.py`: Multi-provider setup

## Contributing

Contributions are welcome! Please see the [contributing guide](https://subscriptionkore.readthedocs.io/en/latest/contributing.html).

## License

MIT License