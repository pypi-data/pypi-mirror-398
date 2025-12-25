from typing import Any, Dict, List, Type, TypeVar, cast

import attr

T = TypeVar("T", bound="BeginUploadResponse")

@attr.s(auto_attribs=True)
class BeginUploadResponse:
    """
    Attributes:
        file_id (str): ID of the file being uploaded.
        upload_id (str): ID of the upload.
        part_urls (List[str]):
        part_size (int):
    """

    file_id: str
    upload_id: str
    part_urls: List[str]
    part_size: int
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        file_id = self.file_id
        upload_id = self.upload_id
        part_urls = self.part_urls




        part_size = self.part_size

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "fileId": file_id,
            "uploadId": upload_id,
            "partUrls": part_urls,
            "partSize": part_size,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        file_id = d.pop("fileId")

        upload_id = d.pop("uploadId")

        part_urls = cast(List[str], d.pop("partUrls"))


        part_size = d.pop("partSize")

        begin_upload_response = cls(
            file_id=file_id,
            upload_id=upload_id,
            part_urls=part_urls,
            part_size=part_size,
        )

        begin_upload_response.additional_properties = d
        return begin_upload_response

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
