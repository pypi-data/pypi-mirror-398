from struct import pack, unpack
import sys
import ctypes
from typing import Union

try:
    from pyaxml.proto import axml_pb2
except ImportError:
    print("proto is not build")
    sys.exit(1)

AXML_HEADER_SIZE = 8
AXML_STRING_POOL_HEADER_SIZE = 28
AXML_RES_TABLE_HEADER_SIZE = AXML_HEADER_SIZE + 4


class AConfiguration:
    """AConfiguration"""

    # See http://aospxref.com/android-13.0.0_r3/xref/frameworks/native/include/android/configuration.h#56

    ORIENTATION_ANY = 0x0000
    ORIENTATION_PORT = 0x0001
    ORIENTATION_LAND = 0x0002
    ORIENTATION_SQUARE = 0x0003
    TOUCHSCREEN_ANY = 0x0000
    TOUCHSCREEN_NOTOUCH = 0x0001
    TOUCHSCREEN_STYLUS = 0x0002
    TOUCHSCREEN_FINGER = 0x0003
    DENSITY_DEFAULT = 0
    DENSITY_LOW = 120
    DENSITY_MEDIUM = 160
    DENSITY_TV = 213
    DENSITY_HIGH = 240
    DENSITY_XHIGH = 320
    DENSITY_XXHIGH = 480
    DENSITY_XXXHIGH = 640
    DENSITY_ANY = 0xFFFE
    DENSITY_NONE = 0xFFFF
    KEYBOARD_ANY = 0x0000
    KEYBOARD_NOKEYS = 0x0001
    KEYBOARD_QWERTY = 0x0002
    KEYBOARD_12KEY = 0x0003
    NAVIGATION_ANY = 0x0000
    NAVIGATION_NONAV = 0x0001
    NAVIGATION_DPAD = 0x0002
    NAVIGATION_TRACKBALL = 0x0003
    NAVIGATION_WHEEL = 0x0004
    KEYSHIDDEN_ANY = 0x0000
    KEYSHIDDEN_NO = 0x0001
    KEYSHIDDEN_YES = 0x0002
    KEYSHIDDEN_SOFT = 0x0003
    NAVHIDDEN_ANY = 0x0000
    NAVHIDDEN_NO = 0x0001
    NAVHIDDEN_YES = 0x0002
    SCREENSIZE_ANY = 0x00
    SCREENSIZE_SMALL = 0x01
    SCREENSIZE_NORMAL = 0x02
    SCREENSIZE_LARGE = 0x03
    SCREENSIZE_XLARGE = 0x04
    SCREENLONG_ANY = 0x00
    SCREENLONG_NO = 0x1
    SCREENLONG_YES = 0x2
    SCREENROUND_ANY = 0x00
    SCREENROUND_NO = 0x1
    SCREENROUND_YES = 0x2
    WIDE_COLOR_GAMUT_ANY = 0x00
    WIDE_COLOR_GAMUT_NO = 0x1
    WIDE_COLOR_GAMUT_YES = 0x2
    HDR_ANY = 0x00
    HDR_NO = 0x1
    HDR_YES = 0x2
    UI_MODE_TYPE_ANY = 0x00
    UI_MODE_TYPE_NORMAL = 0x01
    UI_MODE_TYPE_DESK = 0x02
    UI_MODE_TYPE_CAR = 0x03
    UI_MODE_TYPE_TELEVISION = 0x04
    UI_MODE_TYPE_APPLIANCE = 0x05
    UI_MODE_TYPE_WATCH = 0x06
    UI_MODE_TYPE_VR_HEADSET = 0x07
    UI_MODE_NIGHT_ANY = 0x00
    UI_MODE_NIGHT_NO = 0x1
    UI_MODE_NIGHT_YES = 0x2
    SCREEN_WIDTH_DP_ANY = 0x0000
    SCREEN_HEIGHT_DP_ANY = 0x0000
    SMALLEST_SCREEN_WIDTH_DP_ANY = 0x0000
    LAYOUTDIR_ANY = 0x00
    LAYOUTDIR_LTR = 0x01
    LAYOUTDIR_RTL = 0x02
    MCC = 0x0001
    MNC = 0x0002
    LOCALE = 0x0004
    TOUCHSCREEN = 0x0008
    KEYBOARD = 0x0010
    KEYBOARD_HIDDEN = 0x0020
    NAVIGATION = 0x0040
    ORIENTATION = 0x0080
    DENSITY = 0x0100
    SCREEN_SIZE = 0x0200
    VERSION = 0x0400
    SCREEN_LAYOUT = 0x0800
    UI_MODE = 0x1000
    SMALLEST_SCREEN_SIZE = 0x2000
    LAYOUTDIR = 0x4000
    SCREEN_ROUND = 0x8000
    COLOR_MODE = 0x10000
    MNC_ZERO = 0xFFFF


