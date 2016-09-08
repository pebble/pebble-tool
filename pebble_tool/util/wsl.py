import socket
import sys

import websocket

__author__ = 'katharine'


def is_secretly_windows():
    if sys.platform.startswith('linux'):
        try:
            with open('/proc/version') as f:
                if 'Microsoft' in f.read():
                    return True
        except IOError:
            pass
    return False


def disable_tcp_keepcnt():
    if not hasattr(socket, 'TCP_KEEPCNT'):
        return
    for i, (level, optname, value) in enumerate(websocket.DEFAULT_SOCKET_OPTION):
        if optname == socket.TCP_KEEPCNT:
            del websocket.DEFAULT_SOCKET_OPTION[i]
            break


def maybe_apply_wsl_hacks():
    if is_secretly_windows():
        disable_tcp_keepcnt()
