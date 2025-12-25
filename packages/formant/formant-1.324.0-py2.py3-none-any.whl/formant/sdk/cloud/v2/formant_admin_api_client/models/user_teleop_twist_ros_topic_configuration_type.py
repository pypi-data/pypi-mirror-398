from enum import Enum


class UserTeleopTwistRosTopicConfigurationType(str, Enum):
    GEOMETRY_MSGSTWIST = "geometry_msgs/Twist"

    def __str__(self) -> str:
        return str(self.value)
