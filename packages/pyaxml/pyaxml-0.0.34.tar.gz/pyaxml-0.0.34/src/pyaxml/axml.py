import sys

from struct import pack, unpack
import re
import ctypes

try:
    from lxml import etree
except ImportError:
    import xml.etree.ElementTree as etree
from typing import Union, List
import logging

try:
    from pyaxml.proto import axml_pb2
except ImportError:
    print("proto is not build")
    sys.exit(1)

from pyaxml import public
from pyaxml.stringblocks import StringBlocks, StringBlock, AXMLHeader
from pyaxml.header import AXMLHeaderXML, TypedValue, AXML_HEADER_SIZE
from pyaxml.xmlelement import (
    ClassicalResXml,
    AXMLHeaderResXml,
    Attribute,
    ResXmlStartElement,
    AXMLHeaderStartElement,
    ResXmlStartNamespace,
    ResXmlEndNamespace,
    ResXmlEndElement,
    AXMLHeaderStartNamespace,
    AXMLHeaderEndElement,
    AXMLHeaderEndNamespace,
    ResourceXML,
)
from pyaxml.arscobject import ARSC


##############################################################################
#
#                              RESOURCEMAP
#
##############################################################################


class ResourceMap:
    """ResourceMap class to build all ResourceMap elements"""

    def __init__(
        self,
        res: Union[List[StringBlock], None] = None,
        proto: Union[axml_pb2.ResourceMap, None] = None,
    ):
        """initialize ResourceMap element

        Args:
            res (StringBlock], optional): List of StringBlock elements. Defaults to [].
            proto (axml_pb2.ResourceMap, optional):
              define ResourceMap by a protobuff. Defaults to None.
        """
        if res is None:
            res = []
        if proto is None:
            self.proto = axml_pb2.ResourceMap()
            self.proto.res.extend(res)
            AXMLHeader(axml_pb2.RES_XML_RESOURCE_MAP_TYPE, 8, base_proto=self.proto.header)
            self.proto.header.size = AXML_HEADER_SIZE + 4 * len(res)
        else:
            self.proto = proto

    def pack(self) -> bytes:
        """pack the ResourceMap element

        Returns:
            bytes: return the ResourceMap element packed
        """
        return AXMLHeader(proto=self.proto.header).pack() + b"".join(
            pack("<L", x) for x in self.proto.res
        )

    @staticmethod
    def from_axml(buff: bytes, proto=None):
        """Convert ResourceMap buffer to ResourceMap object

        Args:
            buff (bytes): buffer contain ResourceMap object

        Returns:
            tuple[pyaxml.ResourceMap, bytes]:
                 return ResourceMap element and buffer offset at the end of the reading
        """
        res_maps = ResourceMap()
        if proto:
            res_maps.proto = proto
        _, n_buff = AXMLHeader.from_axml(buff, proto=res_maps.proto.header)
        if res_maps.proto.header.type != axml_pb2.RES_XML_RESOURCE_MAP_TYPE:
            return None, buff
        for _ in range(int((res_maps.proto.header.size - res_maps.proto.header.header_size) / 4)):
            res_maps.proto.res.append(unpack("<L", n_buff[:4])[0])
            n_buff = n_buff[4:]
        return res_maps, n_buff


##############################################################################
#
#                              AXML OBJECT
#
##############################################################################


