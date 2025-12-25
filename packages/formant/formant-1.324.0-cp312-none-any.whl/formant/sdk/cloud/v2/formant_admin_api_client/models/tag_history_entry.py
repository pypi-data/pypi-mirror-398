import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

import attr
from dateutil.parser import isoparse

if TYPE_CHECKING:
  from ..models.tag_history_entry_tags import TagHistoryEntryTags




T = TypeVar("T", bound="TagHistoryEntry")

@attr.s(auto_attribs=True)
class TagHistoryEntry:
    """
    Attributes:
        created_at (datetime.datetime):
        tags (TagHistoryEntryTags):
    """

    created_at: datetime.datetime
    tags: 'TagHistoryEntryTags'
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        created_at = self.created_at.isoformat()

        tags = self.tags.to_dict()


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "createdAt": created_at,
            "tags": tags,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.tag_history_entry_tags import TagHistoryEntryTags
        d = src_dict.copy()
        created_at = isoparse(d.pop("createdAt"))




        tags = TagHistoryEntryTags.from_dict(d.pop("tags"))




        tag_history_entry = cls(
            created_at=created_at,
            tags=tags,
        )

        tag_history_entry.additional_properties = d
        return tag_history_entry

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
