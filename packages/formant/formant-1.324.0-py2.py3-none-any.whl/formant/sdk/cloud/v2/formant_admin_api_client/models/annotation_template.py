import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.annotation_field import AnnotationField
  from ..models.annotation_template_tags import AnnotationTemplateTags
  from ..models.scope_filter import ScopeFilter




T = TypeVar("T", bound="AnnotationTemplate")

@attr.s(auto_attribs=True)
class AnnotationTemplate:
    """
    Attributes:
        name (str): Name of this annotation template.
        fields (List['AnnotationField']): JSON object containing the fields for this annotation template.
        organization_id (Union[Unset, str]): ID of the organization to which you want to add this annotation template.
        description (Union[Unset, str]): Description for this annotation template.
        publish_to_google_spreadsheet_url (Union[Unset, None, str]): If you want to define your annotation template via
            Google Sheets, enter the URL to the sheet.
        device_scope (Union[Unset, None, ScopeFilter]):
        enabled (Union[Unset, bool]):
        id (Union[Unset, str]):
        created_at (Union[Unset, datetime.datetime]):
        updated_at (Union[Unset, datetime.datetime]):
        tags (Union[Unset, AnnotationTemplateTags]):
    """

    name: str
    fields: List['AnnotationField']
    organization_id: Union[Unset, str] = UNSET
    description: Union[Unset, str] = UNSET
    publish_to_google_spreadsheet_url: Union[Unset, None, str] = UNSET
    device_scope: Union[Unset, None, 'ScopeFilter'] = UNSET
    enabled: Union[Unset, bool] = UNSET
    id: Union[Unset, str] = UNSET
    created_at: Union[Unset, datetime.datetime] = UNSET
    updated_at: Union[Unset, datetime.datetime] = UNSET
    tags: Union[Unset, 'AnnotationTemplateTags'] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        fields = []
        for fields_item_data in self.fields:
            fields_item = fields_item_data.to_dict()

            fields.append(fields_item)




        organization_id = self.organization_id
        description = self.description
        publish_to_google_spreadsheet_url = self.publish_to_google_spreadsheet_url
        device_scope: Union[Unset, None, Dict[str, Any]] = UNSET
        if not isinstance(self.device_scope, Unset):
            device_scope = self.device_scope.to_dict() if self.device_scope else None

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
            "name": name,
            "fields": fields,
        })
        if organization_id is not UNSET:
            field_dict["organizationId"] = organization_id
        if description is not UNSET:
            field_dict["description"] = description
        if publish_to_google_spreadsheet_url is not UNSET:
            field_dict["publishToGoogleSpreadsheetUrl"] = publish_to_google_spreadsheet_url
        if device_scope is not UNSET:
            field_dict["deviceScope"] = device_scope
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
        from ..models.annotation_field import AnnotationField
        from ..models.annotation_template_tags import AnnotationTemplateTags
        from ..models.scope_filter import ScopeFilter
        d = src_dict.copy()
        name = d.pop("name")

        fields = []
        _fields = d.pop("fields")
        for fields_item_data in (_fields):
            fields_item = AnnotationField.from_dict(fields_item_data)



            fields.append(fields_item)


        organization_id = d.pop("organizationId", UNSET)

        description = d.pop("description", UNSET)

        publish_to_google_spreadsheet_url = d.pop("publishToGoogleSpreadsheetUrl", UNSET)

        _device_scope = d.pop("deviceScope", UNSET)
        device_scope: Union[Unset, None, ScopeFilter]
        if _device_scope is None:
            device_scope = None
        elif isinstance(_device_scope,  Unset):
            device_scope = UNSET
        else:
            device_scope = ScopeFilter.from_dict(_device_scope)




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
        tags: Union[Unset, AnnotationTemplateTags]
        if isinstance(_tags,  Unset):
            tags = UNSET
        else:
            tags = AnnotationTemplateTags.from_dict(_tags)




        annotation_template = cls(
            name=name,
            fields=fields,
            organization_id=organization_id,
            description=description,
            publish_to_google_spreadsheet_url=publish_to_google_spreadsheet_url,
            device_scope=device_scope,
            enabled=enabled,
            id=id,
            created_at=created_at,
            updated_at=updated_at,
            tags=tags,
        )

        annotation_template.additional_properties = d
        return annotation_template

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
