from enum import Enum


class AwsInfoOutputFormat(str, Enum):
    JSONL = "jsonl"
    PARQUET = "parquet"

    def __str__(self) -> str:
        return str(self.value)
