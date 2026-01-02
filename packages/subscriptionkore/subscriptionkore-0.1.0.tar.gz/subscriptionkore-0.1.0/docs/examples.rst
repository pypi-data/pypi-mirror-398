Examples
========

This section contains example applications demonstrating SubscriptionKore usage.

FastAPI Integration
-------------------

See ``examples/fastapi_app.py`` for a complete FastAPI application.

Multi-Provider Setup
---------------------

See ``examples/multi_provider_app.py`` for an example with multiple payment providers.

Running Examples
----------------

To run the examples:

.. code-block:: bash

   # Install with all dependencies
   pip install -e .[all]

   # Run FastAPI example
   make run-fastapi-example

   # Run multi-provider example
   make run-multi-provider-example

Basic Example
-------------

.. literalinclude:: ../examples/fastapi_app.py
   :language: python
   :lines: 1-50

Multi-Provider Example
-----------------------

.. literalinclude:: ../examples/multi_provider_app.py
   :language: python
   :lines: 1-50