import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.device_configuration_document import \
      DeviceConfigurationDocument
  from ..models.partial_device_configuration_template_tags import \
      PartialDeviceConfigurationTemplateTags




T = TypeVar("T", bound="PartialDeviceConfigurationTemplate")

@attr.s(auto_attribs=True)
class PartialDeviceConfigurationTemplate:
    """
    Attributes:
        organization_id (Union[Unset, str]):
        name (Union[Unset, str]):
        document (Union[Unset, DeviceConfigurationDocument]):
        enabled (Union[Unset, bool]):
        id (Union[Unset, str]):
        created_at (Union[Unset, datetime.datetime]):
        updated_at (Union[Unset, datetime.datetime]):
        tags (Union[Unset, PartialDeviceConfigurationTemplateTags]):
    """

    organization_id: Union[Unset, str] = UNSET
    name: Union[Unset, str] = UNSET
    document: Union[Unset, 'DeviceConfigurationDocument'] = UNSET
    enabled: Union[Unset, bool] = UNSET
    id: Union[Unset, str] = UNSET
    created_at: Union[Unset, datetime.datetime] = UNSET
    updated_at: Union[Unset, datetime.datetime] = UNSET
    tags: Union[Unset, 'PartialDeviceConfigurationTemplateTags'] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        organization_id = self.organization_id
        name = self.name
        document: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.document, Unset):
            document = self.document.to_dict()

        enabled = self.enabled
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
        })
        if organization_id is not UNSET:
            field_dict["organizationId"] = organization_id
        if name is not UNSET:
            field_dict["name"] = name
        if document is not UNSET:
            field_dict["document"] = document
        if enabled is not UNSET:
            field_dict["enabled"] = enabled
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
        from ..models.device_configuration_document import \
            DeviceConfigurationDocument
        from ..models.partial_device_configuration_template_tags import \
            PartialDeviceConfigurationTemplateTags
        d = src_dict.copy()
        organization_id = d.pop("organizationId", UNSET)

        name = d.pop("name", UNSET)

        _document = d.pop("document", UNSET)
        document: Union[Unset, DeviceConfigurationDocument]
        if isinstance(_document,  Unset):
            document = UNSET
        else:
            document = DeviceConfigurationDocument.from_dict(_document)




        enabled = d.pop("enabled", UNSET)

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
        tags: Union[Unset, PartialDeviceConfigurationTemplateTags]
        if isinstance(_tags,  Unset):
            tags = UNSET
        else:
            tags = PartialDeviceConfigurationTemplateTags.from_dict(_tags)




        partial_device_configuration_template = cls(
            organization_id=organization_id,
            name=name,
            document=document,
            enabled=enabled,
            id=id,
            created_at=created_at,
            updated_at=updated_at,
            tags=tags,
        )

        partial_device_configuration_template.additional_properties = d
        return partial_device_configuration_template

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
