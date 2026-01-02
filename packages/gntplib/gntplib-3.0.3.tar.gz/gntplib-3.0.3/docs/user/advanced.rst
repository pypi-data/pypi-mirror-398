==================
Advanced Features
==================

This guide covers advanced features of gntplib including authentication, 
encryption, callbacks, and custom headers.

Authentication
==============

GNTP supports password-based authentication using various hash algorithms.

Basic Authentication
--------------------

.. code-block:: python

   from gntplib import Publisher, Event
   from gntplib.keys import SHA256
   
   events = [Event('secure', 'Secure Notification')]
   
   publisher = Publisher(
       'SecureApp',
       events,
       host='localhost',
       password='my-secret-password',
       key_hashing=SHA256  # Use SHA256 hashing
   )
   
   publisher.register()
   publisher.publish('secure', 'Protected', 'This is authenticated')

Hash Algorithms
---------------

gntplib supports multiple hash algorithms:

.. code-block:: python

   from gntplib.keys import MD5, SHA1, SHA256, SHA512
   
   # MD5 - 128-bit (not recommended for security)
   publisher = Publisher('App', events, password='secret', key_hashing=MD5)
   
   # SHA1 - 160-bit (legacy support)
   publisher = Publisher('App', events, password='secret', key_hashing=SHA1)
   
   # SHA256 - 256-bit (recommended)
   publisher = Publisher('App', events, password='secret', key_hashing=SHA256)
   
   # SHA512 - 512-bit (maximum security)
   publisher = Publisher('App', events, password='secret', key_hashing=SHA512)

.. note::
   SHA256 is recommended for most use cases. It provides good security 
   with reasonable performance.

Encryption
==========

Encrypt GNTP messages for confidentiality.

Installing Encryption Support
------------------------------

First, install the encryption dependency:

.. code-block:: bash

   pip install gntplib[crypto]

Or manually:

.. code-block:: bash

   pip install pycryptodomex

Using Encryption
----------------

.. code-block:: python

   from gntplib import Publisher, Event
   from gntplib.keys import SHA256
   from gntplib.ciphers import AES
   
   events = [Event('encrypted', 'Encrypted Message')]
   
   publisher = Publisher(
       'EncryptedApp',
       events,
       password='my-secret-password',
       key_hashing=SHA256,
       encryption=AES  # Enable AES encryption
   )
   
   publisher.register()
   publisher.publish('encrypted', 'Secret', 'This message is encrypted')

Encryption Algorithms
---------------------

Available encryption algorithms:

.. code-block:: python

   from gntplib.ciphers import AES, DES, DES3
   
   # AES - 192-bit key (recommended)
   publisher = Publisher(
       'App', events,
       password='secret',
       key_hashing=SHA256,
       encryption=AES
   )
   
   # DES - 64-bit key (legacy, not recommended)
   publisher = Publisher(
       'App', events,
       password='secret',
       key_hashing=SHA256,
       encryption=DES
   )
   
   # 3DES - 192-bit key (legacy)
   publisher = Publisher(
       'App', events,
       password='secret',
       key_hashing=SHA256,
       encryption=DES3
   )

.. warning::
   DES is considered weak by modern standards. Use AES for new applications.

Key Size Compatibility
----------------------

The hash algorithm must produce a key large enough for the encryption algorithm:

.. code-block:: python

   from gntplib.keys import MD5, SHA256
   from gntplib.ciphers import AES, DES
   
   # ✓ Valid: SHA256 (256-bit) is large enough for AES (192-bit)
   publisher = Publisher(
       'App', events,
       password='secret',
       key_hashing=SHA256,  # 256-bit
       encryption=AES        # needs 192-bit
   )
   
   # ✓ Valid: MD5 (128-bit) is large enough for DES (64-bit)
   publisher = Publisher(
       'App', events,
       password='secret',
       key_hashing=MD5,  # 128-bit
       encryption=DES    # needs 64-bit
   )
   
   # ✗ Invalid: MD5 (128-bit) is too small for AES (192-bit)
   # This will raise GNTPError
   try:
       publisher = Publisher(
           'App', events,
           password='secret',
           key_hashing=MD5,  # 128-bit - too small!
           encryption=AES    # needs 192-bit
       )
   except Exception as e:
       print(f"Error: {e}")

Callbacks
=========

Callbacks allow your application to respond to user interactions with notifications.

Socket Callbacks
----------------

Socket callbacks provide the most control:

