from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="DeviceDiagnosticsConfiguration")

@attr.s(auto_attribs=True)
class DeviceDiagnosticsConfiguration:
    """
    Attributes:
        report_logs (Union[Unset, None, bool]):
        ingest_logs (Union[Unset, None, bool]):
        report_metrics (Union[Unset, None, bool]):
    """

    report_logs: Union[Unset, None, bool] = UNSET
    ingest_logs: Union[Unset, None, bool] = UNSET
    report_metrics: Union[Unset, None, bool] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        report_logs = self.report_logs
        ingest_logs = self.ingest_logs
        report_metrics = self.report_metrics

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if report_logs is not UNSET:
            field_dict["reportLogs"] = report_logs
        if ingest_logs is not UNSET:
            field_dict["ingestLogs"] = ingest_logs
        if report_metrics is not UNSET:
            field_dict["reportMetrics"] = report_metrics

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        report_logs = d.pop("reportLogs", UNSET)

        ingest_logs = d.pop("ingestLogs", UNSET)

        report_metrics = d.pop("reportMetrics", UNSET)

        device_diagnostics_configuration = cls(
            report_logs=report_logs,
            ingest_logs=ingest_logs,
            report_metrics=report_metrics,
        )

        device_diagnostics_configuration.additional_properties = d
        return device_diagnostics_configuration

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
