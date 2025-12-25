import sys
from struct import pack, unpack
import logging
from typing import Union

try:
    from pyaxml.proto import axml_pb2
except ImportError:
    print("proto is not build")
    sys.exit(1)
from pyaxml.stringblocks import AXMLHeader
from pyaxml.arsctype import ARSCResStringPoolRef


##############################################################################
#
#                              XML ELEMENTS
#
##############################################################################


class AXMLHeaderResXml(AXMLHeader):
    """AXMLHeaderResXml class to build an header of RES_XML"""

    def __init__(self, type_=0, size=0, proto: axml_pb2.AXMLHeader = None):
        """Initialize header of Res_XML

        Args:
            type (int, optional): define the type. Defaults to 0.
            size (int, optional): define the size of whole element. Defaults to 0.
            proto (axml_pb2.AXMLHeader, optional): define RES_XML header by a protobuff. Defaults to None.
        """
        if proto is None:
            super().__init__(type_, size + 8, proto)
            self.proto.header_size = 16
        else:
            self.proto = proto


class AXMLHeaderStartElement(AXMLHeaderResXml):
    """AXMLHeaderStartElement class to build an header of Start element"""

    def __init__(self, size: int):
        """initialize START_ELEMENT element

        Args:
            size (int): size of START_ELEMENT and its header
        """
        super().__init__(axml_pb2.RES_XML_START_ELEMENT_TYPE, size)


class AXMLHeaderEndElement(AXMLHeaderResXml):
    """AXMLHeaderEndElement class to build an header of End element"""

    def __init__(self, size: int):
        """initialize END_ELEMENT element

        Args:
            size (int): size of END_ELEMENT and its header
        """
        super().__init__(axml_pb2.RES_XML_END_ELEMENT_TYPE, size)


class AXMLHeaderStartNamespace(AXMLHeaderResXml):
    """AXMLHeaderStartNamespace class to build an header of Start namespace"""

    def __init__(self, size: int):
        """initialize START_NAMESPACE element

        Args:
            size (int): size of START_NAMESPACE and its header
        """
        super().__init__(axml_pb2.RES_XML_START_NAMESPACE_TYPE, size)


class AXMLHeaderEndNamespace(AXMLHeaderResXml):
    """AXMLHeaderEndNamespace class to build an header of End namespace"""

    def __init__(self, size: int):
        """initialize END_NAMESPACE element

        Args:
            size (int): size of END_NAMESPACE and its header
        """
        super().__init__(axml_pb2.RES_XML_END_NAMESPACE_TYPE, size)


class ClassicalResXml:
    """RES_XML class to build RES_XML element"""

    proto: axml_pb2.ResXML = None

    def __init__(
        self,
        linenumber: int = 0,
        comment: int = 0xFFFFFFFF,
        proto: axml_pb2.ResXML = None,
    ):
        """initialize RES_XML element

        Args:
            lineNumber (int, optional): _description_. Defaults to 0.
            Comment (int, optional): _description_. Defaults to 0xffffffff.
            proto (axml_pb2.ResXML, optional): define RES_XML by a protobuff. Defaults to None.
        """
        if proto is None:
            self.proto.generic.lineNumber = linenumber
            self.proto.generic.Comment = comment
        else:
            self.proto.generic.CopyFrom(proto)

    @property
    def content(self) -> bytes:
        """get content of classical res XML

        Returns:
            bytes: content packed
        """
        return pack("<LL", self.proto.generic.lineNumber, self.proto.generic.Comment)

    def compute(self):
        """Compute all fields to have all RES_XML elements"""

    def pack(self) -> bytes:
        """pack the RES_XML element

        Returns:
            bytes: return the RES_XML element packed
        """
        return self.content

    @staticmethod
    def from_axml(buff: bytes, class_xml=None):
        """Convert ClassicalResXml buffer to ClassicalResXml object

        Args:
            buff (bytes): buffer contain ClassicalResXml object
            class_xml (pyaxml.ClassicalResXml): _description_

        Returns:
            tuple[pyaxml.ClassicalResXml, bytes]: return ClassicalResXml element and buffer offset at the end of the reading
        """
        if class_xml is None:
            raise ValueError("class_xml argument not set")
        class_xml.proto.generic.lineNumber, class_xml.proto.generic.Comment = unpack(
            "<LL", buff[:8]
        )
        return class_xml, buff[8:]


