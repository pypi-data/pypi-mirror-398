from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

import attr

if TYPE_CHECKING:
  from ..models.vector_3 import Vector3




T = TypeVar("T", bound="Camera")

@attr.s(auto_attribs=True)
class Camera:
    """
    Attributes:
        position (Vector3):
        target (Vector3):
    """

    position: 'Vector3'
    target: 'Vector3'
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        position = self.position.to_dict()

        target = self.target.to_dict()


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "position": position,
            "target": target,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.vector_3 import Vector3
        d = src_dict.copy()
        position = Vector3.from_dict(d.pop("position"))




        target = Vector3.from_dict(d.pop("target"))




        camera = cls(
            position=position,
            target=target,
        )

        camera.additional_properties = d
        return camera

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