class AXML:
    """AXML object to parse AXML and generate AXML"""

    def __init__(self, proto: axml_pb2.AXML = None):
        """_summary_

        Args:
            proto (axml_pb2.AXML, optional): _description_. Defaults to None.
        """
        if proto:
            self.proto = proto
            self.stringblocks = StringBlocks(proto=self.proto.stringblocks)
        else:
            self.proto = axml_pb2.AXML()
            self.stringblocks = StringBlocks()

    @property
    def get_proto(self):
        """_summary_

        Returns:
            _type_: _description_
        """
        return self.proto

    ###########################################
    #                                         #
    #           ENCODE from XML               #
    #                                         #
    ###########################################

    def from_xml(self, root):
        """Convert Xml to Axml object

        Args:
            root (etree.ElementBase): Xml representation of AXML object
        """
        self.add_all_attrib(root)
        self.start_namespace("http://schemas.android.com/apk/res/android", "android")
        self.__from_xml_etree(root)
        self.end_namespace("http://schemas.android.com/apk/res/android", "android")
        self.compute()

    def __from_xml_etree(self, root):
        """Convert Xml to Axml object internally

        Args:
            root (etree.ElementBase): Xml representation of AXML object
        """
        self.start(root.tag, root.attrib)
        for e in root:
            self.__from_xml_etree(e)
        self.end(root.tag)

    def add_xml_elt(self, res_xml: ClassicalResXml, header_xml: type[AXMLHeaderResXml]):
        """Function to add an element in function of the type

        Args:
            res_xml (ClassicalResXml): Element
            header_xml (AXMLHeaderResXml): Header
        """
        res_xml.compute()

        header = header_xml(len(res_xml.content))

        elt = axml_pb2.XMLElement()
        elt.header.CopyFrom(header.proto)
        if isinstance(res_xml.proto, axml_pb2.ResXMLStartElement):
            elt.start_elt.CopyFrom(res_xml.proto)
        elif isinstance(res_xml.proto, axml_pb2.ResXMLStartNamespace):
            elt.start_ns.CopyFrom(res_xml.proto)
        elif isinstance(res_xml.proto, axml_pb2.ResXMLEndNamespace):
            elt.end_ns.CopyFrom(res_xml.proto)
        elif isinstance(res_xml.proto, axml_pb2.ResXMLEndElement):
            elt.end_elt.CopyFrom(res_xml.proto)
        self.proto.resourcexml.elts.append(elt)

    def start(self, root: str, attrib: dict):
        """Create start of element

        Args:
            root (str): Name of element
            attrib (dict): dict of all attribute of this element
        """
        index = self.stringblocks.get(root)
        _ = self.stringblocks.get("android")
        attributes = []

        dic_attrib = attrib.items()
        for k, v in dic_attrib:
            tmp = k.split("{")
            if len(tmp) > 1:
                tmp = tmp[1].split("}")
                name = self.stringblocks.get(tmp[1])
                namespace = self.stringblocks.get(tmp[0])
            else:
                namespace = 0xFFFFFFFF
                name = self.stringblocks.get(k)

            if v == "true":
                attributes.append(Attribute(namespace, name, 0xFFFFFFFF, 0x12000008, 1).proto)
            elif v == "false":
                attributes.append(Attribute(namespace, name, 0xFFFFFFFF, 0x12000008, 0).proto)
            elif re.search("^@android:[0-9a-fA-F]+$", v):
                attributes.append(
                    Attribute(namespace, name, 0xFFFFFFFF, 0x1000008, int(v[-8:], 16)).proto
                )
            elif re.search("^@[0-9a-fA-F]+$", v):
                attributes.append(
                    Attribute(namespace, name, 0xFFFFFFFF, 0x1000008, int(v[1:], 16)).proto
                )
            elif re.search("^0x[0-9a-fA-F]+$", v):
                attributes.append(
                    Attribute(namespace, name, 0xFFFFFFFF, 0x11000000, int(v[2:], 16)).proto
                )
            elif re.search("^#[0-9a-fA-F]+$", v):
                attributes.append(
                    Attribute(namespace, name, 0xFFFFFFFF, 0x1C000008, int(v[2:], 16)).proto
                )
            elif re.search(r"^\?[0-9a-fA-F]+$", v):
                attributes.append(
                    Attribute(namespace, name, 0xFFFFFFFF, 0x02000008, int(v[2:], 16)).proto
                )
            elif re.search(r"^\d+\.\d+(dip|dp|sp|px|pt|in|mm)$", v):
                value = TypedValue.float_to_complex(v)
                attributes.append(Attribute(namespace, name, 0xFFFFFFFF, 0x05000008, value).proto)
            else:
                if self.get_elt_string(name) == "versionName":
                    value = self.stringblocks.get(v)
                    attributes.append(Attribute(namespace, name, value, 0x3000008, value).proto)
                elif self.get_elt_string(name) == "compileSdkVersionCodename":
                    value = self.stringblocks.get(v)
                    attributes.append(Attribute(namespace, name, value, 0x3000008, value).proto)
                else:
                    try:
                        value = ctypes.c_uint32(int(v)).value
                        attributes.append(
                            Attribute(namespace, name, 0xFFFFFFFF, 0x10000008, value).proto
                        )
                    except ValueError:
                        try:
                            value = unpack(">L", pack("!f", float(v)))[0]
                            attributes.append(
                                Attribute(namespace, name, 0xFFFFFFFF, 0x04000008, value).proto
                            )
                        except ValueError:
                            value = self.stringblocks.get(v)
                            attributes.append(
                                Attribute(namespace, name, value, 0x3000008, value).proto
                            )

        content = ResXmlStartElement(0xFFFFFFFF, index, attributes)
        self.add_xml_elt(content, AXMLHeaderStartElement)

    def start_namespace(self, prefix: str, uri: str):
        """Create start of namespace

        Args:
            prefix (str): prefix of namespace
            uri (str): uri of namespace
        """
        index = self.stringblocks.get(prefix)
        i_namespace = self.stringblocks.get(uri)

        content = ResXmlStartNamespace(i_namespace, index)
        self.add_xml_elt(content, AXMLHeaderStartNamespace)

    def end_namespace(self, prefix: str, uri: str):
        """Create end of namespace

        Args:
            prefix (str): prefix of namespace
            uri (str): uri of namespace
        """
        index = self.stringblocks.get(prefix)
        i_namespace = self.stringblocks.get(uri)

        content = ResXmlEndNamespace(i_namespace, index)
        self.add_xml_elt(content, AXMLHeaderEndNamespace)

    def end(self, attrib: str):
        """Create end of element

        Args:
            attrib (str): name of end element
        """
        index = self.stringblocks.index(attrib)
        _ = self.stringblocks.index("android")

        content = ResXmlEndElement(0xFFFFFFFF, index)
        self.add_xml_elt(content, AXMLHeaderEndElement)

    def add_all_attrib(self, root):
        """Create Resource Map

        Args:
            root (etree.ElementBase): XML representation of AXML
        """
        res = []
        namespace = "{http://schemas.android.com/apk/res/android}"
        queue = [root]
        while len(queue) > 0:
            r = queue.pop()
            for child in r:
                queue.append(child)
            for k in r.attrib.keys():
                if k.startswith(namespace):
                    name = k[len(namespace) :]
                    if name in public.SYSTEM_RESOURCES["attributes"]["forward"]:
                        val = public.SYSTEM_RESOURCES["attributes"]["forward"][name]
                        if not val in res:
                            self.stringblocks.get(name)
                            res.append(val)
        self.proto.resourcemap.CopyFrom(ResourceMap(res=res).proto)

    ###########################################
    #                                         #
    #           ENCODE from XML               #
    #                                         #
    ###########################################

    def compute(self):
        """Compute all fields to have all AXML elements"""
        self.stringblocks.compute()
        self.proto.header_xml.CopyFrom(AXMLHeaderXML(len(self.pack())).proto)

    def pack(self) -> bytes:
        """pack the AXML element

        Returns:
            bytes: return the AXML element packed
        """
        self.proto.stringblocks.CopyFrom(self.stringblocks.proto)
        sb_pack = self.stringblocks.pack()
        if self.proto.HasField("resourcemap"):
            res = ResourceMap(proto=self.proto.resourcemap).pack()
        else:
            res = b""
        resxml = ResourceXML(proto=self.proto.resourcexml).pack()
        header_xml = AXMLHeaderXML(proto=self.proto.header_xml).pack()
        return header_xml + sb_pack + res + resxml

    @staticmethod
    def from_axml(buff: bytes, proto=None):
        """Convert AXML buffer to AXML object

        Args:
            buff (bytes): buffer contain AXML object

        Returns:
            tuple[pyaxml.AXML, bytes]:
                return AXML element and buffer offset at the end of the reading
        """
        axml = AXML()
        if proto:
            axml.proto = proto
        _, buff = AXMLHeader.from_axml(buff, proto=axml.proto.header_xml)
        sb, buff = StringBlocks.from_axml(buff, proto=axml.proto.stringblocks)

        # Resource Map is Optional we need to check before if it is one
        rmap, buff = ResourceMap.from_axml(buff, proto=axml.proto.resourcemap)
        if rmap is None:
            axml.proto.ClearField("resourcemap")
        _, buff = ResourceXML.from_axml(buff, proto=axml.proto.resourcexml)

        axml.stringblocks = sb

        return axml, buff
    
    def is_system_resources_string(self, index: int) -> bool:
        """Check if index is a part of system resource or not

        Args:
            index (int): index of target element

        Returns:
            bool: True if it is the case false if not
        """
        return index < len(self.proto.resourcemap.res) and self.proto.resourcemap.res[index] != 0
        

    def get_elt_string(self, index: int) -> str:
        """Get string element decoded at index

        Args:
            index (int): index of target element

        Returns:
            str: the string element decoded
        """
        if index == 4294967295:
            return ""
        if (
            self.is_system_resources_string(index)
            ):  # TODO check if this value could be equal to zero in Android implementation
            try:
                return public.SYSTEM_RESOURCES["attributes"]["inverse"][
                        self.proto.resourcemap.res[index]
                        ]
            except KeyError as e:
                logging.error(f"SYSTEM_RESOURCES has no key: {e}")
                data = self.stringblocks.proto.stringblocks[index].data
                if self.proto.stringblocks.hnd.flag & axml_pb2.UTF8_FLAG == axml_pb2.UTF8_FLAG:
                    fake_name = data.decode("utf-8")
                else:
                    fake_name = data.decode("utf-16")
                return f"UNKNOWN_SYSTEM_ATTRIBUTE_{hex(self.proto.resourcemap.res[index])}_{fake_name}"

        data = self.stringblocks.proto.stringblocks[index].data
        if self.proto.stringblocks.hnd.flag & axml_pb2.UTF8_FLAG == axml_pb2.UTF8_FLAG:
            return data.decode("utf-8")
        return data.decode("utf-16")

    def to_xml(self) -> "etree.Element":
        """Convert AXML to XML to manipulate XML Tree

        Returns:
            etree.Element: XML element of all AXML files
        """
        root = None
        cur = root
        nsmap = {"android": "http://schemas.android.com/apk/res/android"}

        for xmlelt in self.proto.resourcexml.elts:
            if xmlelt.HasField("start_elt"):
                ns = self.get_elt_string(xmlelt.start_elt.namespaceURI)
                # If namespace not correctly set enforce it
                if self.is_system_resources_string(xmlelt.start_elt.name) and ns != "android":
                    ns = nsmap["android"]
                name = self.get_elt_string(xmlelt.start_elt.name)
                if ns == "":
                    node = etree.Element(f"{name}")
                else:
                    node = etree.Element("{" + ns + "}" + name)
                for att in xmlelt.start_elt.attributes:
                    ns_att = self.get_elt_string(att.namespaceURI)
                    # If namespace not correctly set enforce it
                    if self.is_system_resources_string(att.name) and ns_att != "android":
                        ns_att = nsmap["android"]
                    name_att = self.get_elt_string(att.name)
                    v = str(att.value)
                    t = TypedValue.get_type(att.type)
                    if t == TypedValue.TYPE_STRING:
                        v = self.get_elt_string(att.value)
                    else:
                        v_tmp = TypedValue.coerce_to_string(t, att.data)
                        if v_tmp is not None:
                            v = v_tmp
                    if ns_att == "":
                        node.attrib[f"{name_att}"] = v
                    else:
                        try:
                            node.attrib["{" + ns_att + "}" + name_att] = v
                        except ValueError as e:
                            logging.error(e)
                            node.attrib["{" + ns_att + "}" + name_att] = "PYAXML_ERROR_INVALID_CHARS"
                if root is None:
                    node = etree.Element(node.tag, attrib=node.attrib, nsmap=nsmap)
                    root = node
                    cur = node
                else:
                    cur.append(node)
                    cur = node
            elif xmlelt.HasField("end_elt"):
                if cur is None:
                    raise RecursionError("{cur} has no parent")
                cur = cur.getparent()
                # xmlelt.end_elt
            elif xmlelt.HasField("start_ns"):
                pass
            elif xmlelt.HasField("end_ns"):
                pass
            elif xmlelt.HasField("cdata"):
                value = self.get_elt_string(xmlelt.cdata.name)
                if value is None:
                    raise ValueError("{xmlelt.cdata.name} has no value")
                if cur is None:
                    raise ValueError("No cur")
                cur.text = value
        return root


class AXMLGuess:
    """Guess the AXML type file (AXML or ARSC) and parse it"""

    @staticmethod
    def from_axml(buff: bytes) -> Union["AXML", "ARSC", None]:
        """Guess the AXML type file (AXML or ARSC) and parse it

        Returns:
            Union["AXML", "ARSC"]: the Object AXML file
        """
        if len(buff) < 8:
            logging.error("file too small")
            return None
        hnd, _ = AXMLHeader.from_axml(buff[:8])
        if hnd.proto.type == axml_pb2.RES_XML_TYPE:
            return AXML.from_axml(buff)
        if hnd.proto.type == axml_pb2.RES_TABLE_TYPE:
            return ARSC.from_axml(buff)
        if hnd.proto.type & 0x00FF == 0x003C:
            logging.warning("You probably parse an xml file")
            root = etree.fromstring(buff)
            ret = AXML()
            ret.from_xml(root)
            return ret
        logging.error("file type not found")
        return None
