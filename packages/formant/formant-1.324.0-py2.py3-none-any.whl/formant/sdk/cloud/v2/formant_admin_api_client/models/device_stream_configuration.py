from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr

from ..models.device_stream_configuration_quality import \
    DeviceStreamConfigurationQuality
from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.device_stream_configuration_tags import \
      DeviceStreamConfigurationTags
  from ..models.device_stream_custom_configuration import \
      DeviceStreamCustomConfiguration
  from ..models.device_stream_directory_watch_configuration import \
      DeviceStreamDirectoryWatchConfiguration
  from ..models.device_stream_file_tail_configuration import \
      DeviceStreamFileTailConfiguration
  from ..models.device_stream_hardware_configuration import \
      DeviceStreamHardwareConfiguration
  from ..models.device_stream_ros_localization_configuration import \
      DeviceStreamRosLocalizationConfiguration
  from ..models.device_stream_ros_topic_configuration import \
      DeviceStreamRosTopicConfiguration
  from ..models.device_stream_ros_transform_tree_configuration import \
      DeviceStreamRosTransformTreeConfiguration
  from ..models.device_stream_transform_configuration import \
      DeviceStreamTransformConfiguration
  from ..models.validation_configuration import ValidationConfiguration




T = TypeVar("T", bound="DeviceStreamConfiguration")

