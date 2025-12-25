from typing import Any, Dict, List, Optional, Union

from formant.sdk.utils.time_utils import current_datapoint_time


def with_timestamp(f):
    """Decorator that injects the timestamp kwarg with self._timestamp"""

    def with_timestamp_inner(*args, **kwargs):
        self = args[0]
        if "timestamp" not in kwargs:
            kwargs["timestamp"] = self._timestamp
        return f(*args, **kwargs)

    return with_timestamp_inner


class IngestionRequest:
    def __init__(self, device_id: str, tags: Dict, timestamp: Optional[int] = None):
        self._device_id = device_id
        self._tags = tags
        self._timestamp = timestamp
        if timestamp is None:
            self._timestamp = current_datapoint_time()
        self._request: Dict[str, List] = {"items": []}

    def __str__(self):
        return str(json.dumps(self._request, indent=4))

    def _get_entry(self, type: str, name: str):
        entry = next(
            (
                item
                for item in self._request["items"]
                if item["name"] == name
                and item["deviceId"] == self._device_id
                and item["type"] == type
            ),
            None,
        )
        if entry is None:
            entry = {
                "deviceId": self._device_id,
                "name": name,
                "type": type,
                "tags": self._tags,
                "points": [],
            }
            self._request["items"].append(entry)
        return entry

    def get_request(self):
        return self._request

    @with_timestamp
    def add_numeric(
        self, name: str, value: Union[int, float], timestamp: Optional[int] = None
    ):
        entry = self._get_entry("numeric", name)
        entry["points"].append([timestamp, value])

    @with_timestamp
    def add_text(self, name: str, value: str, timestamp: Optional[int] = None):
        if value == "" or value == "\n":
            return
        entry = self._get_entry("text", name)
        entry["points"].append([timestamp, str(value)])

    @with_timestamp
    def add_json(self, name: str, value: str, timestamp: Optional[int] = None):
        entry = self._get_entry("json", name)
        entry["points"].append([timestamp, value])

    @with_timestamp
    def add_numeric_set(
        self, name: str, value: List[Dict[str, Any]], timestamp: Optional[int] = None
    ):
        entry = self._get_entry("numeric set", name)
        entry["points"].append([timestamp, value])
        return self

    @with_timestamp
    def add_bitset(
        self, name: str, value: Dict[str, List], timestamp: Optional[int] = None
    ):
        if len(value["keys"]) == 0:
            return
        entry = self._get_entry("bitset", name)
        entry["points"].append([timestamp, value])

    @with_timestamp
    def add_battery(
        self,
        name: str,
        percentage: float,
        voltage: Optional[float] = None,
        current: Optional[float] = None,
        charge: Optional[float] = None,
        timestamp: Optional[int] = None,
    ):
        entry = self._get_entry("battery", name)
        value = {"percentage": percentage}
        if voltage is not None:
            value["voltage"] = voltage
        if current is not None:
            value["current"] = current
        if charge is not None:
            value["charge"] = charge
        entry["points"].append([timestamp, value])

    @with_timestamp
    def add_health(self, name: str, timestamp: Optional[int] = None):
        entry = self._get_entry("health", name)
        entry["points"].append(
            [
                [
                    timestamp,
                    {
                        "status": "operational",
                    },
                ]
            ]
        )

    @with_timestamp
    def add_location(
        self,
        name: str,
        longitude: float,
        latitude: float,
        timestamp: Optional[int] = None,
    ):
        entry = self._get_entry("location", name)
        entry["points"].append(
            [
                [
                    timestamp,
                    {
                        "latitude": latitude,
                        "longitude": longitude,
                    },
                ]
            ]
        )

    @with_timestamp
    def add_image(self, name: str, url: str, timestamp: Optional[int] = None):
        entry = self._get_entry("image", name)
        entry["points"] = [
            [
                self._timestamp,
                {
                    "url": url,
                },
            ]
        ]
        entry["points"].append(
            [
                [
                    timestamp,
                    {
                        "url": url,
                    },
                ]
            ]
        )
