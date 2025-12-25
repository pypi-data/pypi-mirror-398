from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union, cast

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.sql_column import SqlColumn




T = TypeVar("T", bound="SqlResult")

@attr.s(auto_attribs=True)
class SqlResult:
    """
    Attributes:
        rows (List[Any]):
        columns (List['SqlColumn']):
        row_count (float):
        sql_text (str):
        unit (Union[Unset, str]):
        auto_analytics (Union[Unset, Any]): Auto analytics insights
    """

    rows: List[Any]
    columns: List['SqlColumn']
    row_count: float
    sql_text: str
    unit: Union[Unset, str] = UNSET
    auto_analytics: Union[Unset, Any] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        rows = self.rows




        columns = []
        for columns_item_data in self.columns:
            columns_item = columns_item_data.to_dict()

            columns.append(columns_item)




        row_count = self.row_count
        sql_text = self.sql_text
        unit = self.unit
        auto_analytics = self.auto_analytics

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "rows": rows,
            "columns": columns,
            "rowCount": row_count,
            "sqlText": sql_text,
        })
        if unit is not UNSET:
            field_dict["unit"] = unit
        if auto_analytics is not UNSET:
            field_dict["autoAnalytics"] = auto_analytics

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.sql_column import SqlColumn
        d = src_dict.copy()
        rows = cast(List[Any], d.pop("rows"))


        columns = []
        _columns = d.pop("columns")
        for columns_item_data in (_columns):
            columns_item = SqlColumn.from_dict(columns_item_data)



            columns.append(columns_item)


        row_count = d.pop("rowCount")

        sql_text = d.pop("sqlText")

        unit = d.pop("unit", UNSET)

        auto_analytics = d.pop("autoAnalytics", UNSET)

        sql_result = cls(
            rows=rows,
            columns=columns,
            row_count=row_count,
            sql_text=sql_text,
            unit=unit,
            auto_analytics=auto_analytics,
        )

        sql_result.additional_properties = d
        return sql_result

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
