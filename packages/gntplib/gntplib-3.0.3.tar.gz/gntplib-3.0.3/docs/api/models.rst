=====================
Models API Reference
=====================

This page documents data model classes used in gntplib.

Event Class
===========

Defines notification types.

.. autoclass:: gntplib.Event
   :members:
   :special-members: __init__, __repr__, __eq__, __hash__
   :show-inheritance:

   .. rubric:: Attributes

   .. attribute:: name
      
      Unique identifier for the event type (required).

   .. attribute:: display_name
      
      Human-readable name shown in preferences (defaults to name).

   .. attribute:: enabled
      
      Whether event is enabled by default (defaults to True).

   .. attribute:: icon
      
      Optional Resource instance for event icon.

   .. rubric:: Example

   .. code-block:: python

      from gntplib import Event, Resource

      # Simple event
      event1 = Event('update')

      # With display name
      event2 = Event('update', 'Software Update')

      # Disabled by default
      event3 = Event('debug', 'Debug Message', enabled=False)

      # With icon
      icon = Resource.from_file('update.png')
      event4 = Event('update', icon=icon)

Resource Class
==============

Handles binary resources like icons and images.

.. autoclass:: gntplib.Resource
   :members:
   :special-members: __init__, __repr__, __bool__
   :show-inheritance:

   .. rubric:: Attributes

   .. attribute:: data
      
      Binary content of the resource (bytes or None).

   .. attribute:: url
      
      Optional URL string for remote resources.

   .. rubric:: Methods

   .. automethod:: from_file
   .. automethod:: from_url
   .. automethod:: unique_value
   .. automethod:: unique_id

   .. rubric:: Example

   .. code-block:: python

      from gntplib import Resource

      # From file
      icon = Resource.from_file('app_icon.png')
      print(f"Size: {len(icon.data)} bytes")

      # From URL
      remote_icon = Resource.from_url('https://example.com/icon.png')

      # From bytes
      with open('image.png', 'rb') as f:
          embedded = Resource(data=f.read())

      # Get unique identifier
      resource_id = icon.unique_id()  # b'x-growl-resource://...'

Notification Class
==================

Represents individual notification instances.

.. autoclass:: gntplib.models.Notification
   :members:
   :special-members: __init__, __repr__
   :show-inheritance:

   .. rubric:: Attributes

   .. attribute:: name
      
      Event name (must match registered event).

   .. attribute:: title
      
      Notification title (required).

   .. attribute:: text
      
      Notification message body.

   .. attribute:: id_
      
      Optional unique identifier.

   .. attribute:: sticky
      
      Whether notification stays until dismissed.

   .. attribute:: priority
      
      Priority level (-2 to 2).

   .. attribute:: icon
      
      Optional Resource instance.

   .. attribute:: coalescing_id
      
      ID for grouping/replacing notifications.

   .. attribute:: callback
      
      Optional callback handler.

   .. rubric:: Properties

   .. autoproperty:: socket_callback

   .. rubric:: Example

   .. code-block:: python

      from gntplib.models import Notification, Resource

      # Simple notification
      notif = Notification('update', 'New Version', 'v2.0 released')

      # With all options
      icon = Resource.from_file('alert.png')
      notif = Notification(
          name='alert',
          title='Critical Alert',
          text='Server is down!',
          id_='alert-001',
          sticky=True,
          priority=2,
          icon=icon,
          coalescing_id='server-alerts'
      )

Callback Classes
================

SocketCallback
--------------

Socket-based callback for notification interactions.

.. autoclass:: gntplib.SocketCallback
   :members:
   :special-members: __init__, __call__, __repr__
   :show-inheritance:

   .. rubric:: Attributes

   .. attribute:: context
      
      Callback context value (default: 'None').

   .. attribute:: context_type
      
      Type of context (default: 'None').

   .. attribute:: on_click_callback
      
      Function called on click event.

   .. attribute:: on_close_callback
      
      Function called on close event.

   .. attribute:: on_timeout_callback
      
      Function called on timeout event.

   .. rubric:: Methods

   .. automethod:: on_click
   .. automethod:: on_close
   .. automethod:: on_timeout

   .. rubric:: Example

   .. code-block:: python

      from gntplib import SocketCallback

      def handle_click(response):
          print("Notification clicked!")
          context = response.headers.get('Notification-Callback-Context')
          print(f"Context: {context}")

      def handle_close(response):
          print("Notification closed")

      callback = SocketCallback(
          context='action-123',
          context_type='user-action',
          on_click=handle_click,
          on_close=handle_close
      )

      publisher.publish(
          'event',
          'Interactive',
          'Click me!',
          gntp_callback=callback
      )

URLCallback
-----------

URL-based callback for notification interactions.

.. autoclass:: gntplib.models.URLCallback
   :members:
   :special-members: __init__, __repr__
   :show-inheritance:

   .. rubric:: Attributes

   .. attribute:: url
      
      URL to be called on interaction.

   .. rubric:: Example

   .. code-block:: python

      from gntplib.models import URLCallback

      callback = URLCallback('https://example.com/notify')

      publisher.publish(
          'event',
          'Click to visit',
          'Open website',
          gntp_callback=callback
      )


