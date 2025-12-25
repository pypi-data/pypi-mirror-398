from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdatedAgentVersionResponse")

@attr.s(auto_attribs=True)
class UpdatedAgentVersionResponse:
    """
    Attributes:
        desired_agent_version (Union[Unset, str]):
    """

    desired_agent_version: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        desired_agent_version = self.desired_agent_version

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if desired_agent_version is not UNSET:
            field_dict["desiredAgentVersion"] = desired_agent_version

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        desired_agent_version = d.pop("desiredAgentVersion", UNSET)

        updated_agent_version_response = cls(
            desired_agent_version=desired_agent_version,
        )

        updated_agent_version_response.additional_properties = d
        return updated_agent_version_response

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
