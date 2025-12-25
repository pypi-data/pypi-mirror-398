from enum import Enum


class VideoMimeType(str, Enum):
    VIDEOMP4 = "video/mp4"

    def __str__(self) -> str:
        return str(self.value)
