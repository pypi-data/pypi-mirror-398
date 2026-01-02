==========
Quickstart
==========

This guide will get you up and running with gntplib in minutes.

Before You Start
================

Make sure you have:

1. Python 3.7 or higher installed
2. gntplib installed (see :doc:`installation`)
3. A GNTP server running (e.g., Growl, Growl for Windows, or compatible)

.. note::
   If you don't have a GNTP server, you can still follow along. 
   Connection errors are expected without a server.

Your First Notification
=======================

The simplest way to send a notification:

.. code-block:: python

   from gntplib import publish
   
   publish('MyApp', 'Alert', 'Hello World', 'This is my first notification!')

That's it! This one line:

1. Creates an application named "MyApp"
2. Defines an event type called "Alert"
3. Registers the application
4. Sends a notification with title "Hello World"

Understanding the Basics
========================

The ``publish()`` function is a convenience wrapper. Here's what it does:

.. code-block:: python

   from gntplib import Publisher, Event
   
   # Create a publisher with one event type
   publisher = Publisher('MyApp', [Event('Alert')])
   
   # Register with the GNTP server
   publisher.register()
   
   # Send a notification
   publisher.publish('Alert', 'Hello World', 'This is my first notification!')

Working with Events
===================

Events define the types of notifications your app can send.

Single Event
------------

.. code-block:: python

   from gntplib import Publisher, Event
   
   # Create one event
   events = [Event('Message', 'New Message')]
   
   publisher = Publisher('ChatApp', events)
   publisher.register()
   publisher.publish('Message', 'John Doe', 'Hey, how are you?')

Multiple Events
---------------

.. code-block:: python

   from gntplib import Event, Publisher
   
   # Define multiple event types
   events = [
       Event('message', 'New Message', enabled=True),
       Event('call', 'Incoming Call', enabled=True),
       Event('update', 'App Update', enabled=False),  # Disabled by default
   ]
   
   publisher = Publisher('ChatApp', events)
   publisher.register()
   
   # Send different types of notifications
   publisher.publish('message', 'John', 'Hello!')
   publisher.publish('call', 'Jane Doe', 'is calling...')
   publisher.publish('update', 'Version 2.0', 'New features available')

Adding Icons
============

Icons make notifications more recognizable.

From File
---------

.. code-block:: python

   from gntplib import Publisher, Event, Resource
   
   # Load icon from file
   app_icon = Resource.from_file('app_icon.png')
   event_icon = Resource.from_file('message_icon.png')
   
   # Use in publisher
   events = [Event('message', icon=event_icon)]
   publisher = Publisher('ChatApp', events, icon=app_icon)
   publisher.register()
   
   # Icon from another file for specific notification
   notification_icon = Resource.from_file('alert.png')
   publisher.publish('message', 'Alert', 'Important!', icon=notification_icon)

From URL
--------

.. code-block:: python

   from gntplib import Resource
   
   # Icon from URL
   icon = Resource(url='https://example.com/icon.png')
   
   publisher = Publisher('MyApp', events, icon=icon)

.. note::
   URL icons may not work on all GNTP servers. Embedded icons are more reliable.

Simple Way
-----------

.. code-block:: python

   from gntplib import publish, Resource
   
   icon = Resource('icon.png') # auto detection from file/URL/data/base64
   
   publish(
       'MyApp',
       'Info',
       'This is a notification with an icon',
       'Check it out!',
       icon=icon
   )

Notification Options
====================

Priority Levels
---------------

Set notification importance:

.. code-block:: python

   # Very Low: -2
   publisher.publish('update', 'Background', 'Update complete', priority=-2)
   
   # Low: -1
   publisher.publish('info', 'FYI', 'Something happened', priority=-1)
   
   # Normal: 0 (default)
   publisher.publish('message', 'New Message', 'Hello', priority=0)
   
   # High: 1
   publisher.publish('warning', 'Warning', 'Check this out', priority=1)
   
   # Emergency: 2
   publisher.publish('alert', 'Critical', 'Action required!', priority=2)

Sticky Notifications
--------------------

Make notifications stay until dismissed:

.. code-block:: python

   publisher.publish(
       'alert',
       'Important',
       'Please read this carefully',
       sticky=True
   )

Notification IDs
----------------

Use IDs to track or update notifications:

.. code-block:: python

   # Send with ID
   publisher.publish(
       'download',
       'Downloading',
       'File1.zip - 0%',
       id_='download-1'
   )
   
   # Update same notification
   publisher.publish(
       'download',
       'Downloading',
       'File1.zip - 50%',
       id_='download-2',
       coalescing_id='download-1'  # Groups with previous
   )

