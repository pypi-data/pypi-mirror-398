import unittest
from struct import pack, unpack
from pyaxml.arsctype import ARSCResTypeType, ARSCResTableConfig
from pyaxml.proto import axml_pb2
from pyaxml.header import AXMLHeader


class TestARSCResTypeType(unittest.TestCase):
    def setUp(self):
        self.proto = axml_pb2.ARSCResTypeType()

    def test_initialization_with_proto(self):
        obj = ARSCResTypeType(proto=self.proto)
        self.assertIs(obj.proto, self.proto)

    def test_initialization_without_proto(self):
        obj = ARSCResTypeType()
        self.assertIsInstance(obj.proto, axml_pb2.ARSCResTypeType)

    def test_get_proto_property(self):
        obj = ARSCResTypeType(proto=self.proto)
        self.assertIs(obj.get_proto, self.proto)

    def test_compute(self):
        header = AXMLHeader().proto
        obj = ARSCResTypeType(proto=self.proto)
        obj.compute(header)

        self.assertEqual(len(obj.proto.entries), len(obj.proto.tables))
        self.assertEqual(obj.proto.entryCount, len(obj.proto.entries))
        self.assertEqual(
            obj.proto.entryStart, header.header_size + 4 * len(obj.proto.entries)
        )

    def test_pack(self):
        obj = ARSCResTypeType(proto=self.proto)
        obj.proto.entries.append(1)
        obj.proto.entries.append(0xFFFFFFFF)
        obj.proto.id = 1
        obj.proto.flags = 0
        obj.proto.reserved = 0
        obj.proto.entryCount = len(obj.proto.entries)
        obj.proto.entryStart = 100

        packed_data = obj.pack()
        expected_head = pack("<BBHII", 1, 0, 0, 2, 100)
        expected_entries = pack("<I", 1) + pack("<I", 0xFFFFFFFF)
        expected_tables = b"\x00\x01\x02\x03" * len(obj.proto.tables)
        pad = b"\x00" * 16
        self.assertEqual(packed_data, expected_head + pad + expected_entries)

    def test_from_axml(self):
        orig = axml_pb2.ARSCResTypeType()
        orig.id = 1
        orig.flags = 0
        orig.entryCount = 2
        orig.config.CopyFrom(ARSCResTableConfig().proto)
        orig.entries.append(0xFFFFFFFF)
        orig.entries.append(0xFFFFFFFF)
        buffer = ARSCResTypeType(proto=orig).pack()

        obj, _ = ARSCResTypeType.from_axml(buffer)

        self.assertEqual(obj.proto.id, 1)
        self.assertEqual(obj.proto.flags, 0)
        self.assertEqual(obj.proto.entryCount, 2)
        self.assertEqual(len(obj.proto.entries), 2)
        self.assertEqual(obj.proto.entries[0], 0xFFFFFFFF)
        self.assertEqual(obj.proto.entries[1], 0xFFFFFFFF)

    def test_create_element(self):
        obj = ARSCResTypeType.create_element(42)
        self.assertEqual(obj.proto.id, 42)
        self.assertEqual(obj.proto.flags, 0)
        self.assertEqual(obj.proto.entryCount, 0)
        # self.assertIsInstance(obj.proto.config, ARSCResTableConfig)


if __name__ == "__main__":
    unittest.main()
