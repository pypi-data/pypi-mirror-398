from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr

from ..models.teleop_joystick_configuration_position import \
    TeleopJoystickConfigurationPosition
from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.teleop_joystick_axis_configuration import \
      TeleopJoystickAxisConfiguration




T = TypeVar("T", bound="TeleopJoystickConfiguration")

@attr.s(auto_attribs=True)
class TeleopJoystickConfiguration:
    """
    Attributes:
        position (Union[Unset, TeleopJoystickConfigurationPosition]):
        disable_trigger_joystick_mapping (Union[Unset, bool]):
        disable_gamepad_and_keyboard (Union[Unset, bool]):
        same_value_debounce (Union[Unset, float]):
        new_value_debounce (Union[Unset, float]):
        x (Union[Unset, TeleopJoystickAxisConfiguration]):
        y (Union[Unset, TeleopJoystickAxisConfiguration]):
        velocity_stream_name (Union[Unset, str]):
    """

    position: Union[Unset, TeleopJoystickConfigurationPosition] = UNSET
    disable_trigger_joystick_mapping: Union[Unset, bool] = UNSET
    disable_gamepad_and_keyboard: Union[Unset, bool] = UNSET
    same_value_debounce: Union[Unset, float] = UNSET
    new_value_debounce: Union[Unset, float] = UNSET
    x: Union[Unset, 'TeleopJoystickAxisConfiguration'] = UNSET
    y: Union[Unset, 'TeleopJoystickAxisConfiguration'] = UNSET
    velocity_stream_name: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        position: Union[Unset, str] = UNSET
        if not isinstance(self.position, Unset):
            position = self.position.value

        disable_trigger_joystick_mapping = self.disable_trigger_joystick_mapping
        disable_gamepad_and_keyboard = self.disable_gamepad_and_keyboard
        same_value_debounce = self.same_value_debounce
        new_value_debounce = self.new_value_debounce
        x: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.x, Unset):
            x = self.x.to_dict()

        y: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.y, Unset):
            y = self.y.to_dict()

        velocity_stream_name = self.velocity_stream_name

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if position is not UNSET:
            field_dict["position"] = position
        if disable_trigger_joystick_mapping is not UNSET:
            field_dict["disableTriggerJoystickMapping"] = disable_trigger_joystick_mapping
        if disable_gamepad_and_keyboard is not UNSET:
            field_dict["disableGamepadAndKeyboard"] = disable_gamepad_and_keyboard
        if same_value_debounce is not UNSET:
            field_dict["sameValueDebounce"] = same_value_debounce
        if new_value_debounce is not UNSET:
            field_dict["newValueDebounce"] = new_value_debounce
        if x is not UNSET:
            field_dict["x"] = x
        if y is not UNSET:
            field_dict["y"] = y
        if velocity_stream_name is not UNSET:
            field_dict["velocityStreamName"] = velocity_stream_name

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.teleop_joystick_axis_configuration import \
            TeleopJoystickAxisConfiguration
        d = src_dict.copy()
        _position = d.pop("position", UNSET)
        position: Union[Unset, TeleopJoystickConfigurationPosition]
        if isinstance(_position,  Unset):
            position = UNSET
        else:
            position = TeleopJoystickConfigurationPosition(_position)




        disable_trigger_joystick_mapping = d.pop("disableTriggerJoystickMapping", UNSET)

        disable_gamepad_and_keyboard = d.pop("disableGamepadAndKeyboard", UNSET)

        same_value_debounce = d.pop("sameValueDebounce", UNSET)

        new_value_debounce = d.pop("newValueDebounce", UNSET)

        _x = d.pop("x", UNSET)
        x: Union[Unset, TeleopJoystickAxisConfiguration]
        if isinstance(_x,  Unset):
            x = UNSET
        else:
            x = TeleopJoystickAxisConfiguration.from_dict(_x)




        _y = d.pop("y", UNSET)
        y: Union[Unset, TeleopJoystickAxisConfiguration]
        if isinstance(_y,  Unset):
            y = UNSET
        else:
            y = TeleopJoystickAxisConfiguration.from_dict(_y)




        velocity_stream_name = d.pop("velocityStreamName", UNSET)

        teleop_joystick_configuration = cls(
            position=position,
            disable_trigger_joystick_mapping=disable_trigger_joystick_mapping,
            disable_gamepad_and_keyboard=disable_gamepad_and_keyboard,
            same_value_debounce=same_value_debounce,
            new_value_debounce=new_value_debounce,
            x=x,
            y=y,
            velocity_stream_name=velocity_stream_name,
        )

        teleop_joystick_configuration.additional_properties = d
        return teleop_joystick_configuration

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
