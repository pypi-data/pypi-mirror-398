# flake8: noqa
import sys
from .v1 import Client

if sys.version_info >= (3, 6) and __name__ == "formant.sdk.cloud":
    from .v2 import Client as ClientV2

    sys.modules.update({"formant.sdk.cloud.ClientV2": ClientV2})
