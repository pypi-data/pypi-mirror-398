from typing import Any, Dict, List, Type, TypeVar, cast

import attr

T = TypeVar("T", bound="LabeledPolygon")

@attr.s(auto_attribs=True)
class LabeledPolygon:
    """
    Attributes:
        vertices (List[List[Any]]):
        labels (List[str]):
    """

    vertices: List[List[Any]]
    labels: List[str]
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        vertices = []
        for vertices_item_data in self.vertices:
            vertices_item = vertices_item_data




            vertices.append(vertices_item)




        labels = self.labels





        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "vertices": vertices,
            "labels": labels,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        vertices = []
        _vertices = d.pop("vertices")
        for vertices_item_data in (_vertices):
            vertices_item = cast(List[Any], vertices_item_data)

            vertices.append(vertices_item)


        labels = cast(List[str], d.pop("labels"))


        labeled_polygon = cls(
            vertices=vertices,
            labels=labels,
        )

        labeled_polygon.additional_properties = d
        return labeled_polygon

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