.. code-block:: python

   from gntplib import Publisher, Event, SocketCallback
   
   class NotificationHandler:
       def __init__(self):
           events = [Event('interactive', 'Interactive Notification')]
           self.publisher = Publisher('CallbackApp', events)
           self.publisher.register()
       
       def on_notification_clicked(self, response):
           """Called when user clicks the notification."""
           print("User clicked!")
           context = response.headers.get('Notification-Callback-Context')
           print(f"Context: {context}")
           
           # Perform action based on click
           if context == 'open-file':
               self.open_file()
           elif context == 'dismiss':
               self.dismiss()
       
       def on_notification_closed(self, response):
           """Called when notification is closed."""
           print("Notification closed by user")
       
       def on_notification_timeout(self, response):
           """Called when notification times out."""
           print("Notification timed out")
       
       def send_interactive_notification(self):
           """Send notification with callbacks."""
           callback = SocketCallback(
               context='open-file',
               context_type='action',
               on_click=self.on_notification_clicked,
               on_close=self.on_notification_closed,
               on_timeout=self.on_notification_timeout
           )
           
           self.publisher.publish(
               'interactive',
               'Action Required',
               'Click to open file',
               priority=1,
               gntp_callback=callback
           )
       
       def open_file(self):
           print("Opening file...")
       
       def dismiss(self):
           print("Dismissing...")
   
   # Usage
   handler = NotificationHandler()
   handler.send_interactive_notification()

URL Callbacks
-------------

Simpler callback using URLs:

.. code-block:: python

   from gntplib import Publisher, Event
   
   events = [Event('link', 'Link Notification')]
   publisher = Publisher('URLCallbackApp', events)
   publisher.register()
   
   # When clicked, GNTP server will request this URL
   publisher.publish(
       'link',
       'Website Update',
       'Click to view the new content',
       gntp_callback='https://example.com/notification-clicked'
   )

Callback Context
----------------

Pass data through callback context:

.. code-block:: python

   from gntplib import SocketCallback
   import json
   
   # Store complex data in context
   context_data = {
       'action': 'download',
       'file_id': 12345,
       'filename': 'document.pdf'
   }
   
   callback = SocketCallback(
       context=json.dumps(context_data),
       context_type='application/json',
       on_click=handle_click
   )
   
   def handle_click(response):
       # Parse context
       context_str = response.headers.get('Notification-Callback-Context')
       data = json.loads(context_str)
       
       # Use the data
       if data['action'] == 'download':
           download_file(data['file_id'], data['filename'])

Custom Headers
==============

Add custom metadata to notifications.

Custom Headers (X- prefix)
---------------------------

.. code-block:: python

   from gntplib import Publisher, Event
   
   events = [Event('custom', 'Custom Notification')]
   
   # Application-level custom headers
   custom_headers = [
       ('X-Environment', 'production'),
       ('X-Version', '2.0.1'),
       ('X-Region', 'us-east-1'),
   ]
   
   publisher = Publisher(
       'CustomApp',
       events,
       custom_headers=custom_headers
   )
   
   publisher.register()
   
   # Notification-level custom headers (not commonly supported)
   publisher.publish(
       'custom',
       'Custom Event',
       'With custom metadata'
   )

App-Specific Headers (Data- prefix)
------------------------------------

.. code-block:: python

   # Application-specific data
   app_headers = [
       ('Data-UserID', '12345'),
       ('Data-SessionID', 'abc-def-ghi'),
       ('Data-Department', 'Engineering'),
   ]
   
   publisher = Publisher(
       'DataApp',
       events,
       app_specific_headers=app_headers
   )
   
   publisher.register()

Resource Management
===================

Efficiently handle binary resources like icons.

Embedded vs URL Resources
--------------------------

.. code-block:: python

   from gntplib import Resource
   
   # Embedded resource (binary data)
   # More reliable but increases message size
   with open('icon.png', 'rb') as f:
       embedded = Resource(data=f.read())
   
   # URL resource (reference)
   # Smaller message but may not work on all servers
   url = Resource(url='https://example.com/icon.png')
   
   # Convenience methods
   embedded2 = Resource.from_file('icon.png')
   url2 = Resource.from_url('https://example.com/icon.png')

Resource Caching
----------------

Resources are identified by their MD5 hash. Send the same resource 
multiple times efficiently:

.. code-block:: python

   from gntplib import Publisher, Event, Resource
   
   # Load icon once
   icon = Resource.from_file('app_icon.png')
   
   events = [Event('message', icon=icon)]
   publisher = Publisher('App', events, icon=icon)
   publisher.register()
   
   # Icon is sent only once during registration
   # Subsequent notifications reference it by hash
   for i in range(10):
       publisher.publish(
           'message',
           f'Message {i}',
           'Content',
           icon=icon  # References same icon efficiently
       )

Large Resources
---------------

For large resources, consider:

.. code-block:: python

   from gntplib import Resource
   import io
   from PIL import Image
   
   def create_thumbnail(image_path, max_size=(64, 64)):
       """Create small thumbnail for notification."""
       img = Image.open(image_path)
       img.thumbnail(max_size, Image.Resampling.LANCZOS)
       
       # Save to bytes
       buffer = io.BytesIO()
       img.save(buffer, format='PNG')
       buffer.seek(0)
       
       return Resource(data=buffer.read())
   
   # Use thumbnail instead of full image
   icon = create_thumbnail('large_image.jpg')
   publisher = Publisher('App', events, icon=icon)

