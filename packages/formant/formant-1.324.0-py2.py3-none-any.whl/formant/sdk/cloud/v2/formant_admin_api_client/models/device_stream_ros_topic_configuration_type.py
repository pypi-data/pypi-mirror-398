from enum import Enum


class DeviceStreamRosTopicConfigurationType(str, Enum):
    ROS_TOPIC = "ros-topic"

    def __str__(self) -> str:
        return str(self.value)