Combining Options
-----------------

.. code-block:: python

   from gntplib import Resource
   
   icon = Resource.from_file('urgent.png')
   
   publisher.publish(
       'alert',
       'System Critical',
       'Server is down! Immediate action required.',
       priority=2,        # Emergency
       sticky=True,       # Stays visible
       icon=icon,         # Custom icon
       id_='alert-001'    # Trackable ID
   )

Connecting to Remote Servers
=============================

By default, gntplib connects to ``localhost:23053``. To use a different server:

.. code-block:: python

   from gntplib import Publisher, Event
   
   events = [Event('message')]
   publisher = Publisher(
       'MyApp',
       events,
       host='192.168.1.100',
       port=23053
   )
   publisher.register()
   publisher.publish('message', 'Remote', 'Notification on remote server')

Error Handling
==============

Always handle potential errors:

.. code-block:: python

   from gntplib import Publisher, Event
   from gntplib.exceptions import GNTPError, GNTPConnectionError
   
   try:
       publisher = Publisher('MyApp', [Event('test')])
       publisher.register()
       publisher.publish('test', 'Hello', 'World')
       print("✓ Notification sent successfully")
       
   except GNTPConnectionError as e:
       print(f"✗ Cannot connect to GNTP server: {e}")
       
   except GNTPError as e:
       print(f"✗ GNTP error: {e}")
       
   except Exception as e:
       print(f"✗ Unexpected error: {e}")

Complete Example
================

Here's a complete, production-ready example:

.. code-block:: python

   #!/usr/bin/env python3
   """Example: Download notification system."""
   
   from gntplib import Publisher, Event, Resource
   from gntplib.exceptions import GNTPConnectionError
   import time
   
   def main():
       # Define events
       events = [
           Event('start', 'Download Started'),
           Event('progress', 'Download Progress'),
           Event('complete', 'Download Complete'),
           Event('error', 'Download Error'),
       ]
       
       # Create publisher
       try:
           icon = Resource.from_file('download.png')
           publisher = Publisher('DownloadManager', events, icon=icon)
           publisher.register()
           print("✓ Registered with GNTP server")
       except GNTPConnectionError:
           print("✗ GNTP server not available")
           return
       
       # Simulate download
       filename = "large_file.zip"
       
       # Start notification
       publisher.publish(
           'start',
           'Download Started',
           f'{filename} - Starting download...'
       )
       
       # Progress notifications
       for progress in [25, 50, 75]:
           time.sleep(1)
           publisher.publish(
               'progress',
               'Downloading',
               f'{filename} - {progress}% complete',
               id_=f'download-{progress}'
           )
       
       # Complete notification
       time.sleep(1)
       publisher.publish(
           'complete',
           'Download Complete',
           f'{filename} - Ready to use!',
           priority=1,
           sticky=True
       )
       
       print("✓ All notifications sent")
   
   if __name__ == '__main__':
       main()

Next Steps
==========

Now that you know the basics:

* Read the :doc:`tutorial` for more detailed examples
* Learn about :doc:`advanced` features like authentication and encryption
* Explore :doc:`async` usage with Tornado
* Check the :doc:`../api/core` for complete API documentation

Common Patterns
===============

Send and Forget
----------------

For simple notifications where you don't need callbacks:

.. code-block:: python

   from gntplib import publish
   
   publish('MyApp', 'info', 'Quick notification', 'Simple message')

Reusable Publisher
------------------

For applications that send multiple notifications:

.. code-block:: python

   from gntplib import Publisher, Event
   
   # Initialize once
   publisher = Publisher('MyApp', [Event('info')])
   publisher.register()
   
   # Use multiple times
   def notify(title, message):
       publisher.publish('info', title, message)
   
   notify('Event 1', 'First notification')
   notify('Event 2', 'Second notification')

Context Manager (Advanced)
---------------------------

.. code-block:: python

   from gntplib import Publisher, Event
   
   class NotificationManager:
       def __init__(self):
           self.publisher = Publisher('MyApp', [Event('info')])
       
       def __enter__(self):
           self.publisher.register()
           return self
       
       def __exit__(self, *args):
           pass  # Cleanup if needed
       
       def notify(self, title, message):
           self.publisher.publish('info', title, message)
   
   # Usage
   with NotificationManager() as nm:
       nm.notify('Hello', 'World')