import unittest
from struct import pack
from pyaxml.arsctype import ARSCResTableEntry, ARSCComplex, ARSCResStringPoolRef
from pyaxml.proto import axml_pb2


class TestARSCResTableEntry(unittest.TestCase):
    def setUp(self):
        self.proto = axml_pb2.ARSCResTableEntry()

    def test_initialization_with_proto(self):
        obj = ARSCResTableEntry(proto=self.proto)
        self.assertIs(obj.proto, self.proto)

    def test_initialization_without_proto(self):
        obj = ARSCResTableEntry()
        self.assertIsInstance(obj.proto, axml_pb2.ARSCResTableEntry)

    def test_get_proto_property(self):
        obj = ARSCResTableEntry(proto=self.proto)
        self.assertIs(obj.get_proto, self.proto)

    def test_pack_simple_entry(self):
        obj = ARSCResTableEntry(proto=self.proto)
        obj.proto.size = 8
        obj.proto.flags = 0  # Not complex
        obj.proto.index = 42

        packed_data = obj.pack()
        expected_header = pack("<HHI", 8, 0, 42)
        expected_data = b"\x00" * 8
        self.assertEqual(packed_data, expected_header + expected_data)

    def test_pack_complex_entry(self):
        obj = ARSCResTableEntry(proto=self.proto)
        obj.proto.size = 8
        obj.proto.flags = ARSCResTableEntry.FLAG_COMPLEX  # Complex entry
        obj.proto.index = 42

        packed_data = obj.pack()
        expected_header = pack("<HHI", 8, ARSCResTableEntry.FLAG_COMPLEX, 42)
        expected_data = b"\x00" * 8
        self.assertEqual(packed_data, expected_header + expected_data)

    def test_is_public(self):
        obj = ARSCResTableEntry(proto=self.proto)
        obj.proto.flags = ARSCResTableEntry.FLAG_PUBLIC
        self.assertTrue(obj.is_public())

        obj.proto.flags = 0
        self.assertFalse(obj.is_public())

    def test_is_complex(self):
        obj = ARSCResTableEntry(proto=self.proto)
        obj.proto.flags = ARSCResTableEntry.FLAG_COMPLEX
        self.assertTrue(obj.is_complex())

        obj.proto.flags = 0
        self.assertFalse(obj.is_complex())

    def test_is_weak(self):
        obj = ARSCResTableEntry(proto=self.proto)
        obj.proto.flags = ARSCResTableEntry.FLAG_WEAK
        self.assertTrue(obj.is_weak())

        obj.proto.flags = 0
        self.assertFalse(obj.is_weak())

    def test_create_element(self):
        index_name = 42
        data = 100

        obj = ARSCResTableEntry.create_element(index_name, data)
        self.assertEqual(obj.proto.size, 8)
        self.assertEqual(obj.proto.index, index_name)
        self.assertEqual(obj.proto.key.size, 8)
        self.assertEqual(obj.proto.key.data_type, 3)
        self.assertEqual(obj.proto.key.data, data)

    def test_from_axml_simple_entry(self):
        buffer = pack("<HHI", 8, 0, 42) + ARSCResStringPoolRef().pack()
        obj, remaining = ARSCResTableEntry.from_axml(buffer)

        self.assertEqual(obj.proto.size, 8)
        self.assertEqual(obj.proto.flags, 0)
        self.assertEqual(obj.proto.index, 42)
        self.assertEqual(remaining, b"")

    def test_from_axml_complex_entry(self):
        orig = axml_pb2.ARSCResTableEntry()
        orig.size = 8
        orig.flags = ARSCResTableEntry.FLAG_COMPLEX
        orig.index = 42
        orig.item.CopyFrom(ARSCComplex().proto)
        buffer = ARSCResTableEntry(proto=orig).pack()
        obj, remaining = ARSCResTableEntry.from_axml(buffer)

        self.assertEqual(obj.proto.size, 8)
        self.assertEqual(obj.proto.flags, ARSCResTableEntry.FLAG_COMPLEX)
        self.assertEqual(obj.proto.index, 42)
        self.assertEqual(remaining, b"")


if __name__ == "__main__":
    unittest.main()
