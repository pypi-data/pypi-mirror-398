================================
Asynchronous Usage with Tornado
================================

This guide covers using gntplib's asynchronous API with Tornado for non-blocking operations.

Prerequisites
=============

Install Tornado
---------------

.. code-block:: bash

   pip install gntplib[async]

Or install Tornado separately:

.. code-block:: bash

   pip install tornado

Requirements
------------

* Python 3.7 or higher (for async/await support)
* Tornado 5.0 or higher

Why Async?
==========

Asynchronous operations are beneficial when:

* Your application is already using Tornado
* You need to fetch remote resources (icons from URLs)
* You're sending many notifications concurrently
* You want non-blocking I/O in web applications

Basic Async Usage
=================

Simple Async Notification
--------------------------

.. code-block:: python

   import asyncio
   from gntplib.async_gntp import AsyncPublisher
   from gntplib import Event
   
   async def send_notification():
       # Create async publisher
       events = [Event('message', 'New Message')]
       publisher = AsyncPublisher('AsyncApp', events)
       
       # Register
       publisher.register()
       
       # Send notification
       publisher.publish(
           'message',
           'Hello Async',
           'This is an async notification'
       )
   
   # Run
   asyncio.run(send_notification())

.. note::
   The actual GNTP communication is still synchronous, but resource fetching 
   can be done asynchronously.

Async Resource Fetching
========================

The main advantage of async is fetching remote resources concurrently.

Single Async Resource
----------------------

.. code-block:: python

   import asyncio
   from gntplib.async_gntp import AsyncPublisher, AsyncResource
   from gntplib import Event
   
   async def main():
       # Create async resource from URL
       icon = AsyncResource('https://example.com/icon.png')
       
       # Create publisher with async icon
       events = [Event('update', 'Update Available')]
       publisher = AsyncPublisher('UpdateApp', events, icon=icon)
       
       # Register (will fetch icon asynchronously first)
       publisher.register()
       
       # Send notification
       publisher.publish(
           'update',
           'New Version',
           'Version 2.0 is available'
       )
   
   asyncio.run(main())

Multiple Async Resources
-------------------------

Fetch multiple resources in parallel:

.. code-block:: python

   import asyncio
   from gntplib.async_gntp import AsyncPublisher, AsyncResource
   from gntplib import Event
   
   async def main():
       # Create multiple async resources
       app_icon = AsyncResource('https://example.com/app.png')
       event_icon = AsyncResource('https://example.com/update.png')
       notif_icon = AsyncResource('https://example.com/alert.png')
       
       # All icons will be fetched in parallel
       events = [Event('update', icon=event_icon)]
       publisher = AsyncPublisher('App', events, icon=app_icon)
       publisher.register()
       
       # This notification will also fetch its icon
       publisher.publish(
           'update',
           'Alert',
           'Important message',
           icon=notif_icon
       )
   
   asyncio.run(main())

Manual Resource Fetching
-------------------------

For more control over resource fetching:

.. code-block:: python

   import asyncio
   from gntplib.async_gntp import (
       AsyncResource,
       fetch_async_resources_in_parallel
   )
   
   async def main():
       # Create resources
       resources = [
           AsyncResource('https://example.com/icon1.png'),
           AsyncResource('https://example.com/icon2.png'),
           AsyncResource('https://example.com/icon3.png'),
       ]
       
       # Fetch all in parallel
       print("Fetching resources...")
       await fetch_async_resources_in_parallel(resources)
       print("All resources fetched!")
       
       # Check results
       for i, resource in enumerate(resources, 1):
           if resource.data:
               print(f"Resource {i}: {len(resource.data)} bytes")
           else:
               print(f"Resource {i}: Failed to fetch")
   
   asyncio.run(main())

Integration with Tornado
========================

Tornado Web Application
------------------------

Integrate with Tornado web applications:

