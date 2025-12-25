from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr

from ..models.aws_info_output_format import AwsInfoOutputFormat
from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.s3_export import S3Export




T = TypeVar("T", bound="AwsInfo")

@attr.s(auto_attribs=True)
class AwsInfo:
    """
    Attributes:
        account_id (str):
        role_name (Any):
        s_3_export (Union[Unset, S3Export]):
        output_format (Union[Unset, AwsInfoOutputFormat]):
    """

    account_id: str
    role_name: Any
    s_3_export: Union[Unset, 'S3Export'] = UNSET
    output_format: Union[Unset, AwsInfoOutputFormat] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        account_id = self.account_id
        role_name = self.role_name
        s_3_export: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.s_3_export, Unset):
            s_3_export = self.s_3_export.to_dict()

        output_format: Union[Unset, str] = UNSET
        if not isinstance(self.output_format, Unset):
            output_format = self.output_format.value


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "accountId": account_id,
            "roleName": role_name,
        })
        if s_3_export is not UNSET:
            field_dict["s3Export"] = s_3_export
        if output_format is not UNSET:
            field_dict["outputFormat"] = output_format

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.s3_export import S3Export
        d = src_dict.copy()
        account_id = d.pop("accountId")

        role_name = d.pop("roleName")

        _s_3_export = d.pop("s3Export", UNSET)
        s_3_export: Union[Unset, S3Export]
        if isinstance(_s_3_export,  Unset):
            s_3_export = UNSET
        else:
            s_3_export = S3Export.from_dict(_s_3_export)




        _output_format = d.pop("outputFormat", UNSET)
        output_format: Union[Unset, AwsInfoOutputFormat]
        if isinstance(_output_format,  Unset):
            output_format = UNSET
        else:
            output_format = AwsInfoOutputFormat(_output_format)




        aws_info = cls(
            account_id=account_id,
            role_name=role_name,
            s_3_export=s_3_export,
            output_format=output_format,
        )

        aws_info.additional_properties = d
        return aws_info

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
