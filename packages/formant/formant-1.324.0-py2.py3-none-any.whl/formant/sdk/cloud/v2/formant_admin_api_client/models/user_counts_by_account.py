from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

import attr

if TYPE_CHECKING:
  from ..models.user_counts_by_account_counts import UserCountsByAccountCounts




T = TypeVar("T", bound="UserCountsByAccount")

@attr.s(auto_attribs=True)
class UserCountsByAccount:
    """
    Attributes:
        counts (UserCountsByAccountCounts):
    """

    counts: 'UserCountsByAccountCounts'
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        counts = self.counts.to_dict()


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "counts": counts,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.user_counts_by_account_counts import \
            UserCountsByAccountCounts
        d = src_dict.copy()
        counts = UserCountsByAccountCounts.from_dict(d.pop("counts"))




        user_counts_by_account = cls(
            counts=counts,
        )

        user_counts_by_account.additional_properties = d
        return user_counts_by_account

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
