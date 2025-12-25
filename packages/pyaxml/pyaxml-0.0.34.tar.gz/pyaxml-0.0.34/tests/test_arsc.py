import unittest
from struct import pack
from pyaxml.arscobject import ARSC
from pyaxml.stringblocks import StringBlocks
from pyaxml.proto import axml_pb2


class TestARSC(unittest.TestCase):
    def setUp(self):
        """Set up a basic ARSC instance with real axml_pb2 data."""
        # Create a proto instance for the test
        self.proto = axml_pb2.ARSC()

        # Populate proto with basic test data
        self.proto.header_res.hnd.size = 0
        self.proto.header_res.package_count = 1

        # Add a simple package
        package = self.proto.restablespackage.add()
        package.name = "test_package\x00"

        str_blocks = StringBlocks()
        str_blocks.get("string")
        package.type_sp_string.CopyFrom(str_blocks.proto)

        str_blocks = StringBlocks()
        str_blocks.get("name")
        package.key_sp_string.CopyFrom(str_blocks.proto)

        str_blocks = StringBlocks()
        str_blocks.get("test1")
        str_blocks.get("value")
        str_blocks.get("val")
        str_blocks.get("test4")

        self.proto.stringblocks.CopyFrom(str_blocks.proto)
        # Add type and key string blocks to the package
        # package.type_sp_string.append("string\x00")
        # package.key_sp_string.append("name\x00")

        # Add a simple resource type
        restype = package.restypes.add()
        restype.hnd.type = axml_pb2.ResType.RES_TABLE_TYPE_TYPE
        restype.typetype.id = 1
        entry = restype.typetype.tables.add()
        entry.present = True
        entry.index = 0
        entry.key.data = 1  # Simulated value
        entry.key.data_type = 3  # Simulate a string type

        self.arsc = ARSC(proto=self.proto)

    def test_get_packages(self):
        """Test get_packages method."""
        packages = self.arsc.get_packages()
        self.assertEqual(packages, ["test_package"])

    def test_get_value(self):
        """Test get_value method."""

        # Fetch the value using the ARSC method
        value = self.arsc.get_value("test_package", 0x7F010000)
        self.assertEqual(value, "value")

    def test_get_id(self):
        """Test get_id method."""
        type_, key, rid = self.arsc.get_id("test_package", 0x7F010000)
        self.assertEqual(type_, "string")
        self.assertEqual(key, "name")
        self.assertEqual(rid, 0x7F010000)

    def test_get_resource_xml_name(self):
        """Test get_resource_xml_name method."""
        xml_name = self.arsc.get_resource_xml_name(0x7F010000, "test_package")
        self.assertEqual(xml_name, "@string/name")

    def test_add_id_public(self):
        """Test adding a new ID to the public strings."""
        new_id = self.arsc.add_id_public(
            "test_package", "string", "new_name", "new_value"
        )
        self.assertIsNotNone(new_id)

    def test_list_packages(self):
        """Test list_packages method."""
        output = self.arsc.list_packages()
        self.assertIn('type="string"', output)
        self.assertIn('name="name"', output)


if __name__ == "__main__":
    unittest.main()
