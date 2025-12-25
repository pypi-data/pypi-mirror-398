from formant.sdk.agent.v1.localization.utils import get_quaternion_from_euler
from formant.protos.model.v1 import math_pb2
from formant.sdk.agent.v1.localization.utils import validate_type, get_ros_module


class Quaternion:
    @classmethod
    def from_ros(cls, quaternion):
        msgs = get_ros_module("geometry_msgs.msg")
        validate_type(quaternion, msgs.Quaternion)
        return cls(quaternion.x, quaternion.y, quaternion.z, quaternion.w)

    @classmethod
    def from_direction(
        cls, direction  # type: float
    ):
        return cls.from_euler(0, 0, direction)

    @classmethod
    def from_euler(
        cls,
        roll,  # type: float
        pitch,  # type: float
        yaw,  # type: float
    ):
        [x, y, z, w] = get_quaternion_from_euler(roll, pitch, yaw)
        return cls(x, y, z, w)

    @classmethod
    def identity(cls):
        return cls(0, 0, 0, 1)

    def __init__(
        self,
        x,  # type: float
        y,  # type: float
        z,  # type: float
        w,  # type: float
    ):
        self.x = x
        self.y = y
        self.z = z
        self.w = w

    def to_proto(self):
        return math_pb2.Quaternion(x=self.x, y=self.y, z=self.z, w=self.w)
