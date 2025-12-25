import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.filter_ import Filter
  from ..models.view_configuration import ViewConfiguration




T = TypeVar("T", bound="PartialChannel")

@attr.s(auto_attribs=True)
class PartialChannel:
    """
    Attributes:
        organization_id (Union[Unset, str]):
        name (Union[Unset, str]):
        description (Union[Unset, str]):
        filter_ (Union[Unset, None, Filter]):
        layout (Union[Unset, Any]):
        configuration (Union[Unset, List['ViewConfiguration']]):
        id (Union[Unset, str]):
        created_at (Union[Unset, datetime.datetime]):
        updated_at (Union[Unset, datetime.datetime]):
    """

    organization_id: Union[Unset, str] = UNSET
    name: Union[Unset, str] = UNSET
    description: Union[Unset, str] = UNSET
    filter_: Union[Unset, None, 'Filter'] = UNSET
    layout: Union[Unset, Any] = UNSET
    configuration: Union[Unset, List['ViewConfiguration']] = UNSET
    id: Union[Unset, str] = UNSET
    created_at: Union[Unset, datetime.datetime] = UNSET
    updated_at: Union[Unset, datetime.datetime] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        organization_id = self.organization_id
        name = self.name
        description = self.description
        filter_: Union[Unset, None, Dict[str, Any]] = UNSET
        if not isinstance(self.filter_, Unset):
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
        })
        if organization_id is not UNSET:
            field_dict["organizationId"] = organization_id
        if name is not UNSET:
            field_dict["name"] = name
        if description is not UNSET:
            field_dict["description"] = description
        if filter_ is not UNSET:
            field_dict["filter"] = filter_
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
        organization_id = d.pop("organizationId", UNSET)

        name = d.pop("name", UNSET)

        description = d.pop("description", UNSET)

        _filter_ = d.pop("filter", UNSET)
        filter_: Union[Unset, None, Filter]
        if _filter_ is None:
            filter_ = None
        elif isinstance(_filter_,  Unset):
            filter_ = UNSET
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




        partial_channel = cls(
            organization_id=organization_id,
            name=name,
            description=description,
            filter_=filter_,
            layout=layout,
            configuration=configuration,
            id=id,
            created_at=created_at,
            updated_at=updated_at,
        )

        partial_channel.additional_properties = d
        return partial_channel

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
