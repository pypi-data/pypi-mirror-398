from formant.sdk.cloud.v2.src.auth import Auth
from formant.sdk.cloud.v2.src.resources.ingest.ingest import Ingest


class IngestAPI(Auth):
    def __init__(self, email: str, password: str, base_url: str, timeout: int = 30):
        super().__init__(
            email=email,
            password=password,
            api="ingest",
            base_url=base_url,
            timeout=timeout,
        )

        self.ingest = Ingest(self.get_client)
