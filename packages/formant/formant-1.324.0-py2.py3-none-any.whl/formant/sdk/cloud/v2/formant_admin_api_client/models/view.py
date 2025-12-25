import datetime
from typing import (TYPE_CHECKING, Any, Dict, List, Optional, Type, TypeVar,
                    Union)

import attr
from dateutil.parser import isoparse

from ..models.view_layout_type import ViewLayoutType
from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.filter_ import Filter
  from ..models.view_configuration import ViewConfiguration
  from ..models.view_tags import ViewTags




T = TypeVar("T", bound="View")

@attr.s(auto_attribs=True)
class View:
    """
    Attributes:
        name (str):
        layout (Any):
        configuration (List['ViewConfiguration']):
        index (int):
        organization_id (Union[Unset, str]):
        description (Union[Unset, None, str]):
        url (Union[Unset, None, str]):
        show_on_single_device (Union[Unset, bool]):
        show_on_multi_device (Union[Unset, bool]):
        show_on_teleop (Union[Unset, bool]):
        show_timeline (Union[Unset, bool]):
        local_mode_enabled (Union[Unset, bool]):
        filter_ (Optional[Filter]):
        device_filter (Optional[Filter]):
        group_filter (Optional[Filter]):
        layout_type (Union[Unset, None, ViewLayoutType]):
        smart_fleet_id (Union[Unset, None, str]):
        id (Union[Unset, str]):
        created_at (Union[Unset, datetime.datetime]):
        updated_at (Union[Unset, datetime.datetime]):
        tags (Union[Unset, ViewTags]):
    """

    name: str
    layout: Any
    configuration: List['ViewConfiguration']
    index: int
    filter_: Optional['Filter']
    device_filter: Optional['Filter']
    group_filter: Optional['Filter']
    organization_id: Union[Unset, str] = UNSET
    description: Union[Unset, None, str] = UNSET
    url: Union[Unset, None, str] = UNSET
    show_on_single_device: Union[Unset, bool] = UNSET
    show_on_multi_device: Union[Unset, bool] = UNSET
    show_on_teleop: Union[Unset, bool] = UNSET
    show_timeline: Union[Unset, bool] = UNSET
    local_mode_enabled: Union[Unset, bool] = UNSET
    layout_type: Union[Unset, None, ViewLayoutType] = UNSET
    smart_fleet_id: Union[Unset, None, str] = UNSET
    id: Union[Unset, str] = UNSET
    created_at: Union[Unset, datetime.datetime] = UNSET
    updated_at: Union[Unset, datetime.datetime] = UNSET
    tags: Union[Unset, 'ViewTags'] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        layout = self.layout
        configuration = []
        for configuration_item_data in self.configuration:
            configuration_item = configuration_item_data.to_dict()

            configuration.append(configuration_item)




        index = self.index
        organization_id = self.organization_id
        description = self.description
        url = self.url
        show_on_single_device = self.show_on_single_device
        show_on_multi_device = self.show_on_multi_device
        show_on_teleop = self.show_on_teleop
        show_timeline = self.show_timeline
        local_mode_enabled = self.local_mode_enabled
        filter_ = self.filter_.to_dict() if self.filter_ else None

        device_filter = self.device_filter.to_dict() if self.device_filter else None

        group_filter = self.group_filter.to_dict() if self.group_filter else None

        layout_type: Union[Unset, None, str] = UNSET
        if not isinstance(self.layout_type, Unset):
            layout_type = self.layout_type.value if self.layout_type else None

        smart_fleet_id = self.smart_fleet_id
        id = self.id
        created_at: Union[Unset, str] = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: Union[Unset, str] = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        tags: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.tags, Unset):
            tags = self.tags.to_dict()


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "name": name,
            "layout": layout,
            "configuration": configuration,
            "index": index,
            "filter": filter_,
            "deviceFilter": device_filter,
            "groupFilter": group_filter,
        })
        if organization_id is not UNSET:
            field_dict["organizationId"] = organization_id
        if description is not UNSET:
            field_dict["description"] = description
        if url is not UNSET:
            field_dict["url"] = url
        if show_on_single_device is not UNSET:
            field_dict["showOnSingleDevice"] = show_on_single_device
        if show_on_multi_device is not UNSET:
            field_dict["showOnMultiDevice"] = show_on_multi_device
        if show_on_teleop is not UNSET:
            field_dict["showOnTeleop"] = show_on_teleop
        if show_timeline is not UNSET:
            field_dict["showTimeline"] = show_timeline
        if local_mode_enabled is not UNSET:
            field_dict["localModeEnabled"] = local_mode_enabled
        if layout_type is not UNSET:
            field_dict["layoutType"] = layout_type
        if smart_fleet_id is not UNSET:
            field_dict["smartFleetId"] = smart_fleet_id
        if id is not UNSET:
            field_dict["id"] = id
        if created_at is not UNSET:
            field_dict["createdAt"] = created_at
        if updated_at is not UNSET:
            field_dict["updatedAt"] = updated_at
        if tags is not UNSET:
            field_dict["tags"] = tags

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.filter_ import Filter
        from ..models.view_configuration import ViewConfiguration
        from ..models.view_tags import ViewTags
        d = src_dict.copy()
        name = d.pop("name")

        layout = d.pop("layout")

        configuration = []
        _configuration = d.pop("configuration")
        for configuration_item_data in (_configuration):
            configuration_item = ViewConfiguration.from_dict(configuration_item_data)



            configuration.append(configuration_item)


        index = d.pop("index")

        organization_id = d.pop("organizationId", UNSET)

        description = d.pop("description", UNSET)

        url = d.pop("url", UNSET)

        show_on_single_device = d.pop("showOnSingleDevice", UNSET)

        show_on_multi_device = d.pop("showOnMultiDevice", UNSET)

        show_on_teleop = d.pop("showOnTeleop", UNSET)

        show_timeline = d.pop("showTimeline", UNSET)

        local_mode_enabled = d.pop("localModeEnabled", UNSET)

        _filter_ = d.pop("filter")
        filter_: Optional[Filter]
        if _filter_ is None:
            filter_ = None
        else:
            filter_ = Filter.from_dict(_filter_)




        _device_filter = d.pop("deviceFilter")
        device_filter: Optional[Filter]
        if _device_filter is None:
            device_filter = None
        else:
            device_filter = Filter.from_dict(_device_filter)




        _group_filter = d.pop("groupFilter")
        group_filter: Optional[Filter]
        if _group_filter is None:
            group_filter = None
        else:
            group_filter = Filter.from_dict(_group_filter)




        _layout_type = d.pop("layoutType", UNSET)
        layout_type: Union[Unset, None, ViewLayoutType]
        if _layout_type is None:
            layout_type = None
        elif isinstance(_layout_type,  Unset):
            layout_type = UNSET
        else:
            layout_type = ViewLayoutType(_layout_type)




        smart_fleet_id = d.pop("smartFleetId", UNSET)

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




        _tags = d.pop("tags", UNSET)
        tags: Union[Unset, ViewTags]
        if isinstance(_tags,  Unset):
            tags = UNSET
        else:
            tags = ViewTags.from_dict(_tags)




        view = cls(
            name=name,
            layout=layout,
            configuration=configuration,
            index=index,
            organization_id=organization_id,
            description=description,
            url=url,
            show_on_single_device=show_on_single_device,
            show_on_multi_device=show_on_multi_device,
            show_on_teleop=show_on_teleop,
            show_timeline=show_timeline,
            local_mode_enabled=local_mode_enabled,
            filter_=filter_,
            device_filter=device_filter,
            group_filter=group_filter,
            layout_type=layout_type,
            smart_fleet_id=smart_fleet_id,
            id=id,
            created_at=created_at,
            updated_at=updated_at,
            tags=tags,
        )

        view.additional_properties = d
        return view

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
