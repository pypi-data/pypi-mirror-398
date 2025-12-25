from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.tag_sets import TagSets




T = TypeVar("T", bound="SimpleUserScope")

@attr.s(auto_attribs=True)
class SimpleUserScope:
    """
    Attributes:
        tags (TagSets): A map of tag keys to an array of values
        roles (Union[Unset, TagSets]): A map of tag keys to an array of values
        users (Union[Unset, TagSets]): A map of tag keys to an array of values
        teams (Union[Unset, TagSets]): A map of tag keys to an array of values
        devices (Union[Unset, TagSets]): A map of tag keys to an array of values
        fleets (Union[Unset, TagSets]): A map of tag keys to an array of values
        events (Union[Unset, TagSets]): A map of tag keys to an array of values
        views (Union[Unset, TagSets]): A map of tag keys to an array of values
        key_value (Union[Unset, TagSets]): A map of tag keys to an array of values
    """

    tags: 'TagSets'
    roles: Union[Unset, 'TagSets'] = UNSET
    users: Union[Unset, 'TagSets'] = UNSET
    teams: Union[Unset, 'TagSets'] = UNSET
    devices: Union[Unset, 'TagSets'] = UNSET
    fleets: Union[Unset, 'TagSets'] = UNSET
    events: Union[Unset, 'TagSets'] = UNSET
    views: Union[Unset, 'TagSets'] = UNSET
    key_value: Union[Unset, 'TagSets'] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        tags = self.tags.to_dict()

        roles: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.roles, Unset):
            roles = self.roles.to_dict()

        users: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.users, Unset):
            users = self.users.to_dict()

        teams: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.teams, Unset):
            teams = self.teams.to_dict()

        devices: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.devices, Unset):
            devices = self.devices.to_dict()

        fleets: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.fleets, Unset):
            fleets = self.fleets.to_dict()

        events: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.events, Unset):
            events = self.events.to_dict()

        views: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.views, Unset):
            views = self.views.to_dict()

        key_value: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.key_value, Unset):
            key_value = self.key_value.to_dict()


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "tags": tags,
        })
        if roles is not UNSET:
            field_dict["roles"] = roles
        if users is not UNSET:
            field_dict["users"] = users
        if teams is not UNSET:
            field_dict["teams"] = teams
        if devices is not UNSET:
            field_dict["devices"] = devices
        if fleets is not UNSET:
            field_dict["fleets"] = fleets
        if events is not UNSET:
            field_dict["events"] = events
        if views is not UNSET:
            field_dict["views"] = views
        if key_value is not UNSET:
            field_dict["keyValue"] = key_value

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.tag_sets import TagSets
        d = src_dict.copy()
        tags = TagSets.from_dict(d.pop("tags"))




        _roles = d.pop("roles", UNSET)
        roles: Union[Unset, TagSets]
        if isinstance(_roles,  Unset):
            roles = UNSET
        else:
            roles = TagSets.from_dict(_roles)




        _users = d.pop("users", UNSET)
        users: Union[Unset, TagSets]
        if isinstance(_users,  Unset):
            users = UNSET
        else:
            users = TagSets.from_dict(_users)




        _teams = d.pop("teams", UNSET)
        teams: Union[Unset, TagSets]
        if isinstance(_teams,  Unset):
            teams = UNSET
        else:
            teams = TagSets.from_dict(_teams)




        _devices = d.pop("devices", UNSET)
        devices: Union[Unset, TagSets]
        if isinstance(_devices,  Unset):
            devices = UNSET
        else:
            devices = TagSets.from_dict(_devices)




        _fleets = d.pop("fleets", UNSET)
        fleets: Union[Unset, TagSets]
        if isinstance(_fleets,  Unset):
            fleets = UNSET
        else:
            fleets = TagSets.from_dict(_fleets)




        _events = d.pop("events", UNSET)
        events: Union[Unset, TagSets]
        if isinstance(_events,  Unset):
            events = UNSET
        else:
            events = TagSets.from_dict(_events)




        _views = d.pop("views", UNSET)
        views: Union[Unset, TagSets]
        if isinstance(_views,  Unset):
            views = UNSET
        else:
            views = TagSets.from_dict(_views)




        _key_value = d.pop("keyValue", UNSET)
        key_value: Union[Unset, TagSets]
        if isinstance(_key_value,  Unset):
            key_value = UNSET
        else:
            key_value = TagSets.from_dict(_key_value)




        simple_user_scope = cls(
            tags=tags,
            roles=roles,
            users=users,
            teams=teams,
            devices=devices,
            fleets=fleets,
            events=events,
            views=views,
            key_value=key_value,
        )

        simple_user_scope.additional_properties = d
        return simple_user_scope

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
