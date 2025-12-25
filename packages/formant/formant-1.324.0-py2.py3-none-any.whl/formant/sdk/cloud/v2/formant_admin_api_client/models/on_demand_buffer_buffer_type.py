from enum import Enum


class OnDemandBufferBufferType(str, Enum):
    S3_ASSET = "s3_asset"
    DATAPOINT = "datapoint"

    def __str__(self) -> str:
        return str(self.value)
