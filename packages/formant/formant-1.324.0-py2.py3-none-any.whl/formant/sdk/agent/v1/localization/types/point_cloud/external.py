from typing import Optional
from uuid import uuid4
from .internal_types import PointField
from .point_cloud2 import create_cloud, pointcloud2_to_formant_pointcloud
from .laserscan import laserscan_to_formant_pointcloud

from formant.protos.model.v1 import media_pb2
from formant.sdk.agent.v1.localization.utils import get_ros_module, validate_type
from formant.sdk.agent.v1.localization.types import Transform


class PointCloud:
    @classmethod
    def from_xyzi32(cls, points):
        fields = [
            PointField(name="x", offset=0, datatype=PointField.FLOAT32, count=1),
            PointField(name="y", offset=4, datatype=PointField.FLOAT32, count=1),
            PointField(name="z", offset=8, datatype=PointField.FLOAT32, count=1),
            PointField(
                name="intensity", offset=12, datatype=PointField.FLOAT32, count=1
            ),
        ]
        point_cloud2 = create_cloud(fields, points)
        data = pointcloud2_to_formant_pointcloud(point_cloud2)
        return cls(data=data)

    @classmethod
    def from_ros(cls, point_cloud2):
        sensor_msgs = get_ros_module("sensor_msgs.msg")
        validate_type(point_cloud2, sensor_msgs.PointCloud2)
        data = pointcloud2_to_formant_pointcloud(point_cloud2)
        return cls(data=data)

    @classmethod
    def from_ros_laserscan(cls, laserscan):
        sensor_msgs = get_ros_module("sensor_msgs.msg")
        validate_type(laserscan, sensor_msgs.LaserScan)
        data = laserscan_to_formant_pointcloud(laserscan)
        return cls(data=data)

    def __init__(
        self,
        data=None,  # type: Optional[bytes]
        url=None,  # type:  Optional[str]
        transform_to_world=Transform(),  # type: Transform
    ):
        self.data = data
        self.url = url
        self.transform_to_world = transform_to_world
        self.uuid = uuid4()

    def to_proto(self):
        return media_pb2.PointCloud(
            raw=self.data,
            url=self.url,
            world_to_local=self.transform_to_world.to_proto(),
            uuid=str(self.uuid),
        )


def create_cloud_xyzi32(points):

    fields = [
        PointField(name="x", offset=0, datatype=PointField.FLOAT32, count=1),
        PointField(name="y", offset=4, datatype=PointField.FLOAT32, count=1),
        PointField(name="z", offset=8, datatype=PointField.FLOAT32, count=1),
        PointField(name="intensity", offset=12, datatype=PointField.FLOAT32, count=1),
    ]
    point_cloud2 = create_cloud(fields, points)
    return pointcloud2_to_formant_pointcloud(point_cloud2)
