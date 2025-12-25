from formant.protos.model.v1 import navigation_pb2
from .transform import Transform
from .twist import Twist
from formant.sdk.agent.v1.localization.utils import validate_type, get_ros_module


class Odometry:
    @classmethod
    def from_ros(cls, odometry):
        nav_msgs = get_ros_module("nav_msgs.msg")
        validate_type(odometry, nav_msgs.Odometry)
        return cls(
            pose=Transform.from_ros_pose_with_covariance(odometry.pose),
            twist=Twist.from_ros_twist_with_covariance(odometry.twist),
        )

    @classmethod
    def from_pose_with_covariance_stamped(cls, pose_msg):
        geometry_msgs = get_ros_module("geometry_msgs.msg")
        validate_type(pose_msg, geometry_msgs.PoseWithCovarianceStamped)
        return cls(
            pose=Transform.from_ros_pose(pose_msg.pose.pose)
        )

    @classmethod
    def from_xy_direction(
        cls,
        x,  # type: float
        y,  # type: float
        direction,  # type:float
    ):
        return cls(pose=Transform.from_xy_direction(x, y, direction))

    def __init__(
        self,
        pose=Transform(),  # type: Transform
        twist=Twist(),  # type: Twist
        transform_to_world=Transform(),  # type: Transform
    ):
        self.pose = pose
        self.twist = twist
        self.transform_to_world = transform_to_world

    def to_proto(self):
        return navigation_pb2.Odometry(
            pose=self.pose.to_proto(),
            twist=self.twist.to_proto(),
            world_to_local=self.transform_to_world.to_proto(),
        )
