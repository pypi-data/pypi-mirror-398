from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..types import UNSET, Unset

T = TypeVar("T", bound="OAuthConfiguration")

@attr.s(auto_attribs=True)
class OAuthConfiguration:
    """
    Attributes:
        client_id (str):
        redirect_uri (str):
        client_secret (Union[Unset, None, str]):
        oauth_metadata_url (Union[Unset, None, str]):
        authorization_endpoint (Union[Unset, str]):
        token_endpoint (Union[Unset, str]):
        revocation_endpoint (Union[Unset, None, str]):
        scope (Union[Unset, None, str]):
        scope_header (Union[Unset, None, str]):
        audience (Union[Unset, None, str]):
    """

    client_id: str
    redirect_uri: str
    client_secret: Union[Unset, None, str] = UNSET
    oauth_metadata_url: Union[Unset, None, str] = UNSET
    authorization_endpoint: Union[Unset, str] = UNSET
    token_endpoint: Union[Unset, str] = UNSET
    revocation_endpoint: Union[Unset, None, str] = UNSET
    scope: Union[Unset, None, str] = UNSET
    scope_header: Union[Unset, None, str] = UNSET
    audience: Union[Unset, None, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        client_id = self.client_id
        redirect_uri = self.redirect_uri
        client_secret = self.client_secret
        oauth_metadata_url = self.oauth_metadata_url
        authorization_endpoint = self.authorization_endpoint
        token_endpoint = self.token_endpoint
        revocation_endpoint = self.revocation_endpoint
        scope = self.scope
        scope_header = self.scope_header
        audience = self.audience

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "clientId": client_id,
            "redirectUri": redirect_uri,
        })
        if client_secret is not UNSET:
            field_dict["clientSecret"] = client_secret
        if oauth_metadata_url is not UNSET:
            field_dict["oauthMetadataUrl"] = oauth_metadata_url
        if authorization_endpoint is not UNSET:
            field_dict["authorizationEndpoint"] = authorization_endpoint
        if token_endpoint is not UNSET:
            field_dict["tokenEndpoint"] = token_endpoint
        if revocation_endpoint is not UNSET:
            field_dict["revocationEndpoint"] = revocation_endpoint
        if scope is not UNSET:
            field_dict["scope"] = scope
        if scope_header is not UNSET:
            field_dict["scopeHeader"] = scope_header
        if audience is not UNSET:
            field_dict["audience"] = audience

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        client_id = d.pop("clientId")

        redirect_uri = d.pop("redirectUri")

        client_secret = d.pop("clientSecret", UNSET)

        oauth_metadata_url = d.pop("oauthMetadataUrl", UNSET)

        authorization_endpoint = d.pop("authorizationEndpoint", UNSET)

        token_endpoint = d.pop("tokenEndpoint", UNSET)

        revocation_endpoint = d.pop("revocationEndpoint", UNSET)

        scope = d.pop("scope", UNSET)

        scope_header = d.pop("scopeHeader", UNSET)

        audience = d.pop("audience", UNSET)

        o_auth_configuration = cls(
            client_id=client_id,
            redirect_uri=redirect_uri,
            client_secret=client_secret,
            oauth_metadata_url=oauth_metadata_url,
            authorization_endpoint=authorization_endpoint,
            token_endpoint=token_endpoint,
            revocation_endpoint=revocation_endpoint,
            scope=scope,
            scope_header=scope_header,
            audience=audience,
        )

        o_auth_configuration.additional_properties = d
        return o_auth_configuration

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
