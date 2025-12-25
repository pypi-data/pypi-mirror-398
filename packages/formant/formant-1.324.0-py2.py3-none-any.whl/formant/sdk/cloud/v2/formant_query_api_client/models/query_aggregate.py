from enum import Enum


class QueryAggregate(str, Enum):
    YEAR = "year"
    MONTH = "month"
    WEEK = "week"
    DAY = "day"
    VALUE_4 = "12 hours"
    VALUE_5 = "4 hours"
    HOUR = "hour"
    VALUE_7 = "30 minutes"
    VALUE_8 = "5 minutes"
    MINUTE = "minute"
    VALUE_10 = "30 seconds"
    VALUE_11 = "5 seconds"
    SECOND = "second"

    def __str__(self) -> str:
        return str(self.value)
