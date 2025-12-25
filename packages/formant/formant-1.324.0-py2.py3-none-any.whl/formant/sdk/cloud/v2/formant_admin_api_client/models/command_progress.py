from typing import Any, Dict, List, Type, TypeVar

import attr

T = TypeVar("T", bound="CommandProgress")

@attr.s(auto_attribs=True)
class CommandProgress:
    """
    Attributes:
        command_id (str):
        progress (int):
        pending (bool):
    """

    command_id: str
    progress: int
    pending: bool
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        command_id = self.command_id
        progress = self.progress
        pending = self.pending

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "commandId": command_id,
            "progress": progress,
            "pending": pending,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        command_id = d.pop("commandId")

        progress = d.pop("progress")

        pending = d.pop("pending")

        command_progress = cls(
            command_id=command_id,
            progress=progress,
            pending=pending,
        )

        command_progress.additional_properties = d
        return command_progress

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