class ResXmlStartElement(ClassicalResXml):
    """ResXmlStartElement"""

    def __init__(
        self,
        namespaceuri: int = 0xFFFFFFFF,
        name: int = 0xFFFFFFFF,
        attributes: Union[list, None] = None,
        styleAttribute: int = 0,
        classAttribute: int = 0,
        lineNumber: int = 0,
        Comment: int = 0xFFFFFFFF,
        at_start=0x14,
        at_size=0x14,
        proto: axml_pb2.ResXMLStartElement = None,
    ):
        """_summary_

        Args:
            namespaceuri (int, optional): _description_. Defaults to 0xffffffff.
            name (int, optional): _description_. Defaults to 0xffffffff.
            attributes (list, optional): _description_. Defaults to [].
            styleAttribute (int, optional): _description_. Defaults to -1.
            classAttribute (int, optional): _description_. Defaults to -1.
            lineNumber (int, optional): _description_. Defaults to 0.
            Comment (int, optional): _description_. Defaults to 0xffffffff.
            proto (axml_pb2.ResXMLStartElement, optional): _description_. Defaults to None.
        """
        if attributes is None:
            attributes = []
        if proto is None:
            self.proto = axml_pb2.ResXMLStartElement()
            super().__init__(lineNumber, Comment)
            self.proto.namespaceURI = namespaceuri
            self.proto.name = name
            self.proto.attributes.extend(attributes)
            self.proto.styleAttribute = styleAttribute
            self.proto.classAttribute = classAttribute
            self.proto.at_start = at_start
            self.proto.at_size = at_size
        else:
            self.proto = proto
            super().__init__(proto=proto.generic)

    def compute(self):
        """Compute all fields to have all ResXmlStartElement elements"""
        self.proto.len_attributes = len(self.proto.attributes)
        super().compute()

    @property
    def content(self) -> bytes:
        """_summary_

        Returns:
            bytes: _description_
        """
        return (
            super().content
            + pack(
                "<LLhhLhh",
                self.proto.namespaceURI,
                self.proto.name,
                self.proto.at_start,
                self.proto.at_size,
                self.proto.len_attributes,
                self.proto.styleAttribute,
                self.proto.classAttribute,
            )
            + b"".join(Attribute(proto=a).pack() for a in self.proto.attributes)
        )

    @staticmethod
    def from_axml(buff: bytes, class_xml=None, proto=None):
        """Convert ResXmlStartElement buffer to ResXmlStartElement object

        Args:
            buff (bytes): buffer contain ResXmlStartElement object

        Returns:
            tuple[pyaxml.ResXmlStartElement, bytes]: return ResXmlStartElement element and buffer offset at the end of the reading
        """
        if class_xml is None:
            class_xml = ResXmlStartElement()
        if proto:
            class_xml.proto = proto
        class_xml, buff = ClassicalResXml.from_axml(buff, class_xml=class_xml)

        (
            class_xml.proto.namespaceURI,
            class_xml.proto.name,
            class_xml.proto.at_start,
            class_xml.proto.at_size,
            class_xml.proto.len_attributes,
            class_xml.proto.styleAttribute,
            class_xml.proto.classAttribute,
        ) = unpack("<LLhhLhh", buff[:20])
        buff = buff[20:]
        # TODO len_attributes contain id_attribute and count attribute
        for _ in range(class_xml.proto.len_attributes & 0xFFFF):
            padding = class_xml.proto.at_size - 0x14
            attr, buff = Attribute.from_axml(buff, padding)
            class_xml.proto.attributes.append(attr.proto)

        return class_xml, buff


