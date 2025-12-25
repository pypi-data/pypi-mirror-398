from enum import Enum


class LocationViewConfigurationBasemap(str, Enum):
    STREETS = "streets"
    SATELLITE = "satellite"

    def __str__(self) -> str:
        return str(self.value)
