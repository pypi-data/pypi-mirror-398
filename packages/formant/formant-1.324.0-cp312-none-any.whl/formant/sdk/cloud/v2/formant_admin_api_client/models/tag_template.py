import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.label import Label
  from ..models.tag_template_tags import TagTemplateTags




T = TypeVar("T", bound="TagTemplate")

@attr.s(auto_attribs=True)
class TagTemplate:
    """
    Attributes:
        tag_key (Any): Key of this tag template.
        organization_id (Union[Unset, str]): ID of the organization to which to add this tag template.
        is_group (Union[Unset, bool]): Is this tag used to create device groups?
        is_telemetry_filter (Union[Unset, bool]): Is this tag used to filter telemetry data?
        is_event_filter (Union[Unset, bool]): Is this tag used to filter events?
        enabled (Union[Unset, bool]): Set this to `false` to delete this tag template.
        description (Union[Unset, None, str]): Description of this tag template.
        label_set_id (Union[Unset, None, str]): Internal use only, ignore.
        label_enum (Union[Unset, None, List['Label']]): Internal use only, ignore.
        id (Union[Unset, str]):
        created_at (Union[Unset, datetime.datetime]):
        updated_at (Union[Unset, datetime.datetime]):
        tags (Union[Unset, TagTemplateTags]):
    """

    tag_key: Any
    organization_id: Union[Unset, str] = UNSET
    is_group: Union[Unset, bool] = UNSET
    is_telemetry_filter: Union[Unset, bool] = UNSET
    is_event_filter: Union[Unset, bool] = UNSET
    enabled: Union[Unset, bool] = UNSET
    description: Union[Unset, None, str] = UNSET
    label_set_id: Union[Unset, None, str] = UNSET
    label_enum: Union[Unset, None, List['Label']] = UNSET
    id: Union[Unset, str] = UNSET
    created_at: Union[Unset, datetime.datetime] = UNSET
    updated_at: Union[Unset, datetime.datetime] = UNSET
    tags: Union[Unset, 'TagTemplateTags'] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        tag_key = self.tag_key
        organization_id = self.organization_id
        is_group = self.is_group
        is_telemetry_filter = self.is_telemetry_filter
        is_event_filter = self.is_event_filter
        enabled = self.enabled
        description = self.description
        label_set_id = self.label_set_id
        label_enum: Union[Unset, None, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.label_enum, Unset):
            if self.label_enum is None:
                label_enum = None
            else:
                label_enum = []
                for label_enum_item_data in self.label_enum:
                    label_enum_item = label_enum_item_data.to_dict()

                    label_enum.append(label_enum_item)




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
            "tagKey": tag_key,
        })
        if organization_id is not UNSET:
            field_dict["organizationId"] = organization_id
        if is_group is not UNSET:
            field_dict["isGroup"] = is_group
        if is_telemetry_filter is not UNSET:
            field_dict["isTelemetryFilter"] = is_telemetry_filter
        if is_event_filter is not UNSET:
            field_dict["isEventFilter"] = is_event_filter
        if enabled is not UNSET:
            field_dict["enabled"] = enabled
        if description is not UNSET:
            field_dict["description"] = description
        if label_set_id is not UNSET:
            field_dict["labelSetId"] = label_set_id
        if label_enum is not UNSET:
            field_dict["labelEnum"] = label_enum
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
        from ..models.label import Label
        from ..models.tag_template_tags import TagTemplateTags
        d = src_dict.copy()
        tag_key = d.pop("tagKey")

        organization_id = d.pop("organizationId", UNSET)

        is_group = d.pop("isGroup", UNSET)

        is_telemetry_filter = d.pop("isTelemetryFilter", UNSET)

        is_event_filter = d.pop("isEventFilter", UNSET)

        enabled = d.pop("enabled", UNSET)

        description = d.pop("description", UNSET)

        label_set_id = d.pop("labelSetId", UNSET)

        label_enum = []
        _label_enum = d.pop("labelEnum", UNSET)
        for label_enum_item_data in (_label_enum or []):
            label_enum_item = Label.from_dict(label_enum_item_data)



            label_enum.append(label_enum_item)


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
        tags: Union[Unset, TagTemplateTags]
        if isinstance(_tags,  Unset):
            tags = UNSET
        else:
            tags = TagTemplateTags.from_dict(_tags)




        tag_template = cls(
            tag_key=tag_key,
            organization_id=organization_id,
            is_group=is_group,
            is_telemetry_filter=is_telemetry_filter,
            is_event_filter=is_event_filter,
            enabled=enabled,
            description=description,
            label_set_id=label_set_id,
            label_enum=label_enum,
            id=id,
            created_at=created_at,
            updated_at=updated_at,
            tags=tags,
        )

        tag_template.additional_properties = d
        return tag_template

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
