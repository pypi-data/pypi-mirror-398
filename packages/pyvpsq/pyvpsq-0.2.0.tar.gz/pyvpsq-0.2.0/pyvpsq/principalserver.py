from enum import IntEnum
from typing import List, Optional, Tuple, Generator

from .buffer import Buffer
from .connection import Connection
from .constants import ZERO_IP
from .packet import PrincipalPacket
from .server import Server


class Region(IntEnum):
    USEast = 0x00
    USWest = 0x01
    SouthAmerica = 0x02
    Europe = 0x03
    Asia = 0x04
    Australia = 0x05
    MiddleEast = 0x06
    Africa = 0x07
    World = 0xff


class PrincipalServer:
    address: str
    port: int

    connection: Connection

    def __init__(self, address: str, port: int, timeout: float = 2.0):
        self.address = address
        self.port = port
        self.connection = Connection(self.address, self.port, PrincipalPacket, timeout=timeout)

    def __enter__(self):
        return self

    def __exit__(self, *excinfo):
        self.connection.close()

    def get_servers(
            self,
            filters: str,
            region: Region = Region.World,
            max_pages: Optional[int] = None
    ) -> Generator[Server, None, None]:
        after, has_next, page = f'{ZERO_IP}:0', True, 0
        while has_next and (max_pages is None or page < max_pages):
            servers, has_next = self.get_server_page(region, after, filters)
            for server in servers:
                yield server

            if not has_next:
                return

            page += 1
            after = str(servers[-1])

    def get_server_page(self, region: Region, after: str, filters: str) -> Tuple[List[Server], bool]:
        query = self.build_query(region, after, filters)
        self.connection.write(query)

        buffer = self.connection.read().buffer()

        servers = []
        has_next = True
        while buffer.has(6):
            ip, query_port = buffer.read_ip(), buffer.read_ushort()
            if ip == ZERO_IP and query_port == 0:
                has_next = False
                break

            servers.append(Server(ip, query_port))

        return servers, has_next

    @staticmethod
    def build_query(region: Region, after: str, filters: str) -> bytes:
        buffer = Buffer()
        buffer.write_uchar(0x31)
        buffer.write_uchar(region)
        buffer.write_c_string(after)
        buffer.write_c_string(filters)
        return buffer.get_buffer()
