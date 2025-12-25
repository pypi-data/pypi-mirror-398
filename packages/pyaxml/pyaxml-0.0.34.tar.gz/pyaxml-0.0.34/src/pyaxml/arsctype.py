from struct import pack, unpack
import sys

try:
    from pyaxml.proto import axml_pb2
    from pyaxml.header import TypedValue, AXML_HEADER_SIZE
    from pyaxml.arsctableconfig import ARSCResTableConfig
except ImportError:
    print("proto is not build")
    sys.exit(1)


class ARSCResTypeType:
    """ARSCResTypeType"""

    def __init__(self, proto: axml_pb2.ARSCResTypeType = None):
        """ARSCResTypeType initialize

        Args:
            proto (axml_pb2.ARSCResTypeType, optional): _description_. Defaults to None.
        """
        if proto:
            self.proto = proto
        else:
            self.proto = axml_pb2.ARSCResTypeType()

    @property
    def get_proto(self) -> axml_pb2.ARSCResTypeType:
        """protobuf of ARSCResTypeType

        Returns:
            axml_pb2.ARSCResTypeType: protobuf of ARSCResTypeType
        """
        return self.proto

    def compute(self, hnd: axml_pb2.AXMLHeader, recursive=True):
        """Compute all fields to have all ARSCResTypeType elements

        Args:
            hnd (axml_pb2.AXMLHeader): header of ARSCResTypeType element
            recursive (bool, optional): need to compute all field recursively. Defaults to True.
        """
        cur = 0
        index_cur = 0
        for i in self.proto.tables:
            if not i.present:
                continue
            if len(self.proto.entries) <= index_cur:
                self.proto.entries.append(cur)
            else:
                while self.proto.entries[index_cur] == 0xFFFFFFFF:
                    index_cur += 1
                self.proto.entries[index_cur] = cur
            index_cur += 1
            cur += len(ARSCResTableEntry(proto=i).pack())
        self.proto.entryCount = len(self.proto.entries)
        self.proto.entryStart = hnd.header_size + 4 * self.proto.entryCount

    def pack(self) -> bytes:
        """pack the AXML element

        Returns:
            bytes: return the AXML element packed
        """
        head = pack(
            "<BBHII",
            self.proto.id,
            self.proto.flags,
            self.proto.reserved,
            self.proto.entryCount,
            self.proto.entryStart,
        )
        config = ARSCResTableConfig(proto=self.proto.config).pack()
        data = b""
        for i in self.proto.entries:
            data += pack("<I", i)
        for i in self.proto.tables:
            if not i.present:
                continue
            data += ARSCResTableEntry(proto=i).pack()
        return head + config + data

    @staticmethod
    def from_axml(buff: bytes, proto=None):
        """Convert ARSCResTypeType buffer to ARSCResTypeType object

        Args:
            buff (bytes): buffer contain ARSCResTypeType object

        Returns:
            tuple[pyaxml.ARSCResTypeType, bytes]: return ARSCResTypeType element and buffer offset at the end of the reading
        """
        res_table_typetype = ARSCResTypeType()
        if proto:
            res_table_typetype.proto = proto
        (
            res_table_typetype.proto.id,
            res_table_typetype.proto.flags,
            res_table_typetype.proto.reserved,
            res_table_typetype.proto.entryCount,
            res_table_typetype.proto.entryStart,
        ) = unpack("<BBHII", buff[:12])
        buff = buff[12:]
        _, buff = ARSCResTableConfig.from_axml(buff, proto=res_table_typetype.proto.config)
        for i in range(res_table_typetype.proto.entryCount):
            if len(buff) < 4:
                raise ValueError(
                    f"ARSCResTypeType: entryCount: {res_table_typetype.proto.entryCount} is to big for buffer of size: {len(buff)}"
                )
            res_table_typetype.proto.entries.append(unpack("<I", buff[:4])[0])
            buff = buff[4:]

        entrie_cur = buff
        for i in res_table_typetype.proto.entries:
            if i == 0xFFFFFFFF:
                mock = ARSCResTableEntry()
                mock.proto.present = False
                res_table_typetype.proto.tables.append(mock.proto)
                continue
            table, buff = ARSCResTableEntry.from_axml(entrie_cur[i:])
            res_table_typetype.proto.tables.append(table.proto)
        return res_table_typetype, buff

    @staticmethod
    def create_element(id_: int) -> "ARSCResTypeType":
        """create element ARSCResTypeType

        Args:
            id_ (int): id

        Returns:
            ARSCResTypeType: the ARSCResTypeType created
        """
        typetype = ARSCResTypeType()
        typetype.proto.id = id_
        typetype.proto.flags = 0
        typetype.proto.reserved = 0
        typetype.proto.entryCount = 0
        typetype.proto.config.CopyFrom(ARSCResTableConfig().proto)
        typetype.proto.entryStart = AXML_HEADER_SIZE + 64 + 12
        return typetype


