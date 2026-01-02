========
Security
========

This guide covers security best practices when using gntplib.

Authentication
==============

Always Use Strong Passwords
----------------------------

.. code-block:: python

   # ✗ Bad: Weak password
   publisher = Publisher('App', events, password='123456')

   # ✓ Good: Strong random password
   import secrets
   password = secrets.token_urlsafe(32)
   publisher = Publisher('App', events, password=password)

Use SHA256 or SHA512
---------------------

.. code-block:: python

   from gntplib.keys import SHA256, SHA512

   # ✓ Recommended: SHA256 (good balance)
   publisher = Publisher(
       'App', events,
       password='strong-password',
       key_hashing=SHA256
   )

   # ✓ Also good: SHA512 (maximum security)
   publisher = Publisher(
       'App', events,
       password='strong-password',
       key_hashing=SHA512
   )

   # ✗ Avoid: MD5 (weak)
   # ✗ Avoid: SHA1 (deprecated)

Encryption
==========

Enable Encryption for Sensitive Data
-------------------------------------

.. code-block:: python

   from gntplib.keys import SHA256
   from gntplib.ciphers import AES

   publisher = Publisher(
       'App', events,
       password='strong-password',
       key_hashing=SHA256,
       encryption=AES  # Enable encryption
   )

When to Use Encryption
----------------------

**Use encryption when:**

* Notifications contain sensitive information
* Communicating over untrusted networks
* Compliance requirements mandate it
* Defense in depth is desired

**Encryption not needed when:**

* GNTP server is on localhost
* Network is fully trusted
* Notifications are not sensitive
* Performance is critical

Password Management
===================

Store Passwords Securely
-------------------------

.. code-block:: python

   import os
   from gntplib import Publisher

   # ✓ Good: Read from environment
   password = os.environ.get('GNTP_PASSWORD')
   if not password:
       raise ValueError("GNTP_PASSWORD not set")

   publisher = Publisher('App', events, password=password)

.. code-block:: python

   # ✓ Good: Read from secure file
   import json
   from pathlib import Path

   config_file = Path.home() / '.config' / 'myapp' / 'gntp.json'
   with open(config_file) as f:
       config = json.load(f)
   
   password = config['gntp_password']

.. code-block:: python

   # ✗ Bad: Hardcoded password
   password = 'my-secret-password'  # Don't do this!

   # ✗ Bad: Committed to version control
   # config.py
   GNTP_PASSWORD = 'secret'  # Don't commit this!

Use Key Management Systems
---------------------------

For production applications:

.. code-block:: python

   # Example with AWS Secrets Manager
   import boto3

   def get_gntp_password():
       client = boto3.client('secretsmanager')
       response = client.get_secret_value(SecretId='gntp-password')
       return response['SecretString']

   password = get_gntp_password()
   publisher = Publisher('App', events, password=password)

Network Security
================

Use Firewall Rules
------------------

Restrict GNTP server access:

.. code-block:: bash

   # Allow only from specific IPs
   sudo ufw allow from 192.168.1.0/24 to any port 23053

   # Or allow only localhost
   sudo ufw allow from 127.0.0.1 to any port 23053

Use VPN or SSH Tunneling
-------------------------

For remote GNTP servers:

.. code-block:: bash

   # SSH tunnel
   ssh -L 23053:localhost:23053 user@remote-server

.. code-block:: python

   # Then connect to localhost
   publisher = Publisher(
       'App', events,
       host='localhost',
       port=23053,
       password='password'
   )

Input Validation
================

Validate User Input
-------------------

.. code-block:: python

   from gntplib.exceptions import GNTPValidationError

   def send_notification(title: str, message: str):
       """Send notification with validation."""
       # Validate inputs
       if not title or len(title) > 200:
           raise ValueError("Invalid title")
       
       if len(message) > 1000:
           raise ValueError("Message too long")
       
       # Sanitize if needed
       title = title.strip()
       message = message.strip()
       
       try:
           publisher.publish('event', title, message)
       except GNTPValidationError as e:
           raise ValueError(f"Invalid notification: {e}")

Prevent Injection Attacks
--------------------------

.. code-block:: python

   # ✓ Good: Parameterized
   def notify_user(username: str, action: str):
       """Safe notification."""
       title = f"User {username}"
       message = f"performed action: {action}"
       publisher.publish('user_event', title, message)

   # ✗ Bad: String interpolation without validation
   def notify_user_unsafe(username: str):
       """Unsafe: username not validated."""
       # If username contains GNTP control characters,
       # could potentially cause issues
       publisher.publish('event', username, 'logged in')

