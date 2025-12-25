from struct import pack, unpack
import sys
from typing import Union

try:
    from pyaxml.proto import axml_pb2
except ImportError:
    print("proto is not build")
    sys.exit(1)

from pyaxml.stringblocks import StringBlocks
from pyaxml.header import AXMLHeaderRESTABLE, TypedValue, AXMLHeader, AXML_HEADER_SIZE
from pyaxml.arsctype import (
    ARSCResTableConfig,
    ARSCResTableEntry,
    ARSCResTypeSpec,
    ARSCResTypeType,
)

##############################################################################
#
#                              ARSC OBJECT
#
##############################################################################


class ARSC:
    """ARSC"""

    def __init__(self, proto: axml_pb2.ARSC = None):
        """_summary_

        Args:
            proto (axml_pb2.AXML, optional): _description_. Defaults to None.
        """
        if proto:
            self.proto = proto
        else:
            self.proto = axml_pb2.ARSC()

    @property
    def get_proto(self):
        """_summary_

        Returns:
            _type_: _description_
        """
        return self.proto

    def compute(self, recursive=True):
        """Compute all fields to have all AXML elements"""
        if recursive:
            s = StringBlocks(proto=self.proto.stringblocks)
            s.compute(update_size=True)
            self.proto.stringblocks.CopyFrom(s.proto)
            for _, restablespackage in enumerate(
                self.proto.restablespackage
            ):  # range(len(self.proto.restablespackage)):
                package = AXMLResTablePackage(proto=restablespackage)
                package.compute(recursive=recursive)
                restablespackage.CopyFrom(package.proto)

        self.proto.header_res.hnd.size = len(self.pack())
        self.proto.header_res.package_count = len(self.proto.restablespackage)

    def pack(self) -> bytes:
        """pack the AXML element

        Returns:
            bytes: return the AXML element packed
        """
        sb_pack = StringBlocks(proto=self.proto.stringblocks).pack()
        header_res = AXMLHeaderRESTABLE(proto=self.proto.header_res).pack()
        packages = b""
        for package in self.proto.restablespackage:
            packages += AXMLResTablePackage(proto=package).pack()
        return header_res + sb_pack + packages

    @staticmethod
    def from_axml(buff: bytes, proto=None):
        """read an AXML ARSC file to convert in pyaxml.ARSC object

        Args:
            buff (bytes): the string buffer to read

        Returns:
            ARSC: the ARSC object
            str: index of the reading string, if it's a valid file it should be the EOF.
        """
        arsc = ARSC()
        if proto:
            arsc.proto = proto
        header, buff = AXMLHeaderRESTABLE.from_axml(buff, proto=arsc.proto.header_res)
        _, buff = StringBlocks.from_axml(buff, proto=arsc.proto.stringblocks)
        for _ in range(header.proto.package_count):
            restablepackage, buff = AXMLResTablePackage.from_axml(buff)
            arsc.proto.restablespackage.append(restablepackage.proto)

        return arsc, buff

    @staticmethod
    def convert_id(type_id: int, id_: int) -> int:
        """convert id and type to a general id used on AXML file to refer to resources

        Args:
            type_id (int): type of value (xml, string, etc.)
            id (int): index from the list of type value

        Returns:
            int: the id built
        """
        return 0x7F000000 | (type_id & 0xFF) << 16 | type_id & 0xFF00 | id_

    @staticmethod
    def get_type_from_id(id_: int) -> int:
        """get type from id

        Args:
            id_ (int): full id

        Returns:
            int: type
        """
        return (id_ & 0xFF0000) >> 16 | id_ & 0xFF00

    @staticmethod
    def get_local_id_from_id(id_: int) -> int:
        """get local id from full id

        Args:
            id_ (int): full id

        Returns:
            int: id
        """
        return id_ & 0xFF

    def get_id_public(self, package: str, type_: str, name: str) -> Union[tuple[int, int], None]:
        """get ID public from resource

        Args:
            package (str): package name
            type_ (str): type string
            name (str): name of value

        Returns:
            tuple[int, int] | None: return the id and the stringblock index of the value
        """
        for p in self.proto.restablespackage:
            n2 = p.name.split("\x00")[0]
            if n2 == package:
                for r in p.restypes:
                    if r.hnd.type == axml_pb2.ResType.RES_TABLE_TYPE_TYPE:
                        for id_, table in enumerate(r.typetype.tables):
                            index = table.index
                            n = StringBlocks(proto=p.key_sp_string).decode_str(index)
                            t = StringBlocks(proto=p.type_sp_string).decode_str(r.typetype.id - 1)
                            if n == name and t == type_:
                                return (
                                    ARSC.convert_id(r.typetype.id, id_),
                                    table.key.data,
                                )
        return None

    def get_id(
        self, package: str, rid: int
    ) -> tuple[Union[str, None], Union[str, None], Union[int, None]]:
        """get id

        Args:
            package (str): target package
            rid (int): target rid

        Returns:
            tuple[str, str, int]: type, key and rid
        """
        for p in self.proto.restablespackage:
            n2 = p.name.split("\x00")[0]
            if n2 == package:
                for r in p.restypes:
                    if r.hnd.type != axml_pb2.ResType.RES_TABLE_TYPE_TYPE:
                        continue
                    if r.typetype.id != ARSC.get_type_from_id(rid):
                        continue
                    local_id = ARSC.get_local_id_from_id(rid)
                    if local_id >= len(r.typetype.tables):
                        continue
                    table = r.typetype.tables[local_id]
                    n = StringBlocks(proto=p.key_sp_string).decode_str(table.index)
                    t = StringBlocks(proto=p.type_sp_string).decode_str(r.typetype.id - 1)
                    return t, n, rid
        return None, None, None

    def get_resource_xml_name(
        self, r_id: int, package: Union[str, None] = None
    ) -> Union[str, None]:
        """get resource xml name

        Args:
            r_id (int): rid target
            package (Union[str, None], optional): target package. Defaults to None.

        Returns:
            str: xml name from resource
        """
        if package:
            resource, name, i_id = self.get_id(package, r_id)
            if not i_id:
                return None
            return "@{}/{}".format(resource, name)

        for p in self.get_packages():
            r, n, i_id = self.get_id(p, r_id)
            if i_id:
                # found the resource in this package
                package = p
                resource = r
                name = n
                break
        if not package:
            return None
        return "@{}:{}/{}".format(package, resource, name)

    def get_value(self, package: str, rid: int) -> str:
        """get value of resource

        Args:
            package (str): target package
            rid (int): target rid

        Raises:
            ValueError: if rid could not be decoded

        Returns:
            str: value decoded
        """
        general_st = StringBlocks(proto=self.proto.stringblocks)
        for p in self.proto.restablespackage:
            n2 = p.name.split("\x00")[0]
            if n2 == package:
                for r in p.restypes:
                    if r.hnd.type != axml_pb2.ResType.RES_TABLE_TYPE_TYPE:
                        continue
                    if r.typetype.id != ARSC.get_type_from_id(rid):
                        continue
                    local_id = ARSC.get_local_id_from_id(rid)
                    if local_id >= len(r.typetype.tables):
                        continue
                    table = r.typetype.tables[local_id]
                    if table.key.data_type == 3:
                        return general_st.decode_str(table.key.data)
        raise ValueError(f"no value could be decoded for rid: {rid}")

    def add_id_public(self, package: str, type_: str, name: str, path: str) -> Union[int, None]:
        """Add a new id in public string on ARSC resource

        Args:
            package (str): target package
            type_ (str): type of public element
            name (str): name of public element
            path (str): value of element

        Returns:
            int | None: return the id injected
        """
        for p in self.proto.restablespackage:
            n2 = p.name.split("\x00")[0]
            if n2 == package:
                s = StringBlocks(proto=self.proto.stringblocks)
                id_path = s.get(path)
                s.compute()
                self.proto.stringblocks.CopyFrom(s.proto)
                res = AXMLResTablePackage(proto=p)
                ret = res.add_id_public(type_, name, id_path)
                res.compute()
                return ret
        return None

    def list_packages(self) -> str:
        """print all package content"""
        ret = ""
        general_st = StringBlocks(proto=self.proto.stringblocks)
        for package in self.proto.restablespackage:
            # ret += f"{package.name}\n"
            for r in package.restypes:
                if r.hnd.type == axml_pb2.ResType.RES_TABLE_TYPE_TYPE:
                    for id_, table in enumerate(r.typetype.tables):
                        if not table.present:
                            continue
                        index = table.index
                        name = StringBlocks(proto=package.key_sp_string).decode_str(index)
                        type_ = StringBlocks(proto=package.type_sp_string).decode_str(
                            r.typetype.id - 1
                        )
                        identifiant = ARSC.convert_id(r.typetype.id, id_)
                        if table.key.data_type == 3:
                            data = general_st.decode_str(table.key.data)
                        else:
                            data = hex(table.key.data)
                        data_size = table.key.size
                        ret += f'<public type="{type_}" name="{name}" id="{hex(identifiant)}" data="{data}" data_size={data_size}/>\n'
        return ret

    def get_packages(self) -> list[str]:
        """get in a list all package name of the resources.

        Returns:
            list[str]: the list of all packages
        """
        packages = []
        for p in self.proto.restablespackage:
            packages.append(p.name.split("\x00")[0])
        return packages

    def get_type_configs(
        self, package_name: str, type_name: Union[str, None] = None
    ) -> "dict[str, axml_pb2.ARSCResTableConfig]":
        """get type configuration

        Args:
            package_name (str): _description_
            type_name (str, optional): _description_. Defaults to None.

        Returns:
            dict[str, axml_pb2.ARSCResTableConfig]: type configs
        """
        if package_name is None:
            package_name = self.get_packages()[0]
        result: dict[str, axml_pb2.ARSCResTableConfig] = {}

        for restype in self.proto.restablespackage[0].restypes:
            if restype.hnd.type == axml_pb2.ResType.RES_TABLE_TYPE_TYPE:
                t_name = StringBlocks(
                    proto=self.proto.restablespackage[0].type_sp_string
                ).decode_str(restype.typetype.id - 1)
                if type_name is None or t_name == type_name:
                    result[t_name].append(restype.typetype.config)

        return result

    def get_res_configs(
        self, rid: int, config: Union[str, None] = None, fallback: bool = True
    ) -> "list[tuple[ARSCResTableConfig, ARSCResTableEntry]]":
        """get ressource configuration

        Args:
            rid (int): rid value
            config (_type_, optional): config value. Defaults to None.
            fallback (bool, optional): fallback value. Defaults to True.

        Raises:
            ValueError: if rid is not set
            ValueError: if rid is not the correct type (int)

        Returns:
            list[tuple[ARSCResTableConfig, ARSCResTableEntry]]: the list of ressource configuration
        """

        if not rid:
            raise ValueError("'rid' should be set")
        if not isinstance(rid, int):
            raise ValueError("'rid' must be an int")
        res: list[tuple[ARSCResTableConfig, ARSCResTableEntry]] = []
        p = self.proto.restablespackage[0]
        for r in p.restypes:
            if r.hnd.type != axml_pb2.ResType.RES_TABLE_TYPE_TYPE:
                continue
            if r.typetype.id != ARSC.get_type_from_id(rid):
                continue
            local_id = ARSC.get_local_id_from_id(rid)
            if local_id >= len(r.typetype.tables):
                continue
            table = r.typetype.tables[local_id]
            res.append(
                (
                    ARSCResTableConfig(proto=r.typetype.config),
                    ARSCResTableEntry(proto=table),
                )
            )
        return res

    def get_resolved_res_configs(self, rid: int, config=None) -> list[tuple]:
        """
        Return a list of resolved resource IDs with their corresponding configuration.
        It has a similar return type as :meth:`get_res_configs` but also handles complex entries
        and references.
        Also instead of returning :class:`ARSCResTableEntry` in the tuple, the actual values are resolved.

        This is the preferred way of resolving resource IDs to their resources.

        :param int rid: the numerical ID of the resource
        :param ARSCTableResConfig config: the desired configuration or None to retrieve all
        :return: A list of tuples of (ARSCResTableConfig, str)
        """
        resolver = ARSC.ResourceResolver(self, config)
        return resolver.resolve(rid)

    class ResourceResolver:
        """
        Resolves resources by ID and configuration.
        This resolver deals with complex resources as well as with references.
        """

        def __init__(self, android_resources, config=None) -> None:
            """
            :param ARSCParser android_resources: A resource parser
            :param ARSCResTableConfig config: The desired configuration or None to resolve all.
            """
            self.resources = android_resources
            self.wanted_config = config

        def resolve(self, res_id: int) -> list:
            """
            the given ID into the Resource and returns a list of matching resources.

            :param int res_id: numerical ID of the resource
            :return: a list of tuples of (ARSCResTableConfig, str)
            """
            result: "list[Union[str, tuple[ARSCResTableConfig, list], None]]" = []
            self._resolve_into_result(result, res_id, self.wanted_config)
            return result

        def _resolve_into_result(
            self,
            result: "list[Union[str, tuple[ARSCResTableConfig, list], None]]",
            res_id,
            config,
        ) -> None:
            # First: Get all candidates
            configs: "list[tuple[ARSCResTableConfig, ARSCResTableEntry]]" = (
                self.resources.get_res_configs(res_id, config)
            )

            for local_config, ate in configs:
                # deconstruct them and check if more candidates are generated
                self.put_ate_value(result, ate, local_config)

        def put_ate_value(
            self,
            result: "list[Union[str, tuple[ARSCResTableConfig, list], None]]",
            ate: axml_pb2.ARSCResTableEntry,
            config: "Union[ARSCResTableConfig, None]",
        ) -> None:
            """
            Put a ResTableEntry into the list of results
            :param list result: results array
            :param ARSCResTableEntry ate:
            :param ARSCResTableConfig config:
            :return:
            """
            if ate.is_complex():
                complex_array: "list[Union[str, tuple[ARSCResTableConfig, list], None]]" = []
                result.append((config, complex_array))
                for _, item in ate.item.items:
                    self.put_item_value(complex_array, item, config, ate, complex_=True)
            else:
                self.put_item_value(result, ate.key, config, ate, complex_=False)

        def put_item_value(
            self,
            result: list[Union[str, tuple[ARSCResTableConfig, list], None]],
            item,
            config,
            parent,
            complex_: bool,
        ) -> None:
            """
            Put the tuple (ARSCResTableConfig, resolved string) into the result set

            :param list[str | None] result: the result set
            :param ARSCResStringPoolRef item:
            :param ARSCResTableConfig config:
            :param ARSCResTableEntry parent: the originating entry
            :param bool complex_: True if the originating :class:`ARSCResTableEntry` was complex
            :return:
            """
            if item.is_reference():
                res_id = item.proto.data
                if res_id:
                    # Infinite loop detection:
                    # TODO should this stay here or should be detect the loop much earlier?
                    # if res_id == parent.mResId: # mResId == AXMLResTablePackage.id
                    #    logger.warning("Infinite loop detected at resource item {}. It references itself!".format(parent))
                    #    return

                    self._resolve_into_result(result, item.proto.data, self.wanted_config)
            else:
                if complex_:
                    if item.proto.data_type == TypedValue.TYPE_STRING:
                        v = str(item.proto.value)  # TODO string
                    else:
                        v = TypedValue.coerce_to_string(item.proto.data_type, item.proto.data)
                    result.append(v)
                else:
                    result.append((config, item.format_value()))


