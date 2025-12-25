from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..models.teleop_joystick_axis_configuration_dimension import \
    TeleopJoystickAxisConfigurationDimension
from ..types import UNSET, Unset

T = TypeVar("T", bound="TeleopJoystickAxisConfiguration")

@attr.s(auto_attribs=True)
class TeleopJoystickAxisConfiguration:
    """
    Attributes:
        dimension (Union[Unset, TeleopJoystickAxisConfigurationDimension]):
        scale (Union[Unset, float]):
        expo (Union[Unset, float]):
        gamepad_axis (Union[Unset, int]):
    """

    dimension: Union[Unset, TeleopJoystickAxisConfigurationDimension] = UNSET
    scale: Union[Unset, float] = UNSET
    expo: Union[Unset, float] = UNSET
    gamepad_axis: Union[Unset, int] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        dimension: Union[Unset, str] = UNSET
        if not isinstance(self.dimension, Unset):
            dimension = self.dimension.value

        scale = self.scale
        expo = self.expo
        gamepad_axis = self.gamepad_axis

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if dimension is not UNSET:
            field_dict["dimension"] = dimension
        if scale is not UNSET:
            field_dict["scale"] = scale
        if expo is not UNSET:
            field_dict["expo"] = expo
        if gamepad_axis is not UNSET:
            field_dict["gamepadAxis"] = gamepad_axis

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        _dimension = d.pop("dimension", UNSET)
        dimension: Union[Unset, TeleopJoystickAxisConfigurationDimension]
        if isinstance(_dimension,  Unset):
            dimension = UNSET
        else:
            dimension = TeleopJoystickAxisConfigurationDimension(_dimension)




        scale = d.pop("scale", UNSET)

        expo = d.pop("expo", UNSET)

        gamepad_axis = d.pop("gamepadAxis", UNSET)

        teleop_joystick_axis_configuration = cls(
            dimension=dimension,
            scale=scale,
            expo=expo,
            gamepad_axis=gamepad_axis,
        )

        teleop_joystick_axis_configuration.additional_properties = d
        return teleop_joystick_axis_configuration

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
