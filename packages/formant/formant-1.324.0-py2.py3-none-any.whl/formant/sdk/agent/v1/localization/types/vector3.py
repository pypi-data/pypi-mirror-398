from formant.protos.model.v1 import math_pb2
from formant.sdk.agent.v1.localization.utils import validate_type, get_ros_module


class Vector3:
    @classmethod
    def from_ros(cls, vector3):
        msgs = get_ros_module("geometry_msgs.msg")
        validate_type(vector3, msgs.Vector3)
        return cls(vector3.x, vector3.y, vector3.z)

    @classmethod
    def from_ros_point(cls, point):
        msgs = get_ros_module("geometry_msgs.msg")
        validate_type(point, msgs.Point)
        return cls(point.x, point.y, point.z)

    @classmethod
    def from_xy(
        cls,
        x,  # type: float
        y,  # type: float
    ):
        return cls(x, y, 0)

    @classmethod
    def identity(cls):
        return cls(0, 0, 0)

    def __init__(
        self,
        x,  # type: float
        y,  # type: float
        z,  # type: float
    ):
        self.x = x
        self.y = y
        self.z = z

    def to_proto(self):
        return math_pb2.Vector3(x=self.x, y=self.y, z=self.z)
