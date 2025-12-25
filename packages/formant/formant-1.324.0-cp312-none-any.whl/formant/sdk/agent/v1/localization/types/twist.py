from formant.protos.model.v1 import math_pb2
from formant.sdk.agent.v1.localization.utils import validate_type, get_ros_module
from .vector3 import Vector3


class Twist:
    @classmethod
    def from_ros(cls, twist):
        msgs = get_ros_module("geometry_msgs.msg")
        validate_type(twist, msgs.Twist)
        return cls(
            linear=Vector3.from_ros(twist.linear),
            angular=Vector3.from_ros(twist.angular),
        )

    @classmethod
    def from_ros_twist_with_covariance(cls, twist):
        msgs = get_ros_module("geometry_msgs.msg")
        validate_type(twist, msgs.TwistWithCovariance)
        return cls.from_ros(twist.twist)

    def __init__(
        self,
        linear=Vector3.identity(),  # type: Vector3
        angular=Vector3.identity(),  # type: Vector3
    ):
        self.linear = linear
        self.angular = angular

    def to_proto(self):
        return math_pb2.Twist(
            linear=self.linear.to_proto(), angular=self.angular.to_proto()
        )
