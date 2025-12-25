from typing import Any, Dict, List, Type, TypeVar, cast

import attr

T = TypeVar("T", bound="QueryFilesRequest")

@attr.s(auto_attribs=True)
class QueryFilesRequest:
    """
    Attributes:
        file_ids (List[str]):
    """

    file_ids: List[str]
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        file_ids = self.file_ids





        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "fileIds": file_ids,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        file_ids = cast(List[str], d.pop("fileIds"))


        query_files_request = cls(
            file_ids=file_ids,
        )

        query_files_request.additional_properties = d
        return query_files_request

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
