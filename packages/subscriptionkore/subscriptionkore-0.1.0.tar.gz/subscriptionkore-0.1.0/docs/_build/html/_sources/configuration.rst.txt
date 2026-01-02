Configuration
=============

SubscriptionKore uses Pydantic settings for configuration, supporting environment variables and programmatic setup.

Basic Configuration
-------------------

.. code-block:: python

   from subscriptionkore import SubscriptionKoreConfig

   config = SubscriptionKoreConfig(
       default_provider="stripe",
       stripe_api_key="sk_test_...",
       database_url="postgresql+asyncpg://user:pass@localhost/db",
   )

Environment Variables
---------------------

You can use environment variables for configuration:

.. code-block:: bash

   export SUBSCRIPTIONKORE_DEFAULT_PROVIDER=stripe
   export SUBSCRIPTIONKORE_STRIPE_API_KEY=sk_test_...
   export SUBSCRIPTIONKORE_DATABASE_URL=postgresql+asyncpg://user:pass@localhost/db

Then in code:

.. code-block:: python

   from subscriptionkore import SubscriptionKoreConfig

   config = SubscriptionKoreConfig()  # Loads from env vars

Provider-Specific Configuration
-------------------------------

Configure multiple providers:

.. code-block:: python

   config = SubscriptionKoreConfig(
       default_provider="stripe",
       stripe_api_key="sk_test_...",
       paddle_api_key="paddle_key",
       chargebee_api_key="chargebee_key",
   )

Database Configuration
----------------------

For SQLAlchemy integration:

.. code-block:: python

   config = SubscriptionKoreConfig(
       database_url="postgresql+asyncpg://user:pass@localhost/db",
       database_echo=False,  # Set to True for SQL logging
   )

Redis Configuration
-------------------

For caching:

.. code-block:: python

   config = SubscriptionKoreConfig(
       redis_url="redis://localhost:6379",
   )