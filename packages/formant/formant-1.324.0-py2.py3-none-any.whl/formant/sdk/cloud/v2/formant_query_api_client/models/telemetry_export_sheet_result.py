from typing import Any, Dict, List, Type, TypeVar

import attr

T = TypeVar("T", bound="TelemetryExportSheetResult")

@attr.s(auto_attribs=True)
class TelemetryExportSheetResult:
    """
    Attributes:
        spreadsheet_url (str):
        telemetry_not_found (bool):
    """

    spreadsheet_url: str
    telemetry_not_found: bool
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        spreadsheet_url = self.spreadsheet_url
        telemetry_not_found = self.telemetry_not_found

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "spreadsheetUrl": spreadsheet_url,
            "telemetryNotFound": telemetry_not_found,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        spreadsheet_url = d.pop("spreadsheetUrl")

        telemetry_not_found = d.pop("telemetryNotFound")

        telemetry_export_sheet_result = cls(
            spreadsheet_url=spreadsheet_url,
            telemetry_not_found=telemetry_not_found,
        )

        telemetry_export_sheet_result.additional_properties = d
        return telemetry_export_sheet_result

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
