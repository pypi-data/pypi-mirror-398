import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.command_parameter_meta import CommandParameterMeta
  from ..models.file_info import FileInfo




T = TypeVar("T", bound="CommandParameter")

@attr.s(auto_attribs=True)
class CommandParameter:
    """
    Attributes:
        scrubber_time (datetime.datetime): Timestamp associated with this command.
        value (Union[Unset, str]): Enter your parameter and value. This string will be passed along with your command.
        meta (Union[Unset, CommandParameterMeta]): You can use this to add many parameters in a more structured way.
        files (Union[Unset, List['FileInfo']]): File(s) to be sent as a parameter with your command. Up to five files
            allowed.
    """

    scrubber_time: datetime.datetime
    value: Union[Unset, str] = UNSET
    meta: Union[Unset, 'CommandParameterMeta'] = UNSET
    files: Union[Unset, List['FileInfo']] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        scrubber_time = self.scrubber_time.isoformat()

        value = self.value
        meta: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.meta, Unset):
            meta = self.meta.to_dict()

        files: Union[Unset, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.files, Unset):
            files = []
            for files_item_data in self.files:
                files_item = files_item_data.to_dict()

                files.append(files_item)





        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "scrubberTime": scrubber_time,
        })
        if value is not UNSET:
            field_dict["value"] = value
        if meta is not UNSET:
            field_dict["meta"] = meta
        if files is not UNSET:
            field_dict["files"] = files

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.command_parameter_meta import CommandParameterMeta
        from ..models.file_info import FileInfo
        d = src_dict.copy()
        scrubber_time = isoparse(d.pop("scrubberTime"))




        value = d.pop("value", UNSET)

        _meta = d.pop("meta", UNSET)
        meta: Union[Unset, CommandParameterMeta]
        if isinstance(_meta,  Unset):
            meta = UNSET
        else:
            meta = CommandParameterMeta.from_dict(_meta)




        files = []
        _files = d.pop("files", UNSET)
        for files_item_data in (_files or []):
            files_item = FileInfo.from_dict(files_item_data)



            files.append(files_item)


        command_parameter = cls(
            scrubber_time=scrubber_time,
            value=value,
            meta=meta,
            files=files,
        )

        command_parameter.additional_properties = d
        return command_parameter

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
