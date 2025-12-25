from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.transform import Transform




T = TypeVar("T", bound="TransformNode")

@attr.s(auto_attribs=True)
class TransformNode:
    """
    Attributes:
        name (Union[Unset, str]):
        transform (Union[Unset, Transform]):
        children (Union[Unset, List['TransformNode']]):
        url (Union[Unset, str]):
        size (Union[Unset, int]):
    """

    name: Union[Unset, str] = UNSET
    transform: Union[Unset, 'Transform'] = UNSET
    children: Union[Unset, List['TransformNode']] = UNSET
    url: Union[Unset, str] = UNSET
    size: Union[Unset, int] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        transform: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.transform, Unset):
            transform = self.transform.to_dict()

        children: Union[Unset, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.children, Unset):
            children = []
            for children_item_data in self.children:
                children_item = children_item_data.to_dict()

                children.append(children_item)




        url = self.url
        size = self.size

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if name is not UNSET:
            field_dict["name"] = name
        if transform is not UNSET:
            field_dict["transform"] = transform
        if children is not UNSET:
            field_dict["children"] = children
        if url is not UNSET:
            field_dict["url"] = url
        if size is not UNSET:
            field_dict["size"] = size

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.transform import Transform
        d = src_dict.copy()
        name = d.pop("name", UNSET)

        _transform = d.pop("transform", UNSET)
        transform: Union[Unset, Transform]
        if isinstance(_transform,  Unset):
            transform = UNSET
        else:
            transform = Transform.from_dict(_transform)




        children = []
        _children = d.pop("children", UNSET)
        for children_item_data in (_children or []):
            children_item = TransformNode.from_dict(children_item_data)



            children.append(children_item)


        url = d.pop("url", UNSET)

        size = d.pop("size", UNSET)

        transform_node = cls(
            name=name,
            transform=transform,
            children=children,
            url=url,
            size=size,
        )

        transform_node.additional_properties = d
        return transform_node

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