class ResXmlEndElement(ClassicalResXml):
    """ResXmlEndElement"""

    def __init__(
        self,
        namespaceURI: int = 0xFFFFFFFF,
        name: int = 0xFFFFFFFF,
        lineNumber: int = 0,
        Comment: int = 0xFFFFFFFF,
        proto: axml_pb2.ResXMLEndElement = None,
    ):
        """_summary_

        Args:
            namespaceURI (int, optional): _description_. Defaults to 0xffffffff.
            name (int, optional): _description_. Defaults to 0xffffffff.
            lineNumber (int, optional): _description_. Defaults to 0.
            Comment (int, optional): _description_. Defaults to 0xffffffff.
            proto (axml_pb2.ResXMLEndElement, optional): _description_. Defaults to None.
        """
        if proto is None:
            self.proto = axml_pb2.ResXMLEndElement()
            super().__init__(lineNumber, Comment)
            self.proto.namespaceURI = namespaceURI
            self.proto.name = name
        else:
            self.proto = proto
            super().__init__(proto=proto.generic)

    @property
    def content(self) -> bytes:
        """_summary_

        Returns:
            bytes: _description_
        """
        return super().content + pack("<LL", self.proto.namespaceURI, self.proto.name)

    @staticmethod
    def from_axml(buff, class_xml=None, proto=None):
        """Convert ResXmlEndElement buffer to ResXmlEndElement object

        Args:
            buff (bytes): buffer contain ResXmlEndElement object

        Returns:
            tuple[pyaxml.ResXmlEndElement, bytes]: return ResXmlEndElement element and buffer offset at the end of the reading
        """
        if class_xml is None:
            class_xml = ResXmlEndElement()
        if proto:
            class_xml.proto = proto
        class_xml, buff = ClassicalResXml.from_axml(buff, class_xml=class_xml)
        class_xml.proto.namespaceURI, class_xml.proto.name = unpack("<LL", buff[:8])
        return class_xml, buff[8:]


class ResXmlStartNamespace(ClassicalResXml):
    """ResXmlStartNamespace"""

    def __init__(
        self,
        prefix: int = 0xFFFFFFFF,
        uri: int = 0xFFFFFFFF,
        lineNumber: int = 0,
        Comment: int = 0xFFFFFFFF,
        proto: axml_pb2.ResXMLStartNamespace = None,
    ):
        """_summary_

        Args:
            prefix (int, optional): _description_. Defaults to 0xffffffff.
            uri (int, optional): _description_. Defaults to 0xffffffff.
            lineNumber (int, optional): _description_. Defaults to 0.
            Comment (int, optional): _description_. Defaults to 0xffffffff.
            proto (axml_pb2.ResXMLStartNamespace, optional): _description_. Defaults to None.
        """
        if proto is None:
            self.proto = axml_pb2.ResXMLStartNamespace()
            super().__init__(lineNumber, Comment)
            self.proto.prefix = prefix
            self.proto.uri = uri
        else:
            self.proto = proto
            super().__init__(proto=proto.generic)

    @property
    def content(self) -> bytes:
        """_summary_

        Returns:
            bytes: _description_
        """
        return super().content + pack("<LL", self.proto.prefix, self.proto.uri)

    @staticmethod
    def from_axml(buff: bytes, class_xml=None, proto=None):
        """Convert ResXmlStartNamespace buffer to ResXmlStartNamespace object

        Args:
            buff (bytes): buffer contain ResXmlStartNamespace object

        Returns:
            tuple[pyaxml.ResXmlStartNamespace, bytes]: return ResXmlStartNamespace element and buffer offset at the end of the reading
        """
        if class_xml is None:
            class_xml = ResXmlStartNamespace()
        if proto:
            class_xml.proto = proto
        class_xml, buff = ClassicalResXml.from_axml(buff, class_xml=class_xml)
        class_xml.proto.prefix, class_xml.proto.uri = unpack("<LL", buff[:8])
        return class_xml, buff[8:]


