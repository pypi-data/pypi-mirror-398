from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..models.create_intervention_response_intervention_type import \
    CreateInterventionResponseInterventionType
from ..models.create_intervention_response_type import \
    CreateInterventionResponseType
from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateInterventionResponse")

@attr.s(auto_attribs=True)
class CreateInterventionResponse:
    """
    Attributes:
        intervention_type (CreateInterventionResponseInterventionType): Type of intervention to which you are
            responding.
        data (Any): Body of your response to the intevention.
        intervention_id (str): ID of the intervention request to which you are responding.
        type (Union[Unset, CreateInterventionResponseType]): Enter `intervention-response`.
        tags (Union[Unset, Any]): Tags to associate with the intervention response.
        time (Union[Unset, Any]): Timestamp of the intervention response.
        message (Union[Unset, Any]): Message to associate with the intervention response.
        device_id (Union[Unset, Any]): ID of the device relevant to this intervention.
        user_id (Union[Unset, str]): ID of the user who is responding to this intervention request.
    """

    intervention_type: CreateInterventionResponseInterventionType
    data: Any
    intervention_id: str
    type: Union[Unset, CreateInterventionResponseType] = UNSET
    tags: Union[Unset, Any] = UNSET
    time: Union[Unset, Any] = UNSET
    message: Union[Unset, Any] = UNSET
    device_id: Union[Unset, Any] = UNSET
    user_id: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        intervention_type = self.intervention_type.value

        data = self.data
        intervention_id = self.intervention_id
        type: Union[Unset, str] = UNSET
        if not isinstance(self.type, Unset):
            type = self.type.value

        tags = self.tags
        time = self.time
        message = self.message
        device_id = self.device_id
        user_id = self.user_id

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "interventionType": intervention_type,
            "data": data,
            "interventionId": intervention_id,
        })
        if type is not UNSET:
            field_dict["type"] = type
        if tags is not UNSET:
            field_dict["tags"] = tags
        if time is not UNSET:
            field_dict["time"] = time
        if message is not UNSET:
            field_dict["message"] = message
        if device_id is not UNSET:
            field_dict["deviceId"] = device_id
        if user_id is not UNSET:
            field_dict["userId"] = user_id

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        intervention_type = CreateInterventionResponseInterventionType(d.pop("interventionType"))




        data = d.pop("data")

        intervention_id = d.pop("interventionId")

        _type = d.pop("type", UNSET)
        type: Union[Unset, CreateInterventionResponseType]
        if isinstance(_type,  Unset):
            type = UNSET
        else:
            type = CreateInterventionResponseType(_type)




        tags = d.pop("tags", UNSET)

        time = d.pop("time", UNSET)

        message = d.pop("message", UNSET)

        device_id = d.pop("deviceId", UNSET)

        user_id = d.pop("userId", UNSET)

        create_intervention_response = cls(
            intervention_type=intervention_type,
            data=data,
            intervention_id=intervention_id,
            type=type,
            tags=tags,
            time=time,
            message=message,
            device_id=device_id,
            user_id=user_id,
        )

        create_intervention_response.additional_properties = d
        return create_intervention_response

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
