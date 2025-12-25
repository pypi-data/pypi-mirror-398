import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr
from dateutil.parser import isoparse

from ..models.http_integration_method import HttpIntegrationMethod
from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.http_integration_basic_auth import HttpIntegrationBasicAuth
  from ..models.http_integration_no_auth import HttpIntegrationNoAuth




T = TypeVar("T", bound="HttpIntegration")

@attr.s(auto_attribs=True)
class HttpIntegration:
    """
    Attributes:
        name (str):
        url (str):
        method (HttpIntegrationMethod):
        authentication (Union['HttpIntegrationBasicAuth', 'HttpIntegrationNoAuth']):
        organization_id (Union[Unset, str]):
        id (Union[Unset, str]):
        created_at (Union[Unset, datetime.datetime]):
        updated_at (Union[Unset, datetime.datetime]):
    """

    name: str
    url: str
    method: HttpIntegrationMethod
    authentication: Union['HttpIntegrationBasicAuth', 'HttpIntegrationNoAuth']
    organization_id: Union[Unset, str] = UNSET
    id: Union[Unset, str] = UNSET
    created_at: Union[Unset, datetime.datetime] = UNSET
    updated_at: Union[Unset, datetime.datetime] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        from ..models.http_integration_basic_auth import \
            HttpIntegrationBasicAuth
        name = self.name
        url = self.url
        method = self.method.value

        authentication: Dict[str, Any]

        if isinstance(self.authentication, HttpIntegrationBasicAuth):
            authentication = self.authentication.to_dict()

        else:
            authentication = self.authentication.to_dict()



        organization_id = self.organization_id
        id = self.id
        created_at: Union[Unset, str] = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: Union[Unset, str] = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "name": name,
            "url": url,
            "method": method,
            "authentication": authentication,
        })
        if organization_id is not UNSET:
            field_dict["organizationId"] = organization_id
        if id is not UNSET:
            field_dict["id"] = id
        if created_at is not UNSET:
            field_dict["createdAt"] = created_at
        if updated_at is not UNSET:
            field_dict["updatedAt"] = updated_at

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.http_integration_basic_auth import \
            HttpIntegrationBasicAuth
        from ..models.http_integration_no_auth import HttpIntegrationNoAuth
        d = src_dict.copy()
        name = d.pop("name")

        url = d.pop("url")

        method = HttpIntegrationMethod(d.pop("method"))




        def _parse_authentication(data: object) -> Union['HttpIntegrationBasicAuth', 'HttpIntegrationNoAuth']:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                authentication_type_0 = HttpIntegrationBasicAuth.from_dict(data)



                return authentication_type_0
            except: # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            authentication_type_1 = HttpIntegrationNoAuth.from_dict(data)



            return authentication_type_1

        authentication = _parse_authentication(d.pop("authentication"))


        organization_id = d.pop("organizationId", UNSET)

        id = d.pop("id", UNSET)

        _created_at = d.pop("createdAt", UNSET)
        created_at: Union[Unset, datetime.datetime]
        if isinstance(_created_at,  Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)




        _updated_at = d.pop("updatedAt", UNSET)
        updated_at: Union[Unset, datetime.datetime]
        if isinstance(_updated_at,  Unset):
            updated_at = UNSET
        else:
            updated_at = isoparse(_updated_at)




        http_integration = cls(
            name=name,
            url=url,
            method=method,
            authentication=authentication,
            organization_id=organization_id,
            id=id,
            created_at=created_at,
            updated_at=updated_at,
        )

        http_integration.additional_properties = d
        return http_integration

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