class ARSCResTableEntry:
    """ARSCResTableEntry"""

    # If set, this is a complex entry, holding a set of name/value
    # mappings.  It is followed by an array of ResTable_map structures.
    FLAG_COMPLEX = 1

    # If set, this resource has been declared public, so libraries
    # are allowed to reference it.
    FLAG_PUBLIC = 2

    # If set, this is a weak resource and may be overriden by strong
    # resources of the same name/type. This is only useful during
    # linking with other resource tables.
    FLAG_WEAK = 4

    def __init__(self, proto: axml_pb2.ARSCResTableEntry = None):
        """_summary_

        Args:
            proto (axml_pb2.ARSCResTableEntry, optional): _description_. Defaults to None.
        """
        if proto:
            self.proto = proto
        else:
            self.proto = axml_pb2.ARSCResTableEntry()
            self.proto.present = True

    @property
    def get_proto(self):
        """_summary_

        Returns:
            _type_: _description_
        """
        return self.proto

    def compute(self):
        """Compute all fields to have all ARSCResTableEntry elements"""

    def pack(self) -> bytes:
        """pack the AXML element

        Returns:
            bytes: return the AXML element packed
        """
        data = pack("<HHI", self.proto.size, self.proto.flags, self.proto.index)
        if self.is_complex():
            data += ARSCComplex(proto=self.proto.item).pack()
        else:
            data += ARSCResStringPoolRef(proto=self.proto.key).pack()

        return data

    def is_public(self) -> bool:
        """check if element is public

        Returns:
            bool: True if element is public
        """
        return (self.proto.flags & self.FLAG_PUBLIC) != 0

    def is_complex(self) -> bool:
        """check if element is complex

        Returns:
            bool: True if element is complex
        """
        return (self.proto.flags & self.FLAG_COMPLEX) != 0

    def is_weak(self) -> bool:
        """check if element is weak

        Returns:
            bool: True if element is weak
        """
        return (self.proto.flags & self.FLAG_WEAK) != 0

    @staticmethod
    def create_element(index_name: int, data: int):
        """Create a new ARSCResTableEntry element

        Args:
            index_name (int): The index element
            data (int): index of data element

        Returns:
            pyaxml.ARSCResTableEntry: _description_
        """
        spec = ARSCResTableEntry()
        spec.proto.size = 8
        spec.proto.index = index_name
        spec.proto.key.size = 8
        spec.proto.key.data_type = 3
        spec.proto.key.data = data
        return spec

    @staticmethod
    def from_axml(buff: bytes, proto=None):
        """Convert ARSCResTableEntry buffer to ARSCResTableEntry object

        Args:
            buff (bytes): buffer contain ARSCResTableEntry object

        Returns:
            tuple[pyaxml.ARSCResTableEntry, bytes]: return ARSCResTableEntry element and buffer offset at the end of the reading
        """
        table = ARSCResTableEntry()
        if proto:
            table.proto = proto
        table.proto.size, table.proto.flags, table.proto.index = unpack("<HHI", buff[:8])
        buff = buff[8:]
        if table.is_complex():
            _, buff = ARSCComplex.from_axml(buff, proto=table.proto.item)
        else:
            # If FLAG_COMPLEX is not set, a Res_value structure will follow
            _, buff = ARSCResStringPoolRef.from_axml(buff, proto=table.proto.key)
        # table.proto.input = buff[8:]
        return table, buff


