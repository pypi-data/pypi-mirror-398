from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.label import Label
  from ..models.labeled_polygon import LabeledPolygon




T = TypeVar("T", bound="LabelingRequestData")

@attr.s(auto_attribs=True)
class LabelingRequestData:
    """
    Attributes:
        instruction (str): Prompt to be shown to the user to resolve the intervention request.
        image_url (str): URL of the image file to be shown during the intervention request.
        labels (List['Label']):
        hint (Union[Unset, List['LabeledPolygon']]): (x,y) coordinates creating a box around the area in the image you
            would like to suggest as the most likely location of the object in question.
        title (Union[Unset, str]): Title of the intervention request window.
    """

    instruction: str
    image_url: str
    labels: List['Label']
    hint: Union[Unset, List['LabeledPolygon']] = UNSET
    title: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        instruction = self.instruction
        image_url = self.image_url
        labels = []
        for labels_item_data in self.labels:
            labels_item = labels_item_data.to_dict()

            labels.append(labels_item)




        hint: Union[Unset, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.hint, Unset):
            hint = []
            for hint_item_data in self.hint:
                hint_item = hint_item_data.to_dict()

                hint.append(hint_item)




        title = self.title

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "instruction": instruction,
            "imageUrl": image_url,
            "labels": labels,
        })
        if hint is not UNSET:
            field_dict["hint"] = hint
        if title is not UNSET:
            field_dict["title"] = title

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.label import Label
        from ..models.labeled_polygon import LabeledPolygon
        d = src_dict.copy()
        instruction = d.pop("instruction")

        image_url = d.pop("imageUrl")

        labels = []
        _labels = d.pop("labels")
        for labels_item_data in (_labels):
            labels_item = Label.from_dict(labels_item_data)



            labels.append(labels_item)


        hint = []
        _hint = d.pop("hint", UNSET)
        for hint_item_data in (_hint or []):
            hint_item = LabeledPolygon.from_dict(hint_item_data)



            hint.append(hint_item)


        title = d.pop("title", UNSET)

        labeling_request_data = cls(
            instruction=instruction,
            image_url=image_url,
            labels=labels,
            hint=hint,
            title=title,
        )

        labeling_request_data.additional_properties = d
        return labeling_request_data

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
