from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..models.image_view_configuration_mode import ImageViewConfigurationMode
from ..types import UNSET, Unset

T = TypeVar("T", bound="ImageViewConfiguration")

@attr.s(auto_attribs=True)
class ImageViewConfiguration:
    """
    Attributes:
        mode (Union[Unset, ImageViewConfigurationMode]):
    """

    mode: Union[Unset, ImageViewConfigurationMode] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        mode: Union[Unset, str] = UNSET
        if not isinstance(self.mode, Unset):
            mode = self.mode.value


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if mode is not UNSET:
            field_dict["mode"] = mode

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        _mode = d.pop("mode", UNSET)
        mode: Union[Unset, ImageViewConfigurationMode]
        if isinstance(_mode,  Unset):
            mode = UNSET
        else:
            mode = ImageViewConfigurationMode(_mode)




        image_view_configuration = cls(
            mode=mode,
        )

        image_view_configuration.additional_properties = d
        return image_view_configuration

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
