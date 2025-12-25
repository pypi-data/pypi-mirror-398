import time

from formant.sdk.cloud.v2.formant_admin_api_client import AuthenticatedClient, Client
from formant.sdk.cloud.v2.formant_admin_api_client.api.auth import (
    auth_controller_login,
    auth_controller_refresh,
)
from formant.sdk.cloud.v2.formant_admin_api_client.models import (
    LoginRequest,
    LoginResult,
    RefreshRequest,
)
from formant.sdk.cloud.v2.formant_admin_api_client.types import Response

TOKEN_EXPIRATION_SECONDS = 3600


class Auth:
    def __init__(
        self, email: str, password: str, api: str, base_url: str, timeout: int = 30
    ):
        self._email = email
        self._password = password
        self._timeout = timeout
        self._api = api
        self._base_url = base_url
        self._headers = {
            "Content-Type": "application/json",
            "App-ID": "formant/python-cloud-sdk",
        }
        self._unauthenticated_client = Client(base_url="%s/admin" % base_url)
        self._token_expiry = None
        self._access_token = None
        self._refresh_token = None
        self._user_id = None
        self.organization_id = None

    def get_client(self):
        hasRefreshToken = self._refresh_token is not None
        accessTokenIsNone = self._access_token is None
        tokenHasExpired = (
            True
            if self._token_expiry is None
            else self._token_expiry < int(time.time())
        )
        shouldGetNewAccessToken = accessTokenIsNone or tokenHasExpired
        if hasRefreshToken:
            self._refresh_existing_client()
        elif shouldGetNewAccessToken:
            self._create_new_client()

        return self.client

    def _create_new_client(self):
        login_request = LoginRequest(
            email=self._email,
            password=self._password,
            token_expiration_seconds=TOKEN_EXPIRATION_SECONDS,
        )

        response: Response[LoginResult] = auth_controller_login.sync(
            client=self._unauthenticated_client, json_body=login_request
        )
        wasAuthenticationSuccessful = response is not None
        if not wasAuthenticationSuccessful:
            raise ValueError("Authentication failed")
        result = response.authentication

        self._token_expiry = int(time.time()) + 3530
        self._access_token = result.access_token
        self._refresh_token = result.refresh_token
        self.organization_id = result.organization_id
        self._user_id = result.user_id
        self._headers["Org-ID"] = result.organization_id
        self._headers["User-ID"] = result.user_id
        self.client = AuthenticatedClient(
            base_url="%s/%s" % (self._base_url, self._api),
            headers=self._headers,
            token=self._access_token,
        ).with_timeout(self._timeout)

    def _refresh_existing_client(self):
        refresh_request = RefreshRequest(
            self._refresh_token, token_expiration_seconds=TOKEN_EXPIRATION_SECONDS
        )
        response: Response[LoginResult] = auth_controller_refresh.sync(
            client=self._unauthenticated_client, json_body=refresh_request
        )
        result = response.authentication
        self._token_expiry = int(time.time()) + 3530
        self._access_token = result.access_token
        self.client = AuthenticatedClient(
            base_url=f"{self._base_url}/{self._api}", token=self._access_token
        )
