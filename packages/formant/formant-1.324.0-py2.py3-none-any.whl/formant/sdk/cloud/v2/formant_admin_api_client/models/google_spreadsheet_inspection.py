from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.google_sheet_parse_result import GoogleSheetParseResult




T = TypeVar("T", bound="GoogleSpreadsheetInspection")

@attr.s(auto_attribs=True)
class GoogleSpreadsheetInspection:
    """
    Attributes:
        parse_url_failed (Union[Unset, bool]):
        spreadsheet_get_failed (Union[Unset, bool]):
        sheet_find_failed (Union[Unset, bool]):
        sheet_title (Union[Unset, str]):
        parse_result (Union[Unset, GoogleSheetParseResult]):
    """

    parse_url_failed: Union[Unset, bool] = UNSET
    spreadsheet_get_failed: Union[Unset, bool] = UNSET
    sheet_find_failed: Union[Unset, bool] = UNSET
    sheet_title: Union[Unset, str] = UNSET
    parse_result: Union[Unset, 'GoogleSheetParseResult'] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        parse_url_failed = self.parse_url_failed
        spreadsheet_get_failed = self.spreadsheet_get_failed
        sheet_find_failed = self.sheet_find_failed
        sheet_title = self.sheet_title
        parse_result: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.parse_result, Unset):
            parse_result = self.parse_result.to_dict()


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if parse_url_failed is not UNSET:
            field_dict["parseUrlFailed"] = parse_url_failed
        if spreadsheet_get_failed is not UNSET:
            field_dict["spreadsheetGetFailed"] = spreadsheet_get_failed
        if sheet_find_failed is not UNSET:
            field_dict["sheetFindFailed"] = sheet_find_failed
        if sheet_title is not UNSET:
            field_dict["sheetTitle"] = sheet_title
        if parse_result is not UNSET:
            field_dict["parseResult"] = parse_result

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.google_sheet_parse_result import GoogleSheetParseResult
        d = src_dict.copy()
        parse_url_failed = d.pop("parseUrlFailed", UNSET)

        spreadsheet_get_failed = d.pop("spreadsheetGetFailed", UNSET)

        sheet_find_failed = d.pop("sheetFindFailed", UNSET)

        sheet_title = d.pop("sheetTitle", UNSET)

        _parse_result = d.pop("parseResult", UNSET)
        parse_result: Union[Unset, GoogleSheetParseResult]
        if isinstance(_parse_result,  Unset):
            parse_result = UNSET
        else:
            parse_result = GoogleSheetParseResult.from_dict(_parse_result)




        google_spreadsheet_inspection = cls(
            parse_url_failed=parse_url_failed,
            spreadsheet_get_failed=spreadsheet_get_failed,
            sheet_find_failed=sheet_find_failed,
            sheet_title=sheet_title,
            parse_result=parse_result,
        )

        google_spreadsheet_inspection.additional_properties = d
        return google_spreadsheet_inspection

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
