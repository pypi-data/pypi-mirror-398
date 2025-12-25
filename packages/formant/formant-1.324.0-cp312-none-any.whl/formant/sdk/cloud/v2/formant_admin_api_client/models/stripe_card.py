from typing import Any, Dict, List, Type, TypeVar

import attr

T = TypeVar("T", bound="StripeCard")

@attr.s(auto_attribs=True)
class StripeCard:
    """
    Attributes:
        brand (str):
        last4 (str):
    """

    brand: str
    last4: str
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        brand = self.brand
        last4 = self.last4

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "brand": brand,
            "last4": last4,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        brand = d.pop("brand")

        last4 = d.pop("last4")

        stripe_card = cls(
            brand=brand,
            last4=last4,
        )

        stripe_card.additional_properties = d
        return stripe_card

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
