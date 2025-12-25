import datetime
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

import attr
from dateutil.parser import isoparse

from ..models.email_configuration_email_type import EmailConfigurationEmailType
from ..models.email_configuration_language import EmailConfigurationLanguage
from ..types import UNSET, Unset

T = TypeVar("T", bound="EmailConfiguration")

@attr.s(auto_attribs=True)
class EmailConfiguration:
    """
    Attributes:
        email_type (EmailConfigurationEmailType):
        active (bool):
        organization_id (Union[Unset, str]): ID of the organization to which this user belongs.
        subject (Union[Unset, None, str]):
        email_content (Union[Unset, None, str]):
        email_address_alias (Union[Unset, None, str]):
        team_id (Optional[str]):
        language (Union[Unset, EmailConfigurationLanguage]):
        id (Union[Unset, str]):
        created_at (Union[Unset, datetime.datetime]):
        updated_at (Union[Unset, datetime.datetime]):
    """

    email_type: EmailConfigurationEmailType
    active: bool
    team_id: Optional[str]
    organization_id: Union[Unset, str] = UNSET
    subject: Union[Unset, None, str] = UNSET
    email_content: Union[Unset, None, str] = UNSET
    email_address_alias: Union[Unset, None, str] = UNSET
    language: Union[Unset, EmailConfigurationLanguage] = UNSET
    id: Union[Unset, str] = UNSET
    created_at: Union[Unset, datetime.datetime] = UNSET
    updated_at: Union[Unset, datetime.datetime] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        email_type = self.email_type.value

        active = self.active
        organization_id = self.organization_id
        subject = self.subject
        email_content = self.email_content
        email_address_alias = self.email_address_alias
        team_id = self.team_id
        language: Union[Unset, str] = UNSET
        if not isinstance(self.language, Unset):
            language = self.language.value

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
            "emailType": email_type,
            "active": active,
            "teamId": team_id,
        })
        if organization_id is not UNSET:
            field_dict["organizationId"] = organization_id
        if subject is not UNSET:
            field_dict["subject"] = subject
        if email_content is not UNSET:
            field_dict["emailContent"] = email_content
        if email_address_alias is not UNSET:
            field_dict["emailAddressAlias"] = email_address_alias
        if language is not UNSET:
            field_dict["language"] = language
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
        email_type = EmailConfigurationEmailType(d.pop("emailType"))




        active = d.pop("active")

        organization_id = d.pop("organizationId", UNSET)

        subject = d.pop("subject", UNSET)

        email_content = d.pop("emailContent", UNSET)

        email_address_alias = d.pop("emailAddressAlias", UNSET)

        team_id = d.pop("teamId")

        _language = d.pop("language", UNSET)
        language: Union[Unset, EmailConfigurationLanguage]
        if isinstance(_language,  Unset):
            language = UNSET
        else:
            language = EmailConfigurationLanguage(_language)




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




        email_configuration = cls(
            email_type=email_type,
            active=active,
            organization_id=organization_id,
            subject=subject,
            email_content=email_content,
            email_address_alias=email_address_alias,
            team_id=team_id,
            language=language,
            id=id,
            created_at=created_at,
            updated_at=updated_at,
        )

        email_configuration.additional_properties = d
        return email_configuration

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