@attr.s(auto_attribs=True)
class DeviceStreamConfiguration:
    """
    Attributes:
        name (str):
        configuration (Union['DeviceStreamCustomConfiguration', 'DeviceStreamDirectoryWatchConfiguration',
            'DeviceStreamFileTailConfiguration', 'DeviceStreamHardwareConfiguration',
            'DeviceStreamRosLocalizationConfiguration', 'DeviceStreamRosTopicConfiguration',
            'DeviceStreamRosTransformTreeConfiguration']):
        tags (Union[Unset, DeviceStreamConfigurationTags]):
        throttle_hz (Union[Unset, None, float]):
        disabled (Union[Unset, None, bool]):
        on_demand (Union[Unset, None, bool]):
        validation (Union[Unset, None, ValidationConfiguration]):
        transform (Union[Unset, None, DeviceStreamTransformConfiguration]):
        quality (Union[Unset, DeviceStreamConfigurationQuality]):
    """

    name: str
    configuration: Union['DeviceStreamCustomConfiguration', 'DeviceStreamDirectoryWatchConfiguration', 'DeviceStreamFileTailConfiguration', 'DeviceStreamHardwareConfiguration', 'DeviceStreamRosLocalizationConfiguration', 'DeviceStreamRosTopicConfiguration', 'DeviceStreamRosTransformTreeConfiguration']
    tags: Union[Unset, 'DeviceStreamConfigurationTags'] = UNSET
    throttle_hz: Union[Unset, None, float] = UNSET
    disabled: Union[Unset, None, bool] = UNSET
    on_demand: Union[Unset, None, bool] = UNSET
    validation: Union[Unset, None, 'ValidationConfiguration'] = UNSET
    transform: Union[Unset, None, 'DeviceStreamTransformConfiguration'] = UNSET
    quality: Union[Unset, DeviceStreamConfigurationQuality] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        from ..models.device_stream_custom_configuration import \
            DeviceStreamCustomConfiguration
        from ..models.device_stream_directory_watch_configuration import \
            DeviceStreamDirectoryWatchConfiguration
        from ..models.device_stream_hardware_configuration import \
            DeviceStreamHardwareConfiguration
        from ..models.device_stream_ros_localization_configuration import \
            DeviceStreamRosLocalizationConfiguration
        from ..models.device_stream_ros_topic_configuration import \
            DeviceStreamRosTopicConfiguration
        from ..models.device_stream_ros_transform_tree_configuration import \
            DeviceStreamRosTransformTreeConfiguration
        name = self.name
        configuration: Dict[str, Any]

        if isinstance(self.configuration, DeviceStreamHardwareConfiguration):
            configuration = self.configuration.to_dict()

        elif isinstance(self.configuration, DeviceStreamCustomConfiguration):
            configuration = self.configuration.to_dict()

        elif isinstance(self.configuration, DeviceStreamRosTopicConfiguration):
            configuration = self.configuration.to_dict()

        elif isinstance(self.configuration, DeviceStreamRosLocalizationConfiguration):
            configuration = self.configuration.to_dict()

        elif isinstance(self.configuration, DeviceStreamRosTransformTreeConfiguration):
            configuration = self.configuration.to_dict()

        elif isinstance(self.configuration, DeviceStreamDirectoryWatchConfiguration):
            configuration = self.configuration.to_dict()

        else:
            configuration = self.configuration.to_dict()



        tags: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.tags, Unset):
            tags = self.tags.to_dict()

        throttle_hz = self.throttle_hz
        disabled = self.disabled
        on_demand = self.on_demand
        validation: Union[Unset, None, Dict[str, Any]] = UNSET
        if not isinstance(self.validation, Unset):
            validation = self.validation.to_dict() if self.validation else None

        transform: Union[Unset, None, Dict[str, Any]] = UNSET
        if not isinstance(self.transform, Unset):
            transform = self.transform.to_dict() if self.transform else None

        quality: Union[Unset, str] = UNSET
        if not isinstance(self.quality, Unset):
            quality = self.quality.value


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "name": name,
            "configuration": configuration,
        })
        if tags is not UNSET:
            field_dict["tags"] = tags
        if throttle_hz is not UNSET:
            field_dict["throttleHz"] = throttle_hz
        if disabled is not UNSET:
            field_dict["disabled"] = disabled
        if on_demand is not UNSET:
            field_dict["onDemand"] = on_demand
        if validation is not UNSET:
            field_dict["validation"] = validation
        if transform is not UNSET:
            field_dict["transform"] = transform
        if quality is not UNSET:
            field_dict["quality"] = quality

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.device_stream_configuration_tags import \
            DeviceStreamConfigurationTags
        from ..models.device_stream_custom_configuration import \
            DeviceStreamCustomConfiguration
        from ..models.device_stream_directory_watch_configuration import \
            DeviceStreamDirectoryWatchConfiguration
        from ..models.device_stream_file_tail_configuration import \
            DeviceStreamFileTailConfiguration
        from ..models.device_stream_hardware_configuration import \
            DeviceStreamHardwareConfiguration
        from ..models.device_stream_ros_localization_configuration import \
            DeviceStreamRosLocalizationConfiguration
        from ..models.device_stream_ros_topic_configuration import \
            DeviceStreamRosTopicConfiguration
        from ..models.device_stream_ros_transform_tree_configuration import \
            DeviceStreamRosTransformTreeConfiguration
        from ..models.device_stream_transform_configuration import \
            DeviceStreamTransformConfiguration
        from ..models.validation_configuration import ValidationConfiguration
        d = src_dict.copy()
        name = d.pop("name")

        def _parse_configuration(data: object) -> Union['DeviceStreamCustomConfiguration', 'DeviceStreamDirectoryWatchConfiguration', 'DeviceStreamFileTailConfiguration', 'DeviceStreamHardwareConfiguration', 'DeviceStreamRosLocalizationConfiguration', 'DeviceStreamRosTopicConfiguration', 'DeviceStreamRosTransformTreeConfiguration']:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                configuration_type_0 = DeviceStreamHardwareConfiguration.from_dict(data)



                return configuration_type_0
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                configuration_type_1 = DeviceStreamCustomConfiguration.from_dict(data)



                return configuration_type_1
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                configuration_type_2 = DeviceStreamRosTopicConfiguration.from_dict(data)



                return configuration_type_2
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                configuration_type_3 = DeviceStreamRosLocalizationConfiguration.from_dict(data)



                return configuration_type_3
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                configuration_type_4 = DeviceStreamRosTransformTreeConfiguration.from_dict(data)



                return configuration_type_4
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                configuration_type_5 = DeviceStreamDirectoryWatchConfiguration.from_dict(data)



                return configuration_type_5
            except: # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            configuration_type_6 = DeviceStreamFileTailConfiguration.from_dict(data)



            return configuration_type_6

        configuration = _parse_configuration(d.pop("configuration"))


        _tags = d.pop("tags", UNSET)
        tags: Union[Unset, DeviceStreamConfigurationTags]
        if isinstance(_tags,  Unset):
            tags = UNSET
        else:
            tags = DeviceStreamConfigurationTags.from_dict(_tags)




        throttle_hz = d.pop("throttleHz", UNSET)

        disabled = d.pop("disabled", UNSET)

        on_demand = d.pop("onDemand", UNSET)

        _validation = d.pop("validation", UNSET)
        validation: Union[Unset, None, ValidationConfiguration]
        if _validation is None:
            validation = None
        elif isinstance(_validation,  Unset):
            validation = UNSET
        else:
            validation = ValidationConfiguration.from_dict(_validation)




        _transform = d.pop("transform", UNSET)
        transform: Union[Unset, None, DeviceStreamTransformConfiguration]
        if _transform is None:
            transform = None
        elif isinstance(_transform,  Unset):
            transform = UNSET
        else:
            transform = DeviceStreamTransformConfiguration.from_dict(_transform)




        _quality = d.pop("quality", UNSET)
        quality: Union[Unset, DeviceStreamConfigurationQuality]
        if isinstance(_quality,  Unset):
            quality = UNSET
        else:
            quality = DeviceStreamConfigurationQuality(_quality)




        device_stream_configuration = cls(
            name=name,
            configuration=configuration,
            tags=tags,
            throttle_hz=throttle_hz,
            disabled=disabled,
            on_demand=on_demand,
            validation=validation,
            transform=transform,
            quality=quality,
        )

        device_stream_configuration.additional_properties = d
        return device_stream_configuration

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
