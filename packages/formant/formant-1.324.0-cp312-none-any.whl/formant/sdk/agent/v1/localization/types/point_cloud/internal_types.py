import sys
from typing import Any

python3 = True if sys.hexversion > 0x03000000 else False


# TODO: Do not require pointcloud2 as intermidate step
class PointCloud2:
    def __init__(
        self, height, width, is_dense, is_bigendian, fields, point_step, row_step
    ):
        self.height = height
        self.width = width
        self.is_dense = is_dense
        self.is_bigendian = is_bigendian
        self.fields = fields
        self.point_step = point_step
        self.row_step = row_step
        self.data = None  # type: Any


class PointField:

    _full_text = """# This message holds the description of one point entry in the
# PointCloud2 message format.
uint8 INT8    = 1
uint8 UINT8   = 2
uint8 INT16   = 3
uint8 UINT16  = 4
uint8 INT32   = 5
uint8 UINT32  = 6
uint8 FLOAT32 = 7
uint8 FLOAT64 = 8

string name      # Name of field
uint32 offset    # Offset from start of point struct
uint8  datatype  # Datatype enumeration, see above
uint32 count     # How many elements in the field
"""
    # Pseudo-constants
    INT8 = 1
    UINT8 = 2
    INT16 = 3
    UINT16 = 4
    INT32 = 5
    UINT32 = 6
    FLOAT32 = 7
    FLOAT64 = 8

    __slots__ = ["name", "offset", "datatype", "count"]
    _slot_types = ["string", "uint32", "uint8", "uint32"]

    def __init__(self, name, offset, datatype, count):
        self.name = name
        self.offset = offset
        self.datatype = datatype
        self.count = count
