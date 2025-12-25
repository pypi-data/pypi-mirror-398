from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.camera import Camera




T = TypeVar("T", bound="LocalizationViewConfiguration")

@attr.s(auto_attribs=True)
class LocalizationViewConfiguration:
    """
    Attributes:
        camera (Union[Unset, Camera]):
    """

    camera: Union[Unset, 'Camera'] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        camera: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.camera, Unset):
            camera = self.camera.to_dict()


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if camera is not UNSET:
            field_dict["camera"] = camera

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.camera import Camera
        d = src_dict.copy()
        _camera = d.pop("camera", UNSET)
        camera: Union[Unset, Camera]
        if isinstance(_camera,  Unset):
            camera = UNSET
        else:
            camera = Camera.from_dict(_camera)




        localization_view_configuration = cls(
            camera=camera,
        )

        localization_view_configuration.additional_properties = d
        return localization_view_configuration

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
