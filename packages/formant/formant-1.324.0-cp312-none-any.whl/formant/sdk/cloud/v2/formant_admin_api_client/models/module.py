import datetime
from typing import Any, Dict, List, Type, TypeVar, Union

import attr
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="Module")

@attr.s(auto_attribs=True)
class Module:
    """
    Attributes:
        name (str):
        url (str):
        organization_id (Union[Unset, str]):
        preview_image_url (Union[Unset, str]):
        icon_image_url (Union[Unset, None, str]):
        configuration_schema_url (Union[Unset, None, str]):
        default_configuration_id (Union[Unset, None, str]):
        description (Union[Unset, None, str]):
        help_url (Union[Unset, None, str]):
        fullscreen (Union[Unset, None, bool]):
        is_embedded (Union[Unset, bool]):
        prompt_template_url (Union[Unset, None, str]):
        id (Union[Unset, str]):
        created_at (Union[Unset, datetime.datetime]):
        updated_at (Union[Unset, datetime.datetime]):
    """

    name: str
    url: str
    organization_id: Union[Unset, str] = UNSET
    preview_image_url: Union[Unset, str] = UNSET
    icon_image_url: Union[Unset, None, str] = UNSET
    configuration_schema_url: Union[Unset, None, str] = UNSET
    default_configuration_id: Union[Unset, None, str] = UNSET
    description: Union[Unset, None, str] = UNSET
    help_url: Union[Unset, None, str] = UNSET
    fullscreen: Union[Unset, None, bool] = UNSET
    is_embedded: Union[Unset, bool] = UNSET
    prompt_template_url: Union[Unset, None, str] = UNSET
    id: Union[Unset, str] = UNSET
    created_at: Union[Unset, datetime.datetime] = UNSET
    updated_at: Union[Unset, datetime.datetime] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        url = self.url
        organization_id = self.organization_id
        preview_image_url = self.preview_image_url
        icon_image_url = self.icon_image_url
        configuration_schema_url = self.configuration_schema_url
        default_configuration_id = self.default_configuration_id
        description = self.description
        help_url = self.help_url
        fullscreen = self.fullscreen
        is_embedded = self.is_embedded
        prompt_template_url = self.prompt_template_url
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
            "url": url,
        })
        if organization_id is not UNSET:
            field_dict["organizationId"] = organization_id
        if preview_image_url is not UNSET:
            field_dict["previewImageUrl"] = preview_image_url
        if icon_image_url is not UNSET:
            field_dict["iconImageUrl"] = icon_image_url
        if configuration_schema_url is not UNSET:
            field_dict["configurationSchemaUrl"] = configuration_schema_url
        if default_configuration_id is not UNSET:
            field_dict["defaultConfigurationId"] = default_configuration_id
        if description is not UNSET:
            field_dict["description"] = description
        if help_url is not UNSET:
            field_dict["helpUrl"] = help_url
        if fullscreen is not UNSET:
            field_dict["fullscreen"] = fullscreen
        if is_embedded is not UNSET:
            field_dict["isEmbedded"] = is_embedded
        if prompt_template_url is not UNSET:
            field_dict["promptTemplateUrl"] = prompt_template_url
        if id is not UNSET:
            field_dict["id"] = id
        if created_at is not UNSET:
            field_dict["createdAt"] = created_at
        if updated_at is not UNSET:
            field_dict["updatedAt"] = updated_at

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        name = d.pop("name")

        url = d.pop("url")

        organization_id = d.pop("organizationId", UNSET)

        preview_image_url = d.pop("previewImageUrl", UNSET)

        icon_image_url = d.pop("iconImageUrl", UNSET)

        configuration_schema_url = d.pop("configurationSchemaUrl", UNSET)

        default_configuration_id = d.pop("defaultConfigurationId", UNSET)

        description = d.pop("description", UNSET)

        help_url = d.pop("helpUrl", UNSET)

        fullscreen = d.pop("fullscreen", UNSET)

        is_embedded = d.pop("isEmbedded", UNSET)

        prompt_template_url = d.pop("promptTemplateUrl", UNSET)

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




        module = cls(
            name=name,
            url=url,
            organization_id=organization_id,
            preview_image_url=preview_image_url,
            icon_image_url=icon_image_url,
            configuration_schema_url=configuration_schema_url,
            default_configuration_id=default_configuration_id,
            description=description,
            help_url=help_url,
            fullscreen=fullscreen,
            is_embedded=is_embedded,
            prompt_template_url=prompt_template_url,
            id=id,
            created_at=created_at,
            updated_at=updated_at,
        )

        module.additional_properties = d
        return module

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
