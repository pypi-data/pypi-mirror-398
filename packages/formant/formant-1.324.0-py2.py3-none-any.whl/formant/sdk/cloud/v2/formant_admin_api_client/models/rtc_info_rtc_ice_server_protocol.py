from enum import Enum


class RtcInfoRtcIceServerProtocol(str, Enum):
    UDP = "udp"
    TCP = "tcp"

    def __str__(self) -> str:
        return str(self.value)
