import datetime
from typing import (TYPE_CHECKING, Any, Dict, List, Optional, Type, TypeVar,
                    Union)

import attr
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.filter_ import Filter
  from ..models.view_configuration import ViewConfiguration




T = TypeVar("T", bound="Channel")

@attr.s(auto_attribs=True)
class Channel:
    """
    Attributes:
        name (str):
        organization_id (Union[Unset, str]):
        description (Union[Unset, str]):
        filter_ (Optional[Filter]):
        layout (Union[Unset, Any]):
        configuration (Union[Unset, List['ViewConfiguration']]):
        id (Union[Unset, str]):
        created_at (Union[Unset, datetime.datetime]):
        updated_at (Union[Unset, datetime.datetime]):
    """

    name: str
    filter_: Optional['Filter']
    organization_id: Union[Unset, str] = UNSET
    description: Union[Unset, str] = UNSET
    layout: Union[Unset, Any] = UNSET
    configuration: Union[Unset, List['ViewConfiguration']] = UNSET
    id: Union[Unset, str] = UNSET
    created_at: Union[Unset, datetime.datetime] = UNSET
    updated_at: Union[Unset, datetime.datetime] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        organization_id = self.organization_id
        description = self.description
        filter_ = self.filter_.to_dict() if self.filter_ else None

        layout = self.layout
        configuration: Union[Unset, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.configuration, Unset):
            configuration = []
            for configuration_item_data in self.configuration:
                configuration_item = configuration_item_data.to_dict()

                configuration.append(configuration_item)




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
            "filter": filter_,
        })
        if organization_id is not UNSET:
            field_dict["organizationId"] = organization_id
        if description is not UNSET:
            field_dict["description"] = description
        if layout is not UNSET:
            field_dict["layout"] = layout
        if configuration is not UNSET:
            field_dict["configuration"] = configuration
        if id is not UNSET:
            field_dict["id"] = id
        if created_at is not UNSET:
            field_dict["createdAt"] = created_at
        if updated_at is not UNSET:
            field_dict["updatedAt"] = updated_at

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.filter_ import Filter
        from ..models.view_configuration import ViewConfiguration
        d = src_dict.copy()
        name = d.pop("name")

        organization_id = d.pop("organizationId", UNSET)

        description = d.pop("description", UNSET)

        _filter_ = d.pop("filter")
        filter_: Optional[Filter]
        if _filter_ is None:
            filter_ = None
        else:
            filter_ = Filter.from_dict(_filter_)




        layout = d.pop("layout", UNSET)

        configuration = []
        _configuration = d.pop("configuration", UNSET)
        for configuration_item_data in (_configuration or []):
            configuration_item = ViewConfiguration.from_dict(configuration_item_data)



            configuration.append(configuration_item)


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




        channel = cls(
            name=name,
            organization_id=organization_id,
            description=description,
            filter_=filter_,
            layout=layout,
            configuration=configuration,
            id=id,
            created_at=created_at,
            updated_at=updated_at,
        )

        channel.additional_properties = d
        return channel

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
