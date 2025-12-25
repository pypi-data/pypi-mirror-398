from typing import Any, Dict, List, Type, TypeVar

import attr

from ..models.get_features_response_features_item import \
    GetFeaturesResponseFeaturesItem

T = TypeVar("T", bound="GetFeaturesResponse")

@attr.s(auto_attribs=True)
class GetFeaturesResponse:
    """
    Attributes:
        features (List[GetFeaturesResponseFeaturesItem]):
    """

    features: List[GetFeaturesResponseFeaturesItem]
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        features = []
        for features_item_data in self.features:
            features_item = features_item_data.value

            features.append(features_item)





        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "features": features,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        features = []
        _features = d.pop("features")
        for features_item_data in (_features):
            features_item = GetFeaturesResponseFeaturesItem(features_item_data)



            features.append(features_item)


        get_features_response = cls(
            features=features,
        )

        get_features_response.additional_properties = d
        return get_features_response

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
