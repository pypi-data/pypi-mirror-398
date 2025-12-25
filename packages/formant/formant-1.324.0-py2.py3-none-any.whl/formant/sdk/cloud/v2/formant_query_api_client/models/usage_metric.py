import datetime
from typing import Any, Dict, List, Type, TypeVar, Union

import attr
from dateutil.parser import isoparse

from ..models.usage_metric_metric_type import UsageMetricMetricType
from ..types import UNSET, Unset

T = TypeVar("T", bound="UsageMetric")

@attr.s(auto_attribs=True)
class UsageMetric:
    """
    Attributes:
        organization_id (str):
        metric_type (UsageMetricMetricType):
        time (datetime.datetime):
        metric_value (int):
        source_id (str):
        device_id (Union[Unset, None, str]):
        user_id (Union[Unset, None, str]):
        id (Union[Unset, str]):
        created_at (Union[Unset, datetime.datetime]):
        updated_at (Union[Unset, datetime.datetime]):
    """

    organization_id: str
    metric_type: UsageMetricMetricType
    time: datetime.datetime
    metric_value: int
    source_id: str
    device_id: Union[Unset, None, str] = UNSET
    user_id: Union[Unset, None, str] = UNSET
    id: Union[Unset, str] = UNSET
    created_at: Union[Unset, datetime.datetime] = UNSET
    updated_at: Union[Unset, datetime.datetime] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        organization_id = self.organization_id
        metric_type = self.metric_type.value

        time = self.time.isoformat()

        metric_value = self.metric_value
        source_id = self.source_id
        device_id = self.device_id
        user_id = self.user_id
        id = self.id
        created_at: Union[Unset, str] = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: Union[Unset, str] = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "organizationId": organization_id,
            "metricType": metric_type,
            "time": time,
            "metricValue": metric_value,
            "sourceId": source_id,
        })
        if device_id is not UNSET:
            field_dict["deviceId"] = device_id
        if user_id is not UNSET:
            field_dict["userId"] = user_id
        if id is not UNSET:
            field_dict["id"] = id
        if created_at is not UNSET:
            field_dict["createdAt"] = created_at
        if updated_at is not UNSET:
            field_dict["updatedAt"] = updated_at

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        organization_id = d.pop("organizationId")

        metric_type = UsageMetricMetricType(d.pop("metricType"))




        time = isoparse(d.pop("time"))




        metric_value = d.pop("metricValue")

        source_id = d.pop("sourceId")

        device_id = d.pop("deviceId", UNSET)

        user_id = d.pop("userId", UNSET)

        id = d.pop("id", UNSET)

        _created_at = d.pop("createdAt", UNSET)
        created_at: Union[Unset, datetime.datetime]
        if isinstance(_created_at,  Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)




        _updated_at = d.pop("updatedAt", UNSET)
        updated_at: Union[Unset, datetime.datetime]
        if isinstance(_updated_at,  Unset):
            updated_at = UNSET
        else:
            updated_at = isoparse(_updated_at)




        usage_metric = cls(
            organization_id=organization_id,
            metric_type=metric_type,
            time=time,
            metric_value=metric_value,
            source_id=source_id,
            device_id=device_id,
            user_id=user_id,
            id=id,
            created_at=created_at,
            updated_at=updated_at,
        )

        usage_metric.additional_properties = d
        return usage_metric

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
