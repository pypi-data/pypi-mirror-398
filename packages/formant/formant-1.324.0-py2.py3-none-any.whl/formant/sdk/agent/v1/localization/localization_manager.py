import time
import sys
from threading import Lock
from typing import Dict, Optional
from formant.sdk.agent.v1.exceptions import handle_agent_exceptions
from formant.protos.model.v1 import navigation_pb2, datapoint_pb2
from formant.sdk.agent.v1.localization.types import (
    Odometry,
    Path,
    Goal,
    Map,
    PointCloud,
)

DEFAULT_POINTCLOUD_NAME = "defualt"


class LocalizationManager:
    def __init__(
        self,
        stream_name,  # type: str
        client,
        throttle_hz,  # type: float
        rectify_odom_translation=False,  # type: bool
    ):
        self._client = client
        self._stream_name = stream_name  # type: str
        self._last_sent_time = time.time()  # type: float
        self._lock = Lock()
        self._cached_odometry = None  # type: Optional[Odometry]
        self._cached_map = None  # type: Optional[Map]
        self._cached_point_clouds = {}  # type: Dict[str, PointCloud]
        self._cached_path = None  # type: Optional[Path]
        self._cached_goal = None  # type: Optional[Goal]

        self.ignore_throttled = client.ignore_throttled
        self.ignore_unavailable = client.ignore_unavailable

        if throttle_hz == 0:
            self._min_time_between_messages = float("inf")
        else:
            self._min_time_between_messages = 1.0 / throttle_hz
        self._tags = {}  # type: Dict
        self._rectify_odom_translation = rectify_odom_translation

    def update_point_cloud(
        self,
        point_cloud,  # type: PointCloud
        cloud_name=DEFAULT_POINTCLOUD_NAME,  # type:str
    ):
        with self._lock:
            self._cached_point_clouds[cloud_name] = point_cloud
        self._try_send_localization()

    def invalidate_pointcloud(
        self, cloud_name=DEFAULT_POINTCLOUD_NAME  # type: str
    ):
        with self._lock:
            del self._cached_point_clouds[cloud_name]
        self._try_send_localization()

    def update_odometry(
        self, odometry  # type: Odometry
    ):
        with self._lock:
            self._cached_odometry = odometry
        self._try_send_localization()

    def update_map(
        self, map  # type: Map
    ):
        with self._lock:
            self._cached_map = map
        self._try_send_localization()

    def update_path(
        self, path  # type: Path
    ):
        with self._lock:
            self._cached_path = path
        self._try_send_localization()

    def update_goal(
        self, goal  # type: Goal
    ):
        with self._lock:
            self._cached_goal = goal
        self._try_send_localization()

    def set_tags(
        self, tags  # type: Dict
    ):
        with self._lock:
            self._tags = tags

    @handle_agent_exceptions
    def _try_send_localization(self):
        with self._lock:
            # Localization requires odometry
            if self._cached_odometry is None:
                return
            # Don't send messages too fast
            now = time.time()
            if now - self._last_sent_time < self._min_time_between_messages:
                return
            self._last_sent_time = now

            map = self._cached_map
            odometry = self._cached_odometry
            path = self._cached_path
            goal = self._cached_goal
            point_clouds = self._cached_point_clouds
            tags = self._tags

        if self._rectify_odom_translation:
            if map is not None and odometry is not None:
                odometry.transform_to_world.x = -map.origin.translation.x
                odometry.transform_to_world.y = -map.origin.translation.y

        localization = navigation_pb2.Localization(
            map=protected_to_proto(map),
            odometry=protected_to_proto(odometry),
            path=protected_to_proto(path),
            goal=protected_to_proto(goal),
        )
        if len(point_clouds.keys()) != 0:
            del localization.point_clouds[:]
            localization.point_clouds.extend(
                [point_cloud.to_proto() for point_cloud in point_clouds.values()]
            )

        self._client.agent_stub.PostData(
            datapoint_pb2.Datapoint(
                stream=self._stream_name,
                localization=localization,
                tags=tags,
                timestamp=int(time.time() * 1000),
            )
        )


def protected_to_proto(obj):
    if obj is None:
        return None
    return obj.to_proto()
