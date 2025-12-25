
from typing import Any, Callable, Union
from formant.sdk.cloud.v2.formant_admin_api_client import AuthenticatedClient, Client

class Resources():

    def __init__(self, get_client: Callable[([None], Union[(Any, Client, AuthenticatedClient)])]):
        self._get_client = get_client
