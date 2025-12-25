from enum import Enum


class DeviceStreamRosTransformTreeConfigurationType(str, Enum):
    ROS_TRANSFORM_TREE = "ros-transform-tree"

    def __str__(self) -> str:
        return str(self.value)
