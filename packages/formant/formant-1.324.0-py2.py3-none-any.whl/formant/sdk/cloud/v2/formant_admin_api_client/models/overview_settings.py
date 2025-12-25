from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="OverviewSettings")

@attr.s(auto_attribs=True)
class OverviewSettings:
    """
    Attributes:
        overview_show_sidebar (Union[Unset, bool]):
        overview_sidebar_closed (Union[Unset, bool]):
        overview_settings_enabled (Union[Unset, bool]):
        overview_primary_mode (Union[Unset, None, str]):
        overview_secondary_mode (Union[Unset, None, str]):
        overview_show_filters (Union[Unset, bool]):
    """

    overview_show_sidebar: Union[Unset, bool] = UNSET
    overview_sidebar_closed: Union[Unset, bool] = UNSET
    overview_settings_enabled: Union[Unset, bool] = UNSET
    overview_primary_mode: Union[Unset, None, str] = UNSET
    overview_secondary_mode: Union[Unset, None, str] = UNSET
    overview_show_filters: Union[Unset, bool] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        overview_show_sidebar = self.overview_show_sidebar
        overview_sidebar_closed = self.overview_sidebar_closed
        overview_settings_enabled = self.overview_settings_enabled
        overview_primary_mode = self.overview_primary_mode
        overview_secondary_mode = self.overview_secondary_mode
        overview_show_filters = self.overview_show_filters

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if overview_show_sidebar is not UNSET:
            field_dict["overviewShowSidebar"] = overview_show_sidebar
        if overview_sidebar_closed is not UNSET:
            field_dict["overviewSidebarClosed"] = overview_sidebar_closed
        if overview_settings_enabled is not UNSET:
            field_dict["overviewSettingsEnabled"] = overview_settings_enabled
        if overview_primary_mode is not UNSET:
            field_dict["overviewPrimaryMode"] = overview_primary_mode
        if overview_secondary_mode is not UNSET:
            field_dict["overviewSecondaryMode"] = overview_secondary_mode
        if overview_show_filters is not UNSET:
            field_dict["overviewShowFilters"] = overview_show_filters

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        overview_show_sidebar = d.pop("overviewShowSidebar", UNSET)

        overview_sidebar_closed = d.pop("overviewSidebarClosed", UNSET)

        overview_settings_enabled = d.pop("overviewSettingsEnabled", UNSET)

        overview_primary_mode = d.pop("overviewPrimaryMode", UNSET)

        overview_secondary_mode = d.pop("overviewSecondaryMode", UNSET)

        overview_show_filters = d.pop("overviewShowFilters", UNSET)

        overview_settings = cls(
            overview_show_sidebar=overview_show_sidebar,
            overview_sidebar_closed=overview_sidebar_closed,
            overview_settings_enabled=overview_settings_enabled,
            overview_primary_mode=overview_primary_mode,
            overview_secondary_mode=overview_secondary_mode,
            overview_show_filters=overview_show_filters,
        )

        overview_settings.additional_properties = d
        return overview_settings

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
