from typing import Any, Dict, List, Type, TypeVar, cast

import attr

T = TypeVar("T", bound="QueryByDeviceRequest")

@attr.s(auto_attribs=True)
class QueryByDeviceRequest:
    """
    Attributes:
        device_ids (List[str]):
    """

    device_ids: List[str]
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        device_ids = self.device_ids





        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "deviceIds": device_ids,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        device_ids = cast(List[str], d.pop("deviceIds"))


        query_by_device_request = cls(
            device_ids=device_ids,
        )

        query_by_device_request.additional_properties = d
        return query_by_device_request

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
