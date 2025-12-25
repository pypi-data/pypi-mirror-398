from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="S3Export")

@attr.s(auto_attribs=True)
class S3Export:
    """
    Attributes:
        bucket (str):
        path (Union[Unset, str]):
    """

    bucket: str
    path: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        bucket = self.bucket
        path = self.path

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "bucket": bucket,
        })
        if path is not UNSET:
            field_dict["path"] = path

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        bucket = d.pop("bucket")

        path = d.pop("path", UNSET)

        s3_export = cls(
            bucket=bucket,
            path=path,
        )

        s3_export.additional_properties = d
        return s3_export

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
