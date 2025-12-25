from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

import attr

if TYPE_CHECKING:
  from ..models.usage_record import UsageRecord




T = TypeVar("T", bound="UsageRecordQueryResponse")

@attr.s(auto_attribs=True)
class UsageRecordQueryResponse:
    """
    Attributes:
        records (List['UsageRecord']):
    """

    records: List['UsageRecord']
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        records = []
        for records_item_data in self.records:
            records_item = records_item_data.to_dict()

            records.append(records_item)





        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "records": records,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.usage_record import UsageRecord
        d = src_dict.copy()
        records = []
        _records = d.pop("records")
        for records_item_data in (_records):
            records_item = UsageRecord.from_dict(records_item_data)



            records.append(records_item)


        usage_record_query_response = cls(
            records=records,
        )

        usage_record_query_response.additional_properties = d
        return usage_record_query_response

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
