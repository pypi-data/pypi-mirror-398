from formant.sdk.cloud.v2.src.auth import Auth
from formant.sdk.cloud.v2.src.resources.adapters.adapters import Adapters
from formant.sdk.cloud.v2.src.resources.annotations.annotations import Annotations
from formant.sdk.cloud.v2.src.resources.commands.commands import Commands
from formant.sdk.cloud.v2.src.resources.devices.devices import Devices
from formant.sdk.cloud.v2.src.resources.events.events import Events
from formant.sdk.cloud.v2.src.resources.files.files import Files
from formant.sdk.cloud.v2.src.resources.views.views import Views


class AdminAPI(Auth):
    def __init__(self, email: str, password: str, base_url: str, timeout: int = 30):
        super().__init__(
            email=email,
            password=password,
            api="admin",
            base_url=base_url,
            timeout=timeout,
        )
        self.devices = Devices(self.get_client)
        self.commands = Commands(self.get_client)
        self.views = Views(self.get_client)
        self.annotations = Annotations(self.get_client)
        self.events = Events(self.get_client)
        self.files = Files(self.get_client)
        self.adapters = Adapters(self.get_client)

        self.client = self.get_client()
