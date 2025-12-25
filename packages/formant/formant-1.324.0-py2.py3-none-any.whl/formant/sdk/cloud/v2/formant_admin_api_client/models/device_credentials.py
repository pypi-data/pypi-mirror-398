import datetime
from typing import Any, Dict, List, Type, TypeVar

import attr
from dateutil.parser import isoparse

T = TypeVar("T", bound="DeviceCredentials")

@attr.s(auto_attribs=True)
class DeviceCredentials:
    """
    Attributes:
        access_key_id (str):
        secret_access_key (str):
        session_token (str):
        expiration (datetime.datetime):
        s_3_region (str):
        s_3_upload_bucket (str):
    """

    access_key_id: str
    secret_access_key: str
    session_token: str
    expiration: datetime.datetime
    s_3_region: str
    s_3_upload_bucket: str
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        access_key_id = self.access_key_id
        secret_access_key = self.secret_access_key
        session_token = self.session_token
        expiration = self.expiration.isoformat()

        s_3_region = self.s_3_region
        s_3_upload_bucket = self.s_3_upload_bucket

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "accessKeyId": access_key_id,
            "secretAccessKey": secret_access_key,
            "sessionToken": session_token,
            "expiration": expiration,
            "s3Region": s_3_region,
            "s3UploadBucket": s_3_upload_bucket,
        })

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        access_key_id = d.pop("accessKeyId")

        secret_access_key = d.pop("secretAccessKey")

        session_token = d.pop("sessionToken")

        expiration = isoparse(d.pop("expiration"))




        s_3_region = d.pop("s3Region")

        s_3_upload_bucket = d.pop("s3UploadBucket")

        device_credentials = cls(
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
            session_token=session_token,
            expiration=expiration,
            s_3_region=s_3_region,
            s_3_upload_bucket=s_3_upload_bucket,
        )

        device_credentials.additional_properties = d
        return device_credentials

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
