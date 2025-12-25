from typing import Any, Dict, List, Type, TypeVar
from formant.sdk.cloud.v2.formant_query_api_client.models.bitset import Bitset
from formant.sdk.cloud.v2.formant_query_api_client.models.localization import (
    Localization,
)
from formant.sdk.cloud.v2.formant_query_api_client.models.point_cloud import PointCloud
from formant.sdk.cloud.v2.formant_query_api_client.models.location import Location
from formant.sdk.cloud.v2.formant_query_api_client.models.file import File
from formant.sdk.cloud.v2.formant_query_api_client.models.health import (
    Health,
    HealthStatus,
)
from formant.sdk.cloud.v2.formant_query_api_client.models.transform_node import (
    TransformNode,
)
from formant.sdk.cloud.v2.formant_query_api_client.models.battery import Battery
from formant.sdk.cloud.v2.formant_query_api_client.models.video import (
    Video,
    VideoMimeType,
)
from formant.sdk.cloud.v2.formant_query_api_client.models.numeric_set_entry import (
    NumericSetEntry,
)
from formant.sdk.cloud.v2.formant_query_api_client.models.image import Image

from datetime import datetime
from urllib.request import urlopen
import attr

T = TypeVar("T", bound="StreamDataPointsItem")

TYPE_MAP = {
    "bitset": Bitset,
    "localization": Localization,
    "point cloud": PointCloud,
    "location": Location,
    "file": File,
    "health": Health,
    "transform tree": TransformNode,
    "battery": Battery,
    "video": Video,
    "image": Image,
}


@attr.s(auto_attribs=True)
class StreamDataPointsItem:
    """ """

    timestamp: datetime = None
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)
    bitset: Bitset = None
    localization: Localization = None
    point_cloud: PointCloud = None
    location: Location = None
    file: File = None
    health: Health = None
    transform_tree: TransformNode = None
    battery: Battery = None
    video: Video = None
    numeric_set: List[NumericSetEntry] = None
    json: Dict = None
    image: Image = None
    numeric: float = None
    text: str = None

    def to_dict(self) -> Dict[str, Any]:

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], raw_data: List, type: str) -> T:

        d = raw_data.copy()
        stream_data_points_item = cls()
        raw_timestamp = raw_data[0] / 1000.0
        stream_data_points_item.timestamp = datetime.fromtimestamp(raw_timestamp)
        stream_data_points_item.initialize_data(type=type, raw_data=raw_data[1])
        stream_data_points_item.additional_properties = {"value": d}
        return stream_data_points_item

    def initialize_data(self, type: str, raw_data: Any):

        if type == "numeric set":
            numeric_set_instance = []
            for raw_entry in raw_data:
                raw_entry_instance = NumericSetEntry.from_dict(raw_entry)
                numeric_set_instance.append(raw_entry_instance)
            self.numeric_set = numeric_set_instance

        elif type == "json":
            self.json = raw_data

        elif type == "numeric":
            self.numeric = raw_data

        elif type == "text":
            self.text = raw_data

        else:
            custom_data = TYPE_MAP[type].from_dict(raw_data)
            type_new = type.replace(" ", "_")
            setattr(self, type_new, custom_data)

    @property
    def additional_keys(self) -> List[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