.. code-block:: python

   import tornado.ioloop
   import tornado.web
   from gntplib.async_gntp import AsyncPublisher
   from gntplib import Event
   
   # Initialize publisher globally
   events = [Event('user_action', 'User Action')]
   publisher = AsyncPublisher('WebApp', events)
   publisher.register()
   
   class NotificationHandler(tornado.web.RequestHandler):
       async def post(self):
           # Get data from request
           title = self.get_argument('title')
           message = self.get_argument('message')
           
           # Send notification
           publisher.publish('user_action', title, message)
           
           self.write({'status': 'sent'})
   
   def make_app():
       return tornado.web.Application([
           (r'/notify', NotificationHandler),
       ])
   
   if __name__ == '__main__':
       app = make_app()
       app.listen(8888)
       print("Server running on http://localhost:8888")
       tornado.ioloop.IOLoop.current().start()

With Background Tasks
---------------------

.. code-block:: python

   import tornado.ioloop
   from gntplib.async_gntp import AsyncPublisher
   from gntplib import Event
   
   class NotificationService:
       def __init__(self):
           events = [Event('system', 'System Event')]
           self.publisher = AsyncPublisher('BackgroundService', events)
           self.publisher.register()
       
       async def periodic_check(self):
           """Run periodic checks and notify."""
           while True:
               # Do some check
               status = await self.check_system()
               
               if status != 'ok':
                   self.publisher.publish(
                       'system',
                       'System Alert',
                       f'Status: {status}'
                   )
               
               # Wait before next check
               await tornado.gen.sleep(60)  # Check every minute
       
       async def check_system(self):
           """Simulate system check."""
           await tornado.gen.sleep(1)
           return 'ok'
   
   async def main():
       service = NotificationService()
       
       # Start periodic task
       tornado.ioloop.IOLoop.current().spawn_callback(service.periodic_check)
       
       # Keep running
       await tornado.gen.sleep(3600)  # Run for 1 hour
   
   if __name__ == '__main__':
       tornado.ioloop.IOLoop.current().run_sync(main)

Advanced Patterns
=================

Async Context Manager
---------------------

.. code-block:: python

   import asyncio
   from gntplib.async_gntp import AsyncPublisher
   from gntplib import Event
   
   class AsyncNotificationManager:
       def __init__(self, app_name, events):
           self.publisher = AsyncPublisher(app_name, events)
       
       async def __aenter__(self):
           """Async context manager entry."""
           self.publisher.register()
           return self
       
       async def __aexit__(self, *args):
           """Async context manager exit."""
           # Cleanup if needed
           pass
       
       def notify(self, event, title, message):
           """Send notification."""
           self.publisher.publish(event, title, message)
   
   async def main():
       events = [Event('test')]
       
       async with AsyncNotificationManager('AsyncApp', events) as nm:
           nm.notify('test', 'Hello', 'World')
           await asyncio.sleep(1)
   
   asyncio.run(main())

Batched Notifications
---------------------

Send multiple notifications efficiently:

.. code-block:: python

   import asyncio
   from gntplib.async_gntp import AsyncPublisher
   from gntplib import Event
   
   async def send_batch_notifications(notifications):
       """Send multiple notifications."""
       events = [Event('batch', 'Batch Notification')]
       publisher = AsyncPublisher('BatchApp', events)
       publisher.register()
       
       # Send all notifications
       tasks = []
       for title, message in notifications:
           # Create task for each
           task = asyncio.create_task(
               send_one(publisher, title, message)
           )
           tasks.append(task)
       
       # Wait for all
       await asyncio.gather(*tasks)
   
   async def send_one(publisher, title, message):
       """Send one notification with delay."""
       await asyncio.sleep(0.1)  # Small delay between sends
       publisher.publish('batch', title, message)
   
   async def main():
       notifications = [
           ('Notification 1', 'First message'),
           ('Notification 2', 'Second message'),
           ('Notification 3', 'Third message'),
       ]
       
       await send_batch_notifications(notifications)
   
   asyncio.run(main())

Error Handling
==============

Async Error Handling
--------------------

