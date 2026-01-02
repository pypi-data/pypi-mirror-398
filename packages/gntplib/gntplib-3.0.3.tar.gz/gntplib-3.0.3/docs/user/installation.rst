============
Installation
============

This guide covers the installation of gntplib and its optional dependencies.

Requirements
============

Core Requirements
-----------------

* Python 3.7 or higher
* No external dependencies for basic functionality

Optional Dependencies
---------------------

For Async Support (Tornado)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* tornado >= 5.0

.. code-block:: bash

   pip install tornado

For Encryption Support
~~~~~~~~~~~~~~~~~~~~~~

* pycryptodomex >= 3.15

.. code-block:: bash

   pip install pycryptodomex

Installing gntplib
==================

From PyPI (Recommended)
-----------------------

Install the latest stable version:

.. code-block:: bash

   pip install gntplib

With Optional Dependencies
--------------------------

Install with async support:

.. code-block:: bash

   pip install gntplib[async]

Install with encryption support:

.. code-block:: bash

   pip install gntplib[crypto]

Install with all optional features:

.. code-block:: bash

   pip install gntplib[all]

From Source
-----------

Clone the repository and install:

.. code-block:: bash

   git clone https://github.com/cumulus13/gntplib.git
   cd gntplib
   pip install -e .

For development with all dependencies:

.. code-block:: bash

   pip install -e ".[dev,async,crypto]"

Verifying Installation
======================

Check that gntplib is installed correctly:

.. code-block:: python

   import gntplib
   print(gntplib.__version__)

Run a simple test:

.. code-block:: python

   from gntplib import publish
   
   # This will attempt to send a notification to localhost
   try:
       publish('TestApp', 'TestEvent', 'Test Title', 'Test message')
       print("✓ Installation successful!")
   except Exception as e:
       print(f"Note: {e}")
       print("(This is expected if no GNTP server is running)")

Platform-Specific Notes
=======================

Linux
-----

On Linux, you might need to install development headers for building dependencies:

**Debian/Ubuntu:**

.. code-block:: bash

   sudo apt-get update
   sudo apt-get install python3-dev build-essential

**Fedora/RHEL:**

.. code-block:: bash

   sudo dnf install python3-devel gcc

macOS
-----

Install using Homebrew Python:

.. code-block:: bash

   brew install python3
   pip3 install gntplib

Windows
-------

Install Python from `python.org <https://www.python.org/downloads/>`_ and ensure 
pip is included. Then install normally:

.. code-block:: bash

   pip install gntplib

Virtual Environments
====================

It's recommended to use virtual environments for Python projects.

Using venv (Python 3.3+)
------------------------

.. code-block:: bash

   # Create virtual environment
   python3 -m venv venv
   
   # Activate (Linux/macOS)
   source venv/bin/activate
   
   # Activate (Windows)
   venv\Scripts\activate
   
   # Install gntplib
   pip install gntplib

Using conda
-----------

.. code-block:: bash

   # Create conda environment
   conda create -n myproject python=3.10
   
   # Activate environment
   conda activate myproject
   
   # Install gntplib
   pip install gntplib

Upgrading
=========

Upgrade to the latest version:

.. code-block:: bash

   pip install --upgrade gntplib

Upgrade to a specific version:

.. code-block:: bash

   pip install gntplib==1.0.0

Uninstalling
============

Remove gntplib:

.. code-block:: bash

   pip uninstall gntplib

Troubleshooting
===============

Import Errors
-------------

If you encounter import errors:

1. Verify Python version:

   .. code-block:: bash

      python --version  # Should be 3.7+

2. Check installation:

   .. code-block:: bash

      pip show gntplib

3. Verify Python path:

   .. code-block:: python

      import sys
      print(sys.path)

Encryption Issues
-----------------

If encryption doesn't work:

1. Ensure PyCryptodome is installed:

   .. code-block:: bash

      pip install pycryptodomex

2. Try importing manually:

   .. code-block:: python

      from Cryptodome.Cipher import AES  # Should not raise ImportError

Async Issues
------------

If async features don't work:

1. Ensure Tornado is installed:

   .. code-block:: bash

      pip install tornado

2. Verify Tornado import:

   .. code-block:: python

      import tornado
      print(tornado.version)  # Should be 5.0+

Getting Help
============

If you encounter issues:

* Check the `FAQ <https://gntplib.readthedocs.io/en/latest/faq.html>`_
* Search `existing issues <https://github.com/cumulus13/gntplib/issues>`_
* Open a `new issue <https://github.com/cumulus13/gntplib/issues/new>`_

Next Steps
==========

Now that you have gntplib installed, check out the :doc:`quickstart` guide 
to learn basic usage.