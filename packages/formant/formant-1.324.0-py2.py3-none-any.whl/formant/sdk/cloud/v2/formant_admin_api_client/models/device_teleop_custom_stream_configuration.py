from typing import Any, Dict, List, Type, TypeVar, Union, cast

import attr

from ..models.device_teleop_custom_stream_configuration_mode import \
    DeviceTeleopCustomStreamConfigurationMode
from ..models.device_teleop_custom_stream_configuration_numeric_control_visualization import \
    DeviceTeleopCustomStreamConfigurationNumericControlVisualization
from ..models.device_teleop_custom_stream_configuration_quality import \
    DeviceTeleopCustomStreamConfigurationQuality
from ..models.device_teleop_custom_stream_configuration_rtc_stream_type import \
    DeviceTeleopCustomStreamConfigurationRtcStreamType
from ..types import UNSET, Unset

T = TypeVar("T", bound="DeviceTeleopCustomStreamConfiguration")

@attr.s(auto_attribs=True)
class DeviceTeleopCustomStreamConfiguration:
    """
    Attributes:
        name (str):
        rtc_stream_type (DeviceTeleopCustomStreamConfigurationRtcStreamType):
        mode (DeviceTeleopCustomStreamConfigurationMode):
        label (Union[Unset, str]):
        value_stream_name (Union[Unset, str]):
        labels (Union[Unset, List[str]]):
        encode_video (Union[Unset, bool]):
        overlay_clock (Union[Unset, bool]):
        min_ (Union[Unset, float]):
        max_ (Union[Unset, float]):
        default_value (Union[Unset, float]):
        step (Union[Unset, float]):
        numeric_control_visualization (Union[Unset, DeviceTeleopCustomStreamConfigurationNumericControlVisualization]):
        quality (Union[Unset, DeviceTeleopCustomStreamConfigurationQuality]):
        mouse_events_target_stream (Union[Unset, str]):
        button_color (Union[Unset, str]):
        button_label (Union[Unset, str]):
        bitrate (Union[Unset, int]):
        disable_adaptive_quality (Union[Unset, bool]):
        joy_frequency (Union[Unset, float]):
        joy_disable_button_mapping (Union[Unset, bool]):
    """

    name: str
    rtc_stream_type: DeviceTeleopCustomStreamConfigurationRtcStreamType
    mode: DeviceTeleopCustomStreamConfigurationMode
    label: Union[Unset, str] = UNSET
    value_stream_name: Union[Unset, str] = UNSET
    labels: Union[Unset, List[str]] = UNSET
    encode_video: Union[Unset, bool] = UNSET
    overlay_clock: Union[Unset, bool] = UNSET
    min_: Union[Unset, float] = UNSET
    max_: Union[Unset, float] = UNSET
    default_value: Union[Unset, float] = UNSET
    step: Union[Unset, float] = UNSET
    numeric_control_visualization: Union[Unset, DeviceTeleopCustomStreamConfigurationNumericControlVisualization] = UNSET
    quality: Union[Unset, DeviceTeleopCustomStreamConfigurationQuality] = UNSET
    mouse_events_target_stream: Union[Unset, str] = UNSET
    button_color: Union[Unset, str] = UNSET
    button_label: Union[Unset, str] = UNSET
    bitrate: Union[Unset, int] = UNSET
    disable_adaptive_quality: Union[Unset, bool] = UNSET
    joy_frequency: Union[Unset, float] = UNSET
    joy_disable_button_mapping: Union[Unset, bool] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        rtc_stream_type = self.rtc_stream_type.value

        mode = self.mode.value

        label = self.label
        value_stream_name = self.value_stream_name
        labels: Union[Unset, List[str]] = UNSET
        if not isinstance(self.labels, Unset):
            labels = self.labels




        encode_video = self.encode_video
        overlay_clock = self.overlay_clock
        min_ = self.min_
        max_ = self.max_
        default_value = self.default_value
        step = self.step
        numeric_control_visualization: Union[Unset, str] = UNSET
        if not isinstance(self.numeric_control_visualization, Unset):
            numeric_control_visualization = self.numeric_control_visualization.value

        quality: Union[Unset, str] = UNSET
        if not isinstance(self.quality, Unset):
            quality = self.quality.value

        mouse_events_target_stream = self.mouse_events_target_stream
        button_color = self.button_color
        button_label = self.button_label
        bitrate = self.bitrate
        disable_adaptive_quality = self.disable_adaptive_quality
        joy_frequency = self.joy_frequency
        joy_disable_button_mapping = self.joy_disable_button_mapping

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "name": name,
            "rtcStreamType": rtc_stream_type,
            "mode": mode,
        })
        if label is not UNSET:
            field_dict["label"] = label
        if value_stream_name is not UNSET:
            field_dict["valueStreamName"] = value_stream_name
        if labels is not UNSET:
            field_dict["labels"] = labels
        if encode_video is not UNSET:
            field_dict["encodeVideo"] = encode_video
        if overlay_clock is not UNSET:
            field_dict["overlayClock"] = overlay_clock
        if min_ is not UNSET:
            field_dict["min"] = min_
        if max_ is not UNSET:
            field_dict["max"] = max_
        if default_value is not UNSET:
            field_dict["defaultValue"] = default_value
        if step is not UNSET:
            field_dict["step"] = step
        if numeric_control_visualization is not UNSET:
            field_dict["numericControlVisualization"] = numeric_control_visualization
        if quality is not UNSET:
            field_dict["quality"] = quality
        if mouse_events_target_stream is not UNSET:
            field_dict["mouseEventsTargetStream"] = mouse_events_target_stream
        if button_color is not UNSET:
            field_dict["buttonColor"] = button_color
        if button_label is not UNSET:
            field_dict["buttonLabel"] = button_label
        if bitrate is not UNSET:
            field_dict["bitrate"] = bitrate
        if disable_adaptive_quality is not UNSET:
            field_dict["disableAdaptiveQuality"] = disable_adaptive_quality
        if joy_frequency is not UNSET:
            field_dict["joyFrequency"] = joy_frequency
        if joy_disable_button_mapping is not UNSET:
            field_dict["joyDisableButtonMapping"] = joy_disable_button_mapping

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        name = d.pop("name")

        rtc_stream_type = DeviceTeleopCustomStreamConfigurationRtcStreamType(d.pop("rtcStreamType"))




        mode = DeviceTeleopCustomStreamConfigurationMode(d.pop("mode"))




        label = d.pop("label", UNSET)

        value_stream_name = d.pop("valueStreamName", UNSET)

        labels = cast(List[str], d.pop("labels", UNSET))


        encode_video = d.pop("encodeVideo", UNSET)

        overlay_clock = d.pop("overlayClock", UNSET)

        min_ = d.pop("min", UNSET)

        max_ = d.pop("max", UNSET)

        default_value = d.pop("defaultValue", UNSET)

        step = d.pop("step", UNSET)

        _numeric_control_visualization = d.pop("numericControlVisualization", UNSET)
        numeric_control_visualization: Union[Unset, DeviceTeleopCustomStreamConfigurationNumericControlVisualization]
        if isinstance(_numeric_control_visualization,  Unset):
            numeric_control_visualization = UNSET
        else:
            numeric_control_visualization = DeviceTeleopCustomStreamConfigurationNumericControlVisualization(_numeric_control_visualization)




        _quality = d.pop("quality", UNSET)
        quality: Union[Unset, DeviceTeleopCustomStreamConfigurationQuality]
        if isinstance(_quality,  Unset):
            quality = UNSET
        else:
            quality = DeviceTeleopCustomStreamConfigurationQuality(_quality)




        mouse_events_target_stream = d.pop("mouseEventsTargetStream", UNSET)

        button_color = d.pop("buttonColor", UNSET)

        button_label = d.pop("buttonLabel", UNSET)

        bitrate = d.pop("bitrate", UNSET)

        disable_adaptive_quality = d.pop("disableAdaptiveQuality", UNSET)

        joy_frequency = d.pop("joyFrequency", UNSET)

        joy_disable_button_mapping = d.pop("joyDisableButtonMapping", UNSET)

        device_teleop_custom_stream_configuration = cls(
            name=name,
            rtc_stream_type=rtc_stream_type,
            mode=mode,
            label=label,
            value_stream_name=value_stream_name,
            labels=labels,
            encode_video=encode_video,
            overlay_clock=overlay_clock,
            min_=min_,
            max_=max_,
            default_value=default_value,
            step=step,
            numeric_control_visualization=numeric_control_visualization,
            quality=quality,
            mouse_events_target_stream=mouse_events_target_stream,
            button_color=button_color,
            button_label=button_label,
            bitrate=bitrate,
            disable_adaptive_quality=disable_adaptive_quality,
            joy_frequency=joy_frequency,
            joy_disable_button_mapping=joy_disable_button_mapping,
        )

        device_teleop_custom_stream_configuration.additional_properties = d
        return device_teleop_custom_stream_configuration

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
