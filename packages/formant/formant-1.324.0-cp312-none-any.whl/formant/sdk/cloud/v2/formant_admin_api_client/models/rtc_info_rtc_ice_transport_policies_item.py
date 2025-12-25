from enum import Enum


class RtcInfoRtcIceTransportPoliciesItem(str, Enum):
    STUN = "stun"
    TURN = "turn"

    def __str__(self) -> str:
        return str(self.value)
