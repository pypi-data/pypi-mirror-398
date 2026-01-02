=============================================
gntplib - GNTP Client Library for Python
=============================================

**gntplib** is a modern Python 3 implementation of the Growl Notification Transport Protocol (GNTP) 
client library. It provides both synchronous and asynchronous APIs for sending notifications to 
GNTP-compatible notification systems.

.. image:: https://img.shields.io/pypi/v/gntplib.svg
   :target: https://pypi.org/project/gntplib/
   :alt: PyPI Version

.. image:: https://img.shields.io/pypi/pyversions/gntplib.svg
   :target: https://pypi.org/project/gntplib/
   :alt: Python Versions

.. image:: https://img.shields.io/github/license/cumulus13/gntplib.svg
   :target: https://github.com/cumulus13/gntplib/blob/main/LICENSE
   :alt: License

.. image:: _static/logo.png
   :alt: GntpLib Logo
   :width: 350
   :align: center


Quick Start
===========

Installation
------------

Install from PyPI:

.. code-block:: bash

   pip install gntplib

For async support with Tornado:

.. code-block:: bash

   pip install gntplib[async]

For encryption support:

.. code-block:: bash

   pip install gntplib[crypto]

Simple Example
--------------

Send a notification in just two lines:

.. code-block:: python

   from gntplib import publish
   
   publish('MyApp', 'Alert', 'Hello World', 'This is a notification')

More Advanced Usage
-------------------

.. code-block:: python

   from gntplib import Publisher, Event, Resource
   
   # Define notification events
   events = [
       Event('update', 'Software Update', enabled=True),
       Event('download', 'Download Complete', enabled=True),
   ]
   
   # Create publisher with icon
   icon = Resource.from_file('app_icon.png')
   publisher = Publisher('MyApp', events, icon=icon)
   
   # Register with GNTP server
   publisher.register()
   
   # Send notification
   publisher.publish(
       'update',
       'New Version Available',
       'Version 2.0 is ready to install',
       priority=1,
       sticky=True
   )

Async Example
-------------

.. code-block:: python

   import asyncio
   from gntplib.async_gntp import AsyncPublisher, AsyncResource
   from gntplib import Event
   
   async def main():
       # Async resource fetching
       icon = AsyncResource('https://example.com/icon.png')
       
       # Create async publisher
       publisher = AsyncPublisher('MyApp', [Event('test')], icon=icon)
       publisher.register()
       
       # Send notification
       publisher.publish('test', 'Hello', 'Async notification!')
   
   asyncio.run(main())

Key Features
============

✅ **Modern Python 3**
   - Type hints throughout
   - Async/await support with Tornado
   - Clean, maintainable codebase

✅ **Full GNTP Support**
   - REGISTER, NOTIFY, and SUBSCRIBE requests
   - Authentication with multiple hash algorithms
   - Optional encryption (AES, DES, 3DES)

✅ **Flexible Resource Handling**
   - Embed binary resources (icons, images)
   - URL-based resources
   - Async resource fetching

✅ **Callback Support**
   - Socket callbacks for click/close events
   - URL callbacks
   - Custom callback handlers

✅ **Production Ready**
   - Comprehensive error handling
   - Extensive logging support
   - Well-documented API

Contents
========

.. toctree::
   :maxdepth: 2
   :caption: User Guide
   
   user/installation
   user/quickstart
   user/tutorial
   user/advanced
   user/async
   user/security

.. toctree::
   :maxdepth: 2
   :caption: API Reference
   
   api/core
   api/models
   api/requests
   api/connections
   api/async
   api/exceptions

.. toctree::
   :maxdepth: 1
   :caption: Additional Information
   
   contributing
   changelog
   license

Indices and Tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

Links
=====

* `GitHub Repository <https://github.com/cumulus13/gntplib>`_
* `Issue Tracker <https://github.com/cumulus13/gntplib/issues>`_
* `PyPI Package <https://pypi.org/project/gntplib/>`_
* `GNTP Specification <http://www.growlforwindows.com/gfw/help/gntp.aspx>`_