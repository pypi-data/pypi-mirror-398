from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

import attr

if TYPE_CHECKING:
  from ..models.query import Query




T = TypeVar("T", bound="TelemetryExportSheetRequest")

@attr.s(auto_attribs=True)
class TelemetryExportSheetRequest:
    """
    Attributes:
        query (Query):
    """

    query: 'Query'
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        query = self.query.to_dict()


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "query": query,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.query import Query
        d = src_dict.copy()
        query = Query.from_dict(d.pop("query"))




        telemetry_export_sheet_request = cls(
            query=query,
        )

        telemetry_export_sheet_request.additional_properties = d
        return telemetry_export_sheet_request

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
