from typing import Any, Dict, List, Type, TypeVar

import attr

T = TypeVar("T", bound="SsoGroupNameToTeamMapping")

@attr.s(auto_attribs=True)
class SsoGroupNameToTeamMapping:
    """
    Attributes:
        sso_group_name (str):
        team_id (str):
    """

    sso_group_name: str
    team_id: str
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        sso_group_name = self.sso_group_name
        team_id = self.team_id

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "ssoGroupName": sso_group_name,
            "teamId": team_id,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        sso_group_name = d.pop("ssoGroupName")

        team_id = d.pop("teamId")

        sso_group_name_to_team_mapping = cls(
            sso_group_name=sso_group_name,
            team_id=team_id,
        )

        sso_group_name_to_team_mapping.additional_properties = d
        return sso_group_name_to_team_mapping

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
