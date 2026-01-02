#!/usr/bin/env python3

# File: gntplib/async.py
# Author: Hadi Cahyadi <cumulus13@gmail.com>
# Date: 2025-12-25
# Description: DEPRECATED: use gntplib.async_gntp module instead for asyncio support.
# License: MIT

"""This module provides support for asynchronous processing built on Tornado_.

.. _Tornado: http://www.tornadoweb.org/
"""

# DEPRECATED: use gntplib.async_gntp module instead for asyncio support.

from __future__ import unicode_literals
import logging
import socket

from tornado import gen, httpclient, ioloop, iostream

import gntplib


__all__ = ['AsyncIcon', 'AsyncNotifier', 'AsyncPublisher', 'AsyncResource',
           'AsyncSubscriber']


logger = logging.getLogger(__name__)


class AsyncPublisher(gntplib.Publisher):
    """Asynchronous Publisher of Growl Notification Transport Protocol (GNTP).

    Same as :class:`~gntplib.Publisher` except the following:

    * uses :class:`AsyncGNTPClient` as `gntp_client_class`.
    * accepts :class:`tornado.ioloop.IOLoop` instance by additional
      `io_loop` keyword argument.

    :param name: the name of the application.
    :param event_defs: the definitions of the notifications.
    :param icon: url string or an instance of :class:`Resource` for the icon of
                 the application.  Defaults to `None`.
    :param io_loop: :class:`tornado.ioloop.IOLoop` instance.
    :param custom_headers: the list of key-value tuples for Custom Headers.
    :param app_specific_headers: the list of key-value tuples for App-Specific
                                 Headers.
    """

    def __init__(self, name, event_defs, icon=None, io_loop=None, **kwargs):
        io_loop = io_loop or ioloop.IOLoop.instance()
        gntplib.Publisher.__init__(self, name, event_defs, icon,
                                   gntp_client_class=AsyncGNTPClient,
                                   io_loop=io_loop, **kwargs)


class AsyncNotifier(AsyncPublisher, gntplib.Notifier):
    """Deprecated Asynchronous Notifier of Growl Notification Transport
    Protocol (GNTP)."""

    def __init__(self, name, event_defs, icon=None, io_loop=None, **kwargs):
        import warnings
        warnings.warn('AsyncNotifier is deprecated, use AsyncPublisher'
                      ' instead', DeprecationWarning, stacklevel=2)
        AsyncPublisher.__init__(self, name, event_defs, icon, io_loop,
                                **kwargs)


class AsyncSubscriber(gntplib.Subscriber):
    """Asynchronous Subscriber of Growl Notification Transport Protocol (GNTP).

    Same as :class:`~gntplib.Subscriber` except the following:

    * uses :class:`AsyncGNTPClient` as `gntp_client_class`.
    * accepts :class:`tornado.ioloop.IOLoop` instance by additional
      `io_loop` keyword argument.

    :param name: the name of the subscriber.
    :param hub: the subscribed-to machine.  If a string is given, it is used as
                a host of the hub and default port number `23053` is used.
                If host-port tuple is given, it is used directly.
    :param password: the password of the subscribed-to machine.
    :param id_: the unique id of the subscriber.  If not set, randomly
                generated UUID is used.
    :param port: the port number of the subscriber.  Defaults to `23053`.
    :param io_loop: :class:`tornado.ioloop.IOLoop` instance.
    :param custom_headers: the list of key-value tuples for Custom Headers.
    :param app_specific_headers: the list of key-value tuples for App-Specific
                                 Headers.
    """

    def __init__(self, id_, name, hub, password, port=gntplib.DEFAULT_PORT,
                 io_loop=None, **kwargs):
        io_loop = io_loop or ioloop.IOLoop.instance()
        gntplib.Subscriber.__init__(self, id_, name, hub, password, port=port,
                                    gntp_client_class=AsyncGNTPClient,
                                    io_loop=io_loop, **kwargs)


class AsyncGNTPConnection(gntplib.BaseGNTPConnection):
    """Asynchronous GNTP connection built on Tornado."""

    def __init__(self, address, timeout, final_callback, socket_callback=None,
                 io_loop=None):
        gntplib.BaseGNTPConnection.__init__(self, final_callback,
                                            socket_callback)
        sock = socket.create_connection(address, timeout=timeout)
        self.stream = iostream.IOStream(sock, io_loop=io_loop)

    def write_message(self, message):
        """Send the request to the GNTP server."""
        self.stream.write(message)

    def read_message(self, callback):
        """Read a message from opened stream and run callback with it."""
        self.stream.read_until(gntplib.MESSAGE_DELIMITER, callback)

    def close(self):
        """Close the stream."""
        self.stream.close()
        self.stream = None


class AsyncGNTPClient(gntplib.GNTPClient):
    """Asynchronous GNTP client built on Tornado.

    :param io_loop: :class:`tornado.ioloop.IOLoop` instance.
    """

    def __init__(self, io_loop=None, **kwargs):
        gntplib.GNTPClient.__init__(self, connection_class=AsyncGNTPConnection,
                                    **kwargs)
        self.io_loop = io_loop

    @gen.engine
    def process_request(self, request, callback, **kwargs):
        """Process a request.

        If the request contains :class:`AsyncResource` instances, the
        connection to the GNTP server will be established after all their
        fetches are completed asynchronously.
        """
        async_resources = collect_async_resources(request)
        if async_resources:
            yield gen.Task(fetch_async_resources_in_parallel,
                           async_resources,
                           self.io_loop)
        gntplib.GNTPClient.process_request(self, request, callback,
                                           io_loop=self.io_loop, **kwargs)


class AsyncResource(gntplib.Resource):
    """Class for asynchronous resource.

    :param url: url string of the resource.
    """
    def __init__(self, url):
        gntplib.Resource.__init__(self, None)
        self.url = url


class AsyncIcon(AsyncResource):
    """Deprecated asynchronous icon class."""

    def __init__(self, url):
        import warnings
        warnings.warn('AsyncIcon is deprecated, use AsyncResource instead',
                      DeprecationWarning, stacklevel=2)
        AsyncResource.__init__(self, url)


@gen.engine
def fetch_async_resources_in_parallel(async_resources, io_loop, callback):
    """Fetch :class:`AsyncResource`'s url in parallel."""
    http_client = httpclient.AsyncHTTPClient(io_loop=io_loop)
    responses = yield [gen.Task(http_client.fetch, resource.url)
                       for resource in async_resources]
    for resource, response in zip(async_resources, responses):
        if response.error:
            logger.warning('failed to fetch %r: %s', resource.url,
                           response.error)
            resource.data = None
        else:
            resource.data = response.body
    callback(async_resources)


def collect_async_resources(request):
    """Collect :class:`AsyncResource` instances from given request."""
    resources = []

    if isinstance(request, gntplib.RegisterRequest):
        resources = [request.app_icon] + [e.icon for e in request.events]
    elif isinstance(request, gntplib.NotifyRequest):
        resources = [request.notification.icon]

    resources.extend([value for _, value in request.custom_headers
                      if isinstance(value, AsyncResource)])
    resources.extend([value for _, value in request.app_specific_headers
                      if isinstance(value, AsyncResource)])

    return list(set(r for r in resources if isinstance(r, AsyncResource)))
