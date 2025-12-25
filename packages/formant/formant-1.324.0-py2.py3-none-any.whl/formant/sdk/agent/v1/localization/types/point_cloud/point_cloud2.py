import array
import sys
from typing import Iterable
import struct
import lzf
import numpy as np
from .internal_types import PointCloud2, PointField

from formant.protos.model.v1.media_pb2 import PointCloud

# TODO: support different types
FLOAT_DATA_TYPE = 7
DOUBLE_DATA_TYPE = 8


try:
    from numpy.lib.recfunctions import unstructured_to_structured
except ImportError:
    from .numpy_compat import unstructured_to_structured


_DATATYPES = {}
_DATATYPES[PointField.INT8] = np.dtype(np.int8)
_DATATYPES[PointField.UINT8] = np.dtype(np.uint8)
_DATATYPES[PointField.INT16] = np.dtype(np.int16)
_DATATYPES[PointField.UINT16] = np.dtype(np.uint16)
_DATATYPES[PointField.INT32] = np.dtype(np.int32)
_DATATYPES[PointField.UINT32] = np.dtype(np.uint32)
_DATATYPES[PointField.FLOAT32] = np.dtype(np.float32)
_DATATYPES[PointField.FLOAT64] = np.dtype(np.float64)

DUMMY_FIELD_PREFIX = "unnamed_field"


def dtype_from_fields(
    fields,  # type: Iterable[PointField]
):
    # type: (...) -> np.dtype
    """
    Convert a Iterable of sensor_msgs.msg.PointField messages to a np.dtype.
    :param fields: The point cloud fields.
                   (Type: iterable of sensor_msgs.msg.PointField)
    :returns: NumPy datatype
    """
    # Create a lists containing the names, offsets and datatypes of all fields
    field_names = []
    field_offsets = []
    field_datatypes = []
    for i, field in enumerate(fields):
        # Datatype as numpy datatype
        datatype = _DATATYPES[field.datatype]
        # Name field
        if field.name == "":
            name = "%s_%s" % (DUMMY_FIELD_PREFIX, i)
        else:
            name = field.name
        # Handle fields with count > 1 by creating subfields with a suffix consiting
        # of "_" followed by the subfield counter [0 -> (count - 1)]
        assert field.count > 0, "Can't process fields with count = 0."
        for a in range(field.count):
            # Add suffix if we have multiple subfields
            if field.count > 1:
                subfield_name = "%s_%s" % (name, a)
            else:
                subfield_name = name
            assert (
                subfield_name not in field_names
            ), "Duplicate field names are not allowed!"
            field_names.append(subfield_name)
            # Create new offset that includes subfields
            field_offsets.append(field.offset + a * datatype.itemsize)
            field_datatypes.append(datatype.str)

    # Create a tuple for each field containing name and data type
    return np.dtype(
        {"names": field_names, "formats": field_datatypes, "offsets": field_offsets}
    )


def create_cloud(
    fields,  # type: Iterable[PointField]
    points,  # type: Iterable
):
    # type (...)-> PointCloud2
    """
    Create a sensor_msgs.msg.PointCloud2 message.
    :param header: The point cloud header. (Type: std_msgs.msg.Header)
    :param fields: The point cloud fields.
                   (Type: iterable of sensor_msgs.msg.PointField)
    :param points: The point cloud points. List of iterables, i.e. one iterable
                   for each point, with the elements of each iterable being the
                   values of the fields for that point (in the same order as
                   the fields parameter)
    :return: The point cloud as sensor_msgs.msg.PointCloud2
    """
    # Check if input is numpy array
    if isinstance(points, np.ndarray):
        # Check if this is an unstructured array
        if points.dtype.names is None:
            assert all(
                fields[0].datatype == field.datatype for field in fields[1:]
            ), "All fields need to have the same datatype. Pass a structured NumPy array \
                    with multiple dtypes otherwise."
            # Convert unstructured to structured array
            points = unstructured_to_structured(points, dtype=dtype_from_fields(fields))
        else:
            assert points.dtype == dtype_from_fields(
                fields
            ), "PointFields and structured NumPy array dtype do not match for all fields! \
                    Check their field order, names and types."
    else:
        # Cast python objects to structured NumPy array (slow)
        points = np.array(
            # Points need to be tuples in the structured array
            list(map(tuple, points)),
            dtype=dtype_from_fields(fields),
        )

    # Handle organized clouds
    assert (
        len(points.shape) <= 2
    ), "Too many dimensions for organized cloud! \
            Points can only be organized in max. two dimensional space"
    height = 1
    width = points.shape[0]
    # Check if input points are an organized cloud (2D array of points)
    if len(points.shape) == 2:
        height = points.shape[1]

    # Convert numpy points to array.array
    memory_view = memoryview(points)
    casted = memory_view.cast("B")
    array_array = array.array("B")
    array_array.frombytes(casted)

    # Put everything together
    cloud = PointCloud2(
        height=height,
        width=width,
        is_dense=False,
        is_bigendian=sys.byteorder != "little",
        fields=fields,
        point_step=points.dtype.itemsize,
        row_step=(points.dtype.itemsize * width),
    )

    cloud.data = array_array
    return cloud


