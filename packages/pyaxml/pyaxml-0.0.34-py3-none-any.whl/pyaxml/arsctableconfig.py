import sys

try:
    from pyaxml.proto import axml_pb2
except ImportError:
    print("proto is not build")
    sys.exit(1)

from struct import pack, unpack
from pyaxml.header import AConfiguration


class ARSCResTableConfig:
    """ARSCResTableConfig"""

    # http://aospxref.com/android-13.0.0_r3/xref/frameworks/base/libs/androidfw/include/androidfw/ResourceTypes.h#946

    ORIENTATION_ANY = AConfiguration.ORIENTATION_ANY
    ORIENTATION_PORT = AConfiguration.ORIENTATION_PORT
    ORIENTATION_LAND = AConfiguration.ORIENTATION_LAND
    ORIENTATION_SQUARE = AConfiguration.ORIENTATION_SQUARE

    TOUCHSCREEN_ANY = AConfiguration.TOUCHSCREEN_ANY
    TOUCHSCREEN_NOTOUCH = AConfiguration.TOUCHSCREEN_NOTOUCH
    TOUCHSCREEN_STYLUS = AConfiguration.TOUCHSCREEN_STYLUS
    TOUCHSCREEN_FINGER = AConfiguration.TOUCHSCREEN_FINGER

    DENSITY_DEFAULT = AConfiguration.DENSITY_DEFAULT
    DENSITY_LOW = AConfiguration.DENSITY_LOW
    DENSITY_MEDIUM = AConfiguration.DENSITY_MEDIUM
    DENSITY_TV = AConfiguration.DENSITY_TV
    DENSITY_HIGH = AConfiguration.DENSITY_HIGH
    DENSITY_XHIGH = AConfiguration.DENSITY_XHIGH
    DENSITY_XXHIGH = AConfiguration.DENSITY_XXHIGH
    DENSITY_XXXHIGH = AConfiguration.DENSITY_XXXHIGH
    DENSITY_ANY = AConfiguration.DENSITY_ANY
    DENSITY_NONE = AConfiguration.DENSITY_NONE

    KEYBOARD_ANY = AConfiguration.KEYBOARD_ANY
    KEYBOARD_NOKEYS = AConfiguration.KEYBOARD_NOKEYS
    KEYBOARD_QWERTY = AConfiguration.KEYBOARD_QWERTY
    KEYBOARD_12KEY = AConfiguration.KEYBOARD_12KEY

    NAVIGATION_ANY = AConfiguration.NAVIGATION_ANY
    NAVIGATION_NONAV = AConfiguration.NAVIGATION_NONAV
    NAVIGATION_DPAD = AConfiguration.NAVIGATION_DPAD
    NAVIGATION_TRACKBALL = AConfiguration.NAVIGATION_TRACKBALL
    NAVIGATION_WHEEL = AConfiguration.NAVIGATION_WHEEL

    MASK_KEYSHIDDEN = 0x0003
    KEYSHIDDEN_ANY = AConfiguration.KEYSHIDDEN_ANY
    KEYSHIDDEN_NO = AConfiguration.KEYSHIDDEN_NO
    KEYSHIDDEN_YES = AConfiguration.KEYSHIDDEN_YES
    KEYSHIDDEN_SOFT = AConfiguration.KEYSHIDDEN_SOFT

    MASK_NAVHIDDEN = 0x000C
    SHIFT_NAVHIDDEN = 2
    NAVHIDDEN_ANY = AConfiguration.NAVHIDDEN_ANY << SHIFT_NAVHIDDEN
    NAVHIDDEN_NO = AConfiguration.NAVHIDDEN_NO << SHIFT_NAVHIDDEN
    NAVHIDDEN_YES = AConfiguration.NAVHIDDEN_YES << SHIFT_NAVHIDDEN

    SCREENWIDTH_ANY = 0
    SCREENHEIGHT_ANY = 0
    SDKVERSION_ANY = 0
    MINORVERSION_ANY = 0

    MASK_SCREENSIZE = 0x0F
    SCREENSIZE_ANY = AConfiguration.SCREENSIZE_ANY
    SCREENSIZE_SMALL = AConfiguration.SCREENSIZE_SMALL
    SCREENSIZE_NORMAL = AConfiguration.SCREENSIZE_NORMAL
    SCREENSIZE_LARGE = AConfiguration.SCREENSIZE_LARGE
    SCREENSIZE_XLARGE = AConfiguration.SCREENSIZE_XLARGE

    MASK_SCREENLONG = 0x30
    SHIFT_SCREENLONG = 4
    SCREENLONG_ANY = AConfiguration.SCREENLONG_ANY << SHIFT_SCREENLONG
    SCREENLONG_NO = AConfiguration.SCREENLONG_NO << SHIFT_SCREENLONG
    SCREENLONG_YES = AConfiguration.SCREENLONG_YES << SHIFT_SCREENLONG

    MASK_LAYOUTDIR = 0xC0
    SHIFT_LAYOUTDIR = 6
    LAYOUTDIR_ANY = AConfiguration.LAYOUTDIR_ANY << SHIFT_LAYOUTDIR
    LAYOUTDIR_LTR = AConfiguration.LAYOUTDIR_LTR << SHIFT_LAYOUTDIR
    LAYOUTDIR_RTL = AConfiguration.LAYOUTDIR_RTL << SHIFT_LAYOUTDIR

    MASK_UI_MODE_TYPE = 0x0F
    UI_MODE_TYPE_ANY = AConfiguration.UI_MODE_TYPE_ANY
    UI_MODE_TYPE_NORMAL = AConfiguration.UI_MODE_TYPE_NORMAL
    UI_MODE_TYPE_DESK = AConfiguration.UI_MODE_TYPE_DESK
    UI_MODE_TYPE_CAR = AConfiguration.UI_MODE_TYPE_CAR
    UI_MODE_TYPE_TELEVISION = AConfiguration.UI_MODE_TYPE_TELEVISION
    UI_MODE_TYPE_APPLIANCE = AConfiguration.UI_MODE_TYPE_APPLIANCE
    UI_MODE_TYPE_WATCH = AConfiguration.UI_MODE_TYPE_WATCH
    UI_MODE_TYPE_VR_HEADSET = AConfiguration.UI_MODE_TYPE_VR_HEADSET

    MASK_UI_MODE_NIGHT = 0x30
    SHIFT_UI_MODE_NIGHT = 4
    UI_MODE_NIGHT_ANY = AConfiguration.UI_MODE_NIGHT_ANY << SHIFT_UI_MODE_NIGHT
    UI_MODE_NIGHT_NO = AConfiguration.UI_MODE_NIGHT_NO << SHIFT_UI_MODE_NIGHT
    UI_MODE_NIGHT_YES = AConfiguration.UI_MODE_NIGHT_YES << SHIFT_UI_MODE_NIGHT

    MASK_SCREENROUND = 0x03
    SCREENROUND_ANY = AConfiguration.SCREENROUND_ANY
    SCREENROUND_NO = AConfiguration.SCREENROUND_NO
    SCREENROUND_YES = AConfiguration.SCREENROUND_YES

    MASK_WIDE_COLOR_GAMUT = 0x03
    WIDE_COLOR_GAMUT_ANY = AConfiguration.WIDE_COLOR_GAMUT_ANY
    WIDE_COLOR_GAMUT_NO = AConfiguration.WIDE_COLOR_GAMUT_NO
    WIDE_COLOR_GAMUT_YES = AConfiguration.WIDE_COLOR_GAMUT_YES

    MASK_HDR = 0x0C
    SHIFT_HDR = 2
    HDR_ANY = AConfiguration.HDR_ANY << SHIFT_HDR
    HDR_NO = AConfiguration.HDR_NO << SHIFT_HDR
    HDR_YES = AConfiguration.HDR_YES << SHIFT_HDR

    def __init__(self, proto: axml_pb2.ARSCResTableConfig = None):
        """_summary_

        Args:
            proto (axml_pb2.ARSCResTableConfig, optional): _description_. Defaults to None.
        """
        if proto:
            self.proto = proto
        else:
            self.proto = axml_pb2.ARSCResTableConfig()
            self.proto.size = 16

    @property
    def get_proto(self):
        """_summary_

        Returns:
            _type_: _description_
        """
        return self.proto

    def compute(self):
        """Compute all fields to have all AXML elements"""

    def pack(self) -> bytes:
        """pack the AXML element

        Returns:
            bytes: return the AXML element packed
        """
        extra = b""
        if self.proto.HasField("input"):
            extra += pack("<I", self.proto.input)
            if self.proto.HasField("screen_size"):
                extra += pack("<I", self.proto.screen_size)
                if self.proto.HasField("version"):
                    extra += pack("<I", self.proto.version)
                    if self.proto.HasField("screen_config"):
                        extra += pack("<I", self.proto.screen_config)
                        if self.proto.HasField("screen_size_dp"):
                            extra += pack("<I", self.proto.screen_size_dp)
                            if self.proto.HasField("locale_script"):
                                extra += pack("<I", self.proto.locale_script)
                                if self.proto.HasField("locale_variant"):
                                    extra += pack("<I", self.proto.locale_variant)
                                    if self.proto.HasField("screen_config2"):
                                        extra += pack("<I", self.proto.screen_config2)
        extra += self.proto.padding
        return (
            pack(
                "<IIII",
                self.proto.size,
                self.proto.imsi,
                self.proto.locale,
                self.proto.screenType,
            )
            + extra
        )

    @staticmethod
    def from_axml(buff: bytes, proto: axml_pb2.ARSCResTableConfig = None):
        """Convert ARSCResTableConfig buffer to ARSCResTableConfig object

        Args:
            buff (bytes): buffer contain ARSCResTableConfig object

        Returns:
            tuple[pyaxml.ARSCResTableConfig, bytes]:
              return ARSCResTableConfig element and buffer offset at the end of the reading
        """
        config = ARSCResTableConfig()
        if len(buff) < 16:
            raise ValueError(f"size ARSCResTableConfig has no minimal size 16 ({len(buff)})")
        if proto:
            config.proto = proto
        (
            config.proto.size,
            config.proto.imsi,
            config.proto.locale,
            config.proto.screenType,
        ) = unpack("<IIII", buff[:16])
        if len(buff) < config.proto.size or config.proto.size < 16:
            raise ValueError(
                "size ARSCResTableConfig to big to parse buffer or has no minimal size"
            )
        off = 0
        if config.proto.size >= 20:
            config.proto.input = unpack("<I", buff[16:20])[0]
            off += 4
        if config.proto.size >= 20 + off:
            config.proto.screen_size = unpack("<I", buff[16 + off : 20 + off])[0]
            off += 4
        if config.proto.size >= 20 + off:
            config.proto.version = unpack("<I", buff[16 + off : 20 + off])[0]
            off += 4
        if config.proto.size >= 20 + off:
            config.proto.screen_config = unpack("<I", buff[16 + off : 20 + off])[0]
            off += 4
        if config.proto.size >= 20 + off:
            config.proto.screen_size_dp = unpack("<I", buff[16 + off : 20 + off])[0]
            off += 4
        if config.proto.size >= 20 + off:
            config.proto.locale_script = unpack("<I", buff[16 + off : 20 + off])[0]
            off += 4
        if config.proto.size >= 20 + off:
            config.proto.locale_variant = unpack("<I", buff[16 + off : 20 + off])[0]
            off += 4
        if config.proto.size >= 20 + off:
            config.proto.screen_config2 = unpack("<I", buff[16 + off : 20 + off])[0]
            off += 4
        config.proto.padding = buff[16 + off : config.proto.size]
        return config, buff[config.proto.size :]

    def _unpack_language_or_region(self, char_in, char_base):
        char_out = ""
        if char_in[0] & 0x80:
            first = char_in[1] & 0x1F
            second = ((char_in[1] & 0xE0) >> 5) + ((char_in[0] & 0x03) << 3)
            third = (char_in[0] & 0x7C) >> 2
            char_out += chr(first + char_base)
            char_out += chr(second + char_base)
            char_out += chr(third + char_base)
        else:
            if char_in[0]:
                char_out += chr(char_in[0])
            if char_in[1]:
                char_out += chr(char_in[1])
        return char_out

    def _pack_language_or_region(self, char_in: str) -> list[int]:
        char_out = [0x00, 0x00]
        if len(char_in) != 2:
            return char_out
        char_out[0] = ord(char_in[0])
        char_out[1] = ord(char_in[1])
        return char_out

    def set_language_and_region(self, language_region: str) -> None:
        """set language and region

        Args:
            language_region (str): language region
        """
        try:
            language, region = language_region.split("-r")
        except ValueError:
            language, region = language_region, None
        language_bytes = self._pack_language_or_region(language)
        if region:
            region_bytes = self._pack_language_or_region(region)
        else:
            region_bytes = [0x00, 0x00]
        self.proto.locale = (
            language_bytes[0]
            | (language_bytes[1] << 8)
            | (region_bytes[0] << 16)
            | (region_bytes[1] << 24)
        )

    def get_language_and_region(self) -> str:
        """
        Returns the combined language+region string or \x00\x00 for the default locale
        :return:
        """
        if self.proto.locale != 0:
            _language = self._unpack_language_or_region(
                [
                    self.proto.locale & 0xFF,
                    (self.proto.locale & 0xFF00) >> 8,
                ],
                ord("a"),
            )
            _region = self._unpack_language_or_region(
                [
                    (self.proto.locale & 0xFF0000) >> 16,
                    (self.proto.locale & 0xFF000000) >> 24,
                ],
                ord("0"),
            )
            return (_language + "-r" + _region) if _region else _language
        return "\x00\x00"

    def get_config_name_friendly(self) -> str:
        """
        Here for legacy reasons.

        use :meth:`~get_qualifier` instead.
        """
        return self.get_qualifier()

    def get_qualifier(self) -> str:
        """
        Return resource name qualifier for the current configuration.
        for example
        * `ldpi-v4`
        * `hdpi-v4`

        All possible qualifiers are listed in table 2 of
        https://developer.android.com/guide/topics/resources/providing-resources

        You can find how android process this at
        http://aospxref.com/android-13.0.0_r3/xref/frameworks/base/libs/androidfw/ResourceTypes.cpp#3243

        :return: str
        """
        res = []

        mcc = self.proto.imsi & 0xFFFF
        mnc = (self.proto.imsi & 0xFFFF0000) >> 16
        if mcc != 0:
            res.append("mcc%d" % mcc)
        if mnc != 0:
            res.append("mnc%d" % mnc)

        if self.proto.locale != 0:
            res.append(self.proto.get_language_and_region())

        screen_layout = self.proto.screen_config & 0xFF
        if (screen_layout & ARSCResTableConfig.MASK_LAYOUTDIR) != 0:
            if (
                screen_layout & ARSCResTableConfig.MASK_LAYOUTDIR
                == ARSCResTableConfig.LAYOUTDIR_LTR
            ):
                res.append("ldltr")
            elif (
                screen_layout & ARSCResTableConfig.MASK_LAYOUTDIR
                == ARSCResTableConfig.LAYOUTDIR_RTL
            ):
                res.append("ldrtl")
            else:
                res.append("layoutDir_%d" % (screen_layout & ARSCResTableConfig.MASK_LAYOUTDIR))

        smallest_screen_width_dp = (self.proto.screen_config & 0xFFFF0000) >> 16
        if smallest_screen_width_dp != 0:
            res.append("sw%ddp" % smallest_screen_width_dp)

        screen_width_dp = self.proto.screen_size_dp & 0xFFFF
        screen_height_dp = (self.proto.screen_size_dp & 0xFFFF0000) >> 16
        if screen_width_dp != 0:
            res.append("w%ddp" % screen_width_dp)
        if screen_height_dp != 0:
            res.append("h%ddp" % screen_height_dp)

        if (
            screen_layout & ARSCResTableConfig.MASK_SCREENSIZE
        ) != ARSCResTableConfig.SCREENSIZE_ANY:
            if (
                screen_layout & ARSCResTableConfig.MASK_SCREENSIZE
                == ARSCResTableConfig.SCREENSIZE_SMALL
            ):
                res.append("small")
            elif (
                screen_layout & ARSCResTableConfig.MASK_SCREENSIZE
                == ARSCResTableConfig.SCREENSIZE_NORMAL
            ):
                res.append("normal")
            elif (
                screen_layout & ARSCResTableConfig.MASK_SCREENSIZE
                == ARSCResTableConfig.SCREENSIZE_LARGE
            ):
                res.append("large")
            elif (
                screen_layout & ARSCResTableConfig.MASK_SCREENSIZE
                == ARSCResTableConfig.SCREENSIZE_XLARGE
            ):
                res.append("xlarge")
            else:
                res.append(
                    "screenLayoutSize_%d" % (screen_layout & ARSCResTableConfig.MASK_SCREENSIZE)
                )
        if (screen_layout & ARSCResTableConfig.MASK_SCREENLONG) != 0:
            if (
                screen_layout & ARSCResTableConfig.MASK_SCREENLONG
                == ARSCResTableConfig.SCREENLONG_NO
            ):
                res.append("notlong")
            elif (
                screen_layout & ARSCResTableConfig.MASK_SCREENLONG
                == ARSCResTableConfig.SCREENLONG_YES
            ):
                res.append("long")
            else:
                res.append(
                    "screenLayoutLong_%d" % (screen_layout & ARSCResTableConfig.MASK_SCREENLONG)
                )

        screen_layout2 = self.proto.screen_config2 & 0xFF
        if (screen_layout2 & ARSCResTableConfig.MASK_SCREENROUND) != 0:
            if (
                screen_layout2 & ARSCResTableConfig.MASK_SCREENROUND
                == ARSCResTableConfig.SCREENROUND_NO
            ):
                res.append("notround")
            elif (
                screen_layout2 & ARSCResTableConfig.MASK_SCREENROUND
                == ARSCResTableConfig.SCREENROUND_YES
            ):
                res.append("round")
            else:
                res.append(
                    "screenRound_%d" % (screen_layout2 & ARSCResTableConfig.MASK_SCREENROUND)
                )

        color_mode = (self.proto.screen_config2 & 0xFF00) >> 8
        if (color_mode & ARSCResTableConfig.MASK_WIDE_COLOR_GAMUT) != 0:
            if (
                color_mode & ARSCResTableConfig.MASK_WIDE_COLOR_GAMUT
                == ARSCResTableConfig.WIDE_COLOR_GAMUT_NO
            ):
                res.append("nowidecg")
            elif (
                color_mode & ARSCResTableConfig.MASK_WIDE_COLOR_GAMUT
                == ARSCResTableConfig.WIDE_COLOR_GAMUT_YES
            ):
                res.append("widecg")
            else:
                res.append(
                    "wideColorGamut_%d" % (color_mode & ARSCResTableConfig.MASK_WIDE_COLOR_GAMUT)
                )

        if (color_mode & ARSCResTableConfig.MASK_HDR) != 0:
            if color_mode & ARSCResTableConfig.MASK_HDR == ARSCResTableConfig.HDR_NO:
                res.append("lowdr")
            elif color_mode & ARSCResTableConfig.MASK_HDR == ARSCResTableConfig.HDR_YES:
                res.append("highdr")
            else:
                res.append("hdr_%d" % (color_mode & ARSCResTableConfig.MASK_HDR))

        orientation = self.proto.screenType & 0xFF
        if orientation != ARSCResTableConfig.ORIENTATION_ANY:
            if orientation == ARSCResTableConfig.ORIENTATION_PORT:
                res.append("port")
            elif orientation == ARSCResTableConfig.ORIENTATION_LAND:
                res.append("land")
            elif orientation == ARSCResTableConfig.ORIENTATION_SQUARE:
                res.append("square")
            else:
                res.append("orientation_%d" % orientation)

        ui_mode = (self.proto.screen_config & 0xFF00) >> 8
        if (ui_mode & ARSCResTableConfig.MASK_UI_MODE_TYPE) != ARSCResTableConfig.UI_MODE_TYPE_ANY:
            ui_mode = ui_mode & ARSCResTableConfig.MASK_UI_MODE_TYPE
            if ui_mode == ARSCResTableConfig.UI_MODE_TYPE_DESK:
                res.append("desk")
            elif ui_mode == ARSCResTableConfig.UI_MODE_TYPE_CAR:
                res.append("car")
            elif ui_mode == ARSCResTableConfig.UI_MODE_TYPE_TELEVISION:
                res.append("television")
            elif ui_mode == ARSCResTableConfig.UI_MODE_TYPE_APPLIANCE:
                res.append("appliance")
            elif ui_mode == ARSCResTableConfig.UI_MODE_TYPE_WATCH:
                res.append("watch")
            elif ui_mode == ARSCResTableConfig.UI_MODE_TYPE_VR_HEADSET:
                res.append("vrheadset")
            else:
                res.append("uiModeType_%d" % ui_mode)

        if (ui_mode & ARSCResTableConfig.MASK_UI_MODE_NIGHT) != 0:
            if (
                ui_mode & ARSCResTableConfig.MASK_UI_MODE_NIGHT
                == ARSCResTableConfig.UI_MODE_NIGHT_NO
            ):
                res.append("notnight")
            elif (
                ui_mode & ARSCResTableConfig.MASK_UI_MODE_NIGHT
                == ARSCResTableConfig.UI_MODE_NIGHT_YES
            ):
                res.append("night")
            else:
                res.append("uiModeNight_%d" % (ui_mode & ARSCResTableConfig.MASK_UI_MODE_NIGHT))

        density = (self.proto.screenType & 0xFFFF0000) >> 16
        if density != ARSCResTableConfig.DENSITY_DEFAULT:
            if density == ARSCResTableConfig.DENSITY_LOW:
                res.append("ldpi")
            elif density == ARSCResTableConfig.DENSITY_MEDIUM:
                res.append("mdpi")
            elif density == ARSCResTableConfig.DENSITY_TV:
                res.append("tvdpi")
            elif density == ARSCResTableConfig.DENSITY_HIGH:
                res.append("hdpi")
            elif density == ARSCResTableConfig.DENSITY_XHIGH:
                res.append("xhdpi")
            elif density == ARSCResTableConfig.DENSITY_XXHIGH:
                res.append("xxhdpi")
            elif density == ARSCResTableConfig.DENSITY_XXXHIGH:
                res.append("xxxhdpi")
            elif density == ARSCResTableConfig.DENSITY_NONE:
                res.append("nodpi")
            elif density == ARSCResTableConfig.DENSITY_ANY:
                res.append("anydpi")
            else:
                res.append("%ddpi" % (density))

        touchscreen = (self.proto.screenType & 0xFF00) >> 8
        if touchscreen != ARSCResTableConfig.TOUCHSCREEN_ANY:
            if touchscreen == ARSCResTableConfig.TOUCHSCREEN_NOTOUCH:
                res.append("notouch")
            elif touchscreen == ARSCResTableConfig.TOUCHSCREEN_FINGER:
                res.append("finger")
            elif touchscreen == ARSCResTableConfig.TOUCHSCREEN_STYLUS:
                res.append("stylus")
            else:
                res.append("touchscreen_%d" % touchscreen)

        keyboard = self.proto.input & 0xFF
        navigation = (self.proto.input & 0xFF00) >> 8
        input_flags = (self.proto.input & 0xFF0000) >> 16

        if input_flags & ARSCResTableConfig.MASK_KEYSHIDDEN != 0:
            input_flags = input_flags & ARSCResTableConfig.MASK_KEYSHIDDEN
            if input_flags == ARSCResTableConfig.KEYSHIDDEN_NO:
                res.append("keysexposed")
            elif input_flags == ARSCResTableConfig.KEYSHIDDEN_YES:
                res.append("keyshidden")
            elif input_flags == ARSCResTableConfig.KEYSHIDDEN_SOFT:
                res.append("keyssoft")

        if keyboard != ARSCResTableConfig.KEYBOARD_ANY:
            if keyboard == ARSCResTableConfig.KEYBOARD_NOKEYS:
                res.append("nokeys")
            elif keyboard == ARSCResTableConfig.KEYBOARD_QWERTY:
                res.append("qwerty")
            elif keyboard == ARSCResTableConfig.KEYBOARD_12KEY:
                res.append("12key")
            else:
                res.append("keyboard_%d" % keyboard)

        if input_flags & ARSCResTableConfig.MASK_NAVHIDDEN != 0:
            input_flags = input_flags & ARSCResTableConfig.MASK_NAVHIDDEN
            if input_flags == ARSCResTableConfig.NAVHIDDEN_NO:
                res.append("navexposed")
            elif input_flags == ARSCResTableConfig.NAVHIDDEN_YES:
                res.append("navhidden")
            else:
                res.append("inputFlagsNavHidden_%d" % input_flags)

        if navigation != ARSCResTableConfig.NAVIGATION_ANY:
            if navigation == ARSCResTableConfig.NAVIGATION_NONAV:
                res.append("nonav")
            elif navigation == ARSCResTableConfig.NAVIGATION_DPAD:
                res.append("dpad")
            elif navigation == ARSCResTableConfig.NAVIGATION_TRACKBALL:
                res.append("trackball")
            elif navigation == ARSCResTableConfig.NAVIGATION_WHEEL:
                res.append("wheel")
            else:
                res.append("navigation_%d" % navigation)

        screen_size = self.proto.screen_size
        if screen_size != 0:
            screen_width = self.proto.screen_size & 0xFFFF
            screen_height = (self.proto.screen_size & 0xFFFF0000) >> 16
            res.append("%dx%d" % (screen_width, screen_height))

        version = self.proto.version
        if version != 0:
            sdk_version = self.proto.version & 0xFFFF
            minor_version = (self.proto.version & 0xFFFF0000) >> 16
            res.append("v%d" % sdk_version)
            if minor_version != 0:
                res.append(".%d" % minor_version)

        return "-".join(res)

    def get_language(self) -> str:
        """get language

        Returns:
            str: return language in str
        """
        x = self.proto.locale & 0x0000FFFF
        return chr(x & 0x00FF) + chr((x & 0xFF00) >> 8)

    def get_country(self) -> str:
        """get country

        Returns:
            str: return country in str
        """
        x = (self.proto.locale & 0xFFFF0000) >> 16
        return chr(x & 0x00FF) + chr((x & 0xFF00) >> 8)

    def get_density(self) -> str:
        """get density

        Returns:
            str: return density in str
        """
        x = (self.proto.screenType >> 16) & 0xFFFF
        return x

    def is_default(self) -> bool:
        """
        Test if this is a default resource, which matches all

        This is indicated that all fields are zero.
        :return: True if default, False otherwise
        """
        return all(map(lambda x: x == 0, self._get_tuple()))

    def _get_tuple(self):
        return (
            self.proto.imsi,
            self.proto.locale,
            self.proto.screenType,
            self.proto.input,
            self.proto.screen_size,
            self.proto.version,
            self.proto.screen_config,
            self.proto.screen_size_dp,
            self.proto.screen_config2,
        )

    def __hash__(self):
        return hash(self._get_tuple())

    def __eq__(self, other):
        return self._get_tuple() == other._get_tuple()

    def __repr__(self):
        return f"<ARSCResTableConfig '{self.get_qualifier()}'={repr(self._get_tuple())}>"
