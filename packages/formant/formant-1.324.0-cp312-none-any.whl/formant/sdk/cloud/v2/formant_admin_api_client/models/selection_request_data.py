from typing import Any, Dict, List, Type, TypeVar, Union, cast

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="SelectionRequestData")

@attr.s(auto_attribs=True)
class SelectionRequestData:
    """
    Attributes:
        instruction (str): Prompt to be shown to the user to resolve the intervention request.
        image_url (str): URL of the image file to be shown during the intervention request.
        options (List[str]): Array of strings to present to the user as selection options.
        hint (Union[Unset, int]): Index of the option you would like to suggest as the most likely response (zero-
            indexed).
        title (Union[Unset, str]): Title of the intervention request window.
    """

    instruction: str
    image_url: str
    options: List[str]
    hint: Union[Unset, int] = UNSET
    title: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        instruction = self.instruction
        image_url = self.image_url
        options = self.options




        hint = self.hint
        title = self.title

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "instruction": instruction,
            "imageUrl": image_url,
            "options": options,
        })
        if hint is not UNSET:
            field_dict["hint"] = hint
        if title is not UNSET:
            field_dict["title"] = title

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        instruction = d.pop("instruction")

        image_url = d.pop("imageUrl")

        options = cast(List[str], d.pop("options"))


        hint = d.pop("hint", UNSET)

        title = d.pop("title", UNSET)

        selection_request_data = cls(
            instruction=instruction,
            image_url=image_url,
            options=options,
            hint=hint,
            title=title,
        )

        selection_request_data.additional_properties = d
        return selection_request_data

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
