from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="SheetParameters")

@attr.s(auto_attribs=True)
class SheetParameters:
    """
    Attributes:
        spreadsheet_id (str):
        range_ (str):
        url (Union[Unset, str]):
    """

    spreadsheet_id: str
    range_: str
    url: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        spreadsheet_id = self.spreadsheet_id
        range_ = self.range_
        url = self.url

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "spreadsheetId": spreadsheet_id,
            "range": range_,
        })
        if url is not UNSET:
            field_dict["url"] = url

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        spreadsheet_id = d.pop("spreadsheetId")

        range_ = d.pop("range")

        url = d.pop("url", UNSET)

        sheet_parameters = cls(
            spreadsheet_id=spreadsheet_id,
            range_=range_,
            url=url,
        )

        sheet_parameters.additional_properties = d
        return sheet_parameters

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
