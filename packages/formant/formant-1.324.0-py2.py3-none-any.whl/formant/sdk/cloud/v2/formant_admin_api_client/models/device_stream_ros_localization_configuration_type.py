from enum import Enum


class DeviceStreamRosLocalizationConfigurationType(str, Enum):
    ROS_LOCALIZATION = "ros-localization"

    def __str__(self) -> str:
        return str(self.value)