def pointcloud2_to_formant_pointcloud(
    message,  # type: PointCloud2
):
    if message.is_bigendian:
        raise Exception("unsupported point cloud endianness")
    if message.data is None:
        raise Exception("Pointcloud has no data")
    x_offset = None
    y_offset = None
    z_offset = None
    intensity_offset = None

    x_size = None
    y_size = None
    z_size = None
    intensity_size = None

    for field in message.fields:
        if field.name == "x":
            x_offset = field.offset
            x_size = 8 if field.datatype == DOUBLE_DATA_TYPE else 4
        elif field.name == "y":
            y_offset = field.offset
            y_size = 8 if field.datatype == DOUBLE_DATA_TYPE else 4
        elif field.name == "z":
            z_offset = field.offset
            z_size = 8 if field.datatype == DOUBLE_DATA_TYPE else 4
        elif field.name == "intensity" or field.name == "rgb":
            intensity_offset = field.offset
            intensity_size = 8 if field.datatype == DOUBLE_DATA_TYPE else 4
        else:
            continue

        if field.datatype not in [FLOAT_DATA_TYPE, DOUBLE_DATA_TYPE]:
            raise Exception(
                "error: unsupported pointcloud2 datatype: %s for field: %s"
                % (field.datatype, field.name)
            )

        if field.count != 1:
            raise Exception("error: unsupported pointcloud2 count")

    if (
        x_offset is None
        or y_offset is None
        or z_offset is None
        or x_size is None
        or y_size is None
        or z_size is None
    ):
        raise Exception("Error: Missing X, Y, or Z fields")

    count = message.height * message.width

    xs = np.zeros((count, x_size), dtype="b")
    ys = np.zeros((count, y_size), dtype="b")
    zs = np.zeros((count, z_size), dtype="b")
    if intensity_offset is not None:
        intensities = np.zeros((count, intensity_size), dtype="b")

    if message.point_step:
        size = message.point_step
    else:
        size = 4 * x_size

    data = np.reshape(np.array(message.data, dtype="b"), (count, size),)

    xs = data[:, x_offset : x_offset + x_size]
    ys = data[:, y_offset : y_offset + y_size]
    zs = data[:, z_offset : z_offset + z_size]
    if intensity_offset is not None:
        intensities = data[:, intensity_offset : intensity_offset + intensity_size]

    if intensity_offset is None:
        points = np.concatenate((xs, ys, zs)).tobytes()
    else:
        points = np.concatenate((xs, ys, zs, intensities)).tobytes()

    buffer = (
        """VERSION 0.7
FIELDS x y z rgb
SIZE 4 4 4 4
TYPE F F F F
WIDTH %s
HEIGHT 1
DATA binary_compressed
"""
        % count
    )
    compressed = lzf.compress(points, 2 * len(points))
    raw = (
        buffer.encode("utf-8")
        + struct.pack("<I", len(compressed))
        + struct.pack("<I", len(points))
        + compressed
    )

    return raw
