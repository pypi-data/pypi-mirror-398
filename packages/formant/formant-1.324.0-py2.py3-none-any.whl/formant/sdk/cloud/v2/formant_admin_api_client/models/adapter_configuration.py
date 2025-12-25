from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="AdapterConfiguration")

@attr.s(auto_attribs=True)
class AdapterConfiguration:
    """
    Attributes:
        id (str):
        name (str):
        file_id (str):
        exec_command (str):
        configuration (Union[Unset, str]):
    """

    id: str
    name: str
    file_id: str
    exec_command: str
    configuration: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        id = self.id
        name = self.name
        file_id = self.file_id
        exec_command = self.exec_command
        configuration = self.configuration

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "id": id,
            "name": name,
            "fileId": file_id,
            "execCommand": exec_command,
        })
        if configuration is not UNSET:
            field_dict["configuration"] = configuration

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        id = d.pop("id")

        name = d.pop("name")

        file_id = d.pop("fileId")

        exec_command = d.pop("execCommand")

        configuration = d.pop("configuration", UNSET)

        adapter_configuration = cls(
            id=id,
            name=name,
            file_id=file_id,
            exec_command=exec_command,
            configuration=configuration,
        )

        adapter_configuration.additional_properties = d
        return adapter_configuration

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
