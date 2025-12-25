import logging
import sys
import time
import json
from typing import Any, Callable, Dict, List, Optional, Union, Tuple
from threading import Lock, Thread
from multiprocessing.pool import ThreadPool
import grpc
from formant.protos.agent.v1 import agent_pb2, agent_pb2_grpc
from formant.protos.model.v1 import (
    commands_pb2,
    datapoint_pb2,
    event_pb2,
    math_pb2,
    media_pb2,
    navigation_pb2,
    health_pb2,
    text_pb2,
    intervention_pb2,
    file_pb2,
)
from typing_extensions import Literal
from grpc_status import rpc_status


from formant.sdk.agent.v1.localization.localization_manager import LocalizationManager

from .exceptions import (
    InvalidArgument,
    handle_agent_exceptions,
    handle_grpc_exceptions,
    handle_post_data_exceptions,
)
from .cancellable_stream_thread import CancellableStreamThread

import os

DEFAULT_AGENT_URL = "unix:///var/lib/formant/agent.sock"
DEFAULT_IMAGE_CONTENT_TYPE = "image/jpg"  # type: Literal["image/jpg"]
DEFAULT_SEVERITY_TYPE = "info"  # type: Literal["info"]
ALLOWED_IMAGE_CONTENT_TYPES = ["image/jpg", "image/jpeg", "image/png"]
ALLOWED_VIDEO_CONTENT_TYPES = ["video/h264"]
ALLOWED_IMAGE_AND_VIDEO_CONTENT_TYPES = (
    ALLOWED_IMAGE_CONTENT_TYPES + ALLOWED_VIDEO_CONTENT_TYPES
)
ALLOWED_SEVERITY_TYPES = ["info", "warning", "critical", "error"]
DEFAULT_LOCALIZATION_STEAM_NAME = "localization"
DEFAULT_THROTTLE_HZ = 5


def current_timestamp():
    return int(time.time() * 1000)


def set_severity_pb(
    given,  # type: str
):
    severity_pb = event_pb2.INFO
    if given == "warning":
        severity_pb = event_pb2.WARNING
    elif given == "critical":
        severity_pb = event_pb2.CRITICAL
    elif given == "error":
        severity_pb = event_pb2.ERROR
    return severity_pb


def validate_string_in_array(
    given,  # type: Any
    expected_types,  # type: List[str]
    input_name,  # type: str
):
    method_name = sys._getframe(1).f_code.co_name
    if given not in expected_types:
        raise TypeError(
            method_name
            + input_name
            + " is "
            + given
            + "' but must be one of: "
            + str(expected_types)
        )


def validate_type(
    given,  # type: Any
    expected_types,  # type: List[type]
):
    if not any([isinstance(given, t) for t in expected_types]):
        method_name = sys._getframe(1).f_code.co_name

        # e.g.
        # post_text input 'None' has type <class 'NoneType'>,
        # but expected one of: [<class 'str'>]
        raise TypeError(
            method_name
            + " input '"
            + str(given)
            + "' has type "
            + str(type(given))
            + ", but expected one of: "
            + str(expected_types)
        )


