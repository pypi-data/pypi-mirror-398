Quickstart
==========

This guide will get you started with SubscriptionKore quickly.

Basic Setup
-----------

.. code-block:: python

   from subscriptionkore import SubscriptionKore, SubscriptionKoreConfig

   # Configure the library
   config = SubscriptionKoreConfig(
       default_provider="stripe",
       stripe_api_key="sk_test_...",
   )

   # Initialize
   subscriptionkore = SubscriptionKore(config)
   await subscriptionkore.initialize()

   # Use it
   customer = await subscriptionkore.create_customer(
       email="user@example.com",
       name="John Doe"
   )

   print(f"Created customer: {customer.id}")

Don't forget to close when done:

.. code-block:: python

   await subscriptionkore.close()

Async Context Manager
---------------------

For better resource management, use as an async context manager:

.. code-block:: python

   async with SubscriptionKore(config) as sk:
       customer = await sk.create_customer(
           email="user@example.com",
           name="John Doe"
       )
       print(f"Created customer: {customer.id}")