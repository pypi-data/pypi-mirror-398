from enum import Enum


class PartialStreamStreamType(str, Enum):
    BITSET = "bitset"
    LOCALIZATION = "localization"
    POINT_CLOUD = "point cloud"
    LOCATION = "location"
    FILE = "file"
    HEALTH = "health"
    TRANSFORM_TREE = "transform tree"
    BATTERY = "battery"
    VIDEO = "video"
    NUMERIC_SET = "numeric set"
    JSON = "json"
    IMAGE = "image"
    NUMERIC = "numeric"
    TEXT = "text"

    def __str__(self) -> str:
        return str(self.value)
