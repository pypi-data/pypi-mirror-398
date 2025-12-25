from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="CommandDeliverySettings")

@attr.s(auto_attribs=True)
class CommandDeliverySettings:
    """
    Attributes:
        ttl_ms (Union[Unset, int]):
        retryable (Union[Unset, bool]):
    """

    ttl_ms: Union[Unset, int] = UNSET
    retryable: Union[Unset, bool] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        ttl_ms = self.ttl_ms
        retryable = self.retryable

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if ttl_ms is not UNSET:
            field_dict["ttlMs"] = ttl_ms
        if retryable is not UNSET:
            field_dict["retryable"] = retryable

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        ttl_ms = d.pop("ttlMs", UNSET)

        retryable = d.pop("retryable", UNSET)

        command_delivery_settings = cls(
            ttl_ms=ttl_ms,
            retryable=retryable,
        )

        command_delivery_settings.additional_properties = d
        return command_delivery_settings

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
