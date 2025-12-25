import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.task_summary_format_format import TaskSummaryFormatFormat




T = TypeVar("T", bound="TaskSummaryFormat")

@attr.s(auto_attribs=True)
class TaskSummaryFormat:
    """
    Attributes:
        label (str): User-friendly name for this task summary format.
        format_ (TaskSummaryFormatFormat): Enter the data structure for this task summary format in key-value pairs.
        organization_id (Union[Unset, str]): ID of the organization in which to create this new task summary format.
        deleted_at (Union[Unset, None, datetime.datetime]): Internal use only, ignore.
        id (Union[Unset, str]):
        created_at (Union[Unset, datetime.datetime]):
        updated_at (Union[Unset, datetime.datetime]):
    """

    label: str
    format_: 'TaskSummaryFormatFormat'
    organization_id: Union[Unset, str] = UNSET
    deleted_at: Union[Unset, None, datetime.datetime] = UNSET
    id: Union[Unset, str] = UNSET
    created_at: Union[Unset, datetime.datetime] = UNSET
    updated_at: Union[Unset, datetime.datetime] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        label = self.label
        format_ = self.format_.to_dict()

        organization_id = self.organization_id
        deleted_at: Union[Unset, None, str] = UNSET
        if not isinstance(self.deleted_at, Unset):
            deleted_at = self.deleted_at.isoformat() if self.deleted_at else None

        id = self.id
        created_at: Union[Unset, str] = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: Union[Unset, str] = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "label": label,
            "format": format_,
        })
        if organization_id is not UNSET:
            field_dict["organizationId"] = organization_id
        if deleted_at is not UNSET:
            field_dict["deletedAt"] = deleted_at
        if id is not UNSET:
            field_dict["id"] = id
        if created_at is not UNSET:
            field_dict["createdAt"] = created_at
        if updated_at is not UNSET:
            field_dict["updatedAt"] = updated_at

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.task_summary_format_format import TaskSummaryFormatFormat
        d = src_dict.copy()
        label = d.pop("label")

        format_ = TaskSummaryFormatFormat.from_dict(d.pop("format"))




        organization_id = d.pop("organizationId", UNSET)

        _deleted_at = d.pop("deletedAt", UNSET)
        deleted_at: Union[Unset, None, datetime.datetime]
        if _deleted_at is None:
            deleted_at = None
        elif isinstance(_deleted_at,  Unset):
            deleted_at = UNSET
        else:
            deleted_at = isoparse(_deleted_at)




        id = d.pop("id", UNSET)

        _created_at = d.pop("createdAt", UNSET)
        created_at: Union[Unset, datetime.datetime]
        if isinstance(_created_at,  Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)




        _updated_at = d.pop("updatedAt", UNSET)
        updated_at: Union[Unset, datetime.datetime]
        if isinstance(_updated_at,  Unset):
            updated_at = UNSET
        else:
            updated_at = isoparse(_updated_at)




        task_summary_format = cls(
            label=label,
            format_=format_,
            organization_id=organization_id,
            deleted_at=deleted_at,
            id=id,
            created_at=created_at,
            updated_at=updated_at,
        )

        task_summary_format.additional_properties = d
        return task_summary_format

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