class ComplexConsts:
    """ComplexConsts"""
    # Units
    UNIT_PX = 0
    UNIT_DIP = 1
    UNIT_SP = 2
    UNIT_PT = 3
    UNIT_IN = 4
    UNIT_MM = 5
    UNIT_FRACTION = 0
    UNIT_FRACTION_PARENT = 1

    # Radix types
    RADIX_23p0 = 0
    RADIX_16p7 = 1
    RADIX_8p15 = 2
    RADIX_0p23 = 3


class TypedValue:
    """TypedValue"""

    TYPE_NULL = 0x0
    TYPE_REFERENCE = 0x1
    TYPE_ATTRIBUTE = 0x02
    TYPE_STRING = 0x03
    TYPE_FLOAT = 0x04
    TYPE_DIMENSION = 0x05
    TYPE_FRACTION = 0x06
    TYPE_FIRST_INT = 0x10
    TYPE_INT_DEC = 0x10
    TYPE_INT_HEX = 0x11
    TYPE_INT_BOOLEAN = 0x12
    TYPE_FIRST_COLOR_INT = 0x1C
    TYPE_INT_COLOR_ARGB8 = 0x1C
    TYPE_INT_COLOR_RGB8 = 0x1D
    TYPE_INT_COLOR_ARGB4 = 0x1E
    TYPE_INT_COLOR_RGB4 = 0x1F
    TYPE_LAST_COLOR_INT = 0x1F
    TYPE_LAST_INT = 0x1F

    COMPLEX_RADIX_SHIFT = 4
    COMPLEX_RADIX_MASK = 0x3
    COMPLEX_UNIT_SHIFT = 0
    COMPLEX_UNIT_MASK = 0xF

    COMPLEX_MANTISSA_SHIFT = 8
    COMPLEX_MANTISSA_MASK = 0xFFFFFF

    DIMENSION_UNIT_STRS = ["px", "dip", "sp", "pt", "in", "mm"]

    FRACTION_UNIT_STRS = ["%", "%p"]

    @staticmethod
    def get_type(t: int):
        """return type of TypedValue

        Args:
            t (int): UID

        Returns:
            _type_: type link to UID
        """
        return t >> 24

    MANTISSA_MULT = 1.0 / float(1 << COMPLEX_MANTISSA_SHIFT)
    RADIX_MULTS = [
        1.0 * MANTISSA_MULT,
        1.0 / float(1 << 7) * MANTISSA_MULT,
        1.0 / (1 << 15) * MANTISSA_MULT,
        1.0 / float(1 << 23) * MANTISSA_MULT,
    ]

    @staticmethod
    def complex_to_float(complexe: int) -> float:
        """convert complex to float

        Args:
            complexe (int): complex value

        Returns:
            float: float value
        """
        return (
            complexe & (TypedValue.COMPLEX_MANTISSA_MASK << TypedValue.COMPLEX_MANTISSA_SHIFT)
        ) * TypedValue.RADIX_MULTS[
            (complexe >> TypedValue.COMPLEX_RADIX_SHIFT) & TypedValue.COMPLEX_RADIX_MASK
        ]

    @staticmethod
    def float_to_complex(val: str) -> int:
        """Convert float to complex int representation (like Android TypedValue).

        Args:
            value (float): The float value (e.g., 400.000000)

        Returns:
            int: Complex representation
        """
        # --- Match suffix to unit ---
        if val.endswith("%"):
            num = val[:-1]
            unit = ComplexConsts.UNIT_FRACTION
        elif val.endswith("dip"):
            num = val[:-3]
            unit = ComplexConsts.UNIT_DIP
        elif val.endswith("dp"):
            num = val[:-2]
            unit = ComplexConsts.UNIT_DIP
        elif val.endswith("sp"):
            num = val[:-2]
            unit = ComplexConsts.UNIT_SP
        elif val.endswith("px"):
            num = val[:-2]
            unit = ComplexConsts.UNIT_PX
        elif val.endswith("pt"):
            num = val[:-2]
            unit = ComplexConsts.UNIT_PT
        elif val.endswith("in"):
            num = val[:-2]
            unit = ComplexConsts.UNIT_IN
        elif val.endswith("mm"):
            num = val[:-2]
            unit = ComplexConsts.UNIT_MM
        else:
            raise ValueError("Invalid unit suffix in: " + val)

        # --- Convert numeric part ---
        f = float(num)

        if -1.0 < f < 1.0:
            base = int(f * (1 << 23))
            radix = ComplexConsts.RADIX_0p23
        elif -0x100 < f < 0x100:
            base = int(f * (1 << 15))
            radix = ComplexConsts.RADIX_8p15
        elif -0x10000 < f < 0x10000:
            base = int(f * (1 << 7))
            radix = ComplexConsts.RADIX_16p7
        else:
            base = int(f)
            radix = ComplexConsts.RADIX_23p0

        return (base << 8) | (radix << 4) | unit

    @staticmethod
    def coerce_to_string(typet: int, data: int) -> Union[str, None]:
        """coerce to string

        Args:
            typet (int): type of value
            data (int): data link to type

        Returns:
            str: coerce string
        """
        if typet == TypedValue.TYPE_NULL:
            return "nil"
        if typet == TypedValue.TYPE_REFERENCE:
            return "@" + hex(data)[2:]
        if typet == TypedValue.TYPE_ATTRIBUTE:
            return "?" + hex(data)[2:]
        if typet == TypedValue.TYPE_FLOAT:
            return str(ctypes.c_float(data).value)
        if typet == TypedValue.TYPE_DIMENSION:
            return (
                str(TypedValue.complex_to_float(data))
                + TypedValue.DIMENSION_UNIT_STRS[
                    (data >> TypedValue.COMPLEX_UNIT_SHIFT) & TypedValue.COMPLEX_UNIT_MASK
                ]
            )
        if typet == TypedValue.TYPE_FRACTION:
            return (
                str(TypedValue.complex_to_float(data) * 100)
                + TypedValue.FRACTION_UNIT_STRS[
                    (data >> TypedValue.COMPLEX_UNIT_SHIFT) & TypedValue.COMPLEX_UNIT_MASK
                ]
            )
        if typet == TypedValue.TYPE_INT_HEX:
            return hex(data)
        if typet == TypedValue.TYPE_INT_BOOLEAN:
            return "true" if data != 0 else "false"
        if typet >= TypedValue.TYPE_FIRST_COLOR_INT and typet <= TypedValue.TYPE_LAST_COLOR_INT:
            return "#" + hex(data)[2:]
        if typet >= TypedValue.TYPE_FIRST_INT and typet <= TypedValue.TYPE_LAST_INT:
            return str(ctypes.c_int32(data).value)

        return None


