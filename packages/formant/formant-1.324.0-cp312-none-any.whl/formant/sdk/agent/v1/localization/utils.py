import numpy as np
import importlib


# TODO: improve error log
def validate_type(o, t):
    if not isinstance(o, t):
        raise Exception("object %s is not of type %s" % (type(o), type(t())))


def get_ros_module(module_name):
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as e:
        raise Exception("ROS not intalled, could not find module: %s" % e)


def zero_twist(twist):
    zero_vector3(twist.linear)
    zero_vector3(twist.angular)


def zero_transform(transform):
    zero_vector3(transform.translation)
    zero_quanternion(transform.rotation)


def zero_quanternion(quanternion):
    quanternion.x = 0
    quanternion.y = 0
    quanternion.z = 0
    quanternion.w = 1


def zero_vector3(vector3):
    vector3.x = 0
    vector3.y = 0
    vector3.z = 0


def get_quaternion_from_euler(roll, pitch, yaw):
    """
    Convert an Euler angle to a quaternion.

    Input
        :param roll: The roll (rotation around x-axis) angle in radians.
        :param pitch: The pitch (rotation around y-axis) angle in radians.
        :param yaw: The yaw (rotation around z-axis) angle in radians.

    Output
        :return qx, qy, qz, qw: The orientation in quaternion [x,y,z,w] format
    """
    qx = np.sin(roll / 2) * np.cos(pitch / 2) * np.cos(yaw / 2) - np.cos(
        roll / 2
    ) * np.sin(pitch / 2) * np.sin(yaw / 2)
    qy = np.cos(roll / 2) * np.sin(pitch / 2) * np.cos(yaw / 2) + np.sin(
        roll / 2
    ) * np.cos(pitch / 2) * np.sin(yaw / 2)
    qz = np.cos(roll / 2) * np.cos(pitch / 2) * np.sin(yaw / 2) - np.sin(
        roll / 2
    ) * np.sin(pitch / 2) * np.cos(yaw / 2)
    qw = np.cos(roll / 2) * np.cos(pitch / 2) * np.cos(yaw / 2) + np.sin(
        roll / 2
    ) * np.sin(pitch / 2) * np.sin(yaw / 2)

    return [qx, qy, qz, qw]
