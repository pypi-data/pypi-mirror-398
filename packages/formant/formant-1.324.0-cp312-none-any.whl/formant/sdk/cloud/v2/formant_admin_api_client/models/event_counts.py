from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="EventCounts")

@attr.s(auto_attribs=True)
class EventCounts:
    """
    Attributes:
        total (int):
        info (Union[Unset, int]):
        warn (Union[Unset, int]):
        error (Union[Unset, int]):
        critical (Union[Unset, int]):
        triggered_events (Union[Unset, int]):
        intervention_request (Union[Unset, int]):
    """

    total: int
    info: Union[Unset, int] = UNSET
    warn: Union[Unset, int] = UNSET
    error: Union[Unset, int] = UNSET
    critical: Union[Unset, int] = UNSET
    triggered_events: Union[Unset, int] = UNSET
    intervention_request: Union[Unset, int] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        total = self.total
        info = self.info
        warn = self.warn
        error = self.error
        critical = self.critical
        triggered_events = self.triggered_events
        intervention_request = self.intervention_request

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "total": total,
        })
        if info is not UNSET:
            field_dict["info"] = info
        if warn is not UNSET:
            field_dict["warn"] = warn
        if error is not UNSET:
            field_dict["error"] = error
        if critical is not UNSET:
            field_dict["critical"] = critical
        if triggered_events is not UNSET:
            field_dict["triggered-events"] = triggered_events
        if intervention_request is not UNSET:
            field_dict["intervention-request"] = intervention_request

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        total = d.pop("total")

        info = d.pop("info", UNSET)

        warn = d.pop("warn", UNSET)

        error = d.pop("error", UNSET)

        critical = d.pop("critical", UNSET)

        triggered_events = d.pop("triggered-events", UNSET)

        intervention_request = d.pop("intervention-request", UNSET)

        event_counts = cls(
            total=total,
            info=info,
            warn=warn,
            error=error,
            critical=critical,
            triggered_events=triggered_events,
            intervention_request=intervention_request,
        )

        event_counts.additional_properties = d
        return event_counts

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
