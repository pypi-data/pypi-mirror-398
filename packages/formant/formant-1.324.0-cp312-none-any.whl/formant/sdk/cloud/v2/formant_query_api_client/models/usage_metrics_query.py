import datetime
from typing import Any, Dict, List, Type, TypeVar, Union

import attr
from dateutil.parser import isoparse

from ..models.usage_metrics_query_metric_type import \
    UsageMetricsQueryMetricType
from ..types import UNSET, Unset

T = TypeVar("T", bound="UsageMetricsQuery")

@attr.s(auto_attribs=True)
class UsageMetricsQuery:
    """
    Attributes:
        start (datetime.datetime):
        end (datetime.datetime):
        metric_type (Union[Unset, UsageMetricsQueryMetricType]):
        detailed (Union[Unset, bool]):
    """

    start: datetime.datetime
    end: datetime.datetime
    metric_type: Union[Unset, UsageMetricsQueryMetricType] = UNSET
    detailed: Union[Unset, bool] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        start = self.start.isoformat()

        end = self.end.isoformat()

        metric_type: Union[Unset, str] = UNSET
        if not isinstance(self.metric_type, Unset):
            metric_type = self.metric_type.value

        detailed = self.detailed

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "start": start,
            "end": end,
        })
        if metric_type is not UNSET:
            field_dict["metricType"] = metric_type
        if detailed is not UNSET:
            field_dict["detailed"] = detailed

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        start = isoparse(d.pop("start"))




        end = isoparse(d.pop("end"))




        _metric_type = d.pop("metricType", UNSET)
        metric_type: Union[Unset, UsageMetricsQueryMetricType]
        if isinstance(_metric_type,  Unset):
            metric_type = UNSET
        else:
            metric_type = UsageMetricsQueryMetricType(_metric_type)




        detailed = d.pop("detailed", UNSET)

        usage_metrics_query = cls(
            start=start,
            end=end,
            metric_type=metric_type,
            detailed=detailed,
        )

        usage_metrics_query.additional_properties = d
        return usage_metrics_query

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
