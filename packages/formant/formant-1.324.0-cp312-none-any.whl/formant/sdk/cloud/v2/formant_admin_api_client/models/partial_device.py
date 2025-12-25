import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union, cast

import attr
from dateutil.parser import isoparse

from ..models.partial_device_type import PartialDeviceType
from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.device_follower import DeviceFollower
  from ..models.device_scope import DeviceScope
  from ..models.device_state import DeviceState
  from ..models.notification_muted import NotificationMuted
  from ..models.partial_device_tags import PartialDeviceTags
  from ..models.scope_filter import ScopeFilter




T = TypeVar("T", bound="PartialDevice")

@attr.s(auto_attribs=True)
class PartialDevice:
    """
    Attributes:
        organization_id (Union[Unset, str]): ID of the organization which contains this device.
        external_id (Union[Unset, None, str]): External ID of this device.
        name (Union[Unset, str]): Name of this device.
        description (Union[Unset, None, str]): Description of this device.
        type (Union[Unset, PartialDeviceType]): Enter `default`.
        user_id (Union[Unset, None, str]): ID of the user associated with this device.
        fleet_id (Union[Unset, None, str]): ID of the fleet with which this device is associated.
        public_key (Union[Unset, str]):
        scope (Union[Unset, None, ScopeFilter]):
        device_scope (Union[Unset, DeviceScope]):
        desired_agent_version (Union[Unset, None, str]): Agent version you want to install if different from the latest
            version. Must have `formant-sidecar` installed.
        desired_configuration_version (Union[Unset, None, int]): Device configuration version you want to apply. Ignore
            for new device configuration.
        temporary_configuration_version (Union[Unset, None, int]):
        temporary_configuration_expiration (Union[Unset, None, datetime.datetime]):
        temporary_configuration_template_id (Union[Unset, None, str]):
        muted (Union[Unset, None, NotificationMuted]):
        followers (Union[Unset, List['DeviceFollower']]): Users who receive SMS updates from this device.
        slack_channels (Union[Unset, List[str]]): Slack channels which receive updates from this device.
        state (Union[Unset, DeviceState]):
        enabled (Union[Unset, bool]):
        fully_configured (Union[Unset, bool]):
        disabled_at (Union[Unset, None, datetime.datetime]):
        id (Union[Unset, str]):
        created_at (Union[Unset, datetime.datetime]):
        updated_at (Union[Unset, datetime.datetime]):
        tags (Union[Unset, PartialDeviceTags]):
    """

    organization_id: Union[Unset, str] = UNSET
    external_id: Union[Unset, None, str] = UNSET
    name: Union[Unset, str] = UNSET
    description: Union[Unset, None, str] = UNSET
    type: Union[Unset, PartialDeviceType] = UNSET
    user_id: Union[Unset, None, str] = UNSET
    fleet_id: Union[Unset, None, str] = UNSET
    public_key: Union[Unset, str] = UNSET
    scope: Union[Unset, None, 'ScopeFilter'] = UNSET
    device_scope: Union[Unset, 'DeviceScope'] = UNSET
    desired_agent_version: Union[Unset, None, str] = UNSET
    desired_configuration_version: Union[Unset, None, int] = UNSET
    temporary_configuration_version: Union[Unset, None, int] = UNSET
    temporary_configuration_expiration: Union[Unset, None, datetime.datetime] = UNSET
    temporary_configuration_template_id: Union[Unset, None, str] = UNSET
    muted: Union[Unset, None, 'NotificationMuted'] = UNSET
    followers: Union[Unset, List['DeviceFollower']] = UNSET
    slack_channels: Union[Unset, List[str]] = UNSET
    state: Union[Unset, 'DeviceState'] = UNSET
    enabled: Union[Unset, bool] = UNSET
    fully_configured: Union[Unset, bool] = UNSET
    disabled_at: Union[Unset, None, datetime.datetime] = UNSET
    id: Union[Unset, str] = UNSET
    created_at: Union[Unset, datetime.datetime] = UNSET
    updated_at: Union[Unset, datetime.datetime] = UNSET
    tags: Union[Unset, 'PartialDeviceTags'] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        organization_id = self.organization_id
        external_id = self.external_id
        name = self.name
        description = self.description
        type: Union[Unset, str] = UNSET
        if not isinstance(self.type, Unset):
            type = self.type.value

        user_id = self.user_id
        fleet_id = self.fleet_id
        public_key = self.public_key
        scope: Union[Unset, None, Dict[str, Any]] = UNSET
        if not isinstance(self.scope, Unset):
            scope = self.scope.to_dict() if self.scope else None

        device_scope: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.device_scope, Unset):
            device_scope = self.device_scope.to_dict()

        desired_agent_version = self.desired_agent_version
        desired_configuration_version = self.desired_configuration_version
        temporary_configuration_version = self.temporary_configuration_version
        temporary_configuration_expiration: Union[Unset, None, str] = UNSET
        if not isinstance(self.temporary_configuration_expiration, Unset):
            temporary_configuration_expiration = self.temporary_configuration_expiration.isoformat() if self.temporary_configuration_expiration else None

        temporary_configuration_template_id = self.temporary_configuration_template_id
        muted: Union[Unset, None, Dict[str, Any]] = UNSET
        if not isinstance(self.muted, Unset):
            muted = self.muted.to_dict() if self.muted else None

        followers: Union[Unset, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.followers, Unset):
            followers = []
            for followers_item_data in self.followers:
                followers_item = followers_item_data.to_dict()

                followers.append(followers_item)




        slack_channels: Union[Unset, List[str]] = UNSET
        if not isinstance(self.slack_channels, Unset):
            slack_channels = self.slack_channels




        state: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.state, Unset):
            state = self.state.to_dict()

        enabled = self.enabled
        fully_configured = self.fully_configured
        disabled_at: Union[Unset, None, str] = UNSET
        if not isinstance(self.disabled_at, Unset):
            disabled_at = self.disabled_at.isoformat() if self.disabled_at else None

        id = self.id
        created_at: Union[Unset, str] = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: Union[Unset, str] = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        tags: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.tags, Unset):
            tags = self.tags.to_dict()


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if organization_id is not UNSET:
            field_dict["organizationId"] = organization_id
        if external_id is not UNSET:
            field_dict["externalId"] = external_id
        if name is not UNSET:
            field_dict["name"] = name
        if description is not UNSET:
            field_dict["description"] = description
        if type is not UNSET:
            field_dict["type"] = type
        if user_id is not UNSET:
            field_dict["userId"] = user_id
        if fleet_id is not UNSET:
            field_dict["fleetId"] = fleet_id
        if public_key is not UNSET:
            field_dict["publicKey"] = public_key
        if scope is not UNSET:
            field_dict["scope"] = scope
        if device_scope is not UNSET:
            field_dict["deviceScope"] = device_scope
        if desired_agent_version is not UNSET:
            field_dict["desiredAgentVersion"] = desired_agent_version
        if desired_configuration_version is not UNSET:
            field_dict["desiredConfigurationVersion"] = desired_configuration_version
        if temporary_configuration_version is not UNSET:
            field_dict["temporaryConfigurationVersion"] = temporary_configuration_version
        if temporary_configuration_expiration is not UNSET:
            field_dict["temporaryConfigurationExpiration"] = temporary_configuration_expiration
        if temporary_configuration_template_id is not UNSET:
            field_dict["temporaryConfigurationTemplateId"] = temporary_configuration_template_id
        if muted is not UNSET:
            field_dict["muted"] = muted
        if followers is not UNSET:
            field_dict["followers"] = followers
        if slack_channels is not UNSET:
            field_dict["slackChannels"] = slack_channels
        if state is not UNSET:
            field_dict["state"] = state
        if enabled is not UNSET:
            field_dict["enabled"] = enabled
        if fully_configured is not UNSET:
            field_dict["fullyConfigured"] = fully_configured
        if disabled_at is not UNSET:
            field_dict["disabledAt"] = disabled_at
        if id is not UNSET:
            field_dict["id"] = id
        if created_at is not UNSET:
            field_dict["createdAt"] = created_at
        if updated_at is not UNSET:
            field_dict["updatedAt"] = updated_at
        if tags is not UNSET:
            field_dict["tags"] = tags

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.device_follower import DeviceFollower
        from ..models.device_scope import DeviceScope
        from ..models.device_state import DeviceState
        from ..models.notification_muted import NotificationMuted
        from ..models.partial_device_tags import PartialDeviceTags
        from ..models.scope_filter import ScopeFilter
        d = src_dict.copy()
        organization_id = d.pop("organizationId", UNSET)

        external_id = d.pop("externalId", UNSET)

        name = d.pop("name", UNSET)

        description = d.pop("description", UNSET)

        _type = d.pop("type", UNSET)
        type: Union[Unset, PartialDeviceType]
        if isinstance(_type,  Unset):
            type = UNSET
        else:
            type = PartialDeviceType(_type)




        user_id = d.pop("userId", UNSET)

        fleet_id = d.pop("fleetId", UNSET)

        public_key = d.pop("publicKey", UNSET)

        _scope = d.pop("scope", UNSET)
        scope: Union[Unset, None, ScopeFilter]
        if _scope is None:
            scope = None
        elif isinstance(_scope,  Unset):
            scope = UNSET
        else:
            scope = ScopeFilter.from_dict(_scope)




        _device_scope = d.pop("deviceScope", UNSET)
        device_scope: Union[Unset, DeviceScope]
        if isinstance(_device_scope,  Unset):
            device_scope = UNSET
        else:
            device_scope = DeviceScope.from_dict(_device_scope)




        desired_agent_version = d.pop("desiredAgentVersion", UNSET)

        desired_configuration_version = d.pop("desiredConfigurationVersion", UNSET)

        temporary_configuration_version = d.pop("temporaryConfigurationVersion", UNSET)

        _temporary_configuration_expiration = d.pop("temporaryConfigurationExpiration", UNSET)
        temporary_configuration_expiration: Union[Unset, None, datetime.datetime]
        if _temporary_configuration_expiration is None:
            temporary_configuration_expiration = None
        elif isinstance(_temporary_configuration_expiration,  Unset):
            temporary_configuration_expiration = UNSET
        else:
            temporary_configuration_expiration = isoparse(_temporary_configuration_expiration)




        temporary_configuration_template_id = d.pop("temporaryConfigurationTemplateId", UNSET)

        _muted = d.pop("muted", UNSET)
        muted: Union[Unset, None, NotificationMuted]
        if _muted is None:
            muted = None
        elif isinstance(_muted,  Unset):
            muted = UNSET
        else:
            muted = NotificationMuted.from_dict(_muted)




        followers = []
        _followers = d.pop("followers", UNSET)
        for followers_item_data in (_followers or []):
            followers_item = DeviceFollower.from_dict(followers_item_data)



            followers.append(followers_item)


        slack_channels = cast(List[str], d.pop("slackChannels", UNSET))


        _state = d.pop("state", UNSET)
        state: Union[Unset, DeviceState]
        if isinstance(_state,  Unset):
            state = UNSET
        else:
            state = DeviceState.from_dict(_state)




        enabled = d.pop("enabled", UNSET)

        fully_configured = d.pop("fullyConfigured", UNSET)

        _disabled_at = d.pop("disabledAt", UNSET)
        disabled_at: Union[Unset, None, datetime.datetime]
        if _disabled_at is None:
            disabled_at = None
        elif isinstance(_disabled_at,  Unset):
            disabled_at = UNSET
        else:
            disabled_at = isoparse(_disabled_at)




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




        _tags = d.pop("tags", UNSET)
        tags: Union[Unset, PartialDeviceTags]
        if isinstance(_tags,  Unset):
            tags = UNSET
        else:
            tags = PartialDeviceTags.from_dict(_tags)




        partial_device = cls(
            organization_id=organization_id,
            external_id=external_id,
            name=name,
            description=description,
            type=type,
            user_id=user_id,
            fleet_id=fleet_id,
            public_key=public_key,
            scope=scope,
            device_scope=device_scope,
            desired_agent_version=desired_agent_version,
            desired_configuration_version=desired_configuration_version,
            temporary_configuration_version=temporary_configuration_version,
            temporary_configuration_expiration=temporary_configuration_expiration,
            temporary_configuration_template_id=temporary_configuration_template_id,
            muted=muted,
            followers=followers,
            slack_channels=slack_channels,
            state=state,
            enabled=enabled,
            fully_configured=fully_configured,
            disabled_at=disabled_at,
            id=id,
            created_at=created_at,
            updated_at=updated_at,
            tags=tags,
        )

        partial_device.additional_properties = d
        return partial_device

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