class ARSCComplex:
    """ARSCComplex"""

    def __init__(self, proto: axml_pb2.ARSCComplex = None):
        """Initialize ARSCComplex element

        Args:
            proto (axml_pb2.ARSCComplex, optional): _description_. Defaults to None.
        """
        if proto:
            self.proto = proto
        else:
            self.proto = axml_pb2.ARSCComplex()

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
        data = pack("<II", self.proto.id_parent, self.proto.count)
        for item in self.proto.items:
            data += pack("<I", item.id)
            data += ARSCResStringPoolRef(proto=item.data).pack()
        return data

    @staticmethod
    def from_axml(buff: bytes, proto=None) -> tuple["ARSCComplex", bytes]:
        """Convert ARSCComplex buffer to ARSCComplex object

        Args:
            buff (bytes): buffer contain ARSCComplex object

        Returns:
            tuple[pyaxml.ARSCComplex, bytes]: return ARSCComplex element and buffer offset at the end of the reading
        """
        complexe = ARSCComplex()
        if proto:
            complexe.proto = proto

        complexe.proto.id_parent, complexe.proto.count = unpack("<II", buff[:8])
        buff = buff[8:]
        # Parse self.count number of `ResTable_map`
        # these are structs of ResTable_ref and Res_value
        # ResTable_ref is a uint32_t.
        for _ in range(0, complexe.proto.count):
            item = axml_pb2.ItemComplex()
            if len(buff) < 4:
                raise ValueError(
                    f"ARSCComplex is to big {complexe.proto.count} is number of complex for buffer {len(buff)}"
                )
            item.id = unpack("<I", buff[:4])[0]
            buff = buff[4:]
            _, buff = ARSCResStringPoolRef.from_axml(buff, proto=item.data)
            complexe.proto.items.append(item)

        return complexe, buff


class ARSCResTypeSpec:
    """ARSCResTypeSpec"""

    def __init__(self, proto: axml_pb2.ARSCResTypeSpec = None):
        """_summary_

        Args:
            proto (axml_pb2.ARSCResTypeSpec, optional): _description_. Defaults to None.
        """
        if proto:
            self.proto = proto
        else:
            self.proto = axml_pb2.ARSCResTypeSpec()

    @property
    def get_proto(self):
        """_summary_

        Returns:
            _type_: _description_
        """
        return self.proto

    def compute(self, hnd: axml_pb2.AXMLHeader):
        """Compute all fields to have all AXML elements"""
        self.proto.entryCount = len(self.proto.entries)

    def pack(self) -> bytes:
        """pack the AXML element

        Returns:
            bytes: return the AXML element packed
        """
        data = pack(
            "<BBHI",
            self.proto.id,
            self.proto.res0,
            self.proto.res1,
            self.proto.entryCount,
        )
        for entry in self.proto.entries:
            data += pack("<I", entry)
        return data

    @staticmethod
    def from_axml(buff: bytes, proto=None):
        """Convert ARSCResTypeSpec buffer to ARSCResTypeSpec object

        Args:
            buff (bytes): buffer contain ARSCResTypeSpec object

        Returns:
            tuple[pyaxml.ARSCResTypeSpec, bytes]: return ARSCResTypeSpec element and buffer offset at the end of the reading
        """
        res_table_typespec = ARSCResTypeSpec()
        if proto:
            res_table_typespec.proto = proto
        (
            res_table_typespec.proto.id,
            res_table_typespec.proto.res0,
            res_table_typespec.proto.res1,
            res_table_typespec.proto.entryCount,
        ) = unpack("<BBHI", buff[:8])
        buff = buff[8:]
        for _ in range(res_table_typespec.proto.entryCount):
            res_table_typespec.proto.entries.append(unpack("<I", buff[:4])[0])
            buff = buff[4:]

        return res_table_typespec, buff


class ARSCResStringPoolRef:
    """ARSCResStringPoolRef"""

    def __init__(self, proto: axml_pb2.ARSCResStringPoolRef = None):
        """_summary_

        Args:
            proto (axml_pb2.ARSCResStringPoolRef, optional): _description_. Defaults to None.
        """
        if proto:
            self.proto = proto
        else:
            self.proto = axml_pb2.ARSCResStringPoolRef()

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
        data = pack(
            "<HBBI",
            self.proto.size,
            self.proto.res0,
            self.proto.data_type,
            self.proto.data,
        )
        return data

    @staticmethod
    def from_axml(buff: bytes, proto=None):
        """Convert ARSCResStringPoolRef buffer to ARSCResStringPoolRef object

        Args:
            buff (bytes): buffer contain ARSCResStringPoolRef object

        Returns:
            tuple[pyaxml.ARSCResStringPoolRef, bytes]: return ARSCResStringPoolRef element and buffer offset at the end of the reading
        """
        ref = ARSCResStringPoolRef()
        if proto:
            ref.proto = proto

        ref.proto.size, ref.proto.res0, ref.proto.data_type, ref.proto.data = unpack(
            "<HBBI", buff[:8]
        )
        buff = buff[8:]
        return ref, buff

    def is_reference(self) -> bool:
        """
        Returns True if the Res_value is actually a reference to another resource
        """
        return self.proto.data_type == TypedValue.TYPE_REFERENCE
