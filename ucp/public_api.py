# Copyright (c) 2019, NVIDIA CORPORATION. All rights reserved.
# See file LICENSE for terms.

import os

from ._libs import core
from ._libs.core import Endpoint  # noqa TODO: define a public Endpoint

# The module should only instantiate one instance of the application context
# However, the init of CUDA must happen after all process forks thus we delay
# the instantiation of the application context to the first use of the API.
_ctx = None


def _get_ctx():
    global _ctx
    if _ctx is None:
        _ctx = core.ApplicationContext()
    return _ctx


# Here comes the public facing API.
# We could programmable extract the function definitions but
# since the API is small, it might be worth to explicit define
# the functions here.


def init(options={}, env_takes_precedence=False):
    """
    Initiate UCX. Usually this is done automatically at the first API call
    but this function makes it possible to set UCX options programmable.
    Alternatively, UCX options can be specified through environment variables.

    Parameters
    ----------
    options: dict, optional
        UCX options send to the underlaying UCX library
    env_takes_precedence: bool, optional
        Whether environment variables takes precedence over the `options`
        specified here.
    """
    global _ctx
    if _ctx is not None:
        raise RuntimeError(
            "UCX is already initiated. Call reset() and init() "
            "in order to re-initate UCX with new options."
        )
    if env_takes_precedence:
        for k in os.environ.keys():
            if k in options:
                del options[k]

    _ctx = core.ApplicationContext(options)


def create_listener(callback_func, port=None):
    """
    Create and start a listener to accept incoming connections

    NB: the listening is continued until the returned Listener
        object goes out of scope thus remember to keep a reference
        to the object.

    Parameters
    ----------
    callback_func: function or coroutine
        a callback function that gets invoked when an incoming
        connection is accepted
    port: int, optional
        an unused port number for listening

    Returns
    -------
    Listener
        The new listener. When this object is deleted, the listening stops
    """
    return _get_ctx().create_listener(callback_func, port)


async def create_endpoint(ip_address, port):
    """
    Create a new endpoint to a server specified by `ip_address` and `port`

    Parameters
    ----------
    ip_address: str
        IP address of the server the endpoint should connect to
    port: int
        IP address of the server the endpoint should connect to

    Returns
    -------
    Endpoint
        The new endpoint
    """
    return await _get_ctx().create_endpoint(ip_address, port)


def progress():
    """
    Try to progress the communication layer

    Returns
    -------
    bool
        Returns True if progress was made
    """
    return _get_ctx().progress()


def get_ucp_worker():
    """
    Returns the underlying UCP worker handle (ucp_worker_h)
    as a Python integer.
    """
    return _get_ctx().get_ucp_worker()


def get_config():
    """
    Returns all UCX configuration options as a dict.
    If UCX is initialized, the options returned are the
    options used if UCX were to be initialized now.
    Notice, this function doesn't initialize UCX.

    Returns
    -------
    dict
        The current UCX configuration options
    """

    if _ctx is None:
        return core.get_config()
    else:
        return _get_ctx().get_config()


def reset():
    """
    Resets the UCX library by shutting down all of UCX.
    The library is initiated at next API call.
    """
    global _ctx
    _ctx = None
