import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union, cast

import attr
from dateutil.parser import isoparse

from ..models.user_scope_types_item import UserScopeTypesItem
from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.scope_filter import ScopeFilter
  from ..models.tag_sets import TagSets




T = TypeVar("T", bound="UserScope")

@attr.s(auto_attribs=True)
class UserScope:
    """
    Attributes:
        roles (Union[Unset, None, ScopeFilter]):
        users (Union[Unset, None, ScopeFilter]):
        teams (Union[Unset, None, ScopeFilter]):
        devices (Union[Unset, None, ScopeFilter]):
        fleets (Union[Unset, None, ScopeFilter]):
        events (Union[Unset, None, ScopeFilter]):
        views (Union[Unset, None, ScopeFilter]):
        key_value (Union[Unset, None, ScopeFilter]):
        tags (Union['TagSets', List['TagSets'], Unset]): One or more TagSets (combined with OR logic)
        device_ids (Union[Unset, List[str]]):
        names (Union[Unset, List[str]]):
        types (Union[Unset, List[UserScopeTypesItem]]):
        not_tags (Union[Unset, Any]):
        not_names (Union[Unset, List[str]]):
        agent_ids (Union[Unset, List[str]]):
        start (Union[Unset, datetime.datetime]):
        end (Union[Unset, datetime.datetime]):
    """

    roles: Union[Unset, None, 'ScopeFilter'] = UNSET
    users: Union[Unset, None, 'ScopeFilter'] = UNSET
    teams: Union[Unset, None, 'ScopeFilter'] = UNSET
    devices: Union[Unset, None, 'ScopeFilter'] = UNSET
    fleets: Union[Unset, None, 'ScopeFilter'] = UNSET
    events: Union[Unset, None, 'ScopeFilter'] = UNSET
    views: Union[Unset, None, 'ScopeFilter'] = UNSET
    key_value: Union[Unset, None, 'ScopeFilter'] = UNSET
    tags: Union['TagSets', List['TagSets'], Unset] = UNSET
    device_ids: Union[Unset, List[str]] = UNSET
    names: Union[Unset, List[str]] = UNSET
    types: Union[Unset, List[UserScopeTypesItem]] = UNSET
    not_tags: Union[Unset, Any] = UNSET
    not_names: Union[Unset, List[str]] = UNSET
    agent_ids: Union[Unset, List[str]] = UNSET
    start: Union[Unset, datetime.datetime] = UNSET
    end: Union[Unset, datetime.datetime] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        roles: Union[Unset, None, Dict[str, Any]] = UNSET
        if not isinstance(self.roles, Unset):
            roles = self.roles.to_dict() if self.roles else None

        users: Union[Unset, None, Dict[str, Any]] = UNSET
        if not isinstance(self.users, Unset):
            users = self.users.to_dict() if self.users else None

        teams: Union[Unset, None, Dict[str, Any]] = UNSET
        if not isinstance(self.teams, Unset):
            teams = self.teams.to_dict() if self.teams else None

        devices: Union[Unset, None, Dict[str, Any]] = UNSET
        if not isinstance(self.devices, Unset):
            devices = self.devices.to_dict() if self.devices else None

        fleets: Union[Unset, None, Dict[str, Any]] = UNSET
        if not isinstance(self.fleets, Unset):
            fleets = self.fleets.to_dict() if self.fleets else None

        events: Union[Unset, None, Dict[str, Any]] = UNSET
        if not isinstance(self.events, Unset):
            events = self.events.to_dict() if self.events else None

        views: Union[Unset, None, Dict[str, Any]] = UNSET
        if not isinstance(self.views, Unset):
            views = self.views.to_dict() if self.views else None

        key_value: Union[Unset, None, Dict[str, Any]] = UNSET
        if not isinstance(self.key_value, Unset):
            key_value = self.key_value.to_dict() if self.key_value else None

        tags: Union[Dict[str, Any], List[Dict[str, Any]], Unset]
        if isinstance(self.tags, Unset):
            tags = UNSET

        elif isinstance(self.tags, list):
            tags = UNSET
            if not isinstance(self.tags, Unset):
                tags = []
                for tags_type_0_item_data in self.tags:
                    tags_type_0_item = tags_type_0_item_data.to_dict()

                    tags.append(tags_type_0_item)




        else:
            tags = UNSET
            if not isinstance(self.tags, Unset):
                tags = self.tags.to_dict()



        device_ids: Union[Unset, List[str]] = UNSET
        if not isinstance(self.device_ids, Unset):
            device_ids = self.device_ids




        names: Union[Unset, List[str]] = UNSET
        if not isinstance(self.names, Unset):
            names = self.names




        types: Union[Unset, List[str]] = UNSET
        if not isinstance(self.types, Unset):
            types = []
            for types_item_data in self.types:
                types_item = types_item_data.value

                types.append(types_item)




        not_tags = self.not_tags
        not_names: Union[Unset, List[str]] = UNSET
        if not isinstance(self.not_names, Unset):
            not_names = self.not_names




        agent_ids: Union[Unset, List[str]] = UNSET
        if not isinstance(self.agent_ids, Unset):
            agent_ids = self.agent_ids




        start: Union[Unset, str] = UNSET
        if not isinstance(self.start, Unset):
            start = self.start.isoformat()

        end: Union[Unset, str] = UNSET
        if not isinstance(self.end, Unset):
            end = self.end.isoformat()


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
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
        if tags is not UNSET:
            field_dict["tags"] = tags
        if device_ids is not UNSET:
            field_dict["deviceIds"] = device_ids
        if names is not UNSET:
            field_dict["names"] = names
        if types is not UNSET:
            field_dict["types"] = types
        if not_tags is not UNSET:
            field_dict["notTags"] = not_tags
        if not_names is not UNSET:
            field_dict["notNames"] = not_names
        if agent_ids is not UNSET:
            field_dict["agentIds"] = agent_ids
        if start is not UNSET:
            field_dict["start"] = start
        if end is not UNSET:
            field_dict["end"] = end

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.scope_filter import ScopeFilter
        from ..models.tag_sets import TagSets
        d = src_dict.copy()
        _roles = d.pop("roles", UNSET)
        roles: Union[Unset, None, ScopeFilter]
        if _roles is None:
            roles = None
        elif isinstance(_roles,  Unset):
            roles = UNSET
        else:
            roles = ScopeFilter.from_dict(_roles)




        _users = d.pop("users", UNSET)
        users: Union[Unset, None, ScopeFilter]
        if _users is None:
            users = None
        elif isinstance(_users,  Unset):
            users = UNSET
        else:
            users = ScopeFilter.from_dict(_users)




        _teams = d.pop("teams", UNSET)
        teams: Union[Unset, None, ScopeFilter]
        if _teams is None:
            teams = None
        elif isinstance(_teams,  Unset):
            teams = UNSET
        else:
            teams = ScopeFilter.from_dict(_teams)




        _devices = d.pop("devices", UNSET)
        devices: Union[Unset, None, ScopeFilter]
        if _devices is None:
            devices = None
        elif isinstance(_devices,  Unset):
            devices = UNSET
        else:
            devices = ScopeFilter.from_dict(_devices)




        _fleets = d.pop("fleets", UNSET)
        fleets: Union[Unset, None, ScopeFilter]
        if _fleets is None:
            fleets = None
        elif isinstance(_fleets,  Unset):
            fleets = UNSET
        else:
            fleets = ScopeFilter.from_dict(_fleets)




        _events = d.pop("events", UNSET)
        events: Union[Unset, None, ScopeFilter]
        if _events is None:
            events = None
        elif isinstance(_events,  Unset):
            events = UNSET
        else:
            events = ScopeFilter.from_dict(_events)




        _views = d.pop("views", UNSET)
        views: Union[Unset, None, ScopeFilter]
        if _views is None:
            views = None
        elif isinstance(_views,  Unset):
            views = UNSET
        else:
            views = ScopeFilter.from_dict(_views)




        _key_value = d.pop("keyValue", UNSET)
        key_value: Union[Unset, None, ScopeFilter]
        if _key_value is None:
            key_value = None
        elif isinstance(_key_value,  Unset):
            key_value = UNSET
        else:
            key_value = ScopeFilter.from_dict(_key_value)




        def _parse_tags(data: object) -> Union['TagSets', List['TagSets'], Unset]:
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                tags_type_0 = UNSET
                _tags_type_0 = data
                for tags_type_0_item_data in (_tags_type_0 or []):
                    tags_type_0_item = TagSets.from_dict(tags_type_0_item_data)



                    tags_type_0.append(tags_type_0_item)

                return tags_type_0
            except: # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            _tags_type_1 = data
            tags_type_1: Union[Unset, TagSets]
            if isinstance(_tags_type_1,  Unset):
                tags_type_1 = UNSET
            else:
                tags_type_1 = TagSets.from_dict(_tags_type_1)



            return tags_type_1

        tags = _parse_tags(d.pop("tags", UNSET))


        device_ids = cast(List[str], d.pop("deviceIds", UNSET))


        names = cast(List[str], d.pop("names", UNSET))


        types = []
        _types = d.pop("types", UNSET)
        for types_item_data in (_types or []):
            types_item = UserScopeTypesItem(types_item_data)



            types.append(types_item)


        not_tags = d.pop("notTags", UNSET)

        not_names = cast(List[str], d.pop("notNames", UNSET))


        agent_ids = cast(List[str], d.pop("agentIds", UNSET))


        _start = d.pop("start", UNSET)
        start: Union[Unset, datetime.datetime]
        if isinstance(_start,  Unset):
            start = UNSET
        else:
            start = isoparse(_start)




        _end = d.pop("end", UNSET)
        end: Union[Unset, datetime.datetime]
        if isinstance(_end,  Unset):
            end = UNSET
        else:
            end = isoparse(_end)




        user_scope = cls(
            roles=roles,
            users=users,
            teams=teams,
            devices=devices,
            fleets=fleets,
            events=events,
            views=views,
            key_value=key_value,
            tags=tags,
            device_ids=device_ids,
            names=names,
            types=types,
            not_tags=not_tags,
            not_names=not_names,
            agent_ids=agent_ids,
            start=start,
            end=end,
        )

        user_scope.additional_properties = d
        return user_scope

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
