=========
Changelog
=========

All notable changes to gntplib will be documented in this file.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_,
and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

[3.0.0] - 2025-12-20
====================

Added
-----

* **Python 3 Modernization**
  
  * Full Python 3.7+ support with type hints
  * Removed Python 2 compatibility code
  * Modern async/await syntax for Tornado support

* **Enhanced Security**
  
  * Cryptographically secure random generation using ``secrets`` module
  * Increased minimum salt size from 4 to 8 bytes
  * Better key validation and error messages

* **Improved Documentation**
  
  * Complete Sphinx documentation with Furo theme
  * Comprehensive API reference with examples
  * Detailed tutorials and guides
  * ReadTheDocs integration

* **New Features**
  
  * ``Resource.from_file()`` and ``Resource.from_url()`` convenience methods
  * Better error handling with specific exception types
  * Enhanced logging support throughout
  * Validation for all input parameters

* **Developer Experience**
  
  * Comprehensive docstrings for all public APIs
  * Type hints for better IDE support
  * More informative error messages
  * Better separation of concerns in code organization

Changed
-------

* **Breaking Changes**
  
  * Minimum Python version is now 3.7
  * ``Notifier`` class deprecated in favor of ``Publisher``
  * ``notify()`` function deprecated in favor of ``publish()``
  * ``RawIcon`` deprecated in favor of ``Resource``
  * ``AsyncIcon`` deprecated in favor of ``AsyncResource``

* **API Improvements**
  
  * ``Publisher`` replaces ``Notifier`` (with backwards compatibility)
  * ``publish()`` replaces ``notify()`` (with backwards compatibility)
  * More consistent naming conventions
  * Better parameter names (e.g., ``event_defs`` instead of mixed types)

* **Internal Changes**
  
  * Reorganized module structure
  * Split large modules into focused components
  * Improved code quality and maintainability
  * Better test coverage

Fixed
-----

* Proper UTF-8 handling in Python 3
* Resource hashing now works correctly with both bytes and strings
* Connection cleanup is more reliable
* Better error handling for edge cases

Deprecated
----------

* ``Notifier`` class (use ``Publisher`` instead)
* ``notify()`` function (use ``publish()`` instead)
* ``RawIcon`` class (use ``Resource`` instead)
* ``AsyncNotifier`` class (use ``AsyncPublisher`` instead)
* ``AsyncIcon`` class (use ``AsyncResource`` instead)


[0.5.0] - 2020-XX-XX
====================

* Previous version with Python 2/3 compatibility
* See git history for details

