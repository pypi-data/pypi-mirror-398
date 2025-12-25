from formant.sdk.cloud.v2.src.auth import Auth
from formant.sdk.cloud.v2.src.resources.count.count import Count
from formant.sdk.cloud.v2.src.resources.metadata.metadata import Metadata
from formant.sdk.cloud.v2.src.resources.online_devices.online_devices import (
    OnlineDevices,
)
from formant.sdk.cloud.v2.src.resources.presence.presence import Presence
from formant.sdk.cloud.v2.src.resources.queries.queries import Queries
from formant.sdk.cloud.v2.src.resources.stream_current.stream_current import (
    StreamCurrent,
)


class QueryAPI(Auth):
    def __init__(self, email: str, password: str, base_url: str, timeout: int = 30):
        super().__init__(
            email=email,
            password=password,
            api="queries",
            base_url=base_url,
            timeout=timeout,
        )

        self.queries = Queries(self.get_client)
        self.count = Count(self.get_client)
        self.stream_current = StreamCurrent(self.get_client)
        self.metadata = Metadata(self.get_client)
        self.online_devices = OnlineDevices(self.get_client)
        self.presence = Presence(self.get_client)
