=========================
Exceptions API Reference
=========================

This page documents all exception classes in gntplib.

Exception Hierarchy
===================

All gntplib exceptions inherit from ``GNTPError``:

.. code-block:: text

   GNTPError
   ├── GNTPConnectionError
   ├── GNTPAuthenticationError
   ├── GNTPEncryptionError
   ├── GNTPProtocolError
   ├── GNTPResponseError
   ├── GNTPResourceError
   └── GNTPValidationError

Base Exception
==============

.. autoexception:: gntplib.exceptions.GNTPError
   :members:
   :special-members: __init__, __str__
   :show-inheritance:

   .. rubric:: Attributes

   .. attribute:: message
      
      Primary error message.

   .. attribute:: details
      
      Optional additional details.

   .. attribute:: original_message
      
      Original GNTP message that caused error (if applicable).

   .. rubric:: Example

   .. code-block:: python

      from gntplib.exceptions import GNTPError

      try:
          publisher.register()
      except GNTPError as e:
          print(f"Error: {e}")
          if e.details:
              print(f"Details: {e.details}")

Specific Exceptions
===================

Connection Errors
-----------------

.. autoexception:: gntplib.exceptions.GNTPConnectionError
   :show-inheritance:

   Raised when connection to GNTP server fails.

   **Common causes:**

   * Server not running
   * Wrong host/port
   * Network issues
   * Firewall blocking connection

   .. rubric:: Example

   .. code-block:: python

      from gntplib.exceptions import GNTPConnectionError
      import time

      max_retries = 3
      for attempt in range(max_retries):
          try:
              publisher.register()
              break
          except GNTPConnectionError as e:
              print(f"Attempt {attempt + 1} failed: {e}")
              if attempt < max_retries - 1:
                  time.sleep(2)

Authentication Errors
---------------------

.. autoexception:: gntplib.exceptions.GNTPAuthenticationError
   :show-inheritance:

   Raised when authentication fails.

   **Common causes:**

   * Wrong password
   * Incompatible hash algorithm
   * Server doesn't require/support authentication

   .. rubric:: Example

   .. code-block:: python

      from gntplib.exceptions import GNTPAuthenticationError

      try:
          publisher = Publisher(
              'App',
              events,
              password='wrong-password'
          )
          publisher.register()
      except GNTPAuthenticationError as e:
          print(f"Authentication failed: {e}")

Encryption Errors
-----------------

.. autoexception:: gntplib.exceptions.GNTPEncryptionError
   :show-inheritance:

   Raised when encryption operations fail.

   **Common causes:**

   * PyCryptodome not installed
   * Key size mismatch
   * Invalid cipher parameters

   .. rubric:: Example

   .. code-block:: python

      from gntplib.exceptions import GNTPEncryptionError
      from gntplib.keys import MD5
      from gntplib.ciphers import AES

      try:
          # MD5 (128-bit) too small for AES (192-bit)
          publisher = Publisher(
              'App',
              events,
              password='secret',
              key_hashing=MD5,
              encryption=AES
          )
      except GNTPEncryptionError as e:
          print(f"Encryption error: {e}")

Protocol Errors
---------------

.. autoexception:: gntplib.exceptions.GNTPProtocolError
   :show-inheritance:

   Raised when GNTP protocol violations detected.

   **Common causes:**

   * Malformed messages
   * Unsupported version
   * Invalid headers

   .. rubric:: Example

   .. code-block:: python

      from gntplib.exceptions import GNTPProtocolError
      from gntplib.requests import parse_response

      try:
          response = parse_response(malformed_message)
      except GNTPProtocolError as e:
          print(f"Protocol error: {e}")

Response Errors
---------------

.. autoexception:: gntplib.exceptions.GNTPResponseError
   :members:
   :special-members: __init__
   :show-inheritance:

   Raised when server returns error response.

   .. rubric:: Additional Attributes

   .. attribute:: error_code
      
      Error code from server.

   .. attribute:: error_description
      
      Human-readable error from server.

   .. rubric:: Example

   .. code-block:: python

      from gntplib.exceptions import GNTPResponseError

      try:
          publisher.publish('unknown_event', 'Title', 'Text')
      except GNTPResponseError as e:
          print(f"Server error: {e.error_code}")
          print(f"Description: {e.error_description}")

Resource Errors
---------------

.. autoexception:: gntplib.exceptions.GNTPResourceError
   :show-inheritance:

   Raised when resource operations fail.

   **Common causes:**

   * Failed to fetch remote resource
   * Invalid resource data
   * File not found

   .. rubric:: Example

   .. code-block:: python

      from gntplib.exceptions import GNTPResourceError
      from gntplib import Resource

      try:
          icon = Resource.from_file('missing.png')
      except GNTPResourceError as e:
          print(f"Resource error: {e}")

Validation Errors
-----------------

.. autoexception:: gntplib.exceptions.GNTPValidationError
   :show-inheritance:

   Raised when input validation fails.

   **Common causes:**

   * Empty required fields
   * Invalid parameter values
   * Type mismatches

   .. rubric:: Example

   .. code-block:: python

      from gntplib.exceptions import GNTPValidationError
      from gntplib import Event, Publisher

      try:
          # Empty name not allowed
          event = Event('')
      except GNTPValidationError as e:
          print(f"Validation error: {e}")

      try:
          # No events defined
          publisher = Publisher('App', [])
      except GNTPValidationError as e:
          print(f"Validation error: {e}")

Error Handling Best Practices
==============================

Catch Specific Exceptions
--------------------------

.. code-block:: python

   from gntplib.exceptions import (
       GNTPConnectionError,
       GNTPAuthenticationError,
       GNTPError
   )

   try:
       publisher.register()
       publisher.publish('event', 'Title', 'Message')
   
   except GNTPConnectionError:
       # Handle connection issues
       log.error("Cannot connect to GNTP server")
   
   except GNTPAuthenticationError:
       # Handle auth issues
       log.error("Authentication failed")
   
   except GNTPError as e:
       # Catch-all for other GNTP errors
       log.error(f"GNTP error: {e}")
   
   except Exception as e:
       # Unexpected errors
       log.exception("Unexpected error")

Retry Logic
-----------

.. code-block:: python

   import time
   from gntplib.exceptions import GNTPConnectionError

   def send_with_retry(publisher, *args, max_retries=3, **kwargs):
       """Send notification with automatic retry."""
       for attempt in range(max_retries):
           try:
               publisher.publish(*args, **kwargs)
               return True
           except GNTPConnectionError:
               if attempt < max_retries - 1:
                   time.sleep(2 ** attempt)  # Exponential backoff
                   continue
               raise
       return False

Graceful Degradation
--------------------

.. code-block:: python

   from gntplib.exceptions import GNTPError

   def notify_user(title, message):
       """Notify with fallback to console."""
       try:
           publisher.publish('event', title, message)
       except GNTPError:
           # Fallback to console
           print(f"[{title}] {message}")

See Also
========

* :doc:`core` - Core API reference
* :doc:`models` - Data models
* :doc:`../user/advanced` - Advanced error handling