class ResXmlEndNamespace(ClassicalResXml):
    """ResXmlEndNamespace"""

    def __init__(
        self,
        prefix: int = 0xFFFFFFFF,
        uri: int = 0xFFFFFFFF,
        lineNumber: int = 0,
        Comment: int = 0xFFFFFFFF,
        proto: axml_pb2.ResXMLEndNamespace = None,
    ):
        """_summary_

        Args:
            prefix (int, optional): _description_. Defaults to 0xffffffff.
            uri (int, optional): _description_. Defaults to 0xffffffff.
            lineNumber (int, optional): _description_. Defaults to 0.
            Comment (int, optional): _description_. Defaults to 0xffffffff.
            proto (axml_pb2.ResXMLEndNamespace, optional): _description_. Defaults to None.
        """
        if proto is None:
            self.proto = axml_pb2.ResXMLEndNamespace()
            super().__init__(lineNumber, Comment)
            self.proto.prefix = prefix
            self.proto.uri = uri
        else:
            self.proto = proto
            super().__init__(proto=proto.generic)

    @property
    def content(self):
        """_summary_

        Returns:
            _type_: _description_
        """
        return super().content + pack("<LL", self.proto.prefix, self.proto.uri)

    @staticmethod
    def from_axml(buff: bytes, class_xml=None, proto=None):
        """Convert ResXmlEndNamespace buffer to ResXmlEndNamespace object

        Args:
            buff (bytes): buffer contain ResXmlEndNamespace object

        Returns:
            tuple[pyaxml.ResXmlEndNamespace, bytes]: return ResXmlEndNamespace element and buffer offset at the end of the reading
        """
        if class_xml is None:
            class_xml = ResXmlEndNamespace()
        if proto:
            class_xml.proto = proto
        class_xml, buff = ClassicalResXml.from_axml(buff, class_xml=class_xml)
        class_xml.proto.prefix, class_xml.proto.uri = unpack("<LL", buff[:8])
        return class_xml, buff[8:]


class Attribute:
    """Attribute"""

    def __init__(
        self,
        namespaceuri: int = 0xFFFFFFFF,
        name: int = 0xFFFFFFFF,
        value: int = 0xFFFFFFFF,
        type_: int = 0xFFFFFFFF,
        data: int = 0xFFFFFFFF,
        proto: axml_pb2.Attribute = None,
    ):
        """Initialize an Attribute element from protobuff or parameters

        Args:
            namespaceURI (int, optional): namespace of Attribute. Defaults to 0xffffffff.
            name (int, optional): name of Attribute. Defaults to 0xffffffff.
            value (int, optional): value of the attribute. Defaults to 0xffffffff.
            type_ (int, optional): type of attribute. Defaults to 0xffffffff.
            data (int, optional): data of the parameter in function of the type it could be store in value or data. Defaults to 0xffffffff.
            proto (axml_pb2.Attribute, optional): protobuff of Attribute content. Defaults to None.
        """
        if proto is None:
            self.proto = axml_pb2.Attribute()
            self.proto.namespaceURI = namespaceuri
            self.proto.name = name
            self.proto.value = value
            self.proto.type = type_
            self.proto.data = data
        else:
            self.proto = proto

    def pack(self) -> bytes:
        """pack the Attribute element

        Returns:
            bytes: return the Attribute element packed
        """
        return (
            pack(
                "<LLLLL",
                self.proto.namespaceURI,
                self.proto.name,
                self.proto.value,
                self.proto.type,
                self.proto.data,
            )
            + self.proto.padding
        )

    @staticmethod
    def from_axml(buff, padding=0, proto=None):
        """Convert Attribute buffer to Attribute object

        Args:
            buff (bytes): buffer contain Attribute object

        Returns:
            tuple[pyaxml.Attribute, bytes]: return Attribute element and buffer offset at the end of the reading
        """
        attr = Attribute()
        if proto:
            attr.proto = proto
        (
            attr.proto.namespaceURI,
            attr.proto.name,
            attr.proto.value,
            attr.proto.type,
            attr.proto.data,
        ) = unpack("<LLLLL", buff[:20])
        attr.proto.padding = buff[20 : 20 + padding]
        return attr, buff[20 + padding :]


