from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union, cast

import attr

from ..models.ingest_stream_data_type import IngestStreamDataType
from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.ingest_stream_data_tags import IngestStreamDataTags




T = TypeVar("T", bound="IngestStreamData")

@attr.s(auto_attribs=True)
class IngestStreamData:
    """
    Attributes:
        name (str):
        type (IngestStreamDataType):
        tags (IngestStreamDataTags):
        points (List[Any]):
        device_id (Union[Unset, str]):
        agent_id (Union[Unset, str]):
    """

    name: str
    type: IngestStreamDataType
    tags: 'IngestStreamDataTags'
    points: List[Any]
    device_id: Union[Unset, str] = UNSET
    agent_id: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        type = self.type.value

        tags = self.tags.to_dict()

        points = self.points




        device_id = self.device_id
        agent_id = self.agent_id

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "name": name,
            "type": type,
            "tags": tags,
            "points": points,
        })
        if device_id is not UNSET:
            field_dict["deviceId"] = device_id
        if agent_id is not UNSET:
            field_dict["agentId"] = agent_id

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.ingest_stream_data_tags import IngestStreamDataTags
        d = src_dict.copy()
        name = d.pop("name")

        type = IngestStreamDataType(d.pop("type"))




        tags = IngestStreamDataTags.from_dict(d.pop("tags"))




        points = cast(List[Any], d.pop("points"))


        device_id = d.pop("deviceId", UNSET)

        agent_id = d.pop("agentId", UNSET)

        ingest_stream_data = cls(
            name=name,
            type=type,
            tags=tags,
            points=points,
            device_id=device_id,
            agent_id=agent_id,
        )

        ingest_stream_data.additional_properties = d
        return ingest_stream_data

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
