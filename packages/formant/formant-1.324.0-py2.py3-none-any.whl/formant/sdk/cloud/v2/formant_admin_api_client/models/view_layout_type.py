from enum import Enum


class ViewLayoutType(str, Enum):
    DASHBOARD = "dashboard"
    OBSERVE = "observe"
    FULLSCREEN = "fullscreen"
    ANALYTICS = "analytics"
    TELEOP = "teleop"

    def __str__(self) -> str:
        return str(self.value)
