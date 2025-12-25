from struct import pack, unpack
import sys
from typing import Union, Tuple
import logging

try:
    from pyaxml.proto import axml_pb2
    from pyaxml.header import AXMLHeader, AXML_STRING_POOL_HEADER_SIZE
except ImportError:
    print("proto is not build")
    sys.exit(1)


class AXMLHeaderSTRINGPOOL:
    """AXMLHeaderSTRINGPOOL class to build an AXMLHeaderSTRINGPOOL element"""

    def __init__(
        self,
        sb: Union[list, None] = None,
        size: int = 0,
        proto: axml_pb2.AXMLHeaderSTRINGPOOL = None,
    ):
        """Initialize an AXMLHeader of STRING_POOL

        Args:
            sb (list, optional): list of Stringblock elements. Defaults to None.
            size (int, optional): size of data contain belong to this AXMLHeader. Defaults to 0.
            proto (axml_pb2.AXMLHeaderSTRINGPOOL, optional):
                define AXMLHeaderSTRINGPOOL by a protobuff. Defaults to None.
        """
        # TODO make version with initilisation without proto
        if proto:
            self.proto = proto
        else:
            self.proto = axml_pb2.AXMLHeaderSTRINGPOOL()

    def compute(self):
        """Compute all fields to have a Stringpool element"""

    def pack(self) -> bytes:
        """pack the AXMLHeaderSTRINGPOOL element

        Returns:
            bytes: return the AXMLHeaderSTRINGPOOL element packed
        """
        # TODO add style block for the moment force to 0
        self.proto.len_styleblocks = 0
        return AXMLHeader(proto=self.proto.hnd).pack() + pack(
            "<LLLLL",
            self.proto.len_stringblocks,
            self.proto.len_styleblocks,
            self.proto.flag,
            self.proto.stringoffset,
            self.proto.styleoffset,
        )

    @staticmethod
    def from_axml(buff: bytes, proto=None):
        """Convert AXMLHeaderSTRINGPOOL buffer to AXMLHeaderSTRINGPOOL object

        Args:
            buff (bytes): buffer contain AXMLHeaderSTRINGPOOL object

        Returns:
            tuple[pyaxml.AXMLHeaderSTRINGPOOL, bytes]:
                return AXMLHeaderSTRINGPOOL element and buffer offset at the end of the reading
        """
        hnd_str_pool = AXMLHeaderSTRINGPOOL()
        if proto:
            hnd_str_pool.proto = proto
        _, buff = AXMLHeader.from_axml(buff, proto=hnd_str_pool.proto.hnd)
        (
            hnd_str_pool.proto.len_stringblocks,
            hnd_str_pool.proto.len_styleblocks,
            hnd_str_pool.proto.flag,
            hnd_str_pool.proto.stringoffset,
            hnd_str_pool.proto.styleoffset,
        ) = unpack("<LLLLL", buff[: 5 * 4])
        return hnd_str_pool, buff[5 * 4 :]


##############################################################################
#
#                              STRINGBLOCKS
#
##############################################################################


