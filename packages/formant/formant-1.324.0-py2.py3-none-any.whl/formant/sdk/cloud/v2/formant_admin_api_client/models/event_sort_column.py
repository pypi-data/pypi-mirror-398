from enum import Enum


class EventSortColumn(str, Enum):
    TYPE = "type"
    MESSAGE = "message"
    DEVICE_NAME = "device.name"
    TIME = "time"
    EVENT_CREATEDAT = "event.createdAt"
    EVENT_UPDATEDAT = "event.updatedAt"

    def __str__(self) -> str:
        return str(self.value)
