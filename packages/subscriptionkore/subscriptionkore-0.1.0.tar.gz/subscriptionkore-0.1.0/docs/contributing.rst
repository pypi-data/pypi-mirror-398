Contributing
============

We welcome contributions to SubscriptionKore!

Development Setup
-----------------

1. Fork the repository
2. Clone your fork:

   .. code-block:: bash

      git clone https://github.com/yourusername/subscriptionkore.git
      cd subscriptionkore

3. Install development dependencies:

   .. code-block:: bash

      pip install -e .[dev]

4. Run tests:

   .. code-block:: bash

      make test

5. Run linter:

   .. code-block:: bash

      make lint

Code Style
----------

- Use ``ruff`` for linting and formatting
- Follow PEP 8 style guidelines
- Use type hints
- Write docstrings for public APIs

Testing
-------

- Write tests for new features
- Run the full test suite before submitting PRs
- Use ``pytest`` for testing

Submitting Changes
------------------

1. Create a feature branch
2. Make your changes
3. Run tests and linting
4. Submit a pull request

Documentation
-------------

- Update documentation for any API changes
- Build docs locally:

  .. code-block:: bash

     pip install -e .[docs]
     cd docs
     make html

Reporting Issues
----------------

- Use GitHub issues for bug reports
- Include reproduction steps and environment details
- For security issues, email security@innerkore.com