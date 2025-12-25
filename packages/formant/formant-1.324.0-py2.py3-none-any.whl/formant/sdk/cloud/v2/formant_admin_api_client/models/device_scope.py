import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union, cast

import attr
from dateutil.parser import isoparse

from ..models.device_scope_types_item import DeviceScopeTypesItem
from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.scope_filter import ScopeFilter
  from ..models.tag_sets import TagSets




T = TypeVar("T", bound="DeviceScope")

@attr.s(auto_attribs=True)
class DeviceScope:
    """
    Attributes:
        views (Union[Unset, None, ScopeFilter]):
        commands (Union[Unset, None, ScopeFilter]):
        tags (Union['TagSets', List['TagSets'], Unset]): One or more TagSets (combined with OR logic)
        device_ids (Union[Unset, List[str]]):
        names (Union[Unset, List[str]]):
        types (Union[Unset, List[DeviceScopeTypesItem]]):
        not_tags (Union[Unset, Any]):
        not_names (Union[Unset, List[str]]):
        agent_ids (Union[Unset, List[str]]):
        start (Union[Unset, datetime.datetime]):
        end (Union[Unset, datetime.datetime]):
    """

    views: Union[Unset, None, 'ScopeFilter'] = UNSET
    commands: Union[Unset, None, 'ScopeFilter'] = UNSET
    tags: Union['TagSets', List['TagSets'], Unset] = UNSET
    device_ids: Union[Unset, List[str]] = UNSET
    names: Union[Unset, List[str]] = UNSET
    types: Union[Unset, List[DeviceScopeTypesItem]] = UNSET
    not_tags: Union[Unset, Any] = UNSET
    not_names: Union[Unset, List[str]] = UNSET
    agent_ids: Union[Unset, List[str]] = UNSET
    start: Union[Unset, datetime.datetime] = UNSET
    end: Union[Unset, datetime.datetime] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        views: Union[Unset, None, Dict[str, Any]] = UNSET
        if not isinstance(self.views, Unset):
            views = self.views.to_dict() if self.views else None

        commands: Union[Unset, None, Dict[str, Any]] = UNSET
        if not isinstance(self.commands, Unset):
            commands = self.commands.to_dict() if self.commands else None

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
        if views is not UNSET:
            field_dict["views"] = views
        if commands is not UNSET:
            field_dict["commands"] = commands
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
        _views = d.pop("views", UNSET)
        views: Union[Unset, None, ScopeFilter]
        if _views is None:
            views = None
        elif isinstance(_views,  Unset):
            views = UNSET
        else:
            views = ScopeFilter.from_dict(_views)




        _commands = d.pop("commands", UNSET)
        commands: Union[Unset, None, ScopeFilter]
        if _commands is None:
            commands = None
        elif isinstance(_commands,  Unset):
            commands = UNSET
        else:
            commands = ScopeFilter.from_dict(_commands)




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
            types_item = DeviceScopeTypesItem(types_item_data)



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




        device_scope = cls(
            views=views,
            commands=commands,
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

        device_scope.additional_properties = d
        return device_scope

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
