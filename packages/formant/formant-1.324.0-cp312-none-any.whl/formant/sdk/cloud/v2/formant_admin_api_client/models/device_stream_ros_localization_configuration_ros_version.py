from enum import Enum


class DeviceStreamRosLocalizationConfigurationRosVersion(str, Enum):
    ROS_1 = "ROS-1"
    ROS_2 = "ROS-2"

    def __str__(self) -> str:
        return str(self.value)
