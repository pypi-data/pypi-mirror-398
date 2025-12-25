import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union, cast

import attr
from dateutil.parser import isoparse

from ..models.sql_query_aggregate_level import SqlQueryAggregateLevel
from ..models.sql_query_aggregate_type import SqlQueryAggregateType
from ..models.sql_query_types_item import SqlQueryTypesItem
from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.tag_sets import TagSets




T = TypeVar("T", bound="SqlQuery")

@attr.s(auto_attribs=True)
class SqlQuery:
    """
    Attributes:
        sql_query (Union[Unset, str]):
        parameters (Union[Unset, List[str]]):
        start (Union[Unset, datetime.datetime]):
        end (Union[Unset, datetime.datetime]):
        limit (Union[Unset, float]):
        table_columns (Union[Unset, List[Any]]):
        aggregate_level (Union[Unset, None, SqlQueryAggregateLevel]):
        aggregate_type (Union[Unset, SqlQueryAggregateType]):
        order_by_column (Union[Unset, str]):
        order_by_descending (Union[Unset, bool]):
        group_by_device (Union[Unset, bool]):
        time_dimension (Union[Unset, bool]):
        type (Union[Unset, str]):
        fill_gaps (Union[Unset, bool]):
        unit (Union[Unset, str]):
        timezone (Union[Unset, str]):
        account_id (Union[Unset, str]):
        tags (Union['TagSets', List['TagSets'], Unset]): One or more TagSets (combined with OR logic)
        device_ids (Union[Unset, List[str]]):
        names (Union[Unset, List[str]]):
        types (Union[Unset, List[SqlQueryTypesItem]]):
        not_tags (Union[Unset, Any]):
        not_names (Union[Unset, List[str]]):
        agent_ids (Union[Unset, List[str]]):
    """

    sql_query: Union[Unset, str] = UNSET
    parameters: Union[Unset, List[str]] = UNSET
    start: Union[Unset, datetime.datetime] = UNSET
    end: Union[Unset, datetime.datetime] = UNSET
    limit: Union[Unset, float] = UNSET
    table_columns: Union[Unset, List[Any]] = UNSET
    aggregate_level: Union[Unset, None, SqlQueryAggregateLevel] = UNSET
    aggregate_type: Union[Unset, SqlQueryAggregateType] = UNSET
    order_by_column: Union[Unset, str] = UNSET
    order_by_descending: Union[Unset, bool] = UNSET
    group_by_device: Union[Unset, bool] = UNSET
    time_dimension: Union[Unset, bool] = UNSET
    type: Union[Unset, str] = UNSET
    fill_gaps: Union[Unset, bool] = UNSET
    unit: Union[Unset, str] = UNSET
    timezone: Union[Unset, str] = UNSET
    account_id: Union[Unset, str] = UNSET
    tags: Union['TagSets', List['TagSets'], Unset] = UNSET
    device_ids: Union[Unset, List[str]] = UNSET
    names: Union[Unset, List[str]] = UNSET
    types: Union[Unset, List[SqlQueryTypesItem]] = UNSET
    not_tags: Union[Unset, Any] = UNSET
    not_names: Union[Unset, List[str]] = UNSET
    agent_ids: Union[Unset, List[str]] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        sql_query = self.sql_query
        parameters: Union[Unset, List[str]] = UNSET
        if not isinstance(self.parameters, Unset):
            parameters = self.parameters




        start: Union[Unset, str] = UNSET
        if not isinstance(self.start, Unset):
            start = self.start.isoformat()

        end: Union[Unset, str] = UNSET
        if not isinstance(self.end, Unset):
            end = self.end.isoformat()

        limit = self.limit
        table_columns: Union[Unset, List[Any]] = UNSET
        if not isinstance(self.table_columns, Unset):
            table_columns = self.table_columns




        aggregate_level: Union[Unset, None, str] = UNSET
        if not isinstance(self.aggregate_level, Unset):
            aggregate_level = self.aggregate_level.value if self.aggregate_level else None

        aggregate_type: Union[Unset, str] = UNSET
        if not isinstance(self.aggregate_type, Unset):
            aggregate_type = self.aggregate_type.value

        order_by_column = self.order_by_column
        order_by_descending = self.order_by_descending
        group_by_device = self.group_by_device
        time_dimension = self.time_dimension
        type = self.type
        fill_gaps = self.fill_gaps
        unit = self.unit
        timezone = self.timezone
        account_id = self.account_id
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





        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if sql_query is not UNSET:
            field_dict["sqlQuery"] = sql_query
        if parameters is not UNSET:
            field_dict["parameters"] = parameters
        if start is not UNSET:
            field_dict["start"] = start
        if end is not UNSET:
            field_dict["end"] = end
        if limit is not UNSET:
            field_dict["limit"] = limit
        if table_columns is not UNSET:
            field_dict["tableColumns"] = table_columns
        if aggregate_level is not UNSET:
            field_dict["aggregateLevel"] = aggregate_level
        if aggregate_type is not UNSET:
            field_dict["aggregateType"] = aggregate_type
        if order_by_column is not UNSET:
            field_dict["orderByColumn"] = order_by_column
        if order_by_descending is not UNSET:
            field_dict["orderByDescending"] = order_by_descending
        if group_by_device is not UNSET:
            field_dict["groupByDevice"] = group_by_device
        if time_dimension is not UNSET:
            field_dict["timeDimension"] = time_dimension
        if type is not UNSET:
            field_dict["type"] = type
        if fill_gaps is not UNSET:
            field_dict["fillGaps"] = fill_gaps
        if unit is not UNSET:
            field_dict["unit"] = unit
        if timezone is not UNSET:
            field_dict["timezone"] = timezone
        if account_id is not UNSET:
            field_dict["accountId"] = account_id
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

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.tag_sets import TagSets
        d = src_dict.copy()
        sql_query = d.pop("sqlQuery", UNSET)

        parameters = cast(List[str], d.pop("parameters", UNSET))


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




        limit = d.pop("limit", UNSET)

        table_columns = cast(List[Any], d.pop("tableColumns", UNSET))


        _aggregate_level = d.pop("aggregateLevel", UNSET)
        aggregate_level: Union[Unset, None, SqlQueryAggregateLevel]
        if _aggregate_level is None:
            aggregate_level = None
        elif isinstance(_aggregate_level,  Unset):
            aggregate_level = UNSET
        else:
            aggregate_level = SqlQueryAggregateLevel(_aggregate_level)




        _aggregate_type = d.pop("aggregateType", UNSET)
        aggregate_type: Union[Unset, SqlQueryAggregateType]
        if isinstance(_aggregate_type,  Unset):
            aggregate_type = UNSET
        else:
            aggregate_type = SqlQueryAggregateType(_aggregate_type)




        order_by_column = d.pop("orderByColumn", UNSET)

        order_by_descending = d.pop("orderByDescending", UNSET)

        group_by_device = d.pop("groupByDevice", UNSET)

        time_dimension = d.pop("timeDimension", UNSET)

        type = d.pop("type", UNSET)

        fill_gaps = d.pop("fillGaps", UNSET)

        unit = d.pop("unit", UNSET)

        timezone = d.pop("timezone", UNSET)

        account_id = d.pop("accountId", UNSET)

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
            types_item = SqlQueryTypesItem(types_item_data)



            types.append(types_item)


        not_tags = d.pop("notTags", UNSET)

        not_names = cast(List[str], d.pop("notNames", UNSET))


        agent_ids = cast(List[str], d.pop("agentIds", UNSET))


        sql_query = cls(
            sql_query=sql_query,
            parameters=parameters,
            start=start,
            end=end,
            limit=limit,
            table_columns=table_columns,
            aggregate_level=aggregate_level,
            aggregate_type=aggregate_type,
            order_by_column=order_by_column,
            order_by_descending=order_by_descending,
            group_by_device=group_by_device,
            time_dimension=time_dimension,
            type=type,
            fill_gaps=fill_gaps,
            unit=unit,
            timezone=timezone,
            account_id=account_id,
            tags=tags,
            device_ids=device_ids,
            names=names,
            types=types,
            not_tags=not_tags,
            not_names=not_names,
            agent_ids=agent_ids,
        )

        sql_query.additional_properties = d
        return sql_query

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
