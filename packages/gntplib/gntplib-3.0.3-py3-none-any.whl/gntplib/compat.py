#!/usr/bin/env python3

# File: gntplib/compat.py
# Author: Hadi Cahyadi <cumulus13@gmail.com>
# Date: 2025-12-25
# Description: DEPRECATED: use six or future libraries for compatibility.
# License: MIT

"""This module makes gntplib compatible with Python 2 and 3."""

import sys


if sys.version_info[0] == 3:
    text_type = str
else:
    text_type = unicode
