from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

import attr

if TYPE_CHECKING:
  from ..models.bounding_box import BoundingBox




T = TypeVar("T", bound="ImageAnnotation")

@attr.s(auto_attribs=True)
class ImageAnnotation:
    """
    Attributes:
        label (str):
        color (str):
        type (str):
        area (BoundingBox):
    """

    label: str
    color: str
    type: str
    area: 'BoundingBox'
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        label = self.label
        color = self.color
        type = self.type
        area = self.area.to_dict()


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "label": label,
            "color": color,
            "type": type,
            "area": area,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.bounding_box import BoundingBox
        d = src_dict.copy()
        label = d.pop("label")

        color = d.pop("color")

        type = d.pop("type")

        area = BoundingBox.from_dict(d.pop("area"))




        image_annotation = cls(
            label=label,
            color=color,
            type=type,
            area=area,
        )

        image_annotation.additional_properties = d
        return image_annotation

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
