===================
Core API Reference
===================

This page documents the core classes and functions of gntplib.

Quick Functions
===============

These convenience functions provide the simplest way to use gntplib.

.. autofunction:: gntplib.publish

.. autofunction:: gntplib.subscribe

Publisher Class
===============

The main class for sending notifications.

.. autoclass:: gntplib.Publisher
   :members:
   :inherited-members:
   :special-members: __init__
   :show-inheritance:

   .. rubric:: Methods

   .. automethod:: register
      :no-index:

   .. automethod:: publish
      :no-index:

   .. rubric:: Example

   .. code-block:: python

      from gntplib import Publisher, Event

      events = [Event('update', 'Update Available')]
      publisher = Publisher('MyApp', events)
      publisher.register()
      publisher.publish('update', 'New Version', 'v2.0 released')

Subscriber Class
================

For subscribing to notifications from a GNTP hub.

.. autoclass:: gntplib.Subscriber
   :members:
   :inherited-members:
   :special-members: __init__
   :show-inheritance:

   .. rubric:: Methods

   .. automethod:: subscribe
      :no-index:

   .. automethod:: store_ttl
      :no-index:

   .. rubric:: Example

   .. code-block:: python

      from gntplib import Subscriber

      subscriber = Subscriber(
          id_='unique-id',
          name='MySubscriber',
          hub='hub.example.com',
          password='secret'
      )
      subscriber.subscribe()
      print(f"TTL: {subscriber.ttl} seconds")

Authentication & Encryption
===========================

Keys Module
-----------

.. automodule:: gntplib.keys
   :members:
   :exclude-members: algorithm_id
   :show-inheritance:

   .. rubric:: Hash Algorithms

   .. autodata:: gntplib.keys.MD5
      :annotation: = Algorithm('MD5', 16)
      :no-index:

   .. autodata:: gntplib.keys.SHA1
      :annotation: = Algorithm('SHA1', 20)
      :no-index:

   .. autodata:: gntplib.keys.SHA256
      :annotation: = Algorithm('SHA256', 32)
      :no-index:

   .. autodata:: gntplib.keys.SHA512
      :annotation: = Algorithm('SHA512', 64)
      :no-index:

Key Class
~~~~~~~~~

.. autoclass:: gntplib.keys.Key
   :members:
   :special-members: __init__
   :show-inheritance:

   .. rubric:: Properties

   .. autoproperty:: salt_hex
      :no-index:

   .. autoproperty:: key_hex
      :no-index:

   .. autoproperty:: key_hash_hex
      :no-index:

   .. rubric:: Methods

   .. automethod:: verify_password
      :no-index:

   .. rubric:: Example

   .. code-block:: python

      from gntplib.keys import SHA256

      key = SHA256.key('my-password')
      print(f"Key hash: {key.key_hash_hex}")

Ciphers Module
--------------

.. automodule:: gntplib.ciphers
   :members:
   :show-inheritance:

   .. rubric:: Encryption Algorithms

   .. autodata:: gntplib.ciphers.AES
      :annotation: = Algorithm('AES', 24)
      :no-index:

   .. autodata:: gntplib.ciphers.DES
      :annotation: = Algorithm('DES', 8)
      :no-index:

   .. autodata:: gntplib.ciphers.DES3
      :annotation: = Algorithm('3DES', 24)
      :no-index:

Cipher Class
~~~~~~~~~~~~

.. autoclass:: gntplib.ciphers.Cipher
   :members:
   :special-members: __init__
   :show-inheritance:

   .. rubric:: Properties

   .. autoproperty:: iv_hex
      :no-index:

   .. rubric:: Methods

   .. automethod:: encrypt
      :no-index:

   .. automethod:: decrypt
      :no-index:

   .. rubric:: Example

   .. code-block:: python

      from gntplib.keys import SHA256
      from gntplib.ciphers import AES

      key = SHA256.key('password')
      cipher = AES.cipher(key)
      
      encrypted = cipher.encrypt(b'secret data')
      decrypted = cipher.decrypt(encrypted)

Client & Connection
===================

GNTP Client
-----------

.. autoclass:: gntplib.connections.GNTPClient
   :members:
   :special-members: __init__
   :show-inheritance:

   .. rubric:: Methods

   .. automethod:: process_request
      :no-index:

   .. rubric:: Example

   .. code-block:: python

      from gntplib.connections import GNTPClient
      from gntplib.requests import RegisterRequest
      from gntplib import Event

      client = GNTPClient(
          host='localhost',
          port=23053,
          password='secret',
          key_hashing=SHA256,
          encryption=AES
      )

      request = RegisterRequest('MyApp', None, [Event('test')])
      client.process_request(request)

