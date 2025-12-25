from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union, cast

import attr

from ..models.layout_module_configuration_module_type import \
    LayoutModuleConfigurationModuleType
from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.location_module_parameters import LocationModuleParameters




T = TypeVar("T", bound="LayoutModuleConfiguration")

@attr.s(auto_attribs=True)
class LayoutModuleConfiguration:
    """
    Attributes:
        module_type (Union[Unset, LayoutModuleConfigurationModuleType]):
        parameters (Union[Unset, LocationModuleParameters]):
        custom_name (Union[Unset, str]):
        custom_visualization_url (Union[Unset, str]):
        debug (Union[Unset, bool]):
        show_only_current_values (Union[Unset, bool]):
        streams (Union[Unset, List[str]]):
        visible (Union[Unset, bool]):
    """

    module_type: Union[Unset, LayoutModuleConfigurationModuleType] = UNSET
    parameters: Union[Unset, 'LocationModuleParameters'] = UNSET
    custom_name: Union[Unset, str] = UNSET
    custom_visualization_url: Union[Unset, str] = UNSET
    debug: Union[Unset, bool] = UNSET
    show_only_current_values: Union[Unset, bool] = UNSET
    streams: Union[Unset, List[str]] = UNSET
    visible: Union[Unset, bool] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        module_type: Union[Unset, str] = UNSET
        if not isinstance(self.module_type, Unset):
            module_type = self.module_type.value

        parameters: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.parameters, Unset):
            parameters = self.parameters.to_dict()

        custom_name = self.custom_name
        custom_visualization_url = self.custom_visualization_url
        debug = self.debug
        show_only_current_values = self.show_only_current_values
        streams: Union[Unset, List[str]] = UNSET
        if not isinstance(self.streams, Unset):
            streams = self.streams




        visible = self.visible

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if module_type is not UNSET:
            field_dict["moduleType"] = module_type
        if parameters is not UNSET:
            field_dict["parameters"] = parameters
        if custom_name is not UNSET:
            field_dict["customName"] = custom_name
        if custom_visualization_url is not UNSET:
            field_dict["customVisualizationUrl"] = custom_visualization_url
        if debug is not UNSET:
            field_dict["debug"] = debug
        if show_only_current_values is not UNSET:
            field_dict["showOnlyCurrentValues"] = show_only_current_values
        if streams is not UNSET:
            field_dict["streams"] = streams
        if visible is not UNSET:
            field_dict["visible"] = visible

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.location_module_parameters import \
            LocationModuleParameters
        d = src_dict.copy()
        _module_type = d.pop("moduleType", UNSET)
        module_type: Union[Unset, LayoutModuleConfigurationModuleType]
        if isinstance(_module_type,  Unset):
            module_type = UNSET
        else:
            module_type = LayoutModuleConfigurationModuleType(_module_type)




        _parameters = d.pop("parameters", UNSET)
        parameters: Union[Unset, LocationModuleParameters]
        if isinstance(_parameters,  Unset):
            parameters = UNSET
        else:
            parameters = LocationModuleParameters.from_dict(_parameters)




        custom_name = d.pop("customName", UNSET)

        custom_visualization_url = d.pop("customVisualizationUrl", UNSET)

        debug = d.pop("debug", UNSET)

        show_only_current_values = d.pop("showOnlyCurrentValues", UNSET)

        streams = cast(List[str], d.pop("streams", UNSET))


        visible = d.pop("visible", UNSET)

        layout_module_configuration = cls(
            module_type=module_type,
            parameters=parameters,
            custom_name=custom_name,
            custom_visualization_url=custom_visualization_url,
            debug=debug,
            show_only_current_values=show_only_current_values,
            streams=streams,
            visible=visible,
        )

        layout_module_configuration.additional_properties = d
        return layout_module_configuration

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
