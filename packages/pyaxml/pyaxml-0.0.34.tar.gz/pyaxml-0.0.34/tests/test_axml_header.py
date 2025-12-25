import unittest
from struct import pack, unpack
import ctypes
from pyaxml.header import (
    TypedValue,
    AXMLHeader,
    AXML_HEADER_SIZE,
    AXMLHeaderXML,
    AXML_RES_TABLE_HEADER_SIZE,
    AXMLHeaderRESTABLE,
)


class TestTypedValue(unittest.TestCase):
    def test_complex_to_float(self):
        # Testing conversion of a complex value to float
        complex_value = 0x00180080  # Example complex value
        expected_float = 6144
        self.assertAlmostEqual(
            TypedValue.complex_to_float(complex_value), expected_float
        )

    def test_coerce_to_string(self):
        # Testing coercion to string for different types
        self.assertEqual(TypedValue.coerce_to_string(TypedValue.TYPE_NULL, 0), "nil")
        self.assertEqual(
            TypedValue.coerce_to_string(TypedValue.TYPE_REFERENCE, 0x1234), "@1234"
        )
        self.assertEqual(
            TypedValue.coerce_to_string(TypedValue.TYPE_ATTRIBUTE, 0x5678), "?5678"
        )
        self.assertEqual(
            TypedValue.coerce_to_string(TypedValue.TYPE_INT_HEX, 0xABCDEF), "0xabcdef"
        )
        self.assertEqual(
            TypedValue.coerce_to_string(TypedValue.TYPE_INT_BOOLEAN, 1), "true"
        )
        self.assertEqual(
            TypedValue.coerce_to_string(TypedValue.TYPE_INT_BOOLEAN, 0), "false"
        )


class TestAXMLHeader(unittest.TestCase):
    def test_pack(self):
        # Create an AXMLHeader instance
        header = AXMLHeader(type_=0x0001, size=16)
        packed_data = header.pack()
        # Verify the packed data
        expected_data = pack("<HHL", 0x0001, AXML_HEADER_SIZE, 16)
        self.assertEqual(packed_data, expected_data)

    def test_from_axml(self):
        # Create a packed buffer
        packed_data = pack("<HHL", 0x0001, AXML_HEADER_SIZE, 16) + b"extra_data"
        # Parse the buffer
        header, remaining_data = AXMLHeader.from_axml(packed_data)
        # Verify the parsed data
        self.assertEqual(header.proto.type, 0x0001)
        self.assertEqual(header.proto.header_size, AXML_HEADER_SIZE)
        self.assertEqual(header.proto.size, 16)
        self.assertEqual(remaining_data, b"extra_data")


class TestAXMLHeaderXML(unittest.TestCase):
    def test_from_axml_valid(self):
        # Create a valid buffer
        packed_data = pack("<HHL", 0x0003, AXML_HEADER_SIZE, 32) + b"extra_data"
        # Parse the buffer
        header_xml, remaining_data = AXMLHeaderXML.from_axml(packed_data)
        # Verify the parsed data
        self.assertEqual(header_xml.proto.type, 0x0003)
        self.assertEqual(header_xml.proto.header_size, AXML_HEADER_SIZE)
        self.assertEqual(header_xml.proto.size, 32)
        self.assertEqual(remaining_data, b"extra_data")

    def test_from_axml_invalid_type(self):
        # Create an invalid buffer
        packed_data = pack("<HHL", 0x0004, AXML_HEADER_SIZE, 32) + b"extra_data"
        # Verify that a TypeError is raised
        with self.assertRaises(TypeError):
            AXMLHeaderXML.from_axml(packed_data)


class TestAXMLHeaderRESTABLE(unittest.TestCase):
    def test_pack(self):
        # Create an AXMLHeaderRESTABLE instance
        header_restable = AXMLHeaderRESTABLE(size=64, package_count=5)
        packed_data = header_restable.pack()
        # Verify the packed data
        expected_data = pack("<HHL", 0x0002, AXML_RES_TABLE_HEADER_SIZE, 64) + pack(
            "<L", 5
        )
        self.assertEqual(packed_data, expected_data)

    def test_from_axml(self):
        # Create a packed buffer
        packed_data = (
            pack("<HHL", 0x0002, AXML_RES_TABLE_HEADER_SIZE, 64)
            + pack("<L", 5)
            + b"extra_data"
        )
        # Parse the buffer
        header_restable, remaining_data = AXMLHeaderRESTABLE.from_axml(packed_data)
        # Verify the parsed data
        self.assertEqual(header_restable.proto.hnd.type, 0x0002)
        self.assertEqual(
            header_restable.proto.hnd.header_size, AXML_RES_TABLE_HEADER_SIZE
        )
        self.assertEqual(header_restable.proto.hnd.size, 64)
        self.assertEqual(header_restable.proto.package_count, 5)
        self.assertEqual(remaining_data, b"extra_data")


if __name__ == "__main__":
    unittest.main()
