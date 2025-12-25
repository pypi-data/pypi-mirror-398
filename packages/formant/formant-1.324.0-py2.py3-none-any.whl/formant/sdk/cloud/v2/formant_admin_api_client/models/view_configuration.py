from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr

from ..models.view_configuration_type import ViewConfigurationType

if TYPE_CHECKING:
  from ..models.bitset_view_configuration import BitsetViewConfiguration
  from ..models.image_view_configuration import ImageViewConfiguration
  from ..models.localization_view_configuration import \
      LocalizationViewConfiguration
  from ..models.location_view_configuration import LocationViewConfiguration
  from ..models.numeric_view_configuration import NumericViewConfiguration
  from ..models.point_cloud_view_configuration import \
      PointCloudViewConfiguration
  from ..models.transform_tree_view_configuration import \
      TransformTreeViewConfiguration




T = TypeVar("T", bound="ViewConfiguration")

@attr.s(auto_attribs=True)
class ViewConfiguration:
    """
    Attributes:
        stream_name (str):
        type (ViewConfigurationType):
        configuration (Union['BitsetViewConfiguration', 'ImageViewConfiguration', 'LocalizationViewConfiguration',
            'LocationViewConfiguration', 'NumericViewConfiguration', 'PointCloudViewConfiguration',
            'TransformTreeViewConfiguration']):
    """

    stream_name: str
    type: ViewConfigurationType
    configuration: Union['BitsetViewConfiguration', 'ImageViewConfiguration', 'LocalizationViewConfiguration', 'LocationViewConfiguration', 'NumericViewConfiguration', 'PointCloudViewConfiguration', 'TransformTreeViewConfiguration']
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        from ..models.bitset_view_configuration import BitsetViewConfiguration
        from ..models.image_view_configuration import ImageViewConfiguration
        from ..models.localization_view_configuration import \
            LocalizationViewConfiguration
        from ..models.location_view_configuration import \
            LocationViewConfiguration
        from ..models.numeric_view_configuration import \
            NumericViewConfiguration
        from ..models.point_cloud_view_configuration import \
            PointCloudViewConfiguration
        stream_name = self.stream_name
        type = self.type.value

        configuration: Dict[str, Any]

        if isinstance(self.configuration, BitsetViewConfiguration):
            configuration = self.configuration.to_dict()

        elif isinstance(self.configuration, ImageViewConfiguration):
            configuration = self.configuration.to_dict()

        elif isinstance(self.configuration, LocationViewConfiguration):
            configuration = self.configuration.to_dict()

        elif isinstance(self.configuration, NumericViewConfiguration):
            configuration = self.configuration.to_dict()

        elif isinstance(self.configuration, NumericViewConfiguration):
            configuration = self.configuration.to_dict()

        elif isinstance(self.configuration, NumericViewConfiguration):
            configuration = self.configuration.to_dict()

        elif isinstance(self.configuration, LocalizationViewConfiguration):
            configuration = self.configuration.to_dict()

        elif isinstance(self.configuration, PointCloudViewConfiguration):
            configuration = self.configuration.to_dict()

        else:
            configuration = self.configuration.to_dict()




        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "streamName": stream_name,
            "type": type,
            "configuration": configuration,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.bitset_view_configuration import BitsetViewConfiguration
        from ..models.image_view_configuration import ImageViewConfiguration
        from ..models.localization_view_configuration import \
            LocalizationViewConfiguration
        from ..models.location_view_configuration import \
            LocationViewConfiguration
        from ..models.numeric_view_configuration import \
            NumericViewConfiguration
        from ..models.point_cloud_view_configuration import \
            PointCloudViewConfiguration
        from ..models.transform_tree_view_configuration import \
            TransformTreeViewConfiguration
        d = src_dict.copy()
        stream_name = d.pop("streamName")

        type = ViewConfigurationType(d.pop("type"))




        def _parse_configuration(data: object) -> Union['BitsetViewConfiguration', 'ImageViewConfiguration', 'LocalizationViewConfiguration', 'LocationViewConfiguration', 'NumericViewConfiguration', 'PointCloudViewConfiguration', 'TransformTreeViewConfiguration']:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                configuration_type_0 = BitsetViewConfiguration.from_dict(data)



                return configuration_type_0
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                configuration_type_1 = ImageViewConfiguration.from_dict(data)



                return configuration_type_1
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                configuration_type_2 = LocationViewConfiguration.from_dict(data)



                return configuration_type_2
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                configuration_type_3 = NumericViewConfiguration.from_dict(data)



                return configuration_type_3
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                configuration_type_4 = NumericViewConfiguration.from_dict(data)



                return configuration_type_4
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                configuration_type_5 = NumericViewConfiguration.from_dict(data)



                return configuration_type_5
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                configuration_type_6 = LocalizationViewConfiguration.from_dict(data)



                return configuration_type_6
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                configuration_type_7 = PointCloudViewConfiguration.from_dict(data)



                return configuration_type_7
            except: # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            configuration_type_8 = TransformTreeViewConfiguration.from_dict(data)



            return configuration_type_8

        configuration = _parse_configuration(d.pop("configuration"))


        view_configuration = cls(
            stream_name=stream_name,
            type=type,
            configuration=configuration,
        )

        view_configuration.additional_properties = d
        return view_configuration

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
