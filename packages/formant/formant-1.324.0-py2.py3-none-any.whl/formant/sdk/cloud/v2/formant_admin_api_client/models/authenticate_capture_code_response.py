from typing import (TYPE_CHECKING, Any, Dict, List, Optional, Type, TypeVar,
                    Union)

import attr

from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.capture_session import CaptureSession
  from ..models.user_scope import UserScope




T = TypeVar("T", bound="AuthenticateCaptureCodeResponse")

@attr.s(auto_attribs=True)
class AuthenticateCaptureCodeResponse:
    """
    Attributes:
        token (str):
        capture_session (Union[Unset, List['CaptureSession']]):
        scope (Union[Unset, List[Optional['UserScope']]]):
    """

    token: str
    capture_session: Union[Unset, List['CaptureSession']] = UNSET
    scope: Union[Unset, List[Optional['UserScope']]] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        token = self.token
        capture_session: Union[Unset, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.capture_session, Unset):
            capture_session = []
            for capture_session_item_data in self.capture_session:
                capture_session_item = capture_session_item_data.to_dict()

                capture_session.append(capture_session_item)




        scope: Union[Unset, List[Optional[Dict[str, Any]]]] = UNSET
        if not isinstance(self.scope, Unset):
            scope = []
            for scope_item_data in self.scope:
                scope_item = scope_item_data.to_dict() if scope_item_data else None

                scope.append(scope_item)





        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "token": token,
        })
        if capture_session is not UNSET:
            field_dict["captureSession"] = capture_session
        if scope is not UNSET:
            field_dict["scope"] = scope

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.capture_session import CaptureSession
        from ..models.user_scope import UserScope
        d = src_dict.copy()
        token = d.pop("token")

        capture_session = []
        _capture_session = d.pop("captureSession", UNSET)
        for capture_session_item_data in (_capture_session or []):
            capture_session_item = CaptureSession.from_dict(capture_session_item_data)



            capture_session.append(capture_session_item)


        scope = []
        _scope = d.pop("scope", UNSET)
        for scope_item_data in (_scope or []):
            _scope_item = scope_item_data
            scope_item: Optional[UserScope]
            if _scope_item is None:
                scope_item = None
            else:
                scope_item = UserScope.from_dict(_scope_item)



            scope.append(scope_item)


        authenticate_capture_code_response = cls(
            token=token,
            capture_session=capture_session,
            scope=scope,
        )

        authenticate_capture_code_response.additional_properties = d
        return authenticate_capture_code_response

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
