from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

import attr

if TYPE_CHECKING:
  from ..models.usage_prices import UsagePrices




T = TypeVar("T", bound="BillingInfo")

@attr.s(auto_attribs=True)
class BillingInfo:
    """
    Attributes:
        usage_prices (UsagePrices):
        organization_budget_usd_cents (int):
        device_budget_usd_cents (int):
    """

    usage_prices: 'UsagePrices'
    organization_budget_usd_cents: int
    device_budget_usd_cents: int
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        usage_prices = self.usage_prices.to_dict()

        organization_budget_usd_cents = self.organization_budget_usd_cents
        device_budget_usd_cents = self.device_budget_usd_cents

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "usagePrices": usage_prices,
            "organizationBudgetUsdCents": organization_budget_usd_cents,
            "deviceBudgetUsdCents": device_budget_usd_cents,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.usage_prices import UsagePrices
        d = src_dict.copy()
        usage_prices = UsagePrices.from_dict(d.pop("usagePrices"))




        organization_budget_usd_cents = d.pop("organizationBudgetUsdCents")

        device_budget_usd_cents = d.pop("deviceBudgetUsdCents")

        billing_info = cls(
            usage_prices=usage_prices,
            organization_budget_usd_cents=organization_budget_usd_cents,
            device_budget_usd_cents=device_budget_usd_cents,
        )

        billing_info.additional_properties = d
        return billing_info

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
