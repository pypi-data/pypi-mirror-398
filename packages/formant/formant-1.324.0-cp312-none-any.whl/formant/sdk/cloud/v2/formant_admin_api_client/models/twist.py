from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

import attr

if TYPE_CHECKING:
  from ..models.vector_3 import Vector3




T = TypeVar("T", bound="Twist")

@attr.s(auto_attribs=True)
class Twist:
    """
    Attributes:
        linear (Vector3):
        angular (Vector3):
    """

    linear: 'Vector3'
    angular: 'Vector3'
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        linear = self.linear.to_dict()

        angular = self.angular.to_dict()


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "linear": linear,
            "angular": angular,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.vector_3 import Vector3
        d = src_dict.copy()
        linear = Vector3.from_dict(d.pop("linear"))




        angular = Vector3.from_dict(d.pop("angular"))




        twist = cls(
            linear=linear,
            angular=angular,
        )

        twist.additional_properties = d
        return twist

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
