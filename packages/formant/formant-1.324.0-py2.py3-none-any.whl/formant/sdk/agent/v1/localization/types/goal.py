from formant.protos.model.v1 import navigation_pb2
from .transform import Transform


class Goal:
    def __init__(
        self,
        pose=Transform(),  # type: Transform
        transform_to_world=Transform(),  # type: Transform
    ):
        self.pose = pose
        self.transform_to_world = transform_to_world

    def to_proto(self):
        return navigation_pb2.Goal(
            pose=self.pose.to_proto(),
            world_to_local=self.transform_to_world.to_proto(),
        )
