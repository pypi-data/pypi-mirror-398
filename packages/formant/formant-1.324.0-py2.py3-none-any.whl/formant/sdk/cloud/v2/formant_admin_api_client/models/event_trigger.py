import datetime
from typing import (TYPE_CHECKING, Any, Dict, List, Optional, Type, TypeVar,
                    Union)

import attr
from dateutil.parser import isoparse

from ..models.event_trigger_event_type import EventTriggerEventType
from ..models.event_trigger_severity import EventTriggerSeverity
from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.auto_resolve_event_trigger_condition import \
      AutoResolveEventTriggerCondition
  from ..models.base_event_trigger_predicate import BaseEventTriggerPredicate
  from ..models.battery_event_trigger_condition import \
      BatteryEventTriggerCondition
  from ..models.bitset_event_trigger_condition import \
      BitsetEventTriggerCondition
  from ..models.event_trigger_command import EventTriggerCommand
  from ..models.event_trigger_sms_tags import EventTriggerSmsTags
  from ..models.event_trigger_tags import EventTriggerTags
  from ..models.event_trigger_workflow import EventTriggerWorkflow
  from ..models.forwarding_configuration import ForwardingConfiguration
  from ..models.json_event_trigger_condition import JsonEventTriggerCondition
  from ..models.numeric_set_event_trigger_condition import \
      NumericSetEventTriggerCondition
  from ..models.presence_event_trigger_condition import \
      PresenceEventTriggerCondition
  from ..models.regex_event_trigger_condition import RegexEventTriggerCondition
  from ..models.scope_filter import ScopeFilter
  from ..models.stateful_trigger_configuration import \
      StatefulTriggerConfiguration
  from ..models.theopolis_configuration import TheopolisConfiguration
  from ..models.threshold_event_trigger_condition import \
      ThresholdEventTriggerCondition
  from ..models.triggered_configuration import TriggeredConfiguration




T = TypeVar("T", bound="EventTrigger")

