from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union, cast

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.annotation_field_value import AnnotationFieldValue




T = TypeVar("T", bound="GoogleSheetParseResult")

@attr.s(auto_attribs=True)
class GoogleSheetParseResult:
    """
    Attributes:
        header_invalid (Union[Unset, bool]):
        header_preview (Union[Unset, List[str]]):
        content_invalid (Union[Unset, bool]):
        values (Union[Unset, List['AnnotationFieldValue']]):
    """

    header_invalid: Union[Unset, bool] = UNSET
    header_preview: Union[Unset, List[str]] = UNSET
    content_invalid: Union[Unset, bool] = UNSET
    values: Union[Unset, List['AnnotationFieldValue']] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        header_invalid = self.header_invalid
        header_preview: Union[Unset, List[str]] = UNSET
        if not isinstance(self.header_preview, Unset):
            header_preview = self.header_preview




        content_invalid = self.content_invalid
        values: Union[Unset, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.values, Unset):
            values = []
            for values_item_data in self.values:
                values_item = values_item_data.to_dict()

                values.append(values_item)





        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if header_invalid is not UNSET:
            field_dict["headerInvalid"] = header_invalid
        if header_preview is not UNSET:
            field_dict["headerPreview"] = header_preview
        if content_invalid is not UNSET:
            field_dict["contentInvalid"] = content_invalid
        if values is not UNSET:
            field_dict["values"] = values

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.annotation_field_value import AnnotationFieldValue
        d = src_dict.copy()
        header_invalid = d.pop("headerInvalid", UNSET)

        header_preview = cast(List[str], d.pop("headerPreview", UNSET))


        content_invalid = d.pop("contentInvalid", UNSET)

        values = []
        _values = d.pop("values", UNSET)
        for values_item_data in (_values or []):
            values_item = AnnotationFieldValue.from_dict(values_item_data)



            values.append(values_item)


        google_sheet_parse_result = cls(
            header_invalid=header_invalid,
            header_preview=header_preview,
            content_invalid=content_invalid,
            values=values,
        )

        google_sheet_parse_result.additional_properties = d
        return google_sheet_parse_result

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
