from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

import attr

if TYPE_CHECKING:
  from ..models.sql_table import SqlTable




T = TypeVar("T", bound="SqlTablesListReponse")

@attr.s(auto_attribs=True)
class SqlTablesListReponse:
    """
    Attributes:
        items (List['SqlTable']):
    """

    items: List['SqlTable']
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        items = []
        for items_item_data in self.items:
            items_item = items_item_data.to_dict()

            items.append(items_item)





        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "items": items,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.sql_table import SqlTable
        d = src_dict.copy()
        items = []
        _items = d.pop("items")
        for items_item_data in (_items):
            items_item = SqlTable.from_dict(items_item_data)



            items.append(items_item)


        sql_tables_list_reponse = cls(
            items=items,
        )

        sql_tables_list_reponse.additional_properties = d
        return sql_tables_list_reponse

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
