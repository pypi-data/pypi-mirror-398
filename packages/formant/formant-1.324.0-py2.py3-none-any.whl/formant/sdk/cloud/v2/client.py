import os

from .src.admin_api import AdminAPI
from .src.ingest_api import IngestAPI
from .src.query_api import QueryAPI

DEFAULT_BASE_URL = "https://api.formant.io/v1"


class Client:
    """Creates a client to interact with the Formant cloud. Allows you to create, update,
    and delete entities in your Formant organization.

    .. highlight:: python
    .. code-block:: python

        from formant.sdk.cloud.v2 import Client
        fclient = Client()
    """

    def __init__(
        self,
        email: str = None,
        password: str = None,
        base_url: str = DEFAULT_BASE_URL,
    ):
        """
        :param email: Formant email address. This must be provided, or the ``FORMANT_EMAIL``
            environment variable must be set. Defaults to None
        :type email: str, optional
        :param password: Formant password. This must be provided, or the ``FORMANT_PASSWORD``
            environment variable must be set. Defaults to None
        :type password: str, optional
        :param base_url: API base URL, defaults to DEFAULT_BASE_URL
        :type base_url: str, optional
        :raises ValueError: ``email argument missing and FORMANT_EMAIL environment variable not set!``
        :raises ValueError: ``password argument missing and FORMANT_PASSWORD environment variable not set``
        """
        self._email = os.getenv("FORMANT_EMAIL") if email is None else email
        self._password = os.getenv("FORMANT_PASSWORD") if password is None else password
        if self._email is None:
            raise ValueError(
                "email argument missing and FORMANT_EMAIL environment variable not set!"
            )
        if self._password is None:
            raise ValueError(
                "password argument missing and FORMANT_PASSWORD environment variable not set"
            )
        self.admin = AdminAPI(
            email=self._email, password=self._password, base_url=base_url
        )
        self.query = QueryAPI(
            email=self._email, password=self._password, base_url=base_url
        )
        self.ingest = IngestAPI(
            email=self._email, password=self._password, base_url=base_url
        )
