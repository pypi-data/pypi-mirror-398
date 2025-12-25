import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.device_configuration_document import \
      DeviceConfigurationDocument




T = TypeVar("T", bound="DeviceConfiguration")

@attr.s(auto_attribs=True)
class DeviceConfiguration:
    """
    Attributes:
        document (DeviceConfigurationDocument):
        device_id (Union[Unset, str]):
        version (Union[Unset, int]):
        created_at (Union[Unset, datetime.datetime]):
        updated_at (Union[Unset, datetime.datetime]):
    """

    document: 'DeviceConfigurationDocument'
    device_id: Union[Unset, str] = UNSET
    version: Union[Unset, int] = UNSET
    created_at: Union[Unset, datetime.datetime] = UNSET
    updated_at: Union[Unset, datetime.datetime] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        document = self.document.to_dict()

        device_id = self.device_id
        version = self.version
        created_at: Union[Unset, str] = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: Union[Unset, str] = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "document": document,
        })
        if device_id is not UNSET:
            field_dict["deviceId"] = device_id
        if version is not UNSET:
            field_dict["version"] = version
        if created_at is not UNSET:
            field_dict["createdAt"] = created_at
        if updated_at is not UNSET:
            field_dict["updatedAt"] = updated_at

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.device_configuration_document import \
            DeviceConfigurationDocument
        d = src_dict.copy()
        document = DeviceConfigurationDocument.from_dict(d.pop("document"))




        device_id = d.pop("deviceId", UNSET)

        version = d.pop("version", UNSET)

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




        device_configuration = cls(
            document=document,
            device_id=device_id,
            version=version,
            created_at=created_at,
            updated_at=updated_at,
        )

        device_configuration.additional_properties = d
        return device_configuration

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
