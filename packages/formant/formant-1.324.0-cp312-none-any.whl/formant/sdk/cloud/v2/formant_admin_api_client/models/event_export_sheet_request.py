from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

import attr

if TYPE_CHECKING:
  from ..models.event_filter import EventFilter




T = TypeVar("T", bound="EventExportSheetRequest")

@attr.s(auto_attribs=True)
class EventExportSheetRequest:
    """
    Attributes:
        filter_ (EventFilter):
        app_url_origin (str):
    """

    filter_: 'EventFilter'
    app_url_origin: str
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        filter_ = self.filter_.to_dict()

        app_url_origin = self.app_url_origin

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "filter": filter_,
            "appUrlOrigin": app_url_origin,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.event_filter import EventFilter
        d = src_dict.copy()
        filter_ = EventFilter.from_dict(d.pop("filter"))




        app_url_origin = d.pop("appUrlOrigin")

        event_export_sheet_request = cls(
            filter_=filter_,
            app_url_origin=app_url_origin,
        )

        event_export_sheet_request.additional_properties = d
        return event_export_sheet_request

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
