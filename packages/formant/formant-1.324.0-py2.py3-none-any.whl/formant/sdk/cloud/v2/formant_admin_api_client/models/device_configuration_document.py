from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union, cast

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.adapter_configuration import AdapterConfiguration
  from ..models.device_application_configuration import \
      DeviceApplicationConfiguration
  from ..models.device_blob_data import DeviceBlobData
  from ..models.device_configuration_document_tags import \
      DeviceConfigurationDocumentTags
  from ..models.device_diagnostics_configuration import \
      DeviceDiagnosticsConfiguration
  from ..models.device_port_forwarding_configuration import \
      DevicePortForwardingConfiguration
  from ..models.device_realtime_configuration import \
      DeviceRealtimeConfiguration
  from ..models.device_resources_configuration import \
      DeviceResourcesConfiguration
  from ..models.device_telemetry_configuration import \
      DeviceTelemetryConfiguration
  from ..models.device_teleop_configuration import DeviceTeleopConfiguration
  from ..models.rtc_info import RtcInfo




T = TypeVar("T", bound="DeviceConfigurationDocument")

@attr.s(auto_attribs=True)
class DeviceConfigurationDocument:
    """
    Attributes:
        tags (Union[Unset, DeviceConfigurationDocumentTags]):
        resources (Union[Unset, DeviceResourcesConfiguration]):
        telemetry (Union[Unset, DeviceTelemetryConfiguration]):
        realtime (Union[Unset, DeviceRealtimeConfiguration]):
        application (Union[Unset, DeviceApplicationConfiguration]):
        blob_data (Union[Unset, DeviceBlobData]):
        terminal_access (Union[Unset, None, bool]):
        teleop (Union[Unset, DeviceTeleopConfiguration]):
        port_forwarding (Union[Unset, DevicePortForwardingConfiguration]):
        diagnostics (Union[Unset, DeviceDiagnosticsConfiguration]):
        urdf_files (Union[Unset, List[str]]):
        adapters (Union[Unset, List['AdapterConfiguration']]):
        rtc_info (Union[Unset, RtcInfo]):
    """

    tags: Union[Unset, 'DeviceConfigurationDocumentTags'] = UNSET
    resources: Union[Unset, 'DeviceResourcesConfiguration'] = UNSET
    telemetry: Union[Unset, 'DeviceTelemetryConfiguration'] = UNSET
    realtime: Union[Unset, 'DeviceRealtimeConfiguration'] = UNSET
    application: Union[Unset, 'DeviceApplicationConfiguration'] = UNSET
    blob_data: Union[Unset, 'DeviceBlobData'] = UNSET
    terminal_access: Union[Unset, None, bool] = UNSET
    teleop: Union[Unset, 'DeviceTeleopConfiguration'] = UNSET
    port_forwarding: Union[Unset, 'DevicePortForwardingConfiguration'] = UNSET
    diagnostics: Union[Unset, 'DeviceDiagnosticsConfiguration'] = UNSET
    urdf_files: Union[Unset, List[str]] = UNSET
    adapters: Union[Unset, List['AdapterConfiguration']] = UNSET
    rtc_info: Union[Unset, 'RtcInfo'] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        tags: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.tags, Unset):
            tags = self.tags.to_dict()

        resources: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.resources, Unset):
            resources = self.resources.to_dict()

        telemetry: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.telemetry, Unset):
            telemetry = self.telemetry.to_dict()

        realtime: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.realtime, Unset):
            realtime = self.realtime.to_dict()

        application: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.application, Unset):
            application = self.application.to_dict()

        blob_data: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.blob_data, Unset):
            blob_data = self.blob_data.to_dict()

        terminal_access = self.terminal_access
        teleop: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.teleop, Unset):
            teleop = self.teleop.to_dict()

        port_forwarding: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.port_forwarding, Unset):
            port_forwarding = self.port_forwarding.to_dict()

        diagnostics: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.diagnostics, Unset):
            diagnostics = self.diagnostics.to_dict()

        urdf_files: Union[Unset, List[str]] = UNSET
        if not isinstance(self.urdf_files, Unset):
            urdf_files = self.urdf_files




        adapters: Union[Unset, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.adapters, Unset):
            adapters = []
            for adapters_item_data in self.adapters:
                adapters_item = adapters_item_data.to_dict()

                adapters.append(adapters_item)




        rtc_info: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.rtc_info, Unset):
            rtc_info = self.rtc_info.to_dict()


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if tags is not UNSET:
            field_dict["tags"] = tags
        if resources is not UNSET:
            field_dict["resources"] = resources
        if telemetry is not UNSET:
            field_dict["telemetry"] = telemetry
        if realtime is not UNSET:
            field_dict["realtime"] = realtime
        if application is not UNSET:
            field_dict["application"] = application
        if blob_data is not UNSET:
            field_dict["blobData"] = blob_data
        if terminal_access is not UNSET:
            field_dict["terminalAccess"] = terminal_access
        if teleop is not UNSET:
            field_dict["teleop"] = teleop
        if port_forwarding is not UNSET:
            field_dict["portForwarding"] = port_forwarding
        if diagnostics is not UNSET:
            field_dict["diagnostics"] = diagnostics
        if urdf_files is not UNSET:
            field_dict["urdfFiles"] = urdf_files
        if adapters is not UNSET:
            field_dict["adapters"] = adapters
        if rtc_info is not UNSET:
            field_dict["rtcInfo"] = rtc_info

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.adapter_configuration import AdapterConfiguration
        from ..models.device_application_configuration import \
            DeviceApplicationConfiguration
        from ..models.device_blob_data import DeviceBlobData
        from ..models.device_configuration_document_tags import \
            DeviceConfigurationDocumentTags
        from ..models.device_diagnostics_configuration import \
            DeviceDiagnosticsConfiguration
        from ..models.device_port_forwarding_configuration import \
            DevicePortForwardingConfiguration
        from ..models.device_realtime_configuration import \
            DeviceRealtimeConfiguration
        from ..models.device_resources_configuration import \
            DeviceResourcesConfiguration
        from ..models.device_telemetry_configuration import \
            DeviceTelemetryConfiguration
        from ..models.device_teleop_configuration import \
            DeviceTeleopConfiguration
        from ..models.rtc_info import RtcInfo
        d = src_dict.copy()
        _tags = d.pop("tags", UNSET)
        tags: Union[Unset, DeviceConfigurationDocumentTags]
        if isinstance(_tags,  Unset):
            tags = UNSET
        else:
            tags = DeviceConfigurationDocumentTags.from_dict(_tags)




        _resources = d.pop("resources", UNSET)
        resources: Union[Unset, DeviceResourcesConfiguration]
        if isinstance(_resources,  Unset):
            resources = UNSET
        else:
            resources = DeviceResourcesConfiguration.from_dict(_resources)




        _telemetry = d.pop("telemetry", UNSET)
        telemetry: Union[Unset, DeviceTelemetryConfiguration]
        if isinstance(_telemetry,  Unset):
            telemetry = UNSET
        else:
            telemetry = DeviceTelemetryConfiguration.from_dict(_telemetry)




        _realtime = d.pop("realtime", UNSET)
        realtime: Union[Unset, DeviceRealtimeConfiguration]
        if isinstance(_realtime,  Unset):
            realtime = UNSET
        else:
            realtime = DeviceRealtimeConfiguration.from_dict(_realtime)




        _application = d.pop("application", UNSET)
        application: Union[Unset, DeviceApplicationConfiguration]
        if isinstance(_application,  Unset):
            application = UNSET
        else:
            application = DeviceApplicationConfiguration.from_dict(_application)




        _blob_data = d.pop("blobData", UNSET)
        blob_data: Union[Unset, DeviceBlobData]
        if isinstance(_blob_data,  Unset):
            blob_data = UNSET
        else:
            blob_data = DeviceBlobData.from_dict(_blob_data)




        terminal_access = d.pop("terminalAccess", UNSET)

        _teleop = d.pop("teleop", UNSET)
        teleop: Union[Unset, DeviceTeleopConfiguration]
        if isinstance(_teleop,  Unset):
            teleop = UNSET
        else:
            teleop = DeviceTeleopConfiguration.from_dict(_teleop)




        _port_forwarding = d.pop("portForwarding", UNSET)
        port_forwarding: Union[Unset, DevicePortForwardingConfiguration]
        if isinstance(_port_forwarding,  Unset):
            port_forwarding = UNSET
        else:
            port_forwarding = DevicePortForwardingConfiguration.from_dict(_port_forwarding)




        _diagnostics = d.pop("diagnostics", UNSET)
        diagnostics: Union[Unset, DeviceDiagnosticsConfiguration]
        if isinstance(_diagnostics,  Unset):
            diagnostics = UNSET
        else:
            diagnostics = DeviceDiagnosticsConfiguration.from_dict(_diagnostics)




        urdf_files = cast(List[str], d.pop("urdfFiles", UNSET))


        adapters = []
        _adapters = d.pop("adapters", UNSET)
        for adapters_item_data in (_adapters or []):
            adapters_item = AdapterConfiguration.from_dict(adapters_item_data)



            adapters.append(adapters_item)


        _rtc_info = d.pop("rtcInfo", UNSET)
        rtc_info: Union[Unset, RtcInfo]
        if isinstance(_rtc_info,  Unset):
            rtc_info = UNSET
        else:
            rtc_info = RtcInfo.from_dict(_rtc_info)




        device_configuration_document = cls(
            tags=tags,
            resources=resources,
            telemetry=telemetry,
            realtime=realtime,
            application=application,
            blob_data=blob_data,
            terminal_access=terminal_access,
            teleop=teleop,
            port_forwarding=port_forwarding,
            diagnostics=diagnostics,
            urdf_files=urdf_files,
            adapters=adapters,
            rtc_info=rtc_info,
        )

        device_configuration_document.additional_properties = d
        return device_configuration_document

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
