from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..models.health_status import HealthStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="Health")

@attr.s(auto_attribs=True)
class Health:
    """
    Attributes:
        status (HealthStatus):
        clock_skew_ms (Union[Unset, int]):
    """

    status: HealthStatus
    clock_skew_ms: Union[Unset, int] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        status = self.status.value

        clock_skew_ms = self.clock_skew_ms

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "status": status,
        })
        if clock_skew_ms is not UNSET:
            field_dict["clockSkewMs"] = clock_skew_ms

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        status = HealthStatus(d.pop("status"))




        clock_skew_ms = d.pop("clockSkewMs", UNSET)

        health = cls(
            status=status,
            clock_skew_ms=clock_skew_ms,
        )

        health.additional_properties = d
        return health

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