class AXMLHeader:
    """AXMLHeader class to build an AXMLHeader"""

    def __init__(
        self,
        type_: int = 0,
        size: int = 0,
        proto: axml_pb2.AXMLHeader = None,
        base_proto: axml_pb2.AXMLHeader = None,
    ):
        """Initialize an AXMLHeader

        Args:
            type_ (int, optional): type_ element from ResType. Defaults to 0.
            size (int, optional): size of data contain belong to this AXMLHeader. Defaults to 0.
            proto (axml_pb2.AXMLHeader, optional):
              define AXMLHeader by a protobuff. Defaults to None.
        """

        if proto is None:
            if base_proto:
                self.proto = base_proto
            else:
                self.proto = axml_pb2.AXMLHeader()
            self.proto.type = type_
            self.proto.size = size
            self.proto.header_size = AXML_HEADER_SIZE
        else:
            self.proto = proto

    def pack(self) -> bytes:
        """pack the AXMLHeader element

        Returns:
            bytes: return the AXMLHeader element packed
        """
        return pack("<HHL", self.proto.type, self.proto.header_size, self.proto.size)

    @staticmethod
    def from_axml(buff: bytes, proto=None):
        """Convert AXMLHeader buffer to AXMLHeader object

        Args:
            buff (bytes): buffer contain AXMLHeader object

        Returns:
            tuple[pyaxml.AXMLHeader, bytes]:
              return AXMLHeader element and buffer offset at the end of the reading
        """
        header = AXMLHeader()
        if proto:
            header.proto = proto
        header.proto.type, header.proto.header_size, header.proto.size = unpack("<HHL", buff[:8])
        return header, buff[8:]


