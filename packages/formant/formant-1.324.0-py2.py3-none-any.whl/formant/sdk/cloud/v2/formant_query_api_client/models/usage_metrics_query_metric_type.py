from enum import Enum


class UsageMetricsQueryMetricType(str, Enum):
    DATA_IN_BYTES = "data-in-bytes"
    DATA_IN_COUNT = "data-in-count"
    DATA_OUT_BYTES = "data-out-bytes"
    DATA_OUT_CACHED_BYTES = "data-out-cached-bytes"
    DATA_OUT_COUNT = "data-out-count"
    ANALYTICS_OUT_BYTES = "analytics-out-bytes"
    ANALYTICS_OUT_COUNT = "analytics-out-count"
    DATA_STORED_BYTES = "data-stored-bytes"
    ASSET_IN_BYTES = "asset-in-bytes"

    def __str__(self) -> str:
        return str(self.value)
