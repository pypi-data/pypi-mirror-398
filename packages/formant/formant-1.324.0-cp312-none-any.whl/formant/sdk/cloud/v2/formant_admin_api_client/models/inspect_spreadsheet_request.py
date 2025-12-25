from typing import Any, Dict, List, Type, TypeVar

import attr

T = TypeVar("T", bound="InspectSpreadsheetRequest")

@attr.s(auto_attribs=True)
class InspectSpreadsheetRequest:
    """
    Attributes:
        spreadsheet_url (str):
    """

    spreadsheet_url: str
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        spreadsheet_url = self.spreadsheet_url

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "spreadsheetUrl": spreadsheet_url,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        spreadsheet_url = d.pop("spreadsheetUrl")

        inspect_spreadsheet_request = cls(
            spreadsheet_url=spreadsheet_url,
        )

        inspect_spreadsheet_request.additional_properties = d
        return inspect_spreadsheet_request

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
