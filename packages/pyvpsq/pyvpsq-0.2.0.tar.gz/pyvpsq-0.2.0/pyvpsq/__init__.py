from .connection import Connection
from .exceptions import Error, ConnectionError, TimeoutError
from .principalserver import PrincipalServer, Region
from .server import Server, ServerInfo

"""
pyvpsq.

Simple Python library for querying Valve's principal servers and their game servers.
"""

__version__ = '0.2.0'
__author__ = 'cetteup'
__credits__ = [
    'https://github.com/ValvePython/steam',
    'https://github.com/gamedig/node-gamedig',
    'https://github.com/GiyoMoon/steam-server-query',
    'https://developer.valvesoftware.com/wiki/Master_Server_Query_Protocol',

]
__all__ = [
    'Connection',
    'PrincipalServer', 'Server', 'ServerInfo',
    'Region',
    'Error', 'ConnectionError', 'TimeoutError'
]
