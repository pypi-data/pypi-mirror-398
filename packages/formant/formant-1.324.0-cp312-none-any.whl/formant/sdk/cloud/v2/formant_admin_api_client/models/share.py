import datetime
from typing import (TYPE_CHECKING, Any, Dict, List, Optional, Type, TypeVar,
                    Union)

import attr
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.scope_filter import ScopeFilter




T = TypeVar("T", bound="Share")

@attr.s(auto_attribs=True)
class Share:
    """
    Attributes:
        time (datetime.datetime):
        organization_id (Union[Unset, str]):
        user_id (Union[Unset, str]):
        code (Union[Unset, str]):
        scope (Optional[ScopeFilter]):
        expiration (Union[Unset, datetime.datetime]):
        message (Union[Unset, str]):
        user_name (Union[Unset, str]):
        channel_id (Union[Unset, str]):
        dashboard_module_id (Union[Unset, None, str]):
        delegate_teleop (Union[Unset, bool]):
        id (Union[Unset, str]):
        created_at (Union[Unset, datetime.datetime]):
        updated_at (Union[Unset, datetime.datetime]):
    """

    time: datetime.datetime
    scope: Optional['ScopeFilter']
    organization_id: Union[Unset, str] = UNSET
    user_id: Union[Unset, str] = UNSET
    code: Union[Unset, str] = UNSET
    expiration: Union[Unset, datetime.datetime] = UNSET
    message: Union[Unset, str] = UNSET
    user_name: Union[Unset, str] = UNSET
    channel_id: Union[Unset, str] = UNSET
    dashboard_module_id: Union[Unset, None, str] = UNSET
    delegate_teleop: Union[Unset, bool] = UNSET
    id: Union[Unset, str] = UNSET
    created_at: Union[Unset, datetime.datetime] = UNSET
    updated_at: Union[Unset, datetime.datetime] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        time = self.time.isoformat()

        organization_id = self.organization_id
        user_id = self.user_id
        code = self.code
        scope = self.scope.to_dict() if self.scope else None

        expiration: Union[Unset, str] = UNSET
        if not isinstance(self.expiration, Unset):
            expiration = self.expiration.isoformat()

        message = self.message
        user_name = self.user_name
        channel_id = self.channel_id
        dashboard_module_id = self.dashboard_module_id
        delegate_teleop = self.delegate_teleop
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
            "time": time,
            "scope": scope,
        })
        if organization_id is not UNSET:
            field_dict["organizationId"] = organization_id
        if user_id is not UNSET:
            field_dict["userId"] = user_id
        if code is not UNSET:
            field_dict["code"] = code
        if expiration is not UNSET:
            field_dict["expiration"] = expiration
        if message is not UNSET:
            field_dict["message"] = message
        if user_name is not UNSET:
            field_dict["userName"] = user_name
        if channel_id is not UNSET:
            field_dict["channelId"] = channel_id
        if dashboard_module_id is not UNSET:
            field_dict["dashboardModuleId"] = dashboard_module_id
        if delegate_teleop is not UNSET:
            field_dict["delegateTeleop"] = delegate_teleop
        if id is not UNSET:
            field_dict["id"] = id
        if created_at is not UNSET:
            field_dict["createdAt"] = created_at
        if updated_at is not UNSET:
            field_dict["updatedAt"] = updated_at

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.scope_filter import ScopeFilter
        d = src_dict.copy()
        time = isoparse(d.pop("time"))




        organization_id = d.pop("organizationId", UNSET)

        user_id = d.pop("userId", UNSET)

        code = d.pop("code", UNSET)

        _scope = d.pop("scope")
        scope: Optional[ScopeFilter]
        if _scope is None:
            scope = None
        else:
            scope = ScopeFilter.from_dict(_scope)




        _expiration = d.pop("expiration", UNSET)
        expiration: Union[Unset, datetime.datetime]
        if isinstance(_expiration,  Unset):
            expiration = UNSET
        else:
            expiration = isoparse(_expiration)




        message = d.pop("message", UNSET)

        user_name = d.pop("userName", UNSET)

        channel_id = d.pop("channelId", UNSET)

        dashboard_module_id = d.pop("dashboardModuleId", UNSET)

        delegate_teleop = d.pop("delegateTeleop", UNSET)

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




        share = cls(
            time=time,
            organization_id=organization_id,
            user_id=user_id,
            code=code,
            scope=scope,
            expiration=expiration,
            message=message,
            user_name=user_name,
            channel_id=channel_id,
            dashboard_module_id=dashboard_module_id,
            delegate_teleop=delegate_teleop,
            id=id,
            created_at=created_at,
            updated_at=updated_at,
        )

        share.additional_properties = d
        return share

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