class Client:
    """
    A client for interacting with the Formant agent.
    Automatically handles connection and reconnection to the agent.
    There are methods for:

    * Ingesting telemetry datapoints

    * Creating events

    * Handling commands

    * Ingesting transform frames

    * Reading application configuration

    * Handling teleop control datapoints
    """

    def __init__(
        self,
        agent_url=DEFAULT_AGENT_URL,  # type: str
        enable_logging=True,  # type: bool
        ignore_throttled=False,  # type: bool
        ignore_unavailable=False,  # type: bool
        local_dev=False,  # type: bool
        thread_pool_size=10,  # type: int
    ):
        """
        :param agent_url: The address of the Formant agent API.
        :param enable_logging: If ``True``, this client will log some information to ``stdout``.
        :param ignore_throttled: If ``True``, ``telemetry datapoint throttle`` errors
            will not raise Exceptions. Throttled datapoints are still valid for teleoperation.
        :param ignore_unavailable: If ``True``, ``Formant agent unavailable`` errors
            will not raise Exceptions.
        """

        self.logger = logging.getLogger("formant")  # type: Optional[logging.Logger]

        if enable_logging:
            self.logger.setLevel(logging.INFO)
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter("%(levelname)s: %(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        else:
            self.logger.addHandler(logging.NullHandler())

        self.ignore_throttled = ignore_throttled
        self.ignore_unavailable = ignore_unavailable
        self._lock = Lock()
        self._thread_pool = ThreadPool(processes=thread_pool_size)
        self._agent_url = agent_url  # type: str
        if local_dev == True:
            self._agent_url = os.getenv(
                "FORMANT_AGENT_URL", DEFAULT_AGENT_URL
            )  # type: str
        self._app_config = {}  # type: Dict[str, str]
        self._config_update_callbacks = []  # type: List[Callable[[], None]]
        self._command_request_callback_streams = (
            {}
        )  # type: Dict[Callable[..., None], CancellableStreamThread]
        self._teleop_callback_streams = (
            {}
        )  # type: Dict[Callable[..., None], CancellableStreamThread]
        self._teleop_heartbeat_callback_streams = (
            {}
        )  # type: Dict[Callable[..., None], CancellableStreamThread]
        self._telemetry_listener_callback_streams = (
            {}
        )  # type: Dict[Callable[..., None], CancellableStreamThread]
        self._custom_data_channel_message_callback_streams = (
            {}
        )  # type: Dict[Callable[..., None], CancellableStreamThread]
        self._localization_manager_cache = {}  # type: Dict[str,LocalizationManager]
        self._connected = False
        self._setup_agent_communication()

    def get_localization_manager(
        self,
        stream_name=DEFAULT_LOCALIZATION_STEAM_NAME,  # type: str
        throttle_hz=DEFAULT_THROTTLE_HZ,  # type:float
    ):
        # type: (...) -> LocalizationManager
        validate_type(stream_name, [str])
        if self._localization_manager_cache.get(stream_name, None) is None:
            self._localization_manager_cache[stream_name] = LocalizationManager(
                stream_name, self, throttle_hz
            )
        return self._localization_manager_cache[stream_name]

    @handle_agent_exceptions
    def get_agent_id(self):
        """
        Gets the Device ID for this device.

        :rtype: str
        """
        return self.get_agent_configuration().id

    @handle_agent_exceptions
    def get_agent_configuration(self):
        return self.agent_stub.GetAgentConfiguration(
            agent_pb2.GetAgentConfigurationRequest()
        ).configuration

    # Ingesting telemetry datapoints

    @handle_agent_exceptions
    def post_text(
        self,
        stream,  # type: str
        value,  # type: str
        tags=None,  # type: Optional[Dict[str, str]]
        timestamp=None,  # type: Optional[int]
    ):
        # type: (...) -> None
        """
        Post a text datapoint to a stream.

        :param stream: The name of the Formant stream to post the datapoint on
        :param value: The text datapoint value
        :param tags: Tags to include on the posted datapoint
        :param timestamp: Unix timestamp in milliseconds for the posted datapoint.
            Uses the current time by default
        :rtype: None

        .. highlight:: python
        .. code-block:: python

            from formant.sdk.agent.v1 import Client

            fclient = Client()
            fclient.post_text(
                "example.text",
                "Processed 9 items"
            )
        """

        datapoint = self.prepare_text(stream, value, tags, timestamp)
        self.post_data(datapoint)

    @handle_agent_exceptions
    def post_json(
        self,
        stream,  # type: str
        value,  # type: str
        tags=None,  # type: Optional[Dict[str, str]]
        timestamp=None,  # type: Optional[int]
    ):
        # type: (...) -> None
        """
        Post a JSON datapoint to a telemetry stream.

        :param stream: The name of the Formant stream to post the datapoint on
        :param value: The encoded JSON datapoint value
        :param tags: Tags to include on the posted datapoint
        :param timestamp: Unix timestamp in milliseconds for the posted datapoint.
            Uses the current time by default
        :rtype: None
        """

        datapoint = self.prepare_json(stream, value, tags, timestamp)
        self.post_data(datapoint)

    @handle_agent_exceptions
    def post_numeric(
        self,
        stream,  # type: str
        value,  # type: Union[float, int]
        tags=None,  # type: Optional[Dict[str, str]]
        timestamp=None,  # type: Optional[int]
    ):
        # type: (...) -> None
        """
        Post a numeric datapoint to a telemetry stream.

        :param stream: The name of the Formant stream to post the datapoint on
        :param value: The numeric datapoint value
        :param tags: Tags to include on the posted datapoint
        :param timestamp: Unix timestamp in milliseconds for the posted datapoint.
            Uses the current time by default
        :rtype: None
        """

        datapoint = self.prepare_numeric(stream, value, tags, timestamp)
        self.post_data(datapoint)

    @handle_agent_exceptions
    def post_numericset(
        self,
        stream,  # type: str
        numerics_dict,  # type: Dict[str, Tuple[Union[float, int], Optional[str]]]
        tags=None,  # type: Optional[Dict[str, str]]
        timestamp=None,  # type: Optional[int]
    ):
        # type: (...) -> None
        """
        Post a numeric set datapoint to a telemetry stream.
        Numeric sets are collections of related numeric datapoints.

        :param stream: The name of the Formant stream to post the datapoint on
        :param numerics_dict: The numeric set datapoint value,
            a dictionary mapping names to (numeric value, units) tuples.
        :param tags: Tags to include on the posted datapoint
        :param timestamp: Unix timestamp in milliseconds for the posted datapoint.
            Uses the current time by default
        :rtype: None

        .. highlight:: python
        .. code-block:: python

            from formant.sdk.agent.v1 import Client

            fclient = Client()
            fclient.post_numericset(
                "example.numericset2",
                {
                    "frequency": (998, "Hz"),
                    "usage": (30, "percent"),
                    "warp factor": (6.0, None),
                },
            )
        """

        datapoint = self.prepare_numericset(stream, numerics_dict, tags, timestamp)
        self.post_data(datapoint)

    @handle_agent_exceptions
    def post_image(
        self,
        stream,  # type: str
        value=None,  # type: Optional[bytes]
        url=None,  # type: Optional[str]
        content_type="image/jpg",
        # type: Literal["image/jpg", "image/png", "video/h264"]
        tags=None,  # type: Optional[Dict[str, str]]
        timestamp=None,  # type: Optional[int]
    ):
        # type: (...) -> None
        """
        Post an image datapoint to a telemetry stream.

        :param stream: The name of the Formant stream to post the datapoint on
        :param value: The datapoint value: raw bytes of an encoded image or frame
        :param url: The datapoint url: path to local file or valid remote URL for
            remote files
        :param content_type: The format of the encoded image or frame.
            Defaults to ``image/jpg``.
        :param tags: Tags to include on the posted datapoint
        :param timestamp: Unix timestamp in milliseconds for the posted datapoint.
            Uses the current time by default
        :rtype: None
        """
        datapoint = self.prepare_image(
            stream, value, url, content_type, tags, timestamp
        )
        self.post_data(datapoint)

    @handle_agent_exceptions
    def post_bitset(
        self,
        stream,  # type: str
        bitset_dict,  # type: Dict[str, bool]
        tags=None,  # type: Optional[Dict[str, str]]
        timestamp=None,  # type: Optional[int]
    ):
        # type: (...) -> None
        """
        Post a bitset datapoint to a telemetry stream.
        A bitset is a collection of related boolean states.

        :param stream: The name of the Formant stream to post the datapoint on
        :param bitset_dict: The datapoint value, a dictionary mapping names to booleans
        :param tags: Tags to include on the posted datapoint
        :param timestamp: Unix timestamp in milliseconds for the posted datapoint.
            Uses the current time by default
        :rtype: None

        .. highlight:: python
        .. code-block:: python

            from formant.sdk.agent.v1 import Client

            fclient = Client()
            fclient.post_bitset(
                "example.bitset",
                {
                    "standing": False,
                    "walking": False,
                    "sitting": True
                }
            )
        """

        datapoint = self.prepare_bitset(stream, bitset_dict, tags, timestamp)
        self.post_data(datapoint)

    @handle_agent_exceptions
    def post_geolocation(
        self,
        stream,  # type: str
        latitude,  # type: Union[float, int]
        longitude,  # type: Union[float, int]
        tags=None,  # type: Optional[Dict[str, str]]
        timestamp=None,  # type: Optional[int]
        altitude=None,  # type: Union[float, int]
        orientation=None,  # type: Union[float, int]
    ):
        # type: (...) -> None
        """
        Post a geolocation datapoint to a telemetry stream.

        :param stream: The name of the Formant stream to post the datapoint on
        :param latitude: The datapoint value's latitude
        :param longitude: The datapoint value's longitude
        :param tags: Tags to include on the posted datapoint
        :param timestamp: Unix timestamp in milliseconds for the posted datapoint.
            Uses the current time by default
        :rtype: None
        """

        datapoint = self.prepare_geolocation(
            stream, latitude, longitude, tags, timestamp, altitude, orientation
        )
        self.post_data(datapoint)

    @handle_agent_exceptions
    def post_battery(
        self,
        stream,  # type: str
        percentage,  # type: Union[int, float]
        voltage=None,  # type: Optional[Union[int, float]]
        current=None,  # type: Optional[Union[int, float]]
        charge=None,  # type: Optional[Union[int, float]]
        tags=None,  # type: Optional[Dict[str, str]]
        timestamp=None,  # type: Optional[int]
    ):
        # type: (...) -> None
        """
        Post a battery datapoint to a telemetry stream. Only percentage is required.

        :param stream: The name of the Formant stream to post the datapoint on
        :param percentage: The battery charge percentage
        :param voltage: The battery voltage
        :param current: The battery current
        :param charge: The battery charge
        :param tags: Tags to include on the posted datapoint
        :param timestamp: Unix timestamp in milliseconds for the posted datapoint.
            Uses the current time by default
        :rtype: None
        """

        datapoint = self.prepare_battery(
            stream, percentage, voltage, current, charge, tags, timestamp
        )
        self.post_data(datapoint)

    @handle_agent_exceptions
    def post_file(
        self,
        stream,  # type: str
        url=None,  # type: str
        filename=None,  # type: Optional[str]
        tags=None,  # type: Optional[Dict[str, str]]
        timestamp=None,  # type: Optional[int]
    ):
        # type: (...) -> None
        """
        Post a file to a telemetry stream.

        :param stream: The name of the Formant stream to post the file on
        :param url: The file url: path to local file or valid remote URL for
            remote files
        :param filename: The file name: name displayed inside Formant module
        :param tags: Tags to include on the posted file
        :param timestamp: Unix timestamp in milliseconds for the posted file.
            Uses the current time by default
        :rtype: None

        .. highlight:: python
        .. code-block:: python

            from formant.sdk.agent.v1 import Client

            fclient = Client()
            fclient.post_file(
                "example.file",
                /home/user/Desktop/data/planets.csv,
                planets.csv,
            )
        """

        datapoint = self.prepare_file(stream, url, filename, tags, timestamp)
        self.post_data(datapoint)

    @handle_agent_exceptions
    @handle_grpc_exceptions
    def post_data(self, datapoint):
        # type: (...) -> None
        """
        :param datapoint:
        :rtype: None
        """
        self.agent_stub.PostData(datapoint)

    @handle_post_data_exceptions
    def post_data_multi(self, datapoints):
        # type: (...) -> None
        """
        :param datapoints:
        :rtype: None
        """
        request = agent_pb2.PostDataMultiRequest(datapoints=datapoints)
        self.agent_stub.PostDataMulti(request)

    def prepare_text(
        self,
        stream,  # type: str
        value,  # type: str
        tags=None,  # type: Optional[Dict[str, str]]
        timestamp=None,  # type: Optional[int]
    ):
        # type: (...) -> datapoint_pb2.Datapoint
        """
        Prepare a text datapoint without posting it.

        :param stream: The name of the Formant stream for the datapoint
        :param value: The text datapoint value
        :param tags: Tags for the datapoint
        :param timestamp: Unix timestamp in milliseconds for the datapoint.
            Uses the current time by default
        :rtype: datapoint_pb2.Datapoint
        """
        validate_type(value, [str])

        return datapoint_pb2.Datapoint(
            stream=stream,
            text=text_pb2.Text(value=value),
            tags=tags if tags else {},
            timestamp=timestamp if timestamp else current_timestamp(),
        )

    def prepare_json(
        self,
        stream,  # type: str
        value,  # type: str
        tags=None,  # type: Optional[Dict[str, str]]
        timestamp=None,  # type: Optional[int]
    ):
        # type (...) -> datapoint_pb2.Datapoint
        """
        Prepare a JSON datapoint without posting it.

        :param stream: (str) The name of the Formant stream for the datapoint
        :param value: (str) The encoded JSON datapoint value
        :param tags: (Optional[Dict[str, str]]) Tags for the datapoint
        :param timestamp: (Optional[int]) Unix timestamp in milliseconds for the datapoint.
            Uses the current time by default
        :rtype: datapoint_pb2.Datapoint
        """
        validate_type(value, [str])

        return datapoint_pb2.Datapoint(
            stream=stream,
            json=text_pb2.Json(value=value),
            timestamp=timestamp if timestamp else int(time.time() * 1000),
            tags=tags if tags else {},
        )

    def prepare_numeric(
        self,
        stream,  # type: str
        value,  # type: Union[float, int]
        tags=None,  # type: Optional[Dict[str, str]]
        timestamp=None,  # type: Optional[int]
    ):
        # type (...) -> datapoint_pb2.Datapoint
        """
        Prepare a numeric datapoint without posting it.

        :param stream: (str) The name of the Formant stream for the datapoint
        :param value: (Union[float, int]) The numeric datapoint value
        :param tags: (Optional[Dict[str, str]]) Tags for the datapoint
        :param timestamp: (Optional[int]) Unix timestamp in milliseconds for the datapoint.
            Uses the current time by default
        :rtype: datapoint_pb2.Datapoint
        """
        validate_type(value, [float, int])

        return datapoint_pb2.Datapoint(
            stream=stream,
            numeric=math_pb2.Numeric(value=value),
            tags=tags if tags else {},
            timestamp=timestamp if timestamp else current_timestamp(),
        )

    def prepare_numericset(
        self,
        stream,  # type: str
        numerics_dict,  # type: Dict[str, Tuple[Union[float, int], Optional[str]]]
        tags=None,  # type: Optional[Dict[str, str]]
        timestamp=None,  # type: Optional[int]
    ):
        # type (...) -> datapoint_pb2.Datapoint
        """
        Prepare a numeric set datapoint without posting it.

        :param stream: (str) The name of the Formant stream for the datapoint
        :param numerics_dict: (Dict[str, Tuple[Union[float, int], Optional[str]]]) The numeric set datapoint value,
            a dictionary mapping names to (numeric value, units) tuples.
        :param tags: (Optional[Dict[str, str]]) Tags for the datapoint
        :param timestamp: (Optional[int]) Unix timestamp in milliseconds for the datapoint.
            Uses the current time by default
        :rtype: The prepared numeric set datapoint
        :raises: ``TypeError: value v for key k in numericset must have length of 2``
        """
        validate_type(numerics_dict, [dict])

        numeric_set = math_pb2.NumericSet()
        for k, v in numerics_dict.items():
            validate_type(k, [str])
            validate_type(v, [tuple])
            if len(v) != 2:
                raise TypeError(
                    "value %s for key %s in numericset must have length of 2" % (v, k)
                )
            validate_type(v[0], [float, int])
            if v[1]:
                validate_type(v[1], [str])
            numeric_set.numerics.extend(
                [
                    math_pb2.NumericSetEntry(
                        value=v[0],
                        label=k,
                        unit=v[1] if v[1] else None,
                    )
                ]
            )

        return datapoint_pb2.Datapoint(
            stream=stream,
            numeric_set=numeric_set,
            tags=tags if tags else {},
            timestamp=timestamp if timestamp else current_timestamp(),
        )

    def prepare_image(
        self,
        stream,  # type: str
        value=None,  # type: Optional[bytes]
        url=None,  # type: Optional[str]
        content_type="image/jpg",
        # type: Literal["image/jpg", "image/png", "video/h264"]
        tags=None,  # type: Optional[Dict[str, str]]
        timestamp=None,  # type: Optional[int]
    ):
        # type (...) -> datapoint_pb2.Datapoint
        """
        Prepare an image datapoint without posting it.

        :param stream: (str) The name of the Formant stream for the datapoint
        :param value: (Optional[bytes]) The datapoint value: raw bytes of an encoded image or frame
        :param url: (Optional[str]) The datapoint url: path to a local file or valid remote URL for
            remote files
        :param content_type: (Literal["image/jpg", "image/png", "video/h264"]) The format of the encoded image or frame.
            Defaults to ``"image/jpg"``.
        :param tags: (Optional[Dict[str, str]]) Tags for the datapoint
        :param timestamp: (Optional[int]) Unix timestamp in milliseconds for the datapoint.
            Uses the current time by default
        :rtype: datapoint_pb2.Datapoint
        :raises: ``InvalidArgument: One of [url, value] must be used.``
        """

        if value is None and url is None:
            raise InvalidArgument("One of [url, value] must be used.")

        if value is not None and url is not None:
            raise InvalidArgument("Only one of [url, value] can be used.")

        if value is not None:
            validate_type(value, [bytes])

        if url is not None:
            validate_type(url, [str])

        validate_string_in_array(
            content_type, ALLOWED_IMAGE_AND_VIDEO_CONTENT_TYPES, "content_type"
        )

        return datapoint_pb2.Datapoint(
            stream=stream,
            image=media_pb2.Image(raw=value, url=url, content_type=content_type),
            tags=tags if tags else {},
            timestamp=timestamp if timestamp else current_timestamp(),
        )

    def prepare_bitset(
        self,
        stream,  # type: str
        bitset_dict,  # type: Dict[str, bool]
        tags=None,  # type: Optional[Dict[str, str]]
        timestamp=None,  # type: Optional[int]
    ):
        # type(...) -> datapoint_pb2.Datapoint
        """
        Prepare a bitset datapoint without posting it.

        :param stream: (str) The name of the Formant stream for the datapoint
        :param bitset_dict: (Dict[str, bool]) The datapoint value, a dictionary mapping names to booleans
        :param tags: (Optional[Dict[str, str]]) Tags for the datapoint
        :param timestamp: (Optional[int]) Unix timestamp in milliseconds for the datapoint.
            Uses the current time by default
        :rtype: datapoint_pb2.Datapoint
        """
        validate_type(bitset_dict, [dict])

        bitset = math_pb2.Bitset()
        for k, v in bitset_dict.items():
            validate_type(k, [str])
            validate_type(v, [bool])
            bitset.bits.extend([math_pb2.Bit(key=k, value=v)])

        return datapoint_pb2.Datapoint(
            stream=stream,
            bitset=bitset,
            tags=tags if tags else {},
            timestamp=timestamp if timestamp else current_timestamp(),
        )

    def prepare_geolocation(
        self,
        stream,  # type: str
        latitude,  # type: Union[float, int]
        longitude,  # type: Union[float, int]
        tags=None,  # type: Optional[Dict[str, str]]
        timestamp=None,  # type: Optional[int]
        altitude=None,  # type: Union[float, int]
        orientation=None,  # type: Union[float, int]
    ):
        """
        Prepare a geolocation datapoint without posting it.

        :param stream: (str) The name of the Formant stream for the datapoint
        :param latitude: (Union[float, int]) The datapoint value's latitude
        :param longitude: (Union[float, int]) The datapoint value's longitude
        :param tags: (Optional[Dict[str, str]]) Tags for the datapoint
        :param timestamp: (Optional[int]) Unix timestamp in milliseconds for the datapoint.
            Uses the current time by default
        :param altitude: (Union[float, int]) The altitude value (optional)
        :param orientation: (Union[float, int]) The orientation value (optional)
        :return: The prepared geolocation datapoint
        :rtype: datapoint_pb2.Datapoint
        """
        for _ in [latitude, longitude]:
            validate_type(_, [float, int])

        return datapoint_pb2.Datapoint(
            stream=stream,
            location=navigation_pb2.Location(
                latitude=latitude,
                longitude=longitude,
                altitude=altitude,
                orientation=orientation,
            ),
            tags=tags if tags else {},
            timestamp=timestamp if timestamp else current_timestamp(),
        )

    def prepare_battery(
        self,
        stream,  # type: str
        percentage,  # type: Union[int, float]
        voltage=None,  # type: Optional[Union[int, float]]
        current=None,  # type: Optional[Union[int, float]]
        charge=None,  # type: Optional[Union[int, float]]
        tags=None,  # type: Optional[Dict[str, str]]
        timestamp=None,  # type: Optional[int]
    ):
        """
        Prepare a battery datapoint without posting it.

        :param stream: (str) The name of the Formant stream for the datapoint
        :param percentage: (Union[int, float]) The battery charge percentage
        :param voltage: (Optional[Union[int, float]]) The battery voltage (optional)
        :param current: (Optional[Union[int, float]]) The battery current (optional)
        :param charge: (Optional[Union[int, float]]) The battery charge (optional)
        :param tags: (Optional[Dict[str, str]]) Tags for the datapoint
        :param timestamp: (Optional[int]) Unix timestamp in milliseconds for the datapoint.
            Uses the current time by default
        :return: The prepared battery datapoint
        :rtype: datapoint_pb2.Datapoint
        """
        for _ in [percentage, voltage, current, charge]:
            if _:
                validate_type(_, [float, int])

        battery = health_pb2.Battery()
        battery.percentage = percentage
        if voltage is not None:
            battery.voltage = voltage
        if current is not None:
            battery.current = current
        if charge is not None:
            battery.charge = charge

        return datapoint_pb2.Datapoint(
            stream=stream,
            battery=battery,
            tags=tags if tags else {},
            timestamp=timestamp if timestamp else current_timestamp(),
        )

    def prepare_file(
        self,
        stream,  # type: str
        url=None,  # type: str
        filename=None,  # type: Optional[str]
        tags=None,  # type: Optional[Dict[str, str]]
        timestamp=None,  # type: Optional[int]
    ):
        """
        Prepare a file datapoint without posting it.

        :param stream: (str) The name of the Formant stream for the datapoint
        :param url: (str) The file url: path to a local file or valid remote URL for remote files
        :param filename: (Optional[str]) The file name: name displayed inside Formant module
        :param tags: (Optional[Dict[str, str]]) Tags for the datapoint
        :param timestamp: (Optional[int]) Unix timestamp in milliseconds for the datapoint.
            Uses the current time by default
        :return: The prepared file datapoint
        :rtype: datapoint_pb2.Datapoint
        """
        validate_type(filename, [str])
        validate_type(url, [str])

        return datapoint_pb2.Datapoint(
            stream=stream,
            file=file_pb2.File(url=url, filename=filename),
            tags=tags if tags else {},
            timestamp=timestamp if timestamp else current_timestamp(),
        )

    def register_telemetry_listener_callback(
        self,
        f,  # type: Callable[[datapoint_pb2.Datapoint], None]
        stream_filter=None,  # type: Optional[List[str]]
    ):
        # type : (...) -> None
        """
        Datapoints posted to the Formant agent whose "stream" value matches an element
        of the given stream filter will be streamed into the provided callback.
        If no stream filter is provided, datapoints from all streams
        will be received.

        :param f: A callback that will be called when a datapoint is posted
            to the Formant agent
        :param stream_filter: A list of stream names. The provided callback
            is only called for datapoints whose stream name is in this list
        """
        with self._lock:

            def create_stream():
                return self._get_telemetry_listener_stream(stream_filter=stream_filter)

            self._telemetry_listener_callback_streams[f] = CancellableStreamThread(
                f,
                create_stream,
                self.logger,
                ignore_unavailable=self.ignore_unavailable,
            )

    def unregister_telemetry_listener_callback(
        self, f  # type: Callable[[], None]
    ):
        # type : (...) -> None
        """
        Unregisters previously registered telemetry loopback callback.

        :param f: The telemetry loopback callback to be unregistered
        """
        with self._lock:
            stream = self._telemetry_listener_callback_streams.pop(f, None)
            if stream is not None:
                stream.cancel()

    # Ingesting transform frames

    @handle_agent_exceptions
    def set_base_frame_id(
        self, base_reference_frame  # type: str
    ):
        # type(...) -> None
        """
        Sets the base reference frame for tf tree ingestion.

        :param base_reference_frame: The base reference frame for the tf tree.
        :rtype: None
        """
        self.agent_stub.SetBaseFrameID(
            agent_pb2.SetBaseFrameIDRequest(id=base_reference_frame)
        )

    @handle_agent_exceptions
    def post_transform_frame(
        self,
        parent_frame,  # type: str
        child_frame,  # type: str
        tx,  # type: Union[int, float]
        ty,  # type: Union[int, float]
        tz,  # type: Union[int, float]
        rx,  # type: Union[int, float]
        ry,  # type: Union[int, float]
        rz,  # type: Union[int, float]
        rw,  # type: Union[int, float]
    ):
        # type: (...) -> None
        """
        Adds a transform frame, used to position datapoints in 3D space.

        :param parent_frame: The parent frame of the posted transform
        :param child_frame: The child frame of the posted transform
        :param tx: x-translation
        :param ty: y-translation
        :param tz: z-translation
        :param rx: x-rotation (quaternion)
        :param ry: y-rotation (quaternion)
        :param rz: z-rotation (quaternion)
        :param rw: w-rotation (quaternion)
        :rtype: None
        """

        for _ in [parent_frame, child_frame]:
            validate_type(_, [str])
        for _ in [tx, ty, tz, rx, ry, rz, rw]:
            validate_type(_, [float, int])

        frame = math_pb2.TransformFrame()
        frame.parent_frame = parent_frame
        frame.child_frame = child_frame
        frame.transform.translation.x = tx
        frame.transform.translation.y = ty
        frame.transform.translation.z = tz
        frame.transform.rotation.x = rx
        frame.transform.rotation.y = ry
        frame.transform.rotation.z = rz
        frame.transform.rotation.w = rw
        self.agent_stub.PostTransformFrame(frame)

    # Creating events

    @handle_agent_exceptions
    def create_event(
        self,
        message,  # type: str
        tags=None,  # type: Optional[Dict[str, str]]
        timestamp=None,  # type: Optional[int]
        end_timestamp=None,  # type: Optional[int]
        notify=False,  # type: bool
        severity=DEFAULT_SEVERITY_TYPE,
        # type: Literal["info", "warning", "critical", "error"]
    ):
        # type: (...) -> None
        """
        Creates and ingests an event.

        :param message: The text payload of the event
        :param tags: Tags to include on the event
        :param timestamp: Unix starting timestamp for the event.
            Uses the current time by default
        :param end_timestamp: Unix ending timestamp for the event.
            Must be greater than timestamp.
            If end_timestamp is supplied, the event will span a length of time
        :param notify: If True, the created event will trigger a Formant notification
        :param severity: The severity level of the event
        :rtype: None

        .. highlight:: python
        .. code-block:: python

            from formant.sdk.agent.v1 import Client

            fclient = Client()
            fclient.create_event(
                "Confinement beam to warp frequency 0.4e17 hz",
                tags={"Region": "North"},
                notify=True,
                severity="warning"
            )
        """

        validate_type(message, [str])
        validate_type(severity, [str])
        validate_string_in_array(severity, ALLOWED_SEVERITY_TYPES, "severity")

        severity_pb = set_severity_pb(severity)

        self.agent_stub.CreateEvent(
            agent_pb2.CreateEventRequest(
                event=event_pb2.Event(
                    message=message,
                    notification_enabled=notify,
                    tags=tags if tags else {},
                    severity=severity_pb,
                    timestamp=timestamp if timestamp else current_timestamp(),
                    end_timestamp=end_timestamp,
                )
            )
        )

    # Handling commands

    def get_command_request(
        self, command_filter=None  # type: Optional[List[str]]
    ):
        # type: (...) -> Optional[commands_pb2.CommandRequest]
        """
        If there is a command request in the agent's queue whose ``command`` value
        matches an element of the given command filter, takes and returns the
        command request.
        Otherwise, returns ``None`` if there are no matching command requests
        in the agent's queue.

        :param command_filter: A list of command names.
            This method only returns commands whose names are in this list.
        :rtype: CommandRequest, None
        """
        command_request_request = agent_pb2.GetCommandRequestRequest(
            command_filter=command_filter
        )
        try:
            command_request = self.agent_stub.GetCommandRequest(
                command_request_request
            ).request
            return command_request if command_request.command else None
        except grpc.RpcError:
            return None

    def send_command_response(
        self,
        request_id,  # type: str
        success,  # type: bool
        datapoint=None,  # type: Optional[datapoint_pb2.Datapoint]
    ):
        # type: (...) -> None
        """
        Sends a command response for an identified command request to Formant.
        Returns an error if there was a problem sending the command response.

        :param request_id: The ID of the command request to which this method responds
        :param success: Whether the command was successfully executed
        :param datapoint: A datapoint related to the command. Can attach a datapoint
            to a command response. E.g., if a command fails, can ingest a text datapoint
            with an error message related to the failure of the command.
        :rtype: None
        """
        response = commands_pb2.CommandResponse(
            request_id=request_id,
            success=success,
            datapoint=datapoint,
        )
        request = agent_pb2.SendCommandResponseRequest(response=response)
        self.agent_stub.SendCommandResponse(request)

    def register_command_request_callback(
        self,
        f,  # type: Callable[[commands_pb2.CommandRequest], None]
        command_filter=None,  # type: Optional[List[str]]
    ):
        # type: (...) -> None
        """
        Command requests issued to the agent whose ``command`` value matches an element
        of the given command filter will be streamed into the provided callback.
        If no command filter is provided, all command requests will be handled.

        :param f: A callback that will be executed on command requests
            as they are received by the Formant agent.
        :param command_filter: A list of command names. The provided callback
            is only executed on commands whose names are in this list
        :rtype: None
        """
        with self._lock:

            def create_stream():
                return self._get_command_request_stream(command_filter)

            self._command_request_callback_streams[f] = CancellableStreamThread(
                f,
                create_stream,
                self.logger,
                attribute="request",
                ignore_unavailable=self.ignore_unavailable,
            )

    def unregister_command_request_callback(
        self,
        f,  # type: Callable[[commands_pb2.CommandRequest], None]
    ):
        # type: (...) -> None
        """
        Unregisters previously registered command request callback.

        :param f: The command request callback to be unregistered
        :rtype: None
        """
        with self._lock:
            stream = self._command_request_callback_streams.pop(f, None)
            if stream is not None:
                stream.cancel()

    # Teleop

    def register_teleop_callback(
        self,
        f,  # type: Callable[[datapoint_pb2.ControlDatapoint], None]
        stream_filter=None,  # type: Optional[List[str]]
    ):
        # type: (...) -> None
        """
        Control datapoints received from teleop whose ``stream`` value matches an element
        of the given stream filter will be streamed into the provided callback.
        If no stream filter is provided, control datapoints from all streams
        will be received.

        :param f: A callback that will be executed on teleop control datapoints as they
            are received by the Formant agent
        :param stream_filter: A list of stream names. The provided callback
            is only exectued on control datapoints whose names are in this list
        :rtype: None
        """

        with self._lock:

            def create_stream():
                return self._get_teleop_stream(stream_filter)

            self._teleop_callback_streams[f] = CancellableStreamThread(
                f,
                create_stream,
                self.logger,
                attribute="control_datapoint",
                ignore_unavailable=self.ignore_unavailable,
            )

    def unregister_teleop_callback(
        self, f  # type: Callable[[datapoint_pb2.ControlDatapoint], None]
    ):
        # type: (...) -> None
        """
        Unregisters previously registered teleop callback.

        :param f: The teleop callback to be unregistered
        :rtype: None
        """
        with self._lock:
            stream = self._teleop_callback_streams.pop(f, None)
            if stream is not None:
                stream.cancel()

    @handle_agent_exceptions
    def get_teleop_info(self):
        # type: (...) -> agent_pb2.GetTeleopInfoResponse
        """
        Returns current information about teleop connection count.

        :rtype: GetTeleopInfoResponse
        """
        request = agent_pb2.GetTeleopInfoRequest()
        return self.agent_stub.GetTeleopInfo(request)

    def register_teleop_heartbeat_callback(
        self,
        f,  # type: Callable[[agent_pb2.GetTeleopHeartbeatStreamResponse], None]
    ):
        # type : (...) -> None
        """
        The provided callback will be called once each time a heartbeat
        is received over Formant teleop. Heartbeats are streamed from the
        operator machine at 20Hz on a UDP-like channel. This method can be used
        to quickly detect teleop disconnections.

        :param f: A callback that will be called when a heartbeat is received.
        :rtype: None
        """
        with self._lock:

            def create_stream():
                return self._get_teleop_heartbeat_stream()

            self._teleop_heartbeat_callback_streams[f] = CancellableStreamThread(
                f,
                create_stream,
                self.logger,
                ignore_unavailable=self.ignore_unavailable,
            )

    def unregister_teleop_heartbeat_callback(
        self, f  # type: Callable[[], None]
    ):
        # type : (...) -> None
        """
        Unregisters previously registered teleop heartbeat callback.

        :param f: The teleop heartbeat callback to be unregistered
        :rtype: None
        """
        with self._lock:
            stream = self._teleop_heartbeat_callback_streams.pop(f, None)
            if stream is not None:
                stream.cancel()

    # Custom data channel methods

    @handle_agent_exceptions
    def send_on_custom_data_channel(
        self,
        channel_name,  # type: str
        payload,  # type: bytes
    ):
        # type(...) -> None
        """
        Sends data on custom data channel.

        :param channel_name: (str) The name of the channel over which to send data
        :param payload: (bytes) The data payload to send.
        :rtype: None
        """
        self.agent_stub.SendOnCustomDataChannel(
            agent_pb2.SendOnCustomDataChannelRequest(
                channel_name=channel_name, payload=payload
            )
        )

    def register_custom_data_channel_message_callback(
        self,
        f,  # type: Callable[[agent_pb2.GetCustomDataChannelMessageStreamResponse], None] # noqa: E501
        channel_name_filter=None,  # type: Optional[List[str]]
    ):
        # type : (...) -> None
        """
        Registers a callback on data presence on the specified data channel.

        :param f: A callback that will be called with messages
            received on the specified custom data channel.
        :param channel_name_filter: An optional allow list of custom channel names
            for this callback.
        :rtype: None
        """
        with self._lock:

            def create_stream():
                return self._get_custom_data_channel_message_stream(
                    channel_name_filter=channel_name_filter
                )

            self._custom_data_channel_message_callback_streams[f] = (
                CancellableStreamThread(
                    f,
                    create_stream,
                    self.logger,
                    ignore_unavailable=self.ignore_unavailable,
                )
            )

    def unregister_custom_data_channel_message_callback(
        self,
        f,  # type: Callable[[], None]
    ):
        # type : (...) -> None
        """
        Unregisters previously registered custom data channel callback.

        :param f: The custom data channel message callback to be unregistered.
        :rtype: None
        """
        with self._lock:
            stream = self._custom_data_channel_message_callback_streams.pop(f, None)
            if stream is not None:
                stream.cancel()

    def custom_data_channel_request_handler(
        self, channel_name  # type: str
    ):
        # type : (...) -> Callable[Callable[agent_pb2.GetCustomDataChannelMessageStreamResponse, None], Callable[str, str]]: # noqa: E501
        """
        Registers a handler for requests sent by RequestDataChannel instances
        (part of the Formant toolkit).
        See: https://github.com/FormantIO/toolkit/tree/master/examples/request-response
        for an example.

        :param channel_name: The name of the custom data channel to listen on.
        :rtype: GetCustomDataChannelMessageStreamResponse

        .. highlight:: python
        .. code-block:: python

            from formant.sdk.agent.v1 import Client

            fclient = Client()

            @fclient.custom_data_channel_request_handler("my_channel")
            def handler(request_data):
                # Do something with request_data string
                print(json.loads(request_data))

                # Return any string response
                return json.dumps({"message": "Hello world!"})
        """

        def outer_wrapper(f):
            def inner_wrapper(message):
                try:
                    payload = json.loads(message.payload.decode("utf-8"))
                    request_id = payload["id"]
                    request_data = payload["data"]
                except (
                    UnicodeDecodeError,
                    json.decoder.JSONDecodeError,
                    KeyError,
                ) as e:
                    self.logger.error(
                        "Received invalid custom data channel request: "
                        + e.__class__.__name__
                        + ": "
                        + str(e)
                    )

                response_data = None
                try:
                    response = f(request_data)
                    # Place valid responses on the "data" key
                    response_data = json.dumps(
                        {"id": request_id, "data": response}
                    ).encode("utf-8")
                except Exception as e:
                    error_message = (
                        "An error occurred while handling custom data channel request: "
                        + e.__class__.__name__
                        + ": "
                        + str(e)
                    )
                    # Place error responses on the "error" key
                    response_data = json.dumps(
                        {"id": request_id, "error": error_message}
                    ).encode("utf-8")
                self.send_on_custom_data_channel(channel_name, response_data)

            # When the handler function is decorated,
            # we automatically register it as a callback
            self.register_custom_data_channel_message_callback(
                inner_wrapper, [channel_name]
            )

        return outer_wrapper

    def custom_data_channel_binary_request_handler(
        self,
        channel_name,  # type: bytes
        new_thread=False,  # type: bool
    ):
        # type : (...) -> Callable[Callable[agent_pb2.GetCustomDataChannelMessageStreamResponse, None], Callable[str, str]]: # noqa: E501
        """
        :param channel_name: The name of the custom data channel to listen on.

        .. highlight:: python
        .. code-block:: python

            from formant.sdk.agent.v1 import Client

            fclient = Client()

            @fclient.custom_data_channel_request_handler("my_channel")
            def handler(request_data):
                # Do something with request_data bytes
                print(request_data.decode("utf-8"))

                # Return any bytes response
                return b"Hello."
        """

        SUCCESS_RESPONSE_BYTE = b"\00"
        ERROR_RESPONSE_BYTE = b"\01"

        def outer_wrapper(f):
            def inner_wrapper(message):
                try:
                    request_id = message.payload[0:16]
                    request_data = message.payload[16:]
                except TypeError as e:
                    self.logger.error(
                        "Received invalid custom data channel request: "
                        + e.__class__.__name__
                        + ": "
                        + str(e)
                    )

                def call_and_respond():
                    response_data = None
                    try:
                        response = f(request_data)
                        response_data = request_id + SUCCESS_RESPONSE_BYTE + response
                    except Exception as e:
                        error_message = (
                            "An error occurred while handling custom data channel request: "
                            + e.__class__.__name__
                            + ": "
                            + str(e)
                        )
                        response_data = (
                            request_id
                            + ERROR_RESPONSE_BYTE
                            + error_message.encode("utf-8")
                        )

                    self.send_on_custom_data_channel(channel_name, response_data)

                if new_thread:
                    self._thread_pool.apply_async(call_and_respond)
                else:
                    call_and_respond()

            # When the handler function is decorated,
            # we automatically register it as a callback
            self.register_custom_data_channel_message_callback(
                inner_wrapper, [channel_name]
            )

        return outer_wrapper

    # Reading application configuration

    def get_app_config(self, key, *args):
        # type: (str, Any) -> Optional[str]
        """
        Returns the value for the given key that was set in
        Formant application configuration for this device,
        or returns the given default value.

        :param key: The application configuration key
        :param args: (One additional argument)
            The default value to return if the key is not found.
        :raises: ``TypeError: Function takes at most two args: (key: str, default: Any)``
        """
        if len(args) > 1:
            raise TypeError("function takes at most two args: (key: str, default: Any)")
        default = args[0] if len(args) == 1 else None

        # update if there's a connection to the agent API
        self._update_application_configuration()
        return self._app_config.get(key, default)

    @handle_agent_exceptions
    def get_config_blob_data(self):
        # type: (...) -> str
        """
        Returns the blob data defined in the device configuration.

        :rtype: str
        """
        request = agent_pb2.GetConfigBlobDataRequest()
        return self.agent_stub.GetConfigBlobData(request).blob_data.data

    @handle_agent_exceptions
    def get_buffer_metadata(self):
        # type: (...) -> agent_pb2.GetBufferMetadata
        """
        Returns the current WebRTC buffer statistics.

        :rtype: agent_pb2.GetBufferMetadata
        """
        request = agent_pb2.GetBufferMetadataRequest()
        return self.agent_stub.GetBufferMetadata(request)

    def register_config_update_callback(self, f):
        # type: (Callable) -> None
        """
        Adds a function to the list of callbacks that are executed by the client
        when this device receives updated configuration from Formant.

        :param f: The configuration update callback to be registered.
        :rtype: None
        """
        with self._lock:
            self._config_update_callbacks.append(f)

    def unregister_config_update_callback(self, f):
        # type: (Callable) -> None
        """
        Removes a function from the list of callbacks that are executed by the client
        when this device receives updated configuration from Formant.

        :param f: The configuration update callback to be unregistered.
        :rtype: None
        """
        with self._lock:
            self._config_update_callbacks.remove(f)

    # Internal methods

    def _setup_agent_communication(self, subscribe_only=False):
        if subscribe_only:
            self.channel.subscribe(
                self._handle_connectivity_change, try_to_connect=True
            )
        else:
            self.channel = grpc.insecure_channel(self._agent_url)
            self.channel.subscribe(
                self._handle_connectivity_change, try_to_connect=True
            )
            self.agent_stub = agent_pb2_grpc.AgentStub(self.channel)

    def _handle_connectivity_change(self, connectivity):
        """Handle changes to gRPC channel connectivity."""

        self.logger.info("Agent communication status: %s" % connectivity.name)

        if connectivity == grpc.ChannelConnectivity.READY and not self._connected:
            self.logger.info(
                "Agent communication READY. Updating application configuration."
            )
            self._connected = True
            self._update_application_configuration()
            self._run_update_config_callbacks()
        elif connectivity == grpc.ChannelConnectivity.IDLE and self._connected:
            # If the channel is back to idle we have to re-subscribe before we can use it
            # this will transition to READY if the connection is re-established
            self._connected = False
            self.logger.info("Agent communication IDLE. Re-subscribing...")
            self._setup_agent_communication(subscribe_only=True)
        elif connectivity == grpc.ChannelConnectivity.SHUTDOWN:
            # In the case of shutdown, re-establish the connection from scratch
            self.logger.info("Agent communication lost. Re-establishing...")
            self._setup_agent_communication()

    @handle_agent_exceptions
    def _update_application_configuration(self):
        request = agent_pb2.GetApplicationConfigurationRequest()
        response = self.agent_stub.GetApplicationConfiguration(request)
        self._app_config = response.configuration.configuration_map

    def _run_update_config_callbacks(self):
        [f() for f in self._config_update_callbacks]

    def _get_command_request_stream(self, command_filter=None):
        return self.agent_stub.GetCommandRequestStream(
            agent_pb2.GetCommandRequestStreamRequest(command_filter=command_filter)
        )

    def _get_teleop_stream(self, stream_filter=None):
        return self.agent_stub.GetTeleopControlDataStream(
            agent_pb2.GetTeleopControlDataStreamRequest(stream_filter=stream_filter)
        )

    def _get_teleop_heartbeat_stream(self):
        return self.agent_stub.GetTeleopHeartbeatStream(
            agent_pb2.GetTeleopHeartbeatStreamRequest()
        )

    def _get_telemetry_listener_stream(self, stream_filter=None):
        return self.agent_stub.GetTelemetryListenerStream(
            agent_pb2.GetTelemetryListenerStreamRequest(stream_filter=stream_filter)
        )

    def _get_custom_data_channel_message_stream(self, channel_name_filter=None):
        return self.agent_stub.GetCustomDataChannelMessageStream(
            agent_pb2.GetCustomDataChannelMessageStreamRequest(
                channel_name_filter=channel_name_filter
            )
        )

    @handle_agent_exceptions
    def call_cloud(
        self,
        endpoint,  # type: str
        method,  # type: str
        body,  # type: str
        headers,  # type: Dict[str, str]
        require_formant_auth,  # type: bool
        buffer_call,  # type: bool
        is_retryable,  # type: bool
        retryable_status_codes=[],  # type: List[int]
    ):
        """
        Allows the user to call an endpoint of the Formant Admin API
        authenticated by the Formant agent instead of user credentials.

        API calls which allow ``device`` authentication can buffer and retry
        calls. For more information, see the following documentation:

        `Use the Formant agent to authenticate API calls <https://docs.formant.io/reference/use-the-formant-agent-to-authenticate-api-calls>`__

        `Buffering and retrying API calls <https://docs.formant.io/reference/buffering-and-retrying-api-calls>`__

        .. note::

            If buffering is enabled, you will not get a return value from this function.

        :param endpoint: Full URL of the endpoint to call (can be found at https://docs.formant.io/reference).
        :type endpoint: str
        :param method: The HTTP method to use (e.g., ``"POST"``, ``"PUT"``, ``"GET"``, ``"PATCH"``, ``"DELETE"``).
        :type method: str
        :param headers: Set the content type of your payload.
        :type headers: Dict[str, str]
        :param body: Payload of the request (parameters found at https://docs.formant.io/reference).
        :type body: str
        :param require_formant_auth: Whether or not to use device authentication.
                    If ``True``, ``authorization`` header is added automatically.
        :type require_formant_auth: bool
        :param buffer_call: Whether or not to buffer the call.
                    If ``True``, the call is buffered and will be retried if necessary.
                    If ``True``, ``call_cloud()`` returns ``None``.
        :type buffer_call: bool
        :param is_retryable: (``buffer_call=True`` only) Whether to retry the call if it fails.
        :type is_retryable: bool
        :param retryable_status_codes: (``buffer_call=True`` only) The status codes to retry on.
                    A value of ``[-1]`` will retry on all ``5xx`` codes EXCEPT FOR the following: ``[500, 501, 502, 505, 507, 508, 510, 511]``.
        :type retryable_status_codes: List[int]
        :rtype: agent_pb2.PostGenericAPIUnbufferedRequestResponse

        .. code-block:: python

            from formant.sdk.agent.v1 import Client
            import json

            fclient = Client()

            payload = {
                "query": "acme",
                "count": 10
            }

            response = fclient.call_cloud(
                endpoint="https://api.formant.io/v1/admin/devices/query",
                method="POST",
                headers={
                    "Content-Type": "application/json"
                },
                body=json.dumps(payload),
                require_formant_auth=True,
                buffer_call=False,
                is_retryable=False,
                retryable_status_codes=[]
            )

            # You get a response with ``statusCode`` and ``responseBody``
            # when ``buffer_call == False``.
            print(response.statusCode)
            print(response.responseBody)
        """
        validate_type(endpoint, [str])
        validate_type(method, [str])
        validate_type(body, [str])
        validate_type(headers, [dict])
        validate_type(require_formant_auth, [bool])
        validate_type(is_retryable, [bool])
        validate_type(retryable_status_codes, [list])

        request = datapoint_pb2.GenericAPIDatapoint()
        request.Method = method
        request.Endpoint = endpoint
        for key, value in headers.items():
            request.Headers[key] = value

        request.Body = body
        request.RequireFormantAuth = require_formant_auth
        request.IsRetryable = is_retryable
        for code in retryable_status_codes:
            request.RetryableStatusCodes.append(code)
        if buffer_call:
            return self.agent_stub.PostGenericAPIRequest(request)

        return self.agent_stub.PostGenericAPIUnbufferedRequest(request)

    @handle_agent_exceptions
    def create_selection_intervention_request(
        self,
        title,  # type: str
        instruction,  # type: str
        options,  # type: List[str]
        hint,  # type: int
        url=None,  # type: str
        content_type=DEFAULT_IMAGE_CONTENT_TYPE,  # type: Literal["image/jpg", "image/png"]
        timestamp=None,  # type: Optional[int]
        severity=DEFAULT_SEVERITY_TYPE,  # type: Literal["info", "warning", "critical", "error"]
    ):
        # type : (...) -> intervention_pb2.InterventionRequest
        """
        Creates an intervention request based on type ``selection``.
        Takes an image url, options and an integer with an optional
        addition of instructions, and title.

        :param title: (str) The name of the intervention
        :param instruction: (str) The instructions detailing how to resolve the intervention
        :param options: (List[str]) The list with options to select from
        :param hint: (int) The index of the suspected correct answer
        :param url: (str) The path to local file or valid remote URL for remote files
        :param content_type: (Literal["image/jpg", "image/png"]) The format of the encoded image or frame.
            Defaults to ``"image/jpg"``
        :param timestamp: (Optional[int]) Unix timestamp in milliseconds for the posted datapoint.
            Uses the current time by default
        :param severity: (Literal["info", "warning", "critical", "error"]) The severity level of the event
        :rtype: InterventionRequest

        .. highlight:: python
        .. code-block:: python

            from formant.sdk.agent.v1 import Client

            fclient = Client()
            fclient.create_selection_intervention_request(
                "Which fruit is best?",
                "Select the best grape",
                ["fruit_1", "fruit_2", "fruit_3"],
                hint=1,
                url=/home/my_user/data/test-image.jpeg
                severity=critical
            )
        """

        validate_type(title, [str])
        validate_type(instruction, [str])
        validate_type(url, [str])
        validate_type(options, [List])
        validate_type(hint, [int])
        validate_type(severity, [str])
        validate_type(content_type, [str])
        validate_string_in_array(
            content_type, ALLOWED_IMAGE_CONTENT_TYPES, "content_type"
        )
        validate_string_in_array(severity, ALLOWED_SEVERITY_TYPES, "severity")
        for option in options:
            validate_type(option, [str])

        severity_pb = set_severity_pb(severity)

        request = intervention_pb2.InterventionRequest()
        request.timestamp = timestamp if timestamp else current_timestamp()
        request.severity = severity_pb
        request.selection_request.title = title
        request.selection_request.hint = hint
        request.selection_request.instruction = instruction
        request.selection_request.image.content_type = content_type
        request.selection_request.image.url = url
        request.selection_request.options.extend(options)
        return self.agent_stub.CreateInterventionRequest(request)

    @handle_agent_exceptions
    def create_labeling_intervention_request(
        self,
        title,  # type: str
        instruction,  # type: str
        labels,  # type: Dict[str, str]
        hint=None,  # type: Optional[List[intervention_pb2.LabeledPolygon]]
        url=None,  # type: str
        content_type=DEFAULT_IMAGE_CONTENT_TYPE,  # type: Literal["image/jpg", "image/png"]
        timestamp=None,  # type: Optional[int]
        severity=DEFAULT_SEVERITY_TYPE,
        # type: Literal["info", "warning", "critical", "error"]
    ):
        # type : (...) -> intervention_pb2.InterventionRequest

        """
        Creates an intervention request based on type "labeling".

        :param title: (str) The name of the intervention
        :param instruction: (str) The instructions detailing how to resolve the intervention
        :param labels: (Dict[str, str]) An Array of labels
        :param hint: (Optional[List[intervention_pb2.LabeledPolygon]]) An array of label polygons, X and Y coordinates with a label
        :param url: (str) The path to local file or valid remote URL for remote files
        :param content_type: (Literal["image/jpg", "image/png"]) The format of the encoded image or frame.
            Defaults to ``"image/jpg"``.
        :param timestamp: (Optional[int]) Unix timestamp in milliseconds for the posted datapoint.
            Uses the current time by default
        :param severity: (Literal["info", "warning", "critical", "error"]) The severity level of the event
        :rtype: intervention_pb2.InterventionRequest


        Each ``label`` in ``labels`` defined as::

                Label = {
                        value = string;
                        string display_name = string;
                        }

        Hint is an array of "LabeledPolygon", defined as::

                hint = {
                    List of vertex,
                    List of labels
                }

        where each vertex is defined as::

                vertex = {
                    x = float,
                    y = float
                }
        """
        validate_type(title, [str])
        validate_type(instruction, [str])
        validate_type(url, [str])
        validate_type(content_type, [str])
        validate_type(severity, [str])
        validate_string_in_array(severity, ALLOWED_SEVERITY_TYPES, "severity")
        validate_string_in_array(
            content_type, ALLOWED_IMAGE_CONTENT_TYPES, "content_type"
        )
        validate_type(labels, [dict])
        if hint is not None:
            for label in hint:
                validate_type(label, [intervention_pb2.LabeledPolygon])
        for k, v in labels.items():
            validate_type(k, [str])
            validate_type(v, [str])

        severity_pb = set_severity_pb(severity)

        request = intervention_pb2.InterventionRequest()
        request.timestamp = timestamp if timestamp else current_timestamp()
        request.severity = severity_pb
        request.labeling_request.title = title
        request.labeling_request.instruction = instruction
        if hint is not None:
            request.labeling_request.hint.extend(hint)
        request.labeling_request.image.content_type = content_type
        request.labeling_request.image.url = url
        for key, value in labels.items():
            label = intervention_pb2.Label()
            label.value = key
            label.display_name = value
            request.labeling_request.labels.append(label)
        return self.agent_stub.CreateInterventionRequest(request)

    @handle_agent_exceptions
    def get_intervention_response(
        self,
        request_id,  # type: str
        timeout=None,  # type: Optional[int]
    ):
        # type : (...) -> agent_pb2.GetInterventionResponse

        """
        Receives request ID, and returns a response.

        :param request_id: The ID of the intervention request
            to which this method responds
        :type request_id: str
        :param timeout: (Optional) Number of seconds to wait for a response.
        :type timeout: int
        :rtype: agent_pb2.GetInterventionResponse

        .. highlight:: python
        .. code-block:: python

            from formant.sdk.agent.v1 import Client

            fclient = Client()
            request = fclient.create_selection_intervention_request(
                title="",
                instruction="instruction",
                options=["option1", "option2", "option3"],
                hint=0,
                url="/home/formantuser/Downloads/image.png",
            )
            # Waits 5 seconds for a response, then proceeds
            response = fclient.get_intervention_response(request.id, 5)
        """
        validate_type(request_id, [str])
        response_request = agent_pb2.GetInterventionResponseRequest()
        response_request.request_id = request_id
        return self.agent_stub.GetInterventionResponse(
            response_request, timeout=timeout
        )

    def post_task_summary(
            self,
            task_summary_format_id,
            task_summary_report,
            message,
            task_id,
            start_time,
            end_time = None,
            task_summary_url = "https://api.formant.io/v1/admin/task-summaries/",
            additional_request_kwargs = {}
    ):
        """
        Uploads a task summary to the Formant cloud in the provided task summary format.

        You must first create a task summary format and add it to Formant. See `Create a task summary <https://docs.formant.io/docs/create-a-task-summary>`__.

        :param task_summary_format_id: ID of the task summary format which describes this task summary.
        :type task_summary_format_id: str
        :param task_summary_report: Data for this task summary in key-value pairs, as described by the task summary format.
        :type task_summary_report: dict
        :param message: Message associated with this task summary.
        :type message: str
        :param task_id: Enter a unique identifier for this task summary.
        :type task_id: str
        :param start_time: Start datetime of the data range relevant to this event (ISO 8601 format).
        :type start_time: str
        :param end_time: (Optional) End time of the data range relevant to this event.
        :type end_time: str
        :param task_summary_url: (Optional) The URL to which to post the task summary.
        :type task_summary_url: str
        :param additional_request_kwargs: (Optional) Additional request kwargs to pass in the POST request.
            These will be added to the body of the request as key-value pairs.
            See all available request kwargs at `Task Summary POST <https://docs.formant.io/reference/tasksummarycontrollerpost>`__.
        :type additional_request_kwargs: dict

        :rtype: Dictionary containing task summary
        """
        validate_type(task_summary_format_id, [str])
        validate_type(task_summary_report, [dict])
        validate_type(message, [str])
        validate_type(task_id, [str])
        validate_type(start_time, [str])
        validate_type(end_time, [str, type(None)])
        validate_type(task_summary_url, [str])
        validate_type(additional_request_kwargs, [dict])

        device_id = self.get_agent_id()
        generated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        body = {
            "taskSummaryFormatId": task_summary_format_id,
            "report": task_summary_report,
            "message": message,
            "taskId": task_id,
            "deviceId": device_id,
            "time": start_time,
            "generatedAt": generated_at,
        }
        body.update(additional_request_kwargs)

        if end_time is not None:
            body["endTime"] = end_time

        response = self.call_cloud(
            endpoint=task_summary_url,
            method="POST",
            headers={"Content-Type": "application/json"},
            body=json.dumps(body),
            require_formant_auth=True,
            buffer_call=False,
            is_retryable=False,
            retryable_status_codes=[]
        )

        if response.statusCode == 201:
            response_body = json.loads(response.responseBody)
            return response_body
        else:
            raise Exception("Failed to post task summary: {}".format(response.responseBody))