GNTP Connection
---------------

.. autoclass:: gntplib.connections.GNTPConnection
   :members:
   :special-members: __init__
   :show-inheritance:

   .. rubric:: Methods

   .. automethod:: write_message
   .. automethod:: read_message
   .. automethod:: close

Base Connection
---------------

.. autoclass:: gntplib.connections.BaseGNTPConnection
   :members:
   :show-inheritance:

   .. rubric:: Callback Methods

   .. automethod:: on_ok_message
   .. automethod:: on_callback_message

Utility Functions
=================

Message Generation
------------------

.. autofunction:: gntplib.connections.generate_messages

   .. rubric:: Example

   .. code-block:: python

      import socket
      from gntplib.connections import generate_messages

      sock = socket.create_connection(('localhost', 23053))
      sock.send(request_message)
      
      for message in generate_messages(sock):
          print(f"Received: {message}")
          break

Response Parsing
----------------

.. autofunction:: gntplib.requests.parse_response
   :no-index:

   .. rubric:: Example

   .. code-block:: python

      from gntplib.requests import parse_response

      message = b'GNTP/1.0 -OK NONE\r\nResponse-Action: REGISTER\r\n\r\n'
      response = parse_response(message, expected_type='-OK')
      print(response.headers)

Constants
=========

Protocol Constants
------------------

.. automodule:: gntplib.constants
   :members:
   :undoc-members:

   .. rubric:: Network Defaults

   .. autodata:: DEFAULT_PORT
      :annotation: = 23053

   .. autodata:: DEFAULT_TIMEOUT
      :annotation: = 10.0

   .. autodata:: DEFAULT_TTL
      :annotation: = 60

   .. rubric:: Message Limits

   .. autodata:: MAX_MESSAGE_SIZE
      :annotation: = 4096

   .. autodata:: MAX_LINE_SIZE
      :annotation: = 1024

   .. rubric:: Delimiters

   .. autodata:: LINE_DELIMITER
      :annotation: = b'\r\n'

   .. autodata:: MESSAGE_DELIMITER
      :annotation: = b'\r\n\r\n'

   .. rubric:: Priority Levels

   .. autodata:: PRIORITY_VERY_LOW
      :annotation: = -2

   .. autodata:: PRIORITY_LOW
      :annotation: = -1

   .. autodata:: PRIORITY_NORMAL
      :annotation: = 0

   .. autodata:: PRIORITY_HIGH
      :annotation: = 1

   .. autodata:: PRIORITY_EMERGENCY
      :annotation: = 2

   .. rubric:: Response Types

   .. autodata:: RESPONSE_OK
      :annotation: = '-OK'

   .. autodata:: RESPONSE_ERROR
      :annotation: = '-ERROR'

   .. autodata:: RESPONSE_CALLBACK
      :annotation: = '-CALLBACK'

Utility Functions
-----------------

.. autofunction:: gntplib.constants.random_bytes

.. autofunction:: gntplib.constants.random_hex_string

.. autofunction:: gntplib.constants.encode_utf8

.. autofunction:: gntplib.constants.decode_utf8

.. autofunction:: gntplib.constants.validate_priority

   .. rubric:: Example

   .. code-block:: python

      from gntplib.constants import validate_priority

      # Clamps to valid range [-2, 2]
      priority = validate_priority(10)  # Returns 2
      priority = validate_priority(-5)  # Returns -2

Helper Functions
----------------

.. autofunction:: gntplib.lib.coerce_to_events

   .. rubric:: Example

   .. code-block:: python

      from gntplib.lib import coerce_to_events
      from gntplib import Event

      # Mixed event definitions
      events = coerce_to_events([
          'simple_event',              # String
          ('named_event', False),      # Tuple (name, enabled)
          Event('full_event', icon=icon)  # Event object
      ])

.. autofunction:: gntplib.lib.coerce_to_callback

   .. rubric:: Example

   .. code-block:: python

      from gntplib.lib import coerce_to_callback

      # URL callback
      callback = coerce_to_callback('https://example.com/notify')

      # Socket callback
      callback = coerce_to_callback(
          on_click=handle_click,
          on_close=handle_close
      )

See Also
========

* :doc:`models` - Data models (Event, Resource, Notification)
* :doc:`requests` - Request and Response classes
* :doc:`exceptions` - Exception classes
* :doc:`async` - Asynchronous API