Connection Management
=====================

Advanced connection configuration.

Timeouts
--------

.. code-block:: python

   from gntplib import Publisher, Event
   
   events = [Event('test')]
   
   # Custom timeout (default is 10 seconds)
   publisher = Publisher(
       'App',
       events,
       timeout=30.0  # 30 seconds
   )

Connection Errors
-----------------

Handle connection failures gracefully:

.. code-block:: python

   from gntplib import Publisher, Event
   from gntplib.exceptions import (
       GNTPConnectionError,
       GNTPAuthenticationError,
       GNTPResponseError
   )
   import time
   
   def send_with_retry(publisher, event, title, text, max_retries=3):
       """Send notification with automatic retry."""
       for attempt in range(max_retries):
           try:
               publisher.publish(event, title, text)
               return True
           
           except GNTPConnectionError as e:
               print(f"Connection failed (attempt {attempt + 1}): {e}")
               if attempt < max_retries - 1:
                   time.sleep(2 ** attempt)  # Exponential backoff
               continue
           
           except GNTPAuthenticationError as e:
               print(f"Authentication failed: {e}")
               return False  # Don't retry auth errors
           
           except GNTPResponseError as e:
               print(f"Server error: {e}")
               return False
       
       return False
   
   # Usage
   events = [Event('message')]
   publisher = Publisher('ResilientApp', events)
   publisher.register()
   
   success = send_with_retry(
       publisher,
       'message',
       'Important',
       'This will retry on failure'
   )

Multiple Servers
----------------

Send to multiple GNTP servers:

.. code-block:: python

   from gntplib import Publisher, Event
   
   class MultiServerPublisher:
       def __init__(self, app_name, events, servers):
           """
           Args:
               servers: List of (host, port) tuples
           """
           self.publishers = []
           
           for host, port in servers:
               pub = Publisher(
                   app_name,
                   events,
                   host=host,
                   port=port
               )
               pub.register()
               self.publishers.append(pub)
       
       def publish(self, *args, **kwargs):
           """Publish to all servers."""
           for publisher in self.publishers:
               try:
                   publisher.publish(*args, **kwargs)
               except Exception as e:
                   print(f"Failed to publish to {publisher}: {e}")
   
   # Usage
   events = [Event('message')]
   multi_pub = MultiServerPublisher(
       'MultiApp',
       events,
       servers=[
           ('192.168.1.100', 23053),
           ('192.168.1.101', 23053),
       ]
   )
   
   multi_pub.publish('message', 'Hello', 'Sent to multiple servers')

Subscriptions
=============

Subscribe to notifications from a hub.

Basic Subscription
------------------

.. code-block:: python

   from gntplib import Subscriber
   
   # Subscribe to hub
   subscriber = Subscriber(
       id_='unique-subscriber-id',
       name='MySubscriber',
       hub='hub.example.com',  # Hub address
       password='hub-password',
       port=23053  # Your port for receiving notifications
   )
   
   # Send subscription request
   subscriber.subscribe()
   
   # Check subscription TTL
   print(f"Subscription TTL: {subscriber.ttl} seconds")

Subscription with Callback
--------------------------

.. code-block:: python

   def handle_subscription(response):
       """Handle subscription response."""
       ttl = response.headers.get('Subscription-TTL')
       print(f"Subscribed successfully! TTL: {ttl} seconds")
   
   subscriber.subscribe(callback=handle_subscription)

Renewal
-------

Subscriptions expire after TTL. Renew before expiration:

.. code-block:: python

   import time
   import threading
   
   class ManagedSubscriber:
       def __init__(self, *args, **kwargs):
           self.subscriber = Subscriber(*args, **kwargs)
           self.running = False
       
       def start(self):
           """Start subscription with auto-renewal."""
           self.running = True
           self.subscriber.subscribe()
           
           # Start renewal thread
           renewal_thread = threading.Thread(target=self._renewal_loop)
           renewal_thread.daemon = True
           renewal_thread.start()
       
       def stop(self):
           """Stop subscription."""
           self.running = False
       
       def _renewal_loop(self):
           """Automatically renew subscription."""
           while self.running:
               # Sleep until 80% of TTL
               sleep_time = self.subscriber.ttl * 0.8
               time.sleep(sleep_time)
               
               if self.running:
                   try:
                       self.subscriber.subscribe()
                       print(f"Renewed subscription (TTL: {self.subscriber.ttl}s)")
                   except Exception as e:
                       print(f"Failed to renew: {e}")

Next Steps
==========

* Learn about :doc:`async` - Async/await support
* Check :doc:`security` - Security best practices
* See :doc:`../api/core` - Complete API reference