class StringBlock:
    """StringBlock class to build an StringBlock element"""

    def __init__(
        self,
        data: str = "",
        size: int = 0,
        utf8: bool = False,
        proto: axml_pb2.StringBlock = None,
    ):
        """initialize a stringblock element

        Args:
            data (str, optional): value of the stringblock. Defaults to "".
            size (int, optional): size of data contain belong to this Stringblock. Defaults to 0.
            utf8 (bool, optional): Stringblock can be encoded in UTF8 or UTF16.
                 set True if you want to encode in UTF8 else UTF16. Defaults to False.
            proto (axml_pb2.StringBlock, optional): define StringBlock by a protobuff.
                 Defaults to None.
        """
        self.not_decoded = False
        if proto:
            self.proto = proto
            self.utf8 = utf8
        else:
            self.proto = axml_pb2.StringBlock()
            self.utf8 = utf8
            if self.utf8:
                self.proto.data = data.encode("utf-8")
                self.proto.padding = b"\x00"
            else:
                self.proto.data = data.encode("utf-16")[2:]
                self.proto.padding = b"\x00\x00"
            self.proto.size = size

    def compute(self):
        """Compute all fields to have a StringBlock element"""
        _ = self.proto.size
        if self.utf8:
            try:
                size = len(self.proto.data)

                # print(self.proto.data, hex(self.proto.size))
                decoded_size = len(self.proto.data.decode())
                # if (decoded_size | size << 8) != self.proto.size:
                #    print(hex(size), hex(decoded_size | size << 8), hex(self.proto.size), self.proto.data)
                if size > 0x7F:
                    self.proto.size = (
                        (decoded_size | 0x80)
                    )
                    self.proto.redundant_size = size | 0x80
                else:
                    self.proto.redundant_size = size
                    self.proto.size = decoded_size
            except UnicodeDecodeError:
                logging.error(self.proto.data)
                logging.error("error during decode couldn't recompute Stringblock")
        else:
            size = int(len(self.proto.data) / 2)
            if size > 0x7FFF:
                self.proto.size = (size >> 16) | 0x8000
                self.proto.redundant_size = size & 0xFFFF
            else:
                self.proto.size = size

    def pack(self) -> bytes:
        """pack the StringBlock element

        Returns:
            bytes: return the StringBlock element packed
        """
        redundant = b""
        if self.proto.HasField("redundant_size"):
            redundant = pack("<B", self.proto.redundant_size)
        if self.utf8:
            return pack("<B", self.proto.size) + redundant + self.proto.data + self.proto.padding
        return pack("<H", self.proto.size) + redundant + self.proto.data + self.proto.padding
    
    def decode_length(self, data : bytes) -> Tuple[int, int]:
        """
        Decode a variable-length encoded value.
        
        Args:
            data: bytes containing encoded data
            proto: proto of StringBlock to fill
            
        Returns:
            tuple: (decoded_length, new_offset) where new_offset points 
                to the next byte after the encoded length
            
        Raises:
            IOError: If data is missing at required positions
        """

        offset = 0

        if offset >= len(data):
            raise IOError(IOError.PAGES_MISSING)
        
        length = data[offset]

        if (length & 0x80) != 0:
            # Multi-byte encoding
            offset += 1
            if offset >= len(data):
                raise IOError(IOError.PAGES_MISSING)
            
            # Combine high 7 bits with next 8 bits
            length = ((length & 0x7F) << 8) | data[offset]
        self.proto.size = length
        
        offset += 1

        # second time to decode

        if offset >= len(data):
            raise IOError(IOError.PAGES_MISSING)
        
        length = data[offset]

        if (length & 0x80) != 0:
            # Multi-byte encoding
            offset += 1
            if offset >= len(data):
                raise IOError(IOError.PAGES_MISSING)
            
            # Combine high 7 bits with next 8 bits
            length = ((length & 0x7F) << 8) | data[offset]
        self.proto.redundant_size = length
        
        offset += 1
        #print("UTF8", self.proto)


        return length, offset


    def decode_length_16(self, data):
        """
        Decode a variable-length encoded value.
        
        Args:
            data: bytes containing encoded data
            proto: proto of StringBlock to fill
            
        Returns:
            tuple: (decoded_length, new_offset) where new_offset points 
                to the next byte after the encoded length
            
        Raises:
            IOError: If data is missing at required positions
        """
        offset = 0
        if offset + 1 >= len(data):
            raise IOError(IOError.PAGES_MISSING)
        
        length = unpack("<H", data[offset:offset+2])[0]
        offset += 2
        
        if (length & 0x8000) != 0:
            # Multi-word encoding
            if offset + 1 >= len(data):
                raise IOError(IOError.PAGES_MISSING)
            
            # Read second uint16
            second_word = unpack("<H", data[offset:offset+2])[0]
            offset += 2
            
            # Combine high 15 bits with next 16 bits
            length = ((length & 0x7FFF) << 16) | second_word
        
        self.proto.size = length
        
        return length, offset

    @staticmethod
    def from_axml(buff: bytes, utf8: bool, proto=None) -> "Tuple[pyaxml.StringBlock, bytes]":
        """Convert StringBlock buffer to StringBlock object

        Args:
            buff (bytes): buffer contain StringBlock object
            utf8 (bool) : specify the encoding of string

        Returns:
            tuple[pyaxml.StringBlock, bytes]:
                 return StringBlock element and buffer offset at the end of the reading
        """
        str_block = StringBlock()
        if proto:
            str_block.proto = proto
        str_block.utf8 = utf8
        if str_block.utf8:
            size, offset = str_block.decode_length(buff)
        else:
            size, offset = str_block.decode_length_16(buff)
            size *= 2

        str_block.proto.data = buff[offset : offset + size]
        str_block.proto.padding = buff[offset + size :]
        #print(str_block.proto)
        return str_block, b""


