#!/usr/bin/python3

#
#   Developer: Alexey Zakharov (alexey.zakharov@vectioneer.com)
#   All rights reserved. Copyright (c) 2016 - 2025 VECTIONEER.
#

"""
motorcortex-python

Motorcortex is a Python library for connecting to Motorcortex servers, handling requests, subscriptions, and parameter trees.
Provides high-level APIs for communication, login, and data exchange using protocol buffers.

See documentation for usage examples.
"""

from motorcortex.version import __version__
from motorcortex.parameter_tree import ParameterTree
from motorcortex.message_types import MessageTypes
from motorcortex.request import Request, ConnectionState
from motorcortex.reply import Reply
from motorcortex.subscribe import Subscribe
from motorcortex.subscription import Subscription
from motorcortex.timespec import Timespec, compare_timespec, timespec_to_sec, timespec_to_msec, timespec_to_usec, \
    timespec_to_nsec
from motorcortex.setup_logger import logger
from motorcortex.state_callback_handler import StateCallbackHandler
from motorcortex.init_threads import init_nng_threads

init_nng_threads()


def parseUrl(url: str) -> tuple[str, str, int | None, int | None]:
    """
    Parses a Motorcortex connection URL to extract request and subscribe addresses and ports.

    Args:
        url (str): The connection URL, expected in the format 'address:req_port:sub_port'.

    Returns:
        tuple: (req_address, sub_address, req_port, sub_port)
            - req_address (str): Address for request connection.
            - sub_address (str): Address for subscribe connection.
            - req_port (int or None): Port for request connection.
            - sub_port (int or None): Port for subscribe connection.

    If the URL does not contain ports, default endpoints '/mcx_req' and '/mcx_sub' are appended.
    """
    end = url.rfind(':')
    start = url.rfind(':', 0, end)
    if end == -1 or start == -1:
        return url + '/mcx_req', url + '/mcx_sub', None, None
    req_port = int(url[start + 1:end])
    sub_port = int(url[end + 1:])
    address = url[:start]
    return address, address, req_port, sub_port


def makeUrl(address: str, port: int | None) -> str:
    """
    Constructs a URL string from an address and port.

    Args:
        address (str): The base address.
        port (int or None): The port number.

    Returns:
        str: The combined address and port in the format 'address:port', or just 'address' if port is None.
    """
    if port:
        return "{}:{}".format(address, port)

    return address


def connect(
        url: str,
        motorcortex_types: object,
        param_tree: "ParameterTree",
        reconnect: bool = True,
        **kwargs
) -> tuple["Request", "Subscribe"]:
    """
    Establishes connections to Motorcortex request and subscribe endpoints, performs login, and loads the parameter tree.

    Args:
        url (str): Connection URL in the format 'address:req_port:sub_port'.
        motorcortex_types (module): Motorcortex message types module.
        param_tree (ParameterTree): ParameterTree instance to load parameters into.
        reconnect (bool, optional): Whether to enable automatic reconnection. Defaults to True.
        **kwargs: Additional keyword arguments, including 'login' and 'password' for authentication.

    Returns:
        tuple: (req, sub)
            - req (Request): Established request connection.
            - sub (Subscribe): Established subscribe connection.

    Raises:
        RuntimeError: If connection or login fails.

    Examples:
        >>> from motorcortex import connect, MessageTypes, ParameterTree
        >>> url = "127.0.0.1:5555:5556"
        >>> types = MessageTypes()
        >>> tree = ParameterTree()
        >>> req, sub = connect(url, types, tree, certificate="mcx.cert.crt", timeout_ms=1000, login="admin", password="iddqd")
        >>> print(tree)  # Parameter tree loaded from server
    """

    initial_connect_done = [False]  # Now reconnections will trigger callback login

    if reconnect and not kwargs.get("state_update"):

        def stateUpdate(req, sub, state):
            if state == ConnectionState.CONNECTION_OK and initial_connect_done[0]:
                req.login(kwargs.get("login"), kwargs.get("password")).get()
                sub.resubscribe()

        kwargs.update(state_update=stateUpdate)

    # Parse address
    req_address, sub_address, req_port, sub_port = parseUrl(url)
    # Open request connection
    req = Request(motorcortex_types, param_tree, kwargs.get("req_number_of_threads", 2))
    kwargs_copy = kwargs.copy()
    kwargs_copy.update(state_update=None)
    if not req.connect(makeUrl(req_address, req_port), **kwargs_copy).get():
        raise RuntimeError("Failed to establish request connection: {}:{}".format(req_address, req_port))
    # Open subscribe connection
    sub = Subscribe(req, motorcortex_types, kwargs.get("sub_number_of_threads", 2))
    if not sub.connect(makeUrl(sub_address, sub_port), **kwargs).get():
        raise RuntimeError("Failed to establish subscribe connection: {}:{}".format(sub_address, sub_port))
    # Login
    login_reply = req.login(kwargs['login'], kwargs['password'])
    login_reply_msg = login_reply.get()

    motorcortex_msg = motorcortex_types.motorcortex()
    if not login_reply_msg.status == motorcortex_msg.OK:
        raise RuntimeError("Login failed, status: {}".format(login_reply_msg.status))

    # Requesting a parameter tree
    param_tree_reply = req.getParameterTree()
    tree = param_tree_reply.get()
    param_tree.load(tree)

    initial_connect_done[0] = True  # Now reconnections will trigger callback login

    return req, sub


def statusToStr(motorcortex_msg: object, code: int) -> str:
    """Converts status codes to a readable message.

        Args:
            motorcortex_msg(Module): reference to a motorcortex module
            code(int): status code

        Returns:
            str: status message

        Examples:
            >>> login_reply = req.login("admin", "iddqd")
            >>> login_reply_msg = login_reply.get()
            >>> if login_reply_msg.status != motorcortex_msg.OK:
            >>>     print(motorcortex.statusToStr(motorcortex_msg, login_reply_msg.status))

    """

    status = 'Unknown code'
    if code == motorcortex_msg.OK:
        status = 'Success'
    elif code == motorcortex_msg.FAILED:
        status = 'Failed'
    elif code == motorcortex_msg.FAILED_TO_DECODE:
        status = 'Failed to decode request'
    elif code == motorcortex_msg.SUB_LIST_IS_FULL:
        status = 'Failed to subscribe, subscription list is full'
    elif code == motorcortex_msg.WRONG_PARAMETER_PATH:
        status = 'Failed to find parameter'
    elif code == motorcortex_msg.FAILED_TO_SET_REQUESTED_FRQ:
        status = 'Failed to set requested frequency'
    elif code == motorcortex_msg.FAILED_TO_OPEN_FILE:
        status = 'Failed to open file'
    elif code == motorcortex_msg.READ_ONLY_MODE:
        status = 'Logged in, read-only mode'
    elif code == motorcortex_msg.WRONG_PASSWORD:
        status = 'Wrong login or password'
    elif code == motorcortex_msg.USER_NOT_LOGGED_IN:
        status = 'Operation is not permitted, user is not logged in'
    elif code == motorcortex_msg.PERMISSION_DENIED:
        status = 'Operation is not permitted, user has no rights'

    status += str(' (%s)' % hex(code))

    return status
