import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

import attr
from dateutil.parser import isoparse

if TYPE_CHECKING:
  from ..models.command_parameter import CommandParameter




T = TypeVar("T", bound="CommandRequest")

@attr.s(auto_attribs=True)
class CommandRequest:
    """
    Attributes:
        id (str):
        command (str):
        parameter (CommandParameter):
        created_at (datetime.datetime):
    """

    id: str
    command: str
    parameter: 'CommandParameter'
    created_at: datetime.datetime
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        id = self.id
        command = self.command
        parameter = self.parameter.to_dict()

        created_at = self.created_at.isoformat()


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "id": id,
            "command": command,
            "parameter": parameter,
            "createdAt": created_at,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.command_parameter import CommandParameter
        d = src_dict.copy()
        id = d.pop("id")

        command = d.pop("command")

        parameter = CommandParameter.from_dict(d.pop("parameter"))




        created_at = isoparse(d.pop("createdAt"))




        command_request = cls(
            id=id,
            command=command,
            parameter=parameter,
            created_at=created_at,
        )

        command_request.additional_properties = d
        return command_request

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