@attr.s(auto_attribs=True)
class EventTrigger:
    """
    Attributes:
        event_type (EventTriggerEventType):
        message (str):
        interval (int):
        severity (EventTriggerSeverity):
        commands (List['EventTriggerCommand']):
        notification_enabled (bool):
        organization_id (Union[Unset, str]):
        condition (Union['AutoResolveEventTriggerCondition', 'BatteryEventTriggerCondition',
            'BitsetEventTriggerCondition', 'JsonEventTriggerCondition', 'NumericSetEventTriggerCondition',
            'PresenceEventTriggerCondition', 'RegexEventTriggerCondition', 'ThresholdEventTriggerCondition', None]):
        exit_condition (Union['AutoResolveEventTriggerCondition', 'BatteryEventTriggerCondition',
            'BitsetEventTriggerCondition', 'JsonEventTriggerCondition', 'NumericSetEventTriggerCondition',
            'PresenceEventTriggerCondition', 'RegexEventTriggerCondition', 'ThresholdEventTriggerCondition', None]):
        predicate (Union['BaseEventTriggerPredicate', None]):
        enabled (Union[Unset, bool]):
        format_ (Union[Unset, str]):
        triggered_configuration (Optional[TriggeredConfiguration]):
        sms_tags (Union[Unset, EventTriggerSmsTags]):
        device_scope (Union[Unset, None, ScopeFilter]):
        workflows (Optional[List['EventTriggerWorkflow']]):
        last_triggered_time (Union[Unset, None, datetime.datetime]):
        event_trigger_group_id (Union[Unset, None, str]):
        stateful_trigger_configuration (Optional[StatefulTriggerConfiguration]):
        is_stateful (Union[Unset, bool]):
        forwarding_configuration (Optional[ForwardingConfiguration]):
        sets_device_color (Union[Unset, bool]):
        theopolis (Union[Unset, None, TheopolisConfiguration]):
        id (Union[Unset, str]):
        created_at (Union[Unset, datetime.datetime]):
        updated_at (Union[Unset, datetime.datetime]):
        tags (Union[Unset, EventTriggerTags]):
    """

    event_type: EventTriggerEventType
    message: str
    interval: int
    severity: EventTriggerSeverity
    commands: List['EventTriggerCommand']
    notification_enabled: bool
    condition: Union['AutoResolveEventTriggerCondition', 'BatteryEventTriggerCondition', 'BitsetEventTriggerCondition', 'JsonEventTriggerCondition', 'NumericSetEventTriggerCondition', 'PresenceEventTriggerCondition', 'RegexEventTriggerCondition', 'ThresholdEventTriggerCondition', None]
    exit_condition: Union['AutoResolveEventTriggerCondition', 'BatteryEventTriggerCondition', 'BitsetEventTriggerCondition', 'JsonEventTriggerCondition', 'NumericSetEventTriggerCondition', 'PresenceEventTriggerCondition', 'RegexEventTriggerCondition', 'ThresholdEventTriggerCondition', None]
    predicate: Union['BaseEventTriggerPredicate', None]
    triggered_configuration: Optional['TriggeredConfiguration']
    workflows: Optional[List['EventTriggerWorkflow']]
    stateful_trigger_configuration: Optional['StatefulTriggerConfiguration']
    forwarding_configuration: Optional['ForwardingConfiguration']
    organization_id: Union[Unset, str] = UNSET
    enabled: Union[Unset, bool] = UNSET
    format_: Union[Unset, str] = UNSET
    sms_tags: Union[Unset, 'EventTriggerSmsTags'] = UNSET
    device_scope: Union[Unset, None, 'ScopeFilter'] = UNSET
    last_triggered_time: Union[Unset, None, datetime.datetime] = UNSET
    event_trigger_group_id: Union[Unset, None, str] = UNSET
    is_stateful: Union[Unset, bool] = UNSET
    sets_device_color: Union[Unset, bool] = UNSET
    theopolis: Union[Unset, None, 'TheopolisConfiguration'] = UNSET
    id: Union[Unset, str] = UNSET
    created_at: Union[Unset, datetime.datetime] = UNSET
    updated_at: Union[Unset, datetime.datetime] = UNSET
    tags: Union[Unset, 'EventTriggerTags'] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        from ..models.base_event_trigger_predicate import \
            BaseEventTriggerPredicate
        from ..models.battery_event_trigger_condition import \
            BatteryEventTriggerCondition
        from ..models.bitset_event_trigger_condition import \
            BitsetEventTriggerCondition
        from ..models.json_event_trigger_condition import \
            JsonEventTriggerCondition
        from ..models.numeric_set_event_trigger_condition import \
            NumericSetEventTriggerCondition
        from ..models.presence_event_trigger_condition import \
            PresenceEventTriggerCondition
        from ..models.regex_event_trigger_condition import \
            RegexEventTriggerCondition
        from ..models.threshold_event_trigger_condition import \
            ThresholdEventTriggerCondition
        event_type = self.event_type.value

        message = self.message
        interval = self.interval
        severity = self.severity.value

        commands = []
        for commands_item_data in self.commands:
            commands_item = commands_item_data.to_dict()

            commands.append(commands_item)




        notification_enabled = self.notification_enabled
        organization_id = self.organization_id
        condition: Union[Dict[str, Any], None]
        if self.condition is None:
            condition = None

        elif isinstance(self.condition, PresenceEventTriggerCondition):
            condition = self.condition.to_dict()

        elif isinstance(self.condition, ThresholdEventTriggerCondition):
            condition = self.condition.to_dict()

        elif isinstance(self.condition, RegexEventTriggerCondition):
            condition = self.condition.to_dict()

        elif isinstance(self.condition, BitsetEventTriggerCondition):
            condition = self.condition.to_dict()

        elif isinstance(self.condition, BatteryEventTriggerCondition):
            condition = self.condition.to_dict()

        elif isinstance(self.condition, NumericSetEventTriggerCondition):
            condition = self.condition.to_dict()

        elif isinstance(self.condition, JsonEventTriggerCondition):
            condition = self.condition.to_dict()

        else:
            condition = self.condition.to_dict()



        exit_condition: Union[Dict[str, Any], None]
        if self.exit_condition is None:
            exit_condition = None

        elif isinstance(self.exit_condition, PresenceEventTriggerCondition):
            exit_condition = self.exit_condition.to_dict()

        elif isinstance(self.exit_condition, ThresholdEventTriggerCondition):
            exit_condition = self.exit_condition.to_dict()

        elif isinstance(self.exit_condition, RegexEventTriggerCondition):
            exit_condition = self.exit_condition.to_dict()

        elif isinstance(self.exit_condition, BitsetEventTriggerCondition):
            exit_condition = self.exit_condition.to_dict()

        elif isinstance(self.exit_condition, BatteryEventTriggerCondition):
            exit_condition = self.exit_condition.to_dict()

        elif isinstance(self.exit_condition, NumericSetEventTriggerCondition):
            exit_condition = self.exit_condition.to_dict()

        elif isinstance(self.exit_condition, JsonEventTriggerCondition):
            exit_condition = self.exit_condition.to_dict()

        else:
            exit_condition = self.exit_condition.to_dict()



        predicate: Union[Dict[str, Any], None]
        if self.predicate is None:
            predicate = None

        elif isinstance(self.predicate, BaseEventTriggerPredicate):
            predicate = self.predicate.to_dict()

        elif isinstance(self.predicate, BaseEventTriggerPredicate):
            predicate = self.predicate.to_dict()

        elif isinstance(self.predicate, BaseEventTriggerPredicate):
            predicate = self.predicate.to_dict()

        elif isinstance(self.predicate, BaseEventTriggerPredicate):
            predicate = self.predicate.to_dict()

        elif isinstance(self.predicate, BaseEventTriggerPredicate):
            predicate = self.predicate.to_dict()

        elif isinstance(self.predicate, BaseEventTriggerPredicate):
            predicate = self.predicate.to_dict()

        elif isinstance(self.predicate, BaseEventTriggerPredicate):
            predicate = self.predicate.to_dict()

        elif isinstance(self.predicate, BaseEventTriggerPredicate):
            predicate = self.predicate.to_dict()

        elif isinstance(self.predicate, BaseEventTriggerPredicate):
            predicate = self.predicate.to_dict()

        elif isinstance(self.predicate, BaseEventTriggerPredicate):
            predicate = self.predicate.to_dict()

        elif isinstance(self.predicate, BaseEventTriggerPredicate):
            predicate = self.predicate.to_dict()

        elif isinstance(self.predicate, BaseEventTriggerPredicate):
            predicate = self.predicate.to_dict()

        elif isinstance(self.predicate, BaseEventTriggerPredicate):
            predicate = self.predicate.to_dict()

        elif isinstance(self.predicate, BaseEventTriggerPredicate):
            predicate = self.predicate.to_dict()

        elif isinstance(self.predicate, BaseEventTriggerPredicate):
            predicate = self.predicate.to_dict()

        elif isinstance(self.predicate, BaseEventTriggerPredicate):
            predicate = self.predicate.to_dict()

        else:
            predicate = self.predicate.to_dict()



        enabled = self.enabled
        format_ = self.format_
        triggered_configuration = self.triggered_configuration.to_dict() if self.triggered_configuration else None

        sms_tags: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.sms_tags, Unset):
            sms_tags = self.sms_tags.to_dict()

        device_scope: Union[Unset, None, Dict[str, Any]] = UNSET
        if not isinstance(self.device_scope, Unset):
            device_scope = self.device_scope.to_dict() if self.device_scope else None

        if self.workflows is None:
            workflows = None
        else:
            workflows = []
            for workflows_item_data in self.workflows:
                workflows_item = workflows_item_data.to_dict()

                workflows.append(workflows_item)




        last_triggered_time: Union[Unset, None, str] = UNSET
        if not isinstance(self.last_triggered_time, Unset):
            last_triggered_time = self.last_triggered_time.isoformat() if self.last_triggered_time else None

        event_trigger_group_id = self.event_trigger_group_id
        stateful_trigger_configuration = self.stateful_trigger_configuration.to_dict() if self.stateful_trigger_configuration else None

        is_stateful = self.is_stateful
        forwarding_configuration = self.forwarding_configuration.to_dict() if self.forwarding_configuration else None

        sets_device_color = self.sets_device_color
        theopolis: Union[Unset, None, Dict[str, Any]] = UNSET
        if not isinstance(self.theopolis, Unset):
            theopolis = self.theopolis.to_dict() if self.theopolis else None

        id = self.id
        created_at: Union[Unset, str] = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: Union[Unset, str] = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        tags: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.tags, Unset):
            tags = self.tags.to_dict()


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "eventType": event_type,
            "message": message,
            "interval": interval,
            "severity": severity,
            "commands": commands,
            "notificationEnabled": notification_enabled,
            "condition": condition,
            "exitCondition": exit_condition,
            "predicate": predicate,
            "triggeredConfiguration": triggered_configuration,
            "workflows": workflows,
            "statefulTriggerConfiguration": stateful_trigger_configuration,
            "forwardingConfiguration": forwarding_configuration,
        })
        if organization_id is not UNSET:
            field_dict["organizationId"] = organization_id
        if enabled is not UNSET:
            field_dict["enabled"] = enabled
        if format_ is not UNSET:
            field_dict["format"] = format_
        if sms_tags is not UNSET:
            field_dict["smsTags"] = sms_tags
        if device_scope is not UNSET:
            field_dict["deviceScope"] = device_scope
        if last_triggered_time is not UNSET:
            field_dict["lastTriggeredTime"] = last_triggered_time
        if event_trigger_group_id is not UNSET:
            field_dict["eventTriggerGroupId"] = event_trigger_group_id
        if is_stateful is not UNSET:
            field_dict["isStateful"] = is_stateful
        if sets_device_color is not UNSET:
            field_dict["setsDeviceColor"] = sets_device_color
        if theopolis is not UNSET:
            field_dict["theopolis"] = theopolis
        if id is not UNSET:
            field_dict["id"] = id
        if created_at is not UNSET:
            field_dict["createdAt"] = created_at
        if updated_at is not UNSET:
            field_dict["updatedAt"] = updated_at
        if tags is not UNSET:
            field_dict["tags"] = tags

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.auto_resolve_event_trigger_condition import \
            AutoResolveEventTriggerCondition
        from ..models.base_event_trigger_predicate import \
            BaseEventTriggerPredicate
        from ..models.battery_event_trigger_condition import \
            BatteryEventTriggerCondition
        from ..models.bitset_event_trigger_condition import \
            BitsetEventTriggerCondition
        from ..models.event_trigger_command import EventTriggerCommand
        from ..models.event_trigger_sms_tags import EventTriggerSmsTags
        from ..models.event_trigger_tags import EventTriggerTags
        from ..models.event_trigger_workflow import EventTriggerWorkflow
        from ..models.forwarding_configuration import ForwardingConfiguration
        from ..models.json_event_trigger_condition import \
            JsonEventTriggerCondition
        from ..models.numeric_set_event_trigger_condition import \
            NumericSetEventTriggerCondition
        from ..models.presence_event_trigger_condition import \
            PresenceEventTriggerCondition
        from ..models.regex_event_trigger_condition import \
            RegexEventTriggerCondition
        from ..models.scope_filter import ScopeFilter
        from ..models.stateful_trigger_configuration import \
            StatefulTriggerConfiguration
        from ..models.theopolis_configuration import TheopolisConfiguration
        from ..models.threshold_event_trigger_condition import \
            ThresholdEventTriggerCondition
        from ..models.triggered_configuration import TriggeredConfiguration
        d = src_dict.copy()
        event_type = EventTriggerEventType(d.pop("eventType"))




        message = d.pop("message")

        interval = d.pop("interval")

        severity = EventTriggerSeverity(d.pop("severity"))




        commands = []
        _commands = d.pop("commands")
        for commands_item_data in (_commands):
            commands_item = EventTriggerCommand.from_dict(commands_item_data)



            commands.append(commands_item)


        notification_enabled = d.pop("notificationEnabled")

        organization_id = d.pop("organizationId", UNSET)

        def _parse_condition(data: object) -> Union['AutoResolveEventTriggerCondition', 'BatteryEventTriggerCondition', 'BitsetEventTriggerCondition', 'JsonEventTriggerCondition', 'NumericSetEventTriggerCondition', 'PresenceEventTriggerCondition', 'RegexEventTriggerCondition', 'ThresholdEventTriggerCondition', None]:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                condition_type_0 = PresenceEventTriggerCondition.from_dict(data)



                return condition_type_0
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                condition_type_1 = ThresholdEventTriggerCondition.from_dict(data)



                return condition_type_1
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                condition_type_2 = RegexEventTriggerCondition.from_dict(data)



                return condition_type_2
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                condition_type_3 = BitsetEventTriggerCondition.from_dict(data)



                return condition_type_3
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                condition_type_4 = BatteryEventTriggerCondition.from_dict(data)



                return condition_type_4
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                condition_type_5 = NumericSetEventTriggerCondition.from_dict(data)



                return condition_type_5
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                condition_type_6 = JsonEventTriggerCondition.from_dict(data)



                return condition_type_6
            except: # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            condition_type_7 = AutoResolveEventTriggerCondition.from_dict(data)



            return condition_type_7

        condition = _parse_condition(d.pop("condition"))


        def _parse_exit_condition(data: object) -> Union['AutoResolveEventTriggerCondition', 'BatteryEventTriggerCondition', 'BitsetEventTriggerCondition', 'JsonEventTriggerCondition', 'NumericSetEventTriggerCondition', 'PresenceEventTriggerCondition', 'RegexEventTriggerCondition', 'ThresholdEventTriggerCondition', None]:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                exit_condition_type_0 = PresenceEventTriggerCondition.from_dict(data)



                return exit_condition_type_0
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                exit_condition_type_1 = ThresholdEventTriggerCondition.from_dict(data)



                return exit_condition_type_1
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                exit_condition_type_2 = RegexEventTriggerCondition.from_dict(data)



                return exit_condition_type_2
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                exit_condition_type_3 = BitsetEventTriggerCondition.from_dict(data)



                return exit_condition_type_3
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                exit_condition_type_4 = BatteryEventTriggerCondition.from_dict(data)



                return exit_condition_type_4
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                exit_condition_type_5 = NumericSetEventTriggerCondition.from_dict(data)



                return exit_condition_type_5
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                exit_condition_type_6 = JsonEventTriggerCondition.from_dict(data)



                return exit_condition_type_6
            except: # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            exit_condition_type_7 = AutoResolveEventTriggerCondition.from_dict(data)



            return exit_condition_type_7

        exit_condition = _parse_exit_condition(d.pop("exitCondition"))


        def _parse_predicate(data: object) -> Union['BaseEventTriggerPredicate', None]:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                predicate_type_0 = BaseEventTriggerPredicate.from_dict(data)



                return predicate_type_0
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                predicate_type_1 = BaseEventTriggerPredicate.from_dict(data)



                return predicate_type_1
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                predicate_type_2 = BaseEventTriggerPredicate.from_dict(data)



                return predicate_type_2
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                predicate_type_3 = BaseEventTriggerPredicate.from_dict(data)



                return predicate_type_3
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                predicate_type_4 = BaseEventTriggerPredicate.from_dict(data)



                return predicate_type_4
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                predicate_type_5 = BaseEventTriggerPredicate.from_dict(data)



                return predicate_type_5
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                predicate_type_6 = BaseEventTriggerPredicate.from_dict(data)



                return predicate_type_6
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                predicate_type_7 = BaseEventTriggerPredicate.from_dict(data)



                return predicate_type_7
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                predicate_type_8 = BaseEventTriggerPredicate.from_dict(data)



                return predicate_type_8
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                predicate_type_9 = BaseEventTriggerPredicate.from_dict(data)



                return predicate_type_9
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                predicate_type_10 = BaseEventTriggerPredicate.from_dict(data)



                return predicate_type_10
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                predicate_type_11 = BaseEventTriggerPredicate.from_dict(data)



                return predicate_type_11
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                predicate_type_12 = BaseEventTriggerPredicate.from_dict(data)



                return predicate_type_12
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                predicate_type_13 = BaseEventTriggerPredicate.from_dict(data)



                return predicate_type_13
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                predicate_type_14 = BaseEventTriggerPredicate.from_dict(data)



                return predicate_type_14
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                predicate_type_15 = BaseEventTriggerPredicate.from_dict(data)



                return predicate_type_15
            except: # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            predicate_type_16 = BaseEventTriggerPredicate.from_dict(data)



            return predicate_type_16

        predicate = _parse_predicate(d.pop("predicate"))


        enabled = d.pop("enabled", UNSET)

        format_ = d.pop("format", UNSET)

        _triggered_configuration = d.pop("triggeredConfiguration")
        triggered_configuration: Optional[TriggeredConfiguration]
        if _triggered_configuration is None:
            triggered_configuration = None
        else:
            triggered_configuration = TriggeredConfiguration.from_dict(_triggered_configuration)




        _sms_tags = d.pop("smsTags", UNSET)
        sms_tags: Union[Unset, EventTriggerSmsTags]
        if isinstance(_sms_tags,  Unset):
            sms_tags = UNSET
        else:
            sms_tags = EventTriggerSmsTags.from_dict(_sms_tags)




        _device_scope = d.pop("deviceScope", UNSET)
        device_scope: Union[Unset, None, ScopeFilter]
        if _device_scope is None:
            device_scope = None
        elif isinstance(_device_scope,  Unset):
            device_scope = UNSET
        else:
            device_scope = ScopeFilter.from_dict(_device_scope)




        workflows = []
        _workflows = d.pop("workflows")
        for workflows_item_data in (_workflows or []):
            workflows_item = EventTriggerWorkflow.from_dict(workflows_item_data)



            workflows.append(workflows_item)


        _last_triggered_time = d.pop("lastTriggeredTime", UNSET)
        last_triggered_time: Union[Unset, None, datetime.datetime]
        if _last_triggered_time is None:
            last_triggered_time = None
        elif isinstance(_last_triggered_time,  Unset):
            last_triggered_time = UNSET
        else:
            last_triggered_time = isoparse(_last_triggered_time)




        event_trigger_group_id = d.pop("eventTriggerGroupId", UNSET)

        _stateful_trigger_configuration = d.pop("statefulTriggerConfiguration")
        stateful_trigger_configuration: Optional[StatefulTriggerConfiguration]
        if _stateful_trigger_configuration is None:
            stateful_trigger_configuration = None
        else:
            stateful_trigger_configuration = StatefulTriggerConfiguration.from_dict(_stateful_trigger_configuration)




        is_stateful = d.pop("isStateful", UNSET)

        _forwarding_configuration = d.pop("forwardingConfiguration")
        forwarding_configuration: Optional[ForwardingConfiguration]
        if _forwarding_configuration is None:
            forwarding_configuration = None
        else:
            forwarding_configuration = ForwardingConfiguration.from_dict(_forwarding_configuration)




        sets_device_color = d.pop("setsDeviceColor", UNSET)

        _theopolis = d.pop("theopolis", UNSET)
        theopolis: Union[Unset, None, TheopolisConfiguration]
        if _theopolis is None:
            theopolis = None
        elif isinstance(_theopolis,  Unset):
            theopolis = UNSET
        else:
            theopolis = TheopolisConfiguration.from_dict(_theopolis)




        id = d.pop("id", UNSET)

        _created_at = d.pop("createdAt", UNSET)
        created_at: Union[Unset, datetime.datetime]
        if isinstance(_created_at,  Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)




        _updated_at = d.pop("updatedAt", UNSET)
        updated_at: Union[Unset, datetime.datetime]
        if isinstance(_updated_at,  Unset):
            updated_at = UNSET
        else:
            updated_at = isoparse(_updated_at)




        _tags = d.pop("tags", UNSET)
        tags: Union[Unset, EventTriggerTags]
        if isinstance(_tags,  Unset):
            tags = UNSET
        else:
            tags = EventTriggerTags.from_dict(_tags)




        event_trigger = cls(
            event_type=event_type,
            message=message,
            interval=interval,
            severity=severity,
            commands=commands,
            notification_enabled=notification_enabled,
            organization_id=organization_id,
            condition=condition,
            exit_condition=exit_condition,
            predicate=predicate,
            enabled=enabled,
            format_=format_,
            triggered_configuration=triggered_configuration,
            sms_tags=sms_tags,
            device_scope=device_scope,
            workflows=workflows,
            last_triggered_time=last_triggered_time,
            event_trigger_group_id=event_trigger_group_id,
            stateful_trigger_configuration=stateful_trigger_configuration,
            is_stateful=is_stateful,
            forwarding_configuration=forwarding_configuration,
            sets_device_color=sets_device_color,
            theopolis=theopolis,
            id=id,
            created_at=created_at,
            updated_at=updated_at,
            tags=tags,
        )

        event_trigger.additional_properties = d
        return event_trigger

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
