import datetime
from typing import (TYPE_CHECKING, Any, Dict, List, Optional, Type, TypeVar,
                    Union, cast)

import attr
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.analytics_module_layout import AnalyticsModuleLayout




T = TypeVar("T", bound="AnalyticsModule")

@attr.s(auto_attribs=True)
class AnalyticsModule:
    """
    Attributes:
        name (str):
        query (Any):
        stream_ids (List[str]):
        configuration (Any):
        organization_id (Union[Unset, str]):
        layout (Optional[AnalyticsModuleLayout]):
        data (Optional[List[Any]]):
        fullscreen (Union[Unset, bool]):
        id (Union[Unset, str]):
        created_at (Union[Unset, datetime.datetime]):
        updated_at (Union[Unset, datetime.datetime]):
    """

    name: str
    query: Any
    stream_ids: List[str]
    configuration: Any
    layout: Optional['AnalyticsModuleLayout']
    data: Optional[List[Any]]
    organization_id: Union[Unset, str] = UNSET
    fullscreen: Union[Unset, bool] = UNSET
    id: Union[Unset, str] = UNSET
    created_at: Union[Unset, datetime.datetime] = UNSET
    updated_at: Union[Unset, datetime.datetime] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        query = self.query
        stream_ids = self.stream_ids




        configuration = self.configuration
        organization_id = self.organization_id
        layout = self.layout.to_dict() if self.layout else None

        if self.data is None:
            data = None
        else:
            data = self.data




        fullscreen = self.fullscreen
        id = self.id
        created_at: Union[Unset, str] = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: Union[Unset, str] = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "name": name,
            "query": query,
            "streamIds": stream_ids,
            "configuration": configuration,
            "layout": layout,
            "data": data,
        })
        if organization_id is not UNSET:
            field_dict["organizationId"] = organization_id
        if fullscreen is not UNSET:
            field_dict["fullscreen"] = fullscreen
        if id is not UNSET:
            field_dict["id"] = id
        if created_at is not UNSET:
            field_dict["createdAt"] = created_at
        if updated_at is not UNSET:
            field_dict["updatedAt"] = updated_at

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.analytics_module_layout import AnalyticsModuleLayout
        d = src_dict.copy()
        name = d.pop("name")

        query = d.pop("query")

        stream_ids = cast(List[str], d.pop("streamIds"))


        configuration = d.pop("configuration")

        organization_id = d.pop("organizationId", UNSET)

        _layout = d.pop("layout")
        layout: Optional[AnalyticsModuleLayout]
        if _layout is None:
            layout = None
        else:
            layout = AnalyticsModuleLayout.from_dict(_layout)




        data = cast(List[Any], d.pop("data"))


        fullscreen = d.pop("fullscreen", UNSET)

        id = d.pop("id", UNSET)

        _created_at = d.pop("createdAt", UNSET)
        created_at: Union[Unset, datetime.datetime]
        if isinstance(_created_at,  Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)




        _updated_at = d.pop("updatedAt", UNSET)
        updated_at: Union[Unset, datetime.datetime]
        if isinstance(_updated_at,  Unset):
            updated_at = UNSET
        else:
            updated_at = isoparse(_updated_at)




        analytics_module = cls(
            name=name,
            query=query,
            stream_ids=stream_ids,
            configuration=configuration,
            organization_id=organization_id,
            layout=layout,
            data=data,
            fullscreen=fullscreen,
            id=id,
            created_at=created_at,
            updated_at=updated_at,
        )

        analytics_module.additional_properties = d
        return analytics_module

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
