import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr
from dateutil.parser import isoparse

from ..models.partial_event_trigger_event_type import \
    PartialEventTriggerEventType
from ..models.partial_event_trigger_severity import PartialEventTriggerSeverity
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
  from ..models.event_trigger_workflow import EventTriggerWorkflow
  from ..models.forwarding_configuration import ForwardingConfiguration
  from ..models.json_event_trigger_condition import JsonEventTriggerCondition
  from ..models.numeric_set_event_trigger_condition import \
      NumericSetEventTriggerCondition
  from ..models.partial_event_trigger_sms_tags import \
      PartialEventTriggerSmsTags
  from ..models.partial_event_trigger_tags import PartialEventTriggerTags
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




T = TypeVar("T", bound="PartialEventTrigger")

@attr.s(auto_attribs=True)
class PartialEventTrigger:
    """
    Attributes:
        organization_id (Union[Unset, str]):
        event_type (Union[Unset, PartialEventTriggerEventType]):
        message (Union[Unset, str]):
        condition (Union['AutoResolveEventTriggerCondition', 'BatteryEventTriggerCondition',
            'BitsetEventTriggerCondition', 'JsonEventTriggerCondition', 'NumericSetEventTriggerCondition',
            'PresenceEventTriggerCondition', 'RegexEventTriggerCondition', 'ThresholdEventTriggerCondition', None, Unset]):
        exit_condition (Union['AutoResolveEventTriggerCondition', 'BatteryEventTriggerCondition',
            'BitsetEventTriggerCondition', 'JsonEventTriggerCondition', 'NumericSetEventTriggerCondition',
            'PresenceEventTriggerCondition', 'RegexEventTriggerCondition', 'ThresholdEventTriggerCondition', None, Unset]):
        predicate (Union['BaseEventTriggerPredicate', None, Unset]):
        interval (Union[Unset, int]):
        severity (Union[Unset, PartialEventTriggerSeverity]):
        enabled (Union[Unset, bool]):
        format_ (Union[Unset, str]):
        triggered_configuration (Union[Unset, None, TriggeredConfiguration]):
        sms_tags (Union[Unset, PartialEventTriggerSmsTags]):
        device_scope (Union[Unset, None, ScopeFilter]):
        commands (Union[Unset, List['EventTriggerCommand']]):
        workflows (Union[Unset, None, List['EventTriggerWorkflow']]):
        notification_enabled (Union[Unset, bool]):
        last_triggered_time (Union[Unset, None, datetime.datetime]):
        event_trigger_group_id (Union[Unset, None, str]):
        stateful_trigger_configuration (Union[Unset, None, StatefulTriggerConfiguration]):
        is_stateful (Union[Unset, bool]):
        forwarding_configuration (Union[Unset, None, ForwardingConfiguration]):
        sets_device_color (Union[Unset, bool]):
        theopolis (Union[Unset, None, TheopolisConfiguration]):
        id (Union[Unset, str]):
        created_at (Union[Unset, datetime.datetime]):
        updated_at (Union[Unset, datetime.datetime]):
        tags (Union[Unset, PartialEventTriggerTags]):
    """

    organization_id: Union[Unset, str] = UNSET
    event_type: Union[Unset, PartialEventTriggerEventType] = UNSET
    message: Union[Unset, str] = UNSET
    condition: Union['AutoResolveEventTriggerCondition', 'BatteryEventTriggerCondition', 'BitsetEventTriggerCondition', 'JsonEventTriggerCondition', 'NumericSetEventTriggerCondition', 'PresenceEventTriggerCondition', 'RegexEventTriggerCondition', 'ThresholdEventTriggerCondition', None, Unset] = UNSET
    exit_condition: Union['AutoResolveEventTriggerCondition', 'BatteryEventTriggerCondition', 'BitsetEventTriggerCondition', 'JsonEventTriggerCondition', 'NumericSetEventTriggerCondition', 'PresenceEventTriggerCondition', 'RegexEventTriggerCondition', 'ThresholdEventTriggerCondition', None, Unset] = UNSET
    predicate: Union['BaseEventTriggerPredicate', None, Unset] = UNSET
    interval: Union[Unset, int] = UNSET
    severity: Union[Unset, PartialEventTriggerSeverity] = UNSET
    enabled: Union[Unset, bool] = UNSET
    format_: Union[Unset, str] = UNSET
    triggered_configuration: Union[Unset, None, 'TriggeredConfiguration'] = UNSET
    sms_tags: Union[Unset, 'PartialEventTriggerSmsTags'] = UNSET
    device_scope: Union[Unset, None, 'ScopeFilter'] = UNSET
    commands: Union[Unset, List['EventTriggerCommand']] = UNSET
    workflows: Union[Unset, None, List['EventTriggerWorkflow']] = UNSET
    notification_enabled: Union[Unset, bool] = UNSET
    last_triggered_time: Union[Unset, None, datetime.datetime] = UNSET
    event_trigger_group_id: Union[Unset, None, str] = UNSET
    stateful_trigger_configuration: Union[Unset, None, 'StatefulTriggerConfiguration'] = UNSET
    is_stateful: Union[Unset, bool] = UNSET
    forwarding_configuration: Union[Unset, None, 'ForwardingConfiguration'] = UNSET
    sets_device_color: Union[Unset, bool] = UNSET
    theopolis: Union[Unset, None, 'TheopolisConfiguration'] = UNSET
    id: Union[Unset, str] = UNSET
    created_at: Union[Unset, datetime.datetime] = UNSET
    updated_at: Union[Unset, datetime.datetime] = UNSET
    tags: Union[Unset, 'PartialEventTriggerTags'] = UNSET
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
        organization_id = self.organization_id
        event_type: Union[Unset, str] = UNSET
        if not isinstance(self.event_type, Unset):
            event_type = self.event_type.value

        message = self.message
        condition: Union[Dict[str, Any], None, Unset]
        if isinstance(self.condition, Unset):
            condition = UNSET
        elif self.condition is None:
            condition = None

        elif isinstance(self.condition, PresenceEventTriggerCondition):
            condition = UNSET
            if not isinstance(self.condition, Unset):
                condition = self.condition.to_dict()

        elif isinstance(self.condition, ThresholdEventTriggerCondition):
            condition = UNSET
            if not isinstance(self.condition, Unset):
                condition = self.condition.to_dict()

        elif isinstance(self.condition, RegexEventTriggerCondition):
            condition = UNSET
            if not isinstance(self.condition, Unset):
                condition = self.condition.to_dict()

        elif isinstance(self.condition, BitsetEventTriggerCondition):
            condition = UNSET
            if not isinstance(self.condition, Unset):
                condition = self.condition.to_dict()

        elif isinstance(self.condition, BatteryEventTriggerCondition):
            condition = UNSET
            if not isinstance(self.condition, Unset):
                condition = self.condition.to_dict()

        elif isinstance(self.condition, NumericSetEventTriggerCondition):
            condition = UNSET
            if not isinstance(self.condition, Unset):
                condition = self.condition.to_dict()

        elif isinstance(self.condition, JsonEventTriggerCondition):
            condition = UNSET
            if not isinstance(self.condition, Unset):
                condition = self.condition.to_dict()

        else:
            condition = UNSET
            if not isinstance(self.condition, Unset):
                condition = self.condition.to_dict()



        exit_condition: Union[Dict[str, Any], None, Unset]
        if isinstance(self.exit_condition, Unset):
            exit_condition = UNSET
        elif self.exit_condition is None:
            exit_condition = None

        elif isinstance(self.exit_condition, PresenceEventTriggerCondition):
            exit_condition = UNSET
            if not isinstance(self.exit_condition, Unset):
                exit_condition = self.exit_condition.to_dict()

        elif isinstance(self.exit_condition, ThresholdEventTriggerCondition):
            exit_condition = UNSET
            if not isinstance(self.exit_condition, Unset):
                exit_condition = self.exit_condition.to_dict()

        elif isinstance(self.exit_condition, RegexEventTriggerCondition):
            exit_condition = UNSET
            if not isinstance(self.exit_condition, Unset):
                exit_condition = self.exit_condition.to_dict()

        elif isinstance(self.exit_condition, BitsetEventTriggerCondition):
            exit_condition = UNSET
            if not isinstance(self.exit_condition, Unset):
                exit_condition = self.exit_condition.to_dict()

        elif isinstance(self.exit_condition, BatteryEventTriggerCondition):
            exit_condition = UNSET
            if not isinstance(self.exit_condition, Unset):
                exit_condition = self.exit_condition.to_dict()

        elif isinstance(self.exit_condition, NumericSetEventTriggerCondition):
            exit_condition = UNSET
            if not isinstance(self.exit_condition, Unset):
                exit_condition = self.exit_condition.to_dict()

        elif isinstance(self.exit_condition, JsonEventTriggerCondition):
            exit_condition = UNSET
            if not isinstance(self.exit_condition, Unset):
                exit_condition = self.exit_condition.to_dict()

        else:
            exit_condition = UNSET
            if not isinstance(self.exit_condition, Unset):
                exit_condition = self.exit_condition.to_dict()



        predicate: Union[Dict[str, Any], None, Unset]
        if isinstance(self.predicate, Unset):
            predicate = UNSET
        elif self.predicate is None:
            predicate = None

        elif isinstance(self.predicate, BaseEventTriggerPredicate):
            predicate = UNSET
            if not isinstance(self.predicate, Unset):
                predicate = self.predicate.to_dict()

        elif isinstance(self.predicate, BaseEventTriggerPredicate):
            predicate = UNSET
            if not isinstance(self.predicate, Unset):
                predicate = self.predicate.to_dict()

        elif isinstance(self.predicate, BaseEventTriggerPredicate):
            predicate = UNSET
            if not isinstance(self.predicate, Unset):
                predicate = self.predicate.to_dict()

        elif isinstance(self.predicate, BaseEventTriggerPredicate):
            predicate = UNSET
            if not isinstance(self.predicate, Unset):
                predicate = self.predicate.to_dict()

        elif isinstance(self.predicate, BaseEventTriggerPredicate):
            predicate = UNSET
            if not isinstance(self.predicate, Unset):
                predicate = self.predicate.to_dict()

        elif isinstance(self.predicate, BaseEventTriggerPredicate):
            predicate = UNSET
            if not isinstance(self.predicate, Unset):
                predicate = self.predicate.to_dict()

        elif isinstance(self.predicate, BaseEventTriggerPredicate):
            predicate = UNSET
            if not isinstance(self.predicate, Unset):
                predicate = self.predicate.to_dict()

        elif isinstance(self.predicate, BaseEventTriggerPredicate):
            predicate = UNSET
            if not isinstance(self.predicate, Unset):
                predicate = self.predicate.to_dict()

        elif isinstance(self.predicate, BaseEventTriggerPredicate):
            predicate = UNSET
            if not isinstance(self.predicate, Unset):
                predicate = self.predicate.to_dict()

        elif isinstance(self.predicate, BaseEventTriggerPredicate):
            predicate = UNSET
            if not isinstance(self.predicate, Unset):
                predicate = self.predicate.to_dict()

        elif isinstance(self.predicate, BaseEventTriggerPredicate):
            predicate = UNSET
            if not isinstance(self.predicate, Unset):
                predicate = self.predicate.to_dict()

        elif isinstance(self.predicate, BaseEventTriggerPredicate):
            predicate = UNSET
            if not isinstance(self.predicate, Unset):
                predicate = self.predicate.to_dict()

        elif isinstance(self.predicate, BaseEventTriggerPredicate):
            predicate = UNSET
            if not isinstance(self.predicate, Unset):
                predicate = self.predicate.to_dict()

        elif isinstance(self.predicate, BaseEventTriggerPredicate):
            predicate = UNSET
            if not isinstance(self.predicate, Unset):
                predicate = self.predicate.to_dict()

        elif isinstance(self.predicate, BaseEventTriggerPredicate):
            predicate = UNSET
            if not isinstance(self.predicate, Unset):
                predicate = self.predicate.to_dict()

        elif isinstance(self.predicate, BaseEventTriggerPredicate):
            predicate = UNSET
            if not isinstance(self.predicate, Unset):
                predicate = self.predicate.to_dict()

        else:
            predicate = UNSET
            if not isinstance(self.predicate, Unset):
                predicate = self.predicate.to_dict()



        interval = self.interval
        severity: Union[Unset, str] = UNSET
        if not isinstance(self.severity, Unset):
            severity = self.severity.value

        enabled = self.enabled
        format_ = self.format_
        triggered_configuration: Union[Unset, None, Dict[str, Any]] = UNSET
        if not isinstance(self.triggered_configuration, Unset):
            triggered_configuration = self.triggered_configuration.to_dict() if self.triggered_configuration else None

        sms_tags: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.sms_tags, Unset):
            sms_tags = self.sms_tags.to_dict()

        device_scope: Union[Unset, None, Dict[str, Any]] = UNSET
        if not isinstance(self.device_scope, Unset):
            device_scope = self.device_scope.to_dict() if self.device_scope else None

        commands: Union[Unset, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.commands, Unset):
            commands = []
            for commands_item_data in self.commands:
                commands_item = commands_item_data.to_dict()

                commands.append(commands_item)




        workflows: Union[Unset, None, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.workflows, Unset):
            if self.workflows is None:
                workflows = None
            else:
                workflows = []
                for workflows_item_data in self.workflows:
                    workflows_item = workflows_item_data.to_dict()

                    workflows.append(workflows_item)




        notification_enabled = self.notification_enabled
        last_triggered_time: Union[Unset, None, str] = UNSET
        if not isinstance(self.last_triggered_time, Unset):
            last_triggered_time = self.last_triggered_time.isoformat() if self.last_triggered_time else None

        event_trigger_group_id = self.event_trigger_group_id
        stateful_trigger_configuration: Union[Unset, None, Dict[str, Any]] = UNSET
        if not isinstance(self.stateful_trigger_configuration, Unset):
            stateful_trigger_configuration = self.stateful_trigger_configuration.to_dict() if self.stateful_trigger_configuration else None

        is_stateful = self.is_stateful
        forwarding_configuration: Union[Unset, None, Dict[str, Any]] = UNSET
        if not isinstance(self.forwarding_configuration, Unset):
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
        })
        if organization_id is not UNSET:
            field_dict["organizationId"] = organization_id
        if event_type is not UNSET:
            field_dict["eventType"] = event_type
        if message is not UNSET:
            field_dict["message"] = message
        if condition is not UNSET:
            field_dict["condition"] = condition
        if exit_condition is not UNSET:
            field_dict["exitCondition"] = exit_condition
        if predicate is not UNSET:
            field_dict["predicate"] = predicate
        if interval is not UNSET:
            field_dict["interval"] = interval
        if severity is not UNSET:
            field_dict["severity"] = severity
        if enabled is not UNSET:
            field_dict["enabled"] = enabled
        if format_ is not UNSET:
            field_dict["format"] = format_
        if triggered_configuration is not UNSET:
            field_dict["triggeredConfiguration"] = triggered_configuration
        if sms_tags is not UNSET:
            field_dict["smsTags"] = sms_tags
        if device_scope is not UNSET:
            field_dict["deviceScope"] = device_scope
        if commands is not UNSET:
            field_dict["commands"] = commands
        if workflows is not UNSET:
            field_dict["workflows"] = workflows
        if notification_enabled is not UNSET:
            field_dict["notificationEnabled"] = notification_enabled
        if last_triggered_time is not UNSET:
            field_dict["lastTriggeredTime"] = last_triggered_time
        if event_trigger_group_id is not UNSET:
            field_dict["eventTriggerGroupId"] = event_trigger_group_id
        if stateful_trigger_configuration is not UNSET:
            field_dict["statefulTriggerConfiguration"] = stateful_trigger_configuration
        if is_stateful is not UNSET:
            field_dict["isStateful"] = is_stateful
        if forwarding_configuration is not UNSET:
            field_dict["forwardingConfiguration"] = forwarding_configuration
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
        from ..models.event_trigger_workflow import EventTriggerWorkflow
        from ..models.forwarding_configuration import ForwardingConfiguration
        from ..models.json_event_trigger_condition import \
            JsonEventTriggerCondition
        from ..models.numeric_set_event_trigger_condition import \
            NumericSetEventTriggerCondition
        from ..models.partial_event_trigger_sms_tags import \
            PartialEventTriggerSmsTags
        from ..models.partial_event_trigger_tags import PartialEventTriggerTags
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
        organization_id = d.pop("organizationId", UNSET)

        _event_type = d.pop("eventType", UNSET)
        event_type: Union[Unset, PartialEventTriggerEventType]
        if isinstance(_event_type,  Unset):
            event_type = UNSET
        else:
            event_type = PartialEventTriggerEventType(_event_type)




        message = d.pop("message", UNSET)

        def _parse_condition(data: object) -> Union['AutoResolveEventTriggerCondition', 'BatteryEventTriggerCondition', 'BitsetEventTriggerCondition', 'JsonEventTriggerCondition', 'NumericSetEventTriggerCondition', 'PresenceEventTriggerCondition', 'RegexEventTriggerCondition', 'ThresholdEventTriggerCondition', None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                _condition_type_0 = data
                condition_type_0: Union[Unset, PresenceEventTriggerCondition]
                if isinstance(_condition_type_0,  Unset):
                    condition_type_0 = UNSET
                else:
                    condition_type_0 = PresenceEventTriggerCondition.from_dict(_condition_type_0)



                return condition_type_0
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                _condition_type_1 = data
                condition_type_1: Union[Unset, ThresholdEventTriggerCondition]
                if isinstance(_condition_type_1,  Unset):
                    condition_type_1 = UNSET
                else:
                    condition_type_1 = ThresholdEventTriggerCondition.from_dict(_condition_type_1)



                return condition_type_1
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                _condition_type_2 = data
                condition_type_2: Union[Unset, RegexEventTriggerCondition]
                if isinstance(_condition_type_2,  Unset):
                    condition_type_2 = UNSET
                else:
                    condition_type_2 = RegexEventTriggerCondition.from_dict(_condition_type_2)



                return condition_type_2
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                _condition_type_3 = data
                condition_type_3: Union[Unset, BitsetEventTriggerCondition]
                if isinstance(_condition_type_3,  Unset):
                    condition_type_3 = UNSET
                else:
                    condition_type_3 = BitsetEventTriggerCondition.from_dict(_condition_type_3)



                return condition_type_3
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                _condition_type_4 = data
                condition_type_4: Union[Unset, BatteryEventTriggerCondition]
                if isinstance(_condition_type_4,  Unset):
                    condition_type_4 = UNSET
                else:
                    condition_type_4 = BatteryEventTriggerCondition.from_dict(_condition_type_4)



                return condition_type_4
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                _condition_type_5 = data
                condition_type_5: Union[Unset, NumericSetEventTriggerCondition]
                if isinstance(_condition_type_5,  Unset):
                    condition_type_5 = UNSET
                else:
                    condition_type_5 = NumericSetEventTriggerCondition.from_dict(_condition_type_5)



                return condition_type_5
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                _condition_type_6 = data
                condition_type_6: Union[Unset, JsonEventTriggerCondition]
                if isinstance(_condition_type_6,  Unset):
                    condition_type_6 = UNSET
                else:
                    condition_type_6 = JsonEventTriggerCondition.from_dict(_condition_type_6)



                return condition_type_6
            except: # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            _condition_type_7 = data
            condition_type_7: Union[Unset, AutoResolveEventTriggerCondition]
            if isinstance(_condition_type_7,  Unset):
                condition_type_7 = UNSET
            else:
                condition_type_7 = AutoResolveEventTriggerCondition.from_dict(_condition_type_7)



            return condition_type_7

        condition = _parse_condition(d.pop("condition", UNSET))


        def _parse_exit_condition(data: object) -> Union['AutoResolveEventTriggerCondition', 'BatteryEventTriggerCondition', 'BitsetEventTriggerCondition', 'JsonEventTriggerCondition', 'NumericSetEventTriggerCondition', 'PresenceEventTriggerCondition', 'RegexEventTriggerCondition', 'ThresholdEventTriggerCondition', None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                _exit_condition_type_0 = data
                exit_condition_type_0: Union[Unset, PresenceEventTriggerCondition]
                if isinstance(_exit_condition_type_0,  Unset):
                    exit_condition_type_0 = UNSET
                else:
                    exit_condition_type_0 = PresenceEventTriggerCondition.from_dict(_exit_condition_type_0)



                return exit_condition_type_0
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                _exit_condition_type_1 = data
                exit_condition_type_1: Union[Unset, ThresholdEventTriggerCondition]
                if isinstance(_exit_condition_type_1,  Unset):
                    exit_condition_type_1 = UNSET
                else:
                    exit_condition_type_1 = ThresholdEventTriggerCondition.from_dict(_exit_condition_type_1)



                return exit_condition_type_1
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                _exit_condition_type_2 = data
                exit_condition_type_2: Union[Unset, RegexEventTriggerCondition]
                if isinstance(_exit_condition_type_2,  Unset):
                    exit_condition_type_2 = UNSET
                else:
                    exit_condition_type_2 = RegexEventTriggerCondition.from_dict(_exit_condition_type_2)



                return exit_condition_type_2
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                _exit_condition_type_3 = data
                exit_condition_type_3: Union[Unset, BitsetEventTriggerCondition]
                if isinstance(_exit_condition_type_3,  Unset):
                    exit_condition_type_3 = UNSET
                else:
                    exit_condition_type_3 = BitsetEventTriggerCondition.from_dict(_exit_condition_type_3)



                return exit_condition_type_3
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                _exit_condition_type_4 = data
                exit_condition_type_4: Union[Unset, BatteryEventTriggerCondition]
                if isinstance(_exit_condition_type_4,  Unset):
                    exit_condition_type_4 = UNSET
                else:
                    exit_condition_type_4 = BatteryEventTriggerCondition.from_dict(_exit_condition_type_4)



                return exit_condition_type_4
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                _exit_condition_type_5 = data
                exit_condition_type_5: Union[Unset, NumericSetEventTriggerCondition]
                if isinstance(_exit_condition_type_5,  Unset):
                    exit_condition_type_5 = UNSET
                else:
                    exit_condition_type_5 = NumericSetEventTriggerCondition.from_dict(_exit_condition_type_5)



                return exit_condition_type_5
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                _exit_condition_type_6 = data
                exit_condition_type_6: Union[Unset, JsonEventTriggerCondition]
                if isinstance(_exit_condition_type_6,  Unset):
                    exit_condition_type_6 = UNSET
                else:
                    exit_condition_type_6 = JsonEventTriggerCondition.from_dict(_exit_condition_type_6)



                return exit_condition_type_6
            except: # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            _exit_condition_type_7 = data
            exit_condition_type_7: Union[Unset, AutoResolveEventTriggerCondition]
            if isinstance(_exit_condition_type_7,  Unset):
                exit_condition_type_7 = UNSET
            else:
                exit_condition_type_7 = AutoResolveEventTriggerCondition.from_dict(_exit_condition_type_7)



            return exit_condition_type_7

        exit_condition = _parse_exit_condition(d.pop("exitCondition", UNSET))


        def _parse_predicate(data: object) -> Union['BaseEventTriggerPredicate', None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                _predicate_type_0 = data
                predicate_type_0: Union[Unset, BaseEventTriggerPredicate]
                if isinstance(_predicate_type_0,  Unset):
                    predicate_type_0 = UNSET
                else:
                    predicate_type_0 = BaseEventTriggerPredicate.from_dict(_predicate_type_0)



                return predicate_type_0
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                _predicate_type_1 = data
                predicate_type_1: Union[Unset, BaseEventTriggerPredicate]
                if isinstance(_predicate_type_1,  Unset):
                    predicate_type_1 = UNSET
                else:
                    predicate_type_1 = BaseEventTriggerPredicate.from_dict(_predicate_type_1)



                return predicate_type_1
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                _predicate_type_2 = data
                predicate_type_2: Union[Unset, BaseEventTriggerPredicate]
                if isinstance(_predicate_type_2,  Unset):
                    predicate_type_2 = UNSET
                else:
                    predicate_type_2 = BaseEventTriggerPredicate.from_dict(_predicate_type_2)



                return predicate_type_2
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                _predicate_type_3 = data
                predicate_type_3: Union[Unset, BaseEventTriggerPredicate]
                if isinstance(_predicate_type_3,  Unset):
                    predicate_type_3 = UNSET
                else:
                    predicate_type_3 = BaseEventTriggerPredicate.from_dict(_predicate_type_3)



                return predicate_type_3
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                _predicate_type_4 = data
                predicate_type_4: Union[Unset, BaseEventTriggerPredicate]
                if isinstance(_predicate_type_4,  Unset):
                    predicate_type_4 = UNSET
                else:
                    predicate_type_4 = BaseEventTriggerPredicate.from_dict(_predicate_type_4)



                return predicate_type_4
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                _predicate_type_5 = data
                predicate_type_5: Union[Unset, BaseEventTriggerPredicate]
                if isinstance(_predicate_type_5,  Unset):
                    predicate_type_5 = UNSET
                else:
                    predicate_type_5 = BaseEventTriggerPredicate.from_dict(_predicate_type_5)



                return predicate_type_5
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                _predicate_type_6 = data
                predicate_type_6: Union[Unset, BaseEventTriggerPredicate]
                if isinstance(_predicate_type_6,  Unset):
                    predicate_type_6 = UNSET
                else:
                    predicate_type_6 = BaseEventTriggerPredicate.from_dict(_predicate_type_6)



                return predicate_type_6
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                _predicate_type_7 = data
                predicate_type_7: Union[Unset, BaseEventTriggerPredicate]
                if isinstance(_predicate_type_7,  Unset):
                    predicate_type_7 = UNSET
                else:
                    predicate_type_7 = BaseEventTriggerPredicate.from_dict(_predicate_type_7)



                return predicate_type_7
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                _predicate_type_8 = data
                predicate_type_8: Union[Unset, BaseEventTriggerPredicate]
                if isinstance(_predicate_type_8,  Unset):
                    predicate_type_8 = UNSET
                else:
                    predicate_type_8 = BaseEventTriggerPredicate.from_dict(_predicate_type_8)



                return predicate_type_8
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                _predicate_type_9 = data
                predicate_type_9: Union[Unset, BaseEventTriggerPredicate]
                if isinstance(_predicate_type_9,  Unset):
                    predicate_type_9 = UNSET
                else:
                    predicate_type_9 = BaseEventTriggerPredicate.from_dict(_predicate_type_9)



                return predicate_type_9
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                _predicate_type_10 = data
                predicate_type_10: Union[Unset, BaseEventTriggerPredicate]
                if isinstance(_predicate_type_10,  Unset):
                    predicate_type_10 = UNSET
                else:
                    predicate_type_10 = BaseEventTriggerPredicate.from_dict(_predicate_type_10)



                return predicate_type_10
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                _predicate_type_11 = data
                predicate_type_11: Union[Unset, BaseEventTriggerPredicate]
                if isinstance(_predicate_type_11,  Unset):
                    predicate_type_11 = UNSET
                else:
                    predicate_type_11 = BaseEventTriggerPredicate.from_dict(_predicate_type_11)



                return predicate_type_11
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                _predicate_type_12 = data
                predicate_type_12: Union[Unset, BaseEventTriggerPredicate]
                if isinstance(_predicate_type_12,  Unset):
                    predicate_type_12 = UNSET
                else:
                    predicate_type_12 = BaseEventTriggerPredicate.from_dict(_predicate_type_12)



                return predicate_type_12
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                _predicate_type_13 = data
                predicate_type_13: Union[Unset, BaseEventTriggerPredicate]
                if isinstance(_predicate_type_13,  Unset):
                    predicate_type_13 = UNSET
                else:
                    predicate_type_13 = BaseEventTriggerPredicate.from_dict(_predicate_type_13)



                return predicate_type_13
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                _predicate_type_14 = data
                predicate_type_14: Union[Unset, BaseEventTriggerPredicate]
                if isinstance(_predicate_type_14,  Unset):
                    predicate_type_14 = UNSET
                else:
                    predicate_type_14 = BaseEventTriggerPredicate.from_dict(_predicate_type_14)



                return predicate_type_14
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                _predicate_type_15 = data
                predicate_type_15: Union[Unset, BaseEventTriggerPredicate]
                if isinstance(_predicate_type_15,  Unset):
                    predicate_type_15 = UNSET
                else:
                    predicate_type_15 = BaseEventTriggerPredicate.from_dict(_predicate_type_15)



                return predicate_type_15
            except: # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            _predicate_type_16 = data
            predicate_type_16: Union[Unset, BaseEventTriggerPredicate]
            if isinstance(_predicate_type_16,  Unset):
                predicate_type_16 = UNSET
            else:
                predicate_type_16 = BaseEventTriggerPredicate.from_dict(_predicate_type_16)



            return predicate_type_16

        predicate = _parse_predicate(d.pop("predicate", UNSET))


        interval = d.pop("interval", UNSET)

        _severity = d.pop("severity", UNSET)
        severity: Union[Unset, PartialEventTriggerSeverity]
        if isinstance(_severity,  Unset):
            severity = UNSET
        else:
            severity = PartialEventTriggerSeverity(_severity)




        enabled = d.pop("enabled", UNSET)

        format_ = d.pop("format", UNSET)

        _triggered_configuration = d.pop("triggeredConfiguration", UNSET)
        triggered_configuration: Union[Unset, None, TriggeredConfiguration]
        if _triggered_configuration is None:
            triggered_configuration = None
        elif isinstance(_triggered_configuration,  Unset):
            triggered_configuration = UNSET
        else:
            triggered_configuration = TriggeredConfiguration.from_dict(_triggered_configuration)




        _sms_tags = d.pop("smsTags", UNSET)
        sms_tags: Union[Unset, PartialEventTriggerSmsTags]
        if isinstance(_sms_tags,  Unset):
            sms_tags = UNSET
        else:
            sms_tags = PartialEventTriggerSmsTags.from_dict(_sms_tags)




        _device_scope = d.pop("deviceScope", UNSET)
        device_scope: Union[Unset, None, ScopeFilter]
        if _device_scope is None:
            device_scope = None
        elif isinstance(_device_scope,  Unset):
            device_scope = UNSET
        else:
            device_scope = ScopeFilter.from_dict(_device_scope)




        commands = []
        _commands = d.pop("commands", UNSET)
        for commands_item_data in (_commands or []):
            commands_item = EventTriggerCommand.from_dict(commands_item_data)



            commands.append(commands_item)


        workflows = []
        _workflows = d.pop("workflows", UNSET)
        for workflows_item_data in (_workflows or []):
            workflows_item = EventTriggerWorkflow.from_dict(workflows_item_data)



            workflows.append(workflows_item)


        notification_enabled = d.pop("notificationEnabled", UNSET)

        _last_triggered_time = d.pop("lastTriggeredTime", UNSET)
        last_triggered_time: Union[Unset, None, datetime.datetime]
        if _last_triggered_time is None:
            last_triggered_time = None
        elif isinstance(_last_triggered_time,  Unset):
            last_triggered_time = UNSET
        else:
            last_triggered_time = isoparse(_last_triggered_time)




        event_trigger_group_id = d.pop("eventTriggerGroupId", UNSET)

        _stateful_trigger_configuration = d.pop("statefulTriggerConfiguration", UNSET)
        stateful_trigger_configuration: Union[Unset, None, StatefulTriggerConfiguration]
        if _stateful_trigger_configuration is None:
            stateful_trigger_configuration = None
        elif isinstance(_stateful_trigger_configuration,  Unset):
            stateful_trigger_configuration = UNSET
        else:
            stateful_trigger_configuration = StatefulTriggerConfiguration.from_dict(_stateful_trigger_configuration)




        is_stateful = d.pop("isStateful", UNSET)

        _forwarding_configuration = d.pop("forwardingConfiguration", UNSET)
        forwarding_configuration: Union[Unset, None, ForwardingConfiguration]
        if _forwarding_configuration is None:
            forwarding_configuration = None
        elif isinstance(_forwarding_configuration,  Unset):
            forwarding_configuration = UNSET
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
        tags: Union[Unset, PartialEventTriggerTags]
        if isinstance(_tags,  Unset):
            tags = UNSET
        else:
            tags = PartialEventTriggerTags.from_dict(_tags)




        partial_event_trigger = cls(
            organization_id=organization_id,
            event_type=event_type,
            message=message,
            condition=condition,
            exit_condition=exit_condition,
            predicate=predicate,
            interval=interval,
            severity=severity,
            enabled=enabled,
            format_=format_,
            triggered_configuration=triggered_configuration,
            sms_tags=sms_tags,
            device_scope=device_scope,
            commands=commands,
            workflows=workflows,
            notification_enabled=notification_enabled,
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

        partial_event_trigger.additional_properties = d
        return partial_event_trigger

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
