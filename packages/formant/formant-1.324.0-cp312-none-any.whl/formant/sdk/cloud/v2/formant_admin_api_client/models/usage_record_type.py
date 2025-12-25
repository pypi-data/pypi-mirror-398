from enum import Enum


class UsageRecordType(str, Enum):
    DEVICE_COUNT = "device-count"
    DATAPOINT_COUNT = "datapoint-count"
    ASSET_COUNT = "asset-count"
    DATA_STORAGE = "data-storage"
    TURN_NETWORK = "turn-network"
    ADVANCED_CONFIGURATION = "advanced-configuration"
    ANALYTICS = "analytics"
    CUSTOMER_PORTAL = "customer-portal"
    DATA_EXPORT = "data-export"
    DATA_RETENTION = "data-retention"
    SUPPORT = "support"

    def __str__(self) -> str:
        return str(self.value)
