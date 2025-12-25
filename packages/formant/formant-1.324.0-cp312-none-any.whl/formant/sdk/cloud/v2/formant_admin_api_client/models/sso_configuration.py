import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr
from dateutil.parser import isoparse

from ..models.sso_configuration_authentication_flow import \
    SsoConfigurationAuthenticationFlow
from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.sso_group_name_to_team_mapping import SsoGroupNameToTeamMapping




T = TypeVar("T", bound="SsoConfiguration")

@attr.s(auto_attribs=True)
class SsoConfiguration:
    """
    Attributes:
        domain (str):
        authentication_flow (SsoConfigurationAuthenticationFlow):
        enabled (bool):
        organization_id (Union[Unset, str]): ID of the organization to which to apply this SSO configuration.
        default_role_id (Union[Unset, str]): Default role assigned to all new users who sign up via SSO. Either a
            default team or a default role is required.
        default_team_id (Union[Unset, str]): Default team to which all new users who sign up via SSO will be assigned.
            Either a default team or a default role is required.
        default_account_id (Union[Unset, None, str]):
        client_id (Union[Unset, None, str]):
        issuer (Union[Unset, None, str]):
        sso_group_name_to_team_mappings (Union[Unset, List['SsoGroupNameToTeamMapping']]):
        allow_password_login (Union[Unset, bool]):
        id (Union[Unset, str]):
        created_at (Union[Unset, datetime.datetime]):
        updated_at (Union[Unset, datetime.datetime]):
    """

    domain: str
    authentication_flow: SsoConfigurationAuthenticationFlow
    enabled: bool
    organization_id: Union[Unset, str] = UNSET
    default_role_id: Union[Unset, str] = UNSET
    default_team_id: Union[Unset, str] = UNSET
    default_account_id: Union[Unset, None, str] = UNSET
    client_id: Union[Unset, None, str] = UNSET
    issuer: Union[Unset, None, str] = UNSET
    sso_group_name_to_team_mappings: Union[Unset, List['SsoGroupNameToTeamMapping']] = UNSET
    allow_password_login: Union[Unset, bool] = UNSET
    id: Union[Unset, str] = UNSET
    created_at: Union[Unset, datetime.datetime] = UNSET
    updated_at: Union[Unset, datetime.datetime] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        domain = self.domain
        authentication_flow = self.authentication_flow.value

        enabled = self.enabled
        organization_id = self.organization_id
        default_role_id = self.default_role_id
        default_team_id = self.default_team_id
        default_account_id = self.default_account_id
        client_id = self.client_id
        issuer = self.issuer
        sso_group_name_to_team_mappings: Union[Unset, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.sso_group_name_to_team_mappings, Unset):
            sso_group_name_to_team_mappings = []
            for sso_group_name_to_team_mappings_item_data in self.sso_group_name_to_team_mappings:
                sso_group_name_to_team_mappings_item = sso_group_name_to_team_mappings_item_data.to_dict()

                sso_group_name_to_team_mappings.append(sso_group_name_to_team_mappings_item)




        allow_password_login = self.allow_password_login
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
            "domain": domain,
            "authenticationFlow": authentication_flow,
            "enabled": enabled,
        })
        if organization_id is not UNSET:
            field_dict["organizationId"] = organization_id
        if default_role_id is not UNSET:
            field_dict["defaultRoleId"] = default_role_id
        if default_team_id is not UNSET:
            field_dict["defaultTeamId"] = default_team_id
        if default_account_id is not UNSET:
            field_dict["defaultAccountId"] = default_account_id
        if client_id is not UNSET:
            field_dict["clientId"] = client_id
        if issuer is not UNSET:
            field_dict["issuer"] = issuer
        if sso_group_name_to_team_mappings is not UNSET:
            field_dict["ssoGroupNameToTeamMappings"] = sso_group_name_to_team_mappings
        if allow_password_login is not UNSET:
            field_dict["allowPasswordLogin"] = allow_password_login
        if id is not UNSET:
            field_dict["id"] = id
        if created_at is not UNSET:
            field_dict["createdAt"] = created_at
        if updated_at is not UNSET:
            field_dict["updatedAt"] = updated_at

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.sso_group_name_to_team_mapping import \
            SsoGroupNameToTeamMapping
        d = src_dict.copy()
        domain = d.pop("domain")

        authentication_flow = SsoConfigurationAuthenticationFlow(d.pop("authenticationFlow"))




        enabled = d.pop("enabled")

        organization_id = d.pop("organizationId", UNSET)

        default_role_id = d.pop("defaultRoleId", UNSET)

        default_team_id = d.pop("defaultTeamId", UNSET)

        default_account_id = d.pop("defaultAccountId", UNSET)

        client_id = d.pop("clientId", UNSET)

        issuer = d.pop("issuer", UNSET)

        sso_group_name_to_team_mappings = []
        _sso_group_name_to_team_mappings = d.pop("ssoGroupNameToTeamMappings", UNSET)
        for sso_group_name_to_team_mappings_item_data in (_sso_group_name_to_team_mappings or []):
            sso_group_name_to_team_mappings_item = SsoGroupNameToTeamMapping.from_dict(sso_group_name_to_team_mappings_item_data)



            sso_group_name_to_team_mappings.append(sso_group_name_to_team_mappings_item)


        allow_password_login = d.pop("allowPasswordLogin", UNSET)

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




        sso_configuration = cls(
            domain=domain,
            authentication_flow=authentication_flow,
            enabled=enabled,
            organization_id=organization_id,
            default_role_id=default_role_id,
            default_team_id=default_team_id,
            default_account_id=default_account_id,
            client_id=client_id,
            issuer=issuer,
            sso_group_name_to_team_mappings=sso_group_name_to_team_mappings,
            allow_password_login=allow_password_login,
            id=id,
            created_at=created_at,
            updated_at=updated_at,
        )

        sso_configuration.additional_properties = d
        return sso_configuration

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
