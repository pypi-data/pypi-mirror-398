Installation
============

Install SubscriptionKore using pip:

.. code-block:: bash

   pip install subscriptionkore

For development:

.. code-block:: bash

   pip install -e .[dev]

For documentation:

.. code-block:: bash

   pip install -e .[docs]

Optional Dependencies
---------------------

SubscriptionKore supports various optional dependencies for different features:

- **fastapi**: For FastAPI integration
- **sqlalchemy**: For database persistence
- **redis**: For caching
- **stripe**: For Stripe payment provider
- **paddle**: For Paddle payment provider
- **chargebee**: For Chargebee payment provider

Install with all optional dependencies:

.. code-block:: bash

   pip install subscriptionkore[all]