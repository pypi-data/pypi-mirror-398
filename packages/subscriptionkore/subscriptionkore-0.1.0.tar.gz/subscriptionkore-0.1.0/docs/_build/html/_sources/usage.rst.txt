Usage Guide
===========

This section covers common usage patterns and advanced features.

Working with Customers
----------------------

Create a customer:

.. code-block:: python

   customer = await subscriptionkore.create_customer(
       email="user@example.com",
       name="John Doe",
       metadata={"source": "website"}
   )

Retrieve a customer:

.. code-block:: python

   customer = await subscriptionkore.get_customer(customer_id)

Update a customer:

.. code-block:: python

   updated_customer = await subscriptionkore.update_customer(
       customer_id,
       name="Jane Doe"
   )

Working with Subscriptions
--------------------------

Create a subscription:

.. code-block:: python

   subscription = await subscriptionkore.create_subscription(
       customer_id=customer.id,
       price_id="price_123",
       provider="stripe"
   )

Retrieve a subscription:

.. code-block:: python

   subscription = await subscriptionkore.get_subscription(subscription_id)

Cancel a subscription:

.. code-block:: python

   await subscriptionkore.cancel_subscription(subscription_id)

Working with Products and Prices
---------------------------------

List products:

.. code-block:: python

   products = await subscriptionkore.list_products()

Create a product:

.. code-block:: python

   product = await subscriptionkore.create_product(
       name="Premium Plan",
       description="Premium subscription plan"
   )

Event Handling
--------------

Subscribe to events:

.. code-block:: python

   @subscriptionkore.on_event(SubscriptionActivated)
   async def handle_activation(event):
       print(f"Subscription {event.subscription_id} activated")

   @subscriptionkore.on_event(CustomerCreated)
   async def handle_customer_created(event):
       await send_welcome_email(event.customer_id)

Multiple Providers
------------------

Work with different providers:

.. code-block:: python

   # Create customer on Stripe
   stripe_customer = await subscriptionkore.create_customer(
       email="user@example.com",
       provider="stripe"
   )

   # Create subscription on Paddle
   paddle_subscription = await subscriptionkore.create_subscription(
       customer_id=stripe_customer.id,
       price_id="paddle_price_123",
       provider="paddle"
   )