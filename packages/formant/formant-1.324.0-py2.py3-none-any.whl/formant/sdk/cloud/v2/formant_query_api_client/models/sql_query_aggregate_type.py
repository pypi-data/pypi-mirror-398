from enum import Enum


class SqlQueryAggregateType(str, Enum):
    AVG = "avg"
    SUM = "sum"
    COUNT = "count"
    MIN = "min"
    MAX = "max"
    MEDIAN = "median"
    STD_DEV = "std_dev"

    def __str__(self) -> str:
        return str(self.value)