class StringBlocks:
    """StringBlocks class to build all StringBlocks elements"""

    def __init__(self, proto: axml_pb2.StringBlocks = None):
        """initialize the bunch of StringBlocks element

        Args:
            proto (axml_pb2.StringBlocks, optional):
                 define Stringblocks by a protobuff. Defaults to None.
        """

        if proto:
            self.proto = proto
        else:
            self.proto = axml_pb2.StringBlocks()

    def compute(self, update_size=False):
        """Compute all fields to have all StringBlocks elements"""

        idx = 0
        del self.proto.stringoffsets[:]
        for s in self.proto.stringblocks:
            self.proto.stringoffsets.append(idx)
            s_obj = StringBlock(
                proto=s,
                utf8=self.proto.hnd.flag & axml_pb2.UTF8_FLAG == axml_pb2.UTF8_FLAG,
            )
            if update_size:
                s_obj.compute()
                s.CopyFrom(s_obj.proto)
            idx += len(s_obj.pack())
        sb = b"".join(
            StringBlock(
                proto=elt,
                utf8=self.proto.hnd.flag & axml_pb2.UTF8_FLAG == axml_pb2.UTF8_FLAG,
            ).pack()
            for elt in self.proto.stringblocks
        )
        self.proto.pad_stringblocks = b"\x00" * (4 - (len(sb) % 4)) if len(sb) % 4 != 0 else b""

        self.proto.hnd.stringoffset = (
            AXML_STRING_POOL_HEADER_SIZE
            + len(b"".join(pack("<I", x) for x in self.proto.stringoffsets))
            + len(b"".join(pack("<I", x) for x in self.proto.styleoffsets))
        )

        if len(self.proto.styleoffsets) > 0:
            self.proto.hnd.styleoffset = (
                self.proto.hnd.stringoffset + len(sb) + len(self.proto.pad_stringblocks)
            )
        # self.proto.hnd.styleoffset = self.proto.hnd.stringoffset \
        # + len(self.align(b"".join(StringBlock(proto=elt, \
        # utf8=self.proto.hnd.flag & axml_pb2.UTF8_FLAG == axml_pb2.UTF8_FLAG).pack() \
        #  for elt in self.proto.stringblocks)))
        AXMLHeader(
            axml_pb2.RES_STRING_POOL_TYPE,
            len(self.pack()),
            base_proto=self.proto.hnd.hnd,
        )
        self.proto.hnd.hnd.header_size = AXML_STRING_POOL_HEADER_SIZE
        self.proto.hnd.len_stringblocks = len(self.proto.stringoffsets)
        self.proto.hnd.len_styleblocks = len(self.proto.styleoffsets)

    def align(self, buf: bytes) -> bytes:
        """Align stringblocks elements

        Args:
            buf (bytes): align the buffer given in input

        Returns:
            bytes: return the element with padding to align
        """
        pad = b"\x00" * (4 - (len(buf) % 4))
        if len(pad) == 4:
            return buf
        return buf + pad

    def get(self, name: str, index=-1) -> int:
        """Get index of a stringblock or if it doesn't exist append a new one.

        Args:
            name (str): the name of the stringblock

        Returns:
            int: return the index of the stringblock
        """
        if index != -1:
            tmp = StringBlock(
                data=name,
                utf8=self.proto.hnd.flag & axml_pb2.UTF8_FLAG == axml_pb2.UTF8_FLAG,
            )
            tmp.compute()
            while len(self.proto.stringblocks) < index:
                mock = StringBlock(
                data="",
                utf8=self.proto.hnd.flag & axml_pb2.UTF8_FLAG == axml_pb2.UTF8_FLAG,
                )
                mock.compute()
                self.proto.stringblocks.append(mock.proto)
            if len(self.proto.stringblocks) == index:
                self.proto.stringblocks.append(tmp.proto)
            else:
                self.proto.stringblocks[index].CopyFrom(tmp.proto)
            return index
        try:
            index = self.index(name)
        except ValueError:
            index = len(self.proto.stringblocks)
            tmp = StringBlock(
                data=name,
                utf8=self.proto.hnd.flag & axml_pb2.UTF8_FLAG == axml_pb2.UTF8_FLAG,
            )
            tmp.compute()
            self.proto.stringblocks.append(tmp.proto)
        return index

    def index(self, name: str) -> int:
        """Get index of a stringblock or if it doesn't exist raise an error

        Args:
            name (str): the name of the stringblock

        Raises:
            ValueError: raise ValueError if this element didn't exist

        Returns:
            int: return the index of the stringblock
        """
        name_encoded = StringBlock(
            data=name,
            utf8=self.proto.hnd.flag & axml_pb2.UTF8_FLAG == axml_pb2.UTF8_FLAG,
        )
        for i, elt in enumerate(self.proto.stringblocks):
            if elt.data == name_encoded.proto.data:
                return i
        raise ValueError

    def update(self, index: int, name: str) -> None:
        """Update the value of stringblock index with the value name

        Args:
            index (int): index of stringblock
            name (str): value of stringblock
        """
        name_encoded = StringBlock(
            data=name,
            utf8=self.proto.hnd.flag & axml_pb2.UTF8_FLAG == axml_pb2.UTF8_FLAG,
        )
        name_encoded.compute()
        self.proto.stringblocks[index].CopyFrom(name_encoded.proto)

    def replace(self, old_name: str, new_name: str) -> None:
        """Replace a stringblock by a new one

        Args:
            old_name (str): old stringblock
            new_name (str): new stringblock
        """
        index = self.index(old_name)
        self.update(index, new_name)

    def switch(self, name1: str, name2: str) -> None:
        """Switch a name1 stringblock by name2 stringblock

        Args:
            name1 (str): stringblock 1
            name2 (str): stringblock 2
        """
        index1 = self.index(name1)
        index2 = self.index(name2)
        self.update(index1, name2)
        self.update(index2, name1)

    def decode_str(self, index: int) -> str:
        """Decode a stringblock and show its representation in string

        Args:
            index (int): index of stringblock

        Returns:
            str: string representation
        """
        try:
            data = self.proto.stringblocks[index].data
        except IndexError as exc:
            sys.stderr.write(str(self.proto))
            raise IndexError(f"No StringBlock at index: {index}") from exc
        try:
            return (
                data.decode("utf-8")
                if self.proto.hnd.flag & axml_pb2.UTF8_FLAG == axml_pb2.UTF8_FLAG
                else data.decode("utf-16")
            )
        except UnicodeDecodeError:
            return data

    def pack(self) -> bytes:
        """pack the StringBlocks element

        Returns:
            bytes: return the StringBlocks element packed
        """
        sb_offsets = b"".join(pack("<I", x) for x in self.proto.stringoffsets)
        st_offsets = b"".join(pack("<I", x) for x in self.proto.styleoffsets)
        sb = b"".join(
            StringBlock(
                proto=elt,
                utf8=self.proto.hnd.flag & axml_pb2.UTF8_FLAG == axml_pb2.UTF8_FLAG,
            ).pack()
            for elt in self.proto.stringblocks
        )
        sb += self.proto.pad_stringblocks
        st = b""  # TODO
        return AXMLHeaderSTRINGPOOL(proto=self.proto.hnd).pack() + sb_offsets + st_offsets + sb + st

    @staticmethod
    def from_axml(buff: bytes, proto=None):
        """Convert StringBlocks buffer to StringBlocks object

        Args:
            buff (bytes): buffer contain StringBlocks object

        Returns:
            tuple[pyaxml.StringBlocks, bytes]:
              return StringBlocks element and buffer offset at the end of the reading
        """
        rest = buff
        cur_buff = buff
        str_blocks = StringBlocks()
        if proto:
            str_blocks.proto = proto
        hnd, buff = AXMLHeaderSTRINGPOOL.from_axml(buff, proto=str_blocks.proto.hnd)
        buff = buff[: hnd.proto.hnd.size - hnd.proto.hnd.header_size]
        rest = rest[hnd.proto.hnd.size :]
        for i in range(str_blocks.proto.hnd.len_stringblocks):
            str_blocks.proto.stringoffsets.append(unpack("<I", buff[i * 4 : (i + 1) * 4])[0])
        buff = buff[str_blocks.proto.hnd.len_stringblocks * 4 :]
        for i in range(str_blocks.proto.hnd.len_styleblocks):
            # if len(buff[i * 4 : (i + 1) * 4]) != 4:
            #    print(f"WARNING: buff for styleblocks is too small")
            #    return str_blocks, rest
            str_blocks.proto.styleoffsets.append(unpack("<I", buff[i * 4 : (i + 1) * 4])[0])
        buff = buff[str_blocks.proto.hnd.len_styleblocks * 4 :]
        if len(str_blocks.proto.stringoffsets) > 0:
            if str_blocks.proto.hnd.len_styleblocks > 0:
                temp_buff = cur_buff[
                    str_blocks.proto.hnd.stringoffset : str_blocks.proto.hnd.styleoffset
                ]
            else:
                temp_buff = cur_buff[str_blocks.proto.hnd.stringoffset : hnd.proto.hnd.size]
            st_offsets_sort = sorted(set(list(str_blocks.proto.stringoffsets).copy()))
            for i in range(str_blocks.proto.hnd.len_stringblocks):
                next_index = st_offsets_sort.index(str_blocks.proto.stringoffsets[i]) + 1
                if len(st_offsets_sort) > next_index:
                    next_value = st_offsets_sort[next_index]
                    stbl, _ = StringBlock.from_axml(
                        temp_buff[str_blocks.proto.stringoffsets[i] : next_value],
                        str_blocks.proto.hnd.flag & axml_pb2.UTF8_FLAG == axml_pb2.UTF8_FLAG,
                    )
                else:
                    last_str, _ = StringBlock.from_axml(
                        temp_buff[str_blocks.proto.stringoffsets[i] :],
                        str_blocks.proto.hnd.flag & axml_pb2.UTF8_FLAG == axml_pb2.UTF8_FLAG,
                    )
                    stbl = last_str
                str_blocks.proto.stringblocks.append(stbl.proto)
            buff = buff[str_blocks.proto.stringoffsets[-1] + len(last_str.pack()) :]
            if str_blocks.proto.hnd.len_styleblocks > 0:
                str_blocks.proto.pad_stringblocks = buff[: str_blocks.proto.styleoffsets[0]]
            else:
                str_blocks.proto.pad_stringblocks = buff[: hnd.proto.hnd.size]
        # TODO style
        return str_blocks, rest
