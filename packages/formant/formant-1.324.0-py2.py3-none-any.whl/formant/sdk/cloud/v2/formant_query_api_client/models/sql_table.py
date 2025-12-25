from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.sql_column import SqlColumn




T = TypeVar("T", bound="SqlTable")

@attr.s(auto_attribs=True)
class SqlTable:
    """
    Attributes:
        name (str):
        columns (List['SqlColumn']):
        description (Union[Unset, str]):
    """

    name: str
    columns: List['SqlColumn']
    description: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        columns = []
        for columns_item_data in self.columns:
            columns_item = columns_item_data.to_dict()

            columns.append(columns_item)




        description = self.description

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "name": name,
            "columns": columns,
        })
        if description is not UNSET:
            field_dict["description"] = description

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.sql_column import SqlColumn
        d = src_dict.copy()
        name = d.pop("name")

        columns = []
        _columns = d.pop("columns")
        for columns_item_data in (_columns):
            columns_item = SqlColumn.from_dict(columns_item_data)



            columns.append(columns_item)


        description = d.pop("description", UNSET)

        sql_table = cls(
            name=name,
            columns=columns,
            description=description,
        )

        sql_table.additional_properties = d
        return sql_table

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
