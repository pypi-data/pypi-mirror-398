import datetime
from typing import Any, Dict, List, Type, TypeVar, Union, cast

import attr
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="ChatMessage")

@attr.s(auto_attribs=True)
class ChatMessage:
    """
    Attributes:
        message (str):
        organization_id (Union[Unset, str]):
        exploration_id (Union[Unset, str]):
        sender (Union[Unset, str]):
        enabled (Union[Unset, bool]):
        thoughts (Union[Unset, List[Any]]):
        id (Union[Unset, str]):
        created_at (Union[Unset, datetime.datetime]):
        updated_at (Union[Unset, datetime.datetime]):
    """

    message: str
    organization_id: Union[Unset, str] = UNSET
    exploration_id: Union[Unset, str] = UNSET
    sender: Union[Unset, str] = UNSET
    enabled: Union[Unset, bool] = UNSET
    thoughts: Union[Unset, List[Any]] = UNSET
    id: Union[Unset, str] = UNSET
    created_at: Union[Unset, datetime.datetime] = UNSET
    updated_at: Union[Unset, datetime.datetime] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        message = self.message
        organization_id = self.organization_id
        exploration_id = self.exploration_id
        sender = self.sender
        enabled = self.enabled
        thoughts: Union[Unset, List[Any]] = UNSET
        if not isinstance(self.thoughts, Unset):
            thoughts = self.thoughts




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
            "message": message,
        })
        if organization_id is not UNSET:
            field_dict["organizationId"] = organization_id
        if exploration_id is not UNSET:
            field_dict["explorationId"] = exploration_id
        if sender is not UNSET:
            field_dict["sender"] = sender
        if enabled is not UNSET:
            field_dict["enabled"] = enabled
        if thoughts is not UNSET:
            field_dict["thoughts"] = thoughts
        if id is not UNSET:
            field_dict["id"] = id
        if created_at is not UNSET:
            field_dict["createdAt"] = created_at
        if updated_at is not UNSET:
            field_dict["updatedAt"] = updated_at

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        message = d.pop("message")

        organization_id = d.pop("organizationId", UNSET)

        exploration_id = d.pop("explorationId", UNSET)

        sender = d.pop("sender", UNSET)

        enabled = d.pop("enabled", UNSET)

        thoughts = cast(List[Any], d.pop("thoughts", UNSET))


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




        chat_message = cls(
            message=message,
            organization_id=organization_id,
            exploration_id=exploration_id,
            sender=sender,
            enabled=enabled,
            thoughts=thoughts,
            id=id,
            created_at=created_at,
            updated_at=updated_at,
        )

        chat_message.additional_properties = d
        return chat_message

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