class AXMLHeaderXML(AXMLHeader):
    """AXMLHeaderXML class to build an AXMLHeader with the type RES_XML_TYPE"""

    def __init__(self, size: int = 0, proto: axml_pb2.AXMLHeader = None):
        """Initialize an AXMLHeader with the type RES_XML_TYPE

        Args:
            size (int, optional): size of data contain belong to this AXMLHeader. Defaults to 0.
            proto (axml_pb2.AXMLHeader, optional):
              define AXMLHeader by a protobuff. Defaults to None.
        """
        if proto is None:
            super().__init__(axml_pb2.RES_XML_TYPE, size)
        else:
            self.proto = proto

    @staticmethod
    def from_axml(buff: bytes, proto=None):
        """Convert AXMLHeaderXML buffer to AXMLHeaderXML object

        Args:
            buff (bytes): buffer contain AXMLHeaderXML object

        Returns:
            tuple[pyaxml.AXMLHeaderXML, bytes]:
              return AXMLHeaderXML element and buffer offset at the end of the reading
        """
        header_xml = AXMLHeaderXML()
        if proto:
            header_xml.proto = proto
        header, buff = AXMLHeader.from_axml(buff)
        if header.proto.type != axml_pb2.RES_XML_TYPE:
            raise TypeError("AXMLHeaderXML file wrong format no XML_TYPE")
        header_xml.proto.type = header.proto.type
        header_xml.proto.size = header.proto.size
        header_xml.proto.header_size = header.proto.header_size
        return header_xml, buff


class AXMLHeaderRESTABLE:
    """AXMLHeaderRESTABLE class to build an AXMLHeader with the type RES_RES_TABLE_TYPE"""

    def __init__(
        self,
        size: int = 0,
        package_count: int = 0,
        proto: axml_pb2.AXMLHeaderRESTABLE = None,
    ):
        """Initialize AXMLHeader for RES_TABLE

        Args:
            size (int, optional): size of the RES_HEADER block. Defaults to 0.
            package_count (int, optional): number of package. Defaults to 0.
            proto (axml_pb2.AXMLHeaderRESTABLE, optional):
              protobuff of AXMLHeaderRESTABLE. Defaults to None.
        """

        if proto is None:
            self.proto = axml_pb2.AXMLHeaderRESTABLE()
            self.proto.package_count = package_count
            AXMLHeader(axml_pb2.RES_TABLE_TYPE, size, base_proto=self.proto.hnd)
            self.proto.hnd.header_size = AXML_RES_TABLE_HEADER_SIZE
        else:
            self.proto = proto

    def pack(self) -> bytes:
        """pack the AXMLHeader element

        Returns:
            bytes: return the AXMLHeader element packed
        """
        return AXMLHeader(proto=self.proto.hnd).pack() + pack("<L", self.proto.package_count)

    @staticmethod
    def from_axml(buff: bytes, proto=None):
        """Convert AXMLHeaderRESTABLE buffer to AXMLHeaderRESTABLE object

        Args:
            buff (bytes): buffer contain AXMLHeaderRESTABLE object

        Returns:
            tuple[pyaxml.AXMLHeaderRESTABLE, bytes]:
              return AXMLHeaderRESTABLE element and buffer offset at the end of the reading
        """
        restable_header = AXMLHeaderRESTABLE()
        if proto:
            restable_header.proto = proto
        _, buff = AXMLHeader.from_axml(buff, proto=restable_header.proto.hnd)
        restable_header.proto.package_count = unpack("<L", buff[:4])[0]
        return restable_header, buff[4:]