Resource Security
=================

Validate Resource Sources
--------------------------

.. code-block:: python

   from gntplib import Resource
   from urllib.parse import urlparse

   def load_icon_safely(url: str) -> Resource:
       """Load icon with URL validation."""
       # Parse and validate URL
       parsed = urlparse(url)
       
       # Check scheme
       if parsed.scheme not in ('http', 'https'):
           raise ValueError("Only HTTP(S) URLs allowed")
       
       # Check domain (whitelist)
       allowed_domains = ['cdn.example.com', 'assets.myapp.com']
       if parsed.netloc not in allowed_domains:
           raise ValueError("Domain not allowed")
       
       return Resource.from_url(url)

Limit Resource Size
-------------------

.. code-block:: python

   MAX_ICON_SIZE = 1024 * 1024  # 1MB

   def load_icon_with_size_check(filepath: str) -> Resource:
       """Load icon with size limit."""
       import os
       
       size = os.path.getsize(filepath)
       if size > MAX_ICON_SIZE:
           raise ValueError(f"Icon too large: {size} bytes")
       
       return Resource.from_file(filepath)

Error Handling
==============

Don't Leak Sensitive Information
---------------------------------

.. code-block:: python

   from gntplib.exceptions import GNTPError
   import logging

   # ✓ Good: Log securely
   try:
       publisher.publish('event', title, message)
   except GNTPError as e:
       # Log error details server-side
       logging.error(f"GNTP error: {e}", exc_info=True)
       # Return generic message to user
       raise RuntimeError("Failed to send notification")

   # ✗ Bad: Expose details to user
   try:
       publisher.publish('event', title, message)
   except GNTPError as e:
       # Don't expose internal details
       print(f"Error: {e}")
       print(f"Server: {publisher.host}")
       print(f"Password: {publisher.password}")  # Never do this!

Rate Limiting
=============

Implement Rate Limiting
-----------------------

.. code-block:: python

   import time
   from collections import deque

   class RateLimitedPublisher:
       """Publisher with rate limiting."""
       
       def __init__(self, publisher, max_per_minute=60):
           self.publisher = publisher
           self.max_per_minute = max_per_minute
           self.times = deque()
       
       def publish(self, *args, **kwargs):
           """Publish with rate limiting."""
           now = time.time()
           
           # Remove old entries
           minute_ago = now - 60
           while self.times and self.times[0] < minute_ago:
               self.times.popleft()
           
           # Check limit
           if len(self.times) >= self.max_per_minute:
               raise RuntimeError("Rate limit exceeded")
           
           # Send notification
           self.publisher.publish(*args, **kwargs)
           self.times.append(now)

Security Checklist
==================

Before Production
-----------------

- [ ] Strong passwords used
- [ ] SHA256 or SHA512 hash algorithm
- [ ] Encryption enabled for sensitive data
- [ ] Passwords stored securely (not hardcoded)
- [ ] Input validation implemented
- [ ] Resource sources validated
- [ ] Error messages don't leak information
- [ ] Rate limiting implemented
- [ ] Network access restricted
- [ ] Logs don't contain sensitive data
- [ ] Dependencies up to date
- [ ] Security audit performed

Regular Maintenance
-------------------

- [ ] Update dependencies regularly
- [ ] Review security logs
- [ ] Rotate passwords periodically
- [ ] Monitor for security advisories
- [ ] Test backup authentication methods
- [ ] Review access controls

Reporting Security Issues
=========================

If you discover a security vulnerability:

1. **Do NOT** open a public issue
2. Email cumulus13@gmail.com
3. Include:
   
   * Description of the vulnerability
   * Steps to reproduce
   * Potential impact
   * Suggested fix (if any)

4. Wait for confirmation before disclosing

We aim to respond within 48 hours and will work with you to address the issue promptly.

Additional Resources
====================

* `OWASP Top 10 <https://owasp.org/www-project-top-ten/>`_
* `Python Security Best Practices <https://python.readthedocs.io/en/stable/library/security_warnings.html>`_
* `NIST Cryptographic Standards <https://csrc.nist.gov/projects/cryptographic-standards-and-guidelines>`_
* `Building Bulletproof SSL/TLS Connections in Python: A Developer’s Guide to Secure Socket Programming <https://medium.com/@cumulus13/building-bulletproof-ssl-tls-connections-in-python-a-developers-guide-to-secure-socket-4cb1c2d9544e>`_