from enum import Enum


class GoogleStorageInfoOutputFormat(str, Enum):
    JSONL = "jsonl"
    PARQUET = "parquet"

    def __str__(self) -> str:
        return str(self.value)
