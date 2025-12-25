import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union, cast

import attr
from dateutil.parser import isoparse

from ..models.event_seek_query_direction import EventSeekQueryDirection
from ..models.event_seek_query_event_types_item import \
    EventSeekQueryEventTypesItem
from ..models.event_seek_query_severities_item import \
    EventSeekQuerySeveritiesItem
from ..models.event_seek_query_types_item import EventSeekQueryTypesItem
from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.tag_sets import TagSets




T = TypeVar("T", bound="EventSeekQuery")

@attr.s(auto_attribs=True)
class EventSeekQuery:
    """
    Attributes:
        direction (EventSeekQueryDirection):
        from_ (datetime.datetime):
        tags (Union['TagSets', List['TagSets'], Unset]): One or more TagSets (combined with OR logic)
        device_ids (Union[Unset, List[str]]):
        names (Union[Unset, List[str]]):
        types (Union[Unset, List[EventSeekQueryTypesItem]]):
        not_tags (Union[Unset, Any]):
        not_names (Union[Unset, List[str]]):
        agent_ids (Union[Unset, List[str]]):
        start (Union[Unset, datetime.datetime]):
        end (Union[Unset, datetime.datetime]):
        id (Union[Unset, str]):
        viewed (Union[Unset, bool]):
        keyword (Union[Unset, str]):
        message (Union[Unset, str]):
        event_types (Union[Unset, List[EventSeekQueryEventTypesItem]]):
        notification_enabled (Union[Unset, bool]):
        user_ids (Union[Unset, List[str]]):
        annotation_template_ids (Union[Unset, List[str]]):
        disable_null_matches (Union[Unset, bool]):
        severities (Union[Unset, List[EventSeekQuerySeveritiesItem]]):
        sets_device_color (Union[Unset, bool]):
        external_ids (Union[Unset, List[str]]):
        parent_ids (Union[Unset, List[str]]):
    """

    direction: EventSeekQueryDirection
    from_: datetime.datetime
    tags: Union['TagSets', List['TagSets'], Unset] = UNSET
    device_ids: Union[Unset, List[str]] = UNSET
    names: Union[Unset, List[str]] = UNSET
    types: Union[Unset, List[EventSeekQueryTypesItem]] = UNSET
    not_tags: Union[Unset, Any] = UNSET
    not_names: Union[Unset, List[str]] = UNSET
    agent_ids: Union[Unset, List[str]] = UNSET
    start: Union[Unset, datetime.datetime] = UNSET
    end: Union[Unset, datetime.datetime] = UNSET
    id: Union[Unset, str] = UNSET
    viewed: Union[Unset, bool] = UNSET
    keyword: Union[Unset, str] = UNSET
    message: Union[Unset, str] = UNSET
    event_types: Union[Unset, List[EventSeekQueryEventTypesItem]] = UNSET
    notification_enabled: Union[Unset, bool] = UNSET
    user_ids: Union[Unset, List[str]] = UNSET
    annotation_template_ids: Union[Unset, List[str]] = UNSET
    disable_null_matches: Union[Unset, bool] = UNSET
    severities: Union[Unset, List[EventSeekQuerySeveritiesItem]] = UNSET
    sets_device_color: Union[Unset, bool] = UNSET
    external_ids: Union[Unset, List[str]] = UNSET
    parent_ids: Union[Unset, List[str]] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        direction = self.direction.value

        from_ = self.from_.isoformat()

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

        id = self.id
        viewed = self.viewed
        keyword = self.keyword
        message = self.message
        event_types: Union[Unset, List[str]] = UNSET
        if not isinstance(self.event_types, Unset):
            event_types = []
            for event_types_item_data in self.event_types:
                event_types_item = event_types_item_data.value

                event_types.append(event_types_item)




        notification_enabled = self.notification_enabled
        user_ids: Union[Unset, List[str]] = UNSET
        if not isinstance(self.user_ids, Unset):
            user_ids = self.user_ids




        annotation_template_ids: Union[Unset, List[str]] = UNSET
        if not isinstance(self.annotation_template_ids, Unset):
            annotation_template_ids = self.annotation_template_ids




        disable_null_matches = self.disable_null_matches
        severities: Union[Unset, List[str]] = UNSET
        if not isinstance(self.severities, Unset):
            severities = []
            for severities_item_data in self.severities:
                severities_item = severities_item_data.value

                severities.append(severities_item)




        sets_device_color = self.sets_device_color
        external_ids: Union[Unset, List[str]] = UNSET
        if not isinstance(self.external_ids, Unset):
            external_ids = self.external_ids




        parent_ids: Union[Unset, List[str]] = UNSET
        if not isinstance(self.parent_ids, Unset):
            parent_ids = self.parent_ids





        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "direction": direction,
            "from": from_,
        })
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
        if id is not UNSET:
            field_dict["id"] = id
        if viewed is not UNSET:
            field_dict["viewed"] = viewed
        if keyword is not UNSET:
            field_dict["keyword"] = keyword
        if message is not UNSET:
            field_dict["message"] = message
        if event_types is not UNSET:
            field_dict["eventTypes"] = event_types
        if notification_enabled is not UNSET:
            field_dict["notificationEnabled"] = notification_enabled
        if user_ids is not UNSET:
            field_dict["userIds"] = user_ids
        if annotation_template_ids is not UNSET:
            field_dict["annotationTemplateIds"] = annotation_template_ids
        if disable_null_matches is not UNSET:
            field_dict["disableNullMatches"] = disable_null_matches
        if severities is not UNSET:
            field_dict["severities"] = severities
        if sets_device_color is not UNSET:
            field_dict["setsDeviceColor"] = sets_device_color
        if external_ids is not UNSET:
            field_dict["externalIds"] = external_ids
        if parent_ids is not UNSET:
            field_dict["parentIds"] = parent_ids

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.tag_sets import TagSets
        d = src_dict.copy()
        direction = EventSeekQueryDirection(d.pop("direction"))




        from_ = isoparse(d.pop("from"))




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
            types_item = EventSeekQueryTypesItem(types_item_data)



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




        id = d.pop("id", UNSET)

        viewed = d.pop("viewed", UNSET)

        keyword = d.pop("keyword", UNSET)

        message = d.pop("message", UNSET)

        event_types = []
        _event_types = d.pop("eventTypes", UNSET)
        for event_types_item_data in (_event_types or []):
            event_types_item = EventSeekQueryEventTypesItem(event_types_item_data)



            event_types.append(event_types_item)


        notification_enabled = d.pop("notificationEnabled", UNSET)

        user_ids = cast(List[str], d.pop("userIds", UNSET))


        annotation_template_ids = cast(List[str], d.pop("annotationTemplateIds", UNSET))


        disable_null_matches = d.pop("disableNullMatches", UNSET)

        severities = []
        _severities = d.pop("severities", UNSET)
        for severities_item_data in (_severities or []):
            severities_item = EventSeekQuerySeveritiesItem(severities_item_data)



            severities.append(severities_item)


        sets_device_color = d.pop("setsDeviceColor", UNSET)

        external_ids = cast(List[str], d.pop("externalIds", UNSET))


        parent_ids = cast(List[str], d.pop("parentIds", UNSET))


        event_seek_query = cls(
            direction=direction,
            from_=from_,
            tags=tags,
            device_ids=device_ids,
            names=names,
            types=types,
            not_tags=not_tags,
            not_names=not_names,
            agent_ids=agent_ids,
            start=start,
            end=end,
            id=id,
            viewed=viewed,
            keyword=keyword,
            message=message,
            event_types=event_types,
            notification_enabled=notification_enabled,
            user_ids=user_ids,
            annotation_template_ids=annotation_template_ids,
            disable_null_matches=disable_null_matches,
            severities=severities,
            sets_device_color=sets_device_color,
            external_ids=external_ids,
            parent_ids=parent_ids,
        )

        event_seek_query.additional_properties = d
        return event_seek_query

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
