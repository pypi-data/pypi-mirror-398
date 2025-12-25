import datetime
from typing import Any, Dict, List, Type, TypeVar, Union

import attr
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="Adapter")

@attr.s(auto_attribs=True)
class Adapter:
    """
    Attributes:
        name (str): Name of this adapter.
        file_id (str): ID of the zip file which contains the adapter you want to add.
        exec_command (str): Enter the execution command to start this adapter (typically `./start.sh`).
        organization_id (Union[Unset, str]): ID of the organization to which you want to add this adapter.
        configuration_schema (Union[Unset, str]): Enter the configuration schema for this adapter (max 5000 characters).
        id (Union[Unset, str]):
        created_at (Union[Unset, datetime.datetime]):
        updated_at (Union[Unset, datetime.datetime]):
    """

    name: str
    file_id: str
    exec_command: str
    organization_id: Union[Unset, str] = UNSET
    configuration_schema: Union[Unset, str] = UNSET
    id: Union[Unset, str] = UNSET
    created_at: Union[Unset, datetime.datetime] = UNSET
    updated_at: Union[Unset, datetime.datetime] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        file_id = self.file_id
        exec_command = self.exec_command
        organization_id = self.organization_id
        configuration_schema = self.configuration_schema
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
            "fileId": file_id,
            "execCommand": exec_command,
        })
        if organization_id is not UNSET:
            field_dict["organizationId"] = organization_id
        if configuration_schema is not UNSET:
            field_dict["configurationSchema"] = configuration_schema
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

        file_id = d.pop("fileId")

        exec_command = d.pop("execCommand")

        organization_id = d.pop("organizationId", UNSET)

        configuration_schema = d.pop("configurationSchema", UNSET)

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




        adapter = cls(
            name=name,
            file_id=file_id,
            exec_command=exec_command,
            organization_id=organization_id,
            configuration_schema=configuration_schema,
            id=id,
            created_at=created_at,
            updated_at=updated_at,
        )

        adapter.additional_properties = d
        return adapter

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
