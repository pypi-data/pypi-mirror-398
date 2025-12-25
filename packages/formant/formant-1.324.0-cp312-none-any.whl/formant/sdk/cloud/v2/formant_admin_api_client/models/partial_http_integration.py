import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr
from dateutil.parser import isoparse

from ..models.partial_http_integration_method import \
    PartialHttpIntegrationMethod
from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.http_integration_basic_auth import HttpIntegrationBasicAuth
  from ..models.http_integration_no_auth import HttpIntegrationNoAuth




T = TypeVar("T", bound="PartialHttpIntegration")

@attr.s(auto_attribs=True)
class PartialHttpIntegration:
    """
    Attributes:
        organization_id (Union[Unset, str]):
        name (Union[Unset, str]):
        url (Union[Unset, str]):
        method (Union[Unset, PartialHttpIntegrationMethod]):
        authentication (Union['HttpIntegrationBasicAuth', 'HttpIntegrationNoAuth', Unset]):
        id (Union[Unset, str]):
        created_at (Union[Unset, datetime.datetime]):
        updated_at (Union[Unset, datetime.datetime]):
    """

    organization_id: Union[Unset, str] = UNSET
    name: Union[Unset, str] = UNSET
    url: Union[Unset, str] = UNSET
    method: Union[Unset, PartialHttpIntegrationMethod] = UNSET
    authentication: Union['HttpIntegrationBasicAuth', 'HttpIntegrationNoAuth', Unset] = UNSET
    id: Union[Unset, str] = UNSET
    created_at: Union[Unset, datetime.datetime] = UNSET
    updated_at: Union[Unset, datetime.datetime] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        from ..models.http_integration_basic_auth import \
            HttpIntegrationBasicAuth
        organization_id = self.organization_id
        name = self.name
        url = self.url
        method: Union[Unset, str] = UNSET
        if not isinstance(self.method, Unset):
            method = self.method.value

        authentication: Union[Dict[str, Any], Unset]
        if isinstance(self.authentication, Unset):
            authentication = UNSET

        elif isinstance(self.authentication, HttpIntegrationBasicAuth):
            authentication = UNSET
            if not isinstance(self.authentication, Unset):
                authentication = self.authentication.to_dict()

        else:
            authentication = UNSET
            if not isinstance(self.authentication, Unset):
                authentication = self.authentication.to_dict()



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
        })
        if organization_id is not UNSET:
            field_dict["organizationId"] = organization_id
        if name is not UNSET:
            field_dict["name"] = name
        if url is not UNSET:
            field_dict["url"] = url
        if method is not UNSET:
            field_dict["method"] = method
        if authentication is not UNSET:
            field_dict["authentication"] = authentication
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
        organization_id = d.pop("organizationId", UNSET)

        name = d.pop("name", UNSET)

        url = d.pop("url", UNSET)

        _method = d.pop("method", UNSET)
        method: Union[Unset, PartialHttpIntegrationMethod]
        if isinstance(_method,  Unset):
            method = UNSET
        else:
            method = PartialHttpIntegrationMethod(_method)




        def _parse_authentication(data: object) -> Union['HttpIntegrationBasicAuth', 'HttpIntegrationNoAuth', Unset]:
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                _authentication_type_0 = data
                authentication_type_0: Union[Unset, HttpIntegrationBasicAuth]
                if isinstance(_authentication_type_0,  Unset):
                    authentication_type_0 = UNSET
                else:
                    authentication_type_0 = HttpIntegrationBasicAuth.from_dict(_authentication_type_0)



                return authentication_type_0
            except: # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            _authentication_type_1 = data
            authentication_type_1: Union[Unset, HttpIntegrationNoAuth]
            if isinstance(_authentication_type_1,  Unset):
                authentication_type_1 = UNSET
            else:
                authentication_type_1 = HttpIntegrationNoAuth.from_dict(_authentication_type_1)



            return authentication_type_1

        authentication = _parse_authentication(d.pop("authentication", UNSET))


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




        partial_http_integration = cls(
            organization_id=organization_id,
            name=name,
            url=url,
            method=method,
            authentication=authentication,
            id=id,
            created_at=created_at,
            updated_at=updated_at,
        )

        partial_http_integration.additional_properties = d
        return partial_http_integration

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
