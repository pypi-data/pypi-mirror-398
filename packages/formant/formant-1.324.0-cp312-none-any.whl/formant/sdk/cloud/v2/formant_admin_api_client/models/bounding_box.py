from typing import Any, Dict, List, Type, TypeVar

import attr

T = TypeVar("T", bound="BoundingBox")

@attr.s(auto_attribs=True)
class BoundingBox:
    """
    Attributes:
        x (int):
        y (int):
        width (int):
        height (int):
    """

    x: int
    y: int
    width: int
    height: int
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        x = self.x
        y = self.y
        width = self.width
        height = self.height

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "x": x,
            "y": y,
            "width": width,
            "height": height,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        x = d.pop("x")

        y = d.pop("y")

        width = d.pop("width")

        height = d.pop("height")

        bounding_box = cls(
            x=x,
            y=y,
            width=width,
            height=height,
        )

        bounding_box.additional_properties = d
        return bounding_box

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
