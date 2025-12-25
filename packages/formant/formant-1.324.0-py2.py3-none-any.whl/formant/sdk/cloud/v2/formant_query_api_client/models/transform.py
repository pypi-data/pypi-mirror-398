from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

import attr

if TYPE_CHECKING:
  from ..models.quaternion import Quaternion
  from ..models.vector_3 import Vector3




T = TypeVar("T", bound="Transform")

@attr.s(auto_attribs=True)
class Transform:
    """
    Attributes:
        translation (Vector3):
        rotation (Quaternion):
    """

    translation: 'Vector3'
    rotation: 'Quaternion'
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        translation = self.translation.to_dict()

        rotation = self.rotation.to_dict()


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "translation": translation,
            "rotation": rotation,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.quaternion import Quaternion
        from ..models.vector_3 import Vector3
        d = src_dict.copy()
        translation = Vector3.from_dict(d.pop("translation"))




        rotation = Quaternion.from_dict(d.pop("rotation"))




        transform = cls(
            translation=translation,
            rotation=rotation,
        )

        transform.additional_properties = d
        return transform

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
