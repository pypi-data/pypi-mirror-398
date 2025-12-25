from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

import attr

if TYPE_CHECKING:
  from ..models.google_spreadsheet_inspection import \
      GoogleSpreadsheetInspection




T = TypeVar("T", bound="InspectSpreadsheetResponse")

@attr.s(auto_attribs=True)
class InspectSpreadsheetResponse:
    """
    Attributes:
        inspection (GoogleSpreadsheetInspection):
    """

    inspection: 'GoogleSpreadsheetInspection'
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        inspection = self.inspection.to_dict()


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "inspection": inspection,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.google_spreadsheet_inspection import \
            GoogleSpreadsheetInspection
        d = src_dict.copy()
        inspection = GoogleSpreadsheetInspection.from_dict(d.pop("inspection"))




        inspect_spreadsheet_response = cls(
            inspection=inspection,
        )

        inspect_spreadsheet_response.additional_properties = d
        return inspect_spreadsheet_response

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
