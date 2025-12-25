import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import attr
from dateutil.parser import isoparse

from ..models.partial_user_language import PartialUserLanguage
from ..models.partial_user_region import PartialUserRegion
from ..models.partial_user_sms_opt_in_status import PartialUserSmsOptInStatus
from ..models.partial_user_units import PartialUserUnits
from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.partial_user_tags import PartialUserTags
  from ..models.tag_sets import TagSets
  from ..models.user_scope import UserScope




T = TypeVar("T", bound="PartialUser")

@attr.s(auto_attribs=True)
class PartialUser:
    """
    Attributes:
        organization_id (Union[Unset, str]): ID of the organization to which this user belongs.
        account_id (Union[Unset, None, str]): ID of the account to which this user belongs.
        role_id (Union[Unset, None, str]): ID of this user's role.
        email (Union[Unset, str]): Email address of this user.
        external_user_id (Union[Unset, None, str]): Ignore this - for internal use only.
        first_name (Union[Unset, str]): First name of this user.
        last_name (Union[Unset, str]): Last name of this user.
        scope (Union[Unset, None, UserScope]):
        team_id (Union[Unset, None, str]): ID of the team to which this user belongs.
        phone_number (Union[Unset, str]): User's phone number (e.g., +14155550100).
        enabled (Union[Unset, bool]): Enable or disable this user. Set this to False to delete this user.
        is_organization_owner (Union[Unset, bool]): Should this user have organization owner privileges?
        terms_accepted (Union[Unset, str]): Has this user accepted Formant terms and conditions?
        last_logged_in (Union[Unset, None, datetime.datetime]):
        password_hash (Union[Unset, None, str]):
        is_single_sign_on (Union[Unset, bool]):
        sms_opt_in_status (Union[Unset, None, PartialUserSmsOptInStatus]):
        region (Union[Unset, PartialUserRegion]):
        is_service_account (Union[Unset, bool]):
        allow_custom_email_configuration (Union[Unset, bool]):
        job_title (Union[Unset, str]):
        language (Union[Unset, PartialUserLanguage]):
        units (Union[Unset, PartialUserUnits]):
        timezone (Union[Unset, str]):
        title (Union[Unset, None, str]): Title for the user.
        description (Union[Unset, None, str]):
        metadata (Union[Unset, Any]):
        grants (Union[Unset, TagSets]): A map of tag keys to an array of values
        id (Union[Unset, str]):
        created_at (Union[Unset, datetime.datetime]):
        updated_at (Union[Unset, datetime.datetime]):
        tags (Union[Unset, PartialUserTags]):
    """

    organization_id: Union[Unset, str] = UNSET
    account_id: Union[Unset, None, str] = UNSET
    role_id: Union[Unset, None, str] = UNSET
    email: Union[Unset, str] = UNSET
    external_user_id: Union[Unset, None, str] = UNSET
    first_name: Union[Unset, str] = UNSET
    last_name: Union[Unset, str] = UNSET
    scope: Union[Unset, None, 'UserScope'] = UNSET
    team_id: Union[Unset, None, str] = UNSET
    phone_number: Union[Unset, str] = UNSET
    enabled: Union[Unset, bool] = UNSET
    is_organization_owner: Union[Unset, bool] = UNSET
    terms_accepted: Union[Unset, str] = UNSET
    last_logged_in: Union[Unset, None, datetime.datetime] = UNSET
    password_hash: Union[Unset, None, str] = UNSET
    is_single_sign_on: Union[Unset, bool] = UNSET
    sms_opt_in_status: Union[Unset, None, PartialUserSmsOptInStatus] = UNSET
    region: Union[Unset, PartialUserRegion] = UNSET
    is_service_account: Union[Unset, bool] = UNSET
    allow_custom_email_configuration: Union[Unset, bool] = UNSET
    job_title: Union[Unset, str] = UNSET
    language: Union[Unset, PartialUserLanguage] = UNSET
    units: Union[Unset, PartialUserUnits] = UNSET
    timezone: Union[Unset, str] = UNSET
    title: Union[Unset, None, str] = UNSET
    description: Union[Unset, None, str] = UNSET
    metadata: Union[Unset, Any] = UNSET
    grants: Union[Unset, 'TagSets'] = UNSET
    id: Union[Unset, str] = UNSET
    created_at: Union[Unset, datetime.datetime] = UNSET
    updated_at: Union[Unset, datetime.datetime] = UNSET
    tags: Union[Unset, 'PartialUserTags'] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        organization_id = self.organization_id
        account_id = self.account_id
        role_id = self.role_id
        email = self.email
        external_user_id = self.external_user_id
        first_name = self.first_name
        last_name = self.last_name
        scope: Union[Unset, None, Dict[str, Any]] = UNSET
        if not isinstance(self.scope, Unset):
            scope = self.scope.to_dict() if self.scope else None

        team_id = self.team_id
        phone_number = self.phone_number
        enabled = self.enabled
        is_organization_owner = self.is_organization_owner
        terms_accepted = self.terms_accepted
        last_logged_in: Union[Unset, None, str] = UNSET
        if not isinstance(self.last_logged_in, Unset):
            last_logged_in = self.last_logged_in.isoformat() if self.last_logged_in else None

        password_hash = self.password_hash
        is_single_sign_on = self.is_single_sign_on
        sms_opt_in_status: Union[Unset, None, str] = UNSET
        if not isinstance(self.sms_opt_in_status, Unset):
            sms_opt_in_status = self.sms_opt_in_status.value if self.sms_opt_in_status else None

        region: Union[Unset, str] = UNSET
        if not isinstance(self.region, Unset):
            region = self.region.value

        is_service_account = self.is_service_account
        allow_custom_email_configuration = self.allow_custom_email_configuration
        job_title = self.job_title
        language: Union[Unset, str] = UNSET
        if not isinstance(self.language, Unset):
            language = self.language.value

        units: Union[Unset, str] = UNSET
        if not isinstance(self.units, Unset):
            units = self.units.value

        timezone = self.timezone
        title = self.title
        description = self.description
        metadata = self.metadata
        grants: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.grants, Unset):
            grants = self.grants.to_dict()

        id = self.id
        created_at: Union[Unset, str] = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: Union[Unset, str] = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        tags: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.tags, Unset):
            tags = self.tags.to_dict()


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if organization_id is not UNSET:
            field_dict["organizationId"] = organization_id
        if account_id is not UNSET:
            field_dict["accountId"] = account_id
        if role_id is not UNSET:
            field_dict["roleId"] = role_id
        if email is not UNSET:
            field_dict["email"] = email
        if external_user_id is not UNSET:
            field_dict["externalUserId"] = external_user_id
        if first_name is not UNSET:
            field_dict["firstName"] = first_name
        if last_name is not UNSET:
            field_dict["lastName"] = last_name
        if scope is not UNSET:
            field_dict["scope"] = scope
        if team_id is not UNSET:
            field_dict["teamId"] = team_id
        if phone_number is not UNSET:
            field_dict["phoneNumber"] = phone_number
        if enabled is not UNSET:
            field_dict["enabled"] = enabled
        if is_organization_owner is not UNSET:
            field_dict["isOrganizationOwner"] = is_organization_owner
        if terms_accepted is not UNSET:
            field_dict["termsAccepted"] = terms_accepted
        if last_logged_in is not UNSET:
            field_dict["lastLoggedIn"] = last_logged_in
        if password_hash is not UNSET:
            field_dict["passwordHash"] = password_hash
        if is_single_sign_on is not UNSET:
            field_dict["isSingleSignOn"] = is_single_sign_on
        if sms_opt_in_status is not UNSET:
            field_dict["smsOptInStatus"] = sms_opt_in_status
        if region is not UNSET:
            field_dict["region"] = region
        if is_service_account is not UNSET:
            field_dict["isServiceAccount"] = is_service_account
        if allow_custom_email_configuration is not UNSET:
            field_dict["allowCustomEmailConfiguration"] = allow_custom_email_configuration
        if job_title is not UNSET:
            field_dict["jobTitle"] = job_title
        if language is not UNSET:
            field_dict["language"] = language
        if units is not UNSET:
            field_dict["units"] = units
        if timezone is not UNSET:
            field_dict["timezone"] = timezone
        if title is not UNSET:
            field_dict["title"] = title
        if description is not UNSET:
            field_dict["description"] = description
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if grants is not UNSET:
            field_dict["grants"] = grants
        if id is not UNSET:
            field_dict["id"] = id
        if created_at is not UNSET:
            field_dict["createdAt"] = created_at
        if updated_at is not UNSET:
            field_dict["updatedAt"] = updated_at
        if tags is not UNSET:
            field_dict["tags"] = tags

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.partial_user_tags import PartialUserTags
        from ..models.tag_sets import TagSets
        from ..models.user_scope import UserScope
        d = src_dict.copy()
        organization_id = d.pop("organizationId", UNSET)

        account_id = d.pop("accountId", UNSET)

        role_id = d.pop("roleId", UNSET)

        email = d.pop("email", UNSET)

        external_user_id = d.pop("externalUserId", UNSET)

        first_name = d.pop("firstName", UNSET)

        last_name = d.pop("lastName", UNSET)

        _scope = d.pop("scope", UNSET)
        scope: Union[Unset, None, UserScope]
        if _scope is None:
            scope = None
        elif isinstance(_scope,  Unset):
            scope = UNSET
        else:
            scope = UserScope.from_dict(_scope)




        team_id = d.pop("teamId", UNSET)

        phone_number = d.pop("phoneNumber", UNSET)

        enabled = d.pop("enabled", UNSET)

        is_organization_owner = d.pop("isOrganizationOwner", UNSET)

        terms_accepted = d.pop("termsAccepted", UNSET)

        _last_logged_in = d.pop("lastLoggedIn", UNSET)
        last_logged_in: Union[Unset, None, datetime.datetime]
        if _last_logged_in is None:
            last_logged_in = None
        elif isinstance(_last_logged_in,  Unset):
            last_logged_in = UNSET
        else:
            last_logged_in = isoparse(_last_logged_in)




        password_hash = d.pop("passwordHash", UNSET)

        is_single_sign_on = d.pop("isSingleSignOn", UNSET)

        _sms_opt_in_status = d.pop("smsOptInStatus", UNSET)
        sms_opt_in_status: Union[Unset, None, PartialUserSmsOptInStatus]
        if _sms_opt_in_status is None:
            sms_opt_in_status = None
        elif isinstance(_sms_opt_in_status,  Unset):
            sms_opt_in_status = UNSET
        else:
            sms_opt_in_status = PartialUserSmsOptInStatus(_sms_opt_in_status)




        _region = d.pop("region", UNSET)
        region: Union[Unset, PartialUserRegion]
        if isinstance(_region,  Unset):
            region = UNSET
        else:
            region = PartialUserRegion(_region)




        is_service_account = d.pop("isServiceAccount", UNSET)

        allow_custom_email_configuration = d.pop("allowCustomEmailConfiguration", UNSET)

        job_title = d.pop("jobTitle", UNSET)

        _language = d.pop("language", UNSET)
        language: Union[Unset, PartialUserLanguage]
        if isinstance(_language,  Unset):
            language = UNSET
        else:
            language = PartialUserLanguage(_language)




        _units = d.pop("units", UNSET)
        units: Union[Unset, PartialUserUnits]
        if isinstance(_units,  Unset):
            units = UNSET
        else:
            units = PartialUserUnits(_units)




        timezone = d.pop("timezone", UNSET)

        title = d.pop("title", UNSET)

        description = d.pop("description", UNSET)

        metadata = d.pop("metadata", UNSET)

        _grants = d.pop("grants", UNSET)
        grants: Union[Unset, TagSets]
        if isinstance(_grants,  Unset):
            grants = UNSET
        else:
            grants = TagSets.from_dict(_grants)




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




        _tags = d.pop("tags", UNSET)
        tags: Union[Unset, PartialUserTags]
        if isinstance(_tags,  Unset):
            tags = UNSET
        else:
            tags = PartialUserTags.from_dict(_tags)




        partial_user = cls(
            organization_id=organization_id,
            account_id=account_id,
            role_id=role_id,
            email=email,
            external_user_id=external_user_id,
            first_name=first_name,
            last_name=last_name,
            scope=scope,
            team_id=team_id,
            phone_number=phone_number,
            enabled=enabled,
            is_organization_owner=is_organization_owner,
            terms_accepted=terms_accepted,
            last_logged_in=last_logged_in,
            password_hash=password_hash,
            is_single_sign_on=is_single_sign_on,
            sms_opt_in_status=sms_opt_in_status,
            region=region,
            is_service_account=is_service_account,
            allow_custom_email_configuration=allow_custom_email_configuration,
            job_title=job_title,
            language=language,
            units=units,
            timezone=timezone,
            title=title,
            description=description,
            metadata=metadata,
            grants=grants,
            id=id,
            created_at=created_at,
            updated_at=updated_at,
            tags=tags,
        )

        partial_user.additional_properties = d
        return partial_user

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
