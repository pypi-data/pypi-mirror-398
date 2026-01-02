============
Contributing
============

We love contributions! This guide will help you get started with contributing to gntplib.

Getting Started
===============

Fork and Clone
--------------

1. Fork the repository on GitHub
2. Clone your fork locally:

   .. code-block:: bash

      git clone https://github.com/cumulus13/gntplib.git
      cd gntplib

3. Add upstream remote:

   .. code-block:: bash

      git remote add upstream https://github.com/original/gntplib.git

Development Setup
-----------------

Create a virtual environment and install development dependencies:

.. code-block:: bash

   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # Install package in editable mode with dev dependencies
   pip install -e ".[dev,async,crypto]"

   # Install pre-commit hooks (optional but recommended)
   pre-commit install

Development Dependencies
------------------------

The ``[dev]`` extra includes:

* pytest - Testing framework
* pytest-cov - Coverage reporting
* pytest-asyncio - Async test support
* black - Code formatting
* flake8 - Linting
* mypy - Type checking
* sphinx - Documentation generation

Making Changes
==============

Create a Branch
---------------

.. code-block:: bash

   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/issue-description

Code Style
----------

We follow PEP 8 with some modifications:

* Line length: 88 characters (Black default)
* Use type hints for all public APIs
* Docstrings for all public modules, classes, and functions
* Google-style docstrings

Format your code with Black:

.. code-block:: bash

   black gntplib tests

Check with flake8:

.. code-block:: bash

   flake8 gntplib tests

Type check with mypy:

.. code-block:: bash

   mypy gntplib

Writing Tests
=============

Run Tests
---------

Run all tests:

.. code-block:: bash

   pytest

Run with coverage:

.. code-block:: bash

   pytest --cov=gntplib --cov-report=html

Run specific test file:

.. code-block:: bash

   pytest tests/test_publisher.py

Test Structure
--------------

.. code-block:: python

   import pytest
   from gntplib import Publisher, Event

   class TestPublisher:
       """Test Publisher class."""

       def test_create_publisher(self):
           """Test publisher creation."""
           events = [Event('test')]
           publisher = Publisher('TestApp', events)
           assert publisher.name == 'TestApp'

       def test_register(self, mock_server):
           """Test registration with mock server."""
           # Your test code here
           pass

Async Tests
-----------

.. code-block:: python

   import pytest
   from gntplib.async_gntp import AsyncPublisher

   @pytest.mark.asyncio
   async def test_async_publisher():
       """Test async publisher."""
       events = [Event('test')]
       publisher = AsyncPublisher('TestApp', events)
       # Test code here

Documentation
=============

Building Docs
-------------

Build documentation locally:

.. code-block:: bash

   cd docs
   make html

View documentation:

.. code-block:: bash

   open _build/html/index.html  # macOS
   xdg-open _build/html/index.html  # Linux
   start _build/html/index.html  # Windows

Live reload for development:

.. code-block:: bash

   make livehtml

Writing Documentation
---------------------

* Use reStructuredText for documentation files
* Add examples to docstrings
* Update API reference if adding new public APIs
* Add entries to changelog

Docstring Example
-----------------

.. code-block:: python

   def my_function(param1: str, param2: int = 0) -> bool:
       """Short one-line description.

       More detailed description if needed. Can span multiple
       lines and paragraphs.

       Args:
           param1: Description of param1
           param2: Description of param2 (default: 0)

       Returns:
           Description of return value

       Raises:
           ValueError: When param1 is empty
           GNTPError: When connection fails

       Example:
           >>> result = my_function('test', 5)
           >>> print(result)
           True
       """
       if not param1:
           raise ValueError("param1 cannot be empty")
       return True

Submitting Changes
==================

Commit Messages
---------------

Follow conventional commits format:

.. code-block:: text

   type(scope): short description

   Longer description if needed.

   Fixes #123

Types:

* ``feat``: New feature
* ``fix``: Bug fix
* ``docs``: Documentation changes
* ``style``: Code style changes (formatting, etc.)
* ``refactor``: Code refactoring
* ``test``: Test additions or modifications
* ``chore``: Build process or auxiliary tool changes

Examples:

.. code-block:: text

   feat(publisher): add timeout parameter to publish method

   fix(async): handle connection errors in async mode

   docs(tutorial): add example for encrypted notifications

Push and Create PR
------------------

1. Push your changes:

   .. code-block:: bash

      git push origin feature/your-feature-name

2. Create Pull Request on GitHub

3. Ensure CI passes

4. Wait for review

Pull Request Checklist
----------------------

- [ ] Tests pass locally
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] Changelog updated
- [ ] Code follows style guidelines
- [ ] Type hints added
- [ ] Docstrings added/updated

Code Review
===========

What We Look For
----------------

* **Correctness**: Does the code work as intended?
* **Tests**: Are there adequate tests?
* **Documentation**: Is it well documented?
* **Style**: Does it follow project conventions?
* **Performance**: Are there obvious performance issues?
* **Security**: Are there security concerns?

Responding to Feedback
----------------------

* Be open to feedback
* Ask questions if something is unclear
* Make requested changes promptly
* Discuss alternatives constructively

Release Process
===============

For Maintainers
---------------

1. Update version in ``gntplib/__init__.py``
2. Update ``CHANGELOG.md``
3. Create release commit:

   .. code-block:: bash

      git commit -am "Release vX.Y.Z"
      git tag vX.Y.Z
      git push origin main --tags

4. Build and upload to PyPI:

   .. code-block:: bash

      python -m build
      python -m twine upload dist/*

Getting Help
============

* **Questions**: Open a discussion on GitHub
* **Bugs**: Open an issue with reproduction steps
* **Features**: Open an issue to discuss before implementing
* **Chat**: Join our community chat (if available)

Thank you for contributing to gntplib! 🎉

