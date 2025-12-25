from typing import List
from formant.protos.model.v1 import navigation_pb2
from formant.sdk.agent.v1.localization.utils import validate_type, get_ros_module
from .transform import Transform
from uuid import uuid4


class Map:
    @classmethod
    def from_ros(cls, map):
        nav_msgs = get_ros_module("nav_msgs.msg")
        validate_type(map, nav_msgs.OccupancyGrid)
        return cls(
            map.info.resolution,
            map.info.width,
            map.info.height,
            origin=Transform.from_ros_pose(map.info.origin),
            occupancy_grid_data=map.data,
        )

    @classmethod
    def from_costmap(cls, costmap):
        nav2_msgs = get_ros_module("nav2_msgs.msg")
        validate_type(costmap, nav2_msgs.Costmap)

        return cls(
            costmap.metadata.resolution,
            costmap.metadata.size_x,
            costmap.metadata.size_y,
            origin=Transform.from_ros_pose(costmap.metadata.origin),
            occupancy_grid_data=costmap.data
        )

    def __init__(
        self,
        resolution,  # type: float
        width,  # type: float
        height,  # type:  float
        origin=Transform(),  # type: Transform
        transform_to_world=Transform(),  # type: Transform
        url=None,  # type: str
        raw_data=None,  # type: bytes
        occupancy_grid_data=None,  # type:  List[int]
    ):
        self.resolution = resolution
        self.width = width
        self.height = height
        self.origin = origin
        self.transform_to_world = transform_to_world
        self.url = url
        self.raw_data = raw_data
        self.occupancy_grid_data = occupancy_grid_data
        self.uuid = uuid4()

    def to_proto(self):
        map = navigation_pb2.Map(
            resolution=self.resolution,
            width=self.width,
            height=self.height,
            origin=self.origin.to_proto(),
            world_to_local=self.transform_to_world.to_proto(),
            url=self.url,
            raw=self.raw_data,
            uuid=str(self.uuid),
        )
        if self.occupancy_grid_data is not None:
            map.occupancy_grid.data.extend(self.occupancy_grid_data)
        return map
