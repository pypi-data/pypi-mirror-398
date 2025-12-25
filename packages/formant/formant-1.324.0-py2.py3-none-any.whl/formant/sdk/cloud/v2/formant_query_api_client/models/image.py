from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.image_annotation import ImageAnnotation




T = TypeVar("T", bound="Image")

@attr.s(auto_attribs=True)
class Image:
    """
    Attributes:
        url (str):
        size (Union[Unset, int]):
        annotations (Union[Unset, List['ImageAnnotation']]):
    """

    url: str
    size: Union[Unset, int] = UNSET
    annotations: Union[Unset, List['ImageAnnotation']] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        url = self.url
        size = self.size
        annotations: Union[Unset, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.annotations, Unset):
            annotations = []
            for annotations_item_data in self.annotations:
                annotations_item = annotations_item_data.to_dict()

                annotations.append(annotations_item)





        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "url": url,
        })
        if size is not UNSET:
            field_dict["size"] = size
        if annotations is not UNSET:
            field_dict["annotations"] = annotations

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.image_annotation import ImageAnnotation
        d = src_dict.copy()
        url = d.pop("url")

        size = d.pop("size", UNSET)

        annotations = []
        _annotations = d.pop("annotations", UNSET)
        for annotations_item_data in (_annotations or []):
            annotations_item = ImageAnnotation.from_dict(annotations_item_data)



            annotations.append(annotations_item)


        image = cls(
            url=url,
            size=size,
            annotations=annotations,
        )

        image.additional_properties = d
        return image

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
