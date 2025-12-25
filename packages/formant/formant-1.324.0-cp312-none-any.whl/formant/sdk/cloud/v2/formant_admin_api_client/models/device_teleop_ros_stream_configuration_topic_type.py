from enum import Enum


class DeviceTeleopRosStreamConfigurationTopicType(str, Enum):
    STD_MSGSFLOAT64 = "std_msgs/Float64"
    STD_MSGSFLOAT32 = "std_msgs/Float32"
    STD_MSGSBOOL = "std_msgs/Bool"
    GEOMETRY_MSGSTWIST = "geometry_msgs/Twist"
    SENSOR_MSGSCOMPRESSEDIMAGE = "sensor_msgs/CompressedImage"
    GEOMETRY_MSGSPOSESTAMPED = "geometry_msgs/PoseStamped"
    ACTIONLIB_MSGSGOALID = "actionlib_msgs/GoalID"
    FORMANTH264VIDEOFRAME = "formant/H264VideoFrame"
    AUDIO_COMMON_MSGSAUDIODATA = "audio_common_msgs/AudioData"
    SENSOR_MSGSJOINTSTATE = "sensor_msgs/JointState"
    GEOMETRY_MSGSPOSEWITHCOVARIANCESTAMPED = "geometry_msgs/PoseWithCovarianceStamped"
    SENSOR_MSGSLASERSCAN = "sensor_msgs/LaserScan"
    SENSOR_MSGSPOINTCLOUD2 = "sensor_msgs/PointCloud2"
    GEOMETRY_MSGSPOINTSTAMPED = "geometry_msgs/PointStamped"
    VISUALIZATION_MSGSMARKERARRAY = "visualization_msgs/MarkerArray"
    NAV_MSGSODOMETRY = "nav_msgs/Odometry"
    SENSOR_MSGSJOY = "sensor_msgs/Joy"
    STD_MSGSSTRING = "std_msgs/String"
    NAV_MSGSOCCUPANCYGRID = "nav_msgs/OccupancyGrid"
    SENSOR_MSGSNAVSATFIX = "sensor_msgs/NavSatFix"

    def __str__(self) -> str:
        return str(self.value)
