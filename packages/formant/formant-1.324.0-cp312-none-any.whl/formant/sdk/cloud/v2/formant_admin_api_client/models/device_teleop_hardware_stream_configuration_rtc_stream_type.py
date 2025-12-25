from enum import Enum


class DeviceTeleopHardwareStreamConfigurationRtcStreamType(str, Enum):
    PING = "ping"
    PONG = "pong"
    PING_V2 = "ping-v2"
    PONG_V2 = "pong-v2"
    STREAM_CONTROL = "stream-control"
    STREAMS_INFO = "streams-info"
    AGENT_INFO = "agent-info"
    NUMERIC = "numeric"
    BOOLEAN = "boolean"
    BITSET = "bitset"
    TWIST = "twist"
    COMPRESSED_IMAGE = "compressed-image"
    H264_VIDEO_FRAME = "h264-video-frame"
    AUDIO_CHUNK = "audio-chunk"
    POSE = "pose"
    GOAL_ID = "goal-id"
    JOINT_STATE = "joint-state"
    POSE_WITH_COVARIANCE = "pose-with-covariance"
    POINT_CLOUD = "point-cloud"
    POINT = "point"
    MARKER_ARRAY = "marker-array"
    JSON_STRING = "json-string"
    ODOMETRY = "odometry"
    JOY = "joy"
    TEXT = "text"
    MAP = "map"
    LOCATION = "location"
    NUMERIC_SET = "numeric-set"

    def __str__(self) -> str:
        return str(self.value)
