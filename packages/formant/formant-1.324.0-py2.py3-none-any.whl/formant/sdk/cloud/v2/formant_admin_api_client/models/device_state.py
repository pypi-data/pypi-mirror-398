from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.command_progress import CommandProgress
  from ..models.device_reported_configuration_state import \
      DeviceReportedConfigurationState
  from ..models.device_ros_state import DeviceRosState
  from ..models.device_state_env import DeviceStateEnv
  from ..models.hw_info import HwInfo
  from ..models.on_demand_state import OnDemandState




T = TypeVar("T", bound="DeviceState")

@attr.s(auto_attribs=True)
class DeviceState:
    """
    Attributes:
        agent_version (Union[Unset, None, str]):
        reported_configuration (Union[Unset, None, DeviceReportedConfigurationState]):
        hw_info (Union[Unset, None, HwInfo]):
        ros (Union[Unset, None, DeviceRosState]):
        env (Union[Unset, None, DeviceStateEnv]):
        ota_enabled (Union[Unset, None, bool]):
        on_demand (Union[Unset, None, OnDemandState]):
        command_progress (Union[Unset, None, List['CommandProgress']]):
        version (Union[Unset, None, str]):
    """

    agent_version: Union[Unset, None, str] = UNSET
    reported_configuration: Union[Unset, None, 'DeviceReportedConfigurationState'] = UNSET
    hw_info: Union[Unset, None, 'HwInfo'] = UNSET
    ros: Union[Unset, None, 'DeviceRosState'] = UNSET
    env: Union[Unset, None, 'DeviceStateEnv'] = UNSET
    ota_enabled: Union[Unset, None, bool] = UNSET
    on_demand: Union[Unset, None, 'OnDemandState'] = UNSET
    command_progress: Union[Unset, None, List['CommandProgress']] = UNSET
    version: Union[Unset, None, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        agent_version = self.agent_version
        reported_configuration: Union[Unset, None, Dict[str, Any]] = UNSET
        if not isinstance(self.reported_configuration, Unset):
            reported_configuration = self.reported_configuration.to_dict() if self.reported_configuration else None

        hw_info: Union[Unset, None, Dict[str, Any]] = UNSET
        if not isinstance(self.hw_info, Unset):
            hw_info = self.hw_info.to_dict() if self.hw_info else None

        ros: Union[Unset, None, Dict[str, Any]] = UNSET
        if not isinstance(self.ros, Unset):
            ros = self.ros.to_dict() if self.ros else None

        env: Union[Unset, None, Dict[str, Any]] = UNSET
        if not isinstance(self.env, Unset):
            env = self.env.to_dict() if self.env else None

        ota_enabled = self.ota_enabled
        on_demand: Union[Unset, None, Dict[str, Any]] = UNSET
        if not isinstance(self.on_demand, Unset):
            on_demand = self.on_demand.to_dict() if self.on_demand else None

        command_progress: Union[Unset, None, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.command_progress, Unset):
            if self.command_progress is None:
                command_progress = None
            else:
                command_progress = []
                for command_progress_item_data in self.command_progress:
                    command_progress_item = command_progress_item_data.to_dict()

                    command_progress.append(command_progress_item)




        version = self.version

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if agent_version is not UNSET:
            field_dict["agentVersion"] = agent_version
        if reported_configuration is not UNSET:
            field_dict["reportedConfiguration"] = reported_configuration
        if hw_info is not UNSET:
            field_dict["hwInfo"] = hw_info
        if ros is not UNSET:
            field_dict["ros"] = ros
        if env is not UNSET:
            field_dict["env"] = env
        if ota_enabled is not UNSET:
            field_dict["otaEnabled"] = ota_enabled
        if on_demand is not UNSET:
            field_dict["onDemand"] = on_demand
        if command_progress is not UNSET:
            field_dict["commandProgress"] = command_progress
        if version is not UNSET:
            field_dict["version"] = version

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.command_progress import CommandProgress
        from ..models.device_reported_configuration_state import \
            DeviceReportedConfigurationState
        from ..models.device_ros_state import DeviceRosState
        from ..models.device_state_env import DeviceStateEnv
        from ..models.hw_info import HwInfo
        from ..models.on_demand_state import OnDemandState
        d = src_dict.copy()
        agent_version = d.pop("agentVersion", UNSET)

        _reported_configuration = d.pop("reportedConfiguration", UNSET)
        reported_configuration: Union[Unset, None, DeviceReportedConfigurationState]
        if _reported_configuration is None:
            reported_configuration = None
        elif isinstance(_reported_configuration,  Unset):
            reported_configuration = UNSET
        else:
            reported_configuration = DeviceReportedConfigurationState.from_dict(_reported_configuration)




        _hw_info = d.pop("hwInfo", UNSET)
        hw_info: Union[Unset, None, HwInfo]
        if _hw_info is None:
            hw_info = None
        elif isinstance(_hw_info,  Unset):
            hw_info = UNSET
        else:
            hw_info = HwInfo.from_dict(_hw_info)




        _ros = d.pop("ros", UNSET)
        ros: Union[Unset, None, DeviceRosState]
        if _ros is None:
            ros = None
        elif isinstance(_ros,  Unset):
            ros = UNSET
        else:
            ros = DeviceRosState.from_dict(_ros)




        _env = d.pop("env", UNSET)
        env: Union[Unset, None, DeviceStateEnv]
        if _env is None:
            env = None
        elif isinstance(_env,  Unset):
            env = UNSET
        else:
            env = DeviceStateEnv.from_dict(_env)




        ota_enabled = d.pop("otaEnabled", UNSET)

        _on_demand = d.pop("onDemand", UNSET)
        on_demand: Union[Unset, None, OnDemandState]
        if _on_demand is None:
            on_demand = None
        elif isinstance(_on_demand,  Unset):
            on_demand = UNSET
        else:
            on_demand = OnDemandState.from_dict(_on_demand)




        command_progress = []
        _command_progress = d.pop("commandProgress", UNSET)
        for command_progress_item_data in (_command_progress or []):
            command_progress_item = CommandProgress.from_dict(command_progress_item_data)



            command_progress.append(command_progress_item)


        version = d.pop("version", UNSET)

        device_state = cls(
            agent_version=agent_version,
            reported_configuration=reported_configuration,
            hw_info=hw_info,
            ros=ros,
            env=env,
            ota_enabled=ota_enabled,
            on_demand=on_demand,
            command_progress=command_progress,
            version=version,
        )

        device_state.additional_properties = d
        return device_state

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
