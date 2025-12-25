from enum import Enum


class DeviceTeleopCustomStreamConfigurationNumericControlVisualization(str, Enum):
    SLIDER = "slider"
    DIAL = "dial"

    def __str__(self) -> str:
        return str(self.value)
