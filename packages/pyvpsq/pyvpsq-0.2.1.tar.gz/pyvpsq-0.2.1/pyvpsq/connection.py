import socket
from typing import Type, Union

from .buffer import Buffer
from .constants import UDP_MAX_DATA_SIZE
from .exceptions import ConnectionError, TimeoutError, Error
from .logger import logger
from .packet import Packet


class Connection:
    address: str
    port: int
    packet_type: Type[Packet]
    timeout: float

    sock: socket.socket
    is_connected: bool

    def __init__(self, address: str, port: int, packet_type: Type[Packet], timeout: float):
        self.address = address
        self.port = port
        self.packet_type = packet_type
        self.timeout = timeout

        self.is_connected = False

    def connect(self) -> None:
        if self.is_connected:
            return

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(self.timeout)

        logger.debug(f'Connecting to {self.address}:{self.port}')

        try:
            self.sock.connect((self.address, self.port))
            self.is_connected = True
        except socket.timeout:
            self.is_connected = False
            raise TimeoutError(f'Connection attempt to {self.address}:{self.port} timed out')
        except socket.error as e:
            self.is_connected = False
            raise ConnectionError(f'Failed to connect to {self.address}:{self.port} ({e})')

    def write(self, packet: Union[Packet, bytes]) -> None:
        if not self.is_connected:
            logger.debug('Socket is not connected yet, connecting now')
            self.connect()

        logger.debug('Writing to socket')

        try:
            self.sock.sendall(bytes(packet))
        except socket.error:
            raise ConnectionError('Failed to send data to server')

        logger.debug(f'Sent packet/data: {bytes(packet).hex(" ")}')

    def read(self) -> Packet:
        if not self.is_connected:
            logger.debug('Socket is not connected yet, connecting now')
            self.connect()

        logger.debug('Reading from socket')

        buffer = self.read_safe(UDP_MAX_DATA_SIZE)
        packet = self.packet_type.from_buffer(buffer)

        logger.debug(f'Received packet header: {packet.header.hex(" ")}')
        logger.debug(f'Received packet body: {packet.body.hex(" ")}')

        if not packet.is_valid():
            raise Error('Received invalid packet')

        return packet

    def read_safe(self, buflen: int) -> Buffer:
        try:
            return Buffer(self.sock.recv(buflen))
        except socket.timeout:
            raise TimeoutError('Timed out while receiving server data')
        except (socket.error, ConnectionResetError) as e:
            raise ConnectionError(f'Failed to receive data from server ({e})')

    def __del__(self):
        self.close()

    def close(self) -> bool:
        if hasattr(self, 'sock') and isinstance(self.sock, socket.socket):
            if self.is_connected:
                self.sock.shutdown(socket.SHUT_RDWR)
            self.sock.close()
            self.is_connected = False
            return True

        return False