.. code-block:: python

   import asyncio
   from gntplib.async_gntp import AsyncPublisher, AsyncResource
   from gntplib import Event
   from gntplib.exceptions import GNTPError, GNTPResourceError
   
   async def safe_send_notification():
       """Send notification with comprehensive error handling."""
       try:
           # Try to fetch async resource
           icon = AsyncResource('https://example.com/icon.png')
           
           events = [Event('message')]
           publisher = AsyncPublisher('SafeApp', events, icon=icon)
           
           # Register
           publisher.register()
           
           # Send
           publisher.publish('message', 'Hello', 'World')
           
           return True
           
       except GNTPResourceError as e:
           print(f"Failed to fetch resource: {e}")
           # Continue without icon
           publisher = AsyncPublisher('SafeApp', events)
           publisher.register()
           publisher.publish('message', 'Hello', 'World')
           return True
           
       except GNTPError as e:
           print(f"GNTP error: {e}")
           return False
           
       except Exception as e:
           print(f"Unexpected error: {e}")
           return False
   
   async def main():
       success = await safe_send_notification()
       print(f"Result: {'Success' if success else 'Failed'}")
   
   asyncio.run(main())

Timeout Handling
----------------

.. code-block:: python

   import asyncio
   from gntplib.async_gntp import AsyncPublisher, AsyncResource
   from gntplib import Event
   
   async def fetch_with_timeout(url, timeout=5.0):
       """Fetch resource with timeout."""
       try:
           resource = AsyncResource(url)
           
           # Fetch with timeout
           await asyncio.wait_for(
               fetch_async_resources_in_parallel([resource]),
               timeout=timeout
           )
           
           return resource
           
       except asyncio.TimeoutError:
           print(f"Timeout fetching {url}")
           return None
   
   async def main():
       # Try to fetch with 5 second timeout
       icon = await fetch_with_timeout('https://example.com/icon.png', timeout=5.0)
       
       events = [Event('message')]
       if icon and icon.data:
           publisher = AsyncPublisher('App', events, icon=icon)
       else:
           publisher = AsyncPublisher('App', events)
       
       publisher.register()
       publisher.publish('message', 'Hello', 'World')
   
   asyncio.run(main())

Performance Tips
================

1. **Reuse Publishers**

   .. code-block:: python

      # Good: Create once, use many times
      publisher = AsyncPublisher('App', events)
      publisher.register()
      
      for i in range(100):
          publisher.publish('event', f'Message {i}', 'Content')

2. **Batch Resource Fetching**

   .. code-block:: python

      # Good: Fetch all resources in parallel
      resources = [AsyncResource(url) for url in urls]
      await fetch_async_resources_in_parallel(resources)

3. **Avoid Blocking Operations**

   .. code-block:: python

      # Bad: Blocking operation in async function
      async def bad():
          time.sleep(1)  # Blocks event loop!
      
      # Good: Use async sleep
      async def good():
          await asyncio.sleep(1)  # Non-blocking

Testing Async Code
==================

Using pytest-asyncio
--------------------

.. code-block:: python

   import pytest
   from gntplib.async_gntp import AsyncPublisher
   from gntplib import Event
   
   @pytest.mark.asyncio
   async def test_async_publisher():
       """Test async publisher."""
       events = [Event('test')]
       publisher = AsyncPublisher('TestApp', events)
       
       # This would need a mock GNTP server
       # For real tests, use mocking
       assert publisher is not None

Mocking
-------

.. code-block:: python

   import asyncio
   from unittest.mock import AsyncMock, patch
   from gntplib.async_gntp import AsyncPublisher
   from gntplib import Event
   
   async def test_with_mock():
       """Test with mocked client."""
       events = [Event('test')]
       
       with patch('gntplib.async_gntp.AsyncGNTPClient') as mock_client:
           mock_client.return_value.process_request = AsyncMock()
           
           publisher = AsyncPublisher('TestApp', events)
           publisher.register()
           
           # Verify registration was called
           assert mock_client.return_value.process_request.called
   
   asyncio.run(test_with_mock())

Migration from Sync
===================

Converting sync code to async:

.. code-block:: python

   # Before (Sync)
   from gntplib import Publisher, Event
   
   events = [Event('message')]
   publisher = Publisher('App', events)
   publisher.register()
   publisher.publish('message', 'Hello', 'World')
   
   # After (Async)
   import asyncio
   from gntplib.async_gntp import AsyncPublisher
   from gntplib import Event
   
   async def main():
       events = [Event('message')]
       publisher = AsyncPublisher('App', events)
       publisher.register()
       publisher.publish('message', 'Hello', 'World')
   
   asyncio.run(main())

Next Steps
==========

* Review :doc:`advanced` for authentication and encryption
* Check :doc:`../api/async` for complete async API reference
* See :doc:`security` for security best practices