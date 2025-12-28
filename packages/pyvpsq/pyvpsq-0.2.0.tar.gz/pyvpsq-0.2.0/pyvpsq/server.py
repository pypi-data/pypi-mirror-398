from dataclasses import dataclass
from enum import IntEnum
from typing import Any, List, Optional, Tuple

from . import Error
from .buffer import Buffer, ByteOrder
from .connection import Connection
from .logger import logger
from .packet import ServerPacket, ServerPacketType, Packet


class ServerQueryType(IntEnum):
    Info = 0x54
    Players = 0x55


@dataclass
class ServerInfo:
    protocol: int
    name: str
    map: str
    folder: str
    game: str
    app_id: int
    num_players: int
    max_players: int
    num_bots: int
    listen_type: str
    environment: str
    password: bool
    secure: bool
    version: str
    game_port: Optional[int] = None


class Server:
    ip: str
    query_port: int
    game_port: Optional[int]

    def __init__(self, ip: str, query_port: int, game_port: Optional[int] = None):
        self.ip = ip
        self.query_port = query_port
        self.game_port = game_port

    def __iter__(self):
        yield 'ip', self.ip
        yield 'query_port', self.query_port
        yield 'game_port', self.game_port

    def __repr__(self):
        return f'{self.ip}:{self.query_port}'

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, type(self)) and \
            other.ip == self.ip and \
            other.query_port == self.query_port and \
            other.game_port == self.game_port

    def get_info(self, timeout: float = 1.0):
        buffer, *_ = self.query(ServerQueryType.Info, timeout=timeout)

        info = ServerInfo(
            protocol=buffer.read_uchar(),
            name=buffer.read_c_string(),
            map=buffer.read_c_string(),
            folder=buffer.read_c_string(),
            game=buffer.read_c_string(),
            app_id=buffer.read_ushort(byte_order=ByteOrder.LittleEndian),
            num_players=buffer.read_uchar(),
            max_players=buffer.read_uchar(),
            num_bots=buffer.read_uchar(),
            listen_type=chr(buffer.read_uchar()),
            environment=chr(buffer.read_uchar()),
            password=bool(buffer.read_uchar()),
            secure=bool(buffer.read_uchar()),
            version=buffer.read_c_string()
        )

        extra_flag = buffer.read_uchar()
        if extra_flag & 0x80:
            game_port = buffer.read_ushort(byte_order=ByteOrder.LittleEndian)
            self.game_port = game_port
            info.game_port = game_port

        return info


    def query(self, *args: ServerQueryType, timeout: float) -> List[Buffer]:
        connection = Connection(self.ip, self.query_port, ServerPacket, timeout=timeout)

        buffers = []
        for query_type in args:
            query = self.build_query(query_type)
            _, response_type = self.map_query_to_packet_type(query_type)
            connection.write(query)
            buffers.append(self.wrapped_read(connection, query_type, response_type).buffer())

        del connection

        return buffers

    @staticmethod
    def wrapped_read(connection: Connection, query_type: ServerQueryType, response_type: ServerPacketType) -> Packet:
        packet = connection.read()
        packet_type = packet.get_type()
        if packet_type is ServerPacketType.Challenge:
            # Respond to challenge and read another packet
            logger.debug('Received challenge packet, re-sending query with challenge')
            query = Server.build_query(query_type, packet.buffer().get_buffer())
            connection.write(query)
            return Server.wrapped_read(connection, query_type, response_type)
        if packet_type is not response_type:
            # Simply read past packets of unexpected types
            logger.debug(f'Received packet of unexpected type, skipping '
                         f'(expected: {response_type}, received: {packet_type})')
            return Server.wrapped_read(connection, query_type, response_type)

        return packet

    @staticmethod
    def build_query(query_type: ServerQueryType, challenge: Optional[bytes] = None) -> bytes:
        buffer = Buffer(b'\xff\xff\xff\xff')
        buffer.write_uchar(query_type)
        buffer.write_c_string('Source Engine Query')
        if challenge is not None:
            buffer.write(challenge)
        return buffer.get_buffer()

    @staticmethod
    def map_query_to_packet_type(query_type: ServerQueryType) -> Tuple[ServerPacketType, ServerPacketType]:
        if query_type is ServerQueryType.Info:
            return ServerPacketType.InfoRequest, ServerPacketType.InfoResponse
        else:
            raise Error('Unknown query type')