class AXMLResTablePackage:
    """AXMLResTablePackage"""

    def __init__(self, proto: axml_pb2.AXMLResTablePackage = None):
        """Initialize AXMLResTablePackage

        Args:
            proto (axml_pb2.AXML, optional): _description_. Defaults to None.
        """
        if proto:
            self.proto = proto
        else:
            self.proto = axml_pb2.AXMLResTablePackage()

    @property
    def get_proto(self):
        """get proto of AXMLResTablePackage

        Returns:
            _type_: _description_
        """
        return self.proto

    def compute(self, recursive: bool = True):
        """Compute all fields to have all AXML elements

        Args:
            recursive (bool, optional): need to recompute field recursively. Defaults to True.
        """

        if recursive:
            type_sp_string = StringBlocks(proto=self.proto.type_sp_string)
            type_sp_string.compute(update_size=True)
            self.proto.type_sp_string.CopyFrom(type_sp_string.proto)

            key_sp_string = StringBlocks(proto=self.proto.key_sp_string)
            key_sp_string.compute(update_size=True)
            self.proto.key_sp_string.CopyFrom(key_sp_string.proto)

            for restype in self.proto.restypes:
                if restype.hnd.type == axml_pb2.ResType.RES_TABLE_TYPE_SPEC_TYPE:
                    t = ARSCResTypeSpec(proto=restype.typespec)
                    t.compute(restype.hnd)
                    restype.typespec.CopyFrom(t.proto)
                elif restype.hnd.type == axml_pb2.ResType.RES_TABLE_TYPE_TYPE:
                    t = ARSCResTypeType(proto=restype.typetype)
                    t.compute(restype.hnd)
                    restype.hnd.header_size = 20 + len(
                        ARSCResTableConfig(proto=t.proto.config).pack()
                    )
                    restype.typetype.CopyFrom(t.proto)

        for restype in self.proto.restypes:
            if restype.hnd.type == axml_pb2.ResType.RES_TABLE_TYPE_SPEC_TYPE:
                restype.hnd.size = (
                    len(ARSCResTypeSpec(proto=restype.typespec).pack()) + AXML_HEADER_SIZE
                )
            elif restype.hnd.type == axml_pb2.ResType.RES_TABLE_TYPE_TYPE:
                restype.hnd.size = (
                    len(ARSCResTypeType(proto=restype.typetype).pack()) + AXML_HEADER_SIZE
                )  # - restype.hnd.header_size + AXML_HEADER_SIZE

        # TODO analyse if it is needed
        type_sp_string = StringBlocks(proto=self.proto.type_sp_string).pack()
        self.proto.typeStrings = self.proto.hnd.header_size
        self.proto.keyStrings = self.proto.typeStrings + len(type_sp_string)

        self.proto.hnd.size = len(self.pack())

    def pack(self) -> bytes:
        """pack the AXML element

        Returns:
            bytes: return the AXML element packed
        """
        header = AXMLHeader(proto=self.proto.hnd).pack()
        name = self.proto.name.encode("utf-16")[2:]
        name.ljust(256, b"\x00")
        type_sp_string = StringBlocks(proto=self.proto.type_sp_string).pack()
        key_sp_string = StringBlocks(proto=self.proto.key_sp_string).pack()
        data = b""
        for restype in self.proto.restypes:
            hnd = AXMLHeader(proto=restype.hnd)
            data += hnd.pack()
            if hnd.proto.type == axml_pb2.ResType.RES_TABLE_TYPE_SPEC_TYPE:
                d = ARSCResTypeSpec(proto=restype.typespec).pack()
                data += d
            elif hnd.proto.type == axml_pb2.ResType.RES_TABLE_TYPE_TYPE:
                d = ARSCResTypeType(proto=restype.typetype).pack()
                data += d
        return (
            header
            + pack("<L", self.proto.id)
            + name
            + pack(
                "<LLLL",
                self.proto.typeStrings,
                self.proto.lastPublicType,
                self.proto.keyStrings,
                self.proto.lastPublicKey,
            )
            + self.proto.padding
            + type_sp_string
            + key_sp_string
            + data
        )

    @staticmethod
    def from_axml(buff: bytes, proto=None):
        """Convert AXMLResTablePackage buffer to AXMLResTablePackage object

        Args:
            buff (bytes): buffer contain AXMLResTablePackage object

        Returns:
            tuple[pyaxml.AXMLResTablePackage, bytes]: return AXMLResTablePackage element and buffer offset at the end of the reading
        """
        content = buff
        res_table_package = AXMLResTablePackage()
        if proto:
            res_table_package.proto = proto
        header, buff = AXMLHeader.from_axml(buff, proto=res_table_package.proto.hnd)
        rest = content[header.proto.size :]
        content = content[: header.proto.size]
        # buff = buff[32-8:]
        res_table_package.proto.id = unpack("<L", buff[:4])[0]
        buff = buff[4:]
        res_table_package.proto.name = buff[:256].decode("utf-16")
        buff = buff[256:]
        (
            res_table_package.proto.typeStrings,
            res_table_package.proto.lastPublicType,
            res_table_package.proto.keyStrings,
            res_table_package.proto.lastPublicKey,
        ) = unpack("<LLLL", buff[: 4 * 4])
        buff = buff[4 * 4 :]

        t_str_off = len(content[res_table_package.proto.typeStrings :])
        k_str_off = len(content[res_table_package.proto.keyStrings :])
        if t_str_off > k_str_off:
            len_pad = len(buff) - t_str_off
        else:
            len_pad = len(buff) - k_str_off
        res_table_package.proto.padding = buff[:len_pad]

        _, at = StringBlocks.from_axml(
            content[res_table_package.proto.typeStrings :],
            proto=res_table_package.proto.type_sp_string,
        )

        _, ak = StringBlocks.from_axml(
            content[res_table_package.proto.keyStrings :],
            proto=res_table_package.proto.key_sp_string,
        )

        if len(ak) < len(at):
            content = ak
        else:
            content = at

        while len(content) > 0:
            spec = axml_pb2.ARSCResType()
            hdr, _ = AXMLHeader.from_axml(content, proto=spec.hnd)
            if hdr.proto.type == axml_pb2.ResType.RES_TABLE_TYPE_SPEC_TYPE:
                _, _ = ARSCResTypeSpec.from_axml(content[8 : hdr.proto.size], proto=spec.typespec)
                res_table_package.proto.restypes.append(spec)
            elif hdr.proto.type == axml_pb2.ResType.RES_TABLE_TYPE_TYPE:
                _, _ = ARSCResTypeType.from_axml(content[8 : hdr.proto.size], proto=spec.typetype)
                res_table_package.proto.restypes.append(spec)
            else:
                print("other types ??")
            content = content[hdr.proto.size :]

        return res_table_package, rest

    def set_spec_entry(self, id_: int, entry: int, index: int):
        """Add a spec entry

        Args:
            id_ (int): id of spec entry
            entry (int): _description_
            index (int): index in typetype stringblock of the element to set
        """
        for r in self.proto.restypes:
            if r.hnd.type == axml_pb2.ResType.RES_TABLE_TYPE_SPEC_TYPE and r.typespec.id == id_:
                if len(r.typespec.entries) < index:
                    r.typespec.entries[index] = entry
                else:
                    while index > len(r.typespec.entries):
                        r.typespec.entries.append(0)
                    r.typespec.entries.append(entry)

    def add_id_public(self, type_: str, name: str, id_path: int):
        """Add a public id in ARSC

        Args:
            type_ (str): type of public element
            name (str): name of public element
            id_path (int): id of element value to add in public

        Returns:
            _type_: return the id of this element
        """
        for r in self.proto.restypes:
            if r.hnd.type == axml_pb2.ResType.RES_TABLE_TYPE_TYPE:
                t = StringBlocks(proto=self.proto.type_sp_string).decode_str(r.typetype.id - 1)
                if t == type_:
                    st_key = StringBlocks(proto=self.proto.key_sp_string)
                    spec = ARSCResTableEntry.create_element(st_key.get(name), id_path)
                    self.proto.key_sp_string.CopyFrom(st_key.proto)
                    self.set_spec_entry(r.typetype.id, 0, len(r.typetype.tables))
                    r.typetype.tables.append(spec.proto)
                    return ARSC.convert_id(r.typetype.id, len(r.typetype.tables) - 1)

        st_type = StringBlocks(proto=self.proto.type_sp_string)
        id_ = st_type.get(type_)
        typetype = ARSCResTypeType.create_element(id_=id_ + 1)
        r = axml_pb2.ARSCResType()
        r.hnd.CopyFrom(AXMLHeader(axml_pb2.ResType.RES_TABLE_TYPE_TYPE).proto)
        # compute header without need to do it recursively
        r.hnd.header_size = 20 + len(
            ARSCResTableConfig(proto=typetype.proto.config).pack()
        )
        typetype.compute(r.hnd)
        r.typetype.CopyFrom(typetype.proto)

        st_key = StringBlocks(proto=self.proto.key_sp_string)
        spec = ARSCResTableEntry.create_element(st_key.get(name), id_path)
        self.proto.key_sp_string.CopyFrom(st_key.proto)
        r.typetype.tables.append(spec.proto)

        r_spec = axml_pb2.ARSCResType()
        r_spec.hnd.CopyFrom(AXMLHeader(axml_pb2.ResType.RES_TABLE_TYPE_SPEC_TYPE).proto)
        r_spec.hnd.header_size = 16
        r_spec.typespec.id = id_ + 1

        self.proto.restypes.append(r_spec)
        self.proto.restypes.append(r)
        self.set_spec_entry(id_ + 1, 0, 0)
        return ARSC.convert_id(r.typetype.id, len(r.typetype.tables) - 1)
