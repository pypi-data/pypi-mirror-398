=======================
Requests API Reference
=======================

Request and Response classes for GNTP protocol communication.

Request Classes
===============

BaseRequest
-----------

.. autoclass:: gntplib.requests.BaseRequest
   :members:
   :special-members: __init__
   :show-inheritance:

RegisterRequest
---------------

.. autoclass:: gntplib.requests.RegisterRequest
   :members:
   :special-members: __init__
   :show-inheritance:

   .. rubric:: Example

   .. code-block:: python

      from gntplib.requests import RegisterRequest
      from gntplib import Event, Resource

      events = [Event('update', 'Update Available')]
      icon = Resource.from_file('app.png')
      request = RegisterRequest('MyApp', icon, events)

NotifyRequest
-------------

.. autoclass:: gntplib.requests.NotifyRequest
   :members:
   :special-members: __init__
   :show-inheritance:

   .. rubric:: Example

   .. code-block:: python

      from gntplib.requests import NotifyRequest
      from gntplib.models import Notification

      notification = Notification('update', 'New Version', 'v2.0 released')
      request = NotifyRequest('MyApp', notification)

SubscribeRequest
----------------

.. autoclass:: gntplib.requests.SubscribeRequest
   :members:
   :special-members: __init__
   :show-inheritance:

Response Class
==============

.. autoclass:: gntplib.requests.Response
   :members:
   :special-members: __init__, __repr__, __str__
   :show-inheritance:

   .. rubric:: Methods

   .. automethod:: is_ok
      :no-index:
      
   .. automethod:: is_error
      :no-index:

   .. automethod:: is_callback
      :no-index:

   .. automethod:: get_header
      :no-index:

Utility Functions
=================

.. autofunction:: gntplib.requests.parse_response
