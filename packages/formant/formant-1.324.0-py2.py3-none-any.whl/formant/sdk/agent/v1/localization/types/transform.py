from formant.protos.model.v1 import math_pb2
from formant.sdk.agent.v1.localization.utils import validate_type, get_ros_module
from .quaternion import Quaternion
from .vector3 import Vector3


class Transform:
    @classmethod
    def from_ros_transform(cls, transform):
        msgs = get_ros_module("geometry_msgs.msg")
        validate_type(transform, msgs.Transform)
        return cls(
            translation=Vector3.from_ros(transform.translation),
            rotation=Quaternion.from_ros(transform.rotation),
        )

    @classmethod
    def from_ros_transform_stamped(cls, transform_stamped):
        msgs = get_ros_module("geometry_msgs.msg")
        validate_type(transform_stamped, msgs.TransformStamped)
        return cls.from_ros_transform(transform_stamped.transform)

    @classmethod
    def from_ros_pose_stamped(cls, pose_stamped):
        msgs = get_ros_module("geometry_msgs.msg")
        validate_type(pose_stamped, msgs.PoseStamped)
        return cls.from_ros_pose(pose_stamped.pose)

    @classmethod
    def from_ros_pose_with_covariance(cls, pose_with_covariance):
        msgs = get_ros_module("geometry_msgs.msg")
        validate_type(pose_with_covariance, msgs.PoseWithCovariance)
        return cls.from_ros_pose(pose_with_covariance.pose)

    @classmethod
    def from_ros_pose(cls, pose):
        msgs = get_ros_module("geometry_msgs.msg")
        validate_type(pose, msgs.Pose)
        return cls(
            translation=Vector3.from_ros_point(pose.position),
            rotation=Quaternion.from_ros(pose.orientation),
        )

    @classmethod
    def from_xy_direction(
        cls,
        x,  # type: float
        y,  # type: float
        direction,  # type: float
    ):
        return cls(
            translation=Vector3.from_xy(x, y),
            rotation=Quaternion.from_direction(direction),
        )

    def __init__(
        self,
        translation=Vector3.identity(),  # type: Vector3
        rotation=Quaternion.identity(),  # type: Quaternion
    ):
        self.translation = translation
        self.rotation = rotation

    def to_proto(self):
        return math_pb2.Transform(
            translation=self.translation.to_proto(), rotation=self.rotation.to_proto()
        )
