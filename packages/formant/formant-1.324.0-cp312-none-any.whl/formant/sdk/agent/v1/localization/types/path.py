from typing import List
from formant.protos.model.v1 import navigation_pb2
from formant.sdk.agent.v1.localization.utils import validate_type, get_ros_module
from .transform import Transform


class Path:
    @classmethod
    def from_ros(cls, path):
        nav_msgs = get_ros_module("nav_msgs.msg")
        validate_type(path, nav_msgs.Path)
        return cls(poses=[Transform.from_ros_pose_stamped(pose) for pose in path.poses])

    def __init__(
        self,
        poses=[],  # type: List[Transform]
        transform_to_world=Transform(),  # type: Transform
    ):
        self.poses = poses
        self.transform_to_world = transform_to_world

    def to_proto(self):
        path_proto = navigation_pb2.Path(
            world_to_local=self.transform_to_world.to_proto(),
        )
        poses_proto_array = [pose.to_proto() for pose in self.poses]
        del path_proto.poses[:]
        path_proto.poses.extend(poses_proto_array)
        return path_proto
