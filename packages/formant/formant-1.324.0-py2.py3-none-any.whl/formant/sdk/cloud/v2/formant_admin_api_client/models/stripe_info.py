from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.stripe_card import StripeCard




T = TypeVar("T", bound="StripeInfo")

@attr.s(auto_attribs=True)
class StripeInfo:
    """
    Attributes:
        customer_id (str):
        subscription_id (Union[Unset, str]):
        card (Union[Unset, StripeCard]):
        billing_anchor (Union[Unset, int]):
    """

    customer_id: str
    subscription_id: Union[Unset, str] = UNSET
    card: Union[Unset, 'StripeCard'] = UNSET
    billing_anchor: Union[Unset, int] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        customer_id = self.customer_id
        subscription_id = self.subscription_id
        card: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.card, Unset):
            card = self.card.to_dict()

        billing_anchor = self.billing_anchor

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "customerId": customer_id,
        })
        if subscription_id is not UNSET:
            field_dict["subscriptionId"] = subscription_id
        if card is not UNSET:
            field_dict["card"] = card
        if billing_anchor is not UNSET:
            field_dict["billingAnchor"] = billing_anchor

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.stripe_card import StripeCard
        d = src_dict.copy()
        customer_id = d.pop("customerId")

        subscription_id = d.pop("subscriptionId", UNSET)

        _card = d.pop("card", UNSET)
        card: Union[Unset, StripeCard]
        if isinstance(_card,  Unset):
            card = UNSET
        else:
            card = StripeCard.from_dict(_card)




        billing_anchor = d.pop("billingAnchor", UNSET)

        stripe_info = cls(
            customer_id=customer_id,
            subscription_id=subscription_id,
            card=card,
            billing_anchor=billing_anchor,
        )

        stripe_info.additional_properties = d
        return stripe_info

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
