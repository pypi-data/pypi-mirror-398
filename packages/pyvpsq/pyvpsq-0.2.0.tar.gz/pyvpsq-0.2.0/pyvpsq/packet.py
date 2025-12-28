from enum import Enum

from .buffer import Buffer


# https://stackoverflow.com/a/54919285/9395553
class ExtendedEnum(Enum):
    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


class PacketType(int, ExtendedEnum):
    def __str__(self):
        return f'{self.__class__.__name__}.{self.name} ({self.value:02x})'


class Packet:
    header: bytes
    body: bytes

    HEADER_LENGTH: int

    def __init__(self, header: bytes = b'', body: bytes = b''):
        self.header = header
        self.body = body

    def __bytes__(self):
        return self.header + self.body

    @classmethod
    def from_buffer(cls, buffer: Buffer):
        header, body = buffer.read(cls.HEADER_LENGTH), buffer.get_buffer()
        return cls(header, body)

    def is_valid(self) -> bool:
        pass

    def get_type(self) -> PacketType:
        pass

    def buffer(self, skip_header: bool = True) -> Buffer:
        buffer = Buffer(self.header + self.body)

        if skip_header:
            buffer.skip(self.HEADER_LENGTH)

        return buffer


class PrincipalPacket(Packet):
    HEADER_LENGTH = 6

    def is_valid(self) -> bool:
        return self.header == b'\xff\xff\xff\xff\x66\x0a' and len(self.body) % 6 == 0


class ServerPacketType(PacketType):
    Challenge = 0x41
    PlayersResponse = 0x44
    RulesResponse = 0x45
    InfoResponse = 0x49
    InfoRequest = 0x54
    PlayersRequest = 0x55
    RulesRequest = 0x56
    GoldSrcInfoResponse = 0x6d


class ServerPacket(Packet):
    HEADER_LENGTH = 5

    def is_valid(self) -> bool:
        return len(self.header) == self.HEADER_LENGTH and \
            self.header[:4] == b'\xff\xff\xff\xff' \
            and self.header[4] in ServerPacketType.list()

    def get_type(self) -> ServerPacketType:
        return ServerPacketType(self.header[4])
