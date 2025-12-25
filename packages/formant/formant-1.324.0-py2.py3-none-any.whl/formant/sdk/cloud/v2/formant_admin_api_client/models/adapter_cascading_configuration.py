import datetime
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

import attr
from dateutil.parser import isoparse

from ..models.adapter_cascading_configuration_specificity import \
    AdapterCascadingConfigurationSpecificity
from ..models.adapter_cascading_configuration_type import \
    AdapterCascadingConfigurationType
from ..types import UNSET, Unset

T = TypeVar("T", bound="AdapterCascadingConfiguration")

@attr.s(auto_attribs=True)
class AdapterCascadingConfiguration:
    """
    Attributes:
        type (AdapterCascadingConfigurationType):
        organization_id (str):
        entity_id (str):
        specificity (AdapterCascadingConfigurationSpecificity):
        specificity_id (str):
        id (Union[Unset, str]):
        created_at (Union[Unset, datetime.datetime]):
        updated_at (Union[Unset, datetime.datetime]):
        configuration (Optional[str]):
    """

    type: AdapterCascadingConfigurationType
    organization_id: str
    entity_id: str
    specificity: AdapterCascadingConfigurationSpecificity
    specificity_id: str
    configuration: Optional[str]
    id: Union[Unset, str] = UNSET
    created_at: Union[Unset, datetime.datetime] = UNSET
    updated_at: Union[Unset, datetime.datetime] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        type = self.type.value

        organization_id = self.organization_id
        entity_id = self.entity_id
        specificity = self.specificity.value

        specificity_id = self.specificity_id
        id = self.id
        created_at: Union[Unset, str] = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: Union[Unset, str] = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        configuration = self.configuration

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "type": type,
            "organizationId": organization_id,
            "entityId": entity_id,
            "specificity": specificity,
            "specificityId": specificity_id,
            "configuration": configuration,
        })
        if id is not UNSET:
            field_dict["id"] = id
        if created_at is not UNSET:
            field_dict["createdAt"] = created_at
        if updated_at is not UNSET:
            field_dict["updatedAt"] = updated_at

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        type = AdapterCascadingConfigurationType(d.pop("type"))




        organization_id = d.pop("organizationId")

        entity_id = d.pop("entityId")

        specificity = AdapterCascadingConfigurationSpecificity(d.pop("specificity"))




        specificity_id = d.pop("specificityId")

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




        configuration = d.pop("configuration")

        adapter_cascading_configuration = cls(
            type=type,
            organization_id=organization_id,
            entity_id=entity_id,
            specificity=specificity,
            specificity_id=specificity_id,
            id=id,
            created_at=created_at,
            updated_at=updated_at,
            configuration=configuration,
        )

        adapter_cascading_configuration.additional_properties = d
        return adapter_cascading_configuration

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