class ResXmlCDATA(ClassicalResXml):
    """ResXmlCDATA"""

    def __init__(
        self,
        proto: axml_pb2.ResXMLCDATA = None,
        lineNumber: int = 0,
        Comment: int = 0xFFFFFFFF,
    ):
        """Initialize an ResXmlCDATA element from protobuff or parameters

        Args:
            proto (axml_pb2.ResXMLCDATA, optional): _description_. Defaults to None.
        """
        if proto is None:
            self.proto = axml_pb2.ResXMLCDATA()
            super().__init__(lineNumber, Comment)
        else:
            self.proto = proto

    @property
    def content(self):
        """_summary_

        Returns:
            _type_: _description_
        """
        return (
            super().content
            + pack("<L", self.proto.name)
            + ARSCResStringPoolRef(proto=self.proto.res).pack()
        )

    @staticmethod
    def from_axml(buff, class_xml=None, proto=None):
        """Convert ResXmlCDATA buffer to ResXmlCDATA object

        Args:
            buff (bytes): buffer contain ResXmlCDATA object

        Returns:
            tuple[pyaxml.ResXmlCDATA, bytes]: return ResXmlCDATA element and buffer offset at the end of the reading
        """
        class_xml = ResXmlCDATA()
        if proto:
            class_xml.proto = proto
        class_xml, buff = ClassicalResXml.from_axml(buff, class_xml=class_xml)
        class_xml.proto.name = unpack("<L", buff[:4])[0]
        _, buff = ARSCResStringPoolRef.from_axml(buff[4:], proto=class_xml.proto.res)
        return class_xml, buff


class ResourceXML:
    """ResourceXML"""

    def __init__(self, proto: axml_pb2.ResourceXML = None) -> None:
        """Initialize ResourceXML

        Args:
            proto (axml_pb2.ResourceXML, optional): protobuff of ResourceXML content. Defaults to None.
        """
        if proto:
            self.proto = proto
        else:
            self.proto = axml_pb2.ResourceXML()

    def pack(self) -> bytes:
        """pack the ResourceXML element

        Returns:
            bytes: return the ResourceXML element packed
        """
        buf = b""
        for elt in self.proto.elts:
            header = AXMLHeader(proto=elt.header).pack()
            if elt.HasField("start_elt"):
                buf += header + ResXmlStartElement(proto=elt.start_elt).pack()
            elif elt.HasField("end_elt"):
                buf += header + ResXmlEndElement(proto=elt.end_elt).pack()
            elif elt.HasField("start_ns"):
                buf += header + ResXmlStartNamespace(proto=elt.start_ns).pack()
            elif elt.HasField("end_ns"):
                buf += header + ResXmlEndNamespace(proto=elt.end_ns).pack()
            elif elt.HasField("cdata"):
                buf += header + ResXmlCDATA(proto=elt.cdata).pack()
        return buf

    @staticmethod
    def from_axml(buff: bytes, proto=None):
        """Convert ResourceXML buffer to ResourceXML object

        Args:
            buff (bytes): buffer contain ResourceXML object

        Returns:
            tuple[pyaxml.ResourceXML, bytes]: return ResourceXML element and buffer offset at the end of the reading
        """
        xml = ResourceXML()
        if proto:
            xml.proto = proto
        while len(buff) > 0:
            elt = axml_pb2.XMLElement()
            hnd, buff = AXMLHeader.from_axml(buff, proto=elt.header)
            if hnd.proto.type == axml_pb2.RES_XML_START_ELEMENT_TYPE:
                _, buff2 = ResXmlStartElement.from_axml(buff, proto=elt.start_elt)
            elif hnd.proto.type == axml_pb2.RES_XML_END_ELEMENT_TYPE:
                _, buff2 = ResXmlEndElement.from_axml(buff, proto=elt.end_elt)
            elif hnd.proto.type == axml_pb2.RES_XML_START_NAMESPACE_TYPE:
                _, buff2 = ResXmlStartNamespace.from_axml(buff, proto=elt.start_ns)
            elif hnd.proto.type == axml_pb2.RES_XML_END_NAMESPACE_TYPE:
                _, buff2 = ResXmlEndNamespace.from_axml(buff, proto=elt.end_ns)
            elif hnd.proto.type == axml_pb2.RES_XML_CDATA_TYPE:
                _, buff2 = ResXmlCDATA.from_axml(buff, proto=elt.cdata)
            else:
                raise ValueError("RES_XML element header incorrect type")
            buff = buff[hnd.proto.size - hnd.proto.header_size + 8 :]
            if buff != buff2:
                logging.warning(
                    "Size of resourceXML element incorrect from type %s the size difference is %s",
                    hnd.proto.type,
                    len(buff2) - len(buff),
                )
            xml.proto.elts.append(elt)
        return xml, buff
